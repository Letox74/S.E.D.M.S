import csv
import io
from typing import Optional, Literal, Never
from uuid import UUID

from fastapi import APIRouter, status, Depends, Query, Path, Body
from fastapi.responses import StreamingResponse

from api.dependencies import get_db_session, validate_device_exists, validate_firmware_version_exists
from database.connection import DatabaseManager
from internal.schemas.device_models import (
    DeviceTypes,
    DeviceStatus,
    DeviceCreate,
    DeviceUpdate,
    DeviceRead
)
from internal.service import device_service

device_router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)


@device_router.get(
    path="/",
    response_model=list[DeviceRead],
    description="Fetches all registered Devices from the Database",
    status_code=status.HTTP_200_OK
)
async def get_all_devices(
        db: DatabaseManager = Depends(get_db_session)
) -> list[DeviceRead] | list[Never]:
    return await device_service.db_get_all_devices(db)


@device_router.post(
    path="/",
    response_model=DeviceRead,
    description="Creates a new Device inside the Database",
    status_code=status.HTTP_201_CREATED
)
async def create_device(
        data: DeviceCreate = Body(..., embed=True, description="The data needed to create the Device"),
        db: DatabaseManager = Depends(get_db_session)
) -> DeviceRead:
    return await device_service.db_create_device(data, db)


@device_router.get(
    path="/search",
    response_model=list[DeviceRead],
    description="Searches in the name and the description",
    status_code=status.HTTP_200_OK
)
async def search_devices(
        q: str = Query(..., description="The values searched for in the name and description", min_length=1, max_length=200),
        db: DatabaseManager = Depends(get_db_session)
) -> list[DeviceRead] | list[Never]:
    return await device_service.db_search_devices(q, db)


@device_router.get(
    path="/filter",
    response_model=list[DeviceRead],
    description="Filters the Device Database on certain Query Parameters",
    status_code=status.HTTP_200_OK
)
async def filter_devices(
        device_type: Optional[DeviceTypes] = Query(None, description="The Device Type (optional)"),
        firmware_version: Optional[str] = Query(None, description="The firmware version of the Device (optional)", min_length=5, max_length=32),
        device_status: Optional[DeviceStatus] = Query(None, description="The Device Status (optional)"),
        is_active: Optional[bool] = Query(None, description="If the Device should be active (optional)"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[DeviceRead] | list[Never]:
    if firmware_version is not None:
        await validate_firmware_version_exists(firmware_version, db)

    return await device_service.db_filter_devices(device_type, firmware_version, device_status, is_active, db)


@device_router.get(
    path="/active",
    response_model=list[DeviceRead],
    description="Get all Devices which are currently active",
    status_code=status.HTTP_200_OK
)
async def get_active_devices(
        db: DatabaseManager = Depends(get_db_session)
) -> list[DeviceRead] | list[Never]:
    return await device_service.db_get_active_devices(db)


@device_router.get(
    path="/stats/summary",
    response_model=dict[str, int | dict[str, int] | list[str]],
    description="Get stats like total count or status distribution",
    status_code=status.HTTP_200_OK
)
async def get_device_stats(
        db: DatabaseManager = Depends(get_db_session)
) -> dict[str, int | dict[str, int] | list[str]]:
    return await device_service.db_get_device_stats(db)


@device_router.get(
    path="/types",
    response_model=list[str],
    description="Get all allowed types",
    status_code=status.HTTP_200_OK
)
async def get_device_types() -> list[str]:
    return await DeviceTypes.values()


@device_router.get(
    path="/statuses",
    response_model=list[str],
    description="Get all allowed statuses",
    status_code=status.HTTP_200_OK
)
async def get_device_statuses() -> list[str]:
    return await DeviceStatus.values()


@device_router.get(
    path="/export",
    response_model=None,
    description="Get all Devices in JSON or CSV Format",
    status_code=status.HTTP_200_OK
)
async def export_devices(
        file_format: Literal["json", "csv"] = Query(default="json", description="The format of the returned data"),
        db: DatabaseManager = Depends(get_db_session)
) -> StreamingResponse | list[DeviceRead] | list[Never]:
    data = await device_service.db_get_all_devices(db)

    if not data:
        return []

    if file_format == "csv":
        data = [model.model_dump() for model in data]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)

        return StreamingResponse(output, media_type="text/csv")

    return data


@device_router.get(
    path="/{device_id}",
    response_model=DeviceRead,
    description="Gets a Device from the Database",
    status_code=status.HTTP_200_OK
)
async def get_device(
        device_id: UUID = Path(..., description="The ID of the Device"),
        db: DatabaseManager = Depends(get_db_session)
) -> DeviceRead:
    await validate_device_exists(str(device_id), db)
    return await device_service.db_get_device(str(device_id), db)


@device_router.patch(
    path="/{device_id}",
    response_model=DeviceRead,
    description="Updates the stored data in the Database",
    status_code=status.HTTP_200_OK
)
async def update_device(
        device_id: UUID = Path(..., description="The ID of the Device"),
        data: DeviceUpdate = Body(..., embed=True, description="The data needed to update the Device"),
        db: DatabaseManager = Depends(get_db_session)
) -> DeviceRead:
    await validate_device_exists(str(device_id), db)
    return await device_service.db_update_device(str(device_id), data, db)


@device_router.delete(
    path="/{device_id}",
    response_model=None,
    description="Deletes a Device in the Database",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_device(
        device_id: UUID = Path(..., description="The ID of the Device"),
        db: DatabaseManager = Depends(get_db_session)
) -> None:
    await validate_device_exists(str(device_id), db)
    await device_service.db_delete_device(str(device_id), db)

    return None


@device_router.post(
    path="/bulk",
    response_model=list[DeviceRead],
    description="Register multiple Devices at the same time",
    status_code=status.HTTP_201_CREATED
)
async def bulk_register(
        data: list[DeviceCreate] = Body(..., embed=True, description="The data needed to create the Devices"),
        db: DatabaseManager = Depends(get_db_session)
) -> list[DeviceRead]:
    return await device_service.db_bulk_register(data, db)


@device_router.put(
    path="/{device_id}/status",
    response_model=DeviceRead,
    description="Changens the current status of the Device",
    status_code=status.HTTP_200_OK
)
async def set_device_status(
        device_id: UUID = Path(..., description="The ID of the Device"),
        new_status: DeviceStatus = Body(..., embed=True, description="The new status of the Device"),
        db: DatabaseManager = Depends(get_db_session)
) -> DeviceRead:
    await validate_device_exists(str(device_id), db)
    return await device_service.db_set_device_status(str(device_id), new_status.value, db)


@device_router.patch(
    path="/{device_id}/toggle",
    response_model=DeviceRead,
    description="Toggles the is_active column",
    status_code=status.HTTP_200_OK
)
async def toggle_active(
        device_id: UUID = Path(..., description="The ID of the Device"),
        db: DatabaseManager = Depends(get_db_session)
) -> DeviceRead:
    await validate_device_exists(str(device_id), db)
    return await device_service.db_toggle_active(str(device_id), db)
