# V1.1 Evaluation Results

## Dataset

`data/evaluation_v1_1.json` — 105 labeled tickets

| Category | Count |
|---|---:|
| account_auth | 21 |
| billing | 20 |
| technical | 24 |
| product | 20 |
| other | 20 |

| Urgency | Count |
|---|---:|
| high | 32 |
| medium | 33 |
| low | 30 |
| critical | 10 |

| Human review expected | Count |
|---|---:|
| false | 85 |
| true | 20 |

## Live evaluation (Groq, llama-3.3-70b-versatile, 2026-08-15)

| Metric | Value |
|---|---:|
| Total tickets | 105 |
| Exact accuracy | 0.562 |
| Category accuracy | 0.771 |
| Urgency accuracy | 0.724 |
| Routing accuracy | 0.752 |
| Human-review precision | 0.429 |
| Human-review recall | 0.750 |
| API calls | 9 |
| Tickets per API call | 9.9 |
| Total latency | ~47s |
| Rule classifications | 16 |
| Model classifications | 89 |
| Fallback classifications | 0 |
| Structured output failures | 0 |

## Confidence analysis

| Statistic | Value |
|---|---:|
| Mean confidence | 0.818 |
| Median confidence | 0.800 |
| Min confidence | 0.400 |
| Max confidence | 0.960 |
| Stdev | 0.111 |
| Below threshold (< 0.75) | 23 tickets |
| High confidence (≥ 0.85) | 43 tickets |

### High-confidence errors (confidence ≥ 0.85, category wrong)

9 cases where the model was confident but predicted the wrong category:

| Ticket | Confidence | Predicted | Expected | Source |
|---|---:|---|---|---|
| A-007 | 0.90 | technical | account_auth | llm |
| A-011 | 0.90 | technical | account_auth | llm |
| P-004 | 0.90 | technical | product | llm |
| P-010 | 0.90 | technical | product | llm |
| P-014 | 0.90 | technical | product | llm |
| X-001 | 0.90 | account_auth | other | llm |
| X-003 | 0.96 | billing | other | rule |
| X-004 | 0.96 | account_auth | other | rule |
| X-005 | 0.90 | account_auth | other | llm |

### Key patterns

1. **product → technical confusion (9 cases):** The model over-classifies product issues (crashes, timeouts, auto-save loss) as technical. These tickets mention symptoms like "crashes" or "timeout" that overlap with technical vocabulary.

2. **Rule false positives on conflicting tickets (2 cases):** X-003 and X-004 match rule phrases but contain multiple-category signals. The conflict detection works only when BOTH categories match — if one category dominates the keyword match, it's classified as a single-category rule hit.

3. **other → specific category (8 cases):** Conflicting/ambiguous tickets labeled as "other" are sometimes classified by the model into a specific category because the model identifies a primary intent.

## Category confusion matrix (errors only)

| Expected → Predicted | Count |
|---|---:|
| product → technical | 9 |
| other → account_auth | 4 |
| other → technical | 3 |
| account_auth → technical | 2 |
| account_auth → product | 2 |
| billing → account_auth | 1 |
| technical → product | 1 |
| other → product | 1 |
| other → billing | 1 |

## Threshold analysis

The 0.75 threshold sends 23 tickets to human review. Of these:
- 12 are correctly classified (low confidence but right answer) — false positive reviews
- 11 have wrong categories — true positive reviews

The threshold was NOT tuned. These observations are recorded for future calibration when reviewed production labels are available.

## Limitations

1. Labels are synthetic design fixtures, not reviewed production data.
2. "Other" category labeling is subjective for conflicting tickets — the model's "pick the primary intent" behavior may actually be desirable in production.
3. The product/technical boundary is genuinely ambiguous for tickets describing app crashes or timeouts.
4. 105 tickets is sufficient for pattern identification but not for statistical significance of accuracy differences.
5. Single evaluation run — model responses may vary slightly between runs.

## Recommendations (do NOT implement yet)

1. **Rule engine improvement:** Add conflict detection for tickets matching one category by keyword but containing cross-category symptom language.
2. **Prompt refinement:** Clarify the product vs technical boundary in the taxonomy (product = feature/UX, technical = infrastructure/API).
3. **Threshold calibration:** Requires 500+ reviewed production labels before meaningful tuning.
4. **Label review:** Re-evaluate whether conflicting tickets should be labeled "other" or by their primary intent.

These are observations only. No V1 production behavior was changed.
