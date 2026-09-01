from datetime import UTC, datetime
from typing import Annotated, TypeVar
from uuid import UUID

from commerce_os.build.models import Product
from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.audit import AuditService
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import ApprovalRequest, ApprovalStatus, PrincipalType, User
from commerce_os.intelligence.errors import IntelligenceNotFoundError
from commerce_os.intelligence.product_models import ProductEconomicInputProvenance
from commerce_os.intelligence.product_schemas import (
    ProductEconomicInputCreate,
    ProductEconomicInputRead,
)
from commerce_os.intelligence.product_services import ProductEconomicsService
from commerce_os.intelligence.supplier_models import (
    ApprovedProductSupplier,
    ProductSupplierMatch,
    SupplierDecisionRecord,
    SupplierEvaluation,
    SupplierEvidence,
    SupplierProfile,
    SupplierProfileStatus,
    SupplierQuote,
    SupplierRisk,
)
from commerce_os.intelligence.supplier_schemas import (
    ApprovedProductSupplierRead,
    ProductSupplierMatchCreate,
    ProductSupplierMatchRead,
    QuoteEconomicsLinkCreate,
    SupplierComparisonRead,
    SupplierComparisonRow,
    SupplierDecisionCreate,
    SupplierDecisionRead,
    SupplierDetailRead,
    SupplierEvaluationCreate,
    SupplierEvaluationRead,
    SupplierEvidenceCreate,
    SupplierEvidenceRead,
    SupplierProfileCreate,
    SupplierProfileRead,
    SupplierProfileUpdate,
    SupplierQualificationRead,
    SupplierQuoteCreate,
    SupplierQuoteRead,
    SupplierRiskCreate,
    SupplierRiskRead,
    SupplierSelectionExecute,
    SupplierSelectionRequest,
    SupplyReadinessRead,
)
from commerce_os.intelligence.supplier_services import (
    ProductSupplierMatchService,
    SupplierDecisionService,
    SupplierEvaluationService,
    SupplierProfileService,
    SupplierRiskService,
    get_scoped_supplier,
)
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.supplier_governance import product_supply_readiness, qualify_supplier

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _get(session: Session, model: type[ModelT], entity_id: UUID) -> ModelT:
    entity = session.get(model, entity_id)
    if entity is None:
        raise IntelligenceNotFoundError("Supplier intelligence resource was not found.")
    return entity


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    return list(
        session.scalars(
            select(model)
            .where(model.organization_id == organization_id)  # type: ignore[attr-defined]
            .order_by(model.created_at.desc())  # type: ignore[attr-defined]
        )
    )


def _actor_id(request: Request) -> UUID:
    actor = getattr(request.state, "actor", None)
    if actor is not None:
        return UUID(str(actor.id))
    raw = request.headers.get("X-Actor-ID")
    if raw is None:
        raise ApiError(401, "actor_required", "Authenticated actor context is required.")
    return UUID(raw)


def _scoped(
    session: Session, model: type[ModelT], entity_id: UUID, organization_id: UUID
) -> ModelT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise ApiError(404, "not_found", "Supplier intelligence resource was not found.")
    return entity


@router.post("/suppliers", response_model=SupplierProfileRead, status_code=201, tags=["suppliers"])
def create_supplier(payload: SupplierProfileCreate, session: SessionDependency) -> SupplierProfile:
    return SupplierProfileService(session).create(payload)


@router.get("/suppliers", response_model=list[SupplierProfileRead], tags=["suppliers"])
def list_suppliers(organization_id: UUID, session: SessionDependency) -> list[SupplierProfile]:
    return _list(session, SupplierProfile, organization_id)


@router.get("/suppliers/{supplier_id}", response_model=SupplierProfileRead, tags=["suppliers"])
def get_supplier(
    supplier_id: UUID, organization_id: UUID, session: SessionDependency
) -> SupplierProfile:
    return get_scoped_supplier(session, supplier_id, organization_id)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierProfileRead, tags=["suppliers"])
def transition_supplier(
    supplier_id: UUID,
    organization_id: UUID,
    payload: SupplierProfileUpdate,
    session: SessionDependency,
) -> SupplierProfile:
    supplier = get_scoped_supplier(session, supplier_id, organization_id)
    return SupplierProfileService(session).transition(
        supplier, SupplierProfileStatus(payload.status)
    )


@router.post(
    "/supplier-evaluations",
    response_model=SupplierEvaluationRead,
    status_code=201,
    tags=["supplier_evaluations"],
)
def create_evaluation(
    payload: SupplierEvaluationCreate, session: SessionDependency
) -> SupplierEvaluation:
    return SupplierEvaluationService(session).create(payload)


