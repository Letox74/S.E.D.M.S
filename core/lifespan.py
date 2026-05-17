import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.connection import DatabaseManager
from .config import settings

app_logger = logging.getLogger("App")
error_logger = logging.getLogger("Error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # inizialize the database manager class an put it in the app.state
    db_manager = DatabaseManager(settings.db.path)
    await db_manager.connect()
    await db_manager.initialize_schema()

    app.state.db_manager = db_manager
    app_logger.info("Application startup complete")

    yield

    # after the shutdown disconnect from the database
    await db_manager.disconnect()
    app_logger.info("Application shutdown completed successfully")
