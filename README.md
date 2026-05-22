# Perihelion

A Flask-powered text-based space sim played through a browser console.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m flask --app app run --host 127.0.0.1 --port 5000
```

Open <http://127.0.0.1:5000>.

## Optional neural NPC voices

NPC voice playback tries Kokoro first, then falls back to browser speech if Kokoro is not available.
Kokoro currently supports Python 3.10-3.12, so use one of those Python versions for neural voices.

```bash
.venv/bin/python -m pip install -r requirements-tts.txt
```

Kokoro also needs `espeak-ng` available on the machine. On macOS:

```bash
brew install espeak-ng
```

Generated voice lines are cached under `instance/tts_cache` by default. Set `SPACESIM_TTS_CACHE` to use another cache directory.

## Test

```bash
.venv/bin/python -m pytest -q
```

## Project layout

- `app.py` contains the Flask routes.
- `spacesim.py` contains the simulation rules, markets, missions, and travel events.
- `templates/index.html` is the main game screen.
- `static/css/styles.css` and `static/js/game.js` render the browser UI.

## Current mechanics

- Each star system has a persistent station with multiple named areas.
- Station areas can have different controlling factions, wealth levels, economies, and security.
- Each system also has planets with thousands of deterministic visitable places.
- Planet places are generated from stable seeds, so place `#1274` on the same planet is the same place every time.
- The game remembers which local places you have visited during the run.
