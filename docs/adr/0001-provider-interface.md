# ADR 0001 — Replaceable triage providers

Status: accepted.

Services depend on the asynchronous `TriageProvider` protocol and Pydantic `TriageResult`, not on SDK responses. Four implementations cover hosted Groq, local Ollama, deterministic rules, and simulated failures. An async interface matches FastAPI and avoids blocking its event loop while waiting for remote inference. PostgreSQL work runs in threads with per-operation sessions.

The orchestration service owns the ten-second wall-clock cap, exactly one jittered retry for timeout/429/5xx, schema validation, content cache, latency recording and fallback. Concrete HTTP providers own request/response wire formats. Input is untrusted JSON data under a fixed system instruction; enum validation restricts output but cannot prove semantic correctness. CI uses simulated providers and mock HTTP transports; real AI quality needs a labeled evaluation set.

Fallbacks are deliberately not cached for 24 hours: a transient outage should not suppress recovery. Provider/model identity is included in cache keys to avoid serving an old model's classification after configuration changes. Simultaneous first-time identical requests can still cause more than one inference; distributed single-flight is a future cost optimization, not a data-integrity dependency.
