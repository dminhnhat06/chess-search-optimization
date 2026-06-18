"""Alpha-beta search with optional ordering, TT, and quiescence."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import chess

from ai_chess.engine.metrics import SearchMetrics
from ai_chess.optimization.move_ordering import order_moves
from ai_chess.optimization.search_controller import SearchController
from ai_chess.optimization.transposition_table import (
    EXACT,
    LOWER_BOUND,
    UPPER_BOUND,
    TranspositionTable,
    TTEntry,
    compute_board_hash,
)
from ai_chess.search.base import (
    SearchAlgorithm,
    SearchStoppedError,
    finalize_result,
    stable_legal_moves,
)
from ai_chess.search.quiescence import QuiescenceSearch

if TYPE_CHECKING:
    from ai_chess.engine.config import EngineConfig
    from ai_chess.engine.limits import SearchLimits
    from ai_chess.engine.result import SearchResult
    from ai_chess.evaluation.evaluator import BasicEvaluator


class AlphaBetaSearch(SearchAlgorithm):
    """Depth-limited alpha-beta search over White-perspective scores."""

    name = "alpha_beta"

    def __init__(self, transposition_table: TranspositionTable | None = None) -> None:
        self.transposition_table = transposition_table
        self._quiescence = QuiescenceSearch()

    def search(
        self,
        board: chess.Board,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        limits: SearchLimits,
    ) -> SearchResult:
        """Search using alpha-beta pruning."""
        metrics = SearchMetrics()
        controller = SearchController(limits, config.move_overhead_ms, board.turn)
        depth = limits.depth or config.max_depth
        start_time = time.perf_counter()

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
        score = evaluator.evaluate(board)
        pv = [best_move]
        completed_depth = depth

        try:
            best_move, score, pv = self.search_root(
                board=board,
                evaluator=evaluator,
                config=config,
                depth=depth,
                metrics=metrics,
                controller=controller,
                preferred_move=None,
            )
        except SearchStoppedError as exc:
            metrics.completed = False
            metrics.stopped_early = True
            metrics.stop_reason = controller.stop_reason or "stopped"
            completed_depth = 0
            if exc.best_move is not None:
                best_move = exc.best_move
                score = exc.score if exc.score is not None else score
                pv = exc.pv or [best_move]

        elapsed = time.perf_counter() - start_time
        return finalize_result(
            best_move=best_move,
            score=int(score),
            depth=completed_depth,
            pv=pv if best_move is not None else [],
            metrics=metrics,
            elapsed_seconds=elapsed,
        )

    def reset(self) -> None:
        """Clear persistent search state."""
        if self.transposition_table is not None:
            self.transposition_table.clear()

    def search_root(
        self,
        *,
        board: chess.Board,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        depth: int,
        metrics: SearchMetrics,
        controller: SearchController,
        preferred_move: chess.Move | None,
    ) -> tuple[chess.Move | None, int, list[chess.Move]]:
        """Search one root depth with caller-owned metrics and stop control.

        This method is used by iterative deepening to complete one depth while
        preserving cumulative metrics across iterations. It returns
        ``(best_move, score, pv)`` when the root depth completes. If a limit is
        reached, it raises ``SearchStoppedError`` carrying the best completed
        root move when available, and it always restores the board before
        returning or raising.
        """
        legal_moves = stable_legal_moves(board)
        if not legal_moves:
            return None, evaluator.evaluate(board), []

        tt_move = self._tt_best_move(board, config, metrics)
        root_preferred = preferred_move or tt_move
        moves = self._ordered_moves(board, legal_moves, config, root_preferred)

        best_move: chess.Move | None = moves[0]
        best_pv: list[chess.Move] = [best_move]
        fallback_score = evaluator.evaluate(board)
        completed_any = False
        alpha = -float("inf")
        beta = float("inf")

        if board.turn == chess.WHITE:
            best_score = -float("inf")
            for move in moves:
                try:
                    self._raise_if_stopped(controller, metrics)
                except SearchStoppedError as exc:
                    raise self._root_stop_error(
                        exc,
                        completed_any,
                        best_move,
                        best_score,
                        best_pv,
                        moves[0],
                        fallback_score,
                    ) from exc
                board.push(move)
                try:
                    score, child_pv = self._alpha_beta(
                        board,
                        depth - 1,
                        alpha,
                        beta,
                        evaluator,
                        config,
                        metrics,
                        controller,
                        1,
                    )
                except SearchStoppedError as exc:
                    raise self._root_stop_error(
                        exc,
                        completed_any,
                        best_move,
                        best_score,
                        best_pv,
                        moves[0],
                        fallback_score,
                    ) from exc
                finally:
                    board.pop()
                completed_any = True
                if score > best_score:
                    best_score = score
                    best_move = move
                    best_pv = [move, *child_pv]
                alpha = max(alpha, best_score)
            return best_move, int(best_score), best_pv

        best_score = float("inf")
        for move in moves:
            try:
                self._raise_if_stopped(controller, metrics)
            except SearchStoppedError as exc:
                raise self._root_stop_error(
                    exc,
                    completed_any,
                    best_move,
                    best_score,
                    best_pv,
                    moves[0],
                    fallback_score,
                ) from exc
            board.push(move)
            try:
                score, child_pv = self._alpha_beta(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    evaluator,
                    config,
                    metrics,
                    controller,
                    1,
                )
            except SearchStoppedError as exc:
                raise self._root_stop_error(
                    exc,
                    completed_any,
                    best_move,
                    best_score,
                    best_pv,
                    moves[0],
                    fallback_score,
                ) from exc
            finally:
                board.pop()
            completed_any = True
            if score < best_score:
                best_score = score
                best_move = move
                best_pv = [move, *child_pv]
            beta = min(beta, best_score)
        return best_move, int(best_score), best_pv

    @staticmethod
    def _root_stop_error(
        stopped: SearchStoppedError,
        completed_any: bool,
        best_move: chess.Move | None,
        best_score: float,
        best_pv: list[chess.Move],
        fallback_move: chess.Move,
        fallback_score: int,
    ) -> SearchStoppedError:
        if completed_any and best_move is not None:
            return SearchStoppedError(best_move, int(best_score), best_pv)
        if stopped.score is not None:
            fallback_score = stopped.score
        return SearchStoppedError(fallback_move, fallback_score, [fallback_move])

    def _alpha_beta(
        self,
        board: chess.Board,
        depth: int,
        alpha: float,
        beta: float,
        evaluator: BasicEvaluator,
        config: EngineConfig,
        metrics: SearchMetrics,
        controller: SearchController,
        ply: int,
    ) -> tuple[int, list[chess.Move]]:
        metrics.nodes_searched += 1
        metrics.seldepth = max(metrics.seldepth or 0, ply)
        self._raise_if_stopped(controller, metrics)

        if board.is_game_over():
            return evaluator.evaluate(board), []

        if depth <= 0:
            if config.use_quiescence:
                score = self._quiescence.search(
                    board,
                    evaluator,
                    alpha,
                    beta,
                    config.quiescence_max_depth,
                    metrics,
                    controller,
                    ply,
                )
                return score, []
            return evaluator.evaluate(board), []

        alpha_orig = alpha
        beta_orig = beta
        tt_entry = self._probe_tt(board, config, metrics)
        if tt_entry is not None and tt_entry.depth >= depth:
            if tt_entry.flag == EXACT:
                return tt_entry.score, self._pv_from_tt_entry(board, tt_entry)
            if tt_entry.flag == LOWER_BOUND and tt_entry.score >= beta:
                return tt_entry.score, self._pv_from_tt_entry(board, tt_entry)
            if tt_entry.flag == UPPER_BOUND and tt_entry.score <= alpha:
                return tt_entry.score, self._pv_from_tt_entry(board, tt_entry)

            if tt_entry.flag == LOWER_BOUND:
                alpha = max(alpha, tt_entry.score)
            elif tt_entry.flag == UPPER_BOUND:
                beta = min(beta, tt_entry.score)
            if alpha >= beta:
                return tt_entry.score, self._pv_from_tt_entry(board, tt_entry)

        legal_moves = stable_legal_moves(board)
        if not legal_moves:
            return evaluator.evaluate(board), []

        preferred = self._entry_move_if_legal(board, tt_entry)
        moves = self._ordered_moves(board, legal_moves, config, preferred)
        best_move: chess.Move | None = None
        best_pv: list[chess.Move] = []

        if board.turn == chess.WHITE:
            best_score = -float("inf")
            for move in moves:
                self._raise_if_stopped(controller, metrics)
                board.push(move)
                try:
                    score, child_pv = self._alpha_beta(
                        board,
                        depth - 1,
                        alpha,
                        beta,
                        evaluator,
                        config,
                        metrics,
                        controller,
                        ply + 1,
                    )
                finally:
                    board.pop()
                if score > best_score:
                    best_score = score
                    best_move = move
                    best_pv = [move, *child_pv]
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    metrics.cutoffs += 1
                    metrics.beta_cutoffs += 1
                    break
        else:
            best_score = float("inf")
            for move in moves:
                self._raise_if_stopped(controller, metrics)
                board.push(move)
                try:
                    score, child_pv = self._alpha_beta(
                        board,
                        depth - 1,
                        alpha,
                        beta,
                        evaluator,
                        config,
                        metrics,
                        controller,
                        ply + 1,
                    )
                finally:
                    board.pop()
                if score < best_score:
                    best_score = score
                    best_move = move
                    best_pv = [move, *child_pv]
                beta = min(beta, best_score)
                if beta <= alpha:
                    metrics.cutoffs += 1
                    break

        self._store_tt(
            board,
            config,
            metrics,
            depth,
            int(best_score),
            alpha_orig,
            beta_orig,
            best_move,
        )
        return int(best_score), best_pv

    def _ordered_moves(
        self,
        board: chess.Board,
        moves: list[chess.Move],
        config: EngineConfig,
        preferred_move: chess.Move | None = None,
    ) -> list[chess.Move]:
        if config.use_move_ordering:
            return order_moves(board, moves, preferred_move)
        if preferred_move is not None and preferred_move in moves:
            return [preferred_move, *[move for move in moves if move != preferred_move]]
        return moves

    def _table(self, config: EngineConfig) -> TranspositionTable | None:
        if not config.use_transposition_table:
            return None
        if (
            self.transposition_table is None
            or self.transposition_table.hash_size_mb != config.hash_size_mb
        ):
            self.transposition_table = TranspositionTable(config.hash_size_mb)
        return self.transposition_table

    def _probe_tt(
        self,
        board: chess.Board,
        config: EngineConfig,
        metrics: SearchMetrics,
    ) -> TTEntry | None:
        table = self._table(config)
        if table is None:
            return None
        return table.probe(compute_board_hash(board), metrics)

    def _tt_best_move(
        self,
        board: chess.Board,
        config: EngineConfig,
        metrics: SearchMetrics,
    ) -> chess.Move | None:
        entry = self._probe_tt(board, config, metrics)
        return self._entry_move_if_legal(board, entry)

    @staticmethod
    def _entry_move_if_legal(
        board: chess.Board,
        entry: TTEntry | None,
    ) -> chess.Move | None:
        if entry is None or entry.best_move is None:
            return None
        return entry.best_move if entry.best_move in board.legal_moves else None

    @staticmethod
    def _pv_from_tt_entry(
        board: chess.Board,
        entry: TTEntry,
    ) -> list[chess.Move]:
        move = AlphaBetaSearch._entry_move_if_legal(board, entry)
        return [move] if move is not None else []

    def _store_tt(
        self,
        board: chess.Board,
        config: EngineConfig,
        metrics: SearchMetrics,
        depth: int,
        score: int,
        alpha_orig: float,
        beta_orig: float,
        best_move: chess.Move | None,
    ) -> None:
        table = self._table(config)
        if table is None:
            return

        if score <= alpha_orig:
            flag = UPPER_BOUND
        elif score >= beta_orig:
            flag = LOWER_BOUND
        else:
            flag = EXACT

        key = compute_board_hash(board)
        entry = TTEntry(
            key=key,
            depth=depth,
            score=score,
            flag=flag,
            best_move=best_move,
        )
        table.store_with_metrics(key, entry, metrics)

    @staticmethod
    def _raise_if_stopped(
        controller: SearchController,
        metrics: SearchMetrics,
    ) -> None:
        total_nodes = metrics.nodes_searched + metrics.qnodes_searched
        if controller.should_stop() or controller.nodes_exceeded(total_nodes):
            raise SearchStoppedError
