import os
import sys

# Set writable matplotlib cache dir if needed
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), '.matplotlib_cache')

import pandas as pd
import numpy as np

raw_dir = 'data/raw'
files = [
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

print("="*80)
print("OLIST BRAZILIAN E-COMMERCE DATASET - INITIAL AUDIT")
print("="*80)

audit_summary = []

for f in files:
    path = os.path.join(raw_dir, f)
    if not os.path.exists(path):
        print(f"[MISSING] {f}")
        continue
    
    df = pd.read_csv(path)
    total_rows = len(df)
    total_cols = len(df.columns)
    dup_rows = df.duplicated().sum()
    null_cols = df.isnull().sum()
    cols_with_nulls = null_cols[null_cols > 0].to_dict()
    
    print(f"\nTABLE: {f}")
    print(f"Shape: {total_rows:,} rows x {total_cols} columns | Exact Duplicates: {dup_rows:,}")
    print(f"Columns: {list(df.columns)}")
    if cols_with_nulls:
        print("Columns with Nulls:")
        for col, cnt in cols_with_nulls.items():
            pct = (cnt / total_rows) * 100
            print(f"  - {col}: {cnt:,} ({pct:.2f}%)")
    else:
        print("No missing values found.")
        
    audit_summary.append({
        'table': f,
        'rows': total_rows,
        'cols': total_cols,
        'duplicates': dup_rows,
        'null_columns': len(cols_with_nulls)
    })

print("\n" + "="*80)
print("AUDIT SUMMARY TABLE")
print("="*80)
summary_df = pd.DataFrame(audit_summary)
print(summary_df.to_string(index=False))
