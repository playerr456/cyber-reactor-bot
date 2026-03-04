import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any


ALLOWED_TOURNAMENTS = {"clash royale", "dota 2", "cs go"}
_BLOB_PREFIX = "registrations"


def _default_db_path() -> str:
    # Vercel serverless allows writing to /tmp only.
    if os.getenv("VERCEL") and not os.getenv("DB_PATH"):
        return "/tmp/cyber_reactor.db"
    return os.getenv("DB_PATH", "cyber_reactor.db")


DB_PATH = _default_db_path()


def _use_blob_backend() -> bool:
    return bool(os.getenv("BLOB_READ_WRITE_TOKEN"))


def _slug_tournament(name: str) -> str:
    return name.lower().replace(" ", "_")


def _unslug_tournament(name: str) -> str:
    return name.lower().replace("_", " ")


def _extract_tournament_from_path(pathname: str) -> str | None:
    # registrations/<user_id>/<timestamp>__<tournament>.json
    m = re.search(r"__([a-z0-9_\-]+)\.json$", pathname)
    if not m:
        return None
    candidate = _unslug_tournament(m.group(1))
    return candidate if candidate in ALLOWED_TOURNAMENTS else None


def _get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if _use_blob_backend():
        try:
            from vercel.blob import list_objects

            # Validate token / SDK availability early.
            list_objects(limit=1, prefix=f"{_BLOB_PREFIX}/")
            return
        except Exception as exc:
            raise RuntimeError(f"Vercel Blob init failed: {exc}") from exc

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

    if _use_blob_backend():
        try:
            from vercel.blob import put

            ts = int(time.time() * 1000)
            path = f"{_BLOB_PREFIX}/{user_id}/{ts}__{_slug_tournament(tournament_norm)}.json"
            payload = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "tournament": tournament_norm,
                "timestamp_ms": ts,
            }
            put(
                path,
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                access="private",
                add_random_suffix=False,
                content_type="application/json",
            )
            return
        except Exception as exc:
            raise RuntimeError(f"Vercel Blob write failed: {exc}") from exc

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
    if _use_blob_backend():
        try:
            from vercel.blob import list_objects

            result = list_objects(prefix=f"{_BLOB_PREFIX}/{user_id}/", limit=1000)
            blobs = getattr(result, "blobs", None) or []
            if not blobs:
                return None

            latest = max(blobs, key=lambda b: str(getattr(b, "uploaded_at", "")))
            pathname = getattr(latest, "pathname", "")
            tournament = _extract_tournament_from_path(pathname)
            if not tournament:
                return None

            uploaded_at = getattr(latest, "uploaded_at", None)
            uploaded_at_str = uploaded_at.isoformat() if hasattr(uploaded_at, "isoformat") else str(uploaded_at)
            return {
                "user_id": user_id,
                "username": None,
                "first_name": None,
                "tournament": tournament,
                "created_at": uploaded_at_str,
                "updated_at": uploaded_at_str,
            }
        except Exception as exc:
            raise RuntimeError(f"Vercel Blob read failed: {exc}") from exc

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
