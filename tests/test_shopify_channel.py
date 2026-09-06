from datetime import UTC, datetime

import pytest
from commerce_os.build.listing_governance_models import ListingVersion
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import ApprovalStatus, Permission, PrincipalType, Role
from commerce_os.governance.rbac import RbacService
from commerce_os.operations.shopify_adapter import (
    DeterministicShopifyAdapter,
    ShopifyAdapterError,
)
from commerce_os.operations.shopify_models import ShopifyExternalResource
from commerce_os.operations.shopify_schemas import (
    PublicationRequestCreate,
    ShopifyConnectionCreate,
)
from commerce_os.shared.outbox import OutboxEvent, OutboxStatus
from commerce_os.shopify_services import ShopifyChannelService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.worker.main import consume_shopify_job
from tests.test_listing_governance import draft, ready_foundation


def foundation(session: Session, slug: str = "shopify") -> dict[str, object]:
    state = ready_foundation(session, slug)
    listing = draft(session, state)
    listing.status = "approved"
    listing.approved_by = state["user"].id
    listing.approved_at = datetime.now(UTC)
    listing.structured_attributes = {
        "options": [{"name": "Title", "values": [{"name": "Default"}]}],
        "variants": [
            {
                "sku": f"SKU-{slug}",
                "price": "40.00",
                "optionValues": [{"optionName": "Title", "name": "Default"}],
            }
        ],
        "material": "cotton",
    }
    session.commit()
    state["listing"] = listing
    service = ShopifyChannelService(session)
    connection = service.create_connection(
        ShopifyConnectionCreate(
            organization_id=state["organization"].id,
            store_domain=f"{slug}.myshopify.com",
            display_name=f"{slug.title()} Store",
            authentication_mode="mock",
            credential_reference="SHOPIFY_TEST_TOKEN",
        ),
        state["user"].id,
    )
    adapter = DeterministicShopifyAdapter(connection.store_domain)
    service.validate_connection(connection, state["user"].id, adapter)
    state.update(connection=connection, adapter=adapter, service=service)
    return state


def approver(session: Session, state: dict[str, object]):  # type: ignore[no-untyped-def]
    if state.get("approver") is not None:
        return state["approver"]
    user = AuthenticationService(session).create_user(
        organization_id=state["organization"].id,
        email=f"approver-{state['organization'].id}@example.com",
        display_name="Publication Approver",
        password="correct horse battery staple",
    )
    role = Role(
        organization_id=state["organization"].id,
        name="publication-approver",
        grants_human_approval_authority=True,
    )
    permission = session.scalar(
        select(Permission).where(Permission.key == "approval.decide")
    ) or Permission(
        key="approval.decide",
        resource="approval",
        action="decide",
        is_human_approval_permission=True,
    )
    session.add_all([role, permission])
    session.commit()
    rbac = RbacService(session)
    rbac.grant_permission(role_id=role.id, permission_id=permission.id, actor_id=state["user"].id)
    rbac.assign_role(
        user_id=user.id,
        role_id=role.id,
        organization_id=state["organization"].id,
        project_id=None,
        assigned_by=state["user"].id,
    )
    state["approver"] = user
    return user


def service_worker(session: Session, state: dict[str, object]):  # type: ignore[no-untyped-def]
    return AuthenticationService(session).create_user(
        organization_id=state["organization"].id,
        email=f"worker-{state['organization'].id}@example.com",
        display_name="Shopify Worker",
        password="correct horse battery staple",
        principal_type=PrincipalType.SERVICE,
    )


def authorize_and_queue(session: Session, state: dict[str, object]):  # type: ignore[no-untyped-def]
    service: ShopifyChannelService = state["service"]
    publication = service.request_publication(
        state["product"].id,
        payload=PublicationRequestCreate(
            organization_id=state["organization"].id,
            connection_id=state["connection"].id,
            reason="Publish approved Listing as a safe Shopify draft.",
        ),
        actor_id=state["user"].id,
    )
    reviewer = approver(session, state)
    ApprovalWorkflowService(session).decide(
        approval_id=publication.approval_request_id,
        approver_id=reviewer.id,
        decision=ApprovalStatus.APPROVED,
        reason="Store, source versions, projection, and risks reviewed.",
    )
    service.authorize(
        publication.id,
        state["organization"].id,
        publication.approval_request_id,
        reviewer.id,
    )
    service.queue_execution(publication.id, state["organization"].id, reviewer.id)
    return publication, reviewer


