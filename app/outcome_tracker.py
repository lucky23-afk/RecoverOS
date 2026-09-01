from pathlib import Path
import json
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTCOME_FILE = DATA_DIR / "outcomes.jsonl"
TEST_OUTCOME_FILE = DATA_DIR / "test_outcomes.jsonl"


def _write_outcome(file_path, outcome):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(outcome) + "\n")


def record_outcome(
    payment_id,
    amount,
    failure_reason,
    recommended_action,
    final_action,
    recovery_probability,
    expected_revenue,
    recovered,
    recovery_amount=0.0,
):
    """
    Record a REAL production outcome.

    Production learning data is written only to outcomes.jsonl.
    """

    outcome = {
        "timestamp": datetime.now().isoformat(),
        "payment_id": payment_id,
        "amount": float(amount),
        "failure_reason": failure_reason,
        "recommended_action": recommended_action,
        "final_action": final_action,
        "recovery_probability": float(recovery_probability),
        "expected_revenue": float(expected_revenue),
        "recovered": bool(recovered),
        "recovery_amount": float(recovery_amount),
    }

    _write_outcome(OUTCOME_FILE, outcome)

    return outcome


def record_test_outcome(
    payment_id,
    amount,
    failure_reason,
    recommended_action,
    final_action,
    recovery_probability,
    expected_revenue,
    recovered,
    recovery_amount=0.0,
):
    """
    Record a TEST outcome.

    Test data is completely separated from production outcomes.
    """

    outcome = {
        "timestamp": datetime.now().isoformat(),
        "payment_id": payment_id,
        "amount": float(amount),
        "failure_reason": failure_reason,
        "recommended_action": recommended_action,
        "final_action": final_action,
        "recovery_probability": float(recovery_probability),
        "expected_revenue": float(expected_revenue),
        "recovered": bool(recovered),
        "recovery_amount": float(recovery_amount),
    }

    _write_outcome(TEST_OUTCOME_FILE, outcome)

    return outcome


def load_outcomes():
    """
    Load REAL production outcomes only.
    """

    if not OUTCOME_FILE.exists():
        return []

    outcomes = []

    with open(OUTCOME_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                outcomes.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return outcomes


def load_test_outcomes():
    """
    Load TEST outcomes only.
    """

    if not TEST_OUTCOME_FILE.exists():
        return []

    outcomes = []

    with open(TEST_OUTCOME_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                outcomes.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return outcomes


def get_outcome_stats():
    """
    Calculate statistics from REAL production outcomes only.
    """

    outcomes = load_outcomes()

    if not outcomes:
        return {
            "total": 0,
            "recovered": 0,
            "not_recovered": 0,
            "recovery_rate": 0.0,
            "total_recovered_amount": 0.0,
        }

    recovered = sum(
        1
        for outcome in outcomes
        if outcome.get("recovered") is True
    )

    total = len(outcomes)

    total_recovered_amount = sum(
        float(outcome.get("recovery_amount", 0.0))
        for outcome in outcomes
    )

    return {
        "total": total,
        "recovered": recovered,
        "not_recovered": total - recovered,
        "recovery_rate": recovered / total,
        "total_recovered_amount": total_recovered_amount,
    }


def print_stats():
    stats = get_outcome_stats()

    print()
    print("=" * 70)
    print("RecoverOS X - REAL OUTCOME TRACKING")
    print("=" * 70)

    print(f"Real outcomes        : {stats['total']}")
    print(f"Recovered            : {stats['recovered']}")
    print(f"Not recovered        : {stats['not_recovered']}")
    print(f"Recovery rate        : {stats['recovery_rate']:.2%}")
    print(
        f"Recovered amount     : "
        f"₹{stats['total_recovered_amount']:.2f}"
    )

    print("=" * 70)


def print_test_stats():
    outcomes = load_test_outcomes()

    if not outcomes:
        print("No test outcomes found.")
        return

    recovered = sum(
        1
        for outcome in outcomes
        if outcome.get("recovered") is True
    )

    total = len(outcomes)

    recovered_amount = sum(
        float(outcome.get("recovery_amount", 0.0))
        for outcome in outcomes
    )

    print()
    print("=" * 70)
    print("RecoverOS X - TEST OUTCOME TRACKING")
    print("=" * 70)

    print(f"Test outcomes        : {total}")
    print(f"Recovered            : {recovered}")
    print(f"Not recovered        : {total - recovered}")
    print(f"Recovery rate        : {recovered / total:.2%}")
    print(f"Recovered amount     : ₹{recovered_amount:.2f}")

    print("=" * 70)


if __name__ == "__main__":

    print("=" * 70)
    print("RecoverOS X - Outcome Tracker Test")
    print("=" * 70)

    # IMPORTANT:
    # These are TEST records, so they go into
    # test_outcomes.jsonl and NEVER into outcomes.jsonl.

    record_test_outcome(
        payment_id="TEST001",
        amount=2500,
        failure_reason="bank_timeout",
        recommended_action="retry_payment",
        final_action="retry_payment",
        recovery_probability=0.8471,
        expected_revenue=2092.71,
        recovered=True,
        recovery_amount=2500,
    )

    record_test_outcome(
        payment_id="TEST002",
        amount=499,
        failure_reason="expired_card",
        recommended_action="send_update_link",
        final_action="send_update_link",
        recovery_probability=0.3025,
        expected_revenue=190.85,
        recovered=False,
        recovery_amount=0,
    )

    print_test_stats()

    print()
    print("Production outcomes were NOT modified.")
