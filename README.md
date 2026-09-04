RecoverOS

AI-powered revenue recovery platform that detects revenue at risk, selects the safest recovery action, and executes bounded recovery workflows.

🚀 Live Demo

Website: https://recover-os-delta.vercel.app
API: https://recoveros-api-ovp0.onrender.com
API Docs: https://recoveros-api-ovp0.onrender.com/docs

GitHub: https://github.com/lucky23-afk/RecoverOS

Overview

RecoverOS is a revenue recovery decision platform built for the Razorpay Buildathon — Track 03: AI Revenue Recovery.

Instead of blindly retrying failed payments, RecoverOS combines machine-learning recovery prediction with Expected Recovered Value (ERV) optimization, policy controls, safety checks, bounded recovery workflows, verification, and auditability.

The core idea is simple:

Detect risk
    ↓
Predict recovery probability
    ↓
Optimize Expected Recovered Value
    ↓
Apply policy constraints
    ↓
Run safety checks
    ↓
Execute a bounded recovery action
    ↓
Verify outcome
    ↓
Record the decision

Why RecoverOS?

Payment failures do not all need the same response.

A temporary bank timeout may justify a retry, while an expired card should route the customer toward a payment-method update. Suspicious activity should not be automatically retried, and high-value or ambiguous cases can be escalated for human review.

RecoverOS is designed around that distinction.

AI chooses. ERV optimizes. Policy authorizes. Safety constrains. Workflows recover. Audit records.

Key Features

🤖 AI Recovery Decisioning

The ML layer estimates the probability that a payment can be recovered using payment and customer context, including:

Amount

Failure reason

Payment method

Merchant type

Previous successes and failures

Retry count

Customer tenure

Mandate age

Average amount

Recent success rate

Failure frequency

Retry interval

💰 Expected Recovered Value (ERV)

RecoverOS does not simply choose the action with the highest probability.

It compares candidate actions using expected recovered value and risk-aware constraints.

Supported decisions include:

retry_payment

send_update_link

send_reminder

hold_for_review

🛡️ Policy Engine

The policy layer classifies failures and limits the actions that are allowed.

Examples:

Transient failures: retry/reminder/review

Customer-action failures: update-link/reminder/review

Risk failures: review only

Unknown failures: review only

🔒 Safety Engine

The safety layer provides hard stopping conditions around automated recovery.

Controls include:

Maximum retry limits

Low-confidence review

Suspicious-reversal review

Recently changed mandate review

High-value payment review

Blocking when required

🔁 Recovery Workflows

RecoverOS provides separate bounded workflows for:

Payment degradation

Failed subscriptions

Mandate retries

Checkout abandonment

B2B receivables

Promise-to-pay tracking

Hinglish voice recovery

🗣️ Hinglish Voice Recovery

The voice module supports conversational recovery with:

Browser speech recognition

Hinglish interaction

Voice-to-text processing

Recovery conversation turns

Promise-to-pay capture

Payment verification

📋 Auditability

Decision records capture the reasoning chain, including:

Recovery probability

Candidate actions

ERV

Policy decision

Safety decision

Final action

Policy/safety reasons

Expected revenue

Integrity status

Architecture

                    ┌─────────────────────┐
                    │    Next.js Frontend │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend  │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          ┌────────────┐ ┌───────────┐ ┌────────────┐
          │ ML Model   │ │    ERV    │ │   Policy   │
          │ Prediction │ │ Optimizer │ │   Engine   │
          └──────┬─────┘ └─────┬─────┘ └──────┬─────┘
                 └──────────────┼──────────────┘
                                ▼
                       ┌────────────────┐
                       │ Safety Engine  │
                       └───────┬────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Bounded Recovery    │
                    │ Workflows           │
                    └──────────┬──────────┘
                               ▼
                       ┌──────────────┐
                       │ Verification │
                       └──────┬───────┘
                              ▼
                       ┌─────────────┐
                       │ SQLite +    │
                       │ Audit Trail │
                       └─────────────┘

Machine Learning

The current champion model is stored at:

models/recovery_model.pkl

The model evaluator reports:

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

The champion artifact is treated as a controlled model artifact and is not retrained as part of normal application execution.

Recovery Decision Example

A transient payment failure can move through the system like this:

bank_timeout
     ↓
ML recovery probability
     ↓
ERV candidate ranking
     ↓
Policy = ALLOW
     ↓
Safety = ALLOW
     ↓
Final action = retry_payment

A risky failure can instead be stopped:

suspicious_reversal
     ↓
Policy = REVIEW
     ↓
Safety = REVIEW
     ↓
