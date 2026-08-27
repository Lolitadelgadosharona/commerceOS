import type { Metadata } from "next";
import { GrowthCandidateReview } from "../../../../../components/GrowthCandidateReview";
import { resolveExecutiveContext } from "../../../../../lib/api/context";
import { loadGrowthCandidateReview } from "../../../../../lib/api/growth";

export const metadata: Metadata = { title: "Growth candidate review" };

export default async function GrowthCandidatePage({
  params,
}: {
  params: Promise<{ id: string; candidateId: string }>;
}) {
  const { id, candidateId } = await params;
  const actor = await resolveExecutiveContext();
  if (!actor.ok) {
    return (
      <section className="configuration-state">
        <div>
          <h2>Candidate review unavailable</h2>
          <p>{actor.error.message}</p>
        </div>
      </section>
    );
  }
  return (
    <GrowthCandidateReview
      candidateId={candidateId}
      results={await loadGrowthCandidateReview(
        actor.data.organization_id,
        id,
        candidateId,
      )}
    />
  );
}
