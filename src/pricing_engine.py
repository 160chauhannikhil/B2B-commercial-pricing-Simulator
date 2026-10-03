"""
pricing_engine.py
------------------
Core commercial pricing calculations for a single proposal/quote line.

All functions take plain numbers (floats/ints) so they can be reused
identically from the Streamlit app, a notebook, or a test script.
"""


def calculate_total_cost(base_cost, installation_cost=0.0, maintenance_cost=0.0,
                          warranty_cost=0.0, logistics_cost=0.0, other_cost=0.0,
                          quantity=1):
    """Sum of all cost components for the proposal, scaled by quantity."""
    unit_cost = base_cost + installation_cost + maintenance_cost + warranty_cost + logistics_cost + other_cost
    return round(unit_cost * quantity, 2)


def calculate_list_price(standard_price, quantity=1):
    """List price before any discount is applied."""
    return round(standard_price * quantity, 2)


def calculate_discount(list_price, discount_pct):
    """Discount amount in currency given a discount percentage (0-1)."""
    return round(list_price * discount_pct, 2)


def calculate_quoted_price(list_price, discount_pct):
    """Final quoted price to the customer after discount."""
    return round(list_price * (1 - discount_pct), 2)


def calculate_revenue(quoted_price):
    """Revenue recognised if the deal is won (same as quoted price here;
    kept as a separate function so other revenue adjustments can be added
    later, e.g. volume rebates, without touching callers)."""
    return round(quoted_price, 2)


def calculate_gross_profit(revenue, total_cost):
    return round(revenue - total_cost, 2)


def calculate_margin(gross_profit, revenue):
    """Gross margin as a fraction (0-1). Returns 0 if revenue is 0 to avoid division errors."""
    if not revenue:
        return 0.0
    return round(gross_profit / revenue, 4)


def calculate_minimum_price(total_cost, minimum_margin):
    """Lowest price that still clears the minimum acceptable margin.

    Derived from: margin = (price - cost) / price  =>  price = cost / (1 - margin)
    """
    if minimum_margin >= 1:
        raise ValueError("minimum_margin must be less than 1")
    return round(total_cost / (1 - minimum_margin), 2)


def calculate_target_price(total_cost, target_margin):
    """Commercially preferred price based on the target margin."""
    if target_margin >= 1:
        raise ValueError("target_margin must be less than 1")
    return round(total_cost / (1 - target_margin), 2)


def calculate_max_discount_allowed(list_price, minimum_price):
    """The largest discount (as a fraction of list price) that still clears the minimum price."""
    if not list_price:
        return 0.0
    return round(max(0.0, (list_price - minimum_price) / list_price), 4)


def pricing_position(quoted_price, minimum_price, target_price, competitor_price):
    """
    Classifies the quoted price relative to minimum/target margin thresholds
    and the competitor's price. Returns a short, explainable label -- this
    function intentionally never says one price is universally "best"; the
    trade-off between margin and win probability is surfaced separately by
    the win-probability and scenario engines.
    """
    if quoted_price < minimum_price:
        label = "Below Minimum Margin"
    elif quoted_price < target_price:
        label = "Competitive"
    elif quoted_price <= target_price * 1.05:
        label = "Target Margin Achieved"
    else:
        label = "Premium Pricing"

    vs_competitor = "Above Competitor" if quoted_price > competitor_price else (
        "Below Competitor" if quoted_price < competitor_price else "At Competitor Parity")

    return {"margin_position": label, "competitive_position": vs_competitor}


def discount_tier(discount_pct):
    """Maps a discount percentage to a commercial-approval tier."""
    if discount_pct < 0.05:
        return "0-5%: Low discount risk", "none"
    elif discount_pct < 0.10:
        return "5-10%: Normal commercial flexibility", "none"
    elif discount_pct < 0.15:
        return "10-15%: Manager approval recommended", "manager"
    elif discount_pct < 0.20:
        return "15-20%: High discount / margin risk", "manager"
    else:
        return "20%+: Escalation required", "escalation"


def build_full_quote(base_cost, standard_price, installation_cost, maintenance_cost,
                      warranty_cost, logistics_cost, other_cost, quantity,
                      discount_pct, minimum_margin, target_margin, competitor_price):
    """Convenience wrapper that runs the full pricing calculation chain
    and returns a single dict -- this is what the Streamlit app calls."""
    total_cost = calculate_total_cost(base_cost, installation_cost, maintenance_cost,
                                       warranty_cost, logistics_cost, other_cost, quantity)
    list_price = calculate_list_price(standard_price, quantity)
    discount_amount = calculate_discount(list_price, discount_pct)
    quoted_price = calculate_quoted_price(list_price, discount_pct)
    revenue = calculate_revenue(quoted_price)
    gross_profit = calculate_gross_profit(revenue, total_cost)
    margin_pct = calculate_margin(gross_profit, revenue)
    minimum_price = calculate_minimum_price(total_cost, minimum_margin)
    target_price = calculate_target_price(total_cost, target_margin)
    max_discount_allowed = calculate_max_discount_allowed(list_price, minimum_price)
    position = pricing_position(quoted_price, minimum_price, target_price, competitor_price)
    tier_label, approval_level = discount_tier(discount_pct)

    return {
        "total_cost": total_cost,
        "list_price": list_price,
        "discount_amount": discount_amount,
        "quoted_price": quoted_price,
        "revenue": revenue,
        "gross_profit": gross_profit,
        "margin_pct": margin_pct,
        "minimum_price": minimum_price,
        "target_price": target_price,
        "max_discount_allowed": max_discount_allowed,
        "margin_position": position["margin_position"],
        "competitive_position": position["competitive_position"],
        "discount_tier_label": tier_label,
        "discount_approval_level": approval_level,
    }
