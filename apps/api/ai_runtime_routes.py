import json
from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.ai_runtime.execution import AIExecutionService
from commerce_os.ai_runtime.models import (
    AICostObservation,
    AIModelCapability,
    AIProvider,
    AIRequest,
    PromptEvaluation,
    PromptPurpose,
    PromptTemplate,
    PromptVersion,
)
from commerce_os.ai_runtime.schemas import (
    AIExecutionResult,
    AIExecutionSubmit,
    AIRequestCreate,
    AIRequestRead,
    AIRequestTransition,
    CapabilityCreate,
    CapabilityRead,
    CostObservationCreate,
    CostObservationRead,
    PromptEvaluationCreate,
    PromptEvaluationRead,
    PromptPurposeCreate,
    PromptPurposeRead,
    PromptTemplateCreate,
    PromptTemplateRead,
    PromptVersionCreate,
    PromptVersionRead,
    ProviderCreate,
    ProviderRead,
    ResearchAnalysisComposition,
)
from commerce_os.ai_runtime.services import AIRuntimeService
from commerce_os.intelligence.research_models import ResearchAnalysis
from commerce_os.intelligence.research_schemas import ResearchAnalysisCreate, ResearchAnalysisRead
from commerce_os.intelligence.research_services import ResearchAnalystService
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.errors import ApiError
from apps.api.governance_routes import actor_id

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped = cast(Any, model)
    return list(
        session.scalars(
            select(model)
            .where(mapped.organization_id == organization_id)
            .order_by(mapped.created_at.desc())
        )
    )


@router.post("/ai/providers", response_model=ProviderRead, status_code=201)
def create_provider(
    payload: ProviderCreate, request: Request, session: SessionDependency
) -> AIProvider:
    return AIRuntimeService(session).create_provider(payload, actor_id(request))


@router.get("/ai/providers", response_model=list[ProviderRead])
def list_providers(organization_id: UUID, session: SessionDependency) -> list[AIProvider]:
    return _list(session, AIProvider, organization_id)


@router.post("/ai/model-capabilities", response_model=CapabilityRead, status_code=201)
def create_capability(
    payload: CapabilityCreate, request: Request, session: SessionDependency
) -> AIModelCapability:
    return AIRuntimeService(session).create_capability(payload, actor_id(request))


@router.get("/ai/model-capabilities", response_model=list[CapabilityRead])
def list_capabilities(organization_id: UUID, session: SessionDependency) -> list[AIModelCapability]:
    return _list(session, AIModelCapability, organization_id)


@router.post("/ai/requests", response_model=AIRequestRead, status_code=201)
def create_ai_request(
    payload: AIRequestCreate, request: Request, session: SessionDependency
) -> AIRequest:
    return AIRuntimeService(session).create_request(payload, actor_id(request))


@router.get("/ai/requests", response_model=list[AIRequestRead])
def list_ai_requests(organization_id: UUID, session: SessionDependency) -> list[AIRequest]:
    return _list(session, AIRequest, organization_id)


@router.patch("/ai/requests/{request_id}", response_model=AIRequestRead)
def transition_ai_request(
    request_id: UUID,
    payload: AIRequestTransition,
    request: Request,
    session: SessionDependency,
) -> AIRequest:
    return AIRuntimeService(session).transition_request(request_id, payload, actor_id(request))


@router.post("/ai/prompt-purposes", response_model=PromptPurposeRead, status_code=201)
def create_prompt_purpose(
    payload: PromptPurposeCreate, request: Request, session: SessionDependency
) -> PromptPurpose:
    return AIRuntimeService(session).create_purpose(payload, actor_id(request))


@router.get("/ai/prompt-purposes", response_model=list[PromptPurposeRead])
def list_prompt_purposes(organization_id: UUID, session: SessionDependency) -> list[PromptPurpose]:
    return _list(session, PromptPurpose, organization_id)


@router.post("/ai/prompt-templates", response_model=PromptTemplateRead, status_code=201)
def create_prompt_template(
    payload: PromptTemplateCreate, request: Request, session: SessionDependency
) -> PromptTemplate:
    return AIRuntimeService(session).create_template(payload, actor_id(request))


@router.get("/ai/prompt-templates", response_model=list[PromptTemplateRead])
def list_prompt_templates(
    organization_id: UUID, session: SessionDependency
) -> list[PromptTemplate]:
    return _list(session, PromptTemplate, organization_id)


