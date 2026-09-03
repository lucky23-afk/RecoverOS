from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable


# ================================================================
# PATHS
# ================================================================

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent
DATA_DIR = BASE_DIR / "data"

DATABASE_FILE = DATA_DIR / "recoveros.db"


# ================================================================
# DATABASE CONNECTION
# ================================================================

def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_FILE,
        timeout=30,
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ================================================================
# SCHEMA
# ================================================================

SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    customer_id TEXT,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    failure_reason TEXT,
    status TEXT NOT NULL,
    recovered_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    customer_id TEXT,
    payment_id TEXT,
    amount REAL NOT NULL,
    plan TEXT,
    failure_reason TEXT,
    status TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    next_retry_at TEXT,
    recovery_action TEXT,
    recovery_probability REAL,
    payment_verified INTEGER NOT NULL DEFAULT 0,
    recovered_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    FOREIGN KEY (payment_id)
        REFERENCES payments(payment_id)
);

CREATE TABLE IF NOT EXISTS mandates (
    mandate_id TEXT PRIMARY KEY,
    customer_id TEXT,
    payment_id TEXT,
    amount REAL NOT NULL,
    mandate_type TEXT,
    failure_reason TEXT,
    status TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 4,
    next_retry_at TEXT,
    payment_verified INTEGER NOT NULL DEFAULT 0,
    recovered_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    FOREIGN KEY (payment_id)
        REFERENCES payments(payment_id)
);

