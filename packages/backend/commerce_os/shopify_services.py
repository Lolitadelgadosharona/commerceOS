from __future__ import annotations

import hashlib
import hmac
import json
from base64 import b64decode
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.build.listing_governance_models import ListingVersion
from commerce_os.build.models import Product, ProductTruth
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.audit import AuditService
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import ApprovalRequest, ApprovalStatus, PrincipalType, User
from commerce_os.operations.models import Brand
from commerce_os.operations.shopify_adapter import (
    ShopifyAdapter,
    ShopifyAdapterError,
    connector_owned_fields,
)
from commerce_os.operations.shopify_config import SHOPIFY_REQUIRED_SCOPES
from commerce_os.operations.shopify_models import (
    ShopifyConnection,
    ShopifyExternalResource,
    ShopifyPublication,
    ShopifyReconciliation,
    ShopifyWebhookEvent,
)
from commerce_os.operations.shopify_schemas import (
    SHOPIFY_API_VERSION,
    PublicationRequestCreate,
    ReadinessIssue,
    ShopifyConnectionCreate,
    ShopifyProjection,
    ShopifyPublicationReadiness,
)
from commerce_os.shared.events import BusinessEventEnvelope, EventActor
from commerce_os.shared.outbox import OutboxEvent, OutboxStatus, add_to_outbox

SHOPIFY_PUBLICATION_EVENT = "shopify.publication_requested"


