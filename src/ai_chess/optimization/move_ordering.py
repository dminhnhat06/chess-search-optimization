"""Move ordering heuristics for search optimization."""

from __future__ import annotations

import chess


def order_moves(board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
    """Order moves to improve search efficiency.

    Current ordering priority:
    1. Captures (highest priority)
    2. Promotions
    3. Quiet moves (lowest priority)

    This simple ordering is a placeholder. Future versions may use
    MVV-LVA (Most Valuable Victim - Least Valuable Attacker),
    killer moves, history heuristic, etc.

    Args:
        board: The current chess board state.
        moves: List of legal moves to order.

    Returns:
        A new list of moves sorted by the ordering heuristic.
    """

    def move_priority(move: chess.Move) -> int:
        """Assign a sorting priority to a move (lower = higher priority)."""
        if board.is_capture(move):
            return 0
        if move.promotion is not None:
            return 1
        return 2

    return sorted(moves, key=move_priority)
