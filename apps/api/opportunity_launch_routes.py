from datetime import date
from typing import Annotated, Any
from uuid import UUID

from commerce_os.governance.approvals import ApprovalWorkflowService
from commerce_os.governance.audit import AuditService
from commerce_os.governance.executive_models import DecisionQueueItem
from commerce_os.governance.models import ApprovalRequest, ApprovalStatus, User
from commerce_os.intelligence.opportunity_models import MarketOpportunity
from commerce_os.operations.execution_models import ExecutionTask, ProductLaunch
from commerce_os.operations.execution_schemas import (
    ActionPlanCreate,
    ExecutionBlockerCreate,
    ExecutionTaskCreate,
    LaunchMilestoneCreate,
    ProductLaunchCreate,
)
from commerce_os.operations.execution_services import LaunchExecutionService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


class ReadinessItem(BaseModel):
    category: str
    status: str
    reason: str
    references: list[str]
    blocking: bool


class InvestmentMemo(BaseModel):
    opportunity_id: UUID
    organization_id: UUID
    summary: dict[str, Any]
    evidence: list[dict[str, Any]]
    conclusions: dict[str, dict[str, Any]]
    missing_evidence: list[str]
    confidence: float
    recommended_decision: str


class LaunchReadiness(BaseModel):
    opportunity_id: UUID
    categories: list[ReadinessItem]
    overall_status: str
    blocking_reasons: list[str]


class ReviewRequest(BaseModel):
    organization_id: UUID
    requester_id: UUID
    project_id: UUID | None = None
    reason: str = Field(min_length=1)


class ActivateRequest(BaseModel):
    organization_id: UUID
    approval_request_id: UUID
    project_id: UUID
    product_id: UUID
    priority: str = "high"


def scoped_opportunity(session: Session, item_id: UUID, organization_id: UUID) -> MarketOpportunity:
    item = session.get(MarketOpportunity, item_id)
    if item is None or item.organization_id != organization_id:
        raise ApiError(404, "not_found", "Opportunity was not found in this organization.")
    return item


def rows(session: Session, table_name: str, **filters: Any) -> list[dict[str, Any]]:
    table = Base.metadata.tables[table_name]
    statement = select(table)
    for name, value in filters.items():
        statement = statement.where(getattr(table.c, name) == value)
    return [dict(row) for row in session.execute(statement).mappings()]


def first(session: Session, table_name: str, **filters: Any) -> dict[str, Any] | None:
    values = rows(session, table_name, **filters)
    return values[0] if values else None


def references(value: Any) -> list[str]:
    if isinstance(value, dict) and value.get("id"):
        return [str(value["id"])]
    if isinstance(value, list):
        return [str(item["id"]) for item in value if isinstance(item, dict) and item.get("id")]
    return []


def safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: str(item) if isinstance(item, (UUID, date)) else item
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [safe(item) for item in value]
    return value


def check(category: str, value: Any, reason: str, blocking: bool) -> ReadinessItem:
    return ReadinessItem(
        category=category,
        status="ready" if value else "missing",
        reason="Available" if value else reason,
        references=references(value),
        blocking=blocking,
    )


