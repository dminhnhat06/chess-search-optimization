"""Transposition table for caching evaluated positions."""

from __future__ import annotations

from dataclasses import dataclass

import chess


# Flag constants for transposition table entries
EXACT = "EXACT"
LOWER_BOUND = "LOWER_BOUND"
UPPER_BOUND = "UPPER_BOUND"


@dataclass
class TTEntry:
    """A single entry in the transposition table.

    Attributes:
        depth: The search depth at which this entry was recorded.
        score: The evaluation score stored.
        best_move_uci: The best move found, in UCI notation (or None).
        flag: One of EXACT, LOWER_BOUND, or UPPER_BOUND.
    """

    depth: int
    score: int
    best_move_uci: str | None
    flag: str


def compute_board_hash(board: chess.Board) -> int:
    """Compute a hash for the given board position.

    Uses python-chess's Zobrist hashing if available, otherwise
    falls back to hashing the FEN string. The fallback is isolated
    here so it can be replaced later.

    Args:
        board: The chess board to hash.

    Returns:
        An integer hash of the board position.
    """
    try:
        return chess.polyglot.zobrist_hash(board)
    except AttributeError:
        return hash(board.fen())


class TranspositionTable:
    """Hash table storing previously evaluated positions.

    Maps board position hashes to TTEntry objects for reuse
    during search. This avoids re-evaluating positions that
    have already been seen via a different move order.
    """

    def __init__(self) -> None:
        """Initialize an empty transposition table."""
        self._table: dict[int, TTEntry] = {}

    def get(self, key: int) -> TTEntry | None:
        """Look up an entry by its position hash.

        Args:
            key: The Zobrist or FEN-based hash of the position.

        Returns:
            The stored TTEntry, or None if not found.
        """
        return self._table.get(key)

    def store(self, key: int, entry: TTEntry) -> None:
        """Store an entry in the transposition table.

        Args:
            key: The position hash.
            entry: The TTEntry to store.
        """
        self._table[key] = entry

    def clear(self) -> None:
        """Remove all entries from the transposition table."""
        self._table.clear()

    def size(self) -> int:
        """Return the number of entries currently stored.

        Returns:
            The number of entries in the table.
        """
        return len(self._table)
