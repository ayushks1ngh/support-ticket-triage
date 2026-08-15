# Support Ticket Triage Design

Use a hybrid rule-first pipeline. Pydantic validates boundaries; a small conflict-aware rule engine handles obvious cases; unresolved chunks use one no-tools Strands agent with structured output; Python reconciles IDs, derives routing, applies a configurable 0.75 confidence boundary, and emits JSON/CSV plus metrics. Provider errors and malformed model output fail closed to per-ticket human review. See `docs/ARCHITECTURE.md`, `docs/AGENT_DESIGN.md`, and `docs/DATA_SCHEMA.md`.
