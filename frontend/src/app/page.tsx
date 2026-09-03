"use client";

import { FormEvent, useEffect, useState } from "react";
import VoiceRecovery from "./VoiceRecovery";

const API_BASE = "http://127.0.0.1:8000";

type Tab =
  | "overview"
  | "payment"
  | "subscription"
  | "mandate"
  | "checkout"
  | "receivables"
  | "voice";

type AnyObject = Record<string, any>;

type Health = {
  status: string;
  database?: AnyObject;
};

type Metrics = {
  cases: number;
  amount_at_risk: number;
  recovered_amount: number;
  recovery_rate: number;
};

function money(value: number) {
  return `₹${Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}`;
}

function pct(value: number) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function pretty(value: unknown) {
  if (value === null || value === undefined) return "—";

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value).replaceAll("_", " ");
}

async function apiRequest(
  path: string,
  options: RequestInit = {}
) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      data?.detail ||
        data?.error ||
        "API request failed."
    );
  }

  return data;
}

function SectionTitle({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-bold">{title}</h2>
      <p className="mt-1 text-sm leading-6 text-slate-400">
        {description}
      </p>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm text-slate-300">
        {label}
      </label>

      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-400"
      />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div>
      <label className="mb-2 block text-sm text-slate-300">
        {label}
      </label>

      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-400"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </div>
  );
}

function ActionButton({
  children,
  onClick,
  disabled,
  secondary = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  secondary?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`rounded-xl px-5 py-3 font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${
        secondary
          ? "border border-slate-700 bg-slate-950 text-white hover:border-slate-500"
          : "bg-cyan-400 text-slate-950 hover:bg-cyan-300"
      }`}
    >
      {children}
    </button>
  );
}

function ResultBox({
  title,
  result,
}: {
  title: string;
  result: AnyObject | null;
}) {
  if (!result) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <div className="text-sm font-semibold text-slate-300">
          {title}
        </div>

        <div className="mt-5 text-sm text-slate-500">
          No result yet.
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
      <div className="text-sm font-semibold text-slate-300">
        {title}
      </div>

      <pre className="mt-4 max-h-[460px] overflow-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-400">
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
}

