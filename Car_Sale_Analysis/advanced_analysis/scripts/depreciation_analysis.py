"""Analysis 1: Age-related resale-price curve, age-25 anomaly investigation, and regression modeling."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from common import (
    LAKH,
    MIN_SAMPLE_SIZE,
    PALETTE,
    configure_plot_style,
    load_dataset,
    save_chart,
    set_lakhs_axis,
)


def compute_age_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute listing counts, median/mean/IQR prices, and YoY median % change by vehicle_age."""
    summary = (
        df.groupby("vehicle_age")
        .agg(
            count=("selling_price", "count"),
            median_price=("selling_price", "median"),
            mean_price=("selling_price", "mean"),
            std_price=("selling_price", "std"),
            p25_price=("selling_price", lambda s: s.quantile(0.25)),
            p75_price=("selling_price", lambda s: s.quantile(0.75)),
            median_km=("km_driven", "median"),
        )
        .reset_index()
        .sort_values("vehicle_age")
        .reset_index(drop=True)
    )
    summary["low_sample_flag"] = summary["count"] < MIN_SAMPLE_SIZE
    summary["age_gap_from_prev"] = summary["vehicle_age"].diff()
    summary["prev_median_price"] = summary["median_price"].shift(1)
    summary["yoy_abs_change"] = summary["median_price"] - summary["prev_median_price"]
    summary["yoy_pct_change"] = (
        (summary["median_price"] - summary["prev_median_price"])
        / summary["prev_median_price"]
        * 100.0
    )
    # Mark strictly consecutive 1-year transitions within reliable sample sizes
    summary["reliable_consecutive_yoy"] = (
        (~summary["low_sample_flag"])
        & (~summary["low_sample_flag"].shift(1, fill_value=True))
        & (summary["age_gap_from_prev"] == 1)
    )
    return summary


def investigate_age_25_anomaly(df: pd.DataFrame) -> dict[str, Any]:
    """Deep-dive investigation into the vehicle_age == 25 spike."""
    age_25_df = df[df["vehicle_age"] == 25].copy()
    neighbor_ages = [21, 22, 24, 25, 26, 29]
    neighbor_summary = []
    for age in neighbor_ages:
        sub = df[df["vehicle_age"] == age]
        if len(sub) == 0:
            neighbor_summary.append(
                {
                    "vehicle_age": age,
                    "count": 0,
                    "median_price": None,
                    "mean_price": None,
                    "models": [],
                }
            )
        else:
            neighbor_summary.append(
                {
                    "vehicle_age": age,
                    "count": int(len(sub)),
                    "median_price": float(sub["selling_price"].median()),
                    "mean_price": float(sub["selling_price"].mean()),
                    "models": sub["model_grouped"].unique().tolist(),
                }
            )

    model3_df = df[df["model_grouped"] == "3"].copy()
    model3_excluding_25 = model3_df[model3_df["vehicle_age"] != 25]

    return {
        "age_25_count": int(len(age_25_df)),
        "age_25_records": age_25_df.to_dict(orient="records"),
        "neighbor_comparison": neighbor_summary,
        "model_3_total_count": int(len(model3_df)),
        "model_3_other_max_age": int(model3_excluding_25["vehicle_age"].max()),
        "model_3_other_median_age": float(model3_excluding_25["vehicle_age"].median()),
        "model_3_other_median_price": float(model3_excluding_25["selling_price"].median()),
        "recommendation": (
            "RETAIN in master dataset with explicit data-quality flag; EXCLUDE from primary "
            "age-curve milestones and reliable-age regression models (n = 1 < 30 threshold, "
            "and record exhibits both a probable clerical age error and a body-type enrichment mismatch)."
        ),
    }


