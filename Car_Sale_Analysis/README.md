# Car Sale Analysis

A six-section exploratory analysis of the CarDekho used-car dataset. Each notebook corresponds to one lab section, while shared plotting configuration and helpers live in `src/`.

## Project layout

- `data/raw/` — source data, kept unchanged.
- `data/processed/cardekho_cleaned.csv` — cleaned dataset used by the notebooks.
- `notebooks/` — six modular analysis notebooks.
- `outputs/figures/` — exported figures, organized by section at 300 DPI.
- `outputs/reports/` — final report and other exported summaries.
- `src/` — reusable paths, plotting style, and figure-saving helper.

## Setup

From this directory, install the dependencies and start Jupyter:

```bash
python -m pip install -r requirements.txt
jupyter lab
```

Place the cleaned CarDekho CSV at `data/processed/cardekho_cleaned.csv` before running the notebooks. The dataset was not included when this project structure was created; no placeholder or synthetic dataset is provided.

## Lab rubric mapping

| Section | Notebook | Focus |
|---|---|---|
| 1 | `01_dataset_visualization.ipynb` | Dataset exploration and variable types |
| 2 | `02_descriptive_statistics.ipynb` | Central tendency, spread, skewness, and kurtosis |
| 3 | `03_distribution_analysis.ipynb` | Shape, concentration, outliers, and group distributions |
| 4 | `04_correlation_and_association.ipynb` | Regression scatter, correlation matrix, and associations |
| 5 | `05_pattern_detection.ipynb` | Trends, clusters, group differences, and anomalies |
| 6 | `06_summary_of_findings.ipynb` | Key findings, dashboard, and final insights |

Save charts with `src.plot_utils.save_figure` and the matching section directory under `outputs/figures/`.
