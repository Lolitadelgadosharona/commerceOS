"""Minimal worker readiness process; business event delivery is intentionally absent."""

from __future__ import annotations

import json
import logging
import signal
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

from commerce_os.ai_runtime.adapters import ProviderAdapter
from commerce_os.ai_runtime.execution import AIExecutionService
from commerce_os.ai_runtime.models import AIRequest
from commerce_os.ai_runtime.schemas import AIExecutionSubmit
from commerce_os.decision.creative_intelligence_models import CreativeIntelligenceRun
from commerce_os.decision.creative_intelligence_services import (
    CREATIVE_INTELLIGENCE_OUTPUT_SCHEMA,
    CreativeIntelligenceService,
    scoped_creative_intelligence,
)
from commerce_os.decision.creative_intelligence_services import (
    TEMPLATES as CREATIVE_INTELLIGENCE_TEMPLATES,
)
from commerce_os.decision.listing_geo_intelligence_models import ListingIntelligenceRun
from commerce_os.decision.listing_geo_intelligence_services import (
    LISTING_GEO_OUTPUT_SCHEMA,
    ListingIntelligenceService,
    scoped_listing_intelligence,
)
from commerce_os.decision.listing_geo_intelligence_services import (
    TEMPLATES as LISTING_GEO_TEMPLATES,
)
from commerce_os.governance.models import PrincipalType, User, UserStatus
from commerce_os.growth.discovery_models import (
    DiscoveryAutomationPlan,
    GrowthBusinessResearchResult,
    GrowthBusinessResearchRun,
    ProspectCandidate,
    ProspectDiscoveryRun,
)
from commerce_os.growth.discovery_schemas import (
    CandidateCreate,
    GovernedWebDiscoveryCreate,
    QualificationInputs,
    ResearchEvidenceCreate,
)
from commerce_os.growth.discovery_services import (
    RESEARCH_OUTPUT_SCHEMA as GROWTH_RESEARCH_OUTPUT_SCHEMA,
)
from commerce_os.growth.discovery_services import (
    WEB_DISCOVERY_OUTPUT_SCHEMA,
    GrowthDiscoveryService,
    scoped_growth_discovery,
)
from commerce_os.intelligence.business_signal_schemas import BusinessDemandSignalCreate
from commerce_os.intelligence.business_signal_services import BusinessDemandSignalService
from commerce_os.intelligence.discovery_models import OpportunityDiscoveryRun
from commerce_os.intelligence.discovery_services import (
    DISCOVERY_OUTPUT_SCHEMA,
    DISCOVERY_TEMPLATES,
    OpportunityDiscoveryService,
    scoped_discovery,
)
from commerce_os.intelligence.research_models import ResearchRun
from commerce_os.intelligence.research_schemas import ResearchAnalysisCreate, ResearchCitationCreate
from commerce_os.intelligence.research_services import (
    RESEARCH_OUTPUT_SCHEMA,
    RESEARCH_TEMPLATES,
    ResearchAnalystService,
    scoped_research,
)
from commerce_os.operations.shopify_adapter import (
    DeterministicShopifyAdapter,
    ShopifyAdapter,
    ShopifyAdapterError,
    ShopifyGraphQLAdapter,
)
from commerce_os.shared.config import get_settings
from commerce_os.shared.database import SessionLocal
from commerce_os.shared.outbox import OutboxEvent, OutboxStatus
from commerce_os.shopify_services import (
    SHOPIFY_PUBLICATION_EVENT,
    ShopifyChannelService,
)
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
running = True
WORKER_PRINCIPAL = "commerce-os-worker"
GROWTH_RESEARCH_EVENT = "growth.business_research_requested"
GROWTH_WEB_DISCOVERY_EVENT = "growth.web_discovery_requested"
MAX_JOB_ATTEMPTS = 3
WORKER_HEARTBEAT_KEY = "commerce_os:growth_worker:heartbeat"
WORKER_HEARTBEAT_TTL_SECONDS = 15


