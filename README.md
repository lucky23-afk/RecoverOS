RecoverOS

AI-powered revenue recovery platform that detects revenue at risk, chooses the safest recovery action, and runs bounded recovery workflows.

Built for the Razorpay Buildathon — Track 03: AI Revenue Recovery.

🚀 Live Demo

Resource

Link

🌐 Live Demo

https://recover-os-delta.vercel.app/

⚙️ API

https://recoveros-api-ovp0.onrender.com/

📚 API Docs

https://recoveros-api-ovp0.onrender.com/docs

💻 GitHub

https://github.com/lucky23-afk/RecoverOS

Overview

Payment failures are not all the same.

A temporary bank timeout may justify a retry. An expired card needs a payment-method update. Suspicious activity should be stopped and routed for review. High-value or ambiguous cases may require human intervention.

RecoverOS is designed around that distinction.

Decision Flow

Detect revenue at risk
        ↓
Predict recovery probability
        ↓
Optimize Expected Recovered Value (ERV)
        ↓
Apply policy constraints
        ↓
Run safety checks
        ↓
Choose a bounded recovery action
        ↓
Schedule / execute the workflow
        ↓
Verify the outcome
        ↓
Record the decision in the audit trail

AI chooses. ERV optimizes. Policy authorizes. Safety constrains. Workflows recover. Audit records.

✨ Key Features

🤖 AI Recovery Decisioning

The ML layer estimates whether a failed payment can be recovered from payment and customer context.

Inputs include:

Amount

Failure reason

Payment method

Merchant type

Previous successes and failures

Retry count

Days since last payment

Customer tenure

Mandate age

Average amount

Amount vs. average

Recent success rate

Failure frequency

Retry interval

💰 Expected Recovered Value (ERV)

RecoverOS does not blindly choose the action with the highest probability. It ranks candidate actions using expected recovered value with cost and risk considerations.

Supported actions:

retry_payment
send_update_link
send_reminder
hold_for_review

🛡️ Policy Engine

The policy layer classifies failures and limits which actions are allowed.

Failure class

Typical actions

Transient

Retry, reminder, review

Customer action required

Update link, reminder, review

Risk

Review only

Unknown

Review only

🔒 Safety Engine

Hard controls protect automated recovery:

Maximum retry limits

Low-confidence review

Suspicious-reversal review

Recently changed mandate review

High-value payment review

Blocking when required

🔁 Cause-Aware Retry Scheduling

Recovery timing depends on the failure reason.

bank_timeout            → retry_payment        → 15 min
network_error           → retry_payment        → 30 min
temporary_bank_error    → retry_payment        → 60 min
insufficient_funds      → send_reminder        → 24 hours
expired_card            → send_update_link     → immediately
mandate_expired         → send_update_link     → immediately
suspicious_reversal     → hold_for_review      → no retry

Retry caps are enforced. At the retry limit, automatic retry stops and the case moves to review.

🔄 Recovery Workflows

RecoverOS includes bounded workflows for:

Payment degradation

Failed subscriptions

Mandate retries

Checkout abandonment

B2B receivables

Promise-to-pay tracking

Hinglish voice recovery

🗣️ Hinglish Voice Recovery

The voice module supports:

Browser speech recognition

Hinglish interaction

Voice-to-text processing

Recovery conversation turns

Promise-to-pay capture

Payment verification

📋 Auditability

Decision records capture the reasoning chain, including recovery probability, candidate actions, ERV, policy decision, safety decision, final action, reasons, expected revenue, integrity status, and retry plan.

🏗️ Architecture

                 ┌─────────────────────────┐
                 │     Next.js Frontend    │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │     FastAPI Backend     │
                 └────────────┬────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │  ML Model   │     │     ERV     │     │   Policy    │
   │ Prediction  │     │  Optimizer  │     │   Engine    │
   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
          └────────────────────┼────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │    Safety Engine    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Bounded Workflows   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Retry / Scheduling  │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Verification /      │
                    │ Provider Adapter    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ SQLite + Audit Trail│
                    └─────────────────────┘

🧠 Machine Learning

Current champion artifact:

models/recovery_model.pkl

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

The champion artifact is treated as a controlled model artifact and is not retrained during normal application execution.

🔗 Razorpay Test Mode Integration

RecoverOS includes a Razorpay Test Mode adapter and webhook layer.

Supported capabilities include:

Test Mode authentication

Payment lookup

Order lookup

Normalized payment status

Payment signature verification

Webhook signature verification

Webhook event normalization

Duplicate webhook protection

Endpoints:

GET  /razorpay/payment/{payment_id}
POST /razorpay/verify
POST /razorpay/webhook

The webhook layer verifies the provider signature before normalizing the event. Provider events should be enriched with application-side customer/history context before entering the 15-feature ML decision pipeline.

Boundary: the current provider integration is configured for Test Mode. This README does not claim production Razorpay money recovery.

🎯 Recovery Decision Examples

Transient failure

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
    ↓
Retry plan = 15 minutes

Risky failure

suspicious_reversal
    ↓
Policy = REVIEW
    ↓
Safety = REVIEW
    ↓
