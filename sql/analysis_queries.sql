-- ============================================================================
-- E-COMMERCE CUSTOMER ANALYSIS: ADVANCED SQL BUSINESS QUERIES
-- Database Dialect: ANSI SQL / PostgreSQL / MySQL 8+ / SQLite
-- Brazilian E-Commerce Public Dataset by Olist
-- Demonstrating: CTEs, Window Functions (LAG, NTILE, SUM OVER), Joins, Aggregations
-- ============================================================================

-- ----------------------------------------------------------------------------
-- QUERY 1: TOTAL REVENUE & CORE EXECUTIVE FINANCIAL KPIS
-- Purpose: Calculate total gross merchandise value (GMV), item revenue, freight,
-- and total completed orders for delivered transactions.
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT o.order_id) AS total_delivered_orders,
    COUNT(DISTINCT c.customer_unique_id) AS total_unique_customers,
    SUM(oi.price) AS total_product_revenue,
    SUM(oi.freight_value) AS total_freight_value,
    SUM(oi.total_value) AS total_gross_revenue,
    ROUND(SUM(oi.price) / COUNT(DISTINCT o.order_id), 2) AS aov_product_only,
    ROUND(SUM(oi.total_value) / COUNT(DISTINCT o.order_id), 2) AS aov_with_freight
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered';


-- ----------------------------------------------------------------------------
-- QUERY 2: MONTHLY SALES TRENDS & MOM GROWTH (WINDOW FUNCTIONS)
-- Purpose: Track month-over-month revenue growth, order volume, and cumulative revenue
-- using LAG() and SUM() OVER() window functions.
-- ----------------------------------------------------------------------------
WITH monthly_metrics AS (
    SELECT 
        o.order_purchase_year_month AS year_month,
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(oi.order_item_id) AS total_items_sold,
        ROUND(SUM(oi.price), 2) AS monthly_revenue,
        ROUND(SUM(oi.total_value), 2) AS monthly_gross_sales
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_year_month BETWEEN '2017-01' AND '2018-08'
    GROUP BY o.order_purchase_year_month
)
SELECT 
    year_month,
    total_orders,
    total_items_sold,
    monthly_revenue,
    monthly_gross_sales,
    LAG(monthly_revenue, 1) OVER (ORDER BY year_month) AS prev_month_revenue,
    ROUND(
        (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY year_month)) / 
        LAG(monthly_revenue, 1) OVER (ORDER BY year_month) * 100.0, 
        2
    ) AS mom_revenue_growth_pct,
    ROUND(SUM(monthly_revenue) OVER (ORDER BY year_month), 2) AS cumulative_revenue
FROM monthly_metrics
ORDER BY year_month;


-- ----------------------------------------------------------------------------
-- QUERY 3: TOP 10 CUSTOMERS BY LIFETIME SPEND (CLV)
-- Purpose: Identify high-net-worth customers, their order frequency, and primary location.
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(oi.order_item_id) AS total_items_purchased,
    ROUND(SUM(oi.price), 2) AS total_item_spend,
    ROUND(SUM(oi.freight_value), 2) AS total_freight_paid,
    ROUND(SUM(oi.total_value), 2) AS total_lifetime_spend,
    ROUND(AVG(oi.total_value), 2) AS avg_item_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id, c.customer_city, c.customer_state
ORDER BY total_lifetime_spend DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- QUERY 4: TOP 10 PRODUCT CATEGORIES BY REVENUE & ORDER VOLUME
-- Purpose: Analyze top category performers, unit economics, and average item prices.
-- ----------------------------------------------------------------------------
SELECT 
    COALESCE(p.category_clean, 'Other / Unknown') AS category_name,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(oi.order_item_id) AS units_sold,
    ROUND(SUM(oi.price), 2) AS total_revenue,
    ROUND(SUM(oi.freight_value), 2) AS total_freight,
    ROUND(AVG(oi.price), 2) AS avg_unit_price,
    ROUND(
        SUM(oi.price) * 100.0 / SUM(SUM(oi.price)) OVER (), 
        2
    ) AS pct_of_total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY p.category_clean
ORDER BY total_revenue DESC
LIMIT 10;


