from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import DEFAULT_RATE_LIMIT, \
    DEFAULT_TELEMETRY_RATE_LIMIT  # can be set in .env (standard is 35/minute and telemetry is 60/minute)


async def get_default_limit(request: Request) -> str:
    url_path = request.url.path

    if "api/telemetry" in url_path: # if the request is sent to the telemetry endpoint
        return DEFAULT_TELEMETRY_RATE_LIMIT

    return DEFAULT_RATE_LIMIT


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[get_default_limit]
)  # define limiter
