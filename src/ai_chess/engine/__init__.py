"""Chess engine module - orchestration of search, evaluation, and configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_chess.engine.chess_engine import ChessEngine
    from ai_chess.engine.config import EngineConfig
    from ai_chess.engine.limits import SearchLimits
    from ai_chess.engine.metrics import SearchMetrics
    from ai_chess.engine.result import SearchResult

__all__ = [
    "ChessEngine",
    "EngineConfig",
    "SearchLimits",
    "SearchMetrics",
    "SearchResult",
]


def __getattr__(name: str) -> object:
    """Lazily expose public engine classes without import cycles."""
    if name == "ChessEngine":
        from ai_chess.engine.chess_engine import ChessEngine

        return ChessEngine
    if name == "EngineConfig":
        from ai_chess.engine.config import EngineConfig

        return EngineConfig
    if name == "SearchLimits":
        from ai_chess.engine.limits import SearchLimits

        return SearchLimits
    if name == "SearchMetrics":
        from ai_chess.engine.metrics import SearchMetrics

        return SearchMetrics
    if name == "SearchResult":
        from ai_chess.engine.result import SearchResult

        return SearchResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
