# AI Chess Search Optimization

**Evaluating the Effectiveness of Search Optimization Techniques in AI Chess**

## Project Goal

This project builds a modular chess AI engine to compare search optimization
techniques under controlled benchmark conditions. The engine uses
`python-chess` for board and rule handling, while the search algorithms,
optimization layers, benchmark runner, and analysis pipeline live in this repo.

The research goal is not simply to make the strongest chess engine. The goal is
to measure how each optimization stage changes node count, runtime, pruning,
transposition-table reuse, quiescence behavior, and tactical accuracy on a fixed
set of chess positions.

## Architecture Overview

```
ai_chess/
├── engine/          # Engine orchestration, config, limits, result, metrics
├── evaluation/      # Board evaluation
├── search/          # Minimax, alpha-beta, iterative deepening, quiescence
├── optimization/    # Move ordering, transposition table, search controller
├── presets/         # Named V0-V5 engine configurations
├── uci/             # UCI protocol adapter and options
├── experiments/     # FEN loader and benchmark runner
└── utils/           # Shared utilities
```

**Key design principles:**

- **Separation of concerns**: search, evaluation, engine, UCI, benchmark, and
  analysis are independent modules.
- **Controlled comparisons**: V0-V5 are staged presets so each step can be
  compared against the previous one.
- **Research-oriented metrics**: benchmark rows include nodes, timing, cutoffs,
  transposition-table fields, quiescence nodes, depth, PV, and accuracy labels
  when available.
- **Reproducibility**: benchmark inputs live under `data/positions/`; generated
  outputs live under `data/results/` and are ignored by git.

## Installation

```bash
git clone <repo-url>
cd ai-chess-search-optimization

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
# source .venv/bin/activate

pip install -e ".[dev,analysis]"
```

The `analysis` extra installs `pandas` and `matplotlib`, which are required for
the result analysis script and chart generation.

## Running Tests

```bash
python -m pytest
```

On Windows sandboxed environments, if pytest cannot write to the default temp
or cache directory, run:

```bash
python -m pytest --basetemp .pytest_tmp -p no:cacheprovider
```

## Running the Demo

```bash
python main.py
# or, after installation:
ai-chess-demo
```

This runs a depth-2 `v0_minimax` search on the starting position and prints:

- Best move
- Evaluation score
- Nodes searched
- Elapsed time

## Running the UCI Adapter

```bash
python -m ai_chess.uci
# or, after installation:
ai-chess-uci
```

The UCI adapter exposes the same V0-V5 ladder through `setoption name Algorithm
value v0` through `v5`.

## Implemented Algorithm Versions

| Version | Preset | Algorithm | Description |
| --- | --- | --- | --- |
| **V0** | `v0_minimax` | Minimax | Depth-limited minimax baseline |
| **V1** | `v1_alpha_beta` | Alpha-beta pruning | Minimax with alpha-beta cutoffs |
| **V2** | `v2_alpha_beta_ordering` | Alpha-beta + move ordering | Captures, promotions, and preferred moves searched earlier |
| **V3** | `v3_alpha_beta_ordering_tt` | Transposition table | Reuses cached position evaluations and best moves |
| **V4** | `v4_iterative_deepening` | Iterative deepening | Searches progressively deeper and supports time-aware stopping |
| **V5** | `v5_quiescence` | Quiescence search | Extends tactical leaves with bounded capture/evasion search |

## Benchmark Dataset

The benchmark dataset is:

```text
data/positions/benchmark_positions.csv
```

It is a CSV loaded by `load_positions_from_csv` and uses this schema:

```csv
id,fen,category,description,best_move
```

The dataset contains positions across these categories:

- `opening`: early positions with high branching factor.
- `middlegame`: complex positions with many pieces and tactical tension.
- `tactical`: forcing or tactic-heavy positions.
- `check`: positions where the side to move must respond to check.
- `endgame`: reduced-material positions useful for depth comparisons.
- `quiescence`: noisy capture positions designed to expose horizon effects.

