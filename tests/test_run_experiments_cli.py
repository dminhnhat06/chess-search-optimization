"""CLI tests for scripts/run_experiments.py."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from ai_chess.experiments.benchmark_runner import BENCHMARK_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_experiments.py"


def _write_positions(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["id", "fen", "category", "description", "best_move"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "id": "start",
                "fen": (
                    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/"
                    "RNBQKBNR w KQkq - 0 1"
                ),
                "category": "opening",
                "description": "start",
                "best_move": "",
            }
        )


def test_run_experiments_cli_writes_csv_with_expected_header(
    tmp_path: Path,
) -> None:
    positions_path = tmp_path / "positions.csv"
    output_path = tmp_path / "results" / "benchmark.csv"
    _write_positions(positions_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--positions",
            str(positions_path),
            "--output",
            str(output_path),
            "--depths",
            "1",
            "--presets",
            "v0_minimax",
            "--repeats",
            "1",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Wrote 1 benchmark rows" in completed.stdout
    with output_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    assert reader.fieldnames == list(BENCHMARK_FIELDS)
    assert len(rows) == 1
    assert rows[0]["preset"] == "v0_minimax"
    assert rows[0]["depth"] == "1"


def test_run_experiments_cli_writes_valid_json(tmp_path: Path) -> None:
    positions_path = tmp_path / "positions.csv"
    output_path = tmp_path / "results" / "benchmark.json"
    _write_positions(positions_path)

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--positions",
            str(positions_path),
            "--output",
            str(output_path),
            "--depths",
            "1",
            "--presets",
            "v0_minimax",
            "--repeats",
            "1",
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    rows = json.loads(output_path.read_text(encoding="utf-8"))

    assert isinstance(rows, list)
    assert len(rows) == 1
    assert list(rows[0]) == list(BENCHMARK_FIELDS)
    assert rows[0]["preset"] == "v0_minimax"
