import csv
import random

from decision_engine import choose_best_action
from simulator import run_simulation
from baseline import run_baseline
from safety import evaluate_safety
from audit import create_audit_record, save_audit_log


def load_payments(filename="../data/payments.csv"):
    payments = []

    with open(filename, newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            payments.append({
                "customer_id": row["customer_id"],
                "amount": int(row["amount"]),
                "date": row["date"],
                "failure_reason": row["failure_reason"],
                "previous_successes": int(row["previous_successes"]),
                "previous_failures": int(row["previous_failures"]),
                "retry_count": int(row["retry_count"])
            })

    return payments


def run_recoveros(payments):

    total_recovered = 0
    total_at_risk = 0
    flagged = 0
    retries = 0

    unsafe_actions = 0
    retry_limit_violations = 0

    audit_records = []

    for payment in payments:

        # 1. Make decision
        decision = choose_best_action(payment)
        action = decision["action"]

        # 2. Check safety
        safety = evaluate_safety(payment, action)

        if safety["unsafe_action"]:
            unsafe_actions += 1

        if safety["retry_limit_violation"]:
            retry_limit_violations += 1

        # 3. Simulate result
        result = run_simulation(payment, decision)

        total_at_risk += payment["amount"]
        total_recovered += result["recovered_amount"]

        if action == "retry_payment":
            retries += 1

        if result["outcome"] == "flagged":
            flagged += 1

        # 4. Save complete decision to audit record
        audit_record = create_audit_record(
            payment,
            decision,
            result,
            safety
        )

        audit_records.append(audit_record)

    return {
        "total_at_risk": total_at_risk,
        "total_recovered": total_recovered,
        "retries": retries,
        "flagged": flagged,
        "unsafe_actions": unsafe_actions,
        "retry_limit_violations": retry_limit_violations,
        "audit_records": audit_records
    }


# Load our synthetic dataset
payments = load_payments()


# Run baseline with fixed randomness
random.seed(42)
baseline = run_baseline(payments)


# Run RecoverOS with fixed randomness
random.seed(42)
recoveros = run_recoveros(payments)


# Save RecoverOS decisions
save_audit_log(recoveros["audit_records"])


# Calculate recovery rates
baseline_rate = (
    baseline["total_recovered"]
    / baseline["total_at_risk"]
) * 100

recoveros_rate = (
    recoveros["total_recovered"]
    / recoveros["total_at_risk"]
) * 100

additional_recovery = (
    recoveros["total_recovered"]
    - baseline["total_recovered"]
)


# Print results
print()
print("========================================")
print("       RECOVEROS EVALUATION")
print("========================================")


print()
print("NAIVE RETRY STRATEGY")
print("----------------------------------------")
print(f"Recovered: ₹{baseline['total_recovered']:,}")
print(f"Recovery rate: {baseline_rate:.2f}%")
print(f"Retry attempts: {baseline['retry_attempts']}")
print(f"Unsafe retries: {baseline['unsafe_retries']}")


print()
print("RECOVEROS")
print("----------------------------------------")
print(f"Recovered: ₹{recoveros['total_recovered']:,}")
print(f"Recovery rate: {recoveros_rate:.2f}%")
print(f"Retry attempts: {recoveros['retries']}")
print(f"Flagged for review: {recoveros['flagged']}")
print(f"Unsafe automatic actions: {recoveros['unsafe_actions']}")
print(
    f"Retry limit violations: "
    f"{recoveros['retry_limit_violations']}"
)


print()
print("IMPACT")
print("----------------------------------------")
print(f"Additional simulated recovery: ₹{additional_recovery:,}")


print()
print("SAFETY RESULT")
print("----------------------------------------")

if (
    recoveros["unsafe_actions"] == 0
    and recoveros["retry_limit_violations"] == 0
):
    print("PASS: No unsafe automatic actions detected.")
else:
    print("WARNING: Safety violations detected.")


print()
print("AUDIT")
print("----------------------------------------")
print(
    f"Saved {len(recoveros['audit_records'])} "
    f"decision records to data/audit_log.json"
)

print()
print("========================================")
