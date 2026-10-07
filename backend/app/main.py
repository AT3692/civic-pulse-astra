import asyncio
import ipaddress
import logging
import re
import time
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.observability import LATENCY, REQUESTS, configure_logging, request_id
from app.providers.cache import RedisCache
from app.providers.triage.factory import make_provider
from app.repositories.complaints import ComplaintRepository
from app.repositories.database import make_engine, make_sessions
from app.routes.api import router
from app.schemas import ErrorBody
from app.services.complaints import ComplaintService
from app.services.errors import ServiceError
from app.services.triage import TriageService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, supplied_service: ComplaintService | None = None) -> FastAPI:
    config = settings or Settings()
    networks = [ipaddress.ip_network(item.strip()) for item in config.trusted_proxy_cidrs.split(",") if item.strip()]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(config.log_level)
        if supplied_service:
            app.state.service = supplied_service
            yield
            return
        if config.app_env == "production" and len(config.operator_api_key.get_secret_value()) < 20:
            raise RuntimeError("OPERATOR_API_KEY must be at least 20 characters in production")
        engine = make_engine(config.database_url)
        cache = RedisCache(config.redis_url)
        async with httpx.AsyncClient() as client:
            provider = make_provider(config, client)
            app.state.service = ComplaintService(
                ComplaintRepository(make_sessions(engine)),
                cache,
                TriageService(
                    provider, cache, config.llm_model if config.triage_provider == "llm" else config.ollama_model
                ),
                config,
            )
            try:
                yield
            finally:
                # Uvicorn drains in-flight requests before executing lifespan shutdown.
                await cache.close()
                await asyncio.to_thread(engine.dispose)

    app = FastAPI(
        title="CivicPulse",
        version="1.0.0",
        lifespan=lifespan,
        responses={code: {"model": ErrorBody} for code in (400, 401, 404, 409, 429, 503)},
    )
    app.include_router(router)

    @app.middleware("http")
    async def telemetry(request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "")
        rid = incoming if re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", incoming) else str(uuid4())
        token = request_id.set(rid)
        start, status = time.perf_counter(), 500
        client_ip = request.client.host if request.client else "unknown"
        try:
            peer = ipaddress.ip_address(client_ip)
            if any(peer in network for network in networks):
                # Walk right to left and stop at the first untrusted hop; don't trust a user-supplied first IP.
                chain = request.headers.get("X-Forwarded-For", "").split(",")
                for part in reversed(chain):
                    candidate = ipaddress.ip_address(part.strip())
                    client_ip = str(candidate)
                    if not any(candidate in network for network in networks):
                        break
        except ValueError:
            pass
        request.state.client_ip = client_ip
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = rid
            response.headers["Cache-Control"] = "no-store"
            return response
        finally:
            route = getattr(request.scope.get("route"), "path", "unmatched")
            elapsed = time.perf_counter() - start
            REQUESTS.labels(request.method, route, str(status)).inc()
            LATENCY.labels(request.method, route).observe(elapsed)
            logger.info("http_request", extra={"status": status, "route": route, "latency_ms": int(elapsed * 1000)})
            request_id.reset(token)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Validation failed",
                "errors": [
                    {"field": ".".join(str(x) for x in error["loc"]), "message": error["msg"], "type": error["type"]}
                    for error in exc.errors()
                ],
            },
        )

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status, content={"detail": exc.detail}, headers=exc.headers)

    async def dependency_error(request: Request, exc: Exception):
        logger.error("dependency_unavailable", extra={"error_class": type(exc).__name__})
        return JSONResponse(
            status_code=503, content={"detail": "A required dependency is unavailable"}, headers={"Retry-After": "5"}
        )

    app.add_exception_handler(SQLAlchemyError, dependency_error)
    app.add_exception_handler(RedisError, dependency_error)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/ready")
    async def ready(request: Request):
        failed = await request.app.state.service.ready()
        return JSONResponse(
            status_code=503 if failed else 200,
            content={"status": "unavailable" if failed else "ready", "failed_dependencies": failed},
        )

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})

    def openapi():
        if app.openapi_schema is None:
            schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
            for path in schema["paths"].values():
                for operation in path.values():
                    if isinstance(operation, dict):
                        operation.get("responses", {}).pop("422", None)
            app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]  # FastAPI documented schema override
    return app


app = create_app()
