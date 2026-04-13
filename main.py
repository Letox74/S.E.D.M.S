from fastapi import FastAPI

from core.lifespan import lifespan
from core.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="S.E.D.M.S",
    summary="Smart Energy & Device Management System",
    version="0.1.0",
    lifespan=lifespan
)
