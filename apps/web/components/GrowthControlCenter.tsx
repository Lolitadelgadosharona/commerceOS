import Link from "next/link";
import type { loadGrowthHome } from "../lib/api/growth";
import { GrowthActionForm } from "./GrowthActionForm";
import { createGrowthWorkspace } from "../app/growth/actions";

type Data=Awaited<ReturnType<typeof loadGrowthHome>>;
const data=<T,>(result:{ok:boolean;data?:T})=>result.ok?result.data:undefined;
const money=(value:number,currency="USD")=>new Intl.NumberFormat("en-US",{style:"currency",currency}).format(value);

export function GrowthControlCenter({results}:{results:Data}){
  const experiments=data(results.experiments)??[],candidates=data(results.candidates)??[],prospects=data(results.prospects)??[],approvals=data(results.approvals)??[],revenues=data(results.revenues)??[],costs=data(results.costs)??[],profits=data(results.profits)??[],learning=data(results.learning)??[],dashboard=data(results.dashboard),readiness=data(results.readiness);
  const revenue=revenues.reduce((sum,item)=>sum+Number(item.amount),0),cost=costs.reduce((sum,item)=>sum+Number(item.amount),0),pending=approvals.filter(item=>item.status==="pending");
  return <div className="growth-shell">
    <section className="growth-hero"><div><p className="eyebrow">Founder revenue workspace</p><h1>Turn evidence into the next right action.</h1><p>Operate a governed growth loop without confusing drafts, forecasts, or manual activity with real execution.</p></div><div className="mode-card"><span>Execution mode</span><strong>Founder controlled</strong><small>No external Email connector configured — manual send mode active</small></div></section>
    <section className="growth-kpis" aria-label="Growth results">
      <article><span>Active work</span><strong>{experiments.filter(x=>["draft","active","paused"].includes(x.status)).length}</strong><small>Revenue experiments</small></article>
      <article><span>Prospects</span><strong>{prospects.length||candidates.length}</strong><small>{dashboard?.qualified_prospects??0} qualified</small></article>
      <article><span>Needs approval</span><strong>{pending.length}</strong><small>Human decisions</small></article>
      <article><span>Actual revenue</span><strong>{revenues.length?money(revenue):"Unknown"}</strong><small>{revenues.length?"Finance observations":"No actual revenue recorded"}</small></article>
      <article><span>Actual cost</span><strong>{costs.length?money(cost):"Unknown"}</strong><small>{costs.length?"Finance observations":"Cost evidence missing"}</small></article>
      <article className="warning"><span>Actual contribution</span><strong>{profits.length?money(profits.reduce((s,x)=>s+Number(x.contribution_profit),0)):"Unknown"}</strong><small>{profits.length?"Finance-owned assessments":"Not calculated from incomplete facts"}</small></article>
    </section>
    <section className="growth-layout"><div className="growth-main">
      <div className="growth-section-heading"><div><p className="eyebrow">What am I working on?</p><h2>Growth workspaces</h2></div></div>
      {experiments.length?<div className="workspace-list">{experiments.map(item=><Link className="workspace-row" href={`/growth/${item.id}`} key={item.id}><div><span className={`stage-dot ${item.status}`}/><div><strong>{item.name}</strong><p>{item.target_segment}</p></div></div><div><span className="status-chip">{item.status}</span><span>Open workspace →</span></div></Link>)}</div>:<div className="honest-empty"><strong>No Growth workspace yet.</strong><p>Create the first real project below. Nothing has been fabricated for this empty state.</p></div>}
      <details className="growth-create"><summary>Create a Growth workspace</summary><GrowthActionForm action={createGrowthWorkspace} label="Create workspace"><div className="form-grid"><label>Name<input name="name" required placeholder="Beauty Growth Experiment 001"/></label><label>Target segment<input name="segment" required placeholder="Independent beauty studios"/></label><label className="wide">Objective<textarea name="description" required placeholder="Validate an evidence-backed visibility offer with a controlled founder workflow."/></label><label>Offer type<select name="offer_type"><option value="growth_visibility_audit">Growth visibility audit</option><option value="geo_optimization">GEO optimization</option><option value="website_growth_fix">Website growth fix</option><option value="other">Other</option></select></label><label>Target count<input name="target_count" type="number" min="0" defaultValue="6"/></label><label className="wide">Message strategy<input name="message_strategy" defaultValue="Evidence-first founder outreach"/></label></div></GrowthActionForm></details>
    </div><aside className="growth-rail">
      <section className="readiness-card"><p className="eyebrow">Operational readiness</p><h2>{readiness?.growth_os==="ready"?"Growth OS is usable":"Setup needs attention"}</h2><div className="readiness-grid">{[["Growth OS",readiness?.growth_os],["AI",readiness?.ai],["Worker",readiness?.worker],["Database",readiness?.database],["Sending","manual"],["Connectors",readiness?.external_connectors]].map(([label,status])=><div key={label}><span>{label}</span><strong className={`readiness-${status}`}>{String(status??"unknown").replaceAll("_"," ")}</strong></div>)}</div>{readiness?.guidance.map(item=><p className="readiness-guidance" key={item}>{item}</p>)}</section>
      <section className="attention-card"><p className="eyebrow">What needs attention?</p><h2>Founder action queue</h2>{pending.length?pending.slice(0,5).map(item=><div className="attention-item" key={item.id}><span className="attention-icon">!</span><div><strong>{item.requested_action.replaceAll("_"," ")}</strong><p>{item.reason}</p></div></div>):<div className="quiet-state">No pending approvals.</div>}{candidates.filter(x=>x.status==="researching").slice(0,3).map(item=><div className="attention-item" key={item.id}><span className="attention-icon neutral">↻</span><div><strong>{item.business_name}</strong><p>Research or evidence review in progress</p></div></div>)}</section>
      <section className="next-card"><p className="eyebrow">What should I do next?</p><h2>{experiments.length?pending.length?"Review the oldest approval.":candidates.length?"Open a workspace and advance one prospect.":"Add the first evidence-backed prospect.":"Create your first Growth workspace."}</h2><p>Growth OS recommends; a human decides and performs every external action.</p></section>
      <section className="learning-card"><p className="eyebrow">Recent learning</p>{learning.length?learning.slice(0,3).map((item,i)=><div key={item.id??i}><strong>{item.title??item.pattern??"Learning recommendation"}</strong><p>{item.recommendation??"Awaiting human review"}</p></div>):<p>No accepted learning recommendations yet.</p>}</section>
    </aside></section>
  </div>;
}
