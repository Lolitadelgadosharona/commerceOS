import hashlib
import hmac
import json
from base64 import b64encode
from datetime import UTC, datetime
from urllib.error import HTTPError

import pytest
from commerce_os.build.listing_governance_models import ListingVersion
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.authentication import AuthenticationService
from commerce_os.governance.models import ApprovalStatus, Permission, PrincipalType, Role
from commerce_os.governance.rbac import RbacService
from commerce_os.operations.shopify_adapter import (
    DeterministicShopifyAdapter,
    ShopifyAdapterError,
    ShopifyGraphQLAdapter,
)
from commerce_os.operations.shopify_models import ShopifyExternalResource, ShopifyWebhookEvent
from commerce_os.operations.shopify_schemas import (
    PublicationRequestCreate,
    ShopifyConnectionCreate,
)
from commerce_os.shared.outbox import OutboxEvent, OutboxStatus
from commerce_os.shopify_services import ShopifyChannelService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.worker.main import consume_shopify_job, process_next_shopify_job
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


def next_listing(
    session: Session,
    state: dict[str, object],
    source: ListingVersion,
    *,
    version: int,
    title: str,
    reason: str,
) -> ListingVersion:
    source.status = "superseded"
    item = ListingVersion(
        **{
            key: getattr(source, key)
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
        listing_version=version,
        status="approved",
        title=title,
        change_reason=reason,
        approved_by=state["user"].id,
        approved_at=datetime.now(UTC),
    )
    session.add(item)
    session.commit()
    state["listing"] = item
    return item


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


def test_mock_validation_records_safe_merchant_identity(db_session: Session) -> None:
    state = foundation(db_session, "identity")
    connection = state["connection"]
    assert connection.shop_gid == "gid://shopify/Shop/1"
    assert connection.merchant_name == "Deterministic Development Store"
    assert connection.partner_development is True
    assert connection.plan_display_name == "Development"


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
    new = next_listing(
        db_session,
        state,
        old,
        version=2,
        title="Governed Product v2",
        reason="Approved update",
    )
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


def test_missing_external_resource_requires_manual_intervention(db_session: Session) -> None:
    state = foundation(db_session, "missing")
    publication, _ = authorize_and_queue(db_session, state)
    worker = service_worker(db_session, state)
    state["service"].execute(publication.id, state["organization"].id, worker.id, state["adapter"])
    resource = state["service"].external_resource(
        state["organization"].id, state["connection"].id, state["product"].id
    )
    del state["adapter"].resources[resource.external_product_id]
    result = state["service"].reconcile(
        state["product"].id,
        state["connection"].id,
        state["organization"].id,
        state["user"].id,
        state["adapter"],
    )
    assert result.status == "missing_external_resource"


def test_rollback_is_a_fresh_approved_compensating_listing(db_session: Session) -> None:
    state = foundation(db_session, "rollback")
    original: ListingVersion = state["listing"]
    original_title = original.title
    first, _ = authorize_and_queue(db_session, state)
    worker = service_worker(db_session, state)
    state["service"].execute(first.id, state["organization"].id, worker.id, state["adapter"])
    external_id = (
        state["service"]
        .external_resource(state["organization"].id, state["connection"].id, state["product"].id)
        .external_product_id
    )
    changed = next_listing(
        db_session, state, original, version=2, title="Approved change", reason="Forward change"
    )
    second, _ = authorize_and_queue(db_session, state)
    state["service"].execute(second.id, state["organization"].id, worker.id, state["adapter"])
    restored = next_listing(
        db_session,
        state,
        changed,
        version=3,
        title=original_title,
        reason="Governed compensating rollback to prior safe content",
    )
    third, _ = authorize_and_queue(db_session, state)
    state["service"].execute(third.id, state["organization"].id, worker.id, state["adapter"])
    resource = state["service"].external_resource(
        state["organization"].id, state["connection"].id, state["product"].id
    )
    assert resource.external_product_id == external_id
    assert resource.source_listing_version_id == restored.id
    assert state["adapter"].resources[external_id].owned_fields["title"] == original_title
    assert first.id != second.id != third.id


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
    state["service"].queue_execution(publication.id, state["organization"].id, state["user"].id)
    events = list(
        db_session.scalars(
            select(OutboxEvent).where(
                OutboxEvent.payload["publication_id"].as_string() == str(publication.id)
            )
        )
    )
    assert len(events) == 1


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


def test_product_set_contract_is_draft_versioned_and_inventory_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class Response:
        headers = {"X-Shopify-API-Access-Scopes": "read_products,write_products"}

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "data": {
                        "productSet": {
                            "product": {
                                "id": "gid://shopify/Product/1",
                                "status": "DRAFT",
                                "variants": {"nodes": [{"id": "gid://shopify/ProductVariant/2"}]},
                            },
                            "userErrors": [],
                        }
                    }
                }
            ).encode()

    def urlopen(request, timeout):  # type: ignore[no-untyped-def]
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("SHOPIFY_CONTRACT_TOKEN", "deterministic-secret-fixture")
    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    adapter = ShopifyGraphQLAdapter(
        store_domain="contract.myshopify.com",
        api_version="2026-07",
        credential_reference="SHOPIFY_CONTRACT_TOKEN",
    )
    projection = {
        "title": "Safe Product",
        "description_html": "Evidence-backed description",
        "vendor": "Commerce OS",
        "product_type": "test",
        "handle": "safe-product",
        "seo": {"title": "Safe Product", "description": "Safe"},
        "options": [],
        "variants": [{"sku": "SAFE-1", "price": "40.00"}],
        "inventory_quantities": [],
    }
    result = adapter.update_product("gid://shopify/Product/1", projection)
    body = captured["body"]
    variables = body["variables"]  # type: ignore[index]
    assert captured["url"] == "https://contract.myshopify.com/admin/api/2026-07/graphql.json"
    assert variables["identifier"] == {"id": "gid://shopify/Product/1"}  # type: ignore[index]
    assert variables["input"]["status"] == "DRAFT"  # type: ignore[index]
    assert "inventoryQuantities" not in variables["input"]  # type: ignore[operator]
    assert result.status == "draft"
    assert "deterministic-secret-fixture" not in json.dumps(captured["body"])


