"""Entry point for running the UCI engine: ``python -m ai_chess.uci``."""

from __future__ import annotations

import sys

from ai_chess.uci.session import UCISession


def main() -> None:
    """Start the UCI session with standard I/O streams."""
    session = UCISession(input_stream=sys.stdin, output_stream=sys.stdout)
    session.run()


if __name__ == "__main__":
    main()
