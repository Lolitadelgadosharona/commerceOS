from uuid import uuid4

from commerce_os.decision.models import VentureOpportunity
from commerce_os.governance.models import Organization, Project
from commerce_os.operations.models import Customer, SalesOpportunity
from sqlalchemy import inspect
from sqlalchemy.orm import Session


def test_sprint_001_tables_are_registered(db_session: Session) -> None:
    tables = set(inspect(db_session.bind).get_table_names())
    assert {
        "organizations",
        "brands",
        "stores",
        "projects",
        "venture_opportunities",
        "sales_opportunities",
        "customers",
        "customer_identities",
        "conversations",
        "message_metadata",
        "approvals",
        "commercial_policies",
        "outbox_events",
    } <= tables


def test_opportunity_types_are_separate_aggregates(db_session: Session) -> None:
    organization = Organization(name="Example", slug="example")
    db_session.add(organization)
    db_session.flush()
    project = Project(organization_id=organization.id, name="Foundation", slug="foundation")
    customer = Customer(organization_id=organization.id, display_name="Buyer")
    db_session.add_all([project, customer])
    db_session.flush()

    venture = VentureOpportunity(
        organization_id=organization.id, project_id=project.id, name="New market"
    )
    sale = SalesOpportunity(
        organization_id=organization.id,
        project_id=project.id,
        customer_id=customer.id,
        name="B2B deal",
    )
    db_session.add_all([venture, sale])
    db_session.commit()

    assert venture.__tablename__ == "venture_opportunities"
    assert sale.__tablename__ == "sales_opportunities"
    assert venture.id != sale.id


def test_entities_use_typed_uuid_ids() -> None:
    organization = Organization(id=uuid4(), name="Typed", slug="typed")
    assert organization.id.version == 4
