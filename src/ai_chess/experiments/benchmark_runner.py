"""Benchmark runner for evaluating engine performance across positions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import chess

if TYPE_CHECKING:
    from ai_chess.engine.chess_engine import ChessEngine
    from ai_chess.experiments.fen_loader import TestPosition


def run_benchmark(
    positions: list[TestPosition],
    engine: ChessEngine,
) -> list[dict[str, object]]:
    """Run the engine against a set of test positions and collect results.

    For each position, the engine finds the best move and the resulting
    metrics are recorded into a dictionary.

    Args:
        positions: A list of TestPosition objects to evaluate.
        engine: The configured ChessEngine to use.

    Returns:
        A list of dictionaries, one per position, containing
        the position metadata and search metrics.
    """
    results: list[dict[str, object]] = []

    for position in positions:
        board = chess.Board(position.fen)
        best_move, metrics = engine.find_best_move(board)

        result: dict[str, object] = {
            "position_id": position.id,
            "category": position.category,
            "fen": position.fen,
            "best_move_uci": best_move.uci() if best_move else None,
            "expected_best_move": position.best_move,
            "nodes_searched": metrics.nodes_searched,
            "elapsed_seconds": metrics.elapsed_seconds,
            "depth_reached": metrics.depth_reached,
            "score": metrics.score,
        }
        results.append(result)

    return results
