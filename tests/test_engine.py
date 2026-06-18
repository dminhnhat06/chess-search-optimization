"""Tests for ChessEngine."""

import chess
import pytest

from ai_chess.engine.chess_engine import ChessEngine
from ai_chess.engine.config import EngineConfig
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.search.minimax import MinimaxSearch


@pytest.fixture
def engine() -> ChessEngine:
    """Create a ChessEngine with default minimax search."""
    return ChessEngine(
        search_algorithm=MinimaxSearch(),
        evaluator=BasicEvaluator(),
        config=EngineConfig(max_depth=2),
    )


class TestChessEngine:
    """Tests for ChessEngine.find_best_move()."""

    def test_returns_tuple(self, engine: ChessEngine) -> None:
        """find_best_move should return a tuple of (move, metrics)."""
        board = chess.Board()
        result = engine.find_best_move(board)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returned_move_is_legal(self, engine: ChessEngine) -> None:
        """The returned move should be legal in the original position."""
        board = chess.Board()
        move, metrics = engine.find_best_move(board)

        assert move is not None
        assert move in board.legal_moves

    def test_returned_move_is_none_when_checkmated(self) -> None:
        """Should return None for a checkmated position."""
        engine = ChessEngine(
            search_algorithm=MinimaxSearch(),
            config=EngineConfig(max_depth=1),
        )
        # Fool's mate - White is checkmated
        board = chess.Board(
            "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        )
        move, metrics = engine.find_best_move(board)

        assert move is None

    def test_metrics_reset_between_searches(self, engine: ChessEngine) -> None:
        """Metrics should be fresh (reset) for each search call."""
        board = chess.Board()

        _, metrics1 = engine.find_best_move(board)
        _, metrics2 = engine.find_best_move(board)

        # Both should have independent, positive node counts
        assert metrics1.nodes_searched > 0
        assert metrics2.nodes_searched > 0
        # They should be separate objects
        assert metrics1 is not metrics2

    def test_metrics_contain_expected_fields(self, engine: ChessEngine) -> None:
        """Metrics should contain all expected fields after a search."""
        board = chess.Board()
        _, metrics = engine.find_best_move(board)

        result_dict = metrics.to_dict()
        expected_keys = {
            "nodes_searched", "cutoffs", "tt_hits", "depth_reached",
            "elapsed_seconds", "best_move", "score",
        }
        assert expected_keys <= set(result_dict.keys())

    def test_defaults_used_when_none_provided(self) -> None:
        """Engine should use default evaluator and config when None."""
        engine = ChessEngine(search_algorithm=MinimaxSearch())
        board = chess.Board()
        move, metrics = engine.find_best_move(board)

        assert move is not None
        assert metrics.nodes_searched > 0
