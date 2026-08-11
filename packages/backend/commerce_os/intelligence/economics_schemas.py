from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from commerce_os.intelligence.economics_models import ProfitScenario
from commerce_os.shared.schemas import ReadModel

Money = Decimal
Rate = Decimal
Score = Decimal


class ProductEconomicProfileCreate(BaseModel):
    organization_id: UUID
    product_candidate_id: UUID
    product_cost: Money = Field(ge=0, max_digits=19, decimal_places=4)
    shipping_cost: Money = Field(ge=0, max_digits=19, decimal_places=4)
    packaging_cost: Money = Field(ge=0, max_digits=19, decimal_places=4)
    transaction_cost: Money = Field(ge=0, max_digits=19, decimal_places=4)
    estimated_acquisition_cost: Money = Field(ge=0, max_digits=19, decimal_places=4)
    refund_rate_assumption: Rate = Field(ge=0, le=1, max_digits=7, decimal_places=6)
    dispute_rate_assumption: Rate = Field(ge=0, le=1, max_digits=7, decimal_places=6)
    currency: str = Field(min_length=3, max_length=3)
    confidence: Rate = Field(ge=0, le=1, max_digits=7, decimal_places=6)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        if not value.isalpha():
            raise ValueError("Currency must be a three-letter code.")
        return value.upper()


class ProductEconomicProfileRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    product_cost: Decimal
    shipping_cost: Decimal
    packaging_cost: Decimal
    transaction_cost: Decimal
    estimated_acquisition_cost: Decimal
    refund_rate_assumption: Decimal
    dispute_rate_assumption: Decimal
    currency: str
    confidence: Decimal


class ProductProfitAssessmentCreate(BaseModel):
    organization_id: UUID
    product_candidate_id: UUID
    selling_price: Money = Field(gt=0, max_digits=19, decimal_places=4)


class ProductProfitAssessmentRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    selling_price: Decimal
    gross_margin: Decimal
    contribution_profit: Decimal
    margin_score: Decimal
    confidence: Decimal
    formula_version: str


class ProfitScenarioCreate(BaseModel):
    organization_id: UUID
    product_candidate_id: UUID
    scenario: ProfitScenario


class ProfitScenarioRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    scenario: str
    revenue: Decimal
    cost: Decimal
    profit: Decimal
    margin: Decimal


class RiskAdjustedProfitCreate(BaseModel):
    organization_id: UUID
    product_candidate_id: UUID
    opportunity_score: Score = Field(ge=0, le=100, max_digits=7, decimal_places=4)


class RiskAdjustedProfitRead(ReadModel):
    organization_id: UUID
    product_candidate_id: UUID
    opportunity_score: Decimal
    risk_score: Decimal
    profit_score: Decimal
    final_score: Decimal
    recommendation: str
