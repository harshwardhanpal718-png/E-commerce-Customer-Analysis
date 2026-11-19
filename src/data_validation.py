"""
Production Data Quality & Schema Integrity Validation Suite
Implements enterprise data quality assertions (similar to dbt tests & Great Expectations).
Validates primary keys, foreign keys, non-null constraints, domain ranges, and business logic.
"""

import os
import pandas as pd
import numpy as np

def run_data_validation():
    proc_dir = 'data/processed'
    print("="*80)
    print("ENTERPRISE DATA QUALITY VALIDATION (PRODUCTION ASSERTION TESTS)")
    print("="*80)
    
    test_results = []
    
    def log_test(test_name, status, details=""):
        badge = "[PASS]" if status else "[FAIL]"
        print(f"{badge:<8} | {test_name:<50} | {details}")
        test_results.append({'test': test_name, 'status': status, 'details': details})

    # 1. Check file existence
    tables = [
        'customers_cleaned.csv', 'orders_cleaned.csv', 'order_items_cleaned.csv',
        'order_payments_cleaned.csv', 'order_reviews_cleaned.csv', 'products_cleaned.csv',
        'sellers_cleaned.csv', 'geolocation_cleaned.csv', 'master_ecommerce_cleaned.csv',
        'rfm_customer_segments.csv'
    ]
    missing = [t for t in tables if not os.path.exists(os.path.join(proc_dir, t))]
    log_test("All 10 Processed Datasets Exist", len(missing) == 0, f"Missing: {missing}" if missing else "All files found")

    # Load tables
    df_customers = pd.read_csv(os.path.join(proc_dir, 'customers_cleaned.csv'))
    df_orders = pd.read_csv(os.path.join(proc_dir, 'orders_cleaned.csv'))
    df_items = pd.read_csv(os.path.join(proc_dir, 'order_items_cleaned.csv'))
    df_payments = pd.read_csv(os.path.join(proc_dir, 'order_payments_cleaned.csv'))
    df_reviews = pd.read_csv(os.path.join(proc_dir, 'order_reviews_cleaned.csv'))
    df_products = pd.read_csv(os.path.join(proc_dir, 'products_cleaned.csv'))
    df_rfm = pd.read_csv(os.path.join(proc_dir, 'rfm_customer_segments.csv'))

    # 2. Primary Key Uniqueness
    log_test("PK Uniqueness: customers.customer_id", df_customers['customer_id'].is_unique, f"Count: {len(df_customers):,}")
    log_test("PK Uniqueness: orders.order_id", df_orders['order_id'].is_unique, f"Count: {len(df_orders):,}")
    log_test("PK Uniqueness: products.product_id", df_products['product_id'].is_unique, f"Count: {len(df_products):,}")
    log_test("PK Uniqueness: rfm.customer_unique_id", df_rfm['customer_unique_id'].is_unique, f"Count: {len(df_rfm):,}")
    
    # Composite PK Uniqueness for Order Items
    item_pk_unique = not df_items.duplicated(subset=['order_id', 'order_item_id']).any()
    log_test("Composite PK: order_items (order_id, item_id)", item_pk_unique, f"Count: {len(df_items):,}")

    # 3. Referential Integrity (Foreign Keys)
    # Every order in items must exist in orders
    orphaned_order_items = set(df_items['order_id']) - set(df_orders['order_id'])
    log_test("FK Integrity: order_items -> orders", len(orphaned_order_items) == 0, f"Orphans: {len(orphaned_order_items)}")
    
    # Every order in payments must exist in orders
    orphaned_payments = set(df_payments['order_id']) - set(df_orders['order_id'])
    log_test("FK Integrity: order_payments -> orders", len(orphaned_payments) == 0, f"Orphans: {len(orphaned_payments)}")
    
    # Every order in reviews must exist in orders
    orphaned_reviews = set(df_reviews['order_id']) - set(df_orders['order_id'])
    log_test("FK Integrity: order_reviews -> orders", len(orphaned_reviews) == 0, f"Orphans: {len(orphaned_reviews)}")

    # 4. Domain & Range Checks (Financial & Metric Sanity)
    negative_prices = (df_items['price'] <= 0).sum()
    log_test("Financial Range: order_items.price > 0", negative_prices == 0, f"Invalid prices: {negative_prices}")
    
    negative_payments = (df_payments['payment_value'] <= 0).sum()
    log_test("Financial Range: payment_value > 0", negative_payments == 0, f"Invalid payments: {negative_payments}")
    
    valid_review_scores = df_reviews['review_score'].between(1, 5).all()
    log_test("Domain Validity: review_score BETWEEN 1 AND 5", valid_review_scores, "100% scores in [1, 5]")
    
    # 5. RFM Segment Completeness
    expected_segments = {'Champions', 'Loyal Customers', 'Potential Loyalists', 'New Customers', 'Cannot Lose Them', 'At Risk', 'Hibernating'}
    actual_segments = set(df_rfm['segment'].unique())
    log_test("RFM Segments: Exact 7 Business Tiers", actual_segments == expected_segments, f"Segments: {len(actual_segments)}")
    
    rfm_nulls = df_rfm[['recency', 'frequency', 'monetary', 'segment']].isnull().sum().sum()
    log_test("RFM Integrity: Zero Nulls in Core Features", rfm_nulls == 0, f"Null count: {rfm_nulls}")

    # Summary
    passed_tests = sum(1 for t in test_results if t['status'])
    total_tests = len(test_results)
    print("="*80)
    print(f"TEST RUN COMPLETED: {passed_tests}/{total_tests} ASSERTIONS PASSED ({passed_tests/total_tests*100:.1f}%)")
    print("="*80)
    
    return passed_tests == total_tests

if __name__ == '__main__':
    run_data_validation()
