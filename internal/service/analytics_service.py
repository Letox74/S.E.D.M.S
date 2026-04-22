import logging

from database.connection import DatabaseManager
from internal.schemas.analytic_models import AnalyticsCreate, AnalyticsRead

analytics_logger = logging.getLogger("Analytics")


async def insert_new_analytic(data: AnalyticsCreate, db: DatabaseManager) -> AnalyticsRead:
    fields = data.model_dump()  # to not type it manually

    # prepare sql string
    colums = ", ".join(f"{key}" for key in fields.keys())
    placeholders = ", ".join("?" for _ in fields)
    values = tuple(fields.values())

    sql = f"""
        INSERT INTO analytics
        ({colums})
        VALUES ({placeholders})
        RETURNING *;
    """
    row = await db.execute_transaction(sql, values)  # retrieve the entire row (due to RETURNING *)
    analytics_logger.info(f"Received new Analytics Data from Device {fields["device_id"]}")

    return AnalyticsRead(**dict(row))
