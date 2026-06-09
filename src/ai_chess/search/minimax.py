"""Minimax search algorithm implementation."""

from __future__ import annotations

import time

import chess

from ai_chess.engine.config import EngineConfig
from ai_chess.engine.metrics import SearchMetrics
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.search.base import SearchAlgorithm


class MinimaxSearch(SearchAlgorithm):
    """Depth-limited minimax search without any optimizations.

    This is the V0 baseline search algorithm. White maximizes the
    evaluation score and Black minimizes it. The evaluator is called
    at leaf nodes (depth == 0 or terminal positions).
    """

    def find_best_move(
        self,
        board: chess.Board,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        metrics: SearchMetrics,
    ) -> chess.Move | None:
        """Find the best move using depth-limited minimax.

        Args:
            board: The current chess board state.
            evaluator: The position evaluator to use at leaf nodes.
            config: Engine configuration controlling search depth.
            metrics: Metrics object updated during the search.

        Returns:
            The best move found, or None if no legal moves exist.
        """
        start_time = time.perf_counter()

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_move: chess.Move | None = None
        is_maximizing = board.turn == chess.WHITE

        if is_maximizing:
            best_score = -float("inf")
            for move in legal_moves:
                board.push(move)
                score = self._minimax(
                    board, config.max_depth - 1, False, evaluator, metrics
                )
                board.pop()
                if score > best_score:
                    best_score = score
                    best_move = move
        else:
            best_score = float("inf")
            for move in legal_moves:
                board.push(move)
                score = self._minimax(
                    board, config.max_depth - 1, True, evaluator, metrics
                )
                board.pop()
                if score < best_score:
                    best_score = score
                    best_move = move

        elapsed = time.perf_counter() - start_time

        # Update metrics
        metrics.depth_reached = config.max_depth
        metrics.elapsed_seconds = elapsed
        metrics.best_move = best_move.uci() if best_move else None
        metrics.score = int(best_score) if best_move else None

        return best_move

    def _minimax(
        self,
        board: chess.Board,
        depth: int,
        is_maximizing: bool,
        evaluator: BasicEvaluator,
        metrics: SearchMetrics,
    ) -> float:
        """Recursive minimax evaluation.

        Args:
            board: The current chess board state.
            depth: Remaining depth to search.
            is_maximizing: True if the current player is maximizing (White).
            evaluator: The position evaluator.
            metrics: Metrics object to update.

        Returns:
            The evaluation score for this position.
        """
        metrics.nodes_searched += 1

        # Terminal or leaf node
        if depth == 0 or board.is_game_over():
            return evaluator.evaluate(board)

        legal_moves = list(board.legal_moves)

        if is_maximizing:
            max_score = -float("inf")
            for move in legal_moves:
                board.push(move)
                score = self._minimax(
                    board, depth - 1, False, evaluator, metrics
                )
                board.pop()
                if score > max_score:
                    max_score = score
            return max_score
        else:
            min_score = float("inf")
            for move in legal_moves:
                board.push(move)
                score = self._minimax(
                    board, depth - 1, True, evaluator, metrics
                )
                board.pop()
                if score < min_score:
                    min_score = score
            return min_score
