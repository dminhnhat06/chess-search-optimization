"""UCI protocol response formatters.

Provides pure functions that format engine output into UCI-compliant
response strings. Each function returns a string (or list of strings)
ready to be sent to the GUI via stdout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import chess


def uci_id(name: str, author: str) -> list[str]:
    """Format the UCI identification response.

    Sent in reply to the 'uci' command. Includes engine name, author,
    and the mandatory 'uciok' terminator.

    Args:
        name: The engine name.
        author: The engine author.

    Returns:
        A list of response lines: ['id name ...', 'id author ...', 'uciok'].
    """
    return [
        f"id name {name}",
        f"id author {author}",
        "uciok",
    ]


def ready_ok() -> str:
    """Format the 'readyok' response.

    Sent in reply to the 'isready' command to confirm the engine
    is ready to accept further commands.

    Returns:
        The string 'readyok'.
    """
    return "readyok"


def best_move(move: chess.Move | None) -> str:
    """Format the 'bestmove' response.

    Args:
        move: The best move found, or None if no legal moves exist.

    Returns:
        A string like 'bestmove e2e4' or 'bestmove 0000' if no move.
    """
    if move is None:
        return "bestmove 0000"
    return f"bestmove {move.uci()}"


def info(
    *,
    depth: int | None = None,
    score_cp: int | None = None,
    nodes: int | None = None,
    time_ms: int | None = None,
    pv: list[chess.Move] | None = None,
) -> str:
    """Format an 'info' response with search progress data.

    All parameters are optional; only provided fields are included
    in the output string.

    Args:
        depth: The search depth reached.
        score_cp: The evaluation score in centipawns.
        nodes: The number of nodes searched.
        time_ms: The elapsed search time in milliseconds.
        pv: The principal variation (list of moves).

    Returns:
        A formatted 'info' string, e.g.:
        'info depth 3 score cp 25 nodes 1234 time 56 pv e2e4 e7e5'.
    """
    parts: list[str] = ["info"]

    if depth is not None:
        parts.append(f"depth {depth}")

    if score_cp is not None:
        parts.append(f"score cp {score_cp}")

    if nodes is not None:
        parts.append(f"nodes {nodes}")

    if time_ms is not None:
        parts.append(f"time {time_ms}")

    if pv:
        pv_str = " ".join(m.uci() for m in pv)
        parts.append(f"pv {pv_str}")

    return " ".join(parts)
