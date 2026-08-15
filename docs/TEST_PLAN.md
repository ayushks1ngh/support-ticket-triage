# Test Plan

## Unit tests (offline)
- Input/output Pydantic validation, trimming, bounds, duplicates.
- Deterministic rule positives, negatives, conflicts, and urgency.
- Category/urgency routing.
- Confidence threshold and contradictory/invalid output fallback.
- Configuration bounds and missing keys.
- Provider construction and error sanitization with mocks.
- Retry strategy bounds.

## Integration tests (offline)
- JSON and CSV I/O.
- Mixed rule/model batch with fake structured provider.
- Chunking, order preservation, API-call count, provider failure isolation.
- CLI classify/evaluate smoke tests.
- Metrics contain no ticket bodies or keys.

## Optional live tests
Marked `live`; skipped unless explicit environment flag and provider key exist. Run one small ambiguous chunk, validate schema, and never assert model wording.

## Validation commands
```bash
pytest
ruff check .
ruff format --check .
mypy src
support-triage classify --input samples/tickets.json --output /tmp/results.json --offline
support-triage evaluate --dataset data/evaluation.json --offline
```

Tests must not require network or credentials by default.
