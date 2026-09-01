from typing import Annotated
from uuid import UUID

from commerce_os.build.promotion_models import ProductPromotion
from commerce_os.build.promotion_schemas import ProductPromotionRead, PromotionReadiness
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.executive_schemas import DecisionQueueRead
from commerce_os.governance.models import ApprovalRequest
from commerce_os.governance.schemas import ApprovalRequestRead
from commerce_os.intelligence.market_models import (
    MarketSignal,
    MarketSignalEvidence,
    MarketSignalOpportunityLink,
)
from commerce_os.intelligence.market_schemas import MarketEvidenceRead, MarketSignalRead
from commerce_os.intelligence.opportunity_models import OpportunityEvidence
from commerce_os.intelligence.opportunity_schemas import (
    MarketOpportunityRead,
    OpportunityEvidenceRead,
)
from commerce_os.intelligence.product_models import (
    ProductEconomicInputProvenance,
    ProductEconomics,
    ProductHypothesis,
    ProductInvestmentScore,
    ProductRisk,
    SupplierCandidate,
)
from commerce_os.intelligence.product_schemas import (
    ProductEconomicInputRead,
    ProductEconomicsRead,
    ProductHypothesisRead,
    ProductInvestmentScoreRead,
    ProductRiskRead,
    SupplierCandidateRead,
)
from commerce_os.shared.database import get_session
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.opportunity_launch_routes import (
    InvestmentMemo,
    LaunchReadiness,
    compose,
    scoped_opportunity,
)
from apps.api.product_promotion_routes import promotion_readiness

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


class PacketMarketSignal(BaseModel):
    signal: MarketSignalRead
    evidence: list[MarketEvidenceRead]


class PacketProductThesis(BaseModel):
    hypothesis: ProductHypothesisRead
    economics: ProductEconomicsRead | None
    economic_inputs: list[ProductEconomicInputRead]
    supplier_candidates: list[SupplierCandidateRead]
    risks: list[ProductRiskRead]
    investment_score: ProductInvestmentScoreRead | None
    product_truth_relationship_status: str
    promotion_readiness: PromotionReadiness
    promotion: ProductPromotionRead | None
    promotion_approval: ApprovalRequestRead | None


class DecisionQualityWarning(BaseModel):
    code: str
    severity: str
    message: str


class InvestmentCommitteePacket(BaseModel):
    organization_id: UUID
    opportunity: MarketOpportunityRead
    market_evidence: list[OpportunityEvidenceRead]
    market_signals: list[PacketMarketSignal]
    source_diversity: int
    product_theses: list[PacketProductThesis]
    investment_memo: InvestmentMemo
    approval: ApprovalRequestRead | None
    decision_queue: DecisionQueueRead | None
    launch_readiness: LaunchReadiness
    supporting_case: list[str]
    opposing_case: list[str]
    missing_evidence: list[str]
    decision_quality_warnings: list[DecisionQualityWarning]
    unavailable_sections: list[str]


CRITICAL_ECONOMIC_METRICS = {
    "selling_price",
    "estimated_product_cost",
    "estimated_shipping_cost",
    "payment_cost",
    "estimated_marketing_cost",
}


