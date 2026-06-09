"""Tests for the BasicEvaluator."""

import chess
import pytest

from ai_chess.evaluation.evaluator import (
    CHECKMATE_SCORE,
    DRAW_SCORE,
    BasicEvaluator,
)


@pytest.fixture
def evaluator() -> BasicEvaluator:
    """Create a BasicEvaluator instance."""
    return BasicEvaluator()


class TestBasicEvaluator:
    """Tests for BasicEvaluator.evaluate()."""

    def test_starting_position_is_zero(self, evaluator: BasicEvaluator) -> None:
        """Starting position should evaluate to 0 (equal material)."""
        board = chess.Board()
        score = evaluator.evaluate(board)
        assert score == 0

    def test_white_extra_queen_is_positive(self, evaluator: BasicEvaluator) -> None:
        """A position where White has an extra queen should score positive."""
        # Standard position but Black's queen is removed
        board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        score = evaluator.evaluate(board)
        assert score > 0

    def test_black_extra_queen_is_negative(self, evaluator: BasicEvaluator) -> None:
        """A position where Black has an extra queen should score negative."""
        # Standard position but White's queen is removed
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w Kkq - 0 1")
        score = evaluator.evaluate(board)
        assert score < 0

    def test_stalemate_returns_zero(self, evaluator: BasicEvaluator) -> None:
        """A stalemate position should evaluate to DRAW_SCORE (0)."""
        # Black king on a1, White king on a3, White queen on b3 — Black to move, stalemate
        board = chess.Board("8/8/8/8/8/KQ6/8/k7 b - - 0 1")
        assert board.is_stalemate()
        score = evaluator.evaluate(board)
        assert score == DRAW_SCORE

    def test_checkmate_white_wins(self, evaluator: BasicEvaluator) -> None:
        """A checkmate where Black is mated should return +CHECKMATE_SCORE."""
        # Scholar's mate final position (Black is checkmated)
        board = chess.Board("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
        assert board.is_checkmate()
        score = evaluator.evaluate(board)
        assert score == CHECKMATE_SCORE

    def test_checkmate_black_wins(self, evaluator: BasicEvaluator) -> None:
        """A checkmate where White is mated should return -CHECKMATE_SCORE."""
        # Fool's mate (White is checkmated)
        board = chess.Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")
        assert board.is_checkmate()
        score = evaluator.evaluate(board)
        assert score == -CHECKMATE_SCORE
