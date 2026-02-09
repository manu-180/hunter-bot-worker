"""
Retry utilities with exponential backoff for HunterBot.

Provides a reusable async retry mechanism for API calls,
database operations, and other potentially transient failures.
"""

import asyncio
from typing import Any, Callable, Optional, Tuple, Type


async def retry_with_backoff(
    coro_func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    **kwargs: Any,
) -> Any:
    """
    Execute an async function with exponential backoff retry.

    Args:
        coro_func: Async function to execute
        *args: Positional arguments for coro_func
        max_retries: Maximum number of retries (0 = no retries)
        base_delay: Base delay in seconds (doubles each retry)
        max_delay: Maximum delay cap in seconds
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback(exception, attempt_number) on each retry
        **kwargs: Keyword arguments for coro_func

    Returns:
        Result of the function call

    Raises:
        The last exception if all retries are exhausted
    """
    last_exception: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            if on_retry:
                on_retry(e, attempt + 1)
            await asyncio.sleep(delay)
    raise last_exception  # type: ignore[misc]
