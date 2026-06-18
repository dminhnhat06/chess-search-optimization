# Fastchess Usage

Fastchess is used in this project as the tournament runner for comparing UCI
engine configurations. It should not contain project-specific experiment state;
generated PGN, logs, and summaries belong under `data/results/`.

## Role In This Project

Use fastchess after an algorithm passes unit tests and fixed-position
benchmarks. Its role is to answer playing-strength questions such as:

- Does V1 AlphaBeta beat or draw V0 Minimax at the same fixed depth?
- Does V2 MoveOrdering improve V1 when both use alpha-beta pruning?
- Do later versions produce better game outcomes from the same opening set?

For search-efficiency questions, prefer position benchmarks first because they
produce cleaner node/time measurements.

## Preparation

Install the package in editable mode so fastchess can launch the UCI module
without ad hoc batch files:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Verify the UCI entry point manually:

```powershell
.\.venv\Scripts\python.exe -m ai_chess.uci
```

The engine advertises these UCI options:

| Option | Values | Purpose |
| --- | --- | --- |
| `Algorithm` | `v0`, `v1`, `v2`, `v3`, `v4`, `v5` | Select the research version |
| `Depth` | `1` to `10` | Default depth when `go` omits depth |
| `MoveOrdering` | `true`, `false` | Optional override for smoke checks |
| `TranspositionTable` | `true`, `false` | Optional override for smoke checks |
| `Quiescence` | `true`, `false` | Optional override for smoke checks |
| `QuiescenceDepth` | `0` to `12` | Tactical extension limit |

Fastchess can set these options with `option.<Name>=<Value>`.

## Compliance Check

Run this after UCI changes:

```powershell
.\fastchess-windows-x86-64\fastchess.exe --compliance .\.venv\Scripts\python.exe "-m ai_chess.uci"
```

The project should primarily use fixed-depth matches. Normal clock-based tests
should wait until the engine has real time management and interruptible search.

## Fixed-Depth Match Template

This template compares V0 Minimax and V1 AlphaBeta at the same depth:

```powershell
.\fastchess-windows-x86-64\fastchess.exe `
  -engine cmd=D:\chess-search-optimization\.venv\Scripts\python.exe args="-m ai_chess.uci" dir=D:\chess-search-optimization name=V0_Minimax option.Algorithm=v0 depth=3 `
  -engine cmd=D:\chess-search-optimization\.venv\Scripts\python.exe args="-m ai_chess.uci" dir=D:\chess-search-optimization name=V1_AlphaBeta option.Algorithm=v1 depth=3 `
  -openings file=D:\chess-search-optimization\data\positions\openings.epd format=epd order=random `
  -rounds 20 `
  -repeat `
  -concurrency 1 `
  -draw movenumber=40 movecount=8 score=20 `
  -maxmoves 160 `
  -pgnout file=D:\chess-search-optimization\data\results\fastchess\v0_v1_depth3.pgn notation=uci nodes=true append=false `
  -ratinginterval 1
```

Notes:

- `depth=3` is a fastchess engine limit; it sends `go depth 3`.
- `-repeat` plays both colors from each opening.
- `-concurrency 1` gives cleaner timing for a Python CPU-bound engine.
- `append=false` prevents mixing separate experiments.
- Use a new PGN file for every comparison.
- Keep the same machine, Python environment, engine depth, opening file, and
  concurrency fixed across both sides of a comparison.

## Later Comparisons

Recommended comparison sequence:

| Comparison | Purpose |
| --- | --- |
| `V0_Minimax` vs `V1_AlphaBeta` | Measure pruning benefit |
| `V1_AlphaBeta` vs `V2_MoveOrdering` | Measure improved cutoff efficiency |
| `V2_MoveOrdering` vs `V3_TranspositionTable` | Measure repeated-position reuse |
| `V3_TranspositionTable` vs `V4_IterativeDeepening` | Measure practical time-control readiness |
| `V4_IterativeDeepening` vs `V5_Quiescence` | Measure tactical stability |

Use the same `option.Algorithm=<version>` pattern for later versions:

```powershell
option.Algorithm=v2
option.Algorithm=v3
option.Algorithm=v4
option.Algorithm=v5
```

## Output Handling

Recommended outputs:

- Raw games: `data/results/fastchess/<comparison>.pgn`
- Match summaries: `data/results/fastchess/<comparison>_summary.txt`
- Optional parsed rows: `data/results/fastchess/<comparison>.jsonl`

Keep fastchess source files and executable under `fastchess-windows-x86-64/`.
Do not store generated fastchess `config.json`, `results.pgn`, or logs in that
directory.

Short smoke checks are enough during development. Full match counts should wait
until unit tests and fixed-position benchmarks pass for both compared versions.
Treat fastchess results as playing-strength evidence, not direct search
efficiency evidence; use the fixed-position benchmark CSV/JSONL/metadata
artifacts for node and timing claims.
