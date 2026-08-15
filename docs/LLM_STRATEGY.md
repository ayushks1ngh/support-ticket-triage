# LLM Strategy

## When the model is used
Only valid tickets not resolved by narrow, conflict-aware rules are sent to a model. One Strands agent handles classification; routing and review policy remain deterministic.

## Strands API (verified 2026-08-15)
Pinned target: `strands-agents==1.52.0`. Use `Agent(model=..., callback_handler=None, retry_strategy=ModelRetryStrategy(...))`, invoke with `structured_output_model=BatchModelOutput`, and read `AgentResult.structured_output`. Catch `StructuredOutputException`. The older `Agent.structured_output()` method is deprecated and is not used.

## Providers
Both adapters use Strands `OpenAIModel`, the official custom OpenAI-compatible endpoint mechanism:
- Groq: `https://api.groq.com/openai/v1`, key `GROQ_API_KEY`.
- NVIDIA NIM hosted API: `https://integrate.api.nvidia.com/v1`, key `NVIDIA_API_KEY`.
Provider/model selection is environment-driven. Model IDs are explicit configuration because availability changes. The default Groq model is `llama-3.3-70b-versatile`; users should verify current account availability.

## Reliability
Temperature is near zero, output is Pydantic-validated, IDs are reconciled against each requested chunk, and semantic inconsistencies fail closed. Strands retries throttling with bounded exponential backoff. MVP uses at most one additional application-level retry only for a whole transient provider call if configured; defaults avoid layered retry amplification.

## Offline behavior
Core tests use fake providers. `--offline` performs rules and returns human-review fallbacks for unresolved tickets, making demonstrations possible without credentials while never pretending ambiguous tickets were model-classified.

## References
- https://strandsagents.com/docs/user-guide/quickstart/python/
- https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/
- https://strandsagents.com/docs/user-guide/concepts/agents/retry-strategies/
- https://strandsagents.com/docs/user-guide/concepts/model-providers/openai/
- https://console.groq.com/docs/openai
- https://docs.api.nvidia.com/nim/reference/llm-apis
