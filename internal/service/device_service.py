import asyncio
import logging
from datetime import datetime, timezone
from typing import Never, Optional
from uuid import uuid4

from fastapi import HTTPException, status

from database.connection import DatabaseManager
from internal.schemas.device_models import DeviceRead, DeviceCreate, DeviceUpdate

app_logger = logging.getLogger("App")
error_logger = logging.getLogger("Error")


# device status log service
async def get_last_status_timestamp(device_id: str, device_status: str, db: DatabaseManager) -> datetime:
    sql = """
        SELECT timestamp
        FROM device_status_log
        WHERE device_id = ?
            AND status = ?
        ORDER BY timestamp DESC
        LIMIT 1;
    """
    row = await db.fetch_one(sql, (device_id, device_status))
    if not row:
        device = await db_get_device(device_id, db)
        timestamp = device.created_at

    else:
        timestamp = row["timestamp"]

    return timestamp


async def _update_status_log(device_id: str, device_status: str, db: DatabaseManager) -> None:
    sql = """
        INSERT INTO device_status_log
        (device_id, status)
        VALUES (?, ?);
    """
    await db.execute_transaction(sql, (device_id, device_status))


async def db_get_all_devices(db: DatabaseManager) -> list[DeviceRead] | list[Never]:
    sql = f"""
        SELECT * 
        FROM devices;
    """
    rows = await db.fetch_all(sql)

    return [DeviceRead(**dict(row)) for row in rows]  # return single DeviceRead Objects


async def db_create_device(data: DeviceCreate, db: DatabaseManager) -> DeviceRead:
    fields = data.model_dump()  # to not type it manually
    fields = {**{"id": str(uuid4())}, **fields}  # generate key and union the fields

    # prepare sql string
    colums = ", ".join(f"{key}" for key in fields.keys())
    placeholders = ", ".join("?" for _ in fields)
    values = tuple(fields.values())

    sql = f"""
        INSERT INTO devices
        ({colums})
        VALUES ({placeholders})
        RETURNING *;
    """
    row = await db.execute_transaction(sql, values)  # retrieve the entire row (due to RETURNING *)
    app_logger.info(f"New Device registered: {fields["id"]} of type {fields["type"]}")

    # insert status into the status log
    await _update_status_log(fields["id"], fields["status"], db)

    return DeviceRead(**dict(row))


async def db_bulk_register(data: list[DeviceCreate], db: DatabaseManager) -> list[DeviceRead]:
    func_list = [db_create_device(model, db) for model in data]
    return await asyncio.gather(*func_list)


async def db_search_devices(q: str, db: DatabaseManager) -> list[DeviceRead] | list[Never]:
    # search in the name or descripton
    # Use collate nocase for case insensitivity
    sql = f"""
        SELECT *
        FROM devices 
        WHERE name LIKE ? COLLATE NOCASE
            OR description LIKE ? COLLATE NOCASE;
    """
    rows = await db.fetch_all(sql, (f"%{q}%", f"%{q}%"))

    return [DeviceRead(**dict(row)) for row in rows]


async def db_filter_devices(
        type_: Optional[str],
        firmware_version: Optional[str],
        device_status: Optional[str],
        is_active: Optional[bool],
        has_battery: Optional[bool],
        db: DatabaseManager
) -> list[DeviceRead] | list[Never]:
    filters = {
        "type": type_,
        "firmware_version": firmware_version,
        "status": device_status,
        "is_active": is_active,
        "has_battery": has_battery
    }
    active_filters = {key: value for key, value in filters.items() if value is not None}  # only the selected filters

    if not active_filters:
        return await db_get_all_devices(db)

    # prepare sql string
    conditions = " AND ".join(f"{key} = ?" for key in active_filters.keys())
    values = tuple(active_filters.values())

    sql = f"""
        SELECT * 
        FROM devices 
        WHERE {conditions};
    """
    rows = await db.fetch_all(sql, values)

    return [DeviceRead(**dict(row)) for row in rows]


async def db_get_active_devices(db: DatabaseManager) -> list[DeviceRead] | list[Never]:
    sql = """
        SELECT *
        FROM devices 
        WHERE is_active = 1;
    """
    rows = await db.fetch_all(sql)

    return [DeviceRead(**dict(row)) for row in rows]


