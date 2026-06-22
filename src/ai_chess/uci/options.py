"""UCI option handling for selecting research engine presets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai_chess.presets import make_engine

if TYPE_CHECKING:
    from ai_chess.engine.chess_engine import ChessEngine

DEFAULT_ALGORITHM = "v0"
DEFAULT_DEPTH = 4
DEFAULT_QUIESCENCE_DEPTH = 8

_ALGORITHM_PRESETS = {
    "v0": "v0_minimax",
    "v1": "v1_alpha_beta",
    "v2": "v2_alpha_beta_ordering",
    "v3": "v3_alpha_beta_ordering_tt",
    "v4": "v4_iterative_deepening",
    "v5": "v5_quiescence",
}

_OPTION_NAMES = {
    "algorithm": "algorithm",
    "depth": "depth",
    "moveordering": "move_ordering",
    "move ordering": "move_ordering",
    "transpositiontable": "transposition_table",
    "transposition table": "transposition_table",
    "quiescence": "quiescence",
    "quiescencedepth": "quiescence_depth",
    "quiescence depth": "quiescence_depth",
}


@dataclass
class UCIEngineOptions:
    """Mutable UCI options used to build the active engine instance."""

    algorithm: str = DEFAULT_ALGORITHM
    depth: int = DEFAULT_DEPTH
    move_ordering: bool | None = None
    transposition_table: bool | None = None
    quiescence: bool | None = None
    quiescence_depth: int = DEFAULT_QUIESCENCE_DEPTH

    def make_engine(self) -> ChessEngine:
        """Create an engine from the current UCI option state."""
        engine = make_engine(self.preset, max_depth=self.depth)
        config = engine.config

        if self.move_ordering is not None:
            config.use_move_ordering = self.move_ordering
        if self.transposition_table is not None:
            config.use_transposition_table = self.transposition_table
        if self.quiescence is not None:
            config.use_quiescence = self.quiescence

        config.quiescence_max_depth = self.quiescence_depth
        return engine

    @property
    def preset(self) -> str:
        """Return the package preset id for the selected algorithm alias."""
        return _ALGORITHM_PRESETS[self.algorithm]

    def set_option(self, name: str, value: object | None) -> bool:
        """Apply a parsed UCI option.

        Returns ``True`` when the option was recognized and accepted. Unknown
        options and invalid values are ignored so protocol clients cannot crash
        the session with a malformed ``setoption`` command.
        """
        option = _OPTION_NAMES.get(_normalize_name(name))
        if option is None:
            return False

        try:
            if option == "algorithm":
                algorithm = _normalize_algorithm(value)
                if algorithm is None:
                    return False
                self.algorithm = algorithm
            elif option == "depth":
                self.depth = _bounded_int(value, minimum=1, maximum=10)
            elif option == "move_ordering":
                self.move_ordering = _parse_bool(value)
            elif option == "transposition_table":
                self.transposition_table = _parse_bool(value)
            elif option == "quiescence":
                self.quiescence = _parse_bool(value)
            elif option == "quiescence_depth":
                self.quiescence_depth = _bounded_int(value, minimum=0, maximum=12)
            else:
                return False
        except (TypeError, ValueError):
            return False

        return True


def uci_option_lines() -> list[str]:
    """Return UCI option declarations advertised during the handshake."""
    algorithms = " ".join(f"var {algorithm}" for algorithm in _ALGORITHM_PRESETS)
    return [
        f"option name Algorithm type combo default {DEFAULT_ALGORITHM} {algorithms}",
        f"option name Depth type spin default {DEFAULT_DEPTH} min 1 max 10",
        "option name MoveOrdering type check default false",
        "option name TranspositionTable type check default false",
        "option name Quiescence type check default false",
        (
            "option name QuiescenceDepth type spin "
            f"default {DEFAULT_QUIESCENCE_DEPTH} min 0 max 12"
        ),
    ]


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def _normalize_algorithm(value: object | None) -> str | None:
    if value is None:
        return None
    algorithm = str(value).strip().lower()
    if algorithm in _ALGORITHM_PRESETS:
        return algorithm
    for alias, preset in _ALGORITHM_PRESETS.items():
        if algorithm == preset:
            return alias
    return None


def _bounded_int(value: object | None, *, minimum: int, maximum: int) -> int:
    if value is None:
        raise ValueError("missing integer value")
    parsed = int(value)
    if parsed < minimum or parsed > maximum:
        raise ValueError("integer value outside accepted range")
    return parsed


def _parse_bool(value: object | None) -> bool:
    if value is None:
        return True
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")
