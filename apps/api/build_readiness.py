from datetime import date
from uuid import UUID

from commerce_os.build.models import Product, ProductTruth
from commerce_os.build.promotion_models import ProductPromotion
from commerce_os.build.readiness_models import (
    BuildRequirementPolicy,
    ProductBuildRequirement,
    ProductSample,
    SupplierValidationArtifact,
)
from commerce_os.build.readiness_schemas import (
    BuildPackageRead,
    BuildReadinessItem,
    BuildSupplierRelationship,
    SupplierFitItem,
)
from commerce_os.intelligence.product_models import (
    ProductEconomicInputProvenance,
    ProductEconomics,
    ProductRisk,
)
from commerce_os.intelligence.supplier_models import (
    ApprovedProductSupplier,
    SupplierEvidence,
    SupplierQuote,
    SupplierRisk,
)
from sqlalchemy import select
from sqlalchemy.orm import Session


def compose_build_package(
    session: Session, organization_id: UUID, product_id: UUID
) -> BuildPackageRead:
    product = session.get(Product, product_id)
    if product is None or product.organization_id != organization_id:
        raise LookupError("Product was not found in this organization.")
    promotion = session.scalar(
        select(ProductPromotion).where(
            ProductPromotion.organization_id == organization_id,
            ProductPromotion.product_id == product_id,
        )
    )
    truth = session.scalar(
        select(ProductTruth)
        .where(
            ProductTruth.organization_id == organization_id, ProductTruth.product_id == product_id
        )
        .order_by(ProductTruth.version.desc())
    )
    requirements = (
        []
        if truth is None
        else list(
            session.scalars(
                select(ProductBuildRequirement).where(
                    ProductBuildRequirement.organization_id == organization_id,
                    ProductBuildRequirement.product_truth_id == truth.id,
                )
            )
        )
    )
    relationships = list(
        session.scalars(
            select(ApprovedProductSupplier).where(
                ApprovedProductSupplier.organization_id == organization_id,
                ApprovedProductSupplier.product_id == product_id,
            )
        )
    )
    approved = [item for item in relationships if item.status == "approved"]
    supplier_ids = [item.supplier_id for item in approved]
    evidence = (
        []
        if not supplier_ids
        else list(
            session.scalars(
                select(SupplierEvidence).where(
                    SupplierEvidence.organization_id == organization_id,
                    SupplierEvidence.supplier_id.in_(supplier_ids),
                )
            )
        )
    )
    evidence_by_field = {item.field_name: item for item in evidence}
    requirement_values = {
        item.attribute_key: (item.display_label, item.value, item.required_for_build)
        for item in requirements
    }
    if not requirement_values and truth is not None:
        requirement_values = {
            str(key): (str(key).replace("_", " ").title(), value, True)
            for key, value in truth.specifications.items()
        }
    fit: list[SupplierFitItem] = []
    blocking_fit_labels: list[str] = []
    for key, (label, expected, required) in requirement_values.items():
        supplier_fact = evidence_by_field.get(key)
        if supplier_fact is None or supplier_fact.value is None:
            state = "unknown"
        elif supplier_fact.value == expected:
            state = "pass"
        else:
            state = "conditional"
        if required and state in {"unknown", "fail"}:
            blocking_fit_labels.append(label)
        fit.append(
            SupplierFitItem(
                requirement=label,
                required_value=expected,
                supplier_response=None if supplier_fact is None else supplier_fact.value,
                evidence=[] if supplier_fact is None else [str(supplier_fact.id)],
                status=state,
                gap="Supplier validation evidence is missing." if state == "unknown" else None,
            )
        )
    samples = list(
        session.scalars(
            select(ProductSample).where(
                ProductSample.organization_id == organization_id,
                ProductSample.product_id == product_id,
            )
        )
    )
    validations = list(
        session.scalars(
            select(SupplierValidationArtifact).where(
                SupplierValidationArtifact.organization_id == organization_id,
                SupplierValidationArtifact.product_id == product_id,
            )
        )
    )
    policy = session.scalar(
        select(BuildRequirementPolicy).where(
            BuildRequirementPolicy.organization_id == organization_id,
            BuildRequirementPolicy.product_id == product_id,
        )
    )
    quotes = (
        []
        if not supplier_ids
        else list(
            session.scalars(
                select(SupplierQuote).where(
                    SupplierQuote.organization_id == organization_id,
                    SupplierQuote.product_id == product_id,
                    SupplierQuote.supplier_id.in_(supplier_ids),
                )
            )
        )
    )
    economics = (
        None
        if promotion is None
        else session.scalar(
            select(ProductEconomics).where(
                ProductEconomics.organization_id == organization_id,
                ProductEconomics.product_id == promotion.product_hypothesis_id,
            )
        )
    )
    economic_inputs = (
        []
        if economics is None
        else list(
            session.scalars(
                select(ProductEconomicInputProvenance).where(
                    ProductEconomicInputProvenance.organization_id == organization_id,
                    ProductEconomicInputProvenance.product_economics_id == economics.id,
                )
            )
        )
    )
    blockers: list[BuildReadinessItem] = []
    warnings: list[BuildReadinessItem] = []
    if promotion is None:
        blockers.append(
            BuildReadinessItem(
                code="governed_product",
                severity="blocker",
                message="Governed Product promotion origin is required.",
            )
        )
    if truth is None:
        blockers.append(
            BuildReadinessItem(
                code="product_truth",
                severity="blocker",
                message="Approved Product Truth is required.",
            )
        )
    elif not truth.specifications and not requirements:
        blockers.append(
            BuildReadinessItem(
                code="build_specifications",
                severity="blocker",
                message="Product Truth contains no structured build specifications.",
            )
        )
    pending = [item for item in relationships if item.status != "approved"]
    if not approved:
        message = (
            "Execute the approved supplier relationship."
            if pending
            else "An approved Product-Supplier relationship is required."
        )
        blockers.append(
            BuildReadinessItem(
                code="approved_supplier",
                severity="blocker",
                message=message,
                references=[str(item.id) for item in pending],
            )
        )
    if blocking_fit_labels:
        blockers.append(
            BuildReadinessItem(
                code="supplier_fit",
                severity="blocker",
                message="Supplier fit evidence is missing or failed: "
                + ", ".join(blocking_fit_labels),
            )
        )
    failed_validations = [item for item in validations if item.result == "fail"]
    if failed_validations:
        blockers.append(
            BuildReadinessItem(
                code="failed_validation",
                severity="blocker",
                message="A supplier validation result failed.",
                references=[str(item.id) for item in failed_validations],
            )
        )
    if (
        policy
        and policy.sample_required
        and not any(item.status == "accepted" and item.review_status == "pass" for item in samples)
    ):
        blockers.append(
            BuildReadinessItem(
                code="sample_required",
                severity="blocker",
                message="An accepted, passing sample review is required.",
            )
        )
    if (
        policy
        and policy.inspection_required
        and not any(
            item.validation_type == "inspection" and item.result == "pass" for item in validations
        )
    ):
        blockers.append(
            BuildReadinessItem(
                code="inspection_required",
                severity="blocker",
                message="A passing inspection artifact is required.",
            )
        )
    if (
        policy
        and policy.compliance_evidence_required
        and not any(
            item.validation_type in {"certification", "document"} and item.result == "pass"
            for item in validations
        )
    ):
        blockers.append(
            BuildReadinessItem(
                code="compliance_required",
                severity="blocker",
                message="Passing compliance evidence is required.",
            )
        )
    if (
        policy
        and policy.packaging_validation_required
        and not any(
            item.validation_type == "packaging" and item.result == "pass" for item in validations
        )
    ):
        blockers.append(
            BuildReadinessItem(
                code="packaging_required",
                severity="blocker",
                message="Passing packaging validation is required.",
            )
        )
    product_risks = (
        []
        if promotion is None
        else list(
            session.scalars(
                select(ProductRisk).where(
                    ProductRisk.organization_id == organization_id,
                    ProductRisk.product_id == promotion.product_hypothesis_id,
                    ProductRisk.status == "open",
                    ProductRisk.severity == "critical",
                )
            )
        )
    )
    supplier_risks = (
        []
        if not supplier_ids
        else list(
            session.scalars(
                select(SupplierRisk).where(
                    SupplierRisk.organization_id == organization_id,
                    SupplierRisk.supplier_id.in_(supplier_ids),
                    SupplierRisk.status == "open",
                    SupplierRisk.severity == "critical",
                )
            )
        )
    )
    if product_risks:
        blockers.append(
            BuildReadinessItem(
                code="critical_product_risk",
                severity="blocker",
                message="Critical Product Risk remains open.",
                references=[str(item.id) for item in product_risks],
            )
        )
    if supplier_risks:
        blockers.append(
            BuildReadinessItem(
                code="critical_supplier_risk",
                severity="blocker",
                message="Critical Supplier Risk remains open.",
                references=[str(item.id) for item in supplier_risks],
            )
        )
    quote_input_ids = [
        item.id
        for item in economic_inputs
        if item.metric == "estimated_product_cost"
        and item.classification == "quoted"
        and item.supplier_quote_id
    ]
    if approved and not quote_input_ids:
        blockers.append(
            BuildReadinessItem(
                code="quote_cost_provenance",
                severity="blocker",
                message="Supplier cost requires normalized quote provenance.",
            )
        )
    expired = [item for item in quotes if item.valid_until and item.valid_until < date.today()]
    if expired:
        warnings.append(
            BuildReadinessItem(
                code="expired_quote",
                severity="warning",
                message="A supplier quote has expired and should be refreshed.",
                references=[str(item.id) for item in expired],
            )
        )
    if len(approved) == 1:
        warnings.append(
            BuildReadinessItem(
                code="single_supplier",
                severity="warning",
                message="Only one supplier is approved; this does not block Build Ready.",
            )
        )
    conditional_fit = [item.requirement for item in fit if item.status == "conditional"]
    if conditional_fit:
        warnings.append(
            BuildReadinessItem(
                code="conditional_supplier_fit",
                severity="warning",
                message="Supplier responses differ from Product Truth: "
                + ", ".join(conditional_fit),
            )
        )
    if (
        samples
        and not any(item.review_status == "pass" for item in samples)
        and not (policy and policy.sample_required)
    ):
        warnings.append(
            BuildReadinessItem(
                code="sample_unreviewed",
                severity="warning",
                message="A sample exists but has not passed review.",
            )
        )
    if any(item.classification == "legacy_unprovenanced" for item in economic_inputs):
        warnings.append(
            BuildReadinessItem(
                code="legacy_economics",
                severity="warning",
                message="Legacy economic provenance remains visible and unproven.",
            )
        )
    status = "not_ready" if blockers else "conditional" if warnings else "ready"
    actions = {
        "governed_product": "Promote Product through Governance.",
        "product_truth": "Approve Product Truth.",
        "build_specifications": "Add structured Product Truth build specifications.",
        "approved_supplier": "Complete governed supplier selection execution.",
        "supplier_fit": "Add supplier evidence for Product Truth requirements.",
        "sample_required": "Record and review a supplier sample.",
        "inspection_required": "Record passing inspection evidence.",
        "compliance_required": "Complete compliance evidence.",
        "packaging_required": "Validate packaging requirements.",
        "critical_product_risk": "Resolve the critical Product Risk.",
        "critical_supplier_risk": "Resolve the critical Supplier Risk.",
        "quote_cost_provenance": "Link supplier quote to product cost provenance.",
    }
    next_action = (
        actions.get(blockers[0].code, "Review Build Package warnings.")
        if blockers
        else "Review Build Package for commercialization preparation."
    )
    return BuildPackageRead(
        organization_id=organization_id,
        product_id=product_id,
        product_name=product.name,
        product_truth_id=None if truth is None else truth.id,
        product_truth_version=None if truth is None else truth.version,
        specifications={} if truth is None else truth.specifications,
        requirements=requirements,
        approved_suppliers=supplier_ids,
        supplier_relationships=[
            BuildSupplierRelationship(
                id=item.id,
                supplier_id=item.supplier_id,
                approval_request_id=item.approval_request_id,
                role=item.role,
                status=item.status,
            )
            for item in relationships
        ],
        supplier_fit=fit,
        samples=samples,
        validations=validations,
        quote_ids=[item.id for item in quotes],
        quote_economics_ids=quote_input_ids,
        blockers=blockers,
        warnings=warnings,
        status=status,
        next_action=next_action,
        origin_opportunity_id=None if promotion is None else promotion.opportunity_id,
        origin_hypothesis_id=None if promotion is None else promotion.product_hypothesis_id,
    )
