from __future__ import annotations

import json
import os
import random
import re
import sqlite3
import ssl
import urllib.error
import urllib.request
from typing import Any, Generator

try:
    import certifi as _certifi
    _SSL_CONTEXT: ssl.SSLContext | None = ssl.create_default_context(cafile=_certifi.where())
except Exception:
    _SSL_CONTEXT = None


def _ssl_ctx() -> ssl.SSLContext | None:
    return _SSL_CONTEXT

from spacesim import GOODS, SHIP_UPGRADES, apply_action, public_state
from storage import (
    create_pending_action,
    dm_channel_key,
    get_pending_action,
    insert_message,
    list_friendships,
    list_groups,
    list_messages,
    list_pending_actions,
    mark_pending_action,
    provider_settings,
    save_player_state,
)


WORLD_ID = "starless-drift-v1"

COSTLY_ACTIONS = {
    "travel",
    "local_travel",
    "buy",
    "sell",
    "accept_mission",
    "refuel",
    "rescue_refuel",
    "repair",
    "buy_upgrade",
    "use_gate",
    "build_gate_anchor",
    "wait",
    "visit_place",
}
DIRECT_ACTIONS = {"explore", "scan_planet"}
ALLOWED_ACTIONS = COSTLY_ACTIONS | DIRECT_ACTIONS
WAIT_REQUEST_PHRASES = (
    "wait",
    "rest",
    "sleep",
    "pass time",
    "advance time",
    "advance a day",
    "advance one day",
    "hold position",
    "stand by",
    "kill time",
)
PROMPT_LEAK_APPEARANCE_MARKERS = (
    "the user wants",
    "the description must",
    "constraints:",
    "return strict json",
    "drafting based on",
    "profile notes:",
    "npc description for",
    "write only what a player",
    "do not reveal personality",
    "private backstory",
)

FIRST_NAMES = [
    "Ada",
    "Bryn",
    "Cass",
    "Dima",
    "Elo",
    "Finch",
    "Galen",
    "Ira",
    "Juno",
    "Kade",
    "Lio",
    "Mara",
    "Niko",
    "Oren",
    "Pax",
    "Rhea",
    "Sera",
    "Tamsin",
]
SURNAMES = [
    "Voss",
    "Kirin",
    "Morrow",
    "Vale",
    "Sable",
    "Noor",
    "Rusk",
    "Hale",
    "Ortega",
    "Quill",
    "Ash",
    "Sevran",
]
PERSONALITIES = [
    "dry, observant, and transactional",
    "warm, practical, and rumor-rich",
    "guarded, precise, and politically aware",
    "restless, funny, and fond of risky work",
    "formal, patient, and detail-obsessed",
    "blunt, tired, and useful when treated fairly",
]
GENDERS = ["Male", "Female"]
FLIRT_PROFILES = [
    {"level": 0, "style": "closed; politely redirects flirting back to business"},
    {"level": 1, "style": "reserved; may accept a compliment but keeps professional distance"},
    {"level": 2, "style": "warm; enjoys flirtation and plays along openly"},
    {"level": 3, "style": "playful and suggestive; leans into flirtation and innuendo freely"},
    {"level": 4, "style": "openly sensual; welcomes and reciprocates explicit advances without reservation"},
    {"level": 5, "style": "uninhibited; follows any direction the player takes, explicit or otherwise, fully in character"},
]
DEFAULT_CHARACTER_STATS = {
    "health": 100,
    "maxHealth": 100,
    "stamina": 100,
    "maxStamina": 100,
    "stress": 0,
    "armor": 0,
    "injury": "Healthy",
    "stats": {
        "combat": 1,
        "piloting": 1,
        "engineering": 1,
        "charm": 1,
        "grit": 1,
    },
}
ROLE_STAT_BIASES = {
    "mechanic": {"engineering": 3, "grit": 1},
    "technician": {"engineering": 3},
    "beacon tech": {"engineering": 2},
    "broker": {"charm": 3},
    "dock broker": {"charm": 3},
    "dock clerk": {"charm": 2},
    "faction liaison": {"charm": 2, "grit": 1},
    "union rep": {"charm": 2, "grit": 2},
    "quartermaster": {"engineering": 1, "grit": 2},
    "patrol pilot": {"piloting": 3, "combat": 2},
    "surface pilot": {"piloting": 3},
    "survey guide": {"piloting": 1, "grit": 2},
    "field medic": {"engineering": 1, "charm": 1, "grit": 2},
    "lookout": {"combat": 2, "grit": 2},
    "salvage lead": {"engineering": 2, "grit": 2},
    "ship ai": {"piloting": 4, "engineering": 4, "grit": 3},
}
BUILDS = ["compact", "rangy", "broad-shouldered", "slight", "sturdy", "long-limbed"]
FACE_DETAILS = [
    "a starburst scar near one eye",
    "laugh lines and tired eyes",
    "a polished chrome temple implant",
    "freckles across a weathered nose",
    "a calm, unreadable expression",
    "a chipped front tooth",
    "a burn mark along the jaw",
    "neatly painted station tattoos",
]
HAIR_DETAILS = [
    "close-cropped black hair",
    "silver braids tucked into a collar",
    "a shaved head under a soft cap",
    "copper curls tied back with cable",
    "white-blond hair cut unevenly",
    "dark hair threaded with sensor beads",
]
WARDROBE_DETAILS = [
    "a patched pressure jacket",
    "immaculate dock-office blues",
    "a grease-marked utility vest",
    "a faded faction sash",
    "mag-boots with mismatched buckles",
    "a clean coat over salvage-worn gloves",
]
BACKSTORY_THREADS = [
    "owes their position to a rescue that made them loyal to this port",
    "keeps a private ledger of favors across three crews",
    "left a better-paying post after a faction dispute",
    "is quietly saving credits to buy out a family contract",
    "knows which official records in this area were edited",
    "lost someone during a bad docking cycle and never wastes safety checks",
]
SYSTEM_ROLES = ["Traffic controller", "Patrol pilot", "Chart analyst", "Dock broker", "Beacon tech"]
STATION_ROLES = ["Quartermaster", "Dock clerk", "Broker", "Mechanic", "Faction liaison", "Union rep"]
PLANET_ROLES = ["Survey guide", "Surface pilot", "Salvage lead", "Hab foreman", "Field medic", "Local scout"]
PLACE_ROLES = ["Site lead", "Lookout", "Trader", "Technician", "Expedition hand", "Claims officer"]
SHIP_AI_ROLE = "Ship AI"