def canonical_hash(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class ShopifyChannelService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit = AuditService(session)

    def human(self, actor_id: UUID, organization_id: UUID) -> User:
        actor = self.session.get(User, actor_id)
        if (
            actor is None
            or actor.organization_id != organization_id
            or actor.principal_type != PrincipalType.HUMAN
        ):
            raise PermissionError("An in-scope human actor is required.")
        return actor

    def connection(self, connection_id: UUID, organization_id: UUID) -> ShopifyConnection:
        connection = self.session.get(ShopifyConnection, connection_id)
        if connection is None or connection.organization_id != organization_id:
            raise LookupError("Shopify connection was not found in this organization.")
        return connection

    def create_connection(
        self, payload: ShopifyConnectionCreate, actor_id: UUID
    ) -> ShopifyConnection:
        actor = self.human(actor_id, payload.organization_id)
        item = ShopifyConnection(
            organization_id=payload.organization_id,
            store_id=payload.store_id,
            store_domain=payload.store_domain,
            display_name=payload.display_name,
            authentication_mode=payload.authentication_mode,
            credential_reference=payload.credential_reference,
            required_scopes=list(SHOPIFY_REQUIRED_SCOPES),
            granted_scopes=payload.granted_scopes,
            api_version=SHOPIFY_API_VERSION,
            status="not_configured" if payload.authentication_mode != "mock" else "configured",
            publication_policy=payload.publication_policy.model_dump(exclude_none=True),
            created_by=actor.id,
        )
        self.session.add(item)
        self.session.flush()
        self.audit.record(
            organization_id=payload.organization_id,
            actor_type="human",
            actor_id=actor.id,
            action="shopify.connection_created",
            entity_type="shopify_connection",
            entity_id=item.id,
            metadata={"store_domain": item.store_domain, "credential_reference_stored": True},
        )
        self.session.commit()
        self.session.refresh(item)
        return item

    def validate_connection(
        self,
        connection: ShopifyConnection,
        actor_id: UUID,
        adapter: ShopifyAdapter,
    ) -> ShopifyConnection:
        actor = self.human(actor_id, connection.organization_id)
        try:
            result = adapter.validate_connection()
            if result.store_domain != connection.store_domain:
                raise ShopifyAdapterError("validation", "Credential resolves to another store.")
            connection.granted_scopes = result.granted_scopes
            connection.shop_gid = result.shop_gid
            connection.merchant_name = result.merchant_name
            connection.partner_development = result.partner_development
            connection.plan_display_name = result.plan_display_name
            missing = set(connection.required_scopes) - set(result.granted_scopes)
            connection.status = "scope_missing" if missing else "ready"
            connection.validated_at = datetime.now(UTC)
            connection.last_error_category = None
            connection.last_error_message = None
        except ShopifyAdapterError as exc:
            connection.status = "invalid"
            connection.last_error_category = exc.category
            connection.last_error_message = str(exc)[:500]
        self.audit.record(
            organization_id=connection.organization_id,
            actor_type="human",
            actor_id=actor.id,
            action="shopify.connection_validated",
            entity_type="shopify_connection",
            entity_id=connection.id,
            metadata={"result": connection.status},
        )
        self.session.commit()
        self.session.refresh(connection)
        return connection

    def latest_listing(self, organization_id: UUID, product_id: UUID) -> ListingVersion | None:
        return self.session.scalar(
            select(ListingVersion)
            .where(
                ListingVersion.organization_id == organization_id,
                ListingVersion.product_id == product_id,
                ListingVersion.status == "approved",
            )
            .order_by(ListingVersion.listing_version.desc())
        )

    def external_resource(
        self, organization_id: UUID, connection_id: UUID, product_id: UUID
    ) -> ShopifyExternalResource | None:
        return self.session.scalar(
            select(ShopifyExternalResource).where(
                ShopifyExternalResource.organization_id == organization_id,
                ShopifyExternalResource.connection_id == connection_id,
                ShopifyExternalResource.product_id == product_id,
            )
        )

    def project(self, listing: ListingVersion) -> ShopifyProjection:
        product = self.session.get(Product, listing.product_id)
        brand = None if product is None else self.session.get(Brand, product.brand_id)
        attrs = listing.structured_attributes
        return ShopifyProjection(
            title=listing.title,
            description_html=listing.description,
            vendor=None if brand is None else brand.name,
            product_type="" if product is None else product.category,
            handle=listing.slug_suggestion,
            seo={"title": listing.seo_title, "description": listing.meta_description},
            options=attrs.get("options", []) if isinstance(attrs.get("options", []), list) else [],
            variants=attrs.get("variants", [])
            if isinstance(attrs.get("variants", []), list)
            else [],
            metafields={
                k: v for k, v in attrs.items() if k not in {"options", "variants", "media"}
            },
            media=attrs.get("media", []) if isinstance(attrs.get("media", []), list) else [],
        )

    def readiness(
        self, organization_id: UUID, product_id: UUID, connection_id: UUID | None = None
    ) -> ShopifyPublicationReadiness:
        listing = self.latest_listing(organization_id, product_id)
        truth = self.session.scalar(
            select(ProductTruth)
            .where(
                ProductTruth.organization_id == organization_id,
                ProductTruth.product_id == product_id,
            )
            .order_by(ProductTruth.version.desc())
        )
        connection = (
            None if connection_id is None else self.connection(connection_id, organization_id)
        )
        blockers: list[ReadinessIssue] = []
        warnings: list[ReadinessIssue] = []
        projection = None if listing is None else self.project(listing)
        if connection is None:
            blockers.append(
                ReadinessIssue(
                    code="connection_missing",
                    severity="blocker",
                    message="Shopify is not configured.",
                )
            )
        elif connection.status != "ready":
            blockers.append(
                ReadinessIssue(
                    code="connection_not_ready",
                    severity="blocker",
                    message="Shopify connection validation is required.",
                )
            )
            missing = set(connection.required_scopes) - set(connection.granted_scopes)
            if missing:
                blockers.append(
                    ReadinessIssue(
                        code="scope_missing",
                        severity="blocker",
                        message=f"Missing required scopes: {', '.join(sorted(missing))}.",
                    )
                )
        if listing is None:
            blockers.append(
                ReadinessIssue(
                    code="approved_listing_missing",
                    severity="blocker",
                    message="An approved Listing version is required.",
                )
            )
        elif truth is None or listing.product_truth_id != truth.id:
            blockers.append(
                ReadinessIssue(
                    code="listing_stale",
                    severity="blocker",
                    message="Product Truth changed; Listing review is required.",
                )
            )
        if listing and (listing.price_status != "approved" or listing.commercial_price is None):
            blockers.append(
                ReadinessIssue(
                    code="price_not_approved",
                    severity="blocker",
                    message="Approved commercial price is required.",
                )
            )
        variants = [] if projection is None else projection.variants
        if not variants:
            blockers.append(
                ReadinessIssue(
                    code="variant_data_missing",
                    severity="blocker",
                    message="Persisted Shopify variant data is required; no variant is fabricated.",
                )
            )
        elif any(
            not isinstance(v, dict) or not v.get("sku") or v.get("price") is None for v in variants
        ):
            blockers.append(
                ReadinessIssue(
                    code="variant_data_invalid",
                    severity="blocker",
                    message="Every variant requires a stable SKU and approved price.",
                )
            )
        media_required = bool(
            connection and connection.publication_policy.get("media_required", False)
        )
        media = [] if projection is None else projection.media
        media_status = "ready" if media else "missing_blocking" if media_required else "optional"
        if media_status == "missing_blocking":
            blockers.append(
                ReadinessIssue(
                    code="media_missing",
                    severity="blocker",
                    message="Connection policy requires approved media.",
                )
            )
        elif not media:
            warnings.append(
                ReadinessIssue(
                    code="media_optional",
                    severity="warning",
                    message="No approved media is attached; draft publication may continue.",
                )
            )
        if projection and (
            not projection.seo.get("title") or not projection.seo.get("description")
        ):
            warnings.append(
                ReadinessIssue(
                    code="seo_optional",
                    severity="warning",
                    message="Optional Shopify SEO metadata is incomplete.",
                )
            )
        resource = (
            None
            if connection is None
            else self.external_resource(organization_id, connection.id, product_id)
        )
        publication = self.session.scalar(
            select(ShopifyPublication)
            .where(
                ShopifyPublication.organization_id == organization_id,
                ShopifyPublication.product_id == product_id,
                *(
                    []
                    if connection is None
                    else [ShopifyPublication.connection_id == connection.id]
                ),
            )
            .order_by(ShopifyPublication.created_at.desc())
        )
        drift = "unknown"
        if resource and listing:
            drift = (
                "in_sync"
                if resource.source_listing_version_id == listing.id
                else "commerce_os_newer"
            )
        status = "not_ready" if blockers else "conditional" if warnings else "ready"
        publication_matches_source = bool(
            publication
            and listing
            and truth
            and publication.listing_version_id == listing.id
            and publication.product_truth_id == truth.id
        )
        authorization = (
            "not_requested"
            if publication is None
            else "new_authorization_required"
            if not publication_matches_source
            else publication.status
        )
        next_action = (
            blockers[0].message
            if blockers
            else "Request publication authorization."
            if publication is None or not publication_matches_source
            else "Explicit execution required."
            if publication.status == "authorized"
            else "Review publication status."
        )
        payload = None if projection is None else projection.model_dump(mode="json")
        return ShopifyPublicationReadiness(
            organization_id=organization_id,
            product_id=product_id,
            connection_id=None if connection is None else connection.id,
            product_truth_id=None if truth is None else truth.id,
            product_truth_version=None if truth is None else truth.version,
            listing_version_id=None if listing is None else listing.id,
            listing_version=None if listing is None else listing.listing_version,
            projection=projection,
            projection_hash=None if payload is None else canonical_hash(payload),
            status=status,
            blockers=blockers,
            warnings=warnings,
            media_status=media_status,
            publication_status="not_published" if resource is None else resource.external_status,
            authorization_status=authorization,
            external_resource_id=None if resource is None else resource.id,
            external_product_id=None if resource is None else resource.external_product_id,
            drift_status=drift,
            operation="create" if resource is None else "update",
            next_action=next_action,
        )

    def request_publication(
        self, product_id: UUID, payload: PublicationRequestCreate, actor_id: UUID
    ) -> ShopifyPublication:
        actor = self.human(actor_id, payload.organization_id)
        ready = self.readiness(payload.organization_id, product_id, payload.connection_id)
        if (
            ready.status == "not_ready"
            or ready.listing_version_id is None
            or ready.projection is None
            or ready.projection_hash is None
            or ready.product_truth_id is None
            or ready.product_truth_version is None
            or ready.listing_version is None
        ):
            raise ValueError("Shopify publication readiness blockers remain.")
        key = f"shopify:{payload.connection_id}:{ready.listing_version_id}"
        existing = self.session.scalar(
            select(ShopifyPublication).where(
                ShopifyPublication.organization_id == payload.organization_id,
                ShopifyPublication.idempotency_key == key,
            )
        )
        if existing:
            return existing
        item = ShopifyPublication(
            organization_id=payload.organization_id,
            connection_id=payload.connection_id,
            product_id=product_id,
            product_truth_id=ready.product_truth_id,
            product_truth_version=ready.product_truth_version,
            listing_version_id=ready.listing_version_id,
            listing_version=ready.listing_version,
            projection=ready.projection.model_dump(mode="json"),
            projection_hash=ready.projection_hash,
            operation=ready.operation,
            status="requested",
            idempotency_key=key,
            requested_by=actor.id,
        )
        self.session.add(item)
        self.session.flush()
        approval = ApprovalWorkflowService(self.session).request(
            organization_id=payload.organization_id,
            project_id=None,
            requester_id=actor.id,
            object_type="shopify_publication",
            object_id=item.id,
            requested_action="shopify.publication_authorize",
            reason=payload.reason,
            commit=False,
        )
        item.approval_request_id = approval.id
        self.session.add(
            DecisionQueueItem(
                organization_id=payload.organization_id,
                title=f"Shopify publication: {ready.projection.title}",
                domain="governance",
                reason=payload.reason,
                priority="high",
                required_action="shopify_publication",
                status="pending",
                approval_request_id=approval.id,
            )
        )
        self.session.commit()
        self.session.refresh(item)
        return item

    def authorize(
        self, publication_id: UUID, organization_id: UUID, approval_id: UUID, actor_id: UUID
    ) -> ShopifyPublication:
        actor = self.human(actor_id, organization_id)
        item = self.scoped_publication(publication_id, organization_id)
        approval = self.session.get(ApprovalRequest, approval_id)
        if (
            approval is None
            or approval.id != item.approval_request_id
            or approval.object_id != item.id
            or approval.status != ApprovalStatus.APPROVED
        ):
            raise ValueError("Approved Shopify publication authorization is required.")
        current = self.readiness(organization_id, item.product_id, item.connection_id)
        if current.status == "not_ready" or current.listing_version_id != item.listing_version_id:
            raise ValueError("Publication source is no longer current and ready.")
        item.status = "authorized"
        item.authorized_by = actor.id
        item.authorized_at = datetime.now(UTC)
        self.audit.record(
            organization_id=organization_id,
            actor_type="human",
            actor_id=actor.id,
            action="shopify.publication_authorized",
            entity_type="shopify_publication",
            entity_id=item.id,
            metadata={"external_write": False},
        )
        self.session.commit()
        self.session.refresh(item)
        return item

    def queue_execution(
        self, publication_id: UUID, organization_id: UUID, actor_id: UUID
    ) -> ShopifyPublication:
        actor = self.human(actor_id, organization_id)
        item = self.scoped_publication(publication_id, organization_id)
        if item.status == "succeeded":
            return item
        if item.status not in {"authorized", "failed"}:
            raise ValueError("Publication must be authorized before explicit execution.")
        item.status = "queued"
        item.execution_requested_by = actor.id
        event_key = f"{item.idempotency_key}:execute"
        event = self.session.scalar(
            select(OutboxEvent).where(
                OutboxEvent.organization_id == organization_id,
                OutboxEvent.idempotency_key == event_key,
            )
        )
        if event is None:
            add_to_outbox(
                self.session,
                BusinessEventEnvelope(
                    event_type=SHOPIFY_PUBLICATION_EVENT,
                    actor=EventActor(actor_type="human", actor_id=str(actor.id)),
                    source="operations.shopify",
                    idempotency_key=event_key,
                    correlation_id=uuid4(),
                    organization_id=organization_id,
                    product_id=item.product_id,
                    payload={"publication_id": str(item.id)},
                ),
            )
        elif event.status == OutboxStatus.FAILED:
            event.status = OutboxStatus.PENDING
            event.available_at = datetime.now(UTC)
            event.last_error = None
        self.audit.record(
            organization_id=organization_id,
            actor_type="human",
            actor_id=actor.id,
            action="shopify.publication_queued",
            entity_type="shopify_publication",
            entity_id=item.id,
            metadata={"operation": item.operation},
        )
        self.session.commit()
        self.session.refresh(item)
        return item

    def execute(
        self, publication_id: UUID, organization_id: UUID, worker_id: UUID, adapter: ShopifyAdapter
    ) -> ShopifyPublication:
        worker = self.session.get(User, worker_id)
        item = self.scoped_publication(publication_id, organization_id)
        if (
            worker is None
            or worker.organization_id != organization_id
            or worker.principal_type != PrincipalType.SERVICE
        ):
            raise PermissionError("In-scope service identity is required for connector execution.")
        if item.status == "succeeded":
            return item
        if item.status not in {"queued", "executing", "failed"}:
            raise ValueError("Publication is not queued for execution.")
        connection = self.connection(item.connection_id, organization_id)
        if connection.status != "ready":
            raise ValueError("Shopify connection is not ready.")
        resource = self.external_resource(organization_id, item.connection_id, item.product_id)
        item.status = "executing"
        item.attempts += 1
        self.session.commit()
        try:
            result = (
                adapter.create_product(item.projection)
                if resource is None
                else adapter.update_product(resource.external_product_id, item.projection)
            )
        except ShopifyAdapterError as exc:
            item.status = "failed"
            item.last_error_category = exc.category
            item.last_error_message = str(exc)[:500]
            self.session.commit()
            raise
        now = datetime.now(UTC)
        if resource is None:
            resource = ShopifyExternalResource(
                organization_id=organization_id,
                connection_id=item.connection_id,
                product_id=item.product_id,
                external_product_id=result.external_product_id,
                external_variant_ids=result.external_variant_ids,
                external_status=result.status,
                owned_fields_snapshot=result.owned_fields,
                external_hash=canonical_hash(result.owned_fields),
                source_listing_version_id=item.listing_version_id,
                last_publication_id=item.id,
                last_synced_at=now,
                admin_reference=None,
            )
            self.session.add(resource)
        else:
            resource.external_variant_ids = result.external_variant_ids
            resource.external_status = result.status
            resource.owned_fields_snapshot = result.owned_fields
            resource.external_hash = canonical_hash(result.owned_fields)
            resource.source_listing_version_id = item.listing_version_id
            resource.last_publication_id = item.id
            resource.last_synced_at = now
        item.status = "succeeded"
        item.executed_at = now
        item.last_error_category = None
        item.last_error_message = None
        self.audit.record(
            organization_id=organization_id,
            actor_type="service",
            actor_id=worker.id,
            action="shopify.publication_succeeded",
            entity_type="shopify_publication",
            entity_id=item.id,
            metadata={
                "external_product_id": result.external_product_id,
                "api_version": connection.api_version,
            },
        )
        self.session.commit()
        self.session.refresh(item)
        return item

    def reconcile(
        self,
        product_id: UUID,
        connection_id: UUID,
        organization_id: UUID,
        actor_id: UUID,
        adapter: ShopifyAdapter,
    ) -> ShopifyReconciliation:
        actor = self.human(actor_id, organization_id)
        resource = self.external_resource(organization_id, connection_id, product_id)
        listing = self.latest_listing(organization_id, product_id)
        external = None if resource is None else adapter.fetch_product(resource.external_product_id)
        commerce = (
            None
            if listing is None
            else connector_owned_fields(self.project(listing).model_dump(mode="json"))
        )
        commerce_hash = None if commerce is None else canonical_hash(commerce)
        external_hash = None if external is None else canonical_hash(external.owned_fields)
        if resource is None or external is None:
            status, differences = "missing_external_resource", ["external_product"]
        elif listing and resource.source_listing_version_id != listing.id:
            status, differences = "commerce_os_newer", ["listing_version"]
        elif commerce_hash == external_hash:
            status, differences = "in_sync", []
        else:
            status, differences = "shopify_changed_externally", ["connector_owned_fields"]
        item = ShopifyReconciliation(
            organization_id=organization_id,
            connection_id=connection_id,
            product_id=product_id,
            external_resource_id=None if resource is None else resource.id,
            publication_id=None if resource is None else resource.last_publication_id,
            status=status,
            commerce_hash=commerce_hash,
            external_hash=external_hash,
            differences=differences,
            checked_at=datetime.now(UTC),
            checked_by=actor.id,
        )
        self.session.add(item)
        self.session.flush()
        self.audit.record(
            organization_id=organization_id,
            actor_type="human",
            actor_id=actor.id,
            action="shopify.reconciled",
            entity_type="shopify_reconciliation",
            entity_id=item.id,
            metadata={"result": status, "automatic_overwrite": False},
        )
        self.session.commit()
        self.session.refresh(item)
        return item

    def record_verified_webhook(
        self,
        *,
        connection: ShopifyConnection,
        webhook_id: str,
        topic: str,
        raw_body: bytes,
        supplied_signature: str,
        secret: str,
    ) -> ShopifyWebhookEvent:
        """Verify raw-body HMAC and persist only safe, idempotent delivery metadata."""
        try:
            supplied = b64decode(supplied_signature, validate=True)
        except ValueError:
            supplied = b""
        expected = hmac.digest(secret.encode(), raw_body, "sha256")
        if not supplied or not hmac.compare_digest(expected, supplied):
            raise PermissionError("Shopify webhook signature is invalid.")
        existing = self.session.scalar(
            select(ShopifyWebhookEvent).where(
                ShopifyWebhookEvent.connection_id == connection.id,
                ShopifyWebhookEvent.webhook_id == webhook_id,
            )
        )
        if existing:
            return existing
        item = ShopifyWebhookEvent(
            organization_id=connection.organization_id,
            connection_id=connection.id,
            webhook_id=webhook_id,
            topic=topic,
            payload_hash=hashlib.sha256(raw_body).hexdigest(),
            signature_valid=True,
            processed_at=datetime.now(UTC),
        )
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def scoped_publication(self, publication_id: UUID, organization_id: UUID) -> ShopifyPublication:
        item = self.session.get(ShopifyPublication, publication_id)
        if item is None or item.organization_id != organization_id:
            raise LookupError("Shopify publication was not found in this organization.")
        return item
