"""Factory for core engine search presets."""

from __future__ import annotations

from ai_chess.engine.chess_engine import ChessEngine
from ai_chess.engine.config import EngineConfig
from ai_chess.evaluation.evaluator import BasicEvaluator
from ai_chess.optimization.transposition_table import TranspositionTable
from ai_chess.search.alpha_beta import AlphaBetaSearch
from ai_chess.search.iterative_deepening import IterativeDeepeningSearch
from ai_chess.search.minimax import MinimaxSearch


def make_engine(
    preset: str,
    *,
    max_depth: int = 3,
    time_limit_seconds: float | None = None,
) -> ChessEngine:
    """Create a core chess engine for a named search preset."""
    config = _config_for_preset(preset, max_depth, time_limit_seconds)

    if preset == "v0_minimax":
        search_algorithm = MinimaxSearch()
    elif preset in {
        "v1_alpha_beta",
        "v2_alpha_beta_ordering",
        "v3_alpha_beta_ordering_tt",
        "v5_quiescence",
    }:
        table = (
            TranspositionTable(config.hash_size_mb)
            if config.use_transposition_table
            else None
        )
        search_algorithm = AlphaBetaSearch(table)
    elif preset == "v4_iterative_deepening":
        search_algorithm = IterativeDeepeningSearch(
            AlphaBetaSearch(TranspositionTable(config.hash_size_mb))
        )
    else:
        supported = ", ".join(_SUPPORTED_PRESETS)
        raise ValueError(f"Unknown engine preset '{preset}'. Supported: {supported}")

    return ChessEngine(
        search_algorithm=search_algorithm,
        evaluator=BasicEvaluator(),
        config=config,
    )


_SUPPORTED_PRESETS = (
    "v0_minimax",
    "v1_alpha_beta",
    "v2_alpha_beta_ordering",
    "v3_alpha_beta_ordering_tt",
    "v4_iterative_deepening",
    "v5_quiescence",
)


def _config_for_preset(
    preset: str,
    max_depth: int,
    time_limit_seconds: float | None,
) -> EngineConfig:
    if preset == "v0_minimax":
        return EngineConfig(
            max_depth=max_depth,
            time_limit_seconds=time_limit_seconds,
            use_alpha_beta=False,
        )
    if preset == "v1_alpha_beta":
        return EngineConfig(
            max_depth=max_depth,
            time_limit_seconds=time_limit_seconds,
            use_alpha_beta=True,
        )
    if preset == "v2_alpha_beta_ordering":
        return EngineConfig(
            max_depth=max_depth,
            time_limit_seconds=time_limit_seconds,
            use_alpha_beta=True,
            use_move_ordering=True,
        )
    if preset == "v3_alpha_beta_ordering_tt":
        return EngineConfig(
            max_depth=max_depth,
            time_limit_seconds=time_limit_seconds,
            use_alpha_beta=True,
            use_move_ordering=True,
            use_transposition_table=True,
        )
    if preset == "v4_iterative_deepening":
        return EngineConfig(
            max_depth=max_depth,
            time_limit_seconds=time_limit_seconds,
            use_alpha_beta=True,
            use_move_ordering=True,
            use_transposition_table=True,
            use_iterative_deepening=True,
        )
    if preset == "v5_quiescence":
        return EngineConfig(
            max_depth=max_depth,
            time_limit_seconds=time_limit_seconds,
            use_alpha_beta=True,
            use_move_ordering=True,
            use_transposition_table=True,
            use_quiescence=True,
        )

    supported = ", ".join(_SUPPORTED_PRESETS)
    raise ValueError(f"Unknown engine preset '{preset}'. Supported: {supported}")
