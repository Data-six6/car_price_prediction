# Advanced Multi-Variable Analysis Report: Used Car Market Analysis & Price Intelligence (`CDS-76`)

**Project:** Used Car Market Analysis & Price Intelligence  
**Jira User Story:** `CDS-76` — Advanced Analysis (Sprint 2 / Analytical Deep Dive)  
**Primary Dataset:** `data/final_destination.csv` (`15,229` listings, `15` columns)  
**Currency Unit:** Indian Rupees (INR, `₹`), where `1 Lakh = ₹100,000`  

---

## 1. Executive Summary

This report presents an executed, multi-variable statistical and econometric analysis of `15,229` used-car marketplace listings from `final_destination.csv`. Because the dataset is **cross-sectional** (a snapshot of asking/listing prices rather than longitudinal tracking of individual cars or confirmed completed transaction prices), all findings reflect **estimated age-related listing-price patterns** and **conditional listing-price differences** rather than guaranteed transaction margins or true longitudinal depreciation.

Key executive takeaways:

1. **Age-Related Listing-Price Curve & Stabilization:** Across reliable age cohorts (`n >= 30`, covering ages **1–15 years** and **15,161 listings / 99.55%** of the market), median listing prices peak at **Age 2 (`₹8.18 Lakh`, `n = 1,134`)** and decline steadily to **Age 15 (`₹1.43 Lakh`, `n = 90`)**. A mid-life stabilization band occurs between **Ages 6 and 9** (`-8.3%` to `-11.1%` per year, or `~₹0.50 Lakh/year`), followed by steeper percentage drops after **Age 10** (`-16.1%` at Age 10, `-19.2%` at Age 13, and `-25.0%` at Age 15). Controlling for mileage, engine size, power, transmission, seller type, and model (`R² = 0.9229`), each additional year of age corresponds to an estimated **`-10.60%`** listing-price reduction (`95% CI` in log points: `[-0.1139, -0.1102]`).
2. **Age-25 Anomaly Resolved (`₹10.00 Lakh` Spike):** The apparent price spike to `₹1,000,000` (`₹10.00 Lakh`) at `vehicle_age = 25` is caused by **a single anomalous observation (`n = 1`, row `15151`)**—a `model = "3"` (`Series 320d`) listing with `50,000 km`, `Automatic` transmission, `1,995 cc`, `154 bhp`, and a mismatched `real_body_type = "SUV"`. Every other `model = "3"` listing (`151` cars) is at most **13 years old**. We recommend **retaining** the record with a quality flag and **excluding `n < 30` age cohorts** from primary milestones and pricing models.
3. **Transmission × Body-Type Premiums (Confounding vs. True Effect):** Unadjusted Automatic premiums appear massive (`+29.4%` in Hatchbacks vs. `+114.3%` in Sedans, `+81.3%` in SUVs, `+89.5%` in MUVs), largely because Automatic listings disproportionately occur in higher-tier luxury trims and larger-engine variants. After controlling for vehicle age, mileage, engine capacity, seller type, and model (`n = 9,817`, `R² = 0.9183`, HC3 robust SEs), the **true conditional Automatic premium narrows to `+9.6%` to `+16.8%`**: **Sedan `+16.8%`**, **SUV `+14.8%`**, **Hatchback `+13.9%`**, and **MUV `+9.6%`** (joint interaction $F(3, 9740) = 2.86, p = 0.0354$).
4. **Dealer vs. Individual Seller Pricing & Inventory:** Dealers (`n = 9,446`) list at a median of **`₹5.90 Lakh`** vs. Individuals (`n = 5,610`) at **`₹5.10 Lakh`**—a **relative median listing-price difference of `+15.69%` (`+₹80,000`)**. Nearly two-thirds of this raw gap is explained by Dealers stocking **2.7× more Automatic vehicles (`27.05%` vs. `10.09%`)** and larger engines (`median 1,396 cc` vs. `1,248 cc`), despite slightly older median age (`6.0y` vs. `5.0y`). Holding vehicle specs and model fixed (`n = 15,229`, `R² = 0.9220`), **Dealers still list `+5.66%` higher than Individuals** (`95% CI: +4.91% to +6.41%`, `p = 2.19e-52`), whereas **Trustmark Dealers (`n = 173`, analyzed separately)** hold newer, low-mileage mass-market inventory (`median 4.0y`, `28,810 km`) and price at near-parity (`-2.76%` overall; `-0.22%`, `p = 0.911` on major known body types).

