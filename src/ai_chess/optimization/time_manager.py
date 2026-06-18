"""Time allocation helper for engine callers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_chess.optimization.search_controller import SearchController

if TYPE_CHECKING:
    import chess

    from ai_chess.engine.limits import SearchLimits


def make_search_controller(
    limits: SearchLimits,
    move_overhead_ms: int = 20,
    side_to_move: chess.Color | None = None,
) -> SearchController:
    """Create a :class:`SearchController` for a search call."""
    return SearchController(limits, move_overhead_ms, side_to_move)
