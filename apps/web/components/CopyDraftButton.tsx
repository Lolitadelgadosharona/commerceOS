"use client";

import { useState } from "react";

export function CopyDraftButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return <button className="copy-draft" type="button" onClick={async () => { await navigator.clipboard.writeText(text); setCopied(true); }}>
    {copied ? "Copied for manual send" : "Copy approved draft"}
  </button>;
}
