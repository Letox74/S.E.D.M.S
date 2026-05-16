import shutil
import subprocess
import sys

from rich.console import Console
from rich.panel import Panel

console = Console()


def check_command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _print_header() -> None:
    # header
    console.print()
    console.print(
        Panel(
            "[bold magenta]S.E.D.M.S Installation[/bold magenta]\n"
            "[dim]Setting up your environment for S.E.D.M.S[/dim]",
            border_style="cyan",
            expand=False,
        ),
        justify="center",
    )
    console.print()


def _print_success() -> None:
    console.print()
    console.print(
        Panel(
            "[bold green]Installation completed successfully[/bold green]\n\n"
            "From now on you can use [bold magenta]sedms[/bold magenta] in your terminal\n"
            "Type [bold cyan]sedms --help[/bold cyan] for more information",
            title="[bold green]Success[/bold green]",
            border_style="green",
            expand=False
        ),
        justify="center"
    )


def _print_called_process_error(e: subprocess.CalledProcessError) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold red]Installation failed[/bold red]\n\n"
            f"[bold error]Details:[/bold error]\n{e.stderr or e.stdout}",
            title="[bold red]Error[/bold red]",
            border_style="red",
            expand=False
        ),
        justify="center"
    )


def _print_other_error(e: Exception) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold red]An unexpected error occurred:[/bold red]\n{e}",
            title="[bold red]Error[/bold red]",
            border_style="red",
            expand=False
        ),
        justify="center"
    )


def run_install() -> None:
    _print_header()

    # check for uv
    if check_command_exists("uv"):
        console.print("Found [bold cyan]uv[/bold cyan], using it for faster installation", justify="center")
        cmd = ["uv", "pip", "install", "."]

    else:
        console.print("[bold cyan]uv[/bold cyan] not found, falling back to standard [bold cyan]pip[/bold cyan]", justify="center")
        cmd = [sys.executable, "-m", "pip", "install", "."]

    console.print("[bold white]Installing dependencies and packages...[/bold white]", justify="center")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        _print_success()

    except subprocess.CalledProcessError as e:
        _print_called_process_error(e)

    except Exception as e:
        _print_other_error(e)

    console.print()


if __name__ == "__main__":
    run_install()
