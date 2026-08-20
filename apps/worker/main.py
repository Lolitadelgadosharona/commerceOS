"""Minimal worker readiness process; business event delivery is intentionally absent."""

from __future__ import annotations

import json
import logging
import signal
import time
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
from commerce_os.shared.config import get_settings
from redis import Redis
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
running = True
WORKER_PRINCIPAL = "commerce-os-worker"


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


def main() -> None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    client.ping()
    logger.info(
        "Commerce OS worker ready; external delivery disabled; principal=%s",
        WORKER_PRINCIPAL,
    )
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)
    while running:
        time.sleep(1)


if __name__ == "__main__":
    main()