Final action = hold_for_review

The final action is accepted only when it remains inside policy and safety constraints.

📊 Controlled Evaluation

The batch evaluator compares a retry-first baseline with the RecoverOS decision pipeline using a deterministic sample of 1,000 labeled development records.

The metric below is historically recoverable-revenue capture. It is not a causal estimate of production revenue recovered.

Metric

Baseline

RecoverOS

Payments evaluated

1,000

1,000

Revenue at risk

₹5,296,500

₹5,296,500

Historically recoverable revenue captured

₹1,946,104

₹2,103,088

Recoverable-revenue capture rate

78.87%

85.23%

Automatic actions

759

745

Human review

241

255

Blocked

—

0

Comparison

Incremental historically recoverable revenue captured: ₹156,984
Capture-rate uplift: +6.36 percentage points
Policy violations: 0

🛡️ Safety & Production Boundaries

RecoverOS is intentionally designed around bounded automation.

Automatic retry has a maximum retry limit.

Risky cases can be routed to human review.

Low-confidence cases can be stopped.

Policy and safety checks remain authoritative.

The model artifact is not retrained during normal execution.

Production learning is kept separate from synthetic/demo outcomes.

Test Mode credentials and events are not production revenue evidence.

🧩 Recovery Coverage

✅ Payment degradation
✅ Failed subscriptions
✅ Mandate retry
✅ Checkout recovery
✅ B2B receivables
✅ Promise-to-pay
✅ Hinglish voice
✅ Cause-aware retry scheduling
✅ Razorpay Test Mode integration
✅ Shared policy controls
✅ Shared safety controls
✅ Audit trail

🧰 Tech Stack

Backend

Python

FastAPI

scikit-learn

pandas

NumPy

SQLite

Razorpay Python SDK

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

Cause-aware retry scheduler

Bounded workflow orchestration

Verification

Audit trail

Deployment

Frontend: Vercel

Backend: Render

Database: SQLite

📁 Project Structure

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
│   ├── razorpay_adapter.py
│   ├── receivables_recovery.py
│   ├── retry_scheduler.py
│   ├── safety_engine.py
│   ├── simulator.py
│   ├── subscription_recovery.py
│   ├── voice_api.py
│   ├── voice_persistence.py
│   └── voice_recovery.py
├── data/
│   └── advanced_training_data.csv
├── models/
│   └── recovery_model.pkl
└── frontend/
    ├── public/
    ├── src/
    │   └── app/
    │       ├── VoiceRecovery.tsx
    │       ├── globals.css
    │       ├── layout.tsx
    │       └── page.tsx
    ├── next.config.ts
    └── package.json

💻 Running Locally

1. Clone

git clone https://github.com/lucky23-afk/RecoverOS.git
cd RecoverOS

2. Create the Python environment

Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

3. Install backend dependencies

pip install -r requirements.txt

4. Configure environment variables

Create .env in the project root:

RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_secret
RAZORPAY_TEST_MODE=true
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

Never commit .env or real credentials.

5. Start the backend

uvicorn app.api:app --reload --host 127.0.0.1 --port 8000

Backend:

http://127.0.0.1:8000

API docs:

http://127.0.0.1:8000/docs

6. Start the frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:3000

🔌 API Surface

Core

GET  /health
GET  /database/health
GET  /metrics
POST /validate
POST /decision
POST /decision/raw

Razorpay

GET  /razorpay/payment/{payment_id}
POST /razorpay/verify
POST /razorpay/webhook

Recovery Workflows

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

Voice

POST /voice/start
POST /voice/turn
POST /voice/transcribe
POST /voice/verify

Interactive API documentation:

https://recoveros-api-ovp0.onrender.com/docs

🎬 Demo Flow

Payment Recovery

Open the live site.

Go to Payment Recovery.

Enter a failed-payment scenario.

Run the decision.

Show ML probability, ERV ranking, policy, safety, final action, and retry plan.

Show the audit record.

Subscription / Mandate / Checkout / Receivables

Select the workflow.

Start recovery.

Execute the bounded action.

Verify the payment or record the promise-to-pay state.

Show the resulting workflow status.

Voice Recovery

Open Voice Recovery.

Start a voice session.

Speak in Hinglish.

Continue the recovery conversation.

Capture the promise-to-pay response.

Verify the resulting recovery state.

🏆 Hackathon

Razorpay Buildathon — Track 03: AI Revenue Recovery

Team: Fernweh

🔗 Links

🌐 Live Demo: https://recover-os-delta.vercel.app/

⚙️ API: https://recoveros-api-ovp0.onrender.com/

📚 API Docs: https://recoveros-api-ovp0.onrender.com/docs

💻 GitHub: https://github.com/lucky23-afk/RecoverOS

Disclaimer

RecoverOS is a hackathon prototype.

The project demonstrates revenue-risk detection, recovery decisioning, ERV optimization, policy controls, safety guardrails, bounded recovery workflows, voice recovery, verification, Razorpay Test Mode integration, and auditability.

The evaluation figures in this README are controlled benchmark results based on development data. They are not claims of actual production money recovered or live Razorpay recovery performance.
