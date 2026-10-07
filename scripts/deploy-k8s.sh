#!/usr/bin/env bash
# Needs a current kubectl context, Traefik ingress class, and a default StorageClass.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${BACKEND_IMAGE:?Set immutable backend image reference}"
: "${FRONTEND_IMAGE:?Set immutable frontend image reference}"
python3 - <<'PYVALIDATE'
import os, re
for key in ('BACKEND_IMAGE', 'FRONTEND_IMAGE'):
    if not re.search(r'(@sha256:[0-9a-f]{64}|:[0-9a-f]{40})$', os.environ[key]):
        raise SystemExit(key + ' must use a full commit SHA or image digest')
PYVALIDATE
# Create secrets beforehand for persistent deployments. CI supplies random ephemeral values.
kubectl apply -f k8s/base/namespace.yaml
if ! kubectl get secret civicpulse-secrets -n civicpulse >/dev/null 2>&1; then
  : "${POSTGRES_PASSWORD:?Supply a URL-safe DB password}"
  : "${REDIS_PASSWORD:?Supply a URL-safe Redis password}"
  : "${OPERATOR_API_KEY:?Supply a strong operator key}"
  python3 - <<'PYSECRET' | kubectl apply -f -
import json, os, re
for key in ('POSTGRES_PASSWORD', 'REDIS_PASSWORD'):
    if not re.fullmatch(r'[A-Za-z0-9_-]{20,}', os.environ[key]):
        raise SystemExit(key + ' must be URL-safe and at least 20 characters')
print(json.dumps({'apiVersion':'v1','kind':'Secret','metadata':{'name':'civicpulse-secrets','namespace':'civicpulse'},'type':'Opaque','stringData':{k:os.environ.get(k,'') for k in ('POSTGRES_PASSWORD','REDIS_PASSWORD','GROQ_API_KEY','OPERATOR_API_KEY')}}))
PYSECRET
fi
scratch_dir=$(mktemp -d)
trap 'rm -rf "$scratch_dir"' EXIT
kubectl kustomize "k8s/overlays/${OVERLAY:-prod}" > "$scratch_dir/base.yaml"
python3 scripts/render_deployment.py "$scratch_dir/base.yaml" "$scratch_dir/deploy.yaml"
# One migration job per deployment, never one competing migration per replica.
kubectl delete job civicpulse-migrate -n civicpulse --ignore-not-found --wait=true
kubectl apply -f "$scratch_dir/deploy.yaml"
kubectl wait --for=condition=complete job/civicpulse-migrate -n civicpulse --timeout=300s
kubectl rollout status deployment/backend -n civicpulse --timeout=300s
kubectl rollout status deployment/frontend -n civicpulse --timeout=300s
if [[ "${SEED_DEMO:-0}" == 1 ]]; then kubectl exec -n civicpulse deployment/backend -- python -m app.seed; fi
kubectl get hpa -n civicpulse
