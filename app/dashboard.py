from pathlib import Path

import json
import pandas as pd
import streamlit as st

from voice_recovery import (
    start_voice_recovery,
    generate_opening,
    verify_payment,
    transcribe_hinglish_audio,
    generate_voice_response,
    process_conversation_turn,
)

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

# =================================================================
# RecoverOS - PRODUCTION DASHBOARD
# =================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"
REGISTRY_FILE = DATA_DIR / "model_registry.json"
EXPERIMENT_SUMMARY_FILE = (
    DATA_DIR / "recovery_experiment_summary.json"
)


# =================================================================
# PAGE CONFIG
# =================================================================

st.set_page_config(
    page_title="RecoverOS",
    page_icon="💳",
    layout="wide",
)


# =================================================================
# HELPERS
# =================================================================

def load_json_file(path):
    if not path.exists():
        return {}

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)
    except Exception:
        return {}


def load_outcomes():
    records = []

    if not OUTCOMES_FILE.exists():
        return records

    with open(
        OUTCOMES_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)

            except json.JSONDecodeError:
                continue

            records.append(record)

    return records


def is_production(record):
    """
    Only genuine production outcomes are included.

    Explicit sandbox/demo/test records are excluded.
    """

    production_flag = record.get("production")

    data_source = str(
        record.get(
            "data_source",
            "",
        )
    ).upper()

    mode = str(
        record.get(
            "mode",
            "",
        )
    ).upper()

    return (
        production_flag is True
        and data_source not in {
            "SANDBOX",
            "DEMO",
            "DEMO_SIMULATION",
            "TEST",
            "TEST_SIMULATION",
        }
        and mode not in {
            "SANDBOX",
            "DEMO",
            "TEST",
        }
    )


def load_production_outcomes():
    return [
        record
        for record in load_outcomes()
        if is_production(record)
    ]


def money(value):
    try:
        return f"₹{float(value):,.2f}"
    except Exception:
        return "₹0.00"


def percentage(value):
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "0.00%"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def load_experiment_summary():

    if not EXPERIMENT_SUMMARY_FILE.exists():
        return {}

    try:

        with open(
            EXPERIMENT_SUMMARY_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception:

        return {}


# =================================================================
# LOAD DATA
# =================================================================

all_outcomes = load_outcomes()

production_outcomes = (
    load_production_outcomes()
)

registry = load_json_file(
    REGISTRY_FILE
)

experiment = load_experiment_summary()

champion = registry.get(
    "champion",
    {}
)

challengers = registry.get(
    "challengers",
    []
)

if not challengers:

    challengers = registry.get(
        "challenger_models",
        []
    )


# =================================================================
# HEADER
# =================================================================

st.title("RecoverOS")

st.caption(
    "Payment recovery intelligence • "
    "Production monitoring • "
    "Closed-loop learning"
)


# =================================================================
# TOP STATUS
# =================================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Production Recovery",
        "ACTIVE",
    )

with col2:

    st.metric(
        "Model Protection",
        "ENABLED",
    )

with col3:

    st.metric(
        "Safety Layer",
        "ACTIVE",
    )


# =================================================================
# PRODUCTION REVENUE
# =================================================================

st.subheader("Production Recovery")

total_amount = sum(
    safe_float(
        record.get(
            "amount"
        )
    )
    for record in production_outcomes
)

recovered_amount = sum(
    safe_float(
        record.get(
            "recovery_amount"
        )
    )
    for record in production_outcomes
    if bool(
        record.get(
            "recovered"
        )
    )
)

expected_revenue = sum(
    safe_float(
        record.get(
            "expected_revenue"
        )
    )
    for record in production_outcomes
)

revenue_col1, revenue_col2, revenue_col3 = (
    st.columns(3)
)

with revenue_col1:

    st.metric(
        "Failed Payment Value",
        money(
            total_amount
        ),
    )

with revenue_col2:

    st.metric(
        "Recovered Revenue",
        money(
            recovered_amount
        ),
    )

with revenue_col3:

    st.metric(
        "Expected Revenue",
        money(
            expected_revenue
        ),
    )


# =================================================================
# CONTROLLED REVENUE IMPACT EXPERIMENT
# =================================================================

st.subheader(
    "Revenue Impact — Controlled Simulation"
)

if experiment:

    exp_baseline = experiment.get(
        "baseline",
        {}
    )

    exp_recoveros = experiment.get(
        "recoveros",
        {}
    )

    cases = int(
        experiment.get(
            "cases",
            0
        )
    )

    revenue_at_risk = safe_float(
        experiment.get(
            "total_revenue_at_risk",
            0
        )
    )

    baseline_rate = safe_float(
        exp_baseline.get(
            "recovery_rate",
            0
        )
    )

    recoveros_rate = safe_float(
        exp_recoveros.get(
            "recovery_rate",
            0
        )
    )

    baseline_recovered = safe_float(
        exp_baseline.get(
            "recovered_amount",
            0
        )
    )

    recoveros_recovered = safe_float(
        exp_recoveros.get(
            "recovered_amount",
            0
        )
    )

    incremental_recovered = safe_float(
        experiment.get(
            "incremental_recovered_amount",
            0
        )
    )

    uplift_pp = safe_float(
        experiment.get(
            "recovery_rate_uplift_percentage_points",
            0
        )
    )

    policy_violations = int(
        safe_float(
            experiment.get(
                "policy_violations",
                0
            )
        )
    )

    stopping_compliance = safe_float(
        experiment.get(
            "stopping_rule_compliance",
            0
        )
    )

    st.info(
        "Controlled simulation only — "
        "these figures are not production revenue."
    )

    impact_col1, impact_col2, impact_col3, impact_col4 = (
        st.columns(4)
    )

    with impact_col1:

        st.metric(
            "Cases",
            f"{cases:,}"
        )

    with impact_col2:

        st.metric(
            "Revenue at Risk",
            money(
                revenue_at_risk
            )
        )

    with impact_col3:

        st.metric(
            "RecoverOS Recovered",
            money(
                recoveros_recovered
            )
        )

    with impact_col4:

        st.metric(
            "Incremental Revenue",
            money(
                incremental_recovered
            )
        )

    compare_col1, compare_col2, compare_col3 = (
        st.columns(3)
    )

    with compare_col1:

        st.metric(
            "Baseline Recovery",
            percentage(
                baseline_rate
            )
        )

        st.caption(
            f"Recovered: "
            f"{money(baseline_recovered)}"
        )

    with compare_col2:

        st.metric(
            "RecoverOS Recovery",
            percentage(
                recoveros_rate
            )
        )

        st.caption(
            f"Recovered: "
            f"{money(recoveros_recovered)}"
        )

    with compare_col3:

        st.metric(
            "Recovery Uplift",
            f"+{uplift_pp:.2f} pp"
        )

        st.caption(
            f"Policy violations: "
            f"{policy_violations} • "
            f"Stopping compliance: "
            f"{stopping_compliance:.2%}"
        )

    experiment_table = pd.DataFrame(
        [
            {
                "Strategy": "Baseline",
                "Recovery Rate": percentage(
                    baseline_rate
                ),
                "Revenue Recovered": money(
                    baseline_recovered
                ),
            },
            {
                "Strategy": "RecoverOS",
                "Recovery Rate": percentage(
                    recoveros_rate
                ),
                "Revenue Recovered": money(
                    recoveros_recovered
                ),
            },
        ]
    )

    st.dataframe(
        experiment_table,
        width="stretch",
        hide_index=True,
    )

