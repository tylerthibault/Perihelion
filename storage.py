from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from werkzeug.security import check_password_hash, generate_password_hash


DEFAULT_DB_PATH = Path(os.environ.get("SPACESIM_DB", "perihelion.sqlite3"))


def connect_db(path: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    db_path = Path(path or DEFAULT_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(path: str | os.PathLike[str] | None = None) -> None:
    with connect_db(path) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS player_states (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS npc_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                world_id TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                npc_key TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                faction TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'npc',
                gender TEXT NOT NULL DEFAULT 'Unspecified',
                appearance TEXT NOT NULL DEFAULT '',
                description_source TEXT NOT NULL DEFAULT 'procedural',
                description_generated_at TEXT,
                personality TEXT NOT NULL,
                backstory TEXT NOT NULL DEFAULT '',
                flirt_receptiveness INTEGER NOT NULL DEFAULT -1,
                flirt_style TEXT NOT NULL DEFAULT 'unassigned',
                stats_json TEXT NOT NULL DEFAULT '{}',
                public_notes TEXT NOT NULL,
                seed TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(world_id, scope_key, npc_key)
            );

            CREATE TABLE IF NOT EXISTS npc_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npc_id INTEGER NOT NULL REFERENCES npc_profiles(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                summary TEXT NOT NULL DEFAULT '',
                last_interaction_at TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(npc_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_type TEXT NOT NULL,
                channel_key TEXT NOT NULL,
                sender_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                sender_name TEXT NOT NULL,
                sender_kind TEXT NOT NULL,
                npc_id INTEGER REFERENCES npc_profiles(id) ON DELETE SET NULL,
                recipient_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                group_id INTEGER,
                body TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pending_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action_name TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                summary TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            );

            CREATE TABLE IF NOT EXISTS personal_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, target_type, target_id)
            );

            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                friend_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, friend_user_id)
            );

            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL DEFAULT 'member',
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(group_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        ensure_column(db, "npc_profiles", "gender", "TEXT NOT NULL DEFAULT 'Unspecified'")
        ensure_column(db, "npc_profiles", "appearance", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "npc_profiles", "description_source", "TEXT NOT NULL DEFAULT 'procedural'")
        ensure_column(db, "npc_profiles", "description_generated_at", "TEXT")
        ensure_column(db, "npc_profiles", "backstory", "TEXT NOT NULL DEFAULT ''")
        ensure_column(db, "npc_profiles", "kind", "TEXT NOT NULL DEFAULT 'npc'")
        ensure_column(db, "npc_profiles", "flirt_receptiveness", "INTEGER NOT NULL DEFAULT -1")
        ensure_column(db, "npc_profiles", "flirt_style", "TEXT NOT NULL DEFAULT 'unassigned'")
        ensure_column(db, "npc_profiles", "stats_json", "TEXT NOT NULL DEFAULT '{}'")


def ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        db.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def user_count(db: sqlite3.Connection) -> int:
    return int(db.execute("SELECT COUNT(*) FROM users").fetchone()[0])


def public_user(row: sqlite3.Row | dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "isAdmin": bool(row["is_admin"]),
    }


def create_user(db: sqlite3.Connection, username: str, password: str) -> dict[str, Any]:
    username = username.strip()
    if len(username) < 3 or len(username) > 32:
        raise ValueError("Username must be 3-32 characters.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    is_admin = 1 if user_count(db) == 0 else 0
    cursor = db.execute(
        "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
        (username, generate_password_hash(password), is_admin),
    )
    db.commit()
    return get_user(db, cursor.lastrowid)


def get_user(db: sqlite3.Connection, user_id: int | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    return row_to_dict(db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def get_user_by_username(db: sqlite3.Connection, username: str) -> dict[str, Any] | None:
    return row_to_dict(db.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone())


def verify_user(db: sqlite3.Connection, username: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_username(db, username)
    if not user or not check_password_hash(user["password_hash"], password):
        return None
    return user


def load_player_state(db: sqlite3.Connection, user_id: int) -> dict[str, Any] | None:
    row = db.execute("SELECT state_json FROM player_states WHERE user_id = ?", (user_id,)).fetchone()
    return json.loads(row["state_json"]) if row else None


def save_player_state(db: sqlite3.Connection, user_id: int, game: dict[str, Any]) -> None:
    db.execute(
        """
        INSERT INTO player_states (user_id, state_json, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            state_json = excluded.state_json,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, json.dumps(game)),
    )
    db.commit()


def get_setting(db: sqlite3.Connection, key: str) -> str:
    row = db.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else ""


def set_setting(db: sqlite3.Connection, key: str, value: str) -> None:
    db.execute(
        "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    db.commit()


def provider_settings(db: sqlite3.Connection, public: bool = False) -> dict[str, Any]:
    base_url = get_setting(db, "llm_base_url") or os.environ.get("LLM_BASE_URL", "http://localhost:1234/v1")
    model = get_setting(db, "llm_model") or os.environ.get("LLM_MODEL", "")
    api_key = get_setting(db, "llm_api_key") or os.environ.get("LLM_API_KEY", "")
    timeout = get_setting(db, "llm_timeout") or os.environ.get("LLM_TIMEOUT", "20")
    settings = {
        "baseUrl": base_url,
        "model": model,
        "apiKey": "" if public else api_key,
        "apiKeySet": bool(api_key),
        "timeout": int(timeout) if str(timeout).isdigit() else 20,
        "configured": bool(base_url and model),
    }
    return settings


def save_provider_settings(db: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    for field, key in (("baseUrl", "llm_base_url"), ("model", "llm_model"), ("apiKey", "llm_api_key")):
        if field in payload:
            set_setting(db, key, str(payload.get(field) or "").strip())
    return provider_settings(db, public=True)


def insert_message(
    db: sqlite3.Connection,
    *,
    channel_type: str,
    channel_key: str,
    sender_name: str,
    body: str,
    sender_kind: str = "player",
    sender_user_id: int | None = None,
    npc_id: int | None = None,
    recipient_user_id: int | None = None,
    group_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO messages (
            channel_type, channel_key, sender_user_id, sender_name, sender_kind,
            npc_id, recipient_user_id, group_id, body, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            channel_type,
            channel_key,
            sender_user_id,
            sender_name,
            sender_kind,
            npc_id,
            recipient_user_id,
            group_id,
            body,
            json.dumps(metadata or {}),
        ),
    )
    db.commit()
    return get_message(db, cursor.lastrowid)


def get_message(db: sqlite3.Connection, message_id: int) -> dict[str, Any]:
    row = db.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return public_message(row)


def public_message(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "channelType": row["channel_type"],
        "channelKey": row["channel_key"],
        "senderUserId": row["sender_user_id"],
        "senderName": row["sender_name"],
        "senderKind": row["sender_kind"],
        "npcId": row["npc_id"],
        "recipientUserId": row["recipient_user_id"],
        "groupId": row["group_id"],
        "body": row["body"],
        "metadata": json.loads(row["metadata_json"] or "{}"),
        "createdAt": row["created_at"],
    }


def list_messages(db: sqlite3.Connection, channel_type: str, channel_key: str, limit: int = 40) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT * FROM messages
        WHERE channel_type = ? AND channel_key = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (channel_type, channel_key, limit),
    ).fetchall()
    return [public_message(row) for row in reversed(rows)]


def create_pending_action(
    db: sqlite3.Connection,
    user_id: int,
    action_name: str,
    payload: dict[str, Any],
    summary: str,
) -> dict[str, Any]:
    clean_payload = payload or {}
    existing_rows = db.execute(
        """
        SELECT * FROM pending_actions
        WHERE user_id = ? AND action_name = ? AND status = 'pending'
        ORDER BY id DESC
        """,
        (user_id, action_name),
    ).fetchall()
    for row in existing_rows:
        if json.loads(row["payload_json"] or "{}") == clean_payload:
            return get_pending_action(db, row["id"], user_id)

    cursor = db.execute(
        """
        INSERT INTO pending_actions (user_id, action_name, payload_json, summary)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, action_name, json.dumps(clean_payload), summary),
    )
    db.commit()
    return get_pending_action(db, cursor.lastrowid, user_id)


def get_pending_action(db: sqlite3.Connection, action_id: int, user_id: int) -> dict[str, Any] | None:
    row = db.execute(
        "SELECT * FROM pending_actions WHERE id = ? AND user_id = ?",
        (action_id, user_id),
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "action": row["action_name"],
        "payload": json.loads(row["payload_json"] or "{}"),
        "summary": row["summary"],
        "status": row["status"],
        "createdAt": row["created_at"],
    }


def list_pending_actions(db: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        "SELECT * FROM pending_actions WHERE user_id = ? AND status = 'pending' ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "action": row["action_name"],
            "payload": json.loads(row["payload_json"] or "{}"),
            "summary": row["summary"],
            "status": row["status"],
            "createdAt": row["created_at"],
        }
        for row in rows
    ]


def mark_pending_action(db: sqlite3.Connection, action_id: int, user_id: int, status: str) -> None:
    db.execute(
        "UPDATE pending_actions SET status = ? WHERE id = ? AND user_id = ?",
        (status, action_id, user_id),
    )
    db.commit()


NOTE_TARGET_TYPES = {"npc", "system", "place", "planet", "station"}


def validate_note_target(target_type: str, target_id: str) -> tuple[str, str]:
    clean_type = target_type.strip().lower()
    clean_id = target_id.strip()
    if clean_type not in NOTE_TARGET_TYPES:
        raise ValueError("That note target type is not supported.")
    if not clean_id or len(clean_id) > 180:
        raise ValueError("That note target is not valid.")
    return clean_type, clean_id


def public_note(row: sqlite3.Row | dict[str, Any] | None, target_type: str, target_id: str) -> dict[str, Any]:
    if not row:
        return {
            "id": None,
            "targetType": target_type,
            "targetId": target_id,
            "title": "",
            "body": "",
            "createdAt": None,
            "updatedAt": None,
        }
    return {
        "id": row["id"],
        "targetType": row["target_type"],
        "targetId": row["target_id"],
        "title": row["title"],
        "body": row["body"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def get_personal_note(db: sqlite3.Connection, user_id: int, target_type: str, target_id: str) -> dict[str, Any]:
    clean_type, clean_id = validate_note_target(target_type, target_id)
    row = db.execute(
        """
        SELECT * FROM personal_notes
        WHERE user_id = ? AND target_type = ? AND target_id = ?
        """,
        (user_id, clean_type, clean_id),
    ).fetchone()
    return public_note(row, clean_type, clean_id)


def save_personal_note(
    db: sqlite3.Connection,
    user_id: int,
    target_type: str,
    target_id: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    clean_type, clean_id = validate_note_target(target_type, target_id)
    clean_title = title.strip()[:120]
    clean_body = body.strip()[:12000]
    db.execute(
        """
        INSERT INTO personal_notes (user_id, target_type, target_id, title, body, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, target_type, target_id) DO UPDATE SET
            title = excluded.title,
            body = excluded.body,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, clean_type, clean_id, clean_title, clean_body),
    )
    db.commit()
    return get_personal_note(db, user_id, clean_type, clean_id)


def list_personal_notes(db: sqlite3.Connection, user_id: int, limit: int = 40) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT * FROM personal_notes
        WHERE user_id = ? AND (title <> '' OR body <> '')
        ORDER BY updated_at DESC, id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    return [public_note(row, row["target_type"], row["target_id"]) for row in rows]


def dm_channel_key(user_id: int, other_user_id: int) -> str:
    first, second = sorted([int(user_id), int(other_user_id)])
    return f"dm:{first}:{second}"


def list_friendships(db: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT friendships.*, users.username AS friend_username, users.is_admin AS friend_is_admin
        FROM friendships
        JOIN users ON users.id = friendships.friend_user_id
        WHERE friendships.user_id = ?
        ORDER BY users.username COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "userId": row["friend_user_id"],
            "username": row["friend_username"],
            "isAdmin": bool(row["friend_is_admin"]),
            "status": row["status"],
            "createdAt": row["created_at"],
        }
        for row in rows
    ]


def add_friendship(db: sqlite3.Connection, user_id: int, friend_user_id: int) -> None:
    if user_id == friend_user_id:
        raise ValueError("You are already on your own crew manifest.")
    for owner, friend in ((user_id, friend_user_id), (friend_user_id, user_id)):
        db.execute(
            """
            INSERT INTO friendships (user_id, friend_user_id, status)
            VALUES (?, ?, 'accepted')
            ON CONFLICT(user_id, friend_user_id) DO UPDATE SET status = 'accepted'
            """,
            (owner, friend),
        )
    db.commit()


def create_group(db: sqlite3.Connection, owner_user_id: int, name: str) -> dict[str, Any]:
    group_name = name.strip()
    if len(group_name) < 2 or len(group_name) > 48:
        raise ValueError("Group name must be 2-48 characters.")
    cursor = db.execute(
        "INSERT INTO groups (owner_user_id, name) VALUES (?, ?)",
        (owner_user_id, group_name),
    )
    group_id = cursor.lastrowid
    db.execute(
        "INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'owner')",
        (group_id, owner_user_id),
    )
    db.commit()
    return get_group(db, group_id, owner_user_id)


def get_group(db: sqlite3.Connection, group_id: int, user_id: int | None = None) -> dict[str, Any] | None:
    params: list[Any] = [group_id]
    membership_clause = ""
    if user_id is not None:
        membership_clause = "JOIN group_members AS requester ON requester.group_id = groups.id AND requester.user_id = ?"
        params.append(user_id)
    row = db.execute(
        f"""
        SELECT groups.*, users.username AS owner_username
        FROM groups
        JOIN users ON users.id = groups.owner_user_id
        {membership_clause}
        WHERE groups.id = ?
        """,
        tuple(reversed(params)) if user_id is not None else tuple(params),
    ).fetchone()
    if not row:
        return None
    return public_group(db, row)


def list_groups(db: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT groups.*, users.username AS owner_username
        FROM groups
        JOIN group_members ON group_members.group_id = groups.id
        JOIN users ON users.id = groups.owner_user_id
        WHERE group_members.user_id = ?
        ORDER BY groups.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    return [public_group(db, row) for row in rows]


def public_group(db: sqlite3.Connection, row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    members = db.execute(
        """
        SELECT users.id, users.username, group_members.role
        FROM group_members
        JOIN users ON users.id = group_members.user_id
        WHERE group_members.group_id = ?
        ORDER BY group_members.role = 'owner' DESC, users.username COLLATE NOCASE
        """,
        (row["id"],),
    ).fetchall()
    return {
        "id": row["id"],
        "name": row["name"],
        "ownerUserId": row["owner_user_id"],
        "ownerUsername": row["owner_username"],
        "createdAt": row["created_at"],
        "members": [
            {"id": member["id"], "username": member["username"], "role": member["role"]}
            for member in members
        ],
    }


def add_group_member(db: sqlite3.Connection, group_id: int, user_id: int, role: str = "member") -> None:
    db.execute(
        """
        INSERT INTO group_members (group_id, user_id, role)
        VALUES (?, ?, ?)
        ON CONFLICT(group_id, user_id) DO UPDATE SET role = excluded.role
        """,
        (group_id, user_id, role),
    )
    db.commit()


def is_group_member(db: sqlite3.Connection, group_id: int, user_id: int) -> bool:
    row = db.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    ).fetchone()
    return bool(row)
