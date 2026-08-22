from typing import Any, TypeVar, cast
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.intelligence.demand_bridge_models import (
    DemandSignal,
    DemandSignalEvidence,
    DemandSignalSource,
)
from commerce_os.intelligence.demand_bridge_schemas import (
    BusinessDemandSignalCreate,
    CustomerPainClusterOverview,
    DemandAggregationCreate,
    DemandDashboardItem,
    DemandDashboardRead,
    DemandSignalSourceCreate,
    DemandSourceVolume,
    EmergingDemandCategory,
)
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.voice_models import CustomerPainCluster
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)
TRANSITIONS = {
    "draft": {"review", "rejected"},
    "review": {"approved", "rejected"},
    "approved": set(),
    "rejected": set(),
}


class DemandIntelligenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_source(
        self, payload: DemandSignalSourceCreate, actor_id: UUID
    ) -> DemandSignalSource:
        existing = self.session.scalar(
            select(DemandSignalSource).where(
                DemandSignalSource.organization_id == payload.organization_id,
                DemandSignalSource.source_type == payload.source_type,
            )
        )
        if existing is not None:
            raise IntelligenceScopeError(
                "This demand source type is already registered for the organization."
            )
        source = DemandSignalSource(**payload.model_dump(), status="active")
        return self._commit(source, actor_id, "intelligence.demand_source.created")

    def ingest(self, payload: BusinessDemandSignalCreate, actor_id: UUID) -> DemandSignal:
        source = self._registered_source(payload.organization_id, payload.source_type)
        entity = DemandSignal(
            organization_id=payload.organization_id,
            source_domain=source.source_domain,
            source_reference_id=uuid4(),
            source_type=source.source_type,
            source_reference=payload.source_reference,
            collection_method=source.collection_method,
            evidence_origin=source.evidence_origin,
            confidence_basis=payload.confidence_basis,
            customer_segment=payload.customer_segment,
            category=payload.category,
            problem_statement=payload.problem_statement,
            customer_language=payload.customer_language,
            frequency=len(payload.evidence),
            confidence=payload.confidence,
            evidence_count=len(payload.evidence),
            status="draft",
        )
        self.session.add(entity)
        self.session.flush()
        self.session.add_all(
            [
                DemandSignalEvidence(
                    organization_id=payload.organization_id,
                    demand_signal_id=entity.id,
                    source_type=source.source_type,
                    source_id=item.source_id,
                    source_reference=item.source_reference,
                    evidence_text=item.evidence_text,
                )
                for item in payload.evidence
            ]
        )
        return self._commit(entity, actor_id, "intelligence.business_demand.ingested")

    def aggregate(self, payload: DemandAggregationCreate, actor_id: UUID) -> DemandSignal:
        signal_table = Base.metadata.tables["growth_sales_learning_signals"]
        analysis_table = Base.metadata.tables["sales_conversation_analyses"]
        rows = list(
            self.session.execute(
                select(
                    signal_table.c.id,
                    signal_table.c.analysis_id,
                    signal_table.c.insight,
                    signal_table.c.confidence,
                    analysis_table.c.customer_reply,
                    analysis_table.c.status.label("analysis_status"),
                )
                .join(analysis_table, analysis_table.c.id == signal_table.c.analysis_id)
                .where(
                    signal_table.c.organization_id == payload.organization_id,
                    analysis_table.c.organization_id == payload.organization_id,
                    signal_table.c.id.in_(payload.learning_signal_ids),
                )
            ).mappings()
        )
        if len(rows) != len(set(payload.learning_signal_ids)):
            raise IntelligenceScopeError(
                "Every selected learning signal must exist in this organization."
            )
        if any(row["analysis_status"] != "accepted" for row in rows):
            raise IntelligenceScopeError(
                "Demand aggregation requires human-accepted conversation analyses."
            )
        rows.sort(key=lambda row: str(row["id"]))
        evidence_text = [str(row["customer_reply"]).strip() for row in rows]
        if any(not item for item in evidence_text):
            raise IntelligenceScopeError("Demand signals require original customer evidence.")
        ordered_insights = list(dict.fromkeys(str(row["insight"]).strip() for row in rows))
        if (
            self.session.scalar(
                select(DemandSignalSource).where(
                    DemandSignalSource.organization_id == payload.organization_id,
                    DemandSignalSource.source_type == "growthos_conversation",
                )
            )
            is None
        ):
            self.session.add(
                DemandSignalSource(
                    organization_id=payload.organization_id,
                    source_type="growthos_conversation",
                    display_name="GrowthOS Customer Conversations",
                    source_domain="growth",
                    collection_method="deterministic_aggregation",
                    evidence_origin="human_accepted_customer_conversation",
                    status="active",
                )
            )
            self.session.flush()
        entity = DemandSignal(
            organization_id=payload.organization_id,
            source_domain="growth",
            source_reference_id=rows[0]["id"],
            source_type="growthos_conversation",
            source_reference=str(rows[0]["id"]),
            collection_method="deterministic_aggregation",
            evidence_origin="human_accepted_customer_conversation",
            confidence_basis="Arithmetic mean of accepted GrowthOS learning signal confidence.",
            customer_segment=payload.customer_segment,
            category=payload.category,
            problem_statement=" | ".join(ordered_insights),
            customer_language=" | ".join(dict.fromkeys(evidence_text)),
            frequency=len(rows),
            confidence=round(sum(float(row["confidence"]) for row in rows) / len(rows), 4),
            evidence_count=len(rows),
            status="draft",
        )
        self.session.add(entity)
        self.session.flush()
        self.session.add_all(
            [
                DemandSignalEvidence(
                    organization_id=payload.organization_id,
                    demand_signal_id=entity.id,
                    source_type="growth_sales_learning_signal",
                    source_id=row["id"],
                    source_reference=str(row["id"]),
                    evidence_text=row["customer_reply"],
                )
                for row in rows
            ]
        )
        return self._commit(entity, actor_id, "intelligence.demand_signal.aggregated")

    def transition(
        self,
        entity: DemandSignal,
        status: str,
        approval_request_id: UUID | None,
        actor_id: UUID,
    ) -> DemandSignal:
        if status not in TRANSITIONS[entity.status]:
            raise IntelligenceScopeError(
                f"Demand signal cannot transition from {entity.status} to {status}."
            )
        if status == "approved":
            self._approval(entity, approval_request_id)
        entity.status = status
        return self._commit(entity, actor_id, f"intelligence.demand_signal.{status}")

    def dashboard(self, organization_id: UUID) -> DemandDashboardRead:
        def count(status: str) -> int:
            return int(
                self.session.scalar(
                    select(func.count()).where(
                        DemandSignal.organization_id == organization_id,
                        DemandSignal.status == status,
                    )
                )
                or 0
            )

        signals = list(
            self.session.scalars(
                select(DemandSignal)
                .where(
                    DemandSignal.organization_id == organization_id,
                    DemandSignal.status.in_(["review", "approved"]),
                )
                .order_by(
                    DemandSignal.frequency.desc(),
                    DemandSignal.confidence.desc(),
                )
                .limit(20)
            )
        )
        items = []
        analysis_table = Base.metadata.tables["sales_conversation_analyses"]
        learning_table = Base.metadata.tables["growth_sales_learning_signals"]
        for signal in signals:
            evidence_ids = list(
                self.session.scalars(
                    select(DemandSignalEvidence.source_id).where(
                        DemandSignalEvidence.demand_signal_id == signal.id
                    )
                )
            )
            conversation_ids = list(
                self.session.scalars(
                    select(analysis_table.c.id)
                    .join(learning_table, learning_table.c.analysis_id == analysis_table.c.id)
                    .where(learning_table.c.id.in_(evidence_ids))
                )
            )
            items.append(
                DemandDashboardItem(
                    demand_signal_id=signal.id,
                    category=signal.category,
                    customer_segment=signal.customer_segment,
                    problem_statement=signal.problem_statement,
                    frequency=signal.frequency,
                    confidence=signal.confidence,
                    evidence_count=signal.evidence_count,
                    source_type=signal.source_type,
                    evidence_sources=[
                        row.source_reference
                        for row in self.session.scalars(
                            select(DemandSignalEvidence).where(
                                DemandSignalEvidence.demand_signal_id == signal.id
                            )
                        )
                    ],
                    source_conversation_ids=conversation_ids,
                )
            )
        source_rows = self.session.execute(
            select(
                DemandSignal.source_type,
                func.count(DemandSignal.id),
                func.sum(DemandSignal.evidence_count),
                func.avg(DemandSignal.confidence),
            )
            .where(DemandSignal.organization_id == organization_id)
            .group_by(DemandSignal.source_type)
            .order_by(func.count(DemandSignal.id).desc(), DemandSignal.source_type)
        ).all()
        category_rows = self.session.execute(
            select(
                DemandSignal.category,
                func.count(DemandSignal.id),
                func.sum(DemandSignal.frequency),
                func.avg(DemandSignal.confidence),
            )
            .where(DemandSignal.organization_id == organization_id)
            .group_by(DemandSignal.category)
            .order_by(func.sum(DemandSignal.frequency).desc(), DemandSignal.category)
        ).all()
        return DemandDashboardRead(
            organization_id=organization_id,
            draft_signals=count("draft"),
            signals_in_review=count("review"),
            approved_signals=count("approved"),
            source_overview=[
                DemandSourceVolume(
                    source_type=row[0],
                    signal_count=int(row[1]),
                    evidence_count=int(row[2]),
                    average_confidence=round(float(row[3]), 4),
                )
                for row in source_rows
            ],
            emerging_categories=[
                EmergingDemandCategory(
                    category=row[0],
                    signal_count=int(row[1]),
                    total_frequency=int(row[2]),
                    average_confidence=round(float(row[3]), 4),
                )
                for row in category_rows
            ],
            customer_pain_clusters=[
                CustomerPainClusterOverview(
                    cluster_id=cluster.id,
                    name=cluster.name,
                    category=cluster.category,
                    severity_score=cluster.severity_score,
                    confidence_score=cluster.confidence_score,
                    status=cluster.status,
                )
                for cluster in self.session.scalars(
                    select(CustomerPainCluster)
                    .where(CustomerPainCluster.organization_id == organization_id)
                    .order_by(
                        CustomerPainCluster.severity_score.desc(),
                        CustomerPainCluster.confidence_score.desc(),
                    )
                    .limit(20)
                )
            ],
            emerging_customer_pains=items,
        )

    def _registered_source(self, organization_id: UUID, source_type: str) -> DemandSignalSource:
        source = self.session.scalar(
            select(DemandSignalSource).where(
                DemandSignalSource.organization_id == organization_id,
                DemandSignalSource.source_type == source_type,
                DemandSignalSource.status == "active",
            )
        )
        if source is None:
            raise IntelligenceScopeError(
                "Demand source must be registered and active for this organization."
            )
        return source

    def scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or cast(Any, entity).organization_id != organization_id:
            raise IntelligenceScopeError(
                "Demand intelligence record was not found in this organization."
            )
        return entity

    def _approval(self, entity: DemandSignal, approval_request_id: UUID | None) -> None:
        if approval_request_id is None:
            raise IntelligenceScopeError("Demand signal approval requires Governance approval.")
        table = Base.metadata.tables["approval_requests"]
        row = self.session.execute(
            table.select().where(
                table.c.id == approval_request_id,
                table.c.organization_id == entity.organization_id,
                table.c.object_type == "demand_signal",
                table.c.object_id == entity.id,
                table.c.requested_action == "approve_demand_signal",
                table.c.status == "approved",
            )
        ).first()
        if row is None:
            raise IntelligenceScopeError(
                "Governance approval does not authorize this demand signal."
            )

    def _commit(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
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
            metadata={
                "result": "success",
                "authority": "evidence_only",
                "opportunity_created": False,
                "product_created": False,
            },
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