Final action = hold_for_review

The final action is only accepted when it remains within policy and safety constraints.

Recovery Coverage

✅ Payment Degradation
✅ Failed Subscriptions
✅ Mandate Retry
✅ Checkout Recovery
✅ B2B Receivables
✅ Promise-to-Pay
✅ Hinglish Voice
✅ Shared Safety Controls

Tech Stack

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

Random Forest recovery prediction

Expected Recovered Value optimization

Policy engine

Safety engine

Bounded workflow orchestration

Audit trail

Deployment

Frontend: Vercel

Backend: Render

Database: SQLite

Project Structure

RecoverOS/
├── app/
│   ├── api.py
│   ├── batch_evaluation.py
│   ├── checkout_recovery.py
│   ├── database.py
│   ├── decision_orchestrator.py
│   ├── erv_optimizer.py
│   ├── mandate_retry.py
│   ├── ml_model.py
│   ├── persistence.py
│   ├── policy_engine.py
│   ├── receivables_recovery.py
│   ├── safety_engine.py
│   ├── simulator.py
│   ├── subscription_recovery.py
│   ├── voice_api.py
│   ├── voice_persistence.py
│   └── voice_recovery.py
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
    │       ├── VoiceRecovery.tsx
    │       ├── globals.css
    │       ├── layout.tsx
    │       └── page.tsx
    ├── public/
    ├── package.json
    └── next.config.ts

Running Locally

1. Clone

git clone https://github.com/lucky23-afk/RecoverOS.git
cd RecoverOS

2. Create the Python environment

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

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:3000

Public API

The deployed backend exposes:

GET  /health
GET  /database/health
GET  /metrics
POST /validate
POST /decision
POST /decision/raw

POST /subscription/start
POST /subscription/execute
POST /subscription/verify

POST /mandate/start
POST /mandate/execute
POST /mandate/verify

POST /checkout/start
POST /checkout/execute
POST /checkout/verify

POST /receivables/start
POST /receivables/execute
POST /receivables/promise
POST /receivables/verify

POST /voice/start
POST /voice/turn
POST /voice/transcribe
POST /voice/verify

Interactive API documentation:

https://recoveros-api-ovp0.onrender.com/docs

Evaluation

RecoverOS includes a batch evaluation framework designed to compare recovery strategies over a controlled set of cases.

The repository's evaluation figures are presented as controlled/synthetic evaluation, separate from live production metrics.

Current dashboard evaluation figures:

Metric

Controlled Evaluation

Cases

1,000

Revenue at Risk

₹3,624,850

RecoverOS Recovered

₹2,489,750

Recovery Rate

66.5%

Incremental Recovery

₹958,800

Uplift vs baseline

+24.1 percentage points

Policy Violations

0

Safety Compliance

100%

These values are not production revenue claims and should not be interpreted as live Razorpay recovery performance.

Safety & Production Boundaries

RecoverOS is intentionally designed around bounded automation.

Payment execution is disabled by design in the prototype. Automated actions are constrained by policy, retry limits, safety gates, and review paths.

The system also keeps production learning separate from synthetic/demo outcomes. Real production feedback is required before production retraining is allowed.

Demo Flow

For a quick demonstration:

Payment Recovery

Open the live site.

Go to Payment Recovery.

Enter a failed-payment scenario.

Run the decision.

Show the ML probability, ERV recommendation, policy result, safety result, and final action.

Subscription / Mandate / Checkout / Receivables

Select the corresponding workflow.

Start the recovery workflow.

Execute the bounded action.

Verify the payment or record the promise-to-pay state.

Show the resulting workflow status and recovery value.

Voice Recovery

Open Voice Recovery.

Start a voice session.

Speak in Hinglish.

Continue the recovery conversation.

Capture a promise-to-pay response.

Verify the resulting recovery state.

Hackathon

Razorpay Buildathon — Track 03: AI Revenue Recovery

Team: Fernweh

Links

🌐 Live Demo: https://recover-os-delta.vercel.app

⚙️ API: https://recoveros-api-ovp0.onrender.com

📚 API Docs: https://recoveros-api-ovp0.onrender.com/docs

💻 GitHub: https://github.com/lucky23-afk/RecoverOS

Disclaimer

RecoverOS is a hackathon prototype.

The project demonstrates revenue-risk detection, recovery decisioning, ERV optimization, policy controls, safety guardrails, bounded recovery workflows, voice recovery, verification, and auditability.

The controlled evaluation figures shown in the dashboard are synthetic/controlled results and are not claims of actual production money recovered or live Razorpay tra
