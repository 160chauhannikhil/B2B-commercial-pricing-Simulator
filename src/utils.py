"""
utils.py
--------
Shared helpers: data loading, proposal evaluation (GREEN/AMBER/RED), and the
plain-language recommendation engine.
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    deals = pd.read_csv(DATA_DIR / "historical_deals.csv")
    return customers, products, deals


def evaluate_proposal(margin_pct, minimum_margin, target_margin, risk_classification,
                       discount_pct, maximum_discount):
    """
    Returns a commercial status: GREEN / AMBER / RED, based on configurable
    thresholds:
      GREEN: margin >= target AND risk <= Medium AND discount within max threshold
      AMBER: margin >= minimum but risk is Medium/High, or margin between min and target
      RED:   margin < minimum OR discount exceeds maximum OR risk is High with a margin issue
    """
    discount_exceeded = discount_pct > maximum_discount

    if margin_pct < minimum_margin or discount_exceeded:
        return "RED"
    if margin_pct >= target_margin and risk_classification != "High":
        return "GREEN"
    return "AMBER"


def generate_recommendation(status, margin_pct, minimum_margin, target_margin,
                             risk_classification, discount_pct, maximum_discount,
                             win_probability):
    """Produces a short, explainable recommendation string -- never a bare
    'Accept' / 'Reject'."""
    margin_txt = f"{margin_pct:.1%}"
    min_txt = f"{minimum_margin:.1%}"
    target_txt = f"{target_margin:.1%}"
    win_txt = f"{win_probability:.0%}"

    if status == "GREEN":
        return (f"Proposal is commercially viable at the proposed price. Margin ({margin_txt}) "
                f"meets or exceeds the target threshold ({target_txt}), commercial risk is "
                f"{risk_classification.lower()}, and estimated win probability is {win_txt}.")

    if status == "AMBER":
        reasons = []
        if margin_pct < target_margin:
            reasons.append(f"margin ({margin_txt}) is above the minimum ({min_txt}) but below the "
                            f"target ({target_txt})")
        if risk_classification in ("Medium", "High"):
            reasons.append(f"commercial risk is {risk_classification.lower()}")
        reason_txt = " and ".join(reasons) if reasons else "the deal sits between minimum and target thresholds"
        return (f"Proposal requires manager review because {reason_txt}. Estimated win probability "
                f"is {win_txt}.")

    # RED
    reasons = []
    if margin_pct < minimum_margin:
        reasons.append(f"margin ({margin_txt}) falls below the minimum acceptable threshold ({min_txt})")
    if discount_pct > maximum_discount:
        reasons.append(f"requested discount ({discount_pct:.1%}) exceeds the maximum allowed "
                        f"({maximum_discount:.1%})")
    if risk_classification == "High":
        reasons.append("commercial risk is high")
    reason_txt = "; ".join(reasons) if reasons else "multiple commercial thresholds are breached"
    return f"Proposal requires commercial escalation because {reason_txt}."
