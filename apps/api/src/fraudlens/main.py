from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from fraudlens.api import router
from fraudlens.config import get_settings
from fraudlens.database import create_schema, seed_demo_data
from fraudlens.dependencies import get_publisher


@asynccontextmanager
async def lifespan(_: FastAPI):
    publisher = get_publisher()
    if settings.environment == "development":
        await create_schema()
        await seed_demo_data()
    await publisher.start()
    yield
    await publisher.stop()


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Auditable multimodal fraud investigation control plane",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)


@app.middleware("http")
async def operational_headers(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started = perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Server-Timing"] = f"app;dur={(perf_counter() - started) * 1000:.2f}"
    return response


app.include_router(router, prefix=settings.api_prefix)