`best_move` is intentionally sparse. It is filled only for clear labels such as
mate-in-one or obvious forcing tactics. Blank labels are excluded from accuracy
calculations, which avoids treating uncertain chess judgments as ground truth.

See `data/positions/README.md` for dataset details.

## Running Experiments

Run benchmark experiments with:

```bash
python scripts/run_experiments.py \
  --positions data/positions/benchmark_positions.csv \
  --output data/results/depth_benchmark.csv \
  --depths 2 3 4 \
  --repeats 3
```

For a fixed-time search experiment:

```bash
python scripts/run_experiments.py \
  --positions data/positions/benchmark_positions.csv \
  --output data/results/time_benchmark.csv \
  --depths 6 \
  --movetime-ms 1000 \
  --repeats 3
```

Useful options:

- `--presets`: choose a subset of presets. Defaults to all V0-V5 presets.
- `--depths`: one or more search depths.
- `--repeats`: repeated trials for timing stability.
- `--movetime-ms`: optional per-position time limit.
- `--format csv/json`: output format. CSV is the default unless `.json` is
  inferred from the output filename.
- `--fail-fast`: stop on the first benchmark error.

Each row represents one `preset x depth x trial x position` search. The runner
creates a fresh engine for each preset/depth/trial/position combination and
calls `engine.reset()` before every position so transposition-table state does
not leak across benchmark rows.

Generated benchmark outputs should be written under `data/results/`, which is
ignored by git.

## Analyzing Results

Analyze a raw benchmark CSV with:

```bash
python scripts/analyze_results.py \
  --input data/results/depth_benchmark.csv \
  --output-dir data/results/analysis
```

The analysis script writes summary tables:

- `summary_by_preset_depth.csv`
- `summary_by_category.csv`
- `summary_by_preset_category.csv`
- `node_reduction_vs_baseline.csv`
- `accuracy_summary.csv`
- `tt_summary.csv`
- `quiescence_summary.csv`

It also writes charts under `charts/`:

- `mean_nodes_by_preset_depth.png`
- `mean_time_by_preset_depth.png`
- `node_reduction_vs_baseline.png`
- `tt_hit_rate_by_depth.png`
- `accuracy_by_preset.png`
- `quiescence_qnodes.png`

The default baseline for node reduction and speedup is `v0_minimax`. Use
`--baseline-preset` when analyzing a benchmark file that does not include V0.

## Metrics Explained

Raw benchmark rows include:

- `total_nodes`: `nodes_searched + qnodes_searched`.
- `elapsed_ms`: elapsed search time in milliseconds.
- `nps`: total nodes per second.
- `cutoffs`: alpha-beta cutoff count.
- `beta_cutoffs`: beta cutoff count where tracked by the search implementation.
- `tt_probes`: transposition-table lookup attempts.
- `tt_hits`: successful transposition-table lookups.
- `tt_stores`: positions stored into the transposition table.
- `tt_hit_rate`: `tt_hits / tt_probes`, or zero when there are no probes.
- `qnodes_searched`: quiescence nodes searched beyond the fixed-depth leaf.
- `accuracy`: mean correctness over rows with non-empty `expected_best_move`.
- `depth_reached`: completed search depth.
- `seldepth`: maximum selective depth, including quiescence where applicable.
- `pv_uci`: principal variation as UCI moves separated by spaces.

Analysis summary fields include:

- `mean_cutoff_rate`: mean `cutoffs / total_nodes`.
- `node_reduction_ratio`: `1 - total_nodes_preset / total_nodes_baseline`.
- `speedup_ratio`: `elapsed_ms_baseline / elapsed_ms_preset`.

Denominators of zero are handled as missing values in the analysis output.

## Reproducing Report Results

Use a clean environment and install both development and analysis dependencies:

```bash
pip install -e ".[dev,analysis]"
```

Then generate raw benchmark rows:

```bash
python scripts/run_experiments.py \
  --positions data/positions/benchmark_positions.csv \
  --output data/results/depth_benchmark.csv \
  --depths 2 3 4 \
  --repeats 3
```

Then generate summary CSVs and charts:

```bash
python scripts/analyze_results.py \
  --input data/results/depth_benchmark.csv \
  --output-dir data/results/analysis
```

