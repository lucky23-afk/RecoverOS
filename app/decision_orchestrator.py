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
from erv_optimizer import optimize_recovery_action
from policy_engine import evaluate_policy
from safety_engine import evaluate_safety


# Recovery memory is advisory only.
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

def get_value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def save_audit(record):
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        AUDIT_FILE,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def print_line():
    print("-" * 70)


# ================================================================
# POLICY-CONSTRAINED ERV SELECTION
# ================================================================

def choose_policy_allowed_action(
    ranked_actions,
    allowed_actions,
):
    """
    ERV ranks actions economically.

    Policy acts as a hard constraint.

    The highest-ERV action that policy permits is selected.
    """

    allowed = set(
        allowed_actions or []
    )

    candidates = [
        action
        for action in ranked_actions
        if action.get("action") in allowed
    ]

    if not candidates:
        return {
            "action": "hold_for_review",
            "expected_recovered_value": 0.0,
        }

    return max(
        candidates,
        key=lambda row: row.get(
            "expected_recovered_value",
            0.0,
        ),
    )


# ================================================================
# MAIN ORCHESTRATOR
# ================================================================

def run_orchestrator(payment):
    print("=" * 70)
    print("RecoverOS X - DECISION ORCHESTRATOR")
    print("=" * 70)

    # ============================================================
    # 1. ML MODEL
    # ============================================================

    recovery_probability = (
        predict_recovery_probability(
            payment
        )
    )

    recovery_probability = float(
        recovery_probability
    )

    # ============================================================
    # 2. ERV OPTIMIZER
    # ============================================================

    erv_result = optimize_recovery_action(
        amount=float(
            payment["amount"]
        ),
        recovery_probability=
            recovery_probability,
        failure_reason=payment.get(
            "failure_reason",
            "",
        ),
        retry_count=int(
            payment.get(
                "retry_count",
                0,
            )
        ),
        risk_score=float(
            payment.get(
                "risk_score",
                0.0,
            )
        ),
    )

    optimizer_action = (
        erv_result["action"]
    )

    ranked_actions = (
        erv_result["ranked_actions"]
    )

    # ============================================================
    # 3. POLICY
    # ============================================================

    policy_result = evaluate_policy(
        payment.get(
            "failure_reason",
            "",
        ),
        int(
            payment.get(
                "retry_count",
                0,
            )
        ),
        recovery_probability,
    )

    policy_decision = get_value(
        policy_result,
        "decision",
        "REVIEW",
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

    if policy_reasons is None:
        policy_reasons = []

    # ============================================================
    # 4. POLICY-CONSTRAINED ERV
    # ============================================================

    policy_best = (
        choose_policy_allowed_action(
            ranked_actions,
            allowed_actions,
        )
    )

    policy_action = policy_best[
        "action"
    ]

    policy_expected_revenue = (
        policy_best.get(
            "expected_recovered_value",
            0.0,
        )
    )

    # ============================================================
    # 5. RECOVERY MEMORY
    # ============================================================

    memory_action = None
    memory_recovery_rate = None
    memory_revenue = None

    if MEMORY_AVAILABLE:
        try:
            memory_result = (
                recommend_from_memory(
                    payment
                )
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

                memory_recovery_rate = (
                    get_value(
                        memory_result,
                        "historical_recovery",
                        None,
                    )
                )

                memory_revenue = (
                    get_value(
                        memory_result,
                        "recovered_revenue",
                        None,
                    )
                )

        except Exception:
            # Memory is advisory and must never break
            # the financial decision pipeline.
            memory_action = None

    # ============================================================
    # AUTHORITATIVE PATH
    #
    # ML -> ERV -> POLICY
    #
    # Memory does not override this path.
    # ============================================================

    candidate_action = policy_action

    # ============================================================
    # 6. SAFETY
    # ============================================================

    safety_result = evaluate_safety(
        payment=payment,
        recommended_action=candidate_action,
        recovery_probability=recovery_probability,
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
    # 7. FINAL ACTION
    #
    # IMPORTANT:
    # ALLOW  -> recommended action
    # REVIEW -> human review
    # BLOCK  -> blocked
    #
    # REVIEW must NOT be converted to BLOCK.
    # ============================================================

    normalized_safety_decision = str(
        safety_decision
    ).upper()

    if normalized_safety_decision == "ALLOW":
        final_action = safety_final_action

    elif normalized_safety_decision == "REVIEW":
        final_action = "hold_for_review"

    else:
        final_action = "blocked"

    # ============================================================
    # 8. INTEGRITY CHECK
    # ============================================================

    integrity_valid = True

    integrity_reason = (
        "Decision integrity checks passed."
    )

    # Final executable action must be policy-approved.
    if (
        final_action != "blocked"
        and final_action
        not in set(allowed_actions)
    ):
        integrity_valid = False

        integrity_reason = (
            "Final action is not permitted by policy."
        )

    # Safety remains the final authority.
    if (
        normalized_safety_decision == "BLOCK"
        and final_action != "blocked"
    ):
        integrity_valid = False

        integrity_reason = (
            "Final action violates safety decision."
        )

    if not integrity_valid:
        final_action = "blocked"

    # ============================================================
    # 9. DISPLAY
    # ============================================================

    print()
    print("DECISION CHAIN")
    print_line()

    print(
        f"ML probability       : "
        f"{recovery_probability:.2%}"
    )

    print(
        f"ERV optimizer        : "
        f"{optimizer_action}"
    )

    print(
        f"Policy allowed       : "
        f"{', '.join(allowed_actions)}"
    )

    print(
        f"Policy-selected ERV  : "
        f"{policy_action}"
    )

    print(
        f"Expected recovered   : "
        f"₹{policy_expected_revenue:,.2f}"
    )

    if memory_action:
        print(
            f"Memory advisory      : "
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
    # 10. AUDIT
    # ============================================================

    audit_record = {
        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "payment_id":
            payment.get(
                "payment_id"
            ),

        "amount":
            float(
                payment.get(
                    "amount",
                    0.0,
                )
            ),

        "failure_reason":
            payment.get(
                "failure_reason"
            ),

        "recovery_probability":
            recovery_probability,

        "optimizer_action":
            optimizer_action,

        "erv_expected_recovered_value":
            erv_result.get(
                "expected_recovered_value",
                0.0,
            ),

        "erv_ranked_actions":
            ranked_actions,

        "policy_decision":
            policy_decision,

        "policy_allowed_actions":
            allowed_actions,

        "policy_action":
            policy_action,

        "policy_expected_recovered_value":
            policy_expected_revenue,

        "memory_action":
            memory_action,

        "memory_recovery_rate":
            memory_recovery_rate,

        "memory_revenue":
            memory_revenue,

        "safety_decision":
            safety_decision,

        "safety_action":
            safety_final_action,

        "final_action":
            final_action,

        "integrity_valid":
            integrity_valid,

        "integrity_reason":
            integrity_reason,
    }

    save_audit(
        audit_record
    )

    print()
    print("AUDIT")
    print_line()

    print(
        f"Saved to             : "
        f"{AUDIT_FILE}"
    )

    print()

    print("=" * 70)
    print(
        "RecoverOS X decision orchestration completed."
    )
    print("=" * 70)

    # ============================================================
    # API / OTHER MODULES
    # ============================================================

    return {
        "payment":
            payment,

        "recovery_probability":
            recovery_probability,

        "optimizer_action":
            optimizer_action,

        "erv_expected_recovered_value":
            erv_result.get(
                "expected_recovered_value",
                0.0,
            ),

        "erv_ranked_actions":
            ranked_actions,

        "policy_decision":
            policy_decision,

        "policy_allowed_actions":
            allowed_actions,

        "policy_action":
            policy_action,

        "memory_action":
            memory_action,

        "safety_decision":
            safety_decision,

        "safety_action":
            safety_final_action,

        "final_action":
            final_action,

        "integrity_valid":
            integrity_valid,

        "integrity_reason":
            integrity_reason,

        "expected_revenue":
            policy_expected_revenue,

        "policy_reasons":
            policy_reasons,

        "safety_reasons":
            safety_reasons,
    }


# ================================================================
# LOCAL DEMO
# ================================================================

if __name__ == "__main__":

    payment = {
        "payment_id":
            "PX000001",

        "amount":
            2500,

        "failure_reason":
            "bank_timeout",

        "payment_method":
            "netbanking",

        "merchant_type":
            "saas",

        "previous_successes":
            8,

        "previous_failures":
            1,

        "retry_count":
            1,

        "days_since_last_payment":
            12,

        "customer_tenure_months":
            18,

        "mandate_age_days":
            240,

        "average_amount":
            2300,

        "amount_vs_average":
            1.087,

        "recent_success_rate":
            0.89,

        "failure_frequency":
            0.05,

        "retry_interval_hours":
            6,

        "risk_score":
            0.10,
    }

    run_orchestrator(
        payment
    )