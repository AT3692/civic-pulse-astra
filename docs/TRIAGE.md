# Triage behavior and evaluation

| Setting | Provider | Network | Recorded source |
|---|---|---|---|
| `rules` | deterministic English/Urdu-influenced keywords | none | `rules` |
| `simulated` | deterministic rules plus hash-based failure injection | none | `simulated` |
| `llm` | OpenAI-compatible Groq chat API | external HTTPS | `llm:groq` |
| `ollama` | Ollama `/api/chat` and JSON schema | local service | `llm:ollama` |
| any failing provider | deterministic rules | none | `rules:fallback` |

Every result must have one allowed category, one priority, a nonempty single-line summary ≤140 characters, and confidence in [0,1]. Hosted calls request JSON mode; Ollama receives the actual schema. Output is parsed as JSON and validated again. There is no eval and no generated SQL.

Every attempt is capped at ten wall-clock seconds. A timeout, 429, or 5xx gets one 50–250ms jittered retry. Other HTTP errors, malformed output, and network/protocol errors fall back immediately. Two attempts and retry stay below Nginx's 30-second read timeout, excluding unusually slow persistence. Retry tests inject sleep instead of sleeping.

Redis caches successful classifications for 24 hours under a SHA-256 key containing normalized edge whitespace, text, location, provider, model and schema version. Internal whitespace is retained to avoid altering meaning. The last 20 outcomes are a shared Redis list, so the dashboard remains meaningful after HPA scaling. `/api/meta/providers` reports actual aggregate hits/requests; hit rate is not a hard-coded marketing claim.

To demonstrate fallback, set `TRIAGE_PROVIDER=simulated` and `SIMULATED_FAILURE_RATE=1`, recreate backend, submit a **new text/location pair**, and show 201 with `rules:fallback` and one warning. Cached successes may still be used for old pairs. Reset the failure rate afterward.

Tests prove schema confinement and deterministic handling of an injection attempt, not resistance to every semantic prompt attack. Priority/category quality should be evaluated against human-labeled examples. Never claim a live-provider accuracy or latency number without measuring it. The simulated source is intentionally visible; it is not presented as a real model.

Hosted model catalog and limits: https://console.groq.com/docs/models and https://console.groq.com/docs/rate-limits . Record the date, model, and your account's actual quota in the submission evidence after checking them. Default provider is simulated, so no quota or credit-card claim is needed for the quickstart.
