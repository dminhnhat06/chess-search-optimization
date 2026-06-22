"""Tests for UCI command parser."""

from __future__ import annotations

from ai_chess.uci.command_parser import parse_command


class TestSimpleCommands:
    """Tests for simple one-word UCI commands."""

    def test_uci_command(self) -> None:
        """'uci' should parse to a command with name 'uci'."""
        cmd = parse_command("uci")
        assert cmd.name == "uci"
        assert cmd.params == {}

    def test_isready_command(self) -> None:
        """'isready' should parse correctly."""
        cmd = parse_command("isready")
        assert cmd.name == "isready"

    def test_ucinewgame_command(self) -> None:
        """'ucinewgame' should parse correctly."""
        cmd = parse_command("ucinewgame")
        assert cmd.name == "ucinewgame"

    def test_quit_command(self) -> None:
        """'quit' should parse correctly."""
        cmd = parse_command("quit")
        assert cmd.name == "quit"

    def test_stop_command(self) -> None:
        """'stop' should parse correctly."""
        cmd = parse_command("stop")
        assert cmd.name == "stop"

    def test_setoption_command(self) -> None:
        """'setoption' should parse option name and value."""
        cmd = parse_command("setoption name Algorithm value v3")
        assert cmd.name == "setoption"
        assert cmd.params["name"] == "Algorithm"
        assert cmd.params["value"] == "v3"

    def test_setoption_name_with_spaces(self) -> None:
        """'setoption' should preserve multi-token option names."""
        cmd = parse_command("setoption name Move Ordering value true")
        assert cmd.name == "setoption"
        assert cmd.params["name"] == "Move Ordering"
        assert cmd.params["value"] == "true"

    def test_empty_line(self) -> None:
        """An empty line should return a command with empty name."""
        cmd = parse_command("")
        assert cmd.name == ""

    def test_whitespace_only_line(self) -> None:
        """A whitespace-only line should return a command with empty name."""
        cmd = parse_command("   \t  ")
        assert cmd.name == ""

    def test_unknown_command(self) -> None:
        """An unrecognized command should pass through with its name."""
        cmd = parse_command("debug on")
        assert cmd.name == "debug"
        assert cmd.params == {}


class TestPositionCommand:
    """Tests for parsing 'position' commands."""

    def test_startpos_no_moves(self) -> None:
        """'position startpos' with no moves."""
        cmd = parse_command("position startpos")
        assert cmd.name == "position"
        assert cmd.params["fen"] == "startpos"
        assert cmd.params["moves"] == []

    def test_startpos_with_moves(self) -> None:
        """'position startpos moves e2e4 e7e5' should parse moves list."""
        cmd = parse_command("position startpos moves e2e4 e7e5")
        assert cmd.name == "position"
        assert cmd.params["fen"] == "startpos"
        assert cmd.params["moves"] == ["e2e4", "e7e5"]

    def test_fen_no_moves(self) -> None:
        """'position fen <fen>' should extract the full FEN string."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        cmd = parse_command(f"position fen {fen}")
        assert cmd.name == "position"
        assert cmd.params["fen"] == fen
        assert cmd.params["moves"] == []

    def test_fen_with_moves(self) -> None:
        """'position fen <fen> moves ...' should parse both FEN and moves."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        cmd = parse_command(f"position fen {fen} moves e7e5 g1f3")
        assert cmd.name == "position"
        assert cmd.params["fen"] == fen
        assert cmd.params["moves"] == ["e7e5", "g1f3"]

    def test_position_without_subcommand(self) -> None:
        """'position' alone should return empty fen and moves."""
        cmd = parse_command("position")
        assert cmd.name == "position"
        assert cmd.params["fen"] == ""
        assert cmd.params["moves"] == []


class TestGoCommand:
    """Tests for parsing 'go' commands."""

    def test_go_depth(self) -> None:
        """'go depth 5' should set depth param to 5."""
        cmd = parse_command("go depth 5")
        assert cmd.name == "go"
        assert cmd.params["depth"] == 5

    def test_go_movetime(self) -> None:
        """'go movetime 1000' should set movetime param to 1000."""
        cmd = parse_command("go movetime 1000")
        assert cmd.name == "go"
        assert cmd.params["movetime"] == 1000

    def test_go_infinite(self) -> None:
        """'go infinite' should set infinite param to True."""
        cmd = parse_command("go infinite")
        assert cmd.name == "go"
        assert cmd.params["infinite"] is True

    def test_go_time_control(self) -> None:
        """'go wtime ... btime ... winc ... binc ...' should parse all params."""
        cmd = parse_command("go wtime 300000 btime 300000 winc 2000 binc 2000")
        assert cmd.name == "go"
        assert cmd.params["wtime"] == 300000
        assert cmd.params["btime"] == 300000
        assert cmd.params["winc"] == 2000
        assert cmd.params["binc"] == 2000

    def test_go_no_args(self) -> None:
        """'go' without arguments should return empty params."""
        cmd = parse_command("go")
        assert cmd.name == "go"
        assert cmd.params == {}

    def test_go_invalid_depth_value(self) -> None:
        """'go depth abc' should silently skip the invalid value."""
        cmd = parse_command("go depth abc")
        assert cmd.name == "go"
        assert "depth" not in cmd.params
