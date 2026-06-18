# AI Chess Search Optimization

**Evaluating the Effectiveness of Search Optimization Techniques in AI Chess**

## Project Goal

This project builds a modular chess AI engine to compare and evaluate different search optimization techniques. The engine uses the `python-chess` library for board/rules handling and implements all AI search logic manually.

The research goal is to measure and compare the performance of progressively more advanced search algorithms on a set of benchmark chess positions.

## Architecture Overview

```
ai_chess/
├── engine/          # Engine orchestration, config, metrics
├── evaluation/      # Board evaluation (material, positional)
├── search/          # Search algorithms (minimax, alpha-beta, etc.)
├── optimization/    # Search enhancements (move ordering, TT, etc.)
├── experiments/     # Benchmark runner, FEN loader
└── utils/           # Shared utilities (timer, etc.)
```

**Key design principles:**

- **Separation of concerns** — Search, evaluation, engine, and experiments are independent modules.
- **Swappable algorithms** — Any search algorithm implementing `SearchAlgorithm` can be plugged into the engine.
- **Research-oriented metrics** — Every search records nodes searched, elapsed time, depth, cutoffs, and more.
- **Testability** — No hidden global state; all components are unit tested.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd ai-chess-search-optimization

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
# source .venv/bin/activate

# Install the package in development mode
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest
```

## Running the Demo

```bash
python main.py
```

This creates a preset engine, runs a depth-2 structured search on the starting
position, and prints:
- Best move
- Evaluation score
- Nodes searched
- Elapsed time

## Core Engine API

```python
import chess

from ai_chess.engine.limits import SearchLimits
from ai_chess.presets import make_engine

board = chess.Board()
engine = make_engine("v3_alpha_beta_ordering_tt", max_depth=4)
result = engine.search(board, SearchLimits(depth=4))
```

`ChessEngine.search(board, limits)` is the preferred API and returns a
structured `SearchResult`. Existing callers can still use
`find_best_move(board)`, which returns `(best_move, metrics)`.

## Implemented Core Search Versions

| Version | Algorithm | Description |
|---------|-----------|-------------|
| **V0** | Minimax | Depth-limited minimax baseline |
| **V1** | Alpha-Beta Pruning | Minimax with alpha-beta cutoffs |
| **V2** | Alpha-Beta + Move Ordering | Deterministic ordering with preferred moves, captures, promotions, checks, and UCI tie-breaks |
| **V3** | Alpha-Beta + Move Ordering + Transposition Table | Depth-aware table probes, hits, stores, and bound flags |
| **V4** | Iterative Deepening | Progressively deeper alpha-beta searches with time/node-aware stopping |
| **V5** | Quiescence Search | Bounded tactical extension at leaf nodes to reduce horizon effects |

Available presets:

- `v0_minimax`
- `v1_alpha_beta`
- `v2_alpha_beta_ordering`
- `v3_alpha_beta_ordering_tt`
- `v4_iterative_deepening`
- `v5_quiescence`

## Project Structure

```
ai-chess-search-optimization/
│
├── README.md
├── pyproject.toml
├── .gitignore
├── main.py
│
├── src/
│   └── ai_chess/
│       ├── engine/         # ChessEngine, EngineConfig, SearchLimits, SearchResult, SearchMetrics
│       ├── evaluation/     # BasicEvaluator, piece values
│       ├── search/         # Minimax, alpha-beta, iterative deepening, quiescence
│       ├── optimization/   # Move ordering, transposition table, search limits helpers
│       ├── presets/        # Named V0-V5 engine factory
│       ├── experiments/    # FEN loader, benchmark runner
│       └── utils/          # Timer utility
│
├── data/
│   ├── positions/          # Test position CSVs
│   └── results/            # Benchmark output (gitignored)
│
└── tests/                  # Unit tests
```

## Dependencies

- **Runtime:** `chess` (python-chess)
- **Development:** `pytest`, `ruff`
- **Analysis (optional):** `pandas`, `matplotlib`

## License

MIT