-- ----------------------------------------------------------------------------
-- QUERY 5: REPEAT PURCHASE RATE (CTEs & AGGREGATION)
-- Purpose: Determine the exact proportion of single-order vs multi-order customers.
-- ----------------------------------------------------------------------------
WITH customer_order_frequencies AS (
    SELECT 
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
customer_classification AS (
    SELECT 
        customer_unique_id,
        order_count,
        CASE 
            WHEN order_count > 1 THEN 'Repeat Customer' 
            ELSE 'One-Time Customer' 
        END AS customer_type
    FROM customer_order_frequencies
)
SELECT 
    customer_type,
    COUNT(customer_unique_id) AS total_customers,
    ROUND(
        COUNT(customer_unique_id) * 100.0 / (SELECT COUNT(*) FROM customer_classification), 
        2
    ) AS customer_percentage
FROM customer_classification
GROUP BY customer_type;


-- ----------------------------------------------------------------------------
-- QUERY 6: AVERAGE ORDER VALUE (AOV) OVERALL & MONTHLY EVOLUTION
-- Purpose: Assess basket size dynamics and price stability over time.
-- ----------------------------------------------------------------------------
WITH order_aggregates AS (
    SELECT 
        o.order_id,
        o.order_purchase_year_month AS year_month,
        SUM(oi.price) AS order_item_total,
        SUM(oi.total_value) AS order_gross_total
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_year_month BETWEEN '2017-01' AND '2018-08'
    GROUP BY o.order_id, o.order_purchase_year_month
)
SELECT 
    year_month,
    COUNT(order_id) AS orders_count,
    ROUND(SUM(order_item_total), 2) AS monthly_item_revenue,
    ROUND(AVG(order_item_total), 2) AS monthly_aov_item_price,
    ROUND(AVG(order_gross_total), 2) AS monthly_aov_gross
FROM order_aggregates
GROUP BY year_month
ORDER BY year_month;


-- ----------------------------------------------------------------------------
-- QUERY 7: RFM CUSTOMER SEGMENTATION IN PURE SQL
-- Purpose: Calculate Recency, Frequency, and Monetary scores and segment customers
-- using CTEs, window functions (NTILE), and CASE statements.
-- ----------------------------------------------------------------------------
WITH max_date_cte AS (
    SELECT date(MAX(order_purchase_timestamp), '+1 day') AS snapshot_date
    FROM orders
    WHERE order_status = 'delivered'
),
rfm_base AS (
    SELECT 
        c.customer_unique_id,
        CAST(
            JULIANDAY((SELECT snapshot_date FROM max_date_cte)) - 
            JULIANDAY(MAX(o.order_purchase_timestamp)) AS INTEGER
        ) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(oi.total_value), 2) AS monetary
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id
),
rfm_scored AS (
    SELECT 
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        CASE 
            WHEN frequency = 1 THEN 1
            WHEN frequency = 2 THEN 3
            WHEN frequency = 3 THEN 4
            ELSE 5
        END AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
),
rfm_segmented AS (
    SELECT 
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        r_score,
        f_score,
        m_score,
        CASE 
            WHEN r_score >= 4 AND f_score >= 3 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
            WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 4 THEN 'Cannot Lose Them'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
            WHEN r_score >= 4 AND m_score >= 3 THEN 'Potential Loyalists'
            WHEN r_score >= 4 AND m_score <= 2 THEN 'New Customers'
            ELSE 'Hibernating'
        END AS customer_segment
    FROM rfm_scored
)
SELECT 
    customer_segment,
    COUNT(customer_unique_id) AS total_customers,
    ROUND(COUNT(customer_unique_id) * 100.0 / (SELECT COUNT(*) FROM rfm_segmented), 2) AS pct_customers,
    ROUND(SUM(monetary), 2) AS total_revenue,
    ROUND(SUM(monetary) * 100.0 / (SELECT SUM(monetary) FROM rfm_segmented), 2) AS pct_revenue,
    ROUND(AVG(monetary), 2) AS avg_monetary_spend,
    ROUND(AVG(recency_days), 1) AS avg_recency_days
FROM rfm_segmented
GROUP BY customer_segment
ORDER BY total_revenue DESC;


