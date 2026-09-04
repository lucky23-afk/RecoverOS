RecoverOS

AI-powered revenue recovery platform for detecting at-risk payments, selecting the right intervention, and executing bounded recovery workflows.

RecoverOS is a hackathon-built revenue recovery system created for the Razorpay Buildathon — Track 03: AI Revenue Recovery.

It combines machine learning, expected recovered value (ERV) optimization, policy controls, safety checks, recovery workflows, auditability, and a web interface into one decisioning platform.

🚀 What RecoverOS Does

RecoverOS helps merchants identify revenue at risk and decide what to do next:

Detect → Predict → Optimize → Validate → Recover → Audit

It supports recovery workflows for:

💳 Payment failures

🔄 Failed subscriptions

🏦 Mandate retries

🛒 Checkout abandonment

🧾 B2B receivables

🎙️ Hinglish voice recovery

🤝 Promise-to-pay tracking

🧠 Core Decision Flow

Payment / Customer Data
          ↓
   ML Recovery Prediction
          ↓
 Expected Recovered Value
          ↓
     Policy Engine
          ↓
     Safety Engine
          ↓
   Final Recovery Action
          ↓
 ┌────────┼────────────┐
 ↓        ↓            ↓
Retry   Update Link   Review
          ↓
      Audit Trail

RecoverOS does not blindly retry payments. Every action is constrained by recovery probability, failure context, retry limits, policy rules, risk checks, and stopping conditions.

✨ Key Features

AI Recovery Decisioning

The champion Random Forest model predicts recovery probability from payment and customer context including:

Payment amount

Failure reason

Payment method

Merchant type

Previous successes and failures

Retry count

Days since last payment

Customer tenure

Mandate age

Average payment amount

Amount vs. average

Recent success rate

Failure frequency

Retry interval

Expected Recovered Value (ERV)

RecoverOS evaluates candidate actions using expected recovered value instead of probability alone.

Supported actions include:

retry_payment

send_update_link

send_reminder

hold_for_review

The optimizer considers recovery probability, action effectiveness, risk penalties, retry constraints, and review requirements.

Policy Engine

Failure scenarios are classified into categories such as:

Transient — temporary payment/network failures

Customer Action — cases requiring a payment-method update or customer action

Risk — suspicious or potentially unsafe cases

Unknown — cases that require review rather than automated recovery

The policy layer determines which actions are permitted.

Safety Engine

RecoverOS adds a second safety boundary before an action is finalized.

Controls include:

Maximum retry limits

Low-probability review

Suspicious-reversal review

Recently changed mandate review

High-value payment review

Explicit block/review outcomes

Policy and safety integrity checks

Recovery Workflows

Dedicated modules handle:

Subscription recovery

Mandate retry sequencing

Checkout follow-ups

Receivables escalation

Voice recovery

Promise-to-pay tracking

Auditability

Decision records capture the important parts of the decision chain:

ML recovery probability

Optimizer recommendation

Expected recovered value

Policy decision

Safety decision

Final action

Decision reasons

Integrity status

📊 Model Performance

The current champion model is stored at:

models/recovery_model.pkl

The repository's model evaluation reports:

Metric

Result

Records

10,000

Features

15

Accuracy

81.74%

Precision

83.17%

Recall

79.07%

F1 Score

81.07%

ROC-AUC

90.87%

The champion artifact is treated as a controlled model and is not retrained during normal application execution.

🛡️ Production-Safety Design

RecoverOS is designed around bounded automation, not unrestricted autonomous payment execution.

High-risk or low-confidence scenarios can be routed to human review. The system also contains production-feedback and retraining gates so that real production evidence is required before production learning is allowed.

The current project should be considered a hackathon prototype. It does not claim real-world Razorpay recovery amounts or live Razorpay transaction execution.

🧪 Evaluation

A batch evaluation framework is included in the repository to compare recovery strategies over controlled cases and measure:

Revenue at risk

Recovered revenue

Recovery rate

Incremental recovery

Action distribution

Policy violations

Stopping-rule compliance

Evaluation outputs are generated separately from the core source code and are not treated as production evidence.

Any synthetic or controlled evaluation should be interpreted as prototype validation rather than real Razorpay performance.

🛠️ Tech Stack

Backend

Python

FastAPI

scikit-learn

pandas

NumPy

SQLite

Frontend

Next.js

React

TypeScript

Tailwind CSS

Decisioning

Random Forest

Expected Recovered Value optimization

Policy engine

Safety engine

Recovery orchestration

Voice

Browser speech recognition

Hinglish recovery flow

Promise-to-pay capture and verification

📁 Project Structure

RecoverOS/
├── app/
│   ├── api.py
│   ├── database.py
│   ├── persistence.py
│   ├── ml_model.py
│   ├── model_evaluator.py
│   ├── decision_orchestrator.py
│   ├── erv_optimizer.py
│   ├── policy_engine.py
│   ├── safety_engine.py
│   ├── simulator.py
│   ├── batch_evaluation.py
│   ├── subscription_recovery.py
│   ├── mandate_retry.py
│   ├── checkout_recovery.py
│   ├── receivables_recovery.py
│   ├── voice_recovery.py
│   ├── voice_api.py
│   └── voice_persistence.py
│
├── data/
│   └── advanced_training_data.csv
│
├── models/
│   └── recovery_model.pkl
│
└── frontend/
    ├── src/
    │   └── app/
    ├── public/
    ├── package.json
    └── next.config.ts

▶️ Run Locally

1. Clone the repository

git clone https://github.com/lucky23-afk/RecoverOS.git
cd RecoverOS

2. Create and activate the Python environment

Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

3. Install backend dependencies

pip install -r requirements.txt

4. Start the FastAPI backend

uvicorn app.api:app --reload

Backend:

http://127.0.0.1:8000

API docs:

http://127.0.0.1:8000/docs

5. Start the frontend

Open a second terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:3000

🔎 Example Decision

For a transient payment failure, a decision can move through the full pipeline:

bank_timeout
     ↓
ML recovery probability
     ↓
ERV optimization
     ↓
Policy: ALLOW
     ↓
Safety: ALLOW
     ↓
Final Action: retry_payment

A high-risk, high-value, or low-confidence case can instead terminate in:

hold_for_review

This separation makes the decision process explainable and auditable.

🎙️ Voice Recovery

RecoverOS includes a dedicated Voice Recovery interface for customer conversations.

The flow supports:

Starting a recovery conversation

Capturing a customer response

Continuing the recovery flow

Recording a promise to pay

Verifying the promise

The browser speech-recognition experience is intended for the project demo environment.

🏆 Hackathon

Event: Razorpay Buildathon
Track: Track 03 — AI Revenue Recovery
Team: Fernweh

⚠️ Disclaimer

RecoverOS is a hackathon prototype demonstrating AI-assisted revenue recovery decisioning and bounded workflow orchestration.

The project uses controlled/synthetic evaluation data where applicable and does not claim real Razorpay transaction recovery, production payment execution, or real production revenue recovered.

🔗 Repository

GitHub: https://github.com/lucky23-afk/RecoverOS
