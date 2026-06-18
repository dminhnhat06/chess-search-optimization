# Core Engine Package

The reusable engine core lives under `src/ai_chess/`. It accepts a
`python-chess` `Board`, searches under explicit `SearchLimits`, and returns a
structured `SearchResult`. The core does not depend on benchmark runners,
tournament orchestration, notebooks, plotting, PGN analysis, or file output.

## Presets

Create engines through `ai_chess.presets.make_engine`:

```python
import chess

from ai_chess.engine.limits import SearchLimits
from ai_chess.presets import make_engine

board = chess.Board()
engine = make_engine("v3_alpha_beta_ordering_tt", max_depth=4)
result = engine.search(board, SearchLimits(depth=4))
```

Supported presets:

- `v0_minimax`: depth-limited minimax.
- `v1_alpha_beta`: depth-limited alpha-beta pruning.
- `v2_alpha_beta_ordering`: alpha-beta with deterministic move ordering.
- `v3_alpha_beta_ordering_tt`: alpha-beta with move ordering and transposition
  table.
- `v4_iterative_deepening`: iterative deepening with time-aware stopping.
- `v5_quiescence`: alpha-beta with bounded quiescence search.

## Search Limits

`SearchLimits` describes one independent search call:

- `depth`: maximum search depth.
- `movetime_ms`: fixed move time in milliseconds.
- `nodes`: maximum total search nodes.
- `wtime_ms`, `btime_ms`, `winc_ms`, `binc_ms`, `movestogo`: clock-style
  limits for callers such as UCI adapters.
- `infinite`: caller-managed infinite mode.

When limits are omitted, `ChessEngine.search()` uses `EngineConfig.max_depth`
and `EngineConfig.time_limit_seconds`.

## Search Result

`SearchResult` contains:

- `best_move`: legal move for the input board, or `None` when no legal move
  exists.
- `score_cp`: score in centipawns from White's perspective.
- `depth`, `seldepth`: completed search depth and selective depth.
- `nodes`, `nps`, `elapsed_ms`: search performance fields.
- `pv`: principal variation when available.
- `metrics`: detailed `SearchMetrics`.

The legacy API remains available:

```python
best_move, metrics = engine.find_best_move(board)
```

## Metrics

`SearchMetrics` records regular nodes, quiescence nodes, alpha-beta cutoffs,
transposition-table probes/hits/stores, reached depth, elapsed time, best move,
score, completion state, and stop reason. Metrics are reset for each independent
search result.

## Running Tests

Run the full unit suite from the repository root:

```bash
python -m pytest
```
