from fastapi import APIRouter

telemetry_router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"]
)