Do not treat these commands as already-run empirical results. They define the
reproducible workflow. The actual numbers depend on the machine, Python version,
CPU load, selected depths, selected presets, and repeat count.

## Recommended Experiment Configurations

Use these configurations in order:

1. **Workflow smoke check**

   ```bash
   python scripts/run_experiments.py \
     --positions data/positions/benchmark_positions.csv \
     --output data/results/benchmarks/smoke_v0_v1_depth1.csv \
     --depths 1 \
     --presets v0_minimax v1_alpha_beta \
     --repeats 1
   ```

   This validates the pipeline only. Do not report it as final empirical
   evidence.

2. **Main fixed-depth comparison**

   ```bash
   python scripts/run_experiments.py \
     --positions data/positions/benchmark_positions.csv \
     --output data/results/benchmarks/depth_1_3_all.csv \
     --depths 1 2 3 \
     --repeats 3
   ```

   This is the practical default for comparing all V0-V5 presets.

3. **Depth-4 optimized supplement**

   ```bash
   python scripts/run_experiments.py \
     --positions data/positions/benchmark_positions.csv \
     --output data/results/benchmarks/depth_4_optimized.csv \
     --depths 4 \
     --presets v1_alpha_beta v2_alpha_beta_ordering v3_alpha_beta_ordering_tt v4_iterative_deepening v5_quiescence \
     --repeats 3
   ```

   V0 minimax can be very slow at depth 4. Run V0 depth 4 only if the runtime is
   acceptable for the machine being used.

4. **Fixed-time comparison**

   ```bash
   python scripts/run_experiments.py \
     --positions data/positions/benchmark_positions.csv \
     --output data/results/benchmarks/time_1000ms_depth6.csv \
     --depths 6 \
     --movetime-ms 1000 \
     --repeats 3
   ```

   Interpret fixed-time results with care because algorithms may stop at
   different completed depths.

## Interpreting V0-V5 Results

Recommended interpretation:

- **V0 vs V1**: isolates alpha-beta pruning. Expect the most direct node-count
  reduction comparison, because both are fixed-depth minimax-style searches.
- **V1 vs V2**: isolates move ordering. More useful cutoffs should reduce nodes
  and time when the ordering places strong moves early.
- **V2 vs V3**: isolates transposition-table reuse. Look at `tt_probes`,
  `tt_hits`, `tt_stores`, and `tt_hit_rate`, not only raw speed.
- **V3 vs V4**: compares fixed-depth alpha-beta with iterative deepening.
  V4 may do extra work at shallow depths before reaching the final depth, so it
  should be interpreted as a time-management-oriented technique rather than a
  pure node minimizer.
- **V3 vs V5**: isolates quiescence behavior. V5 may search more total nodes
  because it extends tactical leaves. Use `qnodes_searched`, `seldepth`, and
  labeled-position `accuracy` to interpret whether the extra search is useful.

For clean efficiency claims, prefer V0-V3 fixed-depth comparisons. For V4 and
V5, include interpretation caveats because they change the search procedure
instead of only pruning the same tree.

## Project Structure

```
ai-chess-search-optimization/
├── README.md
├── pyproject.toml
├── .gitignore
├── main.py
├── scripts/
│   ├── run_experiments.py
│   └── analyze_results.py
├── docs/
│   ├── core_engine.md
│   ├── experiment_plan.md
│   ├── fastchess_usage.md
│   └── report_outline.md
├── src/
│   └── ai_chess/
│       ├── engine/
│       ├── evaluation/
│       ├── search/
│       ├── optimization/
│       ├── presets/
│       ├── uci/
│       ├── experiments/
│       └── utils/
├── data/
│   ├── positions/
│   └── results/
└── tests/
```

Generated benchmark, fastchess, cache, analysis, and temporary test outputs are
treated as disposable artifacts and are ignored by git.

## Dependencies

- **Runtime:** `chess` (python-chess)
- **Development:** `pytest`, `ruff`
- **Analysis (optional):** `pandas`, `matplotlib`

## License

MIT
