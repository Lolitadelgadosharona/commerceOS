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
