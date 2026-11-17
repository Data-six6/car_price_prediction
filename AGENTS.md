# AGENTS.md — Used Car Market Analysis

## Mission
You are Codex working on **Data-six6/car_price_prediction**. Finish and verify remaining work for the Used Car Market Analysis project, primarily Sprint 2 (Data Analysis, Jira CDS-73/CDS-75/CDS-76/CDS-77) and Sprint 3 (Power BI Delivery, CDS-84 through CDS-88). Treat Jira as the source of truth for requirements and current statuses, and the repository as the source of truth for actual code and deliverables. **Do not assume that a Done parent or a newly created To Do subtask proves its implementation status.**

## Repo orientation
- Application/project folder: `Car_Sale_Analysis/`; run project commands from there.
- `README.md` describes the existing dataset, analysis scripts, reports and dashboard mockups.
- `data/final_destination.csv`: CarDekho listings, 15,229 rows × 15 columns per existing README. Inspect actual files before trusting counts.
- `notebooks/`: foundational EDA notebooks.
- `advanced_analysis/` and `advanced_analysis/scripts/`: advanced analysis and reproducible Python scripts.
- `outputs/reports/advanced_analysis_report.md`, `advanced_analysis_metrics.json`, `business_understanding_CDS-73.md`: existing evidence.
- `outputs/reports/powerbi_dashboard_design_spec.md` and `outputs/dashboard_mockups/`: existing dashboard specification and design references.
- `requirements.txt`: Python dependencies.
- Existing reproduction command from `Car_Sale_Analysis/`: `python -m pip install -r requirements.txt`, then `python advanced_analysis/scripts/run_all_analysis.py`. Inspect environment and scripts before running.

## Core analytical integrity
1. These are **Indian CarDekho vehicle listings**, not Cambodia market data and not verified completed sales. Use **listing count**, **asking/listing price**, and **cross-sectional age-price association**; do not claim transaction volume, realized sales, profit margins, demand, or longitudinal depreciation.
2. Keep original/raw files immutable. Make transformations reproducible, with documented assumptions and output locations. Avoid overwriting validated existing outputs without comparison.
3. Verify currency (INR), price units, schema, nulls, duplicates, seller categories and grouping definitions. Report sample sizes. Do not silently remove outliers; explain handling.
4. Known limitations in existing report: body type Unknown for 5,317 listings (34.91%), rare age-25 observation with n=1; flag low-n groups (previous analysis uses n<30).
5. Distinguish raw comparisons from adjusted statistical associations. Do not infer causation; report uncertainty and data coverage. Recalculate any number used in new dashboards from a documented common dataset.

## Jira mapping and priorities
Jira project: `CDS` at https://chhounvannaksokpanhaclone.atlassian.net .
There are detailed stories and duplicate-looking, mostly empty stories (CDS-97 through CDS-108). **Do not create or expand duplicates**; use the detailed stories below and ask the team if ownership or scope conflicts.

### Sprint 2 — analyze, verify, and close evidence gaps
- CDS-73 Business understanding: questions, hypotheses, stakeholders, decisions; see `outputs/reports/business_understanding_CDS-73.md`. Subtasks CDS-111 and CDS-127–129.
- CDS-75 EDA: price distributions, age/mileage relationships, brand/model listing counts, notebook documentation. Subtasks CDS-130–133.
- CDS-76 Advanced analysis: age curves, transmission × body interaction, seller dynamics, significance tests. Subtasks CDS-134–137. Existing reproducible work is in `advanced_analysis/`; verify, do not rebuild blindly.
- CDS-77 Insights: business findings, actionable recommendations, baseline KPIs and BI handoff. Subtasks CDS-138–141.
- If the Jira board shows these stories Done, audit evidence and document discrepancies; do not reopen or change statuses automatically.

