"""Minimal demo script for the AI Chess Search Optimization engine."""

import chess

from ai_chess.engine.chess_engine import ChessEngine
from ai_chess.engine.config import EngineConfig
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.search.minimax import MinimaxSearch


def main() -> None:
    """Run a simple demo of the chess engine."""
    # Setup
    board = chess.Board()
    evaluator = BasicEvaluator()
    search = MinimaxSearch()
    config = EngineConfig(max_depth=2)
    engine = ChessEngine(search_algorithm=search, evaluator=evaluator, config=config)

    # Search
    print("=" * 50)
    print("AI Chess Engine - Minimax Demo")
    print("=" * 50)
    print()
    print(f"FEN:   {board.fen()}")
    print(f"Depth: {config.max_depth}")
    print()

    best_move, metrics = engine.find_best_move(board)

    # Results
    print("--- Search Results ---")
    print(f"Best move:      {best_move}")
    print(f"Score (cp):     {metrics.score}")
    print(f"Nodes searched: {metrics.nodes_searched}")
    print(f"Depth reached:  {metrics.depth_reached}")
    print(f"Elapsed time:   {metrics.elapsed_seconds:.4f}s")
    print()

    if best_move:
        print(f"The engine suggests: {board.san(best_move)}")
    else:
        print("No legal moves available.")

    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
