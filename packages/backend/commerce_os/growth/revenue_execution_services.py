from decimal import Decimal
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from commerce_os.growth.errors import GrowthError
from commerce_os.growth.industry_intelligence_models import (
    GrowthServiceRecommendation,
    IndustryGrowthPattern,
    IndustryGrowthProfile,
)
from commerce_os.growth.revenue_execution_models import DailyGrowthOpportunity
from commerce_os.growth.revenue_execution_schemas import (
    DailyOpportunityCreate,
    RevenueExecutionDashboard,
)
from commerce_os.growth.revenue_models import (
    GrowthGift,
    GrowthProspect,
    GrowthProspectEvidence,
)
from commerce_os.growth.revenue_services import scoped_revenue
from commerce_os.shared.audit import record_audit_event
from commerce_os.shared.database import Base

EntityT = TypeVar("EntityT", bound=Base)


class RevenueExecutionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_daily_opportunity(
        self, payload: DailyOpportunityCreate, actor_id: UUID
    ) -> DailyGrowthOpportunity:
        prospect = scoped_revenue(
            self.session, GrowthProspect, payload.prospect_id, payload.organization_id
        )
        profile = self._scoped(
            IndustryGrowthProfile, payload.industry_profile_id, payload.organization_id
        )
        if prospect.industry.casefold() not in {
            profile.industry_key.casefold(),
            profile.vertical.casefold(),
            profile.display_name.casefold(),
        }:
            raise GrowthError("Queue industry profile must match the prospect industry.")
        pattern = self._scoped(
            IndustryGrowthPattern, payload.industry_pattern_id, payload.organization_id
        )
        if pattern.industry_profile_id != profile.id:
            raise GrowthError("Queue pattern must belong to the selected industry profile.")
        service = self._scoped(
            GrowthServiceRecommendation,
            payload.service_recommendation_id,
            payload.organization_id,
        )
        if service.prospect_id != prospect.id or service.industry_profile_id != profile.id:
            raise GrowthError("Queue service recommendation must match prospect and industry.")
        for evidence_id in payload.evidence_references:
            evidence = scoped_revenue(
                self.session, GrowthProspectEvidence, evidence_id, payload.organization_id
            )
            if evidence.prospect_id != prospect.id:
                raise GrowthError("Queue evidence must belong to the selected prospect.")
        if payload.growth_gift_id is not None:
            gift = scoped_revenue(
                self.session, GrowthGift, payload.growth_gift_id, payload.organization_id
            )
            if gift.prospect_id != prospect.id:
                raise GrowthError("Recommended Growth Gift must belong to the selected prospect.")
        values = payload.model_dump()
        values["evidence_references"] = [str(item) for item in payload.evidence_references]
        return self._save(
            DailyGrowthOpportunity(**values, status="review"),
            actor_id,
            "growthos.daily_opportunity.created",
        )

    def dashboard(self, organization_id: UUID) -> RevenueExecutionDashboard:
        self._organization(organization_id)
        prospects = Base.metadata.tables["growth_prospects"]
        gifts = Base.metadata.tables["growth_gifts"]
        drafts = Base.metadata.tables["growth_outreach_drafts"]
        analyses = Base.metadata.tables["sales_conversation_analyses"]
        revenue = Base.metadata.tables["revenue_observations"]
        unit_economics = Base.metadata.tables["unit_economic_assessments"]

        def count(table: Any, *criteria: Any) -> int:
            return int(
                self.session.scalar(
                    select(func.count())
                    .select_from(table)
                    .where(table.c.organization_id == organization_id, *criteria)
                )
                or 0
            )

        currencies = list(
            self.session.scalars(
                select(revenue.c.currency)
                .where(revenue.c.organization_id == organization_id)
                .distinct()
            )
        )
        currency = currencies[0] if len(currencies) == 1 else None
        revenue_total = Decimal("0")
        mrr: Decimal | None = None
        if currency is not None:
            revenue_total = Decimal(
                self.session.scalar(
                    select(func.coalesce(func.sum(revenue.c.amount), 0)).where(
                        revenue.c.organization_id == organization_id,
                        revenue.c.currency == currency,
                    )
                )
                or 0
            )
        ltv_value = self.session.scalar(
            select(func.avg(unit_economics.c.lifetime_value_estimate)).where(
                unit_economics.c.organization_id == organization_id
            )
        )
        return RevenueExecutionDashboard(
            organization_id=organization_id,
            prospects_discovered=count(prospects),
            qualified_prospects=count(prospects, prospects.c.status == "qualified"),
            growth_gifts_created=count(gifts),
            outreach_drafts=count(drafts),
            customer_replies=count(gifts, gifts.c.status.in_(["customer_response", "converted"])),
            positive_conversations=count(
                analyses, analyses.c.buying_signal.in_(["positive", "strong"])
            ),
            customers_won=count(prospects, prospects.c.status == "customer"),
            revenue=revenue_total,
            mrr=mrr,
            ltv=Decimal(ltv_value) if ltv_value is not None else None,
            currency=currency,
        )

    def _organization(self, organization_id: UUID) -> None:
        table = Base.metadata.tables["organizations"]
        if self.session.scalar(select(table.c.id).where(table.c.id == organization_id)) is None:
            raise GrowthError("Organization was not found.", "not_found")

    def _scoped(self, model: type[EntityT], entity_id: UUID, organization_id: UUID) -> EntityT:
        entity = self.session.get(model, entity_id)
        if entity is None or entity.organization_id != organization_id:  # type: ignore[attr-defined]
            raise GrowthError(
                "Revenue execution record was not found in this organization.", "not_found"
            )
        return entity

    def _save(self, entity: EntityT, actor_id: UUID, action: str) -> EntityT:
        self.session.add(entity)
        self.session.flush()
        item = cast(Any, entity)
        record_audit_event(
            self.session,
            organization_id=item.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action=action,
            entity_type=item.__tablename__,
            entity_id=cast(UUID, item.id),
            metadata={"result": "success", "external_execution": "none"},
        )
        self.session.commit()
        self.session.refresh(entity)
        return entity
