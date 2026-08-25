import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Customers" };

export default function CustomersPage() {
  return <ModulePage contract={moduleContracts.customers} />;
}
