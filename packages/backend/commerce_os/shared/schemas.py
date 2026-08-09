from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime


class NamedCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class NamedUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
