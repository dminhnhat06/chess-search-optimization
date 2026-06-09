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

This runs a depth-2 minimax search on the starting position and prints:
- Best move
- Evaluation score
- Nodes searched
- Elapsed time

## Planned Algorithm Versions

| Version | Algorithm | Description |
|---------|-----------|-------------|
| **V0** | Minimax | Depth-limited minimax baseline (current) |
| **V1** | Alpha-Beta Pruning | Minimax with alpha-beta cutoffs |
| **V2** | Alpha-Beta + Move Ordering | Captures and promotions searched first |
| **V3** | Transposition Table | Cache evaluated positions to avoid re-computation |
| **V4** | Iterative Deepening | Progressively deeper searches with time control |
| **V5** | Quiescence Search | Extend search at tactical positions to avoid horizon effect |

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
│       ├── engine/         # ChessEngine, EngineConfig, SearchMetrics
│       ├── evaluation/     # BasicEvaluator, piece values
│       ├── search/         # SearchAlgorithm base, MinimaxSearch
│       ├── optimization/   # Move ordering, transposition table
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
