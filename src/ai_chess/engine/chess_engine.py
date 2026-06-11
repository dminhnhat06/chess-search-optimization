"""Chess engine - orchestrates search, evaluation, and metrics collection."""

from __future__ import annotations

import chess

from ai_chess.engine.config import EngineConfig
from ai_chess.engine.metrics import SearchMetrics
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.search.base import SearchAlgorithm

# Engine identity constants used by the UCI protocol layer.
ENGINE_NAME = "AI Chess"
ENGINE_AUTHOR = "AI Chess Research"


class ChessEngine:
    """High-level chess engine that coordinates search and evaluation.

    The engine is configured with a search algorithm, an evaluator,
    and an engine configuration. It manages metrics lifecycle and
    delegates the actual search to the configured algorithm.
    """

    # ------------------------------------------------------------------
    # Identity properties (used by UCI 'id' response)
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the engine name for UCI identification."""
        return ENGINE_NAME

    @property
    def author(self) -> str:
        """Return the engine author for UCI identification."""
        return ENGINE_AUTHOR

    def __init__(
        self,
        search_algorithm: SearchAlgorithm,
        evaluator: BasicEvaluator | None = None,
        config: EngineConfig | None = None,
    ) -> None:
        """Initialize the chess engine.

        Args:
            search_algorithm: The search algorithm to use (e.g., MinimaxSearch).
            evaluator: The board evaluator. Defaults to BasicEvaluator.
            config: Engine configuration. Defaults to EngineConfig().
        """
        self.search_algorithm = search_algorithm
        self.evaluator = evaluator or BasicEvaluator()
        self.config = config or EngineConfig()

    def find_best_move(
        self, board: chess.Board
    ) -> tuple[chess.Move | None, SearchMetrics]:
        """Find the best move for the given board position.

        Creates fresh metrics for each search, delegates to the configured
        search algorithm, and returns the result.

        Args:
            board: The current chess board state.

        Returns:
            A tuple of (best_move, search_metrics). best_move is None
            if no legal moves exist.
        """
        metrics = SearchMetrics()
        best_move = self.search_algorithm.find_best_move(
            board, self.evaluator, self.config, metrics
        )
        return best_move, metrics

    def new_game(self) -> None:
        """Reset engine state for a new game.

        Called by the UCI layer in response to 'ucinewgame'. Clears
        any cached data (e.g., transposition tables) so the next
        search starts fresh.
        """
        # Future: clear transposition table, killer moves, history, etc.
        pass
