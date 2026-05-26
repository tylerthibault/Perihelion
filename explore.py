"""explore.py — DM-driven exploration system for Perihelion.

The player can "walk around" a place by typing free-form actions/observations.
An LLM acting as a D&D-style Dungeon Master narrates the scene.

Key behaviours:
- First visit: DM opens with a rich, atmospheric description of the new location.
  The opening paragraph is saved to `scene_memories` as both the first_description
  and the initial dm_summary.
- Revisit: DM acknowledges the return and references what happened last time
  (drawn from dm_summary in scene_memories).
- After each exchange the dm_summary is refreshed with a brief running note
  so the DM stays consistent across sessions.
- Streaming (SSE) is supported via `stream_dm_reply`.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Generator

from comms import (
    call_llm,
    call_llm_stream,
    comms_status,
    setup_message,
)
from spacesim import public_state
from storage import (
    get_scene_memory,
    insert_explore_message,
    list_explore_messages,
    provider_settings,
    save_scene_memory,
)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are the Dungeon Master for Perihelion, a gritty sci-fi space sim.
Your job is to narrate what the player's captain sees, hears, smells, and experiences
as they walk around a location.

Rules:
- Write in second person ("You see…", "The air tastes of…").
- Be vivid, atmospheric, and specific. Draw on the place's faction, wealth, and economy.
- Do NOT invent game mechanics, prices, routes, or cargo that contradict game state.
- Do NOT break the fourth wall or mention AI / LLM.
- On a first visit, open with a 3–5 sentence scene-setting paragraph.
- On a revisit, briefly acknowledge the return (1 sentence) then continue naturally.
- Keep responses to 3–6 sentences unless the player asks for more.
- If the player tries to perform a costly game action (buy, sell, travel, fight),
  describe the attempt narratively then add exactly one JSON block at the end:
  ```json
  {"game_action": "<action_name>", "summary": "<one-line description>"}
  ```
  Allowed game_actions: buy, sell, travel, refuel, repair, accept_mission.
  For pure narration, omit the JSON block entirely.
"""


def _place_context(place: dict[str, Any], game_state: dict[str, Any]) -> dict[str, Any]:
    """Build a compact place description dict to feed the LLM."""
    ctx: dict[str, Any] = {
        "placeId": place.get("id", ""),
        "placeName": place.get("name", "Unknown"),
        "category": place.get("category", ""),
        "faction": place.get("faction", "Unknown"),
        "wealth": place.get("wealth", "Unknown"),
        "economy": place.get("economy", ""),
        "security": place.get("security", ""),
        "description": place.get("description", ""),
        "terrain": place.get("terrain", ""),
        "kind": place.get("kind", ""),
    }
    loc = game_state.get("travelState", {})
    ctx["travelState"] = loc.get("label", "")
    ctx["system"] = (game_state.get("currentSystem") or {}).get("name", "")
    ctx["captain"] = game_state.get("shipName", "")
    ctx["day"] = game_state.get("day", 0)
    return ctx


def _build_dm_messages(
    user: dict[str, Any],
    place: dict[str, Any],
    game: dict[str, Any],
    scene_memory: dict[str, Any] | None,
    recent_messages: list[dict[str, Any]],
    player_input: str,
) -> list[dict[str, str]]:
    state = public_state(game)
    place_ctx = _place_context(place, state)
    is_first_visit = scene_memory is None

    context_block: dict[str, Any] = {
        "captain": user.get("username", "Captain"),
        "place": place_ctx,
        "firstVisit": is_first_visit,
    }
    if scene_memory:
        context_block["previousVisits"] = scene_memory.get("visit_count", 1)
        context_block["sceneMemory"] = scene_memory.get("dm_summary", "")
        context_block["firstDescription"] = scene_memory.get("first_description", "")

    # Recent conversation history
    transcript = [
        {"from": msg["sender"], "text": msg["body"]}
        for msg in recent_messages[-6:]
    ]

    user_content = json.dumps({
        "context": context_block,
        "recentTranscript": transcript,
        "playerInput": player_input[:600] if player_input else "__ENTER_SCENE__",
    })

    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# Scene memory update
