import type { Metadata } from "next";
import { ModulePage } from "../../components/ModulePage";
import { moduleContracts } from "../../lib/contracts";

export const metadata: Metadata = { title: "Products" };

export default function ProductsPage() {
  return <ModulePage contract={moduleContracts.products} />;
}
