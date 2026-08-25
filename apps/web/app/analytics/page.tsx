import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Analytics" };

export default function AnalyticsPage() {
  return <ModulePage contract={moduleContracts.analytics} />;
}
