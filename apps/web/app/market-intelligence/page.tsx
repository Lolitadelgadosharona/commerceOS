import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Market Intelligence" };

export default function MarketIntelligencePage() {
  return <ModulePage contract={moduleContracts["market-intelligence"]} />;
}
