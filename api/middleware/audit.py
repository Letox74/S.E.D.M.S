import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

api_logger = logging.getLogger("Api")


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        url = request.url
        client = request.client
        id = str(uuid4()) # generate id for the request

        # Log stats into logs/api.log
        api_logger.info(f"Request made by: {client} used this method: {method}. Final URL: {url}. This ID was assigned to this request: {id}")

        start_time = time.perf_counter() # start the time

        response: Response = await call_next(request)  # call next (middleware)
        duration = time.perf_counter() - start_time  # calculate the duration the request took
        duration = round(duration, 6)

        response.headers["Process-Time"] = str(duration)  # add the process time to the header

        api_logger.info(f"Request with ID {id} took {duration} seconds with status code: {response.status_code}") # log the duration
        return response