# Model Benchmark: Groq vs NVIDIA NIM

## Objective

Compare Groq (llama-3.3-70b-versatile) against NVIDIA NIM (nemotron-3.5-lightning-30b-a3b) as runtime providers for the Support Ticket Triage Agent, using identical application configuration and evaluation methodology.

## Models tested

| Provider | Model | Parameters | Endpoint |
|---|---|---|---|
| Groq | llama-3.3-70b-versatile | 70B | `https://api.groq.com/openai/v1` |
| NVIDIA NIM | nvidia/nemotron-3.5-lightning-30b-a3b | 30B (MoE, 3B active) | `https://integrate.api.nvidia.com/v1` |

## Hardware / API assumptions

Both are hosted API endpoints. No local GPU was used. Latency includes network round-trip from the test environment. Results may vary by region, load, and time of day.

## Dataset

`data/evaluation.json` — 8 labeled tickets:
- 4 resolved by deterministic rules (not sent to either model)
- 4 unresolved tickets classified by the model

Both providers received the same 4 unresolved tickets per run.

## Experimental controls

| Control | Value | Same across providers? |
|---|---|---|
| Dataset | `data/evaluation.json` (8 cases) | ✅ |
| Deterministic rules | Unchanged V1 rules | ✅ |
| Prompt | Unchanged V1 system + taxonomy prompt | ✅ |
| Output schema | `BatchModelOutput` Pydantic model | ✅ |
| Confidence threshold | 0.75 | ✅ |
| Routing logic | Deterministic V1 routing | ✅ |
| Human-review policy | Unchanged V1 validator | ✅ |
| Batch size | 10 | ✅ |
| Concurrency | 1 (sequential) | ✅ |
| Temperature | 0.01 | ✅ |
| Max tokens | 4096 | ✅ |
| Retry policy | 3 attempts, exponential backoff | ✅ |
| Timeout | 30s | ✅ |

## Number of runs

3 runs per provider, sequential, with 2-second pauses between runs.

## Results

Date: 2026-08-15

| Metric | Groq (llama-3.3-70b) | NVIDIA (nemotron-3.5-lightning-30b) |
|---|---:|---:|
| Runs | 3 | 3 |
| Exact accuracy | 0.625 | 0.625 |
| Category accuracy | 0.750 | 0.833 |
| Urgency accuracy | 0.875 | 0.750 |
| Routing accuracy | 0.750 | 0.833 |
| Human-review precision | 0.611 | 1.000 |
| Human-review recall | 1.000 | 0.833 |
| Structured output success | 100% (3/3) | 67% (2/3) |
| API calls (total, 3 runs) | 3 | 3 |
| Retries | 0 | 0 |
| Failures | 0 | 4 (1 full-run fallback) |
| Timeout events | 0 | 0 |
| Rule classifications | 4 | 4 |
| Model classifications (avg/run) | 4 | 2.7 (due to 1 failed run) |
| Fallback classifications (total) | 0 | 4 |
| Avg total latency (ms) | 5,134 | 19,944 |
| Avg model-call latency (ms) | 5,134 | 19,944 |
| p95 latency (ms) | 13,160 | 30,863 |
| Malformed outputs | 0 | 4 |

## Errors / failures

**Groq:** Zero errors across all 3 runs. 100% structured-output conformance.

**NVIDIA:** 1 out of 3 runs produced malformed structured output, causing all 4 model-classified tickets in that run to fall back to human review. The failure was intermittent — isolated retests showed NVIDIA can produce valid structured output. This suggests the model's structured-output compliance is less consistent than Groq's for this schema size.

## Latency

Groq is approximately **3.9× faster** than NVIDIA for this workload.

- Groq average: ~5.1 seconds per evaluation pass (4 model tickets in 1 call)
- NVIDIA average: ~19.9 seconds per evaluation pass

Note: NVIDIA's nemotron-3.5-lightning is a reasoning-enabled model and may be spending tokens on internal chain-of-thought, contributing to higher latency.

## API usage

Both providers consumed exactly 1 API call per evaluation run (as designed by the batching architecture). Rule-resolved tickets consumed zero calls on both providers.

## Quality comparison

When NVIDIA succeeded (2 of 3 runs):
- **Category accuracy was higher** (0.833 vs 0.750) — NVIDIA correctly classified one additional ambiguous ticket.
- **Routing accuracy was higher** (0.833 vs 0.750) — directly follows from better category accuracy.
- **Human-review precision was higher** (1.000 vs 0.611) — NVIDIA was more selective about flagging for review.
- **Urgency accuracy was lower** (0.750 vs 0.875) — NVIDIA misclassified one urgency level.
- **Human-review recall was lower** (0.833 vs 1.000) — NVIDIA missed one case that should have been reviewed.

Groq's advantage is **consistency** — it never fails and never misses a review case.

## Limitations

1. **Small sample** — only 4 model-classified tickets per run; quality differences may not be statistically significant.
2. **Single session** — latency can vary by time of day and provider load.
3. **Intermittent failures** — NVIDIA's 33% failure rate may improve with different models or API versions.
4. **No p95 confidence** — 3 observations per provider is insufficient for robust percentile claims.
5. **Model mismatch** — Groq uses a 70B model while NVIDIA uses a 30B MoE; this is not a controlled parameter-count comparison.

## Recommendation

**WINNER BY QUALITY:** Tie — NVIDIA shows slightly better category accuracy when it works, but Groq has better urgency accuracy and never misses review cases.

**WINNER BY LATENCY:** Groq (3.9× faster)

**WINNER BY RELIABILITY:** Groq (100% structured output success vs 67%)

**WINNER BY API EFFICIENCY:** Tie (identical call count by design)

**OVERALL RECOMMENDATION:** **KEEP GROQ AS DEFAULT**

Groq provides the best combination of reliability, latency, and consistent quality for this agent. NVIDIA's intermittent structured-output failures and 4× higher latency make it unsuitable as the primary provider today, despite occasionally better category accuracy.

NVIDIA could be revisited if:
- A more reliable NVIDIA model becomes available for structured output
- The latency difference narrows
- More evaluation data confirms a meaningful quality advantage

The 0.75 confidence threshold remains uncalibrated and should not be tuned based on this small benchmark.
