import Link from "next/link";
import type { CSSProperties } from "react";

type ModuleCardProps = {
  href: string;
  label: string;
  description: string;
  meta: string;
  accent: string;
};

export function ModuleCard({ href, label, description, meta, accent }: ModuleCardProps) {
  return (
    <Link className="module-card" href={href} style={{ "--module-accent": accent } as CSSProperties}>
      <div className="module-card-topline">
        <span className="module-dot" />
        <span>{meta}</span>
      </div>
      <h3>{label}</h3>
      <p>{description}</p>
      <span className="module-card-link">Open module <span aria-hidden="true">→</span></span>
    </Link>
  );
}
