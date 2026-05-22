const stateUrl = "/api/state";
const actionUrl = "/api/action";
const authUrls = {
  register: "/api/auth/register",
  login: "/api/auth/login",
  logout: "/api/auth/logout",
};
const commsUrls = {
  context: "/api/comms/context",
  message: "/api/comms/message",
  stream: "/api/comms/stream",
  confirm: "/api/comms/confirm",
  settings: "/api/comms/settings",
  ttsStatus: "/api/tts/status",
  ttsSpeak: "/api/tts/speak",
  socialMessages: "/api/social/messages",
  friends: "/api/social/friends",
  groups: "/api/social/groups",
};
const notesUrl = "/api/notes";

const els = {
  breadcrumbTrail: document.querySelector("#breadcrumbTrail"),
  shipName: document.querySelector("#shipName"),
  status: document.querySelector("#status"),
  travelState: document.querySelector("#travelState"),
  credits: document.querySelector("#credits"),
  fuel: document.querySelector("#fuel"),
  hull: document.querySelector("#hull"),
  cargo: document.querySelector("#cargo"),
  courseStatus: document.querySelector("#courseStatus"),
  userBadge: document.querySelector("#userBadge"),
  notesButton: document.querySelector("#notesButton"),
  commsButton: document.querySelector("#commsButton"),
  logoutButton: document.querySelector("#logoutButton"),
  authOverlay: document.querySelector("#authOverlay"),
  authUsername: document.querySelector("#authUsername"),
  authPassword: document.querySelector("#authPassword"),
  authMessage: document.querySelector("#authMessage"),
  loginButton: document.querySelector("#loginButton"),
  registerButton: document.querySelector("#registerButton"),
  commsOverlay: document.querySelector("#commsOverlay"),
  commsCloseButton: document.querySelector("#commsCloseButton"),
  commsProviderNotice: document.querySelector("#commsProviderNotice"),
  commsTabs: document.querySelector("#commsTabs"),
  commsNpcList: document.querySelector("#commsNpcList"),
  commsSocialTools: document.querySelector("#commsSocialTools"),
  commsSelectedContext: document.querySelector("#commsSelectedContext"),
  pendingCommsActions: document.querySelector("#pendingCommsActions"),
  commsMessages: document.querySelector("#commsMessages"),
  commsForm: document.querySelector("#commsForm"),
  commsInput: document.querySelector("#commsInput"),
  commsSendButton: document.querySelector("#commsSendButton"),
  notesOverlay: document.querySelector("#notesOverlay"),
  notesCloseButton: document.querySelector("#notesCloseButton"),
  noteTargetTabs: document.querySelector("#noteTargetTabs"),
  noteTitle: document.querySelector("#noteTitle"),
  noteBody: document.querySelector("#noteBody"),
  saveNoteButton: document.querySelector("#saveNoteButton"),
  noteStatus: document.querySelector("#noteStatus"),
  settingsButton: document.querySelector("#settingsButton"),
  settingsOverlay: document.querySelector("#settingsOverlay"),
  settingsCloseButton: document.querySelector("#settingsCloseButton"),
  cheatList: document.querySelector("#cheatList"),
  providerSettings: document.querySelector("#providerSettings"),
  llmBaseUrl: document.querySelector("#llmBaseUrl"),
  llmModel: document.querySelector("#llmModel"),
  llmApiKey: document.querySelector("#llmApiKey"),
  saveProviderButton: document.querySelector("#saveProviderButton"),
  providerStatus: document.querySelector("#providerStatus"),
  systemName: document.querySelector("#systemName"),
  systemDescription: document.querySelector("#systemDescription"),
  systemFaction: document.querySelector("#systemFaction"),
  systemEconomy: document.querySelector("#systemEconomy"),
  systemRisk: document.querySelector("#systemRisk"),
  currentPlace: document.querySelector("#currentPlace"),
  visitedPlaceBadge: document.querySelector("#visitedPlaceBadge"),
  localTargets: document.querySelector("#localTargets"),
  localDetail: document.querySelector(".local-detail"),
  localTargetMeta: document.querySelector("#localTargetMeta"),
  localTargetTitle: document.querySelector("#localTargetTitle"),
  localTargetSummary: document.querySelector("#localTargetSummary"),
  localTargetActions: document.querySelector("#localTargetActions"),
  localSublocations: document.querySelector("#localSublocations"),
  navigationPanel: document.querySelector("#navigationPanel"),
  sectorMap: document.querySelector("#sectorMap"),
  systemDetails: document.querySelector("#systemDetails"),
  plottedCourse: document.querySelector("#plottedCourse"),
  gatePanel: document.querySelector("#gatePanel"),
  catalogDetail: document.querySelector("#catalogDetail"),
  zoomOutButton: document.querySelector("#zoomOutButton"),
  zoomInButton: document.querySelector("#zoomInButton"),
  fitGalaxyButton: document.querySelector("#fitGalaxyButton"),
  expandMapButton: document.querySelector("#expandMapButton"),
  zoomLevel: document.querySelector("#zoomLevel"),
  travelList: document.querySelector("#travelList"),
  missionList: document.querySelector("#missionList"),
  activeMission: document.querySelector("#activeMission"),
  marketContext: document.querySelector("#marketContext"),
  market: document.querySelector("#market"),
  inventory: document.querySelector("#inventory"),
  log: document.querySelector("#log"),
  dayBadge: document.querySelector("#dayBadge"),
  discoveryBadge: document.querySelector("#discoveryBadge"),
  exploreButtons: document.querySelectorAll(".explore-button"),
  refuelButton: document.querySelector("#refuelButton"),
  rescueButton: document.querySelector("#rescueButton"),
  repairButton: document.querySelector("#repairButton"),
  serviceHelp: document.querySelector("#serviceHelp"),
  shipSummary: document.querySelector("#shipSummary"),
  shipAiPanel: document.querySelector("#shipAiPanel"),
  upgradeList: document.querySelector("#upgradeList"),
  waitButton: document.querySelector("#waitButton"),
  newGameButton: document.querySelector("#newGameButton"),
  navButtons: document.querySelectorAll(".console-nav button"),
  viewPanels: document.querySelectorAll(".view"),
  localScopeTabs: document.querySelectorAll("#localScopeTabs button"),
  toastStack: document.querySelector("#toastStack"),
};

let currentState = null;
let activeView = "navigation";
let selectedLocalTarget = "station";
let localScope = "system";
let plottedCourseId = null;
let focusedSystemId = null;
let renderedLocation = null;
let mapExpanded = false;
let navigationMode = "routes";
let catalogSystemId = null;
let catalogPlanetId = null;
let toastCounter = 0;
let commsContext = null;
let activeCommsChannel = "npc";
let selectedNpcId = null;
let commsPollTimer = null;
let socialMessages = [];
let currentNoteTarget = null;
const npcVoiceStorageKey = "starless-drift-npc-voice-enabled";
let npcVoiceEnabled = storageGet(npcVoiceStorageKey) === "true";
let speechVoices = [];
let lastSpokenNpcMessageId = null;
const npcAudioPlayer = new Audio();
let ttsStatus = null;
const galaxySize = { width: 1000, height: 700 };
const mapChart = {
  zoom: 1,
  panX: 0,
  panY: 0,
  fitted: false,
  dragging: false,
  dragStartX: 0,
  dragStartY: 0,
  dragPanX: 0,
  dragPanY: 0,
};

async function fetchState() {
  try {
    const response = await fetch(stateUrl);
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }
    currentState = await response.json();
    render(currentState);
    if (currentState.authRequired) {
      openAuth("Create or login to start saving this run.");
    } else {
      closeAuth();
    }
  } catch (error) {
    console.error(error);
    showToast("Initial load failed. Check that the Flask server is running and refresh the page.", "danger");
  }
}

async function sendAction(payload) {
  setBusy(true);
  try {
    const response = await fetch(actionUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const responseBody = await readJson(response);
    if (!response.ok) {
      if (response.status === 401) {
        openAuth(responseBody.message);
      }
      showToast(responseBody.message || `Server returned ${response.status}`, "warning");
      return;
    }
    currentState = responseBody;
    if (currentState.message) {
      showToast(currentState.message, toastTone(currentState.message));
    }
  } catch (error) {
    console.error(error);
    showToast("Command failed. The console could not reach the ship computer.", "danger");
  } finally {
    setBusy(false);
  }
  if (currentState) {
    render(currentState);
  }
}

async function readJson(response) {
  try {
    return await response.json();
  } catch (error) {
    return {};
  }
}

function setBusy(isBusy) {
  document.querySelectorAll("button:not(.console-nav button)").forEach((button) => {
    button.disabled = isBusy;
  });
}

function showToast(message, tone = "info", title = null) {
  if (!message) {
    return;
  }
  const stack = els.toastStack || createToastStack();
  const toast = document.createElement("div");
  toast.className = `toast toast--${tone}`;
  toast.dataset.toastId = String(++toastCounter);
  const heading = document.createElement("strong");
  const body = document.createElement("span");
  heading.textContent = title || toastTitle(tone);
  body.textContent = message;
  toast.append(heading, body);
  stack.appendChild(toast);
  window.setTimeout(() => dismissToast(toast), 4200);
}

function createToastStack() {
  const stack = document.createElement("div");
  stack.className = "toast-stack";
  stack.id = "toastStack";
  stack.setAttribute("aria-live", "polite");
  stack.setAttribute("aria-atomic", "true");
  document.body.appendChild(stack);
  els.toastStack = stack;
  return stack;
}

function dismissToast(toast) {
  if (!toast || !toast.isConnected) {
    return;
  }
  toast.classList.add("is-leaving");
  window.setTimeout(() => toast.remove(), 180);
}

function toastTitle(tone) {
  if (tone === "warning") {
    return "Action blocked";
  }
  if (tone === "danger") {
    return "Console error";
  }
  if (tone === "success") {
    return "Confirmed";
  }
  return "Notice";
}

function toastTone(message) {
  const text = String(message).toLowerCase();
  if (
    text.includes("blocked") ||
    text.includes("cannot") ||
    text.includes("unavailable") ||
    text.includes("not enough") ||
    text.includes("insufficient") ||
    text.includes("missing") ||
    text.includes("rejected") ||
    text.includes("requires") ||
    text.includes("not been discovered")
  ) {
    return "warning";
  }
  if (
    text.includes("complete") ||
    text.includes("accepted") ||
    text.includes("installed") ||
    text.includes("purchased") ||
    text.includes("bought") ||
    text.includes("sold") ||
    text.includes("refueled") ||
    text.includes("repaired") ||
    text.includes("new captain")
  ) {
    return "success";
  }
  return "info";
}

function renderIdentity(state) {
  const user = state.user;
  els.userBadge.textContent = user ? user.username : "Guest";
  els.logoutButton.classList.toggle("is-hidden", !user);
  els.notesButton.disabled = !user;
  els.commsButton.disabled = !user;
  els.newGameButton.disabled = !user;
  if (els.providerSettings) {
    els.providerSettings.classList.toggle("is-hidden", !user?.isAdmin);
    if (!user?.isAdmin && els.providerStatus) {
      els.providerStatus.textContent = "Provider settings are available to the first/admin account.";
    }
  }
}

function openAuth(message = "") {
  if (!els.authOverlay) {
    return;
  }
  els.authOverlay.classList.remove("is-hidden");
  els.authMessage.textContent = message;
  window.setTimeout(() => els.authUsername?.focus(), 0);
}

function closeAuth() {
  els.authOverlay?.classList.add("is-hidden");
}

async function submitAuth(mode) {
  const username = els.authUsername.value.trim();
  const password = els.authPassword.value;
  if (!username || !password) {
    els.authMessage.textContent = "Username and password are required.";
    return;
  }
  els.authMessage.textContent = "Contacting registry...";
  try {
    const response = await fetch(authUrls[mode], {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const body = await readJson(response);
    if (!response.ok) {
      els.authMessage.textContent = body.message || "Access failed.";
      return;
    }
    currentState = body;
    closeAuth();
    render(currentState);
    showToast(body.message || "Captain access confirmed.", "success");
  } catch (error) {
    console.error(error);
    els.authMessage.textContent = "The account service did not answer.";
  }
}

async function logout() {
  try {
    const response = await fetch(authUrls.logout, { method: "POST" });
    const body = await readJson(response);
    closeComms();
    currentState = null;
    showToast(body.message || "Logged out.", "info");
    await fetchState();
  } catch (error) {
    console.error(error);
    showToast("Logout failed.", "danger");
  }
}

async function loadProviderSettings() {
  if (!currentState?.user?.isAdmin || !els.providerSettings) {
    return;
  }
  try {
    const response = await fetch(commsUrls.settings);
    const body = await readJson(response);
    if (!response.ok) {
      els.providerStatus.textContent = body.message || "Provider settings unavailable.";
      return;
    }
    const provider = body.provider || {};
    els.llmBaseUrl.value = provider.baseUrl || "";
    els.llmModel.value = provider.model || "";
    els.llmApiKey.value = "";
    els.llmApiKey.placeholder = provider.apiKeySet ? "Saved key is masked" : "Optional";
    els.providerStatus.textContent = provider.configured ? "Provider configured." : "Set a model name to enable NPC chat.";
  } catch (error) {
    console.error(error);
    els.providerStatus.textContent = "Could not load provider settings.";
  }
}

async function saveProviderSettings() {
  if (!currentState?.user?.isAdmin) {
    showToast("Only the first/admin account can change provider settings.", "warning");
    return;
  }
  const payload = {
    baseUrl: els.llmBaseUrl.value,
    model: els.llmModel.value,
  };
  if (els.llmApiKey.value) {
    payload.apiKey = els.llmApiKey.value;
  }
  try {
    const response = await fetch(commsUrls.settings, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await readJson(response);
    if (!response.ok) {
      showToast(body.message || "Provider settings were not saved.", "warning");
      return;
    }
    els.providerStatus.textContent = body.provider?.configured ? "Provider configured." : "Provider saved, but a model is still required.";
    showToast(body.message, "success");
    if (commsContext) {
      await refreshCommsContext();
    }
  } catch (error) {
    console.error(error);
    showToast("Provider settings failed to save.", "danger");
  }
}

async function openComms() {
  if (!currentState?.user) {
    openAuth("Login before opening Comms.");
    return;
  }
  els.commsOverlay.classList.remove("is-hidden");
  await Promise.all([refreshCommsContext(), refreshTtsStatus(false)]);
  startCommsPolling();
}

function closeComms() {
  els.commsOverlay?.classList.add("is-hidden");
  stopCommsPolling();
  stopNpcSpeech();
}

async function openNotes(target = null) {
  if (!currentState?.user) {
    openAuth("Login before opening private notes.");
    return;
  }
  els.notesOverlay.classList.remove("is-hidden");
  const targets = noteTargetOptions();
  currentNoteTarget = target || currentNoteTarget || targets[0] || null;
  if (currentNoteTarget && !targets.some((item) => noteTargetKey(item) === noteTargetKey(currentNoteTarget))) {
    targets.unshift(currentNoteTarget);
  }
  renderNoteTargets(targets);
  if (currentNoteTarget) {
    await loadNote(currentNoteTarget);
  }
}

function closeNotes() {
  els.notesOverlay?.classList.add("is-hidden");
}

function noteTargetOptions() {
  const targets = [];
  if (currentState?.currentPlace?.id) {
    targets.push({
      type: "place",
      id: currentState.currentPlace.id,
      label: currentState.currentPlace.name,
      meta: "Current place",
    });
  }
  if (currentState?.location) {
    targets.push({
      type: "system",
      id: currentState.location,
      label: currentState.currentSystem?.name || currentState.location,
      meta: "Current system",
    });
  }
  const selectedNpc = selectedNpcForComms();
  if (selectedNpc) {
    targets.push({
      type: "npc",
      id: String(selectedNpc.id),
      label: selectedNpc.name,
      meta: "Selected NPC",
    });
  }
  return targets;
}

function noteTargetKey(target) {
  return `${target?.type || ""}:${target?.id || ""}`;
}

function renderNoteTargets(targets = noteTargetOptions()) {
  els.noteTargetTabs.innerHTML = targets
    .map(
      (target) => `
        <button class="${noteTargetKey(target) === noteTargetKey(currentNoteTarget) ? "is-active" : ""}" data-note-type="${target.type}" data-note-id="${escapeAttribute(target.id)}">
          ${target.meta}: ${target.label}
        </button>
      `
    )
    .join("");
  els.noteTargetTabs.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", async () => {
      currentNoteTarget = targets.find(
        (target) => target.type === button.dataset.noteType && target.id === button.dataset.noteId
      );
      renderNoteTargets(targets);
      await loadNote(currentNoteTarget);
    });
  });
}

async function loadNote(target) {
  if (!target) {
    return;
  }
  els.noteStatus.textContent = "Loading note...";
  try {
    const params = new URLSearchParams({ targetType: target.type, targetId: target.id });
    const response = await fetch(`${notesUrl}?${params.toString()}`);
    const body = await readJson(response);
    if (!response.ok) {
      els.noteStatus.textContent = body.message || "Could not load that note.";
      return;
    }
    els.noteTitle.value = body.note?.title || "";
    els.noteBody.value = body.note?.body || "";
    els.noteStatus.textContent = body.note?.updatedAt ? `Last saved ${body.note.updatedAt}.` : "No private note saved yet.";
  } catch (error) {
    console.error(error);
    els.noteStatus.textContent = "The notebook did not answer.";
  }
}

async function saveCurrentNote() {
  if (!currentNoteTarget) {
    showToast("Select something to attach this note to.", "warning");
    return;
  }
  try {
    const response = await fetch(notesUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        targetType: currentNoteTarget.type,
        targetId: currentNoteTarget.id,
        title: els.noteTitle.value,
        body: els.noteBody.value,
      }),
    });
    const body = await readJson(response);
    if (!response.ok) {
      showToast(body.message || "Private note was not saved.", "warning");
      return;
    }
    els.noteStatus.textContent = body.note?.updatedAt ? `Last saved ${body.note.updatedAt}.` : "Private note saved.";
    showToast(body.message || "Private note saved.", "success");
  } catch (error) {
    console.error(error);
    showToast("Private note was not saved.", "danger");
  }
}

function startCommsPolling() {
  stopCommsPolling();
  commsPollTimer = window.setInterval(() => {
    if (!els.commsOverlay.classList.contains("is-hidden")) {
      refreshCommsContext(false);
    }
  }, 8000);
}

function stopCommsPolling() {
  if (commsPollTimer) {
    window.clearInterval(commsPollTimer);
    commsPollTimer = null;
  }
}

async function refreshCommsContext(showErrors = true) {
  try {
    const params = selectedNpcId ? `?npcId=${encodeURIComponent(selectedNpcId)}` : "";
    const response = await fetch(`${commsUrls.context}${params}`);
    const body = await readJson(response);
    if (!response.ok) {
      if (response.status === 401) {
        openAuth(body.message);
      }
      if (showErrors) {
        showToast(body.message || "Comms context unavailable.", "warning");
      }
      return;
    }
    commsContext = body;
    selectedNpcId = selectedNpcId || body.selectedNpcId || body.nearbyNpcs?.[0]?.id || null;
    renderComms();
  } catch (error) {
    console.error(error);
    if (showErrors) {
      showToast("Comms could not reach the server.", "danger");
    }
  }
}

async function refreshTtsStatus(showErrors = false) {
  try {
    const response = await fetch(commsUrls.ttsStatus);
    const body = await readJson(response);
    if (!response.ok) {
      if (showErrors) {
        showToast(body.message || "Voice status unavailable.", "warning");
      }
      return;
    }
    ttsStatus = body;
    renderSelectedCommsContext();
  } catch (error) {
    console.error(error);
    if (showErrors) {
      showToast("Voice status unavailable.", "warning");
    }
  }
}

function renderComms() {
  if (!commsContext) {
    return;
  }
  renderCommsTabs();
  renderCommsProvider();
  renderNpcList();
  renderSelectedCommsContext();
  renderCommsSocialTools();
  renderPendingCommsActions();
  renderCommsMessages();
  const npcBlocked = activeCommsChannel === "npc" && !commsContext.provider?.configured;
  const noGroup = activeCommsChannel === "group" && !selectedGroupId();
  const friendsTab = activeCommsChannel === "friends";
  els.commsInput.disabled = npcBlocked || noGroup || friendsTab;
  els.commsSendButton.disabled = npcBlocked || noGroup || friendsTab;
}

function renderCommsTabs() {
  els.commsTabs.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.channel === activeCommsChannel);
  });
}

function renderCommsProvider() {
  const provider = commsContext.provider || {};
  const message = provider.message || "Comms provider status unknown.";
  els.commsProviderNotice.textContent = activeCommsChannel === "npc" || !provider.configured ? message : "";
}

function renderNpcList() {
  const npcs = commsContext.nearbyNpcs || [];
  if (activeCommsChannel !== "npc") {
    els.commsNpcList.innerHTML = "";
    return;
  }
  if (!selectedNpcId && npcs.length) {
    selectedNpcId = npcs[0].id;
  }
  els.commsNpcList.innerHTML = npcs
    .map(
      (npc) => `
        <button class="npc-card npc-card--compact ${npc.id === selectedNpcId ? "is-active" : ""}" data-npc-id="${npc.id}">
          <strong>${npc.name}</strong>
          <span>${npc.role}</span>
        </button>
      `
    )
    .join("");
  els.commsNpcList.querySelectorAll(".npc-card").forEach((button) => {
    button.addEventListener("click", async () => {
      stopNpcSpeech();
      selectedNpcId = Number(button.dataset.npcId);
      await refreshCommsContext();
    });
  });
}

function selectedNpcForComms() {
  return (commsContext?.nearbyNpcs || []).find((npc) => npc.id === selectedNpcId) || null;
}

function renderSelectedCommsContext() {
  if (activeCommsChannel !== "npc") {
    els.commsSelectedContext.classList.add("is-hidden");
    els.commsSelectedContext.innerHTML = "";
    return;
  }
  const npc = selectedNpcForComms();
  if (!npc) {
    els.commsSelectedContext.classList.add("is-hidden");
    els.commsSelectedContext.innerHTML = "";
    return;
  }
  els.commsSelectedContext.classList.remove("is-hidden");
  const stats = npc.stats || {};
  const abilities = stats.stats || {};
  els.commsSelectedContext.innerHTML = `
    <div class="selected-contact">
      <div>
        <strong>${escapeHtml(npc.name)}</strong>
        <div class="selected-contact__facts">
          <span>${escapeHtml(npc.role)}</span>
          <span>${escapeHtml(npc.faction)}</span>
          <span>${escapeHtml(npc.gender || "Unspecified")}</span>
        </div>
        <div class="character-vitals" aria-label="Character stats">
          <span>HP ${escapeHtml(stats.health ?? "?")}/${escapeHtml(stats.maxHealth ?? "?")}</span>
          <span>STA ${escapeHtml(stats.stamina ?? "?")}/${escapeHtml(stats.maxStamina ?? "?")}</span>
          <span>Armor ${escapeHtml(stats.armor ?? 0)}</span>
          <span>${escapeHtml(stats.injury || "Healthy")}</span>
          <span>Combat ${escapeHtml(abilities.combat ?? 0)}</span>
          <span>Pilot ${escapeHtml(abilities.piloting ?? 0)}</span>
          <span>Tech ${escapeHtml(abilities.engineering ?? 0)}</span>
          <span>Charm ${escapeHtml(abilities.charm ?? 0)}</span>
        </div>
        <p class="selected-contact__appearance">${escapeHtml(npc.appearance || "No visual profile logged yet.")}</p>
        <p>${escapeHtml(npc.publicNotes)}</p>
        <p class="selected-contact__voice-status">${escapeHtml(voiceStatusText())}</p>
      </div>
      <div class="selected-contact__actions">
        <button id="selectedNpcVoiceToggle" aria-pressed="${npcVoiceEnabled}">${npcVoiceEnabled ? "Voice on" : "Voice off"}</button>
        <button id="selectedNpcSpeakLastButton">Speak last</button>
        <button id="selectedNpcStopVoiceButton">Stop</button>
        <button id="selectedNpcNoteButton">Private note</button>
      </div>
    </div>
  `;
  els.commsSelectedContext.querySelector("#selectedNpcVoiceToggle").addEventListener("click", toggleNpcVoice);
  els.commsSelectedContext.querySelector("#selectedNpcSpeakLastButton").addEventListener("click", () => {
    speakLatestNpcReply(true);
  });
  els.commsSelectedContext.querySelector("#selectedNpcStopVoiceButton").addEventListener("click", stopNpcSpeech);
  els.commsSelectedContext.querySelector("#selectedNpcNoteButton").addEventListener("click", () => {
    openNotes({ type: "npc", id: String(npc.id), label: npc.name, meta: "Selected NPC" });
  });
}

function voiceStatusText() {
  if (!ttsStatus) {
    return "Voice: checking Kokoro neural voice status...";
  }
  if (ttsStatus.available) {
    return "Voice: Kokoro neural voice ready. Browser speech remains fallback.";
  }
  const browserFallback = speechSupported() ? "Browser speech fallback is active." : "No browser speech fallback is available here.";
  return `Voice: Kokoro not active. ${browserFallback} ${ttsStatus.message || ""}`;
}

function speechSupported() {
  return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

function loadSpeechVoices() {
  if (!speechSupported()) {
    speechVoices = [];
    return;
  }
  speechVoices = window.speechSynthesis.getVoices();
}

function toggleNpcVoice() {
  npcVoiceEnabled = !npcVoiceEnabled;
  storageSet(npcVoiceStorageKey, String(npcVoiceEnabled));
  loadSpeechVoices();
  renderSelectedCommsContext();
  if (npcVoiceEnabled) {
    speakLatestNpcReply(true);
  } else {
    stopNpcSpeech();
  }
}

function speakLatestNpcReply(force = false) {
  const npc = selectedNpcForComms();
  const message = latestNpcMessageForSelectedContact();
  if (!npc || !message) {
    if (force) {
      showToast("No NPC reply to speak yet.", "warning");
    }
    return;
  }
  speakNpcMessage(npc, message, force);
}

function latestNpcMessageForSelectedContact() {
  const messages = commsContext?.messages?.npc || [];
  return [...messages].reverse().find((message) => {
    return message.senderKind === "npc" && (!selectedNpcId || message.npcId === selectedNpcId);
  }) || null;
}

function speakNpcMessage(npc, message, force = false) {
  if (!force && (!npcVoiceEnabled || message.id === lastSpokenNpcMessageId)) {
    return;
  }
  const text = speechText(message.metadata?.speechText || message.body);
  if (!text) {
    return;
  }
  speakNpcMessageWithBestProvider(npc, message, text, force);
}

async function speakNpcMessageWithBestProvider(npc, message, text, force = false) {
  const kokoroSpoke = await speakWithKokoro(npc, text, force);
  if (kokoroSpoke) {
    lastSpokenNpcMessageId = message.id;
    return;
  }
  if (speakWithBrowserVoice(npc, text, force)) {
    lastSpokenNpcMessageId = message.id;
  }
}

async function speakWithKokoro(npc, text, force = false) {
  try {
    const response = await fetch(commsUrls.ttsSpeak, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        npc: {
          id: npc.id,
          name: npc.name,
          gender: npc.gender,
          role: npc.role,
        },
      }),
    });
    const body = await readJson(response);
    if (!response.ok || !body.audioUrl) {
      if (force) {
        showToast(`${body.message || "Kokoro not active."} Using browser fallback.`, "info");
      }
      return false;
    }
    stopNpcSpeech();
    npcAudioPlayer.src = body.audioUrl;
    await npcAudioPlayer.play();
    return true;
  } catch (error) {
    console.warn(error);
    if (force) {
      showToast("Kokoro voice did not answer. Falling back to browser voice.", "warning");
    }
    return false;
  }
}

