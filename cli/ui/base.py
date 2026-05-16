from typing import overload, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

@overload
def print_to_console(*, custom: str, print_whitespace: bool = False) -> None: ...


@overload
def print_to_console(color: str, message: str, print_whitespace: bool = False) -> None: ...


def print_to_console(
        color: Optional[str] = None,
        message: Optional[str] = None,
        *,
        custom: Optional[str] = None,
        print_whitespace: bool = False
) -> None:
    if print_whitespace:
        console.print()

    if custom is not None:
        console.print(custom)

    else:
        console.print(f"[{color}]{message}[/{color}]")


def print_panel(
        message: str,
        title: Optional[str] = None,
        box: Optional[box.Box] = box.ROUNDED,
        border_style: str = "none",
        padding: tuple[int, int] = (0, 1),  # first element is padding top to bottom and second element left and right
        expand: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        print_whitespace: bool = False
) -> None:
    if print_whitespace:
        console.print()

    console.print(
        Panel(
            message,
            title=title,
            box=box,
            title_align="left",
            border_style=border_style,
            padding=padding,
            expand=expand,
            width=width,
            height=height
        )
    )


def confirm(question: str, default: bool = True, color: str = "white", print_whitespace: bool = False) -> bool:
    if print_whitespace:
        console.print()

    formatted_question = f"[{color}]{question}[/{color}]"
    return Confirm.ask(formatted_question, default=default)
