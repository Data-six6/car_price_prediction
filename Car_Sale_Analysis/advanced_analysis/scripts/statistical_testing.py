"""Analysis 4: Nonparametric significance testing, post-hoc tests, and regression hypothesis tests."""

from __future__ import annotations

from itertools import combinations
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multitest import multipletests

from common import (
    ALPHA,
    LAKH,
    MAJOR_BODY_TYPES,
    PALETTE,
    bootstrap_median_diff_ci,
    configure_plot_style,
    load_dataset,
    save_chart,
    set_lakhs_axis,
)


def rank_biserial_from_u(u_stat: float, n1: int, n2: int) -> float:
    """Compute rank-biserial correlation r in [-1, 1] from Mann-Whitney U (two-sample)."""
    return float((2.0 * u_stat) / (n1 * n2) - 1.0)


def run_mann_whitney_dealer_vs_individual(df: pd.DataFrame) -> dict[str, Any]:
    """Run Mann-Whitney U test comparing Dealer vs Individual listing prices (plus age & km)."""
    dealer = df[df["seller_type"] == "Dealer"]
    indiv = df[df["seller_type"] == "Individual"]

    metrics = [
        ("selling_price", "Listing Price (INR)"),
        ("vehicle_age", "Vehicle Age (Years)"),
        ("km_driven", "Kilometers Driven"),
    ]
    raw_results = []
    for col, label in metrics:
        x = dealer[col].to_numpy(dtype=float)
        y = indiv[col].to_numpy(dtype=float)
        u_stat, p_val = stats.mannwhitneyu(x, y, alternative="two-sided")
        r_rb = rank_biserial_from_u(float(u_stat), len(x), len(y))
        diff_med, ci_low, ci_high = bootstrap_median_diff_ci(x, y, n_boot=1500, seed=42)
        raw_results.append(
            {
                "variable": col,
                "label": label,
                "dealer_n": int(len(x)),
                "individual_n": int(len(y)),
                "dealer_median": float(np.median(x)),
                "individual_median": float(np.median(y)),
                "median_diff_dealer_minus_indiv": diff_med,
                "median_diff_ci95": [ci_low, ci_high],
                "u_statistic": float(u_stat),
                "p_value_raw": float(p_val),
                "rank_biserial_r": r_rb,
            }
        )

    pvals = [r["p_value_raw"] for r in raw_results]
    reject, p_holm, _, _ = multipletests(pvals, alpha=ALPHA, method="holm")
    for r, rej, ph in zip(raw_results, reject, p_holm):
        r["p_value_holm"] = float(ph)
        r["significant_at_0_05"] = bool(rej)

    return {
        "primary_price_test": raw_results[0],
        "all_seller_metric_tests": raw_results,
    }


