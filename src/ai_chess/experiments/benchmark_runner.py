"""Benchmark runner for evaluating engine performance across positions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import chess

if TYPE_CHECKING:
    from ai_chess.engine.chess_engine import ChessEngine
    from ai_chess.engine.limits import SearchLimits
    from ai_chess.engine.result import SearchResult
    from ai_chess.experiments.fen_loader import TestPosition


def run_benchmark(
    positions: list[TestPosition],
    engine: ChessEngine,
    limits: SearchLimits | None = None,
) -> list[dict[str, object]]:
    """Run the engine against a set of test positions and collect results.

    For each position, the engine runs the structured search API and records
    the resulting move and metrics into a dictionary.

    Args:
        positions: A list of TestPosition objects to evaluate.
        engine: The configured ChessEngine to use.
        limits: Optional search limits to use for every position. When omitted,
            the engine's configured default limits are used.

    Returns:
        A list of dictionaries, one per position, containing
        the position metadata and search metrics.
    """
    results: list[dict[str, object]] = []

    for position in positions:
        board = chess.Board(position.fen)
        search_result: SearchResult = engine.search(board, limits)
        best_move = search_result.best_move
        metrics = search_result.metrics

        result: dict[str, object] = {
            "position_id": position.id,
            "category": position.category,
            "fen": position.fen,
            "best_move_uci": best_move.uci() if best_move else None,
            "expected_best_move": position.best_move,
            "nodes_searched": metrics.nodes_searched,
            "elapsed_seconds": metrics.elapsed_seconds,
            "depth_reached": metrics.depth_reached,
            "score": search_result.score_cp,
        }
        results.append(result)

    return results
