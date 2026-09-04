from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


# =================================================================
# PATH SETUP
# =================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# =================================================================
# DATABASE / CORE IMPORTS
# =================================================================

from database import initialize_database
from decision_orchestrator import run_orchestrator

from persistence import (
    get_recovery_metrics,
    get_entity_summary,
    persistence_health,
)

# =================================================================
# RECOVERY ENGINE IMPORTS
# =================================================================

from subscription_recovery import (
    start_subscription_recovery,
    execute_subscription_action,
    verify_subscription_payment,
    subscription_recovery_summary,
)

from mandate_retry import (
    start_mandate_recovery,
    execute_next_mandate_retry,
    verify_mandate_payment,
    mandate_recovery_summary,
)

from checkout_recovery import (
    start_checkout_recovery,
    execute_checkout_recovery,
    verify_checkout_payment,
    checkout_recovery_summary,
)

from receivables_recovery import (
    start_receivables_recovery,
    execute_receivables_action,
    record_receivables_promise,
    verify_receivables_payment,
    receivables_recovery_summary,
)
from voice_api import router as voice_router

# =================================================================
# FASTAPI APP
# =================================================================

app = FastAPI(
    title="RecoverOS X API",
    description="AI-powered revenue recovery backend",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://recover-os-delta.vercel.app",
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)

# =================================================================
# STARTUP
# =================================================================

@app.on_event("startup")
def startup() -> None:
    initialize_database()


# =================================================================
# PAYMENT DECISION SCHEMA
# =================================================================

class PaymentPayload(BaseModel):
    payment_id: str
    amount: float = Field(gt=0)

    failure_reason: str
    payment_method: str
    merchant_type: str

    previous_successes: int
    previous_failures: int
    retry_count: int = Field(ge=0)

    days_since_last_payment: int
    customer_tenure_months: int
    mandate_age_days: int

    average_amount: float
    amount_vs_average: float

    recent_success_rate: float = Field(
        ge=0,
        le=1,
    )

    failure_frequency: float = Field(
        ge=0,
        le=1,
    )

    retry_interval_hours: float

    risk_score: float = Field(
        ge=0,
        le=1,
    )


# =================================================================
# SUBSCRIPTION SCHEMA
# =================================================================

class SubscriptionStartRequest(BaseModel):
    subscription_id: str
    customer_id: str
    payment_id: str
    amount: float = Field(gt=0)
    failure_reason: str
    subscription_plan: str = "monthly"


class PaymentVerificationRequest(BaseModel):
    paid_amount: float = Field(gt=0)


# =================================================================
# MANDATE SCHEMA
# =================================================================

class MandateStartRequest(BaseModel):
    mandate_id: str
    customer_id: str
    payment_id: str
    amount: float = Field(gt=0)
    failure_reason: str
    mandate_type: str = "recurring"


# =================================================================
# CHECKOUT SCHEMA
# =================================================================

class CheckoutStartRequest(BaseModel):
    checkout_id: str
    customer_id: str
    payment_id: str
    amount: float = Field(gt=0)
    dropoff_reason: str
    checkout_stage: str = "payment"


# =================================================================
# RECEIVABLE SCHEMA
# =================================================================

class ReceivableStartRequest(BaseModel):
    invoice_id: str
    customer_id: str
    amount: float = Field(gt=0)
    days_overdue: int = Field(ge=0)
    due_date: str
    customer_name: str = "Demo Customer"
    invoice_currency: str = "INR"


class PromiseRequest(BaseModel):
    promised_date: str
    response: str


# =================================================================
# ROOT
# =================================================================

@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "RecoverOS X",
        "status": "running",
        "api": "FastAPI",
        "version": "2.0.0",
        "docs": "/docs",
    }


# =================================================================
# HEALTH
# =================================================================

@app.get("/health")
def health() -> dict[str, Any]:
    db_health = persistence_health()

    return {
        "service": "RecoverOS X",
        "status": "healthy",
        "api": "fastapi",
        "payment_execution": False,
        "database": db_health,
    }


# =================================================================
# DATABASE HEALTH
# =================================================================

@app.get("/database/health")
def database_health() -> dict[str, Any]:
    return persistence_health()


# =================================================================
# PAYMENT VALIDATION
# =================================================================

@app.post("/validate")
def validate(
    payment: PaymentPayload,
) -> dict[str, Any]:
    return {
        "valid": True,
        "reason": "Payment payload is valid.",
    }


# =================================================================
# MAIN PAYMENT DECISION
# =================================================================

