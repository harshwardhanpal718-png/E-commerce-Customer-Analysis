"""
Exploratory Data Analysis (EDA) Pipeline
Computes all core statistical KPIs and generates portfolio-grade visualizations.
"""

import os
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), '.matplotlib_cache')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_eda():
    proc_dir = 'data/processed'
    viz_dir = 'visualizations'
    os.makedirs(viz_dir, exist_ok=True)
    
    # Configure plotting style
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 13
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['figure.dpi'] = 300
    
    color_palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    print("="*75)
    print("PHASE 3: EXPLORATORY DATA ANALYSIS (EDA)")
    print("="*75)
    
    # Load cleaned data
    df_master = pd.read_csv(os.path.join(proc_dir, 'master_ecommerce_cleaned.csv'))
    df_orders = pd.read_csv(os.path.join(proc_dir, 'orders_cleaned.csv'))
    df_customers = pd.read_csv(os.path.join(proc_dir, 'customers_cleaned.csv'))
    df_payments = pd.read_csv(os.path.join(proc_dir, 'order_payments_cleaned.csv'))
    df_reviews = pd.read_csv(os.path.join(proc_dir, 'order_reviews_cleaned.csv'))
    
    # Filter delivered orders for financial accuracy
    delivered_master = df_master[df_master['order_status'] == 'delivered'].copy()
    delivered_orders = df_orders[df_orders['order_status'] == 'delivered'].copy()
    
    # -------------------------------------------------------------
    # 1. CUSTOMER ANALYSIS
    # -------------------------------------------------------------
    print("\n--- 1. CUSTOMER ANALYSIS ---")
    total_unique_cust = df_customers['customer_unique_id'].nunique()
    total_cust_tokens = df_customers['customer_id'].nunique()
    
    # Orders per unique customer
    cust_order_counts = (
        delivered_orders.merge(df_customers, on='customer_id')
        .groupby('customer_unique_id')['order_id'].nunique()
    )
    repeat_customers = (cust_order_counts > 1).sum()
    repeat_rate = (repeat_customers / len(cust_order_counts)) * 100
    
    # Customer Lifetime Value (CLV = Total spend per customer on delivered orders)
    cust_spend = (
        delivered_master.groupby('customer_unique_id')
        .agg(
            total_spend=('price', 'sum'),
            total_freight=('freight_value', 'sum'),
            total_orders=('order_id', 'nunique'),
            total_items=('order_item_id', 'count')
        )
    )
    cust_spend['total_order_value'] = cust_spend['total_spend'] + cust_spend['total_freight']
    
    avg_customer_spend = cust_spend['total_order_value'].mean()
    median_customer_spend = cust_spend['total_order_value'].median()
    max_customer_spend = cust_spend['total_order_value'].max()
    
    print(f"Total Unique Customers: {total_unique_cust:,}")
    print(f"Repeat Customers: {repeat_customers:,} ({repeat_rate:.2f}%)")
    print(f"One-Time Customers: {len(cust_order_counts) - repeat_customers:,} ({100 - repeat_rate:.2f}%)")
    print(f"Average Customer Spend (CLV): R$ {avg_customer_spend:.2f}")
    print(f"Median Customer Spend: R$ {median_customer_spend:.2f}")
    print(f"Max Customer Spend: R$ {max_customer_spend:.2f}")
    
    # Customer geographic distribution
    top_states_cust = df_customers['customer_state'].value_counts().head(10)
    top_cities_cust = df_customers['customer_city'].value_counts().head(10)
    print("\nTop 5 Customer States:")
    for st, count in top_states_cust.head(5).items():
        print(f"  {st}: {count:,} ({count/len(df_customers)*100:.2f}%)")

    # -------------------------------------------------------------
    # 2. SALES ANALYSIS
    # -------------------------------------------------------------
    print("\n--- 2. SALES & FINANCIAL PERFORMANCE ---")
    total_product_revenue = delivered_master['price'].sum()
    total_freight_value = delivered_master['freight_value'].sum()
    total_gross_revenue = total_product_revenue + total_freight_value
    total_delivered_orders = delivered_orders['order_id'].nunique()
    
    # Average Order Value (AOV)
    order_values = delivered_master.groupby('order_id').agg(
        order_price=('price', 'sum'),
        order_freight=('freight_value', 'sum'),
        order_total=('total_value', 'sum')
    )
    aov_price = order_values['order_price'].mean()
    aov_total = order_values['order_total'].mean()
    
    print(f"Total Product Revenue: R$ {total_product_revenue:,.2f}")
    print(f"Total Freight Revenue: R$ {total_freight_value:,.2f}")
    print(f"Total Gross Revenue (Price + Freight): R$ {total_gross_revenue:,.2f}")
    print(f"Total Delivered Orders: {total_delivered_orders:,}")
    print(f"Average Order Value (Product Price Only): R$ {aov_price:.2f}")
    print(f"Average Order Value (Total With Freight): R$ {aov_total:.2f}")

    # Monthly Revenue Trend (2017 - Aug 2018 is core period)
    delivered_master['order_purchase_timestamp'] = pd.to_datetime(delivered_master['order_purchase_timestamp'])
    monthly_sales = (
        delivered_master.groupby('order_purchase_year_month')
        .agg(
            revenue=('price', 'sum'),
            freight=('freight_value', 'sum'),
            total_sales=('total_value', 'sum'),
            order_count=('order_id', 'nunique'),
            items_sold=('order_item_id', 'count')
        )
        .reset_index()
    )
    monthly_sales = monthly_sales[monthly_sales['order_purchase_year_month'] <= '2018-08'] # Complete full months
    
    print("\nRecent Monthly Sales Trajectory (Sample 2018):")
    for _, row in monthly_sales.tail(6).iterrows():
        print(f"  {row['order_purchase_year_month']}: Revenue R$ {row['revenue']:,.2f} | Orders: {row['order_count']:,}")

    # -------------------------------------------------------------
    # 3. PRODUCT CATEGORY ANALYSIS
    # -------------------------------------------------------------
    print("\n--- 3. PRODUCT CATEGORY ANALYSIS ---")
    cat_summary = (
        delivered_master.groupby('category_clean')
        .agg(
            revenue=('price', 'sum'),
            units_sold=('order_item_id', 'count'),
            order_count=('order_id', 'nunique'),
            avg_price=('price', 'mean')
        )
        .sort_values(by='revenue', ascending=False)
        .reset_index()
    )
    top_10_cats_rev = cat_summary.head(10)
    bottom_5_cats_rev = cat_summary.tail(5)
    
    print("Top 5 Revenue Generating Categories:")
    for _, row in top_10_cats_rev.head(5).iterrows():
        print(f"  {row['category_clean']}: R$ {row['revenue']:,.2f} ({row['units_sold']:,} units)")
        
    print("\nBottom 5 Categories by Revenue:")
    for _, row in bottom_5_cats_rev.iterrows():
        print(f"  {row['category_clean']}: R$ {row['revenue']:,.2f} ({row['units_sold']:,} units)")

    # -------------------------------------------------------------
    # 4. CUSTOMER BEHAVIOR & LOGISTICS
    # -------------------------------------------------------------
    print("\n--- 4. CUSTOMER BEHAVIOR & LOGISTICS PERFORMANCE ---")
    # Payment breakdown
    pay_summary = df_payments.groupby('payment_type_clean').agg(
        transaction_count=('payment_value', 'count'),
        total_payment=('payment_value', 'sum'),
        avg_installments=('payment_installments', 'mean')
    ).reset_index()
    pay_summary['pct_value'] = (pay_summary['total_payment'] / pay_summary['total_payment'].sum()) * 100
    print("Payment Preferences:")
    for _, row in pay_summary.sort_values('total_payment', ascending=False).iterrows():
        print(f"  {row['payment_type_clean']}: R$ {row['total_payment']:,.2f} ({row['pct_value']:.1f}%) | Avg Installments: {row['avg_installments']:.1f}")

    # Delivery performance
    avg_delivery_lead_time = delivered_orders['delivery_lead_time_days'].median()
    avg_estimated_lead_time = delivered_orders['estimated_delivery_days'].median()
    delayed_pct = (delivered_orders['is_delayed'] == 1).mean() * 100
    
    print(f"\nMedian Delivery Lead Time: {avg_delivery_lead_time:.1f} days")
    print(f"Median Estimated Delivery Time: {avg_estimated_lead_time:.1f} days")
    print(f"Delayed Deliveries Percentage: {delayed_pct:.2f}%")
    
    # Review score vs delay
    orders_review_delay = delivered_orders.merge(df_reviews[['order_id', 'review_score']], on='order_id', how='inner')
    delay_review_agg = orders_review_delay.groupby('is_delayed')['review_score'].mean()
    print(f"Avg Review Score for On-Time Deliveries: {delay_review_agg[0]:.2f} / 5.0")
    print(f"Avg Review Score for Delayed Deliveries: {delay_review_agg[1]:.2f} / 5.0")

    # =============================================================
    # GENERATING HIGH RESOLUTION VISUALIZATIONS
    # =============================================================
    print("\n--- GENERATING PUBLICATION-QUALITY FIGURES ---")
    
    # -------------------------------------------------------------
    # FIGURE 1: Monthly Revenue & Order Volume Trend
    # -------------------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(12, 6))
    x_labels = monthly_sales['order_purchase_year_month']
    x_indices = np.arange(len(x_labels))
    
    color_bar = '#1f77b4'
    color_line = '#ff7f0e'
    
    bars = ax1.bar(x_indices - 0.15, monthly_sales['revenue'] / 1e3, width=0.5, color=color_bar, alpha=0.85, label='Revenue (k R$)')
    ax1.set_xlabel('Purchase Month (Year-Month)', fontweight='bold')
    ax1.set_ylabel('Monthly Revenue (Thousand R$)', color=color_bar, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color_bar)
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(x_labels, rotation=45, ha='right')
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Secondary axis for order count
    ax2 = ax1.twinx()
    line = ax2.plot(x_indices, monthly_sales['order_count'], color=color_line, marker='o', linewidth=2.5, markersize=6, label='Order Volume')
    ax2.set_ylabel('Total Completed Orders', color=color_line, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color_line)
    ax2.grid(False)
    
    plt.title('Brazilian E-Commerce Monthly Revenue & Order Volume Growth (2017 - 2018)', pad=15)
    plt.tight_layout()
    fig_path1 = os.path.join(viz_dir, 'fig01_monthly_revenue_trend.png')
    plt.savefig(fig_path1)
    plt.close()
    print(f"  [Created] {fig_path1}")

    # -------------------------------------------------------------
    # FIGURE 2: Top 10 Product Categories by Revenue
    # -------------------------------------------------------------
    plt.figure(figsize=(11, 6))
    top10_plot = top_10_cats_rev.sort_values(by='revenue', ascending=True)
    bars = plt.barh(top10_plot['category_clean'], top10_plot['revenue'] / 1e3, color='#2b5c8f', edgecolor='black', alpha=0.85)
    
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 15, bar.get_y() + bar.get_height()/2, f'R$ {width:,.1f}k', 
                 va='center', ha='left', fontsize=9, fontweight='bold', color='#1a252f')
                 
    plt.title('Top 10 Product Categories by Total Revenue (BRL)', pad=15)
    plt.xlabel('Total Revenue (Thousand R$)', fontweight='bold')
    plt.ylabel('Product Category', fontweight='bold')
    plt.xlim(0, top10_plot['revenue'].max()/1e3 * 1.18)
    plt.tight_layout()
    fig_path2 = os.path.join(viz_dir, 'fig02_revenue_by_top_categories.png')
    plt.savefig(fig_path2)
    plt.close()
    print(f"  [Created] {fig_path2}")

    # -------------------------------------------------------------
    # FIGURE 3: Geographic Distribution of Customers by State
    # -------------------------------------------------------------
    plt.figure(figsize=(10, 5))
    top_states = df_customers['customer_state'].value_counts().head(10)
    bars = plt.bar(top_states.index, top_states.values, color='#34495e', edgecolor='black', alpha=0.85)
    
    for bar in bars:
        height = bar.get_height()
        pct = (height / len(df_customers)) * 100
        plt.text(bar.get_x() + bar.get_width()/2, height + 600, f'{pct:.1f}%', 
                 ha='center', va='bottom', fontsize=9, fontweight='bold')
                 
    plt.title('Top 10 Brazilian States by Customer Concentration (% of Total Base)', pad=15)
    plt.xlabel('Brazilian State Code', fontweight='bold')
    plt.ylabel('Number of Registered Customers', fontweight='bold')
    plt.ylim(0, top_states.max() * 1.12)
    plt.tight_layout()
    fig_path3 = os.path.join(viz_dir, 'fig03_geographic_distribution_states.png')
    plt.savefig(fig_path3)
    plt.close()
    print(f"  [Created] {fig_path3}")

    # -------------------------------------------------------------
    # FIGURE 4: Payment Method Breakdown
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Donut chart for transaction share
    colors = ['#2980b9', '#27ae60', '#e67e22', '#e74c3c']
    wedges, texts, autotexts = ax1.pie(
        pay_summary['total_payment'], 
        labels=pay_summary['payment_type_clean'],
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2)
    )
    for at in autotexts:
        at.set_color('white')
        at.set_weight('bold')
    ax1.set_title('Payment Method Share by Total Monetary Value', fontweight='bold')
    
    # Installments comparison bar chart
    cc_installments = df_payments[df_payments['payment_type'] == 'credit_card']['payment_installments'].value_counts().sort_index().head(10)
    ax2.bar(cc_installments.index, cc_installments.values, color='#2980b9', edgecolor='black', alpha=0.85)
    ax2.set_title('Credit Card Installment Distribution (1 to 10 Installments)', fontweight='bold')
    ax2.set_xlabel('Number of Installments', fontweight='bold')
    ax2.set_ylabel('Transaction Count', fontweight='bold')
    ax2.set_xticks(cc_installments.index)
    
    plt.tight_layout()
    fig_path5 = os.path.join(viz_dir, 'fig05_payment_method_breakdown.png')
    plt.savefig(fig_path5)
    plt.close()
    print(f"  [Created] {fig_path5}")

    # -------------------------------------------------------------
    # FIGURE 5: Purchase Hour & Day of Week Heatmap
    # -------------------------------------------------------------
    df_orders['order_purchase_timestamp'] = pd.to_datetime(df_orders['order_purchase_timestamp'])
    df_orders['day_of_week'] = df_orders['order_purchase_timestamp'].dt.day_name()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    pivot_heat = df_orders.pivot_table(
        index='day_of_week', 
        columns='order_purchase_hour', 
        values='order_id', 
        aggfunc='count'
    ).reindex(days_order)
    
    plt.figure(figsize=(13, 6))
    sns.heatmap(pivot_heat, cmap='YlGnBu', annot=False, fmt='d', cbar_kws={'label': 'Order Count'})
    plt.title('Customer Purchasing Heatmap: Day of Week vs. Hour of Day (Peak Shopping Windows)', pad=15)
    plt.xlabel('Hour of Purchase (24-Hour Military Time)', fontweight='bold')
    plt.ylabel('Day of Week', fontweight='bold')
    plt.tight_layout()
    fig_path6 = os.path.join(viz_dir, 'fig06_purchase_timing_heatmap.png')
    plt.savefig(fig_path6)
    plt.close()
    print(f"  [Created] {fig_path6}")

    # -------------------------------------------------------------
    # FIGURE 6: Delivery Delay Impact on Customer Reviews
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    
    # Review Score Distribution
    rev_counts = df_reviews['review_score'].value_counts().sort_index()
    rev_colors = ['#c0392b', '#d35400', '#f39c12', '#27ae60', '#2ecc71']
    bars = ax1.bar(rev_counts.index, rev_counts.values, color=rev_colors, edgecolor='black', alpha=0.9)
    ax1.set_title('Overall Customer Review Score Distribution (1-5 Stars)', fontweight='bold')
    ax1.set_xlabel('Review Score Rating', fontweight='bold')
    ax1.set_ylabel('Number of Reviews', fontweight='bold')
    for bar in bars:
        h = bar.get_height()
        pct = (h / len(df_reviews)) * 100
        ax1.text(bar.get_x() + bar.get_width()/2, h + 1000, f'{pct:.1f}%', ha='center', fontsize=9, fontweight='bold')
    ax1.set_ylim(0, rev_counts.max() * 1.12)
    
    # Review Score by Delivery Timeliness
    status_scores = [delay_review_agg[0], delay_review_agg[1]]
    ax2.bar(['On-Time / Early Delivery', 'Delayed Delivery'], status_scores, color=['#27ae60', '#c0392b'], edgecolor='black', width=0.5, alpha=0.85)
    ax2.set_title('Average Customer Review Score: On-Time vs Delayed Delivery', fontweight='bold')
    ax2.set_ylabel('Average Review Score (out of 5)', fontweight='bold')
    ax2.set_ylim(0, 5.5)
    for i, v in enumerate(status_scores):
        ax2.text(i, v + 0.15, f'{v:.2f} ★', ha='center', fontweight='bold', fontsize=12)
        
    plt.tight_layout()
    fig_path7 = os.path.join(viz_dir, 'fig07_delivery_performance_vs_reviews.png')
    plt.savefig(fig_path7)
    plt.close()
    print(f"  [Created] {fig_path7}")

    print("\nALL EDA TASKS & VISUALIZATIONS GENERATED SUCCESSFULLY!")

if __name__ == '__main__':
    run_eda()
