"""Bounded quiescence search for noisy leaf positions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import chess

from ai_chess.optimization.move_ordering import order_moves
from ai_chess.search.base import SearchStoppedError

if TYPE_CHECKING:
    from ai_chess.engine.metrics import SearchMetrics
    from ai_chess.evaluation.evaluator import BasicEvaluator
    from ai_chess.optimization.search_controller import SearchController


class QuiescenceSearch:
    """Alpha-beta quiescence search over captures and promotions."""

    def search(
        self,
        board: chess.Board,
        evaluator: BasicEvaluator,
        alpha: float,
        beta: float,
        max_depth: int,
        metrics: SearchMetrics,
        controller: SearchController,
        ply: int,
    ) -> int:
        """Return a bounded quiet-position score from White's perspective."""
        metrics.qnodes_searched += 1
        metrics.seldepth = max(metrics.seldepth or 0, ply)
        if controller.should_stop() or controller.nodes_exceeded(
            metrics.nodes_searched + metrics.qnodes_searched
        ):
            raise SearchStoppedError

        if board.is_game_over():
            return evaluator.evaluate(board)

        if board.is_check():
            if max_depth <= 0:
                return evaluator.evaluate(board)
            evasions = order_moves(board, board.legal_moves)
            return self._search_ordered_moves(
                board,
                evasions,
                evaluator,
                alpha,
                beta,
                max_depth,
                metrics,
                controller,
                ply,
            )

        stand_pat = evaluator.evaluate(board)
        if max_depth <= 0:
            return stand_pat

        noisy_moves = [
            move
            for move in board.legal_moves
            if board.is_capture(move) or move.promotion is not None
        ]
        noisy_moves = order_moves(board, noisy_moves)

        if board.turn == chess.WHITE:
            best_score = stand_pat
            if best_score >= beta:
                metrics.cutoffs += 1
                metrics.beta_cutoffs += 1
                return int(best_score)
            alpha = max(alpha, best_score)

            for move in noisy_moves:
                self._raise_if_stopped(controller, metrics)
                board.push(move)
                try:
                    score = self.search(
                        board,
                        evaluator,
                        alpha,
                        beta,
                        max_depth - 1,
                        metrics,
                        controller,
                        ply + 1,
                    )
                finally:
                    board.pop()
                if score > best_score:
                    best_score = score
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    metrics.cutoffs += 1
                    metrics.beta_cutoffs += 1
                    break
            return int(best_score)

        best_score = stand_pat
        if best_score <= alpha:
            metrics.cutoffs += 1
            return int(best_score)
        beta = min(beta, best_score)

        for move in noisy_moves:
            self._raise_if_stopped(controller, metrics)
            board.push(move)
            try:
                score = self.search(
                    board,
                    evaluator,
                    alpha,
                    beta,
                    max_depth - 1,
                    metrics,
                    controller,
                    ply + 1,
                )
            finally:
                board.pop()
            if score < best_score:
                best_score = score
            beta = min(beta, best_score)
            if beta <= alpha:
                metrics.cutoffs += 1
                break
        return int(best_score)

    def _search_ordered_moves(
        self,
        board: chess.Board,
        moves: list[chess.Move],
        evaluator: BasicEvaluator,
        alpha: float,
        beta: float,
        max_depth: int,
        metrics: SearchMetrics,
        controller: SearchController,
        ply: int,
    ) -> int:
        if board.turn == chess.WHITE:
            best_score = -float("inf")
            for move in moves:
                self._raise_if_stopped(controller, metrics)
                board.push(move)
                try:
                    score = self.search(
                        board,
                        evaluator,
                        alpha,
                        beta,
                        max_depth - 1,
                        metrics,
                        controller,
                        ply + 1,
                    )
                finally:
                    board.pop()
                if score > best_score:
                    best_score = score
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    metrics.cutoffs += 1
                    metrics.beta_cutoffs += 1
                    break
            return int(best_score)

        best_score = float("inf")
        for move in moves:
            self._raise_if_stopped(controller, metrics)
            board.push(move)
            try:
                score = self.search(
                    board,
                    evaluator,
                    alpha,
                    beta,
                    max_depth - 1,
                    metrics,
                    controller,
                    ply + 1,
                )
            finally:
                board.pop()
            if score < best_score:
                best_score = score
            beta = min(beta, best_score)
            if beta <= alpha:
                metrics.cutoffs += 1
                break
        return int(best_score)

    @staticmethod
    def _raise_if_stopped(
        controller: SearchController,
        metrics: SearchMetrics,
    ) -> None:
        if controller.should_stop() or controller.nodes_exceeded(
            metrics.nodes_searched + metrics.qnodes_searched
        ):
            raise SearchStoppedError
