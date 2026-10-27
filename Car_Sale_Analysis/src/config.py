"""Shared paths and plotting style for the analysis project."""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATASET_PATH = PROCESSED_DATA_DIR / "cardekho_cleaned.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
REPORTS_DIR = OUTPUTS_DIR / "reports"

SECTION_FIGURE_DIRS = {
    1: FIGURES_DIR / "01_dataset_viz",
    2: FIGURES_DIR / "02_descriptive_stats",
    3: FIGURES_DIR / "03_distributions",
    4: FIGURES_DIR / "04_correlations",
    5: FIGURES_DIR / "05_patterns",
    6: FIGURES_DIR / "06_summary",
}

sns.set_theme(style="whitegrid", context="notebook", palette="deep")
plt.rcParams.update(
    {
        "figure.figsize": (10, 6),
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
    }
)
