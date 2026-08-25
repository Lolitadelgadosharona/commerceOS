import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Growth" };

export default function GrowthPage() {
  return <ModulePage contract={moduleContracts.growth} />;
}
