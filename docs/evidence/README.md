# Evidence still to collect

This directory must contain actual observations. Code and scripts cannot substitute for the assignment's collaboration, deployment and viva evidence.

- Branch-protection screenshot, red then green required checks on one genuine PR, linked Issues and partner review comments.
- A real merge conflict and a short account of why its resolution was chosen; `git shortlog -sn` from the actual collaboration.
- UI screenshots from the running application, including fallback receipt, dashboard and `X-Cache` HIT stats.
- A successful CD run URL and both SHA-tagged GHCR package URLs; download the workflow's SBOM and cluster-evidence artifacts.
- Compose and StatefulSet persistence checks with a complaint UUID before/after restart; frontend-to-database connection failure.
- `scripts/measure-images.sh` produces builder/runtime byte counts and Docker transfer logs. Compare build contexts before/after `.dockerignore` using temporary clean copies, never by sending a real `.env` to the builder. Record measured bytes, not guessed image sizes.
- HPA watch output, captured CSV and chart using the runbook commands; initial resource requests, actual VPA bounds, revised requests, and repeated measurements.
- A ≤5-minute video with both partners speaking: clean start, AI triage, fallback, isolation failure, real scaling, imperative and declarative rollback.

The accompanying VALIDATION.md records what was executable in the implementation workspace. Leave missing evidence labeled pending rather than adding invented successful results.
