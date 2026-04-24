from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import Security, Request, HTTPException, status
from fastapi.security import APIKeyHeader

from database.connection import DatabaseManager
from internal.security import verify_api_key

API_KEY_HEADER = APIKeyHeader(name="API-KEY", scheme_name="API Key")


# Basic Dependencies
async def api_key_auth(api_key: str = Security(API_KEY_HEADER)) -> None:
    await verify_api_key(api_key) # checks if the provided api key matches the one in .env


async def get_db_session(request: Request) -> DatabaseManager:
    return request.app.state.db_manager # get the DBManager out of the app state


# Device Dependencies
async def validate_device_exists(device_id: str, db: DatabaseManager) -> None:
    result = await db.fetch_one("""
        SELECT 1
        FROM devices
        WHERE id = ?;
    """, (device_id,)) # just check if the ID exists

    if result is None:
        raise HTTPException( # raise HTTPException if the ID does not exist
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found"
        )


async def validate_firmware_version_exists(firmware_version: str, db: DatabaseManager) -> None:
    result = await db.fetch_one("""
        SELECT 1
        FROM devices
        WHERE firmware_version = ?;
    """, (firmware_version,)) # check if the firmware_verions exists

    if result is None:
        raise HTTPException( # raise HTTPException if the firmware_version does not exist
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Device found with this firmware version: {firmware_version}"
        )


async def validate_status_with_is_active(
        device_id: Optional[str],
        device_status: str,
        is_active: bool,
        db: DatabaseManager
)-> None:
    if device_id:
        pass


# Telemetry Dependencies
async def validate_device_has_telemetry(device_id: str, db: DatabaseManager) -> None:
    result = await db.fetch_one("""
        SELECT 1
        FROM telemetry
        WHERE device_id = ?
    """, (device_id,))

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Telemetry data found for this Device: {device_id}"
        )

async def validate_daterange(start_datetime: Optional[datetime], end_datetime: Optional[datetime]) -> list[datetime] | None:
    @dataclass(frozen=True)
    class DateRange:
        start: datetime
        end: datetime

        def __post_init__(self) -> None:
            if self.start > self.end:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The start datetime is greater than the end datetime"
                )

        def to_list(self) -> list[datetime]:
            return [self.start, self.end]

    if start_datetime is None and end_datetime is None:
        return None

    start_datetime = start_datetime or datetime(2026, 1, 1, tzinfo=timezone.utc)
    end_datetime = end_datetime or datetime.now(timezone.utc).replace(microsecond=0)

    return DateRange(start_datetime, end_datetime).to_list()

async def validate_device_has_battery(device_id: str, db: DatabaseManager) -> bool:
    sql = """
        SELECT has_battery
        FROM devices
        WHERE id = ?
        LIMIT 1;
    """
    row = await db.fetch_one(sql, (device_id,))

    if not row["has_battery"]:
        return False

    return True