function speakWithBrowserVoice(npc, text, force = false) {
  if (!speechSupported()) {
    if (force) {
      showToast("Kokoro is unavailable and this browser does not expose speech voices.", "warning");
    }
    return false;
  }
  loadSpeechVoices();
  const utterance = new SpeechSynthesisUtterance(text);
  const profile = npcVoiceProfile(npc);
  if (profile.voice) {
    utterance.voice = profile.voice;
  }
  utterance.pitch = profile.pitch;
  utterance.rate = profile.rate;
  utterance.volume = 0.95;
  stopNpcSpeech();
  window.speechSynthesis.speak(utterance);
  return true;
}

function stopNpcSpeech() {
  npcAudioPlayer.pause();
  npcAudioPlayer.removeAttribute("src");
  npcAudioPlayer.load();
  if (speechSupported()) {
    window.speechSynthesis.cancel();
  }
}

function npcVoiceProfile(npc) {
  const voices = preferredSpeechVoices(npc);
  const hash = hashString(`${npc.id}:${npc.name}:${npc.gender}:${npc.role}`);
  const voice = voices.length ? voices[hash % voices.length] : null;
  const genderPitch = npc.gender === "Male" ? 0.84 : 1.08;
  const pitch = clampNumber(genderPitch + ((hash % 9) - 4) * 0.025, 0.72, 1.32);
  const rate = clampNumber(0.88 + ((Math.floor(hash / 11) % 9) - 4) * 0.018, 0.78, 1.06);
  return { voice, pitch, rate };
}

function preferredSpeechVoices(npc) {
  if (!speechVoices.length) {
    return [];
  }
  const englishVoices = speechVoices.filter((voice) => voice.lang?.toLowerCase().startsWith("en"));
  const voicePool = englishVoices.length ? englishVoices : speechVoices;
  const maleHints = ["alex", "daniel", "david", "fred", "george", "guy", "mark", "matthew", "ryan", "tom"];
  const femaleHints = ["amy", "aria", "emma", "fiona", "jenny", "joanna", "karen", "samantha", "salli", "serena", "victoria", "zira"];
  const hints = npc.gender === "Male" ? maleHints : femaleHints;
  const hinted = voicePool.filter((voice) => hints.some((hint) => voice.name.toLowerCase().includes(hint)));
  return hinted.length ? hinted : voicePool;
}