-- ----------------------------------------------------------------------------
-- QUERY 8: STATE-WISE SALES, FREIGHT-TO-REVENUE RATIO & CUSTOMER CONCENTRATION
-- Purpose: Analyze regional market penetration and freight cost burdens across Brazilian states.
-- ----------------------------------------------------------------------------
SELECT 
    c.customer_state,
    COUNT(DISTINCT c.customer_unique_id) AS total_customers,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.price), 2) AS product_revenue,
    ROUND(SUM(oi.freight_value), 2) AS freight_fees,
    ROUND(SUM(oi.total_value), 2) AS gross_sales,
    ROUND(
        SUM(oi.freight_value) * 100.0 / NULLIF(SUM(oi.price), 0), 
        2
    ) AS freight_to_revenue_pct,
    ROUND(
        SUM(oi.price) * 100.0 / SUM(SUM(oi.price)) OVER (), 
        2
    ) AS state_revenue_market_share_pct
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY product_revenue DESC;


-- ----------------------------------------------------------------------------
-- QUERY 9: PAYMENT METHOD ANALYSIS & FINANCING BEHAVIOR
-- Purpose: Evaluate payment rail preferences, installment frequencies, and volume share.
-- ----------------------------------------------------------------------------
SELECT 
    op.payment_type_clean AS payment_method,
    COUNT(op.payment_sequential) AS transaction_count,
    ROUND(SUM(op.payment_value), 2) AS total_monetary_volume,
    ROUND(
        SUM(op.payment_value) * 100.0 / SUM(SUM(op.payment_value)) OVER (), 
        2
    ) AS monetary_share_pct,
    ROUND(AVG(op.payment_value), 2) AS avg_transaction_value,
    ROUND(AVG(op.payment_installments), 1) AS avg_installments,
    MAX(op.payment_installments) AS max_installments
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY op.payment_type_clean
ORDER BY total_monetary_volume DESC;


-- ----------------------------------------------------------------------------
-- QUERY 10: CUSTOMER COHORT RETENTION ANALYSIS (MONTHLY COHORTS)
-- Purpose: Measure customer cohort survival and month-by-month retention dynamics
-- using first purchase cohort grouping and subsequent order activity.
-- ----------------------------------------------------------------------------
WITH first_purchases AS (
    SELECT 
        c.customer_unique_id,
        MIN(o.order_purchase_year_month) AS cohort_month
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_year_month BETWEEN '2017-01' AND '2017-12'
    GROUP BY c.customer_unique_id
),
customer_activities AS (
    SELECT 
        fp.cohort_month,
        c.customer_unique_id,
        o.order_purchase_year_month AS activity_month,
        (
            (CAST(SUBSTR(o.order_purchase_year_month, 1, 4) AS INT) - CAST(SUBSTR(fp.cohort_month, 1, 4) AS INT)) * 12 +
            (CAST(SUBSTR(o.order_purchase_year_month, 6, 2) AS INT) - CAST(SUBSTR(fp.cohort_month, 6, 2) AS INT))
        ) AS month_index
    FROM first_purchases fp
    JOIN customers c ON fp.customer_unique_id = c.customer_unique_id
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
)
SELECT 
    cohort_month,
    COUNT(DISTINCT CASE WHEN month_index = 0 THEN customer_unique_id END) AS cohort_size,
    COUNT(DISTINCT CASE WHEN month_index = 1 THEN customer_unique_id END) AS month_1,
    COUNT(DISTINCT CASE WHEN month_index = 2 THEN customer_unique_id END) AS month_2,
    COUNT(DISTINCT CASE WHEN month_index = 3 THEN customer_unique_id END) AS month_3,
    COUNT(DISTINCT CASE WHEN month_index = 4 THEN customer_unique_id END) AS month_4,
    COUNT(DISTINCT CASE WHEN month_index = 5 THEN customer_unique_id END) AS month_5,
    COUNT(DISTINCT CASE WHEN month_index = 6 THEN customer_unique_id END) AS month_6,
    ROUND(
        COUNT(DISTINCT CASE WHEN month_index = 1 THEN customer_unique_id END) * 100.0 /
        NULLIF(COUNT(DISTINCT CASE WHEN month_index = 0 THEN customer_unique_id END), 0), 
        2
    ) AS month_1_retention_pct
FROM customer_activities
GROUP BY cohort_month
ORDER BY cohort_month;
