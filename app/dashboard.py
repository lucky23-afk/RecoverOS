import streamlit as st
import json
import pandas as pd
import subprocess

# --------------------------------
# PAGE CONFIG
# --------------------------------

st.set_page_config(
    page_title="RecoverOS",
    page_icon="💳",
    layout="wide"
)


# --------------------------------
# LOAD AUDIT DATA
# --------------------------------

@st.cache_data
def load_data():

    with open("../data/audit_log.json", "r") as file:
        records = json.load(file)

    return records


records = load_data()


# --------------------------------
# CONVERT TO TABLE
# --------------------------------

rows = []

for record in records:

    rows.append({
        "Customer": record["customer_id"],
        "Amount": record["payment"]["amount"],
        "Failure Reason": record["payment"]["failure_reason"],
        "Previous Successes": record["payment"]["previous_successes"],
        "Previous Failures": record["payment"]["previous_failures"],
        "Retry Count": record["payment"]["retry_count"],
        "Action": record["decision"]["action"],
        "Recovery Confidence": record["decision"]["confidence"],
        "Expected Revenue": record["decision"]["expected_revenue"],
        "Outcome": record["result"]["outcome"],
        "Recovered Amount": record["result"]["recovered_amount"],
        "Unsafe Action": record["safety"]["unsafe_action"]
    })


df = pd.DataFrame(rows)


# --------------------------------
# TITLE
# --------------------------------

st.title("💳 RecoverOS")
st.subheader(
    "Intelligent Failed Payment Recovery System"
)

