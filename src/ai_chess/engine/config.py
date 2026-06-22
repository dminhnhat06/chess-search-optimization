"""Engine configuration dataclass."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EngineConfig:
    """Configuration for the chess engine.

    Controls default limits and optional feature switches consumed by search
    algorithms. It does not instantiate or select the search algorithm; that is
    controlled by ``ChessEngine.search_algorithm`` or by the preset factory.
    """

    max_depth: int = 3
    time_limit_seconds: float | None = None

    use_move_ordering: bool = False
    use_transposition_table: bool = False
    use_quiescence: bool = False

    hash_size_mb: int = 64
    quiescence_max_depth: int = 8
    move_overhead_ms: int = 20

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
        if self.hash_size_mb < 0:
            raise ValueError(
                f"hash_size_mb must be non-negative, got {self.hash_size_mb}"
            )
        if self.quiescence_max_depth < 0:
            raise ValueError(
                "quiescence_max_depth must be non-negative, "
                f"got {self.quiescence_max_depth}"
            )
        if self.move_overhead_ms < 0:
            raise ValueError(
                f"move_overhead_ms must be non-negative, got {self.move_overhead_ms}"
            )