---

## 2. Dataset Overview

The analytical dataset (`data/final_destination.csv`) contains **`15,229` used-car listings** across **`15` variables** (`8` numeric, `7` categorical/string):

| Feature | Type | Range / Cardinality | Role in Advanced Analysis |
| :--- | :--- | :--- | :--- |
| `selling_price` | `int64` | `₹40,000` – `₹39,500,000` (Median: `₹556,000`, Mean: `₹774,538`) | Primary outcome (`selling_price` & `log(selling_price)`) |
| `vehicle_age` | `int64` | `0` – `29` years (Median: `6.0`, Mean: `6.04`) | Age-curve predictor & anomaly target |
| `km_driven` | `int64` | `100` – `830,000` km (Median: `50,000`, Mean: `54,888`) | Usage control & seller inventory profile |
| `engine` | `int64` | `793` – `6,592` cc (Median: `1,248`, Mean: `1,486`) | Engine displacement control |
| `max_power` | `float64` | `38.4` – `626.0` bhp (Median: `88.5`, Mean: `100.6`) | Power specification control |
| `mileage` | `float64` | `4.0` – `33.54` kmpl (Median: `19.67`, Mean: `19.70`) | Fuel efficiency metric |
| `real_avg_owner_count` | `float64` | `1.00` – `1.75` (Median: `1.15`) | Enriched model-level owner count |
| `real_new_ex_showroom_price` | `float64` | `0.125` – `0.990` (Median: `0.5195`, pre-scaled) | Enriched new-price proxy (note scaling & prior imputation) |
| `transmission_type` | `str` (2) | `Manual` (`12,083`), `Automatic` (`3,146`) | Key factor & interaction term |
| `real_body_type` | `str` (11) | `Unknown` (`5,317`), `Hatchback` (`3,601`), `Sedan` (`2,839`), `SUV` (`2,819`), `MUV` (`558`), + 6 sparse (`95` total) | Key factor & interaction term |
| `seller_type` | `str` (3) | `Dealer` (`9,446`), `Individual` (`5,610`), `Trustmark Dealer` (`173`) | Seller pricing & inventory factor |
| `model` / `model_grouped` | `str` (120 / 90) | `i20` (`898`), `Swift Dzire` (`875`), `Swift` (`774`), etc. | Model fixed-effects control (`model_grouped`) |
| `real_typical_owner_type` | `str` (2) | `First` (`14,925`), `Unknown` (`304`) | Enriched ownership label |
| `real_common_trim` | `str` (84) | `VDI` (`1,115`), `1.2 Magna` (`898`), etc. | Representative trim label |

---

## 3. Data Quality and Preparation

Before statistical modeling, a programmatic audit (`common.inspect_data_quality`) verified the following:

* **Missing Values & Duplicates:** `0` null/NaN values across all 15 columns and `0` exact duplicate rows.
* **Domain & Range Sanity:** Zero non-positive values for `selling_price`, `km_driven`, `engine`, or `max_power`. Zero records exceed `100,000 km/year` (`km_driven / max(vehicle_age, 1)`), confirming prior clerical odometer filtering succeeded. No trailing whitespace or case collisions exist across string categories.
* **Zero-Age Listings:** `4` records have `vehicle_age == 0` (near-new/current-year listings, median `₹5.25 Lakh`), flagged for low sample size.
* **Placeholder `"Unknown"` Labels:**
  * `real_body_type == "Unknown"` accounts for **`5,317` listings (34.91%)**.
  * `real_typical_owner_type == "Unknown"` accounts for **`304` listings (2.00%)**.
* **Small-Sample Categories (`n < 30`):**
  * **Age groups (`9` ages totaling `68` rows / `0.45%`):** Age `0` (`n=4`), `16` (`25`), `17` (`17`), `18` (`11`), `19` (`5`), `21` (`3`), `22` (`1`), `25` (`1`), `29` (`1`). Ages `20, 23, 24, 26, 27, 28` have `0` listings.
  * **Body types:** `MPV` (`24`), `Pick-up` (`6`), `Sports, Convertible` (`6`), `Coupe` (`4`), `Sports` (`1`), plus `Crossover, SUV` (`54` — exclusively Automatic, `0` Manual).
* **Prior Enrichment Nuance:** `real_new_ex_showroom_price` is pre-scaled (`0.125–0.99`) and ~34.9% of records carry a median-imputed constant (`0.5195`), so it is **not** used as a raw INR reference price.

