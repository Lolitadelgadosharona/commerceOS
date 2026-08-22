from uuid import uuid4

import pytest
from commerce_os.build.models import Product
from commerce_os.intelligence.demand_bridge_models import (
    DemandSignalSource,
    DemandThemeSignalLink,
    PredictiveDemandMetadata,
)
from commerce_os.intelligence.demand_bridge_schemas import (
    DemandSignalSourceCreate,
    DemandThemeAnalysisCreate,
    PredictiveDemandInput,
)
from commerce_os.intelligence.demand_bridge_services import DemandIntelligenceService
from commerce_os.intelligence.errors import IntelligenceScopeError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.test_business_demand_intelligence import external_payload
from tests.test_demand_intelligence_bridge import aggregate


def enhanced_source(
    session: Session,
    organization_id,  # type: ignore[no-untyped-def]
    actor_id,  # type: ignore[no-untyped-def]
    *,
    source_type: str,
    source_category: str,
    trend_type: str | None = None,
) -> DemandSignalSource:
    return DemandIntelligenceService(session).create_source(
        DemandSignalSourceCreate(
            organization_id=organization_id,
            source_type=source_type,  # type: ignore[arg-type]
            display_name=source_type.replace("_", " ").title(),
            source_domain="intelligence",
            collection_method="controlled_import",
            evidence_origin="external_observation",
            source_category=source_category,  # type: ignore[arg-type]
            geographic_scope="Europe",
            time_window="next_90_days",
            trend_type=trend_type,  # type: ignore[arg-type]
        ),
        actor_id,
    )


def test_enhanced_source_metadata_and_sprint_053_compatibility(db_session: Session) -> None:
    entities, _, _, growth = aggregate(db_session, "source-enhancement")
    organization, user, *_ = entities
    weather = enhanced_source(
        db_session,
        organization.id,
        user.id,
        source_type="weather_environment",
        source_category="weather",
        trend_type="rising",
    )
    assert growth.source_type == "growthos_conversation"
    assert weather.geographic_scope == "Europe"
    assert weather.time_window == "next_90_days"
    assert weather.source_category == "weather"
    assert weather.trend_type == "rising"


def test_predictive_signal_is_optional_traceable_evidence(db_session: Session) -> None:
    entities, _, _, _ = aggregate(db_session, "predictive-evidence")
    organization, user, *_ = entities
    enhanced_source(
        db_session,
        organization.id,
        user.id,
        source_type="weather_environment",
        source_category="weather",
        trend_type="rising",
    )
    payload = external_payload(
        organization.id, "weather_environment", "weather:europe:summer-risk"
    ).model_copy(
        update={
            "prediction": PredictiveDemandInput(
                prediction_type="summer_heat_risk_increasing",
                forecast_window="next_90_days",
                confidence_score=0.72,
                assumptions=["Current regional forecast remains directionally stable."],
                uncertainty_notes="Long-range weather forecasts may change materially.",
            )
        }
    )
    signal = DemandIntelligenceService(db_session).ingest(payload, user.id)
    prediction = db_session.scalar(
        select(PredictiveDemandMetadata).where(
            PredictiveDemandMetadata.demand_signal_id == signal.id
        )
    )
    assert prediction is not None
    assert prediction.confidence_score == 0.72
    assert prediction.uncertainty_notes
    assert signal.status == "draft"
    prediction.uncertainty_notes = "replacement"
    with pytest.raises(ValueError, match="append-only"):
        db_session.commit()
    db_session.rollback()


def test_independent_signal_diversity_drives_explainable_strength(db_session: Session) -> None:
    products_before = db_session.scalar(select(func.count()).select_from(Product))
    entities, _, _, growth = aggregate(db_session, "signal-diversity")
    organization, user, *_ = entities
    service = DemandIntelligenceService(db_session)
    signals = [growth]
    for source_type, source_category in [
        ("reddit", "social"),
        ("google_trend", "search"),
        ("amazon_review", "marketplace"),
    ]:
        enhanced_source(
            db_session,
            organization.id,
            user.id,
            source_type=source_type,
            source_category=source_category,
            trend_type="rising",
        )
        signals.append(
            service.ingest(
                external_payload(organization.id, source_type, f"{source_type}:workflow-demand"),
                user.id,
            )
        )
    for signal in signals:
        service.transition(signal, "review", None, user.id)

    analyses = [
        service.analyze_theme(
            DemandThemeAnalysisCreate(
                organization_id=organization.id,
                name=f"Workflow demand from {count} source types",
                category="workflow_friction",
                signal_ids=[signal.id for signal in signals[:count]],
                summary="Deterministic combination of reviewed, independent source evidence.",
            ),
            user.id,
        )
        for count in [1, 2, 3]
    ]
    assert [item.evidence_strength for item in analyses] == ["weak", "medium", "strong"]
    assert [item.signal_diversity for item in analyses] == [1, 2, 3]
    assert analyses[2].evidence_count == sum(signal.evidence_count for signal in signals[:3])
    assert db_session.scalar(select(func.count()).select_from(Product)) == products_before


def test_dashboard_distribution_themes_prediction_and_tenant_boundary(
    db_session: Session,
) -> None:
    entities, _, _, growth = aggregate(db_session, "enhanced-dashboard")
    organization, user, *_ = entities
    service = DemandIntelligenceService(db_session)
    enhanced_source(
        db_session,
        organization.id,
        user.id,
        source_type="seasonal_pattern",
        source_category="seasonality",
        trend_type="seasonal",
    )
    prediction_payload = external_payload(
        organization.id, "seasonal_pattern", "seasonality:europe:summer"
    ).model_copy(
        update={
            "prediction": PredictiveDemandInput(
                prediction_type="seasonal_interest_expected",
                forecast_window="next_quarter",
                confidence_score=0.68,
                assumptions=["Prior seasonal timing remains relevant."],
                uncertainty_notes="Timing may shift with regional conditions.",
            )
        }
    )
    seasonal = service.ingest(prediction_payload, user.id)
    service.transition(growth, "review", None, user.id)
    service.transition(seasonal, "review", None, user.id)
    theme = service.analyze_theme(
        DemandThemeAnalysisCreate(
            organization_id=organization.id,
            name="Seasonal workflow pressure",
            category="workflow_friction",
            signal_ids=[growth.id, seasonal.id],
            summary="Customer voice and seasonal evidence align.",
        ),
        user.id,
    )
    dashboard = service.dashboard(organization.id)
    assert sum(item.signal_percentage for item in dashboard.source_overview) == 100
    assert dashboard.emerging_demand_themes[0].theme_analysis_id == theme.id
    assert dashboard.predictive_indicators[0].confidence == 0.68
    assert dashboard.predictive_indicators[0].evidence_sources
    with pytest.raises(IntelligenceScopeError, match="this organization"):
        service.analyze_theme(
            DemandThemeAnalysisCreate(
                organization_id=uuid4(),
                name="Cross tenant",
                category="invalid",
                signal_ids=[growth.id],
                summary="Must fail.",
            ),
            user.id,
        )
    assert db_session.scalar(select(func.count()).select_from(DemandThemeSignalLink)) == 2
