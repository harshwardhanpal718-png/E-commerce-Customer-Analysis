# Power BI Enterprise Data Model & Dashboard Architecture

## 1. Relational Star Schema Specification

The analytical model is structured as a **Kimball-style Dimensional Star Schema** optimized for high-speed DAX evaluation and cross-filtering.

```
                         +-----------------------+
                         |      dim_dates        |
                         +-----------------------+
                                     | 1
                                     |
                                     | *
+--------------------+   *       1   v   *       1   +---------------------+
|   dim_customers    |<----+   +-----------+   +---->|    dim_products     |
+--------------------+     |---| orders    |---|     +---------------------+
| customer_id (PK)   |     |   +-----------+   |     | product_id (PK)     |
| customer_unique_id |     |                   |     | category_clean      |
| customer_city      |     |                   |     | product_volume_cm3  |
| customer_state     |     |                   |     +---------------------+
+--------------------+     |                   |
                           |                   |
                           | 1                 | 1
                           |                   |
                           | *                 | *
                     +-----------+       +-------------------+
                     | payments  |       | order_items       |
                     +-----------+       +-------------------+
                     | order_id  |       | order_id (FK)     |
                     | pay_type  |       | product_id (FK)   |
                     | value     |       | seller_id (FK)    |
                     +-----------+       | price, freight    |
                                         +-------------------+
                                                   | *
                                                   |
                                                   | 1
                                         +-------------------+
                                         |    dim_sellers    |
                                         +-------------------+
                                         | seller_id (PK)    |
                                         | seller_state      |
                                         +-------------------+
```

### Table Relationships & Cardinality

| From Table (Fact / Child) | Foreign Key | To Table (Dim / Parent) | Primary Key | Cardinality | Cross Filter Direction |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `orders` | `customer_id` | `dim_customers` | `customer_id` | Many-to-One (`*:1`) | Single |
| `order_items` | `order_id` | `orders` | `order_id` | Many-to-One (`*:1`) | Single |
| `order_items` | `product_id` | `dim_products` | `product_id` | Many-to-One (`*:1`) | Single |
| `order_items` | `seller_id` | `dim_sellers` | `seller_id` | Many-to-One (`*:1`) | Single |
| `order_payments` | `order_id` | `orders` | `order_id` | Many-to-One (`*:1`) | Single |
| `order_reviews` | `order_id` | `orders` | `order_id` | One-to-One (`1:1`) | Both |
| `dim_customers` | `customer_unique_id` | `dim_rfm_segments` | `customer_unique_id` | Many-to-One (`*:1`) | Both |

---

## 2. 5-Page Dashboard Visual Specifications

### Page 1 – Executive Overview
- **Header KPI Cards**:
  - `Total Gross Revenue` (R$ 15.42M) with MoM trend sparkline
  - `Total Orders` (96,478)
  - `Total Unique Customers` (93,358)
  - `Average Order Value (AOV)` (R$ 159.83)
- **Visuals**:
  - *Monthly Revenue & Order Trajectory*: Combo visual (Column for Gross Revenue, Line for Order Volume).
  - *Top 10 Revenue Generating Categories*: Horizontal bar chart sorted by GMV with data callouts.
  - *Geographical Sales Concentration*: Brazilian State Filled Map / Shape Map shaded by total revenue.
- **Interactivity**: Date slicer (2017 - 2018), State dropdown, Order status filter.

### Page 2 – Customer Insights
- **Header KPI Cards**:
  - `Unique Customers` (96,096 total across lifecycle)
  - `Repeat Customer Rate %` (3.00%)
  - `Average Customer Spend (CLV)` (R$ 165.17)
  - `Median Customer Spend` (R$ 107.78)
- **Visuals**:
  - *New vs. Returning Customer Distribution*: Donut chart (97.0% One-time vs 3.0% Repeat).
  - *Customer Geographic Distribution*: Treemap of top customer states (SP, RJ, MG, RS, PR).
  - *Purchase Frequency Histogram*: Clustered column chart showing orders per customer.
  - *Customer Spending Deciles*: Box-and-whisker plot or percentile area chart showing monetary distribution.

### Page 3 – Customer Segmentation (RFM Analysis)
- **Header KPI Cards**:
  - `Potential Loyalists Count` (21,889 | 23.5% base | 33.5% revenue)
  - `Champions Count` (990 | 1.1% base | R$ 372.04 AOV)
  - `Cannot Lose Them Count` (750 | R$ 353.99 AOV)
  - `Hibernating Share` (58.2% customer base)
- **Visuals**:
  - *Customer Share vs. Revenue Share by Segment*: Side-by-side comparative horizontal bar chart.
  - *RFM Segment Scatter Plot*: Recency (X-axis) vs. Monetary (Y-axis, log scale) with bubble size by frequency.
  - *Segment Detail Matrix*: Interactive grid displaying Customer Count, Total GMV, Avg Spend, Avg Recency, and Recommended Campaign.
- **Interactivity**: Click segment to cross-filter customer table and view top customers in that segment.

### Page 4 – Product & Sales Analysis
- **Header KPI Cards**:
  - `Top Category GMV`: Health Beauty (R$ 1.23M)
  - `Top Volume Category`: Bed Bath Table (10,953 items)
  - `Average Item Price`: R$ 120.65
  - `Credit Card Monetary Share`: 78.5%
- **Visuals**:
  - *Category Performance Quadrant (Scatter)*: Units Sold (X) vs Total Revenue (Y), bubble sized by AOV.
  - *Payment Method Breakdown*: Donut chart of payment volume (Credit Card, Boleto, Voucher, Debit).
  - *Credit Card Installment Distribution*: Column chart showing frequency of 1 to 10 installments.
  - *Bottom 10 Underperforming Long-Tail Categories*: Horizontal bar chart highlighting catalog drag.

### Page 5 – Customer Retention & Logistics SLA
- **Header KPI Cards**:
  - `On-Time Delivery Rate %`: 91.89%
  - `Median Delivery Lead Time`: 10.2 Days (vs 23.2 Days Estimated)
  - `On-Time Delivery Review Score`: 4.29 ★
  - `Delayed Delivery Review Score`: 2.57 ★ (-1.72 ★ drop)
- **Visuals**:
  - *Monthly Cohort Retention Heatmap Matrix*: Cohort month (Y-axis) vs Activity Month Index 0 to 6 (X-axis) shaded by retention %.
  - *Customer Satisfaction vs. Delivery Delay*: Clustered column chart comparing star rating distribution for on-time vs delayed orders.
  - *Delivery Lead Time vs Estimated Lead Time by State*: Grouped bar chart revealing interstate freight bottlenecks.
  - *Weekly Shopping Heatmap*: Day of Week vs Hour of Day order intensity.
