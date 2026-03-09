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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clash_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                group_number TEXT NOT NULL,
                supercell_id TEXT NOT NULL UNIQUE,
                telegram_user_id INTEGER UNIQUE,
                telegram_username TEXT UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(clash_registrations)").fetchall()}
        if "telegram_user_id" not in columns:
            conn.execute("ALTER TABLE clash_registrations ADD COLUMN telegram_user_id INTEGER")
        if "telegram_username" not in columns:
            conn.execute("ALTER TABLE clash_registrations ADD COLUMN telegram_username TEXT")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_clash_supercell_id ON clash_registrations(supercell_id)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_clash_user_id ON clash_registrations(telegram_user_id)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_clash_username ON clash_registrations(telegram_username)")
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


def get_clash_registration(
    telegram_user_id: int | None = None,
    telegram_username: str | None = None,
) -> dict[str, Any] | None:
    username_norm = telegram_username.strip().lower().lstrip("@") if telegram_username else None

    with _get_connection() as conn:
        if telegram_user_id is not None:
            row = conn.execute(
                """
                SELECT full_name, group_number, supercell_id, telegram_user_id, telegram_username, created_at, updated_at
                FROM clash_registrations
                WHERE telegram_user_id = ?
                """,
                (telegram_user_id,),
            ).fetchone()
            if row:
                return dict(row)

        if username_norm:
            row = conn.execute(
                """
                SELECT full_name, group_number, supercell_id, telegram_user_id, telegram_username, created_at, updated_at
                FROM clash_registrations
                WHERE telegram_username = ?
                """,
                (username_norm,),
            ).fetchone()
            if row:
                return dict(row)

    return None


def upsert_clash_registration(
    full_name: str,
    group_number: str,
    supercell_id: str,
    telegram_user_id: int | None = None,
    telegram_username: str | None = None,
    allow_update: bool = False,
) -> str:
    full_name_norm = full_name.strip()
    group_number_norm = group_number.strip()
    supercell_id_norm = supercell_id.strip().upper()
    username_norm = telegram_username.strip().lower().lstrip("@") if telegram_username else None

    if not full_name_norm or not group_number_norm or not supercell_id_norm:
        raise ValueError("All fields are required")
    if allow_update and telegram_user_id is None and not username_norm:
        raise ValueError("IDENTITY_REQUIRED")

    with _get_connection() as conn:
        existing_by_identity = None
        if telegram_user_id is not None:
            existing_by_identity = conn.execute(
                """
                SELECT id
                FROM clash_registrations
                WHERE telegram_user_id = ?
                """,
                (telegram_user_id,),
            ).fetchone()
        if not existing_by_identity and username_norm:
            existing_by_identity = conn.execute(
                """
                SELECT id
                FROM clash_registrations
                WHERE telegram_username = ?
                """,
                (username_norm,),
            ).fetchone()

        existing_by_supercell = conn.execute(
            """
            SELECT id, telegram_user_id, telegram_username
            FROM clash_registrations
            WHERE supercell_id = ?
            """,
            (supercell_id_norm,),
        ).fetchone()

        if existing_by_supercell:
            is_same_owner = False
            if telegram_user_id is not None and existing_by_supercell["telegram_user_id"] == telegram_user_id:
                is_same_owner = True
            if username_norm and existing_by_supercell["telegram_username"] == username_norm:
                is_same_owner = True
            if existing_by_identity and existing_by_identity["id"] == existing_by_supercell["id"]:
                is_same_owner = True

            if not is_same_owner:
                raise ValueError("SUPERCELL_ID_ALREADY_USED")

        if existing_by_identity:
            if not allow_update:
                raise ValueError("USER_ALREADY_REGISTERED")

            conn.execute(
                """
                UPDATE clash_registrations
                SET full_name = ?,
                    group_number = ?,
                    supercell_id = ?,
                    telegram_user_id = COALESCE(?, telegram_user_id),
                    telegram_username = COALESCE(?, telegram_username),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    full_name_norm,
                    group_number_norm,
                    supercell_id_norm,
                    telegram_user_id,
                    username_norm,
                    existing_by_identity["id"],
                ),
            )
            conn.commit()
            return "updated"

        if allow_update:
            raise ValueError("REGISTRATION_NOT_FOUND")

        conn.execute(
            """
            INSERT INTO clash_registrations (
                full_name,
                group_number,
                supercell_id,
                telegram_user_id,
                telegram_username
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (full_name_norm, group_number_norm, supercell_id_norm, telegram_user_id, username_norm),
        )
        conn.commit()
        return "created"
