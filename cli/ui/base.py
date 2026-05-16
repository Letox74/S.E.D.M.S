from rich.console import Console
from rich.prompt import Confirm

console = Console()


def print_to_console(color: str, message: str) -> None:
    console.print(f"[{color}]{message}[/{color}]")


def confirm(question: str, default: bool = True, color: str = "white") -> bool:
    formatted_question = f"[{color}]{question}[/{color}]"
    return Confirm.ask(formatted_question, default=default)