# ---------------------------------------------------------------------------

_SUMMARY_SYSTEM = (
    "You are a memory scribe for a sci-fi game DM. "
    "Given the DM's narration of a scene, write a 2–3 sentence summary of what happened "
    "and what the place felt like. Include any notable characters, objects, or events. "
    "Be compact — this is a memory note, not a retelling. Plain text only."
)


def _make_summary(settings: dict[str, Any], dm_text: str, place_name: str) -> str:
    """Ask the LLM to distill the DM's text into a compact scene memory."""
    try:
        messages = [
            {"role": "system", "content": _SUMMARY_SYSTEM},
            {"role": "user", "content": f"Place: {place_name}\n\nDM narration:\n{dm_text[:1200]}"},
        ]
        result = call_llm(settings, messages)
        # result may be JSON or plain text
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return str(parsed.get("reply") or parsed.get("summary") or result)[:600]
        except (json.JSONDecodeError, ValueError):
            pass
        return result.strip()[:600]
    except Exception:
        # Never crash the main flow for a summary
        return dm_text[:400]


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def enter_scene(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    place: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """Non-streaming entry to a scene. Returns (game, response_dict, http_status)."""
    status = comms_status(db)
    if not status["configured"]:
        return game, {"message": setup_message()}, 503

    place_id = place.get("id", "")
    place_name = place.get("name", "Unknown")
    scene_memory = get_scene_memory(db, user["id"], place_id)
    recent = list_explore_messages(db, user["id"], place_id, limit=6)
    settings = provider_settings(db, public=False)

    prompt = _build_dm_messages(user, place, game, scene_memory, recent, "")
    try:
        raw = call_llm(settings, prompt)
    except RuntimeError as err:
        return game, {"message": f"DM offline: {err}"}, 503

    dm_text = _extract_dm_text(raw)
    game_action = _extract_game_action(raw)

    # Persist the exchange
    insert_explore_message(db, user["id"], place_id, "DM", dm_text)

    # Save scene memory
    first_desc = dm_text if scene_memory is None else (scene_memory.get("first_description") or dm_text)
    summary = _make_summary(settings, dm_text, place_name)
    save_scene_memory(db, user["id"], place_id, place_name, first_desc, summary)

    response: dict[str, Any] = {
        "text": dm_text,
        "placeId": place_id,
        "placeName": place_name,
        "isFirstVisit": scene_memory is None,
    }
    if game_action:
        response["gameAction"] = game_action

    return game, response, 200


def handle_explore_message(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    place: dict[str, Any],
    player_text: str,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """Player says/does something in the current scene. Non-streaming."""
    status = comms_status(db)
    if not status["configured"]:
        return game, {"message": setup_message()}, 503

    place_id = place.get("id", "")
    place_name = place.get("name", "Unknown")
    scene_memory = get_scene_memory(db, user["id"], place_id)
    recent = list_explore_messages(db, user["id"], place_id, limit=6)
    settings = provider_settings(db, public=False)

    insert_explore_message(db, user["id"], place_id, user["username"], player_text)

    prompt = _build_dm_messages(user, place, game, scene_memory, recent, player_text)
    try:
        raw = call_llm(settings, prompt)
    except RuntimeError as err:
        return game, {"message": f"DM offline: {err}"}, 503

    dm_text = _extract_dm_text(raw)
    game_action = _extract_game_action(raw)

    insert_explore_message(db, user["id"], place_id, "DM", dm_text)

    # Update scene memory summary
    first_desc = scene_memory.get("first_description", dm_text) if scene_memory else dm_text
    full_text = (scene_memory.get("dm_summary", "") + "\n" + dm_text).strip()
    summary = _make_summary(settings, full_text, place_name)
    save_scene_memory(db, user["id"], place_id, place_name, first_desc, summary)

    response: dict[str, Any] = {
        "text": dm_text,
        "placeId": place_id,
        "placeName": place_name,
    }
    if game_action:
        response["gameAction"] = game_action

    return game, response, 200


def stream_dm_reply(
    db: sqlite3.Connection,
    user: dict[str, Any],
    game: dict[str, Any],
    place: dict[str, Any],
    player_text: str,
) -> Generator[str, None, None]:
    """SSE generator for streaming DM narration tokens.

    Yields ``data: <json>\\n\\n`` lines:
      - ``{"type": "token", "text": "..."}`` — incremental text
      - ``{"type": "done", "text": "...", "placeId": "...", "isFirstVisit": bool}``
      - ``{"type": "error", "message": "..."}``
    """

    def sse(obj: dict[str, Any]) -> str:
        return f"data: {json.dumps(obj)}\n\n"

    status = comms_status(db)
    if not status["configured"]:
        yield sse({"type": "error", "message": setup_message()})
        return

    place_id = place.get("id", "")
    place_name = place.get("name", "Unknown")
    scene_memory = get_scene_memory(db, user["id"], place_id)
    is_first_visit = scene_memory is None
    recent = list_explore_messages(db, user["id"], place_id, limit=6)
    settings = provider_settings(db, public=False)

    if player_text:
        insert_explore_message(db, user["id"], place_id, user["username"], player_text)

    prompt = _build_dm_messages(user, place, game, scene_memory, recent, player_text or "")

    chunks: list[str] = []
    try:
        for chunk in call_llm_stream(settings, prompt):
            chunks.append(chunk)
            yield sse({"type": "token", "text": chunk})
    except RuntimeError as err:
        yield sse({"type": "error", "message": str(err)})
        return

    full_text = "".join(chunks)
    dm_text = _extract_dm_text(full_text)
    game_action = _extract_game_action(full_text)

    insert_explore_message(db, user["id"], place_id, "DM", dm_text)

    first_desc = scene_memory.get("first_description", dm_text) if scene_memory else dm_text
    existing_summary = scene_memory.get("dm_summary", "") if scene_memory else ""
    combined = (existing_summary + "\n" + dm_text).strip()
    summary = _make_summary(settings, combined, place_name)
    save_scene_memory(db, user["id"], place_id, place_name, first_desc, summary)

    done_payload: dict[str, Any] = {
        "type": "done",
        "text": dm_text,
        "placeId": place_id,
        "placeName": place_name,
        "isFirstVisit": is_first_visit,
    }
    if game_action:
        done_payload["gameAction"] = game_action
    yield sse(done_payload)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_dm_text(raw: str) -> str:
    """Strip any trailing JSON game_action block from the DM's reply."""
    # Remove ```json ... ``` blocks
    clean = re.sub(r"```json.*?```", "", raw, flags=re.DOTALL).strip()
    # Also strip bare JSON objects at the end that look like {"game_action": ...}
    clean = re.sub(r'\{[^{}]*"game_action"[^{}]*\}\s*$', "", clean, flags=re.DOTALL).strip()
    # Try parsing as JSON (LLM might reply with {"reply": "...", ...})
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return str(parsed.get("reply") or parsed.get("text") or parsed.get("narration") or raw).strip()
    except (json.JSONDecodeError, ValueError):
        pass
    return clean or raw.strip()


def _extract_game_action(raw: str) -> dict[str, Any] | None:
    """Pull out a game_action block if the DM included one."""
    # JSON block inside ```json ... ```
    match = re.search(r"```json\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict) and data.get("game_action"):
                return data
        except (json.JSONDecodeError, ValueError):
            pass
    # Bare object at end
    match = re.search(r'(\{"game_action"[^}]+\})', raw)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict) and data.get("game_action"):
                return data
        except (json.JSONDecodeError, ValueError):
            pass
    # Check if reply itself is a JSON dict with game_action
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("game_action"):
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return None
