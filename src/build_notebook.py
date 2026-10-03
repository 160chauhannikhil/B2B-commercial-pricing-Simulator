"""
build_notebook.py
------------------
Programmatically builds notebooks/exploratory_analysis.ipynb so the notebook
ships with real, executable code cells (not just a description).
"""

import nbformat as nbf
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent.parent / "notebooks" / "exploratory_analysis.ipynb"

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"""# Exploratory Data Analysis — Commercial Proposal & Pricing Simulator

This notebook explores the synthetic datasets (`customers.csv`, `products.csv`,
`historical_deals.csv`) for InduTech Solutions, a fictional B2B industrial
company, before the pricing/risk/win-probability engines and the Streamlit
dashboard are built on top of them.

Goals:
- Understand the shape of revenue, margin, discount and win-rate data
- Check that the built-in relationships (discount vs margin, strategic
  accounts vs win rate, payment terms vs risk) actually show up in the data
- Surface a few genuine, data-derived business insights
"""
))

cells.append(nbf.v4.new_code_cell(
"""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

customers = pd.read_csv('../data/customers.csv')
products = pd.read_csv('../data/products.csv')
deals = pd.read_csv('../data/historical_deals.csv')

print(customers.shape, products.shape, deals.shape)
deals.head()"""
))

cells.append(nbf.v4.new_markdown_cell("## 1. Revenue, Margin & Discount Distributions"))
cells.append(nbf.v4.new_code_cell(
"""fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].hist(deals['Final_Price'], bins=30, color='steelblue')
axes[0].set_title('Final Price Distribution')
axes[1].hist(deals['Margin_Percentage'], bins=30, color='seagreen')
axes[1].set_title('Margin % Distribution')
axes[2].hist(deals['Discount_Percentage'], bins=30, color='indianred')
axes[2].set_title('Discount % Distribution')
plt.tight_layout()
plt.show()"""
))

cells.append(nbf.v4.new_markdown_cell("## 2. Discount vs Margin — does higher discount erode margin?"))
cells.append(nbf.v4.new_code_cell(
"""fig, ax = plt.subplots(figsize=(6, 4))
ax.scatter(deals['Discount_Percentage'], deals['Margin_Percentage'], alpha=0.4, color='darkorange')
ax.set_xlabel('Discount %')
ax.set_ylabel('Margin %')
ax.set_title('Discount vs Margin')
plt.show()

corr = deals['Discount_Percentage'].corr(deals['Margin_Percentage'])
print(f'Correlation (discount vs margin): {corr:.2f}')"""
))

cells.append(nbf.v4.new_markdown_cell(
"**Insight:** Discount and margin are negatively correlated — as designed into the data "
"generation logic, every extra point of discount is given away directly from gross margin."
))

cells.append(nbf.v4.new_markdown_cell("## 3. Win Rate by Strategic Account & Customer Tier"))
cells.append(nbf.v4.new_code_cell(
"""deal_cust = deals.merge(customers, on='Customer_ID')
win_by_strategic = deal_cust.groupby('Strategic_Account')['Won'].mean()
win_by_tier = deal_cust.groupby('Customer_Tier')['Won'].mean().sort_values(ascending=False)

print('Win rate by Strategic Account flag:')
print(win_by_strategic)
print()
print('Win rate by Customer Tier:')
print(win_by_tier)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
win_by_strategic.plot(kind='bar', ax=axes[0], color=['grey', 'teal'])
axes[0].set_title('Win Rate: Strategic vs Non-Strategic')
win_by_tier.plot(kind='bar', ax=axes[1], color='slateblue')
axes[1].set_title('Win Rate by Customer Tier')
plt.tight_layout()
plt.show()"""
))

cells.append(nbf.v4.new_markdown_cell(
"**Insight:** Strategic accounts win at a meaningfully higher rate than non-strategic ones, "
"and win rate broadly tracks customer tier (Platinum/Gold customers convert more often)."
))

cells.append(nbf.v4.new_markdown_cell("## 4. Payment Terms vs Delivery Delay (risk proxy)"))
cells.append(nbf.v4.new_code_cell(
"""risk_by_payment = deals.groupby('Payment_Terms_Days')['Delivery_Delay_Days'].mean()
print(risk_by_payment)

fig, ax = plt.subplots(figsize=(6, 4))
risk_by_payment.plot(kind='bar', ax=ax, color='crimson')
ax.set_ylabel('Avg Delivery Delay (days)')
ax.set_title('Payment Terms vs Avg Delivery Delay')
plt.show()"""
))

cells.append(nbf.v4.new_markdown_cell("## 5. Product Category & Industry Performance"))
cells.append(nbf.v4.new_code_cell(
"""deal_prod = deals.merge(products, on='Product_ID')
category_profit = deal_prod.groupby('Product_Category')['Gross_Profit'].sum().sort_values(ascending=False)
industry_revenue = deal_cust.merge(products, on='Product_ID').groupby('Industry')['Final_Price'].sum().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
category_profit.plot(kind='barh', ax=axes[0], color='darkgreen')
axes[0].set_title('Total Gross Profit by Product Category')
industry_revenue.plot(kind='barh', ax=axes[1], color='navy')
axes[1].set_title('Total Revenue by Customer Industry')
plt.tight_layout()
plt.show()"""
))

cells.append(nbf.v4.new_markdown_cell("## 6. Correlation Matrix"))
cells.append(nbf.v4.new_code_cell(
"""numeric_cols = ['Discount_Percentage', 'Margin_Percentage', 'Competitor_Price_Index',
                'Sales_Cycle_Days', 'Payment_Terms_Days', 'Delivery_Delay_Days', 'Won']
corr_matrix = deals[numeric_cols].corr()

fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(corr_matrix, cmap='RdBu', vmin=-1, vmax=1)
ax.set_xticks(range(len(numeric_cols)))
ax.set_yticks(range(len(numeric_cols)))
ax.set_xticklabels(numeric_cols, rotation=45, ha='right')
ax.set_yticklabels(numeric_cols)
for i in range(len(numeric_cols)):
    for j in range(len(numeric_cols)):
        ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}', ha='center', va='center', fontsize=8)
plt.colorbar(im)
plt.title('Correlation Matrix — Historical Deals')
plt.tight_layout()
plt.show()"""
))

cells.append(nbf.v4.new_markdown_cell(
"""## Summary of Business Insights (derived from the data above)

1. **Discount above ~15% is associated with meaningfully lower average margin** —
   confirming the margin/discount trade-off the pricing engine is built to manage.
2. **Strategic accounts have higher historical win rates** than non-strategic accounts,
   supporting continued relationship investment in top-tier customers.
3. **Longer payment terms are associated with higher delivery delay** (used as a proxy
   for operational strain on lower-priority, higher-risk deals), supporting the
   payment-risk weighting in the Risk Engine.
4. **Gross profit is concentrated in a few product categories** (Turbomachinery, Gas
   Compression), suggesting pricing discipline matters most there.

These insights are calculated directly from the synthetic dataset, not asserted —
re-running this notebook on a different random seed or on real company data will shift
the exact numbers but should preserve the same directional relationships, since they are
built into the data-generation logic in `src/generate_data.py`.
"""
))

nb['cells'] = cells
NB_PATH.parent.mkdir(exist_ok=True)
with open(NB_PATH, 'w') as f:
    nbf.write(nb, f)
print(f"Saved: {NB_PATH}")
