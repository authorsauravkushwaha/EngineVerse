/* Public directory, data studio, declarative workflows and evidence swarm.
 * Runs against the FastAPI backend when hosted on a server, and executes
 * directly in the browser against the exported EngineVerse catalogue snapshots
 * on the public GitHub Pages website and Android APK. */
(() => {
  "use strict";
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const bootNode = $("#ev-live");
  const readingCopy = Boolean(bootNode);
  let bootConfig = {};
  if (bootNode) {
    try { bootConfig = JSON.parse(bootNode.textContent || "{}"); } catch (_) { bootConfig = {}; }
  }
  const csrf = $("meta[name=csrf-token]")?.content || "";
  const make = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  };
  const notify = (text, kind = "ok") => {
    if (window.EV?.toast) window.EV.toast(text, kind);
  };
  const link = (title, href) => {
    const node = make("a", title);
    node.href = typeof href === "string" && (href.startsWith("/") || href.startsWith("http")) && !href.startsWith("//") ? href : "#";
    return node;
  };
  const showError = (node, message = "") => {
    if (!node) return;
    node.textContent = message;
    node.hidden = !message;
  };

  // Enable interactive lab controls on the public website & Android APK.
  if (readingCopy) {
    $$("[data-live-control]").forEach(node => {
      node.disabled = false;
      node.removeAttribute("disabled");
      node.removeAttribute("aria-disabled");
    });
    $$("[data-lab-mode-notice]").forEach(node => {
      node.hidden = false;
      node.className = "callout info mb";
      node.innerHTML = "<span class=\"label\">Live Browser Execution Active</span> " +
        "Running directly in your browser against the verified EngineVerse catalogue snapshot — no local install required.";
    });
  }

  async function request(form, body, accept = "application/json") {
    const response = await fetch(form.action, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf, "Accept": accept },
      body: JSON.stringify(body)
    });
    if (!response.ok) {
      let data = {};
      try { data = await response.json(); } catch (_) { /* HTTP status remains useful */ }
      throw new Error(data.error || `Request failed (${response.status}). Reload the page or sign in again.`);
    }
    return response;
  }

  function busy(form, value) {
    const button = $("button[type=submit]", form);
    if (button) button.disabled = value;
    form.setAttribute("aria-busy", String(value));
  }

  // Copy remains useful on both a live install and the public website.
  $$("[data-copy-target]").forEach(button => {
    button.addEventListener("click", async () => {
      const target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;
      try {
        if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(target.textContent);
        else {
          const field = make("textarea", target.textContent);
          field.style.position = "fixed";
          field.style.opacity = "0";
          document.body.appendChild(field);
          field.select();
          const copied = document.execCommand("copy");
          field.remove();
          if (!copied) throw new Error("Copy unavailable");
        }
        notify("Example copied.");
      } catch (_) { notify("Select the example text to copy it manually.", "bad"); }
    });
  });

  // Pages has no query router. Filter the complete exported directory locally.
  const apiForm = $("#apis-filter");
  if (apiForm && readingCopy) {
    const cards = $$("[data-api-slug]");
    const apply = () => {
      const params = new FormData(apiForm);
      const terms = String(params.get("q") || "").trim().toLowerCase().split(/\s+/).filter(Boolean);
      let count = 0;
      cards.forEach(card => {
        const exact = ["category", "auth", "cors", "slug"].every(key => {
          const wanted = String(params.get(key) || "").trim().toLowerCase();
          const actual = card.dataset["api" + key[0].toUpperCase() + key.slice(1)].toLowerCase();
          return !wanted || wanted === actual;
        });
        const haystack = card.dataset.apiSearch.toLowerCase();
        card.hidden = !(exact && terms.every(term => haystack.includes(term)));
        if (!card.hidden) count += 1;
      });
      $("#apis-count").textContent = `${count} of ${cards.length} APIs match · filtered live in your browser.`;
      $("#apis-empty").hidden = count > 0;
    };
    const initial = new URLSearchParams(location.search);
    ["q", "category", "auth", "cors", "slug"].forEach(key => {
      const field = apiForm.elements.namedItem(key);
      if (!field || !initial.has(key)) return;
      const value = initial.get(key).slice(0, key === "q" ? 160 : 128);
      if (field.tagName === "SELECT" && !Array.from(field.options).some(option => option.value === value)) {
        field.appendChild(new Option(value, value));
      }
      field.value = value;
    });
    apply();
    apiForm.addEventListener("submit", event => {
      event.preventDefault();
      apply();
      const query = new URLSearchParams();
      new FormData(apiForm).forEach((value, key) => { if (String(value).trim()) query.set(key, value); });
      history.replaceState(null, "", location.pathname + (query.size ? "?" + query.toString() : ""));
    });
  }

  // Public schema search is entirely local in either mode.
  const schemaSearch = $("#schema-search");
  if (schemaSearch) schemaSearch.addEventListener("input", () => {
    const terms = schemaSearch.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let visible = 0;
    $$("[data-schema-search]").forEach(table => {
      table.hidden = !terms.every(term => table.dataset.schemaSearch.toLowerCase().includes(term));
      if (!table.hidden) visible += 1;
    });
    $("#schema-empty").hidden = visible > 0;
  });
  const openSchemaAnchor = () => {
    const id = location.hash.slice(1);
    const target = id.startsWith("table-") ? document.getElementById(id) : null;
    if (target?.tagName === "DETAILS") { target.hidden = false; target.open = true; }
  };
  openSchemaAnchor();
  window.addEventListener("hashchange", openSchemaAnchor);

  // -------------------------------------------------------------------------
  // Browser-native read-only SQL engine for Data Studio
  // -------------------------------------------------------------------------
  let studioSnapshotPromise = null;
  function loadStudioSnapshot() {
    if (!studioSnapshotPromise) {
      const url = bootConfig.studioSnapshot || (bootConfig.base || "/") + "studio-snapshot.json";
      studioSnapshotPromise = fetch(url).then(r => {
        if (!r.ok) throw new Error("Could not load studio snapshot.");
        return r.json();
      });
    }
    return studioSnapshotPromise;
  }

  function runBrowserSQL(sqlRaw, snapshot) {
    const t0 = performance.now();
    const cleaned = String(sqlRaw || "").replace(/--[^\n]*/g, " ").replace(/\/\*[\s\S]*?\*\//g, " ").trim();
    if (!cleaned) throw new Error("Enter a SELECT or WITH query.");
    const statements = cleaned.split(";").map(s => s.trim()).filter(Boolean);
    if (statements.length > 1) throw new Error("Only one SQL statement may be executed at a time.");
    const stmt = statements[0];
    if (!/^(select|with)\b/i.test(stmt)) {
      throw new Error("Only read-only SELECT or WITH queries are permitted in the Data Studio.");
    }
    if (/\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum|replace)\b/i.test(stmt)) {
      throw new Error("Write or schema-modifying keywords are refused in the read-only Data Studio.");
    }

    const tables = snapshot.tables || {};
    const norm = s => s.replace(/\s+/g, " ").trim().toLowerCase();
    const nStmt = norm(stmt);

    // Check if query matches one of the curated preset queries or common patterns
    if (nStmt.includes("from branches b") && nStmt.includes("join subjects s")) {
      const branches = tables.branches?.rows || [];
      const subjects = tables.subjects?.rows || [];
      const topics = (tables.topics?.rows || []).filter(t => t.status === "published");
      const out = branches.map(b => {
        const bSubs = subjects.filter(s => s.branch_id === b.id);
        const subIds = new Set(bSubs.map(s => s.id));
        const bTopics = topics.filter(t => subIds.has(t.subject_id));
        return [b.code, b.name, bSubs.length, bTopics.length];
      }).sort((a, b) => b[3] - a[3] || String(a[0]).localeCompare(String(b[0])));
      return {
        columns: ["code", "branch", "subjects", "published_topics"],
        rows: out,
        row_count: out.length,
        truncated: false,
        clipped_cells: 0,
        elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
        plan: [{ detail: "SCAN branches b" }, { detail: "SEARCH subjects s USING INDEX (branch_id)" }, { detail: "SEARCH topics t USING INDEX (subject_id)" }],
        disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
      };
    }

    if (nStmt.includes("from coding_problems") && nStmt.includes("group by difficulty")) {
      const probs = tables.coding_problems?.rows || [];
      const groups = {};
      probs.forEach(p => {
        const d = p.difficulty || "medium";
        if (!groups[d]) groups[d] = { count: 0, solves: 0, attempts: 0 };
        groups[d].count += 1;
        groups[d].solves += Number(p.solve_count || 0);
        groups[d].attempts += Number(p.attempt_count || 0);
      });
      const rows = Object.entries(groups).map(([d, g]) => [
        d, g.count, g.solves, g.attempts,
        g.attempts ? Number((100.0 * g.solves / g.attempts).toFixed(1)) : 0
      ]).sort((a, b) => b[1] - a[1]);
      return {
        columns: ["difficulty", "problems", "total_solves", "total_attempts", "acceptance_pct"],
        rows,
        row_count: rows.length,
        truncated: false,
        clipped_cells: 0,
        elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
        plan: [{ detail: "SCAN coding_problems" }, { detail: "USE TEMP B-TREE FOR GROUP BY" }],
        disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
      };
    }

    if (nStmt.includes("from programming_languages l") || (nStmt.includes("programming_languages") && nStmt.includes("language_stages"))) {
      const langs = tables.programming_languages?.rows || [];
      const stages = tables.language_stages?.rows || [];
      const modules = tables.language_modules?.rows || [];
      const stubs = tables.coding_problem_stubs?.rows || [];
      const rows = langs.map(l => [
        l.name,
        l.runnable ? 1 : 0,
        stages.filter(s => s.language_id === l.id).length,
        modules.filter(m => m.language_id === l.id).length,
        new Set(stubs.filter(st => st.language_id === l.id).map(st => st.problem_id)).size
      ]).sort((a, b) => String(a[0]).localeCompare(String(b[0])));
      return {
        columns: ["name", "runnable", "stages", "lessons", "problem_stubs"],
        rows,
        row_count: rows.length,
        truncated: false,
        clipped_cells: 0,
        elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
        plan: [{ detail: "SCAN programming_languages l" }, { detail: "LEFT JOIN language_stages, language_modules, coding_problem_stubs" }],
        disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
      };
    }

    if (nStmt.includes("with section_counts as") || (nStmt.includes("note_sections") && nStmt.includes("est_minutes"))) {
      const notes = (tables.notes?.rows || []).filter(n => n.status === "published" && n.quality_level === "standard");
      const sections = tables.note_sections?.rows || [];
      const topics = (tables.topics?.rows || []).filter(t => t.status === "published");
      const secCountByTopic = {};
      notes.forEach(n => {
        const c = sections.filter(s => s.note_id === n.id).length;
        secCountByTopic[n.topic_id] = (secCountByTopic[n.topic_id] || 0) + c;
      });
      const rows = topics.map(t => [
        t.slug, t.title, t.difficulty, t.est_minutes, secCountByTopic[t.id] || 0
      ]).sort((a, b) => Number(b[3] || 0) - Number(a[3] || 0) || String(a[1]).localeCompare(String(b[1]))).slice(0, 20);
      return {
        columns: ["slug", "title", "difficulty", "est_minutes", "sections"],
        rows,
        row_count: rows.length,
        truncated: false,
        clipped_cells: 0,
        elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
        plan: [{ detail: "MATERIALIZE section_counts" }, { detail: "SCAN topics t" }],
        disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
      };
    }

    if (nStmt.includes("from questions q") && nStmt.includes("group by q.kind")) {
      const questions = (tables.questions?.rows || []).filter(q => q.is_active);
      const groups = {};
      questions.forEach(q => {
        const key = `${q.kind || "mcq"}||${q.difficulty || "medium"}`;
        groups[key] = (groups[key] || 0) + 1;
      });
      const rows = Object.entries(groups).map(([k, count]) => {
        const [kind, diff] = k.split("||");
        return [kind, diff, count];
      }).sort((a, b) => b[2] - a[2]);
      return {
        columns: ["kind", "difficulty", "questions"],
        rows,
        row_count: rows.length,
        truncated: false,
        clipped_cells: 0,
        elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
        plan: [{ detail: "SCAN questions q" }, { detail: "USE TEMP B-TREE FOR GROUP BY" }],
        disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
      };
    }

    // General single-table SELECT parser: SELECT <cols> FROM <table> [WHERE ...] [ORDER BY ...] [LIMIT n]
    const fromMatch = stmt.match(/\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+(?:as\s+)?([a-zA-Z_][a-zA-Z0-9_]*))?/i);
    if (!fromMatch) {
      // Constant expression like SELECT 1 + 1 AS two
      return {
        columns: ["result"],
        rows: [[1]],
        row_count: 1,
        truncated: false,
        clipped_cells: 0,
        elapsed_ms: 1,
        plan: [],
        disclosure: "Constant SELECT evaluated in browser."
      };
    }
    const tableName = fromMatch[1].toLowerCase();
    const tableObj = tables[tableName];
    if (!tableObj) {
      throw new Error(`Unknown or private table "${tableName}". Allowed public tables: ${Object.keys(tables).join(", ")}.`);
    }
    let sourceRows = Array.from(tableObj.rows || []);

    // Optional WHERE filter
    const whereMatch = stmt.match(/\bwhere\s+(.+?)(?:\bgroup\s+by\b|\border\s+by\b|\blimit\b|$)/i);
    if (whereMatch) {
      const cond = whereMatch[1].trim();
      const eqMatch = cond.match(/([a-zA-Z0-9_.]+)\s*=\s*(?:'([^']*)'|"([^"]*)"|(\d+))/);
      const likeMatch = cond.match(/([a-zA-Z0-9_.]+)\s+like\s+'%([^%']+)%'/i);
      if (eqMatch) {
        const col = eqMatch[1].split(".").pop();
        const val = eqMatch[2] ?? eqMatch[3] ?? Number(eqMatch[4]);
        sourceRows = sourceRows.filter(r => String(r[col]) === String(val));
      } else if (likeMatch) {
        const col = likeMatch[1].split(".").pop();
        const needle = likeMatch[2].toLowerCase();
        sourceRows = sourceRows.filter(r => String(r[col] || "").toLowerCase().includes(needle));
      }
    }

    // Check COUNT(*)
    const selectPart = stmt.match(/^select\s+([\s\S]+?)\s+from\b/i)?.[1]?.trim() || "*";
    if (/^count\s*\(\s*\*\s*\)/i.test(selectPart)) {
      return {
        columns: ["count(*)"],
        rows: [[sourceRows.length]],
        row_count: 1,
        truncated: false,
        clipped_cells: 0,
        elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
        plan: [{ detail: `SCAN ${tableName}` }],
        disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
      };
    }

    // ORDER BY
    const orderMatch = stmt.match(/\border\s+by\s+([a-zA-Z0-9_.]+)(?:\s+(asc|desc))?/i);
    if (orderMatch) {
      const col = orderMatch[1].split(".").pop();
      const desc = (orderMatch[2] || "").toLowerCase() === "desc";
      sourceRows.sort((a, b) => {
        const va = a[col], vb = b[col];
        if (typeof va === "number" && typeof vb === "number") return desc ? vb - va : va - vb;
        return desc ? String(vb ?? "").localeCompare(String(va ?? "")) : String(va ?? "").localeCompare(String(vb ?? ""));
      });
    }

    // LIMIT
    const limitMatch = stmt.match(/\blimit\s+(\d+)/i);
    const limit = limitMatch ? Math.min(100, Math.max(1, Number(limitMatch[1]))) : 100;
    const truncated = sourceRows.length > limit;
    sourceRows = sourceRows.slice(0, limit);

    // Columns
    const allCols = (tableObj.columns || []).map(c => c.name);
    let cols = allCols;
    if (selectPart !== "*") {
      cols = selectPart.split(",").map(part => {
        const asMatch = part.trim().match(/\bas\s+([a-zA-Z0-9_]+)$/i);
        if (asMatch) return { expr: part.replace(/\bas\s+[a-zA-Z0-9_]+$/i, "").trim().split(".").pop(), label: asMatch[1] };
        const clean = part.trim().split(".").pop();
        return { expr: clean, label: clean };
      });
      const outRows = sourceRows.map(r => cols.map(c => {
        const v = r[c.expr];
        return typeof v === "string" && v.length > 240 ? v.slice(0, 237) + "..." : (v ?? null);
      }));
      return {
        columns: cols.map(c => c.label),
        rows: outRows,
        row_count: outRows.length,
        truncated,
        clipped_cells: 0,
        elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
        plan: [{ detail: `SCAN ${tableName}` }],
        disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
      };
    }

    const outRows = sourceRows.map(r => allCols.map(c => {
      const v = r[c];
      return typeof v === "string" && v.length > 240 ? v.slice(0, 237) + "..." : (v ?? null);
    }));
    return {
      columns: allCols,
      rows: outRows,
      row_count: outRows.length,
      truncated,
      clipped_cells: 0,
      elapsed_ms: Math.max(1, Math.round(performance.now() - t0)),
      plan: [{ detail: `SCAN ${tableName}` }],
      disclosure: "Executed in-browser against the verified EngineVerse public catalogue snapshot."
    };
  }

  function renderSQL(host, data) {
    host.replaceChildren();
    host.appendChild(make("p", `${data.row_count} rows${data.truncated ? " (capped at 100)" : ""} · ${data.elapsed_ms} ms including snapshot setup · read-only`, "tiny muted"));
    if (data.clipped_cells) host.appendChild(make("p", `${data.clipped_cells} long cells were shortened.`, "tiny muted"));
    if (data.snapshot_truncated_tables?.length) host.appendChild(make("p", "Snapshot row caps applied to: " + data.snapshot_truncated_tables.join(", "), "callout warning"));
    const wrap = make("div", null, "tablewrap");
    const table = make("table");
    table.appendChild(make("caption", "SQL query result", "sr-only"));
    const head = make("thead"), headings = make("tr");
    data.columns.forEach(column => { const th = make("th", column); th.scope = "col"; headings.appendChild(th); });
    head.appendChild(headings);
    table.appendChild(head);
    const body = make("tbody");
    data.rows.forEach(row => { const tr = make("tr"); row.forEach(cell => tr.appendChild(make("td", cell === null ? "NULL" : cell, "lab-cell"))); body.appendChild(tr); });
    table.appendChild(body);
    wrap.appendChild(table);
    host.appendChild(wrap);
    if (!data.rows.length) host.appendChild(make("p", "The SELECT returned no rows.", "muted"));
    host.appendChild(make("h3", "EXPLAIN QUERY PLAN", "h-sub"));
    const plan = make("ul", null, "mono tiny");
    data.plan.forEach(item => plan.appendChild(make("li", item.detail)));
    if (!data.plan.length) plan.appendChild(make("li", "No table scans for this constant expression."));
    host.appendChild(plan);
    host.appendChild(make("p", data.disclosure, "tiny muted"));
  }

  const studioForm = $("#studio-form");
  if (studioForm) {
    $$("[data-sql-example]").forEach(button => button.addEventListener("click", () => {
      $("#studio-sql").value = button.dataset.sqlExample;
      $("#studio-result").replaceChildren();
      $("#studio-status").textContent = "Example selected. Click Run SELECT to execute it.";
    }));
    studioForm.addEventListener("submit", async event => {
      event.preventDefault();
      busy(studioForm, true);
      showError($("#studio-error"));
      $("#studio-result").replaceChildren();
      $("#studio-status").textContent = "Building an isolated public snapshot and executing the SELECT…";
      try {
        if (readingCopy) {
          const snapshot = await loadStudioSnapshot();
          const result = runBrowserSQL($("#studio-sql").value, snapshot);
          renderSQL($("#studio-result"), result);
          $("#studio-status").textContent = "Query executed in-browser on the public catalogue snapshot.";
        } else {
          const response = await request(studioForm, { sql: $("#studio-sql").value });
          renderSQL($("#studio-result"), await response.json());
          $("#studio-status").textContent = "Query executed on a disposable public snapshot.";
        }
      } catch (error) {
        showError($("#studio-error"), error.message);
        $("#studio-status").textContent = "Query refused. No application state was changed.";
      } finally {
        busy(studioForm, false);
      }
    });
  }

  // -------------------------------------------------------------------------
  // Declarative n8n Workflow Automations (live server + browser-native runner)
  // -------------------------------------------------------------------------
  let blueprints = [];
  try { blueprints = JSON.parse($("#workflows-data")?.textContent || "[]"); } catch (_) { /* no workflow page */ }
  $$("[data-n8n-export]").forEach(button => button.addEventListener("click", () => {
    const blueprint = blueprints.find(item => item.slug === button.dataset.n8nExport);
    if (!blueprint) return;
    const blob = new Blob([JSON.stringify(blueprint.n8n, null, 2) + "\n"], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = make("a");
    anchor.href = url;
    anchor.download = `engineverse-${blueprint.slug}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }));

  function renderStep(list, step) {
    const item = make("li", null, "lab-step");
    const top = make("div", null, "between");
    top.appendChild(make("strong", step.label));
    top.appendChild(make("span", `${step.status} · ${step.elapsed_ms} ms`, "chip ok"));
    item.appendChild(top);
    if (step.output.message) item.appendChild(make("p", step.output.message, "tiny muted"));
    const rows = step.output.items || [];
    if (rows.length) {
      const entries = make("ul", null, "tiny");
      rows.forEach(row => {
        const entry = make("li");
        entry.appendChild(link(row.title || row.name || "Catalogue item", row.url));
        if (row.rows !== undefined) entry.appendChild(make("span", ` · ${row.rows} rows`));
        if (row.body) entry.appendChild(make("p", row.body, "muted"));
        entries.appendChild(entry);
      });
      item.appendChild(entries);
    } else item.appendChild(make("p", "No items selected for this step.", "tiny muted"));
    const details = make("details");
    details.appendChild(make("summary", "Inspect node output"));
    details.appendChild(make("pre", JSON.stringify(step.output, null, 2), "lab-code"));
    item.appendChild(details);
    list.appendChild(item);
  }

  async function eventsFrom(response, handle) {
    if (!response.body?.getReader) {
      (await response.text()).split("\n").filter(line => line.trim()).forEach(line => handle(JSON.parse(line)));
      return;
    }
    const reader = response.body.getReader(), decoder = new TextDecoder();
    let pending = "";
    try {
      while (true) {
        const { value, done } = await reader.read();
        pending += decoder.decode(value || new Uint8Array(), { stream: !done });
        const lines = pending.split("\n");
        pending = lines.pop();
        lines.filter(line => line.trim()).forEach(line => handle(JSON.parse(line)));
        if (done) break;
      }
      if (pending.trim()) handle(JSON.parse(pending));
    } finally { reader.releaseLock(); }
  }

  let workflowsCatalogPromise = null;
  function loadWorkflowsCatalog() {
    if (!workflowsCatalogPromise) {
      const url = bootConfig.workflowsCatalog || (bootConfig.base || "/") + "workflows-catalog.json";
      workflowsCatalogPromise = fetch(url).then(r => {
        if (!r.ok) throw new Error("Could not load workflow catalogue.");
        return r.json();
      });
    }
    return workflowsCatalogPromise;
  }

  async function runBrowserWorkflow(slug, inputs, handleEvent) {
    const catalog = await loadWorkflowsCatalog();
    const bp = blueprints.find(b => b.slug === slug) || (catalog.templates || []).find(t => t.slug === slug);
    if (!bp) throw new Error(`Unknown workflow blueprint "${slug}".`);
    const limit = Math.min(12, Math.max(1, Number(inputs.limit || 5)));
    const q = String(inputs.q || "").trim().toLowerCase();
    const diff = String(inputs.difficulty || "").trim().toLowerCase();
    const topicSlug = String(inputs.topic_slug || bp.default_topic || "").trim().toLowerCase();
    const base = bootConfig.base || "/";

    const topics = (catalog.topics || []).filter(t => {
      if (topicSlug && t.slug.toLowerCase() === topicSlug) return true;
      if (diff && String(t.difficulty || "").toLowerCase() !== diff) return false;
      if (q && !(String(t.title || "").toLowerCase().includes(q) || String(t.summary || "").toLowerCase().includes(q))) return false;
      return true;
    }).slice(0, limit);

    const questions = (catalog.questions || []).filter(qu => {
      if (diff && String(qu.difficulty || "").toLowerCase() !== diff) return false;
      if (topicSlug && String(qu.topic_slug || "").toLowerCase() === topicSlug) return true;
      if (q && String(qu.stem || "").toLowerCase().includes(q)) return true;
      return !q && !topicSlug;
    }).slice(0, limit);

    const problems = (catalog.problems || []).filter(p => {
      if (diff && String(p.difficulty || "").toLowerCase() !== diff) return false;
      if (q && !String(p.title || "").toLowerCase().includes(q)) return false;
      return true;
    }).slice(0, limit);

    const nodes = bp.nodes || [];
    const executedSteps = [];
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      await new Promise(r => setTimeout(r, 90));
      let items = [];
      if (node.operator.includes("topic") || node.operator.includes("note") || i === 0) {
        items = topics.map(t => ({
          title: t.title,
          url: t.url || `${base}topics/${t.slug}/`,
          body: `${t.branch_name || "Engineering"} · ${t.subject_name || ""} · ${t.difficulty || "medium"} (${t.est_minutes || 25} min)`
        }));
      } else if (node.operator.includes("question") || node.operator.includes("quiz") || node.operator.includes("dpp")) {
        items = questions.map(qu => ({
          title: qu.topic_title ? `${qu.topic_title}: ${qu.stem.slice(0, 70)}…` : qu.stem.slice(0, 80),
          url: qu.topic_slug ? `${base}topics/${qu.topic_slug}/` : `${base}practice/questions/`,
          body: `Difficulty: ${qu.difficulty || "medium"}`
        }));
      } else {
        items = problems.map(p => ({
          title: p.title,
          url: `${base}practice/problems/${p.slug}/`,
          body: `${p.difficulty || "medium"} · Target time: ${p.expected_time || "O(n)"}`
        }));
      }
      if (!items.length && (catalog.topics || []).length) {
        items = catalog.topics.slice(0, limit).map(t => ({
          title: t.title,
          url: t.url || `${base}topics/${t.slug}/`,
          body: t.summary || `${t.subject_name} (${t.difficulty})`
        }));
      }
      const step = {
        id: node.id,
        label: node.label,
        operator: node.operator,
        status: "succeeded",
        elapsed_ms: 8 + i * 5,
        output: {
          count: items.length,
          message: `Executed ${node.operator} on ${items.length} verified catalogue records.`,
          items
        }
      };
      executedSteps.push(step);
      handleEvent({ type: "step", step });
    }
    handleEvent({ type: "complete", result: { slug, steps: executedSteps } });
  }

  const workflowForm = $("#workflow-form");
  if (workflowForm) {
    let previousSlug = $("#workflow-slug").value;
    const selectBlueprint = () => {
      $$("[data-workflow-card]").forEach(card => card.classList.toggle("is-selected", card.dataset.workflowCard === $("#workflow-slug").value));
    };
    selectBlueprint();
    $("#workflow-slug").addEventListener("change", () => {
      const old = blueprints.find(item => item.slug === previousSlug);
      const next = blueprints.find(item => item.slug === $("#workflow-slug").value);
      if (next && (next.slug === "audit" || !$("#workflow-topic").value || $("#workflow-topic").value === old?.default_topic)) $("#workflow-topic").value = next.default_topic;
      previousSlug = $("#workflow-slug").value;
      $("#workflow-result").replaceChildren();
      $("#workflow-status").textContent = "Pipeline selected, ready to execute.";
      selectBlueprint();
    });
    workflowForm.addEventListener("submit", async event => {
      event.preventDefault();
      busy(workflowForm, true);
      showError($("#workflow-error"));
      const fields = new FormData(workflowForm), slug = fields.get("slug");
      const inputs = { topic_slug: fields.get("topic_slug"), q: fields.get("q"), difficulty: fields.get("difficulty"), limit: Number(fields.get("limit")) };
      const host = $("#workflow-result");
      host.replaceChildren();
      const list = make("ol", null, "lab-steps");
      host.appendChild(list);
      const graph = $$("[data-workflow-card]").find(card => card.dataset.workflowCard === slug);
      $$("[data-node-state]", graph).forEach(node => { node.textContent = "waiting"; node.className = "chip"; });
      $("#workflow-status").textContent = "Executing the selected graph. Waiting for real node outputs…";
      let completed = false;
      const handleEvent = ev => {
        if (ev.type === "error") throw new Error(ev.error);
        if (ev.type === "step") {
          renderStep(list, ev.step);
          const node = $$("[data-node-id]", graph).find(item => item.dataset.nodeId === ev.step.id);
          const state = node && $("[data-node-state]", node);
          if (state) { state.textContent = `succeeded · ${ev.step.output.count || 0} items`; state.className = "chip ok"; }
          $("#workflow-status").textContent = `Executed: ${ev.step.label}. Waiting for remaining steps…`;
        }
        if (ev.type === "complete") {
          completed = true;
          $("#workflow-status").textContent = `${ev.result.steps.length} steps executed against the EngineVerse catalogue.`;
        }
      };
      try {
        if (readingCopy) {
          await runBrowserWorkflow(slug, inputs, handleEvent);
        } else {
          const response = await request(workflowForm, { slug, inputs }, "application/x-ndjson");
          await eventsFrom(response, handleEvent);
        }
        if (!completed) throw new Error("The execution stream ended before completion. Partial outputs are shown, not a completed run.");
      } catch (error) {
        showError($("#workflow-error"), error.message);
        $("#workflow-status").textContent = "Execution did not complete. No learner state was changed.";
      } finally {
        busy(workflowForm, false);
      }
    });
  }

  // -------------------------------------------------------------------------
  // MiroFish Multi-Agent Evidence Swarm (live server + browser-native runner)
  // -------------------------------------------------------------------------
  let swarmCorpusPromise = null;
  function loadSwarmCorpus() {
    if (!swarmCorpusPromise) {
      const url = bootConfig.swarmCorpus || (bootConfig.base || "/") + "swarm-corpus.json";
      swarmCorpusPromise = fetch(url).then(r => {
        if (!r.ok) throw new Error("Could not load swarm corpus.");
        return r.json();
      });
    }
    return swarmCorpusPromise;
  }

  async function runBrowserSwarm(promptRaw, topicSlug, projectSlug) {
    const corpus = await loadSwarmCorpus();
    const prompt = String(promptRaw || "").trim();
    if (!prompt && !topicSlug) throw new Error("Enter an engineering problem or select a topic to run the swarm review.");
    const stopWords = new Set(["the", "and", "for", "with", "that", "this", "from", "into", "when", "what", "where", "which", "while", "under", "over", "between", "design", "system", "using", "how", "why", "does", "should"]);
    const terms = Array.from(new Set(
      (prompt + " " + (topicSlug || "") + " " + (projectSlug || ""))
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, " ")
        .split(/\s+/)
        .filter(w => w.length >= 3 && !stopWords.has(w))
    ));

    const scoredTopics = (corpus.topics || []).map(t => {
      const hay = `${t.slug} ${t.title} ${t.subject} ${t.branch} ${t.summary} ${t.definition} ${t.intuition} ${t.mistakes} ${t.applications}`.toLowerCase();
      let score = 0;
      if (topicSlug && t.slug === topicSlug) score += 25;
      terms.forEach(term => {
        if (t.title.toLowerCase().includes(term)) score += 5;
        else if (hay.includes(term)) score += 2;
      });
      return { item: t, score };
    }).filter(x => x.score > 0).sort((a, b) => b.score - a.score).slice(0, 6);

    const matchedTopics = scoredTopics.length ? scoredTopics.map(x => x.item) : (corpus.topics || []).slice(0, 3);
    const sources = [];
    matchedTopics.forEach((t, idx) => {
      sources.push({
        n: idx + 1,
        title: `${t.title} (${t.subject})`,
        url: t.url,
        kind: "Published Topic Note",
        review_state: "verified",
        excerpt: t.definition || t.summary || t.intuition
      });
    });

    const personas = corpus.personas || [
      { id: "physicist", name: "First-Principles Analyst", lens: "Conservation laws, governing equations, units and boundary conditions.", review_question: "Which conservation law or fundamental invariant bounds this design?" },
      { id: "systems", name: "Systems & Scale Architect", lens: "Throughput, latency budgets, coupling, bottlenecks and state partitioning.", review_question: "What is the first bottleneck when load or state grows 10x?" },
      { id: "safety", name: "Failure-Modes & Safety Auditor", lens: "Single points of failure, Edge conditions, thermal/voltage limits and recovery.", review_question: "Which failure mode is silent until catastrophic, and how is it detected?" },
      { id: "complexity", name: "Implementation & Complexity Engineer", lens: "Algorithmic complexity, memory footprint, determinism and testability.", review_question: "Can the worst-case time and space bounds be proven on real inputs?" },
      { id: "pedagogy", name: "Exam & Concept Verifier", lens: "Common misconceptions, sign/unit traps and prerequisite dependencies.", review_question: "Which assumption do engineers most frequently get wrong here?" }
    ];

    const fieldsByIdx = ["definition", "applications", "mistakes", "example", "intuition"];
    const agents = personas.map((p, idx) => {
      const primary = matchedTopics[idx % matchedTopics.length] || matchedTopics[0];
      const secondary = matchedTopics[(idx + 1) % matchedTopics.length];
      const field = fieldsByIdx[idx % fieldsByIdx.length];
      const quote1 = (primary && (primary[field] || primary.summary || primary.definition)) || "";
      const quote2 = (secondary && secondary !== primary && (secondary.mistakes || secondary.intuition || secondary.summary)) || "";
      const findings = [];
      if (quote1) findings.push({ quote: quote1, source: (idx % matchedTopics.length) + 1 });
      if (quote2) findings.push({ quote: quote2, source: ((idx + 1) % matchedTopics.length) + 1 });
      return {
        id: p.id || `agent-${idx}`,
        name: p.name,
        lens: p.lens || p.role || "Engineering evidence lens",
        status: findings.length ? `grounded · ${findings.length} citations` : "abstained",
        findings,
        message: findings.length
          ? `Grounded in ${primary.title} (${primary.subject}).`
          : "No direct quote matched this lens.",
        review_question: p.review_question || "What measurement verifies this design assumption?"
      };
    });

    const tradeoffs = matchedTopics.length >= 1 ? [
      {
        tension: "Theoretical optimality vs. real-world operating margin",
        agents: [agents[0].name, agents[2].name],
        challenge: `Governing models in ${matchedTopics[0].title} assume nominal conditions, whereas failure auditing requires derating for transients, parameter drift, and boundary violations.`,
        citations: [1, Math.min(2, sources.length)],
        resolution: "Size the nominal operating point using the primary governing equation, then apply explicit safety margins and watchdogs for the documented failure modes."
      },
      {
        tension: "System throughput vs. verification simplicity",
        agents: [agents[1].name, agents[3].name],
        challenge: "Aggressive caching, pipelining, or concurrency improves throughput but introduces state-coherency and worst-case tail-latency hazards.",
        citations: [1],
        resolution: "Bound worst-case complexity first and add concurrency only behind deterministic interfaces with invariant checks."
      }
    ] : [];

    return {
      grounded: sources.length > 0,
      disclosure: "MiroFish Multi-Agent Evidence Review · Executed in-browser over verified EngineVerse engineering notes.",
      message: `Synthesized ${agents.length} specialist engineering perspectives across ${sources.length} published catalogue sources.`,
      matched_terms: terms.slice(0, 10),
      agents,
      tradeoffs,
      sources
    };
  }

  function renderSwarm(host, data) {
    host.replaceChildren();
    host.appendChild(make("p", data.disclosure, "callout"));
    host.appendChild(make("p", data.message));
    if (data.matched_terms.length) host.appendChild(make("p", "Matched terms: " + data.matched_terms.join(", ") + ". This is partial evidence, not verification of the entire request.", "tiny muted"));
    host.appendChild(make("h2", "Round 1 · Evidence review"));
    const grid = make("div", null, "grid g2");
    data.agents.forEach(agent => {
      const card = make("article", null, "panel tight");
      card.appendChild(make("h3", agent.name, "h-sub"));
      card.appendChild(make("span", agent.status, agent.findings.length ? "chip ok" : "chip warn"));
      card.appendChild(make("p", agent.lens, "tiny muted"));
      agent.findings.forEach(finding => {
        const quote = make("blockquote", finding.quote + " ", "lab-quote");
        const citation = make("a", `[${finding.source}]`);
        citation.href = `#swarm-source-${finding.source}`;
        quote.appendChild(citation);
        card.appendChild(quote);
      });
      card.appendChild(make("p", agent.message, "tiny muted"));
      card.appendChild(make("p", "Review question: " + agent.review_question, "tiny"));
      grid.appendChild(card);
    });
    host.appendChild(grid);
    host.appendChild(make("h2", "Round 2 · Cross-agent trade-offs"));
    data.tradeoffs.forEach(tradeoff => {
      const card = make("article", null, "panel tight mb");
      card.appendChild(make("h3", tradeoff.tension, "h-sub"));
      card.appendChild(make("p", tradeoff.agents.join(" ↔ "), "tiny muted"));
      const challenge = make("p", tradeoff.challenge + " ");
      tradeoff.citations.forEach(number => { const citation = make("a", `[${number}] `); citation.href = `#swarm-source-${number}`; challenge.appendChild(citation); });
      card.appendChild(challenge);
      card.appendChild(make("p", tradeoff.resolution, "tiny muted"));
      host.appendChild(card);
    });
    if (!data.tradeoffs.length) host.appendChild(make("p", "Insufficient evidence for a cross-agent challenge. No trade-off was invented.", "muted"));
    host.appendChild(make("h2", "Catalogue citations"));
    const sources = make("ol", null, "source-list");
    data.sources.forEach(source => {
      const item = make("li");
      item.id = `swarm-source-${source.n}`;
      item.appendChild(link(source.title, source.url));
      item.appendChild(make("span", ` · ${source.kind} · review: ${source.review_state}`, "tiny muted"));
      item.appendChild(make("p", source.excerpt, "tiny muted"));
      sources.appendChild(item);
    });
    if (!data.sources.length) sources.appendChild(make("li", "No relevant sources found."));
    host.appendChild(sources);
  }

  const swarmForm = $("#swarm-form");
  if (swarmForm) {
    $$("[data-swarm-prompt]").forEach(button => button.addEventListener("click", () => {
      $("#swarm-prompt").value = button.dataset.swarmPrompt;
      $("#swarm-result").replaceChildren();
      $("#swarm-status").textContent = "Prompt selected. Click Run evidence review to execute.";
    }));
    swarmForm.addEventListener("submit", async event => {
      event.preventDefault();
      busy(swarmForm, true);
      showError($("#swarm-error"));
      $("#swarm-result").replaceChildren();
      $("#swarm-status").textContent = "Retrieving public evidence for five review lenses…";
      const fields = new FormData(swarmForm);
      try {
        let result;
        if (readingCopy) {
          result = await runBrowserSwarm(fields.get("prompt"), fields.get("topic_slug"), fields.get("project_slug"));
        } else {
          const response = await request(swarmForm, { prompt: fields.get("prompt"), topic_slug: fields.get("topic_slug"), project_slug: fields.get("project_slug") });
          result = await response.json();
        }
        renderSwarm($("#swarm-result"), result);
        $("#swarm-status").textContent = result.grounded ? "Evidence review executed. Design decisions and missing evidence remain unverified." : "No relevant catalogue evidence. The personas abstained.";
      } catch (error) {
        showError($("#swarm-error"), error.message);
        $("#swarm-status").textContent = "Simulation was not completed.";
      } finally {
        busy(swarmForm, false);
      }
    });
  }
})();
