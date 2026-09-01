"""
RecoverOS X - ML + Strategy Decision Pipeline

Connects the trained recovery prediction model
to the strategy optimizer.
"""

import os
import sys
import joblib
import pandas as pd

# Allow imports from the app directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from strategy_optimizer import optimize_strategy


MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "recovery_model.pkl",
)


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Recovery model not found: {MODEL_PATH}"
        )

    return joblib.load(MODEL_PATH)


def predict_recovery(model, payment):
    """
    Generate recovery probability for one payment.

    The model was trained using the advanced training dataset.
    """

    features = pd.DataFrame([{
        "amount": payment["amount"],
        "failure_reason": payment["failure_reason"],
        "payment_method": payment["payment_method"],
        "merchant_type": payment["merchant_type"],
        "previous_successes": payment["previous_successes"],
        "previous_failures": payment["previous_failures"],
        "retry_count": payment["retry_count"],
        "days_since_last_payment": payment["days_since_last_payment"],
        "customer_tenure_months": payment["customer_tenure_months"],
        "mandate_age_days": payment["mandate_age_days"],
        "average_amount": payment["average_amount"],
        "amount_vs_average": payment["amount_vs_average"],
        "recent_success_rate": payment["recent_success_rate"],
        "failure_frequency": payment["failure_frequency"],
        "retry_interval_hours": payment["retry_interval_hours"],
    }])

    probability = model.predict_proba(features)[0][1]

    return float(probability)


def evaluate_payment(payment):
    """
    Full RecoverOS X decision pipeline:

    Payment
      ↓
    ML prediction
      ↓
    Strategy optimization
    """

    model = load_model()

    recovery_probability = predict_recovery(
        model,
        payment,
    )

    # Simple synthetic risk score for now.
    # The dedicated risk engine will replace this later.
    risk_score = 0.0

    if payment["failure_reason"] in [
        "suspicious_reversal",
        "mandate_changed",
    ]:
        risk_score = 0.90

    best_strategy, all_strategies = optimize_strategy(
        amount=float(payment["amount"]),
        recovery_probability=recovery_probability,
        retry_count=int(payment["retry_count"]),
        risk_score=risk_score,
    )

    return {
        "recovery_probability": recovery_probability,
        "risk_score": risk_score,
        "recommended_action": best_strategy.action,
        "expected_revenue": best_strategy.expected_revenue,
        "strategies": all_strategies,
    }


if __name__ == "__main__":

    print()
    print("=" * 60)
    print("RecoverOS X - ML Decision Pipeline")
    print("=" * 60)

    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "advanced_training_data.csv",
    )

    df = pd.read_csv(data_path)

    # Use the first payment as a live pipeline example.
    payment = df.iloc[0].to_dict()

    result = evaluate_payment(payment)

    print()
    print("PAYMENT")
    print("-" * 60)
    print(f"Payment ID          : {payment['payment_id']}")
    print(f"Amount              : ₹{payment['amount']:,.2f}")
    print(f"Failure reason      : {payment['failure_reason']}")
    print(f"Payment method      : {payment['payment_method']}")
    print(f"Retry count         : {payment['retry_count']}")

    print()
    print("ML PREDICTION")
    print("-" * 60)
    print(
        f"Recovery probability: "
        f"{result['recovery_probability']:.2%}"
    )

    print()
    print("STRATEGY DECISION")
    print("-" * 60)
    print(
        f"Recommended action  : "
        f"{result['recommended_action']}"
    )
    print(
        f"Expected revenue    : "
        f"₹{result['expected_revenue']:,.2f}"
    )

    print()
    print("=" * 60)