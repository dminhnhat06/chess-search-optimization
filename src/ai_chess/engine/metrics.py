"""Search metrics dataclass for collecting performance data."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class SearchMetrics:
    """Metrics collected during a search operation.

    Used by all search algorithms to record performance statistics
    such as nodes searched, cutoffs, and elapsed time.
    """

    nodes_searched: int = 0
    qnodes_searched: int = 0
    cutoffs: int = 0
    beta_cutoffs: int = 0
    tt_probes: int = 0
    tt_hits: int = 0
    tt_stores: int = 0
    depth_reached: int = 0
    seldepth: int | None = None
    elapsed_seconds: float = 0.0
    best_move: str | None = None
    score: int | None = None
    completed: bool = True
    stopped_early: bool = False
    stop_reason: str | None = None

    def reset(self) -> None:
        """Reset all metrics to their default values."""
        self.nodes_searched = 0
        self.qnodes_searched = 0
        self.cutoffs = 0
        self.beta_cutoffs = 0
        self.tt_probes = 0
        self.tt_hits = 0
        self.tt_stores = 0
        self.depth_reached = 0
        self.seldepth = None
        self.elapsed_seconds = 0.0
        self.best_move = None
        self.score = None
        self.completed = True
        self.stopped_early = False
        self.stop_reason = None

    def to_dict(self) -> dict[str, object]:
        """Convert metrics to a dictionary for serialization or logging."""
        return asdict(self)
