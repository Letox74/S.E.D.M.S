"""
utils because there the same endpoints on telemetry and analytics
"""
import logging
from datetime import datetime
from typing import Optional, Never

import aiosqlite
from aiosqlite import Row

from database.connection import DatabaseManager
from ..schemas.analytic_models import AnalyticsRead, AnalyticsCreate
from ..schemas.device_models import DeviceRead, DeviceCreate
from ..schemas.prediction_models import PredictionRead, PredictionCreate
from ..schemas.telemetry_models import TelemetryRead, TelemetryCreate

app_logger = logging.getLogger("App")
telemetry_logger = logging.getLogger("Telemetry")
analytics_logger = logging.getLogger("Analytics")
ml_logger = logging.getLogger("ML")

# method for device, telemetry and analytics
def _handle_new_row_result(table_name: str, row: Row) -> DeviceRead | TelemetryRead | AnalyticsRead:
    mapping_dict = {
        "devices": (
            lambda: app_logger.info(f"New Device registered: {row["id"]} of type {row["type"]}"),
            lambda: DeviceRead(**dict(row))
        ),
        "telemetry": (
            lambda: telemetry_logger.info(f"New Telemetry Data from Device {row["device_id"]}"),
            lambda: TelemetryRead(**dict(row))
        ),
        "analytics": (
            lambda: analytics_logger.info(f"Received new Analytics Data from Device {row["device_id"]}"),
            lambda: AnalyticsRead(**dict(row))
        ),
        "predictions": (
            lambda: ml_logger.info("Saved new Prediction"),
            lambda: PredictionRead(**dict(row))
        )
    }

    mapping_dict[table_name][0]()
    return mapping_dict[table_name][1]()


async def db_insert_new_row(
        data: DeviceCreate | TelemetryCreate | AnalyticsCreate | PredictionCreate,
        table_name: str,
        db: DatabaseManager
) -> DeviceRead | TelemetryRead | AnalyticsRead | PredictionRead:
    fields = data.model_dump()  # to not type it manually

    # prepare sql string
    colums = ", ".join(f"{key}" for key in fields.keys())
    placeholders = ", ".join("?" for _ in fields)
    values = tuple(fields.values())

    sql = f"""
        INSERT INTO {table_name}
        ({colums})
        VALUES ({placeholders})
        RETURNING *;
    """
    row = await db.execute_transaction(sql, values)  # retrieve the entire row (due to RETURNING *)
    return _handle_new_row_result(table_name, row)


def _return_row(
        rows: list[aiosqlite.Row] | list[Never],
        table_name: str
) -> list[TelemetryRead] | list[AnalyticsRead] | list[PredictionRead] | list[Never]:
    if table_name == "telemetry":
        return [TelemetryRead(**dict(row)) for row in rows]

    elif table_name == "analytics":
        return [AnalyticsRead(**dict(row)) for row in rows]

    return [PredictionRead(**dict(row)) for row in rows]


# methods for telemetry and analytics
async def db_get_latest_row(
        device_id: Optional[str],
        table_name: str,
        db: DatabaseManager
) -> TelemetryRead | AnalyticsRead | PredictionRead | None:
    sql = f"""
        SELECT *
        FROM {table_name}
        {"WHERE device_id = ?" if device_id else ""}
        ORDER BY timestamp DESC
        LIMIT 1;
    """
    row = await db.fetch_one(sql, (device_id,) if device_id else ())

    if row is None:
        return None

    elif table_name == "telemetry":
        return TelemetryRead(**dict(row))

    elif table_name == "analytics":
        return AnalyticsRead(**dict(row))

    return PredictionRead(**dict(row))


async def db_get_history(
        device_id: Optional[str],
        daterange: Optional[list[datetime]],
        limit: Optional[int],
        table_name: str,
        db: DatabaseManager
) -> list[TelemetryRead] | list[AnalyticsRead] | list[PredictionRead] | list[Never]:
    # strftime to a string if datetime was set, then prepare the params
    daterange = daterange or [None]
    params = tuple(param for param in (device_id, *daterange, limit) if param is not None)

    # prepare the where clause
    where_clause = []
    if device_id:
        where_clause.append("device_id = ?")
    if daterange[0]:
        where_clause.append("timestamp BETWEEN ? AND ?")

    where_str = f"WHERE {" AND ".join(where_clause)}" if where_clause else ""

    sql = f"""
        SELECT *
        FROM {table_name}
        {where_str}
        ORDER BY timestamp DESC
        {"LIMIT ?" if limit else ""};
    """
    rows = await db.fetch_all(sql, params)

    return _return_row(rows, table_name)


async def db_get_range(
        device_id: Optional[str],
        daterange: list[datetime],
        table_name: str,
        db: DatabaseManager
) -> list[TelemetryRead] | list[AnalyticsRead] | list[PredictionRead] | list[Never]:
    params = tuple([param for param in (*daterange, device_id) if param is not None])

    sql = f"""
        SELECT *
        FROM {table_name}
        WHERE timestamp BETWEEN ? AND ?
            {"AND device_id = ?" if device_id else ""};
    """
    rows = await db.fetch_all(sql, params)
    # here I don't need to check if the date is None, because it's not an optional parameter

    return _return_row(rows, table_name)


async def db_delete(
        device_id: Optional[str],
        before: Optional[datetime],
        limit: Optional[int],
        table_name: str,
        db: DatabaseManager
) -> int:
    values = tuple(param for param in (device_id, before, limit) if param is not None)  # prepare the params
    where_clause = []
    if device_id:
        where_clause.append("device_id = ?")
    if before:
        where_clause.append("timestamp < ?")
    where_str = f"WHERE {" AND ".join(where_clause)}" if where_clause else ""


    sql = f"""
        DELETE FROM {table_name}
        {where_str}
        ORDER BY timestamp ASC
        {"LIMIT ?" if limit else ""};
    """
    deleted_rows = await db.execute_transaction(sql, values)  # get the deleted row count back

    return deleted_rows


async def db_count(device_id: Optional[str], table_name: str, db: DatabaseManager) -> int:
    sql = f"""
        SELECT COUNT(*) AS count
        FROM {table_name} AS T01
        {"WHERE device_id = ?" if device_id else ""};
    """
    row = await db.fetch_one(sql, (device_id,) if device_id else ())

    return row["count"]  # access column "count"