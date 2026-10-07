#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  python3 - <<'PYENV'
from pathlib import Path
import secrets
text = Path('.env.example').read_text()
text = text.replace('change-me-use-url-safe-chars', secrets.token_hex(24), 1)
text = text.replace('change-me-use-url-safe-chars', secrets.token_hex(24), 1)
text = text.replace('OPERATOR_API_KEY=', 'OPERATOR_API_KEY=' + secrets.token_hex(24), 1)
Path('.env').write_text(text)
Path('.env').chmod(0o600)
PYENV
fi
docker compose up --build -d --wait --wait-timeout 240
docker compose exec -T backend python -m app.seed
printf 'CivicPulse is running at http://localhost:%s (default; see .env).\n' "${FRONTEND_PORT:-8080}"
