import os
import sqlite3
from typing import Any


DB_PATH = os.getenv("DB_PATH", "cyber_reactor.db")
ALLOWED_TOURNAMENTS = {"clash royale", "dota 2", "cs go"}


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                first_name TEXT,
                tournament TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def upsert_registration(
    user_id: int,
    tournament: str,
    username: str | None = None,
    first_name: str | None = None,
) -> None:
    tournament_norm = tournament.strip().lower()
    if tournament_norm not in ALLOWED_TOURNAMENTS:
        raise ValueError("Unsupported tournament")

    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO registrations (user_id, username, first_name, tournament)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                tournament=excluded.tournament,
                updated_at=CURRENT_TIMESTAMP
            """,
            (user_id, username, first_name, tournament_norm),
        )
        conn.commit()


def get_registration(user_id: int) -> dict[str, Any] | None:
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT user_id, username, first_name, tournament, created_at, updated_at
            FROM registrations
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    return dict(row) if row else None

