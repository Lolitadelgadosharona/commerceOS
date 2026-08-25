"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigationItems } from "../lib/navigation";

export function ModuleNavigation() {
  const pathname = usePathname();
  return (
    <nav className="module-navigation" aria-label="Module navigation">
      {navigationItems.map((item) => (
        <Link href={item.href} key={item.href} className={pathname === item.href ? "active" : ""}>
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