def _product_theses(
    session: Session, organization_id: UUID, opportunity_id: UUID
) -> list[PacketProductThesis]:
    hypotheses = list(
        session.scalars(
            select(ProductHypothesis)
            .where(
                ProductHypothesis.organization_id == organization_id,
                ProductHypothesis.opportunity_id == opportunity_id,
            )
            .order_by(ProductHypothesis.created_at)
        )
    )
    result: list[PacketProductThesis] = []
    for hypothesis in hypotheses:
        economics = session.scalar(
            select(ProductEconomics).where(
                ProductEconomics.organization_id == organization_id,
                ProductEconomics.product_id == hypothesis.id,
            )
        )
        inputs = (
            list(
                session.scalars(
                    select(ProductEconomicInputProvenance)
                    .where(
                        ProductEconomicInputProvenance.organization_id == organization_id,
                        ProductEconomicInputProvenance.product_economics_id == economics.id,
                    )
                    .order_by(ProductEconomicInputProvenance.metric)
                )
            )
            if economics
            else []
        )
        suppliers = list(
            session.scalars(
                select(SupplierCandidate).where(
                    SupplierCandidate.organization_id == organization_id,
                    SupplierCandidate.product_id == hypothesis.id,
                )
            )
        )
        risks = list(
            session.scalars(
                select(ProductRisk).where(
                    ProductRisk.organization_id == organization_id,
                    ProductRisk.product_id == hypothesis.id,
                )
            )
        )
        score = session.scalar(
            select(ProductInvestmentScore).where(
                ProductInvestmentScore.organization_id == organization_id,
                ProductInvestmentScore.product_id == hypothesis.id,
            )
        )
        promotion = session.scalar(
            select(ProductPromotion).where(
                ProductPromotion.organization_id == organization_id,
                ProductPromotion.product_hypothesis_id == hypothesis.id,
            )
        )
        promotion_approval = (
            session.get(ApprovalRequest, promotion.approval_request_id) if promotion else None
        )
        result.append(
            PacketProductThesis(
                hypothesis=hypothesis,
                economics=economics,
                economic_inputs=inputs,
                supplier_candidates=suppliers,
                risks=risks,
                investment_score=score,
                product_truth_relationship_status=(
                    "promoted_product"
                    if promotion and promotion.product_id
                    else "no_canonical_relationship"
                ),
                promotion_readiness=promotion_readiness(session, hypothesis),
                promotion=promotion,
                promotion_approval=promotion_approval,
            )
        )
    return result


def _market_signals(
    session: Session, organization_id: UUID, opportunity_id: UUID
) -> list[PacketMarketSignal]:
    signals = list(
        session.scalars(
            select(MarketSignal)
            .join(
                MarketSignalOpportunityLink,
                MarketSignalOpportunityLink.signal_id == MarketSignal.id,
            )
            .where(
                MarketSignal.organization_id == organization_id,
                MarketSignalOpportunityLink.organization_id == organization_id,
                MarketSignalOpportunityLink.opportunity_id == opportunity_id,
            )
            .order_by(MarketSignal.observed_at)
        )
    )
    return [
        PacketMarketSignal(
            signal=signal,
            evidence=list(
                session.scalars(
                    select(MarketSignalEvidence).where(
                        MarketSignalEvidence.organization_id == organization_id,
                        MarketSignalEvidence.signal_id == signal.id,
                    )
                )
            ),
        )
        for signal in signals
    ]


def _warnings(
    product_theses: list[PacketProductThesis],
    market_evidence: list[OpportunityEvidence],
    market_signals: list[PacketMarketSignal],
    memo: InvestmentMemo,
    readiness: LaunchReadiness,
    approval: ApprovalRequest | None,
) -> list[DecisionQualityWarning]:
    values: list[DecisionQualityWarning] = []
    source_types = {str(item.source_type) for item in market_evidence} | {
        str(item.signal.source_id) for item in market_signals
    }
    if len(source_types) <= 1:
        values.append(
            DecisionQualityWarning(
                code="single_source_type",
                severity="warning",
                message="The evidence case relies on one or fewer independent source types.",
            )
        )
    if not product_theses:
        values.append(
            DecisionQualityWarning(
                code="product_thesis_missing",
                severity="blocking",
                message="No ProductHypothesis is linked to this opportunity.",
            )
        )
    for thesis in product_theses:
        if thesis.economics is None:
            values.append(
                DecisionQualityWarning(
                    code="economics_missing",
                    severity="blocking",
                    message="Product economics have not been recorded.",
                )
            )
            continue
        by_metric = {item.metric: item for item in thesis.economic_inputs}
        missing = sorted(CRITICAL_ECONOMIC_METRICS - set(by_metric))
        unknown = sorted(
            metric
            for metric, item in by_metric.items()
            if metric in CRITICAL_ECONOMIC_METRICS and item.classification == "unknown"
        )
        if missing or unknown:
            values.append(
                DecisionQualityWarning(
                    code="critical_economics_unknown",
                    severity="blocking",
                    message="Critical economic inputs are missing or UNKNOWN: "
                    + ", ".join(missing + unknown),
                )
            )
        supplier_input = by_metric.get("estimated_product_cost")
        if supplier_input and supplier_input.classification == "assumption":
            values.append(
                DecisionQualityWarning(
                    code="supplier_cost_assumption",
                    severity="warning",
                    message="Supplier cost is supported only by an assumption.",
                )
            )
        legacy = sorted(
            metric
            for metric, item in by_metric.items()
            if item.classification == "legacy_unprovenanced"
        )
        if legacy:
            values.append(
                DecisionQualityWarning(
                    code="legacy_economics_provenance",
                    severity="warning",
                    message=(
                        "Economic value exists but source provenance is not established: "
                        + ", ".join(legacy)
                    ),
                )
            )
        if not thesis.supplier_candidates:
            values.append(
                DecisionQualityWarning(
                    code="supplier_evidence_missing",
                    severity="warning",
                    message="No supplier candidate or supplier evidence is recorded.",
                )
            )
        if not thesis.risks:
            values.append(
                DecisionQualityWarning(
                    code="product_risk_missing",
                    severity="warning",
                    message="No ProductRisk assessment is recorded.",
                )
            )
    if approval is not None and not memo.summary.get("report"):
        values.append(
            DecisionQualityWarning(
                code="approval_before_report",
                severity="warning",
                message="Approval was requested before an Opportunity Report was recorded.",
            )
        )
    if readiness.overall_status != "ready":
        values.append(
            DecisionQualityWarning(
                code="launch_readiness_incomplete",
                severity="blocking",
                message="Launch readiness remains incomplete after any investment decision.",
            )
        )
    return values


