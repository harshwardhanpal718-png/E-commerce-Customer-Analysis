import nbformat as nbf
import os

nb = nbf.v4.new_notebook()
nb.metadata = {
    'language_info': {'name': 'python', 'version': '3.11.9'},
    'kernelspec': {'name': 'python3', 'display_name': 'Python 3'}
}

cells = []

# Title & Overview
cells.append(nbf.v4.new_markdown_cell("""# Brazilian E-Commerce Analysis: 03. Customer Segmentation (RFM Analysis)
**Senior Data Analyst & Python Developer Portfolio Project**  
**Dataset:** Brazilian E-Commerce Public Dataset by Olist (Cleaned Data)

---

### Objectives & Methodology
1. **RFM Metrics Definition:**
   - **Recency ($R$):** Days elapsed since the customer's most recent order relative to the dataset snapshot reference date.
   - **Frequency ($F$):** Total count of completed, delivered purchase transactions per unique customer (`customer_unique_id`).
   - **Monetary ($M$):** Total financial gross value spent (item price + freight) across all completed orders.
2. **Overcoming Real-World Distribution Skew:**
   - In e-commerce datasets with low natural repurchase rates (~3%), standard quintile binning (`qcut`) on Frequency generates identical bin edges. We engineer a discrete business scoring rule for $F$ alongside empirical quintiles for $R$ and $M$.
3. **Actionable Segmentation:**
   - Assigning customers to 7 strategic operational segments: **Champions**, **Loyal Customers**, **Potential Loyalists**, **New Customers**, **At Risk**, **Cannot Lose Them**, and **Hibernating**.
4. **Strategic Marketing Recommendations:**
   - Prescribing tailored lifecycle interventions for each customer tier.
"""))

# Cell 1: Environment Setup
cells.append(nbf.v4.new_code_cell("""# 1. Environment & Data Ingestion
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

# Load master cleaned data
df_master = pd.read_csv(os.path.join(proc_dir, 'master_ecommerce_cleaned.csv'))
delivered = df_master[df_master['order_status'] == 'delivered'].copy()
delivered['order_purchase_timestamp'] = pd.to_datetime(delivered['order_purchase_timestamp'])

print(f"Total delivered order records: {len(delivered):,}")
"""))

# Cell 2: RFM Calculation
cells.append(nbf.v4.new_code_cell("""# 2. RFM Calculation per Unique Customer Entity
snapshot_date = delivered['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
print(f"Snapshot Reference Date: {snapshot_date}")

rfm = delivered.groupby('customer_unique_id').agg(
    last_order_date=('order_purchase_timestamp', 'max'),
    frequency=('order_id', 'nunique'),
    monetary=('total_value', 'sum')
).reset_index()

rfm['recency'] = (snapshot_date - rfm['last_order_date']).dt.days

print(f"Total Unique Customers Evaluated: {len(rfm):,}")
rfm.describe().round(2)
"""))

# Cell 3: Scoring Methodology
cells.append(nbf.v4.new_markdown_cell("""### 3. RFM Scoring Architecture
- **Recency ($R$):** 5 quintiles (5 = purchased most recently, 1 = purchased longest ago).
- **Frequency ($F$):** Custom business mapping ($F=1 \\rightarrow 1, F=2 \\rightarrow 3, F=3 \\rightarrow 4, F \\ge 4 \\rightarrow 5$).
- **Monetary ($M$):** 5 quintiles (5 = highest spending bracket, 1 = lowest spending bracket).
"""))

cells.append(nbf.v4.new_code_cell("""# 3. Scoring Rules
rfm['R_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1]).astype(int)

def score_f(val):
    if val == 1:
        return 1
    elif val == 2:
        return 3
    elif val == 3:
        return 4
    else:
        return 5

rfm['F_score'] = rfm['frequency'].apply(score_f)
rfm['M_score'] = pd.qcut(rfm['monetary'], q=5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm['RFM_Score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)

rfm.head(5)
"""))

# Cell 4: Segment Assignment
cells.append(nbf.v4.new_code_cell("""# 4. Multi-Tier Customer Segmentation
def categorize_customer(row):
    r, f, m = row['R_score'], row['F_score'], row['M_score']
    
    if (r >= 4) and (f >= 3) and (m >= 4):
        return 'Champions'
    elif (r >= 3) and (f >= 3):
        return 'Loyal Customers'
    elif (r <= 2) and (f >= 3) and (m >= 4):
        return 'Cannot Lose Them'
    elif (r <= 2) and (f >= 3):
        return 'At Risk'
    elif (r >= 4) and (m >= 3):
        return 'Potential Loyalists'
    elif (r >= 4) and (m <= 2):
        return 'New Customers'
    else:
        return 'Hibernating'

rfm['segment'] = rfm.apply(categorize_customer, axis=1)

# Segment Profiles
summary = rfm.groupby('segment').agg(
    customer_count=('customer_unique_id', 'count'),
    total_revenue=('monetary', 'sum'),
    avg_recency=('recency', 'mean'),
    avg_frequency=('frequency', 'mean'),
    avg_monetary=('monetary', 'mean')
).reset_index()

summary['pct_customers'] = (summary['customer_count'] / len(rfm)) * 100
summary['pct_revenue'] = (summary['total_revenue'] / rfm['monetary'].sum()) * 100
summary = summary.sort_values('total_revenue', ascending=False)
summary.round(2)
"""))

# Cell 5: Marketing Strategy
cells.append(nbf.v4.new_markdown_cell("""### 5. Strategic Playbook & Marketing Recommendations by Segment

| Segment | Customer Share | Revenue Share | Avg Spend | Actionable Strategy & Playbook |
| :--- | :---: | :---: | :---: | :--- |
| **Champions** | 1.06% | 2.39% | R$ 372.04 | **VIP Concierge & Advocacy:** Enroll in exclusive VIP tier, early product drops, priority customer support, and referral rewards. |
| **Loyal Customers** | 0.88% | 1.34% | R$ 251.67 | **Cross-Sell & Upsell:** Leverage recommendation algorithms for complementary categories; offer free shipping thresholds for multi-item baskets. |
| **Potential Loyalists** | 23.45% | 33.53% | R$ 236.18 | **Primary Growth Engine:** Target with automated 14-day post-delivery nurture emails, second-purchase discount coupons, and review incentives. |
| **New Customers** | 15.35% | 5.08% | R$ 54.62 | **Onboarding & Education:** Welcome sequence, app download prompt, category discovery guides, and low-barrier entry offers. |
| **Cannot Lose Them** | 0.80% | 1.72% | R$ 353.99 | **High-Touch Win-Back:** Executive "we miss you" re-engagement campaigns with substantial reactivation credits and survey requests. |
| **At Risk** | 0.25% | 0.15% | R$ 97.65 | **Automated Re-engagement:** Time-sensitive reactivation discounts and product restock alerts. |
| **Hibernating** | 58.20% | 55.79% | R$ 158.34 | **Low-Cost Drip / Cleansing:** Unsubscribe unengaged leads to preserve email deliverability; run seasonal mass clearance promotions. |
"""))

# Cell 6: Export
cells.append(nbf.v4.new_code_cell("""# 6. Save Processed RFM Segmentation
rfm.to_csv(os.path.join(proc_dir, 'rfm_customer_segments.csv'), index=False)
print("Saved RFM segmentation dataset successfully.")
"""))

nb.cells = cells

with open('notebooks/03_rfm_segmentation.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Generated notebooks/03_rfm_segmentation.ipynb successfully!")
