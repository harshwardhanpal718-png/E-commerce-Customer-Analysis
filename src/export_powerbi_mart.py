"""
Power BI Analytical Mart Exporter
Merges master cleaned orders with RFM customer segments and exports
a high-performance Power BI reporting dataset.
"""

import os
import pandas as pd

def export_powerbi_mart():
    proc_dir = 'data/processed'
    master_path = os.path.join(proc_dir, 'master_ecommerce_cleaned.csv')
    rfm_path = os.path.join(proc_dir, 'rfm_customer_segments.csv')
    
    print("Loading cleaned datasets for Power BI Mart...")
    df_master = pd.read_csv(master_path)
    df_rfm = pd.read_csv(rfm_path)
    
    # Merge RFM segment onto master line items via customer_unique_id
    mart = df_master.merge(
        df_rfm[['customer_unique_id', 'segment', 'R_score', 'F_score', 'M_score', 'recency', 'frequency', 'monetary']],
        on='customer_unique_id',
        how='left'
    )
    
    # Select optimized column subset for high performance Power BI visuals
    columns_to_keep = [
        'order_id', 'order_item_id', 'order_status',
        'order_purchase_timestamp', 'order_purchase_year', 'order_purchase_month',
        'order_purchase_year_month', 'order_purchase_date', 'order_purchase_day_name', 'order_purchase_hour',
        'customer_id', 'customer_unique_id', 'customer_city', 'customer_state',
        'seller_id', 'seller_city', 'seller_state',
        'product_id', 'category_clean', 'product_weight_g', 'product_volume_cm3',
        'price', 'freight_value', 'total_value',
        'primary_payment_type', 'payment_installments_max',
        'delivery_lead_time_days', 'estimated_delivery_days', 'delivery_delay_days', 'is_delayed',
        'review_score',
        'segment', 'R_score', 'F_score', 'M_score', 'recency', 'frequency', 'monetary'
    ]
    
    mart_clean = mart[[c for c in columns_to_keep if c in mart.columns]].copy()
    
    out_path = os.path.join(proc_dir, 'powerbi_reporting_mart.csv')
    mart_clean.to_csv(out_path, index=False)
    print(f"Successfully generated Power BI Reporting Mart: {len(mart_clean):,} rows x {len(mart_clean.columns)} columns")
    print(f"Saved to: {out_path}")

if __name__ == '__main__':
    export_powerbi_mart()
