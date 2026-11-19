"""
Data Cleaning and Preprocessing Pipeline
Brazilian E-Commerce Public Dataset by Olist
"""

import os
import pandas as pd
import numpy as np

def clean_all_data():
    raw_dir = 'data/raw'
    proc_dir = 'data/processed'
    os.makedirs(proc_dir, exist_ok=True)
    
    print("="*70)
    print("PHASE 2: DATA CLEANING & PREPROCESSING")
    print("="*70)
    
    # -------------------------------------------------------------
    # 1. CUSTOMERS
    # -------------------------------------------------------------
    print("\n[1/8] Processing Customers Dataset...")
    df_customers = pd.read_csv(os.path.join(raw_dir, 'olist_customers_dataset.csv'))
    # Clean city casing
    df_customers['customer_city'] = df_customers['customer_city'].str.title().str.strip()
    df_customers['customer_state'] = df_customers['customer_state'].str.upper().str.strip()
    df_customers.to_csv(os.path.join(proc_dir, 'customers_cleaned.csv'), index=False)
    print(f"  -> Saved customers_cleaned.csv: {len(df_customers):,} records")
    
    # -------------------------------------------------------------
    # 2. GEOLOCATION (DEDUPLICATION & CENTROID AGGREGATION)
    # -------------------------------------------------------------
    print("\n[2/8] Processing Geolocation Dataset...")
    df_geo = pd.read_csv(os.path.join(raw_dir, 'olist_geolocation_dataset.csv'))
    # Filter valid Brazilian bounding box: lat [-34, 6], lng [-74, -34]
    valid_lat = (df_geo['geolocation_lat'] >= -34.0) & (df_geo['geolocation_lat'] <= 6.0)
    valid_lng = (df_geo['geolocation_lng'] >= -74.0) & (df_geo['geolocation_lng'] <= -34.0)
    df_geo_clean = df_geo[valid_lat & valid_lng].copy()
    
    # Aggregate by zip_code_prefix to eliminate duplicate coordinate noise
    geo_agg = df_geo_clean.groupby('geolocation_zip_code_prefix').agg(
        geolocation_lat=('geolocation_lat', 'mean'),
        geolocation_lng=('geolocation_lng', 'mean'),
        geolocation_city=('geolocation_city', lambda x: x.mode()[0] if not x.empty else 'Unknown'),
        geolocation_state=('geolocation_state', lambda x: x.mode()[0] if not x.empty else 'Unknown')
    ).reset_index()
    geo_agg['geolocation_city'] = geo_agg['geolocation_city'].str.title().str.strip()
    geo_agg['geolocation_state'] = geo_agg['geolocation_state'].str.upper().str.strip()
    geo_agg.to_csv(os.path.join(proc_dir, 'geolocation_cleaned.csv'), index=False)
    print(f"  -> Deduplicated {len(df_geo):,} raw rows to {len(geo_agg):,} unique zip codes in geolocation_cleaned.csv")
    
    # -------------------------------------------------------------
    # 3. SELLERS
    # -------------------------------------------------------------
    print("\n[3/8] Processing Sellers Dataset...")
    df_sellers = pd.read_csv(os.path.join(raw_dir, 'olist_sellers_dataset.csv'))
    df_sellers['seller_city'] = df_sellers['seller_city'].str.title().str.strip()
    df_sellers['seller_state'] = df_sellers['seller_state'].str.upper().str.strip()
    df_sellers.to_csv(os.path.join(proc_dir, 'sellers_cleaned.csv'), index=False)
    print(f"  -> Saved sellers_cleaned.csv: {len(df_sellers):,} records")

    # -------------------------------------------------------------
    # 4. PRODUCTS & CATEGORY TRANSLATION
    # -------------------------------------------------------------
    print("\n[4/8] Processing Products & Category Translation...")
    df_products = pd.read_csv(os.path.join(raw_dir, 'olist_products_dataset.csv'))
    df_trans = pd.read_csv(os.path.join(raw_dir, 'product_category_name_translation.csv'))
    
    # Supplement translation dictionary for missing categories
    extra_trans = pd.DataFrame([
        {'product_category_name': 'pc_gamer', 'product_category_name_english': 'pc_gamer'},
        {'product_category_name': 'portateis_cozinha_e_preparadores_de_alimentos', 
         'product_category_name_english': 'small_appliances_food_preparation'}
    ])
    df_trans_full = pd.concat([df_trans, extra_trans], ignore_index=True).drop_duplicates(subset=['product_category_name'])
    
    # Merge translation
    df_products = df_products.merge(df_trans_full, on='product_category_name', how='left')
    
    # Handle missing categories
    df_products['product_category_name_english'] = df_products['product_category_name_english'].fillna('other_unknown')
    df_products['product_category_name'] = df_products['product_category_name'].fillna('outro_desconhecido')
    
    # Rename typo columns for professional schema
    df_products.rename(columns={
        'product_name_lenght': 'product_name_length',
        'product_description_lenght': 'product_description_length'
    }, inplace=True)
    
    # Calculate product volume in cm3
    df_products['product_volume_cm3'] = (
        df_products['product_length_cm'] * 
        df_products['product_height_cm'] * 
        df_products['product_width_cm']
    )
    
    # Clean category name format (replace underscores with spaces and title case for presentation)
    df_products['category_clean'] = (
        df_products['product_category_name_english']
        .str.replace('_', ' ')
        .str.title()
    )
    df_products.to_csv(os.path.join(proc_dir, 'products_cleaned.csv'), index=False)
    print(f"  -> Saved products_cleaned.csv: {len(df_products):,} records with 100% translated categories")

    # -------------------------------------------------------------
    # 5. ORDERS & DATE TIME FEATURE ENGINEERING
    # -------------------------------------------------------------
    print("\n[5/8] Processing Orders Dataset...")
    df_orders = pd.read_csv(os.path.join(raw_dir, 'olist_orders_dataset.csv'))
    
    date_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]
    for col in date_cols:
        df_orders[col] = pd.to_datetime(df_orders[col], errors='coerce')
        
    # Temporal features
    df_orders['order_purchase_year'] = df_orders['order_purchase_timestamp'].dt.year
    df_orders['order_purchase_month'] = df_orders['order_purchase_timestamp'].dt.month
    df_orders['order_purchase_year_month'] = df_orders['order_purchase_timestamp'].dt.to_period('M').astype(str)
    df_orders['order_purchase_date'] = df_orders['order_purchase_timestamp'].dt.date
    df_orders['order_purchase_day_name'] = df_orders['order_purchase_timestamp'].dt.day_name()
    df_orders['order_purchase_dayofweek'] = df_orders['order_purchase_timestamp'].dt.dayofweek
    df_orders['order_purchase_hour'] = df_orders['order_purchase_timestamp'].dt.hour
    
    # Delivery performance calculations (in fractional days)
    df_orders['delivery_lead_time_days'] = (
        df_orders['order_delivered_customer_date'] - df_orders['order_purchase_timestamp']
    ).dt.total_seconds() / 86400.0
    
    df_orders['estimated_delivery_days'] = (
        df_orders['order_estimated_delivery_date'] - df_orders['order_purchase_timestamp']
    ).dt.total_seconds() / 86400.0
    
    df_orders['delivery_delay_days'] = (
        df_orders['order_delivered_customer_date'] - df_orders['order_estimated_delivery_date']
    ).dt.total_seconds() / 86400.0
    
    # 1 if delivered after estimated date, 0 if on-time or early; None if not delivered
    df_orders['is_delayed'] = np.where(
        df_orders['order_delivered_customer_date'].notnull(),
        (df_orders['delivery_delay_days'] > 0).astype(int),
        np.nan
    )
    
    df_orders.to_csv(os.path.join(proc_dir, 'orders_cleaned.csv'), index=False)
    print(f"  -> Saved orders_cleaned.csv: {len(df_orders):,} records with delivery KPIs")

    # -------------------------------------------------------------
    # 6. ORDER ITEMS
    # -------------------------------------------------------------
    print("\n[6/8] Processing Order Items Dataset...")
    df_items = pd.read_csv(os.path.join(raw_dir, 'olist_order_items_dataset.csv'))
    df_items['shipping_limit_date'] = pd.to_datetime(df_items['shipping_limit_date'], errors='coerce')
    df_items['total_value'] = df_items['price'] + df_items['freight_value']
    df_items.to_csv(os.path.join(proc_dir, 'order_items_cleaned.csv'), index=False)
    print(f"  -> Saved order_items_cleaned.csv: {len(df_items):,} records")

    # -------------------------------------------------------------
    # 7. ORDER PAYMENTS
    # -------------------------------------------------------------
    print("\n[7/8] Processing Order Payments Dataset...")
    df_payments = pd.read_csv(os.path.join(raw_dir, 'olist_order_payments_dataset.csv'))
    
    # Remove 'not_defined' records and 0-value voucher tokens
    before_p = len(df_payments)
    df_payments = df_payments[(df_payments['payment_type'] != 'not_defined') & (df_payments['payment_value'] > 0)].copy()
    print(f"  -> Removed {before_p - len(df_payments)} invalid 0-value or 'not_defined' payment records")
    
    df_payments['payment_type_clean'] = (
        df_payments['payment_type']
        .str.replace('_', ' ')
        .str.title()
    )
    df_payments.to_csv(os.path.join(proc_dir, 'order_payments_cleaned.csv'), index=False)
    print(f"  -> Saved order_payments_cleaned.csv: {len(df_payments):,} records")

    # -------------------------------------------------------------
    # 8. ORDER REVIEWS
    # -------------------------------------------------------------
    print("\n[8/8] Processing Order Reviews Dataset...")
    df_reviews = pd.read_csv(os.path.join(raw_dir, 'olist_order_reviews_dataset.csv'))
    
    df_reviews['review_creation_date'] = pd.to_datetime(df_reviews['review_creation_date'], errors='coerce')
    df_reviews['review_answer_timestamp'] = pd.to_datetime(df_reviews['review_answer_timestamp'], errors='coerce')
    
    # Sort by answer timestamp descending and drop duplicates per (order_id, review_id) or order_id
    # Some orders have multiple review entries; keep the latest review per order for clean 1-to-1 order analytics
    df_reviews = df_reviews.sort_values(by='review_answer_timestamp', ascending=False)
    df_reviews_dedup = df_reviews.drop_duplicates(subset=['order_id'], keep='first').copy()
    
    df_reviews_dedup['review_comment_title'] = df_reviews_dedup['review_comment_title'].fillna('No Title')
    df_reviews_dedup['review_comment_message'] = df_reviews_dedup['review_comment_message'].fillna('No Comment')
    
    df_reviews_dedup.to_csv(os.path.join(proc_dir, 'order_reviews_cleaned.csv'), index=False)
    print(f"  -> Saved order_reviews_cleaned.csv: {len(df_reviews_dedup):,} unique-order review records")

    # -------------------------------------------------------------
    # 9. MASTER ANALYTICAL DATASET CREATION
    # -------------------------------------------------------------
    print("\n[9/9] Creating Master Analytical Dataset...")
    # Base: delivered orders joined with items, products, customers, sellers, reviews
    # Aggregate payments to order level to avoid Cartesian product
    order_pay_agg = df_payments.groupby('order_id').agg(
        payment_value=('payment_value', 'sum'),
        payment_installments_max=('payment_installments', 'max'),
        primary_payment_type=('payment_type_clean', lambda x: x.mode()[0] if not x.empty else 'Other'),
        payment_count=('payment_sequential', 'count')
    ).reset_index()

    # Join Order Items + Products
    items_prod = df_items.merge(
        df_products[['product_id', 'product_category_name_english', 'category_clean', 'product_weight_g', 'product_volume_cm3']],
        on='product_id',
        how='left'
    )

    # Join with Sellers
    items_prod_seller = items_prod.merge(
        df_sellers[['seller_id', 'seller_city', 'seller_state', 'seller_zip_code_prefix']],
        on='seller_id',
        how='left'
    )

    # Join with Orders
    master = items_prod_seller.merge(
        df_orders,
        on='order_id',
        how='inner'
    )

    # Join with Customers
    master = master.merge(
        df_customers,
        on='customer_id',
        how='inner'
    )

    # Join with Reviews
    master = master.merge(
        df_reviews_dedup[['order_id', 'review_score']],
        on='order_id',
        how='left'
    )

    # Join with Payments (Aggregated)
    master = master.merge(
        order_pay_agg,
        on='order_id',
        how='left'
    )

    master_path = os.path.join(proc_dir, 'master_ecommerce_cleaned.csv')
    master.to_csv(master_path, index=False)
    print(f"  -> Successfully generated master_ecommerce_cleaned.csv: {len(master):,} rows x {len(master.columns)} columns")
    print("\nALL DATA CLEANING TASKS COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    clean_all_data()