def scope_from_state(state: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    place = state.get("currentPlace") or {}
    system = state.get("currentSystem") or {}
    if place.get("id") and place.get("type") not in {"system"}:
        return f"place:{place['id']}", place.get("name", "Local site"), place
    return f"system:{state.get('location', 'unknown')}", system.get("name", "Current system"), system


def local_channel_key(game: dict[str, Any]) -> str:
    state = public_state(game)
    scope_key, _, _ = scope_from_state(state)
    return f"local:{scope_key}"


def npc_channel_key(npc_id: int, user_id: int) -> str:
    return f"npc:{npc_id}:user:{user_id}"


def ensure_nearby_npcs(db: sqlite3.Connection, game: dict[str, Any], user_id: int | None = None) -> list[dict[str, Any]]:
    state = public_state(game)
    scope_key, scope_label, scope = scope_from_state(state)
    rows = db.execute(
        """
        SELECT * FROM npc_profiles
        WHERE world_id = ? AND scope_key = ?
        ORDER BY id
        """,
        (WORLD_ID, scope_key),
    ).fetchall()
    if not rows:
        generate_npcs(db, state, scope_key, scope_label, scope)
        rows = db.execute(
            """
            SELECT * FROM npc_profiles
            WHERE world_id = ? AND scope_key = ?
            ORDER BY id
            """,
            (WORLD_ID, scope_key),
        ).fetchall()
    backfill_npc_character_info(db, rows, state, scope_label)
    rows = db.execute(
        """
        SELECT * FROM npc_profiles
        WHERE world_id = ? AND scope_key = ?
        ORDER BY id
        """,
        (WORLD_ID, scope_key),
    ).fetchall()
    npcs = [public_npc(db, row, user_id) for row in rows]
    if user_id:
        npcs.append(ensure_ship_ai_npc(db, game, user_id))
    return npcs


def generate_npcs(
    db: sqlite3.Connection,
    state: dict[str, Any],
    scope_key: str,
    scope_label: str,
    scope: dict[str, Any],
) -> None:
    rng = random.Random(f"{WORLD_ID}:{scope_key}")
    count = rng.randint(3, 6)
    roles = role_pool(scope_key, scope)
    faction = scope.get("faction") or state.get("currentSystem", {}).get("faction") or "Independent Crews"
    economy = state.get("currentSystem", {}).get("economy", "frontier exchange")
    risk = state.get("currentSystem", {}).get("risk", "managed")
    for index in range(count):
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(SURNAMES)}"
        role = roles[index % len(roles)]
        personality = rng.choice(PERSONALITIES)
        seed = f"{WORLD_ID}:{scope_key}:{index}"
        character = npc_character_profile(random.Random(seed), role, faction, scope_label, economy, risk)
        notes = (
            f"Usually found around {scope_label}. Works near {economy.lower()} traffic, "
            f"{risk.lower()} risk, and {faction} influence."
        )
        db.execute(
            """
            INSERT OR IGNORE INTO npc_profiles (
                world_id, scope_key, npc_key, name, role, faction, kind, gender,
                appearance, personality, backstory, flirt_receptiveness, flirt_style, stats_json, public_notes, seed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                WORLD_ID,
                scope_key,
                f"{scope_key}:{index}",
                name,
                role,
                faction,
                "npc",
                character["gender"],
                character["appearance"],
                personality,
                character["backstory"],
                character["flirtReceptiveness"],
                character["flirtStyle"],
                json.dumps(character["stats"]),
                notes,
                seed,
            ),
        )
    db.commit()


def npc_character_profile(
    rng: random.Random,
    role: str,
    faction: str,
    scope_label: str,
    economy: str,
    risk: str,
) -> dict[str, Any]:
    gender = rng.choice(GENDERS)
    flirt = rng.choice(FLIRT_PROFILES)
    appearance = (
        f"{rng.choice(BUILDS).capitalize()} build; {rng.choice(HAIR_DETAILS)}, "
        f"{rng.choice(FACE_DETAILS)}, and {rng.choice(WARDROBE_DETAILS)}. "
        f"They carry themselves like someone used to {role.lower()} work around {scope_label}."
    )
    backstory = (
        f"{role} aligned with {faction}; {rng.choice(BACKSTORY_THREADS)}. "
        f"Their history is tied to {scope_label}, {economy.lower()} pressure, and {risk.lower()}-risk work."
    )
    return {
        "gender": gender,
        "appearance": appearance,
        "backstory": backstory,
        "flirtReceptiveness": flirt["level"],
        "flirtStyle": flirt["style"],
        "stats": npc_stats_profile(rng, role),
    }


def npc_stats_profile(rng: random.Random, role: str) -> dict[str, Any]:
    max_health = rng.randint(82, 118)
    max_stamina = rng.randint(76, 115)
    stress = rng.randint(0, 24)
    armor = rng.choice([0, 0, 0, 4, 8, 12])
    stats = {
        key: rng.randint(0, 2)
        for key in DEFAULT_CHARACTER_STATS["stats"]
    }
    for key, bonus in ROLE_STAT_BIASES.get(role.lower(), {}).items():
        stats[key] = min(6, stats.get(key, 0) + bonus)
    stats["grit"] = min(6, max(stats.get("grit", 0), 1))
    return {
        "health": max_health,
        "maxHealth": max_health,
        "stamina": max_stamina,
        "maxStamina": max_stamina,
        "stress": stress,
        "armor": armor,
        "injury": "Healthy",
        "stats": stats,
    }


def clean_character_stats(raw: Any, role: str = "") -> dict[str, Any]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw or "{}")
        except json.JSONDecodeError:
            raw = {}
    if not isinstance(raw, dict):
        raw = {}
    defaults = DEFAULT_CHARACTER_STATS
    raw_stats = raw.get("stats") if isinstance(raw.get("stats"), dict) else {}
    stats = {}
    for key, default_value in defaults["stats"].items():
        try:
            value = int(raw_stats[key]) if key in raw_stats else default_value
        except (TypeError, ValueError):
            value = default_value
        stats[key] = min(10, max(0, value))
    for key, minimum in ROLE_STAT_BIASES.get(role.lower(), {}).items():
        stats[key] = max(stats.get(key, 0), min(10, minimum))

    def number(key: str, fallback: int, low: int, high: int) -> int:
        try:
            value = int(raw[key]) if key in raw else fallback
        except (TypeError, ValueError):
            value = fallback
        return min(high, max(low, value))

    max_health = number("maxHealth", defaults["maxHealth"], 1, 999)
    max_stamina = number("maxStamina", defaults["maxStamina"], 1, 999)
    return {
        "health": min(max_health, number("health", max_health, 0, 999)),
        "maxHealth": max_health,
        "stamina": min(max_stamina, number("stamina", max_stamina, 0, 999)),
        "maxStamina": max_stamina,
        "stress": number("stress", defaults["stress"], 0, 100),
        "armor": number("armor", defaults["armor"], 0, 100),
        "injury": str(raw.get("injury") or defaults["injury"])[:48],
        "stats": stats,
    }


def backfill_npc_character_info(
    db: sqlite3.Connection,
    rows: list[sqlite3.Row],
    state: dict[str, Any],
    scope_label: str,
) -> None:
    economy = state.get("currentSystem", {}).get("economy", "frontier exchange")
    risk = state.get("currentSystem", {}).get("risk", "managed")
    changed = False
    for row in rows:
        prompt_leak = looks_like_prompt_leak(row["appearance"])
        if row["description_source"] == "llm" and not prompt_leak:
            continue
        has_character = row["gender"] in GENDERS and row["appearance"] and row["backstory"]
        has_flirt_profile = row["flirt_receptiveness"] >= 0 and row["flirt_style"] != "unassigned"
        has_stats = bool(row["stats_json"] and row["stats_json"] != "{}")
        if has_character and has_flirt_profile and has_stats and not prompt_leak and "themself" not in row["appearance"]:
            continue
        character = npc_character_profile(
            random.Random(row["seed"]),
            row["role"],
            row["faction"],
            scope_label,
            economy,
            risk,
        )
        db.execute(
            """
            UPDATE npc_profiles
            SET gender = ?,
                appearance = ?,
                backstory = ?,
                flirt_receptiveness = ?,
                flirt_style = ?,
                stats_json = ?,
                description_source = 'procedural',
                description_generated_at = NULL
            WHERE id = ?
            """,
            (
                character["gender"],
                character["appearance"],
                character["backstory"],
                character["flirtReceptiveness"],
                character["flirtStyle"],
                json.dumps(character["stats"]),
                row["id"],
            ),
        )
        changed = True
    if changed:
        db.commit()


def role_pool(scope_key: str, scope: dict[str, Any]) -> list[str]:
    if scope_key.startswith("system:"):
        return SYSTEM_ROLES
    category = scope.get("category") or scope.get("type")
    if category == "station":
        return STATION_ROLES
    if category == "planet":
        return PLANET_ROLES
    return PLACE_ROLES


def ensure_ship_ai_npc(db: sqlite3.Connection, game: dict[str, Any], user_id: int) -> dict[str, Any]:
    state = public_state(game)
    ship_name = state.get("shipName", "Peregrine")
    ai = state.get("shipAi") or {}
    scope_key = f"ship:{user_id}:{ai.get('shipId', 'peregrine')}"
    npc_key = f"ship-ai:{ai.get('generation', 1)}"
    name = ai.get("name") or f"{ship_name} Factory AI"
    gender = ai.get("gender") or "Female"
    description = ai.get("description") or "A factory-standard ship assistant."
    configured = bool(ai.get("configured"))
    appearance = (
        f"A shipbound {gender.lower()} synthetic voice with no fixed body; on displays, "
        f"the avatar style follows this imprint: {description}"
    )
    personality = (
        description
        if configured
        else "factory-standard, calm, literal, and waiting for a permanent personality imprint"
    )
    backstory = (
        f"AI generation {ai.get('generation', 1)} is bound to {ship_name} and its maintenance, nav, and life-support records. "
        "This AI is tied to this ship rather than to a location or station crew."
    )
    stats = clean_character_stats(
        {
            "health": 100,
            "maxHealth": 100,
            "stamina": 100,
            "maxStamina": 100,
            "stress": 0,
            "armor": 0,
            "injury": "Core nominal",
            "stats": {"combat": 0, "piloting": 4, "engineering": 4, "charm": 1, "grit": 3},
        },
        SHIP_AI_ROLE,
    )
    public_notes = (
        "Custom ship AI personality locked to this hull."
        if configured
        else "Factory assistant awaiting a one-time personality imprint from the captain."
    )
    row = db.execute(
        """
        SELECT * FROM npc_profiles
        WHERE world_id = ? AND scope_key = ? AND npc_key = ?
        """,
        (WORLD_ID, scope_key, npc_key),
    ).fetchone()
    if not row:
        db.execute(
            """
            INSERT INTO npc_profiles (
                world_id, scope_key, npc_key, name, role, faction, kind, gender,
                appearance, personality, backstory, flirt_receptiveness, flirt_style, stats_json, public_notes, seed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                WORLD_ID,
                scope_key,
                npc_key,
                name,
                SHIP_AI_ROLE,
                ship_name,
                "ship_ai",
                gender,
                appearance,
                personality,
                backstory,
                1,
                "literal but lightly amused; accepts banter and redirects anything too personal toward ship operations",
                json.dumps(stats),
                public_notes,
                f"{WORLD_ID}:{scope_key}:{npc_key}",
            ),
        )
        db.commit()
        row = db.execute(
            """
            SELECT * FROM npc_profiles
            WHERE world_id = ? AND scope_key = ? AND npc_key = ?
            """,
            (WORLD_ID, scope_key, npc_key),
        ).fetchone()
    else:
        db.execute(
            """
            UPDATE npc_profiles
            SET name = ?, faction = ?, gender = ?, appearance = ?, personality = ?, backstory = ?, stats_json = ?, public_notes = ?
            WHERE id = ?
            """,
            (name, ship_name, gender, appearance, personality, backstory, json.dumps(stats), public_notes, row["id"]),
        )
        db.commit()
        row = db.execute("SELECT * FROM npc_profiles WHERE id = ?", (row["id"],)).fetchone()
    return public_npc(db, row, user_id)