All original CSVs were left untouched.

---

## 4. Age-Related Resale-Price Analysis

### 4.1 Listing Counts, Median/Mean Prices, and YoY Changes

Using the **`n >= 30` reliability threshold**, **Ages 1–15 (`n = 15,161`)** form the reliable analytical curve, while **Ages 0 and 16–29 (`n = 68`)** are flagged and isolated from primary claims:

| Vehicle Age | Listings (`n`) | Reliability | Median Price | Mean Price | IQR (`P25`–`P75`) | YoY Median % Change |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0 | 4 | Low (`n < 30`) | ₹5.25L | ₹15.75L | ₹4.75L–₹16.25L | — |
| 1 | 220 | Reliable | ₹7.50L | ₹10.99L | ₹5.50L–₹10.56L | *(+42.9% vs n=4)* |
| **2** | **1,134** | **Reliable** | **₹8.18L** | **₹11.43L** | ₹5.86L–₹10.98L | **+9.1%** *(mix shift)* |
| 3 | 1,896 | Reliable | ₹7.48L | ₹9.77L | ₹5.50L–₹9.50L | -8.6% |
| 4 | 2,216 | Reliable | ₹6.96L | ₹9.49L | ₹5.18L–₹9.11L | -7.0% |
| **5** | **2,089** | **Reliable** | **₹6.00L** | ₹8.20L | ₹4.50L–₹7.89L | **-13.7%** *(inflection)* |
| 6 | 1,901 | Reliable | ₹5.50L | ₹7.28L | ₹4.50L–₹7.00L | -8.3% |
| 7 | 1,427 | Reliable | ₹5.00L | ₹7.00L | ₹3.95L–₹6.50L | -9.1% |
| 8 | 1,271 | Reliable | ₹4.50L | ₹6.28L | ₹3.50L–₹6.00L | -10.0% |
| 9 | 1,014 | Reliable | ₹4.00L | ₹5.92L | ₹3.00L–₹6.00L | -11.1% |
| **10** | **706** | **Reliable** | **₹3.36L** | ₹4.96L | ₹2.50L–₹5.00L | **-16.1%** *(inflection)* |
| 11 | 541 | Reliable | ₹2.95L | ₹4.29L | ₹2.20L–₹4.00L | -12.1% |
| 12 | 293 | Reliable | ₹2.60L | ₹3.18L | ₹1.80L–₹3.30L | -11.9% |
| 13 | 234 | Reliable | ₹2.10L | ₹2.74L | ₹1.50L–₹3.00L | -19.2% |
| 14 | 129 | Reliable | ₹1.90L | ₹2.61L | ₹1.20L–₹3.00L | -9.5% |
| **15** | **90** | **Reliable** | **₹1.43L** | ₹1.88L | ₹1.00L–₹2.39L | **-25.0%** *(largest drop)* |
| 16–29 *(excl. 25)* | 63 | Low (`n < 30`) | ₹0.60L–₹1.10L | ₹0.60L–₹1.56L | — | Unreliable |
| **25** | **1** | **Anomaly (`n=1`)** | **₹10.00L** | **₹10.00L** | — | **+1,328.6% *(artifact)*** |

### 4.2 Milestones, Stabilization & Inflection Points

* **Early Segment Composition Effect (Ages 1–2):** Age 2 (`₹8.18 Lakh`) exceeds Age 1 (`₹7.50 Lakh`, `+9.1%`) because 1-year-old inventory in this marketplace snapshot contains a higher share of entry-level hatchbacks (`median power 81.8 bhp` vs. more mid/luxury mix at Age 2), not because cars appreciate in value.
* **First Price Inflection (Age 5):** Median listing price drops **`-13.7%`** (`-₹95,500`, from `₹6.96L` to `₹6.00L`), coinciding with typical 5-year warranty expiration and initial loan-cycle turnover.
* **Mid-Life Stabilization Band (Ages 6–9):** Absolute median reductions stabilize at **`₹50,000` (`₹0.50L`) per year** (`-8.3%` to `-11.1%` annually), indicating steady, predictable valuation in the high-volume `4–9` year sweet spot.
* **Post-10-Year Acceleration & 15-Year Regulatory Cliff:** From Age 10 onward, percentage declines accelerate (`-16.1%` at Age 10, `-19.2%` at Age 13, and **`-25.0%`** at Age 15 — the largest reliable YoY percentage drop), consistent with higher maintenance risk and Indian 15-year fitness/registration renewal thresholds.

