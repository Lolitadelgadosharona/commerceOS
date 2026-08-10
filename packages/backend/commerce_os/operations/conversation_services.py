from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.operations.conversation_models import (
    ConversationEmotionSignal,
    ConversationHandoff,
    ConversationIntent,
    ConversationKnowledgeReference,
    ConversationMessage,
    ConversationThread,
    ThreadStatus,
)
from commerce_os.operations.conversation_schemas import (
    EmotionCreate,
    HandoffCreate,
    HandoffUpdate,
    IntentCreate,
    KnowledgeCreate,
    MessageCreate,
    ThreadCreate,
)
from commerce_os.operations.errors import OperationsError
from commerce_os.shared.database import Base
from commerce_os.shared.scope import reference_belongs_to_organization

EntityT = TypeVar("EntityT", bound=Base)
THREAD_TRANSITIONS = {
    "open": {"waiting", "resolved", "escalated", "archived"},
    "waiting": {"open", "resolved", "escalated", "archived"},
    "escalated": {"waiting", "resolved", "archived"},
    "resolved": {"open", "archived"},
    "archived": set(),
}
HANDOFF_TRANSITIONS = {
    "pending": {"assigned", "resolved", "cancelled"},
    "assigned": {"resolved", "cancelled"},
    "resolved": set(),
    "cancelled": set(),
}
KNOWLEDGE_TABLES = {
    "product_truth": "product_truth",
    "product_knowledge": "product_knowledge_items",
    "claim_policy": "product_claim_policies",
    "faq": "product_knowledge_items",
}


def scoped_thread(session: Session, entity_id: UUID, organization_id: UUID) -> ConversationThread:
    entity = session.get(ConversationThread, entity_id)
    if entity is None or entity.organization_id != organization_id:
        raise OperationsError("Conversation was not found in this organization.", "not_found")
    return entity


def scoped_message(session: Session, entity_id: UUID, organization_id: UUID) -> ConversationMessage:
    entity = session.get(ConversationMessage, entity_id)
    if entity is None or entity.organization_id != organization_id:
        raise OperationsError("Message was not found in this organization.", "not_found")
    return entity


class ConversationService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_thread(self, payload: ThreadCreate) -> ConversationThread:
        self._validate_reference(
            "customers", payload.customer_id, payload.organization_id, "Customer"
        )
        self._validate_reference("roles", payload.assigned_role_id, payload.organization_id, "Role")
        return self._save(ConversationThread(**payload.model_dump(), status=ThreadStatus.OPEN))

    def transition_thread(
        self, thread: ConversationThread, status: ThreadStatus
    ) -> ConversationThread:
        if status.value not in THREAD_TRANSITIONS[str(thread.status)]:
            raise OperationsError(
                f"Conversation cannot transition from {thread.status} to {status}."
            )
        thread.status = status
        return self._save(thread)

    def create_message(self, payload: MessageCreate) -> ConversationMessage:
        thread = scoped_thread(self.session, payload.thread_id, payload.organization_id)
        if thread.status in {ThreadStatus.RESOLVED, ThreadStatus.ARCHIVED}:
            raise OperationsError(
                "Messages cannot be added to a resolved or archived conversation."
            )
        if payload.sender_type == "customer" and payload.direction != "inbound":
            raise OperationsError("Customer messages must be inbound.")
        if payload.sender_type in {"human", "system", "ai"} and payload.direction != "outbound":
            raise OperationsError("Human, system, and AI messages must be outbound.")
        sequence = self.session.scalar(
            select(func.coalesce(func.max(ConversationMessage.sequence), 0)).where(
                ConversationMessage.thread_id == payload.thread_id
            )
        )
        return self._save(
            ConversationMessage(**payload.model_dump(), sequence=int(sequence or 0) + 1)
        )

    def create_intent(self, payload: IntentCreate) -> ConversationIntent:
        scoped_message(self.session, payload.message_id, payload.organization_id)
        return self._save(ConversationIntent(**payload.model_dump()))

    def create_emotion(self, payload: EmotionCreate) -> ConversationEmotionSignal:
        scoped_message(self.session, payload.message_id, payload.organization_id)
        return self._save(ConversationEmotionSignal(**payload.model_dump()))

    def create_handoff(self, payload: HandoffCreate) -> ConversationHandoff:
        thread = scoped_thread(self.session, payload.thread_id, payload.organization_id)
        self._validate_reference("users", payload.assigned_user_id, payload.organization_id, "User")
        thread.status = ThreadStatus.ESCALATED
        handoff = ConversationHandoff(**payload.model_dump(), status="pending", resolved_at=None)
        self.session.add_all([thread, handoff])
        self.session.commit()
        self.session.refresh(handoff)
        return handoff

    def transition_handoff(
        self, handoff: ConversationHandoff, payload: HandoffUpdate
    ) -> ConversationHandoff:
        if payload.status not in HANDOFF_TRANSITIONS[handoff.status]:
            raise OperationsError(
                f"Handoff cannot transition from {handoff.status} to {payload.status}."
            )
        self._validate_reference("users", payload.assigned_user_id, handoff.organization_id, "User")
        if payload.status == "assigned" and payload.assigned_user_id is None:
            raise OperationsError("Assigned handoffs require an assigned user.")
        if payload.assigned_user_id is not None:
            handoff.assigned_user_id = payload.assigned_user_id
        handoff.status = payload.status
        handoff.resolved_at = datetime.now(UTC) if payload.status == "resolved" else None
        return self._save(handoff)

    def create_knowledge(self, payload: KnowledgeCreate) -> ConversationKnowledgeReference:
        scoped_thread(self.session, payload.thread_id, payload.organization_id)
        self._validate_reference(
            KNOWLEDGE_TABLES[payload.reference_type],
            payload.reference_id,
            payload.organization_id,
            "Knowledge reference",
        )
        if payload.reference_type == "faq":
            table = Base.metadata.tables["product_knowledge_items"]
            faq_id = self.session.execute(
                select(table.c.id).where(
                    table.c.id == payload.reference_id,
                    table.c.organization_id == payload.organization_id,
                    table.c.type == "faq",
                )
            ).scalar_one_or_none()
            if faq_id is None:
                raise OperationsError(
                    "FAQ reference must point to an organization-scoped FAQ knowledge item.",
                    "not_found",
                )
        return self._save(ConversationKnowledgeReference(**payload.model_dump()))

    def _validate_reference(
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
