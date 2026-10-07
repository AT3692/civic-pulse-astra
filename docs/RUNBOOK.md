# CivicPulse operations runbook

## Local Compose

`bash scripts/quickstart.sh` builds, migrates and seeds. `docker compose logs -f backend` shows JSON request logs. `docker compose exec -T backend python -m app.seed` is safe to repeat. `docker compose down` retains named volumes; `down -v` deliberately deletes them and belongs only in disposable CI.

Ollama weights are pulled manually once (`docker compose exec ollama ollama pull llama3.2:1b`). Cold inference can exceed the ten-second cap on a CPU laptop; that should produce a recorded rules fallback, not a broken submission. Give Ollama more resources or use an appropriately small warmed model rather than removing the cap.

Production Compose is standalone, not an override: set `GITHUB_OWNER` lowercase, `IMAGE_TAG` to a tested 40-character SHA, strong URL-safe database/cache credentials and `OPERATOR_API_KEY`; then run `docker compose -f compose.prod.yaml up -d --wait`. Do not combine the dev file with the production file: dev mounts/build directives could remain. Only Nginx publishes a production port. Place it behind TLS termination before external use.

## Local Kubernetes in two stages

Requirements: Docker, Python 3 + PyYAML, kubectl, k3d; Linux amd64 tool setup is available in `scripts/install-kube-tools.sh` (checksums verified). Add `$HOME/.local/bin` to PATH afterward. The cluster uses k3s's bundled Traefik, metrics-server, local-path provisioner and NetworkPolicy controller.

```bash
k3d cluster create civicpulse --image rancher/k3s:v1.33.3-k3s1   --agents 1 --port '8080:80@loadbalancer' --wait
# Use image digests from a successful CD run. No latest, no example digest.
export BACKEND_IMAGE='ghcr.io/at3692/civicpulse-backend@sha256:ACTUAL_DIGEST'
export FRONTEND_IMAGE='ghcr.io/at3692/civicpulse-frontend@sha256:ACTUAL_DIGEST'
export POSTGRES_PASSWORD="$(openssl rand -hex 24)"
export REDIS_PASSWORD="$(openssl rand -hex 24)"
export OPERATOR_API_KEY="$(openssl rand -hex 24)"
SEED_DEMO=1 bash scripts/deploy-k8s.sh
```

The script validates immutable references, creates the namespace/secret if absent, preserves existing secrets, renders images without editing tracked files, replaces the migration Job, applies resources, waits for migration and rollouts, and optionally seeds. It requires a default StorageClass and the Traefik ingress class. On another cluster edit the Ingress class/host and provision storage. Do not directly `kubectl apply -k` placeholder secrets into a real environment.

Private GHCR packages require credentials. Before deployment, run `docker login ghcr.io` using an appropriately scoped token; create `ghcr-pull` from the resulting Docker config and attach it to the namespace service account, as demonstrated in `cd.yml`. Never commit that config. Public packages need no pull secret.

Add `127.0.0.1 civicpulse.local` to your local hosts file and open http://civicpulse.local:8080, or test without host changes:

```bash
BASE_URL=http://localhost:8080 SMOKE_HOST=civicpulse.local python scripts/smoke.py
kubectl get pods,pvc,svc,ingress,hpa,pdb -n civicpulse
```

For an internet-facing cluster configure your actual DNS hostname and Ingress TLS secret/certificate. Restrict backend ingress to authorized proxies; tune trusted proxy CIDRs to those ranges. `/metrics` is internal; port-forward it for Prometheus or configure private scraping. Public `/api` does not expose health/metrics.

## Rollback

Record both image references before every deployment. For fast incident recovery:

```bash
kubectl rollout undo deployment/backend -n civicpulse
kubectl rollout status deployment/backend -n civicpulse
# Undo frontend too if its API contract changed.
kubectl rollout undo deployment/frontend -n civicpulse
```

Then set `BACKEND_IMAGE` and `FRONTEND_IMAGE` to the known-good digest pair and re-run `scripts/deploy-k8s.sh` from the corresponding repository revision. This makes desired state explicit. Do not downgrade the database automatically: review compatibility, back up, and use forward repair when data would be lost. The current initial migration's downgrade deletes the table and is exercised only on an isolated test database.

## Dependency and triage incidents

