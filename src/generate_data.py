"""
generate_data.py
-----------------
Generates realistic synthetic datasets for InduTech Solutions, a fictional
B2B industrial equipment & services company.

Produces:
    data/customers.csv          (100 customers)
    data/products.csv           (30 products)
    data/historical_deals.csv   (500 historical deals)

The relationships between variables are deliberately built in (not pure
random noise) so that the EDA and win-probability model later produce
genuine, explainable business insights:

    - Higher discount %        -> higher win probability, lower margin
    - Longer payment terms     -> higher risk, slightly lower win probability
    - Strategic accounts       -> higher historical win rate
    - Higher customer risk     -> lower win probability, longer delivery delay
    - Higher delivery delay    -> higher effective cost (expediting, penalties)
"""

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

INDUSTRIES = ["Oil & Gas", "Power Generation", "Manufacturing",
              "Petrochemicals", "Infrastructure", "Renewable Energy"]
REGIONS = ["North India", "South India", "East India", "West India", "Middle East", "SE Asia"]
TIERS = ["Platinum", "Gold", "Silver", "Bronze"]
RISK_LEVELS = ["Low", "Medium", "High"]

PRODUCT_CATALOG = [
    ("Industrial Pump", "Pumps"),
    ("Gas Compression Unit", "Gas Compression"),
    ("Turbomachinery Rotor", "Turbomachinery"),
    ("Turbomachinery Casing", "Turbomachinery"),
    ("Industrial Control Valve", "Valves"),
    ("Safety Relief Valve", "Valves"),
    ("Annual Maintenance Contract", "Maintenance Services"),
    ("Field Installation Package", "Installation Services"),
    ("Spare Parts Kit - Pump", "Spare Parts"),
    ("Spare Parts Kit - Compressor", "Spare Parts"),
]


def generate_customers(n=100) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        tier_probs = [0.10, 0.25, 0.40, 0.25]
        tier = RNG.choice(TIERS, p=tier_probs)
        strategic = 1 if tier in ("Platinum", "Gold") and RNG.random() < 0.5 else 0

        # Annual revenue roughly correlated with tier
        tier_revenue_base = {"Platinum": 5000, "Gold": 1500, "Silver": 500, "Bronze": 150}
        annual_revenue = round(tier_revenue_base[tier] * RNG.uniform(0.6, 1.8), 1)  # $ millions

        relationship_years = max(0, int(RNG.normal(6 if tier in ("Platinum", "Gold") else 3, 2.5)))
        previous_orders = max(0, int(RNG.poisson(relationship_years * 1.8)))

        # Payment reliability correlated with tier & relationship
        base_reliability = {"Platinum": 92, "Gold": 85, "Silver": 75, "Bronze": 65}[tier]
        payment_reliability = int(np.clip(RNG.normal(base_reliability, 8), 30, 100))
        avg_payment_days = int(np.clip(RNG.normal(120 - payment_reliability, 10), 15, 150))

        # Historical win rate: strategic + high reliability + more orders -> higher
        base_win = 0.30 + 0.15 * strategic + 0.002 * previous_orders + 0.002 * payment_reliability
        historical_win_rate = round(float(np.clip(RNG.normal(base_win, 0.08), 0.05, 0.85)), 2)

        avg_order_value = round(RNG.uniform(0.05, 1.2) * (2 if tier in ("Platinum", "Gold") else 1), 3)  # $ millions

        # Customer risk: inversely related to reliability & relationship
        risk_score_raw = (100 - payment_reliability) * 0.5 + max(0, 8 - relationship_years) * 3
        if risk_score_raw < 25:
            risk_level = "Low"
        elif risk_score_raw < 50:
            risk_level = "Medium"
        else:
            risk_level = "High"

        rows.append({
            "Customer_ID": f"CUST{i:04d}",
            "Customer_Name": f"{RNG.choice(['Reliance', 'Adani', 'NTPC', 'ONGC', 'Tata', 'JSW', 'Vedanta', 'GAIL', 'Petronas', 'Sembcorp', 'IOCL', 'BPCL'])} {RNG.choice(['Industries', 'Energy', 'Power', 'Refineries', 'Infra', 'Projects'])} {i}",
            "Industry": RNG.choice(INDUSTRIES),
            "Region": RNG.choice(REGIONS),
            "Annual_Revenue": annual_revenue,
            "Customer_Tier": tier,
            "Previous_Orders": previous_orders,
            "Average_Order_Value": avg_order_value,
            "Historical_Win_Rate": historical_win_rate,
            "Payment_Reliability": payment_reliability,
            "Average_Payment_Days": avg_payment_days,
            "Relationship_Years": relationship_years,
            "Strategic_Account": strategic,
            "Customer_Risk_Level": risk_level,
        })
    return pd.DataFrame(rows)