### 4.3 Curve Visualizations

* `outputs/advanced_analysis/depreciation_curve.png`
* `outputs/advanced_analysis/vehicle_age_sample_size.png`
* `outputs/advanced_analysis/annual_price_change.png`

---

## 5. Age-25 Anomaly Investigation

### 5.1 Evidence from Record Inspection & Neighboring Ages

* **Sample Size:** Exactly **`1` listing (`n = 1`)** exists at `vehicle_age = 25` (index `15151` in `final_destination.csv`).
* **Full Record Profile:**
  * `model` / `model_grouped`: `"3"` (BMW 3 Series — `real_common_trim = "Series 320d"`)
  * `selling_price`: **`₹1,000,000` (`₹10.00 Lakh`)**
  * `km_driven`: `50,000 km` | `seller_type`: `Individual` | `transmission_type`: `Automatic`
  * `engine`: `1,995 cc` | `max_power`: `154.0 bhp` | `mileage`: `11.9 kmpl`
  * `real_body_type`: `"SUV"` *(notably a data-enrichment mismatch for a BMW 3 Series sedan)*
* **Comparison with Neighboring Ages:**
  * Age `21` (`n=3`, `Wagon R`): median `₹85,000`
  * Age `22` (`n=1`, `City`): median `₹70,000`
  * Age `24` (`n=0`): absent | Age `26` (`n=0`): absent
  * Age `29` (`n=1`, `Alto`): median `₹60,000`
* **Comparison with Same Model (`model == "3"`, `n = 152`):** Among the other `151` BMW 3 Series listings, the **maximum age is `13` years** (median age `7.0`, median price `₹16.50 Lakh`). A 25-year-old `Series 320d` with `50,000 km` and a modern 1,995 cc / 154 bhp engine priced at `₹10.00 Lakh` is domain-implausible and points to a **clerical age-entry error** (likely intended as `5` or `12` years) compounded by **`n = 1` sample size**.

### 5.2 Recommendation & Sensitivity Check

* **Data Governance Recommendation:** **Retain** row `15151` in the master dataset with a data-quality flag (`low_sample_age_flag = True` and `anomaly_flag = True`) for auditability; **exclude** `vehicle_age = 25` (and all `n < 30` ages) from primary age-curve reporting and pricing models.
* **Sensitivity Impact:** Removing the `68` low-sample observations (`n < 30`) shifts the piecewise `age > 10` log-price slope from `-0.0751` (all ages) to `-0.0898` (reliable ages `1–15`), removing the upward tail distortion caused by the single Age-25 `₹10.00 Lakh` listing.
* **Diagnostic Visualization:** `outputs/advanced_analysis/age_25_anomaly.png`

---

## 6. Transmission × Body Type Interaction Analysis

### 6.1 Scope & Documented Exclusions

To evaluate within-body-type Automatic vs. Manual differences without sparse-cell distortion, analysis focuses on the **4 major known body types (`n = 9,817`, `64.46%` of dataset)** where both transmissions have substantial sample sizes (`n >= 84` per cell). Excluded records (`n = 5,412`, `35.54%`):

* `Unknown`: `5,317` listings (`4,428` Manual, `889` Automatic) — missing body-type label.
* Single-transmission / sparse categories: `Crossover, SUV` (`54` Auto / `0` Manual), `MPV` (`0` Auto / `24` Manual), `Pick-up` (`0` Auto / `6` Manual), `Sports, Convertible` (`6` Auto / `0` Manual), `Coupe` (`4` Auto / `0` Manual), `Sports` (`1` Auto / `0` Manual).

### 6.2 Unadjusted vs. Confounder-Adjusted Automatic Premiums

| Body Type | Manual `n` | Manual Median | Auto `n` | Auto Median | Unadjusted Median Diff | Unadjusted % Premium | **Adjusted Regression Premium (95% CI)** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Hatchback** | 3,240 | ₹4.25L | 361 | ₹5.50L | +₹1.25L | +29.41% | **+13.85%** (`11.76%–15.99%`) |
| **Sedan** | 1,791 | ₹5.25L | 1,048 | ₹11.25L | +₹6.00L | +114.29% | **+16.80%** (`14.30%–19.35%`) |
| **SUV** | 2,120 | ₹8.00L | 699 | ₹14.50L | +₹6.50L | +81.25% | **+14.85%** (`12.06%–17.71%`) |
| **MUV** | 474 | ₹9.50L | 84 | ₹18.00L | +₹8.50L | +89.47% | **+9.62%** (`5.62%–13.77%`) |

