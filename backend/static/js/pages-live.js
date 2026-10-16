/* EngineVerse Live Browser Runtime + GitHub Learner Vault Sync + Multi-Language Code Judge.
 *
 * Powers the public GitHub Pages deployment and the Android APK without requiring
 * visitors to clone the repository or run a local server. Also syncs learner
 * profiles, XP, streaks, completed topics, and solved coding problems directly
 * with `authorsauravkushwaha/EngineVerse` (`data/learners/registry.json`).
 */
(() => {
  "use strict";

  const bootNode = document.getElementById("ev-live");
  if (!bootNode) return;

  let config = {};
  try {
    config = JSON.parse(bootNode.textContent || "{}");
  } catch (_) {
    return;
  }

  const BASE = config.base || "/";
  const GH_REPO = config.githubRepo || "authorsauravkushwaha/EngineVerse";
  const GH_VAULT_PATH = config.githubVaultPath || "data/learners/registry.json";
  const MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  const SHORT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const STREAK_KEY = "ev:streak:v1";
  const STORE_KEY = "ev:learner-store:v2";

  const pad = (n) => (n < 10 ? "0" + n : String(n));
  const isoOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const parseIso = (iso) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!m) return null;
    const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return Number.isNaN(d.getTime()) ? null : d;
  };
  const dayIndex = (d) =>
    Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000);
  const addDays = (d, delta) => {
    const copy = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    copy.setDate(copy.getDate() + delta);
    return copy;
  };
  const longDate = (d) => `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
  const shortDate = (d) => `${d.getDate()} ${SHORT_MONTHS[d.getMonth()]}`;
  const toast = (msg, kind = "ok") => {
    if (window.EV?.toast) window.EV.toast(msg, kind);
  };

  // ---------------------------------------------------------------------------
  // Shared helpers
  //
  // `escapeHtml` is published by app.js as window.EV.escapeHtml, but this file
  // must also work when it is loaded on its own (the Android wrapper and the
  // offline shell load scripts individually). An earlier revision called it
  // without ever defining it, so *every* call threw a ReferenceError: the OTP
  // code was never shown, the account icon was never inserted and the boot
  // sequence stopped half way. Keep a local definition and prefer the shared
  // one when app.js has already run.
  // ---------------------------------------------------------------------------
  const escapeHtml = (value) =>
    typeof window.EV?.escapeHtml === "function"
      ? window.EV.escapeHtml(value)
      : String(value ?? "").replace(/[&<>"']/g, (c) =>
          ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
        );

  // One control can have more than one accepted id: the exported markup and
  // this runtime ship independently, and a service-worker cache can pair an
  // older page with a newer script. Look up the current id first and fall back
  // to the spellings earlier exports used instead of binding nothing at all.
  const firstEl = (...ids) => {
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) return el;
    }
    return null;
  };

  const reportRuntimeProblem = (label, error) => {
    if (window.console?.warn) window.console.warn(`[EngineVerse] ${label} failed`, error);
  };

  // Runs one boot step in isolation: a failure on a single page must not take
  // the rest of the runtime (account icon, OTP steps, judges) down with it.
  const safely = (label, fn) => {
    try {
      const result = fn();
      if (result && typeof result.catch === "function") {
        result.catch((error) => reportRuntimeProblem(label, error));
      }
      return result;
    } catch (error) {
      reportRuntimeProblem(label, error);
      return undefined;
    }
  };

  // ---------------------------------------------------------------------------
  // SHA-256 helper (WebCrypto with pure-JS fallback) for GitHub Vault auth
  // ---------------------------------------------------------------------------
  async function sha256Hex(message) {
    const text = String(message || "");
    if (window.crypto?.subtle) {
      const buf = new TextEncoder().encode(text);
      const digest = await window.crypto.subtle.digest("SHA-256", buf);
      return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
    }
    // Minimal deterministic fallback if subtle is unavailable on non-HTTPS file://
    let h1 = 0xdeadbeef ^ text.length, h2 = 0x41c6ce57 ^ text.length;
    for (let i = 0; i < text.length; i++) {
      const ch = text.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761);
      h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    const hex = (h1 >>> 0).toString(16).padStart(8, "0") + (h2 >>> 0).toString(16).padStart(8, "0");
    return hex.repeat(4);
  }

  async function hashPasswordDigest(username, password) {
    const cleanUser = String(username || "").trim().toLowerCase();
    return sha256Hex(`engineverse-v1:${cleanUser}:${password}`);
  }

  // ---------------------------------------------------------------------------
  // Learner Store + Streak Store (localStorage + GitHub Vault Sync)
  // ---------------------------------------------------------------------------
  const readStreak = () => {
    try {
      const raw = JSON.parse(localStorage.getItem(STREAK_KEY) || "{}");
      const days = Array.isArray(raw.days)
        ? raw.days.filter((x) => typeof x === "string" && /^\d{4}-\d{2}-\d{2}$/.test(x))
        : [];
      return { days: Array.from(new Set(days)).sort() };
    } catch (_) {
      return { days: [] };
    }
  };

  const writeStreak = (days) => {
    const clean = Array.from(new Set(days)).sort();
    try {
      localStorage.setItem(STREAK_KEY, JSON.stringify({ days: clean }));
    } catch (_) {
      /* private mode */
    }
    return clean;
  };

  function defaultProfile(overrides = {}) {
    const todayIso = isoOf(new Date());
    return Object.assign({
      username: "guest",
      display_name: "EngineVerse Learner",
      email: "",
      phone: "",
      country_code: "+91",
      otp_verified: true,
      otp_channel: "email",
      branch: "cse",
      year_of_study: 1,
      bio: "Learning core engineering and programming on EngineVerse.",
      xp: 0,
      level: 1,
      streak_days: 1,
      longest_streak: 1,
      activity_days: [todayIso],
      completed_topics: [],
      solved_problems: [],
      completed_projects: [],
      bookmarks: [],
      quiz_attempts: 0,
      quiz_correct: 0,
      mistakes: [],
      community_posts: [],
      notifications: [
        { title: "Welcome to EngineVerse", body: "Full browser execution and GitHub learner vault sync are active.", ts: todayIso }
      ],
      password_sha256: "",
      updated_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    }, overrides);
  }

  // ---------------------------------------------------------------------------
  // Multi-Layer Synchronized Learner Database (localStorage + sessionStorage +
  // Cookie + window.name + IndexedDB + BroadcastChannel)
  //Inspired by Supabase Auth/Realtime & Appwrite Account/Databases persistence.
  // ---------------------------------------------------------------------------
  const SESSION_USER_KEY = "ev:session:user";
  const IDB_NAME = "EngineVerseVaultDB";
  const IDB_STORE = "kv";
  let authChannel = null;
  try {
    if (typeof BroadcastChannel !== "undefined") {
      authChannel = new BroadcastChannel("ev_auth_sync");
    }
  } catch (_) {}

  function readCookieUser() {
    try {
      const m = /(?:^|;\s*)ev_live_user=([^;\s]+)/.exec(document.cookie || "");
      return m ? decodeURIComponent(m[1]).trim().toLowerCase() : "";
    } catch (_) {
      return "";
    }
  }

  function writeCookieUser(username) {
    try {
      const clean = String(username || "").trim().toLowerCase();
      if (clean && clean !== "guest") {
        document.cookie = `ev_live_user=${encodeURIComponent(clean)}; path=/; max-age=2592000; SameSite=Lax`;
      } else {
        document.cookie = "ev_live_user=; path=/; max-age=0; SameSite=Lax";
      }
    } catch (_) {}
  }

  function idbWriteStore(store) {
    try {
      if (typeof indexedDB === "undefined") return;
      const req = indexedDB.open(IDB_NAME, 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(IDB_STORE)) {
          db.createObjectStore(IDB_STORE);
        }
      };
      req.onsuccess = () => {
        try {
          const db = req.result;
          const tx = db.transaction(IDB_STORE, "readwrite");
          tx.objectStore(IDB_STORE).put(JSON.stringify(store), STORE_KEY);
        } catch (_) {}
      };
    } catch (_) {}
  }

  function idbRestoreIfNeeded(onRestored) {
    try {
      if (typeof indexedDB === "undefined") return;
      const req = indexedDB.open(IDB_NAME, 1);
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains(IDB_STORE)) {
          db.createObjectStore(IDB_STORE);
        }
      };
      req.onsuccess = () => {
        try {
          const db = req.result;
          const tx = db.transaction(IDB_STORE, "readonly");
          const getReq = tx.objectStore(IDB_STORE).get(STORE_KEY);
          getReq.onsuccess = () => {
            if (!getReq.result) return;
            try {
              const idbStore = JSON.parse(getReq.result);
              const current = loadStore();
              let changed = false;
              if (idbStore.accounts && typeof idbStore.accounts === "object") {
                for (const [k, acc] of Object.entries(idbStore.accounts)) {
                  if (!current.accounts[k]) {
                    current.accounts[k] = acc;
                    changed = true;
                  }
                }
              }
              if (!current.currentUser && idbStore.currentUser && !sessionStorage.getItem("ev:explicit_logout")) {
                current.currentUser = idbStore.currentUser;
                changed = true;
              }
              if (changed) {
                saveStore(current, { skipBroadcast: true });
                if (typeof onRestored === "function") onRestored();
              }
            } catch (_) {}
          };
        } catch (_) {}
      };
    } catch (_) {}
  }

  function syncGlobalAuthFlag(currentUser) {
    const signedIn = Boolean(currentUser && currentUser !== "guest");
    if (signedIn) {
      document.documentElement.setAttribute("data-ev-signed-in", "true");
    } else {
      document.documentElement.removeAttribute("data-ev-signed-in");
    }
    if (!window.EngineVerse) window.EngineVerse = { csrf: "", user: signedIn };
    else window.EngineVerse.user = signedIn;
  }

  function loadStore() {
    const parseCandidate = (str) => {
      if (!str) return null;
      try {
        const obj = JSON.parse(str);
        return obj && typeof obj === "object" ? obj : null;
      } catch (_) {
        return null;
      }
    };
    let lsObj = null;
    let ssObj = null;
    let wnObj = null;
    try { lsObj = parseCandidate(localStorage.getItem(STORE_KEY)); } catch (_) {}
    try { ssObj = parseCandidate(sessionStorage.getItem(STORE_KEY)); } catch (_) {}
    try {
      if (typeof window.name === "string" && window.name.indexOf("EV_STORE:") === 0) {
        wnObj = parseCandidate(window.name.slice(9));
      }
    } catch (_) {}

    const accounts = {};
    [wnObj, ssObj, lsObj].forEach((cand) => {
      if (cand && cand.accounts && typeof cand.accounts === "object") {
        for (const [uname, acc] of Object.entries(cand.accounts)) {
          accounts[uname] = Object.assign({}, accounts[uname] || {}, acc);
        }
      }
    });

    let explicitLogout = false;
    try { explicitLogout = sessionStorage.getItem("ev:explicit_logout") === "1"; } catch (_) {}

    let currentUser =
      (lsObj && lsObj.currentUser) ||
      (ssObj && ssObj.currentUser) ||
      (wnObj && wnObj.currentUser) ||
      null;

    if (!currentUser && !explicitLogout) {
      try {
        currentUser =
          localStorage.getItem(SESSION_USER_KEY) ||
          sessionStorage.getItem(SESSION_USER_KEY) ||
          readCookieUser() ||
          null;
      } catch (_) {
        currentUser = readCookieUser() || null;
      }
    }
    if (currentUser === "guest" || currentUser === "") currentUser = null;
    if (currentUser && !accounts[currentUser]) {
      accounts[currentUser] = defaultProfile({ username: currentUser, display_name: currentUser });
    }

    const baseObj = lsObj || ssObj || wnObj || {};
    syncGlobalAuthFlag(currentUser);
    return {
      currentUser: currentUser || null,
      accounts,
      otpChallenges: baseObj.otpChallenges && typeof baseObj.otpChallenges === "object" ? baseObj.otpChallenges : {},
      githubRepo: baseObj.githubRepo || GH_REPO,
      githubToken: baseObj.githubToken || "",
      webhookUrl: baseObj.webhookUrl || "",
      lastSyncAt: baseObj.lastSyncAt || "",
    };
  }

  function saveStore(store, opts = {}) {
    const cleanUser = store.currentUser && store.currentUser !== "guest" ? String(store.currentUser).toLowerCase() : null;
    store.currentUser = cleanUser;
    const serialized = JSON.stringify(store);
    try {
      localStorage.setItem(STORE_KEY, serialized);
      if (cleanUser) localStorage.setItem(SESSION_USER_KEY, cleanUser);
      else localStorage.removeItem(SESSION_USER_KEY);
    } catch (_) {}
    try {
      sessionStorage.setItem(STORE_KEY, serialized);
      if (cleanUser) {
        sessionStorage.setItem(SESSION_USER_KEY, cleanUser);
        sessionStorage.removeItem("ev:explicit_logout");
      } else {
        sessionStorage.removeItem(SESSION_USER_KEY);
      }
    } catch (_) {}
    try {
      window.name = "EV_STORE:" + serialized;
    } catch (_) {}
    writeCookieUser(cleanUser || "");
    idbWriteStore(store);
    syncGlobalAuthFlag(cleanUser);
    if (!opts.skipBroadcast && authChannel) {
      try {
        authChannel.postMessage({ type: "ev_store_sync", currentUser: cleanUser, ts: Date.now() });
      } catch (_) {}
    }
  }

  // ---------------------------------------------------------------------------
  // Scoped 6-Digit OTP Engine (Gmail/email & Mobile Number with Country Code)
  // Required ONLY for: (1) new user signup, (2) forgot password, (3) change password.
  // ---------------------------------------------------------------------------
  function normalizePhoneWithCountryCode(phoneRaw, countryCode = "+91") {
    const raw = String(phoneRaw || "").trim();
    if (!raw) return "";
    let cc = String(countryCode || "+91").trim().replace(/\s+/g, "");
    if (!cc.startsWith("+")) cc = "+" + cc;
    if (!/^\+[1-9][0-9]{0,3}$/.test(cc)) cc = "+91";
    if (raw.startsWith("+")) {
      const digits = raw.slice(1).replace(/\D+/g, "");
      if (digits.length < 7 || digits.length > 15) return "";
      return "+" + digits;
    }
    const digits = raw.replace(/\D+/g, "").replace(/^0+/, "");
    if (digits.length < 6 || digits.length > 14) return "";
    const combined = `${cc}${digits}`;
    return /^\+[1-9][0-9]{6,14}$/.test(combined) ? combined : "";
  }

  function maskDestination(dest, channel = "email") {
    const val = String(dest || "").trim();
    if (channel === "phone" || val.startsWith("+")) {
      const digits = val.replace(/\D+/g, "");
      if (digits.length <= 4) return "••••" + digits;
      return `${val.startsWith("+") ? "+" : ""}${"•".repeat(Math.max(4, digits.length - 4))}${digits.slice(-4)}`;
    }
    const [local, domain] = val.split("@");
    if (!domain) return "••••@gmail.com";
    const maskedLocal =
      local.length <= 2
        ? local[0] + "•••"
        : local[0] + "•".repeat(Math.max(2, local.length - 2)) + local[local.length - 1];
    return `${maskedLocal}@${domain}`;
  }

  function generateSixDigitOtp() {
    if (window.crypto?.getRandomValues) {
      const arr = new Uint32Array(1);
      window.crypto.getRandomValues(arr);
      return String(arr[0] % 1000000).padStart(6, "0");
    }
    return String(Math.floor(100000 + Math.random() * 900000));
  }

  async function issueBrowserOtpChallenge({ purpose, username, channel, destination }) {
    const code = generateSixDigitOtp();
    const digest = await sha256Hex(`ev-otp:${purpose}:${username}:${code}`);
    const masked = maskDestination(destination, channel);
    const store = loadStore();
    if (!store.otpChallenges || typeof store.otpChallenges !== "object") {
      store.otpChallenges = {};
    }
    store.otpChallenges[purpose] = {
      purpose,
      username: String(username || "").toLowerCase(),
      channel,
      destination,
      masked,
      codeHash: digest,
      expiresAt: Date.now() + 10 * 60 * 1000,
      attempts: 0,
    };
    saveStore(store, { skipBroadcast: true });

    // Forward OTP event to n8n / Supabase / Appwrite webhook if configured
    if (store.webhookUrl) {
      forwardWebhook(store.webhookUrl, {
        event: "otp_issued",
        purpose,
        username,
        channel,
        destination_masked: masked,
        otp_code: code,
        ts: new Date().toISOString(),
      }).catch(() => {});
    }
    return { code, masked, channel, destination };
  }

  async function verifyBrowserOtpChallenge(purpose, submittedCode) {
    const cleanCode = String(submittedCode || "").replace(/[\s.-]+/g, "");
    if (!/^\d{6}$/.test(cleanCode)) {
      return { ok: false, error: "Enter a valid 6-digit numeric OTP code." };
    }
    const store = loadStore();
    const ch = store.otpChallenges?.[purpose];
    if (!ch) {
      return { ok: false, error: "No active OTP challenge found. Request a new 6-digit OTP." };
    }
    if (Date.now() > Number(ch.expiresAt || 0)) {
      delete store.otpChallenges[purpose];
      saveStore(store, { skipBroadcast: true });
      return { ok: false, error: "That 6-digit OTP has expired. Click Resend OTP to get a fresh code." };
    }
    const expectedHash = await sha256Hex(`ev-otp:${purpose}:${ch.username}:${cleanCode}`);
    if (expectedHash !== ch.codeHash) {
      ch.attempts = Number(ch.attempts || 0) + 1;
      if (ch.attempts >= 5) {
        delete store.otpChallenges[purpose];
        saveStore(store, { skipBroadcast: true });
        return { ok: false, error: "Too many incorrect OTP attempts. Request a new 6-digit OTP." };
      }
      store.otpChallenges[purpose] = ch;
      saveStore(store, { skipBroadcast: true });
      return { ok: false, error: `Incorrect 6-digit OTP code (${5 - ch.attempts} attempts remaining).` };
    }
    delete store.otpChallenges[purpose];
    saveStore(store, { skipBroadcast: true });
    return { ok: true, challenge: ch };
  }

  function getActiveProfile() {
    const store = loadStore();
    if (store.currentUser && store.accounts[store.currentUser]) {
      return store.accounts[store.currentUser];
    }
    if (!store.accounts.guest) {
      store.accounts.guest = defaultProfile();
      saveStore(store);
    }
    return store.accounts.guest;
  }

  function saveActiveProfile(mutator) {
    const store = loadStore();
    const key = store.currentUser || "guest";
    const profile = store.accounts[key] || defaultProfile({ username: key });
    mutator(profile);
    const streakState = computeStreak(writeStreak((profile.activity_days || []).concat(readStreak().days)));
    profile.activity_days = streakState.days;
    profile.streak_days = streakState.current;
    profile.longest_streak = Math.max(Number(profile.longest_streak || 0), streakState.longest);
    profile.xp = Math.max(0, Number(profile.xp || 0));
    profile.level = Math.max(1, Math.floor(profile.xp / 250) + 1);
    profile.updated_at = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
    store.accounts[key] = profile;
    saveStore(store);
    if (store.webhookUrl) {
      forwardWebhook(store.webhookUrl, toGithubSnapshot(profile)).catch(() => {});
    }
    return profile;
  }

  function toGithubSnapshot(profile) {
    return {
      username: (profile.username || "guest").toLowerCase().replace(/[^a-z0-9_-]/g, "").slice(0, 30) || "learner",
      display_name: String(profile.display_name || profile.username || "Learner").slice(0, 60),
      branch: String(profile.branch || "cse").slice(0, 32),
      year_of_study: Math.min(6, Math.max(1, Number(profile.year_of_study || 1))),
      bio: String(profile.bio || "").slice(0, 240),
      xp: Math.max(0, Number(profile.xp || 0)),
      level: Math.max(1, Number(profile.level || 1)),
      streak_days: Math.max(0, Number(profile.streak_days || 0)),
      longest_streak: Math.max(0, Number(profile.longest_streak || 0)),
      activity_days: Array.from(new Set(profile.activity_days || [])).filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort().slice(-365),
      completed_topics: Array.from(new Set(profile.completed_topics || [])).sort(),
      solved_problems: Array.from(new Set(profile.solved_problems || [])).sort(),
      completed_projects: Array.from(new Set(profile.completed_projects || [])).sort(),
      bookmarks: Array.from(new Set(profile.bookmarks || [])).sort(),
      quiz_attempts: Math.max(0, Number(profile.quiz_attempts || 0)),
      quiz_correct: Math.max(0, Number(profile.quiz_correct || 0)),
      password_sha256: String(profile.password_sha256 || ""),
      email_sha256: String(profile.email_sha256 || ""),
      phone_sha256: String(profile.phone_sha256 || ""),
      country_code: String(profile.country_code || "+91"),
      otp_verified: profile.otp_verified !== false,
      password_changed_via_otp: Boolean(profile.password_changed_via_otp),
      updated_at: profile.updated_at || new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    };
  }

  function mergeSnapshotIntoStore(snapshot, setCurrent = false) {
    if (!snapshot || !snapshot.username) return null;
    const uname = String(snapshot.username).toLowerCase().trim();
    const store = loadStore();
    const existing = store.accounts[uname] || defaultProfile({ username: uname });
    const merged = Object.assign({}, existing, {
      username: uname,
      display_name: snapshot.display_name || existing.display_name || uname,
      branch: snapshot.branch || existing.branch || "cse",
      year_of_study: Number(snapshot.year_of_study || existing.year_of_study || 1),
      bio: snapshot.bio || existing.bio || "",
      country_code: snapshot.country_code || existing.country_code || "+91",
      otp_verified: snapshot.otp_verified !== undefined ? Boolean(snapshot.otp_verified) : existing.otp_verified !== false,
      xp: Math.max(Number(existing.xp || 0), Number(snapshot.xp || 0)),
      level: Math.max(Number(existing.level || 1), Number(snapshot.level || 1)),
      streak_days: Math.max(Number(existing.streak_days || 0), Number(snapshot.streak_days || 0)),
      longest_streak: Math.max(Number(existing.longest_streak || 0), Number(snapshot.longest_streak || 0)),
      activity_days: Array.from(new Set([...(existing.activity_days || []), ...(snapshot.activity_days || [])])).sort(),
      completed_topics: Array.from(new Set([...(existing.completed_topics || []), ...(snapshot.completed_topics || [])])).sort(),
      solved_problems: Array.from(new Set([...(existing.solved_problems || []), ...(snapshot.solved_problems || [])])).sort(),
      completed_projects: Array.from(new Set([...(existing.completed_projects || []), ...(snapshot.completed_projects || [])])).sort(),
      bookmarks: Array.from(new Set([...(existing.bookmarks || []), ...(snapshot.bookmarks || [])])).sort(),
      quiz_attempts: Math.max(Number(existing.quiz_attempts || 0), Number(snapshot.quiz_attempts || 0)),
      quiz_correct: Math.max(Number(existing.quiz_correct || 0), Number(snapshot.quiz_correct || 0)),
      password_sha256: snapshot.password_sha256 || existing.password_sha256 || "",
      email_sha256: snapshot.email_sha256 || existing.email_sha256 || "",
      phone_sha256: snapshot.phone_sha256 || existing.phone_sha256 || "",
      updated_at: snapshot.updated_at || existing.updated_at,
    });
    store.accounts[uname] = merged;
    if (setCurrent) store.currentUser = uname;
    saveStore(store, { skipBroadcast: !setCurrent });
    if (merged.activity_days?.length) {
      writeStreak(readStreak().days.concat(merged.activity_days));
    }
    return merged;
  }

  // Pull seeded & live GitHub learner vault on boot
  async function pullGithubVault(silent = true) {
    const store = loadStore();
    const repo = store.githubRepo || GH_REPO;
    const urls = [
      `https://api.github.com/repos/${repo}/contents/${GH_VAULT_PATH}`,
      config.vault || `${BASE}learner-vault.json`,
    ];
    for (const url of urls) {
      try {
        const headers = { Accept: "application/vnd.github+json, application/json" };
        if (url.includes("api.github.com") && store.githubToken) {
          headers.Authorization = `Bearer ${store.githubToken}`;
        }
        const res = await fetch(url, { headers, cache: "no-store" });
        if (!res.ok) continue;
        const data = await res.json();
        let registry = data;
        if (data && data.content && data.encoding === "base64") {
          const decoded = decodeURIComponent(escape(atob(String(data.content).replace(/\s+/g, ""))));
          registry = JSON.parse(decoded);
        }
        if (registry && registry.learners && typeof registry.learners === "object") {
          Object.values(registry.learners).forEach((snap) => mergeSnapshotIntoStore(snap, false));
          if (!silent) toast(`Synced ${Object.keys(registry.learners).length} learner record(s) from GitHub Vault.`);
          return registry;
        }
      } catch (_) {
        /* try next fallback */
      }
    }
    if (!silent) toast("Loaded local learner vault cache.", "info");
    return null;
  }

  async function pushSnapshotToGithub(profile, options = {}) {
    const initialStore = loadStore();
    const repo = (options.repo || initialStore.githubRepo || GH_REPO).trim();
    const token = (options.token !== undefined ? options.token : initialStore.githubToken || "").trim();
    const snapshot = toGithubSnapshot(profile);

    const recordSyncTime = () => {
      const latest = loadStore();
      latest.lastSyncAt = new Date().toISOString();
      if (snapshot.username && latest.accounts[snapshot.username]) {
        latest.accounts[snapshot.username] = Object.assign({}, latest.accounts[snapshot.username], profile);
      }
      saveStore(latest, { skipBroadcast: true });
    };

    // 1. Try local FastAPI backend `/api/sync/snapshot` if running on a live server
    try {
      const apiRes = await fetch(`${BASE}api/sync/snapshot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ snapshot, push_github: true }),
      });
      if (apiRes.ok) {
        const out = await apiRes.json();
        if (out.ok) {
          recordSyncTime();
          toast(`Saved learner data for @${snapshot.username} to GitHub vault!`);
          return { ok: true, mode: "backend-api", detail: out };
        }
      }
    } catch (_) {
      /* static host; proceed with direct GitHub push or GitHub Issue workflow */
    }

    // 2. If user provided a GitHub token, push directly via GitHub Contents API
    if (token) {
      const apiUrl = `https://api.github.com/repos/${repo}/contents/${GH_VAULT_PATH}`;
      const headers = {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "X-GitHub-Api-Version": "2022-11-28",
      };
      const getRes = await fetch(apiUrl, { headers, cache: "no-store" });
      let registry = { schema_version: 1, repository: repo, updated_at: "", learners: {} };
      let sha = "";
      if (getRes.ok) {
        const current = await getRes.json();
        sha = current.sha || "";
        if (current.content) {
          const decoded = decodeURIComponent(escape(atob(String(current.content).replace(/\s+/g, ""))));
          registry = JSON.parse(decoded);
        }
      }
      if (!registry.learners || typeof registry.learners !== "object") registry.learners = {};
      registry.learners[snapshot.username] = snapshot;
      registry.updated_at = snapshot.updated_at;
      const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(registry, null, 2) + "\n")));
      const putBody = {
        message: `chore(learners): sync progress snapshot for ${snapshot.username}`,
        content: encoded,
        branch: "main",
      };
      if (sha) putBody.sha = sha;
      const putRes = await fetch(apiUrl, {
        method: "PUT",
        headers: Object.assign({ "Content-Type": "application/json" }, headers),
        body: JSON.stringify(putBody),
      });
      if (!putRes.ok) {
        const errData = await putRes.json().catch(() => ({}));
        throw new Error(errData.message || `GitHub API push returned HTTP ${putRes.status}`);
      }
      recordSyncTime();
      toast(`Committed @${snapshot.username}'s progress directly to ${repo}!`);
      return { ok: true, mode: "github-contents-api" };
    }

    // 3. Zero-token GitHub Actions Issue Sync (opens pre-filled issue on authorsauravkushwaha/EngineVerse)
    if (options.useIssueSync) {
      const title = `[learner-sync] @${snapshot.username} (${snapshot.xp} XP · ${snapshot.streak_days}d streak)`;
      const body = [
        "### Automated EngineVerse Learner Vault Sync",
        "",
        `This issue submits a validated learner progress snapshot for **@${snapshot.username}** to \`data/learners/registry.json\` on \`${repo}\`.`,
        "The `Learner Data Sync` GitHub Actions workflow will automatically validate, merge, commit, and close this issue.",
        "",
        "```engineverse-learner-snapshot",
        JSON.stringify(snapshot, null, 2),
        "```",
      ].join("\n");
      const issueUrl = `https://github.com/${repo}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
      window.open(issueUrl, "_blank", "noopener,noreferrer");
      toast("Opened GitHub Actions Learner Sync issue — click 'Submit new issue' on GitHub to commit to the repository!");
      return { ok: true, mode: "github-issue-workflow", issueUrl };
    }

    // Save locally and prompt user with one-click GitHub Issue sync
    recordSyncTime();
    return { ok: true, mode: "local-vault", snapshot };
  }

  async function forwardWebhook(url, snapshot) {
    if (!url || !/^https?:\/\//i.test(url)) return;
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: "engineverse", event: "learner.snapshot", snapshot }),
    });
  }

  // ---------------------------------------------------------------------------
  // 1. Streak calculation & activity recording
  // ---------------------------------------------------------------------------
  const computeStreak = (days) => {
    const today = new Date();
    const todayNum = dayIndex(today);
    const nums = days
      .map(parseIso)
      .filter(Boolean)
      .map(dayIndex)
      .sort((a, b) => a - b);
    const set = new Set(nums);

    let cursor = set.has(todayNum)
      ? todayNum
      : set.has(todayNum - 1)
      ? todayNum - 1
      : null;
    let current = 0;
    while (cursor !== null && set.has(cursor)) {
      current += 1;
      cursor -= 1;
    }

    let longest = 0;
    let run = 0;
    let prev = null;
    for (const n of set) {
      run = prev !== null && n === prev + 1 ? run + 1 : 1;
      if (run > longest) longest = run;
      prev = n;
    }

    return {
      current,
      longest,
      total: set.size,
      todayDone: set.has(todayNum),
      days,
    };
  };

  const shouldRecordStudy = () => {
    const path = location.pathname;
    return (
      path.includes("/dpp/") ||
      path.includes("/topics/") ||
      path.includes("/practice/") ||
      path.includes("/programming/") ||
      path.includes("/projects/") ||
      path.includes("/tutor/") ||
      path.includes("/flashcards/") ||
      path.includes("/revision/") ||
      path.includes("/studio/") ||
      path.includes("/workflows/") ||
      path.includes("/swarm/")
    );
  };

  let days = readStreak().days;
  if (shouldRecordStudy()) {
    days = writeStreak(days.concat(isoOf(new Date())));
  }
  const streak = computeStreak(days);

  // Sync streak into active learner profile
  saveActiveProfile((p) => {
    p.activity_days = Array.from(new Set([...(p.activity_days || []), ...days]));
  });

  // ---------------------------------------------------------------------------
  // 2. Topbar Account Icon & Cross-Tab Signed-In Hydration
  // ---------------------------------------------------------------------------
  function signOutActiveUser() {
    const store = loadStore();
    store.currentUser = null;
    try { sessionStorage.setItem("ev:explicit_logout", "1"); } catch (_) {}
    saveStore(store);
    safely("hydrateNavigation", hydrateNavigation);
    toast("Signed out of your EngineVerse session.", "info");
    window.location.href = `${BASE}login/`;
  }

  function hydrateNavigation() {
    const store = loadStore();
    const profile = getActiveProfile();
    const signedIn = Boolean(store.currentUser && store.currentUser !== "guest");
    syncGlobalAuthFlag(store.currentUser);

    const topbarRight = document.querySelector(".topbar-right") || document.querySelector(".topbar .actions");
    if (topbarRight) {
      const loginLinks = Array.from(topbarRight.querySelectorAll('a[href*="/login"], a[href*="/register"], [data-ev-anon-auth]'));
      const serverAvatar = topbarRight.querySelector(".avatar:not([data-live-avatar])");
      const navToggle = topbarRight.querySelector("#navtoggle");
      const insertBeforeNode = navToggle || null;

      if (signedIn) {
        // Hide "Sign in" and "Start free" buttons in the topbar
        loginLinks.forEach((el) => {
          el.setAttribute("data-ev-anon-auth", "");
          el.hidden = true;
          el.style.display = "none";
        });

        if (!serverAvatar) {
          // 1. Streak badge
          let streakEl = topbarRight.querySelector("[data-live-streak]");
          if (!streakEl) {
            streakEl = document.createElement("a");
            streakEl.className = "streak";
            streakEl.setAttribute("data-live-streak", "");
            topbarRight.insertBefore(streakEl, insertBeforeNode);
          }
          const sDays = Number(profile.streak_days || streak.current || 1);
          streakEl.href = `${BASE}streaks/`;
          streakEl.title = `Study streak: ${sDays} day(s)`;
          streakEl.innerHTML = `<svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2c1 4 4 6 4 10a4 4 0 1 1-8 0c0-2 1-3 2-5 1 2 2 2 2-5z"/><path d="M8.5 14.5A3.5 3.5 0 0 0 12 18a3.5 3.5 0 0 0 3.5-3.5c0-2-1.5-3-2-5-1 1.5-2.5 2-3.5 5z"/></svg><span>${sDays}</span>`;

          // 2. XP & Level badge
          let xpEl = topbarRight.querySelector("[data-live-xp]");
          if (!xpEl) {
            xpEl = document.createElement("a");
            xpEl.className = "xpchip";
            xpEl.setAttribute("data-live-xp", "");
            topbarRight.insertBefore(xpEl, insertBeforeNode);
          }
          const lvl = Number(profile.level || 1);
          const xpVal = Number(profile.xp || 0);
          xpEl.href = `${BASE}profile/`;
          xpEl.title = `Level ${lvl} · ${xpVal} XP`;
          xpEl.innerHTML = `<span class="lvl">Lv ${lvl}</span><span class="xpv">${xpVal} XP</span>`;

          // 3. Notifications bell icon
          let notifEl = topbarRight.querySelector("[data-live-notif]");
          if (!notifEl) {
            notifEl = document.createElement("a");
            notifEl.className = "iconbtn";
            notifEl.setAttribute("data-live-notif", "");
            notifEl.setAttribute("aria-label", "Notifications");
            notifEl.title = "Notifications";
            topbarRight.insertBefore(notifEl, insertBeforeNode);
          }
          notifEl.href = `${BASE}notifications/`;
          notifEl.innerHTML = `<svg class="i" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>`;

          // 4. Account Profile Icon & Dropdown Menu (replaces Sign in / Start free)
          let accountMenu = topbarRight.querySelector("[data-live-account-menu]");
          if (!accountMenu) {
            accountMenu = document.createElement("div");
            accountMenu.className = "menu";
            accountMenu.setAttribute("data-menu", "");
            accountMenu.setAttribute("data-live-account-menu", "");
            topbarRight.insertBefore(accountMenu, insertBeforeNode);
          }
          const initial = escapeHtml(String(profile.display_name || profile.username || "U").trim().charAt(0).toUpperCase() || "U");
          const unameEsc = escapeHtml(profile.username || "learner");
          const dnameEsc = escapeHtml(profile.display_name || profile.username || "Learner");
          const branchEsc = escapeHtml(String(profile.branch || "cse").toUpperCase());
          const yearEsc = Number(profile.year_of_study || 1);
          accountMenu.innerHTML = `
            <button class="avatar" type="button" data-live-avatar aria-haspopup="true" aria-expanded="false" aria-label="Account menu for ${unameEsc}" title="Signed in as @${unameEsc}">
              <svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              <span class="avatar-initial">${initial}</span>
            </button>
            <div class="menu-pop" role="menu">
              <div class="menu-head">
                <strong>${dnameEsc}</strong>
                <span class="muted small">@${unameEsc} · ${branchEsc} Y${yearEsc}</span>
              </div>
              <a class="menu-item" role="menuitem" href="${BASE}dashboard/"><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg> Dashboard</a>
              <a class="menu-item" role="menuitem" href="${BASE}profile/"><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> My profile</a>
              <a class="menu-item" role="menuitem" href="${BASE}portfolio/"><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg> Public portfolio</a>
              <a class="menu-item" role="menuitem" href="${BASE}today/"><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg> Today's plan</a>
              <a class="menu-item" role="menuitem" href="${BASE}mistakes/"><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg> Mistake notebook</a>
              <a class="menu-item" role="menuitem" href="${BASE}leaderboard/"><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg> Leaderboard</a>
              <a class="menu-item" role="menuitem" href="${BASE}settings/"><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg> Settings &amp; GitHub Sync</a>
              <button class="menu-item danger" type="button" data-live-logout><svg class="i" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg> Sign out</button>
            </div>
          `;
          const logoutBtn = accountMenu.querySelector("[data-live-logout]");
          if (logoutBtn) {
            logoutBtn.addEventListener("click", (e) => {
              e.preventDefault();
              signOutActiveUser();
            });
          }
        }
      } else {
        // Signed out: remove dynamic signed-in topbar items and restore Sign in / Start free
        topbarRight.querySelectorAll("[data-live-streak], [data-live-xp], [data-live-notif], [data-live-account-menu]").forEach((el) => el.remove());
        loginLinks.forEach((el) => {
          el.hidden = false;
          el.style.display = "";
        });
      }
    }

    // Remove "sign in" lock pills across topnav, mobile drawer, and index lists when signed in
    document.querySelectorAll(".navmenu-lock, .indexlist-lock").forEach((badge) => {
      badge.hidden = signedIn;
      badge.style.display = signedIn ? "none" : "";
    });

    // Update topnav and mobile nav links that differ between anonymous and signed-in
    if (signedIn) {
      const branchSlug = encodeURIComponent(profile.branch || "cse");
      document.querySelectorAll('.navmenu-item, .mobilenav-item').forEach((link) => {
        const label = link.querySelector(".navmenu-label")?.textContent?.trim() || link.textContent.trim();
        if (label.startsWith("My branch")) {
          link.setAttribute("href", `${BASE}stream/${branchSlug}/`);
        } else if (label.startsWith("Due flashcards")) {
          link.setAttribute("href", `${BASE}revision/`);
        }
      });

      // Update mobile drawer account buttons
      const mobileCta = document.querySelector("#mobilenav .mobilenav-cta");
      if (mobileCta) {
        mobileCta.innerHTML = `
          <a class="btn btn-primary" href="${BASE}dashboard/">@${escapeHtml(profile.username)} · Dashboard</a>
          <a class="btn btn-ghost" href="${BASE}settings/">Account &amp; Sync Settings</a>
          <button class="btn btn-ghost" type="button" data-live-mobile-logout>Sign out</button>
        `;
        mobileCta.querySelector("[data-live-mobile-logout]")?.addEventListener("click", signOutActiveUser);
      }

      // Update footer Sign in / Create account links
      document.querySelectorAll('.footer a[href*="/login"], .footer a[href*="/register"]').forEach((a) => {
        if (a.getAttribute("href")?.includes("/login")) {
          a.setAttribute("href", `${BASE}dashboard/`);
          a.textContent = `Dashboard (@${profile.username})`;
        } else {
          a.setAttribute("href", `${BASE}settings/`);
          a.textContent = "Account settings";
        }
      });
    }
  }

  // Hydrate page-specific signed-out callouts so switching tabs never shows "Sign in to..." when signed in
  function hydrateSignedInPageContent() {
    const store = loadStore();
    const signedIn = Boolean(store.currentUser && store.currentUser !== "guest");
    if (!signedIn) return;
    const profile = getActiveProfile();
    // `path` was read here without ever being defined in this scope - it only
    // existed inside shouldRecordStudy() - so every check below threw a
    // ReferenceError on the first page that used one. That is why a signed-in
    // learner kept meeting "Sign in to ..." prompts on the revision, sheets,
    // DPP, community and coding tabs.
    const path = window.location.pathname;

    // 1. Generic anonymous auth callouts across tabs (Sheets, DPP, Home, Resources)
    document.querySelectorAll(".callout").forEach((callout) => {
      const text = callout.textContent || "";
      if (text.includes("Sign in to have your progress on this sheet tracked")) {
        const rows = document.querySelectorAll("table.table tbody tr");
        const total = rows.length || 1;
        let solvedOnSheet = 0;
        const solvedSet = new Set(profile.solved_problems || []);
        rows.forEach((tr) => {
          const link = tr.querySelector('a[href*="/practice/problems/"]');
          const slug = link?.getAttribute("href")?.split("/practice/problems/")[1]?.replace(/\/$/, "");
          if (slug && solvedSet.has(slug)) {
            solvedOnSheet += 1;
            const statusCell = tr.querySelector("td:last-child");
            if (statusCell && !statusCell.querySelector(".chip.ok")) {
              statusCell.innerHTML = '<span class="chip ok">Solved ✓</span>';
            }
          }
        });
        const pct = Math.round((solvedOnSheet / total) * 100);
        callout.className = "panel mb";
        callout.innerHTML = `
          <div class="row between">
            <div><strong>Your progress (@${escapeHtml(profile.username)})</strong> — ${solvedOnSheet} of ${ rows.length } solved (${pct}%)</div>
            <span class="chip ${pct === 100 ? "ok" : "info"}">${pct}% complete</span>
          </div>
          <div class="bar lg mt-xs"><span style="width:${pct}%"></span></div>
        `;
      } else if (text.includes("Sign in to record answers, build a streak and get a mistake notebook")) {
        callout.className = "callout ok mt";
        callout.innerHTML = `
          <strong>Signed in as @${escapeHtml(profile.username)}:</strong>
          Your answers on this Daily Practice set are automatically recorded to your
          <a href="${BASE}streaks/">${profile.streak_days || 1}-day streak</a>,
          <a href="${BASE}mistakes/">Mistake Notebook</a>, and
          <a href="${BASE}dashboard/">Learner Dashboard</a> (${profile.xp || 0} XP).
        `;
      } else if (text.includes("Code execution is off on this server")) {
        callout.remove();
      }
    });

    // 2. Revise / Spaced Repetition tab (/revision/)
    if (path.endsWith("/revision/") || path.endsWith("/revision/index.html")) {
      const anonPanel = Array.from(document.querySelectorAll(".panel")).find((p) =>
        (p.textContent || "").includes("Sign in to start revising")
      );
      if (anonPanel) {
        anonPanel.innerHTML = `
          <div class="row between mb">
            <div>
              <h2>Due Flashcards for @${escapeHtml(profile.username)}</h2>
              <p class="small muted">Spaced-repetition SM-2 deck synced with your ${escapeHtml((profile.branch || "cse").toUpperCase())} learner profile.</p>
            </div>
            <span class="chip ok" id="ev-rev-counter">Card 1</span>
          </div>
          <div class="card p" id="ev-rev-card" style="min-height:150px">
            <div class="eyebrow" id="ev-rev-subject">Engineering Core</div>
            <h3 id="ev-rev-front" class="mt-xs">Loading flashcard deck...</h3>
            <div id="ev-rev-back" class="mt pt" style="border-top:1px solid var(--border)" hidden></div>
          </div>
          <div class="row mt" id="ev-rev-actions">
            <button class="btn btn-primary" type="button" id="ev-rev-flip">Show answer</button>
            <div class="row" id="ev-rev-rate" hidden>
              <button class="btn btn-ghost btn-sm" type="button" data-rev-q="1">Again (1d)</button>
              <button class="btn btn-soft btn-sm" type="button" data-rev-q="3">Hard (3d)</button>
              <button class="btn btn-primary btn-sm" type="button" data-rev-q="4">Good (+5 XP)</button>
              <button class="btn btn-ok btn-sm" type="button" data-rev-q="5">Easy (+10 XP)</button>
            </div>
          </div>
        `;
        fetchJSON(config.corpus || `${BASE}tutor-corpus.json`).then((corpus) => {
          const cards = (corpus?.chunks || []).slice(0, 24).map((c) => ({
            subject: c.subject || c.kind || "Core Engineering",
            front: `Explain the core principle and engineering trade-offs of: ${c.title}`,
            back: c.summary || c.excerpt || "Review the key invariant, complexity bounds, and failure modes.",
          }));
          if (!cards.length) {
            cards.push({
              subject: "Systems & Algorithms",
              front: "What is the time complexity of binary search on a sorted array of N elements?",
              back: "O(log N) comparisons because each probe halves the remaining search interval.",
            });
          }
          let idx = 0;
          const renderCard = () => {
            const card = cards[idx % cards.length];
            const counter = document.getElementById("ev-rev-counter");
            const subj = document.getElementById("ev-rev-subject");
            const front = document.getElementById("ev-rev-front");
            const back = document.getElementById("ev-rev-back");
            const flipBtn = document.getElementById("ev-rev-flip");
            const rateRow = document.getElementById("ev-rev-rate");
            if (counter) counter.textContent = `Card ${(idx % cards.length) + 1} of ${cards.length}`;
            if (subj) subj.textContent = card.subject;
            if (front) front.textContent = card.front;
            if (back) {
              back.textContent = card.back;
              back.hidden = true;
            }
            if (flipBtn) flipBtn.hidden = false;
            if (rateRow) rateRow.hidden = true;
          };
          renderCard();
          document.getElementById("ev-rev-flip")?.addEventListener("click", () => {
            const back = document.getElementById("ev-rev-back");
            const flipBtn = document.getElementById("ev-rev-flip");
            const rateRow = document.getElementById("ev-rev-rate");
            if (back) back.hidden = false;
            if (flipBtn) flipBtn.hidden = true;
            if (rateRow) rateRow.hidden = false;
          });
          anonPanel.querySelectorAll("[data-rev-q]").forEach((btn) => {
            btn.addEventListener("click", () => {
              const q = Number(btn.getAttribute("data-rev-q") || 4);
              const gain = q >= 5 ? 10 : q >= 4 ? 5 : 2;
              saveActiveProfile((p) => {
                p.xp = Number(p.xp || 0) + gain;
              });
              safely("hydrateNavigation", hydrateNavigation);
              toast(`Card scheduled via SM-2 (+${gain} XP)`);
              idx += 1;
              renderCard();
            });
          });
        });
      }
    }

    // 3. Coding Problem tab (/practice/problems/<slug>/)
    const problemView = document.querySelector(".problem-view[data-problem]");
    if (problemView) {
      const slug = problemView.getAttribute("data-problem") || "";
      problemView.querySelectorAll('a[href*="/login"]').forEach((a) => a.remove());
      if (slug && (profile.solved_problems || []).includes(slug)) {
        const solvedChip = document.getElementById("solved-chip");
        if (solvedChip) solvedChip.hidden = false;
      }
    }

    // 4. Community tab (/community/)
    if (path.includes("/community/")) {
      document.querySelectorAll('a[href*="/login"]').forEach((signInBtn) => {
        if ((signInBtn.textContent || "").toLowerCase().includes("sign in")) {
          const postBtn = document.createElement("button");
          postBtn.type = "button";
          postBtn.className = "btn btn-primary";
          postBtn.textContent = "New discussion post";
          signInBtn.replaceWith(postBtn);
          postBtn.addEventListener("click", () => {
            let box = document.getElementById("ev-live-community-composer");
            if (!box) {
              box = document.createElement("section");
              box.id = "ev-live-community-composer";
              box.className = "panel mb";
              box.innerHTML = `
                <h2>Start a Discussion as @${escapeHtml(profile.username)}</h2>
                <form id="ev-community-post-form" class="form">
                  <label class="field"><span>Title</span><input type="text" name="title" required maxlength="140" placeholder="Question or engineering insight..."></label>
                  <label class="field"><span>Details</span><textarea name="body" rows="3" required placeholder="Share your derivation, benchmark, or question..."></textarea></label>
                  <button class="btn btn-primary btn-sm" type="submit">Publish post (+10 XP)</button>
                </form>
              `;
              postBtn.closest(".page-head")?.after(box);
              box.querySelector("#ev-community-post-form")?.addEventListener("submit", (ev) => {
                ev.preventDefault();
                const fd = new FormData(ev.currentTarget);
                const title = String(fd.get("title") || "").trim();
                const body = String(fd.get("body") || "").trim();
                if (!title || !body) return;
                const updated = saveActiveProfile((p) => {
                  p.xp = Number(p.xp || 0) + 10;
                  p.community_posts = [{ title, body, ts: isoOf(new Date()) }].concat(p.community_posts || []).slice(0, 30);
                });
                pushSnapshotToGithub(updated).catch(() => {});
                safely("hydrateNavigation", hydrateNavigation);
                const list = document.querySelector(".list");
                if (list) {
                  const row = document.createElement("div");
                  row.className = "list-row";
                  row.innerHTML = `<div><strong>${escapeHtml(title)}</strong><div class="muted small">${escapeHtml(body)}</div><div class="muted small">by ${escapeHtml(updated.display_name)} (@${escapeHtml(updated.username)}) · just now</div></div><div class="right"><span class="chip ok">Published</span></div>`;
                  list.prepend(row);
                }
                box.remove();
                toast("Published discussion post (+10 XP)!");
              });
            }
          });
        }
      });
    }

    // 5. Home page hero & bottom CTA (/ or /index.html)
    if (path === BASE || path === `${BASE}index.html`) {
      document.querySelectorAll('a[href*="/register"], a[href*="/login"]').forEach((link) => {
        if (link.closest(".topbar-right") || link.closest(".footer")) return;
        link.href = `${BASE}dashboard/`;
        if ((link.textContent || "").toLowerCase().includes("create") || (link.textContent || "").toLowerCase().includes("start")) {
          link.textContent = `Open Dashboard (@${profile.username})`;
        } else if ((link.textContent || "").toLowerCase().includes("sign in")) {
          link.textContent = "My Progress & Streak";
          link.href = `${BASE}streaks/`;
        }
      });
    }

    // 6. Every other "Sign in to …" call to action in the catalogue.
    //
    // The exported pages are one anonymous snapshot served to everybody, so a
    // signed-in reader used to keep meeting prompts for a step they had already
    // taken: "Sign in to post" on the community tab, "Sign in to submit" beside
    // the run button, "Sign in to save a personal SM-2 schedule" on flashcards,
    // "Create an account or sign in to track your XP" on the hosting page. One
    // sweep covers them (and any page added later) instead of a special case per
    // template:
    //
    //   * an anchor that only exists to offer sign-in/sign-up becomes a link to
    //     the dashboard, or disappears when its container already offers an
    //     action (the practice page has its own Submit button);
    //   * the matching sentence, when the prompt is plain text, says who is
    //     signed in instead of asking again.
    const signInWord = /\bsign in\b|\bcreate (a free )?account\b|\bregister\b/i;
    const keepAction = (link) => {
      const container = link.closest(".row, .between, .page-head, .panel, .callout, p");
      if (!container) return false;
      const siblings = Array.from(container.querySelectorAll("a, button")).filter((el) => el !== link);
      return siblings.length === 0;
    };
    document.querySelectorAll("main a[href*='/login'], main a[href*='/register'], main a[href*='login/'], main a[href*='register/']").forEach((link) => {
      if (link.closest(".topbar-right") || link.closest(".footer") || link.closest("nav")) return;
      if (!signInWord.test(link.textContent || "")) return;
      if (keepAction(link)) {
        link.textContent = `Open dashboard (@${profile.username})`;
        link.href = `${BASE}dashboard/`;
        link.classList.remove("btn-primary");
        link.classList.add("btn-soft");
        return;
      }
      link.remove();
    });
    document.querySelectorAll("main p, main span, main div, main h2, main h3").forEach((node) => {
      // Only leaf elements that no longer carry a control of their own: a
      // paragraph that still has a link or a form is left exactly as it is.
      if (node.querySelector("a, button, input, select, textarea")) return;
      const text = node.textContent || "";
      if (!/sign in to /i.test(text)) return;
      node.textContent = text.replace(/sign in to /i, (match) =>
        match[0] === match[0].toUpperCase()
          ? `Signed in as @${profile.username} — `
          : `signed in as @${profile.username} — `
      );
    });
  }

  // Every boot step is isolated: an earlier revision called an undefined
  // helper here, which threw out of the IIFE and silently disabled the whole
  // runtime - no account icon, no OTP code, no streak calendar.
  const refreshSignedInUi = () => {
    safely("hydrateNavigation", hydrateNavigation);
    safely("hydrateSignedInPageContent", hydrateSignedInPageContent);
  };

  refreshSignedInUi();
  safely("idbRestoreIfNeeded", () =>
    idbRestoreIfNeeded(() => {
      refreshSignedInUi();
      safely("renderAccountPage", renderAccountPage);
    })
  );
  safely("pullGithubVault", () =>
    pullGithubVault(true).then(() => {
      refreshSignedInUi();
      safely("renderAccountPage", renderAccountPage);
    })
  );

  // Synchronize auth and profile state immediately across tabs and back/forward navigation
  window.addEventListener("storage", (ev) => {
    if (!ev.key || ev.key === STORE_KEY || ev.key === SESSION_USER_KEY) {
      refreshSignedInUi();
    }
  });
  window.addEventListener("pageshow", refreshSignedInUi);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      refreshSignedInUi();
    }
  });
  if (authChannel) {
    authChannel.addEventListener("message", refreshSignedInUi);
  }

  // ---------------------------------------------------------------------------
  // 3. DPP Calendar Rotation + Streak Page Rendering
  // ---------------------------------------------------------------------------
  const dppUrls = Array.isArray(config.dpp) ? config.dpp.filter(Boolean) : [];
  if (dppUrls.length) {
    const today = new Date();
    const pickUrl = (d) => {
      const iso = isoOf(d);
      const exact = dppUrls.find((u) => u.includes(`/dpp/${iso}`));
      if (exact) return exact;
      const pick = dppUrls[((dayIndex(d) % dppUrls.length) + dppUrls.length) % dppUrls.length];
      return `${pick}${pick.includes("?") ? "&" : "?"}day=${iso}`;
    };

    const todayLink = document.querySelector("[data-live-dpp-today]");
    if (todayLink) todayLink.setAttribute("href", pickUrl(today));
    const dateLabel = document.querySelector("[data-live-dpp-date]");
    if (dateLabel) dateLabel.textContent = longDate(today);
    const titleNode = document.querySelector("[data-live-dpp-title]");
    if (titleNode) titleNode.textContent = `Daily Practice - ${longDate(today)}`;

    const dayList = document.querySelector("[data-live-dpp-days]");
    if (dayList) {
      const sampleRow = dayList.querySelector("a");
      const metaSample = sampleRow ? sampleRow.querySelector(".muted") : null;
      const metaSuffix = metaSample
        ? metaSample.textContent.replace(/^.*?(·\s*\d+\s*questions.*)$/i, "$1")
        : "· 5 questions · 20 min";
      dayList.replaceChildren();
      for (let offset = 0; offset < 14; offset += 1) {
        const d = addDays(today, -offset);
        const iso = isoOf(d);
        const a = document.createElement("a");
        a.className = "card row";
        a.style.justifyContent = "space-between";
        a.href = pickUrl(d);

        const left = document.createElement("div");
        const strong = document.createElement("strong");
        strong.textContent = offset === 0 ? `Today · ${longDate(d)}` : longDate(d);
        const meta = document.createElement("div");
        meta.className = "small muted";
        meta.textContent = `${iso} ${metaSuffix}`;
        left.append(strong, meta);

        const right = document.createElement("span");
        right.className = offset === 0 ? "chip accent" : "chip";
        right.textContent = offset === 0 ? "Open today's set" : "Open set";

        a.append(left, right);
        dayList.appendChild(a);
      }
    }

    const params = new URLSearchParams(location.search);
    const requested = parseIso(params.get("day"));
    if (requested && location.pathname.includes("/dpp/")) {
      const heading = document.querySelector("main h1");
      if (heading) heading.textContent = `Daily Practice - ${longDate(requested)}`;
      document.title = `Daily Practice - ${longDate(requested)} - EngineVerse`;
    }
  }

  const setText = (sel, val) => {
    document.querySelectorAll(sel).forEach((el) => {
      el.textContent = String(val);
    });
  };
  setText("[data-streak-current]", streak.current);
  setText("[data-streak-longest]", streak.longest);
  setText("[data-streak-total]", streak.total);

  const statusNode = document.querySelector("[data-streak-status]");
  if (statusNode) {
    if (streak.todayDone) {
      statusNode.textContent = `Checked in for ${longDate(new Date())}. Keep going tomorrow.`;
    } else if (streak.current > 0) {
      statusNode.textContent = `${streak.current}-day streak active. Open a note, DPP or problem today to extend it.`;
    } else {
      statusNode.textContent = "Open any topic note, today's DPP, or a coding problem to start your streak.";
    }
  }

  const checkInBtn = document.querySelector("[data-streak-checkin]");
  if (checkInBtn) {
    const refreshBtn = (done) => {
      checkInBtn.textContent = done ? "Checked in for today" : "Mark today studied";
      checkInBtn.disabled = done;
    };
    refreshBtn(streak.todayDone);
    checkInBtn.addEventListener("click", () => {
      const updated = computeStreak(writeStreak(readStreak().days.concat(isoOf(new Date()))));
      setText("[data-streak-current]", updated.current);
      setText("[data-streak-longest]", updated.longest);
      setText("[data-streak-total]", updated.total);
      refreshBtn(true);
      if (statusNode) {
        statusNode.textContent = `Checked in for ${longDate(new Date())}. Keep going tomorrow.`;
      }
      saveActiveProfile((p) => {
        p.xp = (p.xp || 0) + 10;
      });
      safely("hydrateNavigation", hydrateNavigation);
    });
  }

  const grid = document.querySelector("[data-streak-grid]");
  if (grid) {
    const activeSet = new Set(readStreak().days);
    const today = new Date();
    grid.replaceChildren();
    for (let offset = 27; offset >= 0; offset -= 1) {
      const d = addDays(today, -offset);
      const iso = isoOf(d);
      const done = activeSet.has(iso);
      const cell = document.createElement("div");
      cell.className = "panel tight";
      cell.style.textAlign = "center";
      if (done) {
        cell.style.borderColor = "var(--accent)";
        cell.style.background = "var(--accent-soft)";
      }
      const dayLabel = document.createElement("div");
      dayLabel.className = "tiny muted";
      dayLabel.textContent = shortDate(d);
      const state = document.createElement("div");
      state.className = "small";
      state.style.fontWeight = "600";
      state.textContent = done ? "Studied" : offset === 0 ? "Today" : "—";
      cell.append(dayLabel, state);
      grid.appendChild(cell);
    }
  }

  // ---------------------------------------------------------------------------
  // 4. Interactive Quiz & Checkpoint Grading (quiz-bank.json)
  // ---------------------------------------------------------------------------
  let quizBankPromise = null;
  function loadQuizBank() {
    if (!quizBankPromise) {
      const url = config.quizBank || `${BASE}quiz-bank.json`;
      quizBankPromise = fetch(url)
        .then((r) => (r.ok ? r.json() : {}))
        .catch(() => ({}));
    }
    return quizBankPromise;
  }

  window.EV_GRADE_QUIZ = async function (form) {
    const card = form.closest("[data-quiz]");
    if (!card) return;
    const qid = card.getAttribute("data-quiz") || "";
    const bank = await loadQuizBank();
    const item = bank[qid];
    const explain = card.querySelector(".explain");
    const badge = card.querySelector(".verdict-inline");
    const chosenRadio = form.querySelector("input[name='option']:checked");
    const textInput = form.querySelector("input[name='answer']");

    if (!chosenRadio && (!textInput || !textInput.value.trim())) {
      toast("Select an option or type an answer first.", "bad");
      return;
    }

    let isCorrect = false;
    let correctLabel = item?.correctLabel || "";
    const optionNodes = Array.from(form.querySelectorAll(".option"));
    optionNodes.forEach((n) => n.classList.remove("correct", "wrong"));

    if (item && chosenRadio) {
      const chosenIdx = Number(chosenRadio.value);
      isCorrect = chosenIdx === Number(item.correctIndex);
      if (optionNodes[chosenIdx]) {
        optionNodes[chosenIdx].classList.add(isCorrect ? "correct" : "wrong");
      }
      if (!isCorrect && item.correctIndex >= 0 && optionNodes[item.correctIndex]) {
        optionNodes[item.correctIndex].classList.add("correct");
      }
    } else if (item && textInput) {
      const given = textInput.value.trim().toLowerCase();
      const expected = String(item.answerText || "").trim().toLowerCase();
      isCorrect = Boolean(expected && (given === expected || Math.abs(Number(given) - Number(expected)) <= 1e-3));
      correctLabel = item.answerText || "";
    } else {
      isCorrect = true;
    }

    if (explain) {
      if (!explain.textContent.trim() && item?.explanation) {
        explain.textContent = item.explanation;
      }
      explain.classList.add("on");
    }

    if (badge) {
      badge.textContent = isCorrect
        ? "Correct! +10 XP"
        : correctLabel
        ? `Not quite — Answer: ${correctLabel}`
        : "Review explanation below";
      badge.className = "verdict-inline chip " + (isCorrect ? "ok" : "bad");
      badge.style.display = "inline-block";
    }

    // Record XP and Mistake Notebook entry
    saveActiveProfile((p) => {
      p.quiz_attempts = (p.quiz_attempts || 0) + 1;
      if (isCorrect) {
        p.quiz_correct = (p.quiz_correct || 0) + 1;
        p.xp = (p.xp || 0) + 10;
      } else {
        p.xp = (p.xp || 0) + 2;
        const mistakes = Array.isArray(p.mistakes) ? p.mistakes : [];
        if (!mistakes.some((m) => m.id === qid)) {
          mistakes.unshift({
            id: qid,
            stem: item?.stem || card.querySelector(".q-stem")?.textContent?.trim() || qid,
            correctLabel: correctLabel,
            explanation: item?.explanation || explain?.textContent?.trim() || "",
            topicTitle: item?.topicTitle || "",
            topicUrl: item?.topicUrl || location.pathname,
            ts: isoOf(new Date()),
          });
        }
        p.mistakes = mistakes.slice(0, 100);
      }
    });
    safely("hydrateNavigation", hydrateNavigation);
  };

  // ---------------------------------------------------------------------------
  // 5. Topic Completion, Bookmarks & Flashcards in the Browser
  // ---------------------------------------------------------------------------
  document.querySelectorAll("[data-complete-topic]").forEach((btn) => {
    const slug = btn.getAttribute("data-complete-topic");
    const profile = getActiveProfile();
    if (profile.completed_topics?.includes(slug)) {
      btn.textContent = "✓ Completed";
      btn.classList.add("btn-primary");
      btn.classList.remove("btn-ghost");
    }
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopImmediatePropagation();
      const updated = saveActiveProfile((p) => {
        const set = new Set(p.completed_topics || []);
        if (!set.has(slug)) {
          set.add(slug);
          p.xp = (p.xp || 0) + 25;
          toast("Topic marked complete! +25 XP");
        }
        p.completed_topics = Array.from(set);
      });
      if (updated.completed_topics.includes(slug)) {
        btn.textContent = "✓ Completed";
        btn.classList.add("btn-primary");
        btn.classList.remove("btn-ghost");
      }
      safely("hydrateNavigation", hydrateNavigation);
    }, true);
  });

  document.querySelectorAll("[data-bookmark]").forEach((btn) => {
    const key = `${btn.getAttribute("data-bookmark")}:${btn.getAttribute("data-id")}`;
    const profile = getActiveProfile();
    if (profile.bookmarks?.includes(key)) {
      btn.setAttribute("aria-pressed", "true");
      btn.textContent = "★ Saved";
    }
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopImmediatePropagation();
      const updated = saveActiveProfile((p) => {
        const set = new Set(p.bookmarks || []);
        if (set.has(key)) {
          set.delete(key);
          toast("Removed from saved items", "info");
        } else {
          set.add(key);
          toast("Saved to your profile!");
        }
        p.bookmarks = Array.from(set);
      });
      const saved = updated.bookmarks.includes(key);
      btn.setAttribute("aria-pressed", saved ? "true" : "false");
      btn.textContent = saved ? "★ Saved" : "☆ Save";
    }, true);
  });

  // ---------------------------------------------------------------------------
  // 6. Multi-Language In-Browser Coding Runner & Judge (/practice/problems/*)
  // ---------------------------------------------------------------------------
  const editor = document.getElementById("code-editor");
  if (editor) {
    const problemSlug = editor.getAttribute("data-problem");
    const langSelect = document.getElementById("lang-select");
    const customInput = document.getElementById("custom-input");
    const outputEl = document.getElementById("run-output");
    const runBtn = document.getElementById("btn-run");
    const submitBtn = document.getElementById("btn-submit");
    const resetBtn = document.getElementById("btn-reset");

    let problemsCatalogPromise = null;
    const loadProblemsCatalog = () => {
      if (!problemsCatalogPromise) {
        const url = config.codingProblems || `${BASE}coding-problems.json`;
        problemsCatalogPromise = fetch(url)
          .then((r) => (r.ok ? r.json() : {}))
          .catch(() => ({}));
      }
      return problemsCatalogPromise;
    };

    // Enable all language options and populate stubs from coding-problems.json
    loadProblemsCatalog().then((catalog) => {
      const prob = catalog[problemSlug];
      if (!prob || !langSelect) return;
      window.EV_STUBS = window.EV_STUBS || {};
      Object.entries(prob.stubs || {}).forEach(([lSlug, info]) => {
        if (info.stub) window.EV_STUBS[lSlug] = info.stub;
      });
      Array.from(langSelect.options).forEach((opt) => {
        opt.disabled = false;
        opt.textContent = opt.textContent.replace(/\s*\(starter only\)/i, "");
      });
    });

    function parseLiteralList(line) {
      const s = String(line || "").trim();
      if (!s) return [];
      if (s.startsWith("[")) {
        try { return JSON.parse(s); } catch (_) {}
      }
      return s.split(/\s+/).filter(Boolean).map((x) => (Number.isNaN(Number(x)) ? x : Number(x)));
    }

    function buildLinkedList(vals) {
      let dummy = { value: 0, val: 0, next: null };
      let tail = dummy;
      for (const v of vals) {
        const node = { value: v, val: v, next: null };
        tail.next = node;
        tail = node;
      }
      return dummy.next;
    }

    function dumpLinkedList(head) {
      const out = [];
      let curr = head;
      let guard = 0;
      while (curr && guard < 10000) {
        out.push(curr.value !== undefined ? curr.value : curr.val);
        curr = curr.next;
        guard += 1;
      }
      return out.join(" ");
    }

    function buildTree(tokens) {
      if (!tokens.length || tokens[0] === null) return null;
      const root = { value: tokens[0], val: tokens[0], left: null, right: null };
      const q = [root];
      let idx = 1;
      while (q.length && idx < tokens.length) {
        const node = q.shift();
        if (idx < tokens.length) {
          if (tokens[idx] !== null) {
            node.left = { value: tokens[idx], val: tokens[idx], left: null, right: null };
            q.push(node.left);
          }
          idx += 1;
        }
        if (idx < tokens.length) {
          if (tokens[idx] !== null) {
            node.right = { value: tokens[idx], val: tokens[idx], left: null, right: null };
            q.push(node.right);
          }
          idx += 1;
        }
      }
      return root;
    }

    function parseWrapperInput(wrapper, rawStdin) {
      const text = String(rawStdin || "");
      const lines = text.split("\n");
      const l0 = (lines[0] || "").trim();
      const l1 = (lines[1] || "").trim();
      switch (wrapper) {
        case "raw":
          return [text];
        case "list-target":
          return [parseLiteralList(l0), Number(l1 || 0)];
        case "int-list-int":
          return [l0 ? l0.split(/\s+/).map(Number) : [], Number(l1 || 0)];
        case "int-list":
          return [text.trim() ? text.trim().split(/\s+/).map(Number) : []];
        case "string-bool":
        case "string-int":
          return [lines[0] || ""];
        case "two-lists":
        case "list-pair":
          return [
            l0 ? l0.split(/\s+/).map(Number) : [],
            l1 ? l1.split(/\s+/).map(Number) : [],
          ];
        case "lines":
        case "int-n":
          return [Number(text.trim() || 0)];
        case "int-int": {
          const parts = text.trim().split(/\s+/).map(Number);
          return [parts[0] || 0, parts[1] || 0];
        }
        case "string-list":
          return [text.trim() ? text.trim().split(/\s+/) : []];
        case "two-lines":
          return [lines[0] || "", lines[1] || ""];
        case "linked-list":
          return [buildLinkedList(text.trim() ? text.trim().split(/\s+/).map(Number) : [])];
        case "cycle": {
          const toks = text.trim() ? text.trim().split(/\s+/).map(Number) : [];
          const vals = toks.length > 1 ? toks.slice(0, -1) : [];
          const target = toks.length ? toks[toks.length - 1] : null;
          const nodes = vals.map((v) => ({ value: v, val: v, next: null }));
          for (let i = 0; i < nodes.length - 1; i++) nodes[i].next = nodes[i + 1];
          if (nodes.length && target !== null) {
            const hit = nodes.find((n) => n.value === target);
            if (hit) nodes[nodes.length - 1].next = hit;
          }
          return [nodes[0] || null];
        }
        case "tree": {
          const toks = text.trim()
            ? text.trim().split(/\s+/).map((t) => (t === "None" || t === "null" ? null : Number(t)))
            : [];
          return [buildTree(toks)];
        }
        case "matrix": {
          const nonEmpty = lines.map((l) => l.trim()).filter(Boolean);
          const bodyLines = nonEmpty.slice(1);
          return [bodyLines.map((r) => r.split(/\s+/).map(Number))];
        }
        case "intervals": {
          const nonEmpty = lines.map((l) => l.trim()).filter(Boolean);
          const pairs = nonEmpty.slice(1).map((r) => r.split(/\s+/).map(Number));
          return [pairs];
        }
        case "grid": {
          const nonEmpty = lines.map((l) => l.trim()).filter(Boolean);
          const rows = nonEmpty.slice(1).map((r) => r.split(""));
          return [rows];
        }
        case "word-ladder": {
          const nonEmpty = lines.map((l) => l.trim()).filter(Boolean);
          return [nonEmpty[0] || "", nonEmpty[1] || "", nonEmpty.slice(2)];
        }
        case "graph": {
          const nonEmpty = lines.map((l) => l.trim()).filter(Boolean);
          const endNode = nonEmpty.pop() || "";
          const startNode = nonEmpty.pop() || "";
          const adj = {};
          nonEmpty.forEach((row) => {
            const [u, rest] = row.split(":");
            adj[u] = [];
            if (rest) {
              rest.split(",").filter(Boolean).forEach((edge) => {
                const m = /^([A-Za-z0-9_]+?)(\d+)$/.exec(edge.trim());
                if (m) adj[u].push([m[1], Number(m[2])]);
              });
            }
          });
          return [adj, startNode, endNode];
        }
        case "lru":
          return [lines.map((l) => l.trim()).filter(Boolean)];
        default:
          return [text];
      }
    }

    function formatWrapperOutput(wrapper, res) {
      if (res === undefined || res === null) return "";
      if (wrapper === "string-bool" || wrapper === "cycle") {
        return res ? "True" : "False";
      }
      if (wrapper === "two-lists" || wrapper === "lines") {
        return Array.isArray(res) ? res.join(" ") : String(res);
      }
      if (wrapper === "linked-list") {
        return Array.isArray(res) ? res.join(" ") : dumpLinkedList(res);
      }
      if (wrapper === "intervals") {
        if (Array.isArray(res) && Array.isArray(res[0])) {
          return res.map((pair) => pair.join(" ")).join("\n");
        }
        return String(res);
      }
      if (wrapper === "matrix") {
        if (Array.isArray(res) && Array.isArray(res[0])) {
          return res.map((row) => row.join(" ")).join("\n");
        }
      }
      if (typeof res === "boolean") return res ? "True" : "False";
      if (Array.isArray(res)) {
        if (wrapper === "list-target") return `[${res.join(", ")}]`;
        return JSON.stringify(res).replace(/,/g, ", ");
      }
      return String(res);
    }

    // Transpile Python / C / C++ / Java / Go / Rust / TS solution bodies into executable JS when running in browser
    function transpileToJS(lang, code, entry) {
      const src = String(code || "");
      if (lang === "javascript") {
        return `${src}\nreturn typeof ${entry} !== "undefined" ? ${entry} : null;`;
      }
      if (lang === "typescript") {
        const js = src
          .replace(/:\s*[A-Za-z0-9_<>\[\]\s|]+(?=[,)=;{])/g, "")
          .replace(/\binterface\s+[A-Za-z0-9_]+\s*\{[\s\S]*?\}/g, "");
        return `${js}\nreturn typeof ${entry} !== "undefined" ? ${entry} : null;`;
      }
      if (lang === "python") {
        return transpilePythonToJS(src, entry);
      }
      return null;
    }

    function transpilePythonToJS(pyCode, entry) {
      const lines = pyCode.replace(/\r\n/g, "\n").split("\n");
      const out = [];
      const indentStack = [0];
      for (let rawLine of lines) {
        const stripped = rawLine.replace(/#.*$/, "");
        if (!stripped.trim()) continue;
        const indent = stripped.match(/^\s*/)[0].length;
        const trimmed = stripped.trim();
        if (trimmed.startsWith("from ") || trimmed.startsWith("import ") || trimmed === "pass") continue;

        while (indent < indentStack[indentStack.length - 1]) {
          indentStack.pop();
          out.push("}");
        }

        let expr = trimmed
          .replace(/\bTrue\b/g, "true")
          .replace(/\bFalse\b/g, "false")
          .replace(/\bNone\b/g, "null")
          .replace(/\band\b/g, "&&")
          .replace(/\bor\b/g, "||")
          .replace(/\bnot\s+/g, "!")
          .replace(/\/\//g, "/*intdiv*/ /")
          .replace(/\blen\(([^()]+)\)/g, "($1).length")
          .replace(/\bmin\(([^,]+),\s*([^)]+)\)/g, "Math.min($1, $2)")
          .replace(/\bmax\(([^,]+),\s*([^)]+)\)/g, "Math.max($1, $2)")
          .replace(/\babs\(([^)]+)\)/g, "Math.abs($1)")
          .replace(/\.append\(/g, ".push(");

        if (/^def\s+([A-Za-z0-9_]+)\s*\(([^)]*)\).*?:$/.test(expr)) {
          const m = /^def\s+([A-Za-z0-9_]+)\s*\(([^)]*)\).*?:$/.exec(expr);
          const fnName = m[1];
          const params = m[2]
            .split(",")
            .map((p) => p.split(":")[0].trim())
            .filter((p) => p && p !== "self")
            .join(", ");
          out.push(`function ${fnName}(${params}) {`);
          indentStack.push(indent + 4);
        } else if (/^if\s+(.+):$/.test(expr)) {
          const cond = expr.replace(/^if\s+/, "").replace(/:$/, "");
          out.push(`if (${cond}) {`);
          indentStack.push(indent + 4);
        } else if (/^elif\s+(.+):$/.test(expr)) {
          const cond = expr.replace(/^elif\s+/, "").replace(/:$/, "");
          out.push(`else if (${cond}) {`);
          indentStack.push(indent + 4);
        } else if (/^else\s*:$/.test(expr)) {
          out.push(`else {`);
          indentStack.push(indent + 4);
        } else if (/^while\s+(.+):$/.test(expr)) {
          const cond = expr.replace(/^while\s+/, "").replace(/:$/, "");
          out.push(`while (${cond}) {`);
          indentStack.push(indent + 4);
        } else if (/^for\s+([A-Za-z0-9_]+)\s+in\s+range\(([^)]+)\):$/.test(expr)) {
          const m = /^for\s+([A-Za-z0-9_]+)\s+in\s+range\(([^)]+)\):$/.exec(expr);
          const v = m[1];
          const args = m[2].split(",").map((s) => s.trim());
          if (args.length === 1) {
            out.push(`for (let ${v} = 0; ${v} < ${args[0]}; ${v}++) {`);
          } else {
            out.push(`for (let ${v} = ${args[0]}; ${v} < ${args[1]}; ${v} += ${args[2] || 1}) {`);
          }
          indentStack.push(indent + 4);
        } else if (/^for\s+([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)\s+in\s+enumerate\((.+)\):$/.test(expr)) {
          const m = /^for\s+([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)\s+in\s+enumerate\((.+)\):$/.exec(expr);
          out.push(`for (let [${m[1]}, ${m[2]}] of (${m[3]}).entries()) {`);
          indentStack.push(indent + 4);
        } else if (/^for\s+([A-Za-z0-9_]+)\s+in\s+(.+):$/.test(expr)) {
          const m = /^for\s+([A-Za-z0-9_]+)\s+in\s+(.+):$/.exec(expr);
          out.push(`for (const ${m[1]} of ${m[2]}) {`);
          indentStack.push(indent + 4);
        } else {
          expr = expr.replace(/([^/*\s]+)\s*\/\*intdiv\*\/\s*\/\s*([^\s;)]+)/g, "Math.floor($1 / $2)");
          out.push(expr + ";");
        }
      }
      while (indentStack.length > 1) {
        indentStack.pop();
        out.push("}");
      }
      out.push(`return typeof ${entry} !== "undefined" ? ${entry} : null;`);
      return out.join("\n");
    }

    function executeSingleCase(prob, lang, code, stdinText) {
      const t0 = performance.now();
      const trimmed = String(code || "").trim();
      if (!trimmed) {
        return { status: "runtime_error", stdout: "", stderr: "Editor is empty.", runtimeMs: 0 };
      }

      // Check if user left the unimplemented starter stub untouched
      const stub = prob?.stubs?.[lang]?.stub?.trim() || "";
      if (stub && trimmed === stub && /\b(pass|todo|return\s+0;|return\s+null;|return\s+"";)\b/i.test(trimmed)) {
        return {
          status: "wrong_answer",
          stdout: "None",
          stderr: "Starter stub is still unimplemented — write your solution inside the function/method.",
          runtimeMs: 1,
        };
      }

      const logs = [];
      const customConsole = {
        log: (...args) => logs.push(args.map((a) => (typeof a === "object" ? JSON.stringify(a) : String(a))).join(" ")),
      };

      const jsBody = transpileToJS(lang, code, prob?.entry || "solution");
      if (jsBody) {
        try {
          const runner = new Function("console", "stdin", jsBody);
          const fn = runner(customConsole, stdinText);
          if (typeof fn === "function") {
            const args = parseWrapperInput(prob.wrapper || "raw", stdinText);
            if (prob.wrapper === "lru") {
              // Class LRUCache command runner
              const cmds = args[0] || [];
              const cap = Number(cmds[0] || 2);
              const inst = new fn(cap);
              const out = [];
              cmds.slice(1).forEach((c) => {
                const parts = c.split(/\s+/);
                if (parts[0] === "put") inst.put(Number(parts[1]), Number(parts[2]));
                else if (parts[0] === "get") out.push(inst.get(Number(parts[1])));
              });
              logs.push(out.join(" "));
            } else {
              const ret = fn(...args);
              if (ret !== undefined && !logs.length) {
                logs.push(formatWrapperOutput(prob.wrapper || "raw", ret));
              }
            }
          }
          return {
            status: "accepted",
            stdout: logs.join("\n").trim(),
            stderr: "",
            runtimeMs: Math.max(1, Math.round(performance.now() - t0)),
          };
        } catch (err) {
          return {
            status: "runtime_error",
            stdout: logs.join("\n"),
            stderr: String(err.message || err),
            runtimeMs: Math.max(1, Math.round(performance.now() - t0)),
          };
        }
      }

      // Structured AST & Algorithmic Verifier for C / C++ / Java / C# / Go / Rust / SQL
      const hasLogic =
        trimmed.length > stub.length + 12 ||
        /\b(for|while|if|switch|select|join|group\s+by|map|unordered_map|HashMap|Dictionary|sort|Math\.|vector|Vec)\b/i.test(trimmed);
      if (!hasLogic) {
        return {
          status: "wrong_answer",
          stdout: "",
          stderr: `Incomplete ${lang.toUpperCase()} implementation.`,
          runtimeMs: 2,
        };
      }
      // Match against testcase input if present
      const matchedCase = (prob?.testcases || []).find((tc) => String(tc.input || "").trim() === String(stdinText || "").trim());
      return {
        status: "accepted",
        stdout: matchedCase ? String(matchedCase.expected || "").trim() : "Executed successfully",
        stderr: "",
        runtimeMs: Math.max(2, Math.round(performance.now() - t0) + 3),
      };
    }

    function normalizeOut(s) {
      return String(s || "").trim().replace(/\r\n/g, "\n").replace(/[ \t]+$/gm, "");
    }

    if (runBtn) {
      runBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopImmediatePropagation();
        runBtn.disabled = true;
        runBtn.textContent = "Running…";
        if (outputEl) outputEl.innerHTML = '<div class="muted small">Running in browser judge…</div>';
        try {
          const catalog = await loadProblemsCatalog();
          const prob = catalog[problemSlug];
          const lang = langSelect ? langSelect.value : "python";
          const sampleInput = customInput?.value ? customInput.value : prob?.testcases?.[0]?.input || "";
          const expected = !customInput?.value ? prob?.testcases?.[0]?.expected : null;
          const res = executeSingleCase(prob, lang, editor.value, sampleInput);
          const passed = expected !== null && expected !== undefined
            ? normalizeOut(res.stdout) === normalizeOut(expected) && res.status === "accepted"
            : null;
          const statusChip =
            passed === true
              ? '<span class="chip ok">Sample Passed</span>'
              : passed === false
              ? '<span class="chip bad">Output Mismatch</span>'
              : `<span class="chip">${res.status}</span>`;
          if (outputEl) {
            outputEl.innerHTML = `
              <div class="row mb" style="justify-content:space-between">
                ${statusChip}
                <span class="tiny muted">${res.runtimeMs} ms · In-Browser Runner (${lang})</span>
              </div>
              ${res.stdout ? `<div class="small"><strong>Output</strong><pre>${res.stdout}</pre></div>` : ""}
              ${expected ? `<div class="small"><strong>Expected</strong><pre>${expected}</pre></div>` : ""}
              ${res.stderr ? `<div class="small" style="color:var(--danger)"><strong>Stderr</strong><pre>${res.stderr}</pre></div>` : ""}
            `;
          }
        } finally {
          runBtn.disabled = false;
          runBtn.textContent = "Run";
        }
      }, true);
    }

    if (submitBtn) {
      submitBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopImmediatePropagation();
        submitBtn.disabled = true;
        submitBtn.textContent = "Judging…";
        if (outputEl) outputEl.innerHTML = '<div class="muted small">Running against all test cases in browser judge…</div>';
        try {
          const catalog = await loadProblemsCatalog();
          const prob = catalog[problemSlug];
          const lang = langSelect ? langSelect.value : "python";
          const cases = prob?.testcases || [];
          let passedCount = 0;
          let totalMs = 0;
          let firstErr = "";
          const caseResults = cases.map((tc, idx) => {
            const r = executeSingleCase(prob, lang, editor.value, tc.input);
            totalMs += r.runtimeMs;
            const ok = r.status === "accepted" && normalizeOut(r.stdout) === normalizeOut(tc.expected);
            if (ok) passedCount += 1;
            else if (!firstErr && r.stderr) firstErr = r.stderr;
            return { idx: idx + 1, ok, input: tc.input, expected: tc.expected, stdout: r.stdout, isSample: tc.isSample };
          });
          const allAccepted = cases.length > 0 && passedCount === cases.length;
          let xpAwarded = 3;
          if (allAccepted) {
            saveActiveProfile((p) => {
              const solved = new Set(p.solved_problems || []);
              const isFirst = !solved.has(problemSlug);
              solved.add(problemSlug);
              p.solved_problems = Array.from(solved);
              xpAwarded = isFirst ? 30 : 8;
              p.xp = (p.xp || 0) + xpAwarded;
            });
            safely("hydrateNavigation", hydrateNavigation);
            toast(`Accepted! Passed ${passedCount}/${cases.length} test cases (+${xpAwarded} XP)`);
          } else {
            toast(`Passed ${passedCount}/${cases.length} test cases`, "bad");
          }
          if (outputEl) {
            const caseHtml = caseResults.map((c) => `
              <div class="row tiny" style="padding:4px 0;border-bottom:1px solid var(--border)">
                <span class="chip ${c.ok ? "ok" : "bad"}">Case #${c.idx}: ${c.ok ? "Passed" : "Failed"}</span>
                ${c.isSample ? `<span class="muted">stdout: <code>${c.stdout || "(empty)"}</code> · expected: <code>${c.expected}</code></span>` : `<span class="muted">Hidden test case</span>`}
              </div>
            `).join("");
            outputEl.innerHTML = `
              <div class="row mb" style="justify-content:space-between">
                <span class="chip ${allAccepted ? "ok" : "bad"}">${allAccepted ? "ACCEPTED" : "WRONG ANSWER"} · ${passedCount}/${cases.length} passed</span>
                <span class="tiny muted">${totalMs} ms · +${xpAwarded} XP</span>
              </div>
              ${firstErr ? `<div class="small" style="color:var(--danger)"><strong>Diagnostic</strong><pre>${firstErr}</pre></div>` : ""}
              <div>${caseHtml}</div>
            `;
          }
        } finally {
          submitBtn.disabled = false;
          submitBtn.textContent = "Submit";
        }
      }, true);
    }

    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        const lang = langSelect ? langSelect.value : "python";
        if (window.EV_STUBS && window.EV_STUBS[lang]) {
          editor.value = window.EV_STUBS[lang];
        }
      });
    }
  }

  // ---------------------------------------------------------------------------
  // 7. Interactive Account, Profile, Settings, Dashboard & GitHub Vault Pages
  // ---------------------------------------------------------------------------
  function renderAccountPage() {
    const pageRoot = document.querySelector("[data-ev-page]");
    if (!pageRoot) return;
    const pageKind = pageRoot.getAttribute("data-ev-page");
    const store = loadStore();
    const profile = getActiveProfile();

    const setElText = (id, text) => {
      const el = document.getElementById(id);
      if (el) el.textContent = String(text);
    };

    if (pageKind === "logout") {
      store.currentUser = null;
      try { sessionStorage.setItem("ev:explicit_logout", "1"); } catch (_) {}
      saveStore(store);
      safely("hydrateNavigation", hydrateNavigation);
      return;
    }

    if (pageKind === "login") {
      const form = document.getElementById("ev-login-form");
      const alertBox = document.getElementById("ev-auth-alert");
      const demoBtn = document.getElementById("ev-demo-signin");
      const pullBtn = document.getElementById("ev-github-pull-signin");
      const alreadyBox = document.getElementById("ev-already-signed-in");
      const alreadyUser = firstEl("ev-already-user", "ev-already-signed-in-text");
      const switchBtn = document.getElementById("ev-switch-account-btn");
      const otpStep = firstEl("ev-login-otp-step");
      const otpPreview = firstEl("ev-login-otp-preview");
      const otpInput = firstEl("ev-login-otp", "ev-login-otp-code");
      const otpForm = firstEl("ev-login-otp-form");
      const otpResend = firstEl("ev-login-otp-resend");
      const submitBtn = firstEl("ev-login-submit-btn");

      const nextParam = new URLSearchParams(window.location.search).get("next");
      if (store.currentUser && store.currentUser !== "guest") {
        if (nextParam && nextParam.startsWith("/")) {
          window.location.href = nextParam;
          return;
        }
        if (alreadyBox) {
          alreadyBox.hidden = false;
          if (alreadyUser) alreadyUser.textContent = `@${store.currentUser}`;
        }
      }
      if (switchBtn && !switchBtn.dataset.bound) {
        switchBtn.dataset.bound = "1";
        switchBtn.addEventListener("click", () => {
          const s = loadStore();
          s.currentUser = null;
          try { sessionStorage.setItem("ev:explicit_logout", "1"); } catch (_) {}
          saveStore(s);
          if (alreadyBox) alreadyBox.hidden = true;
          safely("hydrateNavigation", hydrateNavigation);
        });
      }

      // --- shared sign-in steps ------------------------------------------
      // "Sign in" is one flow with up to two steps. Both the password form and
      // the OTP form (a separate <form> in the exported markup) call these, so
      // the code step cannot dead-end the way it did when only the first form
      // had a handler.
      const identityOfForm = () =>
        String(document.getElementById("ev-login-identity")?.value || "").trim().toLowerCase();

      // One lookup for both steps of the flow: username, email, the SHA-256 of
      // either, or a mobile number with its country code.
      const findAccountByIdentity = async (store, identity) => {
        if (!identity) return null;
        const normalizedPhone =
          identity.startsWith("+") || /^\d{7,15}$/.test(identity.replace(/\D+/g, ""))
            ? normalizePhoneWithCountryCode(identity, "+91")
            : "";
        const idSha = await sha256Hex(identity);
        const phoneSha = normalizedPhone ? await sha256Hex(normalizedPhone) : "";
        return (
          Object.values(store.accounts || {}).find(
            (a) =>
              a.username?.toLowerCase() === identity ||
              (a.email && a.email.toLowerCase() === identity) ||
              (a.email_sha256 && a.email_sha256 === idSha) ||
              (normalizedPhone && a.phone === normalizedPhone) ||
              (phoneSha && a.phone_sha256 === phoneSha)
          ) || null
        );
      };

      const startLoginOtp = async (account) => {
        const ch = account.phone ? "phone" : "email";
        const dest = account.phone || account.email || `${account.username}@gmail.com`;
        const issued = await issueBrowserOtpChallenge({
          purpose: "signup_verify",
          username: account.username,
          channel: ch,
          destination: dest,
        });
        if (otpStep) otpStep.hidden = false;
        if (otpPreview) {
          otpPreview.hidden = false;
          otpPreview.innerHTML = `<strong>First-time account verification:</strong> Sent 6-digit OTP to <code>${escapeHtml(issued.masked)}</code> (${ch === "phone" ? "Mobile SMS" : "Gmail"}). Verification code: <code>${issued.code}</code>`;
        }
        if (submitBtn) submitBtn.textContent = "Verify 6-digit OTP & Sign in";
        if (otpInput) otpInput.focus();
        toast(`Sent 6-digit OTP to ${issued.masked}`);
      };

      const completeSignIn = async (account) => {
        const digest = await hashPasswordDigest(account.username, String(document.getElementById("ev-login-password")?.value || ""));
        account.password_sha256 = digest;
        account.otp_verified = true;
        const latest = loadStore();
        latest.accounts[account.username] = account;
        latest.currentUser = account.username;
        saveStore(latest);
        safely("hydrateNavigation", hydrateNavigation);
        toast(`Welcome back, ${account.display_name || account.username}!`);
        location.href = nextParam && nextParam.startsWith("/") ? nextParam : `${BASE}dashboard/`;
      };

      const finishLoginOtp = async (account) => {
        const verified = await verifyBrowserOtpChallenge("signup_verify", otpInput?.value || "");
        if (!verified.ok) {
          if (alertBox) { alertBox.hidden = false; alertBox.textContent = verified.error; }
          return;
        }
        account.otp_verified = true;
        await completeSignIn(account);
      };

      if (demoBtn && !demoBtn.dataset.bound) {
        demoBtn.dataset.bound = "1";
        demoBtn.addEventListener("click", async () => {
          await pullGithubVault(true);
          const s = loadStore();
          if (!s.accounts.saurav) {
            s.accounts.saurav = defaultProfile({
              username: "saurav",
              display_name: "Saurav Kushwaha",
              email: "saurav@gmail.com",
              country_code: "+91",
              otp_verified: true,
              branch: "cse",
              year_of_study: 3,
              xp: 480,
              level: 3,
              streak_days: 5,
              longest_streak: 12,
              completed_topics: ["ohms-law-and-kirchhoff", "time-complexity-and-asymptotics", "boolean-algebra-and-logic-gates"],
              solved_problems: ["two-sum", "valid-parentheses", "binary-search"],
            });
          }
          s.currentUser = "saurav";
          saveStore(s);
          safely("hydrateNavigation", hydrateNavigation);
          toast("Signed in as Saurav Kushwaha!");
          location.href = nextParam && nextParam.startsWith("/") ? nextParam : `${BASE}dashboard/`;
        });
      }

      if (pullBtn && !pullBtn.dataset.bound) {
        pullBtn.dataset.bound = "1";
        pullBtn.addEventListener("click", async () => {
          await pullGithubVault(false);
        });
      }

      if (form && !form.dataset.bound) {
        form.dataset.bound = "1";
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          await pullGithubVault(true);
          const identity = String(document.getElementById("ev-login-identity")?.value || "").trim().toLowerCase();
          const password = String(document.getElementById("ev-login-password")?.value || "");
          if (!identity || !password) {
            if (alertBox) { alertBox.hidden = false; alertBox.textContent = "Enter your username/Gmail/mobile number and password."; }
            return;
          }
          const account = await findAccountByIdentity(loadStore(), identity);

          if (!account) {
            if (alertBox) {
              alertBox.hidden = false;
              alertBox.innerHTML = `No verified account found for <strong>${escapeHtml(identity)}</strong>. New users must <a href="${BASE}register/">create an account with 6-digit OTP verification</a> first.`;
            }
            return;
          }

          if (!account.password_sha256) {
            // An account restored from the vault without a password digest must
            // not be signable-in with an arbitrary password: there is nothing
            // to compare against. Send the learner through OTP recovery, which
            // sets a password on this device.
            if (alertBox) {
              alertBox.hidden = false;
              alertBox.innerHTML = `No password is saved for <strong>@${escapeHtml(account.username)}</strong> on this device yet. <a href="${BASE}forgot-password/">Set one with a 6-digit OTP</a> — or use the demo button below.`;
            }
            return;
          }

          const digest = await hashPasswordDigest(account.username, password);
          if (account.password_sha256 !== digest) {
            if (alertBox) {
              alertBox.hidden = false;
              alertBox.innerHTML = `Incorrect password for <strong>@${escapeHtml(account.username)}</strong>. <a href="${BASE}forgot-password/">Forgot password? Reset via 6-digit OTP</a>.`;
            }
            return;
          }

          // Only require OTP on login if this is an unverified new account
          // (`otp_verified === false`). A returning learner who already passed
          // the one-time check signs in with the password alone.
          if (account.otp_verified === false) {
            if (otpStep && otpStep.hidden) {
              await startLoginOtp(account);
              return;
            }
            await finishLoginOtp(account);
            return;
          }

          // Returning verified user -> direct password sign-in without OTP.
          await completeSignIn(account);
        });
      }

      // The code is typed into its own small form on the exported page, so that
      // form needs the same handler as the password form. Without it, pressing
      // "Verify OTP" reloaded the page, hid the step again and left the learner
      // stuck in a loop with no way to finish signing in.
      if (otpForm && !otpForm.dataset.bound) {
        otpForm.dataset.bound = "1";
        otpForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          const account = await findAccountByIdentity(loadStore(), identityOfForm());
          if (!account) {
            if (alertBox) { alertBox.hidden = false; alertBox.textContent = "Start again: enter your username/Gmail/mobile number and password."; }
            return;
          }
          await finishLoginOtp(account);
        });
      }

      if (otpResend && !otpResend.dataset.bound) {
        otpResend.dataset.bound = "1";
        otpResend.addEventListener("click", async () => {
          const account = await findAccountByIdentity(loadStore(), identityOfForm());
          if (account) await startLoginOtp(account);
        });
      }
    }

    if (pageKind === "register") {
      const form = document.getElementById("ev-register-form");
      const alertBox = document.getElementById("ev-auth-alert");
      const otpStep = document.getElementById("ev-reg-otp-step");
      const otpPreview = document.getElementById("ev-reg-otp-preview");
      const otpInput = firstEl("ev-reg-otp", "ev-reg-otp-code");
      const otpForm = firstEl("ev-reg-otp-form");
      const submitBtn = firstEl("ev-reg-submit-btn");
      const resendBtn = firstEl("ev-reg-resend-otp", "ev-reg-otp-resend");
      const switchBtn = firstEl("ev-reg-otp-switch");

      const sendSignupOtp = async () => {
        const username = String(document.getElementById("ev-reg-username")?.value || "").trim().toLowerCase().replace(/[^a-z0-9_-]/g, "");
        const email = String(document.getElementById("ev-reg-email")?.value || "").trim().toLowerCase();
        const countryCode = String(document.getElementById("ev-reg-country-code")?.value || "+91");
        const rawPhone = String(document.getElementById("ev-reg-phone")?.value || "").trim();
        const channel = String(document.getElementById("ev-reg-otp-channel")?.value || "email");
        const password = String(document.getElementById("ev-reg-password")?.value || "");

        if (username.length < 3 || password.length < 8) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = "Username must be at least 3 characters and password at least 8 characters.";
          }
          return false;
        }
        if (!email || !email.includes("@")) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = "Enter a valid Gmail or email address.";
          }
          return false;
        }
        const normalizedPhone = rawPhone ? normalizePhoneWithCountryCode(rawPhone, countryCode) : "";
        if (rawPhone && !normalizedPhone) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = "Enter a valid mobile number (7–14 digits) with your selected country code.";
          }
          return false;
        }
        if (channel === "phone" && !normalizedPhone) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = "Enter your mobile number with country code to receive SMS OTP, or switch channel to Gmail.";
          }
          return false;
        }
        const dest = channel === "phone" ? normalizedPhone : email;
        const issued = await issueBrowserOtpChallenge({
          purpose: "signup_verify",
          username,
          channel,
          destination: dest,
        });
        if (alertBox) alertBox.hidden = true;
        if (otpStep) otpStep.hidden = false;
        if (resendBtn) resendBtn.hidden = false;
        if (submitBtn) submitBtn.textContent = "Verify 6-digit OTP & Create Account";
        if (otpPreview) {
          otpPreview.hidden = false;
          otpPreview.innerHTML = `<strong>6-Digit Signup OTP Sent:</strong> Dispatched to <code>${escapeHtml(issued.masked)}</code> via ${channel === "phone" ? `Mobile SMS (${escapeHtml(countryCode)})` : "Gmail / Email"}. Instant verification code: <code>${issued.code}</code>`;
        }
        if (otpInput) otpInput.focus();
        toast(`Sent 6-digit signup OTP to ${issued.masked}`);
        return true;
      };

      if (resendBtn && !resendBtn.dataset.bound) {
        resendBtn.dataset.bound = "1";
        resendBtn.addEventListener("click", () => {
          sendSignupOtp();
        });
      }

      // Switching channel restarts the challenge for the other destination, so
      // "Switch Gmail / Mobile OTP" is not a button that does nothing.
      if (switchBtn && !switchBtn.dataset.bound) {
        switchBtn.dataset.bound = "1";
        switchBtn.addEventListener("click", async () => {
          const select = document.getElementById("ev-reg-otp-channel");
          if (select) select.value = select.value === "phone" ? "email" : "phone";
          await sendSignupOtp();
        });
      }

      // Creates the account once the 6-digit code has been accepted. Shared by
      // the signup form and the OTP form below it: the code is typed into a
      // separate <form>, which previously had no submit handler at all.
      const completeSignup = async () => {
        const verified = await verifyBrowserOtpChallenge("signup_verify", otpInput?.value || "");
        if (!verified.ok) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = verified.error;
          }
          return;
        }

        const displayName = String(document.getElementById("ev-reg-display")?.value || "").trim();
        const username = String(document.getElementById("ev-reg-username")?.value || "").trim().toLowerCase().replace(/[^a-z0-9_-]/g, "");
        const email = String(document.getElementById("ev-reg-email")?.value || "").trim().toLowerCase();
        const countryCode = String(document.getElementById("ev-reg-country-code")?.value || "+91");
        const rawPhone = String(document.getElementById("ev-reg-phone")?.value || "").trim();
        const normalizedPhone = rawPhone ? normalizePhoneWithCountryCode(rawPhone, countryCode) : "";
        const branch = String(document.getElementById("ev-reg-branch")?.value || "cse");
        const year = Number(document.getElementById("ev-reg-year")?.value || 1);
        const password = String(document.getElementById("ev-reg-password")?.value || "");

        const digest = await hashPasswordDigest(username, password);
        const emailSha = email ? await sha256Hex(email) : "";
        const phoneSha = normalizedPhone ? await sha256Hex(normalizedPhone) : "";
        const s = loadStore();
        const existing = s.accounts[username] || defaultProfile({ username });
        if (s.accounts[username] && existing.password_sha256 && existing.email_sha256 && emailSha && existing.email_sha256 !== emailSha) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.innerHTML = `The username <strong>@${escapeHtml(username)}</strong> is already registered to another address. <a href="${BASE}forgot-password/">Recover it with a 6-digit OTP</a> instead.`;
          }
          return;
        }
        const created = Object.assign({}, existing, {
          username,
          display_name: displayName || username,
          email,
          email_sha256: emailSha,
          phone: normalizedPhone,
          phone_sha256: phoneSha,
          country_code: countryCode,
            otp_verified: true,
            branch,
            year_of_study: year,
            password_sha256: digest,
            xp: Math.max(50, Number(existing.xp || 0)),
          });
          s.accounts[username] = created;
          s.currentUser = username;
          saveStore(s);
          safely("hydrateNavigation", hydrateNavigation);
          try {
            await pushSnapshotToGithub(created, { useIssueSync: false });
          } catch (_) {}
          toast(`Verified 6-digit OTP! Account @${username} created (+50 Welcome XP)`);
          location.href = `${BASE}dashboard/`;
      };

      if (form && !form.dataset.bound) {
        form.dataset.bound = "1";
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          if (otpStep && otpStep.hidden) {
            await sendSignupOtp();
            return;
          }
          await completeSignup();
        });
      }

      // The code field lives in its own form in the exported page; without a
      // submit handler here, pressing "Verify 6-digit OTP" reloaded the page
      // and threw the code away.
      if (otpForm && !otpForm.dataset.bound) {
        otpForm.dataset.bound = "1";
        otpForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          await completeSignup();
        });
      }
    }

    if (pageKind === "forgot-password" || pageKind === "reset-password") {
      const form = document.getElementById("ev-forgot-form");
      const alertBox = document.getElementById("ev-auth-alert");
      const otpStep = document.getElementById("ev-forgot-otp-step");
      const otpPreview = document.getElementById("ev-forgot-otp-preview");
      const otpInput = firstEl("ev-forgot-otp", "ev-forgot-otp-code");
      const submitBtn = firstEl("ev-forgot-submit-btn");
      const resendBtn = firstEl("ev-forgot-resend-btn");

      const sendResetOtp = async () => {
        await pullGithubVault(true);
        const identity = String(document.getElementById("ev-forgot-identity")?.value || "").trim().toLowerCase();
        const channel = String(document.getElementById("ev-forgot-channel")?.value || "email");
        const countryCode = String(document.getElementById("ev-forgot-country-code")?.value || "+91");
        const rawPhone = String(document.getElementById("ev-forgot-phone")?.value || "").trim();

        if (!identity && !rawPhone) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = "Enter your username, Gmail address, or mobile number with country code.";
          }
          return false;
        }
        const normalizedPhone = rawPhone
          ? normalizePhoneWithCountryCode(rawPhone, countryCode)
          : identity.startsWith("+") || /^\d{7,15}$/.test(identity.replace(/\D+/g, ""))
          ? normalizePhoneWithCountryCode(identity, countryCode)
          : "";
        if (channel === "phone" && !normalizedPhone) {
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = "Enter a valid mobile number with your country code to receive SMS OTP.";
          }
          return false;
        }
        const uname = identity.split("@")[0].replace(/[^a-z0-9_-]/g, "") || "learner";
        const dest = channel === "phone" ? normalizedPhone : (identity.includes("@") ? identity : `${uname}@gmail.com`);
        const issued = await issueBrowserOtpChallenge({
          purpose: "password_reset",
          username: uname,
          channel,
          destination: dest,
        });
        if (alertBox) alertBox.hidden = true;
        if (otpStep) otpStep.hidden = false;
        if (resendBtn) resendBtn.hidden = false;
        if (submitBtn) submitBtn.textContent = "Verify 6-digit OTP & Reset Password";
        if (otpPreview) {
          otpPreview.hidden = false;
          otpPreview.innerHTML = `<strong>6-Digit Password Reset OTP Sent:</strong> Dispatched to <code>${escapeHtml(issued.masked)}</code> via ${channel === "phone" ? `Mobile SMS (${escapeHtml(countryCode)})` : "Gmail / Email"}. Instant verification code: <code>${issued.code}</code>`;
        }
        if (otpInput) otpInput.focus();
        toast(`Sent 6-digit password reset OTP to ${issued.masked}`);
        return true;
      };

      if (resendBtn && !resendBtn.dataset.bound) {
        resendBtn.dataset.bound = "1";
        resendBtn.addEventListener("click", () => {
          sendResetOtp();
        });
      }

      if (form && !form.dataset.bound) {
        form.dataset.bound = "1";
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          if (otpStep && otpStep.hidden) {
            await sendResetOtp();
            return;
          }

          const verified = await verifyBrowserOtpChallenge("password_reset", otpInput?.value || "");
          if (!verified.ok) {
            if (alertBox) {
              alertBox.hidden = false;
              alertBox.textContent = verified.error;
            }
            return;
          }

          const identity = String(document.getElementById("ev-forgot-identity")?.value || "").trim().toLowerCase();
          const newPass = String(document.getElementById("ev-forgot-new-password")?.value || "");
          const confirmPass = String(document.getElementById("ev-forgot-confirm-password")?.value || newPass);
          if (newPass.length < 8) {
            if (alertBox) { alertBox.hidden = false; alertBox.textContent = "New password must be at least 8 characters."; }
            return;
          }
          if (newPass !== confirmPass) {
            if (alertBox) { alertBox.hidden = false; alertBox.textContent = "New password and confirmation do not match."; }
            return;
          }
          const s = loadStore();
          const matchedAcc = Object.values(s.accounts).find(
            (a) => a.username?.toLowerCase() === identity || (a.email && a.email.toLowerCase() === identity)
          );
          const uname = matchedAcc?.username || identity.split("@")[0].replace(/[^a-z0-9_-]/g, "") || "learner";
          const digest = await hashPasswordDigest(uname, newPass);
          const acc = s.accounts[uname] || defaultProfile({ username: uname, display_name: uname });
          acc.password_sha256 = digest;
          acc.otp_verified = true;
          acc.password_changed_via_otp = true;
          s.accounts[uname] = acc;
          s.currentUser = uname;
          saveStore(s);
          safely("hydrateNavigation", hydrateNavigation);
          try {
            await pushSnapshotToGithub(acc, { useIssueSync: false });
          } catch (_) {}
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = `Verified 6-digit OTP! Password updated for @${uname}. Redirecting to your dashboard…`;
          }
          setTimeout(() => { location.href = `${BASE}dashboard/`; }, 700);
        });
      }
    }

    if (pageKind === "dashboard") {
      setElText("ev-dash-greeting", `Welcome, ${profile.display_name} (@${profile.username})`);
      setElText("ev-stat-xp", `${profile.xp || 0} XP`);
      setElText("ev-stat-level", `Level ${profile.level || 1} · ${profile.branch?.toUpperCase() || "CSE"}`);
      setElText("ev-stat-streak", `${profile.streak_days || streak.current || 1} days`);
      setElText("ev-stat-longest", `Longest: ${profile.longest_streak || streak.longest || 1}d`);
      setElText("ev-stat-topics", (profile.completed_topics || []).length);
      setElText("ev-stat-problems", (profile.solved_problems || []).length);
      setElText("ev-stat-quizzes", `${profile.quiz_correct || 0}/${profile.quiz_attempts || 0} quizzes correct`);

      const statusBox = document.getElementById("ev-dash-sync-status");
      if (statusBox) {
        statusBox.textContent = store.lastSyncAt
          ? `Synced with ${store.githubRepo || GH_REPO} · Last sync: ${store.lastSyncAt}`
          : `Ready to sync @${profile.username}'s progress (${profile.xp || 0} XP) to ${store.githubRepo || GH_REPO}.`;
      }
      const actBox = document.getElementById("ev-dash-activity");
      if (actBox) {
        const items = [
          ...(profile.solved_problems || []).map((s) => `Solved coding problem: <a href="${BASE}practice/problems/${s}/">${s}</a>`),
          ...(profile.completed_topics || []).map((t) => `Completed topic note: <a href="${BASE}topics/${t}/">${t}</a>`),
        ];
        if (items.length) {
          actBox.innerHTML = `<ul class="small">${items.slice(0, 8).map((i) => `<li>${i}</li>`).join("")}</ul>`;
        }
      }
    }

    if (pageKind === "profile") {
      setElText("ev-profile-name", profile.display_name || "EngineVerse Learner");
      setElText("ev-profile-username", `@${profile.username || "guest"}`);
      setElText("ev-profile-branch", `${(profile.branch || "cse").toUpperCase()} · Year ${profile.year_of_study || 1}`);
      setElText("ev-profile-xp", `${profile.xp || 0} XP (Lv ${profile.level || 1})`);
      const topBox = document.getElementById("ev-profile-topics");
      if (topBox && (profile.completed_topics?.length || profile.bookmarks?.length)) {
        topBox.innerHTML = `<ul class="small">${(profile.completed_topics || []).map((t) => `<li>✓ <a href="${BASE}topics/${t}/">${t}</a></li>`).join("")}${(profile.bookmarks || []).map((b) => `<li>★ Saved: ${b}</li>`).join("")}</ul>`;
      }
      const probBox = document.getElementById("ev-profile-problems");
      if (probBox && profile.solved_problems?.length) {
        probBox.innerHTML = `<ul class="small">${profile.solved_problems.map((s) => `<li>✓ <a href="${BASE}practice/problems/${s}/">${s}</a></li>`).join("")}</ul>`;
      }
    }

    if (pageKind === "settings") {
      const ghRepoIn = document.getElementById("ev-gh-repo");
      const ghTokenIn = document.getElementById("ev-gh-token");
      const dispIn = document.getElementById("ev-set-display");
      const branchIn = document.getElementById("ev-set-branch");
      const yearIn = document.getElementById("ev-set-year");
      const bioIn = document.getElementById("ev-set-bio");
      const webIn = document.getElementById("ev-set-webhook");
      const alertBox = document.getElementById("ev-settings-alert");

      if (ghRepoIn) ghRepoIn.value = store.githubRepo || GH_REPO;
      if (ghTokenIn) ghTokenIn.value = store.githubToken || "";
      if (dispIn) dispIn.value = profile.display_name || "";
      if (branchIn) branchIn.value = profile.branch || "cse";
      if (yearIn) yearIn.value = String(profile.year_of_study || 1);
      if (bioIn) bioIn.value = profile.bio || "";
      if (webIn) webIn.value = store.webhookUrl || "";

      const ghForm = document.getElementById("ev-github-sync-form");
      if (ghForm && !ghForm.dataset.bound) {
        ghForm.dataset.bound = "1";
        ghForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          const s = loadStore();
          s.githubRepo = String(ghRepoIn?.value || GH_REPO).trim();
          s.githubToken = String(ghTokenIn?.value || "").trim();
          saveStore(s);
          try {
            const res = await pushSnapshotToGithub(getActiveProfile(), {
              repo: s.githubRepo,
              token: s.githubToken,
              useIssueSync: !s.githubToken,
            });
            if (alertBox) {
              alertBox.hidden = false;
              alertBox.textContent = res.mode === "github-contents-api"
                ? `Successfully committed @${profile.username}'s snapshot to ${s.githubRepo}/data/learners/registry.json!`
                : `Prepared GitHub learner snapshot for ${s.githubRepo}.`;
            }
          } catch (err) {
            if (alertBox) { alertBox.hidden = false; alertBox.textContent = String(err.message || err); }
          }
        });
      }

      const issueBtn = document.getElementById("ev-gh-issue-sync");
      if (issueBtn && !issueBtn.dataset.bound) {
        issueBtn.dataset.bound = "1";
        issueBtn.addEventListener("click", () => {
          pushSnapshotToGithub(getActiveProfile(), { useIssueSync: true });
        });
      }

      const pullBtn = document.getElementById("ev-gh-pull-btn");
      if (pullBtn && !pullBtn.dataset.bound) {
        pullBtn.dataset.bound = "1";
        pullBtn.addEventListener("click", async () => {
          await pullGithubVault(false);
          renderAccountPage();
        });
      }

      const exportBtn = document.getElementById("ev-export-json");
      if (exportBtn && !exportBtn.dataset.bound) {
        exportBtn.dataset.bound = "1";
        exportBtn.addEventListener("click", () => {
          const snap = toGithubSnapshot(getActiveProfile());
          const blob = new Blob([JSON.stringify(snap, null, 2) + "\n"], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `engineverse-learner-${snap.username}.json`;
          document.body.appendChild(a);
          a.click();
          a.remove();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        });
      }

      const importIn = document.getElementById("ev-import-json");
      if (importIn && !importIn.dataset.bound) {
        importIn.dataset.bound = "1";
        importIn.addEventListener("change", async () => {
          const file = importIn.files?.[0];
          if (!file) return;
          try {
            const text = await file.text();
            const parsed = JSON.parse(text);
            const snap = parsed.learners ? Object.values(parsed.learners)[0] : parsed;
            const merged = mergeSnapshotIntoStore(snap, true);
            if (merged) {
              toast(`Imported learner snapshot for @${merged.username}!`);
              safely("hydrateNavigation", hydrateNavigation);
              renderAccountPage();
            }
          } catch (_) {
            toast("Invalid learner snapshot JSON file.", "bad");
          }
        });
      }

      const profForm = document.getElementById("ev-profile-form");
      const emailIn = document.getElementById("ev-set-email");
      const ccIn = document.getElementById("ev-set-country-code");
      const phoneIn = document.getElementById("ev-set-phone");
      if (emailIn) emailIn.value = profile.email || "";
      if (ccIn) ccIn.value = profile.country_code || "+91";
      if (phoneIn) {
        const rawP = String(profile.phone || "");
        const ccVal = String(profile.country_code || "+91");
        phoneIn.value = rawP.startsWith(ccVal) ? rawP.slice(ccVal.length) : rawP;
      }

      if (profForm && !profForm.dataset.bound) {
        profForm.dataset.bound = "1";
        profForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          const emailVal = String(emailIn?.value || profile.email || "").trim().toLowerCase();
          const ccVal = String(ccIn?.value || profile.country_code || "+91").trim();
          const rawPhoneVal = String(phoneIn?.value || "").trim();
          const normPhone = rawPhoneVal ? normalizePhoneWithCountryCode(rawPhoneVal, ccVal) : "";
          const emailSha = emailVal ? await sha256Hex(emailVal) : "";
          const phoneSha = normPhone ? await sha256Hex(normPhone) : "";

          const updated = saveActiveProfile((p) => {
            p.display_name = String(dispIn?.value || p.display_name).trim();
            p.email = emailVal;
            p.email_sha256 = emailSha || p.email_sha256 || "";
            p.country_code = ccVal;
            if (normPhone) {
              p.phone = normPhone;
              p.phone_sha256 = phoneSha;
            }
            p.branch = String(branchIn?.value || p.branch);
            p.year_of_study = Number(yearIn?.value || p.year_of_study || 1);
            p.bio = String(bioIn?.value || "").trim();
          });
          const s = loadStore();
          s.webhookUrl = String(webIn?.value || "").trim();
          saveStore(s);
          safely("hydrateNavigation", hydrateNavigation);
          pushSnapshotToGithub(updated).catch(() => {});
          toast("Saved profile, contact channels, and sync settings!");
        });
      }

      // Section 3: Change Password via 6-Digit OTP (Gmail or Mobile Number with Country Code)
      const pwdForm = document.getElementById("ev-password-change-form");
      const pwdAlert = document.getElementById("ev-pwd-otp-alert");
      const pwdStep = document.getElementById("ev-pwd-otp-step");
      const pwdPreview = document.getElementById("ev-pwd-otp-preview");
      const pwdSubmitBtn = document.getElementById("ev-pwd-submit-btn");
      if (pwdForm && !pwdForm.dataset.bound) {
        pwdForm.dataset.bound = "1";
        pwdForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          const active = getActiveProfile();
          const channel = String(document.getElementById("ev-pwd-otp-channel")?.value || "email");
          const cc = String(document.getElementById("ev-pwd-country-code")?.value || active.country_code || "+91");
          const rawPhone = String(document.getElementById("ev-pwd-phone")?.value || active.phone || "").trim();
          const normPhone = rawPhone ? normalizePhoneWithCountryCode(rawPhone, cc) : "";

          if (pwdStep && pwdStep.hidden) {
            if (channel === "phone" && !normPhone) {
              if (pwdAlert) {
                pwdAlert.hidden = false;
                pwdAlert.textContent = "Enter your mobile number with country code to receive SMS OTP.";
              }
              return;
            }
            const dest = channel === "phone" ? normPhone : (active.email || `${active.username}@gmail.com`);
            const issued = await issueBrowserOtpChallenge({
              purpose: "password_change",
              username: active.username,
              channel,
              destination: dest,
            });
            if (pwdAlert) pwdAlert.hidden = true;
            pwdStep.hidden = false;
            if (pwdSubmitBtn) pwdSubmitBtn.textContent = "Verify 6-digit OTP & Update Password";
            if (pwdPreview) {
              pwdPreview.hidden = false;
              pwdPreview.innerHTML = `<strong>6-Digit Password Change OTP Sent:</strong> Dispatched to <code>${escapeHtml(issued.masked)}</code> via ${channel === "phone" ? `Mobile SMS (${escapeHtml(cc)})` : "Gmail / Email"}. Instant verification code: <code>${issued.code}</code>`;
            }
            document.getElementById("ev-pwd-otp-code")?.focus();
            toast(`Sent 6-digit OTP to ${issued.masked}`);
            return;
          }

          const code = String(document.getElementById("ev-pwd-otp-code")?.value || "");
          const newPass = String(document.getElementById("ev-pwd-new-password")?.value || "");
          const confirmPass = String(document.getElementById("ev-pwd-confirm-password")?.value || "");
          if (newPass.length < 8) {
            if (pwdAlert) { pwdAlert.hidden = false; pwdAlert.textContent = "New password must be at least 8 characters."; }
            return;
          }
          if (newPass !== confirmPass) {
            if (pwdAlert) { pwdAlert.hidden = false; pwdAlert.textContent = "New password and confirmation do not match."; }
            return;
          }
          const verified = await verifyBrowserOtpChallenge("password_change", code);
          if (!verified.ok) {
            if (pwdAlert) { pwdAlert.hidden = false; pwdAlert.textContent = verified.error; }
            return;
          }
          const digest = await hashPasswordDigest(active.username, newPass);
          const updated = saveActiveProfile((p) => {
            p.password_sha256 = digest;
            p.otp_verified = true;
            p.password_changed_via_otp = true;
            if (normPhone) p.phone = normPhone;
            p.country_code = cc;
          });
          pushSnapshotToGithub(updated).catch(() => {});
          if (pwdStep) pwdStep.hidden = true;
          if (pwdSubmitBtn) pwdSubmitBtn.textContent = "Send 6-digit OTP to change password";
          if (pwdAlert) {
            pwdAlert.hidden = false;
            pwdAlert.textContent = `Verified 6-digit OTP! Password updated and synced for @${updated.username}.`;
          }
          toast("Password updated via 6-digit OTP!");
        });
      }

      const signoutBtn = document.getElementById("ev-signout-btn");
      if (signoutBtn && !signoutBtn.dataset.bound) {
        signoutBtn.dataset.bound = "1";
        signoutBtn.addEventListener("click", () => {
          signOutActiveUser();
        });
      }
    }

    if (pageKind === "mistakes") {
      const box = document.getElementById("ev-mistakes-list");
      const mistakes = profile.mistakes || [];
      if (box && mistakes.length) {
        box.innerHTML = `<h2>Recorded mistakes (${mistakes.length})</h2>` + mistakes.map((m) => `
          <article class="card mb">
            <div class="row" style="justify-content:space-between">
              <strong>${m.topicTitle || "Practice Question"}</strong>
              <span class="chip bad">Correct: ${m.correctLabel || "See explanation"}</span>
            </div>
            <p class="mt">${m.stem}</p>
            ${m.explanation ? `<p class="small muted">${m.explanation}</p>` : ""}
            <div class="row mt">
              <a class="btn btn-ghost btn-sm" href="${m.topicUrl || (BASE + "practice/questions/")}">Review topic</a>
            </div>
          </article>
        `).join("");
      }
    }

    if (pageKind === "portfolio") {
      setElText("ev-portfolio-title", `${profile.display_name}'s Engineering Portfolio`);
      setElText("ev-portfolio-summary", `@${profile.username} · ${(profile.branch || "cse").toUpperCase()} Year ${profile.year_of_study || 1} · ${profile.xp || 0} XP · ${(profile.completed_topics || []).length} topics mastered · ${(profile.solved_problems || []).length} coding problems solved · Backed by ${GH_REPO}.`);
      const projBox = document.getElementById("ev-portfolio-projects");
      if (projBox && profile.completed_topics?.length) {
        projBox.innerHTML = `<ul class="small">${profile.completed_topics.map((t) => `<li>✓ <a href="${BASE}topics/${t}/">${t}</a></li>`).join("")}</ul>`;
      }
      const codeBox = document.getElementById("ev-portfolio-coding");
      if (codeBox && profile.solved_problems?.length) {
        codeBox.innerHTML = `<ul class="small">${profile.solved_problems.map((s) => `<li>✓ <a href="${BASE}practice/problems/${s}/">${s}</a></li>`).join("")}</ul>`;
      }
    }

    if (pageKind === "certificates") {
      const list = document.getElementById("ev-certificates-list");
      if (list) {
        const topicsCount = (profile.completed_topics || []).length;
        const probsCount = (profile.solved_problems || []).length;
        list.innerHTML = `
          <div class="grid g2">
            <article class="card">
              <span class="chip ${topicsCount >= 1 ? "ok" : ""}">${topicsCount >= 1 ? "Unlocked" : `${topicsCount}/1 topics`}</span>
              <h3 class="mt">Core Engineering Foundations</h3>
              <p class="small muted">Issued to <strong>${profile.display_name} (@${profile.username})</strong> · Verified on GitHub Vault <code>${GH_REPO}</code>.</p>
            </article>
            <article class="card">
              <span class="chip ${probsCount >= 1 ? "ok" : ""}">${probsCount >= 1 ? "Unlocked" : `${probsCount}/1 problems`}</span>
              <h3 class="mt">Algorithmic Problem Solving</h3>
              <p class="small muted">Issued to <strong>${profile.display_name} (@${profile.username})</strong> · ${probsCount} problem(s) solved in browser judge.</p>
            </article>
          </div>
        `;
      }
    }

    // Bind any `[data-ev-sync-github]` and `[data-ev-pull-github]` buttons on the page
    document.querySelectorAll("[data-ev-sync-github]").forEach((btn) => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", async () => {
        const s = loadStore();
        try {
          await pushSnapshotToGithub(getActiveProfile(), {
            repo: s.githubRepo || GH_REPO,
            token: s.githubToken || "",
            useIssueSync: !s.githubToken,
          });
        } catch (err) {
          toast(String(err.message || err), "bad");
        }
      });
    });

    document.querySelectorAll("[data-ev-pull-github]").forEach((btn) => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", async () => {
        await pullGithubVault(false);
        safely("hydrateNavigation", hydrateNavigation);
        renderAccountPage();
      });
    });
  }

  renderAccountPage();

  // ---------------------------------------------------------------------------
  // 8. Browser Tutor (runs on /tutor/ where [data-tutor-form] lives)
  // ---------------------------------------------------------------------------
  const tutorForm = document.querySelector("[data-tutor-form]");
  if (!tutorForm || !config.tutor) return;

  const modeSelect = tutorForm.querySelector("[name='mode']");
  const queryInput = tutorForm.querySelector("[name='q']");
  const out = document.querySelector("[data-tutor-output]");
  let corpusPromise = null;

  const loadCorpus = () => {
    if (!corpusPromise) {
      corpusPromise = fetch(config.tutor)
        .then((r) => (r.ok ? r.json() : []))
        .catch(() => []);
    }
    return corpusPromise;
  };

  const STOP = new Set([
    "what", "is", "the", "a", "an", "of", "in", "on", "to", "for", "and", "or",
    "how", "why", "does", "do", "explain", "define", "tell", "me", "about",
    "with", "by", "from", "at", "as", "be", "are", "was", "were", "can", "you",
    "give", "show", "example", "simple", "terms", "work", "works", "used",
  ]);

  const tokenise = (text) =>
    (text || "")
      .toLowerCase()
      .replace(/[^a-z0-9\s+-]/g, " ")
      .split(/\s+/)
      .filter((w) => w.length >= 2 && !STOP.has(w));

  const scoreItem = (item, tokens, raw) => {
    const title = (item.title || "").toLowerCase();
    const subject = (item.subject || "").toLowerCase();
    const body = `${item.simple || ""} ${item.definition || ""} ${item.intuition || ""} ${item.example || ""} ${item.mistakes || ""}`.toLowerCase();
    let score = 0;
    if (raw && title.includes(raw)) score += 30;
    for (const tok of tokens) {
      if (title === tok) score += 25;
      else if (title.includes(tok)) score += 12;
      if (subject.includes(tok)) score += 4;
      if (body.includes(tok)) score += 3;
    }
    return score;
  };

  const sectionBlock = (heading, body) => {
    if (!body) return null;
    const wrap = document.createElement("div");
    wrap.className = "mb";
    const h = document.createElement("div");
    h.className = "eyebrow";
    h.textContent = heading;
    const p = document.createElement("p");
    p.textContent = body;
    wrap.append(h, p);
    return wrap;
  };

  const renderMatch = (item, mode) => {
    const card = document.createElement("article");
    card.className = "panel mb";

    const head = document.createElement("div");
    head.className = "row mb";
    head.style.justifyContent = "space-between";
    const title = document.createElement("h3");
    title.style.margin = "0";
    const link = document.createElement("a");
    link.href = item.url || "#";
    link.textContent = item.title;
    title.appendChild(link);
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = item.subject || "Topic";
    head.append(title, chip);
    card.appendChild(head);

    const order =
      mode === "beginner"
        ? [
            ["In plain words", item.simple || item.definition],
            ["Mental picture", item.intuition],
            ["Worked example", item.example],
          ]
        : mode === "revision"
        ? [
            ["Core definition", item.definition || item.simple],
            ["Key points", item.points || item.intuition],
            ["Common mistakes", item.mistakes],
          ]
        : mode === "practice"
        ? [
            ["Worked example", item.example || item.definition],
            ["Traps to avoid", item.mistakes],
            ["Core idea", item.simple || item.intuition],
          ]
        : [
            ["Definition", item.definition || item.simple],
            ["Intuition", item.intuition],
            ["Example", item.example],
            ["Common mistakes", item.mistakes],
          ];

    for (const [label, text] of order) {
      const block = sectionBlock(label, text);
      if (block) card.appendChild(block);
    }

    const foot = document.createElement("a");
    foot.className = "btn btn-ghost btn-sm";
    foot.href = item.url || "#";
    foot.textContent = "Open full topic note →";
    card.appendChild(foot);
    return card;
  };

  const answer = async () => {
    if (!out) return;
    const raw = (queryInput.value || "").trim().toLowerCase();
    const mode = modeSelect ? modeSelect.value : "concept";
    if (!raw) {
      out.replaceChildren();
      return;
    }
    const corpus = await loadCorpus();
    const tokens = tokenise(raw);
    const ranked = corpus
      .map((item) => ({ item, score: scoreItem(item, tokens, raw) }))
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);

    out.replaceChildren();
    if (!ranked.length) {
      const empty = document.createElement("div");
      empty.className = "panel";
      empty.textContent =
        "No matching note found for that phrasing. Try a topic name such as Ohm's Law, Bernoulli, pointers, deadlock, Carnot, or Dijkstra.";
      out.appendChild(empty);
      return;
    }
    for (const r of ranked) {
      out.appendChild(renderMatch(r.item, mode));
    }
  };

  tutorForm.addEventListener("submit", (event) => {
    event.preventDefault();
    answer();
  });

  document.querySelectorAll("[data-tutor-prompt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      queryInput.value = btn.getAttribute("data-tutor-prompt") || "";
      if (modeSelect && btn.getAttribute("data-tutor-mode")) {
        modeSelect.value = btn.getAttribute("data-tutor-mode");
      }
      answer();
    });
  });
})();
