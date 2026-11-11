"""Analysis 2: Transmission x Body Type interaction analysis and log-price regression."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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


def summarize_body_type_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize all real_body_type x transmission_type counts and document inclusions/exclusions."""
    ct = pd.crosstab(df["real_body_type"], df["transmission_type"])
    for col in ["Automatic", "Manual"]:
        if col not in ct.columns:
            ct[col] = 0
    ct = ct[["Manual", "Automatic"]].copy()
    ct["Total"] = ct["Manual"] + ct["Automatic"]
    ct["Median_Price"] = df.groupby("real_body_type")["selling_price"].median()
    ct["Mean_Price"] = df.groupby("real_body_type")["selling_price"].mean()
    ct["Included_In_Main_Analysis"] = ct.index.isin(MAJOR_BODY_TYPES)

    def _reason(row: pd.Series) -> str:
        name = str(row.name)
        if name in MAJOR_BODY_TYPES:
            return "Included (major body type with both transmissions, n >= 84 per cell)"
        if name == "Unknown":
            return "Excluded: Unknown/missing body type label"
        if row["Manual"] == 0 or row["Automatic"] == 0:
            return "Excluded: Only one transmission type observed (no within-body comparison)"
        return "Excluded: Small sample size"

    ct["Status_Reason"] = ct.apply(_reason, axis=1)
    return ct.sort_values("Total", ascending=False).reset_index()


