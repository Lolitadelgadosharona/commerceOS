from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from commerce_os.shared.schemas import ReadModel

Severity = Literal["low", "medium", "high", "critical"]
Currency = str


class FinancialPeriodCreate(BaseModel):
    organization_id: UUID
    period_type: Literal["daily", "weekly", "monthly", "quarterly"]
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def valid_range(self) -> "FinancialPeriodCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class FinancialPeriodUpdate(BaseModel):
    status: Literal["closed", "locked"]


class FinancialPeriodRead(ReadModel):
    organization_id: UUID
    period_type: str
    start_date: date
    end_date: date
    status: str


class RevenueObservationCreate(BaseModel):
    organization_id: UUID
    project_id: UUID
    product_id: UUID | None = None
    channel: str | None = Field(default=None, max_length=80)
    amount: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    currency: Currency = Field(pattern=r"^[A-Z]{3}$")
    source_type: Literal["manual", "internal_event", "reconciled"]
    observation_date: date


class RevenueObservationRead(ReadModel):
    organization_id: UUID
    project_id: UUID
    product_id: UUID | None
    channel: str | None
    amount: Decimal
    currency: str
    source_type: str
    observation_date: date


class CostObservationCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    channel: str | None = Field(default=None, max_length=80)
    category: Literal[
        "product_cost",
        "shipping_cost",
        "ad_cost",
        "platform_fee",
        "refund_cost",
        "dispute_cost",
        "operation_cost",
        "creative_cost",
    ]
    amount: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    currency: Currency = Field(pattern=r"^[A-Z]{3}$")
    observation_date: date


class CostObservationRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    channel: str | None
    category: str
    amount: Decimal
    currency: str
    observation_date: date


class ContributionProfitCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    period_id: UUID
    currency: Currency = Field(pattern=r"^[A-Z]{3}$")
    confidence: float = Field(ge=0, le=1)


class ContributionProfitRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    period_id: UUID
    currency: str
    revenue: Decimal
    cost: Decimal
    contribution_profit: Decimal
    margin_percentage: float
    confidence: float
    component_snapshot: dict[str, str]
    formula_version: str


class UnitEconomicsCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    average_order_value: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    customer_acquisition_cost: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    gross_margin: float = Field(ge=0, le=1)
    refund_rate: float = Field(ge=0, le=1)
    dispute_rate: float = Field(ge=0, le=1)
    lifetime_value_estimate: Decimal = Field(ge=0, max_digits=18, decimal_places=2)


class UnitEconomicsRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    average_order_value: Decimal
    customer_acquisition_cost: Decimal
    gross_margin: float
    refund_rate: float
    dispute_rate: float
    lifetime_value_estimate: Decimal
    profitability_score: float
    formula_version: str


class FinancialRiskCreate(BaseModel):
    organization_id: UUID
    period_id: UUID | None = None
    product_id: UUID | None = None
    risk_type: Literal["loss_risk", "margin_compression", "cash_flow_risk", "high_refund_risk"]
    severity: Severity
    evidence_reference: str = Field(min_length=1, max_length=500)


class FinancialRiskRead(ReadModel):
    organization_id: UUID
    period_id: UUID | None
    product_id: UUID | None
    risk_type: str
    severity: str
    evidence_reference: str
