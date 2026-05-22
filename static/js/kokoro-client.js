/**
 * Browser-side Kokoro TTS (kokoro-js via WebGPU / WASM fallback).
 * Loaded as an ES module. Exposes window.kokoroBrowser.
 *
 * The model (~80 MB quantised) is downloaded from Hugging Face on first use
 * and cached in the browser's Cache API automatically by the ONNX runtime.
 */

const MODEL_ID = "onnx-community/Kokoro-82M-v1.0";

// Voice lists mirror tts.py
const FEMALE_VOICES = [
  "af_heart", "af_bella", "af_nicole", "af_sarah",
  "af_sky", "af_nova", "af_river", "af_jessica",
  "af_aoede", "af_kore",
];
const MALE_VOICES = [
  "am_adam", "am_echo", "am_eric", "am_fenrir",
  "am_liam", "am_michael", "am_onyx", "am_puck",
];

function simpleHash(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  }
  return Math.abs(h);
}

function voiceForNpc(npc) {
  const pool = (npc.gender || "").toLowerCase() === "male" ? MALE_VOICES : FEMALE_VOICES;
  const key = `${npc.id}:${npc.name}:${npc.gender}:${npc.role}`;
  return pool[simpleHash(key) % pool.length];
}

// ── pipeline lifecycle ────────────────────────────────────────────────────────

let _pipeline = null;
let _initPromise = null;
let _state = "idle"; // "idle" | "loading" | "ready" | "error"
let _audioCtx = null;

function getAudioContext() {
  if (!_audioCtx || _audioCtx.state === "closed") {
    _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return _audioCtx;
}

async function loadPipeline() {
  _state = "loading";
  const { KokoroTTS } = await import("https://esm.sh/kokoro-js@1.2.2");
  const devices = typeof navigator.gpu !== "undefined" ? ["webgpu", "wasm"] : ["wasm"];
  let lastErr;
  for (const device of devices) {
    try {
      console.log(`[kokoro-client] trying device: ${device}`);
      const tts = await KokoroTTS.from_pretrained(MODEL_ID, {
        dtype: { model: "q8", embeddings: "fp32" },
        device,
      });
      _pipeline = tts;
      _state = "ready";
      console.log(`[kokoro-client] ready on ${device}`);
      return tts;
    } catch (err) {
      console.warn(`[kokoro-client] ${device} failed:`, err);
      lastErr = err;
    }
  }
  _state = "error";
  throw lastErr;
}

function prime() {
  if (!_initPromise) {
    _initPromise = loadPipeline().catch((err) => {
      _initPromise = null; // allow retry
      throw err;
    });
  }
  return _initPromise;
}

// ── speak ─────────────────────────────────────────────────────────────────────

async function speak(text, npc) {
  const tts = await prime();
  const voice = voiceForNpc(npc || {});
  const result = await tts.generate(text, { voice });

  // result is { audio: Float32Array, sampling_rate: number }
  const samples = Float32Array.from(result.audio ?? result.data ?? result);
  const sr = result.sampling_rate ?? 24000;

  const ctx = getAudioContext();
  if (ctx.state === "suspended") {
    await ctx.resume();
  }

  const buffer = ctx.createBuffer(1, samples.length, sr);
  buffer.copyToChannel(samples, 0);

  return new Promise((resolve, reject) => {
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(ctx.destination);
    src.onended = resolve;
    src.onerror = reject;
    src.start(0);
  });
}

// ── public API ────────────────────────────────────────────────────────────────

window.kokoroBrowser = {
  /** Pre-warm the model download without speaking yet. */
  prime,
  /** Speak text aloud for a given npc object. Returns a Promise. */
  speak,
  /** "idle" | "loading" | "ready" | "error" */
  getState: () => _state,
};

// Start loading immediately so the model is warm before the first message.
prime().catch(() => {/* silently degrade to browser speech */});
