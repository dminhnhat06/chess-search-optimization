"""Search module - search algorithms for finding best moves."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_chess.search.alpha_beta import AlphaBetaSearch
    from ai_chess.search.iterative_deepening import IterativeDeepeningSearch
    from ai_chess.search.minimax import MinimaxSearch
    from ai_chess.search.quiescence import QuiescenceSearch

__all__ = [
    "AlphaBetaSearch",
    "IterativeDeepeningSearch",
    "MinimaxSearch",
    "QuiescenceSearch",
]


def __getattr__(name: str) -> object:
    """Lazily expose search classes without initializing every algorithm."""
    if name == "AlphaBetaSearch":
        from ai_chess.search.alpha_beta import AlphaBetaSearch

        return AlphaBetaSearch
    if name == "IterativeDeepeningSearch":
        from ai_chess.search.iterative_deepening import IterativeDeepeningSearch

        return IterativeDeepeningSearch
    if name == "MinimaxSearch":
        from ai_chess.search.minimax import MinimaxSearch

        return MinimaxSearch
    if name == "QuiescenceSearch":
        from ai_chess.search.quiescence import QuiescenceSearch

        return QuiescenceSearch
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