@router.get(
    "/supplier-evaluations",
    response_model=list[SupplierEvaluationRead],
    tags=["supplier_evaluations"],
)
def list_evaluations(organization_id: UUID, session: SessionDependency) -> list[SupplierEvaluation]:
    return _list(session, SupplierEvaluation, organization_id)


@router.post(
    "/supplier-risks", response_model=SupplierRiskRead, status_code=201, tags=["supplier_risks"]
)
def create_risk(payload: SupplierRiskCreate, session: SessionDependency) -> SupplierRisk:
    return SupplierRiskService(session).create(payload)


@router.get("/supplier-risks", response_model=list[SupplierRiskRead], tags=["supplier_risks"])
def list_risks(organization_id: UUID, session: SessionDependency) -> list[SupplierRisk]:
    return _list(session, SupplierRisk, organization_id)


@router.post(
    "/product-supplier-matches",
    response_model=ProductSupplierMatchRead,
    status_code=201,
    tags=["product_supplier_matches"],
)
def create_match(
    payload: ProductSupplierMatchCreate, session: SessionDependency
) -> ProductSupplierMatch:
    return ProductSupplierMatchService(session).create(payload)


@router.get(
    "/product-supplier-matches",
    response_model=list[ProductSupplierMatchRead],
    tags=["product_supplier_matches"],
)
def list_matches(organization_id: UUID, session: SessionDependency) -> list[ProductSupplierMatch]:
    return _list(session, ProductSupplierMatch, organization_id)


@router.post(
    "/supplier-decisions",
    response_model=SupplierDecisionRead,
    status_code=201,
    tags=["supplier_decisions"],
)
def create_decision(
    payload: SupplierDecisionCreate, session: SessionDependency
) -> SupplierDecisionRecord:
    return SupplierDecisionService(session).create(payload)


@router.get(
    "/supplier-decisions", response_model=list[SupplierDecisionRead], tags=["supplier_decisions"]
)
def list_decisions(
    organization_id: UUID, session: SessionDependency
) -> list[SupplierDecisionRecord]:
    return _list(session, SupplierDecisionRecord, organization_id)


