"""Analyze raw benchmark CSV outputs and produce report-ready artifacts."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".matplotlib_cache"))

try:
    import matplotlib
    import pandas as pd
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    raise SystemExit(
        "Missing analysis dependency. Install the optional analysis extras: "
        "pip install -e .[analysis]"
    ) from exc

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SUMMARY_FILES = (
    "summary_by_preset_depth.csv",
    "summary_by_category.csv",
    "summary_by_preset_category.csv",
    "node_reduction_vs_baseline.csv",
    "accuracy_summary.csv",
    "tt_summary.csv",
    "quiescence_summary.csv",
)

CHART_FILES = (
    "mean_nodes_by_preset_depth.png",
    "mean_time_by_preset_depth.png",
    "node_reduction_vs_baseline.png",
    "tt_hit_rate_by_depth.png",
    "accuracy_by_preset.png",
    "quiescence_qnodes.png",
)

REQUIRED_ANALYSIS_COLUMNS = {
    "preset",
    "depth",
    "position_id",
    "category",
    "total_nodes",
    "elapsed_ms",
    "nps",
    "cutoffs",
    "tt_probes",
    "tt_hits",
    "tt_stores",
    "tt_hit_rate",
    "depth_reached",
    "seldepth",
    "qnodes_searched",
}

NUMERIC_COLUMNS = (
    "depth",
    "trial",
    "total_nodes",
    "elapsed_ms",
    "nps",
    "cutoffs",
    "tt_probes",
    "tt_hits",
    "tt_stores",
    "tt_hit_rate",
    "depth_reached",
    "seldepth",
    "qnodes_searched",
)

SUMMARY_METRICS = (
    "num_positions",
    "mean_total_nodes",
    "median_total_nodes",
    "mean_elapsed_ms",
    "median_elapsed_ms",
    "mean_nps",
    "mean_cutoffs",
    "mean_cutoff_rate",
    "mean_tt_hit_rate",
    "mean_depth_reached",
    "mean_seldepth",
    "accuracy",
)

QUIESCENCE_PRESETS = ("v3_alpha_beta_ordering_tt", "v5_quiescence")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_dir = Path(args.output_dir)
    charts_dir = output_dir / "charts"
    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)

    try:
        raw = load_results(args.input)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    artifacts = build_analysis_tables(raw, baseline_preset=args.baseline_preset)
    for filename, table in artifacts.items():
        table.to_csv(output_dir / filename, index=False)

    write_charts(artifacts, charts_dir, baseline_preset=args.baseline_preset)

    print(f"Wrote {len(SUMMARY_FILES)} summary CSV files to {output_dir}")
    print(f"Wrote {len(CHART_FILES)} chart PNG files to {charts_dir}")
    return 0


def load_results(path: str | Path) -> pd.DataFrame:
    """Load and normalize a raw benchmark CSV."""
    data = pd.read_csv(path, keep_default_na=False)
    data = _add_derivable_columns(data)
    _add_optional_analysis_columns(data)

    missing = sorted(REQUIRED_ANALYSIS_COLUMNS - set(data.columns))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            "Input is missing required benchmark columns for analysis: "
            f"{missing_text}"
        )

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data["expected_best_move"] = data["expected_best_move"].astype(str).str.strip()
    data["is_labeled"] = data["expected_best_move"] != ""
    data["is_correct_bool"] = data["is_correct"].map(_parse_bool)
    data["accuracy_value"] = pd.NA
    labeled = data["is_labeled"]
    data.loc[labeled, "accuracy_value"] = data.loc[
        labeled, "is_correct_bool"
    ].map(_bool_to_accuracy)
    data["accuracy_value"] = pd.to_numeric(
        data["accuracy_value"], errors="coerce"
    )
    data["cutoff_rate"] = _safe_divide(data["cutoffs"], data["total_nodes"])
    return data


def build_analysis_tables(
    data: pd.DataFrame,
    *,
    baseline_preset: str,
) -> dict[str, pd.DataFrame]:
    """Build all analysis summary tables."""
    summary_by_preset_depth = _summary_table(data, ["preset", "depth"])
    summary_by_category = _summary_table(data, ["category", "preset", "depth"])
    summary_by_preset_category = _summary_table(data, ["preset", "category"])
    node_reduction = _node_reduction_table(data, baseline_preset)
    accuracy_summary = _accuracy_summary(data)
    tt_summary = _tt_summary(data)
    quiescence_summary = _quiescence_summary(data)

    return {
        "summary_by_preset_depth.csv": summary_by_preset_depth,
        "summary_by_category.csv": summary_by_category,
        "summary_by_preset_category.csv": summary_by_preset_category,
        "node_reduction_vs_baseline.csv": node_reduction,
        "accuracy_summary.csv": accuracy_summary,
        "tt_summary.csv": tt_summary,
        "quiescence_summary.csv": quiescence_summary,
    }


def write_charts(
    artifacts: dict[str, pd.DataFrame],
    charts_dir: Path,
    *,
    baseline_preset: str,
) -> None:
    """Create matplotlib PNG charts from analysis tables."""
    summary = artifacts["summary_by_preset_depth.csv"]
    node_reduction = artifacts["node_reduction_vs_baseline.csv"]
    tt_summary = artifacts["tt_summary.csv"]
    accuracy = artifacts["accuracy_summary.csv"]
    quiescence = artifacts["quiescence_summary.csv"]

    _plot_metric_by_depth(
        summary,
        value_column="mean_total_nodes",
        title="Mean Nodes by Preset and Depth",
        ylabel="Mean total nodes",
        output_path=charts_dir / "mean_nodes_by_preset_depth.png",
    )
    _plot_metric_by_depth(
        summary,
        value_column="mean_elapsed_ms",
        title="Mean Search Time by Preset and Depth",
        ylabel="Mean elapsed ms",
        output_path=charts_dir / "mean_time_by_preset_depth.png",
    )
    _plot_node_reduction(
        node_reduction,
        baseline_preset=baseline_preset,
        output_path=charts_dir / "node_reduction_vs_baseline.png",
    )
    _plot_metric_by_depth(
        tt_summary,
        value_column="tt_hit_rate",
        title="TT Hit Rate by Depth",
        ylabel="TT hit rate",
        output_path=charts_dir / "tt_hit_rate_by_depth.png",
    )
    _plot_accuracy_by_preset(
        accuracy,
        output_path=charts_dir / "accuracy_by_preset.png",
    )
    _plot_metric_by_depth(
        quiescence,
        value_column="mean_qnodes_searched",
        title="Quiescence Nodes by Depth",
        ylabel="Mean quiescence nodes",
        output_path=charts_dir / "quiescence_qnodes.png",
    )


def _summary_table(data: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    grouped = (
        data.groupby(group_columns, dropna=False)
        .agg(
            num_positions=("position_id", "nunique"),
            mean_total_nodes=("total_nodes", "mean"),
            median_total_nodes=("total_nodes", "median"),
            mean_elapsed_ms=("elapsed_ms", "mean"),
            median_elapsed_ms=("elapsed_ms", "median"),
            mean_nps=("nps", "mean"),
            mean_cutoffs=("cutoffs", "mean"),
            mean_cutoff_rate=("cutoff_rate", "mean"),
            mean_tt_hit_rate=("tt_hit_rate", "mean"),
            mean_depth_reached=("depth_reached", "mean"),
            mean_seldepth=("seldepth", "mean"),
            accuracy=("accuracy_value", "mean"),
        )
        .reset_index()
        .sort_values(group_columns)
    )
    return grouped[[*group_columns, *SUMMARY_METRICS]]


def _node_reduction_table(
    data: pd.DataFrame,
    baseline_preset: str,
) -> pd.DataFrame:
    output_columns = [
        "preset",
        "baseline_preset",
        "depth",
        "trial",
        "position_id",
        "category",
        "total_nodes_preset",
        "total_nodes_baseline",
        "elapsed_ms_preset",
        "elapsed_ms_baseline",
        "node_reduction_ratio",
        "speedup_ratio",
    ]
    baseline = data[data["preset"] == baseline_preset]
    if baseline.empty:
        return pd.DataFrame(columns=output_columns)

    baseline_values = baseline[
        ["depth", "trial", "position_id", "total_nodes", "elapsed_ms"]
    ].rename(
        columns={
            "total_nodes": "total_nodes_baseline",
            "elapsed_ms": "elapsed_ms_baseline",
        }
    )
    compared = data[
        [
            "preset",
            "depth",
            "trial",
            "position_id",
            "category",
            "total_nodes",
            "elapsed_ms",
        ]
    ].rename(
        columns={
            "total_nodes": "total_nodes_preset",
            "elapsed_ms": "elapsed_ms_preset",
        }
    )
    merged = compared.merge(
        baseline_values,
        on=["depth", "trial", "position_id"],
        how="inner",
    )
    merged["baseline_preset"] = baseline_preset
    merged["node_reduction_ratio"] = 1 - _safe_divide(
        merged["total_nodes_preset"],
        merged["total_nodes_baseline"],
    )
    merged["speedup_ratio"] = _safe_divide(
        merged["elapsed_ms_baseline"],
        merged["elapsed_ms_preset"],
    )
    return merged[output_columns].sort_values(
        ["depth", "trial", "position_id", "preset"]
    )


def _accuracy_summary(data: pd.DataFrame) -> pd.DataFrame:
    columns = ["preset", "depth", "num_labeled", "num_correct", "accuracy"]
    labeled = data[data["is_labeled"]].copy()
    if labeled.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        labeled.groupby(["preset", "depth"], dropna=False)
        .agg(
            num_labeled=("accuracy_value", "count"),
            num_correct=("accuracy_value", "sum"),
            accuracy=("accuracy_value", "mean"),
        )
        .reset_index()
        .sort_values(["preset", "depth"])
    )
    return summary[columns]


def _tt_summary(data: pd.DataFrame) -> pd.DataFrame:
    summary = (
        data.groupby(["preset", "depth"], dropna=False)
        .agg(
            tt_probes=("tt_probes", "sum"),
            tt_hits=("tt_hits", "sum"),
            tt_stores=("tt_stores", "sum"),
        )
        .reset_index()
        .sort_values(["preset", "depth"])
    )
    summary["tt_hit_rate"] = _safe_divide(
        summary["tt_hits"], summary["tt_probes"]
    )
    return summary[
        ["preset", "depth", "tt_probes", "tt_hits", "tt_stores", "tt_hit_rate"]
    ]


def _quiescence_summary(data: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "preset",
        "depth",
        "num_positions",
        "mean_qnodes_searched",
        "mean_total_nodes",
        "mean_elapsed_ms",
        "accuracy",
        "mean_seldepth",
    ]
    subset = data[data["preset"].isin(QUIESCENCE_PRESETS)]
    if subset.empty:
        return pd.DataFrame(columns=columns)

    common_depths = (
        subset.groupby("depth")["preset"].nunique().loc[lambda values: values == 2]
    )
    subset = subset[subset["depth"].isin(common_depths.index)]
    if subset.empty:
        return pd.DataFrame(columns=columns)

    summary = (
        subset.groupby(["preset", "depth"], dropna=False)
        .agg(
            num_positions=("position_id", "nunique"),
            mean_qnodes_searched=("qnodes_searched", "mean"),
            mean_total_nodes=("total_nodes", "mean"),
            mean_elapsed_ms=("elapsed_ms", "mean"),
            accuracy=("accuracy_value", "mean"),
            mean_seldepth=("seldepth", "mean"),
        )
        .reset_index()
        .sort_values(["preset", "depth"])
    )
    return summary[columns]


def _add_derivable_columns(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    if "trial" not in data.columns:
        data["trial"] = 1
    if "expected_best_move" not in data.columns:
        data["expected_best_move"] = ""
    if "is_correct" not in data.columns:
        data["is_correct"] = ""
    if "total_nodes" not in data.columns and {
        "nodes_searched",
        "qnodes_searched",
    }.issubset(data.columns):
        data["total_nodes"] = (
            pd.to_numeric(data["nodes_searched"], errors="coerce").fillna(0)
            + pd.to_numeric(data["qnodes_searched"], errors="coerce").fillna(0)
        )
    if "elapsed_ms" not in data.columns and "elapsed_seconds" in data.columns:
        data["elapsed_ms"] = (
            pd.to_numeric(data["elapsed_seconds"], errors="coerce") * 1000
        )
    if "nps" not in data.columns and {"total_nodes", "elapsed_ms"}.issubset(
        data.columns
    ):
        elapsed_seconds = pd.to_numeric(data["elapsed_ms"], errors="coerce") / 1000
        data["nps"] = _safe_divide(
            pd.to_numeric(data["total_nodes"], errors="coerce"),
            elapsed_seconds,
        )
    if "tt_hit_rate" not in data.columns and {"tt_hits", "tt_probes"}.issubset(
        data.columns
    ):
        data["tt_hit_rate"] = _safe_divide(
            pd.to_numeric(data["tt_hits"], errors="coerce"),
            pd.to_numeric(data["tt_probes"], errors="coerce"),
        )
    return data


def _add_optional_analysis_columns(data: pd.DataFrame) -> None:
    for column in ("expected_best_move", "is_correct"):
        if column not in data.columns:
            data[column] = ""


def _parse_bool(value: object) -> bool | pd.NA:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return pd.NA


def _bool_to_accuracy(value: object) -> float | pd.NA:
    if value is True:
        return 1.0
    if value is False:
        return 0.0
    return pd.NA


def _safe_divide(numerator: object, denominator: object) -> pd.Series:
    numerator_series = pd.to_numeric(numerator, errors="coerce")
    denominator_series = pd.to_numeric(denominator, errors="coerce")
    return numerator_series / denominator_series.where(denominator_series != 0)


def _plot_metric_by_depth(
    data: pd.DataFrame,
    *,
    value_column: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    required = {"preset", "depth", value_column}
    if data.empty or not required.issubset(data.columns):
        _plot_no_data(title, output_path)
        return

    pivot = data.pivot_table(
        index="depth",
        columns="preset",
        values=value_column,
        aggfunc="mean",
    ).sort_index()
    if pivot.empty:
        _plot_no_data(title, output_path)
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    for preset in pivot.columns:
        ax.plot(pivot.index, pivot[preset], marker="o", label=preset)
    ax.set_title(title)
    ax.set_xlabel("Depth")
    ax.set_ylabel(ylabel)
    if len(pivot.columns) > 1:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def _plot_node_reduction(
    data: pd.DataFrame,
    *,
    baseline_preset: str,
    output_path: Path,
) -> None:
    required = {"preset", "depth", "node_reduction_ratio"}
    data = data[data.get("preset", pd.Series(dtype=object)) != baseline_preset]
    if data.empty or not required.issubset(data.columns):
        _plot_no_data("Node Reduction vs Baseline", output_path)
        return

    summary = (
        data.groupby(["preset", "depth"], dropna=False)["node_reduction_ratio"]
        .mean()
        .reset_index()
    )
    _plot_metric_by_depth(
        summary,
        value_column="node_reduction_ratio",
        title="Node Reduction vs Baseline",
        ylabel="Mean node reduction ratio",
        output_path=output_path,
    )


def _plot_accuracy_by_preset(data: pd.DataFrame, *, output_path: Path) -> None:
    if data.empty or not {"preset", "accuracy"}.issubset(data.columns):
        _plot_no_data("Accuracy by Preset", output_path)
        return

    summary = data.groupby("preset", dropna=False)["accuracy"].mean().dropna()
    if summary.empty:
        _plot_no_data("Accuracy by Preset", output_path)
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(summary.index.astype(str), summary.values)
    ax.set_title("Accuracy by Preset")
    ax.set_xlabel("Preset")
    ax.set_ylabel("Accuracy")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def _plot_no_data(title: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_title(title)
    ax.set_xlabel("No data")
    ax.set_ylabel("Value")
    ax.text(0.5, 0.5, "No data", ha="center", va="center")
    ax.set_xticks([])
    ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze raw AI chess benchmark CSV results."
    )
    parser.add_argument("--input", required=True, help="Raw benchmark CSV path.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for summary CSV files and chart PNGs.",
    )
    parser.add_argument(
        "--baseline-preset",
        default="v0_minimax",
        help="Baseline preset for node reduction and speedup comparisons.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
