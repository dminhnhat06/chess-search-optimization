"""Transposition table for caching evaluated positions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import chess
import chess.polyglot

if TYPE_CHECKING:
    from ai_chess.engine.metrics import SearchMetrics

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
    best_move_uci: str | None = None
    flag: str = EXACT
    key: int | None = None
    best_move: chess.Move | None = None

    def __post_init__(self) -> None:
        """Keep move object and UCI string representations in sync."""
        if self.best_move is None and self.best_move_uci is not None:
            try:
                self.best_move = chess.Move.from_uci(self.best_move_uci)
            except ValueError:
                self.best_move = None
        if self.best_move is not None and self.best_move_uci is None:
            self.best_move_uci = self.best_move.uci()


def compute_board_hash(board: chess.Board) -> int:
    """Compute a hash for the given board position.

    Uses python-chess's Polyglot Zobrist hashing.

    Args:
        board: The chess board to hash.

    Returns:
        An integer hash of the board position.
    """
    return chess.polyglot.zobrist_hash(board)


class TranspositionTable:
    """Hash table storing previously evaluated positions.

    Maps board position hashes to TTEntry objects for reuse
    during search. This avoids re-evaluating positions that
    have already been seen via a different move order.
    """

    def __init__(self, hash_size_mb: int = 64) -> None:
        """Initialize an empty transposition table.

        A hash size of zero disables storage while keeping probe/store methods
        safe to call.
        """
        self._table: dict[int, TTEntry] = {}
        self.hash_size_mb = hash_size_mb
        if hash_size_mb <= 0:
            self._capacity: int | None = 0
        else:
            self._capacity = max(1, (hash_size_mb * 1024 * 1024) // 64)

    def get(self, key: int) -> TTEntry | None:
        """Look up an entry by its position hash.

        Args:
            key: The Zobrist or FEN-based hash of the position.

        Returns:
            The stored TTEntry, or None if not found.
        """
        return self._table.get(key)

    def probe(
        self,
        key: int,
        metrics: SearchMetrics | None = None,
    ) -> TTEntry | None:
        """Look up an entry and update TT probe/hit metrics when supplied."""
        if metrics is not None:
            metrics.tt_probes += 1

        entry = self._table.get(key)
        if entry is not None and metrics is not None:
            metrics.tt_hits += 1
        return entry

    def store(self, key: int, entry: TTEntry) -> None:
        """Store an entry in the transposition table.

        Args:
            key: The position hash.
            entry: The TTEntry to store.
        """
        if self._capacity == 0:
            return

        entry.key = key
        if entry.best_move is not None:
            entry.best_move_uci = entry.best_move.uci()

        existing = self._table.get(key)
        if existing is not None and existing.depth > entry.depth:
            return

        if existing is None and self._capacity is not None:
            self._make_room(entry.depth)
            if len(self._table) >= self._capacity:
                return

        self._table[key] = entry

    def store_with_metrics(
        self,
        key: int,
        entry: TTEntry,
        metrics: SearchMetrics | None = None,
    ) -> None:
        """Store an entry and update observable TT metrics."""
        old_size = len(self._table)
        self.store(key, entry)
        if metrics is not None and (
            self._table.get(key) is entry or len(self._table) > old_size
        ):
            metrics.tt_stores += 1
            # The dict is keyed by the full hash value, so this implementation
            # cannot observe lower-level hash bucket collisions. The metric is
            # reserved for future fixed-size/indexed table implementations.

    def clear(self) -> None:
        """Remove all entries from the transposition table."""
        self._table.clear()

    def size(self) -> int:
        """Return the number of entries currently stored.

        Returns:
            The number of entries in the table.
        """
        return len(self._table)

    def _make_room(self, new_depth: int) -> None:
        if self._capacity is None or len(self._table) < self._capacity:
            return

        shallow_key: int | None = None
        shallow_depth: int | None = None
        for key, value in self._table.items():
            if shallow_depth is None or value.depth < shallow_depth:
                shallow_key = key
                shallow_depth = value.depth

        if (
            shallow_key is not None
            and shallow_depth is not None
            and new_depth >= shallow_depth
        ):
            del self._table[shallow_key]
