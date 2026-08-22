from datetime import UTC, datetime
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.learning.models import (
    ImprovementRecommendation,
    LearningConclusion,
    LearningObservation,
    RecommendationPriorityAssessment,
    RootCauseEvidenceLink,
    RootCauseHypothesis,
)
from commerce_os.learning.schemas import (
    ConclusionCreate,
    ConclusionTransition,
    FeedbackLoopRead,
    HypothesisCreate,
    LearningDashboardRead,
    LearningObservationCreate,
    PriorityCreate,
    RecommendationCreate,
)
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
SOURCE_MAP = {
    "customer_signal": ("intelligence", "customer_signals"),
    "conversation_signal": ("operations", "conversation_intents"),
    "support_signal": ("operations", "support_case_intelligence"),
    "growth_performance": ("growth", "growth_performance_observations"),
    "creative_performance": ("build", "creative_performance_observations"),
    "channel_performance": ("growth", "channel_performance_observations"),
    "revenue_observation": ("finance", "revenue_observations"),
    "cost_observation": ("finance", "cost_observations"),
    "contribution_profit": ("finance", "contribution_profit_assessments"),
    "refund_signal": ("decision", "customer_risk_signals"),
    "dispute_signal": ("decision", "customer_risk_signals"),
    "product_risk": ("intelligence", "product_risk_signals"),
    "market_signal": ("intelligence", "market_signals"),
    "growth_conversation_analysis": ("growth", "sales_conversation_analyses"),
}
TRANSITIONS = {
    "draft": {"under_review", "rejected"},
    "under_review": {"supported", "rejected"},
    "supported": set(),
    "rejected": set(),
}
WEIGHTS = {
    "expected_commercial_impact": 0.15,
    "evidence_confidence": 0.15,
    "customer_frequency": 0.10,
    "customer_severity": 0.10,
    "financial_impact": 0.15,
    "refund_risk": 0.075,
    "dispute_risk": 0.075,
    "implementation_effort": 0.05,
    "reversibility": 0.075,
    "testability": 0.075,
}


class LearningError(ValueError):
    pass


