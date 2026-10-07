# Engineering notes

These answers distinguish implementation facts from experiments still requiring a running cluster. Line references refer to this revision.

## 1. Laptop versus CI

- Interpreter/toolchain versions differ. The backend's Python 3.12 base and digest are fixed at `backend/Dockerfile:4`; the frontend Node 22 builder digest is fixed at `frontend/Dockerfile:4`. CI's setup steps use those major versions. Local verification used Python 3.12 and Node 24, so the Node 22 container/CI run remains an important cross-environment gate.
- Dependency resolution would drift between installations. Exact runtime pins begin at `backend/requirements.txt:2`; the frontend uses its committed lock through `npm ci` at `frontend/Dockerfile:9`. Do not regenerate lockfiles as a side effect of deployment.
- Networks/origins differ. Nginx uses service DNS at `frontend/nginx.conf:55`; the browser derives its origin at `frontend/src/api/client.ts:3`. A localhost container URL would refer to that container itself, not the backend service. The Vite proxy is explicitly a host-development convenience.

## 2. CI/CD maturity

The implemented pipeline is automated CI plus gated image delivery and repeatable deployment to an ephemeral validation cluster: lint/type/test → build/scan → publish/sign → deploy/smoke. The deploy gate is `.github/workflows/cd.yml:81`. This is not a claim of operating a permanent production environment. The next operational step is promotion of the same digest into a persistent staging/production environment with approval policy, monitoring and rollback SLOs; GitOps reconciliation can then make drift visible. The course's precise ladder labels were not supplied, so map this behavior to the lecture terminology instead of inventing a slide quotation.

## 3. Build once, deploy many

The client derives its API origin at `frontend/src/api/client.ts:3`; Nginx routes `/api` to service DNS at `frontend/nginx.conf:55`. No Vite API environment variable is baked in. CD hands digest outputs to deployment at `.github/workflows/cd.yml:72`. Without that origin indirection, each host change requires a frontend rebuild and the tested artifact differs from the deployed one.

## 4. Correctness of a probabilistic provider

Correct has two meanings: protocol correctness (valid enums, one-line summary, confidence bounds, deadline, graceful failure) and semantic classification quality. `TriageResult` enforces the first at `backend/app/schemas.py:37`; labeled human evaluation is needed for the second. Simulated CI is selected at `.github/workflows/ci.yml:46`. Retry/fallback orchestration starts at `backend/app/services/triage.py:47`; deterministic tests inject provider failures and malformed HTTP output, never a live model or a lucky rerun. Schema-valid output can still classify a complaint wrongly.

## 5. HPA lag

**Pending measurement.** No Docker daemon or cluster was available in the implementation workspace, so no scale-out interval is claimed. CPU target and policies are at `k8s/base/hpa.yaml:18`. Run the runbook's k6, HPA watch, CSV capture and plot commands; measure from the first sustained rise in offered VUs to the first rise in current replicas. Expected contributors are metrics sampling, HPA reconciliation, scheduling, image pull and startup/readiness. Warm images, realistic requests, a higher minimum, and sufficient node capacity can reduce lag. A workload that does not exceed CPU targets may not scale; that is a valid observation.

## 6. Why VPA is Off

The explicit recommendation mode is `k8s/addons/vpa.yaml:11`. HPA computes usage/request. VPA Auto raises a request, reducing apparent utilization, so HPA may scale in; load per remaining pod then rises. Both controllers changing the same CPU signal can oscillate. Record lower/target/upper bounds, adjust requests manually, then repeat the identical load. Initial backend requests are `k8s/base/backend.yaml:48`; actual recommendations are pending, not invented.

## 7. Internal network and hosted AI

Isolation is declared at `compose.yaml:8`. Only backend bridges `edge` and `internal` at `compose.yaml:61`, allowing hosted HTTPS while keeping Postgres/Redis off the public network. Frontend remains edge-only. Ollama joins edge for model downloads and exposes no host port. Kubernetes adds pod-selective data NetworkPolicies; those require an enforcing CNI, which the prescribed k3s setup provides.

## 8. Failure and investigation

Actual implementation defects included `list` method names shadowing Python's builtin `list` in later annotations, consumed HTTP response bodies hiding server conflict messages, and an environment proxy affecting a supposedly network-free provider factory test. They were corrected by explicit method names, using openapi-fetch's parsed error object, and constructing a no-network test client with environment proxy discovery disabled. The frontend transport tests now exercise the real adapter. A kube-tool checksum check also initially expected an unprefixed filename; upstream publishes `_dist/k3d-linux-amd64`, now handled at `scripts/install-kube-tools.sh:12`. No >1-hour debugging story is claimed: the students should record their own real extended failure and the decisive command/log before submission.

## Data, caches and resource choices

- `(status, priority)` at `backend/app/repositories/models.py:17` supports the operator queue filtered by state and urgency. `created_at` at `backend/app/repositories/models.py:18` supports newest-first pagination. Very large datasets may need keyset pagination and a composite ordering index; inspect EXPLAIN before changing them.
- Stats TTL is 30 seconds; generation-key invalidation on writes prevents a concurrent old fill from becoming current (`backend/app/services/complaints.py:96`). TTL bounds old-generation storage and stale exposure after a failed invalidation. Invalidation gives immediate freshness on a healthy Redis path; either alone is weaker.
- Redis AOF retains rate-limit windows across restarts and avoids a cold triage cache. Postgres is still the authoritative complaint store. Redis AOF persistence adds I/O and can lose approximately the last second under the default everysec fsync policy; do not equate it to durable complaint persistence.
- Model weights use their own volume to avoid repeat downloads. The frontend runtime receives only compiled files, not Node or source (`frontend/Dockerfile:26`). Builder/runtime image sizes and before/after Docker context sizes must be measured with the supplied script; no byte counts are invented here.
- PostgreSQL has one durable StatefulSet replica, not database high availability. Shared operator authentication is suitable for the course's small demo; individual roles/audit, TLS, backups and retention remain prerequisites for real citizen use.

## Primary implementation references

- [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [Kubernetes startup, liveness and readiness probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/)
- [Kubernetes container lifecycle hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/)

These document the mechanics. Live provider quota, measured inference performance and scaling behavior must come from the actual chosen account and runtime.
