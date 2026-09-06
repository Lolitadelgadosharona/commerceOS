from typing import Annotated
from uuid import UUID

from commerce_os.build.models import Product
from commerce_os.governance.models import User
from commerce_os.operations.shopify_adapter import (
    DeterministicShopifyAdapter,
    ShopifyGraphQLAdapter,
)
from commerce_os.operations.shopify_models import (
    ShopifyConnection,
    ShopifyExternalResource,
    ShopifyPublication,
    ShopifyReconciliation,
)
from commerce_os.operations.shopify_schemas import (
    ConnectionValidationRequest,
    PublicationAuthorization,
    PublicationExecutionRequest,
    PublicationRequestCreate,
    ReconciliationRequest,
    ShopifyConnectionCreate,
    ShopifyConnectionRead,
    ShopifyPublicationRead,
    ShopifyPublicationReadiness,
    ShopifyReconciliationRead,
    ShopifyWorkspaceRead,
)
from commerce_os.shared.database import get_session
from commerce_os.shopify_services import ShopifyChannelService
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError

router = APIRouter(prefix="/shopify")
SessionDependency = Annotated[Session, Depends(get_session)]


def actor_id(request: Request, session: Session, organization_id: UUID) -> UUID:
    actor = getattr(request.state, "actor", None)
    value = None if actor is None else UUID(str(actor.id))
    if value is None and getattr(request.app.state, "auth_test_bypass", False):
        raw = request.headers.get("X-Actor-ID")
        value = None if raw is None else UUID(raw)
    user = None if value is None else session.get(User, value)
    if user is None:
        raise ApiError(401, "actor_required", "Authenticated actor is required.")
    if user.organization_id != organization_id:
        raise ApiError(403, "organization_scope", "Actor is outside this organization.")
    return user.id


def connection_read(item: ShopifyConnection) -> ShopifyConnectionRead:
    return ShopifyConnectionRead(
        id=item.id,
        created_at=item.created_at,
        updated_at=item.updated_at,
        version=item.version,
        organization_id=item.organization_id,
        store_id=item.store_id,
        store_domain=item.store_domain,
        display_name=item.display_name,
        authentication_mode=item.authentication_mode,
        credential_configured=bool(item.credential_reference),
        required_scopes=item.required_scopes,
        granted_scopes=item.granted_scopes,
        api_version=item.api_version,
        status=item.status,
        publication_policy=item.publication_policy,
        created_by=item.created_by,
        validated_at=item.validated_at,
        last_error_category=item.last_error_category,
        last_error_message=item.last_error_message,
    )


def translate(exc: Exception) -> ApiError:
    if isinstance(exc, PermissionError):
        return ApiError(403, "human_authority_required", str(exc))
    if isinstance(exc, LookupError):
        return ApiError(404, "not_found", str(exc))
    return ApiError(409, "shopify_governance", str(exc))


@router.post("/connections", response_model=ShopifyConnectionRead, status_code=201)
def create_connection(
    payload: ShopifyConnectionCreate, request: Request, session: SessionDependency
) -> ShopifyConnectionRead:
    try:
        item = ShopifyChannelService(session).create_connection(
            payload, actor_id(request, session, payload.organization_id)
        )
        return connection_read(item)
    except Exception as exc:
        raise translate(exc) from exc


@router.get("/connections", response_model=list[ShopifyConnectionRead])
def list_connections(
    organization_id: UUID, session: SessionDependency
) -> list[ShopifyConnectionRead]:
    return [
        connection_read(item)
        for item in session.scalars(
            select(ShopifyConnection)
            .where(ShopifyConnection.organization_id == organization_id)
            .order_by(ShopifyConnection.created_at.desc())
        )
    ]


@router.post("/connections/{connection_id}/validate", response_model=ShopifyConnectionRead)
def validate_connection(
    connection_id: UUID,
    payload: ConnectionValidationRequest,
    request: Request,
    session: SessionDependency,
) -> ShopifyConnectionRead:
    service = ShopifyChannelService(session)
    try:
        connection = service.connection(connection_id, payload.organization_id)
        adapter = (
            DeterministicShopifyAdapter(connection.store_domain)
            if connection.authentication_mode == "mock"
            else ShopifyGraphQLAdapter(
                store_domain=connection.store_domain,
                api_version=connection.api_version,
                credential_reference=connection.credential_reference,
            )
        )
        item = service.validate_connection(
            connection, actor_id(request, session, payload.organization_id), adapter
        )
        return connection_read(item)
    except Exception as exc:
        raise translate(exc) from exc