@app.post("/decision")
def decision(
    payment: PaymentPayload,
) -> dict[str, Any]:

    payment_data = payment.model_dump()

    try:
        result = run_orchestrator(
            payment_data
        )

        return {
            "success": True,
            "valid": True,
            "payment_id": payment.payment_id,

            "recovery_probability":
                float(
                    result[
                        "recovery_probability"
                    ]
                ),

            "optimizer_action":
                result[
                    "optimizer_action"
                ],

            "erv_expected_recovered_value":
                float(
                    result.get(
                        "erv_expected_recovered_value",
                        0.0,
                    )
                ),

            "erv_ranked_actions":
                result.get(
                    "erv_ranked_actions",
                    [],
                ),

            "policy_decision":
                result[
                    "policy_decision"
                ],

            "policy_allowed_actions":
                result.get(
                    "policy_allowed_actions",
                    [],
                ),

            "policy_action":
                result[
                    "policy_action"
                ],

            "memory_action":
                result.get(
                    "memory_action"
                ),

            "safety_decision":
                result[
                    "safety_decision"
                ],

            "safety_action":
                result[
                    "safety_action"
                ],

            "final_action":
                result[
                    "final_action"
                ],

            "integrity_valid":
                result[
                    "integrity_valid"
                ],

            "integrity_reason":
                result[
                    "integrity_reason"
                ],

            "expected_revenue":
                float(
                    result[
                        "expected_revenue"
                    ]
                ),

            "policy_reasons":
                result.get(
                    "policy_reasons",
                    [],
                ),

            "safety_reasons":
                result.get(
                    "safety_reasons",
                    [],
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =================================================================
# GENERIC RAW DECISION
# =================================================================

@app.post("/decision/raw")
def decision_raw(
    payment: dict[str, Any] = Body(...),
) -> dict[str, Any]:

    try:
        result = run_orchestrator(
            payment
        )

        return {
            "success": True,
            "payment_id":
                payment.get(
                    "payment_id"
                ),
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =================================================================
# GLOBAL METRICS
# =================================================================

@app.get("/metrics")
def metrics() -> dict[str, Any]:
    try:
        return {
            "success": True,
            "metrics":
                get_recovery_metrics(),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =================================================================
# GENERIC ENTITY SUMMARY
# =================================================================

@app.get(
    "/recovery/{entity_type}/{entity_id}"
)
def recovery_summary(
    entity_type: str,
    entity_id: str,
) -> dict[str, Any]:

    allowed_types = {
        "payment",
        "subscription",
        "mandate",
        "checkout",
        "invoice",
        "receivable",
        "voice",
    }

    if entity_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported entity type. "
                f"Allowed: {sorted(allowed_types)}"
            ),
        )

    try:
        return get_entity_summary(
            entity_type,
            entity_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =================================================================
# SUBSCRIPTION RECOVERY
# =================================================================

@app.post(
    "/subscription/start"
)
def subscription_start(
    request: SubscriptionStartRequest,
) -> dict[str, Any]:

    try:
        subscription = (
            start_subscription_recovery(
                subscription_id=
                    request.subscription_id,
                customer_id=
                    request.customer_id,
                payment_id=
                    request.payment_id,
                amount=
                    request.amount,
                failure_reason=
                    request.failure_reason,
                subscription_plan=
                    request.subscription_plan,
            )
        )

        return {
            "success": True,
            "workflow": "subscription",
            "subscription":
                subscription,
            "summary":
                subscription_recovery_summary(
                    subscription
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/subscription/execute"
)
def subscription_execute(
    subscription: dict[str, Any] = Body(...),
) -> dict[str, Any]:

    try:
        result = (
            execute_subscription_action(
                subscription
            )
        )

        return {
            "success":
                result.get(
                    "success",
                    False,
                ),
            "workflow":
                "subscription",
            "result":
                result,
            "summary":
                subscription_recovery_summary(
                    subscription
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/subscription/verify"
)
def subscription_verify(
    subscription: dict[str, Any] = Body(...),
    request: PaymentVerificationRequest = Body(
        ...
    ),
) -> dict[str, Any]:

    try:
        result = (
            verify_subscription_payment(
                subscription,
                request.paid_amount,
            )
        )

        return {
            "success": True,
            "workflow": "subscription",
            "result": result,
            "summary":
                subscription_recovery_summary(
                    subscription
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =================================================================
# MANDATE RETRY
# =================================================================

@app.post(
    "/mandate/start"
)
def mandate_start(
    request: MandateStartRequest,
) -> dict[str, Any]:

    try:
        mandate = (
            start_mandate_recovery(
                mandate_id=
                    request.mandate_id,
                customer_id=
                    request.customer_id,
                payment_id=
                    request.payment_id,
                amount=
                    request.amount,
                failure_reason=
                    request.failure_reason,
                mandate_type=
                    request.mandate_type,
            )
        )

        return {
            "success": True,
            "workflow": "mandate",
            "mandate":
                mandate,
            "summary":
                mandate_recovery_summary(
                    mandate
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/mandate/execute"
)
def mandate_execute(
    mandate: dict[str, Any] = Body(...),
) -> dict[str, Any]:

    try:
        result = (
            execute_next_mandate_retry(
                mandate
            )
        )

        return {
            "success":
                result.get(
                    "success",
                    False,
                ),
            "workflow": "mandate",
            "result":
                result,
            "summary":
                mandate_recovery_summary(
                    mandate
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/mandate/verify"
)
def mandate_verify(
    mandate: dict[str, Any] = Body(...),
    request: PaymentVerificationRequest = Body(
        ...
    ),
) -> dict[str, Any]:

    try:
        result = (
            verify_mandate_payment(
                mandate,
                request.paid_amount,
            )
        )

        return {
            "success": True,
            "workflow": "mandate",
            "result": result,
            "summary":
                mandate_recovery_summary(
                    mandate
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =================================================================
# CHECKOUT RECOVERY
# =================================================================

@app.post(
    "/checkout/start"
)
def checkout_start(
    request: CheckoutStartRequest,
) -> dict[str, Any]:

    try:
        checkout = (
            start_checkout_recovery(
                checkout_id=
                    request.checkout_id,
                customer_id=
                    request.customer_id,
                payment_id=
                    request.payment_id,
                amount=
                    request.amount,
                dropoff_reason=
                    request.dropoff_reason,
                checkout_stage=
                    request.checkout_stage,
            )
        )

        return {
            "success": True,
            "workflow": "checkout",
            "checkout":
                checkout,
            "summary":
                checkout_recovery_summary(
                    checkout
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/checkout/execute"
)
def checkout_execute(
    checkout: dict[str, Any] = Body(...),
) -> dict[str, Any]:

    try:
        result = (
            execute_checkout_recovery(
                checkout
            )
        )

        return {
            "success":
                result.get(
                    "success",
                    False,
                ),
            "workflow": "checkout",
            "result":
                result,
            "summary":
                checkout_recovery_summary(
                    checkout
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/checkout/verify"
)
def checkout_verify(
    checkout: dict[str, Any] = Body(...),
    request: PaymentVerificationRequest = Body(
        ...
    ),
) -> dict[str, Any]:

    try:
        result = (
            verify_checkout_payment(
                checkout,
                request.paid_amount,
            )
        )

        return {
            "success": True,
            "workflow": "checkout",
            "result": result,
            "summary":
                checkout_recovery_summary(
                    checkout
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =================================================================
# B2B RECEIVABLES
# =================================================================

@app.post(
    "/receivables/start"
)
def receivables_start(
    request: ReceivableStartRequest,
) -> dict[str, Any]:

    try:
        receivable = (
            start_receivables_recovery(
                invoice_id=
                    request.invoice_id,
                customer_id=
                    request.customer_id,
                amount=
                    request.amount,
                days_overdue=
                    request.days_overdue,
                due_date=
                    request.due_date,
                customer_name=
                    request.customer_name,
                invoice_currency=
                    request.invoice_currency,
            )
        )

        return {
            "success": True,
            "workflow": "receivables",
            "receivable":
                receivable,
            "summary":
                receivables_recovery_summary(
                    receivable
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/receivables/execute"
)
def receivables_execute(
    receivable: dict[str, Any] = Body(...),
) -> dict[str, Any]:

    try:
        result = (
            execute_receivables_action(
                receivable
            )
        )

        return {
            "success":
                result.get(
                    "success",
                    False,
                ),
            "workflow":
                "receivables",
            "result":
                result,
            "summary":
                receivables_recovery_summary(
                    receivable
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/receivables/promise"
)
def receivables_promise(
    receivable: dict[str, Any] = Body(...),
    request: PromiseRequest = Body(
        ...
    ),
) -> dict[str, Any]:

    try:
        result = (
            record_receivables_promise(
                receivable,
                request.promised_date,
                request.response,
            )
        )

        return {
            "success":
                result.get(
                    "success",
                    False,
                ),
            "workflow":
                "receivables",
            "result":
                result,
            "summary":
                receivables_recovery_summary(
                    receivable
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post(
    "/receivables/verify"
)
def receivables_verify(
    receivable: dict[str, Any] = Body(...),
    request: PaymentVerificationRequest = Body(
        ...
    ),
) -> dict[str, Any]:

    try:
        result = (
            verify_receivables_payment(
                receivable,
                request.paid_amount,
            )
        )

        return {
            "success": True,
            "workflow":
                "receivables",
            "result": result,
            "summary":
                receivables_recovery_summary(
                    receivable
                ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =================================================================
# RUN SERVER
# =================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("RecoverOS X - FASTAPI BACKEND")
    print("=" * 70)
    print(
        "API      : "
        "http://127.0.0.1:8000"
    )
    print(
        "Docs     : "
        "http://127.0.0.1:8000/docs"
    )
    print("=" * 70)

    uvicorn.run(
        "app.api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )