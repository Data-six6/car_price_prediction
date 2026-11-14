"""Focused investigation: Why vehicle_age == 2 has a 9.1% higher median listing price than vehicle_age == 1."""

from __future__ import annotations

import json
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from common import (
    LAKH,
    OUTPUT_REPORT_DIR,
    PALETTE,
    bootstrap_median_diff_ci,
    configure_plot_style,
    load_dataset,
    save_chart,
)


def summarize_numeric_dimension(g1: pd.DataFrame, g2: pd.DataFrame, col: str, label: str) -> dict[str, Any]:
    """Compare a numeric column across Age 1 and Age 2 with Mann-Whitney U."""
    u_stat, p_val = stats.mannwhitneyu(g2[col], g1[col], alternative="two-sided")
    r_rb = (2.0 * u_stat) / (len(g1) * len(g2)) - 1.0
    med1, med2 = float(g1[col].median()), float(g2[col].median())
    mean1, mean2 = float(g1[col].mean()), float(g2[col].mean())
    return {
        "metric": label,
        "column": col,
        "age1_median": med1,
        "age2_median": med2,
        "median_diff": med2 - med1,
        "median_pct_diff": ((med2 / med1) - 1.0) * 100.0 if med1 else None,
        "age1_mean": mean1,
        "age2_mean": mean2,
        "mean_diff": mean2 - mean1,
        "mean_pct_diff": ((mean2 / mean1) - 1.0) * 100.0 if mean1 else None,
        "age1_p25": float(g1[col].quantile(0.25)),
        "age1_p75": float(g1[col].quantile(0.75)),
        "age2_p25": float(g2[col].quantile(0.25)),
        "age2_p75": float(g2[col].quantile(0.75)),
        "mann_whitney_u": float(u_stat),
        "p_value": float(p_val),
        "rank_biserial_r": float(r_rb),
    }


def summarize_categorical_dimension(g1: pd.DataFrame, g2: pd.DataFrame, col: str) -> list[dict[str, Any]]:
    """Compare category counts and shares (%) between Age 1 and Age 2."""
    c1 = g1[col].value_counts()
    c2 = g2[col].value_counts()
    p1 = g1[col].value_counts(normalize=True) * 100.0
    p2 = g2[col].value_counts(normalize=True) * 100.0
    cats = sorted(set(c1.index) | set(c2.index), key=lambda k: -(p2.get(k, 0.0) + p1.get(k, 0.0)))
    rows = []
    for cat in cats:
        rows.append(
            {
                "category": str(cat),
                "age1_count": int(c1.get(cat, 0)),
                "age1_pct": float(p1.get(cat, 0.0)),
                "age2_count": int(c2.get(cat, 0)),
                "age2_pct": float(p2.get(cat, 0.0)),
                "pp_diff_age2_minus_age1": float(p2.get(cat, 0.0) - p1.get(cat, 0.0)),
            }
        )
    return rows


