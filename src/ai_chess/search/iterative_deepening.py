"""Iterative deepening search with time-aware stopping."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from ai_chess.engine.metrics import SearchMetrics
from ai_chess.optimization.search_controller import SearchController
from ai_chess.search.alpha_beta import AlphaBetaSearch
from ai_chess.search.base import (
    SearchAlgorithm,
    SearchStoppedError,
    finalize_result,
    stable_legal_moves,
)

if TYPE_CHECKING:
    import chess

    from ai_chess.engine.config import EngineConfig
    from ai_chess.engine.limits import SearchLimits
    from ai_chess.engine.result import SearchResult
    from ai_chess.evaluation.evaluator import BasicEvaluator


class IterativeDeepeningSearch(SearchAlgorithm):
    """Search depth 1..N, returning the last fully completed iteration."""

    name = "iterative_deepening"

    def __init__(self, inner_search: AlphaBetaSearch | None = None) -> None:
        self.inner_search = inner_search or AlphaBetaSearch()

    def search(
        self,
        board: chess.Board,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        limits: SearchLimits,
    ) -> SearchResult:
        """Run iterative deepening under depth, time, and node limits."""
        metrics = SearchMetrics()
        controller = SearchController(limits, config.move_overhead_ms, board.turn)
        start_time = time.perf_counter()
        max_depth = limits.depth or config.max_depth

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
        best_score = evaluator.evaluate(board)
        best_pv: list[chess.Move] = [best_move]
        completed_depth = 0
        preferred_move: chess.Move | None = None

        for depth in range(1, max_depth + 1):
            if controller.should_stop() or controller.nodes_exceeded(
                metrics.nodes_searched + metrics.qnodes_searched
            ):
                metrics.completed = False
                metrics.stopped_early = True
                metrics.stop_reason = controller.stop_reason or "stopped"
                break

            try:
                move, score, pv = self.inner_search.search_root(
                    board=board,
                    evaluator=evaluator,
                    config=config,
                    depth=depth,
                    metrics=metrics,
                    controller=controller,
                    preferred_move=preferred_move,
                )
            except SearchStoppedError:
                metrics.completed = False
                metrics.stopped_early = True
                metrics.stop_reason = controller.stop_reason or "stopped"
                break

            if move is not None:
                best_move = move
                best_score = score
                best_pv = pv
                preferred_move = move
            completed_depth = depth

        if completed_depth == 0 and not metrics.stopped_early:
            metrics.completed = False
            metrics.stopped_early = True
            metrics.stop_reason = "no_completed_depth"

        elapsed = time.perf_counter() - start_time
        return finalize_result(
            best_move=best_move,
            score=int(best_score),
            depth=completed_depth,
            pv=best_pv if best_move is not None else [],
            metrics=metrics,
            elapsed_seconds=elapsed,
        )

    def reset(self) -> None:
        """Reset inner search state."""
        self.inner_search.reset()
