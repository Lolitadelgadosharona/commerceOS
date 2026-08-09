from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class CustomerCreate(BaseModel):
    organization_id: UUID
    display_name: str = Field(min_length=1, max_length=200)
    attributes: dict[str, object] = Field(default_factory=dict)


class CustomerUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern=r"^(active|inactive|merged)$")


class CustomerRead(ReadModel):
    organization_id: UUID
    display_name: str
    status: str
    attributes: dict[str, object]


class SalesOpportunityCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    customer_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    owner_ref: str | None = Field(default=None, max_length=200)


class SalesOpportunityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    stage: str | None = Field(
        default=None, pattern=r"^(created|qualified|proposal|negotiation|won|lost)$"
    )
    owner_ref: str | None = Field(default=None, max_length=200)


class SalesOpportunityRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    customer_id: UUID | None
    name: str
    stage: str
    owner_ref: str | None


class BrandCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class StoreCreate(BaseModel):
    organization_id: UUID
    brand_id: UUID
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ConversationCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID | None = None
    channel: str = Field(min_length=1, max_length=50)
    purpose: str = Field(pattern=r"^(b2c|b2b|support)$")
    policy_version: str = Field(min_length=1, max_length=50)


class MessageMetadataCreate(BaseModel):
    conversation_id: UUID
    direction: str = Field(pattern=r"^(inbound|outbound)$")
    external_message_id: str | None = Field(default=None, max_length=255)
    content_reference: str | None = None
    content_hash: str | None = Field(default=None, max_length=128)