async def db_get_device_stats(db: DatabaseManager) -> dict[str, int | dict[str, int]]:
    # sql queries
    sql_total_count = """
        SELECT 
            COUNT(id) AS count 
        FROM devices;
    """
    sql_active_count = """
        SELECT
            COUNT(id) AS count 
        FROM devices 
        WHERE is_active = 1;
    """
    sql_status_distribution = """
        SELECT 
            status,
            COUNT(id)   AS count
        FROM devices
        GROUP BY status 
        ORDER BY count DESC;
    """
    sql_type_distribution = """
        SELECT 
            type,
            COUNT(id)   AS count
        FROM devices
        GROUP BY type 
        ORDER BY count DESC;
    """
    sql_firmware_stats = """
        SELECT 
            firmware_version        AS version,
            COUNT(firmware_version) AS count
        FROM devices
        GROUP BY firmware_version 
        ORDER BY COUNT(id) DESC;
    """

    # gather results
    (
        total_count,
        active_count,
        status_distribution,
        type_distribution,
        firmware_stats
    ) = await asyncio.gather(
        db.fetch_one(sql_total_count),
        db.fetch_one(sql_active_count),
        db.fetch_all(sql_status_distribution),
        db.fetch_all(sql_type_distribution),
        db.fetch_all(sql_firmware_stats)
    )

    return {
        "total_count": total_count["count"],
        "active_count": active_count["count"],
        "status_distribution": {row["status"]: row["count"] for row in status_distribution},
        "type_distribution": {row["type"]: row["count"] for row in type_distribution},
        "firmware_stats": {row["version"]: row["count"] for row in firmware_stats}
    }


async def db_get_device(device_id: str, db: DatabaseManager) -> DeviceRead:
    sql = """
        SELECT * 
        FROM devices 
        WHERE id = ?;
    """
    row = await db.fetch_one(sql, (device_id,))

    return DeviceRead(**dict(row))  # unpack the row into the DeviceRead Object


async def db_update_device(device_id: str, data: DeviceUpdate, db: DatabaseManager) -> DeviceRead:
    old_device = await db_get_device(device_id, db)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)  # exclude_unset and exclude_none to retrieve only the fields need to be updated

    if "status" in changes.keys():
        if changes.get("is_active") and changes["status"] != "online":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cannot change if is active is true and the status is not online"
            )

        await _update_status_log(device_id, changes["status"], db)

    if not changes:
        return old_device

    # prepare sql string
    changes = {**changes, **{"modified_at": datetime.fromisoformat(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))}}
    set_clause = ", ".join(f"{key} = ?" for key in changes)
    values = tuple(changes.values()) + (device_id,)  # add device id (WHERE clause)

    sql = f"""
        UPDATE devices
        SET {set_clause}
        WHERE id = ?;
    """
    await db.execute_transaction(sql, values)
    app_logger.info(f"Device with ID {device_id} updated. Changes: {changes}")

    return old_device.model_copy(update=changes)  # replace the updated fields on the old model


async def db_delete_device(device_id: str, db: DatabaseManager) -> None:
    sql = """
        DELETE FROM devices 
        WHERE id = ?;
    """
    await db.execute_transaction(sql, (device_id,))
    app_logger.info(f"Device with ID {device_id} was deleted")

    return None


async def db_set_device_status(device_id: str, device_status: str, db: DatabaseManager) -> DeviceRead:
    sql = """
        UPDATE devices
        SET status = ?, modified_at = ?
        WHERE id = ?
        RETURNING *;
    """
    row = await db.execute_transaction(sql, (device_status, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), device_id))
    await _update_status_log(device_id, device_status, db)

    return DeviceRead(**dict(row))


async def db_toggle_active(device_id: str, db: DatabaseManager) -> DeviceRead:
    sql = """
        UPDATE devices 
        SET is_active = NOT is_active, modified_at = ?
        WHERE id = ?
        RETURNING *;
    """
    row = await db.execute_transaction(sql, (datetime.now(timezone.utc).replace(microsecond=0), device_id))

    return DeviceRead(**dict(row))


async def db_get_device_by_name_and_location(name: str, location: str, db: DatabaseManager) -> DeviceRead | None:
    sql = """
        SELECT *
        FROM devices
        WHERE name = ? COLLATE NOCASE
            AND location = ? COLLATE NOCASE;
    """
    row = await db.fetch_one(sql, (name, location))
    
    return DeviceRead(**dict(row)) if row else None