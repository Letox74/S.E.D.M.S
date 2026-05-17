import argparse

from cli.ui.base import print_panel
from internal.security import generate_new_api_key


def setup_security_cli(subparsers: argparse._SubParsersAction) -> None:
    security_parser = subparsers.add_parser("security", help="Security functions")  # define a parser for security

    # add arguments
    security_parser.add_argument("--gen-api-key", action="store_true", help="Generate a new API key")

    security_parser.set_defaults(func=_handle_generate_new_key)  # set func to handle the input


def _handle_generate_new_key(args) -> None:
    if args.gen_api_key:
        new_key = generate_new_api_key()

        print_panel(new_key, title="New API key generated", border_style="green")
