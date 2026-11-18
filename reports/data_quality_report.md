# Data Quality & Cleaning Report: Brazilian E-Commerce (Olist)

## Executive Summary
This Data Quality Report provides an exhaustive audit of data hygiene, schema integrity, missingness patterns, anomaly detection, and data transformations applied to the **Brazilian E-Commerce Public Dataset by Olist**. The raw dataset comprises **9 relational tables** totaling **1.5M+ records** spanning transactions from September 2016 through October 2018.

---

## 1. Initial Data Audit & Schema Overview

| Dataset File | Raw Record Count | Column Count | Primary Key / Grain | Missing Columns Identified | Initial Quality Status |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `olist_customers_dataset.csv` | 99,441 | 5 | `customer_id` (Order token) | None (0) | Clean |
| `olist_orders_dataset.csv` | 99,441 | 8 | `order_id` | 3 timestamp columns | Expected lifecycle nulls |
| `olist_order_items_dataset.csv` | 112,650 | 7 | `(order_id, order_item_id)` | None (0) | Clean |
| `olist_order_payments_dataset.csv` | 103,886 | 5 | `(order_id, payment_sequential)` | None (0) | 3 `not_defined` records |
| `olist_order_reviews_dataset.csv` | 99,224 | 7 | `review_id` / `order_id` | `title` (88.3%), `message` (58.7%) | Text optionality |
| `olist_products_dataset.csv` | 32,951 | 9 | `product_id` | 8 columns (category & specs) | 610 missing categories |
| `olist_sellers_dataset.csv` | 3,095 | 4 | `seller_id` | None (0) | Clean |
| `olist_geolocation_dataset.csv` | 1,000,163 | 5 | Zip code lat/lng readings | None (0) | High coordinate redundancy (261k exact duplicates) |
| `product_category_name_translation.csv` | 71 | 2 | `product_category_name` | None (0) | Missing 2 product categories |

---

## 2. Issues Detected and Resolution Matrix

### Issue 1: Customer Identification (`customer_id` vs `customer_unique_id`)
- **Diagnosis**: The Olist dataset maintains two customer keys:
  - `customer_id`: Unique per purchase session / order transaction (99,441 records).
  - `customer_unique_id`: Real-world human identity (96,096 distinct individuals).
- **Business Impact**: Grouping by `customer_id` produces a false 0% repeat purchase rate because each order creates a new `customer_id`.
- **Resolution**: All customer retention, frequency, Customer Lifetime Value (CLV), and RFM segmentation calculations strictly utilize `customer_unique_id` as the primary entity identifier.

### Issue 2: Redundant & Out-of-Bounds Geolocation Coordinates
- **Diagnosis**: `olist_geolocation_dataset.csv` contained 1,000,163 rows with 261,831 exact duplicate rows and thousands of repetitive coordinate points per postal code prefix, as well as coordinates falling outside Brazilian territorial boundaries (lat [-34, 6], lng [-74, -34]).
- **Business Impact**: Severe memory inflation and cartographic skew in Power BI maps.
- **Resolution**: Filtered to coordinates within Brazil's sovereign boundaries, then aggregated to the unique `geolocation_zip_code_prefix` centroid level using geometric mean for latitude and longitude and statistical mode for city and state. Reduced 1M rows to **19,010 clean, high-performance spatial points**.

### Issue 3: Incomplete Product Category Translation & Schema Typos
- **Diagnosis**: 
  - Two active categories in products (`pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`) were absent from the Kaggle translation dictionary.
  - 610 products possessed missing category names and dimensional specs.
  - Typographical errors existed in the raw schema: `product_name_lenght` and `product_description_lenght`.
- **Resolution**:
  - Imputed manual translations: `pc_gamer` $\rightarrow$ `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos` $\rightarrow$ `small_appliances_food_preparation`.
  - Imputed unassigned products to `other_unknown` (`outro_desconhecido`).
  - Corrected column spellings to `product_name_length` and `product_description_length`.
  - Computed volumetric metric: `product_volume_cm3 = product_length_cm * product_height_cm * product_width_cm`.

### Issue 4: Zero-Value Undefined Payment Records
- **Diagnosis**: `olist_order_payments_dataset.csv` included 3 records with `payment_type = 'not_defined'` and `payment_value = 0.00`.
- **Business Impact**: Causes erroneous payment method counts and creates zero-value financial anomalies.
- **Resolution**: Filtered out these 3 invalid placeholder rows, leaving 103,883 validated financial transactions.

### Issue 5: Multiple Reviews per Order
- **Diagnosis**: 99,224 review records across 98,673 distinct orders, indicating duplicate or sequential updated feedback submitted by consumers.
- **Business Impact**: One-to-many joins inflate order monetary totals and duplicate order line items.
- **Resolution**: Sorted by `review_answer_timestamp` in descending order and deduplicated on `order_id` (keeping the final customer review). Imputed null review titles and comments with `'No Title'` and `'No Comment'`.

### Issue 6: Order Lifecycle Timestamp Nulls
- **Diagnosis**:
  - `order_approved_at`: 160 missing
  - `order_delivered_carrier_date`: 1,783 missing
  - `order_delivered_customer_date`: 2,965 missing
- **Business Impact**: These reflect normal e-commerce lifecycle states (orders canceled before dispatch, currently in transit, or undergoing payment confirmation).
- **Resolution**: Retained rows for order funnel conversion analysis; created explicit delivery KPI flags (`is_delayed`, `delivery_lead_time_days`, `delivery_delay_days`) calculated strictly on completed deliveries.

---

## 3. Data Transformation & Feature Engineering

1. **Temporal Dimensions**:
   - `order_purchase_year`, `order_purchase_month`, `order_purchase_year_month` (`YYYY-MM`), `order_purchase_date`
   - `order_purchase_day_name`, `order_purchase_hour`
2. **Delivery Logistics Metrics**:
   - `delivery_lead_time_days`: Elapsed calendar days from purchase to customer delivery.
   - `estimated_delivery_days`: Estimated duration promised to customer at checkout.
   - `delivery_delay_days`: Difference between actual delivery and estimated delivery date (positive values represent late deliveries).
   - `is_delayed`: Binary indicator ($1$ = late delivery, $0$ = on-time / early delivery).
3. **Financial & Basket Metrics**:
   - `total_item_value`: Item `price` + `freight_value`.
   - Aggregated order payments: total order payment, maximum installments, and primary payment type.

---

## 4. Master Analytical Dataset Schema (`master_ecommerce_cleaned.csv`)

- **Grain**: One record per line item (`order_id`, `order_item_id`).
- **Total Volume**: 112,650 rows $\times$ 42 attributes.
- **Key Joins**:
  - `olist_order_items_dataset` (Core)
  - `olist_products_dataset` (via `product_id`)
  - `olist_sellers_dataset` (via `seller_id`)
  - `olist_orders_dataset` (via `order_id`)
  - `olist_customers_dataset` (via `customer_id`)
  - `olist_order_reviews_dataset` (via `order_id`, 1-to-1 deduplicated)
  - Aggregated order payments (via `order_id`, 1-to-1)

---

## 5. Certification & Data Quality Sign-Off
All preprocessed tables have been saved to `data/processed/` in standard UTF-8 CSV format and validated against relational constraints, zero unexpected nulls in core financial metrics, and verified data types.
