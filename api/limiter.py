from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.config import DEFAULT_RATE_LIMIT  # can be set in .env (standard is 35/minute)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_RATE_LIMIT] # also for telemetry, because the Database will not start inserting data again until 15 minutes have passed
)  # define limiter


# rewrite slowapis _rate_limit_exceeded_handler function to safen it
def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            content={"error": "Rate limit exceeded"},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    response = JSONResponse(
        content={"error", f"Rate limit exceeded: {exc.detail}"},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS
    )

    if hasattr(request.state, "view_rate_limit"):  # only call _inject_headers if view_rate_limit was set
        response = request.app.state.limiter._inject_headers(
            response, request.app.state.view_rate_limit
        )

    return response
