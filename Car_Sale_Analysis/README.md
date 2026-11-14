# Car Sale Analysis — Used Car Market Analysis & Price Intelligence

Exploratory and advanced statistical analysis of the CarDekho used-car listings dataset (`data/final_destination.csv`, `15,229` records × `15` columns), covering both the foundational exploratory lab notebooks and **Jira Story CDS-76: Advanced Analysis**.

## Project Layout

- `data/final_destination.csv` — processed `15,229`-listing dataset used by the CDS-76 advanced analysis (`data/raw/` kept unchanged).
- `notebooks/` — six foundational exploratory analysis notebooks (`01`–`06`).
- `advanced_analysis/` — four executed CDS-76 notebooks (`depreciation_analysis.ipynb`, `transmission_body_analysis.ipynb`, `seller_dynamics_analysis.ipynb`, `statistical_testing.ipynb`).
- `advanced_analysis/scripts/` — reproducible modular Python pipeline (`common.py`, `depreciation_analysis.py`, `transmission_body_analysis.py`, `seller_dynamics_analysis.py`, `statistical_testing.py`, `run_all_analysis.py`).
- `outputs/advanced_analysis/` — 11 publication-quality 300 DPI visualizations for CDS-76.
- `outputs/reports/` — executive report (`advanced_analysis_report.md`) and validated metrics (`advanced_analysis_metrics.json`).
- `outputs/figures/` — exported figures for the foundational exploratory notebooks.
- `src/` — foundational plotting style and figure-saving helper.

## Setup & Reproduction

Install dependencies (including `statsmodels` for HC3 robust OLS and Wald tests) and run the full CDS-76 pipeline:

```bash
python -m pip install -r requirements.txt
python advanced_analysis/scripts/run_all_analysis.py
```

In Windows environments with Anaconda alongside an isolated Python installation, execute with the Anaconda interpreter that provides `statsmodels`, `scipy`, `seaborn`, `nbformat`, and `nbconvert`:

```powershell
C:\Users\USER\anaconda3\python.exe advanced_analysis\scripts\run_all_analysis.py
```

## CDS-76 Advanced Analysis Summary

### Business Questions & Statistical Methods

| Analysis | Business Question | Key Methods | Notebook / Script |
|---|---|---|---|
| **1. Age-Related Resale-Price Curve** | How do median listing prices vary across `vehicle_age`, and is `vehicle_age = 25` a true market trend or an anomaly? | Age-stratified medians, YoY % change, `n < 30` reliability threshold & sensitivity analysis, Age-25 record forensics, Linear / Poly (deg 2–3) / Log-Linear / Piecewise Log-Linear (`knots = 5, 10`) & multivariate OLS (`n = 15,161`) | `advanced_analysis/depreciation_analysis.ipynb`<br>`advanced_analysis/scripts/depreciation_analysis.py` |
| **2. Transmission × Body Type Interaction** | Does the Automatic vs. Manual price gap vary by vehicle body type? | Stratified medians across major known body types (`n = 9,817`; excluding `5,317` `Unknown` + `95` niche body types), `log(selling_price)` OLS with `HC3` SEs & `C(transmission_type) * C(real_body_type)`, joint Wald F-test | `advanced_analysis/transmission_body_analysis.ipynb`<br>`advanced_analysis/scripts/transmission_body_analysis.py` |
| **3. Dealer vs. Individual Seller Dynamics** | Do Dealers and Individuals price differently and hold different inventory profiles? | Stratified price/age/mileage comparisons (`Trustmark Dealer` `n = 173` separated), relative listing-price difference formula, multivariable `log(selling_price)` OLS (`HC3`, `n = 15,229` & `n = 9,817`) | `advanced_analysis/seller_dynamics_analysis.ipynb`<br>`advanced_analysis/scripts/seller_dynamics_analysis.py` |
| **4. Statistical Significance Testing** | Are observed group differences statistically robust after multiple-testing correction and practical-effect evaluation? | Two-sided Mann–Whitney U + rank-biserial `r_rb` + bootstrap median-diff CI, Kruskal–Wallis H + epsilon-squared + Holm–Bonferroni post-hoc pairwise tests, HC3 joint Wald F-tests ($\alpha = 0.05$) | `advanced_analysis/statistical_testing.ipynb`<br>`advanced_analysis/scripts/statistical_testing.py` |

