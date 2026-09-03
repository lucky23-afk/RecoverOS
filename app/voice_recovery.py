from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import io
import json
import re
import uuid

import pyttsx3
import speech_recognition as sr


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

P2P_FILE = DATA_DIR / "promise_to_pay.jsonl"
VOICE_AUDIT_FILE = DATA_DIR / "voice_recovery_audit.jsonl"


# =================================================================
# FILE HELPERS
# =================================================================

def _write_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "a",
        encoding="utf-8",
    ) as f:
        f.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


# =================================================================
# OUTCOME INTEGRATION
# =================================================================

try:
    from outcome_tracker import record_test_outcome

    OUTCOME_TRACKING_AVAILABLE = True

except ImportError:
    record_test_outcome = None
    OUTCOME_TRACKING_AVAILABLE = False


# =================================================================
# VOICE SESSION
# =================================================================

def start_voice_recovery(
    payment_id: str,
    amount: float,
    failure_reason: str,
) -> dict:

    return {
        "session_id": str(uuid.uuid4()),
        "payment_id": payment_id,
        "amount": float(amount),
        "failure_reason": failure_reason,
        "language": "HINGLISH",
        "status": "ACTIVE",
        "started_at": datetime.now().isoformat(),
    }


def generate_opening(session: dict) -> str:

    amount = session["amount"]

    return (
        f"Namaste! Aapka payment of ₹{amount:,.0f} "
        "complete nahi ho paya. "
        "Kya aap abhi payment retry karna chahenge, "
        "ya baad mein payment karna prefer karenge?"
    )


# =================================================================
# HINGLISH NORMALIZATION
# =================================================================

def normalize_hinglish(text: str) -> str:

    t = str(text).lower().strip()

    replacements = {
        "skta": "sakta",
        "skti": "sakti",
        "skte": "sakte",
        "kr": "kar",
        "krna": "karna",
        "krni": "karni",
        "krunga": "karunga",
        "krungi": "karungi",
        "krte": "karte",
        "krta": "karta",
        "krti": "karti",
        "krdunga": "kar dunga",
        "krdungi": "kar dungi",
        "krdo": "kar do",
        "krlo": "kar lo",
        "hu": "hoon",
        "h": "hai",
        "mai": "mein",
        "me": "mein",
        "karoonga": "karunga",
        "karoongi": "karungi",
        "pls": "please",
    }

    for old, new in replacements.items():
        t = re.sub(
            rf"\b{re.escape(old)}\b",
            new,
            t,
        )

    t = re.sub(
        r"[^\w\s]",
        " ",
        t,
    )

    t = re.sub(
        r"\s+",
        " ",
        t,
    )

    return t.strip()


# =================================================================
# INTENT DETECTION
# =================================================================

