# Verification record — 2026-10-07

These results were obtained in the implementation workspace, not inferred from workflow YAML.

| Check | Result |
|---|---|
| Python unit/API/provider tests | 50 passed |
| Real PostgreSQL/Redis integration tests | Both passed in GitHub Actions; 52 total backend tests passed |
| Coverage of app/ | 85.09% locally; 88.85% with real-service CI tests, above the 65% gate |
| mypy | Success, 26 application modules |
| Ruff lint and format | Passed across backend and Python scripts |
| Frontend component tests | 7 passed |
| Real typed HTTP-client tests | 3 passed, including verbatim 409, field errors, Retry-After |
| ESLint, TypeScript and Prettier | Passed |
| Vite production build | Passed; JS about 162.5 kB / 52.5 kB gzip, CSS about 5.3 kB / 1.8 kB gzip |
| OpenAPI generation | Passed; generated schema and client included |
| Alembic migrations | Offline generation passed locally; live upgrade/downgrade passed in CI |
| Kustomize dev + prod rendering | Passed |
| Strict kubeconform | 36 resources validated across both overlays; 0 invalid, 0 errors, 0 skipped |
| GitHub Actions actionlint 1.7.7 | Passed for all three workflows |
| Shell syntax + submission checker | Passed |
| Container base image references | Official registry manifest digests resolved and pinned for Python, Node, Nginx, Postgres and Redis |
| Both Docker image builds | Passed in GitHub Actions |
| Five-container Compose startup | Passed; all services healthy, 36 seeded reports |
| HTTP smoke through Nginx | Passed: create, retrieve, stats MISS then HIT |
| Network isolation and seed idempotence | Passed: frontend cannot reach Postgres; repeated seed inserts zero rows |
| Trivy image scan | Both passed after correcting the frontend's two fixable HIGH package findings |
| Production Kubernetes overlay on k3d | Passed: migration Job, backend/frontend rollouts and Ingress smoke |
| Kubernetes volume persistence | Passed: the same report was retrieved after deleting and replacing `postgres-0` |

The first remote run is [37650717631](https://github.com/AT3692/civic-pulse-astra/actions/runs/37650717631), at `1c3ed2f52d6fdee99a4e80206fb6454eea2872f1`. It failed correctly at the frontend security gate: libexpat 2.8.4-r0 and pcre2 10.48-r0 had fixed HIGH findings. The Dockerfile now explicitly installs Alpine's fixed 2.8.5-r0 and 10.49-r0 packages while keeping the base digest and failing scan gate. This is real security-gate evidence, not the rubric's separately requested deliberately failing-test PR.

CI now also creates a disposable k3d cluster before merge, imports locally built SHA-tagged images without registry publishing, applies the production overlay, tests the Ingress and checks persistence after replacing the Postgres pod. This exercises the deployment script without requiring a merge to `main`.

All CI jobs, including the corrected runtime-package scans and disposable Kubernetes deployment/persistence checks, passed in [run 37651497142](https://github.com/AT3692/civic-pulse-astra/actions/runs/37651497142), at `7c701dac8abd41abac24d95e6bd29469621058a6`. This documentation-only follow-up records those results; it does not claim a separate completed run for a later commit. Cluster resource/event/migration/backend logs are attached to that run as `pr-cluster-evidence`.

## Checks not yet demonstrated

The local workspace has no Docker daemon or running Kubernetes cluster. The real-service and Compose results above came from GitHub Actions. GHCR publishing/signing, the CD workflow on merged `main`, Compose down/up volume persistence, live-load rollout behavior, HPA scale-out and VPA recommendations remain separate checks. Their success is not inferred from manifests or unit tests.

The installed Playwright package had no browser executable; browser download did not complete. No rendered UI screenshot or browser-level end-to-end result is claimed. Component and HTTP-adapter tests plus the static production build passed.

Local tools were Python 3.12.14 and Node 24.19.0. Containers/CI specify Python 3.12 and Node 22. Tests emit an upstream Starlette warning about eventual migration from httpx TestClient to httpx2; it is not a test failure. Installed package versions are recorded exactly in the lock/manifests.

The implementation is published on `feat/civicpulse-milestones-2-4`, with [draft PR #1](https://github.com/AT3692/civic-pulse-astra/pull/1) targeting `dev`. Git transport lacked write credentials, so the connected GitHub API published logical commits; each resulting file tree was verified against its local counterpart. Commit IDs changed because the API supplied commit metadata. Original local commits were preserved on backup branches. No commit was pushed to `main`. After review, merge the feature into `dev`, then promote `dev` to `main` through a reviewed PR to run CD.

## Remaining submission evidence

See `docs/evidence/README.md`. Actual partner contributions, protected branches, review comments, genuine merge-conflict history, deployment URLs, screenshots, measured scaling data and a spoken demo must come from real activity. Source files and passing local checks do not substitute for those observations.