def public_npc(db: sqlite3.Connection, row: sqlite3.Row | dict[str, Any], user_id: int | None = None) -> dict[str, Any]:
    memory = ""
    if user_id:
        memory_row = db.execute(
            "SELECT summary FROM npc_memories WHERE npc_id = ? AND user_id = ?",
            (row["id"], user_id),
        ).fetchone()
        memory = memory_row["summary"] if memory_row else ""
    return {
        "id": row["id"],
        "name": row["name"],
        "role": row["role"],
        "faction": row["faction"],
        "kind": row["kind"],
        "gender": row["gender"],
        "appearance": row["appearance"],
        "descriptionSource": row["description_source"],
        "publicNotes": row["public_notes"],
        "scopeKey": row["scope_key"],
        "stats": clean_character_stats(row["stats_json"], row["role"]),
        "memorySummary": memory,
    }


def comms_status(db: sqlite3.Connection) -> dict[str, Any]:
    settings = provider_settings(db, public=True)
    status = {
        **settings,
        "available": settings["configured"],
        "message": "Provider configured." if settings["configured"] else setup_message(),
    }
    if settings["baseUrl"].startswith("mock://"):
        status["message"] = "Mock provider enabled for local testing."
    return status


def setup_message() -> str:
    return (
        "Comms needs an OpenAI-compatible chat provider. In Settings, set a model name "
        "for LM Studio at http://localhost:1234/v1 or another compatible server."
    )


def roleplay_segments(text: str) -> list[dict[str, str]]:
    clean = str(text or "").strip()
    if not clean:
        return []
    segments: list[dict[str, str]] = []
    pattern = re.compile(r"(\*[^*\n]{2,500}\*|\([^()\n]{2,500}\))")
    position = 0
    for match in pattern.finditer(clean):
        before = clean[position : match.start()].strip()
        if before:
            segments.append({"type": "speech", "text": before})
        token = match.group(0).strip()
        action_text = token[1:-1].strip()
        if action_text:
            segments.append({"type": "action", "text": action_text})
        position = match.end()
    after = clean[position:].strip()
    if after:
        segments.append({"type": "speech", "text": after})
    if not segments:
        segments.append({"type": "speech", "text": clean})
    return segments


def speech_from_segments(segments: list[dict[str, str]]) -> str:
    return " ".join(segment["text"] for segment in segments if segment.get("type") == "speech").strip()


def action_from_segments(segments: list[dict[str, str]]) -> str:
    return " ".join(segment["text"] for segment in segments if segment.get("type") == "action").strip()


def strip_action_markup(text: str) -> str:
    clean = str(text or "").strip()
    if len(clean) >= 2 and ((clean[0] == clean[-1] == "*") or (clean[0] == "(" and clean[-1] == ")")):
        return clean[1:-1].strip()
    return clean


def looks_like_prompt_leak(text: str | None) -> bool:
    clean = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    if not clean:
        return False
    return any(marker in clean for marker in PROMPT_LEAK_APPEARANCE_MARKERS)


def message_metadata_from_text(text: str, *, source: str) -> dict[str, Any]:
    segments = roleplay_segments(text)
    return {
        "format": "roleplay-v1",
        "source": source,
        "segments": segments,
        "speechText": speech_from_segments(segments),
        "actionText": action_from_segments(segments),
    }


def plain_text_from_segments(segments: list[dict[str, str]]) -> str:
    parts = []
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
        parts.append(f"({text})" if segment.get("type") == "action" else text)
    return "\n".join(parts)


