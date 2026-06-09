"""Search metrics dataclass for collecting performance data."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SearchMetrics:
    """Metrics collected during a search operation.

    Used by all search algorithms to record performance statistics
    such as nodes searched, cutoffs, and elapsed time.
    """

    nodes_searched: int = 0
    cutoffs: int = 0
    tt_hits: int = 0
    depth_reached: int = 0
    elapsed_seconds: float = 0.0
    best_move: str | None = None
    score: int | None = None

    def reset(self) -> None:
        """Reset all metrics to their default values."""
        self.nodes_searched = 0
        self.cutoffs = 0
        self.tt_hits = 0
        self.depth_reached = 0
        self.elapsed_seconds = 0.0
        self.best_move = None
        self.score = None

    def to_dict(self) -> dict[str, object]:
        """Convert metrics to a dictionary for serialization or logging."""
        return {
            "nodes_searched": self.nodes_searched,
            "cutoffs": self.cutoffs,
            "tt_hits": self.tt_hits,
            "depth_reached": self.depth_reached,
            "elapsed_seconds": self.elapsed_seconds,
            "best_move": self.best_move,
            "score": self.score,
        }
