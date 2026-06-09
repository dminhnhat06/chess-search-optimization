"""Engine configuration dataclass."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EngineConfig:
    """Configuration for the chess engine.

    Controls search depth, time limits, and which optimizations are enabled.
    """

    max_depth: int = 3
    time_limit_seconds: float | None = None
    use_move_ordering: bool = False
    use_transposition_table: bool = False
    use_quiescence: bool = False

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        if self.max_depth < 1:
            raise ValueError(
                f"max_depth must be >= 1, got {self.max_depth}"
            )
        if self.time_limit_seconds is not None and self.time_limit_seconds <= 0:
            raise ValueError(
                f"time_limit_seconds must be positive or None, "
                f"got {self.time_limit_seconds}"
            )
