import csv

from decision_engine import choose_best_action
from simulator import run_simulation


def load_payments(filename="../data/payments.csv"):
    """Load synthetic payment failures from CSV."""

    payments = []

    with open(filename, newline="") as file:

        reader = csv.DictReader(file)

        for row in reader:

            payment = {
                "customer_id": row["customer_id"],
                "amount": int(row["amount"]),
                "date": row["date"],
                "failure_reason": row["failure_reason"],
                "previous_successes": int(row["previous_successes"]),
                "previous_failures": int(row["previous_failures"]),
                "retry_count": int(row["retry_count"])
            }

            payments.append(payment)

    return payments


payments = load_payments()

total_at_risk = 0
total_recovered = 0
flagged_count = 0
gave_up_count = 0


print()
print("========================================")
print("          RECOVEROS ENGINE")
print("========================================")
print()

print(f"Loaded {len(payments)} payment failures.")
print()


for payment in payments:

    decision = choose_best_action(payment)

    result = run_simulation(
        payment,
        decision
    )

    total_at_risk += payment["amount"]
    total_recovered += result["recovered_amount"]

    if result["outcome"] == "flagged":
        flagged_count += 1

    if result["outcome"] == "gave_up":
        gave_up_count += 1


recovery_rate = 0

if total_at_risk > 0:
    recovery_rate = (
        total_recovered / total_at_risk
    ) * 100


print("========================================")
print("             FINAL RESULTS")
print("========================================")
print(f"Payments processed: {len(payments)}")
print(f"Total at risk: ₹{total_at_risk:,}")
print(f"Total recovered: ₹{total_recovered:,}")
print(f"Recovery rate: {recovery_rate:.2f}%")
print(f"Flagged for review: {flagged_count}")
print(f"Stopped after retry limit: {gave_up_count}")
print("========================================")