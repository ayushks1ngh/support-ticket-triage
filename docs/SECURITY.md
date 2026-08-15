# Security

## Implemented MVP controls
- Secrets are read from environment variables; `.env` and common secret files are Git-ignored.
- `.env.example` contains placeholders only.
- Ticket ID, subject, body, file size, batch size, concurrency, retries, and output fields are bounded and validated.
- Logs/metrics exclude ticket text and API keys.
- Model output is untrusted and Pydantic/semantic validated.
- Provider/validation errors become sanitized human-review fallbacks.
- Ticket prompt injection has no tool/action surface; ticket fields are explicitly untrusted prompt data.
- External transmission occurs only for unresolved tickets in online mode.

## Threats and limitations
Support text can contain personal, confidential, or regulated information. Hosted-provider use transfers unresolved content to that provider under its terms. The MVP does not implement PII redaction, encryption-at-rest, authentication, tenant isolation, retention controls, malware scanning, or compliance certification. Use synthetic data for demos and obtain organizational approval before real ticket processing.

## Secret incident
An API key was pasted into the development conversation. It must be revoked/rotated by its owner. It is not stored or used by this repository.

## Reporting
Do not include secrets in issues. Rotate an exposed credential first, then report the location and impact through the repository owner's private channel.
