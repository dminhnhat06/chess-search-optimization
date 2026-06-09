"""Board evaluation for chess positions."""

from __future__ import annotations

import chess

from ai_chess.evaluation.piece_values import PIECE_VALUES

# Score constants
CHECKMATE_SCORE = 1_000_000
DRAW_SCORE = 0


class BasicEvaluator:
    """Evaluates chess positions from White's perspective.

    A positive score indicates White is better; a negative score
    indicates Black is better. Checkmate and draw are handled
    as special cases.

    The initial implementation uses material counting only.
    The design is open for extension with positional, mobility,
    and king safety scoring in future versions.
    """

    def evaluate(self, board: chess.Board) -> int:
        """Evaluate the board position from White's perspective.

        Args:
            board: The current chess board state.

        Returns:
            An integer score in centipawns. Positive favors White,
            negative favors Black.
        """
        # Handle terminal states
        if board.is_checkmate():
            # The side to move is checkmated
            if board.turn == chess.WHITE:
                # White is checkmated -> Black wins
                return -CHECKMATE_SCORE
            else:
                # Black is checkmated -> White wins
                return CHECKMATE_SCORE

        if board.is_stalemate() or board.is_insufficient_material():
            return DRAW_SCORE

        if board.can_claim_draw():
            return DRAW_SCORE

        # Material evaluation
        return self._evaluate_material(board)

    def _evaluate_material(self, board: chess.Board) -> int:
        """Count material balance from White's perspective.

        Args:
            board: The current chess board state.

        Returns:
            Material score in centipawns.
        """
        score = 0
        for piece_type, value in PIECE_VALUES.items():
            white_pieces = len(board.pieces(piece_type, chess.WHITE))
            black_pieces = len(board.pieces(piece_type, chess.BLACK))
            score += value * (white_pieces - black_pieces)
        return score
