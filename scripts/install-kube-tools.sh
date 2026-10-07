#!/usr/bin/env bash
# Linux amd64 CI tools. Verify published checksums before execution.
set -euo pipefail
tools_dir=$(mktemp -d)
trap 'rm -rf "$tools_dir"' EXIT
cd "$tools_dir"
curl -fsSLO https://dl.k8s.io/release/v1.33.3/bin/linux/amd64/kubectl
curl -fsSLO https://dl.k8s.io/release/v1.33.3/bin/linux/amd64/kubectl.sha256
printf '%s  kubectl\n' "$(cat kubectl.sha256)" | sha256sum --check
curl -fsSLO https://github.com/k3d-io/k3d/releases/download/v5.8.3/k3d-linux-amd64
curl -fsSLO https://github.com/k3d-io/k3d/releases/download/v5.8.3/checksums.txt
grep ' _dist/k3d-linux-amd64$' checksums.txt | sed 's|_dist/||' | sha256sum --check
curl -fsSLO https://github.com/yannh/kubeconform/releases/download/v0.7.0/kubeconform-linux-amd64.tar.gz
curl -fsSLo kubeconform-checksums.txt https://github.com/yannh/kubeconform/releases/download/v0.7.0/CHECKSUMS
grep ' kubeconform-linux-amd64.tar.gz$' kubeconform-checksums.txt | sha256sum --check
tar -xzf kubeconform-linux-amd64.tar.gz kubeconform
mkdir -p "$HOME/.local/bin"
install -m 755 kubectl "$HOME/.local/bin/kubectl"
install -m 755 k3d-linux-amd64 "$HOME/.local/bin/k3d"
install -m 755 kubeconform "$HOME/.local/bin/kubeconform"
if [[ -n "${GITHUB_PATH:-}" ]]; then echo "$HOME/.local/bin" >> "$GITHUB_PATH"; fi
