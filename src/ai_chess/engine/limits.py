"""Search limit data passed into the reusable engine core."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchLimits:
    """Constraints for one independent search call.

    These fields mirror common engine/UCI limits without coupling the core
    engine to UCI or any other caller. When ``infinite`` is true, time fields
    are ignored by the core search controller; an explicit node limit still
    applies.
    """

    depth: int | None = None
    movetime_ms: int | None = None
    nodes: int | None = None
    wtime_ms: int | None = None
    btime_ms: int | None = None
    winc_ms: int | None = None
    binc_ms: int | None = None
    movestogo: int | None = None
    infinite: bool = False

    def __post_init__(self) -> None:
        """Validate non-negative numeric limits."""
        if self.depth is not None and self.depth < 1:
            raise ValueError(f"depth must be >= 1 when provided, got {self.depth}")

        for field_name in (
            "movetime_ms",
            "nodes",
            "wtime_ms",
            "btime_ms",
            "winc_ms",
            "binc_ms",
            "movestogo",
        ):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must be non-negative, got {value}")
