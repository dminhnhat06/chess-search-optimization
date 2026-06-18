"""Abstract base class for search algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ai_chess.engine.result import SearchResult

if TYPE_CHECKING:
    import chess

    from ai_chess.engine.config import EngineConfig
    from ai_chess.engine.limits import SearchLimits
    from ai_chess.engine.metrics import SearchMetrics
    from ai_chess.evaluation.evaluator import BasicEvaluator


class SearchStoppedError(Exception):
    """Raised internally when a search limit is reached."""

    def __init__(
        self,
        best_move: chess.Move | None = None,
        score: int | None = None,
        pv: list[chess.Move] | None = None,
    ) -> None:
        super().__init__("search stopped")
        self.best_move = best_move
        self.score = score
        self.pv = pv or []


class SearchAlgorithm(ABC):
    """Abstract base class that all search algorithms must implement.

    Search algorithms must:
    - Not mutate the board permanently (use push/pop).
    - Update SearchMetrics during the search.
    - Return None if the position has no legal moves.
    """

    name = "base"

    @abstractmethod
    def search(
        self,
        board: chess.Board,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        limits: SearchLimits,
    ) -> SearchResult:
        """Search the current position and return a structured result.

        Args:
            board: The current chess board state.
            evaluator: The position evaluator to use at leaf nodes.
            config: Engine configuration.
            limits: Per-search limits.

        Returns:
            Structured search result.
        """
        ...

    def reset(self) -> None:
        """Reset any algorithm-local state."""
        return None


def stable_legal_moves(board: chess.Board) -> list[chess.Move]:
    """Return legal moves in deterministic UCI-string order."""
    return sorted(board.legal_moves, key=lambda move: move.uci())


def finalize_result(
    *,
    best_move: chess.Move | None,
    score: int | None,
    depth: int,
    pv: list[chess.Move],
    metrics: SearchMetrics,
    elapsed_seconds: float,
) -> SearchResult:
    """Build a result object and synchronize common metric fields."""
    metrics.depth_reached = depth
    metrics.elapsed_seconds = elapsed_seconds
    metrics.best_move = best_move.uci() if best_move is not None else None
    metrics.score = score

    elapsed_ms = int(elapsed_seconds * 1000)
    total_nodes = metrics.nodes_searched + metrics.qnodes_searched
    nps = int(total_nodes / elapsed_seconds) if elapsed_seconds > 0 else 0

    return SearchResult(
        best_move=best_move,
        score_cp=score,
        depth=depth,
        seldepth=metrics.seldepth,
        nodes=total_nodes,
        nps=nps,
        elapsed_ms=elapsed_ms,
        pv=pv,
        metrics=metrics,
    )