def fit_age_regression_models(df_sub: pd.DataFrame, label: str) -> dict[str, Any]:
    """Fit linear, polynomial (deg 2 & 3), log-price linear, and piecewise log-price models."""
    y = df_sub["selling_price"].to_numpy(dtype=float)
    log_y = np.log(y)
    age = df_sub["vehicle_age"].to_numpy(dtype=float)

    work = df_sub[["vehicle_age", "selling_price"]].copy()
    work["log_price"] = log_y
    work["age_sq"] = work["vehicle_age"] ** 2
    work["age_cu"] = work["vehicle_age"] ** 3
    # Piecewise knot at age 5 and age 10 to capture early vs mid vs late listing-price slope
    work["age_gt5"] = np.maximum(0.0, work["vehicle_age"] - 5.0)
    work["age_gt10"] = np.maximum(0.0, work["vehicle_age"] - 10.0)

    specs = [
        ("Linear OLS (Price ~ Age)", "selling_price ~ vehicle_age", False),
        ("Polynomial Deg 2 (Price ~ Age + Age^2)", "selling_price ~ vehicle_age + age_sq", False),
        (
            "Polynomial Deg 3 (Price ~ Age + Age^2 + Age^3)",
            "selling_price ~ vehicle_age + age_sq + age_cu",
            False,
        ),
        ("Log-Linear OLS (log(Price) ~ Age)", "log_price ~ vehicle_age", True),
        (
            "Piecewise Log-Linear (knots at Age 5 & 10)",
            "log_price ~ vehicle_age + age_gt5 + age_gt10",
            True,
        ),
    ]

    results = []
    fitted_objects = {}
    for name, formula, is_log in specs:
        model = smf.ols(formula, data=work).fit(cov_type="HC3")
        fitted_objects[name] = model
        pred_raw = model.predict(work).to_numpy()
        if is_log:
            # Duan's smearing estimator for unbiased INR back-transformation
            smearing = float(np.mean(np.exp(model.resid)))
            pred_inr = np.exp(pred_raw) * smearing
            log_r2 = float(model.rsquared)
            log_adj_r2 = float(model.rsquared_adj)
            log_rmse = float(np.sqrt(mean_squared_error(log_y, pred_raw)))
            aic_val = float(model.aic)
        else:
            pred_inr = np.clip(pred_raw, a_min=0.0, a_max=None)
            log_r2 = None
            log_adj_r2 = None
            log_rmse = None
            aic_val = float(model.aic)

        rmse_inr = float(np.sqrt(mean_squared_error(y, pred_inr)))
        mae_inr = float(mean_absolute_error(y, pred_inr))
        r2_inr = float(r2_score(y, pred_inr))

        results.append(
            {
                "subset": label,
                "model": name,
                "formula": formula,
                "n_obs": int(model.nobs),
                "is_log_model": is_log,
                "r2_price_scale": r2_inr,
                "rmse_inr": rmse_inr,
                "mae_inr": mae_inr,
                "log_r2": log_r2,
                "log_adj_r2": log_adj_r2,
                "log_rmse": log_rmse,
                "aic": aic_val,
                "params": {k: float(v) for k, v in model.params.items()},
                "pvalues": {k: float(v) for k, v in model.pvalues.items()},
            }
        )

    # Return predictions along unique sorted ages for curve plotting
    age_grid = pd.DataFrame({"vehicle_age": np.sort(work["vehicle_age"].unique())})
    age_grid["age_sq"] = age_grid["vehicle_age"] ** 2
    age_grid["age_cu"] = age_grid["vehicle_age"] ** 3
    age_grid["age_gt5"] = np.maximum(0.0, age_grid["vehicle_age"] - 5.0)
    age_grid["age_gt10"] = np.maximum(0.0, age_grid["vehicle_age"] - 10.0)

    log_lin = fitted_objects["Log-Linear OLS (log(Price) ~ Age)"]
    pw_log = fitted_objects["Piecewise Log-Linear (knots at Age 5 & 10)"]
    # Plot conditional median estimate exp(X*beta) alongside Duan-smeared mean
    age_grid["pred_linear"] = fitted_objects["Linear OLS (Price ~ Age)"].predict(age_grid)
    age_grid["pred_poly2"] = fitted_objects["Polynomial Deg 2 (Price ~ Age + Age^2)"].predict(age_grid)
    age_grid["pred_log_median"] = np.exp(log_lin.predict(age_grid))
    age_grid["pred_piecewise_log_median"] = np.exp(pw_log.predict(age_grid))

    return {"metrics": results, "age_grid": age_grid}