def execute_ai_request(
    session: Session,
    *,
    request_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> AIRequest:
    """Controlled worker composition path; the service identity has no approval authority."""
    service = AIExecutionService(session, adapters)
    return service.execute(
        service.scoped_request(request_id, organization_id), worker_actor_id=service_actor_id
    )


def execute_growth_business_research(
    session: Session,
    *,
    run_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> GrowthBusinessResearchRun:
    """Execute evidence-only business research without outreach or opportunity creation."""
    growth = GrowthDiscoveryService(session)
    run = scoped_growth_discovery(session, GrowthBusinessResearchRun, run_id, organization_id)
    if run.status != "queued":
        raise ValueError("Only queued GrowthOS business research may execute.")
    evidence = growth.evidence(run)
    execution = AIExecutionService(session, adapters)
    request = execution.submit(
        AIExecutionSubmit(
            organization_id=organization_id,
            purpose="Governed GrowthOS business research",
            context_type="growth_business_research_run",
            context_reference=str(run.id),
            capability_id=run.capability_id,
            prompt_version_id=run.prompt_version_id,
            task_type="business_analysis",
            system_instructions=(
                "Analyze only the supplied prospect evidence. Produce advisory business "
                "research and explicitly list missing information and risk. Never contact "
                "the business, create an opportunity, sales record, invoice, approval, or "
                "external action."
            ),
            input_content=json.dumps(
                {
                    "candidate_id": str(run.candidate_id),
                    "evidence_references": [
                        {
                            "id": str(item.id),
                            "type": item.evidence_type,
                            "source_url": item.source_url,
                            "observation": item.observation,
                            "confidence": item.confidence,
                        }
                        for item in evidence
                    ],
                },
                sort_keys=True,
            ),
            output_classification="analysis",
            expected_output_schema=GROWTH_RESEARCH_OUTPUT_SCHEMA,
            runtime_configuration={"max_output_tokens": 2000},
            provenance_context={
                "source_domain": "growth",
                "growth_business_research_run_id": str(run.id),
                "methodology_version": run.methodology_version,
            },
        ),
        service_actor_id,
    )
    run = growth.start_research(run, request.id, service_actor_id)
    request = execution.execute(request, worker_actor_id=service_actor_id)
    if str(request.status) != "succeeded" or request.response_content is None:
        return growth.fail_research(
            run, request.failure_reason or "Governed AI execution failed.", service_actor_id
        )
    run = growth.complete_research(run, request.response_content, service_actor_id)
    result = session.scalar(
        select(GrowthBusinessResearchResult).where(
            GrowthBusinessResearchResult.research_run_id == run.id
        )
    )
    candidate = session.get(ProspectCandidate, run.candidate_id)
    if result is None or candidate is None:
        raise ValueError("Completed business research is missing its scoped result or candidate.")
    evidence_refs = [str(item.id) for item in evidence]
    signals = BusinessDemandSignalService(session)
    for issue in result.potential_growth_issues:
        signals.create(
            BusinessDemandSignalCreate(
                organization_id=organization_id,
                source_domain="growth",
                industry=candidate.category,
                signal_type="business_growth_issue",
                description=issue,
                evidence_reference=evidence_refs,
                confidence=result.confidence,
                source_research_result_id=result.id,
            ),
            service_actor_id,
        )
    return run


def execute_growth_web_discovery(
    session: Session,
    *,
    run_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    capability_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> ProspectDiscoveryRun:
    """Discover public candidates as evidence only; never activate or contact them."""
    growth = GrowthDiscoveryService(session)
    run = scoped_growth_discovery(session, ProspectDiscoveryRun, run_id, organization_id)
    if run.status != "queued":
        raise ValueError("Only queued governed web discovery may execute.")
    run = growth.transition_run(run, "running", service_actor_id)
    target_count = min(10, max(1, int(run.query_criteria.get("target_count", 10))))
    execution = AIExecutionService(session, adapters)
    request = execution.submit(
        AIExecutionSubmit(
            organization_id=organization_id,
            purpose="Governed public prospect discovery",
            context_type="prospect_discovery_run",
            context_reference=str(run.id),
            capability_id=capability_id,
            prompt_version_id=None,
            task_type="public_prospect_discovery",
            system_instructions=(
                "Search only publicly accessible web sources for real businesses matching the "
                "requested industry, geography, and founder criteria. Return only candidates "
                "worth human review, at most the requested count. Every "
                "candidate must include a directly supporting public source URL and a concise "
                "observed fact. Extract evidence-backed pain points and recommend four 0-100 "
                "qualification inputs: pain signal, purchase probability, accessibility, and "
                "quick-win potential. Use null for any input not supported by public evidence. "
                "Explain the qualification and how the candidate matches the founder filter. "
                "Do not invent missing facts, scrape restricted pages, contact anyone, approve, "
                "activate, create gifts, or send outreach."
            ),
            input_content=json.dumps(
                {
                    "industry": run.target_industry,
                    "geography": run.target_location,
                    "criteria": run.query_criteria.get("criteria", ""),
                    "maximum_candidates": target_count,
                },
                sort_keys=True,
            ),
            output_classification="candidate",
            expected_output_schema=WEB_DISCOVERY_OUTPUT_SCHEMA,
            runtime_configuration={"max_output_tokens": 3500, "web_search": True},
            provenance_context={
                "source_domain": "growth",
                "discovery_run_id": str(run.id),
                "public_evidence_only": True,
            },
        ),
        service_actor_id,
    )
    request = execution.execute(request, worker_actor_id=service_actor_id)
    if str(request.status) != "succeeded" or request.response_content is None:
        return growth.transition_run(
            run,
            "failed",
            service_actor_id,
            request.failure_reason or "Governed web discovery failed.",
        )
    for item in request.response_content.get("candidates", [])[:target_count]:
        confidence = float(item["confidence"])
        if not 0 <= confidence <= 1 or not str(item["source_url"]).startswith(
            ("http://", "https://")
        ):
            continue
        candidate = growth.create_candidate(
            CandidateCreate(
                organization_id=organization_id,
                discovery_run_id=run.id,
                business_name=str(item["business_name"]),
                website=item.get("website"),
                location=str(item["location"]),
                category=str(item["category"]),
                source_reference=str(item["source_url"]),
                confidence=confidence,
            ),
            service_actor_id,
        )
        growth.create_evidence(
            ResearchEvidenceCreate(
                organization_id=organization_id,
                candidate_id=candidate.id,
                evidence_type="governed_web_search",
                source_url=str(item["source_url"]),
                observation=str(item["evidence"]),
                confidence=confidence,
                collected_at=datetime.now(UTC),
            ),
            service_actor_id,
        )
        for pain_point in item.get("pain_points", []):
            growth.create_evidence(
                ResearchEvidenceCreate(
                    organization_id=organization_id,
                    candidate_id=candidate.id,
                    evidence_type="observed_growth_pain",
                    source_url=str(item["source_url"]),
                    observation=str(pain_point),
                    confidence=confidence,
                    collected_at=datetime.now(UTC),
                ),
                service_actor_id,
            )
        qualification = item.get("qualification", {})
        assessment = growth.qualify(
            candidate,
            QualificationInputs(
                organization_id=organization_id,
                pain_signal=qualification.get("pain_signal"),
                purchase_probability=qualification.get("purchase_probability"),
                accessibility=qualification.get("accessibility"),
                quick_win_potential=qualification.get("quick_win_potential"),
            ),
            service_actor_id,
        )
        assessment.explanation = (
            f"{item.get('qualification_rationale', 'Qualification evidence is incomplete.')} "
            f"Filter match: {item.get('filter_match', 'Not evaluated.')} "
            "Scores are advisory evidence-backed recommendations; missing values remain unknown."
        )
        session.add(assessment)
        session.commit()
    return growth.transition_run(run, "completed", service_actor_id)


def execute_research_run(
    session: Session,
    *,
    run_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> ResearchRun:
    research = ResearchAnalystService(session)
    run = scoped_research(session, ResearchRun, run_id, organization_id)
    if run.status != "queued":
        raise ValueError("Only queued research runs may be executed by the worker.")
    evidence = research.run_evidence(run.id, organization_id)
    template = RESEARCH_TEMPLATES[run.research_type]
    execution = AIExecutionService(session, adapters)
    request = execution.submit(
        AIExecutionSubmit(
            organization_id=organization_id,
            purpose=f"Governed research: {run.research_type}",
            context_type="research_run",
            context_reference=str(run.id),
            capability_id=run.capability_id,
            prompt_version_id=run.prompt_version_id,
            task_type=run.research_type,
            system_instructions=(
                "Analyze only the supplied evidence references. Return advisory research; "
                "never approve or execute a business action. "
                "Mark unsupported claims as missing evidence."
            ),
            input_content=json.dumps(
                {
                    "objective": run.objective,
                    "evidence_references": [
                        {
                            "type": item.evidence_type,
                            "id": str(item.evidence_id),
                            "source_reference": item.source_reference,
                        }
                        for item in evidence
                    ],
                },
                sort_keys=True,
            ),
            output_classification=template[2],
            expected_output_schema=RESEARCH_OUTPUT_SCHEMA,
            runtime_configuration={"max_output_tokens": 2000},
            provenance_context={
                "source_domain": "intelligence",
                "research_run_id": str(run.id),
                "methodology_version": run.methodology_version,
            },
        ),
        service_actor_id,
    )
    run = research.start_run(run, request.id, service_actor_id)
    request = execution.execute(request, worker_actor_id=service_actor_id)
    if str(request.status) != "succeeded" or request.response_content is None:
        return research.fail_run(
            run, request.failure_reason or "Governed AI execution failed.", service_actor_id
        )
    content = request.response_content
    analysis = research.create_analysis(
        ResearchAnalysisCreate(
            organization_id=organization_id,
            ai_request_id=request.id,
            analysis_type=run.research_type,
            output_classification=template[2],
            output_summary=str(content["summary"]),
            confidence=float(content["confidence"]),
            methodology_version=run.methodology_version,
        ),
        service_actor_id,
    )
    for item in evidence:
        research.add_citation(
            ResearchCitationCreate(
                organization_id=organization_id,
                analysis_id=analysis.id,
                evidence_type=item.evidence_type,
                evidence_id=item.evidence_id,
                source_reference=item.source_reference,
                citation_note="Evidence supplied to governed research execution.",
                relevance_score=item.confidence,
                citation_location="structured_output.evidence_used",
                methodology_version=run.methodology_version,
                missing_evidence=False,
            ),
            service_actor_id,
        )
    return research.complete_run(run, analysis.id, service_actor_id)


def execute_opportunity_discovery_run(
    session: Session,
    *,
    run_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> OpportunityDiscoveryRun:
    discovery = OpportunityDiscoveryService(session)
    run = scoped_discovery(session, OpportunityDiscoveryRun, run_id, organization_id)
    if run.status != "queued":
        raise ValueError("Only queued discovery runs may be executed by the worker.")
    evidence = discovery.evidence(run.id, organization_id)
    execution = AIExecutionService(session, adapters)
    request = execution.submit(
        AIExecutionSubmit(
            organization_id=organization_id,
            purpose=f"Governed opportunity discovery: {run.discovery_type}",
            context_type="opportunity_discovery_run",
            context_reference=str(run.id),
            capability_id=run.capability_id,
            prompt_version_id=run.prompt_version_id,
            task_type=run.discovery_type,
            system_instructions=(
                "Identify evidence-backed opportunity candidates only. Never approve, create a "
                "MarketOpportunity, create products or launches, or execute business actions. "
                "Return missing evidence explicitly."
            ),
            input_content=json.dumps(
                {
                    "objective": run.objective,
                    "evidence_references": [
                        {
                            "type": item.evidence_type,
                            "id": str(item.evidence_id),
                            "source_reference": item.source_reference,
                        }
                        for item in evidence
                    ],
                },
                sort_keys=True,
            ),
            output_classification="candidate",
            expected_output_schema=DISCOVERY_OUTPUT_SCHEMA,
            runtime_configuration={"max_output_tokens": 2000},
            provenance_context={
                "source_domain": "intelligence",
                "discovery_run_id": str(run.id),
                "methodology_version": run.methodology_version,
                "template": DISCOVERY_TEMPLATES[run.discovery_type][0],
            },
        ),
        service_actor_id,
    )
    run = discovery.start(run, request.id, service_actor_id)
    request = execution.execute(request, worker_actor_id=service_actor_id)
    if str(request.status) != "succeeded" or request.response_content is None:
        return discovery.fail(
            run, request.failure_reason or "Governed AI execution failed.", service_actor_id
        )
    discovery.complete(run, request.response_content, service_actor_id)
    session.refresh(run)
    return run


def execute_creative_intelligence_run(
    session: Session,
    *,
    run_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> CreativeIntelligenceRun:
    creative = CreativeIntelligenceService(session)
    run = scoped_creative_intelligence(session, CreativeIntelligenceRun, run_id, organization_id)
    if run.status != "queued":
        raise ValueError("Only queued creative intelligence runs may execute.")
    evidence = creative.evidence(run.id, organization_id)
    execution = AIExecutionService(session, adapters)
    request = execution.submit(
        AIExecutionSubmit(
            organization_id=organization_id,
            purpose=f"Governed creative intelligence: {run.template_type}",
            context_type="creative_intelligence_run",
            context_reference=str(run.id),
            capability_id=run.capability_id,
            prompt_version_id=run.prompt_version_id,
            task_type=run.template_type,
            system_instructions=(
                "Create an evidence-grounded creative recommendation only. Remain advisory, "
                "preserve every source-domain record, and use only supplied evidence references."
            ),
            input_content=json.dumps(
                {
                    "objective": run.objective,
                    "template": CREATIVE_INTELLIGENCE_TEMPLATES[run.template_type],
                    "evidence_references": [
                        {
                            "type": item.evidence_type,
                            "id": str(item.evidence_id),
                            "source_reference": item.source_reference,
                        }
                        for item in evidence
                    ],
                },
                sort_keys=True,
            ),
            output_classification="recommendation",
            expected_output_schema=CREATIVE_INTELLIGENCE_OUTPUT_SCHEMA,
            runtime_configuration={"max_output_tokens": 2000},
            provenance_context={
                "source_domain": "decision",
                "creative_run_id": str(run.id),
                "methodology_version": run.methodology_version,
            },
        ),
        service_actor_id,
    )
    run = creative.start(run, request.id, service_actor_id)
    request = execution.execute(request, worker_actor_id=service_actor_id)
    if str(request.status) != "succeeded" or request.response_content is None:
        return creative.fail(
            run, request.failure_reason or "Governed AI execution failed.", service_actor_id
        )
    creative.complete(run, request.response_content, service_actor_id)
    session.refresh(run)
    return run


def execute_listing_intelligence_run(
    session: Session,
    *,
    run_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> ListingIntelligenceRun:
    listing = ListingIntelligenceService(session)
    run = scoped_listing_intelligence(session, ListingIntelligenceRun, run_id, organization_id)
    if run.status != "queued":
        raise ValueError("Only queued listing intelligence runs may execute.")
    evidence = listing.evidence(run.id, organization_id)
    execution = AIExecutionService(session, adapters)
    request = execution.submit(
        AIExecutionSubmit(
            organization_id=organization_id,
            purpose=f"Governed listing intelligence: {run.template_type}",
            context_type="listing_intelligence_run",
            context_reference=str(run.id),
            capability_id=run.capability_id,
            prompt_version_id=run.prompt_version_id,
            task_type=run.template_type,
            system_instructions=(
                "Create evidence-grounded listing and GEO recommendations only. Remain "
                "advisory, preserve every source-domain record, and use only supplied evidence "
                "references."
            ),
            input_content=json.dumps(
                {
                    "objective": run.objective,
                    "template": LISTING_GEO_TEMPLATES[run.template_type],
                    "evidence_references": [
                        {
                            "type": x.evidence_type,
                            "id": str(x.evidence_id),
                            "source_reference": x.source_reference,
                        }
                        for x in evidence
                    ],
                },
                sort_keys=True,
            ),
            output_classification="recommendation",
            expected_output_schema=LISTING_GEO_OUTPUT_SCHEMA,
            runtime_configuration={"max_output_tokens": 3000},
            provenance_context={
                "source_domain": "decision",
                "listing_run_id": str(run.id),
                "methodology_version": run.methodology_version,
            },
        ),
        service_actor_id,
    )
    run = listing.start(run, request.id, service_actor_id)
    request = execution.execute(request, worker_actor_id=service_actor_id)
    if str(request.status) != "succeeded" or request.response_content is None:
        return listing.fail(
            run, request.failure_reason or "Governed AI execution failed.", service_actor_id
        )
    listing.complete(run, request.response_content, service_actor_id)
    session.refresh(run)
    return run


def stop_worker(_signum: int, _frame: object) -> None:
    global running
    running = False


def consume_growth_job(session: Session, event: OutboxEvent) -> None:
    """Execute one durable, organization-scoped Growth research job."""
    if event.event_type not in {GROWTH_RESEARCH_EVENT, GROWTH_WEB_DISCOVERY_EVENT}:
        raise ValueError("Unsupported worker event type.")
    run_id = UUID(str(event.payload["run_id"]))
    if event.event_type == GROWTH_RESEARCH_EVENT:
        run_status = scoped_growth_discovery(
            session, GrowthBusinessResearchRun, run_id, event.organization_id
        ).status
    else:
        run_status = scoped_growth_discovery(
            session, ProspectDiscoveryRun, run_id, event.organization_id
        ).status
    if run_status in {"completed", "failed", "cancelled"}:
        return
    if run_status != "queued":
        raise ValueError(f"Growth job is not executable from {run_status}.")
    worker = session.scalar(
        select(User)
        .where(
            User.organization_id == event.organization_id,
            User.principal_type == PrincipalType.SERVICE,
            User.status == UserStatus.ACTIVE,
        )
        .order_by(User.created_at)
        .limit(1)
    )
    if worker is None:
        raise ValueError("No active service identity is configured for this organization.")
    if event.event_type == GROWTH_RESEARCH_EVENT:
        execute_growth_business_research(
            session,
            run_id=run_id,
            organization_id=event.organization_id,
            service_actor_id=worker.id,
        )
    else:
        execute_growth_web_discovery(
            session,
            run_id=run_id,
            organization_id=event.organization_id,
            service_actor_id=worker.id,
            capability_id=UUID(str(event.payload["capability_id"])),
        )


def consume_shopify_job(
    session: Session,
    event: OutboxEvent,
    adapter: ShopifyAdapter | None = None,
) -> None:
    """Execute one explicitly authorized Shopify publication with a service identity."""
    if event.event_type != SHOPIFY_PUBLICATION_EVENT:
        raise ValueError("Unsupported Shopify worker event type.")
    publication_id = UUID(str(event.payload["publication_id"]))
    worker = session.scalar(
        select(User)
        .where(
            User.organization_id == event.organization_id,
            User.principal_type == PrincipalType.SERVICE,
            User.status == UserStatus.ACTIVE,
        )
        .order_by(User.created_at)
        .limit(1)
    )
    if worker is None:
        raise ValueError("No active service identity is configured for this organization.")
    service = ShopifyChannelService(session)
    publication = service.scoped_publication(publication_id, event.organization_id)
    connection = service.connection(publication.connection_id, event.organization_id)
    if adapter is None:
        adapter = (
            DeterministicShopifyAdapter(connection.store_domain)
            if connection.authentication_mode == "mock"
            else ShopifyGraphQLAdapter(
                store_domain=connection.store_domain,
                api_version=connection.api_version,
                credential_reference=connection.credential_reference,
            )
        )
    service.execute(publication.id, event.organization_id, worker.id, adapter)


def process_next_growth_job(session: Session) -> bool:
    """Claim and process one durable job; retries remain visible and bounded."""
    now = datetime.now(UTC)
    event = session.scalar(
        select(OutboxEvent)
        .where(
            OutboxEvent.event_type.in_([GROWTH_RESEARCH_EVENT, GROWTH_WEB_DISCOVERY_EVENT]),
            OutboxEvent.status.in_(
                [OutboxStatus.PENDING, OutboxStatus.FAILED, OutboxStatus.PROCESSING]
            ),
            OutboxEvent.available_at <= now,
            OutboxEvent.attempts < MAX_JOB_ATTEMPTS,
        )
        .order_by(OutboxEvent.occurred_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if event is None:
        return False
    event_id = event.id
    event.status = OutboxStatus.PROCESSING
    event.attempts += 1
    event.available_at = now + timedelta(minutes=5)
    session.commit()
    try:
        consume_growth_job(session, event)
        event = session.get(OutboxEvent, event_id)
        if event is None:
            raise ValueError("Claimed Growth job disappeared.")
        event.status = OutboxStatus.PUBLISHED
        event.published_at = datetime.now(UTC)
        event.last_error = None
        session.commit()
    except Exception as exc:
        session.rollback()
        event = session.get(OutboxEvent, event_id)
        if event is not None:
            event.status = OutboxStatus.FAILED
            event.last_error = str(exc)[:2000]
            event.available_at = datetime.now(UTC) + timedelta(seconds=min(60, 2**event.attempts))
            session.commit()
        logger.exception("Growth research job failed; id=%s", event.id if event else "unknown")
    return True


def process_next_shopify_job(session: Session) -> bool:
    """Claim one publication event; retry only safe transient connector failures."""
    now = datetime.now(UTC)
    event = session.scalar(
        select(OutboxEvent)
        .where(
            OutboxEvent.event_type == SHOPIFY_PUBLICATION_EVENT,
            OutboxEvent.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]),
            OutboxEvent.available_at <= now,
            OutboxEvent.attempts < MAX_JOB_ATTEMPTS,
        )
        .order_by(OutboxEvent.occurred_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if event is None:
        return False
    event_id = event.id
    event.status = OutboxStatus.PROCESSING
    event.attempts += 1
    session.commit()
    try:
        consume_shopify_job(session, event)
        event = session.get(OutboxEvent, event_id)
        if event is None:
            raise ValueError("Claimed Shopify job disappeared.")
        event.status = OutboxStatus.PUBLISHED
        event.published_at = datetime.now(UTC)
        event.last_error = None
        session.commit()
    except ShopifyAdapterError as exc:
        session.rollback()
        event = session.get(OutboxEvent, event_id)
        if event is not None:
            event.status = OutboxStatus.FAILED
            event.last_error = f"{exc.category}: {str(exc)}"[:2000]
            event.available_at = (
                datetime.now(UTC) + timedelta(seconds=min(60, 2**event.attempts))
                if exc.retryable
                else datetime.max.replace(tzinfo=UTC)
            )
            session.commit()
        logger.warning("Shopify publication failed safely; category=%s", exc.category)
    except Exception as exc:
        session.rollback()
        event = session.get(OutboxEvent, event_id)
        if event is not None:
            event.status = OutboxStatus.FAILED
            event.last_error = f"business_rule: {str(exc)}"[:2000]
            event.available_at = datetime.max.replace(tzinfo=UTC)
            session.commit()
        logger.warning("Shopify publication rejected before external execution.")
    return True


def schedule_due_web_discovery(session: Session) -> bool:
    """Queue one due, founder-configured daily plan; execution remains evidence-only."""
    now = datetime.now(UTC)
    plan = session.scalar(
        select(DiscoveryAutomationPlan)
        .where(
            DiscoveryAutomationPlan.status == "active",
            DiscoveryAutomationPlan.next_run_at.is_not(None),
            DiscoveryAutomationPlan.next_run_at <= now,
            DiscoveryAutomationPlan.query_criteria["mode"].as_string() == "governed_web_search",
        )
        .order_by(DiscoveryAutomationPlan.next_run_at)
        .limit(1)
    )
    if plan is None:
        return False
    capability_id = plan.query_criteria.get("capability_id")
    if not capability_id:
        plan.status = "disabled"
        session.commit()
        return False
    GrowthDiscoveryService(session).create_governed_web_discovery(
        GovernedWebDiscoveryCreate(
            organization_id=plan.organization_id,
            capability_id=UUID(str(capability_id)),
            industry=plan.industry,
            geography=plan.geography,
            target_count=int(plan.query_criteria.get("target_count", 10)),
            criteria=str(plan.query_criteria.get("criteria", "")),
        ),
        plan.created_by,
    )
    return True


def main() -> None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    client.ping()
    logger.info(
        "Commerce OS worker ready; governed connector execution available; principal=%s",
        WORKER_PRINCIPAL,
    )
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)
    while running:
        client.set(
            WORKER_HEARTBEAT_KEY,
            datetime.now(UTC).isoformat(),
            ex=WORKER_HEARTBEAT_TTL_SECONDS,
        )
        with SessionLocal() as session:
            scheduled = schedule_due_web_discovery(session)
            processed = process_next_shopify_job(session) or process_next_growth_job(session)
        if not processed and not scheduled:
            time.sleep(1)


if __name__ == "__main__":
    main()
