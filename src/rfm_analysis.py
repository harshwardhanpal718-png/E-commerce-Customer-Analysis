"""
RFM Customer Segmentation Pipeline
Brazilian E-Commerce Public Dataset by Olist
"""

import os
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), '.matplotlib_cache')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_rfm():
    proc_dir = 'data/processed'
    viz_dir = 'visualizations'
    os.makedirs(viz_dir, exist_ok=True)
    
    print("="*75)
    print("PHASE 4: RFM CUSTOMER SEGMENTATION")
    print("="*75)
    
    # Load cleaned data
    df_master = pd.read_csv(os.path.join(proc_dir, 'master_ecommerce_cleaned.csv'))
    
    # Filter strictly delivered orders for financial and customer relationship metrics
    delivered = df_master[df_master['order_status'] == 'delivered'].copy()
    delivered['order_purchase_timestamp'] = pd.to_datetime(delivered['order_purchase_timestamp'])
    
    # Reference Date: Day after max purchase timestamp
    snapshot_date = delivered['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
    print(f"Snapshot Reference Date: {snapshot_date}")
    
    # Calculate R, F, M per unique customer
    rfm_table = delivered.groupby('customer_unique_id').agg(
        last_order_date=('order_purchase_timestamp', 'max'),
        frequency=('order_id', 'nunique'),
        monetary=('total_value', 'sum')
    ).reset_index()
    
    rfm_table['recency'] = (snapshot_date - rfm_table['last_order_date']).dt.days
    
    print(f"Total Unique Customers Evaluated: {len(rfm_table):,}")
    print(f"Recency - Min: {rfm_table['recency'].min()} days | Median: {rfm_table['recency'].median():.0f} days | Max: {rfm_table['recency'].max()} days")
    print(f"Frequency - Min: {rfm_table['frequency'].min()} | Max: {rfm_table['frequency'].max()} | Repeat Count: {(rfm_table['frequency'] > 1).sum():,}")
    print(f"Monetary - Min: R$ {rfm_table['monetary'].min():.2f} | Median: R$ {rfm_table['monetary'].median():.2f} | Max: R$ {rfm_table['monetary'].max():,.2f}")
    
    # -------------------------------------------------------------
    # RFM SCORING METHODOLOGY
    # -------------------------------------------------------------
    # Recency: 5 quintiles (5 = most recent, 1 = least recent)
    rfm_table['R_score'] = pd.qcut(rfm_table['recency'], q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    
    # Frequency: Custom discrete binning (since 97% is 1, qcut produces identical bin edges)
    # 1 order -> 1, 2 orders -> 3, 3 orders -> 4, >=4 orders -> 5
    def score_frequency(f):
        if f == 1:
            return 1
        elif f == 2:
            return 3
        elif f == 3:
            return 4
        else:
            return 5
            
    rfm_table['F_score'] = rfm_table['frequency'].apply(score_frequency)
    
    # Monetary: 5 quintiles (5 = highest spend, 1 = lowest spend)
    rfm_table['M_score'] = pd.qcut(rfm_table['monetary'], q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    # Composite RFM Score
    rfm_table['RFM_Score_Str'] = (
        rfm_table['R_score'].astype(str) + 
        rfm_table['F_score'].astype(str) + 
        rfm_table['M_score'].astype(str)
    )
    
    # -------------------------------------------------------------
    # CUSTOMER SEGMENT DEFINITIONS
    # -------------------------------------------------------------
    def assign_segment(row):
        r = row['R_score']
        f = row['F_score']
        m = row['M_score']
        
        # Champions: Bought recently, buy often, spend high
        if (r >= 4) and (f >= 3) and (m >= 4):
            return 'Champions'
        # Loyal Customers: Consistent repeat buyers with good spend
        elif (r >= 3) and (f >= 3):
            return 'Loyal Customers'
        # Cannot Lose Them: Top historical spenders / repeat buyers who haven't returned in a long time
        elif (r <= 2) and (f >= 3) and (m >= 4):
            return 'Cannot Lose Them'
        # At Risk: Repeat buyers whose recency has slipped
        elif (r <= 2) and (f >= 3):
            return 'At Risk'
        # Potential Loyalists: Recent buyers with above-average spend (prime candidates for nurturing)
        elif (r >= 4) and (m >= 3):
            return 'Potential Loyalists'
        # New Customers: Recent buyers with modest/entry spend
        elif (r >= 4) and (m <= 2):
            return 'New Customers'
        # Hibernating: Long inactive, low-to-medium value single purchase
        else:
            return 'Hibernating'
            
    rfm_table['segment'] = rfm_table.apply(assign_segment, axis=1)
    
    # Segment-wise summary metrics
    segment_summary = rfm_table.groupby('segment').agg(
        customer_count=('customer_unique_id', 'count'),
        total_revenue=('monetary', 'sum'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        avg_monetary=('monetary', 'mean')
    ).reset_index()
    
    segment_summary['pct_customers'] = (segment_summary['customer_count'] / len(rfm_table)) * 100
    segment_summary['pct_revenue'] = (segment_summary['total_revenue'] / rfm_table['monetary'].sum()) * 100
    segment_summary = segment_summary.sort_values(by='total_revenue', ascending=False)
    
    print("\n" + "="*80)
    print("CUSTOMER SEGMENTATION SUMMARY TABLE")
    print("="*80)
    for _, row in segment_summary.iterrows():
        print(f"Segment: {row['segment']:<20} | Cust: {row['customer_count']:>6,} ({row['pct_customers']:>5.2f}%) | "
              f"Revenue: R$ {row['total_revenue']:>11,.2f} ({row['pct_revenue']:>5.2f}%) | "
              f"Avg Spend: R$ {row['avg_monetary']:>6.2f} | Avg Recency: {row['avg_recency']:>5.1f} d")
              
    # Export RFM Table
    rfm_csv_path = os.path.join(proc_dir, 'rfm_customer_segments.csv')
    rfm_table.to_csv(rfm_csv_path, index=False)
    print(f"\nSaved RFM table to: {rfm_csv_path}")
    
    # -------------------------------------------------------------
    # PUBLICATION-GRADE VISUALIZATIONS
    # -------------------------------------------------------------
    # Figure 9: Customer Count and Revenue Share by Segment
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    seg_sorted = segment_summary.sort_values(by='customer_count', ascending=True)
    palette_cust = ['#95a5a6', '#34495e', '#e74c3c', '#e67e22', '#3498db', '#2980b9', '#2ecc71']
    
    # Customers Count
    ax1.barh(seg_sorted['segment'], seg_sorted['customer_count'], color='#2c3e50', edgecolor='black', alpha=0.85)
    ax1.set_title('Customer Base Count by RFM Segment', fontweight='bold', pad=12)
    ax1.set_xlabel('Number of Unique Customers', fontweight='bold')
    for i, (cnt, pct) in enumerate(zip(seg_sorted['customer_count'], seg_sorted['pct_customers'])):
        ax1.text(cnt + 500, i, f'{cnt:,} ({pct:.1f}%)', va='center', fontsize=9, fontweight='bold')
    ax1.set_xlim(0, seg_sorted['customer_count'].max() * 1.25)
    
    # Revenue Share
    seg_rev_sorted = segment_summary.sort_values(by='total_revenue', ascending=True)
    ax2.barh(seg_rev_sorted['segment'], seg_rev_sorted['total_revenue'] / 1e3, color='#27ae60', edgecolor='black', alpha=0.85)
    ax2.set_title('Monetary Value Contribution by RFM Segment', fontweight='bold', pad=12)
    ax2.set_xlabel('Total Revenue (Thousand R$)', fontweight='bold')
    for i, (rev, pct) in enumerate(zip(seg_rev_sorted['total_revenue'], seg_rev_sorted['pct_revenue'])):
        ax2.text(rev/1e3 + 30, i, f'R$ {rev/1e3:,.1f}k ({pct:.1f}%)', va='center', fontsize=9, fontweight='bold')
    ax2.set_xlim(0, seg_rev_sorted['total_revenue'].max()/1e3 * 1.25)
    
    plt.tight_layout()
    fig_path9 = os.path.join(viz_dir, 'fig09_rfm_customer_segments_distribution.png')
    plt.savefig(fig_path9)
    plt.close()
    print(f"  [Created] {fig_path9}")

    # Figure 10: Recency vs Monetary Scatter with Segment Coloring
    plt.figure(figsize=(10, 6))
    sample_rfm = rfm_table.sample(n=min(5000, len(rfm_table)), random_state=42)
    sns.scatterplot(
        data=sample_rfm, 
        x='recency', 
        y='monetary', 
        hue='segment', 
        palette='Set1',
        alpha=0.6,
        s=40
    )
    plt.yscale('log')
    plt.title('Customer Recency vs. Monetary Spend (Log Scale) by RFM Segment', pad=15)
    plt.xlabel('Recency (Days Since Last Order)', fontweight='bold')
    plt.ylabel('Monetary Spend (Log Scale BRL)', fontweight='bold')
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    plt.tight_layout()
    fig_path10 = os.path.join(viz_dir, 'fig10_rfm_recency_monetary_scatter.png')
    plt.savefig(fig_path10)
    plt.close()
    print(f"  [Created] {fig_path10}")

    print("\nRFM SEGMENTATION COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    run_rfm()
