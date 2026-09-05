from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from commerce_os.build.models import Product, ProductTruth
from commerce_os.build.readiness_models import (
    BuildRequirementPolicy,
    ProductBuildRequirement,
    ProductSample,
    SupplierCandidatePromotion,
    SupplierValidationArtifact,
)
from commerce_os.build.readiness_schemas import (
    BuildPackageRead,
    BuildRequirementPolicyCreate,
    BuildRequirementPolicyRead,
    CandidatePromotionCreate,
    CandidatePromotionRead,
    ProductBuildRequirementCreate,
    ProductBuildRequirementRead,
    ProductSampleCreate,
    ProductSampleRead,
    ProductSampleReview,
    SupplierValidationCreate,
    SupplierValidationRead,
)
from commerce_os.governance.audit import AuditService
from commerce_os.governance.models import PrincipalType, User
from commerce_os.intelligence.product_models import SupplierCandidate
from commerce_os.intelligence.supplier_models import (
    ApprovedProductSupplier,
    SupplierProfile,
    SupplierProfileStatus,
)
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.build_readiness import compose_build_package
from apps.api.errors import ApiError

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


def _actor(request: Request, session: Session, organization_id: UUID) -> User:
    actor = getattr(request.state, "actor", None)
    actor_id = None if actor is None else UUID(str(actor.id))
    if actor_id is None and getattr(request.app.state, "auth_test_bypass", False):
        raw_actor_id = request.headers.get("X-Actor-ID")
        actor_id = None if raw_actor_id is None else UUID(raw_actor_id)
    if actor_id is None:
        raise ApiError(401, "actor_required", "Authenticated actor context is required.")
    user = session.get(User, actor_id)
    if user is None or user.organization_id != organization_id:
        raise ApiError(403, "organization_scope", "Actor is outside this organization.")
    if user.principal_type != PrincipalType.HUMAN:
        raise ApiError(403, "human_authority_required", "A human must confirm this action.")
    return user


def _product(session: Session, organization_id: UUID, product_id: UUID) -> Product:
    product = session.get(Product, product_id)
    if product is None or product.organization_id != organization_id:
        raise ApiError(404, "not_found", "Product was not found in this organization.")
    return product


@router.post(
    "/supplier-candidates/{candidate_id}/promote",
    response_model=CandidatePromotionRead,
    status_code=201,
)
def promote_supplier_candidate(
    candidate_id: UUID,
    payload: CandidatePromotionCreate,
    request: Request,
    session: SessionDependency,
) -> SupplierCandidatePromotion:
    candidate = session.get(SupplierCandidate, candidate_id)
    if candidate is None or candidate.organization_id != payload.organization_id:
        raise ApiError(404, "not_found", "Supplier Candidate was not found in this organization.")
    existing = session.scalar(
        select(SupplierCandidatePromotion).where(
            SupplierCandidatePromotion.organization_id == payload.organization_id,
            SupplierCandidatePromotion.supplier_candidate_id == candidate_id,
        )
    )
    if existing:
        return existing
    actor = _actor(request, session, payload.organization_id)
    if payload.supplier_profile_id:
        supplier = session.get(SupplierProfile, payload.supplier_profile_id)
        if supplier is None or supplier.organization_id != payload.organization_id:
            raise ApiError(404, "not_found", "Supplier Profile was not found in this organization.")
    else:
        if not payload.name or not payload.country:
            raise ApiError(
                422,
                "verified_identity_required",
                "Name and country are required to create a canonical Supplier Profile.",
            )
        supplier = SupplierProfile(
            organization_id=payload.organization_id,
            name=payload.name,
            source_type=candidate.source_type,
            country=payload.country,
            capabilities=[],
            certifications=[],
            status=SupplierProfileStatus.EVALUATING,
        )
        session.add(supplier)
        session.flush()
    promotion = SupplierCandidatePromotion(
        organization_id=payload.organization_id,
        supplier_candidate_id=candidate.id,
        supplier_profile_id=supplier.id,
        confirmed_by=actor.id,
        confirmed_at=datetime.now(UTC),
    )
    session.add(promotion)
    session.flush()
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor.id,
        action="supplier_candidate.canonicalized",
        entity_type="supplier_candidate_promotion",
        entity_id=promotion.id,
        metadata={
            "candidate_id": str(candidate.id),
            "supplier_profile_id": str(supplier.id),
            "external_side_effect": False,
        },
    )
    session.commit()
    session.refresh(promotion)
    return promotion


@router.get(
    "/supplier-candidates/{candidate_id}/promotion", response_model=CandidatePromotionRead | None
)
def get_candidate_promotion(
    candidate_id: UUID, organization_id: UUID, session: SessionDependency
) -> SupplierCandidatePromotion | None:
    candidate = session.get(SupplierCandidate, candidate_id)
    if candidate is None or candidate.organization_id != organization_id:
        raise ApiError(404, "not_found", "Supplier Candidate was not found in this organization.")
    return session.scalar(
        select(SupplierCandidatePromotion).where(
            SupplierCandidatePromotion.organization_id == organization_id,
            SupplierCandidatePromotion.supplier_candidate_id == candidate_id,
        )
    )


