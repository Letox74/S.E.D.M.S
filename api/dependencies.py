from fastapi import Security, Request, HTTPException, status
from fastapi.security import APIKeyHeader

from database.connection import DatabaseManager
from internal.security import verify_api_key

API_KEY_HEADER = APIKeyHeader(name="API-KEY", scheme_name="API Key")


# Basic Dependencies
async def api_key_auth(api_key: str = Security(API_KEY_HEADER)) -> str:
    await verify_api_key(api_key) # checks if the provided api key matches the one in .env
    return api_key


async def get_db_session(request: Request) -> DatabaseManager:
    return request.app.state.db_manager # get the DBManager out of the app state


# Device Dependencies
async def validate_device_exists(device_id: str, db: DatabaseManager) -> str:
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

    return device_id


async def validate_firmware_version_exists(firmware_version: str, db: DatabaseManager) -> str:
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

    return firmware_version