def test_connection_scope_validation_and_serialization_never_exposes_credential(
    client: TestClient, db_session: Session
) -> None:
    state = ready_foundation(db_session, "connection")
    response = client.post(
        "/api/v1/shopify/connections",
        headers={"X-Actor-ID": str(state["user"].id)},
        json={
            "organization_id": str(state["organization"].id),
            "store_domain": "connection.myshopify.com",
            "display_name": "Connection Store",
            "authentication_mode": "mock",
            "credential_reference": "SHOPIFY_TEST_TOKEN",
        },
    )
    assert response.status_code == 201
    assert "credential_reference" not in response.json()
    assert response.json()["credential_configured"] is True
    assert response.json()["required_scopes"] == ["read_products", "write_products"]
    assert "SHOPIFY_TEST_TOKEN" not in response.text


def test_readiness_requires_connection_approved_listing_price_variants_and_media_policy(
    db_session: Session,
) -> None:
    state = ready_foundation(db_session, "blockers")
    listing = draft(db_session, state)
    service = ShopifyChannelService(db_session)
    missing = service.readiness(state["organization"].id, state["product"].id)
    assert {x.code for x in missing.blockers} >= {
        "connection_missing",
        "approved_listing_missing",
        "variant_data_missing",
    }
    listing.status = "approved"
    listing.price_status = "unknown"
    listing.structured_attributes = {"variants": [{"sku": "ONE", "price": "40.00"}]}
    db_session.commit()
    connection = service.create_connection(
        ShopifyConnectionCreate(
            organization_id=state["organization"].id,
            store_domain="blockers.myshopify.com",
            display_name="Blocker Store",
            authentication_mode="mock",
            credential_reference="SHOPIFY_TEST_TOKEN",
            publication_policy={"media_required": True},
        ),
        state["user"].id,
    )
    adapter = DeterministicShopifyAdapter(connection.store_domain)
    service.validate_connection(connection, state["user"].id, adapter)
    result = service.readiness(state["organization"].id, state["product"].id, connection.id)
    assert {x.code for x in result.blockers} >= {"price_not_approved", "media_missing"}
    assert result.media_status == "missing_blocking"


def test_publication_authorization_execution_outbox_idempotency_and_reconciliation(
    db_session: Session,
) -> None:
    state = foundation(db_session, "lifecycle")
    publication, _ = authorize_and_queue(db_session, state)
    assert publication.status == "queued"
    assert state["adapter"].create_calls == 0
    event = db_session.scalar(
        select(OutboxEvent).where(
            OutboxEvent.payload["publication_id"].as_string() == str(publication.id)
        )
    )
    assert event is not None and event.status == OutboxStatus.PENDING
    worker = service_worker(db_session, state)
    consume_shopify_job(db_session, event, state["adapter"])
    event.status = OutboxStatus.PUBLISHED
    db_session.commit()
    assert state["adapter"].create_calls == 1
    state["service"].execute(publication.id, state["organization"].id, worker.id, state["adapter"])
    assert state["adapter"].create_calls == 1
    resource = db_session.scalar(select(ShopifyExternalResource))
    assert resource is not None and resource.external_product_id.startswith(
        "gid://shopify/Product/"
    )
    result = state["service"].reconcile(
        state["product"].id,
        state["connection"].id,
        state["organization"].id,
        state["user"].id,
        state["adapter"],
    )
    assert result.status == "in_sync"
    assert resource.external_status == "draft"


