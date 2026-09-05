<div align="center">

⚡ RecoverOS

AI-Powered Revenue Recovery Orchestration

Detect revenue at risk → predict recoverability → optimize the intervention → enforce policy & safety → execute bounded recovery workflows

<p>
  <a href="https://recover-os-delta.vercel.app/">Live Demo</a> ·
  <a href="https://recoveros-api-ovp0.onrender.com/docs">API Docs</a> ·
  <a href="https://github.com/lucky23-afk/RecoverOS">GitHub</a>
</p>

<img src="https://img.shields.io/badge/Razorpay-Buildathon%20Track%2003-0C2340?style=for-the-badge" alt="Razorpay Buildathon Track 03" />
<img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
<img src="https://img.shields.io/badge/Frontend-Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
<img src="https://img.shields.io/badge/ML-scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />

</div>

The idea

Payment failures are not interchangeable.

A temporary bank timeout may be worth retrying. An expired card needs customer action. Insufficient funds may call for a delayed reminder. A suspicious reversal should stop automation and go to review.

RecoverOS turns those differences into decisions.

It is an AI-powered revenue recovery platform that combines ML prediction, Expected Recovered Value (ERV), policy controls, safety guardrails, cause-aware timing, and bounded workflows to decide what should happen next.

AI predicts. ERV optimizes. Policy authorizes. Safety constrains. Workflows execute. Audit records.

Decision Engine



The core decision path is:

Failed Payment
      │
      ▼
Understand Failure Context
      │
      ▼
Predict Recovery Probability
      │
      ▼
Rank Actions by Expected Recovered Value
      │
      ▼
Apply Policy
      │
      ▼
Run Safety Checks
      │
      ▼
Choose Final Action
      │
      ▼
Schedule / Execute Bounded Workflow
      │
      ▼
Verify Outcome
      │
      ▼
Audit Decision

The optimizer never bypasses policy or safety controls.

Why RecoverOS?

Traditional recovery

Payment fails
    ↓
Retry
    ↓
Retry again
    ↓
Retry again

RecoverOS

Payment fails
    ↓
Context
    ↓
Recovery Probability
    ↓
Economic Optimization
    ↓
Policy
    ↓
Safety
    ↓
Cause-Aware Timing
    ↓
Bounded Recovery
    ↓
Verification
    ↓
Audit

The goal is not simply to maximize retries. It is to choose the most useful and defensible intervention for each failure.

What it does

🤖 ML Recovery Prediction

The current champion model predicts the probability that a failed payment can be recovered.

It uses 15 features including:

Payment amount and payment method

Failure reason

Merchant type

Previous successes and failures

Retry count and retry interval

Customer tenure

Mandate age

Average payment amount

Amount vs. average

Recent success rate

Failure frequency

Days since last payment

💰 Expected Recovered Value

RecoverOS does not blindly pick the action with the highest probability.

Candidate actions are evaluated using Expected Recovered Value, taking recovery probability, cost, and risk into account.

Supported actions:

retry_payment · send_update_link · send_reminder · hold_for_review

🛡️ Policy Engine

Policies determine which actions are allowed for each failure class.

Failure class

Typical action

Transient

Retry / Reminder / Review

Customer action required

Update Link / Reminder / Review

Risk

Review only

Unknown

Review only

🔒 Safety Engine

Safety rules provide hard limits around automation:

Maximum retry limits

Low-confidence review

Suspicious-reversal review

Recently changed mandate review

High-value payment review

Blocking when required

Example:

retry_count >= maximum
        ↓
automatic retry stopped
        ↓
hold_for_review

⏱️ Cause-Aware Scheduling

Different failure causes get different recovery timing.

Failure

Action

Timing

bank_timeout

retry_payment

15 min

network_error

retry_payment

30 min

temporary_bank_error

retry_payment

60 min

insufficient_funds

send_reminder

24 hr

expired_card

send_update_link

Immediate

mandate_expired

send_update_link

Immediate

suspicious_reversal

hold_for_review

No automatic retry

Recovery Workflows

RecoverOS is designed beyond a single retry API.

Payment Recovery: ML-driven recovery for failed payments

Subscription Recovery: Bounded recovery for recurring payment failures

Mandate Retry: Controlled retry and verification for mandate-related failures

Checkout Recovery: Recovery of checkout/payment-stage drop-offs

B2B Receivables: Overdue invoice recovery

Promise-to-Pay: Capture and track customer payment commitments

Voice Recovery: Browser-based conversational recovery with Hinglish support

Voice recovery flow

Browser Speech Recognition
          ↓
Voice-to-Text
          ↓
Hinglish Recovery Conversation
          ↓
Promise-to-Pay Capture
          ↓
Payment Verification
          ↓
Recovery State

Evaluation

ML model

Current champion artifact:

models/recovery_model.pkl

Development-dataset evaluator results:

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

These are development/evaluator results, not independent holdout or production performance.

Controlled recovery benchmark

Metric

Retry-first baseline

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

