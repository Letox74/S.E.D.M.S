import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Never

import aiosqlite

from .models_sql import CREATE_DEVICES_SQL, CREATE_TELEMETRY_SQL, CREATE_ANALYTICS_SQL, CREATE_PREDICTIONS_SQL

SCHEMAS = [CREATE_DEVICES_SQL, CREATE_TELEMETRY_SQL, CREATE_ANALYTICS_SQL, CREATE_PREDICTIONS_SQL]

error_logger = logging.getLogger("Error")
app_logger = logging.getLogger("App")

def _adapt_datetime_utc(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode()).replace(tzinfo=timezone.utc)

class DatabaseManager:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None

        sqlite3.register_converter("DATETIME", _adapt_datetime_utc)

    async def connect(self) -> None:
        try:
            self._connection = await aiosqlite.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            self._connection.row_factory = aiosqlite.Row  # enable Row factory to access columns by name

            # WAL Mode, Foreign Keys and auto indexing activation
            await self._connection.execute("PRAGMA journal_mode = WAL;")
            await self._connection.execute("PRAGMA foreign_keys = ON;")
            await self._connection.execute("PRAGMA automatic_index = 1;")
            await self._connection.commit()

            app_logger.info(f"Connected to database at {self.db_path}")

        except Exception as e:
            error_logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()  # close connection
            app_logger.info("Database connection closed")

    async def fetch_all(self, query: str, params: tuple = ()) -> list[aiosqlite.Row] | list[Never]:
        try:
            async with self._connection.execute(query, params) as cursor:
                return await cursor.fetchall()

        except Exception as e:
            error_logger.error(f"Fetch all failed: {e}")
            return []

    async def fetch_one(self, query: str, params: tuple = ()) -> aiosqlite.Row | None:
        try:
            async with self._connection.execute(query, params) as cursor:
                return await cursor.fetchone()

        except Exception as e:
            error_logger.error(f"Fetch one failed: {e}")
            return None

    async def execute_transaction(self, query: str, params: tuple = ()) -> aiosqlite.Row | int:
        # this function is used for INSERT/UPDATE or DELETE
        try:
            if "RETURNING" in query:  # when something needs to be returned from the row after execution
                async with self._connection.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    await self._connection.commit()

                    return row

            async with self._connection.execute(query, params) as cursor:
                row_count = cursor.rowcount # how many rows were deleted, updated or inserted
                self._connection.commit()

                return row_count

        except Exception as e:
            await self._connection.rollback()  # rollback() reverts all changes since last commit
            error_logger.error(f"Transaction failed, rolled back: {e}")
            raise

    async def initialize_schema(self) -> None:
        try:
            for schema in SCHEMAS:
                await self._connection.executescript(schema)

            await self._connection.commit()  # to create the tables (schema found here: database/models_sql.py)

        except Exception as e:
            error_logger.error(f"Schema initialization failed: {e}")
            raise