def test_new_listing_requires_new_authorization_then_updates_existing_resource(
    db_session: Session,
) -> None:
    state = foundation(db_session, "update")
    publication, _ = authorize_and_queue(db_session, state)
    worker = service_worker(db_session, state)
    state["service"].execute(publication.id, state["organization"].id, worker.id, state["adapter"])
    first_resource = state["service"].external_resource(
        state["organization"].id, state["connection"].id, state["product"].id
    )
    original_external_id = first_resource.external_product_id
    old: ListingVersion = state["listing"]
    old.status = "superseded"
    new = ListingVersion(
        **{
            key: getattr(old, key)
            for key in (
                "organization_id",
                "product_id",
                "product_truth_id",
                "product_truth_version",
                "subtitle",
                "summary",
                "description",
                "customer_problem",
                "solution",
                "features",
                "benefits",
                "specifications",
                "use_cases",
                "whats_included",
                "warnings",
                "care_usage",
                "shipping_facts",
                "return_facts",
                "risk_reversal",
                "seo_title",
                "meta_description",
                "slug_suggestion",
                "primary_topic",
                "secondary_topics",
                "structured_attributes",
                "commercial_price",
                "currency",
                "price_status",
                "created_by",
            )
        },
        listing_version=2,
        status="approved",
        title="Governed Product v2",
        change_reason="Approved update",
        approved_by=state["user"].id,
        approved_at=datetime.now(UTC),
    )
    db_session.add(new)
    db_session.commit()
    readiness = state["service"].readiness(
        state["organization"].id, state["product"].id, state["connection"].id
    )
    assert readiness.drift_status == "commerce_os_newer"
    assert readiness.authorization_status == "new_authorization_required"
    second, _ = authorize_and_queue(db_session, state)
    state["service"].execute(second.id, state["organization"].id, worker.id, state["adapter"])
    assert state["adapter"].update_calls == 1
    updated = state["service"].external_resource(
        state["organization"].id, state["connection"].id, state["product"].id
    )
    assert updated.external_product_id == original_external_id
    assert updated.source_listing_version_id == new.id


def test_external_drift_is_visible_and_never_overwritten(db_session: Session) -> None:
    state = foundation(db_session, "drift")
    publication, _ = authorize_and_queue(db_session, state)
    worker = service_worker(db_session, state)
    state["service"].execute(publication.id, state["organization"].id, worker.id, state["adapter"])
    resource = state["service"].external_resource(
        state["organization"].id, state["connection"].id, state["product"].id
    )
    state["adapter"].simulate_drift(resource.external_product_id, "title", "Manual Shopify edit")
    result = state["service"].reconcile(
        state["product"].id,
        state["connection"].id,
        state["organization"].id,
        state["user"].id,
        state["adapter"],
    )
    assert result.status == "shopify_changed_externally"
    assert (
        state["adapter"].resources[resource.external_product_id].owned_fields["title"]
        == "Manual Shopify edit"
    )


def test_failures_are_safe_and_retryability_is_explicit(db_session: Session) -> None:
    state = foundation(db_session, "failure")
    publication, _ = authorize_and_queue(db_session, state)
    worker = service_worker(db_session, state)
    state["adapter"].failure = ShopifyAdapterError("rate_limit", "Retry later.", True)
    with pytest.raises(ShopifyAdapterError) as error:
        state["service"].execute(
            publication.id, state["organization"].id, worker.id, state["adapter"]
        )
    assert error.value.retryable and publication.last_error_category == "rate_limit"
    assert "token" not in publication.last_error_message.lower()


def test_cross_tenant_connection_and_execution_are_denied(db_session: Session) -> None:
    first = foundation(db_session, "tenant-one")
    second = ready_foundation(db_session, "tenant-two")
    with pytest.raises(LookupError):
        first["service"].connection(first["connection"].id, second["organization"].id)
    publication, _ = authorize_and_queue(db_session, first)
    foreign_worker = service_worker(db_session, second)
    with pytest.raises(PermissionError):
        first["service"].execute(
            publication.id,
            first["organization"].id,
            foreign_worker.id,
            first["adapter"],
        )
