from fastapi import FastAPI, Depends
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from api.dependencies import api_key_auth
from api.limiter import limiter
from api.middleware.audit import AuditMiddleware
from api.router import device_router
from core.config import ACTIVATE_RATE_LIMITS
from core.lifespan import lifespan
from core.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="S.E.D.M.S",
    summary="Smart Energy & Device Management System",
    version="0.1.0",
    docs_url="/sedms/api/docs",
    redoc_url="/sedms/api/redoc",
    openapi_url="/sedms/api/openapi.json",
    lifespan=lifespan,
    dependencies=[Depends(api_key_auth)]
)

if ACTIVATE_RATE_LIMITS:
    # Add a limiter and an error handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Register the middleware so that the default limits apply
    app.add_middleware(SlowAPIMiddleware)

app.add_middleware(AuditMiddleware)  # add custom middleware

# include routers
app.include_router(device_router, prefix="/sedms/api")
