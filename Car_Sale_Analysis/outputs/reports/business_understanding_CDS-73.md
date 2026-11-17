# Sprint 2 — Business Understanding and Analytical Plan (CDS-73)

**Project:** Used Car Market Analysis — CarDekho listings  
**Prepared:** 2026-11-17  
**Jira:** https://chhounvannaksokpanhaclone.atlassian.net/browse/CDS-73  
**Primary dataset:** `Car_Sale_Analysis/data/final_destination.csv` (15,229 listings, 15 columns)  
**Currency and market:** Indian rupees (INR); CarDekho listings, not Cambodian market observations.

## 1. Business problem and intended decisions

A used-car listing price can reflect vehicle characteristics, seller positioning and inventory mix. Buyers need comparable asking-price benchmarks; dealers need a way to review their asking prices and decide what kinds of vehicles to list; market analysts need to identify segments for investigation.

**Decision objective:** describe and quantify associations between vehicle characteristics and *advertised asking prices*, distinguish raw differences from composition-adjusted differences, and provide transparent segment benchmarks. This dataset does **not** establish final sale prices, realized dealer margins, units sold, demand or inventory turnover.

**Unit of analysis:** one observed vehicle listing. **Outcome:** `selling_price` (field name notwithstanding, interpreted as listing/asking price, not a confirmed transaction). **Population:** the CarDekho dataset snapshot; not a representative sample of all Indian used-car transactions.

## 2. Stakeholders and use cases

| Audience | Decision or use case | Output |
| --- | --- | --- |
| Used-car dealers / inventory managers | Compare listing prices for similar models, ages and mileage; identify listing-heavy segments | Segment median asking prices, listing counts and composition-adjusted comparisons |
| Buyers | Evaluate whether an advertisement sits above or below comparable advertisements | Model- and specification-matched asking-price ranges, with sample sizes |
| Market analysts / research team | Identify factors related to quoted prices and where data gaps limit inference | Reproducible EDA, regression diagnostics, limitations and visual summaries |
| Product / dashboard users | Filter by age, model, transmission, body and seller category | Clear dashboard definitions and caveats; no sales-volume or turnover labels |

## 3. Business questions, hypotheses, measures and methods

| ID | Question | Working hypothesis (to test, not assume) | Measure and analysis | Business decision |
| --- | --- | --- | --- | --- |
| BQ1 | Which observed attributes most strongly relate to asking price? | Age, model, engine/power, mileage and transmission have material associations, but raw group comparisons are confounded by vehicle mix. | Median and IQR by segment; multivariable log-price regression; model diagnostics and robustness checks | Explain and benchmark advertised prices |
| BQ2 | How do age and mileage relate to asking price after controlling for model and specification? | Greater age and mileage tend to relate to lower quoted prices, and the age-price relationship may be non-linear. | Age-cohort count/median curves with low-n flags; log-price regression with age, mileage and model/spec controls; flexible age terms | Compare cars of different ages/usage; *not* infer longitudinal depreciation |
| BQ3 | Which models appear most frequently in listings, and how do their price distributions differ? | Listing prevalence and price levels differ by model. | Listing count, share and median/IQR by model; minimum sample threshold, segmentation by age and transmission | Identify listing availability and pricing ranges; *not* claim popularity in sales or demand |
| BQ4 | Do dealer, individual and Trustmark Dealer asking prices differ for comparable vehicles? | Raw dealer premiums partly reflect more expensive inventory; adjusted differences will be smaller. | Seller counts and medians, composition checks, HC3-robust multivariable log-price model and confidence intervals | Seller-positioning benchmarks; *not* infer dealer profits |
| BQ5 | Does automatic transmission's association with price differ by body type? | The automatic price premium varies by body type, beyond differences in age/model/spec mix. | Stratified raw medians, adjusted interaction model, confidence intervals and joint test | Segment-aware price comparison |

These are associational hypotheses. Statistical significance alone is not evidence of practical value or causal impact.

## 4. Existing evidence available in GitHub (not newly recalculated here)

The linked advanced analysis report for CDS-76 records the following **previously reported** results:

- **Dataset:** 15,229 listings, median asking price ₹5.56 lakh, median age 6 years, median mileage 50,000 km.
- **Age:** adjusted log-price model reports an association equivalent to approximately **10.60% lower advertised price per additional year**, conditional on its controls (model R² 0.9229). This is not an observed annual depreciation rate for the same car.
- **Seller:** dealer median ₹5.90 lakh (n=9,446), individual median ₹5.10 lakh (n=5,610). The prior adjusted model estimates a **5.66% dealer listing-price difference** (95% CI 4.91%–6.41%) conditional on measured vehicle characteristics.
- **Transmission × body:** reported adjusted automatic associations are +13.85% hatchback, +16.80% sedan, +14.85% SUV and +9.62% MUV, based on the modeled major-body-type subset (n=9,817).
- **Quality:** 5,317 listings (34.91%) have unknown body type; one age-25 observation causes a misleading tail spike. The prior analysis uses n ≥ 30 for reliable age cohorts.
- **Model prevalence:** not yet audited for this Business Understanding task. Compute listing counts from the source CSV instead of inventing rankings.

Evidence sources:
- [Repository README](../../README.md) (relative link from this file may not resolve; use the full link below)
- [Advanced analysis report](../reports/advanced_analysis_report.md)
- [Advanced metrics JSON](../reports/advanced_analysis_metrics.json)

Direct links:  
https://github.com/Data-six6/car_price_prediction/blob/main/Car_Sale_Analysis/README.md  
https://github.com/Data-six6/car_price_prediction/blob/main/Car_Sale_Analysis/outputs/reports/advanced_analysis_report.md  
https://github.com/Data-six6/car_price_prediction/blob/main/Car_Sale_Analysis/outputs/reports/advanced_analysis_metrics.json

## 5. Execution plan and acceptance checks

1. **Validate source and definitions.** Inspect the CSV schema, list missing and duplicate records, confirm units/category labels, and ensure `selling_price` is treated as an asking price. Record filters and sample counts.
2. **Create reproducible descriptive cuts.** Show listing counts, medians, IQRs and sample sizes by model, seller, transmission/body, age cohort and mileage band. Never label listing frequencies as completed sales.
3. **Test adjusted comparisons.** Reuse/refit transparent regression specifications; report coefficients as percentage associations only when appropriate, uncertainty intervals, holdout sensitivity and selection biases.
4. **Build decision-ready outputs.** One summary table per question, at least one defensible chart for each primary theme, and clear caveats on price interpretation and representativeness.
5. **Stakeholder review.** Confirm that the target audience, model segmentation and actionable decisions match project expectations before closing CDS-73.

### Definition of Done for CDS-73

- [x] Core business questions defined (pricing, age/mileage, model listing prevalence and seller differences).
- [x] Hypothesis framework and planned metrics/methods documented.
- [x] Target audiences and business use cases defined.
- [x] Known data limitations and existing analytical evidence recorded.
- [ ] Stakeholders validate objectives and intended business decisions.
- [ ] Reproduce and review model-prevalence statistics if used in conclusions.

**Scope boundary:** Current evidence concerns the *Indian* CarDekho dataset, not Cambodian used-car pricing. Any Cambodia-specific market recommendation requires independently sourced local observations and validation.
