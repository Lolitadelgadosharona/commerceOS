import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from commerce_os.shared.schemas import ReadModel

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            raise ValueError("slug must be lowercase kebab-case")
        return value


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class OrganizationRead(ReadModel):
    name: str
    slug: str
    is_active: bool


class ProjectCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern=r"^(active|paused|completed|archived)$")


class ProjectRead(ReadModel):
    organization_id: UUID
    name: str
    slug: str
    status: str


class CustomerIdentityCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    identity_type: str = Field(min_length=1, max_length=50)
    normalized_value: str = Field(min_length=1, max_length=320)
    source: str = Field(min_length=1, max_length=100)
    provenance: dict[str, object] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)


class ApprovalCreate(BaseModel):
    organization_id: UUID
    action_type: str = Field(min_length=1, max_length=100)
    subject_type: str = Field(min_length=1, max_length=100)
    subject_id: UUID
    requested_by: str = Field(min_length=1, max_length=200)
    policy_version: str = Field(min_length=1, max_length=50)
    idempotency_key: str = Field(min_length=1, max_length=255)


class CommercialPolicyCreate(BaseModel):
    organization_id: UUID
    policy_key: str = Field(min_length=1, max_length=100)
    policy_version: str = Field(min_length=1, max_length=50)
    rules: dict[str, object]
