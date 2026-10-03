"""
win_probability.py
-------------------
Two win-probability approaches, both deliberately transparent:

1. calculate_baseline_win_probability() -- a simple, explainable rule-based
   adjustment on top of the customer's historical win rate. No ML required;
   useful for a quick quote or when historical deal data isn't available.

2. train_win_probability_model() / predict_win_probability() -- a Logistic
   Regression model trained on historical_deals.csv (joined with customer
   attributes). Logistic Regression is used deliberately instead of a
   black-box model (e.g. Random Forest / XGBoost) because:
       - Coefficients are directly interpretable to a sales/commercial
         audience ("+1pt discount -> +X% win probability").
       - The dataset is small (500 historical deals) and the relationships
         are close to linear in log-odds by construction.
       - Explainability matters more than marginal accuracy gains for a
         decision-support tool a sales manager has to trust.
   This is explicitly an ESTIMATE, not a guaranteed probability -- that
   caveat is surfaced in the Streamlit app and the README.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

FEATURES = [
    "Historical_Win_Rate", "Discount_Percentage", "Competitor_Price_Index",
    "Relationship_Years", "Strategic_Account", "Payment_Terms_Days", "Sales_Cycle_Days",
]


def calculate_baseline_win_probability(historical_win_rate, discount_pct, competitor_price_index,
                                        relationship_years, strategic_account, payment_terms_days):
    """
    Transparent, rule-based baseline (no model training required).
    base = historical win rate, then additive adjustments:
    """
    prob = historical_win_rate
    prob += discount_pct * 0.6                               # more discount -> more likely to win
    prob -= (competitor_price_index - 1.0) * 0.5              # pricier than competitor -> less likely
    prob += min(relationship_years, 10) * 0.005                # longstanding relationship helps a little
    prob += 0.05 if strategic_account else 0.0                 # strategic accounts get extra attention/fit
    prob -= max(0, payment_terms_days - 45) * 0.0007           # very long payment terms -> slightly less attractive deal for us, correlates with tougher negotiation
    return float(np.clip(prob, 0.03, 0.95))


def _prepare_training_frame(deals: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    merged = deals.merge(customers[["Customer_ID", "Historical_Win_Rate", "Relationship_Years", "Strategic_Account"]],
                          on="Customer_ID", how="left")
    return merged


def train_win_probability_model(deals: pd.DataFrame, customers: pd.DataFrame, test_size=0.25, random_state=42):
    """
    Trains a Logistic Regression model to predict `Won` from FEATURES.
    Returns a dict with the fitted model, the scaler, and evaluation metrics
    (accuracy, precision, recall, F1, ROC-AUC) plus feature coefficients for
    explainability.
    """
    frame = _prepare_training_frame(deals, customers)
    X = frame[FEATURES].copy()
    y = frame["Won"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=1000, random_state=random_state)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
    }

    coefficients = dict(zip(FEATURES, np.round(model.coef_[0], 4)))

    return {
        "model": model,
        "scaler": scaler,
        "metrics": metrics,
        "coefficients": coefficients,
        "features": FEATURES,
    }


def predict_win_probability(trained, historical_win_rate, discount_pct, competitor_price_index,
                             relationship_years, strategic_account, payment_terms_days, sales_cycle_days):
    """Predicts win probability for a single new opportunity using a trained model dict
    returned by train_win_probability_model()."""
    row = pd.DataFrame([{
        "Historical_Win_Rate": historical_win_rate,
        "Discount_Percentage": discount_pct,
        "Competitor_Price_Index": competitor_price_index,
        "Relationship_Years": relationship_years,
        "Strategic_Account": strategic_account,
        "Payment_Terms_Days": payment_terms_days,
        "Sales_Cycle_Days": sales_cycle_days,
    }])[trained["features"]]
    scaled = trained["scaler"].transform(row)
    proba = trained["model"].predict_proba(scaled)[0, 1]
    return float(proba)