def test_graphql_reconciliation_normalizes_shopify_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Response:
        headers: dict[str, str] = {}

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "data": {
                        "product": {
                            "id": "gid://shopify/Product/1",
                            "title": "Safe Product",
                            "descriptionHtml": "Evidence-backed description",
                            "vendor": "Commerce OS",
                            "productType": "test",
                            "handle": "safe-product",
                            "status": "DRAFT",
                            "seo": {"title": "Safe Product", "description": "Safe"},
                            "options": [{"name": "Title", "optionValues": [{"name": "Default"}]}],
                            "variants": {
                                "nodes": [
                                    {
                                        "id": "gid://shopify/ProductVariant/2",
                                        "sku": "SAFE-1",
                                        "price": "40.00",
                                        "selectedOptions": [{"name": "Title", "value": "Default"}],
                                    }
                                ]
                            },
                        }
                    }
                }
            ).encode()

    monkeypatch.setenv("SHOPIFY_RECONCILIATION_TOKEN", "deterministic-secret-fixture")
    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    adapter = ShopifyGraphQLAdapter(
        store_domain="reconciliation.myshopify.com",
        api_version="2026-07",
        credential_reference="SHOPIFY_RECONCILIATION_TOKEN",
    )
    result = adapter.fetch_product("gid://shopify/Product/1")
    assert result is not None
    assert result.owned_fields["description_html"] == "Evidence-backed description"
    assert result.owned_fields["product_type"] == "test"
    assert result.owned_fields["external_status"] == "draft"
    assert result.owned_fields["variants"] == [
        {
            "sku": "SAFE-1",
            "price": "40.00",
            "optionValues": [{"optionName": "Title", "name": "Default"}],
        }
    ]


