"""Minimax search algorithm implementation."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import chess

from ai_chess.engine.metrics import SearchMetrics
from ai_chess.optimization.search_controller import SearchController
from ai_chess.search.base import (
    SearchAlgorithm,
    SearchStoppedError,
    finalize_result,
    stable_legal_moves,
)

if TYPE_CHECKING:
    from ai_chess.engine.config import EngineConfig
    from ai_chess.engine.limits import SearchLimits
    from ai_chess.engine.result import SearchResult
    from ai_chess.evaluation.evaluator import BasicEvaluator


class MinimaxSearch(SearchAlgorithm):
    """Depth-limited minimax search without any optimizations.

    This is the V0 baseline search algorithm. White maximizes the
    evaluation score and Black minimizes it. The evaluator is called
    at leaf nodes (depth == 0 or terminal positions).
    """

    name = "minimax"

    def search(
        self,
        board: chess.Board,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        limits: SearchLimits,
    ) -> SearchResult:
        """Find the best move using depth-limited minimax.

        Args:
            board: The current chess board state.
            evaluator: The position evaluator to use at leaf nodes.
            config: Engine configuration controlling default search depth.
            limits: Per-search constraints.

        Returns:
            Structured search result.
        """
        metrics = SearchMetrics()
        start_time = time.perf_counter()
        depth = limits.depth or config.max_depth
        controller = SearchController(limits, config.move_overhead_ms, board.turn)

        legal_moves = stable_legal_moves(board)
        if not legal_moves:
            metrics.nodes_searched = 1
            score = evaluator.evaluate(board)
            elapsed = time.perf_counter() - start_time
            return finalize_result(
                best_move=None,
                score=score,
                depth=0,
                pv=[],
                metrics=metrics,
                elapsed_seconds=elapsed,
            )

        best_move: chess.Move | None = legal_moves[0]
        best_pv: list[chess.Move] = [best_move]
        best_score = -float("inf") if board.turn == chess.WHITE else float("inf")
        is_maximizing = board.turn == chess.WHITE

        try:
            if is_maximizing:
                for move in legal_moves:
                    self._raise_if_stopped(controller, metrics)
                    board.push(move)
                    try:
                        score, child_pv = self._minimax(
                            board, depth - 1, evaluator, metrics, controller, 1
                        )
                    finally:
                        board.pop()
                    if score > best_score:
                        best_score = score
                        best_move = move
                        best_pv = [move, *child_pv]
            else:
                for move in legal_moves:
                    self._raise_if_stopped(controller, metrics)
                    board.push(move)
                    try:
                        score, child_pv = self._minimax(
                            board, depth - 1, evaluator, metrics, controller, 1
                        )
                    finally:
                        board.pop()
                    if score < best_score:
                        best_score = score
                        best_move = move
                        best_pv = [move, *child_pv]
        except SearchStoppedError:
            metrics.completed = False
            metrics.stopped_early = True
            metrics.stop_reason = controller.stop_reason or "stopped"
            if best_score in (float("inf"), -float("inf")):
                best_score = evaluator.evaluate(board)

        elapsed = time.perf_counter() - start_time
        return finalize_result(
            best_move=best_move,
            score=int(best_score),
            depth=0 if metrics.stopped_early else depth,
            pv=best_pv if best_move is not None else [],
            metrics=metrics,
            elapsed_seconds=elapsed,
        )

    def _minimax(
        self,
        board: chess.Board,
        depth: int,
        evaluator: BasicEvaluator,
        metrics: SearchMetrics,
        controller: SearchController,
        ply: int,
    ) -> tuple[float, list[chess.Move]]:
        """Recursive minimax evaluation."""
        metrics.nodes_searched += 1
        metrics.seldepth = max(metrics.seldepth or 0, ply)
        self._raise_if_stopped(controller, metrics)

        if depth <= 0 or board.is_game_over():
            return evaluator.evaluate(board), []

        legal_moves = stable_legal_moves(board)
        if not legal_moves:
            return evaluator.evaluate(board), []

        if board.turn == chess.WHITE:
            max_score = -float("inf")
            best_pv: list[chess.Move] = []
            for move in legal_moves:
                board.push(move)
                try:
                    score, child_pv = self._minimax(
                        board, depth - 1, evaluator, metrics, controller, ply + 1
                    )
                finally:
                    board.pop()
                if score > max_score:
                    max_score = score
                    best_pv = [move, *child_pv]
            return max_score, best_pv

        min_score = float("inf")
        best_pv = []
        for move in legal_moves:
            board.push(move)
            try:
                score, child_pv = self._minimax(
                    board, depth - 1, evaluator, metrics, controller, ply + 1
                )
            finally:
                board.pop()
            if score < min_score:
                min_score = score
                best_pv = [move, *child_pv]
        return min_score, best_pv

    @staticmethod
    def _raise_if_stopped(
        controller: SearchController,
        metrics: SearchMetrics,
    ) -> None:
        if controller.should_stop() or controller.nodes_exceeded(
            metrics.nodes_searched
        ):
            raise SearchStoppedError