### 6.3 Interpretation: Confounding vs. True Interaction

* **Why Unadjusted Gaps Mislead:** In Sedans, SUVs, and MUVs, Automatic transmissions are heavily concentrated in luxury brands and larger-displacement trims (e.g., MUV Automatic median engine is `2,755 cc` vs. Manual `2,494 cc`; SUV Automatic `1,995 cc` vs. Manual `1,591 cc`; Sedan Automatic `1,798 cc` vs. Manual `1,498 cc`). Thus, the raw `+81%` to `+114%` differences reflect **segment/trim mix**, not the causal price of an automatic gearbox.
* **True Adjusted Effect (`R² = 0.9183`):** Once `vehicle_age`, `km_driven`, `engine`, `seller_type`, and `model_grouped` are held constant, Automatic vehicles command a consistent **`+9.6%` to `+16.8%` premium**. The joint interaction Wald test is statistically significant ($F(3, 9740) = 2.86, p = 0.0354$), showing that the gearbox premium is slightly higher in **Sedans (`+16.8%`)** and **SUVs (`+14.8%`)** than in **MUVs (`+9.6%`)**, though individual interaction contrasts relative to Hatchback (`Sedan +2.6%, p=0.077`; `SUV +0.9%, p=0.581`; `MUV -3.7%, p=0.069`) are modest (`~7` percentage points total spread across body types).
* **Visualizations:** `outputs/advanced_analysis/transmission_body_price_comparison.png`, `outputs/advanced_analysis/transmission_body_interaction.png`

---

## 7. Dealer vs. Individual Seller Analysis

*(Note: `Trustmark Dealer`, `n = 173` / `1.14%`, is profiled separately due to its small sample size.)*

### 7.1 Price & Inventory Profile Comparison

| Metric | Dealer (`n = 9,446`, 62.0%) | Individual (`n = 5,610`, 36.8%) | Trustmark Dealer (`n = 173`, 1.1%, Separate) |
| :--- | :---: | :---: | :---: |
| **Median Listing Price** | **₹590,000 (₹5.90L)** | **₹510,000 (₹5.10L)** | **₹540,000 (₹5.40L)** |
| **Mean Listing Price** | ₹870,206 (₹8.70L) | ₹619,702 (₹6.20L) | ₹571,960 (₹5.72L) |
| **Std Dev (Price)** | ₹1,023,733 | ₹606,082 | ₹226,203 |
| **Price IQR (`P25`–`P75`)** | ₹411,000 – ₹890,000 | ₹350,000 – ₹730,000 | ₹410,000 – ₹675,000 |
| **Vehicle Age (Med / Mean)** | `6.0 yrs` / `6.15 yrs` | `5.0 yrs` / `5.92 yrs` | `4.0 yrs` / `4.29 yrs` |
| **Mileage (Med / Mean)** | `50,000 km` / `52,478 km` | `50,000 km` / `59,672 km` | `28,810 km` / `31,339 km` |
| **Automatic Share** | **27.05%** | **10.09%** | **14.45%** |
| **Median Engine / Power** | `1,396 cc` / `88.76 bhp` | `1,248 cc` / `82.00 bhp` | `1,197 cc` / `81.83 bhp` |

* **Relative Listing-Price Difference (Dealer vs. Individual):**
  $$\left(\frac{590,000}{510,000} - 1\right) \times 100 = +15.69\% \quad (+₹80,000)$$
  *Important:* This is a **relative listing-price difference**, **not** dealer profit margin or markup over acquisition cost (acquisition costs and final negotiated transaction prices are unobserved).

### 7.2 Inventory Mix & Controlled Seller Pricing

