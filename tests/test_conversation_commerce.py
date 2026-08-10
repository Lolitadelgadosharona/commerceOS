import pytest
from commerce_os.build.models import Product, ProductKnowledgeItem
from commerce_os.governance.models import Organization, User
from commerce_os.operations.conversation_models import ThreadStatus
from commerce_os.operations.conversation_schemas import (
    EmotionCreate,
    HandoffCreate,
    HandoffUpdate,
    IntentCreate,
    KnowledgeCreate,
    MessageCreate,
    ThreadCreate,
)
from commerce_os.operations.conversation_services import ConversationService
from commerce_os.operations.errors import OperationsError
from commerce_os.operations.models import Brand, Customer
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str = "conversation"):
    organization = Organization(name="Conversation Test", slug=slug)
    session.add(organization)
    session.flush()
    customer = Customer(
        organization_id=organization.id, display_name="Customer", status="active", attributes={}
    )
    user = User(
        organization_id=organization.id,
        email=f"human-{slug}@example.com",
        display_name="Human Operator",
        status="active",
        principal_type="human",
    )
    brand = Brand(organization_id=organization.id, name="Brand", slug=f"{slug}-brand")
    session.add_all([customer, user, brand])
    session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Care Kit",
        description="Care product",
        category="Care",
        status="approved",
    )
    session.add(product)
    session.flush()
    faq = ProductKnowledgeItem(
        organization_id=organization.id,
        product_id=product.id,
        type="faq",
        content="How is it used?",
        confidence=1,
        approval_status="approved",
    )
    session.add(faq)
    session.commit()
    return organization, customer, user, faq


def test_lifecycle_ordering_intent_emotion_and_handoff(db_session: Session) -> None:
    organization, customer, user, _faq = foundation(db_session)
    service = ConversationService(db_session)
    thread = service.create_thread(
        ThreadCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            channel="website",
            priority="normal",
        )
    )
    inbound = service.create_message(
        MessageCreate(
            organization_id=organization.id,
            thread_id=thread.id,
            direction="inbound",
            sender_type="customer",
            content="Can I get a refund?",
        )
    )
    advisory_ai_record = service.create_message(
        MessageCreate(
            organization_id=organization.id,
            thread_id=thread.id,
            direction="outbound",
            sender_type="ai",
            content="Draft response retained for review.",
        )
    )
    assert (inbound.sequence, advisory_ai_record.sequence) == (1, 2)
    intent = service.create_intent(
        IntentCreate(
            organization_id=organization.id,
            message_id=inbound.id,
            intent_type="refund_request",
            confidence=0.9,
        )
    )
    emotion = service.create_emotion(
        EmotionCreate(
            organization_id=organization.id,
            message_id=inbound.id,
            emotion="frustrated",
            confidence=0.75,
        )
    )
    assert intent.intent_type == "refund_request" and emotion.emotion == "frustrated"
    handoff = service.create_handoff(
        HandoffCreate(
            organization_id=organization.id,
            thread_id=thread.id,
            reason="policy_exception",
            priority="high",
        )
    )
    assert thread.status == ThreadStatus.ESCALATED
    with pytest.raises(OperationsError):
        service.transition_handoff(handoff, HandoffUpdate(status="assigned"))
    service.transition_handoff(handoff, HandoffUpdate(status="assigned", assigned_user_id=user.id))
    service.transition_handoff(handoff, HandoffUpdate(status="resolved"))
    assert handoff.resolved_at is not None


def test_knowledge_reference_and_api(db_session: Session, client: TestClient) -> None:
    organization, customer, _user, faq = foundation(db_session, "conversation-api")
    base = {"organization_id": str(organization.id)}
    thread = client.post(
        "/api/v1/conversations",
        json=base
        | {
            "customer_id": str(customer.id),
            "channel": "reddit",
            "priority": "normal",
        },
    )
    assert thread.status_code == 201
    thread_id = thread.json()["id"]
    message = client.post(
        "/api/v1/messages",
        json=base
        | {
            "thread_id": thread_id,
            "direction": "inbound",
            "sender_type": "customer",
            "content": "How is this used?",
        },
    )
    assert message.status_code == 201
    message_id = message.json()["id"]
    assert (
        client.post(
            "/api/v1/conversation-intents",
            json=base
            | {"message_id": message_id, "intent_type": "product_question", "confidence": 1},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/conversation-emotions",
            json=base | {"message_id": message_id, "emotion": "neutral", "confidence": 1},
        ).status_code
        == 201
    )
    knowledge = client.post(
        "/api/v1/conversation-knowledge",
        json=base
        | {
            "thread_id": thread_id,
            "reference_type": "faq",
            "reference_id": str(faq.id),
        },
    )
    assert knowledge.status_code == 201
    service = ConversationService(db_session)
    direct = service.create_knowledge(
        KnowledgeCreate(
            organization_id=organization.id,
            thread_id=thread_id,
            reference_type="product_knowledge",
            reference_id=faq.id,
        )
    )
    assert direct.reference_id == faq.id
    for endpoint in (
        "conversations",
        "messages",
        "conversation-intents",
        "conversation-emotions",
        "conversation-handoffs",
        "conversation-knowledge",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
