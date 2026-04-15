import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

api_logger = logging.getLogger("api")


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        url = request.url
        client = request.client

        # Log stats into logs/api.log
        api_logger.info(f"Request made by: {client} used this method: {method}. Final URL: {url}")

        # start time
        start_time = time.perf_counter()

        response = await call_next(request)  # call next (middleware)
        duration = time.perf_counter() - start_time  # calculate the duration the request took

        response.headers["Process-Time"] = str(duration)  # add the process time to the header

        return response
