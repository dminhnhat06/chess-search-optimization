# Benchmark Position Dataset

`benchmark_positions.csv` is the shared FEN dataset for controlled fixed-depth
comparisons of the V0-V5 search presets. It is intended to exercise different
search behaviors without embedding engine-specific evaluation assumptions into
every row.

## CSV Schema

The file is compatible with `load_positions_from_csv` in
`src/ai_chess/experiments/fen_loader.py` and uses these columns:

```csv
id,fen,category,description,best_move
```

- `id`: stable unique identifier for the position.
- `fen`: full FEN string.
- `category`: benchmark category.
- `description`: short human-readable description.
- `best_move`: optional UCI move when the answer is clear.

## Categories

- `opening`: early positions with many legal moves and high branching factor.
- `middlegame`: complex positions with many pieces and tactical tension.
- `tactical`: positions where a forcing idea is present.
- `check`: positions where the side to move is in check and must evade it.
- `endgame`: reduced-material positions useful for depth sensitivity checks.
- `quiescence`: capture-heavy positions that can expose horizon effects.

## Best Move Policy

`best_move` is filled only when the move is clear and easy to validate, such as
mate-in-one patterns or direct forcing tactics. Most rows intentionally leave it
blank because this dataset is primarily for comparing search behavior, node
counts, and timing across presets, not for scoring every position against an
oracle.

Leaving uncertain `best_move` values blank avoids turning the dataset into a
set of weak labels. A questionable label would make benchmark failures harder
to interpret than an intentionally unlabeled position.

## Loading

Use the existing loader:

```python
from ai_chess.experiments.fen_loader import load_positions_from_csv

positions = load_positions_from_csv("data/positions/benchmark_positions.csv")
```

Blank `best_move` cells are returned as `None`.