function speechText(value) {
  let text = String(value || "");
  const parsed = parsedLegacyReply(text);
  if (parsed) {
    text = parsed.filter((segment) => segment.type === "speech").map((segment) => segment.text).join(" ");
  }
  return text
    .replace(/Pending confirmation:.*$/gis, "")
    .replace(/Ship action (?:ignored|applied):.*$/gis, "")
    .replace(/Action rejected:.*$/gis, "")
    .replace(/[`*_#>]/g, "")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 1400);
}

function renderCommsSocialTools() {
  if (activeCommsChannel === "friends") {
    els.commsSocialTools.innerHTML = `
      <label>
        Add friend by username
        <input id="friendUsername" placeholder="Captain name">
      </label>
      <button id="addFriendButton">Add friend</button>
      <div class="npc-list">
        ${(commsContext.friends || [])
          .map((friend) => `<div class="npc-card"><strong>${friend.username}</strong><span>${friend.status}</span></div>`)
          .join("") || "<p class=\"settings-note\">No friends added yet.</p>"}
      </div>
    `;
    els.commsSocialTools.querySelector("#addFriendButton")?.addEventListener("click", addFriend);
    return;
  }
  if (activeCommsChannel === "dm") {
    els.commsSocialTools.innerHTML = `
      <label>
        DM username
        <input id="dmUsername" placeholder="Captain name">
      </label>
      <button id="loadDmButton">Load DM</button>
    `;
    els.commsSocialTools.querySelector("#loadDmButton")?.addEventListener("click", loadSocialMessages);
    return;
  }
  if (activeCommsChannel === "group") {
    const groups = commsContext.groups || [];
    els.commsSocialTools.innerHTML = `
      <label>
        Group channel
        <select id="groupSelect">
          ${groups.map((group) => `<option value="${group.id}">${group.name}</option>`).join("")}
        </select>
      </label>
      <button id="loadGroupButton">Load group</button>
      <label>
        Create group
        <input id="newGroupName" placeholder="Group name">
      </label>
      <button id="createGroupButton">Create group</button>
    `;
    els.commsSocialTools.querySelector("#loadGroupButton")?.addEventListener("click", loadSocialMessages);
    els.commsSocialTools.querySelector("#createGroupButton")?.addEventListener("click", createGroup);
    return;
  }
  els.commsSocialTools.innerHTML = "";
}

function renderPendingCommsActions() {
  const pending = commsContext.pendingActions || [];
  if (!pending.length) {
    els.pendingCommsActions.innerHTML = "";
    return;
  }
  els.pendingCommsActions.innerHTML = pending
    .map(
      (action) => `
        <div class="pending-action">
          <strong>${action.summary}</strong>
          <span>${action.action}</span>
          <button data-confirm-action="${action.id}">Confirm</button>
        </div>
      `
    )
    .join("");
  els.pendingCommsActions.querySelectorAll("[data-confirm-action]").forEach((button) => {
    button.addEventListener("click", () => confirmCommsAction(Number(button.dataset.confirmAction)));
  });
}

function renderCommsMessages() {
  const messages = activeCommsChannel === "dm" || activeCommsChannel === "group"
    ? socialMessages
    : commsContext.messages?.[activeCommsChannel] || [];
  if (!messages.length) {
    els.commsMessages.innerHTML = `<p class="settings-note">${emptyCommsMessage()}</p>`;
    return;
  }
  els.commsMessages.innerHTML = messages
    .map(
      (message) => `
        <article class="comms-message" data-kind="${message.senderKind}">
          <strong>${escapeHtml(message.senderName)}</strong>
          <div class="comms-message__body">${renderCommsMessageBody(message)}</div>
        </article>
      `
    )
    .join("");
  els.commsMessages.scrollTop = els.commsMessages.scrollHeight;
}

function renderCommsMessageBody(message) {
  const segments = messageSegments(message);
  const rendered = segments
    .map((segment) => {
      const type = segment.type === "action" ? "action" : "speech";
      return `<p class="comms-line comms-line--${type}">${escapeHtml(segment.text)}</p>`;
    })
    .join("");
  const note = commsSystemNote(message.body, segments);
  return `${rendered}${note ? `<p class="comms-line comms-line--system">${escapeHtml(note)}</p>` : ""}`;
}

function messageSegments(message) {
  const segments = message.metadata?.segments;
  if (Array.isArray(segments) && segments.length) {
    return segments
      .map((segment) => ({
        type: segment.type === "action" ? "action" : "speech",
        text: String(segment.text || "").trim(),
      }))
      .filter((segment) => segment.text);
  }
  const parsed = parsedLegacyReply(message.body);
  if (parsed) {
    return parsed;
  }
  return displaySegmentsFromText(message.body);
}

function parsedLegacyReply(body) {
  const text = String(body || "").trim();
  if (!text.startsWith("{")) {
    return null;
  }
  try {
    const payload = JSON.parse(text);
    const action = payload.actionText || payload.action_text || payload.stageDirection || payload.stage_direction || "";
    const speech = payload.speech || payload.reply || "";
    const segments = [];
    if (action) {
      segments.push({ type: "action", text: stripRoleplayWrapper(action) });
    }
    if (speech) {
      segments.push(...displaySegmentsFromText(speech));
    }
    return segments.length ? segments : null;
  } catch {
    return null;
  }
}

function stripRoleplayWrapper(value) {
  const text = String(value || "").trim();
  if ((text.startsWith("*") && text.endsWith("*")) || (text.startsWith("(") && text.endsWith(")"))) {
    return text.slice(1, -1).trim();
  }
  return text;
}

function displaySegmentsFromText(value) {
  const text = String(value || "").trim();
  if (!text) {
    return [];
  }
  const pattern = /(\*[^*\n]{2,500}\*|\([^()\n]{2,500}\))/g;
  const segments = [];
  let position = 0;
  for (const match of text.matchAll(pattern)) {
    const before = text.slice(position, match.index).trim();
    if (before) {
      segments.push({ type: "speech", text: before });
    }
    const action = match[0].slice(1, -1).trim();
    if (action) {
      segments.push({ type: "action", text: action });
    }
    position = match.index + match[0].length;
  }
  const after = text.slice(position).trim();
  if (after) {
    segments.push({ type: "speech", text: after });
  }
  return segments.length ? segments : [{ type: "speech", text }];
}

function commsSystemNote(body, segments) {
  const text = String(body || "");
  const spokenAndActions = segments.map((segment) => segment.text).join("\n");
  const suffixes = ["Pending confirmation:", "Ship action ignored:", "Ship action applied:", "Action rejected:"];
  for (const suffix of suffixes) {
    const index = text.indexOf(suffix);
    if (index >= 0 && !spokenAndActions.includes(suffix)) {
      return text.slice(index).trim();
    }
  }
  return "";
}

function emptyCommsMessage() {
  if (activeCommsChannel === "npc" && !commsContext.provider?.configured) {
    return commsContext.provider?.message || "Configure a provider before NPC chat.";
  }
  if (activeCommsChannel === "friends") {
    return "Add friends here, then use DMs or groups to talk.";
  }
  return "No messages on this channel yet.";
}

function appendOptimisticPlayerMessage(body) {
  const article = document.createElement("article");
  article.className = "comms-message";
  article.dataset.kind = "player";
  article.dataset.optimistic = "1";
  article.innerHTML = `<strong>${escapeHtml(currentState?.user?.username || "You")}</strong><div class="comms-message__body">${renderCommsMessageBody({ body, metadata: { segments: displaySegmentsFromText(body) } })}</div>`;
  els.commsMessages.appendChild(article);
  els.commsMessages.scrollTop = els.commsMessages.scrollHeight;
}

function appendNpcTypingIndicator(npcName) {
  const article = document.createElement("article");
  article.className = "comms-message";
  article.dataset.kind = "npc";
  article.dataset.typing = "1";
  article.innerHTML = `<strong>${escapeHtml(npcName || "NPC")}</strong><div class="comms-typing-indicator"><span class="comms-typing-indicator__label">typing</span><span class="comms-typing-indicator__dot"></span><span class="comms-typing-indicator__dot"></span><span class="comms-typing-indicator__dot"></span></div>`;
  els.commsMessages.appendChild(article);
  els.commsMessages.scrollTop = els.commsMessages.scrollHeight;
  return article;
}

async function npcStreamSend(body, payload) {
  const npcName = commsContext?.nearbyNpcs?.find?.((n) => n.id === selectedNpcId)?.name || "NPC";
  appendOptimisticPlayerMessage(body);
  const typingEl = appendNpcTypingIndicator(npcName);
  let streamBodyDiv = typingEl.querySelector(".comms-typing-indicator");
  els.commsInput.value = "";
  els.commsSendButton.disabled = true;
  try {
    const response = await fetch(commsUrls.stream, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      renderComms();
      showToast("Comms stream failed.", "danger");
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let streamedText = "";
    let bodySwapped = false;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const data = line.slice(5).trim();
        let evt;
        try { evt = JSON.parse(data); } catch { continue; }
        if (evt.type === "token") {
          streamedText += evt.text;
          if (!bodySwapped) {
            // Replace animated dots with live text div
            typingEl.innerHTML = `<strong>${escapeHtml(npcName)}</strong><div class="comms-message__body comms-streaming"><p class="comms-line">${escapeHtml(streamedText)}</p></div>`;
            streamBodyDiv = typingEl.querySelector(".comms-message__body p");
            bodySwapped = true;
          } else {
            streamBodyDiv.textContent = streamedText;
          }
          els.commsMessages.scrollTop = els.commsMessages.scrollHeight;
        } else if (evt.type === "done") {
          commsContext = evt.context;
          if (evt.gameState) {
            currentState = { ...currentState, ...evt.gameState };
            render(currentState);
          }
          renderComms();
          speakLatestNpcReply(false);
          showToast("NPC replied.", "success");
        } else if (evt.type === "error") {
          showToast(evt.message, "warning");
          renderComms();
        }
      }
    }
  } catch (error) {
    console.error(error);
    showToast("Comms stream failed.", "danger");
    renderComms();
  } finally {
    els.commsSendButton.disabled = false;
  }
}

async function sendCommsMessage(event) {
  event.preventDefault();
  const body = els.commsInput.value.trim();
  if (!body) {
    showToast("Type a message before opening the channel.", "warning");
    return;
  }
  const payload = { channel: activeCommsChannel, body };
  if (activeCommsChannel === "npc") {
    payload.npcId = selectedNpcId;
    await npcStreamSend(body, payload);
    return;
  }
  if (activeCommsChannel === "dm") {
    payload.username = document.querySelector("#dmUsername")?.value?.trim();
  }
  if (activeCommsChannel === "group") {
    payload.groupId = selectedGroupId();
  }
  try {
    els.commsSendButton.disabled = true;
    const response = await fetch(commsUrls.message, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const responseBody = await readJson(response);
    if (!response.ok) {
      showToast(responseBody.message || "Comms message failed.", response.status === 503 ? "warning" : "danger");
      if (responseBody.context) {
        commsContext = responseBody.context;
        renderComms();
      }
      return;
    }
    els.commsInput.value = "";
    if (responseBody.state) {
      currentState = responseBody.state;
      render(currentState);
    }
    if (responseBody.context) {
      commsContext = responseBody.context;
    }
    if (activeCommsChannel === "dm" || activeCommsChannel === "group") {
      await loadSocialMessages();
    } else {
      renderComms();
    }
    showToast(responseBody.message || "Message sent.", "success");
  } catch (error) {
    console.error(error);
    showToast("Comms message failed.", "danger");
  } finally {
    els.commsSendButton.disabled = false;
  }
}

async function confirmCommsAction(actionId) {
  try {
    const response = await fetch(commsUrls.confirm, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actionId }),
    });
    const body = await readJson(response);
    if (!response.ok) {
      showToast(body.message || "Confirmation failed.", "warning");
      return;
    }
    currentState = body.state;
    commsContext = body.context;
    render(currentState);
    renderComms();
    showToast(body.message, toastTone(body.message));
  } catch (error) {
    console.error(error);
    showToast("Confirmation failed.", "danger");
  }
}

async function addFriend() {
  const username = document.querySelector("#friendUsername")?.value?.trim();
  if (!username) {
    showToast("Enter a username to add.", "warning");
    return;
  }
  const response = await fetch(commsUrls.friends, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  const body = await readJson(response);
  if (!response.ok) {
    showToast(body.message || "Friend add failed.", "warning");
    return;
  }
  commsContext.friends = body.friends || [];
  renderComms();
  showToast(body.message, "success");
}

async function createGroup() {
  const name = document.querySelector("#newGroupName")?.value?.trim();
  if (!name) {
    showToast("Enter a group name.", "warning");
    return;
  }
  const response = await fetch(commsUrls.groups, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const body = await readJson(response);
  if (!response.ok) {
    showToast(body.message || "Group creation failed.", "warning");
    return;
  }
  commsContext.groups = body.groups || [];
  renderComms();
  showToast(body.message, "success");
}

async function loadSocialMessages() {
  const params = new URLSearchParams({ channel: activeCommsChannel });
  if (activeCommsChannel === "dm") {
    const username = document.querySelector("#dmUsername")?.value?.trim();
    if (!username) {
      showToast("Enter a DM username first.", "warning");
      return;
    }
    params.set("username", username);
  }
  if (activeCommsChannel === "group") {
    const groupId = selectedGroupId();
    if (!groupId) {
      showToast("Create or select a group first.", "warning");
      return;
    }
    params.set("groupId", groupId);
  }
  const response = await fetch(`${commsUrls.socialMessages}?${params.toString()}`);
  const body = await readJson(response);
  if (!response.ok) {
    showToast(body.message || "Messages unavailable.", "warning");
    return;
  }
  socialMessages = body.messages || [];
  renderCommsMessages();
}

function selectedGroupId() {
  return document.querySelector("#groupSelect")?.value || "";
}

function disabledAttrs(reason) {
  return `aria-disabled="true" data-disabled-reason="${escapeAttribute(reason || "That action is not available right now.")}"`;
}

function escapeAttribute(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function disabledReason(button) {
  return button?.dataset?.disabledReason || button?.title || "That action is not available right now.";
}

document.addEventListener(
  "click",
  (event) => {
    const target = event.target instanceof Element ? event.target : event.target.parentElement;
    const button = target?.closest('button[aria-disabled="true"]');
    if (!button) {
      return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    showToast(disabledReason(button), "warning");
  },
  true
);

function render(state) {
  renderIdentity(state);
  if (renderedLocation && renderedLocation !== state.location) {
    resetLocalZoom(state);
  }
  renderedLocation = state.location;
  if (plottedCourseId === state.location) {
    plottedCourseId = null;
  }
  els.shipName.textContent = state.shipName;
  els.status.textContent = state.status;
  els.travelState.textContent = state.travelState.label;
  els.credits.textContent = isCheatEnabled(state, "unlimitedCredits") ? "Unlimited" : credits(state.credits);
  els.fuel.textContent = isCheatEnabled(state, "unlimitedFuel") ? `Full (${state.maxFuel})` : `${state.fuel}/${state.maxFuel}`;
  els.hull.textContent = isCheatEnabled(state, "invulnerableHull") ? `Safe (${state.maxHull})` : `${state.hull}/${state.maxHull}`;
  els.cargo.textContent = `${state.cargoUsed}/${state.cargoCapacity}`;
  els.dayBadge.textContent = `Day ${state.day}`;
  els.discoveryBadge.textContent = `${state.discovery.charted}/${state.discovery.total} charted`;
  els.courseStatus.textContent = courseStatusText(state);
  els.breadcrumbTrail.innerHTML = breadcrumbParts(state)
    .map((part) => `<span>${part}</span>`)
    .join("");

  els.systemName.textContent = state.currentSystem.name;
  els.systemDescription.textContent = state.currentSystem.description;
  els.systemFaction.textContent = state.currentSystem.faction;
  els.systemEconomy.textContent = state.currentSystem.economy;
  els.systemRisk.textContent = state.currentSystem.risk;

  renderMap(state);
  renderLocalPlaces(state);
  renderTravel(state);
  renderGates(state);
  renderCatalogDetail(state);
  renderMissions(state);
  renderMarket(state);
  renderShip(state);
  renderInventory(state);
  renderLog(state);
  renderServiceButtons(state);
  renderCheats(state);
  renderView();
}

function renderView() {
  els.navButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === activeView);
  });
  els.viewPanels.forEach((panel) => {
    panel.classList.toggle("is-active", panel.id === `view-${activeView}`);
  });
  if (activeView === "navigation") {
    els.navigationPanel.classList.toggle("map-expanded", mapExpanded);
    els.navigationPanel.classList.toggle("catalog-open", navigationMode === "catalog");
    els.expandMapButton.textContent = mapExpanded ? "Collapse map" : "Expand map";
    els.expandMapButton.setAttribute("aria-pressed", String(mapExpanded));
    updateNavigationModeVisibility();
    if (!mapChart.fitted) {
      fitGalaxy();
    } else {
      applyMapTransform();
    }
  }
}

function updateNavigationModeVisibility() {
  const showingCatalog = navigationMode === "catalog";
  els.systemDetails.classList.toggle("is-hidden", showingCatalog);
  els.plottedCourse.classList.toggle("is-hidden", showingCatalog);
  els.gatePanel.classList.toggle("is-hidden", showingCatalog);
  els.travelList.classList.toggle("is-hidden", showingCatalog);
  els.catalogDetail.classList.toggle("is-hidden", !showingCatalog);
}

function renderMap(state) {
  if (!focusedSystemId || !state.systems.some((system) => system.id === focusedSystemId)) {
    focusedSystemId = plottedCourseId || state.location;
  }
  const xs = state.systems.map((system) => system.x);
  const ys = state.systems.map((system) => system.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const points = Object.fromEntries(
    state.systems.map((system) => [
      system.id,
      {
        ...system,
        chartX: chartScale(system.x, minX, maxX, galaxySize.width),
        chartY: chartScale(system.y, minY, maxY, galaxySize.height),
      },
    ])
  );
  const currentPoint = points[state.location];
  const plottedRoute = state.travel.find((route) => route.id === plottedCourseId && !route.disabled);

  els.sectorMap.innerHTML = "";
  const chart = document.createElement("div");
  chart.className = "galaxy-chart";
  chart.style.width = `${galaxySize.width}px`;
  chart.style.height = `${galaxySize.height}px`;

  const routes = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  routes.setAttribute("class", "galaxy-routes");
  routes.setAttribute("viewBox", `0 0 ${galaxySize.width} ${galaxySize.height}`);
  routes.setAttribute("aria-hidden", "true");
  state.travel
    .filter((route) => !route.disabled)
    .forEach((route) => {
      const destination = points[route.id];
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", currentPoint.chartX);
      line.setAttribute("y1", currentPoint.chartY);
      line.setAttribute("x2", destination.chartX);
      line.setAttribute("y2", destination.chartY);
      line.setAttribute(
        "class",
        `route-line route-${route.risk.toLowerCase()}${route.id === plottedCourseId ? " plotted" : ""}`
      );
      routes.appendChild(line);
    });
  chart.appendChild(routes);

  state.systems.forEach((system) => {
    const point = points[system.id];
    const node = document.createElement("button");
    const isCurrent = system.id === state.location;
    const isPlotted = system.id === plottedCourseId;
    node.className = `system-node${system.charted ? "" : " signal"}${isCurrent ? " current" : ""}${isPlotted ? " plotted" : ""}`;
    node.style.left = `${point.chartX}px`;
    node.style.top = `${point.chartY}px`;
    node.title = `${system.name}: ${system.economy} - ${system.risk} risk`;
    node.setAttribute("aria-label", `Plot course to ${system.name}`);
    if (isCurrent) {
      node.setAttribute("aria-disabled", "true");
      node.dataset.disabledReason = "You are already in this system. Select another system to plot a course.";
    }
    node.innerHTML = `
      <span class="star-core"></span>
      <span class="star-label">${system.name}</span>
      <small>${system.risk}</small>
    `;
    node.addEventListener("mouseenter", () => focusSystem(system.id));
    node.addEventListener("focus", () => focusSystem(system.id));
    node.addEventListener("click", () => plotCourse(system.id));
    chart.appendChild(node);
  });
  els.sectorMap.appendChild(chart);
  renderSystemDetails(state);
  renderPlottedCourse(state, plottedRoute);
  if (!mapChart.fitted) {
    mapChart.fitted = fitGalaxy();
  } else {
    applyMapTransform();
  }
}

function plotCourse(destinationId) {
  if (!currentState) {
    showToast("The navigation charts are still loading.", "warning");
    return;
  }
  if (destinationId === currentState.location) {
    showToast("You are already in this system. Select another system to plot a course.", "warning");
    return;
  }
  const route = currentState.travel.find((item) => item.id === destinationId);
  if (route?.disabled) {
    showToast(route.blockedReason || route.warning || "That route is not available from here.", "warning");
    return;
  }
  plottedCourseId = destinationId;
  focusedSystemId = destinationId;
  render(currentState);
}

function commitCourse() {
  if (!plottedCourseId) {
    showToast("No course is plotted yet.", "warning");
    return;
  }
  const route = currentState?.travel.find((item) => item.id === plottedCourseId);
  if (!route?.canCommit) {
    showToast(route?.blockedReason || route?.warning || "That course cannot be committed right now.", "warning");
    return;
  }
  const destination = plottedCourseId;
  plottedCourseId = null;
  sendAction({ action: "travel", destination });
}

function cancelCourse() {
  plottedCourseId = null;
  focusedSystemId = currentState?.location || null;
  render(currentState);
}

function focusSystem(systemId) {
  focusedSystemId = systemId;
  renderSystemDetails(currentState);
}

function renderSystemDetails(state) {
  if (!state) {
    return;
  }

  const system = state.systems.find((item) => item.id === focusedSystemId) || state.currentSystem;
  const route = state.travel.find((item) => item.id === system.id);
  const isCurrent = system.id === state.location;
  const isPlotted = system.id === plottedCourseId;
  const detailLabel = system.charted ? "Details" : "Signal";
  const plotLabel = system.charted ? "Plot course" : "Plot signal";
  els.systemDetails.innerHTML = `
    <div>
      <small>${isCurrent ? "Current system" : isPlotted ? "Plotted destination" : system.charted ? "Chart selection" : "Uncharted contact"}</small>
      <strong>${system.name}</strong>
      <p>${system.description}</p>
      <div class="place-meta">
        <span>${system.galaxyName}</span>
        <span>${system.faction}</span>
        <span>${system.economy}</span>
        <span>${system.charted ? `${system.risk} risk` : "Risk unresolved"}</span>
        <span>${isCurrent ? state.travelState.label : `${route?.fuelCost ?? 0} fuel`}</span>
        ${route?.timeCost ? `<span>${route.timeCost} day burn</span>` : ""}
      </div>
      ${route?.discoveryNote && !isCurrent ? `<p class="travel-note">${route.discoveryNote}</p>` : ""}
      ${route?.blockedReason && !isCurrent ? `<p class="travel-warning">${route.blockedReason}</p>` : ""}
      ${route?.warning ? `<p class="travel-warning">${route.warning}</p>` : ""}
    </div>
    <div class="system-detail-actions">
      <button class="details-button">${detailLabel}</button>
      <button class="plot-button" ${isCurrent ? disabledAttrs("You are already in this system. Select another system to plot a course.") : ""}>${isPlotted ? "Course plotted" : plotLabel}</button>
    </div>
  `;
  els.systemDetails.querySelector(".details-button").addEventListener("click", () => showSystemCatalog(system.id));
  els.systemDetails.querySelector(".plot-button").addEventListener("click", () => plotCourse(system.id));
}

function renderPlottedCourse(state, plottedRoute) {
  if (!plottedRoute) {
    els.plottedCourse.innerHTML = `
      <strong>No course plotted</strong>
      <span>Select a system on the galaxy chart or from the route list.</span>
    `;
    return;
  }

  els.plottedCourse.innerHTML = `
    <div>
      <strong>Course plotted: ${plottedRoute.name}</strong>
      <span>${plottedRoute.fuelCost} fuel - ${plottedRoute.timeCost} day burn - ${plottedRoute.charted ? `${plottedRoute.risk} risk` : "uncharted signal"}</span>
      ${plottedRoute.discoveryNote ? `<p class="travel-note">${plottedRoute.discoveryNote}</p>` : ""}
      ${plottedRoute.blockedReason ? `<p class="travel-warning">${plottedRoute.blockedReason}</p>` : ""}
      ${plottedRoute.warning ? `<p class="travel-warning">${plottedRoute.warning}</p>` : ""}
    </div>
    <div class="course-actions">
      <button id="cancelCourseButton">Cancel course</button>
      <button id="commitCourseButton" ${
        plottedRoute.canCommit
          ? ""
          : disabledAttrs(plottedRoute.blockedReason || plottedRoute.warning || "That course cannot be committed right now.")
      }>Commit course</button>
    </div>
  `;
  els.plottedCourse.querySelector("#cancelCourseButton").addEventListener("click", cancelCourse);
  els.plottedCourse.querySelector("#commitCourseButton").addEventListener("click", commitCourse);
}

function renderLocalPlaces(state) {
  const place = state.currentPlace;
  const planetIds = state.planets.map((planet) => planet.id);
  if (localScope === "place") {
    selectedLocalTarget = place.category === "planet" ? place.planetId : "station";
  }
  if (selectedLocalTarget !== "station" && !planetIds.includes(selectedLocalTarget)) {
    selectedLocalTarget = "station";
  }
  if (localScope === "planet" && selectedLocalTarget === "station") {
    selectedLocalTarget = state.planets[0]?.id || "station";
  }
  if (localScope === "planet" && selectedLocalTarget === "station") {
    localScope = "system";
  }

  els.visitedPlaceBadge.textContent = `${state.visitedPlaceCount} visited`;
  els.currentPlace.innerHTML = `
    <small>${state.travelState.label} near ${state.travelState.nearLabel}</small>
    <strong>${place.name}</strong>
    <p>${place.description}</p>
    <div class="place-meta">
      <span>${place.faction}</span>
      <span>${place.wealth}</span>
      <span>${place.security}</span>
    </div>
    ${renderMovementButtons(state.travelState.options)}
  `;
  bindMovementButtons(els.currentPlace);

  renderLocalScopeTabs(state);
  renderLocalTargets(state);

  if (localScope === "system") {
    renderSystemZoom(state);
    return;
  }

  if (localScope === "station") {
    selectedLocalTarget = "station";
    renderStationDetail(state);
    return;
  }

  if (localScope === "place") {
    renderPlaceZoom(state);
    return;
  }

  const planet = state.planets.find((item) => item.id === selectedLocalTarget) || state.planets[0];
  if (!planet) {
    renderSystemZoom(state);
    return;
  }
  renderPlanetDetail(state, planet);
}

function renderLocalScopeTabs(state) {
  const hasPlanetSelection = selectedLocalTarget !== "station" && state.planets.some((planet) => planet.id === selectedLocalTarget);
  const hasCurrentPlace = Boolean(state.currentPlace);
  els.localScopeTabs.forEach((button) => {
    const scope = button.dataset.scope;
    const isUnavailable =
      (scope === "planet" && !hasPlanetSelection) ||
      (scope === "place" && !hasCurrentPlace);
    if (isUnavailable) {
      button.setAttribute("aria-disabled", "true");
      button.dataset.disabledReason =
        scope === "planet"
          ? "Select a planet before opening the Planet zoom level."
          : "Select or enter a specific place before opening the Place zoom level.";
    } else {
      button.removeAttribute("aria-disabled");
      delete button.dataset.disabledReason;
    }
    button.classList.toggle("is-active", button.dataset.scope === localScope);
  });
}

function setLocalScope(scope, target = selectedLocalTarget) {
  localScope = scope;
  selectedLocalTarget = target;
  flashLocalTransition();
  renderLocalPlaces(currentState);
}

function resetLocalZoom(state) {
  localScope = "system";
  selectedLocalTarget = "station";
  focusedSystemId = state.location;
}

function flashLocalTransition() {
  els.localDetail.classList.remove("is-transitioning");
  window.requestAnimationFrame(() => {
    els.localDetail.classList.add("is-transitioning");
    window.setTimeout(() => els.localDetail.classList.remove("is-transitioning"), 220);
  });
}

function renderLocalTargets(state) {
  els.localTargets.innerHTML = "";

  const stationButton = document.createElement("button");
  stationButton.className = `target-button${selectedLocalTarget === "station" ? " is-active" : ""}`;
  const stationCount = state.stations?.length || 1;
  const stationAreaCount = state.stations?.reduce((total, station) => total + station.areaCount, 0) || state.station.areas.length;
  stationButton.innerHTML = `
    <small>${stationCount === 1 ? "Station" : "Stations"}</small>
    <strong>${stationCount === 1 ? state.station.name : `${stationCount} stations`}</strong>
    <span>${stationAreaCount} areas - ${movementBrief(state.station.movement)}</span>
  `;
  stationButton.addEventListener("click", () => {
    setLocalScope("station", "station");
  });
  els.localTargets.appendChild(stationButton);

  state.planets.forEach((planet) => {
    const button = document.createElement("button");
    button.className = `target-button${selectedLocalTarget === planet.id ? " is-active" : ""}`;
    button.innerHTML = `
      <small>${planet.type}</small>
      <strong>${planet.name}</strong>
      <span>${planet.placeCount.toLocaleString()} places - ${planet.flightStats.gravity}g</span>
    `;
    button.addEventListener("click", () => {
      setLocalScope("planet", planet.id);
    });
    els.localTargets.appendChild(button);
  });
}

function renderSystemZoom(state) {
  els.localTargetMeta.textContent = "System";
  els.localTargetTitle.textContent = state.currentSystem.name;
  els.localTargetSummary.textContent = state.currentSystem.description;
  els.localTargetActions.innerHTML = "";
  els.localSublocations.innerHTML = "";
  els.localSublocations.appendChild(renderSystemMap(state));

  const stationCard = document.createElement("article");
  stationCard.className = "place-card";
  const stationMove = state.station.movement;
  stationCard.innerHTML = `
    <small>Primary station - ${state.station.areas.length} areas</small>
    <strong>${state.station.name}</strong>
    <p>The primary orbital hub for ${state.currentSystem.name}.</p>
    ${renderPreview(stationMove)}
    <div class="card-actions">
      <button class="local-travel-button" data-movement="dock_station" ${movementDisabled(stationMove)}>
        ${stationMove?.isCurrent ? "Docked" : `Dock (${movementBrief(stationMove)})`}
      </button>
      <button class="open-location-button">Open station</button>
    </div>
  `;
  stationCard.querySelector(".open-location-button").addEventListener("click", () => {
    setLocalScope("station", "station");
  });
  bindMovementButtons(stationCard);
  els.localSublocations.appendChild(stationCard);

  (state.stations || [])
    .filter((station) => !station.primary)
    .forEach((station) => {
      const extraStationCard = document.createElement("article");
      extraStationCard.className = "place-card compact";
      extraStationCard.innerHTML = `
        <small>Charted station - ${station.areaCount} areas</small>
        <strong>${station.name}</strong>
        <p>This station is charted in the system catalog. Direct docking controls still use the primary station.</p>
        <button class="details-button">Open system details</button>
      `;
      extraStationCard.querySelector("button").addEventListener("click", () => {
        showSystemCatalog(state.location);
      });
      els.localSublocations.appendChild(extraStationCard);
    });

  state.planets.forEach((planet) => {
    const planetCard = document.createElement("article");
    planetCard.className = "place-card";
    planetCard.innerHTML = `
      <small>${planet.type} - ${planet.wealth}</small>
      <strong>${planet.name}</strong>
      <p>${planet.placeCount.toLocaleString()} indexed places controlled mostly by ${planet.dominantFaction}.</p>
      <div class="place-meta">
        <span>${planet.flightStats.gravity}g</span>
        <span>${planet.flightStats.atmosphereDensity} atm</span>
        <span>Landing ${planet.flightStats.landingDifficulty}</span>
      </div>
      ${renderPreview(planet.orbitPreview)}
      <div class="card-actions">
        <button class="local-travel-button" data-movement="enter_orbit" data-planet-id="${planet.id}" ${movementDisabled(planet.orbitPreview)}>
          ${planet.orbitPreview?.isCurrent ? "In orbit" : `Enter orbit (${movementBrief(planet.orbitPreview)})`}
        </button>
        <button class="open-location-button">Open planet</button>
      </div>
    `;
    planetCard.querySelector(".open-location-button").addEventListener("click", () => {
      setLocalScope("planet", planet.id);
    });
    bindMovementButtons(planetCard);
    els.localSublocations.appendChild(planetCard);
  });
}

function renderSystemMap(state) {
  const map = document.createElement("section");
  map.className = "system-orbit-map";

  const stationCount = state.stations?.length || 1;
  const planetCount = state.planets.length;
  map.innerHTML = `
    <div class="system-orbit-map__header">
      <div>
        <small>System chart</small>
        <strong>${state.currentSystem.name}</strong>
      </div>
      <span>${stationCount} station${stationCount === 1 ? "" : "s"} - ${planetCount} planet${planetCount === 1 ? "" : "s"}</span>
    </div>
    <div class="local-orbit-chart" aria-label="${state.currentSystem.name} local system map">
      <svg class="local-orbit-rings" viewBox="0 0 100 100" aria-hidden="true">
        <circle class="local-orbit-ring station-ring" cx="50" cy="50" r="13"></circle>
        ${state.planets
          .map((planet, index) => `<circle class="local-orbit-ring" cx="50" cy="50" r="${localPlanetOrbit(index, planetCount)}"></circle>`)
          .join("")}
      </svg>
      <div class="local-star-node" aria-hidden="true">
        <span>${state.currentSystem.name}</span>
      </div>
    </div>
  `;

  const chart = map.querySelector(".local-orbit-chart");
  localStationMapNodes(state).forEach((station) => {
    const node = document.createElement("button");
    node.className = `local-body-node local-body-node--station${station.primary && selectedLocalTarget === "station" ? " is-active" : ""}`;
    node.style.left = `${station.x}%`;
    node.style.top = `${station.y}%`;
    node.setAttribute("aria-label", `Open ${station.name}`);
    node.title = station.primary ? `Open ${station.name}` : `${station.name} is charted in system details`;
    node.innerHTML = `
      <span>${station.name}</span>
      <small>${station.primary ? "Primary station" : "Station"}</small>
    `;
    node.addEventListener("click", () => {
      if (station.primary) {
        setLocalScope("station", "station");
        return;
      }
      showSystemCatalog(state.location);
      showToast(`${station.name} is charted in the system details catalog. Direct docking still uses the primary station.`, "info");
    });
    chart.appendChild(node);
  });

  state.planets.forEach((planet, index) => {
    const position = localPlanetPosition(index, planetCount);
    const node = document.createElement("button");
    node.className = `local-body-node local-body-node--planet${selectedLocalTarget === planet.id ? " is-active" : ""}`;
    node.style.left = `${position.x}%`;
    node.style.top = `${position.y}%`;
    node.setAttribute("aria-label", `Open ${planet.name}`);
    node.title = `${planet.name}: ${planet.type}, ${planet.flightStats.gravity}g`;
    node.innerHTML = `
      <span>${planet.name}</span>
      <small>${planet.flightStats.gravity}g - ${planet.placeCount.toLocaleString()} places</small>
    `;
    node.addEventListener("click", () => {
      setLocalScope("planet", planet.id);
    });
    chart.appendChild(node);
  });

  return map;
}

function localStationMapNodes(state) {
  const stations = state.stations?.length ? state.stations : [{ ...state.station, primary: true }];
  const stationCount = stations.length;
  return stations.map((station, index) => {
    const angle = ((stationCount === 1 ? -54 : -70 + (index * 360) / stationCount) * Math.PI) / 180;
    const radius = 13 + (station.primary ? -1.5 : 1.5);
    return {
      ...station,
      x: 50 + Math.cos(angle) * radius,
      y: 50 + Math.sin(angle) * radius,
    };
  });
}

function localPlanetPosition(index, total) {
  const radius = localPlanetOrbit(index, total);
  const angle = (((index + 1) * 137.508 + 22) * Math.PI) / 180;
  return {
    x: 50 + Math.cos(angle) * radius,
    y: 50 + Math.sin(angle) * radius,
  };
}

function localPlanetOrbit(index, total) {
  if (total <= 1) {
    return 32;
  }
  return 21 + (index / (total - 1)) * 23;
}

function renderStationDetail(state) {
  const isDocked = state.travelState.state === "docked" && state.travelState.near?.type === "station";
  els.localTargetMeta.textContent = "Station";
  els.localTargetTitle.textContent = state.station.name;
  els.localTargetSummary.textContent = isDocked
    ? `${state.station.areas.length} mapped station areas`
    : `Dock before entering station areas. ${state.station.movement.summary}`;
  els.localTargetActions.innerHTML = `
    <button id="backToSystemButton">Back to System</button>
    <button class="local-travel-button" data-movement="dock_station" ${movementDisabled(state.station.movement)}>
      ${state.station.movement?.isCurrent ? "Docked" : `Dock (${movementBrief(state.station.movement)})`}
    </button>
  `;
  els.localTargetActions.querySelector("#backToSystemButton").addEventListener("click", () => {
    setLocalScope("system", "station");
  });
  bindMovementButtons(els.localTargetActions);
  els.localSublocations.innerHTML = "";

  state.station.areas.forEach((area) => {
    const card = document.createElement("article");
    card.className = "place-card";
    const areaBlockedReason = !isDocked
      ? "Dock at the station before entering station areas."
      : state.currentPlace.id === area.id
        ? "You are already in this station area."
        : "";
    card.innerHTML = `
      <small>${area.faction} - ${area.wealth}</small>
      <strong>${area.name}</strong>
      <p>${area.description}</p>
      <div class="place-meta">
        <span>${area.economy}</span>
        <span>${area.security}</span>
        <span>${area.visited ? `${area.visits} visits` : "Unvisited"}</span>
      </div>
      <button ${areaBlockedReason ? disabledAttrs(areaBlockedReason) : ""}>
        ${!isDocked ? "Dock first" : state.currentPlace.id === area.id ? "Current area" : "Enter area"}
      </button>
    `;
    card.querySelector("button").addEventListener("click", () => {
      localScope = "place";
      sendAction({ action: "visit_place", placeId: area.id });
    });
    els.localSublocations.appendChild(card);
  });
}

function renderPlanetDetail(state, planet) {
  els.localTargetMeta.textContent = `${planet.type} - ${planet.wealth}`;
  els.localTargetTitle.textContent = planet.name;
  els.localTargetSummary.textContent = `${planet.placeCount.toLocaleString()} indexed places - ${planet.dominantFaction} - ${planet.flightStats.gravity}g / ${planet.flightStats.atmosphereDensity} atm`;
  els.localTargetActions.innerHTML = `
    <button id="backToSystemButton">Back to System</button>
    <button class="local-travel-button" data-movement="enter_orbit" data-planet-id="${planet.id}" ${movementDisabled(planet.orbitPreview)}>
      ${planet.orbitPreview?.isCurrent ? "In orbit" : `Enter orbit (${movementBrief(planet.orbitPreview)})`}
    </button>
    <button id="scanPlanetButton" ${
      planet.placeCount <= 0 ? disabledAttrs(`${planet.name} has no indexed places to scan.`) : ""
    }>Scan</button>
  `;
  els.localTargetActions.querySelector("#backToSystemButton").addEventListener("click", () => {
    setLocalScope("system", planet.id);
  });
  els.localTargetActions.querySelector("#scanPlanetButton").addEventListener("click", () => {
    sendAction({ action: "scan_planet", planetId: planet.id });
  });
  bindMovementButtons(els.localTargetActions);

  els.localSublocations.innerHTML = `
    ${
      planet.placeCount > 0
        ? `<form class="planet-jump">
            <label>
              Place #
              <input type="number" min="1" max="${planet.placeCount}" value="${planet.shownStart}" aria-label="${planet.name} place number">
            </label>
            <button>Land at # (${movementBrief(planet.landPreview)})</button>
          </form>`
        : `<div class="travel-preview">
            <span>No charted landing locations</span>
            <em>Conditions, survey coverage, or settlement history have left this body without visitable sites.</em>
          </div>`
    }
    <div class="flight-stats">
      <span>Size ${planet.flightStats.size}x</span>
      <span>Mass ${planet.flightStats.mass}x</span>
      <span>Gravity ${planet.flightStats.gravity}g</span>
      <span>Atmosphere ${planet.flightStats.atmosphereDensity}</span>
      <span>Landing ${planet.flightStats.landingDifficulty}</span>
    </div>
  `;

  const jumpForm = els.localSublocations.querySelector(".planet-jump");
  const jumpInput = els.localSublocations.querySelector("input");
  if (jumpForm && jumpInput) {
    jumpForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const index = clamp(Number(jumpInput.value), 1, planet.placeCount);
      localScope = "place";
      sendAction({ action: "local_travel", movement: "land", placeId: `planet:${planet.id}:${index}` });
    });
  }

  planet.places.forEach((sample) => {
    const sampleCard = document.createElement("div");
    sampleCard.className = "place-card compact";
    sampleCard.innerHTML = `
      <small>#${sample.index} - ${sample.kind}</small>
      <strong>${sample.name}</strong>
      <p>${sample.description}</p>
      <div class="place-meta">
        <span>${sample.faction}</span>
        <span>${sample.hazard} hazard</span>
        <span>${sample.visited ? `${sample.visits} visits` : "Unvisited"}</span>
      </div>
      ${renderPreview(sample.movement)}
      <button class="local-travel-button" data-movement="land" data-place-id="${sample.id}" ${movementDisabled(sample.movement)}>
        ${sample.movement?.isCurrent ? "Current site" : `${sample.visited ? "Return" : "Land"} (${movementBrief(sample.movement)})`}
      </button>
    `;
    bindMovementButtons(sampleCard);
    els.localSublocations.appendChild(sampleCard);
  });
}

function renderPlaceZoom(state) {
  const place = state.currentPlace;
  els.localTargetMeta.textContent = place.category === "planet" ? place.planetName : place.stationName;
  els.localTargetTitle.textContent = place.name;
  els.localTargetSummary.textContent = place.description;
  if (place.category === "planet") {
    const launch = state.travelState.options.find((option) => option.action === "launch");
    els.localTargetActions.innerHTML = `
      <button id="backToPlanetButton">Back to Planet</button>
      <button id="backToSystemButton">Back to System</button>
      ${
        launch
          ? `<button class="local-travel-button" data-movement="launch" title="${movementTitle(launch)}" ${movementDisabled(launch)}>
              Launch (${movementBrief(launch)})
            </button>`
          : ""
      }
      ${launch && movementReason(launch) ? `<p class="travel-warning">${movementReason(launch)}</p>` : ""}
    `;
    els.localTargetActions.querySelector("#backToPlanetButton").addEventListener("click", () => {
      setLocalScope("planet", place.planetId);
    });
  } else {
    const undock = state.travelState.options.find((option) => option.action === "undock");
    els.localTargetActions.innerHTML = `
      <button id="backToStationButton">Back to Station</button>
      <button id="backToSystemButton">Back to System</button>
      ${
        undock
          ? `<button class="local-travel-button" data-movement="undock" title="${movementTitle(undock)}" ${movementDisabled(undock)}>
              Undock (${movementBrief(undock)})
            </button>`
          : ""
      }
      ${undock && movementReason(undock) ? `<p class="travel-warning">${movementReason(undock)}</p>` : ""}
    `;
    els.localTargetActions.querySelector("#backToStationButton").addEventListener("click", () => {
      setLocalScope("station", "station");
    });
  }
  els.localTargetActions.querySelector("#backToSystemButton").addEventListener("click", () => {
    setLocalScope("system", selectedLocalTarget);
  });
  bindMovementButtons(els.localTargetActions);
  els.localSublocations.innerHTML = `
    <article class="place-card">
      <small>${place.category} - ${place.wealth}</small>
      <strong>${place.name}</strong>
      <p>${place.description}</p>
      <div class="place-meta">
        <span>${place.faction}</span>
        <span>${place.security}</span>
        <span>${place.visits ? `${place.visits} visits` : "Current"}</span>
      </div>
    </article>
  `;
}

function renderTravel(state) {
  els.travelList.innerHTML = "";
  state.travel.forEach((route) => {
    const card = document.createElement("article");
    card.className = `travel-card${route.id === plottedCourseId ? " plotted" : ""}`;
    card.innerHTML = `
      <small>${route.charted ? `${route.risk} risk` : "Uncharted signal"}</small>
      <strong>${route.name}</strong>
      <span>${route.fuelCost} fuel - ${route.timeCost} days</span>
      ${route.discoveryNote && !route.disabled ? `<p class="travel-note">${route.discoveryNote}</p>` : ""}
      ${route.blockedReason && !route.disabled ? `<p class="travel-warning">${route.blockedReason}</p>` : ""}
      ${route.warning ? `<p class="travel-warning">${route.warning}</p>` : ""}
      <div class="card-actions">
        <button class="details-button">${route.charted ? "Details" : "Signal"}</button>
        <button class="plot-button" ${
          route.disabled ? disabledAttrs(route.blockedReason || route.warning || "That route is not available from here.") : ""
        }>${route.id === plottedCourseId ? "Plotted" : route.charted ? "Plot course" : "Plot signal"}</button>
      </div>
    `;
    card.addEventListener("mouseenter", () => focusSystem(route.id));
    card.addEventListener("focusin", () => focusSystem(route.id));
    card.querySelector(".details-button").addEventListener("click", () => {
      showSystemCatalog(route.id);
    });
    card.querySelector(".plot-button").addEventListener("click", () => {
      plotCourse(route.id);
    });
    els.travelList.appendChild(card);
  });
}

function renderGates(state) {
  const gates = state.gates || [];
  const construction = state.gateConstruction;
  const knownGalaxies = state.knownGalaxies || [];
  els.gatePanel.innerHTML = `
    <div class="gate-header">
      <div>
        <small>Known galaxies / fold gates</small>
        <strong>${state.currentGalaxy.name}</strong>
        <span>${state.currentGalaxy.theme} - ${state.currentGalaxy.size.toLocaleString()} systems - ${state.currentGalaxy.risk} risk</span>
      </div>
      <div class="galaxy-chips">
        ${knownGalaxies.map((galaxy) => `<span>${galaxy.name}</span>`).join("")}
      </div>
    </div>
    <div class="gate-grid">
      ${
        gates.length
          ? gates.map(renderGateCard).join("")
          : `<article class="gate-card empty">
              <small>No active fold gate</small>
              <strong>Local space only</strong>
              <p>Explore for developed gate systems, ancient apertures, or deploy player-built anchors later.</p>
            </article>`
      }
      ${construction ? renderGateConstruction(construction) : ""}
    </div>
  `;

  els.gatePanel.querySelectorAll(".use-gate-button").forEach((button) => {
    button.addEventListener("click", () => {
      sendAction({ action: "use_gate", gateId: button.dataset.gateId });
    });
  });
  const buildButton = els.gatePanel.querySelector("#buildGateAnchorButton");
  if (buildButton) {
    buildButton.addEventListener("click", () => {
      sendAction({ action: "build_gate_anchor" });
    });
  }
}

function renderGateCard(gate) {
  return `
    <article class="gate-card ${gate.type}">
      <small>${gate.typeLabel} - ${gate.risk} risk</small>
      <strong>${gate.destinationGalaxyName}</strong>
      <p>${gate.destinationPreview}</p>
      <div class="place-meta">
        <span>${gate.fee ? `${credits(gate.fee)} fee` : "No fee"}</span>
        <span>${gate.timeCost} day alignment</span>
        <span>${gate.hidden ? "Hidden exit" : gate.destinationSystemName}</span>
      </div>
      ${gate.blockedReason ? `<p class="travel-warning">${gate.blockedReason}</p>` : ""}
      <button class="use-gate-button" data-gate-id="${gate.id}" ${
        gate.canUse ? "" : disabledAttrs(gate.blockedReason || "This fold gate is not available right now.")
      }>
        Use fold gate
      </button>
    </article>
  `;
}

function renderGateConstruction(construction) {
  const materials = construction.materials
    .map((material) => `${material.name} ${material.waived ? "waived" : `${material.owned}/${material.required}`}`)
    .join(" - ");
  return `
    <article class="gate-card player-build">
      <small>Player-built anchor</small>
      <strong>${construction.installedHere ? "Anchor installed" : "Deploy fold anchor"}</strong>
      <p>${construction.anchors} owned anchor${construction.anchors === 1 ? "" : "s"}. ${materials}</p>
      <div class="place-meta">
        <span>${credits(construction.price)}</span>
        <span>2 day deployment</span>
      </div>
      ${construction.blockedReason ? `<p class="travel-warning">${construction.blockedReason}</p>` : ""}
      <button id="buildGateAnchorButton" ${
        construction.canBuild ? "" : disabledAttrs(construction.blockedReason || "You cannot build a fold anchor here right now.")
      }>Build anchor</button>
    </article>
  `;
}

function showSystemCatalog(systemId, planetId = null) {
  if (!currentState) {
    showToast("The system catalog is still loading.", "warning");
    return;
  }
  const system = currentState.systemCatalog.find((item) => item.id === systemId);
  if (!system) {
    showToast("That system is not in the current galaxy catalog yet. Chart it or use a fold gate into its galaxy first.", "warning");
    return;
  }
  activeView = "navigation";
  navigationMode = "catalog";
  catalogSystemId = systemId;
  focusedSystemId = systemId;
  catalogPlanetId = planetId || system?.planets[0]?.id || null;
  render(currentState);
}

function showRoutePlanner() {
  navigationMode = "routes";
  render(currentState);
}

function renderCatalogDetail(state) {
  if (!state) {
    return;
  }
  if (!catalogSystemId || !state.systemCatalog.some((system) => system.id === catalogSystemId)) {
    catalogSystemId = focusedSystemId || state.location;
  }

  const system = state.systemCatalog.find((item) => item.id === catalogSystemId) || state.systemCatalog[0];
  const route = state.travel.find((item) => item.id === system.id);
  const isCurrent = system.id === state.location;
  if (!system.charted) {
    renderUnchartedCatalogDetail(system, route, isCurrent);
    return;
  }
  if (!catalogPlanetId || !system.planets.some((planet) => planet.id === catalogPlanetId)) {
    catalogPlanetId = system.planets[0]?.id || null;
  }
  const planet = system.planets.find((item) => item.id === catalogPlanetId);
  const canPlot = !isCurrent;

  els.catalogDetail.innerHTML = `
    <div class="catalog-header">
      <div>
        <small>${isCurrent ? "Current system" : "System details"}</small>
        <h3>${system.name}</h3>
        <p>${system.description}</p>
        <div class="place-meta">
          <span>${system.faction}</span>
          <span>${system.economy}</span>
          <span>${system.risk} risk</span>
          ${route ? `<span>${route.fuelCost} fuel</span>` : ""}
        </div>
        ${route?.blockedReason && !isCurrent ? `<p class="travel-warning">${route.blockedReason}</p>` : ""}
      </div>
      <div class="catalog-actions">
        <button id="backToRoutesButton">Back to Routes</button>
        <button id="catalogPlotButton" ${
          canPlot ? "" : disabledAttrs("You are already in this system. Select another system to plot a course.")
        }>${system.id === plottedCourseId ? "Course plotted" : "Plot course"}</button>
      </div>
    </div>
    <section class="catalog-section">
      <div class="catalog-section__header">
        <small>Fold access</small>
        <strong>${system.gates?.length || 0} local gate${system.gates?.length === 1 ? "" : "s"}</strong>
      </div>
      <div class="resource-grid compact">
        ${
          system.gates?.length
            ? system.gates
                .map(
                  (gate) => `
                    <div class="resource-card ${gate.type === "ancient" ? "secondary" : "primary"}">
                      <small>${gate.typeLabel}</small>
                      <strong>${gate.destinationGalaxyName}</strong>
                      <span>${gate.destinationPreview}</span>
                      <em>${gate.fee ? `${credits(gate.fee)} fee` : "No fee"} - ${gate.risk} risk</em>
                    </div>
                  `
                )
                .join("")
            : `<div class="resource-card signal-card">
                <small>No gate</small>
                <strong>Local jumps only</strong>
                <span>This system has no active fold infrastructure on current charts.</span>
              </div>`
        }
      </div>
    </section>
    <section class="catalog-section">
      <div class="catalog-section__header">
        <small>Elements and resources</small>
        <strong>Local survey profile</strong>
      </div>
      <div class="resource-grid">
        ${system.resources.map(renderResourceCard).join("")}
      </div>
    </section>
    <section class="catalog-section">
      <div class="catalog-section__header">
        <small>Stations</small>
        <strong>${system.stations.length} known stations</strong>
      </div>
      <p>Primary services use the main dock for now; the station network is charted here for planning and world detail.</p>
      <div class="resource-grid compact">
        ${system.stations
          .map(
            (station) => `
              <div class="resource-card">
                <small>${station.areaCount} areas</small>
                <strong>${station.name}</strong>
                <span>${station.areas.map((area) => area.economy).slice(0, 3).join(", ")}</span>
                <em>${station.areas.map((area) => area.faction).slice(0, 2).join(" / ")}</em>
              </div>
            `
          )
          .join("")}
      </div>
    </section>
    <section class="catalog-section planet-catalog">
      <div class="catalog-section__header">
        <small>Planets</small>
        <strong>${system.planets.length} known bodies</strong>
      </div>
      <div class="planet-catalog__grid">
        <div class="planet-button-list">
          ${system.planets
            .map(
              (item) => `
                <button class="catalog-planet-button${item.id === catalogPlanetId ? " is-active" : ""}" data-planet-id="${item.id}">
                  <small>${item.type}</small>
                  <strong>${item.name}</strong>
                  <span>${item.placeCount.toLocaleString()} places - ${item.flightStats.gravity}g</span>
                </button>
              `
            )
            .join("")}
        </div>
        <div class="planet-detail-panel">
          ${planet ? renderCatalogPlanetDetail(planet) : "<p>No planets charted in this system.</p>"}
        </div>
      </div>
    </section>
  `;

  els.catalogDetail.querySelector("#backToRoutesButton").addEventListener("click", showRoutePlanner);
  els.catalogDetail.querySelector("#catalogPlotButton").addEventListener("click", () => {
    plotCourse(system.id);
    navigationMode = "catalog";
    render(currentState);
  });
  els.catalogDetail.querySelectorAll(".catalog-planet-button").forEach((button) => {
    button.addEventListener("click", () => {
      catalogPlanetId = button.dataset.planetId;
      renderCatalogDetail(currentState);
    });
  });
}

function renderUnchartedCatalogDetail(system, route, isCurrent) {
  const canPlot = !isCurrent;
  els.catalogDetail.innerHTML = `
    <div class="catalog-header signal-header">
      <div>
        <small>Uncharted signal</small>
        <h3>${system.name}</h3>
        <p>${system.signalReading || system.description}</p>
        <div class="place-meta">
          <span>${system.economy}</span>
          <span>${system.faction}</span>
          <span>${route ? `${route.fuelCost} fuel` : system.estimatedDistance}</span>
          ${route?.timeCost ? `<span>${route.timeCost} day burn</span>` : ""}
        </div>
        ${route?.discoveryNote ? `<p class="travel-note">${route.discoveryNote}</p>` : ""}
        ${route?.blockedReason && !isCurrent ? `<p class="travel-warning">${route.blockedReason}</p>` : ""}
        ${route?.warning ? `<p class="travel-warning">${route.warning}</p>` : ""}
      </div>
      <div class="catalog-actions">
        <button id="backToRoutesButton">Back to Routes</button>
        <button id="catalogPlotButton" ${
          canPlot ? "" : disabledAttrs("You are already in this system. Select another system to plot a course.")
        }>${system.id === plottedCourseId ? "Course plotted" : "Plot signal"}</button>
      </div>
    </div>
    <section class="catalog-section signal-section">
      <div class="catalog-section__header">
        <small>Scanner inference</small>
        <strong>No local catalog yet</strong>
      </div>
      <p>${system.hiddenSummary}</p>
      <div class="resource-grid compact">
        <div class="resource-card signal-card">
          <small>Planets</small>
          <strong>Unknown</strong>
          <span>Close survey required before body count, terrain, and gravity data can be trusted.</span>
        </div>
        <div class="resource-card signal-card">
          <small>Stations</small>
          <strong>Unknown</strong>
          <span>Docking services and faction control will resolve after arrival.</span>
        </div>
      </div>
    </section>
  `;

  els.catalogDetail.querySelector("#backToRoutesButton").addEventListener("click", showRoutePlanner);
  els.catalogDetail.querySelector("#catalogPlotButton").addEventListener("click", () => {
    plotCourse(system.id);
    navigationMode = "catalog";
    render(currentState);
  });
}

function renderResourceCard(resource) {
  return `
    <div class="resource-card ${resource.richness.toLowerCase()}">
      <small>${resource.richness}</small>
      <strong>${resource.name}</strong>
      <span>${resource.localPrice} cr local market</span>
      <em>${resource.note}</em>
    </div>
  `;
}

function renderCatalogPlanetDetail(planet) {
  return `
    <small>${planet.type} - ${planet.wealth}</small>
    <strong>${planet.name}</strong>
    <p>${planet.placeCount.toLocaleString()} indexed places, mostly influenced by ${planet.dominantFaction}.</p>
    <div class="flight-stats">
      <span>Size ${planet.flightStats.size}x</span>
      <span>Mass ${planet.flightStats.mass}x</span>
      <span>Gravity ${planet.flightStats.gravity}g</span>
      <span>Atmosphere ${planet.flightStats.atmosphereDensity}</span>
      <span>Landing ${planet.flightStats.landingDifficulty}</span>
    </div>
    <div class="place-meta">
      ${planet.resourceHints.map((hint) => `<span>${hint}</span>`).join("")}
    </div>
    <div class="planet-detail-columns">
      <div>
        <small>Terrain</small>
        <p>${planet.terrain.join(", ")}</p>
      </div>
      <div>
        <small>Factions</small>
        <p>${planet.factions.join(", ")}</p>
      </div>
    </div>
  `;
}

function renderMissions(state) {
  els.activeMission.classList.toggle("is-visible", Boolean(state.activeMission));
  if (state.activeMission) {
    els.activeMission.innerHTML = `
      <strong>${state.activeMission.title}</strong>
      Deliver ${state.activeMission.cargo} to ${systemName(state, state.activeMission.destination)}
      by day ${state.activeMission.dueDay} for ${credits(state.activeMission.reward)}.
    `;
  } else {
    els.activeMission.innerHTML = "";
  }

  els.missionList.innerHTML = "";
  state.missions.forEach((mission) => {
    const card = document.createElement("article");
    card.className = "mission-card";
    card.innerHTML = `
      <small>${mission.risk} risk · ${mission.cargoWeight} cargo</small>
      <strong>${mission.title}</strong>
      <p>Move ${mission.cargo} by day ${mission.dueDay} for ${credits(mission.reward)}.</p>
      <button ${
        state.activeMission ? disabledAttrs("You already have an active contract. Finish it before accepting another.") : ""
      }>Accept</button>
    `;
    card.querySelector("button").addEventListener("click", () => {
      sendAction({ action: "accept_mission", missionId: mission.id });
    });
    els.missionList.appendChild(card);
  });
}

function renderMarket(state) {
  els.marketContext.innerHTML = `
    <strong>${state.marketContext.name}</strong>
    <span>${state.marketContext.summary}</span>
  `;
  els.market.innerHTML = "";
  state.market.forEach((item) => {
    const row = document.createElement("div");
    row.className = "market-row";
    row.innerHTML = `
      <div>
        <strong>${item.name}</strong>
        <small>${credits(item.price)} - ${item.scarcity}</small>
        <em>Source: ${item.source} (${item.sourceDistanceLabel || `${item.sourceDistance} fuel`}) - ${item.localNote}</em>
      </div>
      <input type="number" min="1" value="1" aria-label="${item.name} quantity">
      <button>Buy</button>
      <button>Sell</button>
    `;
    const input = row.querySelector("input");
    row.querySelectorAll("button")[0].addEventListener("click", () => {
      sendAction({ action: "buy", good: item.id, quantity: input.value });
    });
    row.querySelectorAll("button")[1].addEventListener("click", () => {
      sendAction({ action: "sell", good: item.id, quantity: input.value });
    });
    els.market.appendChild(row);
  });
}

function renderShip(state) {
  const stats = state.ship.stats;
  els.shipSummary.innerHTML = `
    <article class="ship-service-card">
      <small>Local ship service</small>
      <strong>${state.ship.serviceLocation}</strong>
      <span>${state.ship.serviceSummary || state.ship.installBlockedReason}</span>
    </article>
    <article>
      <small>Fuel capacity</small>
      <strong>${stats.maxFuel}</strong>
      <span>${stats.jumpFuelDiscount ? `${stats.jumpFuelDiscount}% jump savings` : "Stock jump burn"}</span>
    </article>
    <article>
      <small>Cargo frame</small>
      <strong>${stats.cargoCapacity}</strong>
      <span>${state.cargoUsed} currently used</span>
    </article>
    <article>
      <small>Hull integrity</small>
      <strong>${stats.maxHull}</strong>
      <span>${state.hull} current hull</span>
    </article>
    <article>
      <small>Local flight</small>
      <strong>${stats.localFuelDiscount || 0}%</strong>
      <span>Fuel savings</span>
    </article>
  `;

  renderShipAiPanel(state);

  els.upgradeList.innerHTML = "";
  state.ship.upgrades.forEach((upgrade) => {
    const card = document.createElement("article");
    card.className = `upgrade-card${upgrade.availableHere ? " is-offered" : " is-unavailable"}${upgrade.canInstall ? "" : " is-blocked"}`;
    const materials = upgrade.materials
      .map(
        (material) => `
          <span class="${material.waived ? "waived" : material.missing ? "missing" : ""}">
            ${material.name} ${material.waived ? "waived" : `${material.owned}/${material.required}`}
          </span>
        `
      )
      .join("");
    card.innerHTML = `
      <div>
        <small>${upgrade.system} - Tier ${upgrade.tier}/${upgrade.maxTier} - ${upgrade.availableHere ? upgrade.quality : "not stocked here"}</small>
        <strong>${upgrade.name}</strong>
        <p>${upgrade.description}</p>
      </div>
      <div class="upgrade-effect">
        <span>${upgrade.currentEffect}</span>
        ${upgrade.nextEffect ? `<em>Next: ${upgrade.nextEffect}</em>` : ""}
      </div>
      <div class="upgrade-materials">
        <small>${upgrade.partsLabel}</small>
        ${materials || "<span>No materials required</span>"}
      </div>
      <div class="upgrade-actions">
        <button data-upgrade-id="${upgrade.id}" ${
          upgrade.canInstall ? "" : disabledAttrs(upgrade.blockedReason || "That upgrade is not available here right now.")
        }>
          ${upgrade.nextCost ? `Install - ${credits(upgrade.nextCost)}` : "Max tier"}
        </button>
        ${upgrade.blockedReason ? `<span>${upgrade.blockedReason}</span>` : ""}
      </div>
    `;
    card.querySelector("button").addEventListener("click", () => {
      sendAction({ action: "buy_upgrade", upgradeId: upgrade.id });
    });
    els.upgradeList.appendChild(card);
  });
}

function renderShipAiPanel(state) {
  const ai = state.shipAi;
  if (!ai) {
    els.shipAiPanel.innerHTML = "";
    return;
  }
  if (!ai.configured) {
    els.shipAiPanel.innerHTML = `
      <article class="ship-ai-card">
        <div>
          <small>Ship AI core - blank imprint</small>
          <strong>${escapeHtml(ai.name)}</strong>
          <p>${escapeHtml(ai.description)}</p>
        </div>
        <div class="ship-ai-form">
          <label>
            AI name
            <input id="shipAiName" maxlength="42" placeholder="Example: Selene">
          </label>
          <label>
            Voice / gender
            <select id="shipAiGender">
              <option value="Female">Female</option>
              <option value="Male">Male</option>
            </select>
          </label>
          <label class="ship-ai-description">
            Personality paragraph
            <textarea id="shipAiDescription" rows="4" maxlength="900" placeholder="Describe how the AI speaks, behaves, jokes, flirts, advises, or argues. This imprint is permanent unless you strip the core later."></textarea>
          </label>
          <button id="configureShipAiButton">Imprint AI core</button>
        </div>
      </article>
    `;
    els.shipAiPanel.querySelector("#configureShipAiButton").addEventListener("click", configureShipAi);
    return;
  }

  els.shipAiPanel.innerHTML = `
    <article class="ship-ai-card is-locked">
      <div>
        <small>Ship AI core - locked personality</small>
        <strong>${escapeHtml(ai.name)}</strong>
        <p>${escapeHtml(ai.description)}</p>
        <div class="ship-ai-meta">
          <span>${escapeHtml(ai.gender)}</span>
          <span>Generation ${ai.generation}</span>
          <span>${ai.installedDay ? `Installed day ${ai.installedDay}` : "Installed"}</span>
        </div>
      </div>
      <div class="ship-ai-actions">
        <button id="stripShipAiButton" ${ai.canStrip ? "" : disabledAttrs(`AI core extraction requires ${credits(ai.replacementCost)}.`)}>
          Strip core - ${credits(ai.replacementCost)}
        </button>
        <span>${escapeHtml(ai.lockedReason)}</span>
      </div>
    </article>
  `;
  els.shipAiPanel.querySelector("#stripShipAiButton").addEventListener("click", () => {
    sendAction({ action: "strip_ship_ai" });
  });
}

function configureShipAi() {
  const name = els.shipAiPanel.querySelector("#shipAiName")?.value || "";
  const gender = els.shipAiPanel.querySelector("#shipAiGender")?.value || "Female";
  const description = els.shipAiPanel.querySelector("#shipAiDescription")?.value || "";
  sendAction({
    action: "configure_ship_ai",
    name,
    gender,
    description,
  });
}

function renderInventory(state) {
  els.inventory.innerHTML = "";
  state.inventory.forEach((item) => {
    const row = document.createElement("div");
    row.className = "inventory-row";
    row.innerHTML = `
      <strong>${item.name}</strong>
      <span>${item.amount} units</span>
      <span>${item.weight} ton</span>
    `;
    els.inventory.appendChild(row);
  });
}

function renderLog(state) {
  els.log.innerHTML = "";
  [...state.log].reverse().forEach((entry) => {
    const item = document.createElement("li");
    item.textContent = entry;
    els.log.appendChild(item);
  });
}

function renderServiceButtons(state) {
  const isDocked = state.travelState.state === "docked";
  const near = state.travelState.nearLabel;
  const travelLabel = state.travelState.label.toLowerCase();
  setActionAvailability(
    els.refuelButton,
    isDocked,
    isDocked ? `Station pumps are available at ${near}` : `Station refuel requires docking. You are ${travelLabel} near ${near}.`
  );
  setActionAvailability(
    els.rescueButton,
    state.travelState.rescueAvailable,
    state.travelState.rescueAvailable
      ? "Call a fuel service to your current position."
      : rescueFuelExplanation(state)
  );
  els.serviceHelp.innerHTML = `
    <div class="${isDocked ? "is-available" : "is-blocked"}">
      <strong>Station refuel</strong>
      <span>${
        isDocked
          ? `Available here because you are docked at ${near}.`
          : `Unavailable because you are ${travelLabel} near ${near}. Station pumps require docking.`
      }</span>
    </div>
    <div class="${state.travelState.rescueAvailable ? "is-available" : "is-blocked"}">
      <strong>Rescue fuel</strong>
      <span>${rescueFuelExplanation(state)}</span>
    </div>
  `;
}

function setActionAvailability(button, isAvailable, reason) {
  button.title = reason || "";
  if (isAvailable) {
    button.removeAttribute("aria-disabled");
    delete button.dataset.disabledReason;
    return;
  }
  button.setAttribute("aria-disabled", "true");
  button.dataset.disabledReason = reason || "That action is not available right now.";
}

function renderCheats(state) {
  if (!els.cheatList) {
    return;
  }
  const cheats = state.cheats || [];
  els.cheatList.innerHTML = cheats
    .map(
      (cheat) => `
        <label class="cheat-toggle">
          <input type="checkbox" data-cheat-id="${cheat.id}" ${cheat.enabled ? "checked" : ""}>
          <span>
            <strong>${cheat.label}</strong>
            <em>${cheat.description}</em>
          </span>
        </label>
      `
    )
    .join("");

  els.cheatList.querySelectorAll("input[type='checkbox']").forEach((input) => {
    input.addEventListener("change", () => {
      sendAction({
        action: "set_cheat",
        cheat: input.dataset.cheatId,
        enabled: input.checked,
      });
    });
  });
}

function openSettings() {
  els.settingsOverlay.classList.remove("is-hidden");
  loadProviderSettings();
}

function closeSettings() {
  els.settingsOverlay.classList.add("is-hidden");
}

function renderMovementButtons(options) {
  if (!options?.length) {
    return "";
  }
  return `
    <div class="movement-panel">
      ${options
        .map(
          (option) => `
            <div class="movement-control">
              <button
                class="local-travel-button"
                data-movement="${option.action}"
                title="${movementTitle(option)}"
                ${movementDisabled(option)}
              >
              ${option.label} (${movementBrief(option)})
              </button>
              ${movementReason(option) ? `<span>${movementReason(option)}</span>` : ""}
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function bindMovementButtons(root) {
  root.querySelectorAll(".local-travel-button").forEach((button) => {
    button.addEventListener("click", () => {
      const movement = button.dataset.movement;
      const planetId = button.dataset.planetId;
      const placeId = button.dataset.placeId;
      if (movement === "land") {
        localScope = "place";
      }
      if (movement === "dock_station") {
        localScope = "station";
        selectedLocalTarget = "station";
      }
      if (movement === "enter_orbit" && planetId) {
        selectedLocalTarget = planetId;
      }
      sendAction({
        action: "local_travel",
        movement,
        planetId,
        placeId,
      });
    });
  });
}

function renderPreview(preview) {
  if (!preview) {
    return "";
  }
  const warning = preview.blockedReason || preview.warnings?.[0] || "";
  return `
    <div class="travel-preview">
      <span>${movementBrief(preview)}</span>
      <span>${preview.timeLabel}</span>
      <span>${preview.risk} risk</span>
      ${warning ? `<em>${warning}</em>` : ""}
    </div>
  `;
}

function movementBrief(preview) {
  if (!preview) {
    return "unavailable";
  }
  if (preview.isCurrent) {
    return "current";
  }
  if (preview.blockedReason) {
    return "blocked";
  }
  return `${preview.fuelCost} fuel`;
}

function movementDisabled(preview) {
  const reason = movementBlockReason(preview);
  return reason ? disabledAttrs(reason) : "";
}

function movementTitle(preview) {
  return movementBlockReason(preview) || movementReason(preview) || preview?.summary || "";
}

function movementReason(preview) {
  if (!preview) {
    return "No route is available from the current travel state.";
  }
  return preview.blockedReason || preview.warnings?.[0] || "";
}

function movementBlockReason(preview) {
  if (!preview) {
    return "No route is available from the current travel state.";
  }
  if (preview.isCurrent) {
    return preview.currentMessage || "The ship is already at that local destination.";
  }
  if (preview.blockedReason) {
    return preview.blockedReason;
  }
  if (!preview.canAfford) {
    return preview.warnings?.[0] || `Not enough fuel for that move. It requires ${preview.fuelCost} fuel.`;
  }
  return "";
}

function rescueFuelExplanation(state) {
  if (state.travelState.rescueAvailable) {
    return `Available at your current position, but it costs more and advances time.`;
  }
  if (state.travelState.state === "docked") {
    return "Not needed while docked. Station pumps are the normal option.";
  }
  if (state.fuel >= state.maxFuel) {
    return "Unavailable because your tanks are already full.";
  }
  return "Unavailable from the current travel state.";
}

function systemName(state, id) {
  return state.systems.find((system) => system.id === id)?.name || id;
}

function breadcrumbParts(state) {
  const parts = ["Galaxy", state.currentSystem.name];
  if (state.currentPlace.category === "planet") {
    parts.push(state.currentPlace.planetName);
  } else {
    parts.push(state.currentPlace.stationName);
  }
  parts.push(state.currentPlace.name);
  return parts;
}

function courseStatusText(state) {
  if (!plottedCourseId) {
    return "None";
  }
  const route = state.travel.find((item) => item.id === plottedCourseId);
  if (!route) {
    return "None";
  }
  return route.canCommit ? `${route.name} (${route.fuelCost} fuel)` : `${route.name} blocked`;
}

function chartScale(value, min, max, size) {
  if (max === min) {
    return size / 2;
  }
  const padding = size * 0.14;
  return padding + ((value - min) / (max - min)) * (size - padding * 2);
}

function zoomGalaxy(factor) {
  const rect = els.sectorMap.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  const nextZoom = clampNumber(mapChart.zoom * factor, 0.42, 2.8);
  const worldX = (centerX - mapChart.panX) / mapChart.zoom;
  const worldY = (centerY - mapChart.panY) / mapChart.zoom;
  mapChart.zoom = nextZoom;
  mapChart.panX = centerX - worldX * nextZoom;
  mapChart.panY = centerY - worldY * nextZoom;
  applyMapTransform();
}

function fitGalaxy() {
  const rect = els.sectorMap.getBoundingClientRect();
  if (!rect.width || !rect.height) {
    return false;
  }
  mapChart.zoom = Math.min(rect.width / galaxySize.width, rect.height / galaxySize.height) * 0.92;
  mapChart.panX = (rect.width - galaxySize.width * mapChart.zoom) / 2;
  mapChart.panY = (rect.height - galaxySize.height * mapChart.zoom) / 2;
  applyMapTransform();
  return true;
}

function applyMapTransform() {
  const chart = els.sectorMap.querySelector(".galaxy-chart");
  if (!chart) {
    return;
  }
  chart.style.transform = `translate(${mapChart.panX}px, ${mapChart.panY}px) scale(${mapChart.zoom})`;
  els.zoomLevel.textContent = `${Math.round(mapChart.zoom * 100)}%`;
}

function scale(value, min, max) {
  if (max === min) {
    return 50;
  }
  return 12 + ((value - min) / (max - min)) * 76;
}

function credits(value) {
  return `${Number(value).toLocaleString()} cr`;
}

function isCheatEnabled(state, cheatId) {
  return Boolean(state.cheats?.some((cheat) => cheat.id === cheatId && cheat.enabled));
}

function clamp(value, min, max) {
  if (Number.isNaN(value)) {
    return min;
  }
  return Math.min(max, Math.max(min, Math.floor(value)));
}

function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function hashString(value) {
  return String(value || "").split("").reduce((hash, char) => {
    return ((hash << 5) - hash + char.charCodeAt(0)) >>> 0;
  }, 2166136261);
}

function storageGet(key) {
  try {
    return window.localStorage.getItem(key) || "";
  } catch {
    return "";
  }
}

function storageSet(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    return false;
  }
  return true;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    };
    return entities[char];
  });
}

els.exploreButtons.forEach((button) => {
  button.addEventListener("click", () => sendAction({ action: "explore" }));
});
els.refuelButton.addEventListener("click", () => sendAction({ action: "refuel" }));
els.rescueButton.addEventListener("click", () => sendAction({ action: "rescue_refuel" }));
els.repairButton.addEventListener("click", () => sendAction({ action: "repair" }));
els.waitButton.addEventListener("click", () => sendAction({ action: "wait" }));
els.loginButton.addEventListener("click", () => submitAuth("login"));
els.registerButton.addEventListener("click", () => submitAuth("register"));
els.authPassword.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    submitAuth("login");
  }
});
els.logoutButton.addEventListener("click", logout);
els.notesButton.addEventListener("click", () => openNotes());
els.notesCloseButton.addEventListener("click", closeNotes);
els.notesOverlay.addEventListener("click", (event) => {
  if (event.target === els.notesOverlay) {
    closeNotes();
  }
});
els.saveNoteButton.addEventListener("click", saveCurrentNote);
els.commsButton.addEventListener("click", openComms);
els.commsCloseButton.addEventListener("click", closeComms);
els.commsOverlay.addEventListener("click", (event) => {
  if (event.target === els.commsOverlay) {
    closeComms();
  }
});
els.commsTabs.querySelectorAll("button").forEach((button) => {
  button.addEventListener("click", async () => {
    activeCommsChannel = button.dataset.channel;
    socialMessages = [];
    renderComms();
    if (activeCommsChannel === "global" || activeCommsChannel === "local") {
      await refreshCommsContext(false);
    }
  });
});
els.commsForm.addEventListener("submit", sendCommsMessage);
els.commsInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) {
    return;
  }
  event.preventDefault();
  els.commsForm.requestSubmit();
});
els.settingsButton.addEventListener("click", openSettings);
els.settingsCloseButton.addEventListener("click", closeSettings);
els.settingsOverlay.addEventListener("click", (event) => {
  if (event.target === els.settingsOverlay) {
    closeSettings();
  }
});
els.saveProviderButton.addEventListener("click", saveProviderSettings);
els.newGameButton.addEventListener("click", () => sendAction({ action: "new_game" }));
els.navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activeView = button.dataset.view;
    renderView();
  });
});
els.localScopeTabs.forEach((button) => {
  button.addEventListener("click", () => {
    if (!currentState) {
      return;
    }
    const nextScope = button.dataset.scope;
    if (nextScope === "planet" && selectedLocalTarget === "station") {
      showToast("Select a planet before opening the Planet zoom level.", "warning");
      return;
    }
    setLocalScope(nextScope);
  });
});
els.zoomOutButton.addEventListener("click", () => zoomGalaxy(0.82));
els.zoomInButton.addEventListener("click", () => zoomGalaxy(1.22));
els.fitGalaxyButton.addEventListener("click", () => {
  mapChart.fitted = fitGalaxy();
});
els.expandMapButton.addEventListener("click", () => {
  mapExpanded = !mapExpanded;
  mapChart.fitted = false;
  renderView();
  window.requestAnimationFrame(() => {
    mapChart.fitted = fitGalaxy();
  });
});
els.sectorMap.addEventListener("wheel", (event) => {
  event.preventDefault();
  zoomGalaxy(event.deltaY > 0 ? 0.9 : 1.1);
});
els.sectorMap.addEventListener("pointerdown", (event) => {
  if (event.target.closest(".system-node")) {
    return;
  }
  mapChart.dragging = true;
  mapChart.dragStartX = event.clientX;
  mapChart.dragStartY = event.clientY;
  mapChart.dragPanX = mapChart.panX;
  mapChart.dragPanY = mapChart.panY;
  els.sectorMap.setPointerCapture(event.pointerId);
  els.sectorMap.classList.add("is-dragging");
});
els.sectorMap.addEventListener("pointermove", (event) => {
  if (!mapChart.dragging) {
    return;
  }
  mapChart.panX = mapChart.dragPanX + event.clientX - mapChart.dragStartX;
  mapChart.panY = mapChart.dragPanY + event.clientY - mapChart.dragStartY;
  applyMapTransform();
});
els.sectorMap.addEventListener("pointerup", (event) => {
  mapChart.dragging = false;
  els.sectorMap.releasePointerCapture(event.pointerId);
  els.sectorMap.classList.remove("is-dragging");
});
els.sectorMap.addEventListener("pointercancel", (event) => {
  mapChart.dragging = false;
  els.sectorMap.releasePointerCapture(event.pointerId);
  els.sectorMap.classList.remove("is-dragging");
});
window.addEventListener("resize", () => {
  if (activeView === "navigation") {
    mapChart.fitted = fitGalaxy();
  }
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !els.settingsOverlay.classList.contains("is-hidden")) {
    closeSettings();
  }
  if (event.key === "Escape" && !els.commsOverlay.classList.contains("is-hidden")) {
    closeComms();
  }
  if (event.key === "Escape" && !els.notesOverlay.classList.contains("is-hidden")) {
    closeNotes();
  }
});

if (speechSupported()) {
  loadSpeechVoices();
  window.speechSynthesis.onvoiceschanged = loadSpeechVoices;
}

fetchState();
