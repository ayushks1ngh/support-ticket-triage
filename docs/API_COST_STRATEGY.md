# API Cost and Efficiency Strategy

1. **Rule bypass:** obvious account/auth, billing, and outage cases make zero API calls.
2. **Chunking:** unresolved tickets are grouped by configurable `BATCH_SIZE` (default 10), reducing calls from N to roughly `ceil(unresolved/N)` while limiting output truncation risk.
3. **Sequential default:** bounded concurrency defaults to one. Higher values are allowed but capped and should only be used after observing provider limits.
4. **Bounded retries:** Strands throttling retries use configurable total attempts (default 3), exponential delay, and cap. No infinite or recursive retries.
5. **Compact prompts:** only IDs, subjects, bodies, and stable taxonomy are transmitted. No prior conversation or model validation pass.
6. **No validation LLM:** Pydantic and deterministic semantic validation handle malformed results.
7. **Metrics:** API-call count, retry configuration/events where observable, model-ticket count, and latency are reported.
8. **No persistent MVP cache:** support content may contain sensitive data; avoiding storage is safer than speculative savings. A future cache requires encryption, expiry, access control, and content-hash/privacy review.

Cost is provider/model dependent and is not hardcoded. The evaluation report measures calls and latency; token/currency totals are reported only when provider metrics/pricing are available, never estimated as fact.