* **Inventory Profile:** Dealers actually hold slightly *older* cars (`median 6.0y` vs. `5.0y`) with identical median odometer readings (`50,000 km`), though Individuals have a longer high-mileage tail (`mean 59,672 km` vs. `52,478 km`, `P75 = 80,000` vs. `68,000 km`). The primary driver of the raw `+15.69%` price gap is **inventory composition**: Dealers carry **2.7× more Automatics (`27.05%` vs. `10.09%`)**, larger engines, and luxury outliers (`mean ₹8.70L` vs. median `₹5.90L`).
* **Controlled Multivariable Gap (`n = 15,229`, `R² = 0.9220`, HC3 SEs):** Controlling for `vehicle_age`, `km_driven`, `engine`, `transmission_type`, `real_body_type`, and `model_grouped`, **Dealers still ask `+5.66%` more than Individuals** (`95% CI: +4.91% to +6.41%`, `t = 15.23, p = 2.19e-52`), confirmed on the `n = 9,817` known-body-type sensitivity subset (`+5.42%`, `p = 3.35e-29`). Trustmark Dealers list `-2.76%` (`p = 0.0147`) across all records and `-0.22%` (`p = 0.9109`) on known major body types—effectively at parity with Individual sellers for comparable cars.
* **Visualizations:** `outputs/advanced_analysis/seller_price_comparison.png`, `outputs/advanced_analysis/seller_vehicle_age_comparison.png`, `outputs/advanced_analysis/seller_mileage_comparison.png`, `outputs/advanced_analysis/seller_price_distribution.png`

---

## 8. Statistical Significance Testing

All nonparametric tests were selected due to strong right-skewness in `selling_price` (`α = 0.05`). Multiple comparisons use **Holm–Bonferroni** family-wise error control.

### 8.1 Mann–Whitney U Tests: Dealer (`n = 9,446`) vs. Individual (`n = 5,610`)

* $H_0$: The distribution of `selling_price` (and age / km) is identical across Dealer and Individual listings.
* $H_1$: The distributions differ stochastically (two-sided).

