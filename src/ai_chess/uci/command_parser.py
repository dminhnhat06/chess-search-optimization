"""Stateless parser for UCI protocol commands.

Converts raw UCI command strings into structured UCICommand objects.
Each command carries a name and a dictionary of parsed parameters,
making downstream handling straightforward and testable.
"""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field


@dataclass(frozen=True)
class UCICommand:
    """A parsed UCI command.

    Attributes:
        name: The command name (e.g., 'uci', 'position', 'go', 'quit').
        params: Dictionary of parsed parameters specific to the command.
    """

    name: str
    params: dict[str, object] = field(default_factory=dict)


def parse_command(line: str) -> UCICommand:
    """Parse a raw UCI command string into a UCICommand.

    Handles all standard UCI commands:
        uci, isready, ucinewgame, position, setoption, go, stop, quit.

    Args:
        line: A single line of UCI input (e.g., 'position startpos moves e2e4').

    Returns:
        A UCICommand with the command name and parsed parameters.
        Unrecognized commands return a UCICommand with the original name
        and empty params.
    """
    tokens = line.strip().split()
    if not tokens:
        return UCICommand(name="")

    name = tokens[0].lower()

    if name == "position":
        return _parse_position(tokens)
    if name == "setoption":
        return _parse_setoption(tokens)
    if name == "go":
        return _parse_go(tokens)

    # Simple commands: uci, isready, ucinewgame, stop, quit
    return UCICommand(name=name)


def _parse_position(tokens: list[str]) -> UCICommand:
    """Parse a 'position' command.

    Supported formats::

        position startpos
        position startpos moves e2e4 e7e5 ...
        position fen <fen_string>
        position fen <fen_string> moves e2e4 ...

    Args:
        tokens: The tokenized command line.

    Returns:
        UCICommand with params:
            - 'fen': The FEN string (or 'startpos' for the initial position).
            - 'moves': List of move strings in UCI notation.
    """
    params: dict[str, object] = {"fen": "", "moves": []}

    if len(tokens) < 2:
        return UCICommand(name="position", params=params)

    idx = 1

    if tokens[idx] == "startpos":
        params["fen"] = "startpos"
        idx += 1
    elif tokens[idx] == "fen":
        idx += 1
        # FEN consists of up to 6 space-separated fields; collect until
        # 'moves' keyword or end of tokens.
        fen_parts: list[str] = []
        while idx < len(tokens) and tokens[idx] != "moves":
            fen_parts.append(tokens[idx])
            idx += 1
        params["fen"] = " ".join(fen_parts)

    # Parse moves if present
    if idx < len(tokens) and tokens[idx] == "moves":
        idx += 1
        params["moves"] = tokens[idx:]

    return UCICommand(name="position", params=params)


def _parse_setoption(tokens: list[str]) -> UCICommand:
    """Parse a 'setoption' command.

    Supported format::

        setoption name <option name> [value <option value>]
    """
    params: dict[str, object] = {}
    if len(tokens) < 3 or tokens[1].lower() != "name":
        return UCICommand(name="setoption", params=params)

    idx = 2
    name_parts: list[str] = []
    while idx < len(tokens) and tokens[idx].lower() != "value":
        name_parts.append(tokens[idx])
        idx += 1

    if name_parts:
        params["name"] = " ".join(name_parts)

    if idx < len(tokens) and tokens[idx].lower() == "value":
        value_parts = tokens[idx + 1 :]
        if value_parts:
            params["value"] = " ".join(value_parts)

    return UCICommand(name="setoption", params=params)


def _parse_go(tokens: list[str]) -> UCICommand:
    """Parse a 'go' command.

    Supported sub-commands::

        go depth <n>
        go movetime <ms>
        go wtime <ms> btime <ms> [winc <ms>] [binc <ms>]
        go infinite
        go              (no arguments — treated as infinite)

    Args:
        tokens: The tokenized command line.

    Returns:
        UCICommand with params containing any of:
            - 'depth': int
            - 'movetime': int (milliseconds)
            - 'wtime', 'btime', 'winc', 'binc': int (milliseconds)
            - 'infinite': True
    """
    params: dict[str, object] = {}

    # Keywords that take an integer argument
    int_keywords = {
        "depth",
        "movetime",
        "nodes",
        "wtime",
        "btime",
        "winc",
        "binc",
        "movestogo",
    }

    idx = 1
    while idx < len(tokens):
        token = tokens[idx].lower()

        if token == "infinite":
            params["infinite"] = True
            idx += 1
        elif token in int_keywords and idx + 1 < len(tokens):
            with suppress(ValueError):
                params[token] = int(tokens[idx + 1])
            idx += 2
        else:
            idx += 1

    return UCICommand(name="go", params=params)
