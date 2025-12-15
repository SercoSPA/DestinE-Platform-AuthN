"""
Exception classes and error handling utilities for destinepyauth.
"""

from functools import wraps
from typing import Callable, TypeVar, ParamSpec

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

P = ParamSpec("P")
T = TypeVar("T")


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


def handle_http_errors(error_message: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to handle common HTTP errors with a custom message.

    Args:
        error_message: Base error message to prepend to specific error details.

    Returns:
        Decorated function that raises AuthenticationError on HTTP failures.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Timeout:
                raise AuthenticationError(f"{error_message}: Connection timeout")
            except ConnectionError:
                raise AuthenticationError(f"{error_message}: Connection failed")
            except requests.HTTPError as e:
                status = e.response.status_code if e.response else "unknown"
                raise AuthenticationError(f"{error_message}: HTTP {status}")
            except RequestException as e:
                raise AuthenticationError(f"{error_message}: {e}")

        return wrapper

    return decorator
