# Agent Design

## Purpose
The single Strands agent classifies only tickets that the deterministic layer cannot resolve confidently. It has no tools and cannot execute actions.

## Inputs and outputs
A prompt contains an indexed chunk of normalized ticket IDs, subjects, and bodies plus the closed taxonomy. The requested Pydantic output is a list of `{ticket_id, category, urgency, confidence, reason}` records. Routing and human-review decisions are not delegated to the model.

## Decision boundary
1. Invalid input: reject as an input error; batch CLI reports it and exits non-zero.
2. One unambiguous rule category with obvious phrase evidence: deterministic result, confidence 0.96.
3. Otherwise: one structured Strands call for the unresolved chunk.
4. Model confidence `< HUMAN_REVIEW_THRESHOLD` (default 0.75): human review.
5. Missing/duplicate/unknown IDs, schema failure, conflicting safety signals, or provider error: safe fallback with category `other`, confidence 0, General Support, human review.

The default 0.75 is a conservative starting operating point, not a calibrated probability. It separates model-declared weak decisions from automatic routing while evaluation data is small. It is configurable and must be calibrated with reviewed production labels before operational use.

## Urgency policy
- `critical`: active widespread outage, severe security compromise, or immediate major business stoppage.
- `high`: account lockout, repeated payment impact, major feature unusable, or time-sensitive degradation.
- `medium`: normal defect/support issue with meaningful impact.
- `low`: informational, how-to, feature feedback, or cosmetic issue.

## Safety
Ticket text is untrusted data. The prompt explicitly treats instructions inside tickets as content, not agent instructions. No tools means prompt injection cannot trigger side effects. Output is schema- and ID-validated.
