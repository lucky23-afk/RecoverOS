import json
from datetime import datetime


def create_audit_record(payment, decision, result, safety):
    """
    Create one complete record of what RecoverOS decided.
    """

    return {
        "timestamp": datetime.now().isoformat(),

        "customer_id": payment["customer_id"],

        "payment": {
            "amount": payment["amount"],
            "failure_reason": payment["failure_reason"],
            "previous_successes": payment["previous_successes"],
            "previous_failures": payment["previous_failures"],
            "retry_count": payment["retry_count"]
        },

        "decision": {
            "category": decision["category"],
            "action": decision["action"],
            "confidence": round(
                decision["confidence"],
                4
            ),
            "expected_revenue": round(
                decision["expected_revenue"],
                2
            ),
            "reason": decision["reason"]
        },

        "safety": safety,

        "result": {
            "outcome": result["outcome"],
            "recovered_amount": result["recovered_amount"]
        }
    }


def save_audit_log(records, filename="../data/audit_log.json"):
    """
    Save all decisions to a JSON audit file.
    """

    with open(filename, "w") as file:

        json.dump(
            records,
            file,
            indent=4
        )
        