def create_charts(
    df: pd.DataFrame, age_summary: pd.DataFrame, reg_reliable: dict[str, Any]
) -> list[str]:
    """Generate the 4 required visualizations for Analysis 1."""
    configure_plot_style()
    saved = []

    reliable = age_summary[~age_summary["low_sample_flag"]].copy()
    low_samp = age_summary[age_summary["low_sample_flag"]].copy()
    grid = reg_reliable["age_grid"]

    # 1. depreciation_curve.png
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.fill_between(
        reliable["vehicle_age"],
        reliable["p25_price"],
        reliable["p75_price"],
        color=PALETTE["secondary"],
        alpha=0.16,
        label="IQR Band (25th–75th pct, ages with n ≥ 30)",
    )
    ax.plot(
        reliable["vehicle_age"],
        reliable["median_price"],
        marker="o",
        linewidth=2.5,
        color=PALETTE["primary"],
        label="Median Listing Price (n ≥ 30)",
    )
    ax.plot(
        reliable["vehicle_age"],
        reliable["mean_price"],
        linestyle="--",
        linewidth=1.8,
        color=PALETTE["muted"],
        label="Mean Listing Price (n ≥ 30)",
    )
    ax.plot(
        grid["vehicle_age"],
        grid["pred_piecewise_log_median"],
        linestyle="-.",
        linewidth=2.0,
        color=PALETTE["success"],
        label="Piecewise Log-Linear Fit (knots at age 5, 10)",
    )
    ax.scatter(
        low_samp["vehicle_age"],
        low_samp["median_price"],
        color=PALETTE["danger"],
        s=75,
        zorder=5,
        marker="D",
        label="Low-Sample Age Groups (n < 30)",
    )
    for _, row in low_samp.iterrows():
        age_i = int(row["vehicle_age"])
        cnt_i = int(row["count"])
        if age_i == 25:
            ax.annotate(
                f"Age 25 Anomaly (n=1)\n₹10.00L",
                xy=(age_i, row["median_price"]),
                xytext=(age_i - 1.0, row["median_price"] - 190_000),
                arrowprops=dict(arrowstyle="->", color=PALETTE["danger"]),
                ha="center",
                fontsize=8.5,
                fontweight="bold",
                color=PALETTE["danger"],
            )
        elif age_i in {16, 18, 21}:
            ax.annotate(
                f"{age_i} (n={cnt_i})",
                xy=(age_i, row["median_price"]),
                xytext=(0, 14),
                textcoords="offset points",
                ha="center",
                fontsize=7.8,
                color=PALETTE["danger"],
            )
        elif age_i in {17, 19, 22}:
            ax.annotate(
                f"{age_i} (n={cnt_i})",
                xy=(age_i, row["median_price"]),
                xytext=(0, -16),
                textcoords="offset points",
                ha="center",
                fontsize=7.8,
                color=PALETTE["danger"],
            )
        else:
            ax.annotate(
                f"Age {age_i} (n={cnt_i})",
                xy=(age_i, row["median_price"]),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=PALETTE["danger"],
            )

    # Annotate reliable peak
    peak_row = reliable.loc[reliable["median_price"].idxmax()]
    ax.annotate(
        f"Peak reliable median:\nAge {int(peak_row['vehicle_age'])}: ₹{peak_row['median_price']/LAKH:.2f}L (n={int(peak_row['count']):,})",
        xy=(peak_row["vehicle_age"], peak_row["median_price"]),
        xytext=(peak_row["vehicle_age"] + 2.5, peak_row["median_price"] + 150_000),
        arrowprops=dict(arrowstyle="->", color=PALETTE["primary"]),
        fontsize=9,
        fontweight="bold",
        color=PALETTE["primary"],
    )
    set_lakhs_axis(ax, "y")
    ax.set_xticks(range(0, 30, 2))
    ax.set_ylim(-40_000, 1_300_000)
    ax.set_title("Estimated Age-Related Listing-Price Curve (Cross-Sectional Used-Car Listings)")
    ax.set_xlabel("Vehicle Age (Years)")
    ax.set_ylabel("Listing Price (INR, Lakhs)")
    ax.legend(loc="upper center", ncol=2, frameon=True, fontsize=8.8)
    saved.append(str(save_chart(fig, "depreciation_curve.png")))

    # 2. vehicle_age_sample_size.png
    fig, ax = plt.subplots(figsize=(12, 5.5))
    colors = [
        PALETTE["danger"] if flag else PALETTE["primary"]
        for flag in age_summary["low_sample_flag"]
    ]
    bars = ax.bar(age_summary["vehicle_age"], age_summary["count"], color=colors, width=0.78)
    ax.axhline(
        MIN_SAMPLE_SIZE,
        color=PALETTE["danger"],
        linestyle="--",
        linewidth=1.5,
        label=f"Minimum Reliability Threshold (n = {MIN_SAMPLE_SIZE})",
    )
    for bar, cnt in zip(bars, age_summary["count"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 30,
            f"{cnt:,}" if cnt >= 100 else str(cnt),
            ha="center",
            va="bottom",
            fontsize=7.5,
            rotation=45 if cnt >= 100 else 0,
        )
    ax.set_xticks(age_summary["vehicle_age"])
    ax.set_ylim(0, age_summary["count"].max() * 1.15)
    ax.set_title("Listing Sample Size by Vehicle Age (Highlighting Low-Sample Groups n < 30)")
    ax.set_xlabel("Vehicle Age (Years)")
    ax.set_ylabel("Number of Vehicle Listings")
    ax.legend(loc="upper right")
    saved.append(str(save_chart(fig, "vehicle_age_sample_size.png")))

    # 3. annual_price_change.png
    yoy = reliable[reliable["reliable_consecutive_yoy"]].copy()
    fig, ax = plt.subplots(figsize=(11.5, 5.5))
    bar_colors = [
        PALETTE["success"] if val >= 0 else PALETTE["accent"] for val in yoy["yoy_pct_change"]
    ]
    bars = ax.bar(yoy["vehicle_age"], yoy["yoy_pct_change"], color=bar_colors, width=0.72)
    ax.axhline(0, color="black", linewidth=1)
    for bar, val, cnt in zip(bars, yoy["yoy_pct_change"], yoy["count"]):
        va = "bottom" if val >= 0 else "top"
        y_off = 0.6 if val >= 0 else -0.8
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + y_off,
            f"{val:+.1f}%\n(n={cnt:,})",
            ha="center",
            va=va,
            fontsize=8,
        )
    ax.set_xticks(yoy["vehicle_age"])
    ax.set_ylim(yoy["yoy_pct_change"].min() - 6, max(yoy["yoy_pct_change"].max() + 5, 14))
    ax.set_title("Year-over-Year % Change in Median Listing Price (Reliable Ages 2–15, n ≥ 30)")
    ax.set_xlabel("Vehicle Age (Years, compared to Age - 1)")
    ax.set_ylabel("YoY Median Listing-Price Change (%)")
    saved.append(str(save_chart(fig, "annual_price_change.png")))

    # 4. age_25_anomaly.png
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5))
    old_ages = age_summary[age_summary["vehicle_age"] >= 15].copy()
    bar_cols = [
        PALETTE["danger"] if a == 25 else (PALETTE["muted"] if f else PALETTE["primary"])
        for a, f in zip(old_ages["vehicle_age"], old_ages["low_sample_flag"])
    ]
    b = axes[0].bar(old_ages["vehicle_age"].astype(str), old_ages["median_price"], color=bar_cols)
    for rect, (_, r) in zip(b, old_ages.iterrows()):
        axes[0].text(
            rect.get_x() + rect.get_width() / 2,
            rect.get_height() + 20_000,
            f"₹{r['median_price']/LAKH:.2f}L\n(n={int(r['count'])})",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold" if r["vehicle_age"] == 25 else "normal",
        )
    set_lakhs_axis(axes[0], "y")
    axes[0].set_ylim(0, old_ages["median_price"].max() * 1.18)
    axes[0].set_title("Older-Vehicle Median Price & Sample Size (Ages 15–29)")
    axes[0].set_xlabel("Vehicle Age (Years; missing ages have 0 listings)")
    axes[0].set_ylabel("Median Listing Price (INR, Lakhs)")

    # Right panel: all model == '3' (BMW 3 Series) listings
    m3 = df[df["model_grouped"] == "3"].copy()
    m3_norm = m3[m3["vehicle_age"] != 25]
    m3_25 = m3[m3["vehicle_age"] == 25]
    axes[1].scatter(
        m3_norm["vehicle_age"],
        m3_norm["selling_price"],
        color=PALETTE["secondary"],
        alpha=0.65,
        s=45,
        label=f"Other '3' (Series 320d) listings (n={len(m3_norm)})",
    )
    axes[1].scatter(
        m3_25["vehicle_age"],
        m3_25["selling_price"],
        color=PALETTE["danger"],
        s=140,
        marker="*",
        zorder=6,
        label="Age-25 Anomaly (n=1, ₹10.00L, 50k km)",
    )
    axes[1].annotate(
        "Row 15151: Age 25, ₹10.00L\n(next oldest model '3' is Age 13)",
        xy=(25, 1_000_000),
        xytext=(15.5, 1_900_000),
        arrowprops=dict(arrowstyle="->", color=PALETTE["danger"]),
        fontsize=8.5,
        color=PALETTE["danger"],
        fontweight="bold",
    )
    set_lakhs_axis(axes[1], "y")
    axes[1].set_title("Model '3' (BMW 3 Series) Price vs Age Context")
    axes[1].set_xlabel("Vehicle Age (Years)")
    axes[1].set_ylabel("Listing Price (INR, Lakhs)")
    axes[1].legend(loc="upper right", fontsize=8.5)

    fig.suptitle("Age-25 Anomaly Investigation: Single-Record Luxury Outlier & Probable Age Error", y=1.02)
    saved.append(str(save_chart(fig, "age_25_anomaly.png")))

    return saved


