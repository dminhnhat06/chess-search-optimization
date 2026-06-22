"""CLI for running FEN benchmark experiments."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_chess.experiments.benchmark_runner import (  # noqa: E402
    DEFAULT_PRESETS,
    BenchmarkFormat,
    run_experiment_suite,
    write_benchmark_results,
)
from ai_chess.experiments.fen_loader import load_positions_from_csv  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_format = _resolve_format(args.output, args.format)

    if "v0_minimax" in args.presets and max(args.depths) >= 4:
        print(
            "Warning: v0_minimax can be very slow at depth 4 or higher.",
            file=sys.stderr,
        )

    positions = load_positions_from_csv(args.positions)
    total_rows = len(positions) * len(args.presets) * len(args.depths) * args.repeats
    progress_every = max(1, total_rows // 20)
    print(f"Running {total_rows} benchmark rows...", file=sys.stderr)
    rows = run_experiment_suite(
        positions,
        presets=args.presets,
        depths=args.depths,
        repeats=args.repeats,
        movetime_ms=args.movetime_ms,
        fail_fast=args.fail_fast,
        progress_callback=_progress_printer(progress_every),
    )
    write_benchmark_results(rows, args.output, output_format=output_format)
    print(f"Wrote {len(rows)} benchmark rows to {args.output}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run AI chess search benchmark experiments."
    )
    parser.add_argument("--positions", required=True, help="Input FEN CSV path.")
    parser.add_argument("--output", required=True, help="Output CSV or JSON path.")
    parser.add_argument(
        "--depths",
        required=True,
        nargs="+",
        type=int,
        help="One or more fixed search depths.",
    )
    parser.add_argument(
        "--presets",
        nargs="+",
        default=list(DEFAULT_PRESETS),
        help="Search presets to benchmark. Defaults to all V0-V5 presets.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Number of trials per preset/depth/position.",
    )
    parser.add_argument(
        "--movetime-ms",
        type=int,
        default=None,
        help="Optional UCI-style movetime limit per search.",
    )
    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        default=None,
        help="Output format. Defaults to JSON for .json outputs, otherwise CSV.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Abort on the first benchmark error.",
    )
    return parser.parse_args(argv)


def _progress_printer(progress_every: int):
    def print_progress(progress: dict[str, object]) -> None:
        completed = int(progress["completed"])
        total = int(progress["total"])
        if completed % progress_every != 0 and completed != total:
            return
        percent = completed / total * 100 if total else 100
        print(
            (
                f"Progress {completed}/{total} ({percent:.1f}%) "
                f"preset={progress['preset']} depth={progress['depth']} "
                f"trial={progress['trial']} position={progress['position_id']}"
            ),
            file=sys.stderr,
        )

    return print_progress


def _resolve_format(output: str, requested: str | None) -> BenchmarkFormat:
    if requested is not None:
        return requested
    if Path(output).suffix.lower() == ".json":
        return "json"
    return "csv"


if __name__ == "__main__":
    raise SystemExit(main())
