<div align="center">

# ⚡ RecoverOS

### AI-Powered Revenue Recovery Orchestration

**Detect revenue at risk → predict recoverability → optimize the intervention → enforce policy & safety → execute bounded recovery workflows**

<p>
  <a href="https://recover-os-delta.vercel.app/">🌐 Live Demo</a> •
  <a href="https://recoveros-api-ovp0.onrender.com/docs">📚 API Docs</a> •
  <a href="https://github.com/lucky23-afk/RecoverOS">💻 GitHub</a>
</p>

<img src="https://img.shields.io/badge/Razorpay-Buildathon%20Track%2003-0C2340?style=for-the-badge" alt="Razorpay Buildathon Track 03" />
<img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
<img src="https://img.shields.io/badge/Frontend-Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
<img src="https://img.shields.io/badge/ML-scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="scikit-learn" />

</div>

---

## 🎯 What is RecoverOS?

Payment failures are not all the same.

A temporary bank timeout may justify a retry. An expired card requires customer action. Insufficient funds may need a delayed reminder. Suspicious activity should stop automation and go for review.

**RecoverOS is an AI-powered revenue recovery decision and orchestration platform built to handle these cases differently.**

Instead of blindly retrying every failed payment, RecoverOS combines:

- 🤖 ML-based recovery prediction
- 💰 Expected Recovered Value (ERV) optimization
- 🛡️ Policy-controlled decisioning
- 🔒 Safety guardrails
- ⏱️ Cause-aware retry scheduling
- 🔄 Bounded recovery workflows
- ✅ Verification
- 📋 Auditability

> **AI predicts. ERV optimizes. Policy authorizes. Safety constrains. Workflows execute. Audit records.**

---

## 🧠 Decision Engine

<p align="center">
  <img src="./assets/decision-demo.png" alt="RecoverOS Decision Engine" width="900">
</p>

The core decision pipeline:

```text
Failed Payment
      ↓
Understand Failure Context
      ↓
Predict Recovery Probability
      ↓
Rank Actions by Expected Recovered Value
      ↓
Apply Policy Constraints
      ↓
Run Safety Checks
      ↓
Choose Final Action
      ↓
Schedule / Execute Bounded Workflow
      ↓
Verify Outcome
      ↓
Record Decision