@router.post("/ai/prompt-versions", response_model=PromptVersionRead, status_code=201)
def create_prompt_version(
    payload: PromptVersionCreate, request: Request, session: SessionDependency
) -> PromptVersion:
    return AIRuntimeService(session).create_version(payload, actor_id(request))


@router.get("/ai/prompt-versions", response_model=list[PromptVersionRead])
def list_prompt_versions(organization_id: UUID, session: SessionDependency) -> list[PromptVersion]:
    return _list(session, PromptVersion, organization_id)


@router.post("/ai/prompt-evaluations", response_model=PromptEvaluationRead, status_code=201)
def create_prompt_evaluation(
    payload: PromptEvaluationCreate, request: Request, session: SessionDependency
) -> PromptEvaluation:
    return AIRuntimeService(session).evaluate_prompt(payload, actor_id(request))


@router.get("/ai/prompt-evaluations", response_model=list[PromptEvaluationRead])
def list_prompt_evaluations(
    organization_id: UUID, session: SessionDependency
) -> list[PromptEvaluation]:
    return _list(session, PromptEvaluation, organization_id)


@router.post("/ai/cost-observations", response_model=CostObservationRead, status_code=201)
def create_cost_observation(
    payload: CostObservationCreate, request: Request, session: SessionDependency
) -> AICostObservation:
    return AIRuntimeService(session).observe_cost(payload, actor_id(request))


@router.get("/ai/cost-observations", response_model=list[CostObservationRead])
def list_cost_observations(
    organization_id: UUID, session: SessionDependency
) -> list[AICostObservation]:
    return _list(session, AICostObservation, organization_id)


@router.post("/ai/executions", response_model=AIRequestRead, status_code=202)
def submit_ai_execution(
    payload: AIExecutionSubmit, request: Request, session: SessionDependency
) -> AIRequest:
    return AIExecutionService(session).submit(payload, actor_id(request))


@router.post("/ai/executions/{request_id}/run", response_model=AIExecutionResult)
def run_ai_execution(
    request_id: UUID,
    organization_id: UUID,
    request: Request,
    session: SessionDependency,
) -> AIExecutionResult:
    service = AIExecutionService(session)
    entity = service.execute(service.scoped_request(request_id, organization_id), actor_id(request))
    return service.result(entity)


@router.get("/ai/executions/{request_id}", response_model=AIExecutionResult)
def inspect_ai_execution(
    request_id: UUID, organization_id: UUID, session: SessionDependency
) -> AIExecutionResult:
    service = AIExecutionService(session)
    return service.result(service.scoped_request(request_id, organization_id))


@router.get("/ai/executions/{request_id}/result", response_model=AIExecutionResult)
def inspect_ai_result(
    request_id: UUID, organization_id: UUID, session: SessionDependency
) -> AIExecutionResult:
    return inspect_ai_execution(request_id, organization_id, session)


@router.get("/ai/executions/{request_id}/usage", response_model=AIExecutionResult)
def inspect_ai_usage(
    request_id: UUID, organization_id: UUID, session: SessionDependency
) -> AIExecutionResult:
    return inspect_ai_execution(request_id, organization_id, session)


@router.post("/ai/executions/{request_id}/cancel", response_model=AIExecutionResult)
def cancel_ai_execution(
    request_id: UUID,
    organization_id: UUID,
    request: Request,
    session: SessionDependency,
) -> AIExecutionResult:
    service = AIExecutionService(session)
    entity = service.cancel(service.scoped_request(request_id, organization_id), actor_id(request))
    return service.result(entity)


@router.post(
    "/ai/executions/{request_id}/research-analysis",
    response_model=ResearchAnalysisRead,
    status_code=201,
)
def compose_research_analysis(
    request_id: UUID,
    payload: ResearchAnalysisComposition,
    request: Request,
    session: SessionDependency,
) -> ResearchAnalysis:
    execution = AIExecutionService(session).scoped_request(request_id, payload.organization_id)
    if str(execution.status) != "succeeded" or str(execution.output_classification) != "analysis":
        raise ApiError(
            409,
            "advisory_analysis_required",
            "Only successful ANALYSIS output may compose a research record.",
        )
    content = execution.response_content or {}
    summary = content.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        summary = json.dumps(content, sort_keys=True)
    return ResearchAnalystService(session).create_analysis(
        ResearchAnalysisCreate(
            organization_id=payload.organization_id,
            ai_request_id=execution.id,
            analysis_type=payload.analysis_type,
            output_classification="analysis",
            output_summary=summary,
            confidence=payload.confidence,
            methodology_version=payload.methodology_version,
        ),
        actor_id(request),
    )
