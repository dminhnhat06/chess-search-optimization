"""Tests for benchmark result generation."""

from __future__ import annotations

import chess

from ai_chess.engine.metrics import SearchMetrics
from ai_chess.engine.result import SearchResult
from ai_chess.experiments import benchmark_runner
from ai_chess.experiments.benchmark_runner import (
    BENCHMARK_FIELDS,
    build_benchmark_row,
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