@router.get(
    "/opportunities/{opportunity_id}/committee-packet",
    response_model=InvestmentCommitteePacket,
)
def committee_packet(
    opportunity_id: UUID, organization_id: UUID, session: SessionDependency
) -> InvestmentCommitteePacket:
    opportunity = scoped_opportunity(session, opportunity_id, organization_id)
    memo, readiness = compose(session, opportunity, None)
    evidence = list(
        session.scalars(
            select(OpportunityEvidence)
            .where(
                OpportunityEvidence.organization_id == organization_id,
                OpportunityEvidence.opportunity_id == opportunity_id,
            )
            .order_by(OpportunityEvidence.created_at)
        )
    )
    signals = _market_signals(session, organization_id, opportunity_id)
    theses = _product_theses(session, organization_id, opportunity_id)
    approval = session.scalar(
        select(ApprovalRequest)
        .where(
            ApprovalRequest.organization_id == organization_id,
            ApprovalRequest.object_type == "market_opportunity",
            ApprovalRequest.object_id == opportunity_id,
            ApprovalRequest.requested_action == "approve_investment",
        )
        .order_by(ApprovalRequest.created_at.desc())
    )
    queue = (
        session.scalar(
            select(DecisionQueueItem).where(
                DecisionQueueItem.organization_id == organization_id,
                DecisionQueueItem.approval_request_id == approval.id,
            )
        )
        if approval
        else None
    )
    warnings = _warnings(theses, evidence, signals, memo, readiness, approval)
    supporting = [item.evidence_summary for item in evidence] + [
        item.signal.title for item in signals
    ]
    opposing = [risk.description for thesis in theses for risk in thesis.risks]
    missing = list(dict.fromkeys(memo.missing_evidence + readiness.blocking_reasons))
    opposing.extend(missing)
    unavailable: list[str] = []
    if not signals:
        unavailable.append("market_signal_links")
    if not theses:
        unavailable.append("product_thesis")
    if all(not thesis.economic_inputs for thesis in theses):
        unavailable.append("economics_provenance")
    unavailable.append("product_truth_comparison")
    return InvestmentCommitteePacket(
        organization_id=organization_id,
        opportunity=opportunity,
        market_evidence=evidence,
        market_signals=signals,
        source_diversity=len(
            {str(item.source_type) for item in evidence}
            | {str(item.signal.source_id) for item in signals}
        ),
        product_theses=theses,
        investment_memo=memo,
        approval=approval,
        decision_queue=queue,
        launch_readiness=readiness,
        supporting_case=supporting,
        opposing_case=opposing,
        missing_evidence=missing,
        decision_quality_warnings=warnings,
        unavailable_sections=unavailable,
    )
