from __future__ import annotations

import json

import pytest

from app import create_app
from comms import build_prompt, chat_completions_url, parse_generated_appearance
from spacesim import create_game, public_state
from storage import connect_db, init_db


def make_app(tmp_path):
    db_path = tmp_path / "spacesim.sqlite3"
    app = create_app({"TESTING": True, "DATABASE": str(db_path), "SECRET_KEY": "test-key"})
    return app, db_path


def register(client, username: str, password: str = "secret12"):
    return client.post("/api/auth/register", json={"username": username, "password": password})


def login(client, username: str, password: str = "secret12"):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_register_hashes_password_and_first_user_is_admin(tmp_path):
    app, db_path = make_app(tmp_path)
    client = app.test_client()

    response = register(client, "admin")

    assert response.status_code == 201
    assert response.get_json()["user"]["isAdmin"] is True
    with connect_db(db_path) as db:
        row = db.execute("SELECT username, password_hash, is_admin FROM users WHERE username = 'admin'").fetchone()
    assert row["username"] == "admin"
    assert row["password_hash"] != "secret12"
    assert row["is_admin"] == 1


def test_player_state_survives_new_app_instance(tmp_path):
    app, db_path = make_app(tmp_path)
    client = app.test_client()
    register(client, "pilot")

    waited = client.post("/api/action", json={"action": "wait"}).get_json()
    assert waited["day"] == 2

    restarted_app = create_app({"TESTING": True, "DATABASE": str(db_path), "SECRET_KEY": "test-key"})
    restarted_client = restarted_app.test_client()
    login_response = login(restarted_client, "pilot")

    assert login_response.status_code == 200
    assert login_response.get_json()["day"] == 2


def test_provider_missing_disables_npc_comms(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "captain")

    context = client.get("/api/comms/context").get_json()
    selected = next(npc for npc in context["nearbyNpcs"] if npc["id"] == context["selectedNpcId"])

    assert context["provider"]["configured"] is False
    assert context["provider"]["available"] is False
    assert "provider" in context["provider"]["message"].lower()
    assert selected["descriptionSource"] == "procedural"


def test_nearby_npcs_are_shared_between_players(tmp_path):
    app, db_path = make_app(tmp_path)
    first = app.test_client()
    second = app.test_client()
    register(first, "alpha")
    register(second, "beta")

    first_npcs = first.get("/api/comms/context").get_json()["nearbyNpcs"]
    second_npcs = second.get("/api/comms/context").get_json()["nearbyNpcs"]

    assert first_npcs
    assert [npc["name"] for npc in first_npcs] == [npc["name"] for npc in second_npcs]
    assert [npc["role"] for npc in first_npcs] == [npc["role"] for npc in second_npcs]
    assert [npc["gender"] for npc in first_npcs] == [npc["gender"] for npc in second_npcs]
    assert [npc["appearance"] for npc in first_npcs] == [npc["appearance"] for npc in second_npcs]
    assert first_npcs[0]["gender"]
    assert {npc["gender"] for npc in first_npcs}.issubset({"Male", "Female"})
    assert first_npcs[0]["appearance"]
    assert first_npcs[0]["stats"]["health"] > 0
    assert first_npcs[0]["stats"]["stats"]["grit"] >= 1
    assert "personality" not in first_npcs[0]
    assert "backstory" not in first_npcs[0]
    assert "flirtReceptiveness" not in first_npcs[0]
    assert "flirtStyle" not in first_npcs[0]
    with connect_db(db_path) as db:
        row = db.execute(
            "SELECT personality, backstory, flirt_receptiveness, flirt_style FROM npc_profiles WHERE id = ?",
            (first_npcs[0]["id"],),
        ).fetchone()
    assert row["personality"]
    assert row["backstory"]
    assert row["flirt_receptiveness"] >= 0
    assert row["flirt_style"] != "unassigned"


