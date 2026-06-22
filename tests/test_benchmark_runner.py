"""Tests for benchmark result generation and compatibility wrappers."""

from __future__ import annotations

from types import SimpleNamespace

import chess

from ai_chess.engine.limits import SearchLimits
from ai_chess.engine.metrics import SearchMetrics
from ai_chess.engine.result import SearchResult
from ai_chess.experiments import benchmark_runner
from ai_chess.experiments.benchmark_runner import (
    BENCHMARK_FIELDS,
    build_benchmark_row,
    run_benchmark,
    run_experiment_suite,
)
from ai_chess.experiments.fen_loader import TestPosition as FenPosition


def test_benchmark_row_contains_all_fields_and_derived_metrics() -> None:
    position = FenPosition(
        id="pos1",
        fen=chess.STARTING_FEN,
        category="opening",
        description="start",
        best_move="e2e4",
    )
    metrics = SearchMetrics(
        nodes_searched=10,
        qnodes_searched=5,
        cutoffs=3,
        beta_cutoffs=2,
        tt_probes=4,
        tt_hits=1,
        tt_stores=6,
        depth_reached=2,
        seldepth=3,
        elapsed_seconds=0.5,
        completed=True,
        stopped_early=False,
    )
    result = SearchResult(
        best_move=chess.Move.from_uci("e2e4"),
        score_cp=34,
        depth=2,
        seldepth=3,
        pv=[
            chess.Move.from_uci("e2e4"),
            chess.Move.from_uci("e7e5"),
        ],
        metrics=metrics,
    )

    row = build_benchmark_row(
        preset="v1_alpha_beta",
        depth=2,
        movetime_ms=1000,
        trial=3,
        position=position,
        result=result,
    )

    assert list(row) == list(BENCHMARK_FIELDS)
    assert row["total_nodes"] == 15
    assert row["elapsed_ms"] == 500
    assert row["nps"] == 30
    assert row["tt_hit_rate"] == 0.25
    assert row["is_correct"] is True
    assert row["pv_uci"] == "e2e4 e7e5"


def test_benchmark_row_leaves_unlabeled_positions_uncorrected() -> None:
    position = FenPosition(
        id="pos1",
        fen=chess.STARTING_FEN,
        category="opening",
    )
    result = SearchResult(
        best_move=chess.Move.from_uci("e2e4"),
        metrics=SearchMetrics(elapsed_seconds=0),
    )

    row = build_benchmark_row(
        preset="v0_minimax",
        depth=1,
        movetime_ms=None,
        trial=1,
        position=position,
        result=result,
    )

    assert row["expected_best_move"] == ""
    assert row["is_correct"] is None
    assert row["nps"] == 0
    assert row["tt_hit_rate"] == 0


def test_run_experiment_suite_resets_engine_and_uses_limits(monkeypatch) -> None:
    class FakeEngine:
        def __init__(self) -> None:
            self.reset_count = 0
            self.search_limits = []

        def reset(self) -> None:
            self.reset_count += 1

        def search(
            self,
            board: chess.Board,
            limits: object,
        ) -> SearchResult:
            self.search_limits.append(limits)
            return SearchResult(
                best_move=next(iter(board.legal_moves)),
                metrics=SearchMetrics(nodes_searched=1, elapsed_seconds=1),
            )

    engines: list[FakeEngine] = []

    def fake_make_engine(preset: str, *, max_depth: int) -> FakeEngine:
        assert preset == "v0_minimax"
        assert max_depth == 2
        engine = FakeEngine()
        engines.append(engine)
        return engine

    monkeypatch.setattr(benchmark_runner, "make_engine", fake_make_engine)
    position = FenPosition(
        id="pos1",
        fen=chess.STARTING_FEN,
        category="opening",
    )

    rows = run_experiment_suite(
        [position],
        presets=["v0_minimax"],
        depths=[2],
        repeats=2,
        movetime_ms=50,
    )

    assert len(rows) == 2
    assert len(engines) == 2
    assert all(engine.reset_count == 1 for engine in engines)
    assert rows[0]["movetime_ms"] == 50
    assert rows[0]["depth"] == 2


class StructuredOnlyEngine:
    """Test double that exposes only the structured search path."""

    def __init__(self) -> None:
        self.config = SimpleNamespace(max_depth=1, time_limit_seconds=None)
        self.search_algorithm = SimpleNamespace(name="structured_only")
        self.calls: list[tuple[str, SearchLimits | None]] = []
        self.reset_count = 0

    def reset(self) -> None:
        self.reset_count += 1

    def search(
        self,
        board: chess.Board,
        limits: SearchLimits | None = None,
    ) -> SearchResult:
        self.calls.append((board.fen(), limits))
        move = chess.Move.from_uci("e2e4")
        metrics = SearchMetrics(
            nodes_searched=1,
            elapsed_seconds=0.01,
            depth_reached=1,
            score=23,
        )
        return SearchResult(
            best_move=move,
            score_cp=23,
            depth=1,
            nodes=1,
            elapsed_ms=10,
            metrics=metrics,
        )

    def find_best_move(
        self,
        board: chess.Board,
    ) -> tuple[chess.Move | None, SearchMetrics]:
        raise AssertionError("run_benchmark should use engine.search()")


def test_run_benchmark_uses_structured_search_api() -> None:
    position = FenPosition(
        id="start",
        fen=chess.STARTING_FEN,
        category="opening",
        best_move="e2e4",
    )
    limits = SearchLimits(depth=1)
    engine = StructuredOnlyEngine()

    rows = run_benchmark([position], engine, limits)

    assert engine.reset_count == 1
    assert engine.calls == [(chess.Board().fen(), limits)]
    row = rows[0]
    assert list(row) == list(BENCHMARK_FIELDS)
    assert row["position_id"] == "start"
    assert row["best_move_uci"] == "e2e4"
    assert row["expected_best_move"] == "e2e4"
    assert row["nodes_searched"] == 1
    assert row["score_cp"] == 23
    assert row["depth"] == 1