### Key Verified Findings

1. **Age-Related Listing-Price Patterns:** Across reliable age cohorts (`vehicle_age` 1–15, `n = 15,161`), median listing price peaks at Age 2 (`₹8.18 Lakh`, `n = 1,134`; Age 1 is `₹7.50 Lakh`, `n = 220` due to segment composition) and declines to `₹1.43 Lakh` at Age 15 (`n = 90`). Mid-life prices stabilize at `₹0.50 Lakh/year` across Ages 6–9 (`-8.3%` to `-11.1%` annually) before steepening beyond Age 10 (`-25.0%` at Age 15). Piecewise Log-Linear (`knots = 5, 10`) outperforms single-slope Log-Linear (`AIC = 27,367.28` vs. `27,507.62`; `age_gt10 = -0.0898`, `p = 7.02e-18`), while multivariable log-price regression (`R² = 0.9229`) estimates `-10.60%` listing price per additional year holding specs and model fixed.
2. **Age-25 Anomaly Resolved:** The `₹10.00 Lakh` (`₹1,000,000`) spike at `vehicle_age = 25` is caused by a **single observation (`n = 1`, index `15151`)**—`model = "3"`, `real_common_trim = "Series 320d"`, `engine = 1995`, `max_power = 154.0`, `km_driven = 50,000`, `transmission_type = "Automatic"`, with `real_body_type = "SUV"`. Every other `model = "3"` listing (`151` rows) has `max_age = 13`. Retaining it with a flag while excluding `n < 30` cohorts (`68` rows total across ages `0, 16–29`) prevents distorted trendlines.
3. **Transmission × Body Type Premiums:** Unadjusted Automatic median premiums range from `+29.41%` in Hatchbacks to `+114.29%` in Sedans, `+81.25%` in SUVs, and `+89.47%` in MUVs. After controlling for age, mileage, engine, seller type, and `model_grouped` (`n = 9,817`, `R² = 0.9183`), the interaction remains statistically significant (`F(3, 9740) = 2.86, p = 0.0354`), with adjusted Automatic premiums of `+13.85%` (Hatchback), `+16.80%` (Sedan), `+14.85%` (SUV), and `+9.62%` (MUV).
4. **Dealer vs. Individual Dynamics:** Dealers (`n = 9,446`, median `₹5.90 Lakh`) list `+15.69%` (`+₹80,000`) higher than Individuals (`n = 5,610`, median `₹5.10 Lakh`; Mann–Whitney `U = 31,215,900.5, p_holm = 2.27e-74, r_rb = +0.1781`), largely driven by Automatic share (`27.05%` vs. `10.09%`) and luxury-tail inventory. Controlling for vehicle attributes and model narrows the Dealer relative listing-price difference to `+5.66%` (`95% CI: 4.91%–6.41%, p = 2.19e-52`). `Trustmark Dealer` (`n = 173`) stocks newer (`median age 4.0`) and lower-mileage (`median 28,810 km`) cars at `-2.76%` adjusted (`p = 0.0147`, vanishing to `-0.22%, p = 0.9109` on major body types).

### Visual Deliverables (`outputs/advanced_analysis/`)

