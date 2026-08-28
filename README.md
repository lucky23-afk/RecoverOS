# RecoverOS

### A smarter way to handle failed recurring payments

RecoverOS is a prototype built for the Razorpay Buildathon (Revenue Recovery track).

The basic idea is simple: most recovery systems may retry failed payments the same way without considering why the payment failed. That can waste retry attempts and, in some cases, lead to unsafe automation.

RecoverOS looks at the context around each failure first, then decides what to do next — retry the payment, ask the customer to update their payment method, send a reminder, or flag the case for human review.

---

## The problem

Not all failed payments are the same.

* A bank timeout may be temporary and safe to retry.
* An expired card will not be fixed by repeatedly retrying it — the customer may need to update their payment method.
* A recently changed mandate or suspicious reversal should not be automatically retried. Those cases should be reviewed by a human.

A naive recovery strategy does not make these distinctions. It may simply retry payments until it reaches a limit, regardless of whether another retry makes sense or is safe.

RecoverOS takes a different approach:

Look at the failure context, choose the appropriate action, apply safety rules, log the decision.

---

## How it works

### System Architecture


```text
Failed Payment
      ↓
Context Analysis
(Payment History + Failure Reason + Retry Count)
      ↓
Decision Engine
      ↓
Safety Guardrails
      ↓
Recommended Recovery Action
      ↓
Audit Log + Human Review
```


A failed payment enters RecoverOS and is evaluated using:

* Payment history
* Failure reason
* Previous successful payments
* Previous failed payments
* Retry count

The payment then passes through the decision engine and safety guardrails.

The final decision is written to an audit log and, when necessary, routed to a human review queue.

For every failed payment, RecoverOS can choose one of:

* Retry payment
* Send update link
* Send reminder
* Hold for review
* Gave up

Risky cases are routed away from unsafe automatic actions.

---

## Safety guardrails

This is one of the most important parts of RecoverOS.

It is easy to build a system that appears to recover more revenue simply by retrying aggressively. But more retries do not necessarily mean better recovery.

RecoverOS enforces:

* Suspicious reversals are routed to human review.
* Recently changed mandates are routed to human review.
* Automatic retries have a hard limit of 3 attempts.
* Retry limit violations are detected.
* Unsafe automatic actions are tracked.
* Every decision is written to an audit log.

The goal is not to maximize retries.

The goal is controlled, explainable automation that knows when to act and when to stop.

---

## Prototype results

RecoverOS was tested using a synthetic dataset containing:

* 200 failed payments
* Multiple failure categories
* Simulated customer payment history
* Simulated retry history
* Simulated recovery outcomes

| Metric              |       Naive Retry | RecoverOS |
| ------------------- | ----------------: | --------: |
| Recovery rate       |             7.25% |    26.68% |
| Retry attempts used |               147 |        19 |
| Unsafe actions      | 22 unsafe retries |         0 |
| Human review flags  |              None |        61 |

### Simulated impact

* Naive retry recovered ₹41,079
* RecoverOS recovered ₹151,143
* Additional simulated recovery: ₹110,064
* Unsafe automatic actions: 0
* Retry limit violations: 0

Important: these results are based entirely on synthetic data and simulated outcomes.

They demonstrate how the prototype's decision logic behaves. They do not represent expected results on real transactions.

---

## Explainable decisions

RecoverOS does not just output an action. It also explains why the action was chosen.

Example:

Failure reason: bank timeout

Previous successes: 2
Previous failures: 3
Retry count: 1 of 3

Recommended action: retry payment

Reasoning:
* The failure appears temporarily recoverable.
* The retry limit has not been reached.
* Previous payment history is considered.
* Safety checks passed.

The Streamlit dashboard also provides a Recovery Profile and a "Why This Decision?" explanation for individual payments.

---

## Dashboard

The dashboard is built with Streamlit and includes:

* Recovery rate and simulated recovered revenue
* RecoverOS vs naive retry comparison
* Action distribution
* Failure reason breakdown
* Human review queue
* Payment Decision Explorer
* Per-payment Recovery Profile
* Explainable reasoning for decisions
* Safety status
* Audit-backed decision records
* A "Run RecoverOS Analysis" button to run a fresh evaluation

---

## Project structure

recoveros/
* app/
  * main.py
  * data_generator.py
  * decision_engine.py
  * simulator.py
  * baseline.py
  * safety.py
  * audit.py
  * evaluation.py
  * dashboard.py
* data/
  * payments.csv
  * audit_log.json
* README.md

---

## Running the project

1. Install dependencies

pip install pandas streamlit

2. Generate synthetic payment data

cd app
python data_generator.py

3. Run the evaluation

python evaluation.py

4. Launch the dashboard

streamlit run dashboard.py

---

## Scope, honestly

This is a prototype.

It uses:

* Synthetic payment data
* Rule-based decision logic
* Simulated recovery outcomes

It does not process real customer payment data.

The project is intended to demonstrate:

* Context-aware recovery decisions instead of blind retries
* Safety-controlled automation
* Smarter use of retry attempts
* Clear routing to human review
* Explainable decisions
* Full audit logging

Taking RecoverOS into production would require additional work, including real payment data integration, live gateway integration, authentication, privacy controls, monitoring, security review, and production-grade validation.

---

## The core idea

Not every failed payment deserves the same response.

RecoverOS combines payment context, recovery confidence, explicit safety rules, explainable reasoning, and audit logging to make failed payment recovery more intelligent and safer than simply retrying every failed payment and hoping it succeeds.

---

## Disclaimer

All payment data and results in this repository are synthetic and simulated.

Nothing in this project represents real Razorpay customers, merchants, transactions, or actual production recovery performance.
