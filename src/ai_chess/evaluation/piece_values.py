"""Piece values in centipawns for material evaluation."""

from __future__ import annotations

import chess

# Basic piece values in centipawns
PAWN = 100
KNIGHT = 320
BISHOP = 330
ROOK = 500
QUEEN = 900
KING = 0

# Mapping from chess.PieceType to centipawn value
PIECE_VALUES: dict[int, int] = {
    chess.PAWN: PAWN,
    chess.KNIGHT: KNIGHT,
    chess.BISHOP: BISHOP,
    chess.ROOK: ROOK,
    chess.QUEEN: QUEEN,
    chess.KING: KING,
}
