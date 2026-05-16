import argparse
import asyncio
import inspect

from cli.main_cli import setup_cli


async def main() -> None:
    parser = argparse.ArgumentParser(prog="sedms", description="The CLI Tool for S.E.D.M.S")

    setup_cli(parser)

    args = parser.parse_args()
    if hasattr(args, "func"):
        if inspect.iscoroutinefunction(args.func):
            await args.func(args)
        else:
            args.func(args)

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())  # run the cli
