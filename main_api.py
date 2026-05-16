from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.dependencies import api_key_auth
from api.limiter import limiter, rate_limit_exceeded_handler
from api.middleware.audit import AuditMiddleware
from api.router import device_router, telemetry_router, analytics_router, ml_router
from core.config import settings
from core.lifespan import lifespan
from core.logging_config import setup_logging

if settings.other.ignore_warnings:
    import warnings

    warnings.filterwarnings("ignore")

setup_logging()

app = FastAPI(
    title="S.E.D.M.S",
    summary="Smart Energy & Device Management System",
    version=settings.version,
    docs_url=settings.api.urls.docs_endpoint,
    redoc_url=settings.api.urls.redoc_endpoint,
    openapi_url=settings.api.urls.openapi_endpoint,
    lifespan=lifespan,
    dependencies=[Depends(api_key_auth)]
)

if settings.api.activate_rate_limits:
    # Add a limiter and an error handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Register the middleware so that the default limits apply
    app.add_middleware(SlowAPIMiddleware)

if settings.api.cors.use_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=settings.api.cors.allow_credentials,
        allow_origins=settings.api.cors.allowed_origins,
        allow_methods=settings.api.cors.allowed_methods,
        allow_headers=settings.api.cors.allowed_headers
    )

# add custom middleware
app.add_middleware(AuditMiddleware)

# include routers
app.include_router(device_router, prefix=settings.api.urls.prefix)
app.include_router(telemetry_router, prefix=settings.api.urls.prefix)
app.include_router(analytics_router, prefix=settings.api.urls.prefix)
app.include_router(ml_router, prefix=settings.api.urls.prefix)


# endpoint to check if the api is online
@app.get(
    path=f"{settings.api.urls.prefix}/online",
    description="Endpoint to check if the API is online",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def get_online_status() -> dict[str, str]:
    return {"status": "online"}
