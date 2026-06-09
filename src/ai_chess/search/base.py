"""Abstract base class for search algorithms."""

from __future__ import annotations

from abc import ABC, abstractmethod

import chess

from ai_chess.engine.config import EngineConfig
from ai_chess.engine.metrics import SearchMetrics
from ai_chess.evaluation.evaluator import BasicEvaluator


class SearchAlgorithm(ABC):
    """Abstract base class that all search algorithms must implement.

    Search algorithms must:
    - Not mutate the board permanently (use push/pop).
    - Update SearchMetrics during the search.
    - Return None if the position has no legal moves.
    """

    @abstractmethod
    def find_best_move(
        self,
        board: chess.Board,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        metrics: SearchMetrics,
    ) -> chess.Move | None:
        """Find the best move for the current position.

        Args:
            board: The current chess board state.
            evaluator: The position evaluator to use at leaf nodes.
            config: Engine configuration (depth, time limits, etc.).
            metrics: Metrics object to update during the search.

        Returns:
            The best move found, or None if no legal moves exist.
        """
        ...