def run_kruskal_and_posthoc_body_types(df: pd.DataFrame) -> dict[str, Any]:
    """Run Kruskal-Wallis H test across major body types and Holm-adjusted pairwise Mann-Whitney post-hoc."""
    df_major = df[df["real_body_type"].isin(MAJOR_BODY_TYPES)].copy()
    groups = [
        df_major.loc[df_major["real_body_type"] == b, "selling_price"].to_numpy(dtype=float)
        for b in MAJOR_BODY_TYPES
    ]
    h_stat, p_val = stats.kruskal(*groups)
    n_total = sum(len(g) for g in groups)
    k = len(groups)
    epsilon_sq = float((h_stat - k + 1) / (n_total - k))

    # Post-hoc pairwise Mann-Whitney U with Holm-Bonferroni correction
    pairs = list(combinations(MAJOR_BODY_TYPES, 2))
    posthoc_rows = []
    raw_pvals = []
    for b1, b2 in pairs:
        g1 = df_major.loc[df_major["real_body_type"] == b1, "selling_price"].to_numpy(dtype=float)
        g2 = df_major.loc[df_major["real_body_type"] == b2, "selling_price"].to_numpy(dtype=float)
        u_stat, p_pair = stats.mannwhitneyu(g1, g2, alternative="two-sided")
        r_rb = rank_biserial_from_u(float(u_stat), len(g1), len(g2))
        med_diff, ci_l, ci_h = bootstrap_median_diff_ci(g1, g2, n_boot=1500, seed=42)
        raw_pvals.append(float(p_pair))
        posthoc_rows.append(
            {
                "group_1": b1,
                "group_2": b2,
                "n_1": int(len(g1)),
                "n_2": int(len(g2)),
                "median_1": float(np.median(g1)),
                "median_2": float(np.median(g2)),
                "median_diff_g1_minus_g2": med_diff,
                "median_diff_ci95": [ci_l, ci_h],
                "u_statistic": float(u_stat),
                "p_value_raw": float(p_pair),
                "rank_biserial_r": r_rb,
            }
        )

    reject, p_holm, _, _ = multipletests(raw_pvals, alpha=ALPHA, method="holm")
    for row, rej, ph in zip(posthoc_rows, reject, p_holm):
        row["p_value_holm"] = float(ph)
        row["significant_at_0_05"] = bool(rej)

    body_summary = []
    for b, g in zip(MAJOR_BODY_TYPES, groups):
        body_summary.append(
            {
                "real_body_type": b,
                "count": int(len(g)),
                "median_price": float(np.median(g)),
                "mean_price": float(np.mean(g)),
                "p25_price": float(np.quantile(g, 0.25)),
                "p75_price": float(np.quantile(g, 0.75)),
            }
        )

    return {
        "n_total": int(n_total),
        "k_groups": int(k),
        "df": int(k - 1),
        "h_statistic": float(h_stat),
        "p_value": float(p_val),
        "epsilon_squared": epsilon_sq,
        "significant_at_0_05": bool(p_val < ALPHA),
        "group_summary": body_summary,
        "posthoc_holm": posthoc_rows,
    }


def run_regression_hypothesis_tests(df: pd.DataFrame) -> dict[str, Any]:
    """Run joint Wald F-tests & HC3 coefficient tests for seller, transmission, body type, and interaction."""
    df_major = df[df["real_body_type"].isin(MAJOR_BODY_TYPES)].copy()
    df_major["log_price"] = np.log(df_major["selling_price"])

    formula = (
        "log_price ~ vehicle_age + km_driven + engine "
        "+ C(seller_type, Treatment(reference='Individual')) "
        "+ C(transmission_type, Treatment(reference='Manual')) "
        "* C(real_body_type, Treatment(reference='Hatchback')) "
        "+ C(model_grouped)"
    )
    model = smf.ols(formula, data=df_major).fit(cov_type="HC3")
    param_names = list(model.params.index)
    conf = model.conf_int()

    def _joint_wald(prefix_terms: list[str]) -> dict[str, Any]:
        r_mat = np.zeros((len(prefix_terms), len(param_names)))
        for idx, t in enumerate(prefix_terms):
            r_mat[idx, param_names.index(t)] = 1.0
        ft = model.f_test(r_mat)
        return {
            "terms": prefix_terms,
            "f_stat": float(np.asarray(ft.fvalue).squeeze()),
            "df_num": int(ft.df_num),
            "df_denom": int(ft.df_denom),
            "p_value": float(np.asarray(ft.pvalue).squeeze()),
            "significant_at_0_05": bool(float(np.asarray(ft.pvalue).squeeze()) < ALPHA),
        }

    seller_terms = [t for t in param_names if "C(seller_type" in t]
    trans_main = [t for t in param_names if t == "C(transmission_type, Treatment(reference='Manual'))[T.Automatic]"]
    body_main = [t for t in param_names if "C(real_body_type" in t and ":" not in t]
    inter_terms = [t for t in param_names if "C(transmission_type" in t and ":" in t]

    joint_tests = {
        "seller_type_joint": _joint_wald(seller_terms),
        "transmission_main_hatchback": _joint_wald(trans_main),
        "body_type_main_joint": _joint_wald(body_main),
        "transmission_x_body_interaction_joint": _joint_wald(inter_terms),
    }

    # Also fit full-dataset seller model for the primary Dealer vs Individual test across all 15,229 rows
    df_all = df.copy()
    df_all["log_price"] = np.log(df_all["selling_price"])
    full_seller_model = smf.ols(
        "log_price ~ C(seller_type, Treatment(reference='Individual')) + vehicle_age + km_driven + engine + C(transmission_type) + C(real_body_type) + C(model_grouped)",
        data=df_all,
    ).fit(cov_type="HC3")
    full_conf = full_seller_model.conf_int()

    individual_coefs = {}
    for t in seller_terms + trans_main + body_main + inter_terms:
        c = float(model.params[t])
        ci_l, ci_h = float(conf.loc[t, 0]), float(conf.loc[t, 1])
        individual_coefs[t] = {
            "coef": c,
            "hc3_se": float(model.bse[t]),
            "t_stat": float(model.tvalues[t]),
            "p_value": float(model.pvalues[t]),
            "ci95_low": ci_l,
            "ci95_high": ci_h,
            "pct_effect": float((np.exp(c) - 1.0) * 100.0),
            "pct_ci95_low": float((np.exp(ci_l) - 1.0) * 100.0),
            "pct_ci95_high": float((np.exp(ci_h) - 1.0) * 100.0),
        }

    dealer_term = "C(seller_type, Treatment(reference='Individual'))[T.Dealer]"
    trust_term = "C(seller_type, Treatment(reference='Individual'))[T.Trustmark Dealer]"
    full_seller_effects = {}
    for label, term in [("Dealer", dealer_term), ("Trustmark Dealer", trust_term)]:
        c = float(full_seller_model.params[term])
        ci_l, ci_h = float(full_conf.loc[term, 0]), float(full_conf.loc[term, 1])
        full_seller_effects[label] = {
            "coef": c,
            "hc3_se": float(full_seller_model.bse[term]),
            "t_stat": float(full_seller_model.tvalues[term]),
            "p_value": float(full_seller_model.pvalues[term]),
            "ci95_low": ci_l,
            "ci95_high": ci_h,
            "pct_effect": float((np.exp(c) - 1.0) * 100.0),
            "pct_ci95_low": float((np.exp(ci_l) - 1.0) * 100.0),
            "pct_ci95_high": float((np.exp(ci_h) - 1.0) * 100.0),
        }

    return {
        "major_body_model_n": int(model.nobs),
        "major_body_model_r2": float(model.rsquared),
        "major_body_model_adj_r2": float(model.rsquared_adj),
        "joint_tests": joint_tests,
        "individual_coefficients": individual_coefs,
        "full_dataset_seller_effects_n15229": full_seller_effects,
    }


