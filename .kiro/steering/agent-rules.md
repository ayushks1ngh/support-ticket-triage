# Agent Rules

1. Use the LLM only after narrow deterministic rules decline.
2. Use one stateless Strands classifier with no tools.
3. Request Pydantic structured output via `structured_output_model`; never parse prose.
4. Preserve/reconcile ticket IDs and reject incomplete or duplicate model batches.
5. The model classifies category, urgency, confidence, and reason only. Python owns routing and review policy.
6. Do not expose chain-of-thought; reasons are short evidence summaries.
7. Model confidence is not calibrated probability; low confidence or any inconsistency means human review.
