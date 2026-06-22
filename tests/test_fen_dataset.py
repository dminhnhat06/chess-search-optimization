"""Quality checks for the benchmark FEN dataset."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import chess

from ai_chess.experiments.fen_loader import load_positions_from_csv

DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "positions"
    / "benchmark_positions.csv"
)
REQUIRED_COLUMNS = ["id", "fen", "category", "description", "best_move"]
VALID_CATEGORIES = {
    "opening",
    "middlegame",
    "tactical",
    "check",
    "endgame",
    "quiescence",
}
MIN_POSITIONS_PER_CATEGORY = 5


def _read_rows() -> list[dict[str, str]]:
    with DATASET_PATH.open(newline="", encoding="utf-8") as csvfile:
        return list(csv.DictReader(csvfile))


def test_benchmark_positions_file_exists() -> None:
    assert DATASET_PATH.exists()


def test_benchmark_positions_have_required_columns() -> None:
    with DATASET_PATH.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames

    assert fieldnames == REQUIRED_COLUMNS


def test_benchmark_positions_load_with_public_loader() -> None:
    positions = load_positions_from_csv(DATASET_PATH)

    assert len(positions) >= len(VALID_CATEGORIES) * MIN_POSITIONS_PER_CATEGORY


def test_benchmark_positions_are_valid_and_well_categorized() -> None:
    rows = _read_rows()
    seen_ids: set[str] = set()
    category_counts: Counter[str] = Counter()

    for row in rows:
        position_id = row["id"]
        assert position_id not in seen_ids
        seen_ids.add(position_id)

        category = row["category"]
        assert category in VALID_CATEGORIES
        category_counts[category] += 1

        board = chess.Board(row["fen"])
        assert board.status() == chess.STATUS_VALID

        best_move = row["best_move"].strip()
        if best_move:
            move = chess.Move.from_uci(best_move)
            assert move in board.legal_moves

    assert set(category_counts) == VALID_CATEGORIES
    assert all(
        count >= MIN_POSITIONS_PER_CATEGORY
        for count in category_counts.values()
    )
