import type { Metadata } from "next";
import { GrowthControlCenter } from "../../components/GrowthControlCenter";
import { resolveExecutiveContext } from "../../lib/api/context";
import { loadGrowthHome } from "../../lib/api/growth";

export const metadata: Metadata = { title: "Growth" };

export default async function GrowthPage() {
  const actor = await resolveExecutiveContext();
  if (!actor.ok) return <section className="configuration-state"><span>G</span><div><h2>Growth OS needs a local founder session</h2><p>{actor.error.message}</p><small>Configure the server-side Commerce OS session. Credentials never enter the browser bundle.</small></div></section>;
  return <GrowthControlCenter results={await loadGrowthHome(actor.data.organization_id)} />;
}
