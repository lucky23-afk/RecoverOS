evaluation figures.

<div align="center">

# ⚡ RecoverOS

### AI-Powered Revenue Recovery Orchestration

**Detect revenue at risk → predict recoverability → optimize the intervention → enforce policy & safety → run bounded recovery workflows**

<p>
  <a href="https://recover-os-delta.vercel.app/">🌐 Live Demo</a> •
  <a href="https://recoveros-api-ovp0.onrender.com/docs">📚 API Docs</a> •
  <a href="https://github.com/lucky23-afk/RecoverOS">💻 GitHub</a>
</p>

<img src="https://img.shields.io/badge/Razorpay-Buildathon%20Track%2003-0C2340?style=for-the-badge" alt="Razorpay Buildathon Track 03" />
<img src="https://img.shields.io/badge/Status-Hackathon%20Prototype-7C3AED?style=for-the-badge" alt="Hackathon Prototype" />
<img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
<img src="https://img.shields.io/badge/Frontend-Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
<img src="https://img.shields.io/badge/ML-scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />

</div>

---

## 🎯 What is RecoverOS?

Payment failures are not all the same.

A temporary bank timeout may justify a retry. An expired card requires customer action. Insufficient funds may need a delayed reminder. Suspicious activity should be stopped and sent for review.

**RecoverOS is an AI-powered revenue recovery decision and orchestration platform built to handle those cases differently.**

Instead of blindly retrying every failed payment, RecoverOS combines:

- 🤖 ML-based recovery prediction
- 💰 Expected Recovered Value (ERV) optimization
- 🛡️ Policy-controlled decisioning
- 🔒 Safety guardrails
- ⏱️ Cause-aware retry scheduling
- 🔄 Bounded recovery workflows
- ✅ Verification
- 📋 Auditability

### Core Principle

> **AI chooses. ERV optimizes. Policy authorizes. Safety constrains. Workflows execute. Audit records.**

---

## 🚨 The Problem

Traditional payment recovery can look like this:

