"""Console demo for the package-level engine presets."""

from __future__ import annotations

import chess

from ai_chess.engine.limits import SearchLimits
from ai_chess.presets import make_engine


def run_demo(*, preset: str = "v0_minimax", depth: int = 2) -> None:
    """Run a small deterministic search demo from the starting position."""
    board = chess.Board()
    engine = make_engine(preset, max_depth=depth)

    print("=" * 50)
    print("AI Chess Engine - Search Demo")
    print("=" * 50)
    print()
    print(f"Preset: {preset}")
    print(f"FEN:    {board.fen()}")
    print(f"Depth:  {depth}")
    print()

    result = engine.search(board, SearchLimits(depth=depth))

    print("--- Search Results ---")
    print(f"Best move:      {result.best_move}")
    print(f"Score (cp):     {result.score_cp}")
    print(f"Nodes searched: {result.nodes}")
    print(f"Depth reached:  {result.depth}")
    print(f"Elapsed time:   {result.elapsed_ms}ms")
    print()

    if result.best_move:
        print(f"The engine suggests: {board.san(result.best_move)}")
    else:
        print("No legal moves available.")

    print()
    print("=" * 50)


def main() -> None:
    """Run the default demo."""
    run_demo()


if __name__ == "__main__":
    main()
