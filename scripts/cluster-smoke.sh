#!/usr/bin/env bash
# Disposable cluster only: verifies the Ingress and durable PostgreSQL PVC.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${BASE_URL:=http://localhost:8080}"
: "${SMOKE_HOST:=civicpulse.local}"
export BASE_URL SMOKE_HOST
kubectl rollout status deployment/traefik -n kube-system --timeout=180s
for attempt in $(seq 1 60); do
  if curl -fsS -H "Host: $SMOKE_HOST" "$BASE_URL/api/complaints" > /dev/null; then break; fi
  sleep 2
done
python3 scripts/smoke.py
# Capture an existing record before destroying only the database pod.
report_id=$(curl -fsS -H "Host: $SMOKE_HOST" "$BASE_URL/api/complaints?page_size=1" |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["items"][0]["id"])')
kubectl delete pod postgres-0 -n civicpulse --wait=true
kubectl rollout status statefulset/postgres -n civicpulse --timeout=180s
# Existing API connections may need to reconnect after PostgreSQL restarts.
for attempt in $(seq 1 60); do
  if curl -fsS -H "Host: $SMOKE_HOST" "$BASE_URL/api/complaints/$report_id" |
    python3 -c 'import json,sys; assert json.load(sys.stdin)["id"] == sys.argv[1]' "$report_id"; then
    printf 'PASS: report %s survived Postgres pod replacement\n' "$report_id"
    kubectl get hpa -n civicpulse
    exit 0
  fi
  sleep 2
done
printf 'FAIL: report was not retrievable after Postgres pod replacement\n' >&2
exit 1