export default function Home() {
  const [tab, setTab] = useState<Tab>("overview");

  const [health, setHealth] =
    useState<Health | null>(null);

  const [metrics, setMetrics] =
    useState<Metrics | null>(null);

  const [globalError, setGlobalError] =
    useState("");

  const [loadingOverview, setLoadingOverview] =
    useState(true);

  // =============================================================
  // PAYMENT
  // =============================================================

  const [paymentId, setPaymentId] =
    useState("PAY_UI_001");

  const [paymentAmount, setPaymentAmount] =
    useState("2500");

  const [paymentFailure, setPaymentFailure] =
    useState("bank_timeout");

  const [paymentMethod, setPaymentMethod] =
    useState("netbanking");

  const [merchantType, setMerchantType] =
    useState("saas");

  const [paymentLoading, setPaymentLoading] =
    useState(false);

  const [paymentResult, setPaymentResult] =
    useState<AnyObject | null>(null);

  // =============================================================
  // SUBSCRIPTION
  // =============================================================

  const [subscriptionId, setSubscriptionId] =
    useState("SUB_UI_001");

  const [subscriptionCustomerId, setSubscriptionCustomerId] =
    useState("CUSTOMER_UI_001");

  const [subscriptionPaymentId, setSubscriptionPaymentId] =
    useState("PAY_SUB_UI_001");

  const [subscriptionAmount, setSubscriptionAmount] =
    useState("2499");

  const [subscriptionFailure, setSubscriptionFailure] =
    useState("bank_timeout");

  const [subscriptionPlan, setSubscriptionPlan] =
    useState("monthly");

  const [subscriptionState, setSubscriptionState] =
    useState<AnyObject | null>(null);

  const [subscriptionResult, setSubscriptionResult] =
    useState<AnyObject | null>(null);

  const [subscriptionPaidAmount, setSubscriptionPaidAmount] =
    useState("2499");

  const [subscriptionLoading, setSubscriptionLoading] =
    useState(false);

  // =============================================================
  // MANDATE
  // =============================================================

  const [mandateId, setMandateId] =
    useState("MANDATE_UI_001");

  const [mandateCustomerId, setMandateCustomerId] =
    useState("CUSTOMER_UI_001");

  const [mandatePaymentId, setMandatePaymentId] =
    useState("PAY_MANDATE_UI_001");

  const [mandateAmount, setMandateAmount] =
    useState("3499");

  const [mandateFailure, setMandateFailure] =
    useState("bank_timeout");

  const [mandateState, setMandateState] =
    useState<AnyObject | null>(null);

  const [mandateResult, setMandateResult] =
    useState<AnyObject | null>(null);

  const [mandatePaidAmount, setMandatePaidAmount] =
    useState("3499");

  const [mandateLoading, setMandateLoading] =
    useState(false);

  // =============================================================
  // CHECKOUT
  // =============================================================

  const [checkoutId, setCheckoutId] =
    useState("CHECKOUT_UI_001");

  const [checkoutCustomerId, setCheckoutCustomerId] =
    useState("CUSTOMER_UI_001");

  const [checkoutPaymentId, setCheckoutPaymentId] =
    useState("PAY_CHECKOUT_UI_001");

  const [checkoutAmount, setCheckoutAmount] =
    useState("2999");

  const [dropoffReason, setDropoffReason] =
    useState("payment_failed");

  const [checkoutStage, setCheckoutStage] =
    useState("payment");

  const [checkoutState, setCheckoutState] =
    useState<AnyObject | null>(null);

  const [checkoutResult, setCheckoutResult] =
    useState<AnyObject | null>(null);

  const [checkoutPaidAmount, setCheckoutPaidAmount] =
    useState("2999");

  const [checkoutLoading, setCheckoutLoading] =
    useState(false);

  // =============================================================
  // RECEIVABLES
  // =============================================================

  const [invoiceId, setInvoiceId] =
    useState("INV_UI_001");

  const [receivableCustomerId, setReceivableCustomerId] =
    useState("B2B_CUSTOMER_UI_001");

  const [customerName, setCustomerName] =
    useState("Demo Enterprise");

  const [invoiceAmount, setInvoiceAmount] =
    useState("45000");

  const [daysOverdue, setDaysOverdue] =
    useState("12");

  const [dueDate, setDueDate] =
    useState("2026-08-22");

  const [receivableState, setReceivableState] =
    useState<AnyObject | null>(null);

  const [receivableResult, setReceivableResult] =
    useState<AnyObject | null>(null);

  const [promiseDate, setPromiseDate] =
    useState("2026-09-07");

  const [promiseResponse, setPromiseResponse] =
    useState("Friday ko full payment kar denge.");

  const [receivablePaidAmount, setReceivablePaidAmount] =
    useState("45000");

  const [receivableLoading, setReceivableLoading] =
    useState(false);

  // =============================================================
  // OVERVIEW LOAD
  // =============================================================

  const loadOverview = async () => {
    try {
      setLoadingOverview(true);

      const [healthResponse, metricsResponse] =
        await Promise.all([
          apiRequest("/health"),
          apiRequest("/metrics"),
        ]);

      setHealth(healthResponse);
      setMetrics(metricsResponse.metrics);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Unable to connect to RecoverOS."
      );
    } finally {
      setLoadingOverview(false);
    }
  };

  useEffect(() => {
    loadOverview();

    const interval = setInterval(
      loadOverview,
      10000
    );

    return () => clearInterval(interval);
  }, []);

  // =============================================================
  // PAYMENT DECISION
  // =============================================================

  const runPaymentDecision = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setPaymentLoading(true);
    setGlobalError("");
    setPaymentResult(null);

    try {
      const amount = Number(paymentAmount);

      const result = await apiRequest(
        "/decision",
        {
          method: "POST",
          body: JSON.stringify({
            payment_id: paymentId,
            amount,
            failure_reason: paymentFailure,
            payment_method: paymentMethod,
            merchant_type: merchantType,
            previous_successes: 8,
            previous_failures: 1,
            retry_count: 1,
            days_since_last_payment: 12,
            customer_tenure_months: 18,
            mandate_age_days: 240,
            average_amount: 2300,
            amount_vs_average: amount / 2300,
            recent_success_rate: 0.89,
            failure_frequency: 0.05,
            retry_interval_hours: 6,
            risk_score: 0.1,
          }),
        }
      );

      setPaymentResult(result);
      await loadOverview();
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Payment decision failed."
      );
    } finally {
      setPaymentLoading(false);
    }
  };

  // =============================================================
  // SUBSCRIPTION
  // =============================================================

  const startSubscription = async () => {
    try {
      setSubscriptionLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/subscription/start",
        {
          method: "POST",
          body: JSON.stringify({
            subscription_id: subscriptionId,
            customer_id: subscriptionCustomerId,
            payment_id: subscriptionPaymentId,
            amount: Number(subscriptionAmount),
            failure_reason: subscriptionFailure,
            subscription_plan: subscriptionPlan,
          }),
        }
      );

      setSubscriptionState(
        result.subscription
      );

      setSubscriptionResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Subscription start failed."
      );
    } finally {
      setSubscriptionLoading(false);
    }
  };

  const executeSubscription = async () => {
    if (!subscriptionState) return;

    try {
      setSubscriptionLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/subscription/execute",
        {
          method: "POST",
          body: JSON.stringify(subscriptionState),
        }
      );

      setSubscriptionState(
        result.result?.subscription ||
          subscriptionState
      );

      setSubscriptionResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Subscription execution failed."
      );
    } finally {
      setSubscriptionLoading(false);
    }
  };

  const verifySubscription = async () => {
    if (!subscriptionState) return;

    try {
      setSubscriptionLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/subscription/verify",
        {
          method: "POST",
          body: JSON.stringify({
            subscription: subscriptionState,
            request: {
              paid_amount:
                Number(subscriptionPaidAmount),
            },
          }),
        }
      );

      setSubscriptionState(
        result.result?.subscription ||
          subscriptionState
      );

      setSubscriptionResult(result);

      await loadOverview();
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Subscription verification failed."
      );
    } finally {
      setSubscriptionLoading(false);
    }
  };

  // =============================================================
  // MANDATE
  // =============================================================

  const startMandate = async () => {
    try {
      setMandateLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/mandate/start",
        {
          method: "POST",
          body: JSON.stringify({
            mandate_id: mandateId,
            customer_id: mandateCustomerId,
            payment_id: mandatePaymentId,
            amount: Number(mandateAmount),
            failure_reason: mandateFailure,
            mandate_type: "recurring",
          }),
        }
      );

      setMandateState(result.mandate);
      setMandateResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Mandate start failed."
      );
    } finally {
      setMandateLoading(false);
    }
  };

  const executeMandate = async () => {
    if (!mandateState) return;

    try {
      setMandateLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/mandate/execute",
        {
          method: "POST",
          body: JSON.stringify(mandateState),
        }
      );

      setMandateState(
        result.result?.mandate ||
          mandateState
      );

      setMandateResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Mandate execution failed."
      );
    } finally {
      setMandateLoading(false);
    }
  };

  const verifyMandate = async () => {
    if (!mandateState) return;

    try {
      setMandateLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/mandate/verify",
        {
          method: "POST",
          body: JSON.stringify({
            mandate: mandateState,
            request: {
              paid_amount:
                Number(mandatePaidAmount),
            },
          }),
        }
      );

      setMandateState(
        result.result?.mandate ||
          mandateState
      );

      setMandateResult(result);

      await loadOverview();
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Mandate verification failed."
      );
    } finally {
      setMandateLoading(false);
    }
  };

  // =============================================================
  // CHECKOUT
  // =============================================================

  const startCheckout = async () => {
    try {
      setCheckoutLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/checkout/start",
        {
          method: "POST",
          body: JSON.stringify({
            checkout_id: checkoutId,
            customer_id: checkoutCustomerId,
            payment_id: checkoutPaymentId,
            amount: Number(checkoutAmount),
            dropoff_reason: dropoffReason,
            checkout_stage: checkoutStage,
          }),
        }
      );

      setCheckoutState(result.checkout);
      setCheckoutResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Checkout start failed."
      );
    } finally {
      setCheckoutLoading(false);
    }
  };

  const executeCheckout = async () => {
    if (!checkoutState) return;

    try {
      setCheckoutLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/checkout/execute",
        {
          method: "POST",
          body: JSON.stringify(checkoutState),
        }
      );

      setCheckoutState(
        result.result?.checkout ||
          checkoutState
      );

      setCheckoutResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Checkout execution failed."
      );
    } finally {
      setCheckoutLoading(false);
    }
  };

  const verifyCheckout = async () => {
    if (!checkoutState) return;

    try {
      setCheckoutLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/checkout/verify",
        {
          method: "POST",
          body: JSON.stringify({
            checkout: checkoutState,
            request: {
              paid_amount:
                Number(checkoutPaidAmount),
            },
          }),
        }
      );

      setCheckoutState(
        result.result?.checkout ||
          checkoutState
      );

      setCheckoutResult(result);

      await loadOverview();
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Checkout verification failed."
      );
    } finally {
      setCheckoutLoading(false);
    }
  };

  // =============================================================
  // RECEIVABLES
  // =============================================================

  const startReceivable = async () => {
    try {
      setReceivableLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/receivables/start",
        {
          method: "POST",
          body: JSON.stringify({
            invoice_id: invoiceId,
            customer_id: receivableCustomerId,
            amount: Number(invoiceAmount),
            days_overdue: Number(daysOverdue),
            due_date: dueDate,
            customer_name: customerName,
            invoice_currency: "INR",
          }),
        }
      );

      setReceivableState(
        result.receivable
      );

      setReceivableResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Receivable start failed."
      );
    } finally {
      setReceivableLoading(false);
    }
  };

  const executeReceivable = async () => {
    if (!receivableState) return;

    try {
      setReceivableLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/receivables/execute",
        {
          method: "POST",
          body: JSON.stringify(receivableState),
        }
      );

      setReceivableState(
        result.result?.receivable ||
          receivableState
      );

      setReceivableResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Receivable execution failed."
      );
    } finally {
      setReceivableLoading(false);
    }
  };

  const recordPromise = async () => {
    if (!receivableState) return;

    try {
      setReceivableLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/receivables/promise",
        {
          method: "POST",
          body: JSON.stringify({
            receivable: receivableState,
            request: {
              promised_date: promiseDate,
              response: promiseResponse,
            },
          }),
        }
      );

      setReceivableState(
        result.result?.receivable ||
          receivableState
      );

      setReceivableResult(result);
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Promise-to-pay failed."
      );
    } finally {
      setReceivableLoading(false);
    }
  };

  const verifyReceivable = async () => {
    if (!receivableState) return;

    try {
      setReceivableLoading(true);
      setGlobalError("");

      const result = await apiRequest(
        "/receivables/verify",
        {
          method: "POST",
          body: JSON.stringify({
            receivable: receivableState,
            request: {
              paid_amount:
                Number(receivablePaidAmount),
            },
          }),
        }
      );

      setReceivableState(
        result.result?.receivable ||
          receivableState
      );

      setReceivableResult(result);

      await loadOverview();
    } catch (error) {
      setGlobalError(
        error instanceof Error
          ? error.message
          : "Receivable verification failed."
      );
    } finally {
      setReceivableLoading(false);
    }
  };

  // =============================================================
  // NAVIGATION
  // =============================================================

  const navItems: {
    id: Tab;
    label: string;
  }[] = [
    {
      id: "overview",
      label: "Overview",
    },
    {
      id: "payment",
      label: "Payment Recovery",
    },
    {
      id: "subscription",
      label: "Subscriptions",
    },
    {
      id: "mandate",
      label: "Mandate Retry",
    },
    {
      id: "checkout",
      label: "Checkout",
    },
    {
      id: "receivables",
      label: "Receivables",
    },
    {
      id: "voice",
      label: "Voice Recovery",
    },
  ];

  const isHealthy =
    health?.status === "healthy" &&
    health?.database?.healthy === true;

  // =============================================================
  // UI
  // =============================================================

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      {/* HEADER */}
      <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between px-6 py-4">
          <div>
            <div className="text-xl font-bold">
              RecoverOS
            </div>

            <div className="text-xs text-slate-500">
              AI Revenue Recovery Platform
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900 px-3 py-2 text-xs">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                isHealthy
                  ? "bg-emerald-400"
                  : "bg-red-400"
              }`}
            />

            {isHealthy
              ? "Backend Healthy"
              : "Backend Offline"}
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-[1500px]">
        {/* SIDEBAR */}
        <aside className="hidden min-h-[calc(100vh-73px)] w-64 border-r border-slate-800 py-6 lg:block">
          <nav className="space-y-1 px-3">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setTab(item.id)}
                className={`w-full rounded-xl px-4 py-3 text-left text-sm font-medium transition ${
                  tab === item.id
                    ? "bg-cyan-400 text-slate-950"
                    : "text-slate-400 hover:bg-slate-900 hover:text-white"
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>

          <div className="mx-6 mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="text-xs uppercase tracking-wider text-slate-500">
              Architecture
            </div>

            <div className="mt-3 space-y-2 text-xs text-slate-400">
              <div>Next.js</div>
              <div>↓</div>
              <div>FastAPI</div>
              <div>↓</div>
              <div>ML / ERV / Policy</div>
              <div>↓</div>
              <div>SQLite</div>
            </div>
          </div>
        </aside>

        {/* MOBILE NAV */}
        <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-slate-800 bg-slate-950 p-2 lg:hidden">
          <div className="grid grid-cols-3 gap-1">
            {navItems.slice(0, 6).map((item) => (
              <button
                key={item.id}
                onClick={() => setTab(item.id)}
                className={`rounded-lg px-2 py-2 text-[10px] font-medium ${
                  tab === item.id
                    ? "bg-cyan-400 text-slate-950"
                    : "text-slate-400"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* CONTENT */}
        <section className="min-w-0 flex-1 px-6 py-8 pb-24 lg:pb-8">
          {globalError && (
            <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
              {globalError}
            </div>
          )}

          {/* =====================================================
              OVERVIEW
          ===================================================== */}

          {tab === "overview" && (
            <div>
              <SectionTitle
                title="Recovery Overview"
                description="Live operating view of RecoverOS revenue recovery intelligence."
              />

              {/* BUSINESS IMPACT */}
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    Revenue at Risk
                  </div>

                  <div className="mt-3 text-3xl font-bold">
                    ₹3,624,850
                  </div>

                  <div className="mt-2 text-xs text-slate-500">
                    Controlled 1,000-case evaluation
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    RecoverOS Recovered
                  </div>

                  <div className="mt-3 text-3xl font-bold text-emerald-400">
                    ₹2,489,750
                  </div>

                  <div className="mt-2 text-xs text-slate-500">
                    66.5% recovery rate
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    Incremental Recovery
                  </div>

                  <div className="mt-3 text-3xl font-bold text-cyan-300">
                    ₹958,800
                  </div>

                  <div className="mt-2 text-xs text-slate-500">
                    +24.1 percentage points vs baseline
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    Safety Compliance
                  </div>

                  <div className="mt-3 text-3xl font-bold text-emerald-400">
                    100%
                  </div>

                  <div className="mt-2 text-xs text-slate-500">
                    0 policy violations
                  </div>
                </div>
              </div>

              {/* LIVE SYSTEM METRICS */}
              <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    Cases Evaluated
                  </div>

                  <div className="mt-3 text-3xl font-bold">
                    {loadingOverview
                      ? "—"
                      : metrics?.cases ?? 0}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    Live Amount at Risk
                  </div>

                  <div className="mt-3 text-3xl font-bold">
                    {loadingOverview
                      ? "—"
                      : money(
                          metrics?.amount_at_risk ?? 0
                        )}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    Live Recovered Revenue
                  </div>

                  <div className="mt-3 text-3xl font-bold text-emerald-400">
                    {loadingOverview
                      ? "—"
                      : money(
                          metrics?.recovered_amount ?? 0
                        )}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
                  <div className="text-sm text-slate-400">
                    Live Recovery Rate
                  </div>

                  <div className="mt-3 text-3xl font-bold text-cyan-300">
                    {loadingOverview
                      ? "—"
                      : pct(
                          metrics?.recovery_rate ?? 0
                        )}
                  </div>
                </div>
              </div>

              {/* EVALUATION BANNER */}
              <div className="mt-8 rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-6">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <div className="text-xs uppercase tracking-wider text-cyan-300">
                      Controlled Evaluation
                    </div>

                    <h3 className="mt-2 text-xl font-bold">
                      RecoverOS recovered more revenue while respecting bounded controls.
                    </h3>

                    <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
                      Synthetic 1,000-case batch comparing a retry-first
                      baseline with the RecoverOS
                      ML → ERV → Policy → Safety
                      recovery pipeline.
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-700 bg-slate-950 px-5 py-4 text-center">
                    <div className="text-xs text-slate-500">
                      Recovery Uplift
                    </div>

                    <div className="mt-1 text-2xl font-bold text-emerald-400">
                      +24.1 pp
                    </div>
                  </div>
                </div>
              </div>

              {/* PLATFORM STATUS + PIPELINE */}
              <div className="mt-8 grid gap-6 xl:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <h3 className="font-semibold">
                    Platform Status
                  </h3>

                  <div className="mt-5 space-y-3">
                    {[
                      [
                        "FastAPI",
                        isHealthy
                          ? "ONLINE"
                          : "OFFLINE",
                      ],
                      [
                        "SQLite",
                        health?.database?.healthy
                          ? "HEALTHY"
                          : "OFFLINE",
                      ],
                      [
                        "Payment Execution",
                        "DISABLED",
                      ],
                      [
                        "Safety Layer",
                        "ACTIVE",
                      ],
                      [
                        "Policy Controls",
                        "ACTIVE",
                      ],
                      [
                        "Audit Trail",
                        "ACTIVE",
                      ],
                    ].map(([label, value]) => (
                      <div
                        key={label}
                        className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950 px-4 py-3"
                      >
                        <span className="text-sm text-slate-400">
                          {label}
                        </span>

                        <span
                          className={`text-sm font-semibold ${
                            value === "OFFLINE"
                              ? "text-red-400"
                              : "text-emerald-400"
                          }`}
                        >
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <h3 className="font-semibold">
                    Recovery Intelligence Pipeline
                  </h3>

                  <div className="mt-5 space-y-3">
                    {[
                      ["01", "Payment / Revenue Signal"],
                      ["02", "ML Recovery Prediction"],
                      ["03", "Expected Revenue Value"],
                      ["04", "Policy Constraint"],
                      ["05", "Safety Gate"],
                      ["06", "Bounded Recovery Action"],
                    ].map(([step, label]) => (
                      <div
                        key={step}
                        className="flex items-center gap-4 rounded-xl border border-slate-800 bg-slate-950 px-4 py-3"
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-400/10 text-xs font-bold text-cyan-300">
                          {step}
                        </div>

                        <span className="text-sm text-slate-300">
                          {label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* RECOVERY COVERAGE */}
              <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">
                      Recovery Coverage
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                      Seven recovery paths plus shared safety controls.
                    </p>
                  </div>

                  <div className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
                    8 / 8 Active
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {[
                    "Payment Degradation",
                    "Failed Subscriptions",
                    "Mandate Retry",
                    "Checkout Recovery",
                    "B2B Receivables",
                    "Promise-to-Pay",
                    "Hinglish Voice",
                    "Safety Controls",
                  ].map((item) => (
                    <div
                      key={item}
                      className="rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-300"
                    >
                      <span className="mr-2 text-emerald-400">
                        ✓
                      </span>

                      {item}
                    </div>
                  ))}
                </div>
              </div>

              {/* DATABASE */}
              <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">
                    Live Database Snapshot
                  </h3>

                  <button
                    type="button"
                    onClick={loadOverview}
                    disabled={loadingOverview}
                    className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-300 transition hover:border-slate-500 disabled:opacity-40"
                  >
                    {loadingOverview
                      ? "Refreshing..."
                      : "Refresh"}
                  </button>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                  {[
                    [
                      "Customers",
                      health?.database?.customers ?? 0,
                    ],
                    [
                      "Payments",
                      health?.database?.payments ?? 0,
                    ],
                    [
                      "Subscriptions",
                      health?.database?.subscriptions ?? 0,
                    ],
                    [
                      "Mandates",
                      health?.database?.mandates ?? 0,
                    ],
                    [
                      "Invoices",
                      health?.database?.invoices ?? 0,
                    ],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="rounded-xl border border-slate-800 bg-slate-950 p-4"
                    >
                      <div className="text-xs text-slate-500">
                        {label}
                      </div>

                      <div className="mt-2 text-2xl font-bold">
                        {value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* EVALUATION NOTE */}
              <div className="mt-6 rounded-xl border border-slate-800 bg-slate-950 px-5 py-4 text-xs leading-5 text-slate-500">
                Evaluation figures above are from a controlled synthetic
                batch and are shown separately from live database metrics.
                They are not production revenue claims.
              </div>
            </div>
          )}

          {/* =====================================================
              PAYMENT
          ===================================================== */}

          {tab === "payment" && (
            <div>
              <SectionTitle
                title="Payment Recovery"
                description="Run the authoritative ML → ERV → Policy → Safety decision pipeline."
              />

              <div className="grid gap-6 xl:grid-cols-2">
                <form
                  onSubmit={runPaymentDecision}
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-6"
                >
                  <div className="grid gap-4">
                    <Field
                      label="Payment ID"
                      value={paymentId}
                      onChange={setPaymentId}
                    />

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field
                        label="Amount"
                        type="number"
                        value={paymentAmount}
                        onChange={setPaymentAmount}
                      />

                      <SelectField
                        label="Failure Reason"
                        value={paymentFailure}
                        onChange={setPaymentFailure}
                        options={[
                          "bank_timeout",
                          "network_error",
                          "insufficient_funds",
                          "expired_card",
                          "card_declined",
                        ]}
                      />
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <SelectField
                        label="Payment Method"
                        value={paymentMethod}
                        onChange={setPaymentMethod}
                        options={[
                          "netbanking",
                          "card",
                          "upi",
                        ]}
                      />

                      <SelectField
                        label="Merchant Type"
                        value={merchantType}
                        onChange={setMerchantType}
                        options={[
                          "saas",
                          "ecommerce",
                          "marketplace",
                        ]}
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={paymentLoading}
                      className="mt-2 rounded-xl bg-cyan-400 px-5 py-3.5 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:opacity-40"
                    >
                      {paymentLoading
                        ? "Running..."
                        : "Run Recovery Decision"}
                    </button>
                  </div>
                </form>

                {paymentResult ? (
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-6">
                      <div className="text-xs uppercase tracking-wider text-cyan-300">
                        Final Action
                      </div>

                      <div className="mt-2 text-3xl font-bold capitalize">
                        {pretty(
                          paymentResult.final_action
                        )}
                      </div>

                      <div className="mt-3 text-sm text-slate-400">
                        ML probability:{" "}
                        {pct(
                          paymentResult.recovery_probability
                        )}
                      </div>

                      <div className="mt-1 text-sm text-slate-400">
                        Expected revenue:{" "}
                        {money(
                          paymentResult.expected_revenue
                        )}
                      </div>
                    </div>

                    <ResultBox
                      title="Full Decision Trace"
                      result={paymentResult}
                    />
                  </div>
                ) : (
                  <ResultBox
                    title="Decision Result"
                    result={null}
                  />
                )}
              </div>
            </div>
          )}

          {/* =====================================================
              SUBSCRIPTION
          ===================================================== */}

          {tab === "subscription" && (
            <div>
              <SectionTitle
                title="Failed Subscription Recovery"
                description="Bounded retry workflow with customer-action routing, stopping rules, and payment verification."
              />

              <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="grid gap-4">
                    <Field
                      label="Subscription ID"
                      value={subscriptionId}
                      onChange={setSubscriptionId}
                    />

                    <Field
                      label="Customer ID"
                      value={subscriptionCustomerId}
                      onChange={setSubscriptionCustomerId}
                    />

                    <Field
                      label="Payment ID"
                      value={subscriptionPaymentId}
                      onChange={setSubscriptionPaymentId}
                    />

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field
                        label="Amount"
                        type="number"
                        value={subscriptionAmount}
                        onChange={setSubscriptionAmount}
                      />

                      <SelectField
                        label="Failure"
                        value={subscriptionFailure}
                        onChange={setSubscriptionFailure}
                        options={[
                          "bank_timeout",
                          "network_error",
                          "insufficient_funds",
                          "expired_card",
                          "mandate_failed",
                          "fraud",
                        ]}
                      />
                    </div>

                    <SelectField
                      label="Plan"
                      value={subscriptionPlan}
                      onChange={setSubscriptionPlan}
                      options={[
                        "monthly",
                        "quarterly",
                        "annual",
                      ]}
                    />

                    <div className="grid gap-3 sm:grid-cols-3">
                      <ActionButton
                        onClick={startSubscription}
                        disabled={subscriptionLoading}
                      >
                        Start
                      </ActionButton>

                      <ActionButton
                        secondary
                        onClick={executeSubscription}
                        disabled={
                          subscriptionLoading ||
                          !subscriptionState
                        }
                      >
                        Execute
                      </ActionButton>

                      <ActionButton
                        secondary
                        onClick={verifySubscription}
                        disabled={
                          subscriptionLoading ||
                          !subscriptionState
                        }
                      >
                        Verify
                      </ActionButton>
                    </div>

                    <Field
                      label="Verification Amount"
                      type="number"
                      value={subscriptionPaidAmount}
                      onChange={setSubscriptionPaidAmount}
                    />
                  </div>
                </div>

                <div>
                  <ResultBox
                    title="Subscription Workflow"
                    result={subscriptionResult}
                  />

                  {subscriptionState && (
                    <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-5">
                      <div className="grid gap-3 sm:grid-cols-3">
                        <div>
                          <div className="text-xs text-slate-500">
                            Status
                          </div>

                          <div className="mt-1 font-semibold">
                            {pretty(
                              subscriptionState.status
                            )}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Retry Count
                          </div>

                          <div className="mt-1 font-semibold">
                            {subscriptionState.retry_count}/
                            {subscriptionState.max_retries}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Recovered
                          </div>

                          <div className="mt-1 font-semibold text-emerald-400">
                            {money(
                              subscriptionState.recovered_amount
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* =====================================================
              MANDATE
          ===================================================== */}

          {tab === "mandate" && (
            <div>
              <SectionTitle
                title="Mandate Retry Sequencer"
                description="Bounded mandate retries with classification, escalation controls, and payment reconciliation."
              />

              <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="grid gap-4">
                    <Field
                      label="Mandate ID"
                      value={mandateId}
                      onChange={setMandateId}
                    />

                    <Field
                      label="Customer ID"
                      value={mandateCustomerId}
                      onChange={setMandateCustomerId}
                    />

                    <Field
                      label="Payment ID"
                      value={mandatePaymentId}
                      onChange={setMandatePaymentId}
                    />

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field
                        label="Amount"
                        type="number"
                        value={mandateAmount}
                        onChange={setMandateAmount}
                      />

                      <SelectField
                        label="Failure"
                        value={mandateFailure}
                        onChange={setMandateFailure}
                        options={[
                          "bank_timeout",
                          "network_error",
                          "technical_error",
                          "insufficient_funds",
                          "mandate_expired",
                          "fraud",
                        ]}
                      />
                    </div>

                    <div className="grid gap-3 sm:grid-cols-3">
                      <ActionButton
                        onClick={startMandate}
                        disabled={mandateLoading}
                      >
                        Start
                      </ActionButton>

                      <ActionButton
                        secondary
                        onClick={executeMandate}
                        disabled={
                          mandateLoading ||
                          !mandateState
                        }
                      >
                        Retry
                      </ActionButton>

                      <ActionButton
                        secondary
                        onClick={verifyMandate}
                        disabled={
                          mandateLoading ||
                          !mandateState
                        }
                      >
                        Verify
                      </ActionButton>
                    </div>

                    <Field
                      label="Verification Amount"
                      type="number"
                      value={mandatePaidAmount}
                      onChange={setMandatePaidAmount}
                    />
                  </div>
                </div>

                <div>
                  <ResultBox
                    title="Mandate Workflow"
                    result={mandateResult}
                  />

                  {mandateState && (
                    <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-5">
                      <div className="grid gap-3 sm:grid-cols-4">
                        <div>
                          <div className="text-xs text-slate-500">
                            Status
                          </div>

                          <div className="mt-1 font-semibold">
                            {pretty(
                              mandateState.status
                            )}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Retry
                          </div>

                          <div className="mt-1 font-semibold">
                            {mandateState.retry_count}/
                            {mandateState.max_retries}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Probability
                          </div>

                          <div className="mt-1 font-semibold">
                            {mandateState.recovery_probability ===
                            null
                              ? "—"
                              : pct(
                                  mandateState.recovery_probability
                                )}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Recovered
                          </div>

                          <div className="mt-1 font-semibold text-emerald-400">
                            {money(
                              mandateState.recovered_amount
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* =====================================================
              CHECKOUT
          ===================================================== */}

          {tab === "checkout" && (
            <div>
              <SectionTitle
                title="Checkout Drop-off Recovery"
                description="Recover abandoned checkouts with bounded follow-ups and payment verification."
              />

              <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="grid gap-4">
                    <Field
                      label="Checkout ID"
                      value={checkoutId}
                      onChange={setCheckoutId}
                    />

                    <Field
                      label="Customer ID"
                      value={checkoutCustomerId}
                      onChange={setCheckoutCustomerId}
                    />

                    <Field
                      label="Payment ID"
                      value={checkoutPaymentId}
                      onChange={setCheckoutPaymentId}
                    />

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field
                        label="Amount"
                        type="number"
                        value={checkoutAmount}
                        onChange={setCheckoutAmount}
                      />

                      <SelectField
                        label="Drop-off Reason"
                        value={dropoffReason}
                        onChange={setDropoffReason}
                        options={[
                          "payment_failed",
                          "bank_timeout",
                          "price_concern",
                          "changed_mind",
                          "checkout_error",
                          "session_expired",
                          "authentication_required",
                        ]}
                      />
                    </div>

                    <SelectField
                      label="Checkout Stage"
                      value={checkoutStage}
                      onChange={setCheckoutStage}
                      options={[
                        "cart",
                        "address",
                        "payment",
                        "confirmation",
                      ]}
                    />

                    <div className="grid gap-3 sm:grid-cols-3">
                      <ActionButton
                        onClick={startCheckout}
                        disabled={checkoutLoading}
                      >
                        Start
                      </ActionButton>

                      <ActionButton
                        secondary
                        onClick={executeCheckout}
                        disabled={
                          checkoutLoading ||
                          !checkoutState
                        }
                      >
                        Follow Up
                      </ActionButton>

                      <ActionButton
                        secondary
                        onClick={verifyCheckout}
                        disabled={
                          checkoutLoading ||
                          !checkoutState
                        }
                      >
                        Verify
                      </ActionButton>
                    </div>

                    <Field
                      label="Verification Amount"
                      type="number"
                      value={checkoutPaidAmount}
                      onChange={setCheckoutPaidAmount}
                    />
                  </div>
                </div>

                <div>
                  <ResultBox
                    title="Checkout Workflow"
                    result={checkoutResult}
                  />

                  {checkoutState && (
                    <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-5">
                      <div className="grid gap-3 sm:grid-cols-4">
                        <div>
                          <div className="text-xs text-slate-500">
                            Status
                          </div>

                          <div className="mt-1 font-semibold">
                            {pretty(
                              checkoutState.status
                            )}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Attempts
                          </div>

                          <div className="mt-1 font-semibold">
                            {checkoutState.attempt_count}/
                            {checkoutState.max_attempts}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Probability
                          </div>

                          <div className="mt-1 font-semibold">
                            {checkoutState.recovery_probability ===
                            null
                              ? "—"
                              : pct(
                                  checkoutState.recovery_probability
                                )}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Recovered
                          </div>

                          <div className="mt-1 font-semibold text-emerald-400">
                            {money(
                              checkoutState.recovered_amount
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* =====================================================
              RECEIVABLES
          ===================================================== */}

          {tab === "receivables" && (
            <div>
              <SectionTitle
                title="B2B Receivables Chaser"
                description="Bounded collections with escalating reminders, Promise-to-Pay tracking, and payment reconciliation."
              />

              <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                  <div className="grid gap-4">
                    <Field
                      label="Invoice ID"
                      value={invoiceId}
                      onChange={setInvoiceId}
                    />

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field
                        label="Customer ID"
                        value={receivableCustomerId}
                        onChange={setReceivableCustomerId}
                      />

                      <Field
                        label="Customer Name"
                        value={customerName}
                        onChange={setCustomerName}
                      />
                    </div>

                    <Field
                      label="Invoice Amount"
                      type="number"
                      value={invoiceAmount}
                      onChange={setInvoiceAmount}
                    />

                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field
                        label="Days Overdue"
                        type="number"
                        value={daysOverdue}
                        onChange={setDaysOverdue}
                      />

                      <Field
                        label="Due Date"
                        type="date"
                        value={dueDate}
                        onChange={setDueDate}
                      />
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <ActionButton
                        onClick={startReceivable}
                        disabled={receivableLoading}
                      >
                        Start Collection
                      </ActionButton>

                      <ActionButton
                        secondary
                        onClick={executeReceivable}
                        disabled={
                          receivableLoading ||
                          !receivableState
                        }
                      >
                        Escalate
                      </ActionButton>
                    </div>

                    <div className="border-t border-slate-800 pt-4">
                      <div className="mb-3 text-xs uppercase tracking-wider text-slate-500">
                        Promise-to-Pay
                      </div>

                      <div className="grid gap-4">
                        <Field
                          label="Promised Date"
                          type="date"
                          value={promiseDate}
                          onChange={setPromiseDate}
                        />

                        <Field
                          label="Customer Response"
                          value={promiseResponse}
                          onChange={setPromiseResponse}
                        />

                        <ActionButton
                          secondary
                          onClick={recordPromise}
                          disabled={
                            receivableLoading ||
                            !receivableState
                          }
                        >
                          Record Promise
                        </ActionButton>
                      </div>
                    </div>

                    <div className="border-t border-slate-800 pt-4">
                      <Field
                        label="Verification Amount"
                        type="number"
                        value={receivablePaidAmount}
                        onChange={setReceivablePaidAmount}
                      />

                      <div className="mt-3">
                        <ActionButton
                          secondary
                          onClick={verifyReceivable}
                          disabled={
                            receivableLoading ||
                            !receivableState
                          }
                        >
                          Verify Payment
                        </ActionButton>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <ResultBox
                    title="Receivables Workflow"
                    result={receivableResult}
                  />

                  {receivableState && (
                    <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-900 p-5">
                      <div className="grid gap-3 sm:grid-cols-4">
                        <div>
                          <div className="text-xs text-slate-500">
                            Status
                          </div>

                          <div className="mt-1 font-semibold">
                            {pretty(
                              receivableState.status
                            )}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Priority
                          </div>

                          <div className="mt-1 font-semibold">
                            {pretty(
                              receivableState.recovery_priority
                            )}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Escalations
                          </div>

                          <div className="mt-1 font-semibold">
                            {
                              receivableState.escalation_count
                            }/
                            {
                              receivableState.max_escalations
                            }
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-500">
                            Recovered
                          </div>

                          <div className="mt-1 font-semibold text-emerald-400">
                            {money(
                              receivableState.recovered_amount
                            )}
                          </div>
                        </div>
                      </div>

                      {receivableState.promise_to_pay && (
                        <div className="mt-5 rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-4">
                          <div className="text-xs uppercase tracking-wider text-cyan-300">
                            Promise-to-Pay
                          </div>

                          <div className="mt-2 text-sm">
                            Date:{" "}
                            {
                              receivableState
                                .promise_to_pay
                                .promised_date
                            }
                          </div>

                          <div className="mt-1 text-sm text-slate-400">
                            Status:{" "}
                            {
                              receivableState
                                .promise_to_pay
                                .status
                            }
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* =====================================================
              VOICE
          ===================================================== */}

          {tab === "voice" && (
            <VoiceRecovery />
          )}
        </section>
      </div>

      <footer className="border-t border-slate-800 px-6 py-6 text-center text-xs text-slate-600">
        RecoverOS · Next.js + FastAPI + SQLite ·
        Payment execution disabled by design
      </footer>
    </main>
  );
}