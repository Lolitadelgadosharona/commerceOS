"use client";

import { useState } from "react";
import type { Evidence } from "../lib/api/growth";

export function EvidencePicker({ evidence, label = "Evidence used" }: { evidence: Evidence[]; label?: string }) {
  const [selected, setSelected] = useState<string[]>(evidence.map((item) => item.id));
  const toggle = (id: string) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  return <fieldset className="evidence-picker">
    <legend>{label}</legend>
    <div className="evidence-picker-actions"><span>{selected.length} of {evidence.length} selected</span><button type="button" onClick={() => setSelected(evidence.map((item) => item.id))}>Select all</button><button type="button" onClick={() => setSelected([])}>Clear</button></div>
    {evidence.length ? evidence.map((item) => <label className={selected.includes(item.id) ? "evidence-option selected" : "evidence-option"} key={item.id}>
      <input type="checkbox" name="evidence_ids" value={item.id} checked={selected.includes(item.id)} onChange={() => toggle(item.id)} />
      <span><strong>{item.evidence_type.replaceAll("_", " ")}</strong><small>{item.source_url || "Founder observation"} · {new Date(item.collected_at).toLocaleDateString()} · {Math.round(item.confidence * 100)}% confidence</small><p>{item.observation}</p></span>
    </label>) : <p className="quiet-state">Add prospect evidence before composing this artifact.</p>}
  </fieldset>;
}
