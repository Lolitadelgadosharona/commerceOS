import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator, model_validator

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
    provider: str = Field(min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    external_identifier: str = Field(min_length=1, max_length=320)
    provenance: dict[str, object] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0, le=1)
    verification_status: Literal["unverified", "verified", "rejected"] = "unverified"


class CustomerIdentityRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    provider: str
    external_identifier: str
    confidence_score: float
    verification_status: str
    provenance: dict[str, object]


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


class UserCreate(BaseModel):
    organization_id: UUID
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=200)
    password: SecretStr = Field(min_length=12, max_length=1024)
    principal_type: Literal["human", "service"] = "human"


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    status: Literal["active", "suspended", "disabled"] | None = None


class UserRead(ReadModel):
    organization_id: UUID
    email: EmailStr
    display_name: str
    status: str
    principal_type: str


class RoleCreate(BaseModel):
    organization_id: UUID
    name: Literal["owner", "approver", "operator", "viewer"]
    description: str = Field(default="", max_length=500)
    grants_human_approval_authority: bool = False


class RoleUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class RoleRead(ReadModel):
    organization_id: UUID
    name: str
    description: str
    grants_human_approval_authority: bool
    is_active: bool


class PermissionCreate(BaseModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$", max_length=150)
    resource: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    is_human_approval_permission: bool = False


class PermissionUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=500)


class PermissionRead(ReadModel):
    key: str
    resource: str
    action: str
    description: str
    is_human_approval_permission: bool


class AIActionPolicyCreate(BaseModel):
    organization_id: UUID
    action_type: Literal[
        "recommend",
        "classify",
        "draft_response",
        "send_message",
        "issue_refund",
        "change_price",
        "create_discount",
    ]
    allowed: bool | None = None
    requires_approval: bool | None = None
    domain: Literal["decision", "operations", "governance", "finance", "build"]

    @model_validator(mode="after")
    def safe_defaults(self) -> "AIActionPolicyCreate":
        advisory = self.action_type in {"recommend", "classify"}
        if self.allowed is None:
            self.allowed = advisory
        if self.requires_approval is None:
            self.requires_approval = not advisory
        if advisory and (not self.allowed or self.requires_approval):
            raise ValueError("recommend/classify must remain allowed advisory actions")
        if not advisory and not self.requires_approval:
            raise ValueError("non-advisory AI actions require approval")
        return self


class AIActionPolicyRead(ReadModel):
    organization_id: UUID
    action_type: str
    allowed: bool
    requires_approval: bool
    domain: str


class RolePermissionCreate(BaseModel):
    permission_id: UUID


class UserRoleCreate(BaseModel):
    user_id: UUID
    role_id: UUID
    organization_id: UUID
    project_id: UUID | None = None


class UserRoleRead(ReadModel):
    user_id: UUID
    role_id: UUID
    organization_id: UUID
    project_id: UUID | None
    assigned_by: UUID
    assigned_at: datetime
    revoked_at: datetime | None
    revoked_by: UUID | None
    revocation_reason: str | None


class RevokeRoleRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ApprovalRequestCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    object_type: str = Field(min_length=1, max_length=100)
    object_id: UUID
    requested_action: str = Field(min_length=1, max_length=150)
    reason: str = Field(min_length=1, max_length=5000)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=1, max_length=5000)


class ApprovalCancellation(BaseModel):
    reason: str = Field(min_length=1, max_length=5000)


class ApprovalRequestRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    requester_id: UUID
    object_type: str
    object_id: UUID
    requested_action: str
    reason: str
    status: str
    approver_id: UUID | None
    decision_time: datetime | None
    decision_reason: str | None


class AuditLogRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    organization_id: UUID
    actor_type: str
    actor_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID
    timestamp: datetime
    event_metadata: dict[str, object]
