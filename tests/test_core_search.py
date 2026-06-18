"""Tests for the reusable core search package."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import chess
import pytest

from ai_chess.engine.config import EngineConfig
from ai_chess.engine.limits import SearchLimits
from ai_chess.engine.metrics import SearchMetrics
from ai_chess.engine.result import SearchResult
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.optimization.move_ordering import order_moves
from ai_chess.optimization.search_controller import SearchController
from ai_chess.optimization.transposition_table import (
    EXACT,
    TranspositionTable,
    TTEntry,
)
from ai_chess.presets import make_engine
from ai_chess.search.alpha_beta import AlphaBetaSearch
from ai_chess.search.minimax import MinimaxSearch
from ai_chess.search.quiescence import QuiescenceSearch

PRESETS = [
    "v0_minimax",
    "v1_alpha_beta",
    "v2_alpha_beta_ordering",
    "v3_alpha_beta_ordering_tt",
    "v4_iterative_deepening",
    "v5_quiescence",
]


class LastMoveEvaluator:
    """Scores a selected last move higher for deterministic stop tests."""

    def __init__(self, preferred_uci: str) -> None:
        self.preferred_uci = preferred_uci

    def evaluate(self, board: chess.Board) -> int:
        if board.move_stack and board.move_stack[-1].uci() == self.preferred_uci:
            return 100
        return 0


class CheckedPositionEvaluator:
    """Makes stand-pat-in-check observable in quiescence tests."""

    def evaluate(self, board: chess.Board) -> int:
        if board.is_check():
            return -999 if board.turn == chess.WHITE else 999
        return 42


def test_public_imports_work_in_fresh_interpreters() -> None:
    commands = [
        "import ai_chess.engine",
        "import ai_chess.search",
        "import ai_chess.optimization",
        "from ai_chess.optimization.transposition_table import TranspositionTable",
        "from ai_chess.presets.factory import make_engine",
    ]
    env = {
        **os.environ,
        "PYTHONPATH": str(Path.cwd() / "src"),
    }

    for command in commands:
        subprocess.run(
            [sys.executable, "-c", command],
            cwd=Path.cwd(),
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )


@pytest.mark.parametrize("preset", PRESETS)
def test_make_engine_presets_return_legal_search_result(preset: str) -> None:
    board = chess.Board()
    engine = make_engine(preset, max_depth=2)

    result = engine.search(board, SearchLimits(depth=2))

    assert isinstance(result, SearchResult)
    assert result.best_move in board.legal_moves
    assert result.nodes > 0
    assert result.elapsed_ms >= 0
    assert result.metrics.best_move == result.best_move.uci()


def test_find_best_move_compatibility_wrapper() -> None:
    board = chess.Board()
    engine = make_engine("v1_alpha_beta", max_depth=1)

    move, metrics = engine.find_best_move(board)

    assert move in board.legal_moves
    assert metrics.best_move == move.uci()


def test_minimax_search_api_updates_result_and_metrics() -> None:
    board = chess.Board()
    search = MinimaxSearch()

    result = search.search(
        board,
        BasicEvaluator(),
        EngineConfig(max_depth=2, use_alpha_beta=False),
        SearchLimits(depth=2),
    )

    assert result.best_move in board.legal_moves
    assert result.depth == 2
    assert result.score_cp is not None
    assert result.metrics.nodes_searched > 0
    assert result.metrics.depth_reached == 2


def test_alpha_beta_matches_minimax_score_and_searches_no_more_nodes() -> None:
    board = chess.Board()
    evaluator = BasicEvaluator()
    config = EngineConfig(max_depth=3, use_move_ordering=False)

    minimax_result = MinimaxSearch().search(
        board,
        evaluator,
        EngineConfig(max_depth=3, use_alpha_beta=False),
        SearchLimits(depth=3),
    )
    alpha_beta_result = AlphaBetaSearch().search(
        board,
        evaluator,
        config,
        SearchLimits(depth=3),
    )

    assert alpha_beta_result.best_move in board.legal_moves
    assert alpha_beta_result.score_cp == minimax_result.score_cp
    assert alpha_beta_result.nodes <= minimax_result.nodes
    assert alpha_beta_result.metrics.cutoffs > 0


def test_move_ordering_is_deterministic_and_respects_preferred_move() -> None:
    board = chess.Board()
    moves = list(board.legal_moves)
    preferred = chess.Move.from_uci("e2e4")

    ordered_once = order_moves(board, moves, preferred)
    ordered_twice = order_moves(board, moves, preferred)

    assert ordered_once[0] == preferred
    assert [move.uci() for move in ordered_once] == [
        move.uci() for move in ordered_twice
    ]


def test_move_ordering_prioritizes_captures_and_promotions() -> None:
    capture_board = chess.Board("4k3/8/8/8/4q3/4R3/8/4K3 w - - 0 1")
    capture_moves = list(capture_board.legal_moves)
    ordered_captures = order_moves(capture_board, capture_moves)
    assert capture_board.is_capture(ordered_captures[0])

    promotion_board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
    promotion_moves = list(promotion_board.legal_moves)
    ordered_promotions = order_moves(promotion_board, promotion_moves)
    assert ordered_promotions[0].promotion is not None


def test_transposition_table_store_probe_clear_and_size() -> None:
    table = TranspositionTable()
    move = chess.Move.from_uci("e2e4")
    entry = TTEntry(key=123, depth=2, score=10, flag=EXACT, best_move=move)

    table.store(123, entry)

    assert table.size() == 1
    probed = table.probe(123)
    assert probed is not None
    assert probed.score == 10
    assert probed.best_move == move

    table.clear()
    assert table.size() == 0
    assert table.probe(123) is None


def test_zero_size_transposition_table_is_disabled() -> None:
    table = TranspositionTable(hash_size_mb=0)
    table.store(1, TTEntry(key=1, depth=1, score=50, flag=EXACT))

    assert table.size() == 0
    assert table.probe(1) is None


def test_transposition_table_integrates_with_alpha_beta_and_reset() -> None:
    board = chess.Board()
    engine = make_engine("v3_alpha_beta_ordering_tt", max_depth=3)

    first = engine.search(board, SearchLimits(depth=3))
    second = engine.search(board, SearchLimits(depth=3))

    assert first.metrics.tt_probes > 0
    assert first.metrics.tt_stores > 0
    assert second.metrics.tt_hits > 0

    table = engine.search_algorithm.transposition_table
    assert table is not None
    assert table.size() > 0
    engine.reset()
    assert table.size() == 0


def test_iterative_deepening_completes_depths_and_handles_tiny_time() -> None:
    board = chess.Board()
    engine = make_engine("v4_iterative_deepening", max_depth=3)

    normal = engine.search(board, SearchLimits(depth=3))
    tiny = engine.search(board, SearchLimits(depth=5, movetime_ms=0))

    assert normal.best_move in board.legal_moves
    assert normal.depth == 3
    assert normal.metrics.completed
    assert tiny.best_move in board.legal_moves
    assert tiny.metrics.stopped_early
    assert tiny.metrics.stop_reason == "time"


def test_infinite_limits_ignore_time_but_keep_node_limit() -> None:
    controller = SearchController(
        SearchLimits(movetime_ms=0, nodes=1, infinite=True)
    )

    assert not controller.should_stop()
    assert controller.nodes_exceeded(1)


def test_infinite_search_limit_does_not_stop_on_movetime() -> None:
    board = chess.Board()
    engine = make_engine("v4_iterative_deepening", max_depth=1)

    result = engine.search(board, SearchLimits(depth=1, movetime_ms=0, infinite=True))

    assert result.best_move in board.legal_moves
    assert result.metrics.completed
    assert not result.metrics.stopped_early


def test_quiescence_runs_from_leaf_nodes_and_can_be_bounded() -> None:
    board = chess.Board()
    engine = make_engine("v5_quiescence", max_depth=1)
    engine.config.quiescence_max_depth = 0

    result = engine.search(board, SearchLimits(depth=1))

    assert result.best_move in board.legal_moves
    assert result.metrics.qnodes_searched > 0
    assert result.metrics.seldepth == 1


def test_quiescence_searches_evasions_instead_of_stand_pat_when_checked() -> None:
    board = chess.Board("k3r3/8/8/8/8/8/8/4K3 w - - 0 1")
    original_fen = board.fen()
    metrics = SearchMetrics()

    score = QuiescenceSearch().search(
        board,
        CheckedPositionEvaluator(),
        -float("inf"),
        float("inf"),
        max_depth=1,
        metrics=metrics,
        controller=SearchController(SearchLimits()),
        ply=0,
    )

    assert board.is_check()
    assert score == 42
    assert metrics.qnodes_searched > 1
    assert board.fen() == original_fen


def test_alpha_beta_preserves_completed_root_move_when_stopped() -> None:
    board = chess.Board()
    original_fen = board.fen()
    result = AlphaBetaSearch().search(
        board,
        LastMoveEvaluator("a2a4"),
        EngineConfig(max_depth=1, use_move_ordering=False),
        SearchLimits(depth=1, nodes=3),
    )

    assert result.metrics.stopped_early
    assert result.metrics.stop_reason == "nodes"
    assert result.best_move == chess.Move.from_uci("a2a4")
    assert result.best_move in board.legal_moves
    assert board.fen() == original_fen


@pytest.mark.parametrize("preset", PRESETS)
def test_search_is_deterministic_and_preserves_board(preset: str) -> None:
    board = chess.Board()
    original_fen = board.fen()
    engine = make_engine(preset, max_depth=2)

    first = engine.search(board, SearchLimits(depth=2))
    engine.reset()
    second = engine.search(board, SearchLimits(depth=2))

    assert board.fen() == original_fen
    assert first.best_move == second.best_move


@pytest.mark.parametrize("preset", PRESETS)
def test_all_presets_return_none_without_legal_moves(preset: str) -> None:
    board = chess.Board(
        "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
    )
    engine = make_engine(preset, max_depth=2)

    result = engine.search(board, SearchLimits(depth=2))

    assert board.is_checkmate()
    assert result.best_move is None