### Sprint 3 — primary implementation target
- CDS-84 Data integration (CDS-142–145): import cleaned CSV, confirm column types, create core DAX measures and reconcile values with Python/SQL.
- CDS-85 Dashboard page 1 (CDS-146–148): executive KPI cards, brand/body/price-tier composition, consistent visual hierarchy.
- CDS-86 Dashboard pages 2–3 (CDS-149–152): pricing vs mileage, age-group median, transmission/fuel comparison, model frequency and price metrics, specification filters and inventory table.
- CDS-87 Dashboard page 4 (CDS-153–156): dealer vs individual listing comparisons, age/mileage composition, synchronized slicers, reset, tooltips and cross-filter tests.
- CDS-88 Testing and delivery (CDS-157–160): cross-tool KPI parity, visual/filter QA, documentation/screenshots, final GitHub delivery.
- **Use actual Jira descriptions and acceptance criteria as authoritative.** Story names above are a working index, not a substitute for opening issues.

## Working protocol (every session)
1. Inspect `git status`, branch, README, existing outputs and dependency availability. Do not overwrite teammates' changes.
2. Read current Jira parent and subtask details if connected; otherwise use the mapping above and explicitly note that statuses may be stale.
3. Create a concise status matrix: Jira key | acceptance criterion | existing evidence | gap | proposed file change | verification.
4. Select the smallest high-value unfinished item. Prefer incremental, reviewable commits on a feature branch; avoid pushing directly to main without team approval.
5. Implement actual code, tests, DAX, documentation or reusable dashboard assets. Do not stop at a plan when implementation is feasible.
6. Run relevant tests, inspect output files, and compare with existing reference metrics. Report failures and limitations; never claim tests passed if not executed.
7. Provide a concise handoff: files changed, commands run, test results, evidence links, unresolved blockers and recommended Jira status.
8. Update Jira only when explicitly authorized and connected. Never auto-transition issues to Done, invent worklogs, backdate Sprint Planning, or mark subtasks complete solely because a parent is Done.

## Power BI-specific execution
- First check whether a real `.pbix` or `.pbip` project exists and whether a compatible authoring environment is available. Do not pretend to generate or validate a working `.pbix` from screenshots alone.
- When Power BI Desktop is unavailable (for example on Linux), produce practical handoff artifacts: cleaned validated CSV, Power Query/M transformation notes, documented DAX measures, page-by-page visual specifications, mockups, source-to-measure mapping, QA matrix, and exact manual steps needed in Desktop.
- If an existing `.pbip` project is available, prefer editing its text-based definition with validation, and avoid unsupported binary edits.
- Minimum DAX definitions: Total Listings (count of rows), Avg Listing Price, Median Listing Price, Avg Mileage, Avg Vehicle Age, and comparison-to-overall measures. Document filter context, blanks, price units and denominator behavior. Prefer a dedicated Measures table.
- Dashboard layout must follow the **actual Jira acceptance criteria**; reconcile any differences between the 4-page Jira layout and existing mockups/design specification before implementing.
- Validate all dashboard metrics against Python and/or SQL computed from the **same version** of the cleaned dataset, with stated tolerance for floating-point calculations. Keep evidence in a reproducible QA report.
- Test synchronized filters (brand, age group, mileage band, transmission, seller type), reset behavior, cross-filtering, missing categories and zero-row selections.
- If no compatible BI runtime exists, mark interaction and visual verification as **manual QA pending**, not passed.

## Deliverables and definition of done
- Reproducible scripts and source-backed data/metric definitions.
- Traceable Jira acceptance-criteria matrix with paths to evidence.
- Four dashboard pages or an honest, implementation-ready handoff if BI authoring is unavailable.
- A KPI reconciliation table, documented test outcomes and manual-QA checklist.
- Updated README with setup, run/reproduction, file locations, limitations and screenshots when real screenshots exist.
- No invented charts, test results, business claims, screenshots, approvals or Jira completion statuses.

## Guardrails
- No destructive commands, force pushes, secret exposure, broad reformatting or unrelated refactors.
- No new dependencies unless needed and justified; favor existing Python packages.
- Never edit original data in place. Keep scripts idempotent and paths portable.
- Do not fabricate a Sprint Review history: the recently created Jira subtasks are a retrospective breakdown, not proof they were created at the original planning meeting.
- Ask for human approval before changing project scope, merging to protected/default branches, publishing externally, or transitioning Jira stories.
- For each blocker, produce the closest useful, testable artifact and a precise human action needed to unblock.