def compute_model_mix_shifts(sub: pd.DataFrame) -> dict[str, Any]:
    """Inspect model_grouped composition shifts and matched within-model price comparisons."""
    g1 = sub[sub["vehicle_age"] == 1]
    g2 = sub[sub["vehicle_age"] == 2]

    c1 = g1["model_grouped"].value_counts()
    c2 = g2["model_grouped"].value_counts()
    p1 = g1["model_grouped"].value_counts(normalize=True) * 100.0
    p2 = g2["model_grouped"].value_counts(normalize=True) * 100.0
    med_all = sub.groupby("model_grouped")["selling_price"].median()

    comp = pd.DataFrame(
        {
            "age1_count": c1,
            "age1_pct": p1,
            "age2_count": c2,
            "age2_pct": p2,
            "overall_median_price": med_all,
        }
    ).fillna(0.0)
    comp["age1_count"] = comp["age1_count"].astype(int)
    comp["age2_count"] = comp["age2_count"].astype(int)
    comp["pp_diff"] = comp["age2_pct"] - comp["age1_pct"]
    comp = comp.reset_index().rename(columns={"index": "model_grouped"})

    # Same-model matched comparison for models with >= 5 listings in BOTH ages
    matched_models = sorted(set(c1[c1 >= 5].index) & set(c2[c2 >= 5].index))
    matched_rows = []
    for m in matched_models:
        m1 = g1[g1["model_grouped"] == m]["selling_price"]
        m2 = g2[g2["model_grouped"] == m]["selling_price"]
        med1, med2 = float(m1.median()), float(m2.median())
        matched_rows.append(
            {
                "model_grouped": m,
                "age1_count": int(len(m1)),
                "age2_count": int(len(m2)),
                "age1_median_price": med1,
                "age2_median_price": med2,
                "pct_diff": ((med2 / med1) - 1.0) * 100.0,
            }
        )
    matched_df = pd.DataFrame(matched_rows).sort_values("pct_diff", ascending=True)

    return {
        "unique_models_age1": int(g1["model_grouped"].nunique()),
        "unique_models_age2": int(g2["model_grouped"].nunique()),
        "largest_share_gains_age2": comp.sort_values("pp_diff", ascending=False).head(10).to_dict(orient="records"),
        "largest_share_drops_age2": comp.sort_values("pp_diff", ascending=True).head(10).to_dict(orient="records"),
        "matched_within_model": matched_df.to_dict(orient="records"),
    }


def fit_nested_regressions(sub: pd.DataFrame) -> list[dict[str, Any]]:
    """Fit sequential log(selling_price) OLS models with HC3 SEs to isolate confounders."""
    work = sub.copy()
    work["age2"] = (work["vehicle_age"] == 2).astype(int)
    work["log_price"] = np.log(work["selling_price"])

    specs = [
        ("M0: Unadjusted (Age 2 vs Age 1 only)", "log_price ~ age2"),
        ("M1: + Usage & Specs (km, engine, power)", "log_price ~ age2 + np.log1p(km_driven) + engine + max_power"),
        (
            "M2: + Gearbox, Body Type, Seller Type",
            "log_price ~ age2 + np.log1p(km_driven) + engine + max_power + C(transmission_type) + C(real_body_type) + C(seller_type)",
        ),
        ("M3a: Model Fixed Effects Only", "log_price ~ age2 + C(model_grouped)"),
        (
            "M3b: Full Model + Specs (excl. km penalty)",
            "log_price ~ age2 + engine + max_power + C(transmission_type) + C(real_body_type) + C(seller_type) + C(model_grouped)",
        ),
        (
            "M4: Full Controlled Model (incl. km)",
            "log_price ~ age2 + np.log1p(km_driven) + engine + max_power + C(transmission_type) + C(real_body_type) + C(seller_type) + C(model_grouped)",
        ),
    ]

    rows = []
    for name, formula in specs:
        fit = smf.ols(formula, data=work).fit(cov_type="HC3")
        beta = float(fit.params["age2"])
        ci_lo, ci_hi = [float(x) for x in fit.conf_int().loc["age2"]]
        rows.append(
            {
                "model": name,
                "formula": formula,
                "n_obs": int(fit.nobs),
                "r2": float(fit.rsquared),
                "adj_r2": float(fit.rsquared_adj),
                "beta_age2": beta,
                "se_hc3": float(fit.bse["age2"]),
                "t_stat": float(fit.tvalues["age2"]),
                "p_value": float(fit.pvalues["age2"]),
                "pct_effect": float((np.exp(beta) - 1.0) * 100.0),
                "ci95_pct_low": float((np.exp(ci_lo) - 1.0) * 100.0),
                "ci95_pct_high": float((np.exp(ci_hi) - 1.0) * 100.0),
            }
        )
    return rows


