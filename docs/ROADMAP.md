# Roadmap

Only pursue these after the MVP acceptance criteria remain verified.

1. **Calibration and feedback:** collect reviewer labels, calibrate confidence, tune threshold per category, and measure drift.
2. **Operational integration:** queue-backed API, authentication/authorization, Zendesk/Jira/Slack connectors, idempotency, and SLA-aware routing.
3. **Knowledge:** approved knowledge-base retrieval with citations and strict data access boundaries.
4. **Reliability:** multi-model fallback, circuit breakers, provider health, encrypted/expiring cache, and duplicate detection.
5. **Observability:** OpenTelemetry export, dashboards, alerting, token/cost accounting, and privacy-preserving traces.
6. **Learning loop:** reviewer corrections, versioned datasets, regression gates, and evaluation dashboards.
7. **Security:** PII detection/redaction, retention policy, encryption, tenant isolation, threat modeling, and compliance assessment.

Not included in the MVP: automatic ticket resolution, autonomous escalation actions, memory, RAG, MCP tools, or external write integrations.