@router.post(
    "/products/{product_id}/build-requirements",
    response_model=ProductBuildRequirementRead,
    status_code=201,
)
def create_build_requirement(
    product_id: UUID, payload: ProductBuildRequirementCreate, session: SessionDependency
) -> ProductBuildRequirement:
    _product(session, payload.organization_id, product_id)
    truth = session.get(ProductTruth, payload.product_truth_id)
    if (
        truth is None
        or truth.organization_id != payload.organization_id
        or truth.product_id != product_id
    ):
        raise ApiError(
            409,
            "truth_scope",
            "Build requirement must reference this Product's approved Product Truth.",
        )
    item = ProductBuildRequirement(product_id=product_id, **payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/products/{product_id}/build-policy", response_model=BuildRequirementPolicyRead)
def set_build_policy(
    product_id: UUID, payload: BuildRequirementPolicyCreate, session: SessionDependency
) -> BuildRequirementPolicy:
    _product(session, payload.organization_id, product_id)
    item = session.scalar(
        select(BuildRequirementPolicy).where(
            BuildRequirementPolicy.organization_id == payload.organization_id,
            BuildRequirementPolicy.product_id == product_id,
        )
    )
    values = payload.model_dump(exclude={"organization_id"})
    if item is None:
        item = BuildRequirementPolicy(
            organization_id=payload.organization_id, product_id=product_id, **values
        )
        session.add(item)
    else:
        for key, value in values.items():
            setattr(item, key, value)
    session.commit()
    session.refresh(item)
    return item


@router.post("/products/{product_id}/samples", response_model=ProductSampleRead, status_code=201)
def create_sample(
    product_id: UUID, payload: ProductSampleCreate, request: Request, session: SessionDependency
) -> ProductSample:
    _product(session, payload.organization_id, product_id)
    actor = _actor(request, session, payload.organization_id)
    supplier = session.get(SupplierProfile, payload.supplier_id)
    if supplier is None or supplier.organization_id != payload.organization_id:
        raise ApiError(404, "not_found", "Supplier was not found in this organization.")
    if payload.approved_product_supplier_id:
        relationship = session.get(ApprovedProductSupplier, payload.approved_product_supplier_id)
        if (
            relationship is None
            or relationship.organization_id != payload.organization_id
            or relationship.product_id != product_id
            or relationship.supplier_id != supplier.id
        ):
            raise ApiError(
                409,
                "relationship_scope",
                "Sample relationship does not match Product and Supplier.",
            )
    item = ProductSample(
        product_id=product_id,
        recorded_by=actor.id,
        review_status="unknown",
        review_dimensions={},
        **payload.model_dump(),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.post("/samples/{sample_id}/review", response_model=ProductSampleRead)
def review_sample(
    sample_id: UUID, payload: ProductSampleReview, request: Request, session: SessionDependency
) -> ProductSample:
    item = session.get(ProductSample, sample_id)
    if item is None or item.organization_id != payload.organization_id:
        raise ApiError(404, "not_found", "Sample was not found in this organization.")
    actor = _actor(request, session, payload.organization_id)
    item.review_status = payload.status
    review_dimensions: dict[str, object] = dict(payload.dimensions)
    item.review_dimensions = review_dimensions
    item.review_notes = payload.notes
    item.reviewed_by = actor.id
    item.reviewed_at = datetime.now(UTC)
    item.status = (
        "accepted"
        if payload.status == "pass"
        else "rejected"
        if payload.status == "fail"
        else "under_review"
    )
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type="human",
        actor_id=actor.id,
        action="product_sample.reviewed",
        entity_type="product_sample",
        entity_id=item.id,
        metadata={"result": payload.status, "external_side_effect": False},
    )
    session.commit()
    session.refresh(item)
    return item


@router.post(
    "/products/{product_id}/supplier-validations",
    response_model=SupplierValidationRead,
    status_code=201,
)
def create_validation(
    product_id: UUID,
    payload: SupplierValidationCreate,
    request: Request,
    session: SessionDependency,
) -> SupplierValidationArtifact:
    _product(session, payload.organization_id, product_id)
    actor = _actor(request, session, payload.organization_id)
    supplier = session.get(SupplierProfile, payload.supplier_id)
    if supplier is None or supplier.organization_id != payload.organization_id:
        raise ApiError(404, "not_found", "Supplier was not found in this organization.")
    if payload.sample_id:
        sample = session.get(ProductSample, payload.sample_id)
        if (
            sample is None
            or sample.organization_id != payload.organization_id
            or sample.product_id != product_id
            or sample.supplier_id != supplier.id
        ):
            raise ApiError(
                409, "sample_scope", "Validation sample does not match Product and Supplier."
            )
    item = SupplierValidationArtifact(
        product_id=product_id,
        verified_by=actor.id if payload.classification == "human_verified" else None,
        **payload.model_dump(),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/products/{product_id}/build-package", response_model=BuildPackageRead)
def get_build_package(
    product_id: UUID, organization_id: UUID, session: SessionDependency
) -> BuildPackageRead:
    try:
        return compose_build_package(session, organization_id, product_id)
    except LookupError as error:
        raise ApiError(404, "not_found", str(error)) from error


@router.get("/build-packages", response_model=list[BuildPackageRead])
def list_build_packages(
    organization_id: UUID, session: SessionDependency
) -> list[BuildPackageRead]:
    products = session.scalars(
        select(Product.id)
        .where(Product.organization_id == organization_id)
        .order_by(Product.created_at.desc())
    )
    return [compose_build_package(session, organization_id, product_id) for product_id in products]
