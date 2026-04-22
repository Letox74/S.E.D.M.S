import asyncio
from datetime import datetime, timezone
from functools import reduce

import numpy as np

from database.connection import DatabaseManager
from internal.schemas.analytic_models import AnalyticsCreate
from internal.schemas.telemetry_models import TelemetryRead
from internal.service.device_service import get_last_status_timestamp


async def calculate_statistics(data: list[TelemetryRead], db: DatabaseManager) -> AnalyticsCreate:
    power = [round(telemetry.voltage * telemetry.current, 2) for telemetry in data]
    timestamps = [telemetry.timestamp for telemetry in data]

    results = await asyncio.gather(
        _calculate_power(power),
        _calculate_voltage([telemetry.voltage for telemetry in data]),
        _calculate_current([telemetry.current for telemetry in data]),
        _calculate_signal_strength([telemetry.signal_strength for telemetry in data]),
        _calculate_temperature([telemetry.temperature for telemetry in data]),
        _calculate_battery([telemetry.current_battery_percentage for telemetry in data])
    )
    other_results = await _calculate_other(str(data[0].device_id), power, timestamps, db)
    results_dict = reduce(lambda a, b: a | b, results, other_results)

    return AnalyticsCreate(**results_dict)


async def _helper_calculate(name, data: list[float]) -> dict[str, float]:
    return {
        f"avg_{name}": round(float(np.mean(data)), 2),
        f"peak_{name}": round(float(np.max(data)), 2),
        f"min_{name}": round(float(np.min(data)), 2),
        f"std_{name}": round(float(np.std(data)), 2)
    }


async def _calculate_power(data: list[float]) -> dict[str, float]:
    return await _helper_calculate("power", data)


# avg peak min std
async def _calculate_voltage(data: list[float]) -> dict[str, float]:
    return await _helper_calculate("voltage", data)


async def _calculate_current(data: list[float]):
    return await _helper_calculate("current", data)


async def _calculate_signal_strength(data: list[float]):
    return await _helper_calculate("signal_strength", data)


async def _calculate_temperature(data: list[float]):
    return await _helper_calculate("temperature", data)


async def _calculate_battery(data: list[float]):
    return {
        f"avg_battery_percentage": round(float(np.mean(data)), 0),
        f"min_battery_percentage": round(float(np.min(data)), 0)
    }


# logic to calculate the other stuff
async def _db_helper_error_count(device_id: str, latest_timestamp: datetime, db: DatabaseManager) -> int:
    sql = """
        SELECT COUNT(*) AS count
        FROM device_status_log
        WHERE device_id = ?
            AND status = ?
            AND timestamp >= ?;
    """
    row = await db.fetch_one(sql, (device_id, "error", latest_timestamp))

    return row["count"]


async def _calculate_energy_consumption(power: list[float], timestamps: list[datetime]) -> float:
    first_timestamp = timestamps[0]
    time_in_hours = [(timestamp - first_timestamp).total_seconds() / 3600 for timestamp in timestamps]

    return np.trapezoid(y=power, x=time_in_hours)  # trapz, because it gets the different offsets of the datetime


async def _calculate_efficiency_score(
        error_count: int,
        operation_hours: float,
        power: list[float]
) -> float:
    std_power = np.std(power)
    avg_power = np.mean(power)

    availability = operation_hours / 24
    stability = 1 - (std_power / (avg_power + 1e-9))  # prevent division by 0
    error_penalty = error_count * 0.05

    return max(0.0, min(100.0,
                        (availability * 0.5 + stability * 0.5) * 100 - error_penalty))


async def _calculate_other(
        device_id: str,
        power: list[float],
        timestamps: list[datetime],
        db: DatabaseManager
) -> dict[str, float | datetime]:
    results = await asyncio.gather(
        get_last_status_timestamp(device_id, "online", db),
        _db_helper_error_count(device_id, timestamps[0], db)
    )
    last_reset = results[0]
    operation_hours = (datetime.now(timezone.utc) - last_reset).total_seconds() / 3600

    energy_consumption = await _calculate_energy_consumption(power, timestamps)
    efficiency_score = await _calculate_efficiency_score(results[1], operation_hours, power)

    return {
        "last_reset": last_reset,
        "operation_hours": operation_hours,
        "energy_consumption": energy_consumption,
        "efficiency_score": efficiency_score
    }
