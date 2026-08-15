# Requirements and Traceability

Status values are `planned`, `implemented`, or `verified`. This table is updated as work progresses.

| ID | Requirement | Acceptance criteria | Status | Test coverage |
|---|---|---|---|---|
| REQ-001 | Accept subject and body | Valid JSON/CSV records with non-empty `ticket_id`, `subject`, and `body` are accepted; invalid records are reported without crashing the batch | verified | `test_models.py`, `test_batch.py` |
| REQ-002 | Classify category | Every valid result uses one documented category | verified | `test_rules.py`, `test_classifier.py` |
| REQ-003 | Classify urgency | Every valid result uses low/medium/high/critical | verified | `test_rules.py`, `test_classifier.py` |
| REQ-004 | Produce confidence | Confidence is validated in [0,1] and accompanied by a concise reason | verified | `test_models.py`, `test_validator.py` |
| REQ-005 | Route ticket | Routing is deterministic from validated category/urgency | verified | `test_router.py` |
| REQ-006 | Human review boundary | Confidence below configured threshold, invalid/contradictory output, provider failure, or unsupported cases set `human_review=true` | verified | `test_validator.py`, `test_classifier.py` |
| REQ-007 | Process batches efficiently | Obvious rules avoid LLM calls; unresolved records are chunked; calls and retries are bounded | verified | `test_batch.py`, `test_provider.py` |
| REQ-008 | Structured output | Pydantic validates inputs, model batch output, and final results; JSON and CSV are supported | verified | `test_models.py`, `test_cli.py` |
| REQ-009 | Sample data and output | Versioned input and generated expected/demo output cover categories, urgency, ambiguity, and review | verified | evaluation smoke test |
| REQ-010 | Reproducible setup | Pinned dependencies, `.env.example`, and README commands work from a clean environment | verified | clean install/manual audit |
| REQ-011 | Use Strands Agents | LLM classification uses supported Strands `Agent` structured-output invocation | verified | provider integration test with fake agent |
| REQ-012 | Provider switching | `MODEL_PROVIDER` selects Groq or NVIDIA NIM with no code change; keys remain environment-only | verified | `test_config.py`, `test_provider.py` |
| REQ-013 | Retry/rate-limit hygiene | Total attempts, delay, batch size, and concurrency are bounded/configurable; no infinite retry | verified | `test_provider.py` |
| REQ-014 | Evaluation | Script reports category, urgency, routing, exact accuracy, review behavior, API calls, and latency without fabricated results | verified | `test_evaluation.py` |
| REQ-015 | Basic observability | Run summary includes request ID, counts, provider/model, calls, retries, latency, failures, and reviews without ticket text or keys | verified | `test_batch.py` |
| REQ-016 | Security hygiene | Secrets ignored, inputs bounded, errors sanitized, no sensitive body logging | verified | `test_config.py`, repository audit |

## Functional source
These requirements derive from the Rooman challenge specification supplied in the project conversation. No separate specification file was present in the repository.
