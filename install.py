import shutil
import subprocess
import sys

try:
    from rich.console import Console
    from rich.panel import Panel

    use_rich = True

except ImportError, NameError:  # if rich is not installed
    use_rich = False


console = Console()


def check_command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _print_header() -> None:
    if use_rich:
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

    else:
        print()
        print("S.E.D.M.S Installation")
        print("Setting up your environment for S.E.D.M.S")
        print()


def _print_success() -> None:
    if use_rich:
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

    else:
        print()
        print("Installation completed successfully\n")
        print("From now on you can use sedms in your terminal")
        print("Type [bold cyan]sedms --help[/bold cyan] for more information")


def _print_called_process_error(e: subprocess.CalledProcessError) -> None:
    if use_rich:
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

    else:
        print()
        print("Installation failed")
        print(f"Details: \n{e.stderr or e.stdout}")


def _print_other_error(e: Exception) -> None:
    if use_rich:
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

    else:
        print()
        print(f"An unexpected error occurred: \n{e}")


def run_install() -> None:
    _print_header()

    # check for uv
    if check_command_exists("uv"):
        if use_rich:
            console.print("Found [bold cyan]uv[/bold cyan], using it for faster installation", justify="center")
        else:
            print("Found uv, using it for faster installation")

        cmd = ["uv", "pip", "install", "."]

    else:
        if use_rich:
            console.print("[bold cyan]uv[/bold cyan] not found, falling back to standard [bold cyan]pip[/bold cyan]", justify="center")
        else:
            print("uv not found, falling back to standard pip")

        cmd = [sys.executable, "-m", "pip", "install", "."]

    if use_rich:
        console.print("[bold white]Installing dependencies and packages, this might take a while...[/bold white]", justify="center")
    else:
        print("Installing dependencies and packages, this might take a while...")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        _print_success()

    except subprocess.CalledProcessError as e:
        _print_called_process_error(e)

    except Exception as e:
        _print_other_error(e)

    if use_rich:
        console.print()

    else:
        print()


if __name__ == "__main__":
    run_install()
