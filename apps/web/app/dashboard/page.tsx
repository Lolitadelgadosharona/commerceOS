import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Dashboard" };

export default function DashboardPage() {
  return <ModulePage contract={moduleContracts.dashboard} />;
}
