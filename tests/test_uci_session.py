"""Tests for UCI session — end-to-end protocol interaction tests.

Uses io.StringIO to simulate stdin/stdout, verifying the session
produces correct UCI responses without any mocking.
"""

from __future__ import annotations

import io

import chess
import pytest

from ai_chess.uci.session import UCISession


def _run_session(commands: str) -> str:
    """Helper: run a UCI session with the given commands and return output.

    Args:
        commands: Multi-line string of UCI commands (must end with 'quit').

    Returns:
        The full output produced by the session.
    """
    input_stream = io.StringIO(commands)
    output_stream = io.StringIO()
    session = UCISession(input_stream=input_stream, output_stream=output_stream)
    session.run()
    return output_stream.getvalue()


class TestUCIHandshake:
    """Tests for the UCI identification handshake."""

    def test_uci_identification(self) -> None:
        """'uci' should respond with id name, id author, and uciok."""
        output = _run_session("uci\nquit\n")
        lines = output.strip().split("\n")

        assert any(line.startswith("id name ") for line in lines)
        assert any(line.startswith("id author ") for line in lines)
        assert "uciok" in lines

    def test_isready(self) -> None:
        """'isready' should respond with 'readyok'."""
        output = _run_session("isready\nquit\n")
        assert "readyok" in output.strip().split("\n")

    def test_full_handshake(self) -> None:
        """Full handshake: uci -> isready -> should get both responses."""
        output = _run_session("uci\nisready\nquit\n")
        lines = output.strip().split("\n")

        assert "uciok" in lines
        assert "readyok" in lines
        # uciok should come before readyok
        uciok_idx = lines.index("uciok")
        readyok_idx = lines.index("readyok")
        assert uciok_idx < readyok_idx


class TestPositionAndGo:
    """Tests for position setup and search commands."""

    def test_startpos_and_go(self) -> None:
        """Setting startpos and searching should return a bestmove."""
        output = _run_session(
            "uci\n"
            "isready\n"
            "position startpos\n"
            "go depth 1\n"
            "quit\n"
        )
        lines = output.strip().split("\n")

        # Should contain a bestmove response
        bestmove_lines = [l for l in lines if l.startswith("bestmove")]
        assert len(bestmove_lines) == 1

        # The bestmove should be a valid UCI move (4-5 chars)
        move_str = bestmove_lines[0].split()[1]
        assert len(move_str) >= 4

    def test_startpos_with_moves_and_go(self) -> None:
        """Position with moves applied, then go, should return a bestmove."""
        output = _run_session(
            "position startpos moves e2e4 e7e5\n"
            "go depth 1\n"
            "quit\n"
        )
        lines = output.strip().split("\n")
        bestmove_lines = [l for l in lines if l.startswith("bestmove")]
        assert len(bestmove_lines) == 1

    def test_fen_position_and_go(self) -> None:
        """Setting a FEN position and searching should return a bestmove."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        output = _run_session(
            f"position fen {fen}\n"
            "go depth 1\n"
            "quit\n"
        )
        lines = output.strip().split("\n")
        bestmove_lines = [l for l in lines if l.startswith("bestmove")]
        assert len(bestmove_lines) == 1

    def test_info_before_bestmove(self) -> None:
        """Search should output 'info' before 'bestmove'."""
        output = _run_session(
            "position startpos\n"
            "go depth 1\n"
            "quit\n"
        )
        lines = output.strip().split("\n")

        info_lines = [l for l in lines if l.startswith("info")]
        bestmove_lines = [l for l in lines if l.startswith("bestmove")]

        assert len(info_lines) >= 1
        assert len(bestmove_lines) == 1

        # info should appear before bestmove
        info_idx = next(i for i, l in enumerate(lines) if l.startswith("info"))
        bm_idx = next(i for i, l in enumerate(lines) if l.startswith("bestmove"))
        assert info_idx < bm_idx

    def test_info_contains_depth_and_nodes(self) -> None:
        """Info line should contain depth and nodes fields."""
        output = _run_session(
            "position startpos\n"
            "go depth 2\n"
            "quit\n"
        )
        lines = output.strip().split("\n")
        info_line = next(l for l in lines if l.startswith("info"))

        assert "depth" in info_line
        assert "nodes" in info_line


class TestUCINewGame:
    """Tests for the 'ucinewgame' command."""

    def test_ucinewgame_resets_board(self) -> None:
        """After ucinewgame, board should be reset to starting position."""
        input_stream = io.StringIO(
            "position startpos moves e2e4 e7e5\n"
            "ucinewgame\n"
            "quit\n"
        )
        output_stream = io.StringIO()
        session = UCISession(input_stream=input_stream, output_stream=output_stream)
        session.run()

        # After ucinewgame, board should be at starting position
        assert session.board == chess.Board()


class TestQuitAndEOF:
    """Tests for session termination."""

    def test_quit_stops_loop(self) -> None:
        """'quit' should terminate the session loop."""
        output = _run_session("quit\n")
        # Should return without error; output may be empty
        assert isinstance(output, str)

    def test_eof_stops_loop(self) -> None:
        """EOF (empty input) should terminate the session loop."""
        input_stream = io.StringIO("")
        output_stream = io.StringIO()
        session = UCISession(input_stream=input_stream, output_stream=output_stream)
        session.run()
        # Should not raise

    def test_empty_lines_ignored(self) -> None:
        """Empty lines should be silently ignored."""
        output = _run_session("\n\n\nisready\n\nquit\n")
        assert "readyok" in output.strip().split("\n")


class TestMultipleSearches:
    """Tests for multiple consecutive searches in one session."""

    def test_two_consecutive_searches(self) -> None:
        """Running go twice should produce two bestmove responses."""
        output = _run_session(
            "position startpos\n"
            "go depth 1\n"
            "position startpos moves e2e4\n"
            "go depth 1\n"
            "quit\n"
        )
        lines = output.strip().split("\n")
        bestmove_lines = [l for l in lines if l.startswith("bestmove")]
        assert len(bestmove_lines) == 2
