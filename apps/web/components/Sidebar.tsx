"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { navigationItems } from "../lib/navigation";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <Link className="brand" href="/">
        <span className="brand-mark" aria-hidden="true">CO</span>
        <span><strong>Commerce OS</strong><small>Control Center</small></span>
      </Link>
      <nav className="sidebar-nav" aria-label="Primary navigation">
        <p className="nav-label">Workspace</p>
        {navigationItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link className={active ? "nav-item active" : "nav-item"} href={item.href} key={item.href} aria-current={active ? "page" : undefined}>
              <span className="nav-symbol" aria-hidden="true">{item.shortLabel}</span>
              <span><strong>{item.label}</strong><small>{item.description}</small></span>
            </Link>
          );
        })}
      </nav>
      <div className="sidebar-footer">
        <span className="operator-avatar">RW</span>
        <span><strong>Founder workspace</strong><small>Human authority active</small></span>
      </div>
    </aside>
  );
}