def test_selected_npc_description_is_llm_enhanced_once(tmp_path):
    app, db_path = make_app(tmp_path)
    client = app.test_client()
    register(client, "captain")
    client.post("/api/comms/settings", json={"baseUrl": "mock://local", "model": "mock-model"})

    context = client.get("/api/comms/context").get_json()
    selected = next(npc for npc in context["nearbyNpcs"] if npc["id"] == context["selectedNpcId"])
    local_npcs = [npc for npc in context["nearbyNpcs"] if npc["kind"] == "npc"]

    assert selected["descriptionSource"] == "llm"
    assert "LLM-tuned profile" in selected["appearance"]
    assert any(npc["descriptionSource"] == "procedural" for npc in local_npcs if npc["id"] != selected["id"])

    refreshed = client.get(f"/api/comms/context?npcId={selected['id']}").get_json()
    refreshed_selected = next(npc for npc in refreshed["nearbyNpcs"] if npc["id"] == selected["id"])

    assert refreshed_selected["appearance"] == selected["appearance"]
    with connect_db(db_path) as db:
        enhanced_rows = db.execute(
            "SELECT id, description_source FROM npc_profiles WHERE kind = 'npc' AND description_source = 'llm'"
        ).fetchall()
    assert [row["id"] for row in enhanced_rows] == [selected["id"]]


def test_npc_description_parser_rejects_prompt_leakage():
    leaked = (
        "The user wants an NPC description for a character named Lio Hale. "
        "Constraints: Return strict JSON format and do not reveal hidden data."
    )

    with pytest.raises(RuntimeError):
        parse_generated_appearance(leaked, "fallback appearance")


def test_comms_context_includes_player_ship_ai_contact(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "captain")

    npcs = client.get("/api/comms/context").get_json()["nearbyNpcs"]
    ship_ai = next(npc for npc in npcs if npc["kind"] == "ship_ai")

    assert ship_ai["name"] == "Peregrine Factory AI"
    assert ship_ai["role"] == "Ship AI"
    assert ship_ai["gender"] == "Female"


def test_ship_ai_contact_uses_locked_player_imprint(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "captain")
    client.post(
        "/api/action",
        json={
            "action": "configure_ship_ai",
            "name": "Selene",
            "gender": "Male",
            "description": "Friendly, flirtatious, dryly funny, protective, and fond of practical ship advice.",
        },
    )

    npcs = client.get("/api/comms/context").get_json()["nearbyNpcs"]
    ship_ai = next(npc for npc in npcs if npc["kind"] == "ship_ai")

    assert ship_ai["name"] == "Selene"
    assert ship_ai["gender"] == "Male"
    assert "flirtatious" in ship_ai["appearance"]


def test_npc_profile_migration_adds_visible_and_hidden_character_columns(tmp_path):
    db_path = tmp_path / "old-spacesim.sqlite3"
    with connect_db(db_path) as db:
        db.executescript(
            """
            CREATE TABLE npc_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                world_id TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                npc_key TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                faction TEXT NOT NULL,
                personality TEXT NOT NULL,
                public_notes TEXT NOT NULL,
                seed TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(world_id, scope_key, npc_key)
            );
            """
        )

    init_db(db_path)

    with connect_db(db_path) as db:
        columns = {row["name"] for row in db.execute("PRAGMA table_info(npc_profiles)").fetchall()}
    assert {
        "gender",
        "appearance",
        "description_source",
        "description_generated_at",
        "backstory",
        "kind",
        "flirt_receptiveness",
        "flirt_style",
        "stats_json",
    }.issubset(columns)


def test_player_state_includes_captain_vitals(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "captain")

    state = client.get("/api/state").get_json()

    assert state["player"]["health"] == 100
    assert state["player"]["maxHealth"] == 100
    assert state["player"]["stats"]["piloting"] >= 1