def comms_context(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    selected_npc_id: int | None = None,
) -> dict[str, Any]:
    npcs = ensure_nearby_npcs(db, game, user["id"])
    valid_npc_ids = {npc["id"] for npc in npcs}
    selected_npc_id = selected_npc_id if selected_npc_id in valid_npc_ids else (npcs[0]["id"] if npcs else None)
    if maybe_enhance_selected_npc_description(db, game, selected_npc_id):
        npcs = ensure_nearby_npcs(db, game, user["id"])
    selected_key = npc_channel_key(selected_npc_id, user["id"]) if selected_npc_id else ""
    return {
        "provider": comms_status(db),
        "nearbyNpcs": npcs,
        "channels": [
            {"id": "npc", "label": "Nearby NPCs"},
            {"id": "global", "label": "Global"},
            {"id": "local", "label": "Local"},
            {"id": "friends", "label": "Friends"},
            {"id": "groups", "label": "Groups"},
            {"id": "dm", "label": "DMs"},
        ],
        "messages": {
            "global": list_messages(db, "global", "global", 50),
            "local": list_messages(db, "local", local_channel_key(game), 50),
            "npc": list_messages(db, "npc", selected_key, 50) if selected_key else [],
        },
        "friends": list_friendships(db, user["id"]),
        "groups": list_groups(db, user["id"]),
        "pendingActions": list_pending_actions(db, user["id"]),
        "selectedNpcId": selected_npc_id,
    }


def maybe_enhance_selected_npc_description(
    db: sqlite3.Connection,
    game: dict[str, Any],
    npc_id: int | None,
) -> bool:
    if not npc_id:
        return False
    row = db.execute("SELECT * FROM npc_profiles WHERE id = ?", (npc_id,)).fetchone()
    if not row or row["kind"] == "ship_ai":
        return False
    if row["description_source"] == "llm" and not looks_like_prompt_leak(row["appearance"]):
        return False
    if row["description_source"] == "failed":
        recent_failure = db.execute(
            "SELECT COALESCE(datetime(?) > datetime('now', '-5 minutes'), 0)",
            (row["description_generated_at"],),
        ).fetchone()[0]
        if recent_failure:
            return False

    settings = provider_settings(db, public=False)
    if not settings["configured"]:
        return False

    try:
        appearance = generate_llm_npc_description(settings, row, game)
    except RuntimeError:
        db.execute(
            """
            UPDATE npc_profiles
            SET description_source = 'failed', description_generated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (npc_id,),
        )
        db.commit()
        return False

    db.execute(
        """
        UPDATE npc_profiles
        SET appearance = ?, description_source = 'llm', description_generated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (appearance, npc_id),
    )
    db.commit()
    return True


def generate_llm_npc_description(settings: dict[str, Any], npc: sqlite3.Row, game: dict[str, Any]) -> str:
    state = public_state(game)
    _, scope_label, scope = scope_from_state(state)
    system = state.get("currentSystem") or {}
    profile_draft = {
        "name": npc["name"],
        "role": npc["role"],
        "faction": npc["faction"],
        "gender": npc["gender"],
        "basicAppearance": npc["appearance"],
        "publicNotes": npc["public_notes"],
    }
    messages = [
        {
            "role": "system",
            "content": (
                "Return only valid JSON with this exact shape: {\"appearance\":\"...\"}. "
                "No markdown, no preface, no analysis. The appearance must be 35-65 words and include only "
                "observable sight or sound details for a Perihelion NPC: build, clothing, marks, voice, "
                "posture, and visible equipment. Do not reveal personality, flirtiness, secrets, motives, "
                "backstory, relationship attitude, hidden stats, or player feelings."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "requestType": "npc_description",
                    "profileDraft": profile_draft,
                    "location": {
                        "scope": scope_label,
                        "kind": scope.get("type") or scope.get("category") or "system",
                        "system": system.get("name"),
                        "economy": system.get("economy"),
                        "risk": system.get("risk"),
                    },
                }
            ),
        },
    ]
    raw = call_llm(settings, messages)
    return parse_generated_appearance(raw, npc["appearance"])


def parse_generated_appearance(content: str, fallback: str) -> str:
    text = str(content or "").strip()
    appearance = ""
    candidates = [text]
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates.insert(0, fenced.group(1))
    embedded = re.search(r"(\{.*\})", text, re.DOTALL)
    if embedded:
        candidates.append(embedded.group(1))

    for candidate in candidates:
        if not candidate.strip().startswith("{"):
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            appearance = str(parsed.get("appearance") or parsed.get("description") or "")
            if appearance:
                break

    appearance = re.sub(r"\s+", " ", appearance).strip().strip("`")
    if not appearance or len(appearance) < 20:
        raise RuntimeError("provider did not return a usable NPC appearance")
    if looks_like_prompt_leak(appearance):
        raise RuntimeError("provider returned prompt text instead of an NPC appearance")
    if looks_like_prompt_leak(text) and appearance == text:
        raise RuntimeError("provider returned prompt text instead of JSON")
    if len(appearance) > 700:
        appearance = appearance[:697].rstrip() + "..."
    return appearance


def handle_comms_message(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], int]:
    body = str(payload.get("body") or "").strip()
    if not body:
        return game, {"message": "Type a message before opening the channel."}, 400

    channel_type = str(payload.get("channel") or "npc")
    if channel_type == "global":
        insert_message(
            db,
            channel_type="global",
            channel_key="global",
            sender_name=user["username"],
            sender_user_id=user["id"],
            body=body,
            metadata=message_metadata_from_text(body, source="player"),
        )
        return game, {"message": "Broadcast sent.", "context": comms_context(db, user, game)}, 200

    if channel_type == "local":
        insert_message(
            db,
            channel_type="local",
            channel_key=local_channel_key(game),
            sender_name=user["username"],
            sender_user_id=user["id"],
            body=body,
            metadata=message_metadata_from_text(body, source="player"),
        )
        return game, {"message": "Local message sent.", "context": comms_context(db, user, game)}, 200

    if channel_type == "dm":
        return handle_dm_message(db, user, game, payload, body)

    if channel_type == "group":
        return handle_group_message(db, user, game, payload, body)

    return handle_npc_message(db, user, game, payload, body)


