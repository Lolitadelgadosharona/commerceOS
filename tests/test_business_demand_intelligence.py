from uuid import uuid4

import pytest
from commerce_os.build.models import Product
from commerce_os.intelligence.demand_bridge_models import (
    DemandSignal,
    DemandSignalEvidence,
    DemandSignalSource,
)
from commerce_os.intelligence.demand_bridge_schemas import (
    BusinessDemandEvidenceInput,
    BusinessDemandSignalCreate,
    DemandSignalSourceCreate,
)
from commerce_os.intelligence.demand_bridge_services import DemandIntelligenceService
from commerce_os.intelligence.errors import IntelligenceScopeError
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.test_demand_intelligence_bridge import aggregate


def register_source(
    session: Session,
    organization_id,  # type: ignore[no-untyped-def]
    actor_id,  # type: ignore[no-untyped-def]
    source_type: str,
) -> DemandSignalSource:
    return DemandIntelligenceService(session).create_source(
        DemandSignalSourceCreate(
            organization_id=organization_id,
            source_type=source_type,  # type: ignore[arg-type]
            display_name=source_type.replace("_", " ").title(),
            source_domain="intelligence",
            collection_method="controlled_import",
            evidence_origin="external_market_observation",
        ),
        actor_id,
    )


def external_payload(
    organization_id,
    source_type: str,
    reference: str,  # type: ignore[no-untyped-def]
) -> BusinessDemandSignalCreate:
    return BusinessDemandSignalCreate(
        organization_id=organization_id,
        source_type=source_type,  # type: ignore[arg-type]
        source_reference=reference,
        customer_segment="Independent studio",
        category="workflow_friction",
        problem_statement="Teams repeatedly report manual handoff friction.",
        customer_language="We keep losing context between tools.",
        confidence=0.74,
        confidence_basis="Two independently captured source observations agree.",
        evidence=[
            BusinessDemandEvidenceInput(
                source_id=uuid4(),
                source_reference=f"{reference}:1",
                evidence_text="Manual handoffs repeatedly lose important context.",
            ),
            BusinessDemandEvidenceInput(
                source_id=uuid4(),
                source_reference=f"{reference}:2",
                evidence_text="The team wants a consistent context handoff.",
            ),
        ],
    )


def test_growthos_and_external_sources_share_demand_foundation(db_session: Session) -> None:
    entities, _, _, growth_signal = aggregate(db_session, "unified-demand")
    organization, user, *_ = entities
    service = DemandIntelligenceService(db_session)
    register_source(db_session, organization.id, user.id, "reddit")
    register_source(db_session, organization.id, user.id, "research_analysis")
    reddit = service.ingest(
        external_payload(organization.id, "reddit", "reddit:r/operations:123"), user.id
    )
    research = service.ingest(
        external_payload(organization.id, "research_analysis", "research:run:456"),
        user.id,
    )
    assert growth_signal.source_type == "growthos_conversation"
    assert growth_signal.collection_method == "deterministic_aggregation"
    assert {reddit.source_domain, research.source_domain} == {"intelligence"}
    assert {reddit.source_type, research.source_type} == {"reddit", "research_analysis"}
    assert db_session.scalar(select(func.count()).select_from(DemandSignal)) == 3
    assert db_session.scalar(select(func.count()).select_from(DemandSignalSource)) == 3


def test_external_evidence_is_complete_traceable_and_tenant_scoped(db_session: Session) -> None:
    entities, _, _, _ = aggregate(db_session, "external-traceability")
    organization, user, *_ = entities
    service = DemandIntelligenceService(db_session)
    register_source(db_session, organization.id, user.id, "amazon_review")
    payload = external_payload(organization.id, "amazon_review", "amazon-review:example-product")
    signal = service.ingest(payload, user.id)
    evidence = list(
        db_session.scalars(
            select(DemandSignalEvidence).where(DemandSignalEvidence.demand_signal_id == signal.id)
        )
    )
    assert signal.source_reference == "amazon-review:example-product"
    assert signal.evidence_count == signal.frequency == len(evidence) == 2
    assert {row.source_reference for row in evidence} == {
        item.source_reference for item in payload.evidence
    }
    with pytest.raises(IntelligenceScopeError, match="registered and active"):
        service.ingest(
            external_payload(organization.id, "etsy_review", "etsy-review:missing"),
            user.id,
        )


def test_source_overview_and_categories_remain_evidence_only(db_session: Session) -> None:
    products_before = db_session.scalar(select(func.count()).select_from(Product))
    entities, _, _, growth = aggregate(db_session, "demand-overview")
    organization, user, *_ = entities
    service = DemandIntelligenceService(db_session)
    register_source(db_session, organization.id, user.id, "google_trend")
    external = service.ingest(
        external_payload(organization.id, "google_trend", "trend:workflow-context"),
        user.id,
    )
    service.transition(growth, "review", None, user.id)
    service.transition(external, "review", None, user.id)
    dashboard = service.dashboard(organization.id)
    volume = {row.source_type: row for row in dashboard.source_overview}
    assert volume["growthos_conversation"].signal_count == 1
    assert volume["google_trend"].evidence_count == 2
    assert {row.category for row in dashboard.emerging_categories} == {
        "pricing_clarity",
        "workflow_friction",
    }
    assert {row.source_type for row in dashboard.emerging_customer_pains} == {
        "growthos_conversation",
        "google_trend",
    }
    assert db_session.scalar(select(func.count()).select_from(Product)) == products_before


def test_source_and_evidence_validation(db_session: Session) -> None:
    entities, _, _, _ = aggregate(db_session, "demand-source-validation")
    organization, user, *_ = entities
    register_source(db_session, organization.id, user.id, "manual_input")
    with pytest.raises(IntelligenceScopeError, match="already registered"):
        register_source(db_session, organization.id, user.id, "manual_input")
    with pytest.raises(ValidationError):
        BusinessDemandSignalCreate(
            organization_id=organization.id,
            source_type="manual_input",
            source_reference="manual:empty",
            customer_segment="Founder",
            category="manual_observation",
            problem_statement="Observed demand.",
            customer_language="Need this.",
            confidence=0.5,
            confidence_basis="Founder supplied observation.",
            evidence=[],
        )
