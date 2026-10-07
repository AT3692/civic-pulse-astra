# Verification record — 2026-10-07

These results were obtained in the implementation workspace, not inferred from workflow YAML.

| Check | Result |
|---|---|
| Python unit/API/provider tests | 50 passed |
| Real PostgreSQL/Redis integration tests | 2 skipped locally; CI supplies their required isolated services |
| Coverage of app/ | 85.09%, above the 65% gate; seed CLI excluded, schema-wait CLI included |
| mypy | Success, 26 application modules |
| Ruff lint and format | Passed across backend and Python scripts |
| Frontend component tests | 7 passed |
| Real typed HTTP-client tests | 3 passed, including verbatim 409, field errors, Retry-After |
| ESLint, TypeScript and Prettier | Passed |
| Vite production build | Passed; JS about 162.5 kB / 52.5 kB gzip, CSS about 5.3 kB / 1.8 kB gzip |
| OpenAPI generation | Passed; generated schema and client included |
| Alembic PostgreSQL offline DDL generation | Passed; live migration upgrade/downgrade awaits integration services |
| Kustomize dev + prod rendering | Passed |
| Strict kubeconform | 36 resources validated across both overlays; 0 invalid, 0 errors, 0 skipped |
| GitHub Actions actionlint 1.7.7 | Passed for all three workflows |
| Shell syntax + submission checker | Passed |
| Container base image references | Official registry manifest digests resolved and pinned for Python, Node, Nginx, Postgres and Redis |

## Checks not yet demonstrated

The workspace has no Docker daemon or running Kubernetes cluster. System PostgreSQL/Redis installation was unavailable, so the two real-service tests were explicitly skipped. Consequently Docker builds, Compose smoke/persistence/isolation, Trivy image scanning, GHCR publishing/signing, the ephemeral k3d deployment, actual ingress traffic, load/rollout behavior, HPA scale-out and VPA recommendations have **not** been claimed as passing. They are wired into CI or the runbook for an environment that can execute them.

The installed Playwright package had no browser executable; browser download did not complete. No rendered UI screenshot or browser-level end-to-end result is claimed. Component and HTTP-adapter tests plus the static production build passed.

Local tools were Python 3.12.14 and Node 24.19.0. Containers/CI specify Python 3.12 and Node 22. Tests emit an upstream Starlette warning about eventual migration from httpx TestClient to httpx2; it is not a test failure. Installed package versions are recorded exactly in the lock/manifests.

GitHub installation was confirmed during the task, but its authenticated tools were not yet exposed to this running session. A pre-connection Git push dry-run lacked authentication. No remote branch, PR, or successful Actions run is asserted by this record; publish the prepared branch after tool access refreshes.

## Remaining submission evidence

See `docs/evidence/README.md`. Actual partner contributions, protected branches, review comments, genuine merge-conflict history, deployment URLs, screenshots, measured scaling data and a spoken demo must come from real activity. Source files and passing local checks do not substitute for those observations.
