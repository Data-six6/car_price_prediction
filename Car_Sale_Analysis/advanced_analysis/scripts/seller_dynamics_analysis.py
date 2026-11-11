"""Analysis 3: Dealer vs Individual seller dynamics (with Trustmark Dealer analyzed separately)."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

from common import (
    LAKH,
    MAJOR_BODY_TYPES,
    PALETTE,
    configure_plot_style,
    load_dataset,
    save_chart,
    set_lakhs_axis,
)


def compute_seller_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute price and inventory profile metrics across all seller types."""
    order = ["Dealer", "Individual", "Trustmark Dealer"]
    rows = []
    for stype in order:
        sub = df[df["seller_type"] == stype]
        rows.append(
            {
                "seller_type": stype,
                "analysis_role": (
                    "Primary Comparison" if stype in {"Dealer", "Individual"} else "Separate (Small Sample)"
                ),
                "count": int(len(sub)),
                "share_pct": float(len(sub) / len(df) * 100.0),
                "mean_price": float(sub["selling_price"].mean()),
                "median_price": float(sub["selling_price"].median()),
                "std_price": float(sub["selling_price"].std()),
                "p25_price": float(sub["selling_price"].quantile(0.25)),
                "p75_price": float(sub["selling_price"].quantile(0.75)),
                "median_age": float(sub["vehicle_age"].median()),
                "mean_age": float(sub["vehicle_age"].mean()),
                "p25_age": float(sub["vehicle_age"].quantile(0.25)),
                "p75_age": float(sub["vehicle_age"].quantile(0.75)),
                "median_km": float(sub["km_driven"].median()),
                "mean_km": float(sub["km_driven"].mean()),
                "p25_km": float(sub["km_driven"].quantile(0.25)),
                "p75_km": float(sub["km_driven"].quantile(0.75)),
                "automatic_share_pct": float((sub["transmission_type"] == "Automatic").mean() * 100.0),
                "median_engine_cc": float(sub["engine"].median()),
                "median_power_bhp": float(sub["max_power"].median()),
            }
        )
    return pd.DataFrame(rows)


def fit_seller_regression(df: pd.DataFrame, subset_label: str) -> dict[str, Any]:
    """Fit OLS on log(selling_price) with HC3 SEs controlling for age, km, engine, transmission, body type, model."""
    work = df.copy()
    work["log_price"] = np.log(work["selling_price"])
    formula = (
        "log_price ~ C(seller_type, Treatment(reference='Individual')) "
        "+ vehicle_age + km_driven + engine "
        "+ C(transmission_type, Treatment(reference='Manual')) "
        "+ C(real_body_type) + C(model_grouped)"
    )
    model = smf.ols(formula, data=work).fit(cov_type="HC3")
    conf = model.conf_int()

    seller_terms = {}
    for stype in ["Dealer", "Trustmark Dealer"]:
        term = f"C(seller_type, Treatment(reference='Individual'))[T.{stype}]"
        if term in model.params.index:
            coef = float(model.params[term])
            ci_l, ci_h = float(conf.loc[term, 0]), float(conf.loc[term, 1])
            seller_terms[stype] = {
                "coef": coef,
                "hc3_se": float(model.bse[term]),
                "t_stat": float(model.tvalues[term]),
                "p_value": float(model.pvalues[term]),
                "ci95_low": ci_l,
                "ci95_high": ci_h,
                "pct_diff_vs_individual": float((np.exp(coef) - 1.0) * 100.0),
                "pct_ci95_low": float((np.exp(ci_l) - 1.0) * 100.0),
                "pct_ci95_high": float((np.exp(ci_h) - 1.0) * 100.0),
            }

    return {
        "subset": subset_label,
        "n_obs": int(model.nobs),
        "r2": float(model.rsquared),
        "adj_r2": float(model.rsquared_adj),
        "rmse_log": float(np.sqrt(np.mean(model.resid**2))),
        "seller_coefficients_vs_individual": seller_terms,
    }


