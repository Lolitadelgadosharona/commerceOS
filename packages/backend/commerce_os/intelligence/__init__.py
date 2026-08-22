"""Intelligence domain boundary."""

from commerce_os.intelligence.analysis_models import (
    MarketSignalAnalysis,
    OpportunityAssessment,
    OpportunityReport,
)
from commerce_os.intelligence.commercial_risk_models import (
    CommercialViabilityAssessment,
    ProductRiskAssessment,
    ProductRiskSignal,
)
from commerce_os.intelligence.connector_models import (
    CustomerPainCandidate,
    MarketConnectorDefinition,
    MarketDataRecord,
    MarketIngestionJob,
    NormalizedMarketItem,
    PainEvidence,
    RedditConnector,
)
from commerce_os.intelligence.economics_models import (
    ProductEconomicProfile,
    ProductProfitAssessment,
    ProfitScenarioAssessment,
    RiskAdjustedProfitAssessment,
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
from commerce_os.intelligence.need_models import (
    CustomerBackedOpportunityAssessment,
    CustomerNeed,
    PainNeedMapping,
    ProductSolutionHypothesis,
)
from commerce_os.intelligence.opportunity_models import (
    MarketOpportunity,
    OpportunityEvidence,
    OpportunityRisk,
    OpportunityScore,
    ProductCandidate,
    ProductCandidateEvidence,
    ProductEvaluation,
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
from commerce_os.intelligence.voice_models import (
    CustomerLanguageInsight,
    CustomerPainCluster,
    PainClusterMembership,
    PurchaseIntentSignal,
)

__all__ = [
    "ProductEconomicProfile",
    "ProductProfitAssessment",
    "ProfitScenarioAssessment",
    "RiskAdjustedProfitAssessment",
    "CommercialViabilityAssessment",
    "ProductRiskAssessment",
    "ProductRiskSignal",
    "CustomerInsight",
    "CustomerBackedOpportunityAssessment",
    "CustomerNeed",
    "PainNeedMapping",
    "ProductSolutionHypothesis",
    "CustomerPainCandidate",
    "MarketConnectorDefinition",
    "MarketDataRecord",
    "MarketIngestionJob",
    "NormalizedMarketItem",
    "PainEvidence",
    "RedditConnector",
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
    "ProductCandidateEvidence",
    "ProductEvaluation",
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
    "CustomerLanguageInsight",
    "CustomerPainCluster",
    "PainClusterMembership",
    "PurchaseIntentSignal",
]
