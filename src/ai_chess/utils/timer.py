"""Timer utility for measuring elapsed time."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator


@contextmanager
def elapsed_timer() -> Generator[dict[str, float], None, None]:
    """Context manager that measures elapsed wall-clock time.

    Usage::

        with elapsed_timer() as timer:
            # ... do work ...
        print(f"Took {timer['elapsed']:.3f} seconds")

    Yields:
        A dictionary with an 'elapsed' key that is updated
        with the elapsed time in seconds when the context exits.
    """
    result: dict[str, float] = {"elapsed": 0.0}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["elapsed"] = time.perf_counter() - start