```text
Payment fails
     ↓
Retry
     ↓
Retry again
     ↓
Retry again

That approach treats every failure the same.

RecoverOS instead reasons about why the payment failed and what intervention is appropriate:

Payment Failure
      ↓
Understand the failure context
      ↓
Predict recovery probability
      ↓
Rank recovery actions by expected value
      ↓
Apply policy constraints
      ↓
Run safety checks
      ↓
Choose final action
      ↓
Schedule / execute bounded workflow
      ↓
Verify outcome
      ↓
Record decision

🧠 Decision Pipeline
<p align="center">
  <img src="./assets/decision-demo.png.png" alt="RecoverOS Decision Engine" width="900">
</p>

<p align="center">
  <sub>ML → ERV → Policy → Safety → Final Action → Retry Plan</sub>
</p>

The decision system is deliberately bounded:

ML
 ↓
ERV
 ↓
Policy
 ↓
Safety
 ↓
Final Action

The optimizer does not bypass policy or safety controls.


💡 Why RecoverOS?
Traditional Recovery
Failure
  ↓
Retry
  ↓
Retry
  ↓
Retry
RecoverOS
Failure
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

RecoverOS is designed around the idea that the best recovery action is not always the action with the highest probability of success.

The system considers:

likelihood of recovery
action cost
risk
customer/payment context
retry count
failure type
policy restrictions
safety conditions
✨ Key Features
🤖 AI Recovery Decisioning

The current champion model predicts the probability that a failed payment can be recovered.

The model uses 15 features:

Amount
Failure reason
Payment method
Merchant type
Previous successes
Previous failures
Retry count
Days since last payment
Customer tenure
Mandate age
Average amount
Amount vs average
Recent success rate
Failure frequency
Retry interval
💰 Expected Recovered Value (ERV)

RecoverOS does not blindly choose the action with the highest raw probability.

Instead it evaluates candidate actions using Expected Recovered Value, taking recovery probability, cost, and risk into account.

Supported recovery actions include:

retry_payment
send_update_link
send_reminder
hold_for_review

Example:

Action                  Probability      Expected Value
--------------------------------------------------------
retry_payment              High              ₹X
send_update_link           High              ₹Y
hold_for_review            Lower             ₹Z

The final decision is still constrained by policy and safety.

🛡️ Policy Engine

The policy engine determines which actions are allowed for a failure class.

Failure Class	Typical Allowed Actions
Transient	Retry / Reminder / Review
Customer Action Required	Update Link / Reminder / Review
Risk	Review Only
Unknown	Review Only

Examples:

bank_timeout
→ retry_payment allowed

expired_card
→ send_update_link allowed

insufficient_funds
→ send_reminder allowed

suspicious_reversal
→ hold_for_review only
🔒 Safety Engine

Safety controls provide hard boundaries around automated recovery.

Current controls include:

Maximum retry limit
Low-confidence review
Suspicious-reversal review
Recently changed mandate review
High-value payment review
Blocking when required
Example
retry_count >= maximum
        ↓
automatic retry stopped
        ↓
hold_for_review

The safety layer can override an otherwise favorable recovery recommendation.

⏱️ Cause-Aware Retry Scheduling

RecoverOS does not use one universal retry delay.

The delay depends on the failure cause.

bank_timeout
    → retry_payment
    → 15 minutes

network_error
    → retry_payment
    → 30 minutes

temporary_bank_error
    → retry_payment
    → 60 minutes

insufficient_funds
    → send_reminder
    → 24 hours

expired_card
    → send_update_link
    → immediately

mandate_expired
    → send_update_link
    → immediately

suspicious_reversal
    → hold_for_review
    → no automatic retry

Retry limits are enforced automatically.

🔄 Recovery Workflows

RecoverOS supports multiple revenue-recovery workflows:

Payment Recovery

Recover transient and payment-method failures using ML-driven decisioning.

Failed Subscriptions

Handle recurring payment failures through bounded subscription recovery flows.

Mandate Retry

Manage recurring/mandate-related payment failures with retry limits and verification.

Checkout Recovery

Handle checkout abandonment and payment-stage drop-offs.

B2B Receivables

Manage overdue invoices and recovery actions.

Promise-to-Pay

Capture customer commitments and track promised payment dates.

Voice Recovery

Enable conversational recovery using browser voice interaction and Hinglish support.

🗣️ Hinglish Voice Recovery

The voice workflow supports:

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

The system is designed for customer recovery conversations rather than simply sending static messages.

📋 Auditability

Every decision can preserve the reasoning chain.

Payment Context
      ↓
Recovery Probability
      ↓
Candidate Actions
      ↓
ERV
      ↓
Policy Decision
      ↓
Safety Decision
      ↓
Final Action
      ↓
Retry Plan
      ↓
Integrity Result

This makes the recovery decision explainable and reviewable.

📊 Machine Learning Performance

Current champion artifact:

models/recovery_model.pkl

Evaluator output:

Metric	Result
Records	10,000
Features	15
Accuracy	81.74%
Precision	83.17%
Recall	79.07%
F1 Score	81.07%
ROC-AUC	90.87%

Note: These metrics are evaluator results on the development dataset. They should not be interpreted as independent holdout/test-set performance.

The champion model artifact is treated as controlled and is not retrained during normal application execution.

📈 Controlled Recovery Evaluation

RecoverOS also includes a controlled batch evaluation comparing a retry-first baseline with the RecoverOS decision pipeline.

Latest Evaluation
Metric	Baseline	RecoverOS
Payments evaluated	1,000	1,000
Revenue at risk	₹5,296,500	₹5,296,500
Historically recoverable revenue captured	₹1,946,104	₹2,103,088
Recoverable-revenue capture rate	78.87%	85.23%
Automatic actions	759	745
Human review	241	255
Blocked	—	0
Improvement
Incremental historically recoverable revenue captured
₹156,984

Capture-rate uplift
+6.36 percentage points

Policy violations
0
Important Interpretation

These figures are from a controlled benchmark using development/labeled data.

They represent historically recoverable-revenue capture, not proof that RecoverOS causally recovered that amount of live money.

They should not be presented as actual Razorpay production revenue recovered.

💳 Razorpay Test Mode Integration

RecoverOS includes a Razorpay Test Mode integration layer.

Supported
Razorpay Test Mode authentication
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
Webhook
https://recoveros-api-ovp0.onrender.com/razorpay/webhook

The webhook layer verifies the incoming Razorpay signature before normalizing the event.

Provider events are then intended to be enriched with RecoverOS customer/payment history before entering the full 15-feature ML decision pipeline.

Current boundary: Razorpay integration is configured for Test Mode. This project does not claim live production Razorpay money recovery.

🏗️ System Architecture
                         ┌──────────────────────┐
                         │     Next.js UI       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    FastAPI Backend   │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
      │   ML Model   │      │     ERV      │      │    Policy    │
      │  Prediction  │      │  Optimizer   │      │    Engine    │
      └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
             └─────────────────────┼──────────────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │    Safety Engine    │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Bounded Workflows   │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Retry Scheduler      │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Verification /       │
                         │ Razorpay Adapter    │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ SQLite + Audit Trail │
                         └──────────────────────┘
🧰 Tech Stack
Frontend
Next.js
React
TypeScript
Tailwind CSS
Backend
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
Payment signature verification
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
│
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
│
├── data/
│   └── advanced_training_data.csv
│
├── models/
│   └── recovery_model.pkl
│
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
│
├── requirements.txt
└── README.md
⚙️ Quick Start
1. Clone the repository
git clone https://github.com/lucky23-afk/RecoverOS.git
cd RecoverOS
2. Create the Python environment
Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
3. Install backend dependencies
pip install -r requirements.txt
4. Configure environment variables

Create a .env file in the project root:

RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_secret
RAZORPAY_TEST_MODE=true
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

Never commit secrets to GitHub.

5. Start the backend
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000

Backend:

http://127.0.0.1:8000

API documentation:

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
Subscription Recovery
POST /subscription/start
POST /subscription/execute
POST /subscription/verify
Mandate Recovery
POST /mandate/start
POST /mandate/execute
POST /mandate/verify
Checkout Recovery
POST /checkout/start
POST /checkout/execute
POST /checkout/verify
Receivables
POST /receivables/start
POST /receivables/execute
POST /receivables/promise
POST /receivables/verify
Voice Recovery
POST /voice/start
POST /voice/turn
POST /voice/transcribe
POST /voice/verify
🎬 Demo Flow
Payment Recovery
Open Live Demo
      ↓
Payment Recovery
      ↓
Enter Failed Payment Scenario
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
Example: Transient Failure
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
15 minute retry plan
Example: Risky Failure
suspicious_reversal
     ↓
Policy = REVIEW
     ↓
Safety = REVIEW
     ↓
hold_for_review
🔐 Safety & Production Boundaries

RecoverOS is intentionally designed as a bounded recovery system.

Current boundaries include:

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

The project is a hackathon prototype demonstrating the recovery decision architecture.

🏆 Razorpay Buildathon
Razorpay Buildathon — Track 03: AI Revenue Recovery


RecoverOS was built around the challenge of identifying revenue at risk and selecting the safest, most economically useful intervention for failed payments and related recovery scenarios.

🔗 Links
🌐 Live Demo

https://recover-os-delta.vercel.app/

⚙️ API

https://recoveros-api-ovp0.onrender.com/

📚 API Documentation

https://recoveros-api-ovp0.onrender.com/docs

💻 GitHub

https://github.com/lucky23-afk/RecoverOS

</div> ```