| Metric | Dealer Median | Indiv Median | Median Diff (`95% Boot CI`) | Mann–Whitney `U` | Raw `p`-value | Holm `p`-value | Effect Size (`r_rb`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Listing Price** | **₹590,000** | **₹510,000** | **+₹80,000** (`₹65k–₹98.5k`) | `31,215,900.5` | `7.58e-75` | **`2.27e-74`** | **`+0.178`** *(small-mod)* |
| **Vehicle Age** | `6.0 yrs` | `5.0 yrs` | `+1.0 yr` (`1.0–1.0`) | `28,624,898.5` | `1.00e-16` | `2.00e-16` | `+0.080` *(negligible-small)* |
| **Km Driven** | `50,000 km` | `50,000 km` | `0 km` (`0–1,000`) | `25,400,045.5` | `2.13e-05` | `2.13e-05` | `-0.041` *(negligible)* |

*Note on Practical vs. Statistical Significance:* With `N = 15,056`, even a zero-median-difference tail shift in `km_driven` yields `p = 2.13e-05`, yet `|r_rb| = 0.041` confirms practically negligible difference in typical mileage.

### 8.2 Kruskal–Wallis H Test & Holm Post-Hoc: Major Body Types (`n = 9,817`)

* $H_0$: `Hatchback`, `Sedan`, `SUV`, and `MUV` share identical listing-price distributions.
* $H_1$: At least one body type differs stochastically.
* **Result:** **$H = 3,210.32$**, $df = 3$, **$p < 10^{-300}$**, **$\varepsilon^2 = 0.3268$** (large effect; reject $H_0$).

| Pairwise Comparison | Median 1 | Median 2 | Median Diff (`95% Boot CI`) | Raw `p` | Holm `p` | Effect Size (`r_rb`) | Significant (`α=0.05`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Hatchback vs. Sedan | ₹4.35L | ₹6.25L | -₹1.90L (`-₹2.10L to -₹1.63L`) | `3.23e-225` | **`1.62e-224`** | `-0.464` *(med-large)* | Yes |
| Hatchback vs. SUV | ₹4.35L | ₹8.80L | -₹4.45L (`-₹4.66L to -₹4.25L`) | `< 1e-300` | **`< 1e-300`** | `-0.756` *(large)* | Yes |
| Hatchback vs. MUV | ₹4.35L | ₹10.78L | -₹6.43L (`-₹7.36L to -₹5.59L`) | `1.14e-224` | **`4.54e-224`** | **`-0.841`** *(very large)* | Yes |
| Sedan vs. SUV | ₹6.25L | ₹8.80L | -₹2.55L (`-₹2.85L to -₹2.35L`) | `2.19e-86` | **`6.58e-86`** | `-0.302` *(moderate)* | Yes |
| Sedan vs. MUV | ₹6.25L | ₹10.78L | -₹4.53L (`-₹5.50L to -₹3.70L`) | `6.27e-59` | **`1.25e-58`** | `-0.433` *(med-large)* | Yes |
| SUV vs. MUV | ₹8.80L | ₹10.78L | -₹1.98L (`-₹3.00L to -₹1.10L`) | `1.66e-12` | **`1.66e-12`** | `-0.189` *(small)* | Yes |

### 8.3 Regression Joint Hypothesis Tests (HC3 Robust Covariance, `n = 9,817`)

* **Seller Type (`Dealer`, `Trustmark Dealer` vs. `Individual`):** $F(2, 9740) = 64.84, p = 1.06 \times 10^{-28}$ (reject $H_0$).
* **Transmission Main Effect (`Automatic` in Hatchback):** $F(1, 9740) = 187.99, p = 2.16 \times 10^{-42}$ (`+13.85%`, reject $H_0$).
* **Body Type Main Effects:** $F(3, 9740) = 1,661.24, p < 10^{-300}$ (reject $H_0$).
* **Transmission × Body Type Interaction:** $F(3, 9740) = 2.86, p = 0.0354$ (reject $H_0$; statistically significant, modest practical spread).
* **Summary Visualization:** `outputs/advanced_analysis/statistical_test_summary.png`

---

## 9. Regression Analysis

### 9.1 Age-Curve Functional Form Comparison (Reliable Ages `1–15`, `n = 15,161`)

| Model | Price-Scale `R²` | `log(Price)` `R²` | INR RMSE | INR MAE | AIC | Suitability |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Linear OLS (`Price ~ Age`) | `0.0565` | — | ₹869,624 | ₹427,155 | `457,707.2` | Poor (misses % decay & skew) |
| Polynomial Deg 2 (`Age + Age²`) | `0.0568` | — | ₹869,481 | ₹426,637 | `457,704.2` | Weak (additive error variance) |
| Polynomial Deg 3 (`Age..Age³`) | `0.0569` | — | ₹869,449 | ₹426,678 | `457,705.1` | Over-parameterized (`Age²/³ p > 0.19`) |
| Log-Linear (`log(Price) ~ Age`) | `0.0560` | `0.2194` | ₹869,856 | ₹427,541 | `27,507.6` | Good baseline (`-10.3%/yr`) |
| **Piecewise Log-Linear (knots 5, 10)** | `0.0568` | **`0.2268`** | ₹869,480 | **`₹425,805`** | **`27,367.3`** | **Best bivariate fit (`ΔAIC = -140.3`)** |

*Why univariate `R²` is modest (`0.227` on log-scale):* Age alone ignores whether a car is a Maruti Alto or a BMW 3 Series. Adding `km_driven`, `engine`, `max_power`, `transmission_type`, `seller_type`, and `model_grouped` lifts **`log(Price)` `R²` to `0.9229`** (`Adj R² = 0.9224`).

### 9.2 Full Interaction & Seller Pricing Models (`HC3` Robust SEs)

* **Interaction Model (`n = 9,817`, Major Body Types):** `R² = 0.9183`, `Adj R² = 0.9177`, `log-RMSE = 0.1900`:
  * `vehicle_age`: $\beta = -0.1238$ (`-11.64%/yr`, `p < 1e-300`)
  * `km_driven`: $\beta = -5.70 \times 10^{-7}$ (`-0.57%` per `10,000 km`, `p = 7.04e-13`)
  * `engine`: $\beta = +0.000176$ (`+1.78%` per `100 cc`, `p = 2.32e-15`)
  * `Automatic` (Hatchback ref.): $\beta = +0.1297$ (`+13.85%`, `p = 8.75e-43`)
  * `Dealer` (vs. Individual): $\beta = +0.0529$ (`+5.43%`, `p = 2.80e-29`)
* **Full-Dataset Seller Model (`n = 15,229`):** `R² = 0.9220`, `Adj R² = 0.9215`, `log-RMSE = 0.1918`:
  * `Dealer` vs. `Individual`: $\beta = +0.0550$ (**`+5.66%`**, `95% CI: 4.91%–6.41%`, `p = 2.19e-52`)
  * `Trustmark Dealer` vs. `Individual`: $\beta = -0.0280$ (**`-2.76%`**, `95% CI: -4.93% to -0.55%`, `p = 0.0147`)

---

## 10. Key Findings

1. **Multiplicative Age Structure:** Used-car listing prices follow an exponential (log-linear) decay with clear milestones at **Age 5** (`-13.7%` step-down), a stable **Ages 6–9** plateau (`~₹0.50L/year`), and accelerated discounting past **Age 10** (`-16.1%` to `-25.0%`).
2. **Low-Sample Pitfalls:** Every age outside **1–15 years** has fewer than 30 listings (`0` and `16–29`). Unfiltered charts create false spikes such as **Age 25 (`n = 1`, `₹10.00 Lakh`)**, which is a single mis-aged BMW 3 Series record.
3. **Confounding Drives Raw Gearbox Gaps:** Raw Automatic vs. Manual gaps (`+81%–114%` in Sedans/SUVs/MUVs) are mostly model/trim confounding; true spec-adjusted Automatic premiums are **`+9.6%` to `+16.8%`**.
4. **Dealer Premium Decomposition:** Of the raw **`+15.69%`** Dealer median listing advantage over Individuals, roughly **two-thirds reflects richer inventory mix** (2.7× Automatic share, larger engines, luxury tail) and **`+5.66%` persists** after controlling for vehicle specs and model.

---

## 11. Business Recommendations

1. **Apply Confounder-Adjusted Pricing Rules for Automatics:** Dealership pricing teams should benchmark Automatic appraisals using a **`+10%` to `+17%` trim-adjusted premium** (`+16.8%` Sedan, `+14.8%` SUV, `+13.9%` Hatchback, `+9.6%` MUV) rather than unadjusted segment medians, avoiding over-bidding on mass-market automatics.
2. **Optimize Inventory Acquisition Around the 6–9 Year Plateau & Pre-10-Year Exit:** For fast-turning retail stock, target **3–5 year** vehicles for margin/warranty appeal or **6–9 year** vehicles where annual price drops stabilize (`~₹0.50L/yr`). Accelerate liquidation of stock approaching **Age 10+** and especially **Age 14–15**, where listing prices fall `19%–25%` per year.
3. **Calibrate Dealer Ask Strategy Against Private Sellers:** Because comparable Dealer listings sit **`~5.7%`** above Individual listings, dealerships should explicitly bundle verifiable value-adds (inspection reports, warranty, financing convenience) to justify that `~5.7%` spread—especially in segments where `Trustmark Dealer` competitors price near Individual parity.
4. **Enforce Automated Data-Quality Guardrails in BI & ML Pipelines:** Add ingestion rules flagging `vehicle_age > 15` (or `n < 30` cohorts), age-model mismatches (like row `15151`), and `"Unknown"` body-type records (`34.9%`) before publishing Power BI KPI cards or training price-prediction models.

---

## 12. Limitations

1. **Cross-Sectional Listing Data (Not Longitudinal or Transactional):** Observations reflect *asking prices* at a single point in time, not actual final sale prices after buyer-seller negotiation, and do not track the same car over time (cohort/model-mix shifts can affect adjacent ages like Age 1 vs. Age 2).
2. **Missing & Imputed Metadata:** `real_body_type` is `"Unknown"` for `34.91%` of listings (`5,317` rows), restricting the clean Transmission × Body Type interaction model to `n = 9,817` (`64.5%`). `real_new_ex_showroom_price` is pre-scaled and ~35% imputed, preventing direct percentage-of-MSRP retention calculation.
3. **Unobserved Condition & Geography in `final_destination.csv`:** Service history, accident records, trim-level option packages, and city/region (`real_primary_city` was pruned during prior cleaning) are absent from `final_destination.csv`, meaning residual price gaps (such as Dealer `+5.66%`) may partly reflect unmeasured vehicle condition or geographic mix.
4. **Sparse Older & Niche Segments:** Conclusions do not generalize reliably beyond **Age 15** or to niche body styles (`Coupe`, `Sports`, `Pick-up`, `MPV`, `Crossover, SUV`).

---

## 13. Conclusion

Across `15,229` CarDekho listings, rigorous nonparametric testing and `HC3` robust log-price regressions (`R² ≈ 0.92`) separate genuine market pricing signals from sample-size artifacts and compositional confounding. Listing prices decline at roughly **`10.6%` per year** after controlling for specs and model, with a clear **6–9 year stabilization band** and steeper declines past **Age 10**. The apparent **Age-25 spike** is confirmed to be a **single-record (`n=1`) anomaly**, Automatic transmissions carry a true **`+9.6%` to `+16.8%` premium** that varies modestly by body type, and Dealers command a **`+5.66%` controlled listing premium** above Individuals beyond their richer Automatic and luxury inventory mix.