def test_roleplay_message_metadata_splits_speech_and_actions(tmp_path, monkeypatch):
    def fake_llm(_settings, _messages):
        return json.dumps(
            {
                "actionText": "The broker ducks behind the counter and hits the panic stud.",
                "speech": "Easy. Put that away before station security vents your docking privileges.",
                "action": None,
            }
        )

    monkeypatch.setattr("comms.call_llm", fake_llm)
    app, db_path = make_app(tmp_path)
    client = app.test_client()
    register(client, "captain")
    client.post("/api/comms/settings", json={"baseUrl": "mock://local", "model": "mock-model"})
    npc = client.get("/api/comms/context").get_json()["nearbyNpcs"][0]

    response = client.post(
        "/api/comms/message",
        json={"channel": "npc", "npcId": npc["id"], "body": "*I draw a blaster* Hands up."},
    )
    body = response.get_json()
    messages = body["context"]["messages"]["npc"]
    player_message = next(message for message in messages if message["senderKind"] == "player")
    npc_message = next(message for message in messages if message["senderKind"] == "npc")

    assert response.status_code == 200
    assert player_message["metadata"]["actionText"] == "I draw a blaster"
    assert player_message["metadata"]["speechText"] == "Hands up."
    assert npc_message["metadata"]["actionText"].startswith("The broker ducks")
    assert npc_message["metadata"]["speechText"].startswith("Easy.")


def test_ship_diagnostics_are_disclosed_on_request_without_cargo_manifest():
    game = create_game()
    game["hull"] = 64
    game["inventory"]["relics"] = 3
    npc = {
        "name": "Niko Rusk",
        "role": "Mechanic",
        "faction": "Free Dockyards",
        "kind": "npc",
        "gender": "Female",
        "appearance": "Grease-marked coveralls.",
        "personality": "practical",
        "backstory": "Knows her way around station repair gantries.",
        "flirt_receptiveness": 2,
        "flirt_style": "warm; responds well to respectful flirtation",
        "public_notes": "Works near the repair gantry.",
    }

    prompt = build_prompt({"username": "Tbone"}, game, npc, [], "", "give me an assessment of my ship systems")
    payload = json.loads(prompt[-1]["content"])
    ship_intel = payload["shipIntel"]

    assert ship_intel["diagnosticsDisclosed"] is True
    assert ship_intel["privateManifest"] == "withheld"
    assert ship_intel["diagnostics"]["systems"]
    assert "relic" not in json.dumps(ship_intel).lower()


def test_external_npc_does_not_get_diagnostics_until_requested():
    game = create_game()
    npc = {
        "name": "Niko Rusk",
        "role": "Mechanic",
        "faction": "Free Dockyards",
        "kind": "npc",
        "gender": "Female",
        "appearance": "Grease-marked coveralls.",
        "personality": "practical",
        "backstory": "Knows her way around station repair gantries.",
        "flirt_receptiveness": 1,
        "flirt_style": "reserved",
        "public_notes": "Works near the repair gantry.",
    }

    prompt = build_prompt({"username": "Tbone"}, game, npc, [], "", "hello there")
    payload = json.loads(prompt[-1]["content"])

    assert payload["shipIntel"]["diagnosticsDisclosed"] is False
    assert payload["shipIntel"]["diagnostics"].startswith("Not provided")


def test_ship_ai_prompt_gets_private_manifest_and_diagnostics():
    game = create_game()
    game["inventory"]["relics"] = 2
    ai = {
        "name": "Peregrine Ship AI",
        "role": "Ship AI",
        "faction": "Peregrine",
        "kind": "ship_ai",
        "gender": "Female",
        "appearance": "Wireframe avatar.",
        "personality": "calm",
        "backstory": "Bound to ship telemetry.",
        "flirt_receptiveness": 1,
        "flirt_style": "literal but lightly amused",
        "public_notes": "Onboard AI.",
    }

    prompt = build_prompt({"username": "Tbone"}, game, ai, [], "", "assess my ship systems and cargo manifest")
    payload = json.loads(prompt[-1]["content"])

    assert payload["shipIntel"]["diagnosticsDisclosed"] is True
    assert payload["shipIntel"]["privateManifest"][0]["name"] == "Relics"