def detect_intent(text: str) -> str:
    """
    Returns one of:

    PAY_NOW
    PROMISE_TO_PAY
    DECLINE
    UNCLEAR
    """

    t = normalize_hinglish(text)

    # -------------------------------------------------------------
    # DECLINE
    # -------------------------------------------------------------

    decline_patterns = [
        "nahi karna",
        "nahi karna hai",
        "payment nahi karna",
        "payment nahi karni",
        "pay nahi karna",
        "pay nahi karni",
        "main nahi karunga",
        "main nahi karungi",
        "main payment nahi karunga",
        "main payment nahi karungi",
        "nahi chahiye",
        "payment nahi chahiye",
        "cancel kar do",
        "cancel karo",
        "cancel karna hai",
        "isko cancel",
        "mujhe nahi karna",
        "mujhe payment nahi karni",
        "dont want to pay",
        "do not want to pay",
        "not interested",
        "stop payment",
        "payment band karo",
        "payment mat karo",
    ]

    if any(
        pattern in t
        for pattern in decline_patterns
    ):
        return "DECLINE"

    # -------------------------------------------------------------
    # PROMISE TO PAY
    # -------------------------------------------------------------

    promise_patterns = [
        "kal payment karunga",
        "kal payment karungi",
        "kal pay karunga",
        "kal pay karungi",
        "kal karunga",
        "kal karungi",
        "kal kar dunga",
        "kal kar dungi",
        "tomorrow pay",
        "tomorrow payment",
        "tomorrow karunga",
        "tomorrow karungi",
        "later pay",
        "later payment",
        "baad mein pay",
        "baad mein payment",
        "baad me pay",
        "baad me payment",
        "shaam ko pay",
        "shaam ko payment",
        "evening mein pay",
        "evening me pay",
        "aaj possible nahi",
        "aaj payment possible nahi",
        "aaj pay possible nahi",
        "abhi possible nahi",
        "abhi payment possible nahi",
        "abhi pay possible nahi",
        "abhi nahi kal",
        "aaj nahi kal",
        "monday ko pay",
        "monday ko payment",
        "tuesday ko pay",
        "tuesday ko payment",
        "wednesday ko pay",
        "wednesday ko payment",
        "thursday ko pay",
        "thursday ko payment",
        "friday ko pay",
        "friday ko payment",
        "saturday ko pay",
        "saturday ko payment",
        "sunday ko pay",
        "sunday ko payment",
        "monday pay",
        "tuesday pay",
        "wednesday pay",
        "thursday pay",
        "friday pay",
        "saturday pay",
        "sunday pay",
        "next week pay",
        "next week payment",
        "weekend pe pay",
        "weekend mein pay",
        "weekend me pay",
        "2 din mein pay",
        "2 days mein pay",
        "do din mein pay",
        "few days mein pay",
        "kuch din mein pay",
        "salary aate hi pay",
        "salary aayegi tab pay",
        "salary ke baad pay",
        "funds aate hi pay",
        "paise aate hi pay",
        "paise aane ke baad pay",
        "thoda time do",
        "time do pay karunga",
        "thoda time chahiye",
        "abhi paise nahi hain",
        "abhi funds nahi hain",
        "paise nahi hain abhi",
        "funds nahi hain abhi",
    ]

    if any(
        pattern in t
        for pattern in promise_patterns
    ):
        return "PROMISE_TO_PAY"

    # -------------------------------------------------------------
    # PAY NOW
    # -------------------------------------------------------------

    pay_now_patterns = [
        "aaj payment possible hai",
        "aaj pay possible hai",
        "aaj payment kar",
        "aaj pay kar",
        "aaj hi payment",
        "aaj hi pay",
        "aaj kar sakta",
        "aaj kar sakti",
        "aaj karunga",
        "aaj karungi",
        "abhi payment possible hai",
        "abhi pay possible hai",
        "abhi payment kar",
        "abhi pay kar",
        "abhi payment",
        "abhi pay",
        "abhi kar deta",
        "abhi kar deti",
        "abhi kar dunga",
        "abhi kar dungi",
        "abhi karta hoon",
        "abhi karti hoon",
        "abhi try karta",
        "abhi try kar",
        "abhi retry",
        "payment abhi ho jayega",
        "payment ho jayega",
        "payment kar sakta hoon",
        "payment kar sakti hoon",
        "payment kar sakta",
        "payment kar sakti",
        "pay kar sakta hoon",
        "pay kar sakti hoon",
        "pay kar sakta",
        "pay kar sakti",
        "ready to pay",
        "payment ke liye ready",
        "pay karne ke liye ready",
        "haan payment",
        "haan pay",
        "haan abhi",
        "haan aaj",
        "haan kar sakta",
        "haan kar sakti",
        "yes payment",
        "yes pay",
        "yes now",
        "lets do it now",
        "let us do it now",
        "right now payment",
        "right now pay",
        "complete payment now",
        "make payment now",
        "payment kar lenge",
        "payment kar leta",
        "payment kar leti",
        "pay kar leta",
        "pay kar leti",
    ]

    if any(
        pattern in t
        for pattern in pay_now_patterns
    ):
        return "PAY_NOW"

    # -------------------------------------------------------------
    # DATE + PAYMENT COMBINATION
    # -------------------------------------------------------------

    date_words = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "tomorrow",
        "kal",
    ]

    payment_words = [
        "pay",
        "payment",
        "karunga",
        "karungi",
        "karta",
        "karti",
    ]

    has_date = any(
        word in t
        for word in date_words
    )

    has_payment = any(
        word in t
        for word in payment_words
    )

    if has_date and has_payment:
        return "PROMISE_TO_PAY"

    # -------------------------------------------------------------
    # SIMPLE POSITIVE RESPONSE
    # -------------------------------------------------------------

    positive_patterns = [
        "haan",
        "yes",
        "sure",
        "okay",
        "ok",
        "theek hai",
        "thik hai",
        "done",
    ]

    if any(
        pattern == t
        or t.startswith(pattern + " ")
        for pattern in positive_patterns
    ):
        return "PAY_NOW"

    payment_context = [
        "payment",
        "pay",
        "retry",
        "transaction",
        "complete",
    ]

    if (
        any(
            pattern in t
            for pattern in positive_patterns
        )
        and any(
            word in t
            for word in payment_context
        )
    ):
        return "PAY_NOW"

    return "UNCLEAR"


