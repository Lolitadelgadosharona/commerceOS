from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.errors import (
    IntelligenceNotFoundError,
    IntelligenceScopeError,
    IntelligenceValidationError,
)
from commerce_os.intelligence.opportunity_models import (
    MarketOpportunity,
    OpportunityEvidence,
    OpportunityRisk,
    OpportunityScore,
    ProductCandidate,
)
from commerce_os.intelligence.opportunity_schemas import (
    OpportunityEvidenceCreate,
    OpportunityRiskCreate,
    OpportunityScoreCreate,
    ProductCandidateCreate,
)
from commerce_os.shared.scope import reference_belongs_to_organization

SCORING_FORMULA_VERSION = "v1.0"


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