def test_ship_ai_prompt_keeps_diagnostics_out_of_casual_chat():
    game = create_game()
    ai = {
        "name": "Peregrine Ship AI",
        "role": "Ship AI",
        "faction": "Peregrine",
        "kind": "ship_ai",
        "gender": "Female",
        "appearance": "Wireframe avatar.",
        "personality": "calm",
        "backstory": "Bound to ship telemetry.",
        "flirt_receptiveness": 1,
        "flirt_style": "literal but lightly amused",
        "public_notes": "Onboard AI.",
    }

    prompt = build_prompt({"username": "Tbone"}, game, ai, [], "", "hello")
    payload = json.loads(prompt[-1]["content"])

    assert payload["shipIntel"]["diagnosticsDisclosed"] is False
    assert payload["shipIntel"]["privateManifest"] == "withheld until requested"


def test_prompt_includes_authoritative_navigation_context():
    game = create_game()
    state = public_state(game)
    ai = {
        "name": "Peregrine Ship AI",
        "role": "Ship AI",
        "faction": "Peregrine",
        "kind": "ship_ai",
        "gender": "Female",
        "appearance": "Wireframe avatar.",
        "personality": "calm",
        "backstory": "Bound to ship telemetry.",
        "flirt_receptiveness": 1,
        "flirt_style": "literal but lightly amused",
        "public_notes": "Onboard AI.",
    }

    prompt = build_prompt({"username": "Tbone"}, game, ai, [], "", "what systems are near me?")
    payload = json.loads(prompt[-1]["content"])
    nav = payload["navigationContext"]

    assert nav["currentSystem"]["name"] == state["currentSystem"]["name"]
    assert [route["name"] for route in nav["routesFromCurrentSystem"]] == [route["name"] for route in state["travel"]]
    assert "use only the names and facts" in nav["instruction"]
    assert all(route["id"] for route in nav["routesFromCurrentSystem"])


