import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Never, Optional

from database.connection import DatabaseManager
from internal.schemas.telemetry_models import TelemetryCreate, TelemetryRead
from .analytics_service import insert_new_analytic
from .calculator import calculate_statistics

telemetry_logger = logging.getLogger("Telemetry")
error_logger = logging.getLogger("Error")


# logic for the API Endpoints
async def validate_cooldown(device_id: str, db: DatabaseManager) -> str | None:
    COOLDOWN = timedelta(minutes=15)

    latest_telemetry = await db_get_latest_telemetry(device_id, db)
    if not latest_telemetry:
        return None

    time_since_last = datetime.now(timezone.utc) - latest_telemetry.timestamp

    if time_since_last >= COOLDOWN:
        return None

    # calculate the time
    remaining = COOLDOWN - time_since_last
    remaining_total_seconds = remaining.total_seconds()

    if remaining_total_seconds >= 60:
        display_time = remaining_total_seconds / 60
        unit = "minutes"
    else:
        display_time = remaining_total_seconds
        unit = "seconds"

    message =  (
        f"Telemetry ingestion rejected for device {device_id} "
        f"cooldown active {display_time:.2f} {unit} remaining"
    )

    telemetry_logger.info(message)
    return message

async def db_ingest_telemetry(data: TelemetryCreate, db: DatabaseManager) -> TelemetryRead | str:
    message = await validate_cooldown(data.device_id, db)
    if isinstance(message, str): return message

    fields = data.model_dump()  # to not type it manually

    # prepare sql string
    colums = ", ".join(f"{key}" for key in fields.keys())
    placeholders = ", ".join("?" for _ in fields)
    values = tuple(fields.values())

    sql = f"""
        INSERT INTO telemetry
        ({colums})
        VALUES ({placeholders})
        RETURNING *;
    """
    row = await db.execute_transaction(sql, values)  # retrieve the entire row (due to RETURNING *)
    telemetry_logger.info(f"New Telemetry Data from Device {fields["device_id"]}")

    return TelemetryRead(**dict(row))


async def db_get_latest_telemetry(device_id: str, db: DatabaseManager) -> TelemetryRead | None:
    sql = """
        SELECT *
        FROM telemetry
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT 1;
    """
    row = await db.fetch_one(sql, (device_id,))

    return TelemetryRead(**dict(row)) if row is not None else None


async def db_get_telemetry_history(
        device_id: Optional[str],
        daterange: Optional[list[datetime]],
        limit: Optional[int],
        db: DatabaseManager
) -> list[TelemetryRead]:
    # strftime to a string if datetime was set, then prepare the params
    daterange = daterange or [None]
    params = tuple(param for param in (device_id, *daterange, limit) if param is not None)

    where_clause = []
    if device_id:
        where_clause.append("device_id = ?")
    if daterange[0]:
        where_clause.append("timestamp BETWEEN ? AND ?")

    where_str = f"WHERE {" AND ".join(where_clause)}" if where_clause else ""

    sql = f"""
        SELECT *
        FROM telemetry
        {where_str}
        ORDER BY timestamp DESC
        {"LIMIT ?" if limit else ""};
    """
    rows = await db.fetch_all(sql, params)

    return [TelemetryRead(**dict(row)) for row in rows]


async def db_get_telemetry_range(
        device_id: str,
        daterange: list[datetime],
        db: DatabaseManager
) -> list[TelemetryRead] | list[Never]:
    sql = """
        SELECT *
        FROM telemetry
        WHERE device_id = ?
            AND timestamp BETWEEN ? AND ?;
    """
    rows = await db.fetch_all(sql, (device_id, *[date for date in daterange]))
    # here I don't need to check if the date is None, because it's not an optional parameter

    return [TelemetryRead(**dict(row)) for row in rows]


async def db_delete_telemetry(
        device_id: str,
        before: Optional[datetime],
        limit: Optional[int],
        db: DatabaseManager
) -> int:
    values = tuple(param for param in (device_id, before, limit) if param is not None)  # prepare the params

    sql = f"""
        DELETE FROM telemetry
        WHERE device_id = ?
            {"AND timestamp < ?" if before else ""}
        ORDER BY timestamp ASC
        {"LIMIT ?" if limit else ""};
    """
    deleted_rows = await db.execute_transaction(sql, values)  # get the deleted row count back

    return deleted_rows


async def db_telemetry_count(device_id: str, db: DatabaseManager) -> int:
    sql = """
        SELECT
            COUNT(*) AS count
        FROM telemetry
        WHERE device_id = ?;
    """
    row = await db.fetch_one(sql, (device_id,))

    return row["count"]  # access column "count"


async def _simple_sql_queries(where_clause: str, device_id: Optional[str]) -> tuple[str, str]:
    sql_total_count = f"""
            SELECT 
                COUNT(id) AS total_count
            FROM telemetry
            {where_clause};
        """
    sql_last_ingestion = f"""
            SELECT timestamp
            FROM telemetry
            {"WHERE device_id = ?" if device_id else ""}
            ORDER BY timestamp DESC
            LIMIT 1;
        """

    return sql_total_count, sql_last_ingestion


