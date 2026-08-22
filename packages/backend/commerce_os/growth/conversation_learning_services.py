from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from commerce_os.growth.activation_models import ProspectExperimentLink
from commerce_os.growth.conversation_learning_models import (
    GrowthMessagePerformanceObservation,
    GrowthObjectionRecord,
    GrowthSalesLearningSignal,
)
from commerce_os.growth.conversation_learning_schemas import (
    MessageMetric,
    MessagePerformanceCreate,
    ObjectionMetric,
    ObjectionRecordCreate,
    SalesKnowledgeDashboardRead,
    SalesLearningSignalCreate,
    SegmentMetric,
)
from commerce_os.growth.errors import GrowthError
from commerce_os.growth.revenue_models import (
    GrowthOutreachDraft,
    SalesConversationAnalysis,
)
from commerce_os.growth.revenue_services import scoped_revenue
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
ANALYSIS_TRANSITIONS = {
    "draft": {"reviewed", "rejected"},
    "reviewed": {"accepted", "rejected"},
    "accepted": set(),
    "rejected": set(),
}


class GrowthConversationLearningService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def transition_analysis(
        self, analysis: SalesConversationAnalysis, status: str, actor_id: UUID
    ) -> SalesConversationAnalysis:
        if status not in ANALYSIS_TRANSITIONS[analysis.status]:
            raise GrowthError(
                f"Conversation analysis cannot transition from {analysis.status} to {status}."
            )
        analysis.status = status
        return self._save(analysis, actor_id, f"growthos.conversation_analysis.{status}")

    def create_objection(
        self, payload: ObjectionRecordCreate, actor_id: UUID
    ) -> GrowthObjectionRecord:
        analysis = scoped_revenue(
            self.session,
            SalesConversationAnalysis,
            payload.analysis_id,
            payload.organization_id,
        )
        if analysis.status not in {"reviewed", "accepted"}:
            raise GrowthError("Objection intelligence requires a human-reviewed analysis.")
        if (
            analysis.objection_type is not None
            and analysis.objection_type != payload.objection_type
        ):
            raise GrowthError("Objection category must match the reviewed conversation analysis.")
        return self._save(
            GrowthObjectionRecord(
                organization_id=payload.organization_id,
                analysis_id=analysis.id,
                prospect_id=analysis.prospect_id,
                objection_type=payload.objection_type,
                customer_segment=payload.customer_segment,
                original_message=analysis.customer_reply,
                suggested_response=analysis.suggested_reply,
                outcome=payload.outcome,
            ),
            actor_id,
            "growthos.objection.created",
        )

    def create_learning_signal(
        self,
        payload: SalesLearningSignalCreate,
        learning_observation_id: UUID,
        actor_id: UUID,
    ) -> GrowthSalesLearningSignal:
        analysis = self.validate_learning_signal(payload)
        observation_table = Base.metadata.tables["learning_observations"]
        observation = self.session.execute(
            observation_table.select().where(
                observation_table.c.id == learning_observation_id,
                observation_table.c.organization_id == payload.organization_id,
                observation_table.c.source_record_id == analysis.id,
                observation_table.c.source_type == "growth_conversation_analysis",
            )
        ).first()
        if observation is None:
            raise GrowthError("Learning signal requires its matching Learning observation.")
        return self._save(
            GrowthSalesLearningSignal(
                **payload.model_dump(), learning_observation_id=learning_observation_id
            ),
            actor_id,
            "growthos.sales_learning_signal.created",
        )

    def validate_learning_signal(
        self, payload: SalesLearningSignalCreate
    ) -> SalesConversationAnalysis:
        analysis = scoped_revenue(
            self.session,
            SalesConversationAnalysis,
            payload.analysis_id,
            payload.organization_id,
        )
        if analysis.status != "accepted":
            raise GrowthError("Learning signals require a human-accepted conversation analysis.")
        if payload.objection_record_id is not None:
            objection = self._scoped(
                GrowthObjectionRecord,
                payload.objection_record_id,
                payload.organization_id,
            )
            if objection.analysis_id != analysis.id:
                raise GrowthError("Learning objection must belong to the selected analysis.")
        return analysis

    def create_message_performance(
        self, payload: MessagePerformanceCreate, actor_id: UUID
    ) -> GrowthMessagePerformanceObservation:
        draft = scoped_revenue(
            self.session,
            GrowthOutreachDraft,
            payload.outreach_draft_id,
            payload.organization_id,
        )
        if draft.status != "sent":
            raise GrowthError("Message performance requires a human-approved sent record.")
        if payload.prospect_experiment_link_id is not None:
            link = self._scoped(
                ProspectExperimentLink,
                payload.prospect_experiment_link_id,
                payload.organization_id,
            )
            if link.prospect_id != draft.prospect_id:
                raise GrowthError("Performance assignment must belong to the outreach prospect.")
        values = payload.model_dump(exclude={"metadata"})
        return self._save(
            GrowthMessagePerformanceObservation(**values, observation_metadata=payload.metadata),
            actor_id,
            "growthos.message_performance.appended",
        )

    def dashboard(self, organization_id: UUID) -> SalesKnowledgeDashboardRead:
        total = self._count(SalesConversationAnalysis, organization_id)
        positive = self._count(
            SalesConversationAnalysis,
            organization_id,
            SalesConversationAnalysis.buying_signal.in_(["positive", "strong"]),
        )
        sent = self._count(
            GrowthMessagePerformanceObservation,
            organization_id,
            GrowthMessagePerformanceObservation.outcome == "sent",
        )
        replies = self._count(
            GrowthMessagePerformanceObservation,
            organization_id,
            GrowthMessagePerformanceObservation.outcome.in_(
                ["replied", "positive", "negative", "converted", "lost"]
            ),
        )
        objection_rows = self.session.execute(
            select(GrowthObjectionRecord.objection_type, func.count().label("count"))
            .where(GrowthObjectionRecord.organization_id == organization_id)
            .group_by(GrowthObjectionRecord.objection_type)
            .order_by(func.count().desc())
        )
        lost_rows = self.session.execute(
            select(GrowthObjectionRecord.objection_type, func.count().label("count"))
            .where(
                GrowthObjectionRecord.organization_id == organization_id,
                GrowthObjectionRecord.outcome == "lost",
            )
            .group_by(GrowthObjectionRecord.objection_type)
            .order_by(func.count().desc())
        )
        positive_case = case(
            (GrowthMessagePerformanceObservation.outcome.in_(["positive", "converted"]), 1),
            else_=0,
        )
        message_rows = self.session.execute(
            select(
                GrowthMessagePerformanceObservation.message_strategy,
                func.count().label("observations"),
                func.sum(positive_case).label("positive"),
            )
            .where(GrowthMessagePerformanceObservation.organization_id == organization_id)
            .group_by(GrowthMessagePerformanceObservation.message_strategy)
            .order_by(func.sum(positive_case).desc(), func.count().desc())
        )
        reply_case = case(
            (
                GrowthMessagePerformanceObservation.outcome.in_(
                    ["replied", "positive", "negative", "converted", "lost"]
                ),
                1,
            ),
            else_=0,
        )
        segment_rows = self.session.execute(
            select(
                GrowthMessagePerformanceObservation.customer_segment,
                func.count().label("observations"),
                func.sum(reply_case).label("replies"),
                func.sum(positive_case).label("positive"),
            )
            .where(GrowthMessagePerformanceObservation.organization_id == organization_id)
            .group_by(GrowthMessagePerformanceObservation.customer_segment)
            .order_by(func.sum(positive_case).desc(), func.count().desc())
        )
        return SalesKnowledgeDashboardRead(
            organization_id=organization_id,
            total_conversations=total,
            reply_rate=round(replies / sent, 4) if sent else None,
            positive_signals=positive,
            most_common_objections=[
                ObjectionMetric(objection_type=row.objection_type, count=row.count)
                for row in objection_rows
            ],
            best_performing_messages=[
                MessageMetric(
                    message_strategy=row.message_strategy,
                    observations=row.observations,
                    positive_or_converted=row.positive,
                )
                for row in message_rows
            ],
            lost_reasons=[
                ObjectionMetric(objection_type=row.objection_type, count=row.count)
                for row in lost_rows
            ],
            segment_performance=[
                SegmentMetric(
                    customer_segment=row.customer_segment,
                    observations=row.observations,
                    replies=row.replies,
                    positive_or_converted=row.positive,
                )
                for row in segment_rows
            ],
        )

    def _scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or cast(Any, entity).organization_id != organization_id:
            raise GrowthError("GrowthOS learning record was not found in this organization.")
        return entity

    def _count(self, model: Any, organization_id: UUID, *criteria: Any) -> int:
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.organization_id == organization_id, *criteria)
            )
            or 0
        )

    def _save(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=cast(UUID, item.id),
            metadata={"result": "success", "external_execution": "none"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
