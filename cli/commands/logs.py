import argparse
from collections import deque
from pathlib import Path

from cli.ui.base import print_to_console, confirm
from cli.ui.decorators import handle_error

LOG_DIR = Path(__file__).parent.parent.parent.resolve() / "logs"

LOG_TYPES = ["analytics", "api", "app", "error", "ml", "telemetry"]


@handle_error(show_full_error=False)
def setup_logs_cli(subparsers: argparse._SubParsersAction) -> None:
    # setup parser and subparsers
    logs_parser = subparsers.add_parser("logs", help="Manage the logs files")
    logs_sub = logs_parser.add_subparsers(title="Logs commands")

    # define clear parser + default func
    clear_parser = logs_sub.add_parser("clear", help="Clears the log files")
    clear_parser.set_defaults(func=_clear_logs)

    # define view parser + arguments + default func
    view_parser = logs_sub.add_parser("view", help="View the last n-rows in a log file")
    view_parser.add_argument("--n-rows", dest="rows", default=10, type=int, help="How many rows to view")
    view_parser.add_argument("--log-file", choices=LOG_TYPES, required=True, help="Which log file")
    view_parser.set_defaults(func=_view_last_n_rows)


def _clear_logs(args) -> None:
    if not confirm("Are you sure you wan't to delete your logs?"):  # confirm to clear all log files
        print_to_console("white", "Clearing the logs was canceled")
        return

    for log_type in LOG_TYPES:
        current_log_file = (LOG_DIR / log_type).with_suffix(".log")
        with open(current_log_file, "w"):
            pass  # open in write mode automaticly clears the file
        print_to_console("red", f"{log_type.capitalize()} logs cleared")


def _view_last_n_rows(args) -> None:
    log_path = (LOG_DIR / args.log_file).with_suffix(".log")

    with open(log_path, "r", encoding="utf-8") as log_file:
        lines = list(deque(log_file, maxlen=args.rows))  # automaticly get only the last n rows

    if not lines:
        print_to_console("white", f"The log file {args.log_file} is empty")
        return

    print_to_console("white", f"Last {args.rows}  lines of {args.log_file}: \n{"".join(lines)}")
