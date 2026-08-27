import Link from "next/link";
import type { loadGrowthCandidateReview } from "../lib/api/growth";
import {
  activateGrowthProspect,
  qualifyGrowthCandidate,
  reviseGrowthPackage,
} from "../app/growth/actions";
import { GrowthActionForm } from "./GrowthActionForm";

type Data = Awaited<ReturnType<typeof loadGrowthCandidateReview>>;
const rows = <T,>(result: { ok: boolean; data?: T[] }) =>
  result.ok ? (result.data ?? []) : [];

export function GrowthCandidateReview({
  results,
  candidateId,
}: {
  results: Data;
  candidateId: string;
}) {
  const candidate = rows(results.candidates).find((item) => item.id === candidateId);
  const experiment = rows(results.experiments).find(
    (item) => item.id === results.experimentId,
  );
  if (!candidate || !experiment) {
    return (
      <section className="configuration-state">
        <div>
          <h2>Candidate unavailable</h2>
          <p>This record is missing or outside the active organization.</p>
        </div>
      </section>
    );
  }
  const evidence = rows(results.candidateEvidence).filter(
    (item) => item.candidate_id === candidate.id,
  );
  const qualification = rows(results.qualifications).find(
    (item) => item.candidate_id === candidate.id,
  );
  const assessment = results.candidateQualification.ok
    ? results.candidateQualification.data
    : null;
  const prospect = rows(results.prospects).find(
    (item) => item.source_candidate_id === candidate.id,
  );
  const capability = rows(results.capabilities).find(
    (item) => item.available && item.capability_type === "text_generation",
  );
  const gifts = prospect
    ? rows(results.gifts).filter((item) => item.prospect_id === prospect.id)
    : [];
  const outreach = prospect
    ? rows(results.outreach).filter((item) => item.prospect_id === prospect.id)
    : [];
  const gift = gifts[0];
  const draft = outreach[0];
  const score = qualification?.score;
  const painPoints = evidence.filter(
    (item) => item.evidence_type === "observed_growth_pain",
  );

  return (
    <div className="growth-workspace candidate-review">
      <Link href={`/growth/${experiment.id}`} className="back-link">
        ← Daily candidate list
      </Link>
      <header className="growth-workspace-header">
        <div>
          <p className="eyebrow">Qualification review</p>
          <h1>{candidate.business_name}</h1>
          <p>
            {candidate.category} · {candidate.location}
          </p>
        </div>
        <aside>
          <span>Evidence-backed score</span>
          <strong>{score == null ? "Incomplete" : `${score}/100`}</strong>
          <small>
            Discovery confidence {Math.round(candidate.confidence * 100)}%
          </small>
        </aside>
      </header>

      <section className="growth-stage">
        <header>
          <div>
            <p className="eyebrow">Why this candidate</p>
            <h2>Evidence, pain and qualification factors</h2>
          </div>
        </header>
        <div className="evidence-strip qualification-score-grid">
          {[
            ["Growth pain", "pain_signal"],
            ["Purchase probability", "purchase_probability"],
            ["Accessibility", "accessibility"],
            ["Quick-win potential", "quick_win_potential"],
          ].map(([label, key]) => (
            <span key={key}>
              {label}: {assessment?.calculation_inputs[key] ?? "Unknown"}
            </span>
          ))}
        </div>
        <div className="research-result">
          <strong>Qualification rationale</strong>
          <p>{assessment?.explanation ?? "Automatic qualification has not completed."}</p>
          {qualification?.missing_inputs.length ? (
            <small>Missing: {qualification.missing_inputs.join(", ")}</small>
          ) : null}
        </div>
        <div className="prospect-board">
          {evidence.map((item) => (
            <article className="prospect-card" key={item.id}>
              <div className="prospect-card-head">
                <strong>{item.evidence_type.replaceAll("_", " ")}</strong>
                <span className="status-chip">
                  {Math.round(item.confidence * 100)}%
                </span>
              </div>
              <p>{item.observation}</p>
              {item.source_url ? (
                <a href={item.source_url} target="_blank" rel="noreferrer">
                  Open public source ↗
                </a>
              ) : null}
            </article>
          ))}
        </div>
        {painPoints.length ? null : (
          <p className="configuration-note">
            No evidence-backed pain point has been confirmed yet. Unsupported values stay unknown.
          </p>
        )}
      </section>

      <section className="growth-stage">
        <header>
          <div>
            <p className="eyebrow">Founder decision</p>
            <h2>Approve before preparing customer-facing work</h2>
          </div>
        </header>
        {!prospect && score != null && score >= 70 ? (
          <GrowthActionForm action={activateGrowthProspect} label="Approve candidate">
            <input type="hidden" name="experiment_id" value={experiment.id} />
            <input type="hidden" name="candidate_id" value={candidate.id} />
            {capability ? (
              <input type="hidden" name="capability_id" value={capability.id} />
            ) : null}
            <label>
              Public contact email (optional)
              <input name="email" type="email" />
            </label>
          </GrowthActionForm>
        ) : prospect ? (
          <div className="research-result">
            <strong>Candidate approved</strong>
            <p>
              The prospect and source evidence are now available for Growth Diagnosis,
              Before/After preview, Growth Gift, and outreach drafting.
            </p>
            <Link className="button" href={`/growth/${experiment.id}#diagnosis`}>
              Continue to Growth Package
            </Link>
          </div>
        ) : (
          <p className="configuration-note">
            Approval unlocks when all four evidence-backed inputs produce a score of 70 or higher.
          </p>
        )}
        <details>
          <summary>Correct the qualification recommendation</summary>
          <GrowthActionForm
            action={qualifyGrowthCandidate}
            label="Save corrected score"
            variant="secondary"
          >
            <input type="hidden" name="experiment_id" value={experiment.id} />
            <input type="hidden" name="candidate_id" value={candidate.id} />
            {[
              ["Growth pain", "pain_signal"],
              ["Purchase probability", "purchase_probability"],
              ["Accessibility", "accessibility"],
              ["Quick-win potential", "quick_win_potential"],
            ].map(([label, key]) => (
              <label key={key}>
                {label}
                <input
                  name={key}
                  type="number"
                  min="0"
                  max="100"
                  defaultValue={assessment?.calculation_inputs[key] ?? ""}
                />
              </label>
            ))}
          </GrowthActionForm>
        </details>
      </section>

      <section className="growth-stage">
        <header>
          <div>
            <p className="eyebrow">Delivery boundary</p>
            <h2>Preview, revise, then send</h2>
          </div>
        </header>
        {gift && draft ? (
          <div className="prospect-board">
            <article className="prospect-card">
              <strong>{gift.title}</strong>
              <p>{gift.description}</p>
              <div className="research-result">
                <strong>Before</strong>
                <p>{gift.observed_issue || gift.personalized_diagnosis}</p>
                <strong>After</strong>
                <p>{gift.recommended_improvement}</p>
              </div>
              <span className="status-chip">Gift {gift.status}</span>
            </article>
            <article className="prospect-card">
              <strong>{draft.subject}</strong>
              <p>{draft.body}</p>
              <span className="status-chip">Email {draft.status}</span>
            </article>
          </div>
        ) : (
          <p>
            GrowthOS prepares the evidence-backed Before/After concept and email draft when you
            approve the candidate. Nothing is sent during preparation.
          </p>
        )}
        {prospect && capability ? (
          <details>
            <summary>Give feedback and create a new revision</summary>
            <GrowthActionForm action={reviseGrowthPackage} label="Update package">
              <input type="hidden" name="experiment_id" value={experiment.id} />
              <input type="hidden" name="prospect_id" value={prospect.id} />
              <input type="hidden" name="capability_id" value={capability.id} />
              <label>
                What should change?
                <textarea
                  name="founder_feedback"
                  required
                  placeholder="Make the gift more specific to booking visibility and soften the email opening."
                />
              </label>
            </GrowthActionForm>
          </details>
        ) : null}
        <span className="configuration-note">
          Current local environment: email connector not configured; no message can leave the system.
        </span>
      </section>
    </div>
  );
}
