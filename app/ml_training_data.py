from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "advanced_training_data.csv"


def generate_data(n=10000):
    rng = np.random.default_rng(42)

    failure_reasons = [
        "bank_timeout",
        "insufficient_funds",
        "mandate_expired",
        "expired_card",
        "suspicious_reversal",
    ]

    payment_methods = [
        "upi",
        "card",
        "netbanking",
        "wallet",
    ]

    merchant_types = [
        "subscription",
        "ecommerce",
        "saas",
        "education",
        "media",
    ]

    rows = []

    for i in range(n):
        amount = int(rng.choice([
            499,
            999,
            1499,
            1999,
            2499,
            4999,
            9999,
            19999,
        ]))

        failure_reason = rng.choice(failure_reasons)
        payment_method = rng.choice(payment_methods)
        merchant_type = rng.choice(merchant_types)

        previous_successes = int(rng.poisson(8))
        previous_failures = int(rng.poisson(2))

        retry_count = int(rng.integers(0, 4))

        days_since_last_payment = int(
            rng.integers(1, 61)
        )

        customer_tenure_months = int(
            rng.integers(1, 61)
        )

        mandate_age_days = int(
            rng.integers(1, 731)
        )

        average_amount = max(
            100,
            amount * rng.uniform(0.6, 1.4)
        )

        amount_vs_average = amount / average_amount

        total_attempts = (
            previous_successes
            + previous_failures
        )

        recent_success_rate = (
            previous_successes / total_attempts
            if total_attempts > 0
            else 0.0
        )

        failure_frequency = (
            previous_failures / max(days_since_last_payment, 1)
        )

        retry_interval_hours = float(
            rng.uniform(0.5, 48)
        )

        # Synthetic probability model.
        # This creates a realistic experimental target
        # for ML development. It is NOT real payment data.
        probability = 0.50

        if failure_reason == "bank_timeout":
            probability += 0.22

        elif failure_reason == "insufficient_funds":
            probability += 0.05

        elif failure_reason == "mandate_expired":
            probability -= 0.18

        elif failure_reason == "expired_card":
            probability -= 0.25

        elif failure_reason == "suspicious_reversal":
            probability -= 0.40

        probability += recent_success_rate * 0.20

        probability += min(
            previous_successes * 0.008,
            0.08
        )

        probability -= min(
            previous_failures * 0.015,
            0.10
        )

        probability -= retry_count * 0.07

        if payment_method == "upi":
            probability += 0.03

        if days_since_last_payment > 45:
            probability -= 0.04

        if customer_tenure_months > 24:
            probability += 0.04

        if amount_vs_average > 1.5:
            probability -= 0.05

        probability = np.clip(
            probability,
            0.02,
            0.98
        )

        recovered = int(
            rng.random() < probability
        )

        rows.append({
            "payment_id": f"PX{i + 1:06d}",
            "amount": amount,
            "failure_reason": failure_reason,
            "payment_method": payment_method,
            "merchant_type": merchant_type,
            "previous_successes": previous_successes,
            "previous_failures": previous_failures,
            "retry_count": retry_count,
            "days_since_last_payment": days_since_last_payment,
            "customer_tenure_months": customer_tenure_months,
            "mandate_age_days": mandate_age_days,
            "average_amount": round(average_amount, 2),
            "amount_vs_average": round(
                amount_vs_average,
                3
            ),
            "recent_success_rate": round(
                recent_success_rate,
                3
            ),
            "failure_frequency": round(
                failure_frequency,
                5
            ),
            "retry_interval_hours": round(
                retry_interval_hours,
                2
            ),
            "recovered": recovered,
        })

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print()
    print("=" * 55)
    print("RecoverOS X - Advanced Training Dataset")
    print("=" * 55)
    print(f"Records          : {len(df)}")
    print(f"Recovered        : {df['recovered'].sum()}")
    print(
        f"Not recovered    : "
        f"{(df['recovered'] == 0).sum()}"
    )
    print(
        f"Recovery rate    : "
        f"{df['recovered'].mean():.2%}"
    )
    print()
    print("Features:")
    print(", ".join(df.columns))
    print()
    print(f"Saved to: {OUTPUT_PATH}")
    print("=" * 55)


if __name__ == "__main__":
    generate_data()