import Link from "next/link";
import type { loadGrowthCandidateReview } from "../lib/api/growth";
import {
  activateGrowthProspect,
  qualifyGrowthCandidate,
  reviseGrowthPackage,
} from "../app/growth/actions";
import { GrowthActionForm } from "./GrowthActionForm";
import { GrowthResearchRefresh } from "./GrowthResearchRefresh";

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
  const researchRun = rows(results.runs).find(
    (item) => item.candidate_id === candidate.id,
  );
  const researchResult = researchRun
    ? results.researchResults.find(
        (item) => item.research_run_id === researchRun.id,
      )
    : undefined;
  const researchActive = ["queued", "running"].includes(researchRun?.status ?? "");
  const keyEvidence = evidence
    .filter(
      (item, index, all) =>
        all.findIndex((other) => other.observation === item.observation) === index,
    )
    .sort((left, right) => right.confidence - left.confidence)
    .slice(0, 3);
  const scoreDimensions = [
    ["Growth pain", "pain_signal", "How clearly public evidence reveals a business problem"],
    [
      "Purchase probability",
      "purchase_probability",
      "Likelihood that this business may value the proposed improvement",
    ],
    ["Accessibility", "accessibility", "How reachable and verifiable the business appears"],
    [
      "Quick-win potential",
      "quick_win_potential",
      "How practical a focused before/after improvement appears",
    ],
  ] as const;

  return (
    <div className="growth-workspace candidate-review">
      <GrowthResearchRefresh active={researchActive} />
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

      <section className="candidate-decision-banner">
        <div>
          <p className="eyebrow">Your next decision</p>
          <h2>
            {gift && draft
              ? "Review the prepared solution"
              : prospect
                ? "Generate the customer-specific solution"
                : "Approve this candidate and generate the solution"}
          </h2>
          <p>
            {prospect
              ? "This candidate is approved. Generate an evidence-backed diagnosis, Before/After preview, Growth Gift and email draft. Nothing will be sent."
              : "Approval converts this reviewed candidate into a prospect and prepares the full proposal package. Nothing will be sent."}
          </p>
        </div>
        {gift && draft ? (
          <a className="growth-button candidate-primary-action" href="#solution-package">
            Review solution package
          </a>
        ) : prospect && capability ? (
          <GrowthActionForm action={reviseGrowthPackage} label="Generate solution package">
            <input type="hidden" name="experiment_id" value={experiment.id} />
            <input type="hidden" name="prospect_id" value={prospect.id} />
            <input type="hidden" name="capability_id" value={capability.id} />
          </GrowthActionForm>
        ) : !prospect && score != null && score >= 70 ? (
          <GrowthActionForm action={activateGrowthProspect} label="Approve & generate solution">
            <input type="hidden" name="experiment_id" value={experiment.id} />
            <input type="hidden" name="candidate_id" value={candidate.id} />
            {capability ? (
              <input type="hidden" name="capability_id" value={capability.id} />
            ) : null}
          </GrowthActionForm>
        ) : (
          <span className="configuration-note">
            Approval unlocks after an evidence-backed score of 70 or higher.
          </span>
        )}
      </section>

      <section className="growth-stage candidate-score-dashboard">
        <header>
          <div>
            <p className="eyebrow">Why this candidate</p>
            <h2>Candidate decision dashboard</h2>
          </div>
        </header>
        <div className="candidate-dimension-grid">
          {scoreDimensions.map(([label, key, description]) => (
            <article key={key}>
              <div>
                <span>{label}</span>
                <strong>{assessment?.calculation_inputs[key] ?? "—"}</strong>
              </div>
              <div className="candidate-score-track">
                <span
                  style={{
                    width: `${assessment?.calculation_inputs[key] ?? 0}%`,
                  }}
                />
              </div>
              <p>{description}</p>
            </article>
          ))}
        </div>
        <div className="candidate-analysis-summary">
          <strong>Qualification rationale</strong>
          <p>{assessment?.explanation ?? "Automatic qualification has not completed."}</p>
          {qualification?.missing_inputs.length ? (
            <small>Missing: {qualification.missing_inputs.join(", ")}</small>
          ) : null}
        </div>
        <div className="candidate-key-evidence">
          <div className="candidate-subheading">
            <strong>Key evidence</strong>
            <span>{keyEvidence.length} decision-relevant findings</span>
          </div>
          {keyEvidence.map((item, index) => (
            <article key={item.id}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <p>{item.observation}</p>
              <strong>{Math.round(item.confidence * 100)}%</strong>
              {item.source_url ? (
                <a href={item.source_url} target="_blank" rel="noreferrer">
                  Source ↗
                </a>
              ) : null}
            </article>
          ))}
        </div>
        {evidence.length > keyEvidence.length ? (
          <details className="candidate-all-evidence">
            <summary>View all {evidence.length} evidence records</summary>
            {evidence.map((item) => (
              <p key={item.id}>{item.observation}</p>
            ))}
          </details>
        ) : null}
        {painPoints.length ? null : (
          <p className="configuration-note">
            No evidence-backed pain point has been confirmed yet. Unsupported values stay unknown.
          </p>
        )}
      </section>

      {researchRun ? (
        <section className="growth-stage">
          <header>
            <div>
              <p className="eyebrow">Governed research</p>
              <h2>Research status and next step</h2>
            </div>
            <span className="status-chip">{researchRun.status}</span>
          </header>
          {researchActive ? (
            <div className="research-result">
              <strong>Research is processing</strong>
              <p>This page refreshes automatically. You can keep it open; no customer contact occurs.</p>
            </div>
          ) : researchRun.status === "failed" ? (
            <p className="inline-alert">Research failed: {researchRun.failure_reason}</p>
          ) : researchResult ? (
            <div className="research-result">
              <strong>Research completed</strong>
              <p>{researchResult.summary}</p>
              <strong>Potential growth issues</strong>
              <ul>
                {researchResult.potential_growth_issues.map((item) => <li key={item}>{item}</li>)}
              </ul>
              <small>
                Confidence {Math.round(researchResult.confidence * 100)}% · Missing: {researchResult.missing_information.join(", ") || "None recorded"}
              </small>
              <p className="configuration-note">Next: review the evidence above, then approve the candidate to prepare the Growth Gift and email draft.</p>
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="growth-stage">
        <header>
          <div>
            <p className="eyebrow">Solution direction</p>
            <h2>What GrowthOS recommends solving</h2>
          </div>
        </header>
        <div className="candidate-solution-grid">
          <article>
            <span>01 · Conversion path</span>
            <strong>Make the booking next step unmistakable</strong>
            <p>
              Turn the current booking call-to-action into a clearer, lower-friction decision path.
            </p>
          </article>
          <article>
            <span>02 · Trust</span>
            <strong>Place proof beside the booking decision</strong>
            <p>
              Build a customer-safe trust section using only verified services, approved claims and
              available proof.
            </p>
          </article>
          <article>
            <span>03 · Positioning</span>
            <strong>Clarify why this studio is the right choice</strong>
            <p>
              Translate broad brand language into a focused service promise without unsupported
              claims.
            </p>
          </article>
        </div>
        <p className="configuration-note">
          These are advisory solution directions derived from the reviewed public evidence. The
          generated package will turn them into a customer-specific Before/After preview.
        </p>
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

      <section className="growth-stage" id="solution-package">
        <header>
          <div>
            <p className="eyebrow">Delivery boundary</p>
            <h2>Preview, revise, then send</h2>
          </div>
        </header>
        {gift && draft ? (
          <div className="candidate-package-grid">
            <article className="candidate-preview-card">
              <strong>{gift.title}</strong>
              <p>{gift.description}</p>
              <div className="candidate-before-after">
                <div>
                  <span>Before</span>
                  <p>{gift.before_state || gift.observed_issue}</p>
                </div>
                <div>
                  <span>After</span>
                  <p>{gift.after_state || gift.recommended_improvement}</p>
                </div>
              </div>
              <span className="status-chip">Gift {gift.status}</span>
            </article>
            <article className="candidate-email-card">
              <span>Email draft</span>
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
        {prospect && capability && gift && draft ? (
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
