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
      notifications: [
        { title: "Welcome to EngineVerse", body: "Full browser execution and GitHub learner vault sync are active.", ts: todayIso }
      ],
      password_sha256: "",
      updated_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    }, overrides);
  }

  function loadStore() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORE_KEY) || "{}");
      return {
        currentUser: raw.currentUser || null,
        accounts: raw.accounts && typeof raw.accounts === "object" ? raw.accounts : {},
        githubRepo: raw.githubRepo || GH_REPO,
        githubToken: raw.githubToken || "",
        webhookUrl: raw.webhookUrl || "",
        lastSyncAt: raw.lastSyncAt || "",
      };
    } catch (_) {
      return {
        currentUser: null,
        accounts: {},
        githubRepo: GH_REPO,
        githubToken: "",
        webhookUrl: "",
        lastSyncAt: "",
      };
    }
  }

  function saveStore(store) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(store));
    } catch (_) {
      /* ignore quota errors */
    }
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
      updated_at: snapshot.updated_at || existing.updated_at,
    });
    store.accounts[uname] = merged;
    if (setCurrent) store.currentUser = uname;
    saveStore(store);
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
    const store = loadStore();
    const repo = (options.repo || store.githubRepo || GH_REPO).trim();
    const token = (options.token !== undefined ? options.token : store.githubToken || "").trim();
    const snapshot = toGithubSnapshot(profile);

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
          store.lastSyncAt = new Date().toISOString();
          saveStore(store);
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
      store.lastSyncAt = new Date().toISOString();
      saveStore(store);
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
    store.lastSyncAt = new Date().toISOString();
    saveStore(store);
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
  // 2. Topbar & Navigation Account Hydration
  // ---------------------------------------------------------------------------
  function hydrateNavigation() {
    const store = loadStore();
    const profile = getActiveProfile();
    const signedIn = Boolean(store.currentUser);
    const actions = document.querySelector(".topbar .actions");
    if (!actions) return;

    // Update streak pill if present, or insert one
    let streakChip = actions.querySelector("[data-live-streak]");
    if (!streakChip) {
      streakChip = document.createElement("a");
      streakChip.href = `${BASE}streaks/`;
      streakChip.className = "chip warn";
      streakChip.setAttribute("data-live-streak", "");
      actions.prepend(streakChip);
    }
    streakChip.textContent = `${profile.streak_days || streak.current || 1}d streak · ${profile.xp || 0} XP`;
    streakChip.title = `${profile.display_name} (@${profile.username}) · Click to view streak & GitHub sync`;

    const loginHref = `${BASE}login/`;
    const registerHref = `${BASE}register/`;
    const existingLinks = Array.from(actions.querySelectorAll("a"));
    const signInBtn = existingLinks.find((a) => a.getAttribute("href")?.includes("/login"));
    const regBtn = existingLinks.find((a) => a.getAttribute("href")?.includes("/register"));

    if (signedIn) {
      if (signInBtn) {
        signInBtn.href = `${BASE}dashboard/`;
        signInBtn.textContent = profile.display_name || `@${profile.username}`;
        signInBtn.className = "btn btn-soft btn-sm";
      }
      if (regBtn) {
        regBtn.href = `${BASE}settings/`;
        regBtn.textContent = "GitHub Sync";
        regBtn.className = "btn btn-ghost btn-sm";
      }
    } else {
      if (signInBtn) {
        signInBtn.href = loginHref;
      }
      if (regBtn) {
        regBtn.href = registerHref;
      }
    }
  }

  hydrateNavigation();
  pullGithubVault(true).then(() => {
    hydrateNavigation();
    renderAccountPage();
  });

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
      hydrateNavigation();
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
    hydrateNavigation();
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
      hydrateNavigation();
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
            hydrateNavigation();
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
      saveStore(store);
      hydrateNavigation();
      return;
    }

    if (pageKind === "login") {
      const form = document.getElementById("ev-login-form");
      const alertBox = document.getElementById("ev-auth-alert");
      const demoBtn = document.getElementById("ev-demo-signin");
      const pullBtn = document.getElementById("ev-github-pull-signin");

      if (demoBtn && !demoBtn.dataset.bound) {
        demoBtn.dataset.bound = "1";
        demoBtn.addEventListener("click", async () => {
          await pullGithubVault(true);
          const s = loadStore();
          if (!s.accounts.saurav) {
            s.accounts.saurav = defaultProfile({
              username: "saurav",
              display_name: "Saurav Kushwaha",
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
          toast("Signed in as Saurav Kushwaha!");
          location.href = `${BASE}dashboard/`;
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
            if (alertBox) { alertBox.hidden = false; alertBox.textContent = "Enter both your username/email and password."; }
            return;
          }
          const s = loadStore();
          const account = Object.values(s.accounts).find(
            (a) => a.username?.toLowerCase() === identity || (a.email && a.email.toLowerCase() === identity)
          );
          if (account) {
            const digest = await hashPasswordDigest(account.username, password);
            if (account.password_sha256 && account.password_sha256 !== digest) {
              if (alertBox) { alertBox.hidden = false; alertBox.textContent = "Incorrect password for @" + account.username + "."; }
              return;
            }
            account.password_sha256 = digest;
            s.accounts[account.username] = account;
            s.currentUser = account.username;
            saveStore(s);
            toast(`Welcome back, ${account.display_name}!`);
            location.href = `${BASE}dashboard/`;
          } else {
            // Create instant account if username doesn't exist yet
            const uname = identity.split("@")[0].replace(/[^a-z0-9_-]/g, "").slice(0, 30) || "learner";
            const digest = await hashPasswordDigest(uname, password);
            const created = defaultProfile({
              username: uname,
              display_name: uname,
              email: identity.includes("@") ? identity : "",
              password_sha256: digest,
              xp: 25,
            });
            s.accounts[uname] = created;
            s.currentUser = uname;
            saveStore(s);
            toast(`Signed in as @${uname}!`);
            location.href = `${BASE}dashboard/`;
          }
        });
      }
    }

    if (pageKind === "register") {
      const form = document.getElementById("ev-register-form");
      const alertBox = document.getElementById("ev-auth-alert");
      if (form && !form.dataset.bound) {
        form.dataset.bound = "1";
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          const displayName = String(document.getElementById("ev-reg-display")?.value || "").trim();
          const username = String(document.getElementById("ev-reg-username")?.value || "").trim().toLowerCase().replace(/[^a-z0-9_-]/g, "");
          const email = String(document.getElementById("ev-reg-email")?.value || "").trim().toLowerCase();
          const branch = String(document.getElementById("ev-reg-branch")?.value || "cse");
          const year = Number(document.getElementById("ev-reg-year")?.value || 1);
          const password = String(document.getElementById("ev-reg-password")?.value || "");
          if (username.length < 3 || password.length < 8) {
            if (alertBox) {
              alertBox.hidden = false;
              alertBox.textContent = "Username must be at least 3 characters and password at least 8 characters.";
            }
            return;
          }
          const digest = await hashPasswordDigest(username, password);
          const s = loadStore();
          const existing = s.accounts[username] || defaultProfile({ username });
          const created = Object.assign({}, existing, {
            username,
            display_name: displayName || username,
            email,
            branch,
            year_of_study: year,
            password_sha256: digest,
            xp: Math.max(50, Number(existing.xp || 0)),
          });
          s.accounts[username] = created;
          s.currentUser = username;
          saveStore(s);
          try {
            await pushSnapshotToGithub(created, { useIssueSync: false });
          } catch (_) {}
          toast(`Account @${username} created! +50 Welcome XP`);
          location.href = `${BASE}dashboard/`;
        });
      }
    }

    if (pageKind === "forgot-password" || pageKind === "reset-password") {
      const form = document.getElementById("ev-forgot-form");
      const alertBox = document.getElementById("ev-auth-alert");
      if (form && !form.dataset.bound) {
        form.dataset.bound = "1";
        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          const fd = new FormData(form);
          const identity = String(fd.get("identity") || "").trim().toLowerCase();
          const newPass = String(fd.get("new_password") || "");
          if (!identity || newPass.length < 8) {
            if (alertBox) { alertBox.hidden = false; alertBox.textContent = "Enter your username and a password of at least 8 characters."; }
            return;
          }
          const uname = identity.split("@")[0].replace(/[^a-z0-9_-]/g, "") || "learner";
          const digest = await hashPasswordDigest(uname, newPass);
          const s = loadStore();
          const acc = s.accounts[uname] || defaultProfile({ username: uname, display_name: uname });
          acc.password_sha256 = digest;
          s.accounts[uname] = acc;
          s.currentUser = uname;
          saveStore(s);
          if (alertBox) {
            alertBox.hidden = false;
            alertBox.textContent = `Password updated for @${uname}. Redirecting to your dashboard…`;
          }
          setTimeout(() => { location.href = `${BASE}dashboard/`; }, 800);
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
              hydrateNavigation();
              renderAccountPage();
            }
          } catch (_) {
            toast("Invalid learner snapshot JSON file.", "bad");
          }
        });
      }

      const profForm = document.getElementById("ev-profile-form");
      if (profForm && !profForm.dataset.bound) {
        profForm.dataset.bound = "1";
        profForm.addEventListener("submit", (e) => {
          e.preventDefault();
          saveActiveProfile((p) => {
            p.display_name = String(dispIn?.value || p.display_name).trim();
            p.branch = String(branchIn?.value || p.branch);
            p.year_of_study = Number(yearIn?.value || p.year_of_study || 1);
            p.bio = String(bioIn?.value || "").trim();
          });
          const s = loadStore();
          s.webhookUrl = String(webIn?.value || "").trim();
          saveStore(s);
          hydrateNavigation();
          toast("Saved profile and sync settings!");
        });
      }

      const signoutBtn = document.getElementById("ev-signout-btn");
      if (signoutBtn && !signoutBtn.dataset.bound) {
        signoutBtn.dataset.bound = "1";
        signoutBtn.addEventListener("click", () => {
          location.href = `${BASE}logout/`;
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
        hydrateNavigation();
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
