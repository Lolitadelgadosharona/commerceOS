from typing import Annotated, Any, TypeVar, cast
from uuid import UUID

from commerce_os.operations.execution_models import (
    ActionPlan,
    ExecutionBlocker,
    ExecutionTask,
    LaunchMilestone,
    ProductLaunch,
)
from commerce_os.operations.execution_schemas import (
    ActionPlanCreate,
    ActionPlanRead,
    ExecutionBlockerCreate,
    ExecutionBlockerRead,
    ExecutionBlockerUpdate,
    ExecutionTaskCreate,
    ExecutionTaskRead,
    ExecutionTaskUpdate,
    LaunchMilestoneCreate,
    LaunchMilestoneRead,
    LaunchMilestoneUpdate,
    ProductLaunchCreate,
    ProductLaunchRead,
    ProductLaunchUpdate,
)
from commerce_os.operations.execution_services import LaunchExecutionService, scoped_execution
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    mapped_model = cast(Any, model)
    statement = select(model).where(mapped_model.organization_id == organization_id)
    if model is LaunchMilestone:
        statement = statement.order_by(LaunchMilestone.launch_id, LaunchMilestone.sequence)
    else:
        statement = statement.order_by(mapped_model.created_at.desc())
    return list(session.scalars(statement))


@router.post("/product-launches", response_model=ProductLaunchRead, status_code=201)
def create_launch(payload: ProductLaunchCreate, session: SessionDependency) -> ProductLaunch:
    return LaunchExecutionService(session).create_launch(payload)


@router.get("/product-launches", response_model=list[ProductLaunchRead])
def list_launches(organization_id: UUID, session: SessionDependency) -> list[ProductLaunch]:
    return _list(session, ProductLaunch, organization_id)


@router.patch("/product-launches/{launch_id}", response_model=ProductLaunchRead)
def transition_launch(
    launch_id: UUID,
    organization_id: UUID,
    payload: ProductLaunchUpdate,
    session: SessionDependency,
) -> ProductLaunch:
    launch = scoped_execution(session, ProductLaunch, launch_id, organization_id)
    return LaunchExecutionService(session).transition_launch(
        launch, payload.status, payload.approval_request_id
    )


@router.post("/launch-milestones", response_model=LaunchMilestoneRead, status_code=201)
def create_milestone(payload: LaunchMilestoneCreate, session: SessionDependency) -> LaunchMilestone:
    return LaunchExecutionService(session).create_milestone(payload)


@router.get("/launch-milestones", response_model=list[LaunchMilestoneRead])
def list_milestones(organization_id: UUID, session: SessionDependency) -> list[LaunchMilestone]:
    return _list(session, LaunchMilestone, organization_id)


@router.patch("/launch-milestones/{milestone_id}", response_model=LaunchMilestoneRead)
def transition_milestone(
    milestone_id: UUID,
    organization_id: UUID,
    payload: LaunchMilestoneUpdate,
    session: SessionDependency,
) -> LaunchMilestone:
    milestone = scoped_execution(session, LaunchMilestone, milestone_id, organization_id)
    return LaunchExecutionService(session).transition_milestone(milestone, payload.status)


@router.post("/execution-tasks", response_model=ExecutionTaskRead, status_code=201)
def create_task(payload: ExecutionTaskCreate, session: SessionDependency) -> ExecutionTask:
    return LaunchExecutionService(session).create_task(payload)


@router.get("/execution-tasks", response_model=list[ExecutionTaskRead])
def list_tasks(organization_id: UUID, session: SessionDependency) -> list[ExecutionTask]:
    return _list(session, ExecutionTask, organization_id)


@router.patch("/execution-tasks/{task_id}", response_model=ExecutionTaskRead)
def transition_task(
    task_id: UUID,
    organization_id: UUID,
    payload: ExecutionTaskUpdate,
    session: SessionDependency,
) -> ExecutionTask:
    task = scoped_execution(session, ExecutionTask, task_id, organization_id)
    return LaunchExecutionService(session).transition_task(task, payload.status)


@router.post("/action-plans", response_model=ActionPlanRead, status_code=201)
def create_action_plan(payload: ActionPlanCreate, session: SessionDependency) -> ActionPlan:
    return LaunchExecutionService(session).create_action_plan(payload)


@router.get("/action-plans", response_model=list[ActionPlanRead])
def list_action_plans(organization_id: UUID, session: SessionDependency) -> list[ActionPlan]:
    return _list(session, ActionPlan, organization_id)


@router.post("/execution-blockers", response_model=ExecutionBlockerRead, status_code=201)
def create_blocker(payload: ExecutionBlockerCreate, session: SessionDependency) -> ExecutionBlocker:
    return LaunchExecutionService(session).create_blocker(payload)


@router.get("/execution-blockers", response_model=list[ExecutionBlockerRead])
def list_blockers(organization_id: UUID, session: SessionDependency) -> list[ExecutionBlocker]:
    return _list(session, ExecutionBlocker, organization_id)


@router.patch("/execution-blockers/{blocker_id}", response_model=ExecutionBlockerRead)
def transition_blocker(
    blocker_id: UUID,
    organization_id: UUID,
    payload: ExecutionBlockerUpdate,
    session: SessionDependency,
) -> ExecutionBlocker:
    blocker = scoped_execution(session, ExecutionBlocker, blocker_id, organization_id)
    return LaunchExecutionService(session).transition_blocker(blocker, payload.status)