def run_depreciation_analysis(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Execute full Analysis 1 pipeline and return structured metrics."""
    if df is None:
        df = load_dataset()

    age_summary = compute_age_summary(df)
    anomaly_info = investigate_age_25_anomaly(df)

    df_reliable = df[~df["vehicle_age"].isin(age_summary.loc[age_summary["low_sample_flag"], "vehicle_age"])].copy()
    reg_reliable = fit_age_regression_models(df_reliable, label="Reliable Ages (n >= 30, ages 1-15)")
    reg_all = fit_age_regression_models(df, label="All Ages (ages 0-29, sensitivity)")

    # Multivariate age slope check controlling for confounders on reliable ages
    df_mv = df_reliable.copy()
    df_mv["log_price"] = np.log(df_mv["selling_price"])
    mv_model = smf.ols(
        "log_price ~ vehicle_age + np.log1p(km_driven) + engine + max_power + C(transmission_type) + C(seller_type) + C(model_grouped)",
        data=df_mv,
    ).fit(cov_type="HC3")

    chart_paths = create_charts(df, age_summary, reg_reliable)

    reliable_yoy = age_summary[age_summary["reliable_consecutive_yoy"]].copy()
    largest_decline = reliable_yoy.loc[reliable_yoy["yoy_pct_change"].idxmin()].to_dict()

    return {
        "age_summary": age_summary.to_dict(orient="records"),
        "reliable_age_range": [
            int(age_summary.loc[~age_summary["low_sample_flag"], "vehicle_age"].min()),
            int(age_summary.loc[~age_summary["low_sample_flag"], "vehicle_age"].max()),
        ],
        "reliable_row_count": int(len(df_reliable)),
        "excluded_low_sample_row_count": int(len(df) - len(df_reliable)),
        "largest_reliable_yoy_decline": largest_decline,
        "age_25_investigation": anomaly_info,
        "regression_reliable": reg_reliable["metrics"],
        "regression_all_sensitivity": reg_all["metrics"],
        "multivariate_age_control": {
            "n_obs": int(mv_model.nobs),
            "r2": float(mv_model.rsquared),
            "adj_r2": float(mv_model.rsquared_adj),
            "vehicle_age_coef": float(mv_model.params["vehicle_age"]),
            "vehicle_age_se": float(mv_model.bse["vehicle_age"]),
            "vehicle_age_pval": float(mv_model.pvalues["vehicle_age"]),
            "vehicle_age_pct_effect_per_year": float((np.exp(mv_model.params["vehicle_age"]) - 1) * 100),
            "vehicle_age_ci95": [float(x) for x in mv_model.conf_int().loc["vehicle_age"]],
        },
        "charts": chart_paths,
    }


if __name__ == "__main__":
    out = run_depreciation_analysis()
    print("Analysis 1 completed. Charts:", out["charts"])
    print("Age 25 count:", out["age_25_investigation"]["age_25_count"])
    print("Multivariate controlled age effect (%/yr):", round(out["multivariate_age_control"]["vehicle_age_pct_effect_per_year"], 2))
