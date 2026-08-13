from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class IdentityLinkCreate(BaseModel):
    organization_id: UUID
    customer_id: UUID
    identity_type: Literal["email", "social", "website", "chat", "other"]
    external_reference: str = Field(min_length=1, max_length=500)
    source: str = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0, le=1)
    status: Literal["observed", "verified", "rejected"] = "observed"


class IdentityLinkRead(ReadModel):
    organization_id: UUID
    customer_id: UUID
    identity_type: str
    external_reference: str
    source: str
    confidence: float
    status: str