class ClosedLoopLearningService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_observation(
        self, payload: LearningObservationCreate, actor_id: UUID
    ) -> LearningObservation:
        domain, table_name = SOURCE_MAP[payload.source_type]
        self._row(table_name, payload.source_record_id, payload.organization_id)
        self._optional_ref("projects", payload.project_id, payload.organization_id)
        self._optional_ref("products", payload.product_id, payload.organization_id)
        values = payload.model_dump(exclude={"metadata", "source_type"})
        entity = LearningObservation(
            **values,
            source_domain=domain,
            source_type=payload.source_type,
            observation_metadata=payload.metadata,
        )
        return self._save(entity, actor_id, "learning.observation.appended")

    def create_hypothesis(self, payload: HypothesisCreate, actor_id: UUID) -> RootCauseHypothesis:
        self._guard_causal_claim(payload.hypothesis)
        self._optional_ref("projects", payload.project_id, payload.organization_id)
        self._optional_ref("products", payload.product_id, payload.organization_id)
        observations = [
            self.scoped(LearningObservation, link.observation_id, payload.organization_id)
            for link in payload.evidence_links
        ]
        entity = RootCauseHypothesis(
            **payload.model_dump(exclude={"evidence_links"}), status="draft"
        )
        self.session.add(entity)
        self.session.flush()
        self.session.add_all(
            [
                RootCauseEvidenceLink(
                    organization_id=payload.organization_id,
                    hypothesis_id=entity.id,
                    observation_id=observation.id,
                    evidence_role=link.evidence_role,
                )
                for link, observation in zip(payload.evidence_links, observations, strict=True)
            ]
        )
        return self._commit(entity, actor_id, "learning.hypothesis.created")

    def transition_hypothesis(
        self, entity: RootCauseHypothesis, status: str, actor_id: UUID
    ) -> RootCauseHypothesis:
        if status not in TRANSITIONS[entity.status]:
            raise LearningError(f"Hypothesis cannot transition from {entity.status} to {status}.")
        if status == "supported":
            supporting = (
                self.session.scalar(
                    select(func.count())
                    .select_from(RootCauseEvidenceLink)
                    .where(
                        RootCauseEvidenceLink.hypothesis_id == entity.id,
                        RootCauseEvidenceLink.evidence_role == "supporting",
                    )
                )
                or 0
            )
            if supporting < 2 or entity.evidence_coverage < 0.5 or entity.confidence < 0.5:
                raise LearningError(
                    "Supported hypotheses require two supporting observations and minimum "
                    "0.5 coverage/confidence."
                )
        entity.status = status
        return self._save(entity, actor_id, f"learning.hypothesis.{status}")

    def create_conclusion(self, payload: ConclusionCreate, actor_id: UUID) -> LearningConclusion:
        hypothesis = self.scoped(
            RootCauseHypothesis, payload.hypothesis_id, payload.organization_id
        )
        links = list(
            self.session.scalars(
                select(RootCauseEvidenceLink).where(
                    RootCauseEvidenceLink.hypothesis_id == hypothesis.id
                )
            )
        )
        supporting = [
            str(link.observation_id) for link in links if link.evidence_role == "supporting"
        ]
        contradicting = [
            str(link.observation_id) for link in links if link.evidence_role == "contradicting"
        ]
        return self._save(
            LearningConclusion(
                **payload.model_dump(),
                supporting_observation_ids=supporting,
                contradicting_observation_ids=contradicting,
                status="draft",
                reviewer_id=None,
                reviewed_at=None,
                review_metadata={},
            ),
            actor_id,
            "learning.conclusion.created",
        )

    def transition_conclusion(
        self, entity: LearningConclusion, payload: ConclusionTransition, actor_id: UUID
    ) -> LearningConclusion:
        hypothesis = self.scoped(RootCauseHypothesis, entity.hypothesis_id, entity.organization_id)
        if entity.status != "draft":
            raise LearningError("Conclusion review is terminal.")
        if payload.status == "supported" and (
            hypothesis.status != "supported"
            or len(entity.supporting_observation_ids) < 2
            or entity.evidence_coverage < 0.5
            or entity.confidence < 0.5
        ):
            raise LearningError(
                "Supported conclusions require a supported hypothesis and minimum evidence."
            )
        entity.status = payload.status
        entity.reviewer_id = actor_id
        entity.reviewed_at = datetime.now(UTC)
        entity.review_metadata = payload.review_metadata
        return self._save(entity, actor_id, f"learning.conclusion.{payload.status}")

    def create_recommendation(
        self, payload: RecommendationCreate, actor_id: UUID
    ) -> ImprovementRecommendation:
        conclusion = self.scoped(LearningConclusion, payload.conclusion_id, payload.organization_id)
        if conclusion.status != "supported":
            raise LearningError("Recommendations require a supported conclusion.")
        return self._save(
            ImprovementRecommendation(
                **payload.model_dump(), status="advisory", decision_queue_item_id=None
            ),
            actor_id,
            "learning.recommendation.created",
        )

    def assess_priority(
        self, payload: PriorityCreate, actor_id: UUID
    ) -> RecommendationPriorityAssessment:
        self.scoped(ImprovementRecommendation, payload.recommendation_id, payload.organization_id)
        supplied = payload.inputs.model_dump()
        present = {key: value for key, value in supplied.items() if value is not None}
        components = {
            key: (100 - value if key == "implementation_effort" else value) * WEIGHTS[key]
            for key, value in present.items()
        }
        weight = sum(WEIGHTS[key] for key in present)
        score = round(sum(components.values()) / weight, 2)
        return self._save(
            RecommendationPriorityAssessment(
                organization_id=payload.organization_id,
                recommendation_id=payload.recommendation_id,
                formula_version="risk-adjusted-learning-v1.0",
                supplied_inputs=supplied,
                missing_inputs=[key for key, value in supplied.items() if value is None],
                calculated_score=score,
                explanation_components={
                    "weighted_components": components,
                    "normalization_weight": weight,
                    "objective": "risk_adjusted_contribution_profit_and_customer_value",
                },
            ),
            actor_id,
            "learning.priority.assessed",
        )

    def review_queue_priority(
        self, recommendation: ImprovementRecommendation
    ) -> tuple[RecommendationPriorityAssessment, bool]:
        if recommendation.decision_queue_item_id is not None:
            raise LearningError("Recommendation is already queued.")
        assessment = self.session.scalar(
            select(RecommendationPriorityAssessment).where(
                RecommendationPriorityAssessment.recommendation_id == recommendation.id
            )
        )
        if assessment is None:
            raise LearningError("Priority assessment is required before queue placement.")
        inputs = assessment.supplied_inputs
        high_risk = (inputs.get("refund_risk") or 0) >= 80 or (
            inputs.get("dispute_risk") or 0
        ) >= 80
        if assessment.calculated_score < 75 and not high_risk:
            raise LearningError("Only high-priority or high-risk recommendations may be queued.")
        return assessment, high_risk

    def attach_decision_queue(
        self,
        recommendation: ImprovementRecommendation,
        decision_queue_item_id: UUID,
        actor_id: UUID,
    ) -> ImprovementRecommendation:
        recommendation.decision_queue_item_id = decision_queue_item_id
        return self._save(recommendation, actor_id, "learning.recommendation.queued")

    def feedback_loop(self, recommendation_id: UUID, organization_id: UUID) -> FeedbackLoopRead:
        recommendation = self.scoped(ImprovementRecommendation, recommendation_id, organization_id)
        conclusion = self.scoped(LearningConclusion, recommendation.conclusion_id, organization_id)
        hypothesis = self.scoped(RootCauseHypothesis, conclusion.hypothesis_id, organization_id)
        links = list(
            self.session.scalars(
                select(RootCauseEvidenceLink).where(
                    RootCauseEvidenceLink.hypothesis_id == hypothesis.id
                )
            )
        )
        observations = [
            self.scoped(LearningObservation, link.observation_id, organization_id) for link in links
        ]
        priority = self.session.scalar(
            select(RecommendationPriorityAssessment).where(
                RecommendationPriorityAssessment.recommendation_id == recommendation.id
            )
        )
        missing = []
        if priority is None:
            missing.append("priority")
        if recommendation.decision_queue_item_id is None:
            missing.append("human_decision")
        missing.append("future_execution")
        missing.append("new_evidence")
        return FeedbackLoopRead(
            observation=observations,
            hypothesis=hypothesis,
            conclusion=conclusion,
            recommendation=recommendation,
            priority=priority,
            decision_queue_item_id=recommendation.decision_queue_item_id,
            missing_stages=missing,
        )

    def dashboard(self, organization_id: UUID) -> LearningDashboardRead:
        def count(model: Any, *conditions: Any) -> int:
            return int(
                self.session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.organization_id == organization_id, *conditions)
                )
                or 0
            )

        priorities = list(
            self.session.execute(
                select(
                    RecommendationPriorityAssessment.calculated_score,
                    ImprovementRecommendation.id,
                    ImprovementRecommendation.target_type,
                )
                .join(
                    ImprovementRecommendation,
                    ImprovementRecommendation.id
                    == RecommendationPriorityAssessment.recommendation_id,
                )
                .where(RecommendationPriorityAssessment.organization_id == organization_id)
                .order_by(RecommendationPriorityAssessment.calculated_score.desc())
                .limit(5)
            ).mappings()
        )
        source_counts: dict[str, int] = {
            source_type: int(total)
            for source_type, total in self.session.execute(
                select(LearningObservation.source_type, func.count())
                .where(LearningObservation.organization_id == organization_id)
                .group_by(LearningObservation.source_type)
            )
        }
        return LearningDashboardRead(
            organization_id=organization_id,
            active_hypotheses=count(
                RootCauseHypothesis, RootCauseHypothesis.status.in_(["draft", "under_review"])
            ),
            supported_conclusions=count(
                LearningConclusion, LearningConclusion.status == "supported"
            ),
            highest_priority_improvements=[dict(row) for row in priorities],
            recurring_customer_problems=source_counts.get("customer_signal", 0)
            + source_counts.get("support_signal", 0),
            revenue_leakage_signals=source_counts.get("revenue_observation", 0)
            + source_counts.get("cost_observation", 0)
            + source_counts.get("contribution_profit", 0),
            refund_dispute_signals=source_counts.get("refund_signal", 0)
            + source_counts.get("dispute_signal", 0),
            creative_channel_signals=source_counts.get("creative_performance", 0)
            + source_counts.get("channel_performance", 0)
            + source_counts.get("growth_performance", 0),
            unresolved_evidence_gaps=count(
                RootCauseHypothesis, RootCauseHypothesis.evidence_coverage < 0.5
            ),
        )

    def scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or cast(Any, entity).organization_id != organization_id:
            raise LearningError("Learning record was not found in this organization.")
        return entity

    def _row(self, table_name: str, entity_id: UUID, organization_id: UUID) -> Any:
        table = Base.metadata.tables[table_name]
        row = (
            self.session.execute(
                table.select().where(
                    table.c.id == entity_id, table.c.organization_id == organization_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise LearningError("Source evidence was not found in this organization.")
        return row

    def _optional_ref(self, table_name: str, entity_id: UUID | None, organization_id: UUID) -> None:
        if entity_id is not None:
            self._row(table_name, entity_id, organization_id)

    @staticmethod
    def _guard_causal_claim(statement: str) -> None:
        lowered = statement.lower()
        if any(
            phrase in lowered
            for phrase in (" causes ", " proves ", " guarantees ", " is caused by ")
        ):
            raise LearningError(
                "Hypotheses must use correlation language and cannot claim causal certainty."
            )

    def _save(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        return self._commit(entity, actor_id, action)

    def _commit(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=item.id,
            metadata={"result": "success", "authority": "advisory_only"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
