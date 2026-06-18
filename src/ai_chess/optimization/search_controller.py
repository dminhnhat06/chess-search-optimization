"""Reusable search stopping controller."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import chess

if TYPE_CHECKING:
    from ai_chess.engine.limits import SearchLimits


class SearchController:
    """Tracks elapsed time, node limits, and early stop state."""

    def __init__(
        self,
        limits: SearchLimits,
        move_overhead_ms: int = 20,
        side_to_move: chess.Color | None = None,
    ) -> None:
        self.limits = limits
        self.move_overhead_ms = max(0, move_overhead_ms)
        self.side_to_move = side_to_move
        self.start_time = time.perf_counter()
        self.stop_reason: str | None = None
        self._deadline = self._compute_deadline()

    def should_stop(self) -> bool:
        """Return True when the active time limit has expired."""
        if self._deadline is None:
            return False
        if time.perf_counter() >= self._deadline:
            self.stop_reason = "time"
            return True
        return False

    def nodes_exceeded(self, nodes: int) -> bool:
        """Return True when the node limit has been reached."""
        if self.limits.nodes is None:
            return False
        if nodes >= self.limits.nodes:
            self.stop_reason = "nodes"
            return True
        return False

    def elapsed_seconds(self) -> float:
        """Return elapsed wall-clock search time in seconds."""
        return time.perf_counter() - self.start_time

    def elapsed_ms(self) -> int:
        """Return elapsed wall-clock search time in milliseconds."""
        return int(self.elapsed_seconds() * 1000)

    def _compute_deadline(self) -> float | None:
        budget_ms = self._time_budget_ms()
        if budget_ms is None:
            return None
        usable_ms = max(0, budget_ms - self.move_overhead_ms)
        return self.start_time + (usable_ms / 1000)

    def _time_budget_ms(self) -> int | None:
        if self.limits.infinite:
            return None

        if self.limits.movetime_ms is not None:
            return self.limits.movetime_ms

        if self.side_to_move is None:
            return None

        remaining = (
            self.limits.wtime_ms
            if self.side_to_move == chess.WHITE
            else self.limits.btime_ms
        )
        if remaining is None:
            return None

        increment = (
            self.limits.winc_ms
            if self.side_to_move == chess.WHITE
            else self.limits.binc_ms
        ) or 0
        moves = max(1, self.limits.movestogo or 30)
        allocated = int(remaining / moves + increment * 0.5)
        return max(0, allocated)
