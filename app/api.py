
from flask import Flask, jsonify, request
from pathlib import Path
import sys


# ================================================================
# PATH SETUP
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ================================================================
# IMPORT ORCHESTRATOR
# ================================================================

from decision_orchestrator import run_orchestrator


# ================================================================
# FLASK APP
# ================================================================

app = Flask(__name__)


# ================================================================
# REQUIRED PAYMENT FIELDS
# ================================================================

REQUIRED_FIELDS = [
    "payment_id",
    "amount",
    "failure_reason",
    "payment_method",
    "merchant_type",
    "previous_successes",
    "previous_failures",
    "retry_count",
    "days_since_last_payment",
    "customer_tenure_months",
    "mandate_age_days",
    "average_amount",
    "amount_vs_average",
    "recent_success_rate",
    "failure_frequency",
    "retry_interval_hours",
    "risk_score",
]


# ================================================================
# VALIDATION
# ================================================================

def validate_payment(payment):
    if not isinstance(payment, dict):
        return False, "Payment payload must be a JSON object."

    missing = [
        field
        for field in REQUIRED_FIELDS
        if field not in payment
    ]

    if missing:
        return False, (
            "Missing required fields: "
            + ", ".join(missing)
        )

    try:
        if float(payment["amount"]) <= 0:
            return False, "Amount must be greater than zero."

        if int(payment["retry_count"]) < 0:
            return False, "Retry count cannot be negative."

        if not 0 <= float(payment["risk_score"]) <= 1:
            return False, "Risk score must be between 0 and 1."

        if not 0 <= float(payment["recent_success_rate"]) <= 1:
            return False, (
                "Recent success rate must be between 0 and 1."
            )

        if not 0 <= float(payment["failure_frequency"]) <= 1:
            return False, (
                "Failure frequency must be between 0 and 1."
            )

    except (TypeError, ValueError):
        return False, "One or more numeric fields are invalid."

    return True, "Payment payload is valid."


# ================================================================
# HEALTH CHECK
# ================================================================

@app.get("/health")
def health():
    return jsonify({
        "service": "RecoverOS X",
        "status": "healthy",
        "payment_execution": False,
    })


# ================================================================
# VALIDATION ENDPOINT
# ================================================================

@app.post("/validate")
def validate():
    payment = request.get_json(silent=True)

    valid, reason = validate_payment(payment)

    return jsonify({
        "valid": valid,
        "reason": reason,
    })


# ================================================================
# DECISION ENDPOINT
# ================================================================

@app.post("/decision")
def decision():
    payment = request.get_json(silent=True)

    valid, reason = validate_payment(payment)

    if not valid:
        return jsonify({
            "success": False,
            "valid": False,
            "error": reason,
        }), 400

    try:
        result = run_orchestrator(payment)

        return jsonify({
            "success": True,
            "valid": True,
            "payment_id": payment["payment_id"],
            "recovery_probability": float(
                result["recovery_probability"]
            ),
            "optimizer_action": result["optimizer_action"],
            "policy_decision": result["policy_decision"],
            "policy_action": result["policy_action"],
            "memory_action": result["memory_action"],
            "safety_decision": result["safety_decision"],
            "safety_action": result["safety_action"],
            "final_action": result["final_action"],
            "integrity_valid": result["integrity_valid"],
            "integrity_reason": result["integrity_reason"],
            "expected_revenue": float(
                result["expected_revenue"]
            ),
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "valid": True,
            "error": str(exc),
        }), 500


# ================================================================
# LOCAL TEST
# ================================================================

def run_test():
    print("=" * 70)
    print("RecoverOS X - API LAYER TEST")
    print("=" * 70)

    test_payment = {
        "payment_id": "API_TEST_001",
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

    print()
    print("VALIDATION")
    print("-" * 70)

    valid, reason = validate_payment(test_payment)

    print(f"Valid : {valid}")
    print(f"Reason: {reason}")

    print()
    print("API layer initialized successfully.")
    print("Payment execution is NOT performed by this service.")

    print("=" * 70)


# ================================================================
# START SERVER
# ================================================================

if __name__ == "__main__":
    run_test()

    print()
    print("Starting RecoverOS X API server...")
    print("Health endpoint : http://127.0.0.1:5000/health")
    print("Decision endpoint: http://127.0.0.1:5000/decision")
    print()
    print("Press CTRL+C to stop the server.")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )

