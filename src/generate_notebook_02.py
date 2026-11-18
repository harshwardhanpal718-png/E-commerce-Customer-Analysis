import nbformat as nbf
import os

nb = nbf.v4.new_notebook()
nb.metadata = {
    'language_info': {'name': 'python', 'version': '3.11.9'},
    'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}
}

cells = []

# Title & Overview
cells.append(nbf.v4.new_markdown_cell("""# Brazilian E-Commerce Analysis: 02. Exploratory Data Analysis (EDA)
**Senior Data Analyst & Python Developer Portfolio Project**  
**Dataset:** Brazilian E-Commerce Public Dataset by Olist (Cleaned Data)

---

### Notebook Structure
1. **Executive Setup & Data Loading:** Ingesting master cleaned datasets.
2. **Customer Demographics & Concentration:** State and city distribution, repeat purchase rate, and customer lifetime value.
3. **Sales & Revenue Dynamics:** Gross merchandise value (GMV), monthly revenue trends, average order value (AOV).
4. **Product Category Diagnostics:** Revenue leaders, volume drivers, and underperforming catalog long-tails.
5. **Customer Purchasing Behaviors:** Hourly/daily shopping patterns, payment methods, and installment usage.
6. **Logistics & Customer Satisfaction:** Fulfillment lead times, SLA delay metrics, and customer review impact.
"""))

# Cell 1: Environment Setup
cells.append(nbf.v4.new_code_cell("""# 1. Environment & Library Setup
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

if os.path.basename(os.getcwd()) == 'notebooks':
    os.chdir('..')

proc_dir = 'data/processed'
viz_dir = 'visualizations'

# Styling
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (10, 5)
plt.rcParams['font.size'] = 10

# Load Cleaned Datasets
df_master = pd.read_csv(os.path.join(proc_dir, 'master_ecommerce_cleaned.csv'))
df_orders = pd.read_csv(os.path.join(proc_dir, 'orders_cleaned.csv'))
df_customers = pd.read_csv(os.path.join(proc_dir, 'customers_cleaned.csv'))
df_payments = pd.read_csv(os.path.join(proc_dir, 'order_payments_cleaned.csv'))
df_reviews = pd.read_csv(os.path.join(proc_dir, 'order_reviews_cleaned.csv'))

# Delivered orders cohort for revenue analysis
delivered_master = df_master[df_master['order_status'] == 'delivered'].copy()
delivered_orders = df_orders[df_orders['order_status'] == 'delivered'].copy()

print(f"Delivered Line Items: {len(delivered_master):,}")
print(f"Delivered Orders: {len(delivered_orders):,}")
"""))

# Cell 2: Customer Demographics & Repeat Rate
cells.append(nbf.v4.new_markdown_cell("""### 2. Customer Demographics, Repeat Purchase Rate & CLV
We evaluate customer geographic concentration and quantify the repeat purchase rate using the true identity key `customer_unique_id`.
"""))

cells.append(nbf.v4.new_code_cell("""# 2. Customer Base & Retention Analysis
total_unique_cust = df_customers['customer_unique_id'].nunique()

# Orders per unique customer
cust_orders = (
    delivered_orders.merge(df_customers, on='customer_id')
    .groupby('customer_unique_id')['order_id'].nunique()
)
repeat_cust = (cust_orders > 1).sum()
one_time_cust = len(cust_orders) - repeat_cust
repeat_pct = (repeat_cust / len(cust_orders)) * 100

print(f"Total Unique Customers: {total_unique_cust:,}")
print(f"Active Customers with Delivered Orders: {len(cust_orders):,}")
print(f"Repeat Customers: {repeat_cust:,} ({repeat_pct:.2f}%)")
print(f"One-Time Buyers: {one_time_cust:,} ({100 - repeat_pct:.2f}%)")

# Customer Spend / CLV
cust_clv = delivered_master.groupby('customer_unique_id')['total_value'].sum()
print(f"Average Customer Spend (CLV): R$ {cust_clv.mean():.2f}")
print(f"Median Customer Spend: R$ {cust_clv.median():.2f}")
print(f"Top 1% Customer Spend Threshold: R$ {cust_clv.quantile(0.99):.2f}")
"""))

# Cell 3: Geographic Distribution
cells.append(nbf.v4.new_code_cell("""# 3. Geographic Concentration by State
state_dist = df_customers['customer_state'].value_counts()
top_5_states_share = state_dist.head(5).sum() / len(df_customers) * 100

print(f"Top 5 States Share of Customers: {top_5_states_share:.2f}%")
print("\\nTop 10 States Breakdown:")
print(pd.DataFrame({'Customers': state_dist.head(10), 'Percentage': (state_dist.head(10)/len(df_customers)*100).round(2)}))
"""))

# Cell 4: Sales Performance & AOV
cells.append(nbf.v4.new_markdown_cell("""### 3. Sales Performance, Monthly Revenue & AOV
We analyze total merchandise value, freight fees, and Average Order Value (AOV).
"""))