async def _complex_queries(where_clause: str) -> tuple[dict[str, str]] | tuple[dict[str, tuple[str, str]]]:
    # using a mapping dict to not type manually
    mapping_dict = {
        "voltage": ("lowest_voltage", "highest_voltage"),
        "current": ("lowest_current", "highest_current"),
        "signal_strength": ("lowest_signal_strength", "highest_signal_strength"),
        "frequency": ("lowest_frequency", "highest_frequency"),
        "temperature": ("lowest_temperature", "highest_temperature"),
        "current_battery_percentage": ("lowest_battery_percentage", "highest_battery_percentage")
    }
    queries = {}
    for key, (low_alias, high_alias) in mapping_dict.items():
        # insert the queries into a dict to easier access it
        queries[f"{key}_min"] = f"""
                    SELECT 
                        {key} AS {low_alias}, 
                        timestamp, 
                        device_id
                    FROM telemetry
                    {where_clause}
                    ORDER BY {key} ASC
                    LIMIT 1;
                """
        queries[f"{key}_max"] = f"""
                    SELECT 
                        {key} AS {high_alias}, 
                        timestamp, 
                        device_id
                    FROM telemetry
                    {where_clause}
                    ORDER BY {key} DESC
                    LIMIT 1;
                """

    return queries, mapping_dict


async def _handle_results(
        results,
        mapping_dict: dict[str, tuple[str, str]]
) -> dict[str, int | str | dict[str, float | str]]:
    # extract the results
    stats = {
        "total_count": results[0]["total_count"],
        "last_ingestion": str(results[1]["timestamp"])
    }

    for index, (key, (low_alias, high_alias)) in enumerate(mapping_dict.items()):
        min_row = results[2 + index * 2]  # because total_count and last_ingestion is for them in the results
        max_row = results[2 + index * 2 + 1]

        # extract query results
        stats[low_alias] = {
            "value": min_row[low_alias],
            "timestamp": str(min_row["timestamp"]),
            "device_id": min_row["device_id"]
        }
        stats[high_alias] = {
            "value": max_row[high_alias],
            "timestamp": str(max_row["timestamp"]),
            "device_id": max_row["device_id"]
        }

    return stats


async def db_get_telmetry_stats(
        device_id: Optional[str],
        daterange: Optional[list[datetime]],
        db: DatabaseManager
) -> dict[str, int | str | dict[str, float | str]]:
    # redefine types and format if daterange was set
    daterange = daterange or [None]

    where_clause = []
    params = []
    if daterange[0]:
        where_clause.append("timestamp BETWEEN ? AND ?")
        params.extend(daterange)
    if device_id:
        where_clause.append("device_id = ?")
        params.append(device_id)

    params = tuple(params)
    where_str = f"WHERE {" AND ".join(where_clause)}" if where_clause else ""

    # get queries
    sql_strings, queries = await asyncio.gather(
        _simple_sql_queries(where_str, device_id),
        _complex_queries(where_str)
    )

    # fetch the results asynchron
    results = await asyncio.gather(
        db.fetch_one(sql_strings[0], params),
        db.fetch_one(sql_strings[1], (device_id,) if device_id else ()),
        *[
            db.fetch_one(query, params)
            for query in queries[0].values()
        ]
    )
    return await _handle_results(results, queries[1])


async def db_alerts_battery(threshold: float, after: Optional[datetime], db: DatabaseManager) -> list[TelemetryRead]:
    # standard is 1 hour back
    after = after or (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0)

    sql = """
        SELECT *
        FROM telemetry
        WHERE current_battery_percentage < ? AND >= 0
            AND timestamp > ?
        ORDER BY timestamp DESC;
    """
    rows = await db.fetch_all(sql, (threshold, after))

    return [TelemetryRead(**dict(row)) for row in rows]


async def db_alerts_temperature(
        threshold: float,
        after: Optional[datetime],
        db: DatabaseManager
) -> list[TelemetryRead]:
    after = after or (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0)

    sql = """
        SELECT *
        FROM telemetry
        WHERE temperature > ?
            AND timestamp > ?
        ORDER BY timestamp DESC;
    """
    rows = await db.fetch_all(sql, (threshold, after))

    return [TelemetryRead(**dict(row)) for row in rows]


# logic for the Backgroundtask (calculate analytics)
async def get_last_24h(device_id: str, db: DatabaseManager) -> list[TelemetryRead]:
    time = (datetime.now(timezone.utc) - timedelta(hours=24)).replace(microsecond=0)

    sql = """
        SELECT * 
        FROM telemetry
        WHERE device_id = ?
            AND timestamp > ?
        ORDER BY timestamp ASC;
    """
    rows = await db.fetch_all(sql, (device_id, time))

    return [TelemetryRead(**dict(row)) for row in rows]


async def process_analytic_calculations(task_id: str, device_id: str, db: DatabaseManager) -> None:
    start_time = time.perf_counter()

    telemetry_logger.info(f"Task ID: {task_id}\t has started")
    telemetry_logger.info(f"Task ID: {task_id}\t fetching last telemetry entry of Device with ID: {device_id}")

    telemetry_count = await db_telemetry_count(device_id, db)
    if telemetry_count <= 1:
        telemetry_logger.info(f"Task ID {task_id}\t stopped, can't process with only one telemetry entry")
        return

    telemetry = await db_get_latest_telemetry(device_id, db)
    telemetry_logger.info(f"Task ID: {task_id}\t Infos fetched")
    telemetry_logger.info(f"Task ID: {task_id}\t start fetching Infos for the last 24 hours")

    past_telemetry = await get_last_24h(device_id, db)
    past_telemetry.append(telemetry)
    telemetry_logger.info(f"Task ID: {task_id}\t Infos found, calculating the analytics")

    analytic_data = await calculate_statistics(past_telemetry, db)
    await insert_new_analytic(analytic_data, db)

    duration = time.perf_counter() - start_time
    telemetry_logger.info(f"Task ID: {task_id}\t calculation and insertion done, Task done in {duration:.6f} seconds")
