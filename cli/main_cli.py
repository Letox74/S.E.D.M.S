import argparse

from core.config import settings
from .commands.analytics import setup_analytics_cli
from .commands.db import setup_db_cli
from .commands.devices import setup_devices_cli
from .commands.logs import setup_logs_cli
from .commands.ml import setup_ml_cli
from .commands.other import setup_other_cli
from .commands.run import setup_run_cli
from .commands.security import setup_security_cli
from .commands.telemetry import setup_telemetry_cli


def setup_cli(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-v", "--version", action="version", version=f"Current S.E.D.M.S version: {settings.version}")
    # define version argument here, because it doesn't need a subparser

    # add subparsers from the main parser
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Available categories",
        required=True
    )

    # setup all the cli commands
    setup_analytics_cli(subparsers)
    setup_db_cli(subparsers)
    setup_devices_cli(subparsers)
    setup_logs_cli(subparsers)
    setup_ml_cli(subparsers)
    setup_other_cli(subparsers)
    setup_run_cli(subparsers)
    setup_security_cli(subparsers)
    setup_telemetry_cli(subparsers)
