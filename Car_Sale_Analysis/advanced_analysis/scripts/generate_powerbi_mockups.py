"""Generate four 1920x1080 high-fidelity Power BI Desktop dashboard mockup PNGs for the Used Car Market Intelligence project."""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

from common import LAKH, MAJOR_BODY_TYPES, PROJECT_ROOT, load_dataset

MOCKUP_DIR = PROJECT_ROOT / "outputs" / "dashboard_mockups"
ADV_OUT_DIR = PROJECT_ROOT / "outputs" / "advanced_analysis"

# Required Design System Palette
COLORS = {
    "primary": "#142B49",      # Dark Navy
    "secondary": "#245B86",    # Blue
    "accent": "#438EAD",       # Light Blue
    "bg": "#F4F6F9",           # Light Grey Canvas
    "card": "#FFFFFF",         # White Card
    "card_border": "#DCE2EA",  # Subtle Card Border
    "positive": "#2E8B57",     # Green
    "negative": "#E87524",     # Orange
    "text_dark": "#142B49",
    "text_muted": "#5C6F84",
    "grid": "#E9EEF4",
}

NAV_ITEMS = [
    "Home",
    "Market Overview",
    "Vehicle Analysis",
    "Seller & Pricing Insights",
]


def setup_segoe_style() -> None:
    """Configure Segoe UI typography and clean enterprise chart defaults."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
            "axes.edgecolor": "#D0D8E2",
            "axes.linewidth": 0.8,
            "grid.color": COLORS["grid"],
            "grid.linewidth": 0.7,
            "xtick.color": COLORS["text_muted"],
            "ytick.color": COLORS["text_muted"],
            "text.color": COLORS["text_dark"],
        }
    )


def create_base_canvas(
    active_page: str,
    main_title: str,
    subtitle: str,
    slicers: list[tuple[str, str]] | None = None,
) -> Figure:
    """Create a 1920x1080 (16:9) Power BI Desktop canvas with left sidebar, header, slicers, and footer."""
    setup_segoe_style()
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=COLORS["bg"])

    # 1. Left Navigation Sidebar (x: 0.0 -> 0.135)
    sidebar_w = 0.135
    sidebar = Rectangle(
        (0.0, 0.0),
        sidebar_w,
        1.0,
        facecolor=COLORS["primary"],
        edgecolor="none",
        transform=fig.transFigure,
        zorder=-5,
    )
    fig.patches.append(sidebar)

    # Automotive Brand Logo Box in Sidebar
    logo_box = FancyBboxPatch(
        (0.014, 0.905),
        0.107,
        0.068,
        boxstyle="round,pad=0.003,rounding_size=0.008",
        facecolor=COLORS["secondary"],
        edgecolor=COLORS["accent"],
        linewidth=1.2,
        transform=fig.transFigure,
        zorder=-3,
    )
    fig.patches.append(logo_box)

    # Simple stylized car silhouette icon inside logo box
    car_body = FancyBboxPatch(
        (0.024, 0.927),
        0.032,
        0.016,
        boxstyle="round,pad=0.001,rounding_size=0.004",
        facecolor=COLORS["accent"],
        edgecolor="white",
        linewidth=1.0,
        transform=fig.transFigure,
        zorder=-2,
    )
    fig.patches.append(car_body)
    fig.patches.append(Circle((0.031, 0.924), 0.0045, facecolor="white", transform=fig.transFigure, zorder=-1))
    fig.patches.append(Circle((0.049, 0.924), 0.0045, facecolor="white", transform=fig.transFigure, zorder=-1))

    fig.text(0.063, 0.948, "AUTO BI", color="white", fontsize=11.5, fontweight="bold", va="center", zorder=1)
    fig.text(0.063, 0.925, "Intelligence", color="#B8D4E8", fontsize=8.5, va="center", zorder=1)

    fig.text(
        0.016,
        0.865,
        "NAVIGATION",
        color="#7FA6C4",
        fontsize=8.0,
        fontweight="bold",
        va="center",
        zorder=1,
    )

    # Navigation Items
    nav_y_start = 0.805
    nav_step = 0.068
    for idx, item in enumerate(NAV_ITEMS):
        y_top = nav_y_start - idx * nav_step
        is_active = item == active_page
        bg_col = COLORS["secondary"] if is_active else COLORS["primary"]
        edge_col = COLORS["accent"] if is_active else "none"
        nav_pill = FancyBboxPatch(
            (0.010, y_top),
            sidebar_w - 0.020,
            0.052,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            facecolor=bg_col,
            edgecolor=edge_col,
            linewidth=1.1 if is_active else 0.0,
            transform=fig.transFigure,
            zorder=-3,
        )
        fig.patches.append(nav_pill)
        if is_active:
            accent_bar = Rectangle(
                (0.010, y_top + 0.006),
                0.0045,
                0.040,
                facecolor=COLORS["accent"],
                edgecolor="none",
                transform=fig.transFigure,
                zorder=-1,
            )
            fig.patches.append(accent_bar)
        txt_col = "#FFFFFF" if is_active else "#B0C4D8"
        weight = "bold" if is_active else "normal"
        fig.text(
            0.024,
            y_top + 0.026,
            f"{idx + 1}.  {item}",
            color=txt_col,
            fontsize=9.5,
            fontweight=weight,
            va="center",
            zorder=1,
        )

    # Sidebar bottom metadata panel
    meta_box = FancyBboxPatch(
        (0.012, 0.048),
        sidebar_w - 0.024,
        0.135,
        boxstyle="round,pad=0.002,rounding_size=0.006",
        facecolor="#0E2038",
        edgecolor="#24476E",
        linewidth=0.9,
        transform=fig.transFigure,
        zorder=-3,
    )
    fig.patches.append(meta_box)
    fig.text(0.020, 0.160, "DATASET SCOPE", color=COLORS["accent"], fontsize=7.8, fontweight="bold", zorder=1)
    fig.text(0.020, 0.133, "Source: final_destination.csv", color="#D0E0EE", fontsize=7.6, zorder=1)
    fig.text(0.020, 0.109, "Records: 15,229 Listings", color="#D0E0EE", fontsize=7.6, zorder=1)
    fig.text(0.020, 0.085, "Type: Cross-Sectional Ask", color="#D0E0EE", fontsize=7.6, zorder=1)
    fig.text(0.020, 0.061, "Status: Design Mockup", color=COLORS["negative"], fontsize=7.6, fontweight="bold", zorder=1)

    # 2. Top Header Banner (x: 0.148 -> 0.988, y: 0.902 -> 0.982)
    hdr_card = FancyBboxPatch(
        (0.148, 0.904),
        0.840,
        0.078,
        boxstyle="round,pad=0.002,rounding_size=0.007",
        facecolor=COLORS["card"],
        edgecolor=COLORS["card_border"],
        linewidth=1.1,
        transform=fig.transFigure,
        zorder=-4,
    )
    fig.patches.append(hdr_card)
    hdr_strip = Rectangle(
        (0.148, 0.904),
        0.005,
        0.078,
        facecolor=COLORS["primary"],
        edgecolor="none",
        transform=fig.transFigure,
        zorder=-3,
    )
    fig.patches.append(hdr_strip)

    fig.text(
        0.163,
        0.953,
        main_title,
        color=COLORS["primary"],
        fontsize=15.5,
        fontweight="bold",
        va="center",
        zorder=1,
    )
    fig.text(
        0.163,
        0.923,
        subtitle,
        color=COLORS["text_muted"],
        fontsize=9.8,
        va="center",
        zorder=1,
    )

    # Slicers inside right side of Header Bar (if provided)
    if slicers:
        n_s = len(slicers)
        s_w = 0.108
        s_gap = 0.008
        total_w = n_s * s_w + (n_s - 1) * s_gap
        start_x = 0.980 - total_w
        for i, (s_label, s_val) in enumerate(slicers):
            sx = start_x + i * (s_w + s_gap)
            sy = 0.916
            sh = 0.054
            s_box = FancyBboxPatch(
                (sx, sy),
                s_w,
                sh,
                boxstyle="round,pad=0.001,rounding_size=0.005",
                facecolor=COLORS["bg"],
                edgecolor="#C5D1DE",
                linewidth=0.9,
                transform=fig.transFigure,
                zorder=-2,
            )
            fig.patches.append(s_box)
            fig.text(sx + 0.007, sy + 0.038, f"SLICER: {s_label.upper()}", color=COLORS["text_muted"], fontsize=6.8, fontweight="bold", va="center", zorder=1)
            fig.text(sx + 0.007, sy + 0.016, s_val, color=COLORS["primary"], fontsize=8.3, fontweight="bold", va="center", zorder=1)
            fig.text(sx + s_w - 0.009, sy + 0.017, "▼", color=COLORS["secondary"], fontsize=7.5, va="center", ha="center", zorder=1)
    else:
        badge = FancyBboxPatch(
            (0.835, 0.922),
            0.142,
            0.042,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            facecolor=COLORS["bg"],
            edgecolor=COLORS["accent"],
            linewidth=1.0,
            transform=fig.transFigure,
            zorder=-2,
        )
        fig.patches.append(badge)
        fig.text(0.906, 0.943, "Power BI Desktop  |  16:9", color=COLORS["secondary"], fontsize=8.8, fontweight="bold", ha="center", va="center", zorder=1)

    # 3. Footer Bar (x: 0.148 -> 0.988, y: 0.010 -> 0.036)
    ftr = FancyBboxPatch(
        (0.148, 0.010),
        0.840,
        0.026,
        boxstyle="round,pad=0.001,rounding_size=0.004",
        facecolor=COLORS["card"],
        edgecolor=COLORS["card_border"],
        linewidth=0.8,
        transform=fig.transFigure,
        zorder=-4,
    )
    fig.patches.append(ftr)
    fig.text(
        0.158,
        0.023,
        "Used Car Market Intelligence Dashboard  •  University Data Analytics Project  •  Dataset: final_destination.csv (~15,229 listings)",
        color=COLORS["text_muted"],
        fontsize=8.0,
        va="center",
        zorder=1,
    )
    fig.text(
        0.978,
        0.023,
        f"Page: {active_page}  |  1920 × 1080 Design Mockup (Placeholder / Visual Reference)",
        color=COLORS["secondary"],
        fontsize=8.0,
        fontweight="bold",
        ha="right",
        va="center",
        zorder=1,
    )

    return fig


def add_kpi_row(
    fig: Figure,
    kpis: list[tuple[str, str, str, str]],
    y: float = 0.790,
    h: float = 0.098,
) -> None:
    """Render a row of 4 or 6 evenly spaced KPI cards across x=0.148..0.988."""
    n = len(kpis)
    total_w = 0.840
    gap = 0.010
    card_w = (total_w - gap * (n - 1)) / n
    start_x = 0.148

    for i, (label, value, subtext, strip_color) in enumerate(kpis):
        cx = start_x + i * (card_w + gap)
        card = FancyBboxPatch(
            (cx, y),
            card_w,
            h,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            facecolor=COLORS["card"],
            edgecolor=COLORS["card_border"],
            linewidth=1.0,
            transform=fig.transFigure,
            zorder=-3,
        )
        fig.patches.append(card)
        top_strip = Rectangle(
            (cx, y + h - 0.006),
            card_w,
            0.006,
            facecolor=strip_color,
            edgecolor="none",
            transform=fig.transFigure,
            zorder=-2,
        )
        fig.patches.append(top_strip)

        fig.text(
            cx + 0.010,
            y + h * 0.73,
            label.upper(),
            color=COLORS["text_muted"],
            fontsize=7.8 if n == 6 else 8.3,
            fontweight="bold",
            va="center",
            zorder=1,
        )
        fig.text(
            cx + 0.010,
            y + h * 0.41,
            value,
            color=COLORS["primary"],
            fontsize=14.5 if n == 6 else 16.5,
            fontweight="bold",
            va="center",
            zorder=1,
        )
        fig.text(
            cx + 0.010,
            y + h * 0.15,
            subtext,
            color=strip_color,
            fontsize=7.5 if n == 6 else 8.0,
            fontweight="bold",
            va="center",
            zorder=1,
        )


def add_visual_card(
    fig: Figure,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    pad_left: float = 0.038,
    pad_bottom: float = 0.042,
    pad_right: float = 0.016,
    pad_top: float = 0.052,
):
    """Draw a white Power BI visual container card and return an embedded Matplotlib Axes."""
    card = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.002,rounding_size=0.007",
        facecolor=COLORS["card"],
        edgecolor=COLORS["card_border"],
        linewidth=1.0,
        transform=fig.transFigure,
        zorder=-3,
    )
    fig.patches.append(card)
    fig.text(
        x + 0.012,
        y + h - 0.022,
        title,
        color=COLORS["primary"],
        fontsize=10.2,
        fontweight="bold",
        va="center",
        zorder=2,
    )
    if subtitle:
        fig.text(
            x + w - 0.012,
            y + h - 0.022,
            subtitle,
            color=COLORS["text_muted"],
            fontsize=8.0,
            ha="right",
            va="center",
            zorder=2,
        )
    ax = fig.add_axes(
        [x + pad_left, y + pad_bottom, w - pad_left - pad_right, h - pad_bottom - pad_top],
        zorder=5,
    )
    ax.set_facecolor(COLORS["card"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8.2)
    return ax


def style_donut(ax, labels: list[str], sizes: list[float], colors: list[str], center_text: str) -> None:
    """Render a clean Power BI donut chart with legend and center metric."""
    wedges, _ = ax.pie(
        sizes,
        colors=colors,
        startangle=140,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.8),
    )
    ax.text(0, 0, center_text, ha="center", va="center", fontsize=9.2, fontweight="bold", color=COLORS["primary"])
    total = sum(sizes)
    legend_labels = [f"{l}: {s / total * 100:.1f}% ({int(s):,})" for l, s in zip(labels, sizes)]
    ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(0.92, 0.5),
        frameon=False,
        fontsize=8.0,
    )
    ax.set_aspect("equal")


# ==============================================================================
# PAGE 1: HOME — EXECUTIVE OVERVIEW
# ==============================================================================
def build_page1_home(df: pd.DataFrame) -> Path:
    fig = create_base_canvas(
        active_page="Home",
        main_title="USED CAR MARKET INTELLIGENCE",
        subtitle="Executive Overview | Market Performance & Pricing Insights",
        slicers=None,
    )

    kpis = [
        ("Total Listings", f"{len(df):,}", "100% Market Sample", COLORS["primary"]),
        ("Median Listing Price", f"₹{df['selling_price'].median() / LAKH:.2f} L", "P25: ₹3.80L | P75: ₹8.20L", COLORS["secondary"]),
        ("Average Listing Price", f"₹{df['selling_price'].mean() / LAKH:.2f} L", "Right-Skewed Luxury Tail", COLORS["accent"]),
        ("Average Vehicle Age", f"{df['vehicle_age'].mean():.1f} Yrs", "Median Age: 6.0 Yrs", COLORS["secondary"]),
        ("Average Mileage", f"{df['km_driven'].mean():,.0f} km", "Median: 50,000 km", COLORS["accent"]),
        ("Total Vehicle Models", f"{df['model'].nunique()} Models", f"{df['model_grouped'].nunique()} Grouped Families", COLORS["positive"]),
    ]
    add_kpi_row(fig, kpis, y=0.790, h=0.098)

    # Row 1 Visuals (y: 0.435 -> 0.772)
    # 1. Listings by Body Type (Donut)
    ax1 = add_visual_card(
        fig, 0.148, 0.435, 0.272, 0.337,
        "Listings by Body Type", "Share of Total",
        pad_left=0.01, pad_right=0.11, pad_bottom=0.02, pad_top=0.045,
    )
    bt_counts = df["real_body_type"].value_counts()
    top_bt = ["Unknown", "Hatchback", "Sedan", "SUV", "MUV"]
    bt_vals = [float(bt_counts.get(k, 0)) for k in top_bt] + [float(bt_counts.drop(top_bt, errors="ignore").sum())]
    bt_lbls = ["Unknown", "Hatchback", "Sedan", "SUV", "MUV", "Other (6)"]
    bt_cols = ["#95A5B5", COLORS["primary"], COLORS["secondary"], COLORS["accent"], COLORS["positive"], COLORS["negative"]]
    style_donut(ax1, bt_lbls, bt_vals, bt_cols, "15.2K\nCars")

    # 2. Listings by Transmission (Donut)
    ax2 = add_visual_card(
        fig, 0.432, 0.435, 0.268, 0.337,
        "Listings by Transmission", "Manual vs Automatic",
        pad_left=0.01, pad_right=0.11, pad_bottom=0.02, pad_top=0.045,
    )
    tr_counts = df["transmission_type"].value_counts()
    style_donut(
        ax2,
        ["Manual", "Automatic"],
        [float(tr_counts["Manual"]), float(tr_counts["Automatic"])],
        [COLORS["primary"], COLORS["negative"]],
        "79.3%\nManual",
    )

    # 3. Top 10 Vehicle Models (Horizontal Bar)
    ax3 = add_visual_card(
        fig, 0.712, 0.435, 0.276, 0.337,
        "Top 10 Vehicle Models", "By Listing Count",
        pad_left=0.055, pad_right=0.025, pad_bottom=0.045, pad_top=0.050,
    )
    top10_m = df["model_grouped"].value_counts().head(10).iloc[::-1]
    y_pos = np.arange(len(top10_m))
    bars = ax3.barh(y_pos, top10_m.values, color=COLORS["secondary"], height=0.68)
    bars[-1].set_color(COLORS["primary"])
    bars[-2].set_color(COLORS["primary"])
    for bar in bars:
        w = bar.get_width()
        ax3.text(w + 12, bar.get_y() + bar.get_height() / 2, f"{int(w)}", va="center", fontsize=7.8, color=COLORS["primary"], fontweight="bold")
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(top10_m.index, fontsize=8.2)
    ax3.set_xlim(0, top10_m.max() * 1.18)
    ax3.grid(axis="x")
    ax3.set_xlabel("Listings", fontsize=8.2)

    # Row 2: Median Listing Price by Seller Type (Column Chart) + Executive Insights Card (y: 0.052 -> 0.418)
    ax4 = add_visual_card(
        fig, 0.148, 0.052, 0.415, 0.366,
        "Median Listing Price by Seller Type", "INR (Lakhs)",
        pad_left=0.048, pad_right=0.022, pad_bottom=0.052, pad_top=0.058,
    )
    sellers = ["Dealer", "Trustmark Dealer", "Individual"]
    s_meds = [df[df["seller_type"] == s]["selling_price"].median() / LAKH for s in sellers]
    s_counts = [len(df[df["seller_type"] == s]) for s in sellers]
    s_cols = [COLORS["primary"], COLORS["accent"], COLORS["secondary"]]
    xb = np.arange(len(sellers))
    cbars = ax4.bar(xb, s_meds, color=s_cols, width=0.46)
    for bar, med, cnt in zip(cbars, s_meds, s_counts):
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            med + 0.18,
            f"₹{med:.2f} L\n(n={cnt:,})",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color=COLORS["primary"],
        )
    ax4.set_xticks(xb)
    ax4.set_xticklabels(sellers, fontsize=9.2, fontweight="bold")
    ax4.set_ylim(0, 7.2)
    ax4.set_ylabel("Median Price (₹ Lakhs)", fontsize=8.8)
    ax4.grid(axis="y")

    # Executive Insights Panel (Right Bottom)
    ins_x, ins_y, ins_w, ins_h = 0.575, 0.052, 0.413, 0.366
    ins_card = FancyBboxPatch(
        (ins_x, ins_y),
        ins_w,
        ins_h,
        boxstyle="round,pad=0.002,rounding_size=0.007",
        facecolor=COLORS["card"],
        edgecolor=COLORS["card_border"],
        linewidth=1.0,
        transform=fig.transFigure,
        zorder=-3,
    )
    fig.patches.append(ins_card)
    fig.text(
        ins_x + 0.015,
        ins_y + ins_h - 0.026,
        "EXECUTIVE INSIGHTS — 10-SECOND MARKET TAKEAWAYS",
        color=COLORS["primary"],
        fontsize=10.5,
        fontweight="bold",
        va="center",
        zorder=2,
    )
    fig.text(
        ins_x + ins_w - 0.015,
        ins_y + ins_h - 0.026,
        "Key Highlights",
        color=COLORS["positive"],
        fontsize=8.5,
        fontweight="bold",
        ha="right",
        va="center",
        zorder=2,
    )

    insights = [
        (
            "1. Core Market Concentrates in 3–8 Year Mass-Market Vehicles",
            "Over 75% of supply sits between ₹3.5L and ₹9.0L (median ₹5.56L, age 6.0 yrs). High-volume hatchbacks and compact sedans (i20, Swift Dzire, Swift, Alto, Baleno) drive rapid inventory turnover.",
            COLORS["primary"],
        ),
        (
            "2. Automatic Vehicles Command a Strong Price Premium Across All Segments",
            "Although Manuals represent 79.3% of listings, Automatic vehicles (20.7%) list at substantially higher medians (+29% to +114% raw; +10% to +17% like-for-like across body styles).",
            COLORS["positive"],
        ),
        (
            "3. Dealer Channel Leads Supply (62.0%) With a +15.7% Higher Median Ask",
            "Dealers list at ₹5.90L vs. ₹5.10L for Individual sellers (+₹80,000), driven by 2.7× higher Automatic share (27.1% vs 10.1%) and a +5.7% controlled showroom premium.",
            COLORS["negative"],
        ),
    ]
    for idx, (head, body, col) in enumerate(insights):
        by = ins_y + 0.225 - idx * 0.102
        pill = FancyBboxPatch(
            (ins_x + 0.014, by),
            ins_w - 0.028,
            0.088,
            boxstyle="round,pad=0.002,rounding_size=0.005",
            facecolor=COLORS["bg"],
            edgecolor="#D5E0EC",
            linewidth=0.9,
            transform=fig.transFigure,
            zorder=-2,
        )
        fig.patches.append(pill)
        bar_left = Rectangle(
            (ins_x + 0.014, by),
            0.0045,
            0.088,
            facecolor=col,
            edgecolor="none",
            transform=fig.transFigure,
            zorder=-1,
        )
        fig.patches.append(bar_left)
        fig.text(ins_x + 0.026, by + 0.064, head, color=COLORS["primary"], fontsize=8.8, fontweight="bold", va="center", zorder=2)
        fig.text(
            ins_x + 0.026,
            by + 0.028,
            textwrap.fill(body, width=78),
            color=COLORS["text_muted"],
            fontsize=7.8,
            va="center",
            zorder=2,
        )

    MOCKUP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = MOCKUP_DIR / "dashboard_home.png"
    fig.savefig(out_path, dpi=100, facecolor=COLORS["bg"])
    plt.close(fig)
    return out_path


# ==============================================================================
# PAGE 2: MARKET OVERVIEW
# ==============================================================================
def build_page2_market_overview(df: pd.DataFrame) -> Path:
    fig = create_base_canvas(
        active_page="Market Overview",
        main_title="USED CAR MARKET OVERVIEW",
        subtitle="Understanding Market Composition and Pricing Distribution",
        slicers=[
            ("Vehicle Model", "All Models (120)"),
            ("Body Type", "All Types"),
            ("Transmission", "All (Manual/Auto)"),
            ("Seller Type", "All Sellers"),
        ],
    )

    kpis = [
        ("Total Listings", f"{len(df):,}", "Active Marketplace Inventory", COLORS["primary"]),
        ("Median Listing Price", f"₹{df['selling_price'].median() / LAKH:.2f} L", "Mean Price: ₹7.75 L", COLORS["secondary"]),
        ("Most Common Body Type", "Hatchback (3,601)", "36.3% of Known Body Types", COLORS["accent"]),
        ("Most Listed Vehicle Model", "Hyundai i20 (898)", "5.90% of Total Market Share", COLORS["positive"]),
    ]
    add_kpi_row(fig, kpis, y=0.790, h=0.098)

    # 3x2 Grid of 6 Visualizations
    col_w = (0.840 - 2 * 0.012) / 3
    x_cols = [0.148 + i * (col_w + 0.012) for i in range(3)]
    row1_y, row1_h = 0.428, 0.345
    row2_y, row2_h = 0.052, 0.358

    # 1. Top 10 Vehicle Models by Listings (Horizontal Bar)
    ax1 = add_visual_card(
        fig, x_cols[0], row1_y, col_w, row1_h,
        "1. Top 10 Vehicle Models by Listings", "Volume Leaders",
        pad_left=0.052, pad_right=0.022, pad_bottom=0.045, pad_top=0.050,
    )
    top10 = df["model_grouped"].value_counts().head(10).iloc[::-1]
    y1 = np.arange(len(top10))
    b1 = ax1.barh(y1, top10.values, color=COLORS["secondary"], height=0.68)
    b1[-1].set_color(COLORS["primary"])
    for bar in b1:
        w = bar.get_width()
        ax1.text(w + 12, bar.get_y() + bar.get_height() / 2, f"{int(w)}", va="center", fontsize=7.6, fontweight="bold")
    ax1.set_yticks(y1)
    ax1.set_yticklabels(top10.index, fontsize=8.0)
    ax1.set_xlim(0, top10.max() * 1.18)
    ax1.grid(axis="x")
    ax1.set_xlabel("Listings", fontsize=8.0)

    # 2. Median Price by Body Type (Column Chart)
    ax2 = add_visual_card(
        fig, x_cols[1], row1_y, col_w, row1_h,
        "2. Median Price by Body Type", "Major Segments (₹L)",
        pad_left=0.042, pad_right=0.015, pad_bottom=0.048, pad_top=0.052,
    )
    bt_order = ["Hatchback", "Unknown", "Sedan", "SUV", "MUV"]
    bt_meds = [df[df["real_body_type"] == b]["selling_price"].median() / LAKH for b in bt_order]
    bt_cols = [COLORS["secondary"], "#95A5B5", COLORS["secondary"], COLORS["primary"], COLORS["positive"]]
    x2 = np.arange(len(bt_order))
    b2 = ax2.bar(x2, bt_meds, color=bt_cols, width=0.55)
    for bar, v in zip(b2, bt_meds):
        ax2.text(bar.get_x() + bar.get_width() / 2, v + 0.25, f"₹{v:.2f}L", ha="center", va="bottom", fontsize=7.8, fontweight="bold")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(bt_order, fontsize=8.0)
    ax2.set_ylim(0, 12.6)
    ax2.set_ylabel("Median Price (₹L)", fontsize=8.0)
    ax2.grid(axis="y")

    # 3. Listings by Transmission (Donut)
    ax3 = add_visual_card(
        fig, x_cols[2], row1_y, col_w, row1_h,
        "3. Listings by Transmission", "Gearbox Split",
        pad_left=0.01, pad_right=0.11, pad_bottom=0.02, pad_top=0.045,
    )
    tr_c = df["transmission_type"].value_counts()
    style_donut(
        ax3,
        ["Manual", "Automatic"],
        [float(tr_c["Manual"]), float(tr_c["Automatic"])],
        [COLORS["primary"], COLORS["negative"]],
        "20.7%\nAuto",
    )

    # 4. Listings by Seller Type (Donut)
    ax4 = add_visual_card(
        fig, x_cols[0], row2_y, col_w, row2_h,
        "4. Listings by Seller Type", "Channel Split",
        pad_left=0.01, pad_right=0.11, pad_bottom=0.02, pad_top=0.045,
    )
    sl_c = df["seller_type"].value_counts()
    style_donut(
        ax4,
        ["Dealer", "Individual", "Trustmark"],
        [float(sl_c["Dealer"]), float(sl_c["Individual"]), float(sl_c["Trustmark Dealer"])],
        [COLORS["primary"], COLORS["secondary"], COLORS["positive"]],
        "62.0%\nDealer",
    )

    # 5. Median Listing Price by Vehicle Model (Bar Chart — Top 10 popular models)
    ax5 = add_visual_card(
        fig, x_cols[1], row2_y, col_w, row2_h,
        "5. Median Price by Vehicle Model", "Top 10 Volume Models (₹L)",
        pad_left=0.052, pad_right=0.022, pad_bottom=0.048, pad_top=0.050,
    )
    top10_names = df["model_grouped"].value_counts().head(10).index.tolist()
    m_meds = (
        df[df["model_grouped"].isin(top10_names)]
        .groupby("model_grouped")["selling_price"]
        .median()
        .div(LAKH)
        .sort_values()
    )
    y5 = np.arange(len(m_meds))
    b5 = ax5.barh(y5, m_meds.values, color=COLORS["accent"], height=0.68)
    b5[-1].set_color(COLORS["primary"])
    b5[-2].set_color(COLORS["primary"])
    for bar, v in zip(b5, m_meds.values):
        ax5.text(v + 0.2, bar.get_y() + bar.get_height() / 2, f"₹{v:.2f}L", va="center", fontsize=7.6, fontweight="bold")
    ax5.set_yticks(y5)
    ax5.set_yticklabels(m_meds.index, fontsize=8.0)
    ax5.set_xlim(0, m_meds.max() * 1.22)
    ax5.grid(axis="x")
    ax5.set_xlabel("Median Listing Price (₹L)", fontsize=8.0)

    # 6. Vehicle Age Distribution (Column Chart)
    ax6 = add_visual_card(
        fig, x_cols[2], row2_y, col_w, row2_h,
        "6. Vehicle Age Distribution", "Listings by Age (0–20+ Yrs)",
        pad_left=0.044, pad_right=0.015, pad_bottom=0.048, pad_top=0.050,
    )
    age_c = df["vehicle_age"].value_counts().sort_index()
    ages_plot = list(range(1, 16))
    vals_plot = [int(age_c.get(a, 0)) for a in ages_plot]
    c_age = [COLORS["primary"] if a in (3, 4, 5, 6) else COLORS["secondary"] for a in ages_plot]
    ax6.bar(ages_plot, vals_plot, color=c_age, width=0.72)
    ax6.set_xticks(range(1, 16, 2))
    ax6.set_xlabel("Vehicle Age (Years)", fontsize=8.0)
    ax6.set_ylabel("Listings", fontsize=8.0)
    ax6.grid(axis="y")
    ax6.text(
        0.96, 0.88,
        "Peak Supply: Age 4 (2,216)\nAges 16–29: n=64 (<30/age)",
        transform=ax6.transAxes,
        ha="right", va="top",
        fontsize=7.6,
        bbox=dict(boxstyle="round,pad=0.3", facecolor=COLORS["bg"], edgecolor=COLORS["card_border"]),
    )

    out_path = MOCKUP_DIR / "dashboard_market_overview.png"
    fig.savefig(out_path, dpi=100, facecolor=COLORS["bg"])
    plt.close(fig)
    return out_path


# ==============================================================================
# PAGE 3: VEHICLE ANALYSIS
# ==============================================================================
def build_page3_vehicle_analysis(df: pd.DataFrame) -> Path:
    fig = create_base_canvas(
        active_page="Vehicle Analysis",
        main_title="VEHICLE ANALYSIS & PRICE INTELLIGENCE",
        subtitle="Understanding How Vehicle Characteristics Relate to Listing Prices",
        slicers=[
            ("Vehicle Age", "Ages 1–15 (Reliable)"),
            ("Model", "All Models"),
            ("Transmission", "All Gearboxes"),
            ("Body Type", "All Body Types"),
        ],
    )

    kpis = [
        ("Average Vehicle Age", f"{df['vehicle_age'].mean():.2f} Yrs", "Median Age: 6.0 Yrs (IQR 4–8)", COLORS["primary"]),
        ("Median Listing Price", f"₹{df['selling_price'].median() / LAKH:.2f} L", "-10.6% / Yr Controlled Slope", COLORS["secondary"]),
        ("Average Mileage", f"{df['km_driven'].mean():,.0f} km", "Median: 50,000 km", COLORS["accent"]),
        ("Highest Median Price Body Type", "MUV (₹10.78 L)", "Followed by SUV (₹8.80 L)", COLORS["positive"]),
    ]
    add_kpi_row(fig, kpis, y=0.790, h=0.098)

    row1_y, row1_h = 0.428, 0.345
    row2_y, row2_h = 0.052, 0.358

    # Top Row: Chart 1 (Line) + Chart 2 (Diverging YoY) + Dedicated AGE 25 ANOMALY CARD + Chart 4 (Engine)
    # Wait: We have 6 visualizations + 1 dedicated Anomaly Card! Let's arrange:
    # Top row: [1. Price by Age Line (w=0.26)] [2. YoY Price Change % (w=0.25)] [AGE 25 ANOMALY CARD (w=0.145)] [4. Price by Engine Capacity (w=0.155)]
    # Bottom row: [3. Mileage vs Listing Price Scatter (w=0.272)] [5. Transmission x Body Type (w=0.272)] [6. Vehicle Age vs Mileage Scatter (w=0.272)]

    # 1. Median Listing Price by Vehicle Age (Line Chart)
    ax1 = add_visual_card(
        fig, 0.148, row1_y, 0.255, row1_h,
        "1. Median Price by Vehicle Age", "Ages 1–15 Curve (₹L)",
        pad_left=0.040, pad_right=0.014, pad_bottom=0.048, pad_top=0.052,
    )
    age_med = df[df["vehicle_age"].between(1, 15)].groupby("vehicle_age")["selling_price"].median() / LAKH
    ax1.plot(age_med.index, age_med.values, marker="o", markersize=4.5, linewidth=2.2, color=COLORS["primary"])
    ax1.axvspan(6, 9, color=COLORS["accent"], alpha=0.15, label="Ages 6–9 Plateau")
    ax1.set_xlabel("Vehicle Age (Yrs)", fontsize=8.0)
    ax1.set_ylabel("Median Price (₹L)", fontsize=8.0)
    ax1.set_xticks(range(1, 16, 2))
    ax1.grid(True)
    ax1.legend(loc="upper right", fontsize=7.5)

    # 2. Year-over-Year Price Change (%) — Diverging Column Chart
    ax2 = add_visual_card(
        fig, 0.413, row1_y, 0.245, row1_h,
        "2. YoY Median Price Change (%)", "Green (+) vs Orange (-)",
        pad_left=0.042, pad_right=0.012, pad_bottom=0.048, pad_top=0.052,
    )
    yoy = age_med.pct_change() * 100.0
    yoy = yoy.dropna()
    yoy_cols = [COLORS["positive"] if v >= 0 else COLORS["negative"] for v in yoy.values]
    ax2.bar(yoy.index, yoy.values, color=yoy_cols, width=0.68)
    ax2.axhline(0, color=COLORS["primary"], linewidth=0.9)
    ax2.set_xticks(range(2, 16, 2))
    ax2.set_ylim(-30, 15)
    ax2.set_xlabel("Vehicle Age (Yrs)", fontsize=8.0)
    ax2.set_ylabel("YoY Change (%)", fontsize=8.0)
    ax2.grid(axis="y")

    # Dedicated Anomaly Insight Card: AGE 25 PRICE ANOMALY
    anom_x, anom_y, anom_w, anom_h = 0.668, row1_y, 0.146, row1_h
    anom_card = FancyBboxPatch(
        (anom_x, anom_y),
        anom_w,
        anom_h,
        boxstyle="round,pad=0.002,rounding_size=0.007",
        facecolor="#FFF9F5",
        edgecolor=COLORS["negative"],
        linewidth=1.5,
        transform=fig.transFigure,
        zorder=-3,
    )
    fig.patches.append(anom_card)
    anom_hdr = FancyBboxPatch(
        (anom_x, anom_y + anom_h - 0.046),
        anom_w,
        0.046,
        boxstyle="round,pad=0.002,rounding_size=0.006",
        facecolor=COLORS["negative"],
        edgecolor="none",
        transform=fig.transFigure,
        zorder=-2,
    )
    fig.patches.append(anom_hdr)
    fig.text(
        anom_x + anom_w / 2,
        anom_y + anom_h - 0.023,
        "[!] AGE 25 PRICE ANOMALY",
        color="white",
        fontsize=8.5,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=2,
    )
    anom_items = [
        ("UNUSUAL PRICE SPIKE", "Median jumps to ₹10.00L at Age 25 vs. ₹0.60L–₹0.85L at ages 21–29."),
        ("SAMPLE SIZE WARNING", "n = 1 listing at Age 25 (below n >= 30 threshold). Single car drives spike."),
        ("INVESTIGATION STATUS", "Flagged in audit log; isolated from primary curve via n >= 30 filter."),
    ]
    for idx, (h_txt, b_txt) in enumerate(anom_items):
        iy = anom_y + 0.205 - idx * 0.095
        fig.text(anom_x + 0.008, iy + 0.062, f"• {h_txt}", color=COLORS["negative"], fontsize=7.4, fontweight="bold", zorder=2)
        fig.text(
            anom_x + 0.008,
            iy + 0.026,
            textwrap.fill(b_txt, width=30),
            color=COLORS["primary"],
            fontsize=7.1,
            va="center",
            zorder=2,
        )

    # 4. Median Price by Engine Capacity (Column Chart)
    ax4 = add_visual_card(
        fig, 0.824, row1_y, 0.164, row1_h,
        "4. Price by Engine Size", "Median (₹L)",
        pad_left=0.036, pad_right=0.010, pad_bottom=0.052, pad_top=0.052,
    )
    eng_bins = [0, 1000, 1250, 1550, 2050, 10000]
    eng_lbls = ["≤1.0L", "1.0–1.2L", "1.2–1.5L", "1.5–2.0L", ">2.0L"]
    eng_meds = (
        df.groupby(pd.cut(df["engine"], bins=eng_bins, labels=eng_lbls), observed=False)["selling_price"]
        .median()
        .div(LAKH)
    )
    x4 = np.arange(len(eng_lbls))
    ax4.bar(x4, eng_meds.values, color=[COLORS["accent"], COLORS["secondary"], COLORS["secondary"], COLORS["primary"], COLORS["primary"]], width=0.58)
    ax4.set_xticks(x4)
    ax4.set_xticklabels(eng_lbls, fontsize=6.8, rotation=18)
    ax4.set_ylabel("₹ Lakhs", fontsize=7.5)
    ax4.grid(axis="y")

    # Bottom Row: 3 equal cards (3. Mileage vs Price Scatter, 5. Transmission x Body Type, 6. Age vs Mileage Scatter)
    col_w = (0.840 - 2 * 0.012) / 3
    x_cols = [0.148 + i * (col_w + 0.012) for i in range(3)]

    # 3. Mileage vs Listing Price (Scatter Plot)
    ax3 = add_visual_card(
        fig, x_cols[0], row2_y, col_w, row2_h,
        "3. Mileage vs Listing Price", "Sampled Listings (Log Scale)",
        pad_left=0.044, pad_right=0.015, pad_bottom=0.048, pad_top=0.050,
    )
    samp = df[(df["km_driven"] <= 200_000) & (df["selling_price"] <= 50 * LAKH)].sample(1200, random_state=42)
    man_s = samp[samp["transmission_type"] == "Manual"]
    aut_s = samp[samp["transmission_type"] == "Automatic"]
    ax3.scatter(man_s["km_driven"] / 1000, man_s["selling_price"] / LAKH, s=10, alpha=0.35, color=COLORS["secondary"], label="Manual")
    ax3.scatter(aut_s["km_driven"] / 1000, aut_s["selling_price"] / LAKH, s=12, alpha=0.45, color=COLORS["negative"], label="Automatic")
    ax3.set_xlabel("Mileage (Thousand km)", fontsize=8.0)
    ax3.set_ylabel("Listing Price (₹L)", fontsize=8.0)
    ax3.legend(loc="upper right", fontsize=7.5)
    ax3.grid(True)

    # 5. Transmission x Body Type Price Comparison (Clustered Column Chart)
    ax5 = add_visual_card(
        fig, x_cols[1], row2_y, col_w, row2_h,
        "5. Transmission × Body Type Price", "Manual vs Automatic Median (₹L)",
        pad_left=0.042, pad_right=0.015, pad_bottom=0.048, pad_top=0.050,
    )
    sub_b = df[df["real_body_type"].isin(MAJOR_BODY_TYPES)]
    piv = sub_b.groupby(["real_body_type", "transmission_type"])["selling_price"].median().unstack().loc[MAJOR_BODY_TYPES] / LAKH
    x5 = np.arange(len(MAJOR_BODY_TYPES))
    w5 = 0.36
    ax5.bar(x5 - w5 / 2, piv["Manual"], width=w5, color=COLORS["primary"], label="Manual")
    ax5.bar(x5 + w5 / 2, piv["Automatic"], width=w5, color=COLORS["negative"], label="Automatic")
    ax5.set_xticks(x5)
    ax5.set_xticklabels(MAJOR_BODY_TYPES, fontsize=8.2)
    ax5.set_ylabel("Median Price (₹L)", fontsize=8.0)
    ax5.legend(loc="upper left", fontsize=7.8)
    ax5.grid(axis="y")

    # 6. Vehicle Age vs Mileage (Scatter Plot + Median Trend)
    ax6 = add_visual_card(
        fig, x_cols[2], row2_y, col_w, row2_h,
        "6. Vehicle Age vs Mileage", "Odometer Accumulation by Age",
        pad_left=0.044, pad_right=0.015, pad_bottom=0.048, pad_top=0.050,
    )
    ax6.scatter(samp["vehicle_age"], samp["km_driven"] / 1000, s=10, alpha=0.25, color=COLORS["accent"], label="Listings")
    med_km = df[df["vehicle_age"].between(1, 15)].groupby("vehicle_age")["km_driven"].median() / 1000
    ax6.plot(med_km.index, med_km.values, color=COLORS["primary"], marker="o", markersize=4, linewidth=2.0, label="Median km")
    ax6.set_xlabel("Vehicle Age (Years)", fontsize=8.0)
    ax6.set_ylabel("Mileage (Thousand km)", fontsize=8.0)
    ax6.set_xlim(0, 16)
    ax6.legend(loc="upper left", fontsize=7.5)
    ax6.grid(True)

    out_path = MOCKUP_DIR / "dashboard_vehicle_analysis.png"
    fig.savefig(out_path, dpi=100, facecolor=COLORS["bg"])
    plt.close(fig)
    return out_path


# ==============================================================================
# PAGE 4: SELLER & PRICING INSIGHTS
# ==============================================================================
def build_page4_seller_insights(df: pd.DataFrame) -> Path:
    fig = create_base_canvas(
        active_page="Seller & Pricing Insights",
        main_title="SELLER & PRICING INTELLIGENCE",
        subtitle="Comparing Dealer and Individual Seller Behavior",
        slicers=[
            ("Seller Type", "All Channels"),
            ("Vehicle Model", "All Models"),
            ("Body Type", "All Body Types"),
            ("Transmission", "All Gearboxes"),
        ],
    )

    d_df = df[df["seller_type"] == "Dealer"]
    i_df = df[df["seller_type"] == "Individual"]

    kpis = [
        ("Dealer Listings", f"{len(d_df):,}", "62.0% of Total Supply", COLORS["primary"]),
        ("Individual Listings", f"{len(i_df):,}", "36.8% of Total Supply", COLORS["secondary"]),
        ("Dealer Median Price", f"₹{d_df['selling_price'].median() / LAKH:.2f} L", "+15.7% Raw | +5.7% Controlled", COLORS["positive"]),
        ("Individual Median Price", f"₹{i_df['selling_price'].median() / LAKH:.2f} L", "P25: ₹3.50L | P75: ₹7.30L", COLORS["negative"]),
    ]
    add_kpi_row(fig, kpis, y=0.790, h=0.098)

    row1_y, row1_h = 0.428, 0.345
    row2_y, row2_h = 0.052, 0.358

    sellers = ["Dealer", "Individual", "Trustmark Dealer"]
    s_short = ["Dealer", "Individual", "Trustmark"]
    s_cols = [COLORS["primary"], COLORS["secondary"], COLORS["accent"]]

    # Top Row: [1. Median Price Bar] [2. Avg Age Column] [3. Median Mileage Column] [Comparison Section Card]
    # 1. Median Price by Seller Type (Bar Chart)
    ax1 = add_visual_card(
        fig, 0.148, row1_y, 0.205, row1_h,
        "1. Median Price by Seller", "INR (Lakhs)",
        pad_left=0.050, pad_right=0.022, pad_bottom=0.048, pad_top=0.052,
    )
    med_p = [df[df["seller_type"] == s]["selling_price"].median() / LAKH for s in sellers]
    y1 = np.arange(len(s_short))
    b1 = ax1.barh(y1, med_p, color=s_cols, height=0.55)
    for bar, v in zip(b1, med_p):
        ax1.text(v + 0.12, bar.get_y() + bar.get_height() / 2, f"₹{v:.2f}L", va="center", fontsize=8.0, fontweight="bold")
    ax1.set_yticks(y1)
    ax1.set_yticklabels(s_short, fontsize=8.2)
    ax1.set_xlim(0, 7.2)
    ax1.set_xlabel("Median Price (₹L)", fontsize=8.0)
    ax1.grid(axis="x")

    # 2. Average Vehicle Age by Seller Type (Column Chart)
    ax2 = add_visual_card(
        fig, 0.363, row1_y, 0.195, row1_h,
        "2. Avg Vehicle Age", "Years by Seller",
        pad_left=0.040, pad_right=0.012, pad_bottom=0.048, pad_top=0.052,
    )
    avg_a = [df[df["seller_type"] == s]["vehicle_age"].mean() for s in sellers]
    x2 = np.arange(len(s_short))
    b2 = ax2.bar(x2, avg_a, color=s_cols, width=0.52)
    for bar, v in zip(b2, avg_a):
        ax2.text(bar.get_x() + bar.get_width() / 2, v + 0.15, f"{v:.2f}y", ha="center", va="bottom", fontsize=8.0, fontweight="bold")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(s_short, fontsize=8.0)
    ax2.set_ylim(0, 7.5)
    ax2.set_ylabel("Avg Age (Yrs)", fontsize=8.0)
    ax2.grid(axis="y")

    # 3. Median Mileage by Seller Type (Column Chart)
    ax3 = add_visual_card(
        fig, 0.568, row1_y, 0.195, row1_h,
        "3. Median Mileage", "Km Driven by Seller",
        pad_left=0.042, pad_right=0.012, pad_bottom=0.048, pad_top=0.052,
    )
    med_k = [df[df["seller_type"] == s]["km_driven"].median() / 1000 for s in sellers]
    b3 = ax3.bar(x2, med_k, color=s_cols, width=0.52)
    for bar, v in zip(b3, med_k):
        ax3.text(bar.get_x() + bar.get_width() / 2, v + 1.2, f"{v:.1f}k", ha="center", va="bottom", fontsize=8.0, fontweight="bold")
    ax3.set_xticks(x2)
    ax3.set_xticklabels(s_short, fontsize=8.0)
    ax3.set_ylim(0, 62)
    ax3.set_ylabel("Median Km (Thousands)", fontsize=8.0)
    ax3.grid(axis="y")

    # Dedicated Comparison Section Card (Dealer vs Individual)
    cmp_x, cmp_y, cmp_w, cmp_h = 0.773, row1_y, 0.215, row1_h
    cmp_card = FancyBboxPatch(
        (cmp_x, cmp_y),
        cmp_w,
        cmp_h,
        boxstyle="round,pad=0.002,rounding_size=0.007",
        facecolor=COLORS["card"],
        edgecolor=COLORS["primary"],
        linewidth=1.3,
        transform=fig.transFigure,
        zorder=-3,
    )
    fig.patches.append(cmp_card)
    cmp_hdr = FancyBboxPatch(
        (cmp_x, cmp_y + cmp_h - 0.046),
        cmp_w,
        0.046,
        boxstyle="round,pad=0.002,rounding_size=0.006",
        facecolor=COLORS["primary"],
        edgecolor="none",
        transform=fig.transFigure,
        zorder=-2,
    )
    fig.patches.append(cmp_hdr)
    fig.text(
        cmp_x + cmp_w / 2,
        cmp_y + cmp_h - 0.023,
        "DEALER VS. INDIVIDUAL SUMMARY",
        color="white",
        fontsize=8.8,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=2,
    )
    cmp_notes = [
        ("PRICE DIFFERENCES", "Dealer median (₹5.90L) is +15.69% (+₹80k) above Individual (₹5.10L). Controlled gap is +5.66%.", COLORS["positive"]),
        ("INVENTORY AGE PROFILE", "Dealers hold slightly older stock (6.15y avg / 6.0y med) vs. Individuals (5.92y avg / 5.0y med).", COLORS["secondary"]),
        ("MILEAGE DIFFERENCES", "Identical 50,000 km median, but Individuals show a heavier high-mileage tail (59.7k vs 52.5k avg).", COLORS["negative"]),
    ]
    for idx, (h_t, b_t, c_col) in enumerate(cmp_notes):
        cy = cmp_y + 0.205 - idx * 0.095
        fig.text(cmp_x + 0.010, cy + 0.062, f"▪ {h_t}", color=c_col, fontsize=7.5, fontweight="bold", zorder=2)
        fig.text(
            cmp_x + 0.010,
            cy + 0.026,
            textwrap.fill(b_t, width=44),
            color=COLORS["text_dark"],
            fontsize=7.2,
            va="center",
            zorder=2,
        )

    # Bottom Row: 3 equal charts (4. Box Plot, 5. Seller by Body Type Stacked, 6. Seller by Transmission Stacked)
    col_w = (0.840 - 2 * 0.012) / 3
    x_cols = [0.148 + i * (col_w + 0.012) for i in range(3)]

    # 4. Listing Price Distribution by Seller Type (Box Plot)
    ax4 = add_visual_card(
        fig, x_cols[0], row2_y, col_w, row2_h,
        "4. Price Distribution by Seller", "Box Plot (Log10 Scale, ₹L)",
        pad_left=0.044, pad_right=0.015, pad_bottom=0.048, pad_top=0.050,
    )
    data_bp = [np.log10(df[df["seller_type"] == s]["selling_price"] / LAKH) for s in sellers]
    bp = ax4.boxplot(data_bp, patch_artist=True, tick_labels=s_short, widths=0.45, showfliers=False)
    for patch, col in zip(bp["boxes"], s_cols):
        patch.set_facecolor(col)
        patch.set_alpha(0.85)
    for median in bp["medians"]:
        median.set_color("white")
        median.set_linewidth(2.0)
    ax4.set_yticks([0, 0.477, 0.699, 1.0, 1.301])
    ax4.set_yticklabels(["₹1L", "₹3L", "₹5L", "₹10L", "₹20L"], fontsize=7.8)
    ax4.set_ylabel("Listing Price (Log Scale)", fontsize=8.0)
    ax4.grid(axis="y")

    # 5. Seller Type by Body Type (Stacked Bar Chart)
    ax5 = add_visual_card(
        fig, x_cols[1], row2_y, col_w, row2_h,
        "5. Seller Type by Body Type", "100% Stacked Channel Share",
        pad_left=0.048, pad_right=0.015, pad_bottom=0.048, pad_top=0.050,
    )
    ct_body = (
        pd.crosstab(df[df["real_body_type"].isin(MAJOR_BODY_TYPES)]["real_body_type"], df["seller_type"], normalize="index")
        .loc[MAJOR_BODY_TYPES]
        * 100.0
    )
    y5 = np.arange(len(MAJOR_BODY_TYPES))
    left5 = np.zeros(len(MAJOR_BODY_TYPES))
    for s_name, s_lbl, col in zip(sellers, s_short, s_cols):
        vals = ct_body[s_name].values
        ax5.barh(y5, vals, left=left5, color=col, height=0.58, label=s_lbl)
        left5 += vals
    ax5.set_yticks(y5)
    ax5.set_yticklabels(MAJOR_BODY_TYPES, fontsize=8.2)
    ax5.set_xlim(0, 100)
    ax5.set_xlabel("Share of Listings (%)", fontsize=8.0)
    ax5.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=3, frameon=False, fontsize=7.2)
    ax5.grid(axis="x")

    # 6. Seller Type by Transmission (Stacked Bar Chart)
    ax6 = add_visual_card(
        fig, x_cols[2], row2_y, col_w, row2_h,
        "6. Seller Type by Transmission", "Manual vs Automatic Share (%)",
        pad_left=0.048, pad_right=0.015, pad_bottom=0.048, pad_top=0.050,
    )
    ct_tr = pd.crosstab(df["seller_type"], df["transmission_type"], normalize="index").loc[sellers] * 100.0
    y6 = np.arange(len(s_short))
    ax6.barh(y6, ct_tr["Manual"].values, color=COLORS["primary"], height=0.55, label="Manual")
    ax6.barh(y6, ct_tr["Automatic"].values, left=ct_tr["Manual"].values, color=COLORS["negative"], height=0.55, label="Automatic")
    for i, a_pct in enumerate(ct_tr["Automatic"].values):
        ax6.text(100 - a_pct / 2, i, f"{a_pct:.1f}%", va="center", ha="center", color="white", fontsize=7.8, fontweight="bold")
    ax6.set_yticks(y6)
    ax6.set_yticklabels(s_short, fontsize=8.2)
    ax6.set_xlim(0, 100)
    ax6.set_xlabel("Share of Seller Inventory (%)", fontsize=8.0)
    ax6.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, frameon=False, fontsize=7.5)
    ax6.grid(axis="x")

    out_path = MOCKUP_DIR / "dashboard_seller_insights.png"
    fig.savefig(out_path, dpi=100, facecolor=COLORS["bg"])
    plt.close(fig)
    return out_path


def main() -> None:
    df = load_dataset()
    paths = [
        build_page1_home(df),
        build_page2_market_overview(df),
        build_page3_vehicle_analysis(df),
        build_page4_seller_insights(df),
    ]
    for p in paths:
        print("Generated:", p)


if __name__ == "__main__":
    main()
