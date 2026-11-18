import nbformat as nbf
import os

nb = nbf.v4.new_notebook()
nb.metadata = {
    'language_info': {'name': 'python', 'version': '3.11.9'},
    'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}
}

cells = []

# Title & Overview
cells.append(nbf.v4.new_markdown_cell("""# Brazilian E-Commerce Analysis: 01. Data Cleaning & Preprocessing Pipeline
**Senior Data Analyst & Python Developer Portfolio Project**  
**Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle)

---

### Project & Notebook Objectives
1. **Raw Data Ingestion & Audit:** Inspect all 9 relational tables comprising over 1.5 million records.
2. **Missing Value & Duplicate Analysis:** Identify structural nulls vs anomalies, eliminate duplicates.
3. **Data Type & Date-Time Transformation:** Parse all lifecycle timestamps, handle timezone considerations.
4. **Logistics & Delivery Feature Engineering:** Calculate delivery lead times, estimated durations, and delay flags.
5. **Entity Resolution:** Clarify `customer_id` (session token) vs `customer_unique_id` (human customer).
6. **Master Analytical Dataset Generation:** Merge relational tables without Cartesian explosion and export clean datasets to `data/processed/`.
"""))

# Cell 1: Environment Setup
cells.append(nbf.v4.new_code_cell("""# 1. Environment & Library Imports
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Set working directory to project root if running from notebooks folder
if os.path.basename(os.getcwd()) == 'notebooks':
    os.chdir('..')

raw_dir = 'data/raw'
proc_dir = 'data/processed'
os.makedirs(proc_dir, exist_ok=True)

print(f"Working directory: {os.getcwd()}")
print(f"Pandas version: {pd.__version__}")
"""))

# Cell 2: Raw Data Audit
cells.append(nbf.v4.new_code_cell("""# 2. Raw Dataset Ingestion and Surface Inspection
file_list = [
    'olist_customers_dataset.csv',
    'olist_orders_dataset.csv',
    'olist_order_items_dataset.csv',
    'olist_order_payments_dataset.csv',
    'olist_order_reviews_dataset.csv',
    'olist_products_dataset.csv',
    'olist_sellers_dataset.csv',
    'olist_geolocation_dataset.csv',
    'product_category_name_translation.csv'
]

audit_records = []
for fname in file_list:
    path = os.path.join(raw_dir, fname)
    df = pd.read_csv(path)
    audit_records.append({
        'Table Name': fname,
        'Row Count': len(df),
        'Column Count': len(df.columns),
        'Duplicate Rows': df.duplicated().sum(),
        'Missing Values': df.isnull().sum().sum()
    })

pd.DataFrame(audit_records)
"""))

# Cell 3: Customers Dataset
cells.append(nbf.v4.new_markdown_cell("""### 3. Customer Identity & Geolocation Cleaning
In the Olist dataset:
- `customer_id` is an order-level surrogate key assigned per transaction.
- `customer_unique_id` identifies the actual distinct human customer.
"""))

cells.append(nbf.v4.new_code_cell("""# 3. Clean Customers Dataset
df_customers = pd.read_csv(os.path.join(raw_dir, 'olist_customers_dataset.csv'))
print(f"Total Customer Records: {len(df_customers):,}")
print(f"Unique Customer IDs (Orders): {df_customers['customer_id'].nunique():,}")
print(f"Unique Individual Customers: {df_customers['customer_unique_id'].nunique():,}")

# Standardize text casings
df_customers['customer_city'] = df_customers['customer_city'].str.title().str.strip()
df_customers['customer_state'] = df_customers['customer_state'].str.upper().str.strip()

df_customers.to_csv(os.path.join(proc_dir, 'customers_cleaned.csv'), index=False)
df_customers.head(3)
"""))

# Cell 4: Geolocation Deduplication
cells.append(nbf.v4.new_markdown_cell("""### 4. Geolocation Spatial Deduplication & Centroids
The raw geolocation dataset contains ~1 million rows with high coordinate redundancy for the same postal codes.
We filter coordinates to Brazil's geographic bounding box and aggregate to the postal code prefix centroid.
"""))