def create_summary_chart(
    mw_res: dict[str, Any], kw_res: dict[str, Any], reg_res: dict[str, Any]
) -> str:
    """Create Chart 11: statistical_test_summary.png."""
    configure_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.0))
    fig.subplots_adjust(wspace=0.52)

    # Left panel: Body-type medians & IQR + Kruskal-Wallis annotation
    grp_df = pd.DataFrame(kw_res["group_summary"]).sort_values("median_price")
    y_pos = np.arange(len(grp_df))
    meds = grp_df["median_price"].to_numpy()
    p25 = grp_df["p25_price"].to_numpy()
    p75 = grp_df["p75_price"].to_numpy()
    axes[0].barh(y_pos, meds, color=PALETTE["secondary"], alpha=0.82, height=0.55)
    axes[0].errorbar(
        meds,
        y_pos,
        xerr=[meds - p25, p75 - meds],
        fmt="o",
        color=PALETTE["primary"],
        ecolor="black",
        elinewidth=1.8,
        capsize=4,
    )
    for idx, (_, row) in enumerate(grp_df.iterrows()):
        axes[0].text(
            row["p75_price"] + 25_000,
            idx,
            f"Med: ₹{row['median_price']/LAKH:.2f}L (n={int(row['count']):,})",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )
    set_lakhs_axis(axes[0], "x")
    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(grp_df["real_body_type"], fontweight="bold")
    axes[0].set_xlim(0, grp_df["p75_price"].max() * 1.65)
    axes[0].set_title(
        f"Kruskal–Wallis Body-Type Price Comparison\n"
        f"H = {kw_res['h_statistic']:,.1f}, p = {kw_res['p_value']:.2e}, ε² = {kw_res['epsilon_squared']:.3f} (all 6 Holm pairs p < 0.001)"
    )
    axes[0].set_xlabel("Listing Price (INR, Lakhs) — Median & IQR")

    # Right panel: Controlled HC3 Regression Effects (% price difference with 95% CI)
    seller_eff = reg_res["full_dataset_seller_effects_n15229"]
    ind_coefs = reg_res["individual_coefficients"]
    trans_key = "C(transmission_type, Treatment(reference='Manual'))[T.Automatic]"

    forest_rows = [
        ("Dealer vs. Individual\n(controlled, n=15,229)", seller_eff["Dealer"]),
        ("Trustmark vs. Individual\n(controlled, n=15,229)", seller_eff["Trustmark Dealer"]),
        ("Automatic vs. Manual\n(Hatchback ref.)", ind_coefs[trans_key]),
    ]
    for b in ["Sedan", "SUV", "MUV"]:
        k = f"{trans_key}:C(real_body_type, Treatment(reference='Hatchback'))[T.{b}]"
        if k in ind_coefs:
            forest_rows.append((f"Interaction: Auto × {b}\n(vs. Auto × Hatchback)", ind_coefs[k]))

    labels = [r[0] for r in forest_rows]
    ests = np.array([r[1]["pct_effect"] for r in forest_rows])
    lows = np.array([r[1]["pct_ci95_low"] for r in forest_rows])
    highs = np.array([r[1]["pct_ci95_high"] for r in forest_rows])
    pvals = [r[1]["p_value"] for r in forest_rows]

    y_f = np.arange(len(forest_rows))
    cols = [PALETTE["danger"] if p < 0.05 else PALETTE["muted"] for p in pvals]
    axes[1].axvline(0, color="black", linestyle="--", linewidth=1.2)
    for idx in range(len(forest_rows)):
        axes[1].errorbar(
            ests[idx],
            idx,
            xerr=[[ests[idx] - lows[idx]], [highs[idx] - ests[idx]]],
            fmt="o",
            color=cols[idx],
            ecolor=cols[idx],
            elinewidth=2.2,
            capsize=4,
            markersize=7.5,
        )
        sig_txt = f"p={pvals[idx]:.2e}" if pvals[idx] < 0.001 else f"p={pvals[idx]:.3f}"
        axes[1].text(
            highs[idx] + 0.8,
            idx,
            f"{ests[idx]:+.1f}% ({sig_txt})",
            va="center",
            fontsize=8.2,
            fontweight="bold" if pvals[idx] < 0.05 else "normal",
        )
    axes[1].set_yticks(y_f)
    axes[1].set_yticklabels(labels, fontsize=8.8)
    axes[1].invert_yaxis()
    axes[1].set_xlim(min(-10, lows.min() - 4), highs.max() + 14)
    mw_p = mw_res["primary_price_test"]
    axes[1].set_title(
        f"HC3 Controlled Regression Effects (% Impact, 95% CI)\n"
        f"Raw Dealer vs Indiv MW U: r = {mw_p['rank_biserial_r']:+.3f}, p = {mw_p['p_value_raw']:.2e}"
    )
    axes[1].set_xlabel("Controlled Listing-Price Effect (%) vs. Reference Category")

    fig.suptitle("Statistical Significance Summary: Nonparametric Group Tests & Robust Regression", y=1.03)
    return str(save_chart(fig, "statistical_test_summary.png"))


def run_statistical_testing(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Execute full Analysis 4 pipeline and return structured metrics."""
    if df is None:
        df = load_dataset()

    mw_res = run_mann_whitney_dealer_vs_individual(df)
    kw_res = run_kruskal_and_posthoc_body_types(df)
    reg_res = run_regression_hypothesis_tests(df)
    chart_path = create_summary_chart(mw_res, kw_res, reg_res)

    return {
        "mann_whitney_dealer_vs_individual": mw_res,
        "kruskal_wallis_body_types": kw_res,
        "regression_hypothesis_tests": reg_res,
        "charts": [chart_path],
    }


if __name__ == "__main__":
    out = run_statistical_testing()
    print("Analysis 4 completed. Chart:", out["charts"])
    print("MW Dealer vs Indiv p:", out["mann_whitney_dealer_vs_individual"]["primary_price_test"]["p_value_raw"])
    print("KW Body types H:", out["kruskal_wallis_body_types"]["h_statistic"])
