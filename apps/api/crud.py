from typing import Annotated, Generic, TypeVar
from uuid import UUID

from commerce_os.shared.database import Base, get_session
from commerce_os.shared.repository import Repository
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.errors import ApiError

ModelT = TypeVar("ModelT", bound=Base)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)
SessionDependency = Annotated[Session, Depends(get_session)]


class CrudRouter(Generic[ModelT, CreateT, UpdateT]):
    def __init__(
        self,
        *,
        prefix: str,
        tag: str,
        model: type[ModelT],
        create_schema: type[CreateT],
        update_schema: type[UpdateT],
        read_schema: type[BaseModel],
    ) -> None:
        router = APIRouter(prefix=prefix, tags=[tag])

        @router.get("", response_model=list[read_schema])  # type: ignore[valid-type]
        def list_entities(session: SessionDependency, limit: int = 100) -> list[ModelT]:
            if limit < 1 or limit > 100:
                raise ApiError(422, "invalid_limit", "limit must be between 1 and 100")
            return Repository(session, model).list(limit=limit)

        @router.post("", response_model=read_schema, status_code=status.HTTP_201_CREATED)
        def create_entity(payload: create_schema, session: SessionDependency) -> ModelT:  # type: ignore[valid-type]
            return Repository(session, model).create(payload.model_dump())  # type: ignore[attr-defined]

        @router.get("/{entity_id}", response_model=read_schema)
        def get_entity(entity_id: UUID, session: SessionDependency) -> ModelT:
            entity = Repository(session, model).get(entity_id)
            if entity is None:
                raise ApiError(404, "not_found", "The requested resource was not found.")
            return entity

        @router.patch("/{entity_id}", response_model=read_schema)
        def update_entity(
            entity_id: UUID,
            payload: update_schema,  # type: ignore[valid-type]
            session: SessionDependency,
        ) -> ModelT:
            repository = Repository(session, model)
            entity = repository.get(entity_id)
            if entity is None:
                raise ApiError(404, "not_found", "The requested resource was not found.")
            return repository.update(
                entity,
                payload.model_dump(exclude_unset=True),  # type: ignore[attr-defined]
            )

        @router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
        def delete_entity(entity_id: UUID, session: SessionDependency) -> Response:
            repository = Repository(session, model)
            entity = repository.get(entity_id)
            if entity is None:
                raise ApiError(404, "not_found", "The requested resource was not found.")
            repository.delete(entity)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        self.router = router
