import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Decision Committee" };

export default function DecisionsPage() {
  return <ModulePage contract={moduleContracts.decisions} />;
}
