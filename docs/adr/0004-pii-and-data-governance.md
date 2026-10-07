# ADR 0004 — Complaint data and hosted AI

Status: accepted for the university demonstration.

Reporter contact is stored in PostgreSQL for future authorized follow-up but is excluded from all public API representations and every AI payload. The hosted Groq adapter sends only complaint text, with basic phone/email redaction; it omits the location field. Names or addresses embedded in prose can still escape regex redaction. The form explains this and asks citizens not to include sensitive details. This is data minimization, not a claim of anonymization.

Rules and simulated modes transmit nothing to an external AI service. Ollama sends complaint/location to the local Ollama service only. A municipality that cannot permit residual PII exposure must use rules/Ollama or implement stronger redaction and an approved processor agreement before enabling hosted inference. Provider retention and free-tier limits must be reviewed against current account terms; no free-tier quota is assumed by this code.

Public dashboard text and locations are public by design. Do not use real citizen data in this assignment. Logs contain request IDs, route templates, timing, provider names and error classes, never complaint bodies, contact values, API keys, or raw provider exceptions. Cache keys are content hashes and rate-limit IP keys are hashed, but Redis values can contain summaries: AOF volumes and backups deserve the same protection as application data. Production rollout requires a documented retention period, deletion process, access control, TLS and encrypted backups. Shared operator keys are a demo boundary, not individual accountability.
