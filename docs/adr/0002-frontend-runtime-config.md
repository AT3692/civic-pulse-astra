# ADR 0002 — Same-origin API proxy

Status: accepted.

The typed client derives its base URL from `window.location.origin` at runtime and uses `/api`. Nginx proxies to Docker/Kubernetes service DNS `backend:8000`. Kubernetes Ingress may route `/api` directly to that same backend. The exact frontend build is reusable across environments without rebuilding JavaScript or injecting secrets.

This eliminates CORS configuration for the intended topology. An independent frontend/API origin would need an explicit origin allowlist; it is not silently enabled here. Vite's localhost proxy applies only to host development, never to service-to-service container traffic. Generated OpenAPI types and CI drift checks keep the client contract synchronized.

Nginx replaces forwarded client headers at the public edge. Uvicorn proxy interpretation is disabled; the application walks trusted proxy hops from right to left. Deployment operators must configure `TRUSTED_PROXY_CIDRS` to match their actual proxy ranges and prevent bypass access to the backend.
