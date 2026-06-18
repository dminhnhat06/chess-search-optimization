"""Tests for benchmark runner API alignment."""

from __future__ import annotations

import chess

from ai_chess.engine.limits import SearchLimits
from ai_chess.engine.metrics import SearchMetrics
from ai_chess.engine.result import SearchResult
from ai_chess.experiments.benchmark_runner import run_benchmark
from ai_chess.experiments.fen_loader import TestPosition as FenPosition


class StructuredOnlyEngine:
    """Test double that exposes only the structured search path."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, SearchLimits | None]] = []

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
    """Benchmark runner should consume SearchResult while preserving row fields."""
    position = FenPosition(
        id="start",
        fen=chess.STARTING_FEN,
        category="opening",
        best_move="e2e4",
    )
    limits = SearchLimits(depth=1)
    engine = StructuredOnlyEngine()

    rows = run_benchmark([position], engine, limits)

    assert engine.calls == [(chess.Board().fen(), limits)]
    assert rows == [
        {
            "position_id": "start",
            "category": "opening",
            "fen": chess.STARTING_FEN,
            "best_move_uci": "e2e4",
            "expected_best_move": "e2e4",
            "nodes_searched": 1,
            "elapsed_seconds": 0.01,
            "depth_reached": 1,
            "score": 23,
        }
    ]
