from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from commerce_os.shared.schemas import ReadModel

RiskLevel = Literal["low", "medium", "high", "critical"]


class ProductHypothesisCreate(BaseModel):
    organization_id: UUID
    opportunity_id: UUID
    name: str = Field(min_length=1, max_length=250)
    description: str = Field(min_length=1, max_length=5000)
    customer_problem: str = Field(min_length=1, max_length=5000)
    solution_description: str = Field(min_length=1, max_length=5000)
    target_customer: str = Field(min_length=1, max_length=500)
    target_market: str = Field(min_length=1, max_length=250)
    status: Literal["proposed", "evaluating", "validated", "rejected", "archived"] = "proposed"
    confidence_score: float = Field(ge=0, le=1)


class ProductHypothesisRead(ReadModel):
    organization_id: UUID
    opportunity_id: UUID
    name: str
    description: str
    customer_problem: str
    solution_description: str
    target_customer: str
    target_market: str
    status: str
    confidence_score: float


class ProductEconomicsCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    selling_price: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    estimated_product_cost: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    estimated_shipping_cost: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    payment_cost: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    estimated_marketing_cost: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class ProductEconomicsRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    selling_price: Decimal
    estimated_product_cost: Decimal
    estimated_shipping_cost: Decimal
    payment_cost: Decimal
    estimated_marketing_cost: Decimal
    contribution_margin: Decimal
    margin_percentage: Decimal
    currency: str


EconomicMetric = Literal[
    "selling_price",
    "estimated_product_cost",
    "estimated_shipping_cost",
    "payment_cost",
    "estimated_marketing_cost",
    "fulfillment_cost",
    "platform_fee",
    "refund_rate",
    "dispute_rate",
    "customer_acquisition_cost",
    "conversion_rate",
]
EconomicClassification = Literal[
    "actual", "quoted", "observed", "assumption", "forecast", "ai_inference", "unknown"
]


class ProductEconomicInputCreate(BaseModel):
    organization_id: UUID
    product_economics_id: UUID
    metric: EconomicMetric
    value: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=4)
    classification: EconomicClassification
    source: str = Field(min_length=1, max_length=250)
    confidence: float | None = Field(default=None, ge=0, le=1)
    as_of: datetime | None = None
    evidence_reference: str | None = Field(default=None, min_length=1, max_length=500)
    notes: str | None = Field(default=None, min_length=1, max_length=5000)

    @field_validator("value")
    @classmethod
    def validate_unknown_value(cls, value: Decimal | None, info: object) -> Decimal | None:
        return value

    @field_validator("classification")
    @classmethod
    def validate_classification_value(cls, classification: str, info: object) -> str:
        data = getattr(info, "data", {})
        value = data.get("value")
        if classification == "unknown" and value is not None:
            raise ValueError("UNKNOWN economic inputs must not carry a numeric value.")
        if classification != "unknown" and value is None:
            raise ValueError("Known economic inputs require a numeric value, including known zero.")
        return classification


class ProductEconomicInputRead(ReadModel):
    organization_id: UUID
    product_economics_id: UUID
    metric: str
    value: Decimal | None
    classification: str
    source: str
    confidence: float | None
    as_of: datetime | None
    evidence_reference: str | None
    notes: str | None


class SupplierCandidateCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    source_type: Literal[
        "manual", "manufacturer", "wholesaler", "distributor", "marketplace_reference"
    ]
    supplier_reference: str = Field(min_length=1, max_length=500)
    estimated_cost: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    minimum_order_quantity: int = Field(ge=1)
    lead_time: str = Field(min_length=1, max_length=200)
    quality_notes: str = Field(min_length=1, max_length=5000)
    risk_level: RiskLevel


class SupplierCandidateRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    source_type: str
    supplier_reference: str
    estimated_cost: Decimal
    minimum_order_quantity: int
    lead_time: str
    quality_notes: str
    risk_level: str


class ProductRiskCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    risk_type: Literal["trademark", "patent", "brand", "policy", "dispute", "quality"]
    severity: RiskLevel
    description: str = Field(min_length=1, max_length=5000)
    status: Literal["open", "mitigated", "accepted", "dismissed"] = "open"


class ProductRiskRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    risk_type: str
    severity: str
    description: str
    status: str


class ProductInvestmentScoreCreate(BaseModel):
    organization_id: UUID
    product_id: UUID
    competition_score: float = Field(ge=0, le=100)


class ProductInvestmentScoreRead(ReadModel):
    organization_id: UUID
    product_id: UUID
    opportunity_score: float
    margin_score: float
    risk_score: float
    competition_score: float
    confidence_score: float
    overall_score: float
    formula_version: str
