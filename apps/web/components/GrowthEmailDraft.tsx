"use client";

import { useState } from "react";

type Props = {
  businessName: string;
  recipientEmail: string | null;
  subject: string;
  opening: string;
  observation: string;
  giftExplanation: string;
  valueHook: string;
  softCta: string;
  previewSrc: string;
};

const escapeHtml = (value: string) => value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");

async function imageAsDataUrl(src: string) {
  const response = await fetch(src);
  if (!response.ok) throw new Error("Preview image could not be loaded.");
  const blob = await response.blob();
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

export function GrowthEmailDraft({ businessName, recipientEmail, subject, opening, observation, giftExplanation, valueHook, softCta, previewSrc }: Props) {
  const [copyState, setCopyState] = useState<"idle" | "copying" | "copied" | "error">("idle");
  const paragraphs = [opening, observation, giftExplanation, valueHook, softCta].filter(Boolean);
  const plainText = `${paragraphs.join("\n\n")}\n\nBest,\n[Your name]`;
  const copyEmail = async () => {
    setCopyState("copying");
    try {
      const imageData = await imageAsDataUrl(previewSrc);
      const html = `<div style="max-width:680px;font-family:Arial,sans-serif;color:#202421;font-size:16px;line-height:1.6">${paragraphs.slice(0, 3).map((p) => `<p>${escapeHtml(p)}</p>`).join("")}<div style="margin:24px 0"><img src="${imageData}" alt="${escapeHtml(businessName)} booking clarity concept preview" style="display:block;width:100%;max-width:680px;height:auto;border:1px solid #e2e2df;border-radius:12px"/><p style="margin:8px 0 0;color:#6a716c;font-size:12px">Concept preview for discussion — not a live implementation.</p></div>${paragraphs.slice(3).map((p) => `<p>${escapeHtml(p)}</p>`).join("")}<p>Best,<br>[Your name]</p></div>`;
      if (typeof ClipboardItem !== "undefined" && navigator.clipboard.write) {
        try {
          await navigator.clipboard.write([new ClipboardItem({ "text/html": new Blob([html], { type: "text/html" }), "text/plain": new Blob([plainText], { type: "text/plain" }) })]);
        } catch {
          const holder = document.createElement("div");
          holder.contentEditable = "true";
          holder.style.position = "fixed";
          holder.style.left = "-10000px";
          holder.innerHTML = html;
          document.body.appendChild(holder);
          const selection = window.getSelection();
          const range = document.createRange();
          range.selectNodeContents(holder);
          selection?.removeAllRanges();
          selection?.addRange(range);
          const copied = document.execCommand("copy");
          selection?.removeAllRanges();
          holder.remove();
          if (!copied) throw new Error("Rich clipboard copy was rejected.");
        }
      } else await navigator.clipboard.writeText(plainText);
      setCopyState("copied");
    } catch { setCopyState("error"); }
  };
  return <article className="growth-email-composer">
    <header><div><span>Standard email preview</span><strong>Founder outreach</strong></div><button type="button" onClick={copyEmail} disabled={copyState === "copying"}>{copyState === "copying" ? "Preparing image…" : copyState === "copied" ? "Email copied" : copyState === "error" ? "Copy failed — retry" : "Copy email + image"}</button></header>
    <dl><div><dt>From</dt><dd>[Your name]</dd></div><div><dt>To</dt><dd>{recipientEmail || `${businessName} · contact email not added`}</dd></div><div><dt>Subject</dt><dd>{subject}</dd></div></dl>
    <div className="growth-email-body">{paragraphs.slice(0, 3).map((p) => <p key={p}>{p}</p>)}<figure><img src={previewSrc} alt={`${businessName} booking clarity current-versus-concept preview`} /><figcaption>Concept preview for discussion — not a live implementation.</figcaption></figure>{paragraphs.slice(3).map((p) => <p key={p}>{p}</p>)}<p>Best,<br />[Your name]</p></div>
    <footer>Copy creates a rich email with the visual embedded. Review the recipient and signature before sending.</footer>
  </article>;
}