1. `depreciation_curve.png` — Median & mean listing-price curve with IQR band, `n < 30` reliability threshold, and piecewise model fit.
2. `vehicle_age_sample_size.png` — Listing counts by `vehicle_age` highlighting reliable vs. low-sample (`n < 30`) cohorts.
3. `annual_price_change.png` — Year-over-year percentage change in median listing price with milestone declines highlighted.
4. `age_25_anomaly.png` — Forensic comparison of `vehicle_age = 25` (`n = 1`, `BMW 320d`) against neighboring ages and the broader `model = "3"` cohort.
5. `transmission_body_price_comparison.png` — Grouped Automatic vs. Manual median listing prices with sample counts across major body types.
6. `transmission_body_interaction.png` — Unadjusted median gap slopes alongside HC3 adjusted Automatic premium forest plot (`95% CI`).
7. `seller_price_comparison.png` — Median, mean, and IQR comparison for Dealer, Individual, and Trustmark Dealer listings.
8. `seller_vehicle_age_comparison.png` — Inventory age distribution and summary statistics by seller type.
9. `seller_mileage_comparison.png` — Inventory `km_driven` distribution by seller type.
10. `seller_price_distribution.png` — Log10 price density curves and luxury-tail boxplots across seller types.
11. `statistical_test_summary.png` — Non-parametric test summary, rank-biserial effect sizes (`r_rb`), and HC3 joint Wald F-test summary.
12. `age_1_vs_2_composition_comparison.png` — Deep-dive comparison of `vehicle_age == 1` (`n = 220`) vs. `vehicle_age == 2` (`n = 1,134`) across price tiers, Sedan/Dealer mix, model shifts, and engine/power specs (`advanced_analysis/scripts/age_1_vs_2_investigation.py`).
13. `age_1_vs_2_regression_decomposition.png` — Same-model matched price check (`16` models) and nested HC3 regression showing the `+9.1%` raw median gap vanishing to `+0.29%` (`p = 0.860`).

### Power BI Dashboard UI/UX Design Mockups (`outputs/dashboard_mockups/`)

Generated via `advanced_analysis/scripts/generate_powerbi_mockups.py` (`1920 × 1080` widescreen `16:9`, documented in [`outputs/reports/powerbi_dashboard_design_spec.md`](outputs/reports/powerbi_dashboard_design_spec.md)):

1. `dashboard_home.png` — **Page 1: Home (Executive Overview)** (6 KPIs, 4 core charts, 3-point Executive Insights panel).
2. `dashboard_market_overview.png` — **Page 2: Market Overview** (4 dropdown slicers, 4 KPIs, 6 composition & pricing charts).
3. `dashboard_vehicle_analysis.png` — **Page 3: Vehicle Analysis & Price Intelligence** (Age curve, YoY % change, dedicated `AGE 25 PRICE ANOMALY` warning card, Engine tiers, Mileage scatter, Transmission × Body Type).
4. `dashboard_seller_insights.png` — **Page 4: Seller & Pricing Intelligence** (Dealer vs. Individual KPIs, price/age/km bars, summary card, log-price box plot, 100% stacked body & transmission splits).

### Limitations

- **Cross-sectional listings:** Reflects asking/listing prices at snapshot time, not completed transaction prices, dealer acquisition margins, or longitudinal single-vehicle depreciation.
- **High missingness in enriched categorical metadata:** `5,317` rows (`34.91%`) carry `real_body_type = "Unknown"` (plus `95` niche body-type rows), excluded from body-type comparisons and checked via sensitivity models.
- **Residual confounding & label anomalies:** Trim-level options, service history, accident history, and city/state geography are unobserved; rare metadata issues (such as the age-25 `"3"` labeled `"SUV"`) highlight reliance on listing text.

Full narrative report: [`outputs/reports/advanced_analysis_report.md`](outputs/reports/advanced_analysis_report.md)

## Foundational Lab Rubric Mapping

| Section | Notebook | Focus |
|---|---|---|
| 1 | `notebooks/01_dataset_visualization.ipynb` | Dataset exploration and variable types |
| 2 | `notebooks/02_descriptive_statistics.ipynb` | Central tendency, spread, skewness, and kurtosis |
| 3 | `notebooks/03_distribution_analysis.ipynb` | Shape, concentration, outliers, and group distributions |
| 4 | `notebooks/04_correlation_and_association.ipynb` | Regression scatter, correlation matrix, and associations |
| 5 | `notebooks/05_pattern_detection.ipynb` | Trends, clusters, group differences, and anomalies |
| 6 | `notebooks/06_summary_of_findings.ipynb` | Key findings, dashboard, and final insights |