def compose(
    session: Session, item: MarketOpportunity, product_id: UUID | None
) -> tuple[InvestmentMemo, LaunchReadiness]:
    org = item.organization_id
    evidence = rows(session, "opportunity_evidence", organization_id=org, opportunity_id=item.id)
    assessment = first(
        session, "opportunity_assessments", organization_id=org, market_opportunity_id=item.id
    )
    report = first(session, "opportunity_reports", organization_id=org, opportunity_id=item.id)
    candidate = first(session, "product_candidates", organization_id=org, opportunity_id=item.id)
    customer = first(
        session,
        "customer_backed_opportunity_assessments",
        organization_id=org,
        opportunity_id=item.id,
    )
    candidate_id = candidate["id"] if candidate else None
    risk = (
        first(
            session,
            "product_risk_assessments",
            organization_id=org,
            product_candidate_id=candidate_id,
        )
        if candidate_id
        else None
    )
    viability = (
        first(
            session,
            "commercial_viability_assessments",
            organization_id=org,
            product_candidate_id=candidate_id,
        )
        if candidate_id
        else None
    )
    economics = (
        first(
            session,
            "product_economic_profiles",
            organization_id=org,
            product_candidate_id=candidate_id,
        )
        if candidate_id
        else None
    )
    scenarios = (
        rows(
            session,
            "profit_scenario_assessments",
            organization_id=org,
            product_candidate_id=candidate_id,
        )
        if candidate_id
        else []
    )
    adjusted = (
        first(
            session,
            "risk_adjusted_profit_assessments",
            organization_id=org,
            product_candidate_id=candidate_id,
        )
        if candidate_id
        else None
    )
    truth = (
        first(session, "product_truth", organization_id=org, product_id=product_id)
        if product_id
        else None
    )
    positioning = (
        first(session, "product_positioning", organization_id=org, product_id=product_id)
        if product_id
        else None
    )
    offer = (
        first(session, "offer_strategies", organization_id=org, product_id=product_id)
        if product_id
        else None
    )
    listing = (
        first(session, "listing_blueprints", organization_id=org, product_id=product_id)
        if product_id
        else None
    )
    geo = (
        first(
            session,
            "ai_discovery_readiness_assessments",
            organization_id=org,
            product_id=product_id,
        )
        if product_id
        else None
    )
    creative = (
        first(session, "creative_strategies", organization_id=org, product_id=product_id)
        if product_id
        else None
    )
    channel = (
        first(session, "channel_strategies", organization_id=org, product_id=product_id)
        if product_id
        else None
    )
    risk_item = check(
        "risk", risk and viability, "Risk and viability assessments are required", True
    )
    if risk and risk["risk_level"] == "critical":
        risk_item = ReadinessItem(
            category="risk",
            status="blocked",
            reason="Critical product risk blocks progression",
            references=references(risk),
            blocking=True,
        )
    categories = [
        check("market_evidence", evidence, "Market evidence is required", True),
        check("customer_evidence", customer, "Customer evidence is required", True),
        check("product_solution", candidate, "Product candidate is required", True),
        risk_item,
        check(
            "economics",
            economics and adjusted,
            "Economic and risk-adjusted assessments are required",
            True,
        ),
        check("supplier", None, "Supplier readiness is not linked", False),
        check("product_truth", truth, "Approved Product Truth is required", True),
        check("positioning", positioning and offer, "Positioning and offer are required", False),
        check("listing_geo", listing and geo, "Listing and GEO readiness are required", False),
        check("creative", creative, "Creative strategy is required", False),
        check("channel", channel, "Channel strategy is required", False),
        check("governance", report, "Opportunity report is required", True),
    ]
    blocking = [
        value.reason
        for value in categories
        if value.blocking and value.status in {"missing", "blocked"}
    ]
    overall = (
        "blocked"
        if any(value.status == "blocked" for value in categories)
        else "missing"
        if blocking
        else "ready"
    )
    confidence = round(sum(value.status == "ready" for value in categories) / len(categories), 4)
    recommendation = (
        "reject"
        if risk_item.status == "blocked"
        else "hold"
        if blocking
        else "proceed_with_conditions"
        if any(value.status != "ready" for value in categories)
        else "proceed"
    )
    sources = {
        "commercial_viability": viability,
        "risk": risk,
        "economic_assumptions": economics,
        "profit_scenarios": scenarios or None,
        "risk_adjusted_profitability": adjusted,
        "supplier_readiness": None,
        "product_truth_readiness": truth,
        "positioning_readiness": positioning,
        "offer_readiness": offer,
        "listing_readiness": listing,
        "geo_readiness": geo,
        "creative_readiness": creative,
        "channel_readiness": channel,
    }
    conclusions = {
        name: {
            "classification": (
                "estimated"
                if name in {"economic_assumptions", "profit_scenarios"}
                else "derived"
                if name
                in {"commercial_viability", "risk", "risk_adjusted_profitability", "geo_readiness"}
                else "observed"
            )
            if value
            else "missing",
            "value": safe(value),
        }
        for name, value in sources.items()
    }
    memo = InvestmentMemo(
        opportunity_id=item.id,
        organization_id=org,
        summary={
            "title": item.title,
            "description": item.description,
            "why_now": item.timing_window,
            "assessment": safe(assessment),
            "report": safe(report),
        },
        evidence=safe(evidence),
        conclusions=conclusions,
        missing_evidence=[value.reason for value in categories if value.status == "missing"],
        confidence=confidence,
        recommended_decision=recommendation,
    )
    return memo, LaunchReadiness(
        opportunity_id=item.id,
        categories=categories,
        overall_status=overall,
        blocking_reasons=blocking,
    )


