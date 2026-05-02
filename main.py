from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.dependencies import api_key_auth
from api.limiter import limiter, rate_limit_exceeded_handler
from api.middleware.audit import AuditMiddleware
from api.router import device_router, telemetry_router, analytics_router, ml_router
from core.config import (
    VERSION,
    DOCS_URL,
    REDOC_URL,
    OPENAPI_URL,
    USE_CORS,
    ALLOW_CREDENTIALS,
    ALLOWED_ORIGINS,
    ALLOWED_METHODS,
    ALLOWED_HEADERS,
    ACTIVATE_RATE_LIMITS,
    IGNORE_WARNINGS
)
from core.lifespan import lifespan
from core.logging_config import setup_logging

if IGNORE_WARNINGS:
    import warnings
    warnings.filterwarnings("ignore")

setup_logging()

app = FastAPI(
    title="S.E.D.M.S",
    summary="Smart Energy & Device Management System",
    version=VERSION,
    docs_url=DOCS_URL,
    redoc_url=REDOC_URL,
    openapi_url=OPENAPI_URL,
    lifespan=lifespan,
    dependencies=[Depends(api_key_auth)]
)

if ACTIVATE_RATE_LIMITS:
    # Add a limiter and an error handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Register the middleware so that the default limits apply
    app.add_middleware(SlowAPIMiddleware)

if USE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=ALLOW_CREDENTIALS,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS
    )

# add custom middleware
app.add_middleware(AuditMiddleware)

# include routers
app.include_router(device_router, prefix="/sedms/api")
app.include_router(telemetry_router, prefix="/sedms/api")
app.include_router(analytics_router, prefix="/sedms/api")
app.include_router(ml_router, prefix="/sedms/api")