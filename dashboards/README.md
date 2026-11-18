# Power BI Dashboard Implementation Guide

## Overview
This directory contains the full business intelligence asset suite for the **Brazilian E-Commerce Executive Dashboard**. It provides everything required to build, customize, or preview the enterprise dashboard in Microsoft Power BI Desktop or any web browser.

---

## Deliverables in this Directory

1. **`interactive_powerbi_dashboard.html`**:
   - A standalone, fully interactive 5-page Power BI Dashboard simulator.
   - Built with dark theme UI, Chart.js visualizations, live tab switching, KPI cards, and data tables.
   - Double-click to open in any web browser (Chrome, Edge, Firefox) for immediate presentation during interviews or reviews.

2. **`DAX_Measures_Library.dax`**:
   - Complete, verified production DAX measures formatted for Power BI Desktop.
   - Includes Core Financial KPIs (`Total Gross Revenue`, `AOV`), Time Intelligence (`MoM Growth %`), Customer Retention (`Repeat Customer Rate %`), Logistics SLA (`On-Time Delivery %`), and RFM segmentation values.

3. **`PowerBI_Data_Model_Architecture.md`**:
   - Comprehensive Kimball-style Star Schema documentation.
   - Entity relationship diagram (ERD), table cardinalities, foreign key mappings, and cross-filtering rules.
   - Detailed visual layout requirements for all 5 dashboard pages.

4. **`dark_theme.json`**:
   - Custom Obsidian Dark visual palette.
   - Can be imported directly into Power BI Desktop via `View -> Themes -> Browse for themes`.

---

## How to Load into Microsoft Power BI Desktop (.pbix)

1. **Launch Power BI Desktop** and click **Get Data -> Text/CSV**.
2. Select `data/processed/powerbi_reporting_mart.csv` (or load individual normalized tables from `data/processed/` following the schema in `PowerBI_Data_Model_Architecture.md`).
3. Click **Transform Data** in Power Query:
   - Ensure `order_purchase_timestamp` is set to **Date/Time**.
   - Ensure `price`, `freight_value`, and `total_value` are set to **Decimal Number**.
   - Click **Close & Apply**.
4. **Apply Theme**:
   - Navigate to the **View** ribbon $\rightarrow$ **Themes** dropdown $\rightarrow$ **Browse for themes**.
   - Select `dashboards/dark_theme.json`.
5. **Create DAX Measures**:
   - Right-click your fact table $\rightarrow$ **New Measure**, then copy-paste the measures from `dashboards/DAX_Measures_Library.dax`.
6. **Build the 5 Pages**:
   - **Page 1 (Executive Overview)**: Add KPI cards for Revenue, Orders, Customers, AOV; Monthly column/line trend chart; Top 10 categories bar chart; State sales table.
   - **Page 2 (Customer Insights)**: Add New vs Returning donut chart; State customer concentration chart; Frequency histogram; Spend deciles.
   - **Page 3 (Customer Segmentation)**: Add RFM customer share vs revenue share clustered bar chart; Recency vs Monetary scatter plot; Segment summary table.
   - **Page 4 (Product & Sales)**: Add Category revenue vs volume quadrant chart; Payment method donut chart; Credit card installments histogram.
   - **Page 5 (Customer Retention & SLA)**: Add Monthly cohort retention heatmap table; Delivery lead time vs estimated bar chart; Review score impact comparison (On-Time vs Delayed).
7. Save the project as `dashboards/powerbi_dashboard.pbix`.
