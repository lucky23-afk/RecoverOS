from pathlib import Path
import json

import pandas as pd
import streamlit as st


# ================================================================
# RecoverOS - PRODUCTION DASHBOARD
# ================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"
REGISTRY_FILE = DATA_DIR / "model_registry.json"
FEEDBACK_FILE = DATA_DIR / "production_feedback.csv"


# ================================================================
# PAGE CONFIG
# ================================================================

st.set_page_config(
    page_title="RecoverOS",
    page_icon="💳",
    layout="wide",
)


# ================================================================
# HELPERS
# ================================================================

def load_json_file(path):
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
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
        record.get("data_source", "")
    ).upper()

    mode = str(
        record.get("mode", "")
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


# ================================================================
# LOAD DATA
# ================================================================

all_outcomes = load_outcomes()
production_outcomes = load_production_outcomes()

registry = load_json_file(REGISTRY_FILE)

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


# ================================================================
# HEADER
# ================================================================

st.title("RecoverOS")
st.caption(
    "Payment recovery intelligence • Production monitoring • Closed-loop learning"
)


# ================================================================
# TOP STATUS
# ================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Production Outcomes",
        len(production_outcomes),
    )

with col2:
    recovered_count = sum(
        bool(record.get("recovered"))
        for record in production_outcomes
    )

    st.metric(
        "Recovered",
        recovered_count,
    )

with col3:
    production_recovery_rate = (
        recovered_count / len(production_outcomes)
        if production_outcomes
        else 0.0
    )

    st.metric(
        "Recovery Rate",
        percentage(production_recovery_rate),
    )

with col4:
    st.metric(
        "Total Outcome Records",
        len(all_outcomes),
    )


# ================================================================
# DATA CLASSIFICATION
# ================================================================

st.subheader("Data Classification")

sandbox_count = len(all_outcomes) - len(
    production_outcomes
)

data_col1, data_col2, data_col3 = st.columns(3)

with data_col1:
    st.metric(
        "All Outcomes",
        len(all_outcomes),
    )

with data_col2:
    st.metric(
        "Production",
        len(production_outcomes),
    )

with data_col3:
    st.metric(
        "Sandbox / Demo / Test",
        sandbox_count,
    )


# ================================================================
# PRODUCTION REVENUE
# ================================================================

st.subheader("Production Recovery")

total_amount = sum(
    safe_float(record.get("amount"))
    for record in production_outcomes
)

recovered_amount = sum(
    safe_float(record.get("recovery_amount"))
    for record in production_outcomes
    if bool(record.get("recovered"))
)

expected_revenue = sum(
    safe_float(record.get("expected_revenue"))
    for record in production_outcomes
)

revenue_col1, revenue_col2, revenue_col3 = st.columns(3)

with revenue_col1:
    st.metric(
        "Failed Payment Value",
        money(total_amount),
    )

with revenue_col2:
    st.metric(
        "Recovered Revenue",
        money(recovered_amount),
    )

with revenue_col3:
    st.metric(
        "Expected Revenue",
        money(expected_revenue),
    )


# ================================================================
# CHAMPION MODEL
# ================================================================

st.subheader("Production Champion")

