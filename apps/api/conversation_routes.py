from typing import Annotated, TypeVar
from uuid import UUID

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
    EmotionRead,
    HandoffCreate,
    HandoffRead,
    HandoffUpdate,
    IntentCreate,
    IntentRead,
    KnowledgeCreate,
    KnowledgeRead,
    MessageCreate,
    MessageRead,
    ThreadCreate,
    ThreadRead,
    ThreadUpdate,
)
from commerce_os.operations.conversation_services import ConversationService, scoped_thread
from commerce_os.operations.errors import OperationsError
from commerce_os.shared.database import Base, get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
ModelT = TypeVar("ModelT", bound=Base)


def _list(session: Session, model: type[ModelT], organization_id: UUID) -> list[ModelT]:
    statement = select(model).where(model.organization_id == organization_id)  # type: ignore[attr-defined]
    if model is ConversationMessage:
        statement = statement.order_by(ConversationMessage.thread_id, ConversationMessage.sequence)
    else:
        statement = statement.order_by(model.created_at.desc())  # type: ignore[attr-defined]
    return list(session.scalars(statement))


@router.post("/conversations", response_model=ThreadRead, status_code=201)
def create_conversation(payload: ThreadCreate, session: SessionDependency) -> ConversationThread:
    return ConversationService(session).create_thread(payload)


@router.get("/conversations", response_model=list[ThreadRead])
def list_conversations(
    organization_id: UUID, session: SessionDependency
) -> list[ConversationThread]:
    return _list(session, ConversationThread, organization_id)


@router.patch("/conversations/{thread_id}", response_model=ThreadRead)
def transition_conversation(
    thread_id: UUID, organization_id: UUID, payload: ThreadUpdate, session: SessionDependency
) -> ConversationThread:
    return ConversationService(session).transition_thread(
        scoped_thread(session, thread_id, organization_id), ThreadStatus(payload.status)
    )


@router.post("/messages", response_model=MessageRead, status_code=201)
def create_message(payload: MessageCreate, session: SessionDependency) -> ConversationMessage:
    return ConversationService(session).create_message(payload)


@router.get("/messages", response_model=list[MessageRead])
def list_messages(organization_id: UUID, session: SessionDependency) -> list[ConversationMessage]:
    return _list(session, ConversationMessage, organization_id)


@router.post("/conversation-intents", response_model=IntentRead, status_code=201)
def create_intent(payload: IntentCreate, session: SessionDependency) -> ConversationIntent:
    return ConversationService(session).create_intent(payload)


@router.get("/conversation-intents", response_model=list[IntentRead])
def list_intents(organization_id: UUID, session: SessionDependency) -> list[ConversationIntent]:
    return _list(session, ConversationIntent, organization_id)


@router.post("/conversation-emotions", response_model=EmotionRead, status_code=201)
def create_emotion(payload: EmotionCreate, session: SessionDependency) -> ConversationEmotionSignal:
    return ConversationService(session).create_emotion(payload)


@router.get("/conversation-emotions", response_model=list[EmotionRead])
def list_emotions(
    organization_id: UUID, session: SessionDependency
) -> list[ConversationEmotionSignal]:
    return _list(session, ConversationEmotionSignal, organization_id)


@router.post("/conversation-handoffs", response_model=HandoffRead, status_code=201)
def create_handoff(payload: HandoffCreate, session: SessionDependency) -> ConversationHandoff:
    return ConversationService(session).create_handoff(payload)


@router.get("/conversation-handoffs", response_model=list[HandoffRead])
def list_handoffs(organization_id: UUID, session: SessionDependency) -> list[ConversationHandoff]:
    return _list(session, ConversationHandoff, organization_id)


@router.patch("/conversation-handoffs/{handoff_id}", response_model=HandoffRead)
def transition_handoff(
    handoff_id: UUID,
    organization_id: UUID,
    payload: HandoffUpdate,
    session: SessionDependency,
) -> ConversationHandoff:
    handoff = session.get(ConversationHandoff, handoff_id)
    if handoff is None or handoff.organization_id != organization_id:
        raise OperationsError("Handoff was not found in this organization.", "not_found")
    return ConversationService(session).transition_handoff(handoff, payload)


@router.post("/conversation-knowledge", response_model=KnowledgeRead, status_code=201)
def create_knowledge(
    payload: KnowledgeCreate, session: SessionDependency
) -> ConversationKnowledgeReference:
    return ConversationService(session).create_knowledge(payload)


@router.get("/conversation-knowledge", response_model=list[KnowledgeRead])
def list_knowledge(
    organization_id: UUID, session: SessionDependency
) -> list[ConversationKnowledgeReference]:
    return _list(session, ConversationKnowledgeReference, organization_id)
