# Tradeoffs

| Decision | Benefit | Cost / limitation |
|---|---|---|
| Narrow rules before LLM | Fewer calls, predictable obvious cases | Rules cover only a small phrase set and may defer easy paraphrases |
| Single Strands agent | Explainable and low overhead | No specialist-agent decomposition |
| Batched structured output | Lower call count | Larger chunks can reduce completeness; size is bounded |
| Deterministic routing | Stable operations and easy tests | Cannot account for dynamic staffing/SLA policy |
| Model self-reported confidence + threshold | Simple explicit review boundary | Not calibrated probability; requires future labeled calibration |
| Fail closed to human review | Avoids silent misrouting | Provider incidents increase manual load |
| OpenAI-compatible provider adapters | One supported Strands integration path | Model-specific structured/tool support still varies |
| No persistent cache | Avoids sensitive retention and invalidation | Repeated ambiguous tickets incur calls |
| CLI/library MVP | Reproducible and interview-friendly | No service auth, queue, UI, or horizontal scaling |

The design intentionally favors transparent Python decisions over artificial tools, multiple agents, or repeated LLM judging.
