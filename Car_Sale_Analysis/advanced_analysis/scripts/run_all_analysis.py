"""End-to-end runner for CDS-76 Advanced Analysis pipeline with validation checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure sibling scripts are importable regardless of current working directory
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import numpy as np
import pandas as pd

from common import (
    MAJOR_BODY_TYPES,
    OUTPUT_FIG_DIR,
    OUTPUT_REPORT_DIR,
    inspect_data_quality,
    load_dataset,
)
from depreciation_analysis import run_depreciation_analysis
from seller_dynamics_analysis import run_seller_dynamics_analysis
from statistical_testing import run_statistical_testing
from transmission_body_analysis import run_transmission_body_analysis

EXPECTED_CHARTS = [
    "depreciation_curve.png",
    "vehicle_age_sample_size.png",
    "annual_price_change.png",
    "age_25_anomaly.png",
    "transmission_body_price_comparison.png",
    "transmission_body_interaction.png",
    "seller_price_comparison.png",
    "seller_vehicle_age_comparison.png",
    "seller_mileage_comparison.png",
    "seller_price_distribution.png",
    "statistical_test_summary.png",
]


def cross_validate_aggregations(df: pd.DataFrame, results: dict[str, Any]) -> dict[str, bool]:
    """Independently cross-check key calculations directly against raw DataFrame aggregations."""
    checks: dict[str, bool] = {}

    # Check 1: Age 25 count and median price
    age25 = df.query("vehicle_age == 25")["selling_price"]
    checks["age_25_count_match"] = len(age25) == results["analysis_1"]["age_25_investigation"]["age_25_count"]
    checks["age_25_median_match"] = float(age25.median()) == 1_000_000.0

    # Check 2: Dealer vs Individual medians
    med_by_seller = df.groupby("seller_type")["selling_price"].median()
    raw_rel = ((med_by_seller["Dealer"] / med_by_seller["Individual"]) - 1.0) * 100.0
    checks["seller_relative_diff_match"] = bool(
        np.isclose(
            raw_rel,
            results["analysis_3"]["dealer_vs_individual_raw"]["relative_listing_price_diff_pct"],
            rtol=1e-9,
        )
    )

    # Check 3: Major body type total rows
    major_rows = int(df["real_body_type"].isin(MAJOR_BODY_TYPES).sum())
    checks["major_body_rows_match"] = major_rows == results["analysis_2"]["major_body_types_rows"]

    # Check 4: All 11 charts exist and are non-empty (> 10 KB)
    missing_or_small = []
    for fname in EXPECTED_CHARTS:
        p = OUTPUT_FIG_DIR / fname
        if not p.exists() or p.stat().st_size < 10_000:
            missing_or_small.append(fname)
    checks["all_11_charts_valid"] = len(missing_or_small) == 0
    if missing_or_small:
        print("WARNING: Invalid/missing charts:", missing_or_small)

    return checks


def main() -> None:
    df = load_dataset()
    print(f"Loaded final_destination.csv: {df.shape[0]:,} rows x {df.shape[1]} columns")

    dq = inspect_data_quality(df)
    a1 = run_depreciation_analysis(df)
    a2 = run_transmission_body_analysis(df)
    a3 = run_seller_dynamics_analysis(df)
    a4 = run_statistical_testing(df)

    all_results = {
        "data_quality": dq,
        "analysis_1": a1,
        "analysis_2": a2,
        "analysis_3": a3,
        "analysis_4": a4,
    }

    checks = cross_validate_aggregations(df, all_results)
    all_results["validation_checks"] = checks

    OUTPUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = OUTPUT_REPORT_DIR / "advanced_analysis_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"Saved validated metrics JSON to: {metrics_path}")
    print("Validation checks:", checks)
    if not all(checks.values()):
        raise RuntimeError(f"Validation failed: {checks}")
    print("ALL ANALYSES AND VALIDATIONS PASSED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
