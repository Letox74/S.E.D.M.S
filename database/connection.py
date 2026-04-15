import logging
from pathlib import Path

import aiosqlite

from models_sql import CREATE_DEVICES_SQL, CREATE_TELEMETRY_SQL, CREATE_ANALYTICS_SQL, CREATE_PREDICTIONS_SQL

SCHEMAS = [CREATE_DEVICES_SQL, CREATE_TELEMETRY_SQL, CREATE_ANALYTICS_SQL, CREATE_PREDICTIONS_SQL]

error_logger = logging.getLogger("error")
app_logger = logging.getLogger("app")

class DatabaseManager:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = db_path
        self._connection = None

    async def connect(self) -> None:
        try:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row # enable Row factory to access columns by name

            # WAL Mode and Foreign Keys activation
            await self._connection.execute("PRAGMA journal_model=WAL;")
            await self._connection.execute("PRAGMA foreign_keys=ON;")
            await self._connection.commit()

            app_logger.info(f"Connected to database at {self.db_path}")

        except Exception as e:
            error_logger.error(f"Failed to connect to database: {e}")
            raise


    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close() # close connection
            app_logger.info("Database connection closed")


    async def fetch_all(self, query: str, params: tuple = ()):
        try:
            async with self._connection.execute(query, params) as cursor:
                return await cursor.fetchall() #

        except Exception as e:
            error_logger.error(f"Fetch all failed: {e}")
            return []

    async def fetch_one(self, query: str, params: tuple = ()):
        try:
            async with self._connection.execute(query, params) as cursor:
                return await cursor.fetchone()

        except Exception as e:
            error_logger.error(f"Fetch one failed: {e}")
            return None

    async def execute_transaction(self, query: str, params: tuple = ()):
        # this function is used or INSERT/UPDATE or DELETE
        try:
            await self._connection.execute(query, params)
            await self._connection.commit()

        except Exception as e:
            await self._connection.rollback() # rollback() reverts all changes since last commit
            error_logger.error(f"Transaction failed, rolled back: {e}")
            raise

    async def initialize_schema(self):
        try:
            for schema in SCHEMAS:
                await self._connection.executescript(schema)
            await self._connection.commit() # to create the tables (schema found here: database/models_sql.py)

        except Exception as e:
            error_logger.error(f"Schema initialization failed: {e}")
            raise