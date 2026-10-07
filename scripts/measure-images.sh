#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p docs/evidence
for component in backend frontend; do
  stage=builder
  [[ "$component" == frontend ]] && stage=build
  docker build --progress=plain --target "$stage" -t "civicpulse-$component:builder" "$component" 2>&1 | tee "docs/evidence/$component-build.log"
  docker build --progress=plain -t "civicpulse-$component:measured" "$component" 2>&1 | tee "docs/evidence/$component-runtime-build.log"
  docker image inspect "civicpulse-$component:builder" "civicpulse-$component:measured" --format '{{.RepoTags}} {{.Size}} bytes' | tee "docs/evidence/$component-sizes.txt"
done