# =================================================================
# DATE EXTRACTION
# =================================================================

def extract_promised_date(
    text: str,
) -> str | None:

    t = normalize_hinglish(text)

    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    for (
        day_name,
        target_weekday,
    ) in weekday_map.items():

        if re.search(
            rf"\b{day_name}\b",
            t,
        ):

            today = date.today()

            delta = (
                target_weekday
                - today.weekday()
            ) % 7

            if delta == 0:
                delta = 7

            return str(
                today
                + timedelta(days=delta)
            )

    if (
        "tomorrow" in t
        or "kal" in t
    ):
        return str(
            date.today()
            + timedelta(days=1)
        )

    return None


# =================================================================
# PROMISE-TO-PAY
# =================================================================

def create_promise_to_pay(
    session: dict,
    customer_text: str,
) -> dict:

    promised_date = (
        extract_promised_date(
            customer_text
        )
    )

    record = {
        "promise_id": str(uuid.uuid4()),
        "session_id": session["session_id"],
        "payment_id": session["payment_id"],
        "promised_amount": session["amount"],
        "promised_date": promised_date,
        "customer_response": customer_text,
        "language": "HINGLISH",
        "status": "PENDING",
        "created_at": datetime.now().isoformat(),
        "payment_verified": False,
        "recovery_amount": 0.0,
    }

    _write_jsonl(
        P2P_FILE,
        record,
    )

    _write_jsonl(
        VOICE_AUDIT_FILE,
        {
            "event": "PROMISE_TO_PAY_CREATED",
            "payment_id": session["payment_id"],
            "promise_id": record["promise_id"],
            "amount": session["amount"],
            "status": "PENDING",
            "language": "HINGLISH",
            "timestamp": datetime.now().isoformat(),
        },
    )

    return record


# =================================================================
# PAYMENT VERIFICATION
# =================================================================

