import argparse

from commands.analytics import setup_analytics_cli
from commands.db import setup_db_cli
from commands.devices import setup_devices_cli
from commands.logs import setup_logs_cli
from commands.ml import setup_ml_cli
from commands.other import setup_other_cli
from commands.run import setup_run_cli
from commands.security import setup_security_cli
from commands.telemetry import setup_telemetry_cli


def setup_cli(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Available categories",
        required=True
    )

    setup_analytics_cli(subparsers)
    setup_db_cli(subparsers)
    setup_devices_cli(subparsers)
    setup_logs_cli(subparsers)
    setup_ml_cli(subparsers)
    setup_other_cli(subparsers)
    setup_run_cli(subparsers)
    setup_security_cli(subparsers)
    setup_telemetry_cli(subparsers)
