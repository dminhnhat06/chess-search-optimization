"""UCI session — stateful command loop coordinating parser, engine, and I/O.

The UCISession manages the lifecycle of a single UCI connection:
board state, engine instance, and the read-parse-dispatch-respond loop.
I/O streams are injected via the constructor so the session can be tested
with ``io.StringIO`` without mocking ``sys.stdin``/``sys.stdout``.
"""

from __future__ import annotations

import sys
from typing import TextIO

import chess

from ai_chess.engine.chess_engine import ChessEngine
from ai_chess.engine.config import EngineConfig
from ai_chess.engine.limits import SearchLimits
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.search.minimax import MinimaxSearch
from ai_chess.uci.command_parser import UCICommand, parse_command
from ai_chess.uci.response import best_move, info, ready_ok, uci_id

# Default search depth when 'go' is issued without depth or time params.
_DEFAULT_DEPTH = 4


class UCISession:
    """Manages a single UCI protocol session.

    Reads lines from *input_stream*, dispatches each parsed command
    to the appropriate handler, and writes responses to *output_stream*.

    Attributes:
        board: The current chess board state.
        engine: The chess engine instance used for search.
    """

    def __init__(
        self,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        """Initialize the UCI session.

        Args:
            input_stream: Readable text stream for UCI commands.
                Defaults to ``sys.stdin``.
            output_stream: Writable text stream for UCI responses.
                Defaults to ``sys.stdout``.
        """
        self._input = input_stream or sys.stdin
        self._output = output_stream or sys.stdout
        self.board = chess.Board()
        self.engine = ChessEngine(
            search_algorithm=MinimaxSearch(),
            evaluator=BasicEvaluator(),
            config=EngineConfig(max_depth=_DEFAULT_DEPTH),
        )
        self._running = False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Run the UCI command loop until 'quit' or EOF.

        Reads one line at a time, parses it, and dispatches to the
        matching handler. Unrecognized commands are silently ignored
        per the UCI specification.
        """
        self._running = True

        while self._running:
            try:
                line = self._input.readline()
            except EOFError:
                break

            if not line:
                # EOF reached
                break

            line = line.strip()
            if not line:
                continue

            cmd = parse_command(line)
            self._dispatch(cmd)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, cmd: UCICommand) -> None:
        """Route a parsed command to its handler.

        Args:
            cmd: The parsed UCI command.
        """
        handler = {
            "uci": self._handle_uci,
            "isready": self._handle_isready,
            "ucinewgame": self._handle_ucinewgame,
            "position": self._handle_position,
            "go": self._handle_go,
            "stop": self._handle_stop,
            "quit": self._handle_quit,
        }.get(cmd.name)

        if handler is not None:
            handler(cmd)

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    def _handle_uci(self, _cmd: UCICommand) -> None:
        """Handle the 'uci' command — send engine identification."""
        lines = uci_id(self.engine.name, self.engine.author)
        for line in lines:
            self._send(line)

    def _handle_isready(self, _cmd: UCICommand) -> None:
        """Handle the 'isready' command — confirm engine readiness."""
        self._send(ready_ok())

    def _handle_ucinewgame(self, _cmd: UCICommand) -> None:
        """Handle the 'ucinewgame' command — reset for a new game."""
        self.board = chess.Board()
        self.engine.new_game()

    def _handle_position(self, cmd: UCICommand) -> None:
        """Handle the 'position' command — set up the board.

        Args:
            cmd: Parsed command with 'fen' and 'moves' params.
        """
        fen = cmd.params.get("fen", "startpos")
        moves = cmd.params.get("moves", [])

        if fen == "startpos":
            self.board = chess.Board()
        else:
            self.board = chess.Board(str(fen))

        # Apply the move sequence
        for move_uci in moves:  # type: ignore[union-attr]
            try:
                move = chess.Move.from_uci(str(move_uci))
                if move in self.board.legal_moves:
                    self.board.push(move)
            except (ValueError, chess.InvalidMoveError):
                # Silently skip invalid moves per UCI convention
                pass

    def _handle_go(self, cmd: UCICommand) -> None:
        """Handle the 'go' command — run the search and send results.

        Determines the search depth from the command parameters, runs
        the engine, and sends 'info' followed by 'bestmove'.

        Args:
            cmd: Parsed command with optional 'depth', 'movetime', etc.
        """
        depth = cmd.params.get("depth")
        search_depth = int(depth) if depth is not None else _DEFAULT_DEPTH
        self.engine.config = EngineConfig(max_depth=search_depth)

        limits = SearchLimits(
            depth=search_depth,
            movetime_ms=_optional_int(cmd.params.get("movetime")),
            nodes=_optional_int(cmd.params.get("nodes")),
            wtime_ms=_optional_int(cmd.params.get("wtime")),
            btime_ms=_optional_int(cmd.params.get("btime")),
            winc_ms=_optional_int(cmd.params.get("winc")),
            binc_ms=_optional_int(cmd.params.get("binc")),
            movestogo=_optional_int(cmd.params.get("movestogo")),
            infinite=bool(cmd.params.get("infinite", False)),
        )

        result = self.engine.search(self.board, limits)
        move = result.best_move
        metrics = result.metrics

        # Send search info
        time_ms = int(metrics.elapsed_seconds * 1000)
        self._send(
            info(
                depth=metrics.depth_reached,
                score_cp=metrics.score,
                nodes=result.nodes,
                time_ms=time_ms,
                pv=result.pv,
            )
        )

        # Send best move
        self._send(best_move(move))

    def _handle_stop(self, _cmd: UCICommand) -> None:
        """Handle the 'stop' command — placeholder for future interruption."""
        # Currently search is synchronous; nothing to stop.
        pass

    def _handle_quit(self, _cmd: UCICommand) -> None:
        """Handle the 'quit' command — terminate the session loop."""
        self._running = False

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def _send(self, text: str) -> None:
        """Write a line to the output stream and flush immediately.

        UCI protocol requires each response to be flushed immediately
        so the GUI receives it without delay.

        Args:
            text: The response line to send.
        """
        self._output.write(text + "\n")
        self._output.flush()


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
