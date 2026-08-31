export type NavigationItem = {
  href: string;
  label: string;
  shortLabel: string;
  description: string;
};

export const navigationItems: NavigationItem[] = [
  { href: "/dashboard", label: "Dashboard", shortLabel: "DB", description: "Executive overview" },
  { href: "/opportunities", label: "Opportunities", shortLabel: "OP", description: "Demand to decision" },
  { href: "/customers", label: "Customers", shortLabel: "CU", description: "Customer intelligence" },
  { href: "/market-intelligence", label: "Market Intelligence", shortLabel: "MI", description: "Signals and evidence" },
  { href: "/growth", label: "Growth", shortLabel: "GR", description: "Revenue experiments" },
  { href: "/products", label: "Products", shortLabel: "PR", description: "Product truth" },
  { href: "/decision-committee", label: "Decision Committee", shortLabel: "DC", description: "Governed approvals" },
  { href: "/analytics", label: "Analytics", shortLabel: "AN", description: "Performance and learning" },
];
