"""Tests for benchmark analysis CLI outputs."""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pandas as pd

from ai_chess.experiments.benchmark_runner import BENCHMARK_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "analyze_results.py"

SUMMARY_FILES = (
    "summary_by_preset_depth.csv",
    "summary_by_category.csv",
    "summary_by_preset_category.csv",
    "node_reduction_vs_baseline.csv",
    "accuracy_summary.csv",
    "tt_summary.csv",
    "quiescence_summary.csv",
)

CHART_FILES = (
    "mean_nodes_by_preset_depth.png",
    "mean_time_by_preset_depth.png",
    "node_reduction_vs_baseline.png",
    "tt_hit_rate_by_depth.png",
    "accuracy_by_preset.png",
    "quiescence_qnodes.png",
)


def _write_benchmark_csv(path: Path) -> None:
    rows = [
        _row(
            preset="v0_minimax",
            position_id="p1",
            category="tactical",
            best_move_uci="e2e4",
            expected_best_move="e2e4",
            is_correct=True,
            total_nodes=100,
            elapsed_ms=10,
        ),
        _row(
            preset="v1_alpha_beta",
            position_id="p1",
            category="tactical",
            best_move_uci="e2e4",
            expected_best_move="e2e4",
            is_correct=True,
            total_nodes=50,
            elapsed_ms=5,
            cutoffs=10,
        ),
        _row(
            preset="v0_minimax",
            position_id="p2",
            category="opening",
            total_nodes=200,
            elapsed_ms=20,
        ),
        _row(
            preset="v1_alpha_beta",
            position_id="p2",
            category="opening",
            total_nodes=100,
            elapsed_ms=10,
            cutoffs=20,
        ),
        _row(
            preset="v3_alpha_beta_ordering_tt",
            position_id="p3",
            category="quiescence",
            best_move_uci="a2a3",
            expected_best_move="a2a3",
            is_correct=True,
            total_nodes=80,
            elapsed_ms=8,
            qnodes_searched=0,
            tt_probes=20,
            tt_hits=10,
            tt_stores=30,
            tt_hit_rate=0.5,
            seldepth=2,
        ),
        _row(
            preset="v5_quiescence",
            position_id="p3",
            category="quiescence",
            best_move_uci="a2a3",
            expected_best_move="a2a3",
            is_correct=True,
            total_nodes=120,
            elapsed_ms=12,
            qnodes_searched=40,
            tt_probes=20,
            tt_hits=8,
            tt_stores=35,
            tt_hit_rate=0.4,
            seldepth=4,
        ),
    ]

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=BENCHMARK_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _row(
    *,
    preset: str,
    position_id: str,
    category: str,
    best_move_uci: str = "",
    expected_best_move: str = "",
    is_correct: bool | str = "",
    total_nodes: int,
    elapsed_ms: float,
    qnodes_searched: int = 0,
    cutoffs: int = 0,
    tt_probes: int = 0,
    tt_hits: int = 0,
    tt_stores: int = 0,
    tt_hit_rate: float = 0,
    seldepth: int = 2,
) -> dict[str, object]:
    nodes_searched = total_nodes - qnodes_searched
    return {
        "preset": preset,
        "depth": 2,
        "movetime_ms": "",
        "trial": 1,
        "position_id": position_id,
        "category": category,
        "fen": "8/8/8/8/8/8/8/K6k w - - 0 1",
        "description": position_id,
        "best_move_uci": best_move_uci,
        "expected_best_move": expected_best_move,
        "is_correct": is_correct,
        "score_cp": 0,
        "nodes_searched": nodes_searched,
        "qnodes_searched": qnodes_searched,
        "total_nodes": total_nodes,
        "elapsed_seconds": elapsed_ms / 1000,
        "elapsed_ms": elapsed_ms,
        "nps": total_nodes / (elapsed_ms / 1000),
        "cutoffs": cutoffs,
        "beta_cutoffs": cutoffs,
        "tt_probes": tt_probes,
        "tt_hits": tt_hits,
        "tt_stores": tt_stores,
        "tt_hit_rate": tt_hit_rate,
        "depth_reached": 2,
        "seldepth": seldepth,
        "completed": True,
        "stopped_early": False,
        "stop_reason": "",
        "pv_uci": best_move_uci,
    }


def test_analyze_results_cli_creates_summaries_and_charts(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "benchmark.csv"
    output_dir = tmp_path / "analysis"
    _write_benchmark_csv(input_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Wrote 7 summary CSV files" in completed.stdout
    for filename in SUMMARY_FILES:
        path = output_dir / filename
        assert path.exists()
        assert path.stat().st_size > 0
    for filename in CHART_FILES:
        path = output_dir / "charts" / filename
        assert path.exists()
        assert path.stat().st_size > 0

    accuracy = pd.read_csv(output_dir / "accuracy_summary.csv")
    v0_accuracy = accuracy[
        (accuracy["preset"] == "v0_minimax") & (accuracy["depth"] == 2)
    ].iloc[0]
    assert v0_accuracy["num_labeled"] == 1
    assert v0_accuracy["accuracy"] == 1.0

    reduction = pd.read_csv(output_dir / "node_reduction_vs_baseline.csv")
    v1_p1 = reduction[
        (reduction["preset"] == "v1_alpha_beta")
        & (reduction["position_id"] == "p1")
    ].iloc[0]
    assert v1_p1["node_reduction_ratio"] == 0.5
    assert v1_p1["speedup_ratio"] == 2.0
