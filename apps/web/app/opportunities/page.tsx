import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Opportunities" };

export default function OpportunitiesPage() {
  return <ModulePage contract={moduleContracts.opportunities} />;
}