@router.get("/products/{product_id}/readiness", response_model=ShopifyPublicationReadiness)
def publication_readiness(
    product_id: UUID,
    organization_id: UUID,
    session: SessionDependency,
    connection_id: UUID | None = None,
) -> ShopifyPublicationReadiness:
    try:
        return ShopifyChannelService(session).readiness(organization_id, product_id, connection_id)
    except Exception as exc:
        raise translate(exc) from exc


@router.post(
    "/products/{product_id}/publication-requests",
    response_model=ShopifyPublicationRead,
    status_code=201,
)
def request_publication(
    product_id: UUID,
    payload: PublicationRequestCreate,
    request: Request,
    session: SessionDependency,
) -> ShopifyPublication:
    try:
        return ShopifyChannelService(session).request_publication(
            product_id, payload, actor_id(request, session, payload.organization_id)
        )
    except Exception as exc:
        raise translate(exc) from exc


@router.post("/publications/{publication_id}/authorize", response_model=ShopifyPublicationRead)
def authorize_publication(
    publication_id: UUID,
    payload: PublicationAuthorization,
    request: Request,
    session: SessionDependency,
) -> ShopifyPublication:
    try:
        return ShopifyChannelService(session).authorize(
            publication_id,
            payload.organization_id,
            payload.approval_request_id,
            actor_id(request, session, payload.organization_id),
        )
    except Exception as exc:
        raise translate(exc) from exc


@router.post("/publications/{publication_id}/execute", response_model=ShopifyPublicationRead)
def execute_publication(
    publication_id: UUID,
    payload: PublicationExecutionRequest,
    request: Request,
    session: SessionDependency,
) -> ShopifyPublication:
    try:
        return ShopifyChannelService(session).queue_execution(
            publication_id,
            payload.organization_id,
            actor_id(request, session, payload.organization_id),
        )
    except Exception as exc:
        raise translate(exc) from exc


@router.post(
    "/connections/{connection_id}/products/{product_id}/reconcile",
    response_model=ShopifyReconciliationRead,
)
def reconcile(
    connection_id: UUID,
    product_id: UUID,
    payload: ReconciliationRequest,
    request: Request,
    session: SessionDependency,
) -> ShopifyReconciliation:
    service = ShopifyChannelService(session)
    try:
        connection = service.connection(connection_id, payload.organization_id)
        if connection.authentication_mode == "mock":
            raise ValueError("Mock reconciliation is exercised only through deterministic tests.")
        adapter = ShopifyGraphQLAdapter(
            store_domain=connection.store_domain,
            api_version=connection.api_version,
            credential_reference=connection.credential_reference,
        )
        return service.reconcile(
            product_id,
            connection_id,
            payload.organization_id,
            actor_id(request, session, payload.organization_id),
            adapter,
        )
    except Exception as exc:
        raise translate(exc) from exc


@router.get("/workspace", response_model=ShopifyWorkspaceRead)
def workspace(organization_id: UUID, session: SessionDependency) -> ShopifyWorkspaceRead:
    connections = list(
        session.scalars(
            select(ShopifyConnection).where(ShopifyConnection.organization_id == organization_id)
        )
    )
    selected = connections[0] if connections else None
    service = ShopifyChannelService(session)
    products = list(
        session.scalars(select(Product).where(Product.organization_id == organization_id))
    )
    return ShopifyWorkspaceRead(
        connections=[connection_read(item) for item in connections],
        products=[
            service.readiness(
                organization_id, product.id, None if selected is None else selected.id
            )
            for product in products
        ],
        publications=list(
            session.scalars(
                select(ShopifyPublication).where(
                    ShopifyPublication.organization_id == organization_id
                )
            )
        ),
        resources=list(
            session.scalars(
                select(ShopifyExternalResource).where(
                    ShopifyExternalResource.organization_id == organization_id
                )
            )
        ),
        reconciliations=list(
            session.scalars(
                select(ShopifyReconciliation)
                .where(ShopifyReconciliation.organization_id == organization_id)
                .order_by(ShopifyReconciliation.checked_at.desc())
            )
        ),
    )