def create_charts(df: pd.DataFrame, summary_df: pd.DataFrame, reg_full: dict[str, Any]) -> list[str]:
    """Generate the 4 required visualizations for Analysis 3."""
    configure_plot_style()
    saved = []

    color_map = {
        "Dealer": PALETTE["dealer"],
        "Individual": PALETTE["individual"],
        "Trustmark Dealer": PALETTE["trustmark"],
    }
    dealer_row = summary_df[summary_df["seller_type"] == "Dealer"].iloc[0]
    indiv_row = summary_df[summary_df["seller_type"] == "Individual"].iloc[0]
    rel_diff_pct = ((dealer_row["median_price"] / indiv_row["median_price"]) - 1.0) * 100.0

    # 7. seller_price_comparison.png
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5), gridspec_kw={"width_ratios": [1.3, 1.0]})
    primary = summary_df[summary_df["seller_type"].isin(["Dealer", "Individual"])].copy()
    x = np.arange(len(primary))
    w = 0.35
    b1 = axes[0].bar(x - w / 2, primary["median_price"], width=w, color=PALETTE["primary"], label="Median Listing Price")
    b2 = axes[0].bar(x + w / 2, primary["mean_price"], width=w, color=PALETTE["secondary"], label="Mean Listing Price")
    for b in list(b1) + list(b2):
        axes[0].text(
            b.get_x() + b.get_width() / 2,
            b.get_height() + 20_000,
            f"₹{b.get_height()/LAKH:.2f}L",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f"{r['seller_type']}\n(n={int(r['count']):,})" for _, r in primary.iterrows()], fontweight="bold")
    set_lakhs_axis(axes[0], "y")
    axes[0].set_ylim(0, primary["mean_price"].max() * 1.24)
    axes[0].set_title(
        f"Dealer vs. Individual Listing Prices\n(Relative Median Listing-Price Difference: +{rel_diff_pct:.1f}%)"
    )
    axes[0].set_ylabel("Listing Price (INR, Lakhs)")
    axes[0].legend(loc="upper right")

    # Right panel: All 3 seller types median + IQR error bars + controlled regression difference
    y_pos = np.arange(len(summary_df))
    meds = summary_df["median_price"].to_numpy()
    p25 = summary_df["p25_price"].to_numpy()
    p75 = summary_df["p75_price"].to_numpy()
    axes[1].errorbar(
        meds,
        y_pos,
        xerr=[meds - p25, p75 - meds],
        fmt="o",
        color="black",
        ecolor=PALETTE["muted"],
        elinewidth=3,
        capsize=6,
        markersize=8,
    )
    for idx, (_, row) in enumerate(summary_df.iterrows()):
        axes[1].scatter(row["median_price"], idx, color=color_map[row["seller_type"]], s=110, zorder=5)
        axes[1].text(
            row["p75_price"] + 25_000,
            idx,
            f"Median: ₹{row['median_price']/LAKH:.2f}L\nIQR: ₹{row['p25_price']/LAKH:.2f}L–₹{row['p75_price']/LAKH:.2f}L",
            va="center",
            fontsize=8.3,
        )
    set_lakhs_axis(axes[1], "x")
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels(
        [
            f"{r['seller_type']}\n(n={int(r['count']):,})" + (" *" if r["seller_type"] == "Trustmark Dealer" else "")
            for _, r in summary_df.iterrows()
        ],
        fontweight="bold",
    )
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, summary_df["p75_price"].max() * 1.55)
    adj_dealer = reg_full["seller_coefficients_vs_individual"]["Dealer"]["pct_diff_vs_individual"]
    axes[1].set_title(
        f"Median & IQR by Seller Type (*Trustmark analyzed separately)\n"
        f"After Controls (Age, km, Engine, Trans, Body, Model): Dealer = {adj_dealer:+.1f}%"
    )
    axes[1].set_xlabel("Listing Price (INR, Lakhs)")

    fig.suptitle("Seller Listing-Price Comparison (Raw Difference vs. Confounder-Controlled Gap)", y=1.03)
    saved.append(str(save_chart(fig, "seller_price_comparison.png")))

    # 8. seller_vehicle_age_comparison.png
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))
    sns.boxplot(
        data=df,
        x="seller_type",
        y="vehicle_age",
        order=["Dealer", "Individual", "Trustmark Dealer"],
        hue="seller_type",
        palette=color_map,
        legend=False,
        ax=axes[0],
        showfliers=False,
    )
    for idx, (_, row) in enumerate(summary_df.iterrows()):
        axes[0].text(
            idx,
            row["median_age"] + 0.35,
            f"Med: {row['median_age']:.1f}y\nMean: {row['mean_age']:.2f}y",
            ha="center",
            va="bottom",
            fontsize=8.3,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85, edgecolor="none"),
        )
    axes[0].set_title("Vehicle Age Boxplot by Seller Type (Outliers Hidden)")
    axes[0].set_xlabel("Seller Type (Trustmark Dealer: n=173 separate)")
    axes[0].set_ylabel("Vehicle Age (Years)")

    for stype in ["Dealer", "Individual", "Trustmark Dealer"]:
        sub = df[df["seller_type"] == stype]
        sns.kdeplot(
            sub["vehicle_age"],
            ax=axes[1],
            color=color_map[stype],
            linewidth=2.2,
            linestyle="--" if stype == "Trustmark Dealer" else "-",
            label=f"{stype} (n={len(sub):,}, med={sub['vehicle_age'].median():.0f}y)",
        )
    axes[1].set_xlim(0, 20)
    axes[1].set_title("Vehicle Age Density Distribution by Seller Type")
    axes[1].set_xlabel("Vehicle Age (Years)")
    axes[1].set_ylabel("Density")
    axes[1].legend(loc="upper right")
    fig.suptitle("Inventory Age Profile Across Seller Types", y=1.02)
    saved.append(str(save_chart(fig, "seller_vehicle_age_comparison.png")))

    # 9. seller_mileage_comparison.png
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))
    sns.boxplot(
        data=df,
        x="seller_type",
        y="km_driven",
        order=["Dealer", "Individual", "Trustmark Dealer"],
        hue="seller_type",
        palette=color_map,
        legend=False,
        ax=axes[0],
        showfliers=False,
    )
    for idx, (_, row) in enumerate(summary_df.iterrows()):
        axes[0].text(
            idx,
            row["median_km"] + 2_000,
            f"Med: {row['median_km']:,.0f}\nMean: {row['mean_km']:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8.3,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85, edgecolor="none"),
        )
    axes[0].set_title("Odometer (km_driven) Boxplot by Seller Type (Outliers Hidden)")
    axes[0].set_xlabel("Seller Type")
    axes[0].set_ylabel("Kilometers Driven")

    p99_km = df["km_driven"].quantile(0.99)
    for stype in ["Dealer", "Individual", "Trustmark Dealer"]:
        sub = df[(df["seller_type"] == stype) & (df["km_driven"] <= p99_km)]
        sns.kdeplot(
            sub["km_driven"],
            ax=axes[1],
            color=color_map[stype],
            linewidth=2.2,
            linestyle="--" if stype == "Trustmark Dealer" else "-",
            label=f"{stype} (med={df[df['seller_type']==stype]['km_driven'].median():,.0f} km)",
        )
    axes[1].set_title(f"Odometer Density (Up to 99th Percentile: {p99_km:,.0f} km)")
    axes[1].set_xlabel("Kilometers Driven")
    axes[1].set_ylabel("Density")
    axes[1].legend(loc="upper right")
    fig.suptitle("Inventory Usage (Kilometers Driven) Profile Across Seller Types", y=1.02)
    saved.append(str(save_chart(fig, "seller_mileage_comparison.png")))

    # 10. seller_price_distribution.png
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))
    for stype in ["Dealer", "Individual", "Trustmark Dealer"]:
        sub = df[df["seller_type"] == stype]
        sns.kdeplot(
            np.log10(sub["selling_price"]),
            ax=axes[0],
            color=color_map[stype],
            linewidth=2.3,
            linestyle="--" if stype == "Trustmark Dealer" else "-",
            fill=True,
            alpha=0.14 if stype != "Trustmark Dealer" else 0.04,
            label=f"{stype} (n={len(sub):,})",
        )
    tick_vals = [100_000, 300_000, 500_000, 1_000_000, 3_000_000, 10_000_000]
    axes[0].set_xticks([np.log10(v) for v in tick_vals])
    axes[0].set_xticklabels(["₹1L", "₹3L", "₹5L", "₹10L", "₹30L", "₹100L"])
    axes[0].set_title("Listing-Price Distribution (Log10 Scale Preserving Right Tail)")
    axes[0].set_xlabel("Listing Price (INR, Log10 Scale)")
    axes[0].set_ylabel("Density")
    axes[0].legend(loc="upper right")

    sns.boxplot(
        data=df,
        x="seller_type",
        y="selling_price",
        order=["Dealer", "Individual", "Trustmark Dealer"],
        hue="seller_type",
        palette=color_map,
        legend=False,
        ax=axes[1],
    )
    axes[1].set_yscale("log")
    axes[1].set_yticks(tick_vals)
    axes[1].set_yticklabels(["₹1L", "₹3L", "₹5L", "₹10L", "₹30L", "₹100L"])
    axes[1].set_title("Listing-Price Spread & Luxury Outliers (Log Y-Axis)")
    axes[1].set_xlabel("Seller Type")
    axes[1].set_ylabel("Listing Price (INR, Log Scale)")
    fig.suptitle("Seller Listing-Price Distribution & Dispersion", y=1.02)
    saved.append(str(save_chart(fig, "seller_price_distribution.png")))

    return saved


