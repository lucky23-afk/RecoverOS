from pathlib import Path
import json
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_FILE = DATA_DIR / "recovery_memory.json"


def load_memory():
    """Load persistent recovery strategy memory."""

    if not MEMORY_FILE.exists():
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        pass

    return []


def save_memory(memory):
    """Persist recovery strategy memory."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temporary_file = MEMORY_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2)

    temporary_file.replace(MEMORY_FILE)


def build_memory_key(
    failure_reason,
    payment_method,
    merchant_type,
):
    """Create a stable context key for strategy learning."""

    return "|".join(
        [
            str(failure_reason).strip().lower(),
            str(payment_method).strip().lower(),
            str(merchant_type).strip().lower(),
        ]
    )


def record_strategy_outcome(
    failure_reason,
    payment_method,
    merchant_type,
    action,
    recovered,
    recovery_amount=0.0,
):
    """
    Record what happened after a recovery strategy was used.

    This is observational memory only.
    It does NOT modify the production model.
    """

    memory = load_memory()

    key = build_memory_key(
        failure_reason,
        payment_method,
        merchant_type,
    )

    matching = None

    for record in memory:
        if record.get("context_key") == key:
            matching = record
            break

    if matching is None:
        matching = {
            "context_key": key,
            "failure_reason": failure_reason,
            "payment_method": payment_method,
            "merchant_type": merchant_type,
            "strategies": {},
            "updated_at": None,
        }

        memory.append(matching)

    strategies = matching.setdefault("strategies", {})

    strategy = strategies.setdefault(
        action,
        {
            "attempts": 0,
            "recoveries": 0,
            "recovery_rate": 0.0,
            "recovered_amount": 0.0,
        },
    )

    strategy["attempts"] += 1

    if recovered:
        strategy["recoveries"] += 1

    strategy["recovered_amount"] += float(recovery_amount)

    strategy["recovery_rate"] = (
        strategy["recoveries"] / strategy["attempts"]
    )

    matching["updated_at"] = datetime.now().isoformat()

    save_memory(memory)

    return strategy


def get_strategy_memory(
    failure_reason,
    payment_method,
    merchant_type,
):
    """Return learned strategy performance for a context."""

    memory = load_memory()

    key = build_memory_key(
        failure_reason,
        payment_method,
        merchant_type,
    )

    for record in memory:
        if record.get("context_key") == key:
            return record

    return None


def recommend_from_memory(
    failure_reason,
    payment_method,
    merchant_type,
    allowed_actions=None,
):
    """
    Recommend the historically strongest strategy.

    Memory can recommend, but cannot override policy.
    """

    record = get_strategy_memory(
        failure_reason,
        payment_method,
        merchant_type,
    )

    if not record:
        return None

    strategies = record.get("strategies", {})

    if allowed_actions is not None:
        allowed_actions = set(allowed_actions)

    candidates = []

    for action, stats in strategies.items():

        if allowed_actions is not None:
            if action not in allowed_actions:
                continue

        attempts = stats.get("attempts", 0)
        recovery_rate = stats.get("recovery_rate", 0.0)
        recovered_amount = stats.get("recovered_amount", 0.0)

        if attempts <= 0:
            continue

        candidates.append(
            (
                recovery_rate,
                recovered_amount,
                action,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    best = candidates[0]

    return {
        "action": best[2],
        "recovery_rate": best[0],
        "recovered_amount": best[1],
        "source": "recovery_memory",
    }


def print_memory():

    memory = load_memory()

    print()
    print("=" * 70)
    print("RecoverOS X - RECOVERY MEMORY")
    print("=" * 70)

    print()
    print("MEMORY RECORDS")
    print("-" * 70)

    print(f"Contexts stored      : {len(memory)}")

    for record in memory:

        print()
        print(
            f"Context              : "
            f"{record.get('context_key', 'unknown')}"
        )

        strategies = record.get("strategies", {})

        for action, stats in strategies.items():

            print(
                f" - {action:<20} "
                f"Attempts: {stats.get('attempts', 0):<3} "
                f"Recovery: "
                f"{stats.get('recovery_rate', 0.0):.2%} "
                f"Revenue: "
                f"₹{stats.get('recovered_amount', 0.0):.2f}"
            )

    print()
    print("=" * 70)


if __name__ == "__main__":

    print("=" * 70)
    print("RecoverOS X - RECOVERY MEMORY TEST")
    print("=" * 70)

    record_strategy_outcome(
        failure_reason="bank_timeout",
        payment_method="netbanking",
        merchant_type="saas",
        action="retry_payment",
        recovered=True,
        recovery_amount=2500,
    )

    record_strategy_outcome(
        failure_reason="bank_timeout",
        payment_method="netbanking",
        merchant_type="saas",
        action="send_update_link",
        recovered=False,
        recovery_amount=0,
    )

    record_strategy_outcome(
        failure_reason="bank_timeout",
        payment_method="netbanking",
        merchant_type="saas",
        action="retry_payment",
        recovered=True,
        recovery_amount=2500,
    )

    recommendation = recommend_from_memory(
        failure_reason="bank_timeout",
        payment_method="netbanking",
        merchant_type="saas",
        allowed_actions=[
            "retry_payment",
            "send_update_link",
            "send_reminder",
            "hold_for_review",
        ],
    )

    print_memory()

    print()
    print("MEMORY RECOMMENDATION")
    print("-" * 70)

    if recommendation:
        print(f"Recommended action  : {recommendation['action']}")
        print(
            f"Historical recovery : "
            f"{recommendation['recovery_rate']:.2%}"
        )
        print(
            f"Recovered revenue   : "
            f"₹{recommendation['recovered_amount']:.2f}"
        )
        print(f"Source              : {recommendation['source']}")
    else:
        print("No learned strategy available.")

    print()
    print("=" * 70)
    print("Recovery memory test completed.")
    print("=" * 70)