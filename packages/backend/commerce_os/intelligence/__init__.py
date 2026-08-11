"""Intelligence domain boundary."""

from commerce_os.intelligence.analysis_models import (
    MarketSignalAnalysis,
    OpportunityAssessment,
    OpportunityReport,
)
from commerce_os.intelligence.connector_models import (
    MarketConnectorDefinition,
    MarketDataRecord,
    MarketIngestionJob,
    NormalizedMarketItem,
)
from commerce_os.intelligence.market_models import (
    MarketDataSource,
    MarketSignal,
    MarketSignalCluster,
    MarketSignalClusterMembership,
    MarketSignalEvidence,
    MarketSignalOpportunityLink,
)
from commerce_os.intelligence.models import (
    CustomerInsight,
    CustomerSignal,
    CustomerVoiceCluster,
    InsightEvidence,
    SignalClusterMembership,
    SignalSource,
)
from commerce_os.intelligence.opportunity_models import (
    MarketOpportunity,
    OpportunityEvidence,
    OpportunityRisk,
    OpportunityScore,
    ProductCandidate,
)
from commerce_os.intelligence.product_models import (
    ProductEconomics,
    ProductHypothesis,
    ProductInvestmentScore,
    ProductRisk,
    SupplierCandidate,
)
from commerce_os.intelligence.supplier_models import (
    ProductSupplierMatch,
    SupplierDecisionRecord,
    SupplierEvaluation,
    SupplierProfile,
    SupplierRisk,
)

__all__ = [
    "CustomerInsight",
    "MarketConnectorDefinition",
    "MarketDataRecord",
    "MarketIngestionJob",
    "NormalizedMarketItem",
    "MarketDataSource",
    "MarketSignal",
    "MarketSignalCluster",
    "MarketSignalClusterMembership",
    "MarketSignalEvidence",
    "MarketSignalOpportunityLink",
    "MarketSignalAnalysis",
    "OpportunityAssessment",
    "OpportunityReport",
    "CustomerSignal",
    "CustomerVoiceCluster",
    "InsightEvidence",
    "SignalClusterMembership",
    "SignalSource",
    "MarketOpportunity",
    "OpportunityEvidence",
    "OpportunityRisk",
    "OpportunityScore",
    "ProductCandidate",
    "ProductEconomics",
    "ProductHypothesis",
    "ProductInvestmentScore",
    "ProductRisk",
    "SupplierCandidate",
    "SupplierProfile",
    "SupplierEvaluation",
    "SupplierRisk",
    "ProductSupplierMatch",
    "SupplierDecisionRecord",
]