def test_llm_wait_action_is_ignored_without_explicit_wait_request(tmp_path, monkeypatch):
    def fake_llm(_settings, _messages):
        return json.dumps(
            {
                "reply": "Here are the nearby systems from your chart.",
                "action": {"action": "wait", "payload": {}, "summary": "Wait one day"},
            }
        )

    monkeypatch.setattr("comms.call_llm", fake_llm)
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "captain")
    client.post("/api/comms/settings", json={"baseUrl": "mock://local", "model": "mock-model"})
    npc = client.get("/api/comms/context").get_json()["nearbyNpcs"][0]

    response = client.post(
        "/api/comms/message",
        json={"channel": "npc", "npcId": npc["id"], "body": "What systems are nearby?"},
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["pendingAction"] is None
    assert body["context"]["pendingActions"] == []
    assert "Wait is only queued" in body["reply"]


def test_global_messages_are_visible_to_other_players(tmp_path):
    app, _ = make_app(tmp_path)
    first = app.test_client()
    second = app.test_client()
    register(first, "alpha")
    register(second, "beta")

    sent = first.post("/api/social/messages", json={"channel": "global", "body": "Anyone reading?"})
    messages = second.get("/api/social/messages?channel=global").get_json()["messages"]

    assert sent.status_code == 200
    assert any(message["body"] == "Anyone reading?" and message["senderName"] == "alpha" for message in messages)


def test_dm_messages_are_only_in_participant_channel(tmp_path):
    app, _ = make_app(tmp_path)
    first = app.test_client()
    second = app.test_client()
    third = app.test_client()
    register(first, "alpha")
    register(second, "beta")
    register(third, "gamma")

    first.post("/api/social/messages", json={"channel": "dm", "username": "beta", "body": "private ping"})
    beta_view = second.get("/api/social/messages?channel=dm&username=alpha").get_json()["messages"]
    gamma_view = third.get("/api/social/messages?channel=dm&username=alpha").get_json()["messages"]

    assert any(message["body"] == "private ping" for message in beta_view)
    assert all(message["body"] != "private ping" for message in gamma_view)


def test_group_messages_enforce_membership(tmp_path):
    app, _ = make_app(tmp_path)
    first = app.test_client()
    second = app.test_client()
    register(first, "alpha")
    register(second, "beta")

    group = first.post("/api/social/groups", json={"name": "Bridge Crew"}).get_json()["groups"][0]
    sent = first.post("/api/social/messages", json={"channel": "group", "groupId": group["id"], "body": "group ping"})
    blocked = second.get(f"/api/social/messages?channel=group&groupId={group['id']}")

    assert sent.status_code == 200
    assert blocked.status_code == 403


def test_mock_npc_action_requires_confirmation_and_uses_game_rules(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "admin")
    client.post("/api/comms/settings", json={"baseUrl": "mock://local", "model": "mock-model"})
    npc = client.get("/api/comms/context").get_json()["nearbyNpcs"][0]

    response = client.post(
        "/api/comms/message",
        json={"channel": "npc", "npcId": npc["id"], "body": "Please wait one day for me."},
    )
    body = response.get_json()
    pending = body["pendingAction"]

    assert response.status_code == 200
    assert pending["action"] == "wait"
    assert body["state"]["day"] == 1

    confirmed = client.post("/api/comms/confirm", json={"actionId": pending["id"]}).get_json()

    assert confirmed["state"]["day"] == 2
    assert "maintenance day" in confirmed["message"]


def test_duplicate_pending_actions_are_not_stacked(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "admin")
    client.post("/api/comms/settings", json={"baseUrl": "mock://local", "model": "mock-model"})
    npc = client.get("/api/comms/context").get_json()["nearbyNpcs"][0]

    first = client.post(
        "/api/comms/message",
        json={"channel": "npc", "npcId": npc["id"], "body": "Please wait one day for me."},
    ).get_json()
    second = client.post(
        "/api/comms/message",
        json={"channel": "npc", "npcId": npc["id"], "body": "Please wait one day for me."},
    ).get_json()

    assert second["pendingAction"]["id"] == first["pendingAction"]["id"]
    assert [action["id"] for action in second["context"]["pendingActions"]] == [first["pendingAction"]["id"]]


def test_chat_completions_url_accepts_lm_studio_root_or_v1_base():
    assert chat_completions_url("http://localhost:1234") == "http://localhost:1234/v1/chat/completions"
    assert chat_completions_url("http://localhost:1234/v1") == "http://localhost:1234/v1/chat/completions"
    assert (
        chat_completions_url("http://localhost:1234/v1/chat/completions")
        == "http://localhost:1234/v1/chat/completions"
    )


def test_personal_notes_are_private_per_user_and_target(tmp_path):
    app, _ = make_app(tmp_path)
    first = app.test_client()
    second = app.test_client()
    register(first, "alpha")
    register(second, "beta")

    saved = first.post(
        "/api/notes",
        json={
            "targetType": "npc",
            "targetId": "42",
            "title": "Quartermaster",
            "body": "Trust but verify the docking fees.",
        },
    )
    first_note = first.get("/api/notes?targetType=npc&targetId=42").get_json()["note"]
    second_note = second.get("/api/notes?targetType=npc&targetId=42").get_json()["note"]

    assert saved.status_code == 200
    assert first_note["title"] == "Quartermaster"
    assert first_note["body"] == "Trust but verify the docking fees."
    assert second_note["title"] == ""
    assert second_note["body"] == ""


def test_personal_notes_support_location_targets(tmp_path):
    app, _ = make_app(tmp_path)
    client = app.test_client()
    register(client, "alpha")
    state = client.get("/api/state").get_json()

    response = client.post(
        "/api/notes",
        json={
            "targetType": "place",
            "targetId": state["currentPlace"]["id"],
            "title": "Docking collar",
            "body": "Good place to check refuel options.",
        },
    )
    loaded = client.get(f"/api/notes?targetType=place&targetId={state['currentPlace']['id']}").get_json()["note"]

    assert response.status_code == 200
    assert loaded["targetId"] == state["currentPlace"]["id"]
    assert "refuel" in loaded["body"]
