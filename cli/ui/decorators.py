import functools
import inspect
import traceback
from typing import Any, Callable, Coroutine

import rich

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


def _handle_exception(e: Exception, show_error: bool, show_full_error: bool) -> None:
    console = rich.Console()
    if show_error:
        msg = str(e) if show_full_error else "".join(traceback.format_exception_only(type(e), e)).strip()
        console.print(f"[bold red]Error:[/bold red]\n{msg}")
    else:
        console.print("[bold red]Oops, an error occurred[/bold red]")


def handle_error(show_full_error: bool = True, show_error: bool = True) -> Callable | Coroutine:
    def decorator(func: Callable) -> Callable | Coroutine:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any | None:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    _handle_exception(e, show_error, show_full_error)

            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any | None:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    _handle_exception(e, show_error, show_full_error)

            return sync_wrapper
    return decorator


def spinner(message: str) -> Callable | Coroutine:
    def decorator(func: Callable) -> Callable | Coroutine:
        console = rich.Console()

        if inspect.iscoroutinefunction(func):
            @handle_error(show_full_error=False)
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                with console.status(f"[bold blue]{message}[/bold blue]", spinner="dots"):
                    return await func(*args, **kwargs)


        else:
            @handle_error(show_full_error=False)
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                with console.status(f"[bold blue]{message}[/bold blue]", spinner="dots"):
                    return func(*args, **kwargs)


        return wrapper
    return decorator
