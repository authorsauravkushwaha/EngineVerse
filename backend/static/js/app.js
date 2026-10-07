/* EngineVerse front-end.
 * Vanilla JS, no dependencies, no CDN. Everything here is progressive
 * enhancement: every feature has a working no-JS path via plain HTML forms.
 */
(() => {
  "use strict";

  const cfg = window.EngineVerse || { csrf: "", user: false };
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  // ---------------------------------------------------------------- API ----
  async function api(path, options = {}) {
    const opts = Object.assign({ headers: {} }, options);
    opts.headers["X-CSRF-Token"] = cfg.csrf;
    if (opts.body && !(opts.body instanceof FormData)) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(path, opts);
    let data = {};
    try { data = await res.json(); } catch (_) { /* non-JSON */ }
    if (!res.ok || data.ok === false) {
      const err = new Error(data.error || `Request failed (${res.status})`);
      err.status = res.status;
      throw err;
    }
    return data;
  }

  function toast(message, kind = "ok") {
    let box = $("#toast");
    if (!box) {
      box = document.createElement("div");
      box.id = "toast";
      box.setAttribute("role", "status");
      box.style.cssText = "position:fixed;left:50%;bottom:26px;transform:translateX(-50%);" +
        "background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:10px 20px;" +
        "box-shadow:var(--shadow-lg);z-index:200;font-size:.9rem;max-width:90vw;transition:opacity .3s";
      document.body.appendChild(box);
    }
    box.textContent = message;
    box.style.borderColor = kind === "bad" ? "var(--bad)" : "var(--ok)";
    box.style.opacity = "1";
    clearTimeout(box._t);
    box._t = setTimeout(() => { box.style.opacity = "0"; }, 3200);
  }

  // ------------------------------------------------------- mobile nav + menu
  const toggle = $("#navtoggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const bar = $(".topbar");
      const open = bar.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }
  $$("[data-menu]").forEach((menu) => {
    const btn = $("button", menu);
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const open = menu.hasAttribute("data-open");
      $$("[data-menu]").forEach((m) => m.removeAttribute("data-open"));
      if (!open) menu.setAttribute("data-open", "");
      btn.setAttribute("aria-expanded", String(!open));
    });
  });
  document.addEventListener("click", () =>
    $$("[data-menu]").forEach((m) => m.removeAttribute("data-open")));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") $$("[data-menu]").forEach((m) => m.removeAttribute("data-open"));
  });

  // --------------------------------------------------------- live search box
  const searchInput = $("#global-search");
  const suggestBox = $("#suggest");
  if (searchInput && suggestBox) {
    let timer = null;
    searchInput.addEventListener("input", () => {
      const q = searchInput.value.trim();
      clearTimeout(timer);
      if (q.length < 2) { suggestBox.hidden = true; return; }
      timer = setTimeout(async () => {
        try {
          const data = await api(`/api/search/suggest?q=${encodeURIComponent(q)}`);
          if (!data.suggestions.length) { suggestBox.hidden = true; return; }
          suggestBox.innerHTML = data.suggestions
            .map((s) => `<a href="/search?q=${encodeURIComponent(s.title)}">
              <span class="t">${escapeHtml(s.type)}</span><span>${escapeHtml(s.title)}</span></a>`)
            .join("");
          suggestBox.hidden = false;
        } catch (_) { suggestBox.hidden = true; }
      }, 180);
    });
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".searchbox")) suggestBox.hidden = true;
    });
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // -------------------------------------------------------------- bookmarks
  $$("[data-bookmark]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!cfg.user) { location.href = "/login"; return; }
      const type = btn.dataset.type || btn.dataset.bookmark;
      const id = btn.dataset.id;
      try {
        const res = await api("/api/bookmarks", { method: "POST", body: { entityType: type, entityId: id } });
        btn.classList.toggle("on", res.bookmarked);
        btn.setAttribute("aria-pressed", String(res.bookmarked));
        btn.textContent = res.bookmarked ? "★ Saved" : "☆ Save";
        toast(res.bookmarked ? "Saved to your bookmarks" : "Removed from bookmarks");
      } catch (err) { toast(err.message, "bad"); }
    });
  });

  // ------------------------------------------------------------- MCQ quiz
  $$("[data-quiz]").forEach((card) => {
    const qid = card.dataset.quiz;
    const form = $("form", card);
    if (!form) return;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const picked = form.querySelector("input[name=option]:checked");
      if (!picked) { toast("Pick an answer first", "bad"); return; }
      const index = Number(picked.value);
      const submit = $("button[type=submit]", form);
      submit.disabled = true;
      try {
        const res = await api("/api/practice/answer", {
          method: "POST",
          body: { questionId: qid, optionIndex: index, setId: card.dataset.set || null },
        });
        $$(".opt", card).forEach((opt) => {
          opt.classList.add("locked");
          const i = Number(opt.dataset.index);
          if (i === res.correctIndex) opt.classList.add("correct");
          else if (i === index) opt.classList.add("wrong");
          $$("input", opt).forEach((inp) => { inp.disabled = true; });
        });
        const explain = $(".explain", card);
        if (explain) explain.classList.add("on");
        const badge = $(".verdict-inline", card);
        if (badge) {
          badge.textContent = res.correct ? "Correct" : "Not quite";
          badge.className = `verdict-inline chip ${res.correct ? "ok" : "bad"}`;
          badge.style.display = "inline-block";
        }
        if (res.xpAwarded) toast(`+${res.xpAwarded} XP`);
      } catch (err) {
        toast(err.message, "bad");
        submit.disabled = false;
      }
    });
  });

  // ---------------------------------------------------------- code editor
  const editor = $("#code-editor");
  if (editor) {
    const langSelect = $("#lang-select");
    const stubs = JSON.parse(editor.dataset.stubs || "{}");
    const problemSlug = editor.dataset.problem || "";
    const output = $("#run-output");
    const customInput = $("#custom-input");
    const STORAGE = `ev:code:${problemSlug}`;

    const saved = localStorage.getItem(STORAGE);
    if (saved) editor.value = saved;

    editor.addEventListener("input", () => localStorage.setItem(STORAGE, editor.value));

    // Real tab handling instead of losing focus.
    editor.addEventListener("keydown", (e) => {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = editor.selectionStart;
        editor.value = editor.value.slice(0, start) + "    " + editor.value.slice(editor.selectionEnd);
        editor.selectionStart = editor.selectionEnd = start + 4;
        localStorage.setItem(STORAGE, editor.value);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        $("#btn-run")?.click();
      }
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "b") {
        e.preventDefault();
        $("#btn-submit")?.click();
      }
    });

    if (langSelect) {
      langSelect.addEventListener("change", () => {
        const lang = langSelect.value;
        const stored = localStorage.getItem(`${STORAGE}:${lang}`);
        if (stored) { editor.value = stored; return; }
        const stub = stubs[lang];
        if (stub) editor.value = stub.stub || stub;
        $("#stub-signature")?.replaceChildren(
          Object.assign(document.createElement("code"), { textContent: (stub && stub.signature) || "" }));
      });
    }

    function renderRun(result) {
      if (!output) return;
      const status = result.status || "internal_error";
      const lines = [`status: ${status}`];
      if (result.runtime_ms != null) lines.push(`time: ${result.runtime_ms} ms`);
      if (result.stdout) lines.push("", "--- stdout ---", result.stdout);
      if (result.stderr) lines.push("", "--- stderr ---", result.stderr.slice(0, 4000));
      output.innerHTML = `<div class="verdict ${status}">${status.replace(/_/g, " ")}</div>` +
        `<pre class="console">${escapeHtml(lines.join("\n"))}</pre>`;
    }

    function renderEvaluation(result) {
      if (!output) return;
      const parts = [`<div class="verdict ${result.status}">${result.status.replace(/_/g, " ")} — ` +
        `${result.passed}/${result.total} tests</div>`];
      parts.push('<pre class="console">' + escapeHtml(
        `time: ${result.runtime_ms} ms` + (result.stderr ? `\n\n${result.stderr.slice(0, 3000)}` : "")) + "</pre>");
      (result.cases || []).forEach((c, i) => {
        parts.push(`<div class="testcase ${c.passed ? "pass" : "fail"}">
          <div class="lbl">${c.passed ? "✓" : "✗"} Test ${i + 1}${c.is_sample ? " (sample)" : ""}</div>
          <pre>input:    ${escapeHtml(c.input || "(none)")}
expected: ${escapeHtml(c.expected)}
actual:   ${escapeHtml(c.actual)}</pre></div>`);
      });
      output.innerHTML = parts.join("");
    }

    $("#btn-run")?.addEventListener("click", async () => {
      const btn = $("#btn-run");
      btn.disabled = true;
      btn.innerHTML = '<span class="spin"></span> Running';
      try {
        const lang = langSelect ? langSelect.value : "python";
        localStorage.setItem(`${STORAGE}:${lang}`, editor.value);
        const res = await api("/api/coding/run", {
          method: "POST",
          body: { language: lang, code: editor.value, input: customInput ? customInput.value : "",
                  problemSlug: problemSlug || null },
        });
        renderRun(res.result);
      } catch (err) { toast(err.message, "bad"); }
      btn.disabled = false;
      btn.textContent = "Run";
    });

    $("#btn-submit")?.addEventListener("click", async () => {
      if (!cfg.user) { location.href = "/login"; return; }
      const btn = $("#btn-submit");
      btn.disabled = true;
      btn.innerHTML = '<span class="spin"></span> Judging';
      try {
        const lang = langSelect ? langSelect.value : "python";
        const res = await api("/api/coding/submit", {
          method: "POST",
          body: { problemSlug, language: lang, code: editor.value },
        });
        renderEvaluation(res.result);
        if (res.result.status === "accepted") {
          toast(`Accepted — +${res.result.xpAwarded || 0} XP`);
          const solved = $("#solved-chip");
          if (solved) solved.classList.remove("hide");
        }
      } catch (err) { toast(err.message, "bad"); }
      btn.disabled = false;
      btn.textContent = "Submit";
    });

    $("#btn-reset")?.addEventListener("click", () => {
      const lang = langSelect ? langSelect.value : "python";
      const stub = stubs[lang];
      if (stub) editor.value = stub.stub || stub;
      localStorage.removeItem(`${STORAGE}:${lang}`);
    });
  }

  // ---------------------------------------------------------- flashcards
  const deck = $("#flashdeck");
  if (deck) {
    const cards = JSON.parse(deck.dataset.cards || "[]");
    let i = Number(deck.dataset.start || 0);
    const face = $("#card-face");
    const counter = $("#card-counter");

    function paint() {
      if (!cards.length) {
        deck.innerHTML = '<div class="empty"><span class="em">🎉</span>Nothing due right now. Come back later.</div>';
        return;
      }
      i = ((i % cards.length) + cards.length) % cards.length;
      const card = cards[i];
      face.querySelector(".front .txt").textContent = card.front;
      face.querySelector(".back .txt").textContent = card.back;
      face.classList.remove("flip");
      counter.textContent = `Card ${i + 1} of ${cards.length}`;
      deck.dataset.current = card.id;
    }

    face.addEventListener("click", () => face.classList.toggle("flip"));
    deck.addEventListener("keydown", (e) => {
      if (e.key === " " || e.key === "Enter") { e.preventDefault(); face.classList.toggle("flip"); }
    });
    $$(".rate", deck).forEach((btn) => {
      btn.addEventListener("click", async () => {
        const rating = btn.dataset.rate;
        try {
          await api("/api/revision/review", {
            method: "POST", body: { cardId: deck.dataset.current, rating },
          });
          const stats = await api("/api/revision/due?limit=1");
          const remaining = $("#due-count");
          if (remaining && stats.stats) remaining.textContent = stats.stats.due;
          cards.splice(i, 1);
          paint();
          toast(rating === "again" ? "Card will come back sooner" : "Reviewed");
        } catch (err) { toast(err.message, "bad"); }
      });
    });
    paint();
  }

  // ------------------------------------------------------------- voting
  $$("[data-vote]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!cfg.user) { location.href = "/login"; return; }
      try {
        const res = await api("/api/community/vote", {
          method: "POST",
          body: { entityType: btn.dataset.type, entityId: btn.dataset.id, value: Number(btn.dataset.vote) },
        });
        const box = btn.closest(".votebox");
        box.querySelector(".n").textContent = res.score;
        $$("button", box).forEach((b) => b.classList.remove("on"));
        btn.classList.add("on");
      } catch (err) { toast(err.message, "bad"); }
    });
  });

  // ---------------------------------------------------- mark topic complete
  $$("[data-complete-topic]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!cfg.user) { location.href = "/login"; return; }
      btn.disabled = true;
      try {
        const res = await api("/api/me/progress/topic", {
          method: "POST", body: { topicId: btn.dataset.id, status: "completed" },
        });
        btn.textContent = "Completed ✓";
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-soft");
        const lvl = $(".xpchip .lvl");
        if (lvl && res.stats) lvl.textContent = res.stats.level;
        toast("Topic marked complete — +20 XP");
      } catch (err) { toast(err.message, "bad"); btn.disabled = false; }
    });
  });

  // ------------------------------------------------------- diagram hotspots
  $$("[data-diagram]").forEach((wrap) => {
    const spots = JSON.parse(wrap.dataset.hotspots || "[]");
    const note = $(".hotspot-note", wrap);
    const svg = $("svg", wrap);
    if (!svg || !spots.length) return;
    const vb = svg.viewBox.baseVal;
    spots.forEach((spot) => {
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("x", spot.x); rect.setAttribute("y", spot.y);
      rect.setAttribute("width", spot.w); rect.setAttribute("height", spot.h);
      rect.setAttribute("fill", "rgba(56,189,248,.10)");
      rect.setAttribute("stroke", "#38bdf8"); rect.setAttribute("stroke-width", "1.5");
      rect.setAttribute("rx", "6");
      rect.style.cursor = "pointer";
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = spot.label;
      rect.appendChild(title);
      rect.addEventListener("click", () => {
        note.innerHTML = `<strong>${escapeHtml(spot.label)}.</strong> ${escapeHtml(spot.explain)}`;
        note.classList.add("on");
      });
      svg.appendChild(rect);
    });
    void vb;
  });

  // -------------------------------------------------------------- PWA
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => { /* offline support optional */ });
    });
  }
  let deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const btn = $("#install-btn");
    if (btn) btn.classList.remove("hide");
  });
  $("#install-btn")?.addEventListener("click", async () => {
    if (!deferredPrompt) { toast("Use your browser menu → Add to Home Screen"); return; }
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
  });

  // -------------------------------------------------- auto-dismiss flash
  const flash = $(".flash");
  if (flash) setTimeout(() => { flash.style.transition = "opacity .5s"; flash.style.opacity = "0";
    setTimeout(() => flash.remove(), 500); }, 4200);

  // ----------------------------------------------------- 3D tilt on tiles
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    $$(".tile").forEach((tile) => {
      tile.addEventListener("mousemove", (e) => {
        const r = tile.getBoundingClientRect();
        const rx = ((e.clientY - r.top) / r.height - 0.5) * -10;
        const ry = ((e.clientX - r.left) / r.width - 0.5) * 10;
        tile.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg) translateY(-5px)`;
      });
      tile.addEventListener("mouseleave", () => { tile.style.transform = ""; });
    });
  }

  window.EV = { api, toast, escapeHtml };
})();