@pytest.mark.parametrize(
    ("status", "category", "retryable"),
    [
        (401, "authentication", False),
        (403, "authorization_scope", False),
        (429, "rate_limit", True),
        (503, "network", True),
    ],
)
def test_graphql_failure_classification_is_safe(
    monkeypatch: pytest.MonkeyPatch, status: int, category: str, retryable: bool
) -> None:
    monkeypatch.setenv("SHOPIFY_FAILURE_TOKEN", "must-never-appear")

    def fail(request, timeout):  # type: ignore[no-untyped-def]
        raise HTTPError(
            request.full_url, status, "provider detail with must-never-appear", {}, None
        )

    monkeypatch.setattr("urllib.request.urlopen", fail)
    adapter = ShopifyGraphQLAdapter(
        store_domain="failure-contract.myshopify.com",
        api_version="2026-07",
        credential_reference="SHOPIFY_FAILURE_TOKEN",
    )
    with pytest.raises(ShopifyAdapterError) as caught:
        adapter.fetch_product("gid://shopify/Product/1")
    assert caught.value.category == category
    assert caught.value.retryable is retryable
    assert "must-never-appear" not in str(caught.value)


def test_webhook_hmac_verification_is_public_idempotent_and_payload_safe(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = foundation(db_session, "webhook")
    state["connection"].publication_policy = {
        "media_required": False,
        "webhook_secret_reference": "SHOPIFY_WEBHOOK_TEST_SECRET",
    }
    db_session.commit()
    secret = "signed-fixture-secret"
    monkeypatch.setenv("SHOPIFY_WEBHOOK_TEST_SECRET", secret)
    body = b'{"id":123,"title":"safe fixture"}'
    signature = b64encode(hmac.digest(secret.encode(), body, "sha256")).decode()
    headers = {
        "X-Shopify-Shop-Domain": "webhook.myshopify.com",
        "X-Shopify-Webhook-Id": "fixture-delivery-1",
        "X-Shopify-Topic": "products/update",
        "X-Shopify-Hmac-Sha256": signature,
    }
    first = client.post("/api/v1/shopify/webhooks", content=body, headers=headers)
    second = client.post("/api/v1/shopify/webhooks", content=body, headers=headers)
    assert first.status_code == second.status_code == 202
    events = list(db_session.scalars(select(ShopifyWebhookEvent)))
    assert len(events) == 1
    assert events[0].payload_hash == hashlib.sha256(body).hexdigest()
    assert "safe fixture" not in json.dumps(events[0].__dict__, default=str)
    invalid = client.post(
        "/api/v1/shopify/webhooks",
        content=body,
        headers={
            **headers,
            "X-Shopify-Webhook-Id": "fixture-delivery-2",
            "X-Shopify-Hmac-Sha256": "invalid",
        },
    )
    assert invalid.status_code == 401


@pytest.mark.parametrize("retryable", [True, False])
def test_worker_schedules_only_retryable_connector_failures(
    db_session: Session, monkeypatch: pytest.MonkeyPatch, retryable: bool
) -> None:
    state = foundation(db_session, f"worker-{str(retryable).lower()}")
    publication, _ = authorize_and_queue(db_session, state)

    def fail(*_: object, **__: object) -> None:
        raise ShopifyAdapterError(
            "rate_limit" if retryable else "validation", "Safe failure.", retryable
        )

    monkeypatch.setattr("apps.worker.main.consume_shopify_job", fail)
    assert process_next_shopify_job(db_session) is True
    event = db_session.scalar(
        select(OutboxEvent).where(
            OutboxEvent.payload["publication_id"].as_string() == str(publication.id)
        )
    )
    assert event is not None and event.status == OutboxStatus.FAILED
    if retryable:
        assert event.available_at.year < 9999
    else:
        assert event.available_at.year == 9999
