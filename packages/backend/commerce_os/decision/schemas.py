from uuid import UUID

from pydantic import BaseModel, Field

from commerce_os.shared.schemas import ReadModel


class VentureOpportunityCreate(BaseModel):
    organization_id: UUID
    project_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    thesis: str | None = Field(default=None, max_length=5000)


class VentureOpportunityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    thesis: str | None = Field(default=None, max_length=5000)
    stage: str | None = Field(
        default=None, pattern=r"^(observed|researching|validated|approved|rejected)$"
    )


class VentureOpportunityRead(ReadModel):
    organization_id: UUID
    project_id: UUID | None
    name: str
    thesis: str | None
    stage: str
