# Data Schema

## Input ticket
```json
{"ticket_id":"T-001","subject":"Cannot sign in","body":"Password reset link has expired."}
```
Constraints: strings are trimmed; IDs are non-empty and unique within a batch; subject/body are non-empty and length-bounded.

## Final result
```json
{
  "ticket_id": "T-001",
  "category": "account_auth",
  "urgency": "high",
  "confidence": 0.96,
  "routing_team": "Account Support",
  "human_review": false,
  "reason": "Clear account access issue.",
  "source": "rule"
}
```

`source` is `rule`, `llm`, or `fallback`. Confidence is a finite number from 0 through 1. The final schema is stable across JSON and CSV.

## Model-only schema
The model returns a batch envelope with classifications containing only ticket ID, category, urgency, confidence, and reason. Team and review status are derived in Python. Pydantic rejects extra fields to expose drift.

## Run summary
Includes request ID, ticket counts, deterministic/model/fallback counts, provider, model ID, API calls, retries, elapsed milliseconds, failure count, and human-review count. It contains no ticket body or secret.
