"""Shared paths, data-quality checks, formatting, and plotting utilities for CDS-76 advanced analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "final_destination.csv"
RAW_FALLBACK_PATH = PROJECT_ROOT / "data" / "raw" / "final_destination.csv"
OUTPUT_FIG_DIR = PROJECT_ROOT / "outputs" / "advanced_analysis"
OUTPUT_REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"

MIN_SAMPLE_SIZE = 30
MAJOR_BODY_TYPES = ["Hatchback", "Sedan", "SUV", "MUV"]
ALPHA = 0.05
LAKH = 100_000.0

PALETTE = {
    "primary": "#1f4e78",
    "secondary": "#2b8cbe",
    "accent": "#d95f02",
    "danger": "#c0392b",
    "muted": "#7f8c8d",
    "success": "#2e7d32",
    "manual": "#3b6998",
    "automatic": "#e07a5f",
    "dealer": "#1f4e78",
    "individual": "#e07a5f",
    "trustmark": "#5f9e6e",
}


def configure_plot_style() -> None:
    """Apply consistent, clean business visualization styling."""
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.figsize": (11, 6),
            "figure.dpi": 130,
            "savefig.dpi": 300,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "legend.fontsize": 9.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def load_dataset(path: Path | None = None) -> pd.DataFrame:
    """Load final_destination.csv without mutating source files."""
    target = path if path is not None else DATA_PATH
    if not target.exists() and RAW_FALLBACK_PATH.exists():
        target = RAW_FALLBACK_PATH
    if not target.exists():
        raise FileNotFoundError(f"Dataset not found at {target.resolve()}")

    df = pd.read_csv(target)
    return df


def format_lakhs(x: float, _pos: float | None = None) -> str:
    """Format INR values as Lakhs (e.g., 5.5L)."""
    return f"₹{x / LAKH:,.1f}L" if abs(x) >= LAKH or x == 0 else f"₹{x / 1000:,.0f}k"


def format_inr(x: float) -> str:
    """Format an INR amount nicely for text annotations and reports."""
    return f"₹{x:,.0f} ({x / LAKH:,.2f} Lakh)"


def save_chart(fig: Figure, filename: str) -> Path:
    """Save figure to outputs/advanced_analysis/<filename> at 300 DPI."""
    OUTPUT_FIG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_FIG_DIR / filename
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


def inspect_data_quality(df: pd.DataFrame) -> dict[str, Any]:
    """Run comprehensive data quality inspection on final_destination.csv."""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]

    missing_by_col = {col: int(cnt) for col, cnt in df.isna().sum().items()}
    duplicate_rows = int(df.duplicated().sum())

    # Check domain anomalies / impossible values
    km_per_year = df["km_driven"] / df["vehicle_age"].clip(lower=1)
    extreme_km_per_year = int((km_per_year > 100_000).sum())
    zero_age_count = int((df["vehicle_age"] == 0).sum())
    non_positive_price = int((df["selling_price"] <= 0).sum())
    non_positive_km = int((df["km_driven"] <= 0).sum())
    non_positive_engine = int((df["engine"] <= 0).sum())
    non_positive_power = int((df["max_power"] <= 0).sum())

    # Check categorical "Unknown" or small-sample categories
    unknown_body = int((df["real_body_type"] == "Unknown").sum())
    unknown_owner = int((df["real_typical_owner_type"] == "Unknown").sum())

    age_counts = df["vehicle_age"].value_counts().sort_index()
    low_sample_ages = {int(age): int(cnt) for age, cnt in age_counts.items() if cnt < MIN_SAMPLE_SIZE}

    body_counts = df["real_body_type"].value_counts()
    low_sample_bodies = {str(k): int(v) for k, v in body_counts.items() if v < MIN_SAMPLE_SIZE}

    seller_counts = df["seller_type"].value_counts().to_dict()
    transmission_counts = df["transmission_type"].value_counts().to_dict()

    # Check case/whitespace inconsistencies in string columns
    whitespace_issues = {}
    case_collisions = {}
    for col in categorical_cols:
        s = df[col].astype(str)
        ws = int((s != s.str.strip()).sum())
        if ws > 0:
            whitespace_issues[col] = ws
        lower_map = s.str.strip().str.lower()
        if s.nunique() != lower_map.nunique():
            case_collisions[col] = {
                "raw_unique": int(s.nunique()),
                "lower_unique": int(lower_map.nunique()),
            }

    numeric_ranges = {}
    for col in numeric_cols:
        numeric_ranges[col] = {
            "min": float(df[col].min()),
            "p25": float(df[col].quantile(0.25)),
            "median": float(df[col].median()),
            "mean": float(df[col].mean()),
            "p75": float(df[col].quantile(0.75)),
            "max": float(df[col].max()),
            "std": float(df[col].std()),
        }

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "missing_by_col": missing_by_col,
        "total_missing": int(sum(missing_by_col.values())),
        "duplicate_rows": duplicate_rows,
        "domain_checks": {
            "extreme_km_per_year_gt_100k": extreme_km_per_year,
            "zero_vehicle_age_rows": zero_age_count,
            "non_positive_selling_price": non_positive_price,
            "non_positive_km_driven": non_positive_km,
            "non_positive_engine": non_positive_engine,
            "non_positive_max_power": non_positive_power,
            "unknown_real_body_type": unknown_body,
            "unknown_real_typical_owner_type": unknown_owner,
        },
        "low_sample_ages_lt_30": low_sample_ages,
        "low_sample_body_types_lt_30": low_sample_bodies,
        "body_type_counts": {str(k): int(v) for k, v in body_counts.items()},
        "seller_type_counts": {str(k): int(v) for k, v in seller_counts.items()},
        "transmission_type_counts": {str(k): int(v) for k, v in transmission_counts.items()},
        "whitespace_issues": whitespace_issues,
        "case_collisions": case_collisions,
        "numeric_ranges": numeric_ranges,
        "age_distribution": {int(k): int(v) for k, v in age_counts.items()},
    }


def bootstrap_median_diff_ci(
    group_a: np.ndarray,
    group_b: np.ndarray,
    n_boot: int = 2000,
    seed: int = 42,
    alpha: float = ALPHA,
) -> tuple[float, float, float]:
    """Compute bootstrap CI for (median(group_a) - median(group_b))."""
    rng = np.random.default_rng(seed)
    obs_diff = float(np.median(group_a) - np.median(group_b))
    n_a, n_b = len(group_a), len(group_b)
    diffs = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        samp_a = rng.choice(group_a, size=n_a, replace=True)
        samp_b = rng.choice(group_b, size=n_b, replace=True)
        diffs[i] = np.median(samp_a) - np.median(samp_b)
    low = float(np.quantile(diffs, alpha / 2))
    high = float(np.quantile(diffs, 1 - alpha / 2))
    return obs_diff, low, high


def set_lakhs_axis(ax: plt.Axes, axis: str = "y") -> None:
    """Format axis ticks in Indian Rupees (Lakhs)."""
    formatter = mticker.FuncFormatter(format_lakhs)
    if axis == "y":
        ax.yaxis.set_major_formatter(formatter)
    else:
        ax.xaxis.set_major_formatter(formatter)
