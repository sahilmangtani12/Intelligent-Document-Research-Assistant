import logging
import time
from typing import Callable, TypeVar

T = TypeVar("T")
log = logging.getLogger(__name__)


def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    should_retry: Callable[[Exception], bool] = lambda _: True,
) -> T:
    """Call fn, retrying with exponential backoff while should_retry(exc) is true."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - provider SDKs raise many error types
            if attempt == attempts or not should_retry(exc):
                raise
            delay = base_delay * (2 ** (attempt - 1))
            log.warning("Attempt %d/%d failed (%s); retrying in %.1fs", attempt, attempts, exc, delay)
            time.sleep(delay)
    raise RuntimeError("unreachable")
