from datetime import datetime, date
from typing import Optional, Literal, Never
from uuid import UUID

from fastapi import APIRouter, status, Depends, Query, Path
from fastapi.responses import StreamingResponse

from api.dependencies import (
    get_db_session,
    validate_device_exists,
    validate_device_has_analytics,
    validate_daterange
)
from api.router.utils import to_csv
from database.connection import DatabaseManager
from internal.schemas.analytic_models import AnalyticsRead
from internal.service import analytics_service

analytics_router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@analytics_router.get(
    path="/latest",
    description="Get the lastes Analytics data from a Device",
    response_model=AnalyticsRead,
    status_code=status.HTTP_200_OK
)
async def get_latest_analytic(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        db: DatabaseManager = Depends(get_db_session)
) -> AnalyticsRead | None:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_analytics(device_id, db)

    return await analytics_service.db_get_latest_analytic(device_id, db)


@analytics_router.get(
    path="/history",
    description="Gets the Analytics History of the Device with optional arguments like dates and limits",
    response_model=list[AnalyticsRead],
    status_code=status.HTTP_200_OK
)
async def get_analytics_history(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=None, description="A optional limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_analytics(device_id, db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await analytics_service.db_get_analytics_history(device_id, daterange, limit, db)


@analytics_router.get(
    path="/range",
    description="Get the Analytics data in a daterange",
    response_model=list[AnalyticsRead],
    status_code=status.HTTP_200_OK
)
async def get_analytics_range(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        start_datetime: datetime = Query(default=..., description="The start datetime"),
        end_datetime: datetime = Query(default=..., description="The end datetime"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_analytics(device_id, db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    return await analytics_service.db_get_analytics_range(device_id, daterange, db)


@analytics_router.delete(
    path="/clear",
    description="Clears the Analytics data",
    status_code=status.HTTP_200_OK
)
async def clear_analytics(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        before: Optional[datetime] = Query(default=None, description="Only clear before this datetime"),
        limit: Optional[int] = Query(default=None, description="A optional limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | int]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(device_id, db)
        await validate_device_has_analytics(device_id, db)
    deleted_rows = await analytics_service.db_delete_analytics(device_id, before, limit, db)

    return {"deleted_rows": deleted_rows}


@analytics_router.get(
    path="/count",
    description="Cont how many entries there are from this Device",
    status_code=status.HTTP_200_OK
)
async def get_analytics_count(
        device_id: Optional[UUID] = Query(default=None, description="The Device ID"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | int]:
    device_id = str(device_id) if device_id else None

    if device_id:
        await validate_device_exists(str(device_id), db)
        await validate_device_has_analytics(str(device_id), db)
    count = await analytics_service.db_analytics_count(str(device_id), db)

    return {"count": count}


@analytics_router.get(
    path="/summary/daily/device/{device_id}",
    description="Get a daily summary of a Device",
    status_code=status.HTTP_200_OK
)
async def get_daily_summary(
        device_id: UUID = Path(default=..., description="The Device ID"),
        summary_date: Optional[date] = Query(default=None, description="The date"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | float | int] | None:
    await validate_device_exists(str(device_id), db)
    await validate_device_has_analytics(str(device_id), db)

    return await analytics_service.db_get_daily_summary(str(device_id), summary_date, db)


@analytics_router.get(
    path="/summary/daily",
    description="Get a daily summary",
    status_code=status.HTTP_200_OK
)
async def get_daily_summary(
        summary_date: Optional[date] = Query(default=None, description="The date"),
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, str | float | int] | None:
    return await analytics_service.db_get_daily_summary(None, summary_date, db)


@analytics_router.get(
    path="/alerts/efficiency",
    response_model=list[AnalyticsRead],
    description="Get every row where the efficiency score is below a threshold",
    status_code=status.HTTP_200_OK
)
async def get_efficiency_alerts(
        threshold: float = Query(default=50, ge=0, le=100, description="The threshold"),
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_alerts_efficiency(threshold, after, db)


@analytics_router.get(
    path="/alerts/operation-hours",
    response_model=list[AnalyticsRead],
    description="Get every row where the operation hours is above a threshold",
    status_code=status.HTTP_200_OK
)
async def get_operation_hour_alerts(
        threshold: float = Query(default=100, ge=0, description="The threshold"),
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_alerts_operation_hours(threshold, after, db)


@analytics_router.get(
    path="/alerts/stability/power",
    response_model=list[AnalyticsRead],
    description="Get every row where the std power is above a threshold",
    status_code=status.HTTP_200_OK
)
async def get_std_power_alerts(
        threshold: float = Query(default=100, ge=0, description="The threshold"),
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_alerts_std_power(threshold, after, db)


@analytics_router.get(
    path="/alerts/stability/voltage",
    response_model=list[AnalyticsRead],
    description="Get every row where the std voltage is above a threshold",
    status_code=status.HTTP_200_OK
)
async def get_std_voltage_alerts(
        threshold: float = Query(default=100, ge=0, description="The threshold"),
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_alerts_std_voltage(threshold, after, db)


@analytics_router.get(
    path="/alerts/stability/current",
    response_model=list[AnalyticsRead],
    description="Get every row where the std current is above a threshold",
    status_code=status.HTTP_200_OK
)
async def get_std_current_alerts(
        threshold: float = Query(default=100, ge=0, description="The threshold"),
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_alerts_std_current(threshold, after, db)


@analytics_router.get(
    path="/alerts/stability/signal-strength",
    response_model=list[AnalyticsRead],
    description="Get every row where the std signal strength is above a threshold",
    status_code=status.HTTP_200_OK
)
async def get_std_power_alerts(
        threshold: float = Query(default=100, ge=0, description="The threshold"),
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_alerts_std_signal_strength(threshold, after, db)


@analytics_router.get(
    path="/alerts/stability/temperature",
    response_model=list[AnalyticsRead],
    description="Get every row where the std temperature is above a threshold",
    status_code=status.HTTP_200_OK
)
async def get_std_power_alerts(
        threshold: float = Query(default=100, ge=0, description="The threshold"),
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_alerts_std_temperature(threshold, after, db)


@analytics_router.get(
    path="/ranking/efficiency",
    response_model=list[AnalyticsRead],
    description="Get a ranking decreasing from the efficiency score",
    status_code=status.HTTP_200_OK
)
async def get_efficiency_ranking(
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        limit: Optional[int] = Query(default=10, ge=0, description="The limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_ranking_efficiency(after, limit, db)


@analytics_router.get(
    path="/ranking/energy-consumption",
    response_model=list[AnalyticsRead],
    description="Get a ranking decreasing from the energy consumption",
    status_code=status.HTTP_200_OK
)
async def get_consumption_ranking(
        after: Optional[datetime] = Query(default=None, description="After what timestamp"),
        limit: Optional[int] = Query(default=10, ge=0, description="The limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never]:
    return await analytics_service.db_ranking_consumption(after, limit, db)


@analytics_router.get(
    path="/export/device/{device_id}",
    description="Export data from the Device",
    response_model=None,
    status_code=status.HTTP_200_OK
)
async def export_device_analytics(
        file_format: Literal["json", "csv"] = Query(default="json", description="The format of the returned data"),
        device_id: UUID = Path(default=..., description="The Device ID"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=None, ge=0, description="A limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never] | StreamingResponse:
    await validate_device_exists(str(device_id), db)
    await validate_device_has_analytics(str(device_id), db)
    daterange = await validate_daterange(start_datetime, end_datetime)

    data = await analytics_service.db_get_analytics_history(str(device_id), daterange, limit, db)

    if not data:
        return []

    if file_format == "csv":
        return to_csv(data)

    return data


@analytics_router.get(
    path="/export/all",
    description="Export all analytics data",
    response_model=None,
    status_code=status.HTTP_200_OK
)
async def export_all_analytics(
        file_format: Literal["json", "csv"] = Query(default="json", description="The format of the returned data"),
        start_datetime: Optional[datetime] = Query(default=None, description="The start datetime"),
        end_datetime: Optional[datetime] = Query(default=None, description="The end datetime"),
        limit: Optional[int] = Query(default=None, ge=0, description="A limit"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[AnalyticsRead] | list[Never] | StreamingResponse:
    daterange = await validate_daterange(start_datetime, end_datetime)
    data = await analytics_service.db_get_analytics_history(None, daterange, limit, db)

    if not data:
        return []

    if file_format == "csv":
        return to_csv(data)

    return data