"""Tests for FEN position loader."""

import csv
import tempfile
from pathlib import Path

import pytest

from ai_chess.experiments.fen_loader import load_positions_from_csv


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    """Helper to write a CSV file for testing."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class TestFenLoader:
    """Tests for load_positions_from_csv()."""

    def test_valid_csv_loads_correctly(self, tmp_path: Path) -> None:
        """Valid CSV with all required columns should load successfully."""
        csv_path = tmp_path / "positions.csv"
        _write_csv(
            csv_path,
            [
                {
                    "id": "pos1",
                    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "category": "opening",
                    "description": "Start",
                    "best_move": "e2e4",
                },
                {
                    "id": "pos2",
                    "fen": "8/5k2/8/8/8/8/3K1Q2/8 w - - 0 1",
                    "category": "endgame",
                    "description": "KQ vs K",
                    "best_move": "",
                },
            ],
            fieldnames=["id", "fen", "category", "description", "best_move"],
        )

        positions = load_positions_from_csv(csv_path)

        assert len(positions) == 2
        assert positions[0].id == "pos1"
        assert positions[0].category == "opening"
        assert positions[0].best_move == "e2e4"
        assert positions[1].best_move is None  # empty string -> None

    def test_missing_required_columns_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """CSV missing required columns should raise ValueError."""
        csv_path = tmp_path / "bad.csv"
        _write_csv(
            csv_path,
            [{"id": "pos1", "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}],
            fieldnames=["id", "fen"],  # missing 'category'
        )

        with pytest.raises(ValueError, match="missing required columns"):
            load_positions_from_csv(csv_path)

    def test_invalid_fen_raises_value_error(self, tmp_path: Path) -> None:
        """Invalid FEN string should raise ValueError."""
        csv_path = tmp_path / "invalid_fen.csv"
        _write_csv(
            csv_path,
            [
                {
                    "id": "bad_pos",
                    "fen": "not-a-valid-fen",
                    "category": "test",
                    "description": "",
                    "best_move": "",
                }
            ],
            fieldnames=["id", "fen", "category", "description", "best_move"],
        )

        with pytest.raises(ValueError, match="Invalid FEN"):
            load_positions_from_csv(csv_path)

    def test_file_not_found_raises_error(self) -> None:
        """Non-existent CSV file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_positions_from_csv("/nonexistent/path/to/file.csv")

    def test_optional_columns_have_defaults(self, tmp_path: Path) -> None:
        """Rows without optional columns should use defaults."""
        csv_path = tmp_path / "minimal.csv"
        _write_csv(
            csv_path,
            [
                {
                    "id": "pos1",
                    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "category": "opening",
                }
            ],
            fieldnames=["id", "fen", "category"],
        )

        positions = load_positions_from_csv(csv_path)

        assert len(positions) == 1
        assert positions[0].description == ""
        assert positions[0].best_move is None