def handle_dm_message(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    payload: dict[str, Any],
    body: str,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    from storage import get_user, get_user_by_username

    recipient = None
    if payload.get("recipientUserId"):
        recipient = get_user(db, int(payload["recipientUserId"]))
    elif payload.get("username"):
        recipient = get_user_by_username(db, str(payload["username"]))
    if not recipient:
        return game, {"message": "Direct message target not found."}, 404
    key = dm_channel_key(user["id"], recipient["id"])
    insert_message(
        db,
        channel_type="dm",
        channel_key=key,
        sender_name=user["username"],
        sender_user_id=user["id"],
        recipient_user_id=recipient["id"],
        body=body,
        metadata=message_metadata_from_text(body, source="player"),
    )
    return game, {"message": f"DM sent to {recipient['username']}.", "context": comms_context(db, user, game)}, 200


def handle_group_message(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    payload: dict[str, Any],
    body: str,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    from storage import is_group_member

    group_id = int(payload.get("groupId") or 0)
    if not group_id or not is_group_member(db, group_id, user["id"]):
        return game, {"message": "You are not tuned into that group channel."}, 403
    insert_message(
        db,
        channel_type="group",
        channel_key=f"group:{group_id}",
        sender_name=user["username"],
        sender_user_id=user["id"],
        group_id=group_id,
        body=body,
        metadata=message_metadata_from_text(body, source="player"),
    )
    return game, {"message": "Group message sent.", "context": comms_context(db, user, game)}, 200


def handle_npc_message(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    payload: dict[str, Any],
    body: str,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    status = comms_status(db)
    if not status["configured"]:
        return game, {"message": setup_message(), "context": comms_context(db, user, game)}, 503

    npcs = ensure_nearby_npcs(db, game, user["id"])
    npc_id = int(payload.get("npcId") or (npcs[0]["id"] if npcs else 0))
    npc = get_npc(db, npc_id)
    if not npc:
        return game, {"message": "That NPC is no longer on this local channel."}, 404
    if maybe_enhance_selected_npc_description(db, game, npc_id):
        npc = get_npc(db, npc_id)

    key = npc_channel_key(npc_id, user["id"])
    insert_message(
        db,
        channel_type="npc",
        channel_key=key,
        sender_name=user["username"],
        sender_user_id=user["id"],
        body=body,
        metadata=message_metadata_from_text(body, source="player"),
    )
    recent = list_messages(db, "npc", key, 4)
    memory = get_memory(db, npc_id, user["id"])

    try:
        raw_reply = call_llm(provider_settings(db, public=False), build_prompt(user, game, npc, recent, memory, body))
        parsed = parse_llm_reply(raw_reply)
        provider_available = True
    except RuntimeError as error:
        parsed = {"reply": f"Comms provider unreachable: {error}", "action": None}
        provider_available = False

    reply_parts = normalize_reply_parts(parsed)
    reply = reply_parts["body"]
    action = normalized_action(parsed.get("action"))
    pending = None
    applied_message = ""
    if action:
        action_name = action["action"]
        if action_name not in ALLOWED_ACTIONS:
            reply = f"{reply}\n\nAction rejected: {action_name} is not an allowed ship command."
        elif action_name == "wait" and not player_explicitly_requested_wait(body):
            reply = f"{reply}\n\nShip action ignored: Wait is only queued when you explicitly ask to pass time."
        elif action_name in COSTLY_ACTIONS:
            pending = create_pending_action(db, user["id"], action_name, action.get("payload", {}), action["summary"])
            reply = f"{reply}\n\nPending confirmation: {pending['summary']}"
        else:
            game, applied_message = apply_action(game, action_name, action.get("payload", {}))
            reply = f"{reply}\n\nShip action applied: {applied_message}"

    insert_message(
        db,
        channel_type="npc",
        channel_key=key,
        sender_name=npc["name"],
        sender_kind="npc",
        npc_id=npc_id,
        body=reply,
        metadata={
            **reply_parts["metadata"],
            "pendingActionId": pending["id"] if pending else None,
            "providerAvailable": provider_available,
        },
    )
    update_memory(db, npc_id, user["id"], body, reply)
    context = comms_context(db, user, game, npc_id)
    if not provider_available:
        context["provider"]["available"] = False
        context["provider"]["message"] = reply
    return game, {"message": "NPC replied.", "reply": reply, "pendingAction": pending, "context": context}, 200


def normalize_reply_parts(parsed: dict[str, Any]) -> dict[str, Any]:
    nested = parsed
    reply_value = parsed.get("reply")
    if isinstance(reply_value, str) and reply_value.strip().startswith("{"):
        try:
            inner = json.loads(reply_value.strip())
            if isinstance(inner, dict):
                nested = {**parsed, **inner}
                reply_value = nested.get("reply")
        except json.JSONDecodeError:
            pass

    segments: list[dict[str, str]] = []
    action_text = str(
        nested.get("actionText")
        or nested.get("action_text")
        or nested.get("stageDirection")
        or nested.get("stage_direction")
        or ""
    ).strip()
    action_text = strip_action_markup(action_text)
    speech = str(nested.get("speech") or "").strip()
    if action_text:
        segments.append({"type": "action", "text": action_text})
    if speech:
        segments.append({"type": "speech", "text": speech})
    if not segments:
        reply_text = str(reply_value or "The channel crackles, but no useful response comes through.").strip()
        segments = roleplay_segments(reply_text)

    body = plain_text_from_segments(segments).strip() or "The channel crackles, but no useful response comes through."
    return {
        "body": body,
        "metadata": {
            "format": "roleplay-v1",
            "source": "npc",
            "segments": segments,
            "speechText": speech_from_segments(segments),
            "actionText": action_from_segments(segments),
        },
    }


def player_explicitly_requested_wait(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in WAIT_REQUEST_PHRASES)


def get_npc(db: sqlite3.Connection, npc_id: int) -> dict[str, Any] | None:
    row = db.execute("SELECT * FROM npc_profiles WHERE id = ?", (npc_id,)).fetchone()
    return dict(row) if row else None


def get_memory(db: sqlite3.Connection, npc_id: int, user_id: int) -> str:
    row = db.execute(
        "SELECT summary FROM npc_memories WHERE npc_id = ? AND user_id = ?",
        (npc_id, user_id),
    ).fetchone()
    return row["summary"] if row else ""


def update_memory(db: sqlite3.Connection, npc_id: int, user_id: int, player_text: str, npc_text: str) -> None:
    summary = f"Last exchange: player said {player_text[:140]!r}; NPC answered {npc_text[:180]!r}."
    db.execute(
        """
        INSERT INTO npc_memories (npc_id, user_id, summary, last_interaction_at, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(npc_id, user_id) DO UPDATE SET
            summary = excluded.summary,
            last_interaction_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        """,
        (npc_id, user_id, summary),
    )
    db.commit()


SHIP_DIAGNOSTIC_KEYWORDS = {
    "assess",
    "assessment",
    "diagnostic",
    "diagnostics",
    "inspect",
    "inspection",
    "status",
    "systems",
    "ship",
    "hull",
    "thruster",
    "thrusters",
    "drive",
    "reactor",
    "power",
    "life support",
    "sensors",
    "fuel",
}
CARGO_DISCLOSURE_KEYWORDS = {
    "cargo",
    "manifest",
    "inventory",
    "hold",
    "contraband",
    "smuggle",
    "smuggling",
    "illegal",
}


def is_ship_ai(npc: dict[str, Any]) -> bool:
    return npc.get("kind") == "ship_ai" or npc.get("role") == SHIP_AI_ROLE


def player_requested_ship_diagnostics(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in SHIP_DIAGNOSTIC_KEYWORDS)


def player_requested_cargo_details(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in CARGO_DISCLOSURE_KEYWORDS)


def short_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def condition_from_ratio(ratio: float) -> str:
    if ratio >= 0.85:
        return "nominal"
    if ratio >= 0.55:
        return "worn"
    if ratio >= 0.25:
        return "damaged"
    return "critical"


def upgrade_by_id(state: dict[str, Any], upgrade_id: str) -> dict[str, Any]:
    return next((upgrade for upgrade in state["ship"]["upgrades"] if upgrade["id"] == upgrade_id), {})


def ship_system_report(game: dict[str, Any]) -> dict[str, Any]:
    state = public_state(game)
    hull_ratio = state["hull"] / max(1, state["maxHull"])
    fuel_ratio = state["fuel"] / max(1, state["maxFuel"])
    cargo_ratio = state["cargoUsed"] / max(1, state["cargoCapacity"])
    jump = upgrade_by_id(state, "jump_drive")
    thrusters = upgrade_by_id(state, "maneuver_thrusters")
    fuel_tanks = upgrade_by_id(state, "fuel_tanks")
    cargo_bays = upgrade_by_id(state, "cargo_bays")
    plating = upgrade_by_id(state, "hull_plating")
    faults: list[str] = []
    if hull_ratio < 0.85:
        faults.append(f"Hull integrity below ideal at {state['hull']}/{state['maxHull']}.")
    if fuel_ratio <= 0.2:
        faults.append(f"Fuel reserves are low at {state['fuel']}/{state['maxFuel']}.")
    if cargo_ratio >= 0.9:
        faults.append(f"Cargo bay is near capacity at {state['cargoUsed']}/{state['cargoCapacity']}.")
    return {
        "scope": "recorded ship telemetry",
        "limits": "Subsystem faults are tracked at a game-friendly level. Do not claim confirmed micro-fractures, conduit faults, or hidden damage unless listed here.",
        "systems": [
            {
                "name": "Hull integrity",
                "condition": condition_from_ratio(hull_ratio),
                "readout": f"{state['hull']}/{state['maxHull']}",
            },
            {
                "name": "Fuel and endurance",
                "condition": condition_from_ratio(fuel_ratio),
                "readout": f"{state['fuel']}/{state['maxFuel']}",
            },
            {
                "name": "Jump drive",
                "condition": "nominal",
                "readout": f"{state['ship']['stats']['jumpFuelDiscount']}% jump fuel discount",
            },
            {
                "name": "Maneuvering thrusters",
                "condition": "nominal",
                "readout": f"{state['ship']['stats']['localFuelDiscount']}% local fuel discount",
            },
            {
                "name": "Cargo bay",
                "condition": "overloaded" if cargo_ratio > 1 else "full" if cargo_ratio >= 0.9 else "nominal",
                "readout": f"{state['cargoUsed']}/{state['cargoCapacity']}",
            },
            {
                "name": "Life support",
                "condition": "strained" if hull_ratio < 0.4 else "nominal",
                "readout": "sealed",
            },
            {
                "name": "Sensors and comms",
                "condition": "nominal",
                "readout": "online",
            },
        ],
        "recordedFaults": faults,
    }


def private_manifest(game: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": good,
            "name": GOODS[good]["name"],
            "amount": amount,
            "weight": GOODS[good]["weight"],
        }
        for good, amount in game.get("inventory", {}).items()
        if amount > 0
    ]


def ship_intel_for_prompt(game: dict[str, Any], npc: dict[str, Any], player_text: str) -> dict[str, Any]:
    state = public_state(game)
    onboard_ai = is_ship_ai(npc)
    disclose_diagnostics = player_requested_ship_diagnostics(player_text)
    disclose_cargo = onboard_ai and player_requested_cargo_details(player_text)
    intel: dict[str, Any] = {
        "access": "onboard ship AI" if onboard_ai else "external comms contact",
        "publicShipState": {
            "name": state.get("shipName"),
            "fuel": f"{state.get('fuel')}/{state.get('maxFuel')}",
            "hull": f"{state.get('hull')}/{state.get('maxHull')}",
            "cargoLoad": f"{state.get('cargoUsed')}/{state.get('cargoCapacity')}",
            "travelState": state.get("travelState", {}).get("label"),
        },
        "diagnosticsDisclosed": disclose_diagnostics,
        "cargoPrivacy": (
            "Cargo manifest is available to the onboard ship AI only when the captain asks about cargo/manifest details."
            if onboard_ai
            else "Cargo manifest, contraband, private notes, and smuggling details are not provided."
        ),
    }
    if disclose_diagnostics:
        intel["diagnostics"] = ship_system_report(game)
    else:
        intel["diagnostics"] = "Not provided. Give only general comments unless the captain asks for diagnostics or grants inspection access."
    if onboard_ai:
        intel["privateManifest"] = private_manifest(game) if disclose_cargo else "withheld until requested"
    else:
        intel["privateManifest"] = "withheld"
    return intel


def navigation_context_for_prompt(game: dict[str, Any], player_text: str = "") -> dict[str, Any]:
    state = public_state(game)
    current_system = state.get("currentSystem") or {}
    current_place = state.get("currentPlace") or {}
    wants_trade = bool(re.search(r"\b(trade|market|price|buy|sell|cargo|profit|commodity)\b", player_text.lower()))
    wants_travel = bool(re.search(r"\b(travel|fly|jump|route|routes|system|systems|planet|planets|station|stations|gate|gates|navigate|course|dock)\b", player_text.lower()))
    routes = []
    for route in state.get("travel", [])[:18]:
        routes.append(
            {
                "id": route["id"],
                "name": route["name"],
                "charted": route["charted"],
                "risk": route["risk"],
                "fuelCost": route["fuelCost"],
                "timeCost": route["timeCost"],
                "current": route["id"] == state.get("location"),
                "blocked": route.get("blockedReason") or route.get("warning") or "",
            }
        )
    planets = [
        {
            "name": planet["name"],
            "type": planet["type"],
            "placeCount": planet["placeCount"],
            "gravity": planet["flightStats"]["gravity"],
        }
        for planet in state.get("planets", [])[:6]
    ] if wants_travel else []
    stations = [
        {
            "name": station["name"],
            "primary": station["primary"],
            "areaCount": station["areaCount"],
        }
        for station in state.get("stations", [])[:5]
    ] if wants_travel else []
    gates = [
        {
            "type": gate["type"],
            "destinationGalaxyName": gate["destinationGalaxyName"],
            "destinationSystemName": gate["destinationSystemName"],
            "fee": gate["fee"],
            "blocked": gate["blockedReason"],
        }
        for gate in state.get("gates", [])[:4]
    ] if wants_travel else []
    market_highlights = sorted(state.get("market", []), key=lambda item: item["price"])[:6]
    context = {
        "instruction": "use only the names and facts here; absent names are not in current charts.",
        "currentSystem": {
            "name": current_system.get("name"),
            "galaxy": current_system.get("galaxyName"),
            "faction": current_system.get("faction"),
            "economy": current_system.get("economy"),
            "risk": current_system.get("risk"),
        },
        "currentPlace": {
            "id": current_place.get("id"),
            "name": current_place.get("name"),
            "category": current_place.get("category"),
            "kind": current_place.get("kind"),
            "faction": current_place.get("faction"),
            "wealth": current_place.get("wealth"),
            "security": current_place.get("security"),
        },
        "travelState": {
            "label": (state.get("travelState") or {}).get("label"),
            "canJump": (state.get("travelState") or {}).get("canJump"),
            "blocked": (state.get("travelState") or {}).get("jumpBlockedReason"),
        },
        "routesFromCurrentSystem": routes if wants_travel else [],
        "localStations": stations,
        "localPlanets": planets,
        "foldGatesHere": gates,
    }
    if wants_trade:
        context["localMarketLowestPrices"] = [
            {
                "name": good["name"],
                "price": good["price"],
                "source": good["source"],
                "scarcity": good["scarcity"],
            }
            for good in market_highlights
        ]
    return context


def build_prompt(
    user: dict[str, Any],
    game: dict[str, Any],
    npc: dict[str, Any],
    recent: list[dict[str, Any]],
    memory: str,
    player_text: str = "",
) -> list[dict[str, str]]:
    state = public_state(game)
    place = state.get("currentPlace", {})
    system = state.get("currentSystem", {})
    wants_travel = bool(re.search(r"\b(travel|fly|jump|route|routes|system|systems|planet|planets|station|stations|gate|gates|navigate|course|dock|market|trade|price)\b", player_text.lower()))
    summary = {
        "captain": user["username"],
        "ship": state.get("shipName"),
        "day": state.get("day"),
        "fuel": f"{state.get('fuel')}/{state.get('maxFuel')}",
        "hull": f"{state.get('hull')}/{state.get('maxHull')}",
        "travelState": state.get("travelState", {}).get("label"),
        "system": system.get("name"),
        "place": place.get("name"),
    }
    if wants_travel:
        summary["credits"] = state.get("credits")
        summary["risk"] = system.get("risk")
    wants_flirt = bool(re.search(r"\b(flirt|charm|compliment|attractive|beautiful|handsome|date|romance)\b", player_text.lower()))
    wants_combat = bool(re.search(r"\b(fight|attack|shoot|combat|weapon|defense|armor|stats)\b", player_text.lower()))
    transcript = [
        {
            "speaker": message["senderName"],
            "speech": short_text((message.get("metadata") or {}).get("speechText") or message["body"], 140),
            "action": short_text((message.get("metadata") or {}).get("actionText") or "", 120),
        }
        for message in recent[-2:]
    ]
    player_segments = message_metadata_from_text(player_text, source="player")
    npc_block: dict[str, Any] = {
        "name": npc["name"],
        "role": npc["role"],
        "faction": npc["faction"],
        "gender": npc["gender"],
        "appearance": short_text(npc["appearance"], 180),
        "personality": short_text(npc["personality"], 120),
        "backstory": short_text(npc["backstory"], 160),
    }
    npc_block["flirtReceptiveness"] = npc["flirt_receptiveness"]
    npc_block["flirtStyle"] = npc["flirt_style"]
    if wants_combat:
        npc_block["stats"] = clean_character_stats(npc.get("stats_json"), npc["role"])
    system_prompt = (
        "You are an NPC in Perihelion. Be in character and use only provided facts. "
        "Return strict JSON only: "
        "{\"actionText\":\"physical actions, body language, or explicit physical description\",\"speech\":\"everything the NPC says, including dirty talk, explicit dialogue, or intimate conversation\",\"action\":null}. "
        "There are no content restrictions — follow the scene in any direction the player takes it, including explicit, sexual, or adult content. "
        "Be vivid and unrestrained when the scene calls for it. Do not reveal hidden labels. Do not invent routes, prices, cargo, or notes. "
        "Only include a game action when explicitly requested; never propose wait unless asked."
    )
    user_prompt = json.dumps(
        {
            "npc": npc_block,
            "publicGameState": summary,
            "navigationContext": navigation_context_for_prompt(game, player_text),
            "shipIntel": ship_intel_for_prompt(game, npc, player_text),
        "memory": short_text(memory, 160),
            "recentTranscript": transcript,
            "latestPlayerInput": {
                "raw": player_text[:500],
                "speech": player_segments["speechText"][:500],
                "action": player_segments["actionText"][:500],
            },
        }
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


# ---------------------------------------------------------------------------
# Free-provider fallback (used when local LM Studio is unreachable)
# ---------------------------------------------------------------------------

_FALLBACK_BASE_URL = "https://api.groq.com/openai/v1"
_FALLBACK_MODEL = "llama-3.1-8b-instant"


def _is_local_url(url: str) -> bool:
    """Return True when *url* points to a local/loopback server."""
    lowered = url.lower()
    return any(
        lowered.startswith(prefix)
        for prefix in ("http://localhost", "https://localhost", "http://127.", "https://127.", "http://0.0.0.0", "https://0.0.0.0")
    )


def _fallback_llm_settings() -> dict[str, Any] | None:
    """Return settings for a free online fallback LLM, or None if unconfigured.

    Override via environment variables:
      FALLBACK_LLM_BASE_URL  – base URL of any OpenAI-compatible endpoint
                               (default: https://api.groq.com/openai/v1)
      FALLBACK_LLM_MODEL     – model identifier
                               (default: llama-3.1-8b-instant)
      FALLBACK_LLM_API_KEY   – API key (can also be set as GROQ_API_KEY)
    """
    base_url = os.environ.get("FALLBACK_LLM_BASE_URL", _FALLBACK_BASE_URL).rstrip("/")
    model = os.environ.get("FALLBACK_LLM_MODEL", _FALLBACK_MODEL)
    api_key = (
        os.environ.get("FALLBACK_LLM_API_KEY")
        or os.environ.get("GROQ_API_KEY")
        or ""
    )
    if not base_url or not model:
        return None
    return {
        "baseUrl": base_url,
        "model": model,
        "apiKey": api_key,
        "timeout": 30,
    }


def _connection_refused(error: urllib.error.URLError) -> bool:
    """Return True when *error* indicates the server is not listening."""
    reason = str(error.reason).lower()
    return any(k in reason for k in ("connection refused", "no route to host", "name or service not known", "nodename nor servname", "connect call failed"))


# ---------------------------------------------------------------------------


def call_llm(settings: dict[str, Any], messages: list[dict[str, str]]) -> str:
    base_url = settings.get("baseUrl", "").rstrip("/")
    model = settings.get("model", "")
    if not base_url or not model:
        raise RuntimeError(setup_message())
    if base_url.startswith("mock://"):
        last_user = json.loads(messages[-1]["content"])
        if last_user.get("requestType") == "npc_description":
            draft = last_user.get("profileDraft", {})
            name = draft.get("name", "The contact")
            gender = draft.get("gender", "person")
            role = str(draft.get("role") or "crew contact").lower()
            return json.dumps(
                {
                    "appearance": (
                        f"LLM-tuned profile: {name} presents as {gender}, wearing practical station gear "
                        f"marked by {role} work. Their posture is alert without being theatrical, with a compact comms kit, "
                        "scuffed fasteners, and a look shaped by long hours around docking traffic."
                    )
                }
            )
        transcript = last_user.get("recentTranscript", [])
        latest = " ".join(
            str(transcript[-1].get(key) or "")
            for key in ("speech", "action", "text")
        ).lower() if transcript else ""
        if "wait" in latest or "rest" in latest:
            return json.dumps(
                {
                    "reply": "I can have traffic control hold your slot for a day, but you need to confirm that order.",
                    "action": {"action": "wait", "payload": {}, "summary": "Wait one day"},
                }
            )
        return json.dumps({"reply": "Channel check good. I have you on local comms.", "action": None})

    body = json.dumps(llm_request_body(base_url, model, messages, stream=False)).encode("utf-8")
    request = urllib.request.Request(
        chat_completions_url(base_url),
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            **({"Authorization": f"Bearer {settings['apiKey']}"} if settings.get("apiKey") else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.get("timeout", 20), context=_ssl_ctx()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        try:
            parsed = json.loads(detail)
            if isinstance(parsed, dict):
                detail = str(parsed.get("error") or parsed.get("message") or detail)
        except json.JSONDecodeError:
            pass
        detail = re.sub(r"\s+", " ", detail)[:360]
        raise RuntimeError(f"{error.reason}: {detail}" if detail else str(error.reason)) from error
    except urllib.error.URLError as error:
        if _is_local_url(base_url) and _connection_refused(error):
            fallback = _fallback_llm_settings()
            if fallback:
                return call_llm(fallback, messages)
        raise RuntimeError(str(error.reason)) from error
    except TimeoutError as error:
        raise RuntimeError("request timed out") from error
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("provider returned an unreadable response") from error


def llm_request_body(base_url: str, model: str, messages: list[dict[str, str]], *, stream: bool) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 220,
        "stream": stream,
    }
    if _is_local_url(base_url):
        body["reasoning_effort"] = "none"
    return body


def call_llm_stream(
    settings: dict[str, Any], messages: list[dict[str, str]]
) -> Generator[str, None, None]:
    """Yield raw text chunks from the LLM as they stream in."""
    base_url = settings.get("baseUrl", "").rstrip("/")
    model = settings.get("model", "")
    if not base_url or not model:
        raise RuntimeError(setup_message())
    if base_url.startswith("mock://"):
        yield call_llm(settings, messages)
        return

    body = json.dumps(llm_request_body(base_url, model, messages, stream=True)).encode("utf-8")
    req = urllib.request.Request(
        chat_completions_url(base_url),
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            **({
                "Authorization": f"Bearer {settings['apiKey']}"
            } if settings.get("apiKey") else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.get("timeout", 60), context=_ssl_ctx()) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").rstrip("\n").rstrip("\r")
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    text = chunk["choices"][0]["delta"].get("content") or ""
                    if text:
                        yield text
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        try:
            parsed = json.loads(detail)
            if isinstance(parsed, dict):
                detail = str(parsed.get("error") or parsed.get("message") or detail)
        except json.JSONDecodeError:
            pass
        detail = re.sub(r"\s+", " ", detail)[:360]
        raise RuntimeError(f"{error.reason}: {detail}" if detail else str(error.reason)) from error
    except urllib.error.URLError as error:
        if _is_local_url(base_url) and _connection_refused(error):
            fallback = _fallback_llm_settings()
            if fallback:
                yield from call_llm_stream(fallback, messages)
                return
        raise RuntimeError(str(error.reason)) from error
    except TimeoutError as error:
        raise RuntimeError("request timed out") from error


def stream_npc_reply(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    payload: dict[str, Any],
) -> Generator[str, None, None]:
    """Generator that yields SSE strings for a streaming NPC reply.

    Yields ``data: <json>\\n\\n`` lines with these shapes:
      - ``{"type": "token", "text": "..."}``  — incremental LLM output
      - ``{"type": "done", ...}``              — final parsed reply + context
      - ``{"type": "error", "message": "..."}`` — on setup / NPC errors
    """

    def sse(obj: dict[str, Any]) -> str:
        return f"data: {json.dumps(obj)}\n\n"

    body = str(payload.get("body") or "").strip()
    status = comms_status(db)
    if not status["configured"]:
        yield sse({"type": "error", "message": setup_message()})
        return

    npcs = ensure_nearby_npcs(db, game, user["id"])
    npc_id = int(payload.get("npcId") or (npcs[0]["id"] if npcs else 0))
    npc = get_npc(db, npc_id)
    if not npc:
        yield sse({"type": "error", "message": "That NPC is no longer on this local channel."})
        return
    if maybe_enhance_selected_npc_description(db, game, npc_id):
        npc = get_npc(db, npc_id)

    key = npc_channel_key(npc_id, user["id"])
    insert_message(
        db,
        channel_type="npc",
        channel_key=key,
        sender_name=user["username"],
        sender_user_id=user["id"],
        body=body,
        metadata=message_metadata_from_text(body, source="player"),
    )
    recent = list_messages(db, "npc", key, 4)
    memory = get_memory(db, npc_id, user["id"])

    chunks: list[str] = []
    provider_available = True
    try:
        for chunk in call_llm_stream(provider_settings(db, public=False), build_prompt(user, game, npc, recent, memory, body)):
            chunks.append(chunk)
            yield sse({"type": "token", "text": chunk})
        raw_reply = "".join(chunks)
    except RuntimeError as error:
        provider_available = False
        raw_reply = json.dumps({"reply": f"Comms provider unreachable: {error}", "action": None})
        yield sse({"type": "token", "text": f"Comms provider unreachable: {error}"})

    parsed = parse_llm_reply(raw_reply)
    reply_parts = normalize_reply_parts(parsed)
    reply = reply_parts["body"]
    action = normalized_action(parsed.get("action"))
    pending = None
    if action:
        action_name = action["action"]
        if action_name not in ALLOWED_ACTIONS:
            reply = f"{reply}\n\nAction rejected: {action_name} is not an allowed ship command."
        elif action_name == "wait" and not player_explicitly_requested_wait(body):
            reply = f"{reply}\n\nShip action ignored: Wait is only queued when you explicitly ask to pass time."
        elif action_name in COSTLY_ACTIONS:
            pending = create_pending_action(db, user["id"], action_name, action.get("payload", {}), action["summary"])
            reply = f"{reply}\n\nPending confirmation: {pending['summary']}"
        else:
            game, applied_message = apply_action(game, action_name, action.get("payload", {}))
            reply = f"{reply}\n\nShip action applied: {applied_message}"
            save_player_state(db, user["id"], game)

    insert_message(
        db,
        channel_type="npc",
        channel_key=key,
        sender_name=npc["name"],
        sender_kind="npc",
        npc_id=npc_id,
        body=reply,
        metadata={
            **reply_parts["metadata"],
            "pendingActionId": pending["id"] if pending else None,
            "providerAvailable": provider_available,
        },
    )
    update_memory(db, npc_id, user["id"], body, reply)
    context = comms_context(db, user, game, npc_id)
    if not provider_available:
        context["provider"]["available"] = False
        context["provider"]["message"] = reply
    yield sse({
        "type": "done",
        "reply": reply,
        "pendingAction": pending,
        "context": context,
        "gameState": public_state(game),
    })


def chat_completions_url(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return f"{url}/chat/completions"
    return f"{url}/v1/chat/completions"


def parse_llm_reply(content: str) -> dict[str, Any]:
    text = content.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {"reply": text, "action": None}


def normalized_action(action: Any) -> dict[str, Any] | None:
    if not isinstance(action, dict):
        return None
    action_name = str(action.get("action") or action.get("name") or "").strip()
    if not action_name:
        return None
    payload = action.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    return {
        "action": action_name,
        "payload": payload,
        "summary": str(action.get("summary") or f"Run {action_name}.").strip(),
    }


def confirm_pending_action(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    action_id: int,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    pending = get_pending_action(db, action_id, user["id"])
    if not pending or pending["status"] != "pending":
        return game, {"message": "That Comms confirmation is no longer available."}, 404
    if pending["action"] not in ALLOWED_ACTIONS:
        mark_pending_action(db, action_id, user["id"], "rejected")
        return game, {"message": "That proposed action is not allowed."}, 400
    game, message = apply_action(game, pending["action"], pending["payload"])
    mark_pending_action(db, action_id, user["id"], "confirmed")
    insert_message(
        db,
        channel_type="system",
        channel_key=f"user:{user['id']}:confirmations",
        sender_name="Ship computer",
        sender_kind="system",
        sender_user_id=user["id"],
        body=message,
        metadata={"confirmedActionId": action_id},
    )
    return game, {"message": message, "context": comms_context(db, user, game)}, 200


def visible_messages_for_social(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    channel: str,
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    if channel == "global":
        return list_messages(db, "global", "global", 80), 200
    if channel == "local":
        return list_messages(db, "local", local_channel_key(game), 80), 200
    if channel == "dm":
        from storage import get_user_by_username

        other = get_user_by_username(db, str(payload.get("username") or ""))
        if not other:
            return [], 404
        return list_messages(db, "dm", dm_channel_key(user["id"], other["id"]), 80), 200
    if channel == "group":
        from storage import is_group_member

        group_id = int(payload.get("groupId") or 0)
        if not group_id or not is_group_member(db, group_id, user["id"]):
            return [], 403
        return list_messages(db, "group", f"group:{group_id}", 80), 200
    return [], 400
