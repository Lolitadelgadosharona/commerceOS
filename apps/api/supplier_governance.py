"""Deterministic supplier qualification and supply-readiness projections."""

from uuid import UUID

from commerce_os.build.models import ProductTruth
from commerce_os.build.promotion_models import ProductPromotion
from commerce_os.intelligence.supplier_models import (
    ApprovedProductSupplier,
    ProductSupplierMatch,
    SupplierEvaluation,
    SupplierEvidence,
    SupplierProfile,
    SupplierQuote,
    SupplierRisk,
)
from commerce_os.intelligence.supplier_schemas import (
    QualificationDimension,
    ReadinessItem,
    SupplierQualificationRead,
    SupplyReadinessRead,
)
from sqlalchemy import select
from sqlalchemy.orm import Session


def _grade(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 70:
        return "pass"
    if score >= 50:
        return "conditional"
    return "fail"


def _dimension(
    name: str,
    score: float | None,
    evidence: list[str],
    gap: str,
    *,
    risk: str | None = None,
) -> QualificationDimension:
    status = _grade(score)
    return QualificationDimension(
        dimension=name,
        status=status,
        evidence=evidence,
        confidence=None if score is None else min(1, max(0, score / 100)),
        gaps=[] if status == "pass" else [gap],
        risk=risk,
    )


def qualify_supplier(
    session: Session, organization_id: UUID, supplier_id: UUID, product_id: UUID
) -> SupplierQualificationRead:
    supplier = session.get(SupplierProfile, supplier_id)
    if supplier is None or supplier.organization_id != organization_id:
        raise LookupError("Supplier was not found in this organization.")
    truth = session.scalar(
        select(ProductTruth)
        .where(
            ProductTruth.organization_id == organization_id,
            ProductTruth.product_id == product_id,
        )
        .order_by(ProductTruth.version.desc())
    )
    match = session.scalar(
        select(ProductSupplierMatch).where(
            ProductSupplierMatch.organization_id == organization_id,
            ProductSupplierMatch.product_id == product_id,
            ProductSupplierMatch.supplier_id == supplier_id,
        )
    )
    evaluation = session.scalar(
        select(SupplierEvaluation)
        .where(
            SupplierEvaluation.organization_id == organization_id,
            SupplierEvaluation.supplier_id == supplier_id,
        )
        .order_by(SupplierEvaluation.created_at.desc())
    )
    quote = session.scalar(
        select(SupplierQuote)
        .where(
            SupplierQuote.organization_id == organization_id,
            SupplierQuote.product_id == product_id,
            SupplierQuote.supplier_id == supplier_id,
        )
        .order_by(SupplierQuote.quote_date.desc(), SupplierQuote.created_at.desc())
    )
    evidence = list(
        session.scalars(
            select(SupplierEvidence).where(
                SupplierEvidence.organization_id == organization_id,
                SupplierEvidence.supplier_id == supplier_id,
            )
        )
    )
    risks = list(
        session.scalars(
            select(SupplierRisk).where(
                SupplierRisk.organization_id == organization_id,
                SupplierRisk.supplier_id == supplier_id,
                SupplierRisk.status == "open",
            )
        )
    )
    fields = {item.field_name: item for item in evidence}
    quote_ref = [str(quote.id)] if quote else []
    eval_ref = [str(evaluation.id)] if evaluation else []
    commercial_score = (
        100.0
        if quote and quote.unit_price is not None and quote.minimum_order_quantity is not None
        else 60.0
        if quote and (quote.unit_price is not None or quote.minimum_order_quantity)
        else None
    )
    dimensions = [
        _dimension(
            "product_fit",
            match.match_score if match else None,
            [str(match.id)] if match else [],
            "Record a Product-Supplier match supported by Product Truth.",
        ),
        _dimension(
            "commercial_fit",
            commercial_score,
            quote_ref,
            "Record quoted unit price and minimum order quantity.",
        ),
        _dimension(
            "quality",
            evaluation.quality_score if evaluation else None,
            eval_ref,
            "Record evidence-backed quality evaluation.",
        ),
        _dimension(
            "capacity",
            100.0 if "production_capacity" in fields else None,
            [str(fields["production_capacity"].id)] if "production_capacity" in fields else [],
            "Verify production capacity.",
        ),
        _dimension(
            "lead_time",
            100.0 if quote and quote.lead_time else None,
            quote_ref,
            "Record supplier lead time.",
        ),
        _dimension(
            "compliance",
            evaluation.compliance_score if evaluation else None,
            eval_ref + ([str(truth.id)] if truth else []),
            "Compare certifications and evidence with current Product Truth requirements.",
        ),
        _dimension(
            "logistics",
            100.0 if quote and quote.incoterm else None,
            quote_ref,
            "Record logistics term or Incoterm.",
        ),
        _dimension(
            "payment_terms",
            100.0 if quote and quote.payment_terms else None,
            quote_ref,
            "Record payment terms; this does not authorize payment.",
        ),
        _dimension(
            "supplier_reliability",
            evaluation.communication_score if evaluation else None,
            eval_ref,
            "Record evidence-backed supplier reliability evaluation.",
        ),
        _dimension(
            "provenance_quality",
            (
                100.0
                if evidence
                and all(
                    item.classification in {"observed", "verified", "quoted"} for item in evidence
                )
                else 60.0
                if evidence
                else None
            ),
            [str(item.id) for item in evidence],
            "Add observed, quoted, or verified supplier evidence.",
        ),
    ]
    blockers: list[ReadinessItem] = []
    if truth is None:
        blockers.append(
            ReadinessItem(
                code="product_truth",
                severity="blocker",
                status="blocked",
                message="Approved Product Truth is required for supplier qualification.",
            )
        )
    if match is None:
        blockers.append(
            ReadinessItem(
                code="product_match",
                severity="blocker",
                status="blocked",
                message="Product-Supplier relationship is missing.",
            )
        )
    if quote is None or quote.unit_price is None or quote.minimum_order_quantity is None:
        blockers.append(
            ReadinessItem(
                code="commercial_terms",
                severity="blocker",
                status="blocked",
                message="Quoted unit price and MOQ are required.",
            )
        )
    critical = [risk for risk in risks if risk.severity == "critical"]
    if critical:
        blockers.append(
            ReadinessItem(
                code="critical_supplier_risk",
                severity="blocker",
                status="blocked",
                message="Critical supplier risks remain open.",
                references=[str(risk.id) for risk in critical],
            )
        )
    failures = [item.dimension for item in dimensions if item.status == "fail"]
    if failures:
        blockers.append(
            ReadinessItem(
                code="failed_dimensions",
                severity="blocker",
                status="blocked",
                message="Qualification dimensions failed: " + ", ".join(failures),
            )
        )
    warnings = [
        ReadinessItem(
            code=f"unknown_{item.dimension}",
            severity="warning",
            status="unknown",
            message=item.gaps[0],
        )
        for item in dimensions
        if item.status == "unknown"
    ]
    ready = not blockers
    next_action = (
        blockers[0].message
        if blockers
        else warnings[0].message
        if warnings
        else "Request governed supplier approval."
    )
    return SupplierQualificationRead(
        organization_id=organization_id,
        supplier_id=supplier_id,
        product_id=product_id,
        dimensions=dimensions,
        readiness=blockers + warnings,
        ready=ready,
        next_action=next_action,
    )


def product_supply_readiness(
    session: Session, organization_id: UUID, product_id: UUID
) -> SupplyReadinessRead:
    items: list[ReadinessItem] = []
    origin = session.scalar(
        select(ProductPromotion).where(
            ProductPromotion.organization_id == organization_id,
            ProductPromotion.product_id == product_id,
        )
    )
    items.append(
        ReadinessItem(
            code="governed_product_origin",
            severity="blocker",
            status="ready" if origin else "blocked",
            message="Governed Product promotion origin is recorded."
            if origin
            else "Legacy direct Product has no governed promotion origin.",
        )
    )
    truth = session.scalar(
        select(ProductTruth)
        .where(
            ProductTruth.product_id == product_id, ProductTruth.organization_id == organization_id
        )
        .order_by(ProductTruth.version.desc())
    )
    items.append(
        ReadinessItem(
            code="product_truth",
            severity="blocker",
            status="ready" if truth else "blocked",
            message="Current Product Truth is available."
            if truth
            else "Approved Product Truth is required.",
        )
    )
    relationships = list(
        session.scalars(
            select(ApprovedProductSupplier).where(
                ApprovedProductSupplier.organization_id == organization_id,
                ApprovedProductSupplier.product_id == product_id,
                ApprovedProductSupplier.status == "approved",
            )
        )
    )
    items.append(
        ReadinessItem(
            code="approved_supplier",
            severity="blocker",
            status="ready" if relationships else "blocked",
            message="At least one governed Product-Supplier relationship is approved."
            if relationships
            else "A qualified supplier must be approved for this Product.",
            references=[str(item.id) for item in relationships],
        )
    )
    critical: list[SupplierRisk] = []
    for relationship in relationships:
        critical.extend(
            session.scalars(
                select(SupplierRisk).where(
                    SupplierRisk.organization_id == organization_id,
                    SupplierRisk.supplier_id == relationship.supplier_id,
                    SupplierRisk.status == "open",
                    SupplierRisk.severity == "critical",
                )
            ).all()
        )
    items.append(
        ReadinessItem(
            code="supplier_risk",
            severity="blocker",
            status="blocked" if critical else "ready",
            message="Critical approved-supplier risks remain open."
            if critical
            else "No open critical risk is recorded for approved suppliers.",
            references=[str(risk.id) for risk in critical],
        )
    )
    ready = all(item.status == "ready" for item in items if item.severity == "blocker")
    first = next(
        (item.message for item in items if item.status != "ready"),
        "Supply foundation is ready for a governed next decision.",
    )
    return SupplyReadinessRead(
        organization_id=organization_id,
        product_id=product_id,
        ready=ready,
        approved_suppliers=relationships,
        items=items,
        next_action=first,
    )
