
from pathlib import Path
import sys
from datetime import datetime, timezone

from flask import Flask, jsonify, request

# Allow imports from the app directory when this file is run directly.
APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from outcome_tracker import record_outcome


app = Flask(__name__)


def validate_outcome(payload):
    required = [
        "payment_id",
        "amount",
        "failure_reason",
        "recommended_action",
        "final_action",
        "recovery_probability",
        "expected_revenue",
        "recovered",
    ]

    missing = [
        field
        for field in required
        if field not in payload
    ]

    if missing:
        return False, f"Missing fields: {', '.join(missing)}"

    try:
        float(payload["amount"])
        float(payload["recovery_probability"])
        float(payload["expected_revenue"])
    except (TypeError, ValueError):
        return False, "amount, recovery_probability and expected_revenue must be numeric."

    if not isinstance(payload["recovered"], bool):
        return False, "recovered must be true or false."

    probability = float(payload["recovery_probability"])

    if not 0 <= probability <= 1:
        return False, "recovery_probability must be between 0 and 1."

    if float(payload["amount"]) < 0:
        return False, "amount cannot be negative."

    if float(payload["expected_revenue"]) < 0:
        return False, "expected_revenue cannot be negative."

    if payload["recovered"]:
        if "recovery_amount" not in payload:
            return False, "recovery_amount is required when recovered=true."

        try:
            recovery_amount = float(payload["recovery_amount"])
        except (TypeError, ValueError):
            return False, "recovery_amount must be numeric."

        if recovery_amount < 0:
            return False, "recovery_amount cannot be negative."

    return True, "Outcome payload is valid."


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "RecoverOS X outcome API healthy",
            "production_outcome_recording": True,
        }
    )


@app.post("/outcome")
def create_outcome():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {
                "success": False,
                "error": "Request body must be JSON.",
            }
        ), 400

    valid, reason = validate_outcome(payload)

    if not valid:
        return jsonify(
            {
                "success": False,
                "valid": False,
                "error": reason,
            }
        ), 400

    recovery_amount = float(
        payload.get("recovery_amount", 0.0)
    )

    outcome = record_outcome(
        payment_id=payload["payment_id"],
        amount=payload["amount"],
        failure_reason=payload["failure_reason"],
        recommended_action=payload["recommended_action"],
        final_action=payload["final_action"],
        recovery_probability=payload["recovery_probability"],
        expected_revenue=payload["expected_revenue"],
        recovered=payload["recovered"],
        recovery_amount=recovery_amount,
    )

    outcome["recorded_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    return jsonify(
        {
            "success": True,
            "message": "Production outcome recorded.",
            "outcome": outcome,
        }
    ), 201


if __name__ == "__main__":
    print("=" * 70)
    print("RecoverOS X - OUTCOME API")
    print("=" * 70)

    print()
    print("Health endpoint  : http://127.0.0.1:5001/health")
    print("Outcome endpoint : http://127.0.0.1:5001/outcome")

    print()
    print("IMPORTANT")
    print("-" * 70)
    print("This API records OBSERVED payment outcomes.")
    print("It does not execute payments.")
    print("Only actual outcomes are eligible for learning.")

    print()
    print("Starting outcome API server...")
    print("Press CTRL+C to stop the server.")

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=False,
    )