else:

    st.warning(
        "No controlled recovery experiment found."
    )


# =================================================================
# FAILED SUBSCRIPTION RECOVERY
# =================================================================

st.subheader(
    "Failed-Subscription Recovery"
)

st.caption(
    "RecoverOS detects the subscription failure state, "
    "chooses a bounded intervention, limits retries, "
    "and reconciles the later payment."
)

subscription_col1, subscription_col2 = (
    st.columns(2)
)

with subscription_col1:

    subscription_id = st.text_input(
        "Subscription ID",
        value="SUB_DEMO_001",
        key="subscription_id",
    )

    customer_id = st.text_input(
        "Customer ID",
        value="CUSTOMER_DEMO_001",
        key="subscription_customer_id",
    )

    subscription_payment_id = st.text_input(
        "Payment ID",
        value="PAY_SUB_DEMO_001",
        key="subscription_payment_id",
    )

with subscription_col2:

    subscription_amount = st.number_input(
        "Subscription Amount (₹)",
        min_value=1.0,
        value=2499.0,
        step=500.0,
        key="subscription_amount",
    )

    subscription_plan = st.selectbox(
        "Subscription Plan",
        [
            "monthly",
            "quarterly",
            "annual",
        ],
        key="subscription_plan",
    )

    subscription_failure = st.selectbox(
        "Failure Reason",
        [
            "bank_timeout",
            "network_error",
            "insufficient_funds",
            "expired_card",
            "mandate_failed",
            "temporary_bank_error",
        ],
        key="subscription_failure",
    )


# -----------------------------------------------------------------
# START SUBSCRIPTION RECOVERY
# -----------------------------------------------------------------

if st.button(
    "Start Subscription Recovery",
    type="primary",
    key="start_subscription_recovery",
):

    subscription = start_subscription_recovery(
        subscription_id=subscription_id,
        customer_id=customer_id,
        payment_id=subscription_payment_id,
        amount=subscription_amount,
        failure_reason=subscription_failure,
        subscription_plan=subscription_plan,
    )

    st.session_state[
        "subscription_recovery"
    ] = subscription

    st.session_state[
        "subscription_result"
    ] = None

    st.session_state[
        "subscription_verification"
    ] = None


# -----------------------------------------------------------------
# ACTIVE SUBSCRIPTION RECOVERY
# -----------------------------------------------------------------

if st.session_state.get(
    "subscription_recovery"
):

    subscription = (
        st.session_state[
            "subscription_recovery"
        ]
    )

    st.markdown(
        "#### Subscription Recovery Agent"
    )

    sub_status_col1, sub_status_col2, sub_status_col3, sub_status_col4 = (
        st.columns(4)
    )

    with sub_status_col1:

        st.metric(
            "Subscription",
            subscription.get(
                "subscription_id"
            )
        )

    with sub_status_col2:

        st.metric(
            "Amount",
            money(
                subscription.get(
                    "amount",
                    0
                )
            )
        )

    with sub_status_col3:

        st.metric(
            "Failure",
            subscription.get(
                "failure_reason",
                "-"
            )
        )

    with sub_status_col4:

        st.metric(
            "Retries",
            f"{subscription.get('retry_count', 0)} / "
            f"{subscription.get('max_retries', 3)}"
        )


    # -------------------------------------------------------------
    # RUN RECOVERY DECISION
    # -------------------------------------------------------------

    if st.button(
        "Run Recovery Decision",
        type="primary",
        key="run_subscription_decision",
    ):

        result = execute_subscription_action(
            subscription
        )

        st.session_state[
            "subscription_recovery"
        ] = subscription

        st.session_state[
            "subscription_result"
        ] = result


    subscription_result = st.session_state.get(
        "subscription_result"
    )

    if subscription_result:

        st.markdown(
            "#### Recovery Decision"
        )

        decision_col1, decision_col2, decision_col3 = (
            st.columns(3)
        )

        with decision_col1:

            st.metric(
                "Action",
                subscription_result.get(
                    "action",
                    "UNKNOWN"
                )
            )

        with decision_col2:

            st.metric(
                "Status",
                subscription_result.get(
                    "status",
                    "UNKNOWN"
                )
            )

        with decision_col3:

            st.metric(
                "Recovery Probability",
                percentage(
                    subscription.get(
                        "recovery_probability",
                        0
                    )
                )
            )

        st.info(
            subscription_result.get(
                "reason",
                "No decision reason available."
            )
        )


        # ---------------------------------------------------------
        # NEXT RETRY
        # ---------------------------------------------------------

        if subscription.get(
            "next_retry_at"
        ):

            st.caption(
                "Next retry / follow-up: "
                f"{subscription['next_retry_at']}"
            )


        # ---------------------------------------------------------
        # BOUNDED RETRY STATE
        # ---------------------------------------------------------

        retry_count = int(
            subscription.get(
                "retry_count",
                0
            )
        )

        max_retries = int(
            subscription.get(
                "max_retries",
                3
            )
        )

        retry_progress = min(
            retry_count / max_retries,
            1.0
        )

        st.progress(
            retry_progress
        )

        if retry_count >= max_retries:

            st.warning(
                "Stopping rule reached — "
                "no further automatic subscription retries."
            )


        # ---------------------------------------------------------
        # PAYMENT VERIFICATION
        # ---------------------------------------------------------

        st.markdown(
            "#### Later Subscription Payment"
        )

        if subscription.get(
            "payment_verified"
        ):

            st.success(
                "SUBSCRIPTION PAYMENT VERIFIED"
            )

            st.metric(
                "Recovered Revenue",
                money(
                    subscription.get(
                        "recovered_amount",
                        0
                    )
                )
            )

        else:

            verified_subscription_amount = st.number_input(
                "Simulated Payment Received (₹)",
                min_value=0.0,
                value=float(
                    subscription.get(
                        "amount",
                        0
                    )
                ),
                step=500.0,
                key="verified_subscription_amount",
            )

            if st.button(
                "Verify Subscription Payment",
                key="verify_subscription_payment",
            ):

                verification = (
                    verify_subscription_payment(
                        subscription,
                        verified_subscription_amount,
                    )
                )

                st.session_state[
                    "subscription_recovery"
                ] = subscription

                st.session_state[
                    "subscription_verification"
                ] = verification

                if verification.get(
                    "verified"
                ):

                    st.success(
                        "SUBSCRIPTION PAYMENT VERIFIED"
                    )

                    st.metric(
                        "Recovered Revenue",
                        money(
                            verification.get(
                                "recovered_amount",
                                0
                            )
                        )
                    )

                    st.caption(
                        "Recovery event recorded in the "
                        "subscription audit trail."
                    )

                else:

                    st.error(
                        verification.get(
                            "reason",
                            "Subscription payment verification failed."
                        )
                    )


        # ---------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------

        summary = subscription_recovery_summary(
            subscription
        )

        with st.expander(
            "View subscription recovery state"
        ):

            st.json(
                summary
            )

