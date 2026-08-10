import pytest
from commerce_os.build.models import Product
from commerce_os.decision.creative_models import CreativeExperimentStatus, CreativeStrategyStatus
from commerce_os.decision.creative_schemas import (
    CreativeExperimentCreate,
    CreativeExperimentUpdate,
    CreativeHypothesisCreate,
    CreativeStrategyCreate,
)
from commerce_os.decision.creative_services import CreativePlanningService, CreativeStrategyService
from commerce_os.decision.errors import DecisionStateError
from commerce_os.governance.models import Organization
from commerce_os.operations.models import Brand
from sqlalchemy.orm import Session


def test_creative_strategy_and_experiment_workflow(db_session: Session) -> None:
    organization = Organization(name="Creative Test", slug="creative-test")
    db_session.add(organization)
    db_session.flush()
    brand = Brand(organization_id=organization.id, name="Creative Brand", slug="creative-brand")
    db_session.add(brand)
    db_session.flush()
    product = Product(
        organization_id=organization.id,
        brand_id=brand.id,
        name="Care Kit",
        description="Product",
        category="Care",
        status="approved",
    )
    db_session.add(product)
    db_session.commit()
    strategy_service = CreativeStrategyService(db_session)
    strategy = strategy_service.create(
        CreativeStrategyCreate(
            organization_id=organization.id,
            product_id=product.id,
            target_audience="Care-focused households",
            marketing_objective="Increase trust",
            core_message="Verified reusable care",
            emotional_angle="Confidence",
            creative_direction="Evidence-led storytelling",
        )
    )
    strategy_service.transition(strategy, CreativeStrategyStatus.APPROVED)
    strategy_service.transition(strategy, CreativeStrategyStatus.ACTIVE)
    planning = CreativePlanningService(db_session)
    hypothesis = planning.create_hypothesis(
        CreativeHypothesisCreate(
            organization_id=organization.id,
            strategy_id=strategy.id,
            hypothesis="Emotional storytelling improves trust",
            expected_behavior="More qualified engagement",
            success_metric="trust_engagement_rate",
            confidence_score=0.8,
        )
    )
    experiment = planning.create_experiment(
        CreativeExperimentCreate(
            organization_id=organization.id,
            hypothesis_id=hypothesis.id,
            variant_name="Story A",
            test_objective="Test trust response",
            metric="trust_engagement_rate",
        )
    )
    with pytest.raises(DecisionStateError):
        planning.transition_experiment(experiment, CreativeExperimentUpdate(status="completed"))
    planning.transition_experiment(experiment, CreativeExperimentUpdate(status="running"))
    planning.transition_experiment(
        experiment, CreativeExperimentUpdate(status="completed", result="Observed 12% engagement")
    )
    assert experiment.status == CreativeExperimentStatus.COMPLETED
