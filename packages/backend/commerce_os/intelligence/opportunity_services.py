from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.discovery_models import OpportunityCandidate
from commerce_os.intelligence.errors import (
    IntelligenceNotFoundError,
    IntelligenceScopeError,
    IntelligenceValidationError,
)
from commerce_os.intelligence.opportunity_models import (
    CandidateStatus,
    MarketOpportunity,
    OpportunityEvidence,
    OpportunityRisk,
    OpportunityScore,
    ProductCandidate,
    ProductCandidateEvidence,
    ProductEvaluation,
)
from commerce_os.intelligence.opportunity_schemas import (
    OpportunityEvidenceCreate,
    OpportunityRiskCreate,
    OpportunityScoreCreate,
    ProductCandidateCreate,
    ProductCandidateRead,
    ProductEvaluationDashboard,
    ProductEvaluationRead,
    ProductOpportunityCandidateCreate,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

SCORING_FORMULA_VERSION = "v1.0"
PRODUCT_EVALUATION_FORMULA_VERSION = "deterministic-product-evaluation-v1"
RISK_VALUES = {"low": 100.0, "medium": 70.0, "high": 40.0, "critical": 10.0}


def _get_scoped_opportunity(
    session: Session, opportunity_id: UUID, organization_id: UUID
) -> MarketOpportunity:
    opportunity = session.get(MarketOpportunity, opportunity_id)
    if opportunity is None:
        raise IntelligenceNotFoundError("Market opportunity was not found.")
    if opportunity.organization_id != organization_id:
        raise IntelligenceScopeError("Market opportunity belongs to another organization.")
    return opportunity


class OpportunityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_evidence(self, payload: OpportunityEvidenceCreate) -> OpportunityEvidence:
        _get_scoped_opportunity(self.session, payload.opportunity_id, payload.organization_id)
        if payload.source_type == "customer_signal":
            try:
                signal_id = UUID(payload.source_reference)
            except ValueError as error:
                raise IntelligenceValidationError(
                    "Customer-signal evidence requires a signal UUID source reference."
                ) from error
            if not reference_belongs_to_organization(
                self.session,
                table_name="customer_signals",
                reference_id=signal_id,
                organization_id=payload.organization_id,
            ):
                raise IntelligenceScopeError("Customer signal was not found in this organization.")
        evidence = OpportunityEvidence(**payload.model_dump())
        self.session.add(evidence)
        self.session.commit()
        self.session.refresh(evidence)
        return evidence

    def add_candidate(self, payload: ProductCandidateCreate) -> ProductCandidate:
        _get_scoped_opportunity(self.session, payload.opportunity_id, payload.organization_id)
        candidate = ProductCandidate(**payload.model_dump())
        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(candidate)
        return candidate

    def evaluate_candidate(
        self, payload: ProductOpportunityCandidateCreate, actor_id: UUID
    ) -> ProductCandidate:
        opportunity = self.session.get(OpportunityCandidate, payload.opportunity_candidate_id)
        if opportunity is None or opportunity.organization_id != payload.organization_id:
            raise IntelligenceScopeError(
                "Opportunity candidate was not found in this organization."
            )
        if opportunity.status != "accepted":
            raise IntelligenceValidationError(
                "Product evaluation requires a human-accepted opportunity candidate."
            )
        if payload.estimated_price_range.minimum > payload.estimated_price_range.maximum:
            raise IntelligenceValidationError("Estimated price range minimum exceeds maximum.")
        if payload.estimated_cost_range.minimum > payload.estimated_cost_range.maximum:
            raise IntelligenceValidationError("Estimated cost range minimum exceeds maximum.")
        if payload.estimated_price_range.currency != payload.estimated_cost_range.currency:
            raise IntelligenceValidationError("Price and cost ranges must use the same currency.")
        self._validate_evidence(payload)
        risk_levels = [
            payload.fulfillment_risk,
            payload.ip_risk,
            payload.regulatory_risk,
            payload.payment_risk,
            payload.dispute_risk,
        ]
        risk_score = sum(RISK_VALUES[item] for item in risk_levels) / len(risk_levels)
        simplicity = RISK_VALUES[payload.shipping_complexity]
        score = round(
            payload.demand_fit_score * 0.25
            + payload.problem_solution_fit * 0.25
            + payload.gross_margin_estimate * 100 * 0.20
            + simplicity * 0.15
            + risk_score * 0.15,
            2,
        )
        recommendation = (
            "Suitable for further validation"
            if score >= 65
            else "Requires additional evidence before validation"
        )
        candidate = ProductCandidate(
            organization_id=payload.organization_id,
            opportunity_id=None,
            opportunity_candidate_id=payload.opportunity_candidate_id,
            product_name=payload.product_name,
            category=payload.product_category,
            customer_need=payload.customer_problem,
            target_customer=payload.target_customer,
            product_description=payload.product_description,
            value_proposition=payload.value_proposition,
            confidence_score=payload.confidence_score,
            estimated_margin=payload.gross_margin_estimate,
            risk_level=max(risk_levels, key=lambda item: 100 - RISK_VALUES[item]),
            status=CandidateStatus.DRAFT,
        )
        self.session.add(candidate)
        self.session.flush()
        evaluation_values = payload.model_dump(
            exclude={
                "organization_id",
                "opportunity_candidate_id",
                "product_name",
                "product_category",
                "customer_problem",
                "target_customer",
                "product_description",
                "value_proposition",
                "confidence_score",
                "evidence",
            },
            mode="json",
        )
        self.session.add(
            ProductEvaluation(
                organization_id=payload.organization_id,
                product_candidate_id=candidate.id,
                **evaluation_values,
                evaluation_score=score,
                recommendation=recommendation,
                formula_version=PRODUCT_EVALUATION_FORMULA_VERSION,
            )
        )
        self.session.add_all(
            [
                ProductCandidateEvidence(
                    organization_id=payload.organization_id,
                    product_candidate_id=candidate.id,
                    **item.model_dump(),
                )
                for item in payload.evidence
            ]
        )
        return self._commit(candidate, actor_id, "product_evaluation.candidate.created")

    def evidence(self, candidate_id: UUID, organization_id: UUID) -> list[ProductCandidateEvidence]:
        self._candidate(candidate_id, organization_id)
        return list(
            self.session.scalars(
                select(ProductCandidateEvidence)
                .where(ProductCandidateEvidence.product_candidate_id == candidate_id)
                .order_by(ProductCandidateEvidence.created_at)
            )
        )

    def evaluation(self, candidate_id: UUID, organization_id: UUID) -> ProductEvaluation:
        self._candidate(candidate_id, organization_id)
        entity = self.session.scalar(
            select(ProductEvaluation).where(ProductEvaluation.product_candidate_id == candidate_id)
        )
        if entity is None:
            raise IntelligenceNotFoundError("Product evaluation was not found.")
        return entity

    def review(
        self,
        candidate: ProductCandidate,
        action: str,
        approval_request_id: UUID | None,
        actor_id: UUID,
    ) -> ProductCandidate:
        if candidate.status not in {"draft", "under_review"}:
            raise IntelligenceValidationError("Only pending product candidates may be reviewed.")
        if action == "accept":
            approvals = Base.metadata.tables["approval_requests"]
            approved = (
                self.session.scalar(
                    select(approvals.c.id).where(
                        approvals.c.id == approval_request_id,
                        approvals.c.organization_id == candidate.organization_id,
                        approvals.c.status == "approved",
                    )
                )
                if approval_request_id is not None
                else None
            )
            if approved is None:
                raise IntelligenceValidationError(
                    "Acceptance requires an approved governance request in this organization."
                )
            candidate.status = CandidateStatus.ACCEPTED
        else:
            candidate.status = CandidateStatus.REJECTED
        return self._commit(candidate, actor_id, f"product_evaluation.candidate.{candidate.status}")

    def dashboard(self, organization_id: UUID) -> ProductEvaluationDashboard:
        candidates = list(
            self.session.scalars(
                select(ProductCandidate)
                .where(
                    ProductCandidate.organization_id == organization_id,
                    ProductCandidate.opportunity_candidate_id.is_not(None),
                )
                .order_by(ProductCandidate.created_at.desc())
            )
        )
        evaluations = list(
            self.session.scalars(
                select(ProductEvaluation)
                .where(ProductEvaluation.organization_id == organization_id)
                .order_by(ProductEvaluation.created_at.desc())
            )
        )
        return ProductEvaluationDashboard(
            candidate_products=[ProductCandidateRead.model_validate(item) for item in candidates],
            economics_view=[ProductEvaluationRead.model_validate(item) for item in evaluations],
            validation_queue=[
                ProductCandidateRead.model_validate(item)
                for item in candidates
                if item.status in {"draft", "under_review"}
            ],
        )

    def _candidate(self, candidate_id: UUID, organization_id: UUID) -> ProductCandidate:
        candidate = self.session.get(ProductCandidate, candidate_id)
        if candidate is None or candidate.organization_id != organization_id:
            raise IntelligenceScopeError("Product candidate was not found in this organization.")
        return candidate

    def _validate_evidence(self, payload: ProductOpportunityCandidateCreate) -> None:
        table_map = {
            "demand_signal": "demand_signals",
            "opportunity_evidence": "opportunity_candidate_evidence",
            "marketplace_evidence": "marketplace_review_evidence",
            "customer_conversation": "conversation_messages",
            "research_analysis": "research_analyses",
        }
        for item in payload.evidence:
            try:
                reference_id = UUID(item.source_reference)
            except ValueError as error:
                raise IntelligenceValidationError(
                    "Product evidence source_reference must be an entity UUID."
                ) from error
            if not reference_belongs_to_organization(
                self.session,
                table_name=table_map[item.evidence_source],
                reference_id=reference_id,
                organization_id=payload.organization_id,
            ):
                raise IntelligenceScopeError(
                    "Product evaluation evidence was not found in this organization."
                )
            if item.evidence_source == "opportunity_evidence":
                evidence_table = Base.metadata.tables["opportunity_candidate_evidence"]
                if (
                    self.session.scalar(
                        select(evidence_table.c.id).where(
                            evidence_table.c.id == reference_id,
                            evidence_table.c.opportunity_candidate_id
                            == payload.opportunity_candidate_id,
                        )
                    )
                    is None
                ):
                    raise IntelligenceScopeError(
                        "Opportunity evidence does not belong to this opportunity candidate."
                    )

    def _commit(self, candidate: ProductCandidate, actor_id: UUID, action: str) -> ProductCandidate:
        self.session.add(candidate)
        self.session.flush()
        record_audit_event(
            self.session,
            organization_id=candidate.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=candidate.__tablename__,
            entity_id=candidate.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(candidate)
        return candidate


class OpportunityScoringService:
    """Apply frozen V1 weights; competition and legal/dispute risks are penalties."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def calculate(payload: OpportunityScoreCreate) -> float:
        overall = (
            payload.demand_score * 0.25
            + payload.pain_score * 0.15
            + payload.trend_score * 0.15
            + payload.margin_score * 0.20
            + (100 - payload.competition_score) * 0.10
            + (100 - payload.ip_risk_score) * 0.075
            + (100 - payload.dispute_risk_score) * 0.075
        )
        return round(overall, 2)

    def score(self, payload: OpportunityScoreCreate) -> OpportunityScore:
        _get_scoped_opportunity(self.session, payload.opportunity_id, payload.organization_id)
        score = self.session.scalar(
            select(OpportunityScore).where(
                OpportunityScore.opportunity_id == payload.opportunity_id
            )
        )
        values = payload.model_dump()
        values["overall_score"] = self.calculate(payload)
        values["formula_version"] = SCORING_FORMULA_VERSION
        if score is None:
            score = OpportunityScore(**values)
            self.session.add(score)
        else:
            for field, value in values.items():
                setattr(score, field, value)
        self.session.commit()
        self.session.refresh(score)
        return score


class OpportunityRiskService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: OpportunityRiskCreate) -> OpportunityRisk:
        _get_scoped_opportunity(self.session, payload.opportunity_id, payload.organization_id)
        risk = OpportunityRisk(**payload.model_dump())
        self.session.add(risk)
        self.session.commit()
        self.session.refresh(risk)
        return risk
