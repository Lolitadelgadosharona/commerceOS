import pytest
from commerce_os.build.models import Product
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.decision.sales_support_models import RecommendationStatus
from commerce_os.decision.sales_support_schemas import (
    RecommendationCreate,
    RiskSignalCreate,
    SalesProfileCreate,
    SupportIntelligenceCreate,
)
from commerce_os.decision.sales_support_services import SalesSupportDecisionService
from commerce_os.governance.models import Organization
from commerce_os.operations.conversation_schemas import IntentCreate, MessageCreate, ThreadCreate
from commerce_os.operations.conversation_services import ConversationService
from commerce_os.operations.models import Brand, Customer
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def foundation(session: Session, slug: str):
    organization = Organization(name=f"Sales Support Test {slug}", slug=slug)
    session.add(organization)
    session.flush()
    customer = Customer(
        organization_id=organization.id, display_name="Customer", status="active", attributes={}
    )
    brand = Brand(organization_id=organization.id, name="Brand", slug=f"{slug}-brand")
    session.add_all([customer, brand])
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
    session.commit()
    conversations = ConversationService(session)
    thread = conversations.create_thread(
        ThreadCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            channel="website",
        )
    )
    message = conversations.create_message(
        MessageCreate(
            organization_id=organization.id,
            thread_id=thread.id,
            direction="inbound",
            sender_type="customer",
            content="I want this product but have a price question.",
        )
    )
    conversations.create_intent(
        IntentCreate(
            organization_id=organization.id,
            message_id=message.id,
            intent_type="price_objection",
            confidence=0.9,
        )
    )
    return organization, customer, product, thread


def test_sales_aggregation_lifecycle_support_risk_and_tenant_isolation(
    db_session: Session,
) -> None:
    organization, customer, product, thread = foundation(db_session, "sales-support")
    other, _, _, _ = foundation(db_session, "sales-support-other")
    service = SalesSupportDecisionService(db_session)
    profile = service.create_profile(
        SalesProfileCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            conversation_id=thread.id,
            product_id=product.id,
            intent="price_objection",
            estimated_value=120,
            repeat_probability=0.4,
            risk_level="medium",
        )
    )
    recommendation = service.create_recommendation(
        RecommendationCreate(
            organization_id=organization.id,
            sales_profile_id=profile.id,
            recommendation_type="objection_handling",
            reason="Review approved value evidence with a human operator.",
            confidence=0.8,
        )
    )
    with pytest.raises(DecisionStateError):
        service.transition_recommendation(recommendation, RecommendationStatus.ACCEPTED)
    service.transition_recommendation(recommendation, RecommendationStatus.REVIEWED)
    service.transition_recommendation(recommendation, RecommendationStatus.ACCEPTED)
    assert recommendation.status == RecommendationStatus.ACCEPTED
    support = service.create_support(
        SupportIntelligenceCreate(
            organization_id=organization.id,
            conversation_id=thread.id,
            issue_category="payment",
            severity="medium",
            customer_impact="Purchase decision is delayed.",
            risk_level="medium",
            recommended_resolution="Human review of the payment question.",
        )
    )
    risk = service.create_risk(
        RiskSignalCreate(
            organization_id=organization.id,
            customer_id=customer.id,
            risk_type="churn_risk",
            severity="medium",
            evidence_reference=f"conversation:{thread.id}",
        )
    )
    assert support.issue_category == "payment" and risk.risk_type == "churn_risk"
    with pytest.raises(DecisionScopeError):
        service.create_profile(
            SalesProfileCreate(
                organization_id=other.id,
                customer_id=customer.id,
                conversation_id=thread.id,
                intent="price_objection",
            )
        )


def test_api_and_ai_authority_boundaries(client: TestClient, db_session: Session) -> None:
    organization, customer, product, thread = foundation(db_session, "sales-support-api")
    base = {"organization_id": str(organization.id)}
    profile = client.post(
        "/api/v1/sales-intelligence",
        json=base
        | {
            "customer_id": str(customer.id),
            "conversation_id": str(thread.id),
            "product_id": str(product.id),
            "intent": "price_objection",
        },
    )
    assert profile.status_code == 201
    recommendation = client.post(
        "/api/v1/sales-recommendations",
        json=base
        | {
            "sales_profile_id": profile.json()["id"],
            "recommendation_type": "qualification",
            "reason": "A human should qualify the request.",
            "confidence": 0.7,
        },
    )
    assert recommendation.status_code == 201
    recommendation_id = recommendation.json()["id"]
    assert (
        client.patch(
            f"/api/v1/sales-recommendations/{recommendation_id}",
            params=base,
            json={"status": "reviewed"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/support-intelligence",
            json=base
            | {
                "conversation_id": str(thread.id),
                "issue_category": "other",
                "severity": "low",
                "customer_impact": "Question pending.",
                "risk_level": "low",
                "recommended_resolution": "Human review.",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/customer-risk-signals",
            json=base
            | {
                "customer_id": str(customer.id),
                "risk_type": "refund_risk",
                "severity": "low",
                "evidence_reference": f"conversation:{thread.id}",
            },
        ).status_code
        == 201
    )
    recommend_policy = client.post(
        "/api/v1/ai-action-policies",
        json=base | {"action_type": "recommend", "domain": "decision"},
    )
    assert recommend_policy.status_code == 201
    assert recommend_policy.json()["allowed"] is True
    assert recommend_policy.json()["requires_approval"] is False
    refund_policy = client.post(
        "/api/v1/ai-action-policies",
        json=base | {"action_type": "issue_refund", "domain": "finance"},
    )
    assert refund_policy.status_code == 201
    assert refund_policy.json()["allowed"] is False
    assert refund_policy.json()["requires_approval"] is True
    unsafe = client.post(
        "/api/v1/ai-action-policies",
        json=base
        | {
            "action_type": "send_message",
            "domain": "operations",
            "allowed": True,
            "requires_approval": False,
        },
    )
    assert unsafe.status_code == 422
    for endpoint in (
        "sales-intelligence",
        "sales-recommendations",
        "support-intelligence",
        "customer-risk-signals",
        "ai-action-policies",
    ):
        assert client.get(f"/api/v1/{endpoint}", params=base).status_code == 200
