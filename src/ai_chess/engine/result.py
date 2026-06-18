"""Structured search result returned by the core engine API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ai_chess.engine.metrics import SearchMetrics

if TYPE_CHECKING:
    import chess


@dataclass
class SearchResult:
    """Result of one engine search call."""

    best_move: chess.Move | None
    ponder_move: chess.Move | None = None
    score_cp: int | None = None
    mate_in: int | None = None
    depth: int = 0
    seldepth: int | None = None
    nodes: int = 0
    nps: int = 0
    elapsed_ms: int = 0
    pv: list[chess.Move] = field(default_factory=list)
    metrics: SearchMetrics = field(default_factory=SearchMetrics)
