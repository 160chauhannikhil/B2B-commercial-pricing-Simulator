"""
scenario_engine.py
-------------------
Scenario comparison (e.g. 5% / 10% / 15% / 20% discount scenarios) and
sensitivity tables (e.g. discount vs margin, cost increase vs margin).

Expected Revenue / Expected Profit use a simplified expected-value approach:
    Expected Revenue = Revenue * Win Probability
    Expected Profit  = Gross Profit * Win Probability
This is explicitly a simplification (it does not account for correlation
between scenarios, portfolio effects, or risk-adjusted discount rates) --
stated plainly in the README and the app.
"""

import pandas as pd
from . import pricing_engine as pe
from . import risk_engine as re
from . import win_probability as wp


def run_scenario(base_cost, standard_price, installation_cost, maintenance_cost,
                  warranty_cost, logistics_cost, other_cost, quantity,
                  discount_pct, minimum_margin, target_margin, competitor_price,
                  historical_win_rate, relationship_years, strategic_account,
                  payment_terms_days, customer_risk_level, expected_delivery_days,
                  maximum_discount):
    """Runs the full pricing + risk + win-probability chain for ONE discount scenario."""
    quote = pe.build_full_quote(base_cost, standard_price, installation_cost, maintenance_cost,
                                 warranty_cost, logistics_cost, other_cost, quantity,
                                 discount_pct, minimum_margin, target_margin, competitor_price)

    competitor_price_index = competitor_price / quote["quoted_price"] if quote["quoted_price"] else 1.0

    win_prob = wp.calculate_baseline_win_probability(
        historical_win_rate, discount_pct, competitor_price_index,
        relationship_years, strategic_account, payment_terms_days
    )

    risk = re.full_risk_assessment(
        customer_risk_level, payment_terms_days, quote["margin_pct"], minimum_margin, target_margin,
        discount_pct, maximum_discount, expected_delivery_days, warranty_cost, base_cost,
        competitor_price_index, strategic_account
    )

    expected_revenue = round(quote["revenue"] * win_prob, 2)
    expected_profit = round(quote["gross_profit"] * win_prob, 2)

    return {
        "discount_pct": discount_pct,
        "quoted_price": quote["quoted_price"],
        "revenue": quote["revenue"],
        "cost": quote["total_cost"],
        "gross_profit": quote["gross_profit"],
        "margin_pct": quote["margin_pct"],
        "win_probability": round(win_prob, 4),
        "expected_revenue": expected_revenue,
        "expected_profit": expected_profit,
        "risk_score": risk["score"],
        "risk_classification": risk["classification"],
    }


def compare_scenarios(discount_list, **kwargs):
    """Runs run_scenario() for each discount % in discount_list and returns a DataFrame."""
    rows = []
    for d in discount_list:
        row = run_scenario(discount_pct=d, **kwargs)
        rows.append(row)
    return pd.DataFrame(rows)


def run_sensitivity_analysis(variable, value_list, **kwargs):
    """
    Generic one-variable sensitivity table. `variable` must be a keyword
    accepted by run_scenario (e.g. 'discount_pct', 'base_cost', 'competitor_price',
    'payment_terms_days'). Returns a DataFrame with the margin/win-probability/
    risk impact of varying that one input while holding everything else constant.
    """
    rows = []
    for v in value_list:
        call_kwargs = dict(kwargs)
        call_kwargs[variable] = v
        result = run_scenario(**call_kwargs)
        result[variable] = v
        rows.append(result)
    return pd.DataFrame(rows)
