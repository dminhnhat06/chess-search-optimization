"""Move ordering heuristics for search optimization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import chess

from ai_chess.evaluation.piece_values import PIECE_VALUES

if TYPE_CHECKING:
    from collections.abc import Iterable


def order_moves(
    board: chess.Board,
    moves: Iterable[chess.Move],
    preferred_move: chess.Move | None = None,
) -> list[chess.Move]:
    """Order moves to improve search efficiency.

    Ordering priority:
    1. Preferred move, if present in *moves*
    2. Captures scored by MVV-LVA
    2. Promotions
    3. Checking moves
    4. Remaining moves by UCI string

    Args:
        board: The current chess board state.
        moves: List of legal moves to order.
        preferred_move: Move to place first when it is legal.

    Returns:
        A new list of moves sorted by the ordering heuristic.
    """
    move_list = list(moves)
    preferred = preferred_move if preferred_move in move_list else None

    def move_priority(move: chess.Move) -> tuple[int, int, str]:
        """Assign a sorting priority to a move."""
        if preferred is not None and move == preferred:
            return (0, 0, move.uci())
        if board.is_capture(move):
            return (1, -_mvv_lva_score(board, move), move.uci())
        if move.promotion is not None:
            return (2, -PIECE_VALUES.get(move.promotion, 0), move.uci())
        if board.gives_check(move):
            return (3, 0, move.uci())
        return (4, 0, move.uci())

    return sorted(move_list, key=move_priority)


def _mvv_lva_score(board: chess.Board, move: chess.Move) -> int:
    """Return a deterministic Most Valuable Victim - Least Valuable Attacker score."""
    victim = board.piece_at(move.to_square)
    if victim is None and board.is_en_passant(move):
        victim_value = PIECE_VALUES[chess.PAWN]
    else:
        victim_value = PIECE_VALUES.get(victim.piece_type, 0) if victim else 0

    attacker = board.piece_at(move.from_square)
    attacker_value = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
    promotion_bonus = PIECE_VALUES.get(move.promotion, 0) if move.promotion else 0
    return victim_value * 10 - attacker_value + promotion_bonus
