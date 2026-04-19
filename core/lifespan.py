import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.connection import DatabaseManager
from .config import DB_PATH

app_logger = logging.getLogger("App")
error_logger = logging.getLogger("Error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager = DatabaseManager(DB_PATH)
    await db_manager.connect()
    await db_manager.initialize_schema()

    app.state.db_manager = db_manager
    app_logger.info("Application startup complete")

    yield

    await db_manager.disconnect()
    app_logger.info("Application shutdown completed successfully")
