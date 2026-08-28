import csv
import random
from datetime import date, timedelta


FAILURE_REASONS = [
    "insufficient_funds",
    "card_expired",
    "bank_timeout",
    "mandate_expired",
    "suspicious_reversal",
    "mandate_changed_recently"
]


def generate_payment(customer_number):
    amount = random.choice([
        499,
        799,
        999,
        1499,
        1999,
        2499,
        4999,
        9999
    ])

    reason = random.choice(FAILURE_REASONS)

    previous_successes = random.randint(0, 25)
    previous_failures = random.randint(0, 5)

    retry_count = random.randint(0, 3)

    days_ago = random.randint(0, 30)

    payment_date = (
        date.today() - timedelta(days=days_ago)
    ).isoformat()

    return {
        "customer_id": f"C{customer_number:04d}",
        "amount": amount,
        "date": payment_date,
        "failure_reason": reason,
        "previous_successes": previous_successes,
        "previous_failures": previous_failures,
        "retry_count": retry_count
    }


def generate_dataset(number_of_payments=200):

    payments = []

    for customer_number in range(1, number_of_payments + 1):
        payment = generate_payment(customer_number)
        payments.append(payment)

    return payments


def save_to_csv(payments, filename="../data/payments.csv"):

    fieldnames = [
        "customer_id",
        "amount",
        "date",
        "failure_reason",
        "previous_successes",
        "previous_failures",
        "retry_count"
    ]

    with open(filename, "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(payments)


if __name__ == "__main__":

    payments = generate_dataset(200)

    save_to_csv(payments)

    print("Generated 200 synthetic payment failures.")
    print("Saved to data/payments.csv")
    