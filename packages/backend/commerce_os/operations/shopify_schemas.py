from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from commerce_os.shared.schemas import ReadModel

SHOPIFY_REQUIRED_SCOPES = ["read_products", "write_products"]
SHOPIFY_API_VERSION = "2026-07"


class ShopifyConnectionCreate(BaseModel):
    organization_id: UUID
    store_id: UUID | None = None
    store_domain: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$")
    display_name: str = Field(min_length=1, max_length=255)
    authentication_mode: Literal["local_token", "oauth", "mock"] = "local_token"
    credential_reference: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,199}$")
    granted_scopes: list[str] = Field(default_factory=list)
    publication_policy: dict[str, object] = Field(default_factory=dict)

    @field_validator("credential_reference")
    @classmethod
    def reject_secret_material(cls, value: str) -> str:
        if value.startswith(("shp", "sk-")):
            raise ValueError("Provide an environment variable name, never secret material.")
        return value


class ShopifyConnectionRead(ReadModel):
    organization_id: UUID
    store_id: UUID | None
    store_domain: str
    display_name: str
    authentication_mode: str
    credential_configured: bool
    required_scopes: list[str]
    granted_scopes: list[str]
    api_version: str
    status: str
    publication_policy: dict[str, object]
    created_by: UUID
    validated_at: datetime | None
    last_error_category: str | None
    last_error_message: str | None


class ConnectionValidationRequest(BaseModel):
    organization_id: UUID


class ReadinessIssue(BaseModel):
    code: str
    severity: Literal["blocker", "warning"]
    message: str


class ShopifyProjection(BaseModel):
    title: str
    description_html: str
    vendor: str | None
    product_type: str
    handle: str | None
    seo: dict[str, str | None]
    options: list[dict[str, object]]
    variants: list[dict[str, object]]
    metafields: dict[str, object]
    media: list[dict[str, object]]
    external_status: Literal["draft"] = "draft"
    inventory_quantities: list[object] = Field(default_factory=list)


class ShopifyPublicationReadiness(BaseModel):
    organization_id: UUID
    product_id: UUID
    connection_id: UUID | None
    product_truth_id: UUID | None
    product_truth_version: int | None
    listing_version_id: UUID | None
    listing_version: int | None
    projection: ShopifyProjection | None
    projection_hash: str | None
    status: Literal["not_ready", "conditional", "ready"]
    blockers: list[ReadinessIssue]
    warnings: list[ReadinessIssue]
    media_status: Literal["ready", "optional", "missing_blocking"]
    publication_status: str
    authorization_status: str
    external_resource_id: UUID | None
    external_product_id: str | None
    drift_status: str
    operation: Literal["create", "update"]
    next_action: str


class PublicationRequestCreate(BaseModel):
    organization_id: UUID
    connection_id: UUID
    reason: str = Field(min_length=3, max_length=5000)


class PublicationAuthorization(BaseModel):
    organization_id: UUID
    approval_request_id: UUID


class PublicationExecutionRequest(BaseModel):
    organization_id: UUID


class ShopifyPublicationRead(ReadModel):
    organization_id: UUID
    connection_id: UUID
    product_id: UUID
    product_truth_id: UUID
    product_truth_version: int
    listing_version_id: UUID
    listing_version: int
    projection: dict[str, object]
    projection_hash: str
    operation: str
    status: str
    approval_request_id: UUID | None
    idempotency_key: str
    requested_by: UUID
    authorized_by: UUID | None
    authorized_at: datetime | None
    execution_requested_by: UUID | None
    executed_at: datetime | None
    attempts: int
    last_error_category: str | None
    last_error_message: str | None


class ShopifyExternalResourceRead(ReadModel):
    organization_id: UUID
    connection_id: UUID
    product_id: UUID
    external_product_id: str
    external_variant_ids: list[str]
    external_status: str
    source_listing_version_id: UUID
    last_publication_id: UUID
    last_synced_at: datetime
    admin_reference: str | None
    active: bool


class ReconciliationRequest(BaseModel):
    organization_id: UUID


class ShopifyReconciliationRead(ReadModel):
    organization_id: UUID
    connection_id: UUID
    product_id: UUID
    external_resource_id: UUID | None
    publication_id: UUID | None
    status: str
    commerce_hash: str | None
    external_hash: str | None
    differences: list[str]
    checked_at: datetime
    checked_by: UUID


class ShopifyWorkspaceRead(BaseModel):
    connections: list[ShopifyConnectionRead]
    products: list[ShopifyPublicationReadiness]
    publications: list[ShopifyPublicationRead]
    resources: list[ShopifyExternalResourceRead]
    reconciliations: list[ShopifyReconciliationRead]