cells.append(nbf.v4.new_code_cell("""# 4. Geolocation Centroid Calculation
df_geo = pd.read_csv(os.path.join(raw_dir, 'olist_geolocation_dataset.csv'))

# Bounding box for Brazil
valid_lat = (df_geo['geolocation_lat'] >= -34.0) & (df_geo['geolocation_lat'] <= 6.0)
valid_lng = (df_geo['geolocation_lng'] >= -74.0) & (df_geo['geolocation_lng'] <= -34.0)
df_geo_valid = df_geo[valid_lat & valid_lng]

# Aggregate by zip code prefix
geo_centroids = df_geo_valid.groupby('geolocation_zip_code_prefix').agg(
    geolocation_lat=('geolocation_lat', 'mean'),
    geolocation_lng=('geolocation_lng', 'mean'),
    geolocation_city=('geolocation_city', lambda x: x.mode()[0] if not x.empty else 'Unknown'),
    geolocation_state=('geolocation_state', lambda x: x.mode()[0] if not x.empty else 'Unknown')
).reset_index()

geo_centroids['geolocation_city'] = geo_centroids['geolocation_city'].str.title().str.strip()
geo_centroids['geolocation_state'] = geo_centroids['geolocation_state'].str.upper().str.strip()

geo_centroids.to_csv(os.path.join(proc_dir, 'geolocation_cleaned.csv'), index=False)
print(f"Raw Geolocation Records: {len(df_geo):,} -> Clean Postal Centroids: {len(geo_centroids):,}")
geo_centroids.head(3)
"""))

# Cell 5: Products & English Category Translation
cells.append(nbf.v4.new_markdown_cell("""### 5. Product Category Translation & Dimensional Cleaning
We translate Portuguese product category names to standardized English, fill missing categories, fix raw column typos (`lenght`), and calculate cubic volume.
"""))

cells.append(nbf.v4.new_code_cell("""# 5. Products Cleaning and Translation
df_products = pd.read_csv(os.path.join(raw_dir, 'olist_products_dataset.csv'))
df_trans = pd.read_csv(os.path.join(raw_dir, 'product_category_name_translation.csv'))

# Add manual translation for uncovered categories
extra_trans = pd.DataFrame([
    {'product_category_name': 'pc_gamer', 'product_category_name_english': 'pc_gamer'},
    {'product_category_name': 'portateis_cozinha_e_preparadores_de_alimentos', 
     'product_category_name_english': 'small_appliances_food_preparation'}
])
df_trans_full = pd.concat([df_trans, extra_trans], ignore_index=True).drop_duplicates('product_category_name')

# Merge translation
df_products = df_products.merge(df_trans_full, on='product_category_name', how='left')

# Impute missing categories
df_products['product_category_name_english'] = df_products['product_category_name_english'].fillna('other_unknown')
df_products['product_category_name'] = df_products['product_category_name'].fillna('outro_desconhecido')

# Rename column typos
df_products.rename(columns={
    'product_name_lenght': 'product_name_length',
    'product_description_lenght': 'product_description_length'
}, inplace=True)

# Volume calculation in cm3
df_products['product_volume_cm3'] = (
    df_products['product_length_cm'] * 
    df_products['product_height_cm'] * 
    df_products['product_width_cm']
)

df_products['category_clean'] = df_products['product_category_name_english'].str.replace('_', ' ').str.title()
df_products.to_csv(os.path.join(proc_dir, 'products_cleaned.csv'), index=False)
print(f"Products cleaned: {len(df_products):,} records with 0 missing English categories.")
df_products.head(3)
"""))

# Cell 6: Orders & Feature Engineering
cells.append(nbf.v4.new_markdown_cell("""### 6. Orders Lifecycle, Datetimes & Logistics Performance
We parse all 5 lifecycle timestamps and engineer logistics KPIs:
- `delivery_lead_time_days`: Actual time taken from order purchase to arrival at customer.
- `estimated_delivery_days`: Estimated duration promised to customer.
- `delivery_delay_days`: Variance from estimated delivery (positive = late).
- `is_delayed`: Binary indicator ($1$ for late delivery, $0$ otherwise).
"""))

cells.append(nbf.v4.new_code_cell("""# 6. Orders Datetime Parsing & Logistics KPIs
df_orders = pd.read_csv(os.path.join(raw_dir, 'olist_orders_dataset.csv'))

date_cols = [
    'order_purchase_timestamp', 'order_approved_at',
    'order_delivered_carrier_date', 'order_delivered_customer_date',
    'order_estimated_delivery_date'
]
for col in date_cols:
    df_orders[col] = pd.to_datetime(df_orders[col], errors='coerce')

# Date-time features
df_orders['order_purchase_year'] = df_orders['order_purchase_timestamp'].dt.year
df_orders['order_purchase_month'] = df_orders['order_purchase_timestamp'].dt.month
df_orders['order_purchase_year_month'] = df_orders['order_purchase_timestamp'].dt.to_period('M').astype(str)
df_orders['order_purchase_date'] = df_orders['order_purchase_timestamp'].dt.date
df_orders['order_purchase_day_name'] = df_orders['order_purchase_timestamp'].dt.day_name()
df_orders['order_purchase_hour'] = df_orders['order_purchase_timestamp'].dt.hour

# Logistics KPIs
df_orders['delivery_lead_time_days'] = (
    df_orders['order_delivered_customer_date'] - df_orders['order_purchase_timestamp']
).dt.total_seconds() / 86400.0

df_orders['estimated_delivery_days'] = (
    df_orders['order_estimated_delivery_date'] - df_orders['order_purchase_timestamp']
).dt.total_seconds() / 86400.0

df_orders['delivery_delay_days'] = (
    df_orders['order_delivered_customer_date'] - df_orders['order_estimated_delivery_date']
).dt.total_seconds() / 86400.0

df_orders['is_delayed'] = np.where(
    df_orders['order_delivered_customer_date'].notnull(),
    (df_orders['delivery_delay_days'] > 0).astype(int),
    np.nan
)

df_orders.to_csv(os.path.join(proc_dir, 'orders_cleaned.csv'), index=False)
print("Order status breakdown:")
print(df_orders['order_status'].value_counts())
print(f"Delayed deliveries rate: {df_orders['is_delayed'].mean()*100:.2f}% of delivered orders")
"""))

