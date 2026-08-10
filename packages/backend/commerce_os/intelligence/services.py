from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.errors import (
    IntelligenceNotFoundError,
    IntelligenceScopeError,
    IntelligenceValidationError,
)
from commerce_os.intelligence.models import (
    CustomerInsight,
    CustomerSignal,
    CustomerVoiceCluster,
    InsightEvidence,
    InsightStatus,
    Severity,
    SignalClusterMembership,
    SignalSource,
)
from commerce_os.intelligence.schemas import (
    CustomerInsightCreate,
    CustomerSignalCreate,
    CustomerVoiceClusterCreate,
)
from commerce_os.shared.scope import reference_belongs_to_organization

SEVERITY_RANK = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def _unique_ids(values: list[UUID]) -> list[UUID]:
    return list(dict.fromkeys(values))


class SignalService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: CustomerSignalCreate) -> CustomerSignal:
        source = self.session.get(SignalSource, payload.signal_source_id)
        if source is None:
            raise IntelligenceNotFoundError("Signal source was not found.")
        if source.organization_id != payload.organization_id:
            raise IntelligenceScopeError("Signal source belongs to another organization.")
        if not source.is_active:
            raise IntelligenceValidationError("Inactive signal sources cannot accept signals.")
        if str(source.source_type) != payload.source_type:
            raise IntelligenceValidationError(
                "Signal source type does not match its source record."
            )
        if payload.customer_id is not None and not reference_belongs_to_organization(
            self.session,
            table_name="customers",
            reference_id=payload.customer_id,
            organization_id=payload.organization_id,
        ):
            raise IntelligenceScopeError("Customer was not found in this organization.")
        signal = CustomerSignal(**payload.model_dump())
        self.session.add(signal)
        self.session.commit()
        self.session.refresh(signal)
        return signal


class ClusterService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: CustomerVoiceClusterCreate) -> CustomerVoiceCluster:
        signal_ids = _unique_ids(payload.signal_ids)
        signals = list(
            self.session.scalars(select(CustomerSignal).where(CustomerSignal.id.in_(signal_ids)))
        )
        if len(signals) != len(signal_ids):
            raise IntelligenceNotFoundError("One or more customer signals were not found.")
        if any(signal.organization_id != payload.organization_id for signal in signals):
            raise IntelligenceScopeError("Cluster membership cannot cross organizations.")
        derived_severity = max(
            (Severity(str(signal.severity)) for signal in signals),
            key=SEVERITY_RANK.__getitem__,
        )
        severity = Severity(payload.severity) if payload.severity else derived_severity
        cluster = CustomerVoiceCluster(
            organization_id=payload.organization_id,
            name=payload.name,
            description=payload.description,
            signal_count=len(signals),
            severity=severity,
            trend_direction=payload.trend_direction,
        )
        self.session.add(cluster)
        self.session.flush()
        self.session.add_all(
            SignalClusterMembership(cluster_id=cluster.id, signal_id=signal.id)
            for signal in signals
        )
        self.session.commit()
        self.session.refresh(cluster)
        return cluster


class InsightService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: CustomerInsightCreate) -> CustomerInsight:
        signal_ids = _unique_ids(payload.signal_ids)
        signals = list(
            self.session.scalars(select(CustomerSignal).where(CustomerSignal.id.in_(signal_ids)))
        )
        if len(signals) != len(signal_ids):
            raise IntelligenceNotFoundError("One or more insight signals were not found.")
        if any(signal.organization_id != payload.organization_id for signal in signals):
            raise IntelligenceScopeError("Insight evidence cannot cross organizations.")
        if payload.cluster_id is not None:
            cluster = self.session.get(CustomerVoiceCluster, payload.cluster_id)
            if cluster is None:
                raise IntelligenceNotFoundError("Customer voice cluster was not found.")
            if cluster.organization_id != payload.organization_id:
                raise IntelligenceScopeError("Insight cluster belongs to another organization.")
        insight = CustomerInsight(
            organization_id=payload.organization_id,
            cluster_id=payload.cluster_id,
            title=payload.title,
            summary=payload.summary,
            evidence_count=len(signals),
            impact_level=payload.impact_level,
            recommended_action=payload.recommended_action,
            status=InsightStatus(payload.status),
        )
        self.session.add(insight)
        self.session.flush()
        self.session.add_all(
            InsightEvidence(insight_id=insight.id, signal_id=signal.id) for signal in signals
        )
        self.session.commit()
        self.session.refresh(insight)
        return insight

    def update_status(self, insight_id: UUID, status: InsightStatus) -> CustomerInsight:
        insight = self.session.get(CustomerInsight, insight_id)
        if insight is None:
            raise IntelligenceNotFoundError("Customer insight was not found.")
        insight.status = status
        self.session.commit()
        self.session.refresh(insight)
        return insight