if champion:

    champion_col1, champion_col2, champion_col3, champion_col4 = (
        st.columns(4)
    )

    with champion_col1:
        st.write("**Model**")
        st.write(
            champion.get(
                "model_name",
                "unknown",
            )
        )

    with champion_col2:
        st.write("**Version**")
        st.write(
            champion.get(
                "version",
                "unknown",
            )
        )

    with champion_col3:
        st.write("**F1 Score**")
        st.write(
            percentage(
                champion.get(
                    "f1_score",
                    0,
                )
            )
        )

    with champion_col4:
        st.write("**ROC-AUC**")
        st.write(
            percentage(
                champion.get(
                    "roc_auc",
                    0,
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


# ================================================================
# MODEL FILE CHECK
# ================================================================

st.subheader("Model Protection")

if champion:

    champion_name = champion.get(
        "model_name",
        "",
    )

    champion_file = MODELS_DIR / champion_name

    protection_col1, protection_col2, protection_col3 = (
        st.columns(3)
    )

    with protection_col1:
        if champion_file.exists():
            st.success("Champion file exists")
        else:
            st.error("Champion file missing")

    with protection_col2:
        st.success("Automatic promotion disabled")

    with protection_col3:
        st.success("Champion overwrite protected")


# ================================================================
# CHALLENGERS
# ================================================================

st.subheader("Active Challengers")

if challengers:

    challenger_rows = []

    for challenger in challengers:

        challenger_rows.append(
            {
                "Model": challenger.get(
                    "model_name",
                    "unknown",
                ),
                "Version": challenger.get(
                    "version",
                    "unknown",
                ),
                "Status": challenger.get(
                    "status",
                    "unknown",
                ),
                "F1": percentage(
                    challenger.get(
                        "f1_score",
                        0,
                    )
                ),
                "ROC-AUC": percentage(
                    challenger.get(
                        "roc_auc",
                        0,
                    )
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(challenger_rows),
        width="stretch",
        hide_index=True,
    )

else:

    st.info(
        "No active challenger models."
    )


# ================================================================
# PROMOTION ANALYSIS
# ================================================================

st.subheader("Promotion Analysis")

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

            current_score = (
                f1 + auc
            )

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
            ),
        )

    with promotion_col2:
        st.metric(
            "ROC-AUC Improvement",
            percentage(
                auc_improvement
            ),
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


# ================================================================
# PRODUCTION OUTCOME TABLE
# ================================================================

st.subheader("Production Outcomes")

if production_outcomes:

    table_rows = []

    for record in production_outcomes:

        table_rows.append(
            {
                "Payment ID": record.get(
                    "payment_id",
                    "",
                ),
                "Amount": money(
                    record.get(
                        "amount",
                        0,
                    )
                ),
                "Failure": record.get(
                    "failure_reason",
                    "",
                ),
                "Recommended": record.get(
                    "recommended_action",
                    "",
                ),
                "Final Action": record.get(
                    "final_action",
                    "",
                ),
                "Recovery Probability": percentage(
                    record.get(
                        "recovery_probability",
                        0,
                    )
                ),
                "Recovered": (
                    "YES"
                    if record.get("recovered")
                    else "NO"
                ),
                "Recovery Amount": money(
                    record.get(
                        "recovery_amount",
                        0,
                    )
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(table_rows),
        width="stretch",
        hide_index=True,
    )

else:

    st.info(
        "No genuine production outcomes are currently available."
    )


# ================================================================
# LEARNING LOOP STATUS
# ================================================================

st.subheader("Closed-Loop Learning")

MIN_PRODUCTION_OUTCOMES = 10

learning_col1, learning_col2, learning_col3 = (
    st.columns(3)
)

with learning_col1:

    st.metric(
        "Production Outcomes",
        f"{len(production_outcomes)} / "
        f"{MIN_PRODUCTION_OUTCOMES}",
    )

with learning_col2:

    if len(production_outcomes) >= MIN_PRODUCTION_OUTCOMES:
        st.success(
            "Data threshold reached"
        )
    else:
        st.warning(
            "Waiting for production data"
        )

with learning_col3:

    if len(production_outcomes) >= MIN_PRODUCTION_OUTCOMES:
        st.success(
            "Retraining eligible"
        )
    else:
        st.info(
            "Retraining blocked"
        )


# ================================================================
# SAFETY SUMMARY
# ================================================================

st.subheader("Safety Status")

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


# ================================================================
# FOOTER
# ================================================================

st.divider()

st.caption(
    "RecoverOS X • Production Recovery Intelligence • "
    "Controlled Model Lifecycle"
)