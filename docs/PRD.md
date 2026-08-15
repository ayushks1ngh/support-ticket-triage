# Product Requirements Document

## Problem
Support teams need consistent first-pass triage without spending an API call on every obvious ticket. The MVP accepts a ticket subject and body, assigns a category and urgency, routes it, and safely defers uncertain or invalid decisions to a human.

## Users
- Support operations reviewing routed queues.
- Engineers running batch triage from JSON or CSV.
- Reviewers evaluating a reproducible Strands Agents implementation.

## MVP outcomes
1. Validate and normalize individual or batched tickets.
2. Resolve obvious cases with narrow deterministic rules.
3. Classify unresolved tickets in small chunks with one Strands agent call per chunk.
4. Validate all model output, apply deterministic routing, and flag low-confidence or inconsistent decisions.
5. Export a stable JSON or CSV schema and report lightweight run metrics.

## Taxonomy
Categories: `account_auth`, `billing`, `technical`, `product`, `other`.
Urgency: `low`, `medium`, `high`, `critical`.
Routing is deterministic: Account Support, Billing Operations, Technical Support, Product Support, or General Support. Critical tickets additionally route to Incident Response except obvious auth/billing tickets, which retain the domain team and are marked critical.

## Success criteria
- Offline unit/integration tests pass without API credentials.
- A sample batch runs end-to-end in offline deterministic mode.
- Ambiguous tickets use a configured provider when credentials exist, otherwise fail safely to human review.
- The README enables clone, install, configure, run, test, and evaluate workflows.

## Out of scope
RAG, ticket memory, external help-desk integrations, SLA systems, queues, dashboards, model fallback, and automated remediation.