CREATE TABLE IF NOT EXISTS checkouts (
    checkout_id TEXT PRIMARY KEY,
    customer_id TEXT,
    payment_id TEXT,
    amount REAL NOT NULL,
    checkout_stage TEXT,
    dropoff_reason TEXT,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 2,
    next_followup_at TEXT,
    recovery_action TEXT,
    recovery_probability REAL,
    payment_verified INTEGER NOT NULL DEFAULT 0,
    recovered_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    FOREIGN KEY (payment_id)
        REFERENCES payments(payment_id)
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    customer_id TEXT,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    due_date TEXT,
    days_overdue INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    recovery_priority TEXT,
    escalation_count INTEGER NOT NULL DEFAULT 0,
    max_escalations INTEGER NOT NULL DEFAULT 3,
    next_followup_at TEXT,
    recovery_action TEXT,
    payment_verified INTEGER NOT NULL DEFAULT 0,
    recovered_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS recovery_attempts (
    attempt_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    recovery_probability REAL,
    scheduled_for TEXT,
    executed_at TEXT,
    recovered_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS promise_to_pay (
    promise_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    customer_id TEXT,
    promised_date TEXT NOT NULL,
    promised_amount REAL NOT NULL,
    response TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    payment_verified INTEGER NOT NULL DEFAULT 0,
    recovered_amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TEXT
);

CREATE TABLE IF NOT EXISTS recovery_outcomes (
    outcome_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    customer_id TEXT,
    amount_at_risk REAL NOT NULL DEFAULT 0,
    recovered_amount REAL NOT NULL DEFAULT 0,
    recovered INTEGER NOT NULL DEFAULT 0,
    final_action TEXT,
    recovery_probability REAL,
    source TEXT NOT NULL DEFAULT 'DEMO',
    production INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,
    source TEXT NOT NULL DEFAULT 'RECOVEROS',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_versions (
    model_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    accuracy REAL,
    precision_score REAL,
    recall REAL,
    f1_score REAL,
    roc_auc REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_customer
    ON payments(customer_id);

CREATE INDEX IF NOT EXISTS idx_payments_status
    ON payments(status);

CREATE INDEX IF NOT EXISTS idx_subscriptions_customer
    ON subscriptions(customer_id);

CREATE INDEX IF NOT EXISTS idx_mandates_customer
    ON mandates(customer_id);

CREATE INDEX IF NOT EXISTS idx_checkouts_customer
    ON checkouts(customer_id);

CREATE INDEX IF NOT EXISTS idx_invoices_customer
    ON invoices(customer_id);

CREATE INDEX IF NOT EXISTS idx_invoices_status
    ON invoices(status);

CREATE INDEX IF NOT EXISTS idx_recovery_attempts_entity
    ON recovery_attempts(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_ptp_entity
    ON promise_to_pay(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_outcomes_entity
    ON recovery_outcomes(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_audit_entity
    ON audit_events(entity_type, entity_id);
"""


# ================================================================
# INITIALIZATION
# ================================================================

def initialize_database() -> None:
    connection = get_connection()

    try:
        connection.executescript(
            SCHEMA
        )

        connection.commit()

    finally:
        connection.close()


# ================================================================
# GENERIC HELPERS
# ================================================================

def execute(
    query: str,
    parameters: Iterable[Any] = (),
) -> None:

    connection = get_connection()

    try:
        connection.execute(
            query,
            tuple(parameters),
        )

        connection.commit()

    finally:
        connection.close()


def fetch_one(
    query: str,
    parameters: Iterable[Any] = (),
) -> dict[str, Any] | None:

    connection = get_connection()

    try:
        row = connection.execute(
            query,
            tuple(parameters),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def fetch_all(
    query: str,
    parameters: Iterable[Any] = (),
) -> list[dict[str, Any]]:

    connection = get_connection()

    try:
        rows = connection.execute(
            query,
            tuple(parameters),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


# ================================================================
# CUSTOMER
# ================================================================

def upsert_customer(
    customer_id: str,
    customer_name: str = "",
) -> None:

    execute(
        """
        INSERT INTO customers (
            customer_id,
            customer_name
        )
        VALUES (?, ?)
        ON CONFLICT(customer_id)
        DO UPDATE SET
            customer_name = excluded.customer_name
        """,
        (
            customer_id,
            customer_name,
        ),
    )


def get_customer(
    customer_id: str,
) -> dict[str, Any] | None:

    return fetch_one(
        """
        SELECT *
        FROM customers
        WHERE customer_id = ?
        """,
        (
            customer_id,
        ),
    )


# ================================================================
# PAYMENT
# ================================================================

def upsert_payment(
    payment_id: str,
    customer_id: str,
    amount: float,
    failure_reason: str,
    status: str,
) -> None:

    upsert_customer(
        customer_id
    )

    execute(
        """
        INSERT INTO payments (
            payment_id,
            customer_id,
            amount,
            failure_reason,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(payment_id)
        DO UPDATE SET
            customer_id = excluded.customer_id,
            amount = excluded.amount,
            failure_reason = excluded.failure_reason,
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            payment_id,
            customer_id,
            float(amount),
            failure_reason,
            status,
        ),
    )


def get_payment(
    payment_id: str,
) -> dict[str, Any] | None:

    return fetch_one(
        """
        SELECT *
        FROM payments
        WHERE payment_id = ?
        """,
        (
            payment_id,
        ),
    )


# ================================================================
# RECOVERY ATTEMPT
# ================================================================

def save_recovery_attempt(
    attempt_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    attempt_number: int,
    status: str,
    recovery_probability: float | None = None,
    scheduled_for: str | None = None,
    executed_at: str | None = None,
    recovered_amount: float = 0.0,
) -> None:

    execute(
        """
        INSERT OR REPLACE INTO recovery_attempts (
            attempt_id,
            entity_type,
            entity_id,
            action,
            attempt_number,
            status,
            recovery_probability,
            scheduled_for,
            executed_at,
            recovered_amount
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attempt_id,
            entity_type,
            entity_id,
            action,
            int(attempt_number),
            status,
            recovery_probability,
            scheduled_for,
            executed_at,
            float(recovered_amount),
        ),
    )


def get_recovery_attempts(
    entity_type: str,
    entity_id: str,
) -> list[dict[str, Any]]:

    return fetch_all(
        """
        SELECT *
        FROM recovery_attempts
        WHERE entity_type = ?
          AND entity_id = ?
        ORDER BY attempt_number ASC
        """,
        (
            entity_type,
            entity_id,
        ),
    )


# ================================================================
# PROMISE TO PAY
# ================================================================

def save_promise_to_pay(
    promise_id: str,
    entity_type: str,
    entity_id: str,
    customer_id: str,
    promised_date: str,
    promised_amount: float,
    response: str,
    status: str = "PENDING",
) -> None:

    execute(
        """
        INSERT OR REPLACE INTO promise_to_pay (
            promise_id,
            entity_type,
            entity_id,
            customer_id,
            promised_date,
            promised_amount,
            response,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            promise_id,
            entity_type,
            entity_id,
            customer_id,
            promised_date,
            float(promised_amount),
            response,
            status,
        ),
    )


def get_promise_to_pay(
    promise_id: str,
) -> dict[str, Any] | None:

    return fetch_one(
        """
        SELECT *
        FROM promise_to_pay
        WHERE promise_id = ?
        """,
        (
            promise_id,
        ),
    )


# ================================================================
# RECOVERY OUTCOME
# ================================================================

def save_recovery_outcome(
    outcome_id: str,
    entity_type: str,
    entity_id: str,
    customer_id: str,
    amount_at_risk: float,
    recovered_amount: float,
    recovered: bool,
    final_action: str,
    recovery_probability: float | None = None,
    source: str = "DEMO",
    production: bool = False,
) -> None:

    execute(
        """
        INSERT OR REPLACE INTO recovery_outcomes (
            outcome_id,
            entity_type,
            entity_id,
            customer_id,
            amount_at_risk,
            recovered_amount,
            recovered,
            final_action,
            recovery_probability,
            source,
            production
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            outcome_id,
            entity_type,
            entity_id,
            customer_id,
            float(amount_at_risk),
            float(recovered_amount),
            int(bool(recovered)),
            final_action,
            recovery_probability,
            source,
            int(bool(production)),
        ),
    )


def get_recovery_outcomes(
    production_only: bool = False,
) -> list[dict[str, Any]]:

    if production_only:

        return fetch_all(
            """
            SELECT *
            FROM recovery_outcomes
            WHERE production = 1
            ORDER BY created_at DESC
            """
        )

    return fetch_all(
        """
        SELECT *
        FROM recovery_outcomes
        ORDER BY created_at DESC
        """
    )


# ================================================================
# AUDIT
# ================================================================

def save_audit_event(
    event_id: str,
    entity_type: str,
    entity_id: str,
    event_type: str,
    event_data: str,
    source: str = "RECOVEROS",
) -> None:

    execute(
        """
        INSERT OR REPLACE INTO audit_events (
            event_id,
            entity_type,
            entity_id,
            event_type,
            event_data,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            entity_type,
            entity_id,
            event_type,
            event_data,
            source,
        ),
    )


def get_audit_events(
    entity_type: str,
    entity_id: str,
) -> list[dict[str, Any]]:

    return fetch_all(
        """
        SELECT *
        FROM audit_events
        WHERE entity_type = ?
          AND entity_id = ?
        ORDER BY created_at ASC
        """,
        (
            entity_type,
            entity_id,
        ),
    )


# ================================================================
# MODEL REGISTRY
# ================================================================

def save_model_version(
    model_id: str,
    model_name: str,
    version: str,
    status: str,
    accuracy: float | None = None,
    precision_score: float | None = None,
    recall: float | None = None,
    f1_score: float | None = None,
    roc_auc: float | None = None,
) -> None:

    execute(
        """
        INSERT OR REPLACE INTO model_versions (
            model_id,
            model_name,
            version,
            status,
            accuracy,
            precision_score,
            recall,
            f1_score,
            roc_auc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            model_id,
            model_name,
            version,
            status,
            accuracy,
            precision_score,
            recall,
            f1_score,
            roc_auc,
        ),
    )


def get_model_versions() -> list[dict[str, Any]]:

    return fetch_all(
        """
        SELECT *
        FROM model_versions
        ORDER BY created_at DESC
        """
    )


# ================================================================
# DATABASE STATUS
# ================================================================

def database_status() -> dict[str, Any]:

    connection = get_connection()

    try:

        tables = fetch_all(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )

        return {
            "database": str(
                DATABASE_FILE
            ),
            "exists": DATABASE_FILE.exists(),
            "tables": [
                row["name"]
                for row in tables
            ],
        }

    finally:

        connection.close()


# ================================================================
# INITIALIZE WHEN RUN DIRECTLY
# ================================================================

if __name__ == "__main__":

    initialize_database()

    status = database_status()

    print()
    print("=" * 70)
    print("RecoverOS SQL DATABASE")
    print("=" * 70)

    print(
        f"Database : {status['database']}"
    )

    print(
        f"Exists   : {status['exists']}"
    )

    print()
    print("Tables")
    print("-" * 70)

    for table in status[
        "tables"
    ]:

        print(
            f"✓ {table}"
        )

    print()
    print(
        f"Total tables: "
        f"{len(status['tables'])}"
    )

    print("=" * 70)