Incremental historically recoverable revenue captured: ₹156,984
Capture-rate uplift: +6.36 percentage points
Policy violations: 0

This is a controlled benchmark on development/labeled data. It represents historically recoverable-revenue capture, not proof of live-money recovery or causal impact.

Razorpay Test Mode

RecoverOS includes a Razorpay Test Mode integration layer for:

Payment lookup

Order lookup

Payment status normalization

Payment signature verification

Webhook signature verification

Webhook event normalization

Duplicate-event protection

Endpoints

GET  /razorpay/payment/{payment_id}
POST /razorpay/verify
POST /razorpay/webhook

Webhook:

https://recoveros-api-ovp0.onrender.com/razorpay/webhook

Incoming webhooks are signature-verified before event normalization. Provider events are then intended to be enriched with RecoverOS customer/payment history before entering the full decision pipeline.

Boundary: the current integration is configured for Razorpay Test Mode. RecoverOS does not claim live production Razorpay money recovery.

Architecture

                         ┌──────────────────┐
                         │    Next.js UI    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  FastAPI Backend │
                         └────────┬─────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
       ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
       │  ML Model    │    │     ERV      │    │   Policy     │
       │  Prediction  │    │  Optimizer   │    │   Engine     │
       └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
              └───────────────────┼───────────────────┘
                                  ▼
                         ┌──────────────────┐
                         │  Safety Engine   │
                         └────────┬─────────┘
                                  ▼
                         ┌──────────────────┐
                         │ Bounded Workflow│
                         └────────┬─────────┘
                                  ▼
                         ┌──────────────────┐
                         │ Retry Scheduler  │
                         └────────┬─────────┘
                                  ▼
                         ┌──────────────────┐
                         │ Verification /   │
                         │ Razorpay Adapter │
                         └────────┬─────────┘
                                  ▼
                         ┌──────────────────┐
                         │ SQLite + Audit   │
                         └──────────────────┘

Tech Stack

Frontend

Next.js

React

TypeScript

Tailwind CSS

Backend & ML

Python

FastAPI

Pydantic

scikit-learn

pandas

NumPy

SQLite

Payments

Razorpay Python SDK

Razorpay Test Mode

Razorpay webhooks

Payment/signature verification

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
├── frontend/
│   ├── public/
│   ├── src/
│   │   └── app/
│   │       ├── VoiceRecovery.tsx
│   │       ├── globals.css
│   │       ├── layout.tsx
│   │       └── page.tsx
│   ├── next.config.ts
│   └── package.json
├── requirements.txt
└── README.md

Quick Start

1. Clone

git clone https://github.com/lucky23-afk/RecoverOS.git
cd RecoverOS

2. Backend environment

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

3. Environment variables

Create .env in the project root:

RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_secret
RAZORPAY_TEST_MODE=true
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

Never commit secrets to GitHub.

4. Start the backend

uvicorn app.api:app --reload --host 127.0.0.1 --port 8000

Backend:

http://127.0.0.1:8000

API docs:

http://127.0.0.1:8000/docs

5. Start the frontend

cd frontend
npm install
npm run dev

Frontend:

http://localhost:3000

API Surface

Core

GET  /health
GET  /database/health
GET  /metrics
POST /validate
POST /decision
POST /decision/raw

Recovery

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

Demo Flow

A typical payment-recovery demo looks like this:

Failed Payment Scenario
        ↓
Run Decision
        ↓
ML Probability
        ↓
ERV Ranking
        ↓
Policy Decision
        ↓
Safety Decision
        ↓
Final Action
        ↓
Retry Plan
        ↓
Audit Record

Example: transient failure

bank_timeout
    ↓
ML
    ↓
ERV
    ↓
Policy = ALLOW
    ↓
Safety = ALLOW
    ↓
retry_payment
    ↓
15-minute retry plan

Example: risky failure

suspicious_reversal
    ↓
Policy = REVIEW
    ↓
Safety = REVIEW
    ↓
hold_for_review

Safety & Production Boundaries

RecoverOS is intentionally a bounded recovery system.

It includes:

Maximum retry limits

Policy-controlled actions

Safety-controlled actions

Human-review paths

Low-confidence stopping

High-value review

Suspicious-event review

Controlled model artifact

Separation of production learning from demo/synthetic outcomes

RecoverOS does not claim:

Production Razorpay revenue recovery

Causal recovery from the controlled benchmark

Production-grade distributed payment infrastructure

Arbitrary LLM-controlled payment execution

This project is a hackathon prototype demonstrating the recovery decision architecture.

Razorpay Buildathon

Track 03: AI Revenue Recovery

RecoverOS was built around the challenge of identifying revenue at risk and selecting the safest, most economically useful intervention for failed payments and related recovery scenarios.

Links

Live Demo: https://recover-os-delta.vercel.app/

API: https://recoveros-api-ovp0.onrender.com/

API Documentation: https://recoveros-api-ovp0.onrender.com/docs

GitHub: https://github.com/lucky23-afk/RecoverOS

<div align="center">

RecoverOS · AI Revenue Recovery Orchestration

</div>
