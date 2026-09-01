# RecoverOS

### A smarter way to handle failed recurring payments

RecoverOS is an AI-assisted payment recovery prototype built for the **Razorpay Buildathon – Revenue Recovery track**.

Instead of blindly retrying every failed payment, RecoverOS evaluates payment context, predicts recovery probability, selects a recovery strategy, applies policy and safety controls, validates the final decision, and records the outcome for future analysis.

---

## The problem

Not all failed payments are the same.

- A temporary bank timeout may be worth retrying.
- Insufficient funds may require a payment-method update.
- Risky or suspicious cases may need human review.
- Blind retries can waste attempts and create unsafe automation.

RecoverOS takes a context-aware approach:

```text
Failure Context
      ↓
Recovery Prediction
      ↓
Strategy Selection
      ↓
Policy Rules
      ↓
Safety Controls
      ↓
Final Decision
      ↓
Audit + Outcome
      ↓
Controlled Learning
Key features
ML-based recovery probability prediction
Context-aware recovery strategy selection
Policy enforcement
Safety guardrails
Decision integrity validation
Audit logging
Outcome intelligence
Production-data filtering
Controlled challenger-model retraining
Model registry
Strict promotion gate
Human-approved model promotion
Streamlit monitoring dashboard
System architecture
Failed Payment
      │
      ▼
Payment / Customer Context
      │
      ▼
ML Recovery Prediction
      │
      ▼
Strategy Optimizer
      │
      ▼
Policy Engine
      │
      ▼
Safety Engine
      │
      ▼
Decision Orchestrator
      │
      ▼
Integrity Validation
      │
      ▼
Audit Log
      │
      ▼
Outcome Recording
      │
      ▼
Production Feedback
      │
      ▼
Controlled Retraining
      │
      ▼
Challenger Model
      │
      ▼
Promotion Gate
      │
      ▼
Human Approval
      │
      ▼
Production Champion
Recovery actions

RecoverOS can select actions such as:

retry_payment
send_update_link
send_reminder
hold_for_review

The ML model recommends based on recovery probability and payment context, while policy and safety layers can override unsafe recommendations.

Machine learning

The current baseline model is:

Model    : recovery_model.pkl
Version  : v1
Status   : production
Baseline performance
Metric	Score
Accuracy	81.74%
Precision	83.17%
Recall	79.07%
F1 Score	81.07%
ROC-AUC	90.87%

These are baseline evaluation metrics and are not presented as guaranteed real-world production performance.

Example decision
ML probability       : 84.71%
Optimizer action     : send_update_link
Policy action        : hold_for_review
Safety decision      : ALLOW
Final action         : hold_for_review

RecoverOS also validates the decision chain:

Integrity valid : True
Reason          : Decision integrity checks passed.
Safety guardrails

RecoverOS is designed so that the ML model does not directly control the final action.

Safety controls include:

retry-limit enforcement
human-review routing
suspicious-case protection
decision integrity checks
audit logging
production-data isolation
champion-model protection
human approval for model promotion

The goal is not maximum retries.

The goal is controlled and explainable recovery.

Outcome intelligence

The outcome engine analyzes:

total decisions
recovered payments
recovery rate
average ML prediction
prediction error
recovered revenue
strategy performance
failure categories
learning signals
Closed-loop learning

RecoverOS supports a controlled learning cycle:

Decision
   ↓
Observed Outcome
   ↓
Production Feedback
   ↓
Retraining
   ↓
Challenger Model
   ↓
Promotion Gate
   ↓
Human Approval
   ↓
New Champion
Production data protection

Production learning requires explicit production classification.

Example:

{
  "production": true,
  "data_source": "PRODUCTION"
}

Sandbox, demo, test, and simulated records are excluded from production retraining.

This prevents simulated outcomes from being presented as genuine production evidence.

Current learning state

Current repository state:

Total outcome records : 30
Production outcomes   : 1
Sandbox/demo outcomes  : 29

Production retraining requires at least:

10 genuine production outcomes

Current state:

WAITING_FOR_DATA

This is intentional.

The system does not convert simulated outcomes into production evidence simply to satisfy the training threshold.

Model lifecycle
Production Champion
        │
        ▼
Production Outcomes
        │
        ▼
Production Feedback
        │
        ▼
Controlled Retraining
        │
        ▼
Challenger
        │
        ▼
Promotion Gate
        │
        ├── Reject
        │
        └── Candidate
                │
                ▼
          Human Approval
                │
                ▼
          Champion Backup
                │
                ▼
          New Champion

Automatic champion overwrite is disabled.

Dashboard

The Streamlit dashboard provides:

recovery metrics
recovered revenue
outcome analysis
champion model information
challenger information
promotion status
production-data status
safety status
production outcomes
Run
streamlit run app\dashboard.py

Then open the local Streamlit URL, normally:

http://localhost:8501
Project structure
recoveros/
│
├── app/
│   ├── api.py
│   ├── approve_promotion.py
│   ├── dashboard.py
│   ├── decision_engine.py
│   ├── decision_orchestrator.py
│   ├── learning_loop.py
│   ├── ml_model.py
│   ├── model_evaluator.py
│   ├── model_registry.py
│   ├── outcome_api.py
│   ├── outcome_engine.py
│   ├── policy_engine.py
│   ├── production_feedback.py
│   ├── production_retraining.py
│   ├── promotion_gate.py
│   ├── recovery_memory.py
│   ├── safety_engine.py
│   ├── sandbox_runner.py
│   └── strategy_optimizer.py
│
├── data/
│   ├── advanced_training_data.csv
│   ├── decision_audit.jsonl
│   ├── model_registry.json
│   ├── outcomes.jsonl
│   ├── production_feedback.csv
│   └── recovery_memory.json
│
├── models/
│   ├── model_registry.json
│   ├── recovery_model.pkl
│   └── recovery_model_challenger.pkl
│
├── requirements.txt
└── README.md
Running the project
Install dependencies
pip install -r requirements.txt
Run decision orchestration
python app\decision_orchestrator.py
Analyze outcomes
python app\outcome_engine.py
Build production feedback
python app\production_feedback.py
Check learning status
python app\learning_loop.py
Train a production challenger

Only after the production safety threshold is reached:

python app\production_retraining.py
Run the promotion gate
python app\promotion_gate.py
Human-approved promotion
python app\approve_promotion.py
Inspect the model registry
python app\model_registry.py
Launch the dashboard
streamlit run app\dashboard.py
Demo and sandbox data

RecoverOS contains demo and sandbox tools for demonstrating the system without real customer transactions.

Examples:

python app\demo_outcomes.py
python app\sandbox_runner.py

These records are explicitly classified as simulated/non-production data.

They should not be presented as real customer production outcomes.

Verification

Run:

python -m compileall app
python app\model_registry.py
python app\decision_orchestrator.py
python app\outcome_engine.py
python app\production_feedback.py
python app\learning_loop.py
streamlit run app\dashboard.py
Scope and limitations

RecoverOS is a prototype.

The repository includes synthetic/demo/sandbox data and a limited amount of production-marked outcome data.

The current project therefore does not claim large-scale real-world production validation.

Production deployment would require additional work including:

live payment gateway integration
larger real-world datasets
authentication and authorization
privacy and security controls
monitoring and alerting
model drift detection
stronger statistical validation
temporal validation
production infrastructure
compliance review
Why RecoverOS?

RecoverOS is built around a simple principle:

Not every failed payment deserves the same response.

By combining payment context, machine learning, strategy optimization, policy rules, safety controls, explainability, auditability, and controlled model learning, RecoverOS aims to make payment recovery more intelligent and safer than blind retry automation.

Disclaimer

All demo, sandbox, test, and simulated payment data in this repository are synthetic or simulated.

This project does not claim that simulated outcomes represent real Razorpay customers, merchants, transactions, or production recovery performance.

RecoverOS is a prototype created for experimentation, learning, and demonstration.
