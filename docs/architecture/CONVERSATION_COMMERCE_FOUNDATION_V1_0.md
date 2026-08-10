# Conversation Commerce Foundation v1.0

Status: frozen Sprint 011 implementation contract

## Purpose and ownership

Operations owns conversation threads, message history, human-handoff workflow, and links from conversations to trusted knowledge. Customer remains the optional canonical participant; identity resolution remains Governance-owned. Product Truth, product knowledge, and claim policy remain Build-owned and are referenced without copying or changing them.

This foundation stores interaction state. It does not contact channels, generate replies, execute customer service, make commitments, approve exceptions, issue refunds, negotiate terms, or create orders.

## Thread lifecycle

A `ConversationThread` is organization-scoped and may reference a canonical Customer. Supported channel classifications are website, email, Instagram, Facebook, TikTok, WhatsApp, Reddit, and other. They are classifications only; no connector exists.

The lifecycle is open, waiting, resolved, escalated, and archived. Archived is terminal. Resolved threads may be reopened by an explicit authorized operation. A handoff escalates its thread. Priority is low, normal, high, or urgent. Optional role assignment references Governance's revocable role registry and conveys responsibility, not approval authority.

## Messages

Messages have a unique, monotonically increasing sequence within each thread, direction, sender classification, immutable content, and timestamps. Customer messages are inbound. Human, system, and AI records are outbound. Messages cannot be appended to resolved or archived threads.

`AI` is a provenance classification only. It does not grant delivery, approval, negotiation, exception, refund, financial, or other execution authority. Sprint 011 contains no reply generation or delivery path.

## Intent and emotion observations

Intent and emotion signals are explicit, confidence-scored records attached to a message. Supported intents cover buying, product questions, objections/concerns, support, refunds, and negotiation. Supported emotions are positive, neutral, confused, frustrated, and angry.

The API accepts supplied classifications only. It performs no sentiment analysis, LLM inference, or automated classification. Confidence records evidence uncertainty and is constrained to 0–1.

## Human handoff

Handoffs record reason, priority, status, optional assigned human user, and resolution time. Reasons include high-value customer, angry customer, complex negotiation, policy exception, and AI uncertainty. Assignment requires an organization-scoped User. Handoff status is pending, assigned, resolved, or cancelled. Handoffs create work for humans; they do not resolve the underlying customer request automatically.

## Trusted knowledge links

Conversation knowledge references point to organization-scoped Product Truth, Product Knowledge, Claim Policy, or FAQ records. References are validated against the authoritative source table and never duplicate claims. A FAQ is represented by a Product Knowledge item categorized as FAQ. Future response systems must re-read current authorized knowledge and respect claim policy before presenting content.

## Security and scope

All records are organization-scoped and cross-organization references are rejected. Conversation content can contain PII and must follow the Security and Privacy Foundation's access, logging, minimization, retention, and deletion rules. The existing authentication activation limitation still prohibits public deployment.

Explicitly excluded: LLMs, agents, automation, automated replies, sentiment analysis, external messaging APIs, Shopify chat, social DMs, WhatsApp, email integrations, and customer-service execution.
