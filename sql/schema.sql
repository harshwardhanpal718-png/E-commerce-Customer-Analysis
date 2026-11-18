-- ============================================================================
-- E-COMMERCE CUSTOMER ANALYSIS: RELATIONAL DATABASE SCHEMA (DDL)
-- Database Dialect: PostgreSQL / ANSI SQL Standard (Compatible with SQLite & MySQL 8+)
-- Brazilian E-Commerce Public Dataset by Olist
-- ============================================================================

-- Drop tables in reverse foreign-key order if existing
DROP TABLE IF EXISTS order_reviews;
DROP TABLE IF EXISTS order_payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS geolocation;

-- ----------------------------------------------------------------------------
-- 1. GEOLOCATION TABLE (Postal Centroids)
-- ----------------------------------------------------------------------------
CREATE TABLE geolocation (
    geolocation_zip_code_prefix VARCHAR(10) PRIMARY KEY,
    geolocation_lat DECIMAL(10, 6) NOT NULL,
    geolocation_lng DECIMAL(10, 6) NOT NULL,
    geolocation_city VARCHAR(100) NOT NULL,
    geolocation_state CHAR(2) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. CUSTOMERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,          -- Per-order session token
    customer_unique_id VARCHAR(50) NOT NULL,      -- True human customer identifier
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100) NOT NULL,
    customer_state CHAR(2) NOT NULL
);

CREATE INDEX idx_customers_unique_id ON customers(customer_unique_id);
CREATE INDEX idx_customers_state ON customers(customer_state);

-- ----------------------------------------------------------------------------
-- 3. SELLERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10),
    seller_city VARCHAR(100) NOT NULL,
    seller_state CHAR(2) NOT NULL
);

-- ----------------------------------------------------------------------------
-- 4. PRODUCTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100),
    category_clean VARCHAR(100),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g DECIMAL(10, 2),
    product_length_cm DECIMAL(10, 2),
    product_height_cm DECIMAL(10, 2),
    product_width_cm DECIMAL(10, 2),
    product_volume_cm3 DECIMAL(12, 2)
);

CREATE INDEX idx_products_category ON products(category_clean);

-- ----------------------------------------------------------------------------
-- 5. ORDERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP NOT NULL,
    order_purchase_year INTEGER,
    order_purchase_month INTEGER,
    order_purchase_year_month VARCHAR(7),
    order_purchase_date DATE,
    order_purchase_day_name VARCHAR(15),
    order_purchase_dayofweek INTEGER,
    order_purchase_hour INTEGER,
    delivery_lead_time_days DECIMAL(10, 2),
    estimated_delivery_days DECIMAL(10, 2),
    delivery_delay_days DECIMAL(10, 2),
    is_delayed SMALLINT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_purchase_date ON orders(order_purchase_timestamp);

-- ----------------------------------------------------------------------------
-- 6. ORDER ITEMS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE order_items (
    order_id VARCHAR(50) NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,
    shipping_limit_date TIMESTAMP NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    freight_value DECIMAL(10, 2) NOT NULL,
    total_value DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

CREATE INDEX idx_items_product_id ON order_items(product_id);
CREATE INDEX idx_items_seller_id ON order_items(seller_id);

-- ----------------------------------------------------------------------------
-- 7. ORDER PAYMENTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE order_payments (
    order_id VARCHAR(50) NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(20) NOT NULL,
    payment_type_clean VARCHAR(30) NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE INDEX idx_payments_order_id ON order_payments(order_id);
CREATE INDEX idx_payments_type ON order_payments(payment_type_clean);

-- ----------------------------------------------------------------------------
-- 8. ORDER REVIEWS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE order_reviews (
    review_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP NOT NULL,
    review_answer_timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (order_id),  -- Enforced 1-to-1 deduplicated review per order
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE INDEX idx_reviews_score ON order_reviews(review_score);