def compute_transmission_body_table(df_major: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute detailed cell stats and Automatic-vs-Manual premium table by body type."""
    cell_stats = (
        df_major.groupby(["real_body_type", "transmission_type"])
        .agg(
            count=("selling_price", "count"),
            median_price=("selling_price", "median"),
            mean_price=("selling_price", "mean"),
            std_price=("selling_price", "std"),
            p25_price=("selling_price", lambda s: s.quantile(0.25)),
            p75_price=("selling_price", lambda s: s.quantile(0.75)),
            median_age=("vehicle_age", "median"),
            median_engine=("engine", "median"),
        )
        .reset_index()
    )

    piv_med = cell_stats.pivot(index="real_body_type", columns="transmission_type", values="median_price")
    piv_mean = cell_stats.pivot(index="real_body_type", columns="transmission_type", values="mean_price")
    piv_cnt = cell_stats.pivot(index="real_body_type", columns="transmission_type", values="count")

    premium_rows = []
    for body in MAJOR_BODY_TYPES:
        man_med = float(piv_med.loc[body, "Manual"])
        auto_med = float(piv_med.loc[body, "Automatic"])
        man_mean = float(piv_mean.loc[body, "Manual"])
        auto_mean = float(piv_mean.loc[body, "Automatic"])
        man_n = int(piv_cnt.loc[body, "Manual"])
        auto_n = int(piv_cnt.loc[body, "Automatic"])
        diff_med = auto_med - man_med
        pct_prem = ((auto_med / man_med) - 1.0) * 100.0
        premium_rows.append(
            {
                "real_body_type": body,
                "manual_n": man_n,
                "automatic_n": auto_n,
                "total_n": man_n + auto_n,
                "manual_median_price": man_med,
                "automatic_median_price": auto_med,
                "manual_mean_price": man_mean,
                "automatic_mean_price": auto_mean,
                "median_diff_inr": diff_med,
                "median_pct_premium": pct_prem,
            }
        )

    premium_df = pd.DataFrame(premium_rows)
    return cell_stats, premium_df


def fit_interaction_regression(df_major: pd.DataFrame) -> dict[str, Any]:
    """Fit OLS on log(selling_price) with C(transmission_type) * C(real_body_type) and HC3 SEs."""
    work = df_major.copy()
    work["log_price"] = np.log(work["selling_price"])

    formula = (
        "log_price ~ vehicle_age + km_driven + engine "
        "+ C(transmission_type, Treatment(reference='Manual')) "
        "* C(real_body_type, Treatment(reference='Hatchback')) "
        "+ C(seller_type, Treatment(reference='Individual')) "
        "+ C(model_grouped)"
    )
    model = smf.ols(formula, data=work).fit(cov_type="HC3")

    trans_term = "C(transmission_type, Treatment(reference='Manual'))[T.Automatic]"
    body_prefix = "C(real_body_type, Treatment(reference='Hatchback'))"

    interaction_terms = [name for name in model.params.index if trans_term in name and ":" in name]
    # Joint Wald F-test for all interaction terms = 0
    if interaction_terms:
        r_matrix = np.zeros((len(interaction_terms), len(model.params)))
        param_names = list(model.params.index)
        for row_i, term in enumerate(interaction_terms):
            r_matrix[row_i, param_names.index(term)] = 1.0
        joint_test = model.f_test(r_matrix)
        joint_f = float(np.asarray(joint_test.fvalue).squeeze())
        joint_p = float(np.asarray(joint_test.pvalue).squeeze())
        joint_df_num = int(joint_test.df_num)
        joint_df_denom = int(joint_test.df_denom)
    else:
        joint_f, joint_p, joint_df_num, joint_df_denom = 0.0, 1.0, 0, 0

    # Key non-model-FE coefficients
    conf = model.conf_int()
    key_terms = {}
    for term in model.params.index:
        if "C(model_grouped)" in term:
            continue
        coef = float(model.params[term])
        se = float(model.bse[term])
        pval = float(model.pvalues[term])
        ci_low, ci_high = float(conf.loc[term, 0]), float(conf.loc[term, 1])
        key_terms[term] = {
            "coef": coef,
            "hc3_se": se,
            "t_stat": float(model.tvalues[term]),
            "p_value": pval,
            "ci95_low": ci_low,
            "ci95_high": ci_high,
            "pct_effect": float((np.exp(coef) - 1.0) * 100.0),
            "pct_ci95_low": float((np.exp(ci_low) - 1.0) * 100.0),
            "pct_ci95_high": float((np.exp(ci_high) - 1.0) * 100.0),
        }

    # Adjusted Automatic vs Manual effect inside each body type via linear contrast
    param_names = list(model.params.index)
    adjusted_premiums = []
    for body in MAJOR_BODY_TYPES:
        vec = np.zeros(len(param_names))
        vec[param_names.index(trans_term)] = 1.0
        if body != "Hatchback":
            inter_name = f"{trans_term}:{body_prefix}[T.{body}]"
            if inter_name in param_names:
                vec[param_names.index(inter_name)] = 1.0
        t_res = model.t_test(vec)
        est = float(np.asarray(t_res.effect).squeeze())
        se = float(np.asarray(t_res.sd).squeeze())
        pval = float(np.asarray(t_res.pvalue).squeeze())
        ci = t_res.conf_int()
        ci_l = float(np.asarray(ci[0, 0]).squeeze())
        ci_h = float(np.asarray(ci[0, 1]).squeeze())
        adjusted_premiums.append(
            {
                "real_body_type": body,
                "log_effect": est,
                "hc3_se": se,
                "p_value": pval,
                "adj_pct_premium": float((np.exp(est) - 1.0) * 100.0),
                "adj_pct_ci95_low": float((np.exp(ci_l) - 1.0) * 100.0),
                "adj_pct_ci95_high": float((np.exp(ci_h) - 1.0) * 100.0),
            }
        )

    return {
        "n_obs": int(model.nobs),
        "r2": float(model.rsquared),
        "adj_r2": float(model.rsquared_adj),
        "rmse_log": float(np.sqrt(np.mean(model.resid**2))),
        "joint_interaction_f_test": {
            "f_stat": joint_f,
            "df_num": joint_df_num,
            "df_denom": joint_df_denom,
            "p_value": joint_p,
        },
        "key_coefficients": key_terms,
        "adjusted_auto_premium_by_body": adjusted_premiums,
    }


def create_charts(
    premium_df: pd.DataFrame, reg_res: dict[str, Any]
) -> list[str]:
    """Generate the 2 required visualizations for Analysis 2."""
    configure_plot_style()
    saved = []

    # 5. transmission_body_price_comparison.png
    fig, ax = plt.subplots(figsize=(11.5, 6))
    x = np.arange(len(premium_df))
    width = 0.36
    bars_man = ax.bar(
        x - width / 2,
        premium_df["manual_median_price"],
        width=width,
        color=PALETTE["manual"],
        label="Manual",
    )
    bars_auto = ax.bar(
        x + width / 2,
        premium_df["automatic_median_price"],
        width=width,
        color=PALETTE["automatic"],
        label="Automatic",
    )

    for b, n_val, p_val in zip(
        bars_man, premium_df["manual_n"], premium_df["manual_median_price"]
    ):
        ax.text(
            b.get_x() + b.get_width() / 2,
            p_val + 25_000,
            f"₹{p_val/LAKH:.2f}L\n(n={n_val:,})",
            ha="center",
            va="bottom",
            fontsize=8.2,
        )
    for b, n_val, p_val, prem in zip(
        bars_auto,
        premium_df["automatic_n"],
        premium_df["automatic_median_price"],
        premium_df["median_pct_premium"],
    ):
        ax.text(
            b.get_x() + b.get_width() / 2,
            p_val + 25_000,
            f"₹{p_val/LAKH:.2f}L\n(n={n_val:,})\n[+{prem:.1f}%]",
            ha="center",
            va="bottom",
            fontsize=8.2,
            fontweight="bold",
            color="#8c2d19",
        )

    set_lakhs_axis(ax, "y")
    ax.set_xticks(x)
    ax.set_xticklabels(premium_df["real_body_type"], fontsize=10.5, fontweight="bold")
    ax.set_ylim(0, premium_df["automatic_median_price"].max() * 1.24)
    ax.set_title(
        "Median Listing Price by Transmission & Body Type (Excluding Unknown & Sparse Body Types)"
    )
    ax.set_xlabel("Body Type (Major Categories with Both Transmissions)")
    ax.set_ylabel("Median Listing Price (INR, Lakhs)")
    ax.legend(title="Transmission Type", loc="upper left")
    saved.append(str(save_chart(fig, "transmission_body_price_comparison.png")))

    # 6. transmission_body_interaction.png
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5))
    x_idx = np.arange(len(premium_df))

    axes[0].plot(
        x_idx,
        premium_df["manual_median_price"],
        marker="o",
        linewidth=2.4,
        color=PALETTE["manual"],
        label="Manual (Median)",
    )
    axes[0].plot(
        x_idx,
        premium_df["automatic_median_price"],
        marker="s",
        linewidth=2.4,
        color=PALETTE["automatic"],
        label="Automatic (Median)",
    )
    for i, row in premium_df.iterrows():
        axes[0].vlines(
            i,
            row["manual_median_price"],
            row["automatic_median_price"],
            colors=PALETTE["muted"],
            linestyles="dotted",
            linewidth=1.5,
        )
        mid_y = (row["manual_median_price"] + row["automatic_median_price"]) / 2
        y_text = row["automatic_median_price"] + 75_000 if i == 0 else mid_y
        x_text = i if i == 0 else i + 0.06
        ha_align = "center" if i == 0 else "left"
        axes[0].text(
            x_text,
            y_text,
            f"+₹{row['median_diff_inr']/LAKH:.2f}L\n(+{row['median_pct_premium']:.0f}%)",
            fontsize=8.3,
            color="#333333",
            ha=ha_align,
            va="center",
        )
    set_lakhs_axis(axes[0], "y")
    axes[0].set_xticks(x_idx)
    axes[0].set_xticklabels(premium_df["real_body_type"], fontweight="bold")
    axes[0].set_ylim(0, premium_df["automatic_median_price"].max() * 1.15)
    axes[0].set_title("Unadjusted Interaction: Median Price Gap by Body Type")
    axes[0].set_xlabel("Body Type")
    axes[0].set_ylabel("Median Listing Price (INR, Lakhs)")
    axes[0].legend(loc="upper left")

    # Right panel: Confounder-adjusted Automatic % premium with 95% HC3 CI
    adj_df = pd.DataFrame(reg_res["adjusted_auto_premium_by_body"])
    y_pos = np.arange(len(adj_df))
    est = adj_df["adj_pct_premium"].to_numpy()
    err_low = est - adj_df["adj_pct_ci95_low"].to_numpy()
    err_high = adj_df["adj_pct_ci95_high"].to_numpy() - est

    axes[1].errorbar(
        est,
        y_pos,
        xerr=[err_low, err_high],
        fmt="o",
        color=PALETTE["primary"],
        ecolor=PALETTE["secondary"],
        elinewidth=2.5,
        capsize=5,
        markersize=8,
    )
    axes[1].axvline(0, color=PALETTE["danger"], linestyle="--", linewidth=1.2)
    for y_i, row in adj_df.iterrows():
        axes[1].text(
            row["adj_pct_premium"],
            y_i + 0.16,
            f"+{row['adj_pct_premium']:.1f}% (95% CI: {row['adj_pct_ci95_low']:.1f}%–{row['adj_pct_ci95_high']:.1f}%)",
            ha="center",
            fontsize=8.5,
            color=PALETTE["primary"],
            fontweight="bold",
        )
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels(adj_df["real_body_type"], fontweight="bold")
    axes[1].set_ylim(-0.5, len(adj_df) - 0.3)
    axes[1].set_xlim(min(0, adj_df["adj_pct_ci95_low"].min() - 4), adj_df["adj_pct_ci95_high"].max() + 8)
    joint = reg_res["joint_interaction_f_test"]
    axes[1].set_title(
        f"Adjusted Automatic Premium (Controlling for Age, km, Engine, Seller, Model)\n"
        f"Joint Interaction F({joint['df_num']}, {joint['df_denom']}) = {joint['f_stat']:.2f}, p = {joint['p_value']:.2e}"
    )
    axes[1].set_xlabel("Adjusted Automatic vs. Manual Price Difference (%)")

    fig.suptitle("Transmission × Body Type Interaction Effects on Used-Car Listing Prices", y=1.03)
    saved.append(str(save_chart(fig, "transmission_body_interaction.png")))

    return saved


def run_transmission_body_analysis(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Execute full Analysis 2 pipeline and return structured metrics."""
    if df is None:
        df = load_dataset()

    coverage_df = summarize_body_type_coverage(df)
    df_major = df[df["real_body_type"].isin(MAJOR_BODY_TYPES)].copy()
    cell_stats, premium_df = compute_transmission_body_table(df_major)
    reg_res = fit_interaction_regression(df_major)
    charts = create_charts(premium_df, reg_res)

    return {
        "total_rows": int(len(df)),
        "major_body_types_rows": int(len(df_major)),
        "excluded_rows": int(len(df) - len(df_major)),
        "coverage_table": coverage_df.to_dict(orient="records"),
        "cell_stats": cell_stats.to_dict(orient="records"),
        "premium_table": premium_df.to_dict(orient="records"),
        "regression": reg_res,
        "charts": charts,
    }


if __name__ == "__main__":
    out = run_transmission_body_analysis()
    print("Analysis 2 completed. Charts:", out["charts"])
    print("Joint interaction test:", out["regression"]["joint_interaction_f_test"])