@router.get("/opportunities/{item_id}/investment-memo", response_model=InvestmentMemo)
def memo(
    item_id: UUID, organization_id: UUID, session: SessionDependency, product_id: UUID | None = None
) -> InvestmentMemo:
    return compose(session, scoped_opportunity(session, item_id, organization_id), product_id)[0]


@router.get("/opportunities/{item_id}/launch-readiness", response_model=LaunchReadiness)
def readiness(
    item_id: UUID, organization_id: UUID, session: SessionDependency, product_id: UUID | None = None
) -> LaunchReadiness:
    return compose(session, scoped_opportunity(session, item_id, organization_id), product_id)[1]


@router.post("/opportunities/{item_id}/request-investment-review", status_code=201)
def request_review(
    item_id: UUID, payload: ReviewRequest, session: SessionDependency
) -> dict[str, UUID]:
    item = scoped_opportunity(session, item_id, payload.organization_id)
    duplicate = session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.organization_id == payload.organization_id,
            ApprovalRequest.object_type == "market_opportunity",
            ApprovalRequest.object_id == item.id,
            ApprovalRequest.requested_action == "approve_investment",
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
    )
    if duplicate:
        raise ApiError(409, "conflict", "Investment review already pending.")
    approval = ApprovalWorkflowService(session).request(
        organization_id=payload.organization_id,
        project_id=payload.project_id,
        requester_id=payload.requester_id,
        object_type="market_opportunity",
        object_id=item.id,
        requested_action="approve_investment",
        reason=payload.reason,
    )
    queue = DecisionQueueItem(
        organization_id=payload.organization_id,
        title=f"Investment decision: {item.title}",
        domain="decision",
        reason=payload.reason,
        priority="high",
        required_action="approve",
        status="pending",
        approval_request_id=approval.id,
    )
    session.add(queue)
    session.commit()
    session.refresh(queue)
    return {"approval_request_id": approval.id, "decision_queue_item_id": queue.id}


