from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.intelligence.errors import (
    IntelligenceNotFoundError,
    IntelligenceScopeError,
    IntelligenceValidationError,
)
from commerce_os.intelligence.supplier_models import (
    ProductSupplierMatch,
    SupplierDecisionRecord,
    SupplierEvaluation,
    SupplierProfile,
    SupplierProfileStatus,
    SupplierRisk,
)
from commerce_os.intelligence.supplier_schemas import (
    ProductSupplierMatchCreate,
    SupplierDecisionCreate,
    SupplierEvaluationCreate,
    SupplierProfileCreate,
    SupplierRiskCreate,
)
from commerce_os.shared.scope import reference_belongs_to_organization

FORMULA_VERSION = "v1.0"
TRANSITIONS = {
    "discovered": {"evaluating", "rejected", "archived"},
    "evaluating": {"approved", "rejected", "archived"},
    "approved": {"archived"},
    "rejected": {"archived"},
    "archived": set(),
}


def get_scoped_supplier(
    session: Session, supplier_id: UUID, organization_id: UUID
) -> SupplierProfile:
    supplier = session.get(SupplierProfile, supplier_id)
    if supplier is None:
        raise IntelligenceNotFoundError("Supplier profile was not found.")
    if supplier.organization_id != organization_id:
        raise IntelligenceScopeError("Supplier profile belongs to another organization.")
    return supplier


def require_product(session: Session, product_id: UUID, organization_id: UUID) -> None:
    if not reference_belongs_to_organization(
        session, table_name="products", reference_id=product_id, organization_id=organization_id
    ):
        raise IntelligenceScopeError("Product was not found in this organization.")


class SupplierProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: SupplierProfileCreate) -> SupplierProfile:
        supplier = SupplierProfile(**payload.model_dump(), status=SupplierProfileStatus.DISCOVERED)
        self.session.add(supplier)
        self.session.commit()
        self.session.refresh(supplier)
        return supplier

    def transition(
        self, supplier: SupplierProfile, status: SupplierProfileStatus
    ) -> SupplierProfile:
        if status.value not in TRANSITIONS[str(supplier.status)]:
            raise IntelligenceValidationError(
                f"Supplier cannot transition from {supplier.status} to {status.value}."
            )
        if status == SupplierProfileStatus.APPROVED:
            evaluation = self.session.scalar(
                select(SupplierEvaluation)
                .where(SupplierEvaluation.supplier_id == supplier.id)
                .order_by(SupplierEvaluation.created_at.desc())
            )
            if evaluation is None:
                raise IntelligenceValidationError(
                    "An evaluation is required before supplier approval."
                )
        supplier.status = status
        self.session.commit()
        self.session.refresh(supplier)
        return supplier


class SupplierEvaluationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def calculate(payload: SupplierEvaluationCreate) -> float:
        return round(
            (
                payload.quality_score
                + payload.price_score
                + payload.lead_time_score
                + payload.communication_score
                + payload.compliance_score
            )
            / 5,
            2,
        )

    def create(self, payload: SupplierEvaluationCreate) -> SupplierEvaluation:
        get_scoped_supplier(self.session, payload.supplier_id, payload.organization_id)
        evaluation = SupplierEvaluation(
            **payload.model_dump(),
            overall_score=self.calculate(payload),
            formula_version=FORMULA_VERSION,
        )
        self.session.add(evaluation)
        self.session.commit()
        self.session.refresh(evaluation)
        return evaluation


class SupplierRiskService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: SupplierRiskCreate) -> SupplierRisk:
        get_scoped_supplier(self.session, payload.supplier_id, payload.organization_id)
        risk = SupplierRisk(**payload.model_dump())
        self.session.add(risk)
        self.session.commit()
        self.session.refresh(risk)
        return risk


class ProductSupplierMatchService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: ProductSupplierMatchCreate) -> ProductSupplierMatch:
        require_product(self.session, payload.product_id, payload.organization_id)
        get_scoped_supplier(self.session, payload.supplier_id, payload.organization_id)
        match = ProductSupplierMatch(**payload.model_dump(), recommended=payload.match_score >= 70)
        self.session.add(match)
        self.session.commit()
        self.session.refresh(match)
        return match


class SupplierDecisionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: SupplierDecisionCreate) -> SupplierDecisionRecord:
        require_product(self.session, payload.product_id, payload.organization_id)
        supplier = get_scoped_supplier(
            self.session, payload.selected_supplier_id, payload.organization_id
        )
        match = self.session.scalar(
            select(ProductSupplierMatch).where(
                ProductSupplierMatch.product_id == payload.product_id,
                ProductSupplierMatch.supplier_id == payload.selected_supplier_id,
            )
        )
        if (
            supplier.status != SupplierProfileStatus.APPROVED
            or match is None
            or not match.recommended
        ):
            raise IntelligenceValidationError(
                "Supplier decisions require an approved supplier and recommended product match."
            )
        decision = SupplierDecisionRecord(**payload.model_dump())
        self.session.add(decision)
        self.session.commit()
        self.session.refresh(decision)
        return decision