def create_charts(
    sub: pd.DataFrame,
    price_tiers: list[dict[str, Any]],
    body_rows: list[dict[str, Any]],
    seller_rows: list[dict[str, Any]],
    trans_rows: list[dict[str, Any]],
    model_mix: dict[str, Any],
    reg_rows: list[dict[str, Any]],
) -> list[str]:
    """Generate two diagnostic charts for Age 1 vs Age 2."""
    configure_plot_style()
    saved = []

    # Chart 1: 2x2 Composition & Spec Comparison
    fig, axes = plt.subplots(2, 2, figsize=(15.5, 11.2))
    fig.subplots_adjust(hspace=0.32, wspace=0.22)

    # (0, 0) Price Tiers
    tiers_df = pd.DataFrame(price_tiers)
    x = np.arange(len(tiers_df))
    w = 0.36
    b1 = axes[0, 0].bar(x - w / 2, tiers_df["age1_pct"], width=w, color=PALETTE["secondary"], label="Age 1 (n=220)")
    b2 = axes[0, 0].bar(x + w / 2, tiers_df["age2_pct"], width=w, color=PALETTE["primary"], label="Age 2 (n=1,134)")
    for bar in b1:
        h = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=8)
    for bar in b2:
        h = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=8)
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(["<₹5L", "₹5L–10L", "₹10L–15L", "₹15L–25L", "≥₹25L"])
    axes[0, 0].set_ylim(0, 62)
    axes[0, 0].set_ylabel("Share of Listings (%)")
    axes[0, 0].set_title("A. Price-Bracket Shift: Fewer <₹5L Budget, More ₹10L–25L at Age 2")
    axes[0, 0].legend(loc="upper right")

    # (0, 1) Key Mix Drivers: Body Type, Seller Type, Transmission
    body_map = {r["category"]: r for r in body_rows}
    seller_map = {r["category"]: r for r in seller_rows}
    trans_map = {r["category"]: r for r in trans_rows}
    mix_labels = ["Sedan\n(Body)", "Unknown\n(Body)", "Hatchback\n(Body)", "SUV\n(Body)", "Dealer\n(Seller)", "Automatic\n(Gearbox)"]
    mix_age1 = [
        body_map["Sedan"]["age1_pct"],
        body_map["Unknown"]["age1_pct"],
        body_map["Hatchback"]["age1_pct"],
        body_map["SUV"]["age1_pct"],
        seller_map["Dealer"]["age1_pct"],
        trans_map["Automatic"]["age1_pct"],
    ]
    mix_age2 = [
        body_map["Sedan"]["age2_pct"],
        body_map["Unknown"]["age2_pct"],
        body_map["Hatchback"]["age2_pct"],
        body_map["SUV"]["age2_pct"],
        seller_map["Dealer"]["age2_pct"],
        trans_map["Automatic"]["age2_pct"],
    ]
    xm = np.arange(len(mix_labels))
    m1 = axes[0, 1].bar(xm - w / 2, mix_age1, width=w, color=PALETTE["secondary"], label="Age 1")
    m2 = axes[0, 1].bar(xm + w / 2, mix_age2, width=w, color=PALETTE["primary"], label="Age 2")
    for bar in m1:
        h = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=7.8)
    for bar in m2:
        h = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width() / 2, h + 0.8, f"{h:.1f}%", ha="center", va="bottom", fontsize=7.8)
    axes[0, 1].set_xticks(xm)
    axes[0, 1].set_xticklabels(mix_labels, fontsize=8.5)
    axes[0, 1].set_ylim(0, 58)
    axes[0, 1].set_ylabel("Share of Listings (%)")
    axes[0, 1].set_title("B. Mix Shifts: Sedan Nearly Doubles (8.2%→15.1%) & More Dealers")
    axes[0, 1].legend(loc="upper right")

    # (1, 0) Top Model Share Changes (Age 2 - Age 1 percentage points)
    gains = model_mix["largest_share_gains_age2"][:5]
    drops = model_mix["largest_share_drops_age2"][:5]
    combined = list(reversed(drops)) + list(reversed(gains))
    comb_df = pd.DataFrame(combined).sort_values("pp_diff")
    colors = [PALETTE["danger"] if v < 0 else PALETTE["primary"] for v in comb_df["pp_diff"]]
    y_pos = np.arange(len(comb_df))
    axes[1, 0].barh(y_pos, comb_df["pp_diff"], color=colors, alpha=0.9)
    axes[1, 0].axvline(0, color="#333333", linewidth=1)
    for i, (_, row) in enumerate(comb_df.iterrows()):
        v = row["pp_diff"]
        med_l = row["overall_median_price"] / LAKH
        offset = 0.08 if v >= 0 else -0.08
        ha = "left" if v >= 0 else "right"
        axes[1, 0].text(v + offset, i, f"{v:+.2f} pp (₹{med_l:.1f}L)", va="center", ha=ha, fontsize=8)
    axes[1, 0].set_yticks(y_pos)
    axes[1, 0].set_yticklabels(comb_df["model_grouped"])
    axes[1, 0].set_xlim(-5.8, 5.4)
    axes[1, 0].set_xlabel("Share Change from Age 1 to Age 2 (Percentage Points)")
    axes[1, 0].set_title("C. Biggest Model-Mix Shifts (Median Price Shown)")

    # (1, 1) Spec & Mileage Medians (% Change from Age 1 to Age 2)
    g1, g2 = sub[sub["vehicle_age"] == 1], sub[sub["vehicle_age"] == 2]
    spec_items = [
        ("Median Price\n(₹7.50L→₹8.18L)", (g2["selling_price"].median() / g1["selling_price"].median() - 1) * 100),
        ("Max Power\n(81.9→88.7 bhp)", (g2["max_power"].median() / g1["max_power"].median() - 1) * 100),
        ("Engine Size\n(1,197→1,248 cc)", (g2["engine"].median() / g1["engine"].median() - 1) * 100),
        ("Fuel Efficiency\n(20.2→19.7 kmpl)", (g2["mileage"].median() / g1["mileage"].median() - 1) * 100),
        ("Odometer Km\n(6.0k→15.0k km)", (g2["km_driven"].median() / g1["km_driven"].median() - 1) * 100),
    ]
    s_labels = [x[0] for x in spec_items]
    s_vals = [x[1] for x in spec_items]
    s_cols = [PALETTE["accent"], PALETTE["primary"], PALETTE["primary"], PALETTE["muted"], PALETTE["secondary"]]
    xs = np.arange(len(s_items := s_labels))
    bars = axes[1, 1].bar(xs, s_vals, color=s_cols, width=0.58)
    axes[1, 1].axhline(0, color="#333333", linewidth=1)
    for bar, v in zip(bars, s_vals):
        va = "bottom" if v >= 0 else "top"
        dy = 3.5 if v >= 0 else -5.5
        axes[1, 1].text(bar.get_x() + bar.get_width() / 2, v + dy, f"{v:+.1f}%", ha="center", va=va, fontsize=8.5, fontweight="bold")
    axes[1, 1].set_xticks(xs)
    axes[1, 1].set_xticklabels(s_items, fontsize=8.2)
    axes[1, 1].set_ylim(-24, 175)
    axes[1, 1].set_ylabel("% Change in Median (Age 2 vs Age 1)")
    axes[1, 1].set_title("D. Spec & Usage Shifts: Larger Engines & Power (+4% to +8%) + 2.5× Km")

    fig.suptitle("Why Age-2 Listings Have a 9.1% Higher Median Price Than Age-1 Listings", fontsize=14, fontweight="bold", y=0.98)
    saved.append(str(save_chart(fig, "age_1_vs_2_composition_comparison.png")))

    # Chart 2: Same-model comparison & Nested Regression Decomposition
    fig, axes = plt.subplots(1, 2, figsize=(16.5, 6.6))
    fig.subplots_adjust(wspace=0.62)

    # Left: Same-model median % differences
    m_df = pd.DataFrame(model_mix["matched_within_model"])
    m_colors = [PALETTE["success"] if v > 0 else PALETTE["primary"] for v in m_df["pct_diff"]]
    ym = np.arange(len(m_df))
    axes[0].barh(ym, m_df["pct_diff"], color=m_colors, alpha=0.9)
    axes[0].axvline(0, color="#333333", linewidth=1.1)
    axes[0].axvline(9.07, color=PALETTE["danger"], linestyle="--", linewidth=1.3, label="Raw All-Car Median Gap (+9.1%)")
    for i, (_, r) in enumerate(m_df.iterrows()):
        v = r["pct_diff"]
        off = 0.35 if v >= 0 else -0.35
        ha = "left" if v >= 0 else "right"
        axes[0].text(v + off, i, f"{v:+.1f}%", va="center", ha=ha, fontsize=8)
    axes[0].set_yticks(ym)
    axes[0].set_yticklabels([f"{r['model_grouped']} ({r['age1_count']} vs {r['age2_count']})" for _, r in m_df.iterrows()], fontsize=8.5)
    axes[0].set_xlim(-18.5, 13.5)
    axes[0].set_xlabel("Median Price Change Within Exact Same Model (%)")
    axes[0].set_title("Same-Model Check (16 Common Models)\nMost Models Stay Flat or Drop")
    axes[0].legend(loc="lower left", fontsize=8.5)

    # Right: Regression forest plot
    short_reg_labels = [
        "M4: Full Controls (incl. km)",
        "M3b: Full Model + Specs (no km)",
        "M3a: Model Fixed Effects Only",
        "M2: + Gearbox, Body, Seller",
        "M1: + Km, Engine, Power",
        "M0: Unadjusted (Age 2 vs 1)",
    ]
    reg_df = pd.DataFrame(reg_rows).iloc[::-1].reset_index(drop=True)
    yr = np.arange(len(reg_df))
    x_err_low = reg_df["pct_effect"] - reg_df["ci95_pct_low"]
    x_err_high = reg_df["ci95_pct_high"] - reg_df["pct_effect"]
    axes[1].errorbar(
        reg_df["pct_effect"],
        yr,
        xerr=[x_err_low, x_err_high],
        fmt="o",
        color=PALETTE["primary"],
        ecolor=PALETTE["secondary"],
        elinewidth=2.5,
        capsize=5,
        markersize=8,
    )
    axes[1].axvline(0, color="#333333", linewidth=1.2)
    axes[1].axvline(9.07, color=PALETTE["danger"], linestyle="--", linewidth=1.3, label="Unadjusted Median Gap (+9.1%)")
    for i, r in reg_df.iterrows():
        axes[1].text(
            r["pct_effect"],
            i + 0.22,
            f"{r['pct_effect']:+.2f}% (p={r['p_value']:.2f}, R²={r['r2']:.2f})",
            ha="center",
            va="bottom",
            fontsize=8.2,
            color=PALETTE["primary"],
            fontweight="bold",
        )
    axes[1].set_yticks(yr)
    axes[1].set_yticklabels(short_reg_labels, fontsize=9)
    axes[1].set_ylim(-0.6, len(reg_df) - 0.2)
    axes[1].set_xlim(-7.5, 18.0)
    axes[1].set_xlabel("Estimated Age-2 vs Age-1 Price Difference (%) with 95% HC3 CI")
    axes[1].set_title("Regression Decomposition (HC3)\nGap Vanishes Once Specs & Model Are Fixed")
    axes[1].legend(loc="lower right", fontsize=8.5)

    fig.suptitle("Controlled Analysis: Does the Age-2 Price Advantage Persist for Comparable Cars?", fontsize=13.5, fontweight="bold", y=1.03)
    saved.append(str(save_chart(fig, "age_1_vs_2_regression_decomposition.png")))

    return saved


