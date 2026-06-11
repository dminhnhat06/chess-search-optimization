"""UCI (Universal Chess Interface) protocol layer.

This subpackage provides a clean UCI interface for the chess engine,
enabling integration with standard chess GUIs such as Arena, Cute Chess,
and Lichess Bot.

Usage::

    python -m ai_chess.uci

Architecture:
    - command_parser: Stateless parsing of UCI command strings.
    - response: Formatting of UCI protocol responses.
    - session: Stateful UCI session loop coordinating parser, engine, and I/O.
"""

from ai_chess.uci.session import UCISession

__all__ = ["UCISession"]