- `/health` 200 but `/ready` 503: inspect the named dependency, pod events, PVCs, DNS and Secret references. Never turn database readiness into liveness; that would restart healthy web processes during a DB incident.
- Triage fallback increases: inspect `civicpulse_triage_fallback_total`, `/api/meta/providers`, and JSON `triage_fallback` warnings. Check model availability, provider quota, API key configuration, Ollama warm-up and connectivity. Switch to `rules` to avoid repeated remote latency while repairing the provider. Do not print the key or raw prompts.
- 429: honor Retry-After. Confirm trusted proxy CIDRs and forwarded headers before increasing the limit; a misidentified proxy IP can make all citizens share one bucket. Redis failure rejects new submissions with 503 to avoid an unbounded paid/provider workload.
- Stats cache failure: reads recompute from Postgres. Writes return success after a durable DB commit even if invalidation fails; a restored stale Redis cache may remain stale for its remaining 30-second TTL. A Redis outage should not persuade clients to resubmit an already persisted report.
- CrashLoopBackOff: `kubectl logs POD -n civicpulse --previous`, `kubectl describe pod POD -n civicpulse`, and migration Job logs. Production refuses an empty operator key.
- Migration blocked: inspect `kubectl logs job/civicpulse-migrate -n civicpulse`; backend init containers deliberately wait for schema readiness.

Uvicorn runs as PID 1, stops accepting new requests on SIGTERM, drains in-flight work for 25 seconds, then lifespan closes HTTP/Redis connections and DB pools. A five-second preStop drain and 35-second pod grace leave room for endpoint propagation. Force termination can still interrupt requests that exceed the grace window; prove rollout behavior with live load.

## HPA and VPA measurements

K3s includes metrics-server. Check `kubectl top pods -n civicpulse` first. CPU requests are the HPA denominator; limits alone are insufficient. VPA CRDs/controllers must be installed separately:

```bash
git clone --depth 1 --branch vertical-pod-autoscaler-1.3.0 https://github.com/kubernetes/autoscaler.git /tmp/civicpulse-autoscaler
(cd /tmp/civicpulse-autoscaler/vertical-pod-autoscaler && ./hack/vpa-up.sh)
kubectl apply -n civicpulse -f k8s/addons/vpa.yaml
```

Use a disposable local cluster for this exercise. The upstream installer adds cluster-wide components. VPA stays `Off` so only recommendations are produced; HPA owns replica changes.

Run in separate terminals from the repo root:

```bash
kubectl get hpa -n civicpulse -w | tee docs/evidence/hpa-watch.txt
k6 run --out json=/tmp/civicpulse-load.json load/k6-script.js
python scripts/capture-scaling.py /tmp/civicpulse-load.json 360
# Install matplotlib in your development venv for this evidence-only chart.
python scripts/plot-scaling.py
kubectl describe vpa backend-vpa -n civicpulse > docs/evidence/vpa-before.txt
```

Save the initial CPU/memory requests, VPA lower/target/upper bounds, then update requests deliberately and repeat the same load, saving a second CSV/chart. Report observed lag, including no scale-out if CPU never crosses the threshold. Increase realistic offered load if needed; do not fabricate replicas. For zero-downtime evidence, run k6 during an image update and retain its exit status and failed-request count. `k6-script.js` requires zero failed requests.

## Persistence and backups

Compose: submit a report, record its UUID, `docker compose down`, then `up -d --wait`, and retrieve it. Kubernetes: record a report, delete only `postgres-0`, wait for StatefulSet recovery, and retrieve it again. Never delete its PVC for this test. Redis uses AOF; its volume preserves rate-limit windows and cache state across restart, but it is not the source of truth for complaints.

This single-node PostgreSQL deployment has durable storage, not high availability. Implement scheduled `pg_dump` or managed backups, encrypted off-cluster storage, and tested restoration before using real citizen data. Local-path PVCs are tied to a node; deleting the k3d cluster removes the local demonstration environment.

## GitHub repository setup

Enable Actions and package writes. Protect `main`: PR required, one reviewer, require the `required` check from CI, block force pushes/deletion, and require checks on the latest commit. Create `dev` and feature branches. Collaborate through real linked Issues and reviewed PRs; do not manufacture the rubric's commit/review history. GitHub's ephemeral `GITHUB_TOKEN` publishes to GHCR; no personal password belongs in a workflow. Live LLM keys are unnecessary for CI. The default CD target is an ephemeral runner cluster, so no cloud credentials are needed.
