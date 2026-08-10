from typing import TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from commerce_os.operations.errors import OperationsError
from commerce_os.operations.execution_models import (
    ActionPlan,
    ExecutionBlocker,
    ExecutionTask,
    LaunchMilestone,
    ProductLaunch,
)
from commerce_os.operations.execution_schemas import (
    ActionPlanCreate,
    ExecutionBlockerCreate,
    ExecutionTaskCreate,
    LaunchMilestoneCreate,
    ProductLaunchCreate,
)
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
LAUNCH_TRANSITIONS = {
    "draft": {"approved", "cancelled"},
    "approved": {"in_progress", "cancelled"},
    "in_progress": {"blocked", "completed", "cancelled"},
    "blocked": {"in_progress", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}
WORK_TRANSITIONS = {
    "todo": {"in_progress", "blocked", "done"},
    "in_progress": {"blocked", "done"},
    "blocked": {"in_progress"},
    "done": set(),
}
BLOCKER_TRANSITIONS = {
    "open": {"acknowledged", "resolved"},
    "acknowledged": {"resolved"},
    "resolved": set(),
}


def scoped_execution(
    session: Session, model: type[EntityT], entity_id: UUID, organization_id: UUID
) -> EntityT:
    entity = session.get(model, entity_id)
    if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
        raise OperationsError("Execution record was not found in this organization.", "not_found")
    return entity


class LaunchExecutionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_launch(self, payload: ProductLaunchCreate) -> ProductLaunch:
        self._reference("projects", payload.project_id, payload.organization_id, "Project")
        self._reference("products", payload.product_id, payload.organization_id, "Product")
        return self._save(
            ProductLaunch(**payload.model_dump(), status="draft", approval_request_id=None)
        )

    def transition_launch(
        self, launch: ProductLaunch, status: str, approval_request_id: UUID | None
    ) -> ProductLaunch:
        if status not in LAUNCH_TRANSITIONS[launch.status]:
            raise OperationsError(f"Launch cannot transition from {launch.status} to {status}.")
        if status == "approved":
            self._approved_launch_request(launch, approval_request_id)
            launch.approval_request_id = approval_request_id
        launch.status = status
        return self._save(launch)

    def create_milestone(self, payload: LaunchMilestoneCreate) -> LaunchMilestone:
        self._launch(payload.launch_id, payload.organization_id)
        self._reference("roles", payload.owner_role_id, payload.organization_id, "Owner role")
        return self._save(LaunchMilestone(**payload.model_dump(), status="todo"))

    def transition_milestone(self, entity: LaunchMilestone, status: str) -> LaunchMilestone:
        if status not in WORK_TRANSITIONS[entity.status]:
            raise OperationsError(f"Work cannot transition from {entity.status} to {status}.")
        entity.status = status
        return self._save(entity)

    def transition_task(self, entity: ExecutionTask, status: str) -> ExecutionTask:
        if status not in WORK_TRANSITIONS[entity.status]:
            raise OperationsError(f"Work cannot transition from {entity.status} to {status}.")
        entity.status = status
        return self._save(entity)

    def create_task(self, payload: ExecutionTaskCreate) -> ExecutionTask:
        self._launch(payload.launch_id, payload.organization_id)
        return self._save(ExecutionTask(**payload.model_dump(), status="todo"))

    def create_action_plan(self, payload: ActionPlanCreate) -> ActionPlan:
        self._launch(payload.related_launch_id, payload.organization_id)
        return self._save(ActionPlan(**payload.model_dump()))

    def create_blocker(self, payload: ExecutionBlockerCreate) -> ExecutionBlocker:
        launch = self._launch(payload.launch_id, payload.organization_id)
        if launch.status == "in_progress":
            launch.status = "blocked"
        blocker = ExecutionBlocker(**payload.model_dump(), status="open")
        self.session.add_all([launch, blocker])
        self.session.commit()
        self.session.refresh(blocker)
        return blocker

    def transition_blocker(self, blocker: ExecutionBlocker, status: str) -> ExecutionBlocker:
        if status not in BLOCKER_TRANSITIONS[blocker.status]:
            raise OperationsError(f"Blocker cannot transition from {blocker.status} to {status}.")
        blocker.status = status
        return self._save(blocker)

    def _launch(self, launch_id: UUID, organization_id: UUID) -> ProductLaunch:
        return scoped_execution(self.session, ProductLaunch, launch_id, organization_id)

    def _approved_launch_request(
        self, launch: ProductLaunch, approval_request_id: UUID | None
    ) -> None:
        if approval_request_id is None:
            raise OperationsError("Launch approval requires an approved Governance request.")
        table = Base.metadata.tables["approval_requests"]
        request = (
            self.session.execute(
                table.select().where(
                    table.c.id == approval_request_id,
                    table.c.organization_id == launch.organization_id,
                    table.c.project_id == launch.project_id,
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            request is None
            or request["status"] != "approved"
            or request["object_type"] != "product_launch"
            or request["object_id"] != launch.id
            or request["requested_action"] != "approve_launch"
        ):
            raise OperationsError("Governance approval does not authorize this launch.")

    def _reference(
        self, table: str, reference_id: UUID | None, organization_id: UUID, label: str
    ) -> None:
        if reference_id and not reference_belongs_to_organization(
            self.session,
            table_name=table,
            reference_id=reference_id,
            organization_id=organization_id,
        ):
            raise OperationsError(f"{label} was not found in this organization.", "not_found")

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
