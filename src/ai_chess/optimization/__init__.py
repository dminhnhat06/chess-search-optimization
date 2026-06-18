"""Optimization module - move ordering, transposition tables, and search control."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_chess.optimization.move_ordering import order_moves
    from ai_chess.optimization.search_controller import SearchController
    from ai_chess.optimization.transposition_table import (
        EXACT,
        LOWER_BOUND,
        UPPER_BOUND,
        TranspositionTable,
        TTEntry,
        compute_board_hash,
    )

__all__ = [
    "EXACT",
    "LOWER_BOUND",
    "SearchController",
    "TTEntry",
    "TranspositionTable",
    "UPPER_BOUND",
    "compute_board_hash",
    "order_moves",
]


def __getattr__(name: str) -> object:
    """Lazily expose optimization helpers without import cycles."""
    if name == "order_moves":
        from ai_chess.optimization.move_ordering import order_moves

        return order_moves
    if name == "SearchController":
        from ai_chess.optimization.search_controller import SearchController

        return SearchController
    if name in {"EXACT", "LOWER_BOUND", "UPPER_BOUND"}:
        from ai_chess.optimization import transposition_table

        return getattr(transposition_table, name)
    if name == "TTEntry":
        from ai_chess.optimization.transposition_table import TTEntry

        return TTEntry
    if name == "TranspositionTable":
        from ai_chess.optimization.transposition_table import TranspositionTable

        return TranspositionTable
    if name == "compute_board_hash":
        from ai_chess.optimization.transposition_table import compute_board_hash

        return compute_board_hash
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
