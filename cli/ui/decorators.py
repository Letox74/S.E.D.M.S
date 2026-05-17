import functools
import inspect
import traceback
from typing import Any, Callable, Coroutine

from rich.console import Console
from rich.status import Status

from cli.utils import api_client


def is_api_online(func: Callable) -> Any:
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if (await api_client.async_request("GET", "/online")).is_success:
                kwargs["is_api_online"] = True

            else:
                kwargs["is_api_online"] = False

            return await func(*args, **kwargs)

    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if api_client.sync_request("GET", "/online").is_success:
                kwargs["is_api_online"] = True

            else:
                kwargs["is_api_online"] = False

            return func(*args, **kwargs)

    return wrapper


def bypass_error_handling(func: Callable) -> Callable:
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                setattr(e, "__bypass_error_handling__", True)
                raise e

    else:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                setattr(e, "__bypass_error_handling__", True)
                raise e

    return wrapper


def _handle_exception(e: Exception, show_error: bool, show_full_error: bool) -> None:
    if getattr(e, "__bypass_error_handling__", False):
        raise e

    console = Console()
    if show_error:
        msg = "".join(traceback.format_exception(type(e), e, e.__traceback__)) if show_full_error \
            else "".join(traceback.format_exception_only(type(e), e)).strip()
        console.print(f"[bold red]Error:[/bold red]\n{msg}")
    else:
        console.print("[bold red]Oops, an error occurred[/bold red]")


def handle_error(show_full_error: bool = True, show_error: bool = True) -> Callable | Coroutine:
    def decorator(func: Callable) -> Callable | Coroutine:
        if getattr(func, "__bypass_error_handling__", False):
            return func

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> Any | None:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    _handle_exception(e, show_error, show_full_error)

        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any | None:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    _handle_exception(e, show_error, show_full_error)

        return wrapper

    return decorator


def spinner(message: str) -> Callable | Coroutine:
    def decorator(func: Callable) -> Callable | Coroutine:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                with Status(f"[bold cyan]{message}[/bold cyan]", spinner="arc"):
                    return await func(*args, **kwargs)


        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                with Status(f"[bold cyan]{message}[/bold cyan]", spinner="dots"):
                    return func(*args, **kwargs)

        return wrapper

    return decorator