def run_age_1_vs_2_investigation() -> dict[str, Any]:
    """Run complete Age 1 vs Age 2 comparison and save results + charts."""
    df = load_dataset()
    sub = df[df["vehicle_age"].isin([1, 2])].copy()
    g1 = sub[sub["vehicle_age"] == 1]
    g2 = sub[sub["vehicle_age"] == 2]

    med_diff, boot_lo, boot_hi = bootstrap_median_diff_ci(
        g2["selling_price"].to_numpy(),
        g1["selling_price"].to_numpy(),
    )

    numeric_comparisons = [
        summarize_numeric_dimension(g1, g2, "selling_price", "Listing Price (INR)"),
        summarize_numeric_dimension(g1, g2, "km_driven", "Odometer Mileage (km)"),
        summarize_numeric_dimension(g1, g2, "mileage", "Fuel Efficiency (kmpl)"),
        summarize_numeric_dimension(g1, g2, "engine", "Engine Capacity (cc)"),
        summarize_numeric_dimension(g1, g2, "max_power", "Max Power (bhp)"),
    ]
    numeric_comparisons[0]["bootstrap_median_diff_ci95"] = [boot_lo, boot_hi]

    bins = [0, 500_000, 1_000_000, 1_500_000, 2_500_000, 100_000_000]
    labels = ["<₹5L", "₹5L–₹10L", "₹10L–₹15L", "₹15L–₹25L", ">=₹25L"]
    sub["price_tier"] = pd.cut(sub["selling_price"], bins=bins, labels=labels, right=False)
    t1_c = sub[sub["vehicle_age"] == 1]["price_tier"].value_counts()
    t2_c = sub[sub["vehicle_age"] == 2]["price_tier"].value_counts()
    t1_p = sub[sub["vehicle_age"] == 1]["price_tier"].value_counts(normalize=True) * 100.0
    t2_p = sub[sub["vehicle_age"] == 2]["price_tier"].value_counts(normalize=True) * 100.0
    price_tiers = [
        {
            "tier": lbl,
            "age1_count": int(t1_c.get(lbl, 0)),
            "age1_pct": float(t1_p.get(lbl, 0.0)),
            "age2_count": int(t2_c.get(lbl, 0)),
            "age2_pct": float(t2_p.get(lbl, 0.0)),
            "pp_diff": float(t2_p.get(lbl, 0.0) - t1_p.get(lbl, 0.0)),
        }
        for lbl in labels
    ]

    trans_rows = summarize_categorical_dimension(g1, g2, "transmission_type")
    body_rows = summarize_categorical_dimension(g1, g2, "real_body_type")
    seller_rows = summarize_categorical_dimension(g1, g2, "seller_type")
    model_mix = compute_model_mix_shifts(sub)
    reg_rows = fit_nested_regressions(sub)

    charts = create_charts(sub, price_tiers, body_rows, seller_rows, trans_rows, model_mix, reg_rows)

    out = {
        "counts": {"age1": int(len(g1)), "age2": int(len(g2)), "total": int(len(sub))},
        "numeric_comparisons": numeric_comparisons,
        "price_tiers": price_tiers,
        "transmission_distribution": trans_rows,
        "body_type_distribution": body_rows,
        "seller_type_distribution": seller_rows,
        "model_mix": model_mix,
        "nested_regressions": reg_rows,
        "charts": charts,
    }

    OUTPUT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUTPUT_REPORT_DIR / "age_1_vs_2_metrics.json"
    out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    res = run_age_1_vs_2_investigation()
    print("Counts:", res["counts"])
    for t in res["price_tiers"]:
        print("Tier:", t)
    print("Body type top rows:", res["body_type_distribution"][:5])
    print("Regressions:")
    for r in res["nested_regressions"]:
        print(f"  {r['model']}: {r['pct_effect']:+.2f}% [{r['ci95_pct_low']:+.2f}%, {r['ci95_pct_high']:+.2f}%], p={r['p_value']:.4f}, R2={r['r2']:.4f}")
    print("Charts:", res["charts"])