def generate_products(n=30) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        name, category = PRODUCT_CATALOG[(i - 1) % len(PRODUCT_CATALOG)]
        suffix = (i - 1) // len(PRODUCT_CATALOG) + 1
        full_name = f"{name} Model {suffix}" if suffix > 1 else name

        if category in ("Turbomachinery", "Gas Compression"):
            base_cost = RNG.uniform(150000, 600000)
        elif category == "Pumps":
            base_cost = RNG.uniform(20000, 120000)
        elif category == "Valves":
            base_cost = RNG.uniform(5000, 40000)
        elif category in ("Maintenance Services", "Installation Services"):
            base_cost = RNG.uniform(8000, 60000)
        else:  # Spare Parts
            base_cost = RNG.uniform(1000, 15000)

        base_cost = round(base_cost, 2)
        standard_margin = RNG.uniform(0.28, 0.45)
        standard_price = round(base_cost / (1 - standard_margin), 2)

        installation_cost = round(base_cost * RNG.uniform(0.03, 0.10), 2) if "Services" not in category else 0.0
        warranty_cost = round(base_cost * RNG.uniform(0.02, 0.06), 2)
        maintenance_cost = round(base_cost * RNG.uniform(0.01, 0.05), 2)
        logistics_cost = round(base_cost * RNG.uniform(0.02, 0.08), 2)

        minimum_margin = round(RNG.uniform(0.12, 0.18), 3)
        maximum_discount = round(RNG.uniform(0.15, 0.25), 3)

        rows.append({
            "Product_ID": f"PROD{i:03d}",
            "Product_Name": full_name,
            "Product_Category": category,
            "Base_Cost": base_cost,
            "Standard_Price": standard_price,
            "Installation_Cost": installation_cost,
            "Warranty_Cost": warranty_cost,
            "Maintenance_Cost": maintenance_cost,
            "Logistics_Cost": logistics_cost,
            "Minimum_Margin": minimum_margin,
            "Maximum_Discount": maximum_discount,
        })
    return pd.DataFrame(rows)


def generate_historical_deals(customers: pd.DataFrame, products: pd.DataFrame, n=500) -> pd.DataFrame:
    rows = []
    cust_ids = customers["Customer_ID"].tolist()
    prod_ids = products["Product_ID"].tolist()
    cust_lookup = customers.set_index("Customer_ID")
    prod_lookup = products.set_index("Product_ID")

    for i in range(1, n + 1):
        cust_id = RNG.choice(cust_ids)
        prod_id = RNG.choice(prod_ids)
        cust = cust_lookup.loc[cust_id]
        prod = prod_lookup.loc[prod_id]

        quantity = RNG.integers(1, 6)
        base_cost_total = prod["Base_Cost"] * quantity
        extra_costs = (prod["Installation_Cost"] + prod["Warranty_Cost"] +
                       prod["Maintenance_Cost"] + prod["Logistics_Cost"]) * quantity
        cost = round(base_cost_total + extra_costs, 2)

        list_price = prod["Standard_Price"] * quantity

        # Discount tends to be higher for lower-tier / lower win-rate customers
        base_discount = 0.08 + (0.5 - cust["Historical_Win_Rate"]) * 0.15
        discount_pct = float(np.clip(RNG.normal(base_discount, 0.05), 0.0, prod["Maximum_Discount"] + 0.05))
        deal_value = round(list_price, 2)
        final_price = round(list_price * (1 - discount_pct), 2)

        gross_profit = round(final_price - cost, 2)
        margin_pct = round(gross_profit / final_price, 4) if final_price else 0.0

        competitor_price_index = round(float(np.clip(RNG.normal(1.0, 0.08), 0.75, 1.3)), 3)

        sales_cycle_days = int(np.clip(RNG.normal(60 - cust["Strategic_Account"] * 10, 20), 10, 180))
        payment_terms_days = int(RNG.choice([30, 45, 60, 90, 120], p=[0.35, 0.2, 0.2, 0.15, 0.10]))

        # delivery delay worsens with customer risk & high discount deals (rushed/low-margin jobs)
        risk_factor = {"Low": 0, "Medium": 4, "High": 9}[cust["Customer_Risk_Level"]]
        delivery_delay_days = max(0, int(RNG.normal(risk_factor + discount_pct * 20, 5)))

        # Win probability logic -> used to decide Won flag
        win_prob = (
            cust["Historical_Win_Rate"]
            + discount_pct * 0.6
            - (competitor_price_index - 1.0) * 0.5
            + cust["Strategic_Account"] * 0.05
            - (payment_terms_days - 45) * 0.0007
        )
        win_prob = float(np.clip(win_prob, 0.03, 0.95))
        won = 1 if RNG.random() < win_prob else 0

        rows.append({
            "Deal_ID": f"DEAL{i:05d}",
            "Customer_ID": cust_id,
            "Product_ID": prod_id,
            "Deal_Value": deal_value,
            "Discount_Percentage": round(discount_pct, 4),
            "Final_Price": final_price,
            "Cost": cost,
            "Gross_Profit": gross_profit,
            "Margin_Percentage": margin_pct,
            "Competitor_Price_Index": competitor_price_index,
            "Sales_Cycle_Days": sales_cycle_days,
            "Payment_Terms_Days": payment_terms_days,
            "Delivery_Delay_Days": delivery_delay_days,
            "Won": won,
        })
    return pd.DataFrame(rows)


def main():
    customers = generate_customers(100)
    products = generate_products(30)
    deals = generate_historical_deals(customers, products, 500)

    customers.to_csv(DATA_DIR / "customers.csv", index=False)
    products.to_csv(DATA_DIR / "products.csv", index=False)
    deals.to_csv(DATA_DIR / "historical_deals.csv", index=False)

    print(f"customers.csv       -> {len(customers)} rows")
    print(f"products.csv        -> {len(products)} rows")
    print(f"historical_deals.csv-> {len(deals)} rows")
    print(f"Historical win rate in deals: {deals['Won'].mean():.2%}")


if __name__ == "__main__":
    main()
