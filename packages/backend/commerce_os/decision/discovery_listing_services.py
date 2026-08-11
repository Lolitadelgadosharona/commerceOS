from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.decision.discovery_listing_models import (
    AIDiscoveryReadinessAssessment,
    GeoKnowledgeAsset,
    ListingBlueprint,
    ListingQualityAssessment,
)
from commerce_os.decision.discovery_listing_schemas import (
    GeoKnowledgeAssetCreate,
    ListingAssessmentCreate,
    ListingBlueprintCreate,
)
from commerce_os.decision.errors import DecisionScopeError, DecisionStateError
from commerce_os.decision.launch_models import ProductObjectionMap
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)


class DiscoveryListingService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_blueprint(self, payload: ListingBlueprintCreate) -> ListingBlueprint:
        self._product(payload.product_id, payload.organization_id)
        return self._save(ListingBlueprint(**payload.model_dump()))

    def create_geo_asset(self, payload: GeoKnowledgeAssetCreate) -> GeoKnowledgeAsset:
        self._product(payload.product_id, payload.organization_id)
        return self._save(GeoKnowledgeAsset(**payload.model_dump()))

    def assess_quality(self, payload: ListingAssessmentCreate) -> ListingQualityAssessment:
        self._product(payload.product_id, payload.organization_id)
        blueprint = self._latest(ListingBlueprint, payload.product_id, payload.organization_id)
        geo = self._latest(GeoKnowledgeAsset, payload.product_id, payload.organization_id)
        truth = self._truth(payload.product_id, payload.organization_id)
        objection_count = self.session.scalar(
            select(func.count())
            .select_from(ProductObjectionMap)
            .where(
                ProductObjectionMap.organization_id == payload.organization_id,
                ProductObjectionMap.product_id == payload.product_id,
            )
        )
        truth_score = self._truth_score(truth)
        language_score = min(100.0, float((objection_count or 0) * 25))
        geo_score = self._geo_score(geo)
        trust_score = self._trust_score(blueprint, truth)
        conversion_score = self._conversion_score(blueprint)
        overall = round(
            truth_score * 0.25
            + language_score * 0.20
            + geo_score * 0.20
            + trust_score * 0.15
            + conversion_score * 0.20,
            2,
        )
        return self._save(
            ListingQualityAssessment(
                **payload.model_dump(),
                truth_score=truth_score,
                customer_language_score=language_score,
                geo_score=geo_score,
                trust_score=trust_score,
                conversion_score=conversion_score,
                overall_score=overall,
            )
        )

    def assess_discovery(self, payload: ListingAssessmentCreate) -> AIDiscoveryReadinessAssessment:
        self._product(payload.product_id, payload.organization_id)
        quality = self._latest(
            ListingQualityAssessment, payload.product_id, payload.organization_id
        )
        if quality is None:
            raise DecisionStateError(
                "AI discovery readiness requires a listing quality assessment."
            )
        components = {
            "product_truth": quality.truth_score,
            "customer_language": quality.customer_language_score,
            "geo_knowledge": quality.geo_score,
            "trust_evidence": quality.trust_score,
            "conversion_structure": quality.conversion_score,
        }
        missing = [name for name, score in components.items() if score < 70]
        if quality.overall_score >= 80 and not missing:
            recommendation = "ready_for_human_review"
        elif quality.overall_score >= 60:
            recommendation = "improve_missing_information"
        else:
            recommendation = "insufficient_evidence"
        return self._save(
            AIDiscoveryReadinessAssessment(
                **payload.model_dump(),
                coverage_score=quality.overall_score,
                missing_information=missing,
                recommendation=recommendation,
            )
        )

    def _product(self, product_id: UUID, organization_id: UUID) -> None:
        table = Base.metadata.tables["products"]
        status = self.session.scalar(
            select(table.c.status).where(
                table.c.id == product_id,
                table.c.organization_id == organization_id,
            )
        )
        if status is None:
            raise DecisionScopeError("Product was not found in this organization.")
        if status not in {"approved", "active"}:
            raise DecisionStateError(
                "Listing intelligence requires an approved or active Build product."
            )

    def _truth(self, product_id: UUID, organization_id: UUID) -> dict[str, Any] | None:
        table = Base.metadata.tables["product_truth"]
        row = self.session.execute(
            select(
                table.c.summary,
                table.c.features,
                table.c.specifications,
                table.c.approved_claims,
                table.c.usage_notes,
            )
            .where(
                table.c.product_id == product_id,
                table.c.organization_id == organization_id,
            )
            .order_by(table.c.version.desc())
        ).first()
        return None if row is None else dict(row._mapping)

    def _latest(
        self, model: type[EntityT], product_id: UUID, organization_id: UUID
    ) -> EntityT | None:
        mapped = cast(Any, model)
        return self.session.scalar(
            select(model)
            .where(
                mapped.organization_id == organization_id,
                mapped.product_id == product_id,
            )
            .order_by(mapped.created_at.desc(), mapped.id.desc())
        )

    @staticmethod
    def _truth_score(truth: dict[str, Any] | None) -> float:
        if truth is None:
            return 0.0
        fields = ("summary", "features", "specifications", "approved_claims", "usage_notes")
        return float(sum(20 for field in fields if truth.get(field)))

    @staticmethod
    def _geo_score(asset: GeoKnowledgeAsset | None) -> float:
        if asset is None:
            return 0.0
        fields = (
            asset.entity_description,
            asset.attributes,
            asset.use_cases,
            asset.customer_questions,
            asset.answer_structure,
            asset.evidence_reference,
        )
        return round(sum(1 for value in fields if value) / len(fields) * 100, 2)

    @staticmethod
    def _trust_score(blueprint: ListingBlueprint | None, truth: dict[str, Any] | None) -> float:
        blueprint_points = 50.0 if blueprint and blueprint.trust_elements else 0.0
        truth_points = 50.0 if truth and truth.get("approved_claims") else 0.0
        return blueprint_points + truth_points

    @staticmethod
    def _conversion_score(blueprint: ListingBlueprint | None) -> float:
        if blueprint is None:
            return 0.0
        fields = (
            blueprint.title_strategy,
            blueprint.benefit_structure,
            blueprint.feature_structure,
            blueprint.faq_structure,
            blueprint.trust_elements,
            blueprint.comparison_points,
        )
        return round(sum(1 for value in fields if value) / len(fields) * 100, 2)

    def _save(self, entity: EntityT) -> EntityT:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
