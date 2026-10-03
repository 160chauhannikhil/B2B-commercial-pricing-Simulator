"""
risk_engine.py
--------------
Commercial Risk Score: a simplified, configurable, weighted scoring model
across eight risk dimensions. Each dimension is scored 0 (low), 1 (moderate)
or 2 (high), then combined with configurable weights into a 0-100 score.

This is a decision-support heuristic, not an actuarial or accounting-standard
risk model -- that limitation is stated explicitly in the README and in the
Streamlit app.
"""

DEFAULT_WEIGHTS = {
    "customer_risk": 0.15,
    "payment_risk": 0.15,
    "margin_risk": 0.20,
    "discount_risk": 0.15,
    "delivery_risk": 0.10,
    "warranty_risk": 0.10,
    "competitive_risk": 0.10,
    "contract_risk": 0.05,
}


def calculate_customer_risk(customer_risk_level):
    return {"Low": 0, "Medium": 1, "High": 2}.get(customer_risk_level, 1)


def calculate_payment_risk(payment_terms_days):
    if payment_terms_days <= 30:
        return 0
    elif payment_terms_days <= 60:
        return 1
    else:
        return 2


def calculate_margin_risk(margin_pct, minimum_margin, target_margin):
    if margin_pct < minimum_margin:
        return 2
    elif margin_pct < target_margin:
        return 1
    else:
        return 0


def calculate_discount_risk(discount_pct, maximum_discount):
    if discount_pct > maximum_discount:
        return 2
    elif discount_pct > maximum_discount * 0.6:
        return 1
    else:
        return 0


def calculate_delivery_risk(expected_delivery_days, standard_lead_time=45):
    overrun = expected_delivery_days - standard_lead_time
    if overrun <= 0:
        return 0
    elif overrun <= 15:
        return 1
    else:
        return 2


def calculate_warranty_risk(warranty_cost, base_cost):
    if base_cost <= 0:
        return 1
    ratio = warranty_cost / base_cost
    if ratio < 0.03:
        return 0
    elif ratio < 0.06:
        return 1
    else:
        return 2


def calculate_competitive_risk(competitor_price_index):
    """competitor_price_index < 1 means our price is above competitor (riskier to win)."""
    if competitor_price_index >= 1.05:
        return 0
    elif competitor_price_index >= 0.95:
        return 1
    else:
        return 2


def calculate_contract_risk(payment_terms_days, strategic_account):
    """Simplified proxy: long payment terms on a non-strategic account raise contract risk."""
    if payment_terms_days >= 90 and not strategic_account:
        return 2
    elif payment_terms_days >= 60:
        return 1
    else:
        return 0


def calculate_total_risk(risk_components: dict, weights: dict = None):
    """
    risk_components: dict with keys matching DEFAULT_WEIGHTS, values 0/1/2.
    Returns (score_0_to_100, classification_str).
    """
    weights = weights or DEFAULT_WEIGHTS
    # Each component is 0-2; normalise to 0-100 scale before weighting.
    weighted_sum = sum((risk_components.get(k, 0) / 2) * 100 * w for k, w in weights.items())
    score = round(weighted_sum, 1)

    if score <= 30:
        classification = "Low"
    elif score <= 60:
        classification = "Medium"
    else:
        classification = "High"

    return score, classification


def full_risk_assessment(customer_risk_level, payment_terms_days, margin_pct,
                          minimum_margin, target_margin, discount_pct, maximum_discount,
                          expected_delivery_days, warranty_cost, base_cost,
                          competitor_price_index, strategic_account, weights=None):
    components = {
        "customer_risk": calculate_customer_risk(customer_risk_level),
        "payment_risk": calculate_payment_risk(payment_terms_days),
        "margin_risk": calculate_margin_risk(margin_pct, minimum_margin, target_margin),
        "discount_risk": calculate_discount_risk(discount_pct, maximum_discount),
        "delivery_risk": calculate_delivery_risk(expected_delivery_days),
        "warranty_risk": calculate_warranty_risk(warranty_cost, base_cost),
        "competitive_risk": calculate_competitive_risk(competitor_price_index),
        "contract_risk": calculate_contract_risk(payment_terms_days, strategic_account),
    }
    score, classification = calculate_total_risk(components, weights)
    return {"components": components, "score": score, "classification": classification}
