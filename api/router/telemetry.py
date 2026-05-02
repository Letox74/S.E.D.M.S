from datetime import datetime
from typing import Optional, Literal, Never
from uuid import UUID, uuid4

from fastapi import APIRouter, status, Depends, Query, Path, Body, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import (
    get_db_session,
    validate_device_exists,
    validate_device_has_telemetry,
    validate_daterange,
    validate_device_has_battery
)
from database.connection import DatabaseManager
from internal.schemas.telemetry_models import (
    TelemetryCreate,
    TelemetryRead
)
from internal.service import telemetry_service
from .utils import to_csv

telemetry_router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"]
)


@telemetry_router.post(
    path="/",
    description="Ingests a new Telemetry and starts calculation the analytics",
    status_code=status.HTTP_202_ACCEPTED
)
async def ingest_telemetry(
        bg_task: BackgroundTasks,
        data: TelemetryCreate = Body(..., embed=True, description="The data needed to create the Telemetry"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str] | TelemetryRead:
    if not await validate_device_has_battery(data.device_id, db) and data.current_battery_percentage != -1:
        data.current_battery_percentage = -1

    result = await telemetry_service.db_ingest_telemetry(data, db)

    if isinstance(result, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    bg_task.add_task(telemetry_service.process_analytic_calculations, str(uuid4()), data.device_id, db)
    return result


@telemetry_router.get(
    path="/device/{device_id}/latest",
    description="Get the lastes Telemetry data from a Device",
    response_model=TelemetryRead,
    status_code=status.HTTP_200_OK
)
async def get_latest_telemetry(
        device_id: Optional[UUID] = Path(default=..., description="The Device ID"),
        db: DatabaseManager = Depends(get_db_session)
) -> TelemetryRead | None:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)

    return await telemetry_service.db_get_latest_telemetry(device_id, db)


@telemetry_router.get(
    path="/device/{device_id}/history",
    description="Gets the Telemetry History of the Device with optional arguments like dates and limits",
    response_model=list[TelemetryRead],
    status_code=status.HTTP_200_OK
)
async def get_telemetry_history(
        device_id: Optional[UUID] = Path(default=None, description="The Device ID"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=20, ge=0, description="A optional limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[TelemetryRead]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(str(device_id), db)
        await validate_device_has_telemetry(str(device_id), db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await telemetry_service.db_get_telemetry_history(str(device_id), daterange, limit, db)


@telemetry_router.get(
    path="/device/{device_id}/range",
    description="Get the Telemetry data in a daterange",
    response_model=list[TelemetryRead],
    status_code=status.HTTP_200_OK
)
async def get_telemetry_range(
        device_id: Optional[UUID] = Path(default=None, description="The Device ID"),
        start_datetime: datetime = Query(default=..., description="The start datetime"),
        end_datetime: datetime = Query(default=..., description="The end datetime"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[TelemetryRead]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await telemetry_service.db_get_telemetry_range(device_id, daterange, db)


@telemetry_router.delete(
    path="/device/{device_id}/clear",
    description="Clears the Telemetry data",
    status_code=status.HTTP_200_OK
)
async def clear_telemetry(
        device_id: Optional[UUID] = Path(default=None, description="The Device ID"),
        before: Optional[datetime] = Query(default=None, description="Only clear before this datetime"),
        limit: Optional[int] = Query(default=50, ge=0, description="A optional limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | int]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)
    deleted_rows = await telemetry_service.db_delete_telemetry(device_id, before, limit, db)

    return {"deleted_rows": deleted_rows}


@telemetry_router.get(
    path="/device/{device_id}/count",
    description="Cont how many entries there are from this Device",
    status_code=status.HTTP_200_OK
)
async def get_telemetry_count(
        device_id: Optional[UUID] = Path(default=None, description="The Device ID"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | int]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_telemetry(device_id, db)
    count = await telemetry_service.db_telemetry_count(device_id, db)

    return {"count": count}


@telemetry_router.get(
    path="/stats/device/{device_id}",
    description="Get stats for this Device",
    status_code=status.HTTP_200_OK
)
async def get_device_telemetry_stats(
        device_id: UUID = Path(default=..., description="The Device ID"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, int | str | dict[str, float | str]]:
    await validate_device_exists(str(device_id), db)
    await validate_device_has_telemetry(str(device_id), db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await telemetry_service.db_get_telmetry_stats(str(device_id), daterange, db)


@telemetry_router.get(
    path="/stats/global",
    description="Get stats from every Device",
    status_code=status.HTTP_200_OK
)
async def get_global_telemetry_stats(
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, int | str | dict[str, float | str]] | dict[str, str]:
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await telemetry_service.db_get_telmetry_stats(None, daterange, db)


@telemetry_router.get(
    path="/alerts/battery",
    description="Get every Telemetry where the battery is below a threshold (default 20) in the last hour if not datetime was set",
    response_model=list[TelemetryRead],
    status_code=status.HTTP_200_OK
)
async def get_battery_alerts(
        threshold: float = Query(default=20, description="The threshold", ge=0, le=100),
        after: Optional[datetime] = Query(default=None, description="In after what timeslot it should get checked"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[TelemetryRead]:
    return await telemetry_service.db_alerts_battery(threshold, after, db)


@telemetry_router.get(
    path="/alerts/temperature",
    description="Get every Telemetry where the temperature is above the set threshold",
    response_model=list[TelemetryRead],
    status_code=status.HTTP_200_OK
)
async def get_temperature_alerts(
        threshold: float = Query(default=50, description="The threshold", ge=-20, le=100),
        after: Optional[datetime] = Query(default=None, description="In after what timeslot it should get checked"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[TelemetryRead]:
    return await telemetry_service.db_alerts_temperature(threshold, after, db)


@telemetry_router.get(
    path="/export/device/{device_id}",
    description="Export data from the Device",
    response_model=None,
    status_code=status.HTTP_200_OK
)
async def export_device_telemetry(
        file_format: Literal["json", "csv"] = Query(default="json", description="The format of the returned data"),
        device_id: UUID = Path(default=..., description="The Device ID"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=None, ge=0, description="A limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[TelemetryRead] | list[Never] | StreamingResponse:
    await validate_device_exists(str(device_id), db)
    await validate_device_has_telemetry(str(device_id), db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    data = await telemetry_service.db_get_telemetry_history(str(device_id), daterange, limit, db)

    if not data:
        return []

    if file_format == "csv":
        return to_csv(data)

    return data


@telemetry_router.get(
    path="/export/all",
    description="Export all telemetry data",
    response_model=None,
    status_code=status.HTTP_200_OK
)
async def export_all_telemetry(
        file_format: Literal["json", "csv"] = Query(default="json", description="The format of the returned data"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=None, ge=0, description="A limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[TelemetryRead] | list[Never] | StreamingResponse:
    daterange = await validate_daterange(start_datetime, end_datetime)
    data = await telemetry_service.db_get_telemetry_history(None, daterange, limit, db)

    if not data:
        return []

    if file_format == "csv":
        return to_csv(data)

    return data
