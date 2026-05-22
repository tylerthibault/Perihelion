from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, Response, jsonify, render_template, request, send_file, session, stream_with_context

from comms import (
    comms_context,
    comms_status,
    confirm_pending_action,
    ensure_nearby_npcs,
    handle_comms_message,
    stream_npc_reply,
    visible_messages_for_social,
)
from spacesim import apply_action, create_game, public_state
from storage import (
    add_friendship,
    add_group_member,
    connect_db,
    create_group,
    create_user,
    get_user,
    get_user_by_username,
    init_db,
    list_friendships,
    list_groups,
    list_personal_notes,
    list_pending_actions,
    load_player_state,
    provider_settings,
    public_user,
    get_personal_note,
    save_player_state,
    save_personal_note,
    save_provider_settings,
    verify_user,
)
import tts


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-space-sim-key"),
        DATABASE=os.environ.get("SPACESIM_DB", str(Path("perihelion.sqlite3"))),
        TTS_CACHE_DIR=os.environ.get("SPACESIM_TTS_CACHE", ""),
    )
    if config:
        app.config.update(config)
    if not app.config["TTS_CACHE_DIR"]:
        app.config["TTS_CACHE_DIR"] = str(Path(app.instance_path) / "tts_cache")
    init_db(app.config["DATABASE"])

    @app.after_request
    def add_coop_coep_headers(response):
        """Required for SharedArrayBuffer used by kokoro-js ONNX runtime."""
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"
        return response

    def db_connection() -> sqlite3.Connection:
        return connect_db(app.config["DATABASE"])

    def current_user(db: sqlite3.Connection) -> dict[str, Any] | None:
        return get_user(db, session.get("user_id"))

    def load_game_for_user(db: sqlite3.Connection, user: dict[str, Any]) -> dict[str, Any]:
        game = load_player_state(db, user["id"])
        if game is None:
            game = create_game()
            save_player_state(db, user["id"], game)
        return game

    def state_payload(
        db: sqlite3.Connection,
        user: dict[str, Any] | None,
        game: dict[str, Any],
        message: str | None = None,
    ) -> dict[str, Any]:
        payload = public_state(game)
        payload["user"] = public_user(user)
        payload["authRequired"] = user is None
        payload["commsStatus"] = comms_status(db)
        payload["nearbyNpcs"] = ensure_nearby_npcs(db, game, user["id"]) if user else []
        payload["pendingCommsActions"] = list_pending_actions(db, user["id"]) if user else []
        if message:
            payload["message"] = message
        return payload

    def require_user(db: sqlite3.Connection) -> tuple[dict[str, Any] | None, Any | None]:
        user = current_user(db)
        if not user:
            return None, (jsonify({"message": "Log in or register before using the ship console."}), 401)
        return user, None

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/state")
    def state():
        with db_connection() as db:
            user = current_user(db)
            game = load_game_for_user(db, user) if user else create_game()
            return jsonify(state_payload(db, user, game))

    @app.post("/api/action")
    def action():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error

            if payload.get("action") == "new_game":
                game = create_game()
                message = "New captain registered. The Peregrine is ready at Aurora Station."
            else:
                game = load_game_for_user(db, user)
                game, message = apply_action(game, payload.get("action"), payload)

            save_player_state(db, user["id"], game)
            return jsonify(state_payload(db, user, game, message))

    @app.post("/api/auth/register")
    def register():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            try:
                user = create_user(db, str(payload.get("username") or ""), str(payload.get("password") or ""))
            except sqlite3.IntegrityError:
                return jsonify({"message": "That username is already registered."}), 409
            except ValueError as error:
                return jsonify({"message": str(error)}), 400
            session["user_id"] = user["id"]
            game = create_game()
            save_player_state(db, user["id"], game)
            return jsonify(state_payload(db, user, game, f"Welcome aboard, {user['username']}.")), 201

    @app.post("/api/auth/login")
    def login():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user = verify_user(db, str(payload.get("username") or ""), str(payload.get("password") or ""))
            if not user:
                return jsonify({"message": "Username or password did not match."}), 401
            session["user_id"] = user["id"]
            game = load_game_for_user(db, user)
            return jsonify(state_payload(db, user, game, f"Logged in as {user['username']}."))

    @app.post("/api/auth/logout")
    def logout():
        session.clear()
        return jsonify({"user": None, "message": "Logged out."})

    @app.get("/api/auth/me")
    def me():
        with db_connection() as db:
            user = current_user(db)
            return jsonify({"user": public_user(user)})

    @app.get("/api/comms/context")
    def comms_context_route():
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            game = load_game_for_user(db, user)
            try:
                selected_npc_id = int(request.args.get("npcId") or 0) or None
            except ValueError:
                selected_npc_id = None
            return jsonify(comms_context(db, user, game, selected_npc_id))

    @app.post("/api/comms/stream")
    def comms_stream_route():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            game = load_game_for_user(db, user)

        def generate():
            with db_connection() as db:
                yield from stream_npc_reply(db, user, game, payload)

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/api/comms/message")
    def comms_message_route():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            game = load_game_for_user(db, user)
            game, response, status = handle_comms_message(db, user, game, payload)
            save_player_state(db, user["id"], game)
            response["state"] = state_payload(db, user, game)
            return jsonify(response), status

    @app.post("/api/comms/confirm")
    def comms_confirm_route():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            game = load_game_for_user(db, user)
            game, response, status = confirm_pending_action(db, user, game, int(payload.get("actionId") or 0))
            save_player_state(db, user["id"], game)
            response["state"] = state_payload(db, user, game)
            return jsonify(response), status

    @app.get("/api/comms/settings")
    def get_comms_settings():
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            return jsonify({"provider": provider_settings(db, public=True), "user": public_user(user)})

    @app.post("/api/comms/settings")
    def update_comms_settings():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            if not user["is_admin"]:
                return jsonify({"message": "Only the first/admin account can change provider settings."}), 403
            settings = save_provider_settings(db, payload)
            return jsonify({"provider": settings, "message": "Comms provider settings saved."})

    @app.get("/api/tts/status")
    def tts_status_route():
        with db_connection() as db:
            _, error = require_user(db)
            if error:
                return error
            return jsonify(tts.tts_status(app.config["TTS_CACHE_DIR"]))

    @app.post("/api/tts/speak")
    def tts_speak_route():
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text") or "")
        npc = payload.get("npc") if isinstance(payload.get("npc"), dict) else {}
        with db_connection() as db:
            _, error = require_user(db)
            if error:
                return error
            try:
                result = tts.synthesize_tts(text, npc, app.config["TTS_CACHE_DIR"])
            except ValueError as error:
                return jsonify({"message": str(error), "fallbackProvider": "browser"}), 400
            except tts.TTSUnavailable as error:
                return jsonify({"message": str(error), "fallbackProvider": "browser"}), 503
            result["audioUrl"] = f"/api/tts/audio/{result['filename']}"
            result["fallbackProvider"] = "browser"
            return jsonify(result)

    @app.get("/api/tts/audio/<filename>")
    def tts_audio_route(filename: str):
        with db_connection() as db:
            _, error = require_user(db)
            if error:
                return error
            if not tts.valid_audio_filename(filename):
                return jsonify({"message": "Audio cache entry not found."}), 404
            audio_path = Path(app.config["TTS_CACHE_DIR"]) / filename
            if not audio_path.exists():
                return jsonify({"message": "Audio cache entry not found."}), 404
            return send_file(audio_path, mimetype="audio/wav", conditional=True)

    @app.get("/api/notes")
    def get_note():
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            target_type = str(request.args.get("targetType") or "")
            target_id = str(request.args.get("targetId") or "")
            if not target_type and not target_id:
                return jsonify({"notes": list_personal_notes(db, user["id"])})
            try:
                note = get_personal_note(db, user["id"], target_type, target_id)
            except ValueError as error:
                return jsonify({"message": str(error)}), 400
            return jsonify({"note": note})

    @app.post("/api/notes")
    def save_note():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            try:
                note = save_personal_note(
                    db,
                    user["id"],
                    str(payload.get("targetType") or ""),
                    str(payload.get("targetId") or ""),
                    str(payload.get("title") or ""),
                    str(payload.get("body") or ""),
                )
            except ValueError as error:
                return jsonify({"message": str(error)}), 400
            return jsonify({"note": note, "message": "Private note saved."})

    @app.get("/api/social/messages")
    def social_messages():
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            game = load_game_for_user(db, user)
            messages, status = visible_messages_for_social(db, user, game, request.args.get("channel", "global"), request.args)
            if status == 403:
                return jsonify({"message": "You are not allowed to view that channel."}), 403
            if status == 404:
                return jsonify({"message": "That user or channel was not found."}), 404
            if status != 200:
                return jsonify({"message": "Unknown social channel."}), 400
            return jsonify({"messages": messages})

    @app.post("/api/social/messages")
    def send_social_message():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            game = load_game_for_user(db, user)
            game, response, status = handle_comms_message(db, user, game, payload)
            save_player_state(db, user["id"], game)
            return jsonify(response), status

    @app.get("/api/social/friends")
    def get_friends():
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            return jsonify({"friends": list_friendships(db, user["id"])})

    @app.post("/api/social/friends")
    def post_friend():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            friend = get_user_by_username(db, str(payload.get("username") or ""))
            if not friend:
                return jsonify({"message": "No registered player uses that username."}), 404
            try:
                add_friendship(db, user["id"], friend["id"])
            except ValueError as error:
                return jsonify({"message": str(error)}), 400
            return jsonify({"friends": list_friendships(db, user["id"]), "message": f"{friend['username']} added."})

    @app.get("/api/social/groups")
    def get_groups_route():
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            return jsonify({"groups": list_groups(db, user["id"])})

    @app.post("/api/social/groups")
    def post_group():
        payload = request.get_json(silent=True) or {}
        with db_connection() as db:
            user, error = require_user(db)
            if error:
                return error
            try:
                group = create_group(db, user["id"], str(payload.get("name") or ""))
            except ValueError as error:
                return jsonify({"message": str(error)}), 400
            for username in payload.get("members") or []:
                member = get_user_by_username(db, str(username))
                if member:
                    add_group_member(db, group["id"], member["id"])
            return jsonify({"groups": list_groups(db, user["id"]), "message": f"Group {group['name']} created."}), 201

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    create_app().run(host="127.0.0.1", port=port, debug=True)

app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5399, host="0.0.0.0")
