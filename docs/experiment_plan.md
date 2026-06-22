# Experiment Plan

## Research Question

How do staged search optimizations affect chess-engine search efficiency,
runtime, transposition-table reuse, tactical stability, and labeled-position
accuracy when evaluated on a fixed benchmark FEN dataset?

The project compares algorithms under controlled conditions. It does not try to
prove absolute playing strength from one benchmark CSV. Playing strength can be
studied separately with UCI tournament tools such as fastchess.

## Presets

| Version | Preset | Technique |
| --- | --- | --- |
| V0 | `v0_minimax` | Depth-limited minimax baseline |
| V1 | `v1_alpha_beta` | Alpha-beta pruning |
| V2 | `v2_alpha_beta_ordering` | Alpha-beta with deterministic move ordering |
| V3 | `v3_alpha_beta_ordering_tt` | Alpha-beta with move ordering and transposition table |
| V4 | `v4_iterative_deepening` | Iterative deepening over alpha-beta |
| V5 | `v5_quiescence` | Alpha-beta with transposition table and bounded quiescence |

V0-V3 are the cleanest fixed-depth efficiency comparison set. V4 and V5 should
be interpreted with caveats because they change the search procedure rather
than only pruning the same fixed-depth tree.

## Benchmark Dataset

The input dataset is:

```text
data/positions/benchmark_positions.csv
```

It uses this schema:

```csv
id,fen,category,description,best_move
```

Categories:

- `opening`: early positions with many legal moves.
- `middlegame`: complex positions with many pieces and tactical tension.
- `tactical`: forcing or tactic-heavy positions.
- `check`: positions where the side to move is in check.
- `endgame`: reduced-material positions suited for depth tests.
- `quiescence`: capture-heavy positions that can expose horizon effects.

`best_move` is optional. It should be used only when the expected move is clear,
for example a mate-in-one or obvious forcing tactic. Blank labels are excluded
from accuracy calculations.

## Experiment Modes

### Fixed Depth

Fixed-depth experiments compare algorithms at the same requested depth:

```bash
python scripts/run_experiments.py \
  --positions data/positions/benchmark_positions.csv \
  --output data/results/depth_benchmark.csv \
  --depths 2 3 4 \
  --repeats 3
```

This mode is best for node-count, pruning, and transposition-table comparisons.
V0 minimax can be very slow at depth 4, so practical report workflows may split
the run into a main depth 1-3 comparison and a depth-4 supplement without V0.

### Fixed Time

Fixed-time experiments apply a per-position time budget:

```bash
python scripts/run_experiments.py \
  --positions data/positions/benchmark_positions.csv \
  --output data/results/time_benchmark.csv \
  --depths 6 \
  --movetime-ms 1000 \
  --repeats 3
```

This mode is useful for studying how much depth each preset can complete under
a time budget. Interpret fixed-time results with care because `depth_reached`
may differ across algorithms and positions.

## Metrics

- `total_nodes`: total searched nodes, computed as
  `nodes_searched + qnodes_searched`.
- `elapsed_ms`: elapsed search time in milliseconds.
- `nps`: total nodes per second.
- `cutoffs`: alpha-beta cutoff count.
- `cutoff_rate`: `cutoffs / total_nodes`, with zero denominators handled as
  missing values in analysis.
- `tt_hit_rate`: `tt_hits / tt_probes`, or zero when no probes were made.
- `qnodes_searched`: nodes searched by quiescence extensions.
- `accuracy`: mean correctness on rows with non-empty `expected_best_move`.
- `depth_reached`: completed search depth.
- `seldepth`: maximum selective depth, including tactical extensions when
  available.

The analysis script also computes:

- `node_reduction_ratio`: `1 - total_nodes_preset / total_nodes_baseline`.
- `speedup_ratio`: `elapsed_ms_baseline / elapsed_ms_preset`.

## Analysis Workflow

1. Run the benchmark to create a raw CSV under `data/results/`.
2. Run:

   ```bash
   python scripts/analyze_results.py \
     --input data/results/depth_benchmark.csv \
     --output-dir data/results/analysis
   ```

3. Inspect summary CSV files:

   - `summary_by_preset_depth.csv`
   - `summary_by_category.csv`
   - `summary_by_preset_category.csv`
   - `node_reduction_vs_baseline.csv`
   - `accuracy_summary.csv`
   - `tt_summary.csv`
   - `quiescence_summary.csv`

4. Use generated charts under `data/results/analysis/charts/` for report
   figures.

When the benchmark file does not contain `v0_minimax`, pass a different
baseline:

```bash
python scripts/analyze_results.py \
  --input data/results/benchmarks/depth_4_optimized.csv \
  --output-dir data/results/analysis/depth_4_optimized \
  --baseline-preset v1_alpha_beta
```

## Experiment Limitations

- Runtime is hardware dependent. Use repeats and report the machine context
  when presenting final results.
- Fixed-depth and fixed-time experiments answer different questions and should
  not be mixed without explanation.
- Accuracy is sparse because only clear `best_move` labels are used.
- V4 iterative deepening can search shallower iterations before the target
  depth, so it may do more work than a direct fixed-depth alpha-beta search.
- V5 quiescence intentionally adds tactical leaf search, so more nodes are not
  automatically a regression.
- The evaluation function is intentionally simple, so benchmark results measure
  search behavior more than chess strength.
- Generated outputs under `data/results/` are disposable artifacts and should
  not be committed as source.
