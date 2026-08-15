# Evaluation Plan

## Dataset
`data/evaluation.json` contains labeled examples across every category and urgency, obvious rule cases, ambiguous model cases, and expected human-review behavior. Labels are design fixtures, not claims about real production distribution.

## Metrics
- Exact triage accuracy: category, urgency, and routing all correct.
- Category accuracy.
- Urgency accuracy.
- Routing accuracy.
- Human-review precision and recall when both positive/negative expected labels exist.
- API calls and tickets per call.
- End-to-end latency.
- Rule/model/fallback counts.

## Modes
- `--offline`: reproducible rule/fallback baseline; ambiguous cases are intentionally reviewed.
- Fake-provider integration tests: deterministic full-pipeline correctness.
- Optional live provider: measures configured model behavior and cost/call metadata where exposed.

## Reporting discipline
The script emits measurements from that invocation only. README results must name mode, dataset, timestamp, and command. No fabricated live-model quality or cost claims.

## Exit behavior
Evaluation exits non-zero for malformed datasets or execution failures. Accuracy alone does not fail the command unless a future explicit quality gate is configured.