def verify_payment(
    promise_id: str,
    payment_amount: float,
) -> dict:

    if not P2P_FILE.exists():
        return {
            "verified": False,
            "reason": (
                "No Promise-to-Pay records found."
            ),
        }

    records = []
    target = None

    with open(
        P2P_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            records.append(record)

            if (
                record.get("promise_id")
                == promise_id
            ):
                target = record

    if target is None:
        return {
            "verified": False,
            "reason": (
                "Promise-to-Pay record not found."
            ),
        }

    # Prevent duplicate verification.
    if target.get("payment_verified") is True:
        return {
            "verified": False,
            "reason": (
                "This Promise-to-Pay has "
                "already been verified."
            ),
            "status": target.get(
                "status",
                "VERIFIED",
            ),
            "payment_id": target.get(
                "payment_id"
            ),
            "promise_id": promise_id,
            "recovery_amount": float(
                target.get(
                    "recovery_amount",
                    0.0,
                )
            ),
        }

    payment_amount = float(
        payment_amount
    )

    promised_amount = float(
        target.get(
            "promised_amount",
            0,
        )
    )

    if payment_amount < promised_amount:
        return {
            "verified": False,
            "reason": (
                "Payment amount is below "
                "the promised amount."
            ),
        }

    # -------------------------------------------------------------
    # UPDATE P2P RECORD
    # -------------------------------------------------------------

    target["status"] = "VERIFIED"
    target["payment_verified"] = True
    target["recovery_amount"] = payment_amount
    target["verified_at"] = (
        datetime.now().isoformat()
    )

    temp_file = P2P_FILE.with_suffix(".tmp")

    with open(
        temp_file,
        "w",
        encoding="utf-8",
    ) as f:

        for record in records:

            if (
                record.get("promise_id")
                == promise_id
            ):
                record = target

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    temp_file.replace(
        P2P_FILE
    )

    # -------------------------------------------------------------
    # VOICE AUDIT
    # -------------------------------------------------------------

    _write_jsonl(
        VOICE_AUDIT_FILE,
        {
            "event": "PAYMENT_VERIFIED",
            "payment_id": target["payment_id"],
            "promise_id": promise_id,
            "recovery_amount": payment_amount,
            "timestamp": datetime.now().isoformat(),
        },
    )

    # -------------------------------------------------------------
    # TEST OUTCOME
    #
    # IMPORTANT:
    # This is a simulated/demo voice flow.
    # It MUST NOT enter outcomes.jsonl.
    # -------------------------------------------------------------

    test_outcome = None

    if OUTCOME_TRACKING_AVAILABLE:

        try:
            test_outcome = record_test_outcome(
                payment_id=target["payment_id"],
                amount=target["promised_amount"],
                failure_reason=target.get(
                    "failure_reason",
                    "voice_promise_to_pay",
                ),
                recommended_action="track_promise",
                final_action="track_promise",
                recovery_probability=0.0,
                expected_revenue=0.0,
                recovered=True,
                recovery_amount=payment_amount,
            )

        except Exception as exc:

            _write_jsonl(
                VOICE_AUDIT_FILE,
                {
                    "event": "TEST_OUTCOME_WRITE_FAILED",
                    "payment_id": target["payment_id"],
                    "promise_id": promise_id,
                    "error": str(exc),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    else:

        _write_jsonl(
            VOICE_AUDIT_FILE,
            {
                "event": "TEST_OUTCOME_TRACKING_UNAVAILABLE",
                "payment_id": target["payment_id"],
                "promise_id": promise_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    return {
        "verified": True,
        "payment_id": target["payment_id"],
        "promise_id": promise_id,
        "recovery_amount": payment_amount,
        "status": "VERIFIED",
        "test_outcome_recorded": (
            test_outcome is not None
        ),
    }


# =================================================================
# CONVERSATION HANDLER
# =================================================================

def process_voice_message(
    session: dict,
    customer_text: str,
) -> dict:
    """
    Process one customer Hinglish message.

    Returns:
        intent
        next_action
        response
        status
    """

    intent = detect_intent(
        customer_text
    )

    # -------------------------------------------------------------
    # PAY NOW
    # -------------------------------------------------------------

    if intent == "PAY_NOW":

        response = (
            "Great! Aap abhi payment "
            "kar sakte hain. "
            "Main aapko payment link "
            "provide karta hoon."
        )

        result = {
            "session_id": session["session_id"],
            "payment_id": session["payment_id"],
            "intent": "PAY_NOW",
            "next_action": "PAYMENT_LINK",
            "response": response,
            "status": "AWAITING_PAYMENT",
            "customer_text": customer_text,
            "timestamp": datetime.now().isoformat(),
        }

        _write_jsonl(
            VOICE_AUDIT_FILE,
            {
                "event": "PAY_NOW_INTENT",
                "session_id": session["session_id"],
                "payment_id": session["payment_id"],
                "customer_text": customer_text,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return result

    # -------------------------------------------------------------
    # PROMISE TO PAY
    # -------------------------------------------------------------

    if intent == "PROMISE_TO_PAY":

        promised_date = (
            extract_promised_date(
                customer_text
            )
        )

        promise = (
            create_promise_to_pay(
                session=session,
                customer_text=customer_text,
            )
        )

        if promised_date:

            formatted_date = (
                date.fromisoformat(
                    promised_date
                ).strftime("%d %b %Y")
            )

            response = (
              f"Okay, noted. Aap "
              f"{formatted_date} ko payment karenge. "
              "Main aapka Promise-to-Pay record "
              "kar raha hoon."
           )

        else:

            response = (
                "Okay, main aapka "
                "Promise-to-Pay note kar raha hoon. "
                "Please payment date confirm "
                "kar dijiye."
            )

        return {
            "session_id": session["session_id"],
            "payment_id": session["payment_id"],
            "intent": "PROMISE_TO_PAY",
            "next_action": "TRACK_PROMISE",
            "response": response,
            "status": "PROMISE_RECORDED",
            "promise": promise,
            "customer_text": customer_text,
            "timestamp": datetime.now().isoformat(),
        }

    # -------------------------------------------------------------
    # DECLINE
    # -------------------------------------------------------------

    if intent == "DECLINE":

        response = (
            "Theek hai. Hum payment recovery "
            "ke liye aur attempt nahi karenge."
        )

        _write_jsonl(
            VOICE_AUDIT_FILE,
            {
                "event": "RECOVERY_DECLINED",
                "session_id": session["session_id"],
                "payment_id": session["payment_id"],
                "customer_text": customer_text,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return {
            "session_id": session["session_id"],
            "payment_id": session["payment_id"],
            "intent": "DECLINE",
            "next_action": "STOP",
            "response": response,
            "status": "DECLINED",
            "customer_text": customer_text,
            "timestamp": datetime.now().isoformat(),
        }

    # -------------------------------------------------------------
    # UNCLEAR
    # -------------------------------------------------------------

    response = (
        "Koi problem nahi. Aap abhi "
        "payment karna chahte hain "
        "ya baad mein payment karenge?"
    )

    _write_jsonl(
        VOICE_AUDIT_FILE,
        {
            "event": "INTENT_UNCLEAR",
            "session_id": session["session_id"],
            "payment_id": session["payment_id"],
            "customer_text": customer_text,
            "timestamp": datetime.now().isoformat(),
        },
    )

    return {
        "session_id": session["session_id"],
        "payment_id": session["payment_id"],
        "intent": "UNCLEAR",
        "next_action": "CLARIFY",
        "response": response,
        "status": "NEEDS_CLARIFICATION",
        "customer_text": customer_text,
        "timestamp": datetime.now().isoformat(),
    }

# =================================================================
# SPEECH-TO-TEXT
# =================================================================

def transcribe_hinglish_audio(audio_file) -> dict:
    """
    Convert browser-recorded audio into text.

    Uses the SpeechRecognition Google recognizer with
    an India English locale, then passes the result
    through the existing Hinglish pipeline.
    """

    if audio_file is None:
        return {
            "success": False,
            "text": "",
            "reason": "No audio recording provided.",
        }

    try:
        recognizer = sr.Recognizer()

        audio_bytes = audio_file.getvalue()

        with sr.AudioFile(
            io.BytesIO(audio_bytes)
        ) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(
            audio_data,
            language="en-IN",
        )

        normalized = normalize_hinglish(
            text
        )

        return {
            "success": True,
            "text": text,
            "normalized_text": normalized,
            "reason": "",
        }

    except sr.UnknownValueError:
        return {
            "success": False,
            "text": "",
            "reason": (
                "Speech could not be understood."
            ),
        }

    except sr.RequestError as exc:
        return {
            "success": False,
            "text": "",
            "reason": (
                f"Speech recognition service error: {exc}"
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "text": "",
            "reason": str(exc),
        }

# =================================================================
# TEXT-TO-SPEECH
# =================================================================

def generate_voice_response(text: str) -> str | None:
    """
    Convert a RecoverOS response into a WAV audio file
    using the local Windows TTS engine.
    """

    if not text:
        return None

    try:
        output_file = (
            DATA_DIR / "recoveros_voice_response.wav"
        )

        engine = pyttsx3.init()

        engine.setProperty(
            "rate",
            155,
        )

        engine.setProperty(
            "volume",
            1.0,
        )

        engine.save_to_file(
            text,
            str(output_file),
        )

        engine.runAndWait()
        engine.stop()

        if output_file.exists():
            return str(output_file)

        return None

    except Exception as exc:

        _write_jsonl(
            VOICE_AUDIT_FILE,
            {
                "event": "TTS_ERROR",
                "error": str(exc),
                "timestamp": datetime.now().isoformat(),
            },
        )

        return None

# =================================================================
# MULTI-TURN CONVERSATION HANDLER
# =================================================================

def process_conversation_turn(
    session: dict,
    customer_text: str,
) -> dict:
    """
    Process a customer message while preserving
    conversation state.

    The agent can ask for a payment date when the
    customer indicates they cannot pay immediately.
    """

    history = session.setdefault(
        "conversation_history",
        [],
    )

    history.append(
        {
            "speaker": "CUSTOMER",
            "text": customer_text,
            "timestamp": datetime.now().isoformat(),
        }
    )

    normalized = normalize_hinglish(
        customer_text
    )

    # -------------------------------------------------------------
    # Check for an explicit Promise-to-Pay date
    # -------------------------------------------------------------

    promised_date = extract_promised_date(
        customer_text
    )

    if promised_date:
        intent = detect_intent(
            customer_text
        )

        if intent == "PROMISE_TO_PAY":
            promise = create_promise_to_pay(
                session,
                customer_text,
            )

            response = (
                "Okay, noted. Aap "
                f"{promised_date} ko payment karenge. "
                "Main aapka Promise-to-Pay record kar raha hoon."
            )

            history.append(
                {
                    "speaker": "RECOVEROS",
                    "text": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {
                "intent": "PROMISE_TO_PAY",
                "next_action": "TRACK_PROMISE",
                "status": "PROMISE_RECORDED",
                "response": response,
                "promise": promise,
                "conversation_history": history,
            }

    # -------------------------------------------------------------
    # Customer says they cannot pay now, but gives no date
    # -------------------------------------------------------------

    cannot_pay_patterns = [
        "abhi nahi",
        "abhi possible nahi",
        "abhi payment possible nahi",
        "aaj nahi",
        "aaj possible nahi",
        "aaj payment possible nahi",
        "paise nahi hain",
        "funds nahi hain",
        "abhi funds nahi hain",
        "paise nahi hain abhi",
        "later",
        "baad mein",
        "baad me",
        "thoda time",
        "time chahiye",
    ]

    if any(
        pattern in normalized
        for pattern in cannot_pay_patterns
    ):
        response = (
            "Theek hai. Aap kis din payment "
            "kar paayenge?"
        )

        history.append(
            {
                "speaker": "RECOVEROS",
                "text": response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        session["status"] = (
            "WAITING_FOR_PROMISE_DATE"
        )

        return {
            "intent": "PROMISE_DATE_REQUIRED",
            "next_action": "ASK_PAYMENT_DATE",
            "status": "WAITING_FOR_PROMISE_DATE",
            "response": response,
            "conversation_history": history,
        }

    # -------------------------------------------------------------
    # If we already asked for a date, interpret a date response
    # -------------------------------------------------------------

    if (
        session.get("status")
        == "WAITING_FOR_PROMISE_DATE"
    ):
        if promised_date:
            promise = create_promise_to_pay(
                session,
                customer_text,
            )

            response = (
                "Perfect, noted. Aap "
                f"{promised_date} ko payment karenge. "
                "Aapka Promise-to-Pay record ho gaya hai."
            )

            history.append(
                {
                    "speaker": "RECOVEROS",
                    "text": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            session["status"] = (
                "PROMISE_RECORDED"
            )

            return {
                "intent": "PROMISE_TO_PAY",
                "next_action": "TRACK_PROMISE",
                "status": "PROMISE_RECORDED",
                "response": response,
                "promise": promise,
                "conversation_history": history,
            }

    # -------------------------------------------------------------
    # Fall back to normal single-turn detection
    # -------------------------------------------------------------

    result = process_voice_message(
        session,
        customer_text,
    )

    history.append(
        {
            "speaker": "RECOVEROS",
            "text": result["response"],
            "timestamp": datetime.now().isoformat(),
        }
    )

    return {
        **result,
        "conversation_history": history,
    }

# =================================================================
# LOCAL TEST
# =================================================================

if __name__ == "__main__":

    session = start_voice_recovery(
        payment_id="VOICE001",
        amount=2499,
        failure_reason="bank_timeout",
    )

    print("=" * 70)
    print("RecoverOS - HINGLISH RECOVERY DEMO")
    print("=" * 70)

    print()
    print("BOT:")
    print(
        generate_opening(session)
    )

    customer_text = (
        "Aaj possible nahi hai, "
        "Monday ko karunga"
    )

    print()
    print("CUSTOMER:")
    print(customer_text)

    result = process_voice_message(
        session,
        customer_text,
    )

    print()
    print("DETECTED INTENT:")
    print(result["intent"])

    print()
    print("NEXT ACTION:")
    print(result["next_action"])

    print()
    print("BOT:")
    print(result["response"])

    if result.get("promise"):

        promise = result["promise"]

        print()
        print("PROMISE STATUS:")
        print(promise["status"])

        print(
            "PROMISED DATE:"
        )
        print(
            promise["promised_date"]
        )

        verification = verify_payment(
            promise["promise_id"],
            2499,
        )

        print()
        print("PAYMENT VERIFICATION:")
        print(verification)

    print()
    print("=" * 70)
    