"use client";

import { useRef, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

type Session = Record<string, any>;

type VoiceResult = {
  intent?: string;
  next_action?: string;
  status?: string;
  response?: string;
  promise?: Record<string, any>;
  conversation_history?: Array<{
    speaker: string;
    text: string;
    timestamp?: string;
  }>;
};

export default function VoiceRecovery() {
  const [paymentId, setPaymentId] =
    useState("VOICE_UI_001");

  const [amount, setAmount] =
    useState("2499");

  const [failureReason, setFailureReason] =
    useState("bank_timeout");

  const [session, setSession] =
    useState<Session | null>(null);

  const [result, setResult] =
    useState<VoiceResult | null>(null);

  const [message, setMessage] =
    useState("");

  const [promiseId, setPromiseId] =
    useState("");

  const [verificationAmount, setVerificationAmount] =
    useState("2499");

  const [verification, setVerification] =
    useState<Record<string, any> | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [listening, setListening] =
    useState(false);

  const [error, setError] =
    useState("");

  const recognitionRef = useRef<any>(null);
  const manualStopRef = useRef(false);

  // ================================================================
  // START SESSION
  // ================================================================

  const startSession = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    setVerification(null);
    setPromiseId("");

    try {
      const response = await fetch(
        `${API_BASE}/voice/start`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            payment_id: paymentId,
            amount: Number(amount),
            failure_reason: failureReason,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to start voice session."
        );
      }

      setSession(data.session);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Voice session failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // ================================================================
  // SEND MESSAGE
  // ================================================================

  const sendMessage = async (
    textOverride?: string
  ) => {
    const text = (
      textOverride ?? message
    ).trim();

    if (!session || !text) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE}/voice/turn`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session,
            message: text,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Voice turn failed."
        );
      }

      const nextResult =
        data.result || {};

      setResult(nextResult);

      if (
        nextResult.promise?.promise_id
      ) {
        setPromiseId(
          nextResult.promise.promise_id
        );
      }

      if (
        nextResult.conversation_history
      ) {
        setSession({
          ...session,
          conversation_history:
            nextResult.conversation_history,
          status:
            nextResult.status ||
            session.status,
        });
      } else {
        setSession({
          ...session,
          status:
            nextResult.status ||
            session.status,
        });
      }

      setMessage("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to process message."
      );
    } finally {
      setLoading(false);
    }
  };

  // ================================================================
  // START MICROPHONE
  // ================================================================

  const startListening = () => {
    setError("");

    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError(
        "Brave does not expose speech recognition in this session. Please enable microphone access and allow speech recognition for localhost."
      );
      return;
    }

    // Prevent duplicate recognizers.
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore already-stopped recognizer.
      }
    }

    manualStopRef.current = false;

    const recognition =
      new SpeechRecognition();

    recognition.lang = "en-IN";

    // Keep recognition alive instead of ending
    // after the first short pause.
    recognition.continuous = false;

    // Show partial speech while speaking.
    recognition.interimResults = false;
    

    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setListening(true);
      setError("");
    };

    recognition.onresult = (
      event: any
    ) => {
      let finalText = "";
      let interimText = "";

      for (
        let i = event.resultIndex;
        i < event.results.length;
        i++
      ) {
        const transcript =
          event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalText += transcript + " ";
        } else {
          interimText += transcript;
        }
      }

      const combinedText =
        `${finalText}${interimText}`.trim();

      if (combinedText) {
        setMessage(combinedText);
      }
    };

    recognition.onerror = (
      event: any
    ) => {
      const errorCode =
        event?.error || "unknown";

      // "no-speech" can happen naturally.
      // Do not treat it as a fatal error.
      if (
        errorCode !== "no-speech" &&
        errorCode !== "aborted"
      ) {
        setError(
          `Microphone error: ${errorCode}`
        );
      }

      if (errorCode !== "no-speech") {
        setListening(false);
      }
    };

    recognition.onend = () => {
      // Brave may occasionally end recognition
      // automatically. Restart while the user still
      // considers the recording active.
      setListening(false);
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (err) {
      setListening(false);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to start microphone."
      );
    }
  };

  // ================================================================
  // STOP MICROPHONE
  // ================================================================

  const stopListening = () => {
    manualStopRef.current = true;

    try {
      recognitionRef.current?.stop();
    } catch {
      // Ignore already stopped recognizer.
    }

    setListening(false);
  };

  // ================================================================
  // VERIFY PAYMENT
  // ================================================================

  const verifyPayment = async () => {
    if (!promiseId) {
      setError(
        "No Promise-to-Pay has been created yet."
      );
      return;
    }

    setLoading(true);
    setError("");
    setVerification(null);

    try {
      const response = await fetch(
        `${API_BASE}/voice/verify`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            promise_id: promiseId,
            payment_amount:
              Number(verificationAmount),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Payment verification failed."
        );
      }

      setVerification(data.result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Verification failed."
      );
    } finally {
      setLoading(false);
    }
  };

  const history =
    session?.conversation_history || [];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">
          Hinglish Voice Recovery
        </h2>

        <p className="mt-1 text-sm leading-6 text-slate-400">
          Conversational recovery with Hinglish intent
          detection and Promise-to-Pay tracking.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        {/* LEFT */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="font-semibold">
              Start Recovery Session
            </h3>

            <div className="mt-5 grid gap-4">
              <div>
                <label className="mb-2 block text-sm text-slate-300">
                  Payment ID
                </label>

                <input
                  value={paymentId}
                  onChange={(e) =>
                    setPaymentId(e.target.value)
                  }
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">
                  Amount
                </label>

                <input
                  type="number"
                  min="1"
                  value={amount}
                  onChange={(e) =>
                    setAmount(e.target.value)
                  }
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">
                  Failure Reason
                </label>

                <select
                  value={failureReason}
                  onChange={(e) =>
                    setFailureReason(e.target.value)
                  }
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400"
                >
                  <option value="bank_timeout">
                    bank_timeout
                  </option>

                  <option value="network_error">
                    network_error
                  </option>

                  <option value="insufficient_funds">
                    insufficient_funds
                  </option>

                  <option value="expired_card">
                    expired_card
                  </option>
                </select>
              </div>

              <button
                type="button"
                onClick={startSession}
                disabled={loading}
                className="rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-300 disabled:opacity-40"
              >
                {loading
                  ? "Starting..."
                  : "Start Voice Recovery"}
              </button>
            </div>
          </div>

          {session && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">
                  Session
                </h3>

                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400">
                  {session.status}
                </span>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-slate-950 p-4">
                  <div className="text-xs text-slate-500">
                    Payment
                  </div>

                  <div className="mt-1 text-sm font-medium">
                    {session.payment_id}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-950 p-4">
                  <div className="text-xs text-slate-500">
                    Amount
                  </div>

                  <div className="mt-1 text-sm font-medium">
                    ₹
                    {Number(
                      session.amount || 0
                    ).toLocaleString("en-IN")}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900">
          <div className="border-b border-slate-800 px-6 py-5">
            <h3 className="font-semibold">
              Conversation
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Speak naturally in Hinglish or type a
              message.
            </p>
          </div>

          <div className="flex min-h-[620px] flex-col">
            <div className="flex-1 space-y-4 overflow-auto p-6">
              {!session && (
                <div className="flex min-h-[400px] items-center justify-center text-center">
                  <div>
                    <div className="text-3xl">
                      🎙️
                    </div>

                    <div className="mt-4 font-medium">
                      Start a recovery session
                    </div>

                    <div className="mt-2 text-sm text-slate-500">
                      RecoverOS will guide the customer
                      toward payment or a Promise-to-Pay.
                    </div>
                  </div>
                </div>
              )}

              {session && (
                <div className="rounded-2xl bg-cyan-400/10 p-4">
                  <div className="text-xs uppercase tracking-wider text-cyan-300">
                    RecoverOS
                  </div>

                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    Namaste! Aapka payment of ₹
                    {Number(
                      session.amount || 0
                    ).toLocaleString("en-IN")}{" "}
                    complete nahi ho paya. Kya aap abhi
                    payment retry karna chahenge, ya baad
                    mein payment karna prefer karenge?
                  </p>
                </div>
              )}

              {history.map(
                (
                  item: any,
                  index: number
                ) => (
                  <div
                    key={`${item.timestamp}-${index}`}
                    className={
                      item.speaker ===
                      "CUSTOMER"
                        ? "ml-8 rounded-2xl bg-slate-800 p-4"
                        : "mr-8 rounded-2xl border border-slate-800 bg-slate-950 p-4"
                    }
                  >
                    <div className="text-xs uppercase tracking-wider text-slate-500">
                      {item.speaker}
                    </div>

                    <div className="mt-2 text-sm leading-6 text-slate-300">
                      {item.text}
                    </div>
                  </div>
                )
              )}

              {message && listening && (
                <div className="ml-8 rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-4">
                  <div className="text-xs uppercase tracking-wider text-cyan-300">
                    Listening
                  </div>

                  <div className="mt-2 text-sm text-slate-300">
                    {message}
                  </div>
                </div>
              )}
            </div>

            {result && (
              <div className="border-t border-slate-800 p-5">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl bg-slate-950 p-3">
                    <div className="text-xs text-slate-500">
                      Intent
                    </div>

                    <div className="mt-1 text-sm font-semibold capitalize">
                      {result.intent?.replaceAll(
                        "_",
                        " "
                      ) || "—"}
                    </div>
                  </div>

                  <div className="rounded-xl bg-slate-950 p-3">
                    <div className="text-xs text-slate-500">
                      Next Action
                    </div>

                    <div className="mt-1 text-sm font-semibold capitalize">
                      {result.next_action?.replaceAll(
                        "_",
                        " "
                      ) || "—"}
                    </div>
                  </div>

                  <div className="rounded-xl bg-slate-950 p-3">
                    <div className="text-xs text-slate-500">
                      Status
                    </div>

                    <div className="mt-1 text-sm font-semibold">
                      {result.status || "—"}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {result?.promise && (
              <div className="mx-5 mb-5 rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-4">
                <div className="text-xs uppercase tracking-wider text-cyan-300">
                  Promise-to-Pay Recorded
                </div>

                <div className="mt-2 text-sm">
                  Promise ID:{" "}
                  {result.promise.promise_id}
                </div>

                <div className="mt-1 text-sm text-slate-400">
                  Promised date:{" "}
                  {result.promise.promised_date ||
                    "Date pending"}
                </div>

                <div className="mt-1 text-sm text-slate-400">
                  Amount: ₹
                  {Number(
                    result.promise.promised_amount ||
                      0
                  ).toLocaleString("en-IN")}
                </div>
              </div>
            )}

            {session && (
              <div className="border-t border-slate-800 p-5">
                <div className="flex gap-2">
                  <input
                    value={message}
                    onChange={(e) =>
                      setMessage(e.target.value)
                    }
                    onKeyDown={(e) => {
                      if (
                        e.key === "Enter" &&
                        !e.shiftKey
                      ) {
                        e.preventDefault();
                        sendMessage();
                      }
                    }}
                    placeholder="Type: Abhi nahi ho payega..."
                    className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none focus:border-cyan-400"
                  />

                  <button
                    type="button"
                    onClick={
                      listening
                        ? stopListening
                        : startListening
                    }
                    className={`rounded-xl px-4 py-3 text-sm font-semibold ${
                      listening
                        ? "bg-red-400 text-slate-950"
                        : "border border-slate-700 bg-slate-950"
                    }`}
                  >
                    {listening
                      ? "Stop"
                      : "🎙️"}
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      sendMessage()
                    }
                    disabled={
                      loading ||
                      !message.trim()
                    }
                    className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-40"
                  >
                    Send
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {promiseId && (
        <div className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h3 className="font-semibold">
            Promise-to-Pay Verification
          </h3>

          <p className="mt-1 text-sm text-slate-500">
            Verify the payment once the promised amount
            is received.
          </p>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <input
              type="number"
              min="1"
              value={verificationAmount}
              onChange={(e) =>
                setVerificationAmount(
                  e.target.value
                )
              }
              className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400"
            />

            <button
              type="button"
              onClick={verifyPayment}
              disabled={loading}
              className="rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 hover:bg-emerald-300 disabled:opacity-40"
            >
              Verify Payment
            </button>
          </div>

          {verification && (
            <div className="mt-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
              <div className="font-semibold text-emerald-400">
                {verification.verified
                  ? "Payment Verified"
                  : "Verification Failed"}
              </div>

              <pre className="mt-3 overflow-auto whitespace-pre-wrap text-xs text-slate-400">
                {JSON.stringify(
                  verification,
                  null,
                  2
                )}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}