# =================================================================
# MANDATE RETRY SEQUENCER
# =================================================================

st.subheader(
    "Mandate Retry Sequencer"
)

st.caption(
    "RecoverOS schedules bounded mandate retries based on "
    "failure type, enforces a maximum retry limit, and "
    "verifies the eventual payment."
)

mandate_col1, mandate_col2 = st.columns(2)

with mandate_col1:

    mandate_id = st.text_input(
        "Mandate ID",
        value="MANDATE_DEMO_001",
        key="mandate_id",
    )

    mandate_customer_id = st.text_input(
        "Customer ID",
        value="CUSTOMER_DEMO_001",
        key="mandate_customer_id",
    )

    mandate_payment_id = st.text_input(
        "Payment ID",
        value="PAY_MANDATE_DEMO_001",
        key="mandate_payment_id",
    )

with mandate_col2:

    mandate_amount = st.number_input(
        "Mandate Amount (₹)",
        min_value=1.0,
        value=3499.0,
        step=500.0,
        key="mandate_amount",
    )

    mandate_type = st.selectbox(
        "Mandate Type",
        [
            "recurring",
            "subscription",
            "autopay",
        ],
        key="mandate_type",
    )

    mandate_failure = st.selectbox(
        "Failure Reason",
        [
            "bank_timeout",
            "network_error",
            "temporary_bank_error",
            "issuer_unavailable",
            "technical_error",
            "gateway_timeout",
            "insufficient_funds",
            "expired_card",
            "mandate_expired",
            "authentication_required",
            "mandate_revoked",
        ],
        key="mandate_failure",
    )


# -----------------------------------------------------------------
# START MANDATE RECOVERY
# -----------------------------------------------------------------

if st.button(
    "Start Mandate Recovery",
    type="primary",
    key="start_mandate_recovery",
):

    mandate = start_mandate_recovery(
        mandate_id=mandate_id,
        customer_id=mandate_customer_id,
        payment_id=mandate_payment_id,
        amount=mandate_amount,
        failure_reason=mandate_failure,
        mandate_type=mandate_type,
    )

    st.session_state[
        "mandate_recovery"
    ] = mandate

    st.session_state[
        "mandate_last_result"
    ] = None

    st.session_state[
        "mandate_verification"
    ] = None


# -----------------------------------------------------------------
# ACTIVE MANDATE RECOVERY
# -----------------------------------------------------------------

