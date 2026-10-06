# syntax=docker/dockerfile:1

# ---------- Stage 1: builder ----------
FROM python:3.12-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Isolated venv so the runtime stage can copy it wholesale
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Requirements before source: this layer is cached until dependencies change
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Fixed UID/GID so Kubernetes securityContext (runAsUser: 10001) matches
RUN groupadd --system --gid 10001 appuser \
 && useradd  --system --uid 10001 --gid appuser \
             --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Liveness only: /health must not touch the database.
# slim has no curl/wget, so use the stdlib.
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

# Exec form: uvicorn is PID 1 and receives SIGTERM directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "25"]