# Cell 7: Payments, Items, Reviews
cells.append(nbf.v4.new_code_cell("""# 7. Order Items, Payments & Reviews Processing
# Order Items
df_items = pd.read_csv(os.path.join(raw_dir, 'olist_order_items_dataset.csv'))
df_items['shipping_limit_date'] = pd.to_datetime(df_items['shipping_limit_date'], errors='coerce')
df_items['total_value'] = df_items['price'] + df_items['freight_value']
df_items.to_csv(os.path.join(proc_dir, 'order_items_cleaned.csv'), index=False)

# Order Payments (remove not_defined)
df_payments = pd.read_csv(os.path.join(raw_dir, 'olist_order_payments_dataset.csv'))
df_payments = df_payments[df_payments['payment_type'] != 'not_defined'].copy()
df_payments['payment_type_clean'] = df_payments['payment_type'].str.replace('_', ' ').str.title()
df_payments.to_csv(os.path.join(proc_dir, 'order_payments_cleaned.csv'), index=False)

# Order Reviews (deduplicate to latest review per order)
df_reviews = pd.read_csv(os.path.join(raw_dir, 'olist_order_reviews_dataset.csv'))
df_reviews['review_answer_timestamp'] = pd.to_datetime(df_reviews['review_answer_timestamp'], errors='coerce')
df_reviews_dedup = df_reviews.sort_values(by='review_answer_timestamp', ascending=False).drop_duplicates(subset=['order_id'], keep='first').copy()
df_reviews_dedup['review_comment_title'] = df_reviews_dedup['review_comment_title'].fillna('No Title')
df_reviews_dedup['review_comment_message'] = df_reviews_dedup['review_comment_message'].fillna('No Comment')
df_reviews_dedup.to_csv(os.path.join(proc_dir, 'order_reviews_cleaned.csv'), index=False)

# Sellers
df_sellers = pd.read_csv(os.path.join(raw_dir, 'olist_sellers_dataset.csv'))
df_sellers['seller_city'] = df_sellers['seller_city'].str.title().str.strip()
df_sellers['seller_state'] = df_sellers['seller_state'].str.upper().str.strip()
df_sellers.to_csv(os.path.join(proc_dir, 'sellers_cleaned.csv'), index=False)

print("Items, Payments, Reviews, and Sellers processed successfully.")
"""))

# Cell 8: Master Table
cells.append(nbf.v4.new_markdown_cell("""### 8. Master Analytical Table Creation
We aggregate payment data to the order level to avoid Cartesian multiplication, then perform relational joins to construct a comprehensive analytical dataset.
"""))

cells.append(nbf.v4.new_code_cell("""# 8. Relational Joins into Master Dataset
order_pay_agg = df_payments.groupby('order_id').agg(
    payment_value=('payment_value', 'sum'),
    payment_installments_max=('payment_installments', 'max'),
    primary_payment_type=('payment_type_clean', lambda x: x.mode()[0] if not x.empty else 'Other'),
    payment_count=('payment_sequential', 'count')
).reset_index()

master = (
    df_items
    .merge(df_products[['product_id', 'product_category_name_english', 'category_clean', 'product_weight_g', 'product_volume_cm3']], on='product_id', how='left')
    .merge(df_sellers[['seller_id', 'seller_city', 'seller_state', 'seller_zip_code_prefix']], on='seller_id', how='left')
    .merge(df_orders, on='order_id', how='inner')
    .merge(df_customers, on='customer_id', how='inner')
    .merge(df_reviews_dedup[['order_id', 'review_score']], on='order_id', how='left')
    .merge(order_pay_agg, on='order_id', how='left')
)

master_path = os.path.join(proc_dir, 'master_ecommerce_cleaned.csv')
master.to_csv(master_path, index=False)
print(f"Master Dataset Shape: {master.shape[0]:,} rows x {master.shape[1]} columns")
print(f"Exported to: {master_path}")
master.info()
"""))

nb.cells = cells

with open('notebooks/01_data_cleaning.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Generated notebooks/01_data_cleaning.ipynb successfully!")
