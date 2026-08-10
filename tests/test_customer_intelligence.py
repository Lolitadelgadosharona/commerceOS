from uuid import uuid4

import pytest
from commerce_os.governance.models import Organization
from commerce_os.intelligence.errors import IntelligenceScopeError
from commerce_os.intelligence.models import (
    CustomerInsight,
    CustomerSignal,
    CustomerVoiceCluster,
    InsightEvidence,
    SignalClusterMembership,
    SignalSource,
)
from commerce_os.intelligence.schemas import (
    CustomerInsightCreate,
    CustomerSignalCreate,
    CustomerVoiceClusterCreate,
)
from commerce_os.intelligence.services import ClusterService, InsightService, SignalService
from commerce_os.operations.models import Customer
from sqlalchemy import select
from sqlalchemy.orm import Session


def intelligence_context(session: Session):  # type: ignore[no-untyped-def]
    organization = Organization(name="Intelligence Org", slug="intelligence-org")
    session.add(organization)
    session.flush()
    customer = Customer(organization_id=organization.id, display_name="Customer")
    source = SignalSource(
        organization_id=organization.id,
        source_type="support",
        name="Support inbox",
        description="Manual foundation source",
    )
    session.add_all([customer, source])
    session.commit()
    return organization, customer, source


def signal_payload(organization, customer, source, reference: str, severity: str):  # type: ignore[no-untyped-def]
    return CustomerSignalCreate(
        organization_id=organization.id,
        signal_source_id=source.id,
        source_type="support",
        source_reference=reference,
        customer_id=customer.id,
        signal_type="delivery_delay",
        content_reference=f"object://signals/{reference}",
        sentiment="negative",
        severity=severity,
        confidence=0.9,
    )


def test_intelligence_entities_are_registered() -> None:
    assert CustomerSignal.__tablename__ == "customer_signals"
    assert SignalSource.__tablename__ == "signal_sources"
    assert CustomerVoiceCluster.__tablename__ == "customer_voice_clusters"
    assert CustomerInsight.__tablename__ == "customer_insights"


def test_services_create_signals_clusters_and_evidence_backed_insights(
    db_session: Session,
) -> None:
    organization, customer, source = intelligence_context(db_session)
    signal_service = SignalService(db_session)
    low = signal_service.create(
        signal_payload(organization, customer, source, "ticket-1", "medium")
    )
    high = signal_service.create(signal_payload(organization, customer, source, "ticket-2", "high"))
    cluster = ClusterService(db_session).create(
        CustomerVoiceClusterCreate(
            organization_id=organization.id,
            name="Shipping complaints increasing",
            description="Explicitly grouped delivery-delay evidence.",
            signal_ids=[low.id, high.id, high.id],
            trend_direction="increasing",
        )
    )
    assert cluster.signal_count == 2
    assert cluster.severity == "high"
    assert (
        len(
            list(
                db_session.scalars(
                    select(SignalClusterMembership).where(
                        SignalClusterMembership.cluster_id == cluster.id
                    )
                )
            )
        )
        == 2
    )

    insight = InsightService(db_session).create(
        CustomerInsightCreate(
            organization_id=organization.id,
            cluster_id=cluster.id,
            signal_ids=[low.id, high.id],
            title="Delivery reliability needs investigation",
            summary="Two explicitly selected support signals report delivery delays.",
            impact_level="high",
            recommended_action="Review carrier performance with Operations.",
        )
    )
    assert insight.evidence_count == 2
    assert insight.status == "new"
    assert (
        len(
            list(
                db_session.scalars(
                    select(InsightEvidence).where(InsightEvidence.insight_id == insight.id)
                )
            )
        )
        == 2
    )


def test_signal_service_rejects_cross_organization_customer(db_session: Session) -> None:
    organization, _customer, source = intelligence_context(db_session)
    other = Organization(name="Other Org", slug="other-org")
    db_session.add(other)
    db_session.flush()
    other_customer = Customer(organization_id=other.id, display_name="Other")
    db_session.add(other_customer)
    db_session.commit()
    with pytest.raises(IntelligenceScopeError):
        SignalService(db_session).create(
            CustomerSignalCreate(
                organization_id=organization.id,
                signal_source_id=source.id,
                source_type="support",
                source_reference=str(uuid4()),
                customer_id=other_customer.id,
                signal_type="trust_concern",
                content_reference="object://signals/cross-scope",
                sentiment="negative",
                severity="critical",
                confidence=0.95,
            )
        )