@router.post("/opportunities/{item_id}/activate-approved-project", status_code=201)
def activate(
    item_id: UUID, payload: ActivateRequest, request: Request, session: SessionDependency
) -> dict[str, Any]:
    item = scoped_opportunity(session, item_id, payload.organization_id)
    approval = session.get(ApprovalRequest, payload.approval_request_id)
    if (
        approval is None
        or approval.organization_id != payload.organization_id
        or approval.status != ApprovalStatus.APPROVED
        or approval.object_type != "market_opportunity"
        or approval.object_id != item.id
        or approval.requested_action != "approve_investment"
    ):
        raise ApiError(409, "approval_required", "Approved investment authority is required.")
    if session.scalar(
        select(ProductLaunch).where(
            ProductLaunch.organization_id == payload.organization_id,
            ProductLaunch.project_id == payload.project_id,
            ProductLaunch.product_id == payload.product_id,
        )
    ):
        raise ApiError(409, "conflict", "Launch already exists.")
    service = LaunchExecutionService(session)
    launch = service.create_launch(
        ProductLaunchCreate(
            organization_id=payload.organization_id,
            project_id=payload.project_id,
            product_id=payload.product_id,
            market=item.market,
            priority=payload.priority,
        )
    )
    _, state = compose(session, item, payload.product_id)
    task_ids = []
    blocker_ids = []
    for gap in state.categories:
        if gap.status == "ready":
            continue
        title = f"Resolve {gap.category.replace('_', ' ')} gap"
        if not session.scalar(
            select(ExecutionTask).where(
                ExecutionTask.launch_id == launch.id, ExecutionTask.title == title
            )
        ):
            task = service.create_task(
                ExecutionTaskCreate(
                    organization_id=payload.organization_id,
                    launch_id=launch.id,
                    title=title,
                    description=(
                        f"{gap.reason}. Source gap: {gap.category}. No autonomous execution."
                    ),
                    owner_type="human" if gap.category == "governance" else "team",
                    priority="critical" if gap.blocking else "medium",
                )
            )
            task_ids.append(task.id)
        if gap.blocking:
            blocker = service.create_blocker(
                ExecutionBlockerCreate(
                    organization_id=payload.organization_id,
                    launch_id=launch.id,
                    reason=gap.reason,
                    severity="high",
                    impact="Launch cannot advance until resolved.",
                )
            )
            blocker_ids.append(blocker.id)
    for sequence, name in enumerate(
        (
            "product_approval",
            "supplier_ready",
            "listing_ready",
            "creative_ready",
            "channel_ready",
            "launch_ready",
        ),
        1,
    ):
        service.create_milestone(
            LaunchMilestoneCreate(
                organization_id=payload.organization_id,
                launch_id=launch.id,
                name=name,
                sequence=sequence,
            )
        )
    plan = service.create_action_plan(
        ActionPlanCreate(
            organization_id=payload.organization_id,
            plan_date=date.today(),
            related_launch_id=launch.id,
            priority=payload.priority,
            summary="Human-controlled plan generated from readiness gaps.",
            generated_from=f"opportunity-readiness:{item.id}",
        )
    )
    actor = getattr(request.state, "actor", None)
    AuditService(session).record(
        organization_id=payload.organization_id,
        actor_type=str(actor.principal_type) if isinstance(actor, User) else "system",
        actor_id=actor.id if isinstance(actor, User) else None,
        action="launch.activation",
        entity_type="product_launch",
        entity_id=launch.id,
        metadata={"approval_request_id": str(approval.id), "result": "success"},
    )
    session.commit()
    return {
        "launch_id": launch.id,
        "task_ids": task_ids,
        "blocker_ids": blocker_ids,
        "action_plan_id": plan.id,
    }


@router.get("/projects/{project_id}/daily-action-plan")
@router.get("/projects/{project_id}/execution-overview")
def overview(project_id: UUID, organization_id: UUID, session: SessionDependency) -> dict[str, Any]:
    launches = list(
        session.scalars(
            select(ProductLaunch).where(
                ProductLaunch.organization_id == organization_id,
                ProductLaunch.project_id == project_id,
            )
        )
    )
    if not launches and not first(
        session, "projects", organization_id=organization_id, id=project_id
    ):
        raise ApiError(404, "not_found", "Project was not found.")
    result = []
    for launch in launches:
        tasks = rows(
            session, "execution_tasks", organization_id=organization_id, launch_id=launch.id
        )
        milestones = rows(
            session, "launch_milestones", organization_id=organization_id, launch_id=launch.id
        )
        blockers = rows(
            session, "execution_blockers", organization_id=organization_id, launch_id=launch.id
        )
        result.append(
            {
                "launch_id": str(launch.id),
                "status": launch.status,
                "highest_priority_tasks": safe(
                    [task for task in tasks if task["status"] != "done"]
                ),
                "blocked_tasks": safe([task for task in tasks if task["status"] == "blocked"]),
                "waiting_for_human": safe(
                    [task for task in tasks if task["owner_type"] == "human"]
                ),
                "future_ai_suitable": safe([task for task in tasks if task["owner_type"] == "ai"]),
                "completed_milestones": safe(
                    [value for value in milestones if value["status"] == "done"]
                ),
                "next_milestone": safe(
                    next(
                        (
                            value
                            for value in sorted(milestones, key=lambda row: row["sequence"])
                            if value["status"] != "done"
                        ),
                        None,
                    )
                ),
                "critical_path": safe(
                    [value for value in blockers if value["status"] != "resolved"]
                ),
                "launch_readiness": "blocked"
                if any(value["status"] != "resolved" for value in blockers)
                else "ready",
            }
        )
    return {"project_id": project_id, "launches": result}
