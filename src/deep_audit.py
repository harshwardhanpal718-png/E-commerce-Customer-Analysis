import pandas as pd
import numpy as np

# Load tables
customers = pd.read_csv('data/raw/olist_customers_dataset.csv')
orders = pd.read_csv('data/raw/olist_orders_dataset.csv')
items = pd.read_csv('data/raw/olist_order_items_dataset.csv')
payments = pd.read_csv('data/raw/olist_order_payments_dataset.csv')
reviews = pd.read_csv('data/raw/olist_order_reviews_dataset.csv')
products = pd.read_csv('data/raw/olist_products_dataset.csv')
translation = pd.read_csv('data/raw/product_category_name_translation.csv')

print("--- ORDER STATUSES ---")
print(orders['order_status'].value_counts())

print("\n--- ORDER DATE RANGE ---")
orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
print(f"Min purchase date: {orders['order_purchase_timestamp'].min()}")
print(f"Max purchase date: {orders['order_purchase_timestamp'].max()}")

print("\n--- CUSTOMER COUNTS ---")
print(f"Total order-customer tokens (customer_id): {customers['customer_id'].nunique():,}")
print(f"Total distinct customers (customer_unique_id): {customers['customer_unique_id'].nunique():,}")

orders_per_cust = customers.groupby('customer_unique_id').size()
repeat_cust = (orders_per_cust > 1).sum()
print(f"Customers with >1 orders in customer table: {repeat_cust:,} ({repeat_cust/len(orders_per_cust)*100:.2f}%)")

print("\n--- PAYMENT TYPES ---")
print(payments['payment_type'].value_counts())
print(f"Payment value min: {payments['payment_value'].min()}, max: {payments['payment_value'].max()}, sum: {payments['payment_value'].sum():,.2f}")

print("\n--- REVIEW SCORES ---")
print(reviews['review_score'].value_counts().sort_index())

print("\n--- PRODUCT CATEGORIES ---")
missing_cats = products['product_category_name'].isnull().sum()
print(f"Missing category in products: {missing_cats}")
translated_cats = set(translation['product_category_name'])
product_cats = set(products['product_category_name'].dropna())
untranslated = product_cats - translated_cats
print(f"Categories without English translation: {len(untranslated)} -> {untranslated}")

print("\n--- ORDER ITEMS PRICING ---")
print(f"Item price min: {items['price'].min()}, max: {items['price'].max()}, median: {items['price'].median()}")
print(f"Freight value min: {items['freight_value'].min()}, max: {items['freight_value'].max()}, median: {items['freight_value'].median()}")
print(f"Total item price sum: {items['price'].sum():,.2f}")
print(f"Total freight sum: {items['freight_value'].sum():,.2f}")
