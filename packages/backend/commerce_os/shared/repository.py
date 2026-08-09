from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from commerce_os.shared.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def list(self, *, limit: int = 100) -> list[ModelT]:
        statement: Select[tuple[ModelT]] = select(self.model).limit(limit)
        return list(self.session.scalars(statement))

    def get(self, entity_id: UUID) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def create(self, values: dict[str, Any]) -> ModelT:
        entity = self.model(**values)
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: ModelT, values: dict[str, Any]) -> ModelT:
        for key, value in values.items():
            if value is not None:
                setattr(entity, key, value)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)
        self.session.commit()