def run_seller_dynamics_analysis(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Execute full Analysis 3 pipeline and return structured metrics."""
    if df is None:
        df = load_dataset()

    summary_df = compute_seller_summary(df)
    dealer_med = float(summary_df.loc[summary_df["seller_type"] == "Dealer", "median_price"].iloc[0])
    indiv_med = float(summary_df.loc[summary_df["seller_type"] == "Individual", "median_price"].iloc[0])
    rel_diff_pct = ((dealer_med / indiv_med) - 1.0) * 100.0
    abs_diff_inr = dealer_med - indiv_med

    reg_full = fit_seller_regression(df, subset_label="All records (n=15,229)")
    df_major = df[df["real_body_type"].isin(MAJOR_BODY_TYPES)].copy()
    reg_major = fit_seller_regression(df_major, subset_label="Major known body types (n=9,817)")

    charts = create_charts(df, summary_df, reg_full)

    return {
        "seller_summary": summary_df.to_dict(orient="records"),
        "dealer_vs_individual_raw": {
            "dealer_median_inr": dealer_med,
            "individual_median_inr": indiv_med,
            "absolute_median_diff_inr": abs_diff_inr,
            "relative_listing_price_diff_pct": rel_diff_pct,
        },
        "regression_full": reg_full,
        "regression_major_body_sensitivity": reg_major,
        "charts": charts,
    }


if __name__ == "__main__":
    out = run_seller_dynamics_analysis()
    print("Analysis 3 completed. Charts:", out["charts"])
    print("Raw Dealer vs Individual median diff (%):", round(out["dealer_vs_individual_raw"]["relative_listing_price_diff_pct"], 2))
    print("Adjusted Dealer diff (%):", round(out["regression_full"]["seller_coefficients_vs_individual"]["Dealer"]["pct_diff_vs_individual"], 2))