cells.append(nbf.v4.new_code_cell("""# 4. Gross Revenue and Average Order Value
total_product_sales = delivered_master['price'].sum()
total_freight_fees = delivered_master['freight_value'].sum()
total_gmv = total_product_sales + total_freight_fees

order_totals = delivered_master.groupby('order_id').agg(
    order_price=('price', 'sum'),
    order_freight=('freight_value', 'sum'),
    order_total=('total_value', 'sum')
)

print(f"Total Product Sales: R$ {total_product_sales:,.2f}")
print(f"Total Freight Charged: R$ {total_freight_fees:,.2f} ({total_freight_fees/total_gmv*100:.1f}% of GMV)")
print(f"Total Gross Revenue: R$ {total_gmv:,.2f}")
print(f"Overall Average Order Value (AOV - Total): R$ {order_totals['order_total'].mean():.2f}")
print(f"Average Order Value (Item Price Only): R$ {order_totals['order_price'].mean():.2f}")
print(f"Median Order Total: R$ {order_totals['order_total'].median():.2f}")
"""))

# Cell 5: Monthly Trajectory
cells.append(nbf.v4.new_code_cell("""# 5. Monthly Revenue Trend
monthly_perf = (
    delivered_master.groupby('order_purchase_year_month')
    .agg(
        revenue=('price', 'sum'),
        total_sales=('total_value', 'sum'),
        orders=('order_id', 'nunique'),
        aov=('total_value', lambda x: x.sum() / x.index.nunique())
    )
    .reset_index()
)
# Filter complete months (Jan 2017 to Aug 2018)
monthly_perf = monthly_perf[(monthly_perf['order_purchase_year_month'] >= '2017-01') & 
                            (monthly_perf['order_purchase_year_month'] <= '2018-08')]
monthly_perf.tail(8)
"""))

# Cell 6: Product Category Leaders
cells.append(nbf.v4.new_markdown_cell("""### 4. Product Category Diagnostics
We analyze which categories drive revenue versus unit volume, and examine the underperforming tail.
"""))

cells.append(nbf.v4.new_code_cell("""# 6. Category Performance Analysis
cat_perf = delivered_master.groupby('category_clean').agg(
    revenue=('price', 'sum'),
    units=('order_item_id', 'count'),
    orders=('order_id', 'nunique'),
    avg_item_price=('price', 'mean')
).sort_values('revenue', ascending=False).reset_index()

print("Top 10 Categories by Revenue:")
print(cat_perf.head(10).to_string(index=False))

print("\\nBottom 5 Categories by Revenue:")
print(cat_perf.tail(5).to_string(index=False))
"""))

# Cell 7: Payment & Consumer Behavior
cells.append(nbf.v4.new_markdown_cell("""### 5. Consumer Behavior: Payment Methods & Installment Dynamics
Brazilian consumers rely heavily on installment financing (parcelamento).
"""))

cells.append(nbf.v4.new_code_cell("""# 7. Payment Type and Financing Preferences
pay_breakdown = df_payments.groupby('payment_type_clean').agg(
    transactions=('payment_value', 'count'),
    total_value=('payment_value', 'sum'),
    avg_installments=('payment_installments', 'mean')
).reset_index()
pay_breakdown['pct_share'] = (pay_breakdown['total_value'] / pay_breakdown['total_value'].sum()) * 100
pay_breakdown.sort_values('total_value', ascending=False)
"""))

# Cell 8: Logistics SLA & Review Scores
cells.append(nbf.v4.new_markdown_cell("""### 6. Logistics SLA & Customer Satisfaction Correlation
We measure delivery lead times and evaluate the statistical impact of delivery delays on review ratings.
"""))

cells.append(nbf.v4.new_code_cell("""# 8. Delivery SLA & Review Score Impact
lead_time_median = delivered_orders['delivery_lead_time_days'].median()
estimated_time_median = delivered_orders['estimated_delivery_days'].median()
delay_rate = (delivered_orders['is_delayed'] == 1).mean() * 100

orders_rev = delivered_orders.merge(df_reviews[['order_id', 'review_score']], on='order_id')
sla_review_comp = orders_rev.groupby('is_delayed').agg(
    avg_review_score=('review_score', 'mean'),
    median_review_score=('review_score', 'median'),
    orders_count=('order_id', 'count')
).reset_index()
sla_review_comp['delivery_status'] = sla_review_comp['is_delayed'].map({0.0: 'On-Time / Early', 1.0: 'Delayed'})

print(f"Median Actual Lead Time: {lead_time_median:.1f} days")
print(f"Median Estimated Delivery Window: {estimated_time_median:.1f} days")
print(f"Delivery Delay Rate: {delay_rate:.2f}%")
print("\\nReview Score by Delivery SLA:")
print(sla_review_comp[['delivery_status', 'avg_review_score', 'orders_count']])
"""))

nb.cells = cells

with open('notebooks/02_exploratory_analysis.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Generated notebooks/02_exploratory_analysis.ipynb successfully!")
