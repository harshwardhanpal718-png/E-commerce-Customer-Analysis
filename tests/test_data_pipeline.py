"""
CI/CD Pytest Suite for E-Commerce Data Pipeline
"""

import os
import pytest
import pandas as pd
import sqlite3

PROC_DIR = 'data/processed'

def test_processed_files_exist():
    expected_files = [
        'customers_cleaned.csv', 'orders_cleaned.csv', 'order_items_cleaned.csv',
        'order_payments_cleaned.csv', 'order_reviews_cleaned.csv', 'products_cleaned.csv',
        'sellers_cleaned.csv', 'geolocation_cleaned.csv', 'rfm_customer_segments.csv'
    ]
    for f in expected_files:
        assert os.path.exists(os.path.join(PROC_DIR, f)), f"Missing expected dataset: {f}"

def test_customers_primary_key():
    df = pd.read_csv(os.path.join(PROC_DIR, 'customers_cleaned.csv'))
    assert df['customer_id'].is_unique, "Customer ID must be unique"
    assert df['customer_unique_id'].nunique() > 90000, "Human unique customers count sanity check"

def test_financial_sanity():
    df_items = pd.read_csv(os.path.join(PROC_DIR, 'order_items_cleaned.csv'))
    assert (df_items['price'] > 0).all(), "All items must have positive price"
    assert (df_items['freight_value'] >= 0).all(), "Freight must be non-negative"

def test_rfm_segments_integrity():
    df_rfm = pd.read_csv(os.path.join(PROC_DIR, 'rfm_customer_segments.csv'))
    assert set(df_rfm['segment'].unique()) == {
        'Champions', 'Loyal Customers', 'Potential Loyalists', 'New Customers',
        'Cannot Lose Them', 'At Risk', 'Hibernating'
    }
    assert (df_rfm['recency'] >= 0).all()
    assert (df_rfm['frequency'] >= 1).all()
    assert (df_rfm['monetary'] > 0).all()

def test_sqlite_db_connectivity():
    db_path = 'data/ecommerce.db'
    assert os.path.exists(db_path), "SQLite database must exist"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE order_status = 'delivered'")
    delivered_count = cur.fetchone()[0]
    conn.close()
    assert delivered_count == 96478, f"Expected 96,478 delivered orders, got {delivered_count}"
