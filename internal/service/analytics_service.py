import logging
from datetime import datetime, date, timezone, time, timedelta
from enum import Enum
from typing import Optional, Never

from database.connection import DatabaseManager
from internal.schemas.analytic_models import AnalyticsCreate, AnalyticsRead
from .utils import (
    db_insert_new_row,
    db_get_latest_row,
    db_get_range,
    db_get_history,
    db_delete,
    db_count
)

analytics_logger = logging.getLogger("Analytics")


async def insert_new_analytic(data: AnalyticsCreate, db: DatabaseManager) -> AnalyticsRead:
    return await db_insert_new_row(data, "analytics", db)


async def db_get_latest_analytic(device_id: Optional[str], db: DatabaseManager) -> AnalyticsRead | None:
    return await db_get_latest_row(device_id, "analytics", db)


async def db_get_analytics_history(
        device_id: Optional[str],
        daterange: Optional[list[datetime]],
        limit: Optional[int],
        db: DatabaseManager
) -> list[AnalyticsRead]:
    return await db_get_history(device_id, daterange, limit, "analytics", db)


async def db_get_analytics_range(
        device_id: Optional[str],
        daterange: list[datetime],
        db: DatabaseManager
) -> list[AnalyticsRead]:
    return await db_get_range(device_id, daterange, "analytics", db)


async def db_delete_analytics(
        device_id: Optional[str],
        before: Optional[datetime],
        limit: Optional[int],
        db: DatabaseManager
) -> int:
    return await db_delete(device_id, before, limit, "analytics", db)


async def db_analytics_count(device_id: Optional[str], db: DatabaseManager) -> int:
    return await db_count(device_id, "analytics", db)


async def db_get_daily_summary(
        device_id: Optional[str],
        summary_date: Optional[date],
        db: DatabaseManager
) -> dict[str, str | float | int] | None:
    if summary_date is None:
        summary_date = date.today()

    # combine the dates to a datetime
    start_dt = datetime.combine(summary_date, time.min, timezone.utc)
    end_dt = datetime.combine(summary_date, time.max, timezone.utc)
    params = tuple([param for param in (device_id, start_dt, end_dt, device_id) if param])

    sql = f"""
        SELECT 
            ROUND(AVG(T02.avg_power), 2)            AS avg_power,
            ROUND(AVG(T02.avg_voltage), 2)          AS avg_voltage,
            ROUND(AVG(T02.avg_current), 2)          AS avg_current,
            ROUND(AVG(T02.avg_signal_strength), 2)  AS avg_signal_strength,
            ROUND(AVG(T02.avg_temperature), 2)      AS avg_temperature,
            ROUND(AVG(T02.efficiency_score), 2)     AS avg_efficiency,
            
            ROUND(SUM(T02.energy_consumption) / 1000, 2)     AS total_energy_kwh,
            
            (
                SELECT COUNT(DISTINCT T01.device_id)
                FROM analytics AS T01
                {"WHERE T01.device_id = ?" if device_id else ""}
            ) AS device_count
            
        FROM analytics AS T02
        WHERE T02.timestamp BETWEEN ? AND ?
        {"AND T02.device_id = ?" if device_id else ""};
    """
    row = await db.fetch_one(sql, params)

    if row is None:
        return None

    # return results
    return {
        "date": str(summary_date),
        "avg_power": row["avg_power"],
        "avg_voltage": row["avg_voltage"],
        "avg_current": row["avg_current"],
        "avg_signal_strength": row["avg_signal_strength"],
        "avg_temperature": row["avg_temperature"],
        "avg_efficiency": row["avg_efficiency"],
        "total_energy_kwh": row["total_energy_kwh"],
        "active_devices": row["device_count"]
    }


def _get_alerts_where_clause(
        after: datetime,
        efficiency_threshold: Optional[float | int] = None,
        std_threshold: Optional[float | int] = None,
        std_name: Optional[str] = None,
        operation_hours_threshold: Optional[float | int] = None
) -> tuple[str, tuple[float | int | datetime]]:
    where_clause = ["timestamp > ?"]
    params = [after]

    # prepare where clause
    if efficiency_threshold is not None:
        where_clause.append("efficiency_score < ?")
        params.append(efficiency_threshold)

    if std_threshold is not None:
        where_clause.append(f"{std_name} > ?")
        params.append(std_threshold)

    if operation_hours_threshold is not None:
        where_clause.append("operation_hours > ?")
        params.append(operation_hours_threshold)

    where_str = f"WHERE {" AND ".join(where_clause)}" if where_clause else ""
    return where_str, tuple(params)


def _get_alerts_sql(where_str: str) -> str:
    sql = f"""
        SELECT 
            T01.*,
            T02.name     AS device_name,
            T02.location AS device_location
        FROM analytics AS T01
        JOIN devices AS T02 ON T01.device_id = T02.id
        {where_str}
        ORDER BY timestamp DESC;
    """
    return sql

# define enum
class _AlertMode(str, Enum):
    STD = "std"
    EFFICIENCY = "efficiency"
    OPERATION_HOURS = "operation_hours"

# define gerneric func for many actions
def _alert_fetcher(mode: _AlertMode, std_name: Optional[str] = None):
    async def fetcher(
            threshold: float | int,
            after: Optional[datetime],
            db: DatabaseManager,
    ) -> list[AnalyticsRead] | list[Never]:
        after = after or datetime.now(timezone.utc) - timedelta(hours=1)

        # geht the right arguments for the where clause functions
        kwargs = {
            _AlertMode.STD: dict(std_threshold=threshold, std_name=std_name),
            _AlertMode.EFFICIENCY: dict(efficiency_threshold=threshold),
            _AlertMode.OPERATION_HOURS: dict(operation_hours_threshold=threshold),
        }[mode]

        where_str, params = _get_alerts_where_clause(after, **kwargs)
        rows = await db.fetch_all(_get_alerts_sql(where_str), params)

        return [AnalyticsRead(**dict(row)) for row in rows]

    return fetcher

# define many alerts funcs
db_alerts_efficiency = _alert_fetcher(_AlertMode.EFFICIENCY)
db_alerts_operation_hours = _alert_fetcher(_AlertMode.OPERATION_HOURS)
db_alerts_std_power = _alert_fetcher(_AlertMode.STD, "std_power")
db_alerts_std_voltage = _alert_fetcher(_AlertMode.STD, "std_voltage")
db_alerts_std_current = _alert_fetcher(_AlertMode.STD, "std_current")
db_alerts_std_signal_strength = _alert_fetcher(_AlertMode.STD, "std_signal_strength")
db_alerts_std_temperature = _alert_fetcher(_AlertMode.STD, "std_temperature")


# same as above, generic func for many uses
def _ranking_fetcher(column: str):
    async def fetcher(
            after: Optional[datetime],
            limit: Optional[int],
            db: DatabaseManager
    ) -> list[AnalyticsRead] | list[Never]:
        after = after or datetime.now(timezone.utc) - timedelta(hours=1)
        params = tuple([param for param in (after, limit) if param])

        sql = f"""
            SELECT
                T01.*,
                T02.name     AS device_name,
                T02.location AS device_location
            
            FROM analytics AS T01
            JOIN devices AS T02 ON T01.device_id = T02.id
            WHERE timestamp > ?
            ORDER BY {column} DESC
            {"LIMIT ?" if limit else ""};
        """
        rows = await db.fetch_all(sql, params)

        return [AnalyticsRead(**dict(row)) for row in rows]

    return fetcher


db_ranking_efficiency = _ranking_fetcher("efficiency_score")
db_ranking_consumption = _ranking_fetcher("energy_consumption")