@router.post("/supplier-evidence", response_model=SupplierEvidenceRead, status_code=201)
def create_supplier_evidence(
    payload: SupplierEvidenceCreate, session: SessionDependency
) -> SupplierEvidence:
    _scoped(session, SupplierProfile, payload.supplier_id, payload.organization_id)
    item = SupplierEvidence(**payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/supplier-evidence", response_model=list[SupplierEvidenceRead])
def list_supplier_evidence(
    organization_id: UUID, session: SessionDependency, supplier_id: UUID | None = None
) -> list[SupplierEvidence]:
    statement = select(SupplierEvidence).where(SupplierEvidence.organization_id == organization_id)
    if supplier_id:
        statement = statement.where(SupplierEvidence.supplier_id == supplier_id)
    return list(session.scalars(statement.order_by(SupplierEvidence.created_at.desc())))


@router.post("/supplier-quotes", response_model=SupplierQuoteRead, status_code=201)
def create_supplier_quote(
    payload: SupplierQuoteCreate, session: SessionDependency
) -> SupplierQuote:
    _scoped(session, SupplierProfile, payload.supplier_id, payload.organization_id)
    _scoped(session, Product, payload.product_id, payload.organization_id)
    quote = SupplierQuote(**payload.model_dump())
    session.add(quote)
    session.commit()
    session.refresh(quote)
    return quote


@router.get("/supplier-quotes", response_model=list[SupplierQuoteRead])
def list_supplier_quotes(
    organization_id: UUID,
    session: SessionDependency,
    supplier_id: UUID | None = None,
    product_id: UUID | None = None,
) -> list[SupplierQuote]:
    statement = select(SupplierQuote).where(SupplierQuote.organization_id == organization_id)
    if supplier_id:
        statement = statement.where(SupplierQuote.supplier_id == supplier_id)
    if product_id:
        statement = statement.where(SupplierQuote.product_id == product_id)
    return list(session.scalars(statement.order_by(SupplierQuote.quote_date.desc())))


@router.post(
    "/supplier-quotes/{quote_id}/economic-provenance",
    response_model=ProductEconomicInputRead,
)
def link_quote_to_economics(
    quote_id: UUID, payload: QuoteEconomicsLinkCreate, session: SessionDependency
) -> ProductEconomicInputProvenance:
    quote = _scoped(session, SupplierQuote, quote_id, payload.organization_id)
    if quote.unit_price is None:
        raise ApiError(409, "quote_price_unknown", "A numeric quoted unit price is required.")
    return ProductEconomicsService(session).upsert_input(
        ProductEconomicInputCreate(
            organization_id=payload.organization_id,
            product_economics_id=payload.product_economics_id,
            metric="estimated_product_cost",
            value=quote.unit_price,
            classification="quoted",
            source=f"supplier_quote:{quote.id}",
            confidence=payload.confidence if payload.confidence is not None else quote.confidence,
            as_of=datetime.combine(quote.quote_date, datetime.min.time(), tzinfo=UTC),
            evidence_reference=quote.evidence_reference or f"supplier_quote:{quote.id}",
            notes="Supplier quote input; advisory cost evidence, not actual Finance truth.",
        )
    )


@router.get("/suppliers/{supplier_id}/qualification", response_model=SupplierQualificationRead)
def supplier_qualification(
    supplier_id: UUID, product_id: UUID, organization_id: UUID, session: SessionDependency
) -> SupplierQualificationRead:
    try:
        return qualify_supplier(session, organization_id, supplier_id, product_id)
    except LookupError as error:
        raise ApiError(404, "not_found", str(error)) from error


@router.get("/products/{product_id}/supplier-comparison", response_model=SupplierComparisonRead)
def supplier_comparison(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> SupplierComparisonRead:
    matches = list(
        session.scalars(
            select(ProductSupplierMatch).where(
                ProductSupplierMatch.organization_id == organization_id,
                ProductSupplierMatch.product_id == product_id,
            )
        )
    )
    rows: list[SupplierComparisonRow] = []
    for match in matches:
        supplier = _scoped(session, SupplierProfile, match.supplier_id, organization_id)
        evaluation = session.scalar(
            select(SupplierEvaluation)
            .where(
                SupplierEvaluation.organization_id == organization_id,
                SupplierEvaluation.supplier_id == supplier.id,
            )
            .order_by(SupplierEvaluation.created_at.desc())
        )
        quote = session.scalar(
            select(SupplierQuote)
            .where(
                SupplierQuote.organization_id == organization_id,
                SupplierQuote.supplier_id == supplier.id,
                SupplierQuote.product_id == product_id,
            )
            .order_by(SupplierQuote.quote_date.desc())
        )
        risks = list(
            session.scalars(
                select(SupplierRisk).where(
                    SupplierRisk.organization_id == organization_id,
                    SupplierRisk.supplier_id == supplier.id,
                )
            )
        )
        rows.append(
            SupplierComparisonRow(
                supplier=supplier,
                match=match,
                evaluation=evaluation,
                quote=quote,
                risks=risks,
                qualification=qualify_supplier(session, organization_id, supplier.id, product_id),
            )
        )
    return SupplierComparisonRead(organization_id=organization_id, product_id=product_id, rows=rows)


@router.get("/products/{product_id}/supply-readiness", response_model=SupplyReadinessRead)
def supply_readiness(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> SupplyReadinessRead:
    return product_supply_readiness(session, organization_id, product_id)


@router.post(
    "/suppliers/{supplier_id}/selection-request",
    response_model=ApprovedProductSupplierRead,
    status_code=201,
)
def request_supplier_selection(
    supplier_id: UUID,
    payload: SupplierSelectionRequest,
    request: Request,
    session: SessionDependency,
) -> ApprovedProductSupplier:
    supplier = _scoped(session, SupplierProfile, supplier_id, payload.organization_id)
    state = qualify_supplier(session, payload.organization_id, supplier_id, payload.product_id)
    if not state.ready:
        raise ApiError(409, "supplier_not_qualified", state.next_action)
    existing = session.scalar(
        select(ApprovedProductSupplier).where(
            ApprovedProductSupplier.organization_id == payload.organization_id,
            ApprovedProductSupplier.product_id == payload.product_id,
            ApprovedProductSupplier.supplier_id == supplier_id,
        )
    )
    if existing:
        return existing
    actor = _actor_id(request)
    approval = ApprovalWorkflowService(session).request(
        organization_id=payload.organization_id,
        project_id=None,
        requester_id=actor,
        object_type="product_supplier_selection",
        object_id=supplier_id,
        requested_action="supplier.select",
        reason=payload.reason,
        commit=False,
    )
    relationship = ApprovedProductSupplier(
        organization_id=payload.organization_id,
        product_id=payload.product_id,
        supplier_id=supplier_id,
        source_candidate_id=payload.source_candidate_id,
        approval_request_id=approval.id,
        role=payload.role,
        status="pending",
    )
    session.add_all(
        [
            relationship,
            DecisionQueueItem(
                organization_id=payload.organization_id,
                title=f"Supplier selection: {supplier.name}",
                domain="governance",
                reason=payload.reason,
                priority="high",
                required_action="approve",
                status="pending",
                approval_request_id=approval.id,
            ),
        ]
    )
    session.commit()
    session.refresh(relationship)
    return relationship


@router.post(
    "/suppliers/{supplier_id}/approve-for-product", response_model=ApprovedProductSupplierRead
)
def execute_supplier_selection(
    supplier_id: UUID,
    payload: SupplierSelectionExecute,
    request: Request,
    session: SessionDependency,
) -> ApprovedProductSupplier:
    relationship = session.scalar(
        select(ApprovedProductSupplier)
        .where(
            ApprovedProductSupplier.organization_id == payload.organization_id,
            ApprovedProductSupplier.product_id == payload.product_id,
            ApprovedProductSupplier.supplier_id == supplier_id,
            ApprovedProductSupplier.approval_request_id == payload.approval_request_id,
        )
        .with_for_update()
    )
    if relationship is None:
        raise ApiError(
            409, "selection_request_required", "Supplier selection request was not found."
        )
    if relationship.status == "approved":
        return relationship
    state = qualify_supplier(session, payload.organization_id, supplier_id, payload.product_id)
    if not state.ready:
        raise ApiError(409, "supplier_not_qualified", state.next_action)
    approval = session.get(ApprovalRequest, payload.approval_request_id)
    if (
        approval is None
        or approval.status != ApprovalStatus.APPROVED
        or approval.requested_action != "supplier.select"
        or approval.object_id != supplier_id
    ):
        raise ApiError(
            409, "supplier_approval_required", "Approved supplier selection is required."
        )
    actor_id = _actor_id(request)
    actor = session.get(User, actor_id)
    if (
        actor is None
        or actor.organization_id != payload.organization_id
        or actor.principal_type != PrincipalType.HUMAN
    ):
        raise ApiError(403, "human_authority_required", "An in-scope human actor is required.")
    relationship.status = "approved"
    relationship.role = payload.role
    relationship.approved_by = actor.id
    relationship.approved_at = datetime.now(UTC)
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor.id,
        action="supplier.approved_for_product",
        entity_type="approved_product_supplier",
        entity_id=relationship.id,
        metadata={
            "product_id": str(payload.product_id),
            "supplier_id": str(supplier_id),
            "approval_request_id": str(approval.id),
            "authority_boundary": "selection_only_no_purchase",
        },
    )
    session.commit()
    session.refresh(relationship)
    return relationship


@router.get("/approved-product-suppliers", response_model=list[ApprovedProductSupplierRead])
def list_approved_product_suppliers(
    organization_id: UUID, session: SessionDependency, product_id: UUID | None = None
) -> list[ApprovedProductSupplier]:
    statement = select(ApprovedProductSupplier).where(
        ApprovedProductSupplier.organization_id == organization_id
    )
    if product_id:
        statement = statement.where(ApprovedProductSupplier.product_id == product_id)
    return list(session.scalars(statement.order_by(ApprovedProductSupplier.created_at.desc())))


@router.get("/suppliers/{supplier_id}/intelligence", response_model=SupplierDetailRead)
def supplier_detail(
    supplier_id: UUID, organization_id: UUID, session: SessionDependency
) -> SupplierDetailRead:
    supplier = _scoped(session, SupplierProfile, supplier_id, organization_id)
    matches = list(
        session.scalars(
            select(ProductSupplierMatch).where(
                ProductSupplierMatch.organization_id == organization_id,
                ProductSupplierMatch.supplier_id == supplier_id,
            )
        )
    )
    evidence = list(
        session.scalars(
            select(SupplierEvidence).where(
                SupplierEvidence.organization_id == organization_id,
                SupplierEvidence.supplier_id == supplier_id,
            )
        )
    )
    quotes = list(
        session.scalars(
            select(SupplierQuote).where(
                SupplierQuote.organization_id == organization_id,
                SupplierQuote.supplier_id == supplier_id,
            )
        )
    )
    evaluations = list(
        session.scalars(
            select(SupplierEvaluation).where(
                SupplierEvaluation.organization_id == organization_id,
                SupplierEvaluation.supplier_id == supplier_id,
            )
        )
    )
    risks = list(
        session.scalars(
            select(SupplierRisk).where(
                SupplierRisk.organization_id == organization_id,
                SupplierRisk.supplier_id == supplier_id,
            )
        )
    )
    approved = list(
        session.scalars(
            select(ApprovedProductSupplier).where(
                ApprovedProductSupplier.organization_id == organization_id,
                ApprovedProductSupplier.supplier_id == supplier_id,
            )
        )
    )
    qualifications = [
        qualify_supplier(session, organization_id, supplier_id, match.product_id)
        for match in matches
    ]
    next_action = (
        qualifications[0].next_action
        if qualifications
        else "Link this supplier to a Product before qualification."
    )
    return SupplierDetailRead(
        supplier=supplier,
        products=matches,
        evidence=evidence,
        quotes=quotes,
        evaluations=evaluations,
        risks=risks,
        approved_relationships=approved,
        qualifications=qualifications,
        next_action=next_action,
    )
