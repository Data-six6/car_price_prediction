# Power BI Dashboard UI/UX Design Specification

**Project Name:** Used Car Market Intelligence Dashboard  
**Target Tool:** Microsoft Power BI Desktop (`16:9` Widescreen, `1920 × 1080` px)  
**Dataset:** `data/final_destination.csv` (`15,229` used-car listings × `15` columns)  

---

## 1. Mockup Files (`outputs/dashboard_mockups/`)

1. **Page 1 — Home (Executive Overview):** [`dashboard_home.png`](../dashboard_mockups/dashboard_home.png)
2. **Page 2 — Market Overview:** [`dashboard_market_overview.png`](../dashboard_mockups/dashboard_market_overview.png)
3. **Page 3 — Vehicle Analysis & Price Intelligence:** [`dashboard_vehicle_analysis.png`](../dashboard_mockups/dashboard_vehicle_analysis.png)
4. **Page 4 — Seller & Pricing Insights:** [`dashboard_seller_insights.png`](../dashboard_mockups/dashboard_seller_insights.png)

*(Note: All four images are UI/UX design mockups for Power BI Desktop implementation.)*

---

## 2. Global Design System

### Color Palette
| Role | Name | Hex Code | Application |
| :--- | :--- | :---: | :--- |
| **Primary** | Dark Navy | `#142B49` | Left navigation sidebar, main titles, primary data bars (`Dealer`, `Manual`, top models) |
| **Secondary** | Corporate Blue | `#245B86` | Active navigation button fill, secondary data series (`Individual`, standard segments) |
| **Accent** | Light Blue | `#438EAD` | Active navigation indicator bar, `Trustmark Dealer`, highlight bands (`Ages 6–9`) |
| **Background** | Light Grey | `#F4F6F9` | Canvas background, slicer dropdown boxes, insight pills |
| **Cards** | White | `#FFFFFF` | KPI & visual containers (`1 px` border `#DCE2EA`, `8 px` rounded corners) |
| **Positive** | Green | `#2E8B57` | Positive YoY change, top segment highlights (`MUV`, controlled premiums) |
| **Negative / Alert** | Orange | `#E87524` | Negative YoY change, `Automatic` contrast series, `Age 25 Anomaly` warning card |

### Typography (`Segoe UI`)
* **Dashboard Main Title:** `Segoe UI Bold`, `20 pt`, `#142B49`
* **Dashboard Subtitle:** `Segoe UI Regular`, `11 pt`, `#5C6F84`
* **KPI Value:** `Segoe UI Bold`, `22 pt` (`4-card` row) / `19 pt` (`6-card` row), `#142B49`
* **KPI & Slicer Label:** `Segoe UI Semibold`, `9 pt` uppercase, `#5C6F84`
* **Chart Title:** `Segoe UI Bold`, `12 pt`, `#142B49`
* **Axis & Data Labels:** `Segoe UI Regular / Semibold`, `9–10 pt`, `#142B49` / `#5C6F84`

---

## 3. Canvas Layout & Pixel Coordinates (`1920 × 1080` px)

| Component | `X` (px) | `Y` (px) | `Width` (px) | `Height` (px) | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Left Navigation Sidebar** | `0` | `0` | `260` | `1080` | Brand icon + 4 page buttons (`Home`, `Market Overview`, `Vehicle Analysis`, `Seller & Pricing Insights`) |
| **Top Header & Slicers Bar** | `284` | `20` | `1612` | `84` | Main title on left; 4 Dropdown Slicers on right (`W = 205` each on Pages 2–4) |
| **KPI Row (Page 1 — 6 Cards)** | `284` | `120` | `253` each | `106` | `18 px` horizontal gap |
| **KPI Row (Pages 2–4 — 4 Cards)** | `284` | `120` | `388` each | `106` | `20 px` horizontal gap |
| **Middle Visual Row (3 Cards)** | `284` | `244` | `522` each | `372` | `X = 284, 829, 1374` (`23 px` gap) |
| **Bottom Visual Row (3 Cards)** | `284` | `636` | `522` each | `386` | `X = 284, 829, 1374` (`23 px` gap) |
| **Bottom Visual Row (Page 1 — 2 Cards)** | `284` / `1104` | `636` | `796` / `792` | `386` | Seller Column Chart (left) + Executive Insights (right) |
| **Footer Bar** | `284` | `1034` | `1612` | `28` | Project metadata & page status |

---

## 4. Page-by-Page Visual Mapping

### Page 1: Home — Executive Overview (`dashboard_home.png`)
* **KPIs (6):** Total Listings (`15,229`), Median Listing Price (`₹5.56 L`), Average Listing Price (`₹7.75 L`), Average Vehicle Age (`6.0 Yrs`), Average Mileage (`54,888 km`), Total Vehicle Models (`120 Models`).
* **Visuals:** Listings by Body Type (*Donut*), Listings by Transmission (*Donut*), Top 10 Vehicle Models (*Clustered Bar*), Median Listing Price by Seller Type (*Clustered Column*), plus 3-point *Executive Insights* card.

### Page 2: Market Overview (`dashboard_market_overview.png`)
* **Slicers (4):** `Vehicle Model`, `Body Type`, `Transmission`, `Seller Type`.
* **KPIs (4):** Total Listings (`15,229`), Median Listing Price (`₹5.56 L`), Most Common Body Type (`Hatchback — 3,601`), Most Listed Vehicle Model (`Hyundai i20 — 898`).
* **Visuals (6):** Top 10 Vehicle Models by Listings (*Bar*), Median Price by Body Type (*Column*), Listings by Transmission (*Donut*), Listings by Seller Type (*Donut*), Median Price by Vehicle Model (*Bar*), Vehicle Age Distribution (*Column*).

### Page 3: Vehicle Analysis & Price Intelligence (`dashboard_vehicle_analysis.png`)
* **Slicers (4):** `Vehicle Age`, `Model`, `Transmission`, `Body Type`.
* **KPIs (4):** Average Vehicle Age (`6.04 Yrs`), Median Listing Price (`₹5.56 L`), Average Mileage (`54,888 km`), Highest Median Price Body Type (`MUV — ₹10.78 L`).
* **Visuals (6 + Anomaly Card):** Median Price by Vehicle Age (*Line*), YoY Price Change % (*Diverging Column*), **`[!] AGE 25 PRICE ANOMALY` Warning Card** (`₹10.00L` spike, `n = 1` sample size warning, flagged status), Price by Engine Size (*Column*), Mileage vs Listing Price (*Scatter*), Transmission × Body Type Price (*Clustered Column*), Vehicle Age vs Mileage (*Scatter*).

### Page 4: Seller & Pricing Insights (`dashboard_seller_insights.png`)
* **Slicers (4):** `Seller Type`, `Vehicle Model`, `Body Type`, `Transmission`.
* **KPIs (4):** Dealer Listings (`9,446`), Individual Listings (`5,610`), Dealer Median Price (`₹5.90 L`), Individual Median Price (`₹5.10 L`).
* **Visuals (6 + Summary Card):** Median Price by Seller (*Bar*), Avg Vehicle Age by Seller (*Column*), Median Mileage by Seller (*Column*), **Dealer vs. Individual Summary Card** (price, age, and mileage comparison), Price Distribution by Seller (*Box Plot*), Seller Type by Body Type (*100% Stacked Bar*), Seller Type by Transmission (*100% Stacked Bar*).
