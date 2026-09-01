

from pathlib import Path
import sys
from datetime import datetime, timezone
import json


# ================================================================
# PATH SETUP
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ================================================================
# IMPORTS
# ================================================================

from ml_model import predict_recovery_probability
from strategy_optimizer import optimize_strategy
from policy_engine import evaluate_policy
from safety_engine import evaluate_safety

# Recovery memory is optional so the main pipeline does not crash
# if the memory module is temporarily unavailable.
try:
    from recovery_memory import recommend_from_memory
    MEMORY_AVAILABLE = True
except ImportError:
    recommend_from_memory = None
    MEMORY_AVAILABLE = False


# ================================================================
# CONFIGURATION
# ================================================================

AUDIT_FILE = DATA_DIR / "decision_audit.jsonl"


# ================================================================
# HELPERS
# ================================================================

def print_line():
    print("-" * 70)


def get_value(obj, key, default=None):
    """
    Supports both dictionary-style and object-style results.
    """
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def save_audit(record):
    """
    Save one decision to the audit log.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(AUDIT_FILE, "a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False
            ) + "\n"
        )


# ================================================================
# MAIN ORCHESTRATOR
# ================================================================

def run_orchestrator(payment):
    print("=" * 70)
    print("RecoverOS X - DECISION ORCHESTRATOR")
    print("=" * 70)

    # ============================================================
    # 1. ML PREDICTION
    # ============================================================

    recovery_probability = predict_recovery_probability(payment)

    # ============================================================
    # 2. STRATEGY OPTIMIZER
    # ============================================================

    best_strategy, all_strategies = optimize_strategy(
        amount=float(payment["amount"]),
        recovery_probability=float(recovery_probability),
        retry_count=int(payment.get("retry_count", 0)),
        risk_score=float(payment.get("risk_score", 0.0)),
    )

    optimizer_action = best_strategy.action

    # ============================================================
    # 3. DETERMINISTIC POLICY
    # ============================================================

    policy_result = evaluate_policy(
        payment,
        int(payment.get("retry_count", 0)),
        float(recovery_probability),
    )

    policy_decision = get_value(
        policy_result,
        "decision",
        "BLOCK",
    )

    allowed_actions = get_value(
        policy_result,
        "allowed_actions",
        [],
    )

    policy_reasons = get_value(
        policy_result,
        "reasons",
        [],
    )

    if allowed_actions is None:
        allowed_actions = []

    # ============================================================
    # 4. POLICY-CONSTRAINED OPTIMIZATION
    # ============================================================

    allowed_set = set(allowed_actions)

    policy_approved_strategies = [
        strategy
        for strategy in all_strategies
        if strategy.action in allowed_set
    ]

    if policy_approved_strategies:
        policy_best_strategy = max(
            policy_approved_strategies,
            key=lambda strategy: strategy.score,
        )

        policy_action = policy_best_strategy.action
        policy_expected_revenue = (
            policy_best_strategy.expected_revenue
        )

    else:
        policy_action = "hold_for_review"

        policy_expected_revenue = 0.0

    # ============================================================
    # 5. RECOVERY MEMORY
    # ============================================================

    memory_action = None
    memory_recovery_rate = None
    memory_revenue = None

    if MEMORY_AVAILABLE:
        try:
            memory_result = recommend_from_memory(
                payment
            )

            if memory_result:
                memory_action = get_value(
                    memory_result,
                    "recommended_action",
                    None,
                )

                if memory_action is None:
                    memory_action = get_value(
                        memory_result,
                        "action",
                        None,
                    )

                memory_recovery_rate = get_value(
                    memory_result,
                    "historical_recovery",
                    None,
                )

                memory_revenue = get_value(
                    memory_result,
                    "recovered_revenue",
                    None,
                )

        except Exception:
            # Memory must never break the decision pipeline.
            memory_action = None

    # ============================================================
    # 6. MEMORY-AWARE ACTION SELECTION
    # ============================================================

    #
    # Memory is advisory only.
    #
    # It can influence the decision only if:
    #
    # 1. The action is allowed by policy.
    # 2. Safety later approves it.
    #
    # Otherwise the policy optimizer remains the source of truth.
    #

    candidate_action = policy_action

    if (
        memory_action
        and memory_action in allowed_set
    ):
        candidate_action = memory_action

    # ============================================================
    # 7. SAFETY ENGINE
    # ============================================================

    safety_result = evaluate_safety(
        payment=payment,
        recommended_action=candidate_action,
        recovery_probability=float(recovery_probability),
    )

    safety_decision = get_value(
        safety_result,
        "decision",
        "BLOCK",
    )

    safety_final_action = get_value(
        safety_result,
        "final_action",
        "blocked",
    )

    safety_reasons = get_value(
        safety_result,
        "reasons",
        [],
    )

    if safety_reasons is None:
        safety_reasons = []

    # ============================================================
    # 8. FINAL DECISION
    # ============================================================

    if str(safety_decision).upper() == "ALLOW":
        final_action = safety_final_action
    else:
        final_action = "blocked"

    # ============================================================
    # 9. INTEGRITY CHECK
    # ============================================================

    integrity_valid = True
    integrity_reason = "Decision integrity checks passed."

    if policy_decision == "BLOCK":
        if final_action not in {"hold_for_review", "blocked"}:
            integrity_valid = False
            integrity_reason = (
                "Final action violates blocked policy."
            )

    if (
        final_action != "blocked"
        and final_action not in allowed_set
    ):
        integrity_valid = False
        integrity_reason = (
            "Final action is not permitted by policy."
        )

    if not integrity_valid:
        final_action = "blocked"

    # ============================================================
    # 10. DISPLAY
    # ============================================================

    print()
    print("DECISION CHAIN")
    print_line()

    print(
        f"ML probability       : "
        f"{float(recovery_probability):.2%}"
    )

    print(
        f"Optimizer action     : "
        f"{optimizer_action}"
    )

    print(
        f"Policy action        : "
        f"{policy_action}"
    )

    if memory_action:
        print(
            f"Memory recommendation: "
            f"{memory_action}"
        )

    print(
        f"Safety decision      : "
        f"{safety_decision}"
    )

    print(
        f"Final action         : "
        f"{final_action}"
    )

    print()
    print("INTEGRITY CHECK")
    print_line()

    print(
        f"Valid                : "
        f"{integrity_valid}"
    )

    print(
        f"Reason               : "
        f"{integrity_reason}"
    )

    # ============================================================
    # 11. AUDIT RECORD
    # ============================================================

    audit_record = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "payment_id": payment.get(
            "payment_id"
        ),

        "amount": float(
            payment.get("amount", 0.0)
        ),

        "failure_reason": payment.get(
            "failure_reason"
        ),

        "recovery_probability": float(
            recovery_probability
        ),

        "optimizer_action": optimizer_action,

        "policy_decision": policy_decision,

        "policy_action": policy_action,

        "memory_action": memory_action,

        "safety_decision": safety_decision,

        "safety_action": safety_final_action,

        "final_action": final_action,

        "integrity_valid": integrity_valid,

        "integrity_reason": integrity_reason,
    }

    save_audit(audit_record)

    print()
    print("AUDIT")
    print_line()

    print(
        f"Saved to             : "
        f"{AUDIT_FILE}"
    )

    print()
    print("=" * 70)
    print("RecoverOS X decision orchestration completed.")
    print("=" * 70)

    return {
        "payment": payment,
        "recovery_probability": recovery_probability,
        "optimizer_action": optimizer_action,
        "policy_decision": policy_decision,
        "policy_action": policy_action,
        "memory_action": memory_action,
        "safety_decision": safety_decision,
        "safety_action": safety_final_action,
        "final_action": final_action,
        "integrity_valid": integrity_valid,
        "integrity_reason": integrity_reason,
        "expected_revenue": policy_expected_revenue,
        "policy_reasons": policy_reasons,
        "safety_reasons": safety_reasons,
    }


# ================================================================
# DEMO PAYMENT
# ================================================================

if __name__ == "__main__":

    payment = {
        "payment_id": "PX000001",
        "amount": 2500,

        "failure_reason": "bank_timeout",
        "payment_method": "netbanking",
        "merchant_type": "saas",

        "previous_successes": 8,
        "previous_failures": 1,
        "retry_count": 1,

        "days_since_last_payment": 12,
        "customer_tenure_months": 18,
        "mandate_age_days": 240,

        "average_amount": 2300,
        "amount_vs_average": 1.087,

        "recent_success_rate": 0.89,
        "failure_frequency": 0.05,

        "retry_interval_hours": 6,

        "risk_score": 0.10,
    }

    run_orchestrator(payment)

