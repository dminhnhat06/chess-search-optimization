"""FEN position loader for experiment benchmarks."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import chess

REQUIRED_COLUMNS = {"id", "fen", "category"}


@dataclass
class TestPosition:
    """A chess test position loaded from CSV.

    Attributes:
        id: Unique identifier for the position.
        fen: FEN string representing the board state.
        category: Category label (e.g., 'opening', 'middlegame', 'endgame').
        description: Optional human-readable description.
        best_move: Optional expected best move in UCI notation.
    """

    id: str
    fen: str
    category: str
    description: str = ""
    best_move: str | None = None


def load_positions_from_csv(path: str | Path) -> list[TestPosition]:
    """Load test positions from a CSV file.

    Expected CSV columns: id, fen, category, description (optional),
    best_move (optional).

    Args:
        path: Path to the CSV file.

    Returns:
        A list of validated TestPosition objects.

    Raises:
        ValueError: If required columns are missing or a FEN is invalid.
        FileNotFoundError: If the CSV file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    positions: list[TestPosition] = []

    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row.")

        header_set = set(reader.fieldnames)
        missing = REQUIRED_COLUMNS - header_set
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {sorted(missing)}"
            )

        for row_num, row in enumerate(reader, start=2):
            pos_id = row["id"].strip()
            fen = row["fen"].strip()
            category = row["category"].strip()
            description = row.get("description", "").strip()
            best_move = row.get("best_move", "").strip() or None

            # Validate FEN by attempting to create a board
            try:
                chess.Board(fen)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid FEN at row {row_num} (id='{pos_id}'): {exc}"
                ) from exc

            positions.append(
                TestPosition(
                    id=pos_id,
                    fen=fen,
                    category=category,
                    description=description,
                    best_move=best_move,
                )
            )

    return positions
