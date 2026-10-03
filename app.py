"""
app.py
------
Commercial Proposal & Pricing Simulator -- B2B Sales & Commercial Decision Support
Streamlit application for InduTech Solutions (fictional B2B industrial company).

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src import pricing_engine as pe
from src import risk_engine as re
from src import win_probability as wp
from src import scenario_engine as se
from src import utils

st.set_page_config(page_title="Commercial Proposal & Pricing Simulator", layout="wide")

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def get_data():
    return utils.load_data()


@st.cache_resource
def get_trained_model(_deals, _customers):
    return wp.train_win_probability_model(_deals, _customers)


customers, products, deals = get_data()
trained_model = get_trained_model(deals, customers)

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("Proposal Inputs")

customer_name = st.sidebar.selectbox("Customer", customers["Customer_Name"].tolist())
customer = customers[customers["Customer_Name"] == customer_name].iloc[0]

product_name = st.sidebar.selectbox("Product", products["Product_Name"].tolist())
product = products[products["Product_Name"] == product_name].iloc[0]

quantity = st.sidebar.number_input("Quantity", min_value=1, max_value=50, value=2)
discount_pct = st.sidebar.slider("Discount %", 0.0, 0.35, 0.10, 0.01)
competitor_price = st.sidebar.number_input(
    "Competitor Price (total, $)", min_value=0.0,
    value=float(product["Standard_Price"] * quantity * 0.95), step=1000.0
)
payment_terms_days = st.sidebar.selectbox("Payment Terms (days)", [30, 45, 60, 90, 120], index=1)
expected_delivery_days = st.sidebar.slider("Expected Delivery (days)", 10, 150, 50)
other_cost = st.sidebar.number_input("Other Cost (total, $)", min_value=0.0, value=0.0, step=500.0)

target_margin = st.sidebar.slider("Target Margin %", 0.10, 0.45, 0.25, 0.01)

st.sidebar.caption(
    "Minimum margin and maximum discount come from the selected product's "
    "configured thresholds (editable in data/products.csv)."
)

# ---------------------------------------------------------------------------
# Run the core calculation chain
# ---------------------------------------------------------------------------
quote = pe.build_full_quote(
    base_cost=product["Base_Cost"], standard_price=product["Standard_Price"],
    installation_cost=product["Installation_Cost"], maintenance_cost=product["Maintenance_Cost"],
    warranty_cost=product["Warranty_Cost"], logistics_cost=product["Logistics_Cost"],
    other_cost=other_cost, quantity=quantity, discount_pct=discount_pct,
    minimum_margin=product["Minimum_Margin"], target_margin=target_margin,
    competitor_price=competitor_price,
)

competitor_price_index = competitor_price / quote["quoted_price"] if quote["quoted_price"] else 1.0

win_probability = wp.calculate_baseline_win_probability(
    historical_win_rate=customer["Historical_Win_Rate"], discount_pct=discount_pct,
    competitor_price_index=competitor_price_index, relationship_years=customer["Relationship_Years"],
    strategic_account=bool(customer["Strategic_Account"]), payment_terms_days=payment_terms_days,
)

ml_win_probability = wp.predict_win_probability(
    trained_model, historical_win_rate=customer["Historical_Win_Rate"], discount_pct=discount_pct,
    competitor_price_index=competitor_price_index, relationship_years=customer["Relationship_Years"],
    strategic_account=int(customer["Strategic_Account"]), payment_terms_days=payment_terms_days,
    sales_cycle_days=60,
)

risk = re.full_risk_assessment(
    customer_risk_level=customer["Customer_Risk_Level"], payment_terms_days=payment_terms_days,
    margin_pct=quote["margin_pct"], minimum_margin=product["Minimum_Margin"], target_margin=target_margin,
    discount_pct=discount_pct, maximum_discount=product["Maximum_Discount"],
    expected_delivery_days=expected_delivery_days, warranty_cost=product["Warranty_Cost"],
    base_cost=product["Base_Cost"], competitor_price_index=competitor_price_index,
    strategic_account=bool(customer["Strategic_Account"]),
)

status = utils.evaluate_proposal(
    quote["margin_pct"], product["Minimum_Margin"], target_margin, risk["classification"],
    discount_pct, product["Maximum_Discount"],
)
recommendation = utils.generate_recommendation(
    status, quote["margin_pct"], product["Minimum_Margin"], target_margin, risk["classification"],
    discount_pct, product["Maximum_Discount"], win_probability,
)

expected_revenue = round(quote["revenue"] * win_probability, 2)
expected_profit = round(quote["gross_profit"] * win_probability, 2)

# ---------------------------------------------------------------------------
# Header + KPI row
# ---------------------------------------------------------------------------
st.title("Commercial Proposal & Pricing Simulator")
st.caption("B2B Sales & Commercial Decision Support — InduTech Solutions (fictional company, synthetic data)")

status_colors = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
st.subheader(f"{status_colors[status]} Commercial Status: {status}")

kpi_cols = st.columns(7)
kpi_cols[0].metric("Quoted Price", f"${quote['quoted_price']:,.0f}")
kpi_cols[1].metric("Revenue", f"${quote['revenue']:,.0f}")
kpi_cols[2].metric("Gross Profit", f"${quote['gross_profit']:,.0f}")
kpi_cols[3].metric("Gross Margin", f"{quote['margin_pct']:.1%}")
kpi_cols[4].metric("Win Probability", f"{win_probability:.0%}")
kpi_cols[5].metric("Commercial Risk", f"{risk['classification']} ({risk['score']})")
kpi_cols[6].metric("Expected Profit", f"${expected_profit:,.0f}")

st.info(recommendation)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Executive Summary", "Pricing Analysis", "Scenario Analysis",
    "Risk Assessment", "Customer Analysis", "Proposal Summary",
])

# --- TAB 1: Executive Summary -----------------------------------------------
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Recommended Price Range")
        st.write(f"**Minimum Price:** ${quote['minimum_price']:,.0f}")
        st.write(f"**Target Price:** ${quote['target_price']:,.0f}")
        st.write(f"**Quoted Price:** ${quote['quoted_price']:,.0f}")
        st.write(f"**Margin Position:** {quote['margin_position']}")
        st.write(f"**vs Competitor:** {quote['competitive_position']}")
    with c2:
        st.markdown("#### Deal Health")
        st.write(f"**Margin:** {quote['margin_pct']:.1%}  (min {product['Minimum_Margin']:.1%}, target {target_margin:.1%})")
        st.write(f"**Win Probability (rule-based):** {win_probability:.0%}")
        st.write(f"**Win Probability (logistic regression):** {ml_win_probability:.0%}")
        st.write(f"**Commercial Risk:** {risk['classification']} ({risk['score']}/100)")
        st.write(f"**Expected Profit:** ${expected_profit:,.0f}")
    st.caption("Win probability estimates are model-based approximations, not guarantees. "
               "See the README for methodology and limitations.")

# --- TAB 2: Pricing Analysis -------------------------------------------------
with tab2:
    cost_breakdown = pd.DataFrame({
        "Component": ["Base Cost", "Installation", "Maintenance", "Warranty", "Logistics", "Other"],
        "Amount": [product["Base_Cost"] * quantity, product["Installation_Cost"] * quantity,
                   product["Maintenance_Cost"] * quantity, product["Warranty_Cost"] * quantity,
                   product["Logistics_Cost"] * quantity, other_cost],
    })
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### Cost Breakdown")
        st.dataframe(cost_breakdown, hide_index=True, use_container_width=True)
        st.markdown("#### Price Waterfall")
        st.write(f"List Price: ${quote['list_price']:,.0f}")
        st.write(f"Discount ({discount_pct:.1%}): -${quote['discount_amount']:,.0f}")
        st.write(f"Quoted Price: ${quote['quoted_price']:,.0f}")
        st.write(f"**{quote['discount_tier_label']}**")
    with c2:
        fig = px.pie(cost_breakdown, names="Component", values="Amount", title="Cost Composition")
        st.plotly_chart(fig, use_container_width=True)

        price_points = pd.DataFrame({
            "Price Type": ["Minimum", "Quoted", "Target", "Competitor"],
            "Price": [quote["minimum_price"], quote["quoted_price"], quote["target_price"], competitor_price],
        })
        fig2 = px.bar(price_points, x="Price Type", y="Price", title="Price vs Margin Thresholds",
                      color="Price Type")
        st.plotly_chart(fig2, use_container_width=True)

# --- TAB 3: Scenario Analysis -------------------------------------------------
with tab3:
    st.markdown("#### Discount Scenario Comparison (5% / 10% / 15% / 20%)")
    scenario_df = se.compare_scenarios(
        [0.05, 0.10, 0.15, 0.20],
        base_cost=product["Base_Cost"], standard_price=product["Standard_Price"],
        installation_cost=product["Installation_Cost"], maintenance_cost=product["Maintenance_Cost"],
        warranty_cost=product["Warranty_Cost"], logistics_cost=product["Logistics_Cost"],
        other_cost=other_cost, quantity=quantity, minimum_margin=product["Minimum_Margin"],
        target_margin=target_margin, competitor_price=competitor_price,
        historical_win_rate=customer["Historical_Win_Rate"], relationship_years=customer["Relationship_Years"],
        strategic_account=bool(customer["Strategic_Account"]), payment_terms_days=payment_terms_days,
        customer_risk_level=customer["Customer_Risk_Level"], expected_delivery_days=expected_delivery_days,
        maximum_discount=product["Maximum_Discount"],
    )
    st.dataframe(scenario_df, hide_index=True, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.line(scenario_df, x="discount_pct", y=["margin_pct", "win_probability"],
                       markers=True, title="Discount vs Margin & Win Probability")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.bar(scenario_df, x="discount_pct", y="expected_profit",
                       title="Expected Profit by Discount Scenario")
        st.plotly_chart(fig2, use_container_width=True)

    st.caption("Expected Revenue/Profit = Revenue or Gross Profit × Win Probability — a simplified "
               "expected-value approach, not a portfolio-level risk-adjusted calculation.")

    st.markdown("#### Sensitivity: Cost Increase vs Margin")
    cost_increase_pcts = [0.0, 0.05, 0.10, 0.15]
    sens_rows = []
    for inc in cost_increase_pcts:
        bumped_cost = product["Base_Cost"] * (1 + inc)
        q = pe.build_full_quote(bumped_cost, product["Standard_Price"], product["Installation_Cost"],
                                 product["Maintenance_Cost"], product["Warranty_Cost"], product["Logistics_Cost"],
                                 other_cost, quantity, discount_pct, product["Minimum_Margin"], target_margin,
                                 competitor_price)
        sens_rows.append({"Cost Increase": f"{inc:.0%}", "Margin %": q["margin_pct"]})
    sens_df = pd.DataFrame(sens_rows)
    fig3 = px.bar(sens_df, x="Cost Increase", y="Margin %", title="Cost Shock Impact on Margin")
    st.plotly_chart(fig3, use_container_width=True)

# --- TAB 4: Risk Assessment ---------------------------------------------------
with tab4:
    st.markdown("#### Commercial Risk Components")
    comp_df = pd.DataFrame({
        "Risk Dimension": list(risk["components"].keys()),
        "Score (0=Low, 1=Medium, 2=High)": list(risk["components"].values()),
    })
    c1, c2 = st.columns([1, 1])
    with c1:
        st.dataframe(comp_df, hide_index=True, use_container_width=True)
        st.metric("Total Commercial Risk Score", f"{risk['score']} / 100", risk["classification"])
    with c2:
        fig = px.bar(comp_df, x="Risk Dimension", y="Score (0=Low, 1=Medium, 2=High)",
                     title="Risk Matrix by Dimension", color="Score (0=Low, 1=Medium, 2=High)",
                     color_continuous_scale="RdYlGn_r")
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Payment Terms vs Risk Score Sensitivity")
    pay_rows = []
    for days in [30, 60, 90, 120]:
        r = re.full_risk_assessment(customer["Customer_Risk_Level"], days, quote["margin_pct"],
                                     product["Minimum_Margin"], target_margin, discount_pct,
                                     product["Maximum_Discount"], expected_delivery_days,
                                     product["Warranty_Cost"], product["Base_Cost"],
                                     competitor_price_index, bool(customer["Strategic_Account"]))
        pay_rows.append({"Payment Terms (days)": days, "Risk Score": r["score"]})
    pay_df = pd.DataFrame(pay_rows)
    fig2 = px.line(pay_df, x="Payment Terms (days)", y="Risk Score", markers=True,
                   title="Payment Terms vs Commercial Risk")
    st.plotly_chart(fig2, use_container_width=True)

# --- TAB 5: Customer Analysis -------------------------------------------------
with tab5:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Customer Profile")
        st.write(f"**Tier:** {customer['Customer_Tier']}")
        st.write(f"**Industry:** {customer['Industry']}")
        st.write(f"**Region:** {customer['Region']}")
        st.write(f"**Strategic Account:** {'Yes' if customer['Strategic_Account'] else 'No'}")
        st.write(f"**Relationship (years):** {customer['Relationship_Years']}")
        st.write(f"**Previous Orders:** {customer['Previous_Orders']}")
        st.write(f"**Average Order Value:** ${customer['Average_Order_Value']*1_000_000:,.0f}")
    with c2:
        st.markdown("#### Payment & Win Behaviour")
        st.write(f"**Historical Win Rate:** {customer['Historical_Win_Rate']:.0%}")
        st.write(f"**Payment Reliability:** {customer['Payment_Reliability']}/100")
        st.write(f"**Average Payment Days:** {customer['Average_Payment_Days']}")
        st.write(f"**Customer Risk Level:** {customer['Customer_Risk_Level']}")

    cust_deals = deals[deals["Customer_ID"] == customer["Customer_ID"]]
    if len(cust_deals) > 0:
        st.markdown(f"#### Historical Deals with {customer_name} ({len(cust_deals)})")
        st.dataframe(cust_deals, hide_index=True, use_container_width=True)
    else:
        st.caption("No historical deals on file for this customer in the synthetic dataset.")

# --- TAB 6: Proposal Summary ---------------------------------------------------
with tab6:
    st.markdown("### Proposal Summary")
    summary = pd.DataFrame({
        "Field": ["Customer", "Product", "Quantity", "Quoted Price", "Discount", "Total Contract Value",
                  "Expected Margin", "Payment Terms", "Expected Delivery", "Risk Level", "Win Probability",
                  "Commercial Recommendation"],
        "Value": [customer_name, product_name, quantity, f"${quote['quoted_price']:,.0f}",
                  f"{discount_pct:.1%}", f"${quote['quoted_price']:,.0f}", f"{quote['margin_pct']:.1%}",
                  f"{payment_terms_days} days", f"{expected_delivery_days} days",
                  risk["classification"], f"{win_probability:.0%}", recommendation],
    })
    st.dataframe(summary, hide_index=True, use_container_width=True)

    csv_bytes = summary.to_csv(index=False).encode("utf-8")
    st.download_button("Download Proposal Summary (CSV)", data=csv_bytes,
                        file_name=f"proposal_summary_{customer['Customer_ID']}_{product['Product_ID']}.csv",
                        mime="text/csv")

st.divider()
with st.expander("Limitations"):
    st.markdown("""
- Dataset is synthetic (generated for this project, not real Baker Hughes or InduTech data).
- Win probability is an estimate, not a guaranteed outcome.
- Risk scoring uses configurable business rules, not an actuarial model.
- Pricing recommendations support, but do not replace, commercial judgment.
- Expected-profit calculation uses a simplified expected-value approach.
- Contract/legal terms are not reviewed by this tool.
- Competitor pricing is a user-entered assumption, not live market data.
""")
