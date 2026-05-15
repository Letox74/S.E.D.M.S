import argparse

from cli.main_cli import setup_cli


def main() -> None:
    parser = argparse.ArgumentParser(prog="sedms", description="The CLI Tool for S.E.D.M.S")

    setup_cli(parser)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()  # run the cli