if st.session_state.get(
    "mandate_recovery"
):

    mandate = st.session_state[
        "mandate_recovery"
    ]

    st.markdown(
        "#### Mandate Recovery Agent"
    )

    mandate_status_col1, mandate_status_col2, mandate_status_col3, mandate_status_col4 = (
        st.columns(4)
    )

    with mandate_status_col1:

        st.metric(
            "Mandate",
            mandate.get(
                "mandate_id",
                "-"
            )
        )

    with mandate_status_col2:

        st.metric(
            "Amount",
            money(
                mandate.get(
                    "amount",
                    0
                )
            )
        )

    with mandate_status_col3:

        st.metric(
            "Failure",
            mandate.get(
                "failure_reason",
                "-"
            )
        )

    with mandate_status_col4:

        st.metric(
            "Retries",
            f"{mandate.get('retry_count', 0)} / "
            f"{mandate.get('max_retries', 4)}"
        )


    # -------------------------------------------------------------
    # RUN NEXT RETRY
    # -------------------------------------------------------------

    st.markdown(
        "#### Bounded Retry Sequence"
    )

    retry_count = int(
        mandate.get(
            "retry_count",
            0
        )
    )

    max_retries = int(
        mandate.get(
            "max_retries",
            4
        )
    )

    if retry_count < max_retries:

        if st.button(
            "Execute Next Retry Step",
            type="primary",
            key="execute_mandate_retry",
        ):

            result = execute_next_mandate_retry(
                mandate
            )

            st.session_state[
                "mandate_recovery"
            ] = mandate

            st.session_state[
                "mandate_last_result"
            ] = result

    else:

        st.warning(
            "Maximum mandate retry limit reached."
        )


    # -------------------------------------------------------------
    # LAST DECISION
    # -------------------------------------------------------------

    mandate_result = st.session_state.get(
        "mandate_last_result"
    )

    if mandate_result:

        st.markdown(
            "#### Latest Recovery Decision"
        )

        decision_col1, decision_col2, decision_col3 = (
            st.columns(3)
        )

        with decision_col1:

            st.metric(
                "Action",
                mandate_result.get(
                    "action",
                    "UNKNOWN"
                )
            )

        with decision_col2:

            st.metric(
                "Status",
                mandate_result.get(
                    "status",
                    "UNKNOWN"
                )
            )

        with decision_col3:

            st.metric(
                "Retry",
                f"{mandate.get('retry_count', 0)} / "
                f"{mandate.get('max_retries', 4)}"
            )

        st.info(
            mandate_result.get(
                "reason",
                "No decision reason available."
            )
        )

        if mandate_result.get(
            "next_retry_at"
        ):

            st.caption(
                "Next scheduled retry: "
                f"{mandate_result['next_retry_at']}"
            )


    # -------------------------------------------------------------
    # RETRY PROGRESS
    # -------------------------------------------------------------

    current_retry_count = int(
        mandate.get(
            "retry_count",
            0
        )
    )

    max_retry_count = int(
        mandate.get(
            "max_retries",
            4
        )
    )

    retry_progress = min(
        current_retry_count / max_retry_count,
        1.0
    )

    st.progress(
        retry_progress
    )

    if current_retry_count >= max_retry_count:

        st.warning(
            "Stopping rule reached — no further automatic "
            "mandate retries are permitted."
        )

    else:

        st.caption(
            f"Retry budget remaining: "
            f"{max_retry_count - current_retry_count}"
        )


    # -------------------------------------------------------------
    # RETRY TABLE
    # -------------------------------------------------------------

    retry_sequence = mandate.get(
        "retry_sequence",
        []
    )

    if retry_sequence:

        st.markdown(
            "#### Retry Schedule"
        )

        retry_rows = []

        for retry in retry_sequence:

            retry_rows.append(
                {
                    "Retry": retry.get(
                        "retry_number"
                    ),
                    "Status": retry.get(
                        "status"
                    ),
                    "Delay": (
                        f"{retry.get('delay_hours', 0)} hours"
                    ),
                    "Scheduled For": retry.get(
                        "scheduled_for"
                    ),
                    "Recovery Probability": percentage(
                        retry.get(
                            "recovery_probability",
                            0
                        )
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                retry_rows
            ),
            width="stretch",
            hide_index=True,
        )


    # -------------------------------------------------------------
    # PAYMENT VERIFICATION
    # -------------------------------------------------------------

    st.markdown(
        "#### Later Mandate Payment"
    )

    if mandate.get(
        "payment_verified"
    ):

        st.success(
            "MANDATE PAYMENT VERIFIED"
        )

        st.metric(
            "Recovered Revenue",
            money(
                mandate.get(
                    "recovered_amount",
                    0
                )
            )
        )

    else:

        verified_mandate_amount = st.number_input(
            "Simulated Payment Received (₹)",
            min_value=0.0,
            value=float(
                mandate.get(
                    "amount",
                    0
                )
            ),
            step=500.0,
            key="verified_mandate_amount",
        )

        if st.button(
            "Verify Mandate Payment",
            key="verify_mandate_payment",
        ):

            verification = verify_mandate_payment(
                mandate,
                verified_mandate_amount,
            )

            st.session_state[
                "mandate_recovery"
            ] = mandate

            st.session_state[
                "mandate_verification"
            ] = verification

            if verification.get(
                "verified"
            ):

                st.success(
                    "MANDATE PAYMENT VERIFIED"
                )

                st.metric(
                    "Recovered Revenue",
                    money(
                        verification.get(
                            "recovered_amount",
                            0
                        )
                    )
                )

                st.caption(
                    "Mandate verification event recorded "
                    "in the mandate retry audit trail."
                )

            else:

                st.error(
                    verification.get(
                        "reason",
                        "Mandate payment verification failed."
                    )
                )


    # -------------------------------------------------------------
    # MANDATE STATE
    # -------------------------------------------------------------

    with st.expander(
        "View mandate recovery state"
    ):

        st.json(
            mandate_recovery_summary(
                mandate
            )
        )

# =================================================================
# CHECKOUT DROP-OFF RECOVERY
# =================================================================

st.subheader(
    "Checkout Drop-off Recovery"
)

st.caption(
    "RecoverOS detects checkout abandonment, classifies the "
    "drop-off reason, selects a bounded intervention, and "
    "verifies the recovered payment."
)

checkout_col1, checkout_col2 = st.columns(2)

with checkout_col1:

    checkout_id = st.text_input(
        "Checkout ID",
        value="CHECKOUT_DEMO_001",
        key="checkout_id",
    )

    checkout_customer_id = st.text_input(
        "Customer ID",
        value="CUSTOMER_DEMO_001",
        key="checkout_customer_id",
    )

    checkout_payment_id = st.text_input(
        "Payment ID",
        value="PAY_CHECKOUT_DEMO_001",
        key="checkout_payment_id",
    )

with checkout_col2:

    checkout_amount = st.number_input(
        "Checkout Amount (₹)",
        min_value=1.0,
        value=2999.0,
        step=500.0,
        key="checkout_amount",
    )

    checkout_stage = st.selectbox(
        "Checkout Stage",
        [
            "cart",
            "address",
            "payment",
            "confirmation",
        ],
        key="checkout_stage",
    )

    checkout_dropoff_reason = st.selectbox(
        "Drop-off Reason",
        [
            "payment_failed",
            "bank_timeout",
            "network_error",
            "technical_error",
            "price_concern",
            "changed_mind",
            "needs_time",
            "checkout_error",
            "page_error",
            "session_expired",
            "authentication_required",
            "otp_failed",
            "customer_not_ready",
            "fraud",
            "suspicious_activity",
        ],
        key="checkout_dropoff_reason",
    )


# -----------------------------------------------------------------
# START CHECKOUT RECOVERY
# -----------------------------------------------------------------

if st.button(
    "Start Checkout Recovery",
    type="primary",
    key="start_checkout_recovery",
):

    checkout = start_checkout_recovery(
        checkout_id=checkout_id,
        customer_id=checkout_customer_id,
        payment_id=checkout_payment_id,
        amount=checkout_amount,
        dropoff_reason=checkout_dropoff_reason,
        checkout_stage=checkout_stage,
    )

    st.session_state[
        "checkout_recovery"
    ] = checkout

    st.session_state[
        "checkout_last_result"
    ] = None

    st.session_state[
        "checkout_verification"
    ] = None


# -----------------------------------------------------------------
# ACTIVE CHECKOUT RECOVERY
# -----------------------------------------------------------------

if st.session_state.get(
    "checkout_recovery"
):

    checkout = st.session_state[
        "checkout_recovery"
    ]

    st.markdown(
        "#### Checkout Recovery Agent"
    )

    checkout_status_col1, checkout_status_col2, checkout_status_col3, checkout_status_col4 = (
        st.columns(4)
    )

    with checkout_status_col1:

        st.metric(
            "Checkout",
            checkout.get(
                "checkout_id",
                "-"
            )
        )

    with checkout_status_col2:

        st.metric(
            "Amount",
            money(
                checkout.get(
                    "amount",
                    0
                )
            )
        )

    with checkout_status_col3:

        st.metric(
            "Drop-off",
            checkout.get(
                "dropoff_reason",
                "-"
            )
        )

    with checkout_status_col4:

        st.metric(
            "Attempts",
            f"{checkout.get('attempt_count', 0)} / "
            f"{checkout.get('max_attempts', 2)}"
        )


    # -------------------------------------------------------------
    # RUN RECOVERY
    # -------------------------------------------------------------

    st.markdown(
        "#### Bounded Recovery"
    )

    attempt_count = int(
        checkout.get(
            "attempt_count",
            0
        )
    )

    max_attempts = int(
        checkout.get(
            "max_attempts",
            2
        )
    )

    if (
        attempt_count < max_attempts
        and not checkout.get(
            "payment_verified"
        )
    ):

        if st.button(
            "Execute Recovery Attempt",
            type="primary",
            key="execute_checkout_recovery",
        ):

            result = execute_checkout_recovery(
                checkout
            )

            st.session_state[
                "checkout_recovery"
            ] = checkout

            st.session_state[
                "checkout_last_result"
            ] = result

    elif not checkout.get(
        "payment_verified"
    ):

        st.warning(
            "Maximum checkout recovery attempts reached."
        )


    # -------------------------------------------------------------
    # LATEST DECISION
    # -------------------------------------------------------------

    checkout_result = st.session_state.get(
        "checkout_last_result"
    )

    if checkout_result:

        st.markdown(
            "#### Recovery Decision"
        )

        decision_col1, decision_col2, decision_col3 = (
            st.columns(3)
        )

        with decision_col1:

            st.metric(
                "Action",
                checkout_result.get(
                    "action",
                    "UNKNOWN"
                )
            )

        with decision_col2:

            st.metric(
                "Status",
                checkout_result.get(
                    "status",
                    "UNKNOWN"
                )
            )

        with decision_col3:

            st.metric(
                "Recovery Probability",
                percentage(
                    checkout_result.get(
                        "recovery_probability",
                        checkout.get(
                            "recovery_probability",
                            0
                        )
                    )
                )
            )

        st.info(
            checkout_result.get(
                "reason",
                "No decision reason available."
            )
        )

        if checkout_result.get(
            "next_followup_at"
        ):

            st.caption(
                "Next follow-up: "
                f"{checkout_result['next_followup_at']}"
            )


    # -------------------------------------------------------------
    # ATTEMPT PROGRESS
    # -------------------------------------------------------------

    current_attempts = int(
        checkout.get(
            "attempt_count",
            0
        )
    )

    attempt_progress = min(
        current_attempts / max_attempts,
        1.0
    )

    st.progress(
        attempt_progress
    )

    if current_attempts >= max_attempts:

        st.warning(
            "Stopping rule reached — no further automatic "
            "checkout recovery attempts are permitted."
        )

    else:

        st.caption(
            f"Recovery attempts remaining: "
            f"{max_attempts - current_attempts}"
        )


    # -------------------------------------------------------------
    # ATTEMPT TABLE
    # -------------------------------------------------------------

    attempt_sequence = checkout.get(
        "attempt_sequence",
        []
    )

    if attempt_sequence:

        st.markdown(
            "#### Recovery Attempt Schedule"
        )

        attempt_rows = []

        for attempt in attempt_sequence:

            attempt_rows.append(
                {
                    "Attempt": attempt.get(
                        "attempt_number"
                    ),
                    "Action": attempt.get(
                        "action"
                    ),
                    "Status": attempt.get(
                        "status"
                    ),
                    "Delay": (
                        f"{attempt.get('delay_minutes', 0)} min"
                    ),
                    "Scheduled For": attempt.get(
                        "scheduled_for"
                    ),
                    "Recovery Probability": percentage(
                        attempt.get(
                            "recovery_probability",
                            0
                        )
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                attempt_rows
            ),
            width="stretch",
            hide_index=True,
        )


    # -------------------------------------------------------------
    # PAYMENT VERIFICATION
    # -------------------------------------------------------------

    st.markdown(
        "#### Later Checkout Payment"
    )

    if checkout.get(
        "payment_verified"
    ):

        st.success(
            "CHECKOUT PAYMENT VERIFIED"
        )

        st.metric(
            "Recovered Revenue",
            money(
                checkout.get(
                    "recovered_amount",
                    0
                )
            )
        )

    else:

        verified_checkout_amount = st.number_input(
            "Simulated Payment Received (₹)",
            min_value=0.0,
            value=float(
                checkout.get(
                    "amount",
                    0
                )
            ),
            step=500.0,
            key="verified_checkout_amount",
        )

        if st.button(
            "Verify Checkout Payment",
            key="verify_checkout_payment",
        ):

            verification = verify_checkout_payment(
                checkout,
                verified_checkout_amount,
            )

            st.session_state[
                "checkout_recovery"
            ] = checkout

            st.session_state[
                "checkout_verification"
            ] = verification

            if verification.get(
                "verified"
            ):

                st.success(
                    "CHECKOUT PAYMENT VERIFIED"
                )

                st.metric(
                    "Recovered Revenue",
                    money(
                        verification.get(
                            "recovered_amount",
                            0
                        )
                    )
                )

                st.caption(
                    "Checkout recovery event recorded "
                    "in the audit trail."
                )

            else:

                st.error(
                    verification.get(
                        "reason",
                        "Checkout payment verification failed."
                    )
                )


    # -------------------------------------------------------------
    # CHECKOUT STATE
    # -------------------------------------------------------------

    with st.expander(
        "View checkout recovery state"
    ):

        st.json(
            checkout_recovery_summary(
                checkout
            )
        )

# =================================================================
# B2B RECEIVABLES CHASER
# =================================================================

st.subheader(
    "B2B Receivables Chaser"
)

st.caption(
    "RecoverOS prioritizes overdue invoices, applies bounded "
    "collection escalation, captures Promise-to-Pay commitments, "
    "and verifies recovered revenue."
)

receivable_col1, receivable_col2 = st.columns(2)

with receivable_col1:

    receivable_invoice_id = st.text_input(
        "Invoice ID",
        value="INV_DEMO_001",
        key="receivable_invoice_id",
    )

    receivable_customer_id = st.text_input(
        "Customer ID",
        value="B2B_CUSTOMER_001",
        key="receivable_customer_id",
    )

    receivable_customer_name = st.text_input(
        "Customer Name",
        value="Demo Enterprise",
        key="receivable_customer_name",
    )

with receivable_col2:

    receivable_amount = st.number_input(
        "Invoice Amount (₹)",
        min_value=1.0,
        value=45000.0,
        step=5000.0,
        key="receivable_amount",
    )

    receivable_days_overdue = st.number_input(
        "Days Overdue",
        min_value=0,
        value=12,
        step=1,
        key="receivable_days_overdue",
    )

    receivable_due_date = st.text_input(
        "Due Date",
        value="2026-08-22",
        key="receivable_due_date",
    )


# -----------------------------------------------------------------
# START RECEIVABLE RECOVERY
# -----------------------------------------------------------------

if st.button(
    "Start Receivables Recovery",
    type="primary",
    key="start_receivables_recovery",
):

    receivable = start_receivables_recovery(
        invoice_id=receivable_invoice_id,
        customer_id=receivable_customer_id,
        amount=receivable_amount,
        days_overdue=receivable_days_overdue,
        due_date=receivable_due_date,
        customer_name=receivable_customer_name,
    )

    st.session_state[
        "receivables_recovery"
    ] = receivable

    st.session_state[
        "receivables_last_result"
    ] = None

    st.session_state[
        "receivables_verification"
    ] = None


# -----------------------------------------------------------------
# ACTIVE RECEIVABLE
# -----------------------------------------------------------------

if st.session_state.get(
    "receivables_recovery"
):

    receivable = st.session_state[
        "receivables_recovery"
    ]

    st.markdown(
        "#### Receivables Recovery Agent"
    )

    receivable_status_col1, receivable_status_col2, receivable_status_col3, receivable_status_col4 = (
        st.columns(4)
    )

    with receivable_status_col1:

        st.metric(
            "Invoice",
            receivable.get(
                "invoice_id",
                "-"
            )
        )

    with receivable_status_col2:

        st.metric(
            "Amount",
            money(
                receivable.get(
                    "amount",
                    0
                )
            )
        )

    with receivable_status_col3:

        st.metric(
            "Days Overdue",
            receivable.get(
                "days_overdue",
                0
            )
        )

    with receivable_status_col4:

        st.metric(
            "Priority",
            receivable.get(
                "recovery_priority",
                "NOT ASSESSED"
            )
        )


    # -------------------------------------------------------------
    # COLLECTION STEP
    # -------------------------------------------------------------

    st.markdown(
        "#### Bounded Collection Escalation"
    )

    escalation_count = int(
        receivable.get(
            "escalation_count",
            0
        )
    )

    max_escalations = int(
        receivable.get(
            "max_escalations",
            3
        )
    )

    if (
        escalation_count < max_escalations
        and not receivable.get(
            "payment_verified"
        )
    ):

        if st.button(
            "Execute Next Collection Step",
            type="primary",
            key="execute_receivables_action",
        ):

            result = execute_receivables_action(
                receivable
            )

            st.session_state[
                "receivables_recovery"
            ] = receivable

            st.session_state[
                "receivables_last_result"
            ] = result

    elif not receivable.get(
        "payment_verified"
    ):

        st.warning(
            "Maximum automated collection escalations reached."
        )


    # -------------------------------------------------------------
    # LATEST DECISION
    # -------------------------------------------------------------

    receivable_result = st.session_state.get(
        "receivables_last_result"
    )

    if receivable_result:

        st.markdown(
            "#### Recovery Decision"
        )

        decision_col1, decision_col2, decision_col3 = (
            st.columns(3)
        )

        with decision_col1:

            st.metric(
                "Action",
                receivable_result.get(
                    "action",
                    "UNKNOWN"
                )
            )

        with decision_col2:

            st.metric(
                "Status",
                receivable_result.get(
                    "status",
                    "UNKNOWN"
                )
            )

        with decision_col3:

            st.metric(
                "Recovery Probability",
                percentage(
                    receivable_result.get(
                        "recovery_probability",
                        0
                    )
                )
            )

        st.info(
            receivable_result.get(
                "reason",
                "No decision reason available."
            )
        )

        if receivable_result.get(
            "next_followup_at"
        ):

            st.caption(
                "Next follow-up: "
                f"{receivable_result['next_followup_at']}"
            )


    # -------------------------------------------------------------
    # ESCALATION PROGRESS
    # -------------------------------------------------------------

    current_escalations = int(
        receivable.get(
            "escalation_count",
            0
        )
    )

    escalation_progress = min(
        current_escalations / max_escalations,
        1.0
    )

    st.progress(
        escalation_progress
    )

    if current_escalations >= max_escalations:

        st.warning(
            "Stopping rule reached — no further automated "
            "collection escalation is permitted."
        )

    else:

        st.caption(
            f"Escalations remaining: "
            f"{max_escalations - current_escalations}"
        )


    # -------------------------------------------------------------
    # ESCALATION TABLE
    # -------------------------------------------------------------

    escalation_sequence = receivable.get(
        "escalation_sequence",
        []
    )

    if escalation_sequence:

        st.markdown(
            "#### Collection Escalation Schedule"
        )

        escalation_rows = []

        for escalation in escalation_sequence:

            escalation_rows.append(
                {
                    "Step": escalation.get(
                        "escalation_number"
                    ),
                    "Action": escalation.get(
                        "action"
                    ),
                    "Status": escalation.get(
                        "status"
                    ),
                    "Delay": (
                        f"{escalation.get('delay_days', 0)} days"
                    ),
                    "Scheduled For": escalation.get(
                        "scheduled_for"
                    ),
                    "Recovery Probability": percentage(
                        escalation.get(
                            "recovery_probability",
                            0
                        )
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                escalation_rows
            ),
            width="stretch",
            hide_index=True,
        )


    # -------------------------------------------------------------
    # PROMISE TO PAY
    # -------------------------------------------------------------

    if (
        receivable.get(
            "status"
        ) == "AWAITING_PROMISE_TO_PAY"
        or receivable.get(
            "recovery_action"
        ) == "REQUEST_PROMISE_TO_PAY"
    ):

        st.markdown(
            "#### B2B Promise-to-Pay"
        )

        promise_date = st.text_input(
            "Promised Payment Date",
            value="2026-09-07",
            key="receivable_promise_date",
        )

        promise_response = st.text_input(
            "Customer Commitment",
            value=(
                "Friday ko full payment kar denge."
            ),
            key="receivable_promise_response",
        )

        if not receivable.get(
            "promise_to_pay"
        ):

            if st.button(
                "Record Promise-to-Pay",
                key="record_receivable_promise",
            ):

                promise_result = (
                    record_receivables_promise(
                        receivable,
                        promise_date,
                        promise_response,
                    )
                )

                st.session_state[
                    "receivables_recovery"
                ] = receivable

                if promise_result.get(
                    "success"
                ):

                    st.success(
                        "PROMISE-TO-PAY RECORDED"
                    )

                    st.write(
                        "Promised Date: "
                        f"{promise_date}"
                    )

                else:

                    st.error(
                        promise_result.get(
                            "reason",
                            "Could not record Promise-to-Pay."
                        )
                    )

        else:

            promise = receivable[
                "promise_to_pay"
            ]

            st.info(
                f"Promise-to-Pay: "
                f"{promise.get('promised_date', '-')}"
            )

            st.caption(
                f"Status: "
                f"{promise.get('status', '-')}"
            )


    # -------------------------------------------------------------
    # PAYMENT VERIFICATION
    # -------------------------------------------------------------

    st.markdown(
        "#### Later Invoice Payment"
    )

    if receivable.get(
        "payment_verified"
    ):

        st.success(
            "B2B PAYMENT VERIFIED"
        )

        st.metric(
            "Recovered Revenue",
            money(
                receivable.get(
                    "recovered_amount",
                    0
                )
            )
        )

        if receivable.get(
            "promise_to_pay"
        ):

            st.success(
                "Promise-to-Pay FULFILLED"
            )

    else:

        verified_receivable_amount = st.number_input(
            "Simulated Payment Received (₹)",
            min_value=0.0,
            value=float(
                receivable.get(
                    "amount",
                    0
                )
            ),
            step=5000.0,
            key="verified_receivable_amount",
        )

        if st.button(
            "Verify Invoice Payment",
            key="verify_receivables_payment",
        ):

            verification = verify_receivables_payment(
                receivable,
                verified_receivable_amount,
            )

            st.session_state[
                "receivables_recovery"
            ] = receivable

            st.session_state[
                "receivables_verification"
            ] = verification

            if verification.get(
                "verified"
            ):

                st.success(
                    "B2B PAYMENT VERIFIED"
                )

                st.metric(
                    "Recovered Revenue",
                    money(
                        verification.get(
                            "recovered_amount",
                            0
                        )
                    )
                )

                st.caption(
                    "Receivables recovery event recorded "
                    "in the audit trail."
                )

            else:

                st.error(
                    verification.get(
                        "reason",
                        "Invoice payment verification failed."
                    )
                )


    # -------------------------------------------------------------
    # RECEIVABLE STATE
    # -------------------------------------------------------------

    with st.expander(
        "View receivables recovery state"
    ):

        st.json(
            receivables_recovery_summary(
                receivable
            )
        )

# =================================================================
# CHAMPION MODEL
# =================================================================

st.subheader(
    "Production Champion"
)

if champion:

    champion_col1, champion_col2, champion_col3, champion_col4 = (
        st.columns(4)
    )

    with champion_col1:

        st.write(
            "**Model**"
        )

        st.write(
            champion.get(
                "model_name",
                "unknown"
            )
        )

    with champion_col2:

        st.write(
            "**Version**"
        )

        st.write(
            champion.get(
                "version",
                "unknown"
            )
        )

    with champion_col3:

        st.write(
            "**F1 Score**"
        )

        st.write(
            percentage(
                champion.get(
                    "f1_score",
                    0
                )
            )
        )

    with champion_col4:

        st.write(
            "**ROC-AUC**"
        )

        st.write(
            percentage(
                champion.get(
                    "roc_auc",
                    0
                )
            )
        )

    st.success(
        "Production champion is ACTIVE."
    )

else:

    st.warning(
        "No production champion is registered."
    )


# =================================================================
# MODEL PROTECTION
# =================================================================

st.subheader(
    "Model Protection"
)

if champion:

    champion_name = champion.get(
        "model_name",
        ""
    )

    champion_file = (
        MODELS_DIR / champion_name
    )

    protection_col1, protection_col2, protection_col3 = (
        st.columns(3)
    )

    with protection_col1:

        if champion_file.exists():

            st.success(
                "Champion file exists"
            )

        else:

            st.error(
                "Champion file missing"
            )

    with protection_col2:

        st.success(
            "Automatic promotion disabled"
        )

    with protection_col3:

        st.success(
            "Champion overwrite protected"
        )


# =================================================================
# CHALLENGERS
# =================================================================

st.subheader(
    "Active Challengers"
)

if challengers:

    challenger_rows = []

    for challenger in challengers:

        challenger_rows.append(
            {
                "Model": challenger.get(
                    "model_name",
                    "unknown"
                ),
                "Version": challenger.get(
                    "version",
                    "unknown"
                ),
                "Status": challenger.get(
                    "status",
                    "unknown"
                ),
                "F1": percentage(
                    challenger.get(
                        "f1_score",
                        0
                    )
                ),
                "ROC-AUC": percentage(
                    challenger.get(
                        "roc_auc",
                        0
                    )
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            challenger_rows
        ),
        width="stretch",
        hide_index=True,
    )

else:

    st.info(
        "No active challenger models."
    )


# =================================================================
# PROMOTION ANALYSIS
# =================================================================

st.subheader(
    "Promotion Analysis"
)

if champion and challengers:

    champion_f1 = safe_float(
        champion.get(
            "f1_score"
        )
    )

    champion_auc = safe_float(
        champion.get(
            "roc_auc"
        )
    )

    best_challenger = None

    for challenger in challengers:

        f1 = safe_float(
            challenger.get(
                "f1_score"
            )
        )

        auc = safe_float(
            challenger.get(
                "roc_auc"
            )
        )

        if best_challenger is None:

            best_challenger = challenger

        else:

            current_score = f1 + auc

            best_score = (
                safe_float(
                    best_challenger.get(
                        "f1_score"
                    )
                )
                +
                safe_float(
                    best_challenger.get(
                        "roc_auc"
                    )
                )
            )

            if current_score > best_score:

                best_challenger = challenger

    challenger_f1 = safe_float(
        best_challenger.get(
            "f1_score"
        )
    )

    challenger_auc = safe_float(
        best_challenger.get(
            "roc_auc"
        )
    )

    f1_improvement = (
        challenger_f1
        - champion_f1
    )

    auc_improvement = (
        challenger_auc
        - champion_auc
    )

    promotion_col1, promotion_col2, promotion_col3 = (
        st.columns(3)
    )

    with promotion_col1:

        st.metric(
            "F1 Improvement",
            percentage(
                f1_improvement
            )
        )

    with promotion_col2:

        st.metric(
            "ROC-AUC Improvement",
            percentage(
                auc_improvement
            )
        )

    with promotion_col3:

        promotion_allowed = (
            challenger_f1 > champion_f1
            and challenger_auc > champion_auc
        )

        if promotion_allowed:

            st.success(
                "PROMOTION CANDIDATE"
            )

        else:

            st.error(
                "PROMOTION REJECTED"
            )

    st.info(
        "Automatic champion overwrite is disabled. "
        "Human approval is required."
    )


# =================================================================
# RECOVERY VERIFICATION
# =================================================================

st.subheader(
    "Recovery Verification"
)

st.caption(
    "Bounded recovery workflow for customer commitment, "
    "payment verification, and outcome tracking."
)

ppt_col1, ppt_col2, ppt_col3, ppt_col4 = (
    st.columns(4)
)

with ppt_col1:

    st.metric(
        "Recovery State",
        "ACTION SELECTED"
    )

with ppt_col2:

    st.metric(
        "Promise-to-Pay",
        "READY"
    )

with ppt_col3:

    st.metric(
        "Payment Verification",
        "READY"
    )

with ppt_col4:

    st.metric(
        "Outcome Logging",
        "ENABLED"
    )

with st.expander(
    "View bounded recovery workflow"
):

    st.write(
        "1. RecoverOS selects the recovery action."
    )

    st.write(
        "2. Customer can provide a Promise-to-Pay date."
    )

    st.write(
        "3. A later payment event can verify the commitment."
    )

    st.write(
        "4. Verified recovery amount is written to the "
        "Promise-to-Pay record and test outcome trail."
    )

    st.write(
        "5. Production retraining remains blocked until "
        "sufficient genuine production evidence is available."
    )


# =================================================================
# HINGLISH VOICE RECOVERY
# =================================================================

st.subheader(
    "Hinglish Voice Recovery"
)

st.caption(
    "Controlled voice demo — multi-turn Hinglish conversation, "
    "speech-to-text, Promise-to-Pay capture, payment verification, "
    "and recovery audit."
)

voice_col1, voice_col2 = st.columns(2)

with voice_col1:

    voice_payment_id = st.text_input(
        "Payment ID",
        value="SIM_VOICE_001",
        key="voice_payment_id",
    )

    voice_amount = st.number_input(
        "Amount (₹)",
        min_value=1.0,
        value=5000.0,
        step=500.0,
        key="voice_amount",
    )

with voice_col2:

    voice_failure = st.selectbox(
        "Failure Reason",
        [
            "bank_timeout",
            "network_error",
            "insufficient_funds",
        ],
        key="voice_failure",
    )


# =================================================================
# START HINGLISH SESSION
# =================================================================

if st.button(
    "Start Hinglish Recovery",
    type="primary",
    key="start_hinglish_recovery",
):

    st.session_state[
        "voice_session"
    ] = start_voice_recovery(
        voice_payment_id,
        voice_amount,
        voice_failure,
    )

    st.session_state.pop(
        "voice_intent",
        None,
    )

    st.session_state.pop(
        "promise",
        None,
    )

    st.session_state.pop(
        "voice_transcription",
        None,
    )

    st.session_state[
        "customer_response"
    ] = ""

    st.session_state[
        "last_voice_turn"
    ] = None


# =================================================================
# ACTIVE HINGLISH SESSION
# =================================================================

if st.session_state.get(
    "voice_session"
):

    session = st.session_state[
        "voice_session"
    ]

    st.markdown(
        "#### RecoverOS Voice Agent"
    )

    opening_message = generate_opening(
        session
    )

    st.info(
        opening_message
    )

    opening_audio = generate_voice_response(
        opening_message
    )

    if opening_audio:

        try:

            with open(
                opening_audio,
                "rb",
            ) as audio_file:

                st.audio(
                    audio_file.read(),
                    format="audio/wav",
                )

        except Exception:

            pass


    # -------------------------------------------------------------
    # CONVERSATION
    # -------------------------------------------------------------

    st.markdown(
        "#### Conversation"
    )

    conversation_history = session.get(
        "conversation_history",
        []
    )

    if conversation_history:

        for message in conversation_history:

            speaker = message.get(
                "speaker",
                "UNKNOWN"
            )

            text = message.get(
                "text",
                ""
            )

            if speaker == "CUSTOMER":

                st.write(
                    f"**Customer:** {text}"
                )

            else:

                st.write(
                    f"**RecoverOS:** {text}"
                )

    else:

        st.caption(
            "No customer response recorded yet."
        )


    # -------------------------------------------------------------
    # MICROPHONE
    # -------------------------------------------------------------

    st.markdown(
        "#### 🎙 Speak to RecoverOS"
    )

    st.caption(
        "First turn example: "
        "\"Abhi nahi ho payega.\""
    )

    audio_input = st.audio_input(
        "Record customer response",
        sample_rate=16000,
        key="hinglish_audio",
    )

    if audio_input:

        st.audio(
            audio_input
        )

        if st.button(
            "Transcribe Voice",
            key="transcribe_voice",
            type="primary",
        ):

            transcription = (
                transcribe_hinglish_audio(
                    audio_input
                )
            )

            st.session_state[
                "voice_transcription"
            ] = transcription

            if transcription.get(
                "success"
            ):

                st.session_state[
                    "customer_response"
                ] = transcription[
                    "text"
                ]

                st.success(
                    "Speech recognized successfully."
                )

                st.write(
                    "**Transcribed:** "
                    + transcription[
                        "text"
                    ]
                )

                st.write(
                    "**Normalized:** "
                    + transcription[
                        "normalized_text"
                    ]
                )

            else:

                st.error(
                    transcription.get(
                        "reason",
                        "Speech recognition failed."
                    )
                )


    # -------------------------------------------------------------
    # TEXT FALLBACK
    # -------------------------------------------------------------

    customer_text = st.text_area(
        "Customer response",
        value=st.session_state.get(
            "customer_response",
            ""
        ),
        key="customer_response_box",
        help=(
            "You can edit the transcription or type "
            "a response manually."
        ),
    )


    # -------------------------------------------------------------
    # PROCESS TURN
    # -------------------------------------------------------------

    if st.button(
        "Process Customer Turn",
        key="process_customer_turn",
        type="primary",
    ):

        if not customer_text.strip():

            st.warning(
                "Please record or enter a customer response first."
            )

        else:

            result = process_conversation_turn(
                session,
                customer_text,
            )

            st.session_state[
                "voice_session"
            ] = session

            st.session_state[
                "last_voice_turn"
            ] = result

            st.session_state[
                "customer_response"
            ] = ""

            st.session_state[
                "voice_intent"
            ] = result.get(
                "intent"
            )

            if result.get(
                "promise"
            ):

                st.session_state[
                    "promise"
                ] = result[
                    "promise"
                ]

            response_text = result.get(
                "response",
                ""
            )

            intent = result.get(
                "intent"
            )

            if intent == "PROMISE_TO_PAY":

                st.success(
                    "Intent detected: PROMISE_TO_PAY"
                )

            elif intent == "PAY_NOW":

                st.success(
                    "Intent detected: PAY_NOW"
                )

            elif intent == "DECLINE":

                st.warning(
                    "Intent detected: DECLINE"
                )

            elif intent == "PROMISE_DATE_REQUIRED":

                st.info(
                    "RecoverOS needs a payment date."
                )

            else:

                st.warning(
                    "Intent unclear — clarification required."
                )

            if response_text:

                st.markdown(
                    "#### RecoverOS Response"
                )

                st.info(
                    response_text
                )

                response_audio = (
                    generate_voice_response(
                        response_text
                    )
                )

                if response_audio:

                    try:

                        with open(
                            response_audio,
                            "rb",
                        ) as audio_file:

                            st.audio(
                                audio_file.read(),
                                format="audio/wav",
                            )

                    except Exception:

                        pass


    # =============================================================
    # PROMISE-TO-PAY
    # =============================================================

    if st.session_state.get(
        "promise"
    ):

        promise = st.session_state[
            "promise"
        ]

        st.markdown(
            "#### Promise-to-Pay Tracker"
        )

        p1, p2, p3, p4 = st.columns(4)

        with p1:

            st.metric(
                "Status",
                promise[
                    "status"
                ],
            )

        with p2:

            st.metric(
                "Promised Amount",
                money(
                    promise[
                        "promised_amount"
                    ]
                ),
            )

        with p3:

            st.metric(
                "Promised Date",
                promise.get(
                    "promised_date"
                )
                or "Not extracted",
            )

        with p4:

            st.metric(
                "Payment Verified",
                "YES"
                if promise[
                    "payment_verified"
                ]
                else "NO",
            )

        st.caption(
            "Promise-to-Pay is stored as a structured "
            "recovery commitment."
        )


        if not promise.get(
            "payment_verified"
        ):

            st.markdown(
                "#### Later Payment Verification"
            )

            verified_amount = st.number_input(
                "Simulated Later Payment (₹)",
                min_value=0.0,
                value=float(
                    promise[
                        "promised_amount"
                    ]
                ),
                step=500.0,
                key="verified_amount",
            )

            if st.button(
                "Verify Later Payment",
                key="verify_payment",
            ):

                result = verify_payment(
                    promise[
                        "promise_id"
                    ],
                    verified_amount,
                )

                if result.get(
                    "verified"
                ):

                    st.success(
                        "PAYMENT VERIFIED"
                    )

                    st.metric(
                        "Recovered Revenue",
                        money(
                            result[
                                "recovery_amount"
                            ]
                        ),
                    )

                    st.caption(
                        "Verification event appended to the "
                        "Hinglish recovery audit trail."
                    )

                    promise[
                        "status"
                    ] = "VERIFIED"

                    promise[
                        "payment_verified"
                    ] = True

                    promise[
                        "recovery_amount"
                    ] = result[
                        "recovery_amount"
                    ]

                    st.session_state[
                        "promise"
                    ] = promise

                else:

                    st.error(
                        result.get(
                            "reason",
                            "Verification failed."
                        )
                    )

        else:

            st.success(
                "This Promise-to-Pay is already VERIFIED."
            )

            st.metric(
                "Recovered Revenue",
                money(
                    promise.get(
                        "recovery_amount",
                        0
                    )
                ),
            )


    # -------------------------------------------------------------
    # SESSION STATUS
    # -------------------------------------------------------------

    st.markdown(
        "#### Session Status"
    )

    status_col1, status_col2 = (
        st.columns(2)
    )

    with status_col1:

        st.metric(
            "Session",
            session.get(
                "status",
                "ACTIVE"
            ),
        )

    with status_col2:

        history_count = len(
            session.get(
                "conversation_history",
                []
            )
        )

        st.metric(
            "Conversation Events",
            history_count,
        )


# =================================================================
# CLOSED-LOOP LEARNING
# =================================================================

st.subheader(
    "Closed-Loop Learning"
)

MIN_PRODUCTION_OUTCOMES = 10

learning_col1, learning_col2, learning_col3 = (
    st.columns(3)
)

with learning_col1:

    st.metric(
        "Learning Status",
        "GATED"
    )

with learning_col2:

    if (
        len(production_outcomes)
        >= MIN_PRODUCTION_OUTCOMES
    ):

        st.success(
            "Production threshold reached"
        )

    else:

        st.warning(
            "Awaiting sufficient production evidence"
        )

with learning_col3:

    if (
        len(production_outcomes)
        >= MIN_PRODUCTION_OUTCOMES
    ):

        st.success(
            "Retraining eligible"
        )

    else:

        st.info(
            "Production retraining blocked"
        )

st.caption(
    "The production model is protected until sufficient "
    "genuine production outcomes are available. "
    "Controlled simulation and demo outcomes are not used "
    "for production retraining."
)


# =================================================================
# SAFETY SUMMARY
# =================================================================

st.subheader(
    "Safety Status"
)

safety_col1, safety_col2, safety_col3, safety_col4 = (
    st.columns(4)
)

with safety_col1:

    st.success(
        "Production data only"
    )

with safety_col2:

    st.success(
        "Sandbox data excluded"
    )

with safety_col3:

    st.success(
        "Champion protected"
    )

with safety_col4:

    st.success(
        "Automatic promotion disabled"
    )


# =================================================================
# FOOTER
# =================================================================

st.divider()

st.caption(
    "RecoverOS X • Production Recovery Intelligence • "
    "Controlled Model Lifecycle"
)
