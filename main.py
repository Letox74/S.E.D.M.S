from fastapi import FastAPI, Depends
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.dependencies import api_key_auth
from api.limiter import limiter, rate_limit_exceeded_handler
from api.middleware.audit import AuditMiddleware
from api.router import device_router
from core.config import (
    VERSION,
    DOCS_URL,
    REDOC_URL,
    OPENAPI_URL,
    ACTIVATE_RATE_LIMITS
)
from core.lifespan import lifespan
from core.logging_config import setup_logging

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

# add custom middleware
app.add_middleware(AuditMiddleware)

# include routers
app.include_router(device_router, prefix="/sedms/api")
