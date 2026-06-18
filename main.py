"""Minimal demo script for the AI Chess Search Optimization engine."""

import chess

from ai_chess.engine.limits import SearchLimits
from ai_chess.presets.factory import make_engine


def main() -> None:
    """Run a simple demo of the chess engine."""
    board = chess.Board()
    preset = "v3_alpha_beta_ordering_tt"
    depth = 2
    engine = make_engine(preset, max_depth=depth)

    print("=" * 50)
    print("AI Chess Engine - Core API Demo")
    print("=" * 50)
    print()
    print(f"FEN:   {board.fen()}")
    print(f"Preset: {preset}")
    print(f"Depth:  {depth}")
    print()

    result = engine.search(board, SearchLimits(depth=depth))
    best_move = result.best_move
    metrics = result.metrics

    print("--- Search Results ---")
    print(f"Best move:      {best_move}")
    print(f"Score (cp):     {result.score_cp}")
    print(f"Nodes searched: {result.nodes}")
    print(f"Depth reached:  {result.depth}")
    print(f"Elapsed time:   {result.elapsed_ms}ms")
    print(f"Cutoffs:        {metrics.cutoffs}")
    print(f"TT hits:        {metrics.tt_hits}")
    print()

    if best_move:
        print(f"The engine suggests: {board.san(best_move)}")
    else:
        print("No legal moves available.")

    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
