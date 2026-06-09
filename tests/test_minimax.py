"""Tests for MinimaxSearch."""

import chess
import pytest

from ai_chess.engine.config import EngineConfig
from ai_chess.engine.metrics import SearchMetrics
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.search.minimax import MinimaxSearch


@pytest.fixture
def minimax() -> MinimaxSearch:
    """Create a MinimaxSearch instance."""
    return MinimaxSearch()


@pytest.fixture
def evaluator() -> BasicEvaluator:
    """Create a BasicEvaluator instance."""
    return BasicEvaluator()


class TestMinimaxSearch:
    """Tests for MinimaxSearch.find_best_move()."""

    def test_returns_legal_move_from_starting_position(
        self,
        minimax: MinimaxSearch,
        evaluator: BasicEvaluator,
    ) -> None:
        """Minimax should return a legal move from the starting position."""
        board = chess.Board()
        config = EngineConfig(max_depth=2)
        metrics = SearchMetrics()

        move = minimax.find_best_move(board, evaluator, config, metrics)

        assert move is not None
        assert move in board.legal_moves

    def test_board_fen_unchanged_after_search(
        self,
        minimax: MinimaxSearch,
        evaluator: BasicEvaluator,
    ) -> None:
        """The board FEN should be identical before and after searching."""
        board = chess.Board()
        original_fen = board.fen()
        config = EngineConfig(max_depth=2)
        metrics = SearchMetrics()

        minimax.find_best_move(board, evaluator, config, metrics)

        assert board.fen() == original_fen

    def test_nodes_searched_is_positive(
        self,
        minimax: MinimaxSearch,
        evaluator: BasicEvaluator,
    ) -> None:
        """nodes_searched must be > 0 after a search."""
        board = chess.Board()
        config = EngineConfig(max_depth=2)
        metrics = SearchMetrics()

        minimax.find_best_move(board, evaluator, config, metrics)

        assert metrics.nodes_searched > 0

    def test_depth_reached_matches_config(
        self,
        minimax: MinimaxSearch,
        evaluator: BasicEvaluator,
    ) -> None:
        """depth_reached should match the configured max_depth."""
        board = chess.Board()
        config = EngineConfig(max_depth=3)
        metrics = SearchMetrics()

        minimax.find_best_move(board, evaluator, config, metrics)

        assert metrics.depth_reached == config.max_depth

    def test_returns_none_when_no_legal_moves(
        self,
        minimax: MinimaxSearch,
        evaluator: BasicEvaluator,
    ) -> None:
        """Should return None when there are no legal moves (checkmate)."""
        # Fool's mate position - White is checkmated
        board = chess.Board(
            "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        )
        assert board.is_checkmate()
        config = EngineConfig(max_depth=2)
        metrics = SearchMetrics()

        move = minimax.find_best_move(board, evaluator, config, metrics)

        assert move is None

    def test_best_move_and_score_set_in_metrics(
        self,
        minimax: MinimaxSearch,
        evaluator: BasicEvaluator,
    ) -> None:
        """Metrics should have best_move and score set after search."""
        board = chess.Board()
        config = EngineConfig(max_depth=2)
        metrics = SearchMetrics()

        minimax.find_best_move(board, evaluator, config, metrics)

        assert metrics.best_move is not None
        assert metrics.score is not None
        assert metrics.elapsed_seconds > 0
