import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from cli.ui.base import print_to_console
from cli.ui.decorators import handle_error, bypass_error_handling
from core.config import settings

BASE_DIR = Path(__file__).parent.parent.parent.resolve()


class VenvNotActiveError(Exception): pass

class InvalidRateLimitFormat(Exception): pass

class SamePortError(Exception): pass


def setup_run_cli(subparsers: argparse._SubParsersAction) -> None:
    run_parser = subparsers.add_parser("run", help="Starts the API Server and the website")

    run_parser.add_argument("--no-frontend", dest="frontend", action="store_false", help="Deactivate the frontend")
    run_parser.add_argument("--no-rate-limits", dest="rate_limits", action="store_false",
                            help="Deactivate the rate limits for the API")
    run_parser.add_argument("--with-cors", dest="cors", action="store_true", help="If CORS should be activated")
    run_parser.add_argument("--rate-limit", type=str, help="Set a specific rate limit")
    run_parser.add_argument("--host", type=str, help="Set a specific host")
    run_parser.add_argument("--api-port", type=int, help="Set the API Port")
    run_parser.add_argument("--frontend-port", type=int, help="Set the frontend Port")
    run_parser.add_argument("--dev", action="store_true", help="Starts Uvicorn with --reload")

    run_parser.set_defaults(func=_start_severs)


@bypass_error_handling
def _validate_input(args) -> None:
    if args.rate_limit:
        pattern = r"^\d+\s*(?:per|\/)\s*\d*\s*(?:second|minute|hour|day)s?$"
        if not re.match(pattern, args.rate_limit.strip()):
            raise InvalidRateLimitFormat(f"Invalid rate limit format: '{args.rate_limit}'. "
                                         "Please use a valid format such as '5 per minute', '100/day', or '10 per 2 hours'")

    api_port = args.api_port or settings.api.port
    frontend_port = args.frontend_port or settings.frontend.port

    if api_port == frontend_port:
        raise SamePortError("The API Port and the frontend port cannot be the same")


def _insert_input_into_settings(args) -> None:
    if args.rate_limits is False:
        settings.api.activate_rate_limits = False

    if args.cors:
        settings.api.cors.use_cors = True

    if args.rate_limit:
        settings.api.default_rate_limits = args.rate_limit

    if args.host:
        settings.host = args.host

    if args.api_port:
        settings.api.port = args.api_port

    if args.frontend_port:
        settings.frontend.port = args.frontend_port


@bypass_error_handling
def _check_venv() -> None:
    if Path("/.dockerenv").exists():
        return

    is_venv = "VIRTUAL_ENV" in os.environ or sys.prefix != sys.base_prefix

    if not is_venv:
        raise VenvNotActiveError("Please activate your virtual enviroment first")


def _get_streamlit_cmd(args) -> list[str]:
    base_cmd = [sys.executable, "-m", "streamlit", "run", "frontend/Dashboard.py"]
    base_cmd.extend(["--server.address", str(settings.host)])
    base_cmd.extend(["--server.port", str(settings.frontend.port)])

    return base_cmd


def _get_uvicorn_cmd(args) -> list[str]:
    base_cmd = [sys.executable, "-m", "uvicorn", "main_api:app"]
    base_cmd.extend(["--host", str(settings.host)])
    base_cmd.extend(["--port", str(settings.api.port)])

    if args.dev:
        base_cmd.append("--reload")

    return base_cmd


@handle_error()
def _start_severs(args) -> None:
    _validate_input(args)
    _insert_input_into_settings(args)
    _check_venv()

    processes = []
    print_to_console("white", f"Starting {"Servers" if args.frontend else "Server"}...")

    # start streamlit
    if args.frontend:
        streamlit_process = subprocess.Popen(
            _get_streamlit_cmd(args),
            cwd=BASE_DIR,
            stdout=None,
            stderr=None
        )
        processes.append(streamlit_process)

    # start uvicorn
    uvicorn_process = subprocess.Popen(
        _get_uvicorn_cmd(args),
        cwd=BASE_DIR,
        stdout=None,
        stderr=None
    )
    processes.append(uvicorn_process)

    print_to_console("white", f"{"Servers are" if args.frontend else "Server is"} online. Press Ctrl+C to stop")

    try:
        while True:
            if args.frontend:
                if streamlit_process.poll() is not None:
                    print_to_console("bold red", "Streamlit unexpectedly crashed")
                    break

            if uvicorn_process.poll() is not None:
                print_to_console("bold red", "Uvicorn unexpectedly crashed")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print_to_console("white", f"Stopping the {"Servers" if args.frontend else "Server"}...")

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        time.sleep(1)
        for process in processes:
            if process.poll() is None:
                process.kill()

        print_to_console("green",
                         f"{"All Server processes" if args.frontend else "The Server process"} stopped successfully")