st.caption(
    "AI-inspired decision engine • "
    "Safety-controlled automation • "
    "Synthetic prototype evaluation"
)
if st.button("▶ Run RecoverOS Analysis"):
    with st.spinner("Running RecoverOS decision engine..."):
        result = subprocess.run(
    ["python", "-X", "utf8", "evaluation.py"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

    if result.returncode == 0:
        st.cache_data.clear()
        st.success("RecoverOS analysis completed successfully!")
    else:
        st.error("Analysis failed.")
        st.code(result.stderr)
if st.button("🔄 Refresh Latest Recovery Data"):
    st.cache_data.clear()
    st.success("Latest recovery data loaded successfully.")
st.divider()

# --------------------------------
# HOW RECOVEROS WORKS
# --------------------------------

st.header("⚙️ How RecoverOS Works")

flow_col1, flow_col2, flow_col3, flow_col4, flow_col5 = st.columns(5)

flow_col1.info(
    "💳\n\nFAILED PAYMENT"
)

flow_col2.info(
    "📊\n\nPAYMENT CONTEXT\n\nHistory • Reason • Retries"
)

flow_col3.info(
    "🧠\n\nDECISION ENGINE"
)

flow_col4.info(
    "🛡️\n\nSAFETY GUARDRAILS"
)

flow_col5.info(
    "✅\n\nRECOVERY ACTION\n\nAudit • Review"
)

st.divider()
# --------------------------------
# CALCULATE METRICS
# --------------------------------

total_payments = len(df)

total_at_risk = df["Amount"].sum()

total_recovered = df["Recovered Amount"].sum()

recovery_rate = (
    total_recovered / total_at_risk
) * 100

flagged = len(
    df[df["Outcome"] == "flagged"]
)

unsafe_actions = len(
    df[df["Unsafe Action"] == True]
)


# --------------------------------
# TOP METRICS
# --------------------------------

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Payments Processed",
    total_payments
)

col2.metric(
    "Money at Risk",
    f"₹{total_at_risk:,}"
)

col3.metric(
    "Simulated Recovery",
    f"₹{total_recovered:,}"
)

col4.metric(
    "Recovery Rate",
    f"{recovery_rate:.2f}%"
)

col5.metric(
    "Unsafe Actions",
    unsafe_actions
)


st.divider()

# --------------------------------
# IMPACT SUMMARY
# --------------------------------

st.header("⚡ RecoverOS Impact")

baseline_recovery_rate = 7.25
baseline_recovered = 41079

additional_recovery = total_recovered - baseline_recovered

impact_col1, impact_col2, impact_col3, impact_col4 = st.columns(4)

impact_col1.metric(
    "Additional Recovery",
    f"₹{additional_recovery:,}"
)

impact_col2.metric(
    "Recovery Improvement",
    f"+{recovery_rate - baseline_recovery_rate:.2f}%"
)

impact_col3.metric(
    "Human Reviews",
    flagged
)

impact_col4.metric(
    "Unsafe Actions",
    unsafe_actions
)

st.success(
    "RecoverOS recovered more simulated revenue while "
    "reducing unnecessary retries and blocking unsafe "
    "automatic actions."
)

st.divider()
# --------------------------------
# BASELINE COMPARISON
# --------------------------------

st.header("📊 RecoverOS vs Naive Retry")

comparison = pd.DataFrame({
    "Strategy": [
        "Naive Retry",
        "RecoverOS"
    ],
    "Recovery Rate": [
        7.25,
        recovery_rate
    ]
})

st.bar_chart(
    comparison,
    x="Strategy",
    y="Recovery Rate"
)

st.info(
    "On this synthetic dataset, RecoverOS evaluates "
    "failure context and applies safety rules instead "
    "of blindly retrying every payment."
)


# --------------------------------
# ACTION DISTRIBUTION
# --------------------------------

col1, col2 = st.columns(2)

with col1:

    st.subheader("Actions Selected")

    action_counts = (
        df["Action"]
        .value_counts()
    )

    st.bar_chart(action_counts)


with col2:

    st.subheader("Failure Reasons")

    failure_counts = (
        df["Failure Reason"]
        .value_counts()
    )

    st.bar_chart(failure_counts)


st.divider()


# --------------------------------
# REVIEW QUEUE
# --------------------------------

st.header("🚨 Human Review Queue")

review_queue = df[
    df["Outcome"] == "flagged"
]

st.write(
    f"{len(review_queue)} payments require human review."
)

st.dataframe(
    review_queue[
        [
            "Customer",
            "Amount",
            "Failure Reason",
            "Action"
        ]
    ],
    use_container_width=True
)


st.divider()


# --------------------------------
# PAYMENT EXPLORER
# --------------------------------

st.header("🔍 Payment Decision Explorer")

customer = st.selectbox(
    "Select a customer",
    df["Customer"]
)

selected = df[
    df["Customer"] == customer
].iloc[0]


col1, col2 = st.columns(2)

with col1:

    st.subheader("Payment Context")

    st.write(
        "Amount:",
        f"₹{selected['Amount']:,}"
    )

    st.write(
        "Failure Reason:",
        selected["Failure Reason"]
    )

    st.write(
        "Previous Successes:",
        selected["Previous Successes"]
    )

    st.write(
        "Previous Failures:",
        selected["Previous Failures"]
    )

    st.write(
        "Retry Count:",
        selected["Retry Count"]
    )


with col2:

    st.subheader("RecoverOS Decision")

    st.write(
        "Recommended Action:",
        selected["Action"]
    )

    st.write(
        "Recovery Confidence:",
        f"{selected['Recovery Confidence'] * 100:.1f}%"
    )

    st.write(
        "Expected Revenue:",
        f"₹{selected['Expected Revenue']:,.2f}"
    )

    st.write(
        "Outcome:",
        selected["Outcome"]
    )

    st.write(
        "Safety Violation:",
        selected["Unsafe Action"]
    )
    st.subheader("📊 Recovery Profile")

    successes = selected["Previous Successes"]
    failures = selected["Previous Failures"]
    retries = selected["Retry Count"]
    confidence = selected["Recovery Confidence"]

    # Calculate a simple profile
    if successes >= 10 and failures <= 2:
        profile = "STRONG"
        profile_message = "Strong history of successful payments"
    elif successes >= 4:
        profile = "MODERATE"
        profile_message = "Mixed but reasonably positive payment history"
    else:
        profile = "LIMITED"
        profile_message = "Limited payment history available"

    col_a, col_b, col_c = st.columns(3)

    col_a.metric(
        "Payment History",
        profile
    )

    col_b.metric(
        "Success / Failure",
        f"{successes} / {failures}"
    )

    col_c.metric(
        "Retry Status",
        f"{retries} / 3"
    )

    st.write(profile_message)

    st.progress(float(confidence))
    st.subheader("🧠 Why This Decision?")

    successes = selected["Previous Successes"]
    failures = selected["Previous Failures"]
    retries = selected["Retry Count"]
    reason = selected["Failure Reason"]
    action = selected["Action"]

    if successes >= 10:
        st.success("✓ Strong previous payment history")
    elif successes >= 4:
        st.info("✓ Moderate previous payment history")
    else:
        st.warning("⚠ Limited successful payment history")

    if failures >= 5:
        st.warning("⚠ Multiple previous payment failures")
    elif failures > 0:
        st.info("✓ Some previous payment failures")
    else:
        st.success("✓ No previous payment failures")

    if retries >= 3:
        st.error("✗ Retry limit reached — no further automatic retry")
    else:
        st.success(
            f"✓ Retry count ({retries}/3) is within safety limit"
        )

    st.write("**Current failure context:**", reason)

    if action == "retry_payment":
        st.info(
            "RecoverOS selected retry because this failure "
            "appears recoverable and the retry safety limit "
            "has not been reached."
        )

    elif action == "send_update_link":
        st.info(
            "RecoverOS selected an update link because the "
            "payment method likely needs customer action."
        )

    elif action == "send_reminder":
        st.info(
            "RecoverOS selected a reminder because customer "
            "intervention is more appropriate than immediate retry."
        )

    elif action == "hold_for_review":
        st.error(
            "RecoverOS blocked automatic recovery because this "
            "payment requires human review."
        )

    elif action == "gave_up":
        st.warning(
            "RecoverOS stopped automatic recovery because the "
            "retry safety limit was reached."
        )

st.divider()


# --------------------------------
# ALL PAYMENTS
# --------------------------------

st.header("📋 All Payment Decisions")

st.dataframe(
    df,
    use_container_width=True
)

# --------------------------------
# PROTOTYPE SCOPE
# --------------------------------

st.divider()

st.header("🔬 Prototype Scope")

st.info(
    "RecoverOS is a prototype evaluated on synthetic payment "
    "failure data. Recovery outcomes are simulated to test "
    "decision quality, safety constraints, retry behavior, "
    "and comparative performance."
)

st.markdown(
    """
**What the prototype demonstrates:**

- Context-aware recovery decisions
- Payment history-based confidence
- Safety-controlled automation
- Retry limits
- Human review for risky cases
- Full audit logging
- Comparison against a naive retry strategy
"""
)
# --------------------------------
# FOOTER
# --------------------------------

st.caption(
    "RecoverOS is a prototype using synthetic payment "
    "data and simulated outcomes. Results do not "
    "represent real payment recovery."
)