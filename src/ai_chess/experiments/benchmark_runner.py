"""Benchmark runner for evaluating engine performance across FEN positions."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import chess

from ai_chess.engine.limits import SearchLimits
from ai_chess.presets import make_engine

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ai_chess.engine.chess_engine import ChessEngine
    from ai_chess.engine.result import SearchResult
    from ai_chess.experiments.fen_loader import TestPosition


DEFAULT_PRESETS = (
    "v0_minimax",
    "v1_alpha_beta",
    "v2_alpha_beta_ordering",
    "v3_alpha_beta_ordering_tt",
    "v4_iterative_deepening",
    "v5_quiescence",
)

BENCHMARK_FIELDS = (
    "preset",
    "depth",
    "movetime_ms",
    "trial",
    "position_id",
    "category",
    "fen",
    "description",
    "best_move_uci",
    "expected_best_move",
    "is_correct",
    "score_cp",
    "nodes_searched",
    "qnodes_searched",
    "total_nodes",
    "elapsed_seconds",
    "elapsed_ms",
    "nps",
    "cutoffs",
    "beta_cutoffs",
    "tt_probes",
    "tt_hits",
    "tt_stores",
    "tt_hit_rate",
    "depth_reached",
    "seldepth",
    "completed",
    "stopped_early",
    "stop_reason",
    "pv_uci",
)

BenchmarkFormat = Literal["csv", "json"]
BenchmarkRow = dict[str, object]
ProgressCallback = Callable[[dict[str, object]], None]


def run_benchmark(
    positions: list[TestPosition],
    engine: ChessEngine,
    limits: SearchLimits | None = None,
) -> list[BenchmarkRow]:
    """Run a preconfigured engine against positions.

    This compatibility wrapper keeps the old public entry point while returning
    the expanded benchmark row schema used by the experiment suite.
    """
    depth = (
        limits.depth
        if limits is not None and limits.depth is not None
        else engine.config.max_depth
    )
    movetime_ms = limits.movetime_ms if limits is not None else (
        int(engine.config.time_limit_seconds * 1000)
        if engine.config.time_limit_seconds is not None
        else None
    )
    preset = getattr(engine.search_algorithm, "name", "custom")
    rows: list[BenchmarkRow] = []

    for position in positions:
        board = chess.Board(position.fen)
        engine.reset()
        result = engine.search(
            board,
            limits or SearchLimits(depth=depth, movetime_ms=movetime_ms),
        )
        rows.append(
            build_benchmark_row(
                preset=preset,
                depth=depth,
                movetime_ms=movetime_ms,
                trial=1,
                position=position,
                result=result,
            )
        )

    return rows


def run_experiment_suite(
    positions: Sequence[TestPosition],
    *,
    presets: Iterable[str] = DEFAULT_PRESETS,
    depths: Iterable[int],
    repeats: int = 1,
    movetime_ms: int | None = None,
    fail_fast: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> list[BenchmarkRow]:
    """Run all requested preset/depth/trial/position combinations."""
    depth_values = tuple(depths)
    preset_values = tuple(presets)
    _validate_suite_args(depth_values, preset_values, repeats, movetime_ms)

    rows: list[BenchmarkRow] = []
    total_rows = len(preset_values) * len(depth_values) * repeats * len(positions)
    for preset in preset_values:
        for depth in depth_values:
            for trial in range(1, repeats + 1):
                for position in positions:
                    try:
                        board = chess.Board(position.fen)
                        engine = make_engine(preset, max_depth=depth)
                        engine.reset()
                        result = engine.search(
                            board,
                            SearchLimits(depth=depth, movetime_ms=movetime_ms),
                        )
                        row = build_benchmark_row(
                            preset=preset,
                            depth=depth,
                            movetime_ms=movetime_ms,
                            trial=trial,
                            position=position,
                            result=result,
                        )
                    except Exception as exc:
                        if fail_fast:
                            raise
                        row = build_error_row(
                            preset=preset,
                            depth=depth,
                            movetime_ms=movetime_ms,
                            trial=trial,
                            position=position,
                            error=exc,
                        )
                    rows.append(row)
                    if progress_callback is not None:
                        progress_callback(
                            {
                                "completed": len(rows),
                                "total": total_rows,
                                "preset": preset,
                                "depth": depth,
                                "trial": trial,
                                "position_id": position.id,
                            }
                        )

    return rows


def build_benchmark_row(
    *,
    preset: str,
    depth: int,
    movetime_ms: int | None,
    trial: int,
    position: TestPosition,
    result: SearchResult,
) -> BenchmarkRow:
    """Flatten one structured search result into the benchmark schema."""
    metrics = result.metrics
    nodes_searched = metrics.nodes_searched
    qnodes_searched = metrics.qnodes_searched
    total_nodes = nodes_searched + qnodes_searched
    elapsed_seconds = metrics.elapsed_seconds
    elapsed_ms = elapsed_seconds * 1000
    nps = total_nodes / elapsed_seconds if elapsed_seconds > 0 else 0
    tt_hit_rate = (
        metrics.tt_hits / metrics.tt_probes if metrics.tt_probes > 0 else 0
    )
    best_move_uci = result.best_move.uci() if result.best_move is not None else ""
    expected_best_move = position.best_move or ""

    return {
        "preset": preset,
        "depth": depth,
        "movetime_ms": movetime_ms,
        "trial": trial,
        "position_id": position.id,
        "category": position.category,
        "fen": position.fen,
        "description": position.description,
        "best_move_uci": best_move_uci,
        "expected_best_move": expected_best_move,
        "is_correct": (
            best_move_uci == expected_best_move if expected_best_move else None
        ),
        "score_cp": result.score_cp,
        "nodes_searched": nodes_searched,
        "qnodes_searched": qnodes_searched,
        "total_nodes": total_nodes,
        "elapsed_seconds": elapsed_seconds,
        "elapsed_ms": elapsed_ms,
        "nps": nps,
        "cutoffs": metrics.cutoffs,
        "beta_cutoffs": metrics.beta_cutoffs,
        "tt_probes": metrics.tt_probes,
        "tt_hits": metrics.tt_hits,
        "tt_stores": metrics.tt_stores,
        "tt_hit_rate": tt_hit_rate,
        "depth_reached": metrics.depth_reached,
        "seldepth": metrics.seldepth,
        "completed": metrics.completed,
        "stopped_early": metrics.stopped_early,
        "stop_reason": metrics.stop_reason or "",
        "pv_uci": " ".join(move.uci() for move in result.pv),
    }


def build_error_row(
    *,
    preset: str,
    depth: int,
    movetime_ms: int | None,
    trial: int,
    position: TestPosition,
    error: Exception,
) -> BenchmarkRow:
    """Build a schema-compatible row for non-fail-fast benchmark errors."""
    return {
        "preset": preset,
        "depth": depth,
        "movetime_ms": movetime_ms,
        "trial": trial,
        "position_id": position.id,
        "category": position.category,
        "fen": position.fen,
        "description": position.description,
        "best_move_uci": "",
        "expected_best_move": position.best_move or "",
        "is_correct": None,
        "score_cp": None,
        "nodes_searched": 0,
        "qnodes_searched": 0,
        "total_nodes": 0,
        "elapsed_seconds": 0,
        "elapsed_ms": 0,
        "nps": 0,
        "cutoffs": 0,
        "beta_cutoffs": 0,
        "tt_probes": 0,
        "tt_hits": 0,
        "tt_stores": 0,
        "tt_hit_rate": 0,
        "depth_reached": 0,
        "seldepth": None,
        "completed": False,
        "stopped_early": True,
        "stop_reason": f"error: {error}",
        "pv_uci": "",
    }


def write_benchmark_results(
    rows: Sequence[BenchmarkRow],
    output_path: str | Path,
    *,
    output_format: BenchmarkFormat = "csv",
) -> None:
    """Write benchmark rows as CSV or JSON, creating parent directories."""
    path = Path(output_path)
    if path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "csv":
        with path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=BENCHMARK_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return

    if output_format == "json":
        with path.open("w", encoding="utf-8") as jsonfile:
            json.dump(list(rows), jsonfile, indent=2)
            jsonfile.write("\n")
        return

    raise ValueError(f"Unsupported benchmark output format: {output_format}")


def _validate_suite_args(
    depths: Sequence[int],
    presets: Sequence[str],
    repeats: int,
    movetime_ms: int | None,
) -> None:
    if not presets:
        raise ValueError("at least one preset is required")
    if not depths:
        raise ValueError("at least one depth is required")
    if any(depth < 1 for depth in depths):
        raise ValueError("all depths must be >= 1")
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    if movetime_ms is not None and movetime_ms < 0:
        raise ValueError("movetime_ms must be non-negative")
