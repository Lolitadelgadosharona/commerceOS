import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ModuleNavigation } from "../components/ModuleNavigation";
import { Sidebar } from "../components/Sidebar";
import { TopNavigation } from "../components/TopNavigation";
import "./styles.css";

export const metadata: Metadata = {
  title: { default: "Commerce OS Control Center", template: "%s · Commerce OS" },
  description: "Evidence-first operating control center for Commerce OS.",
};

async function apiIsAvailable(): Promise<boolean> {
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${baseUrl}/api/v1/health`, { cache: "no-store" });
    return response.ok;
  } catch {
    return false;
  }
}

export default async function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  const apiAvailable = await apiIsAvailable();
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <Sidebar />
          <div className="workspace-shell">
            <TopNavigation apiAvailable={apiAvailable} />
            <ModuleNavigation />
            <main className="workspace-main">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
