/* Public directory, data studio, declarative workflows and evidence swarm.
 * No libraries or third-party requests. Live operators are same-origin only;
 * the Pages reading copy never pretends to execute a backend operation. */
(() => {
  "use strict";
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const readingCopy = Boolean($("#ev-live"));
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
    node.href = typeof href === "string" && href.startsWith("/") && !href.startsWith("//") ? href : "#";
    return node;
  };
  const showError = (node, message = "") => {
    if (!node) return;
    node.textContent = message;
    node.hidden = !message;
  };
  async function request(form, body, accept = "application/json") {
    if (readingCopy) throw new Error("Execution requires a self-hosted EngineVerse backend.");
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
    if (button) button.disabled = value || readingCopy;
    form.setAttribute("aria-busy", String(value));
  }
  if (readingCopy) {
    $$("[data-live-control]").forEach(node => { node.disabled = true; });
    $$("[data-lab-mode-notice]").forEach(node => { node.hidden = false; });
  }

  // Copy remains useful on both a live install and the static reading copy.
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
      $("#apis-count").textContent = `${count} of ${cards.length} APIs match · filtered in this reading copy.`;
      $("#apis-empty").hidden = count > 0;
    };
    const initial = new URLSearchParams(location.search);
    ["q", "category", "auth", "cors", "slug"].forEach(key => {
      const field = apiForm.elements.namedItem(key);
      if (!field || !initial.has(key)) return;
      const value = initial.get(key).slice(0, key === "q" ? 160 : 128);
      // Keep unknown select values as real filters, rather than widening them.
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
      $("#studio-status").textContent = readingCopy ? "Example selected for copying. Executing it requires a self-hosted backend." : "Example selected, not executed. Run SELECT to inspect its result.";
    }));
    studioForm.addEventListener("submit", async event => {
      event.preventDefault();
      if (readingCopy) return;
      busy(studioForm, true);
      showError($("#studio-error"));
      $("#studio-result").replaceChildren();
      $("#studio-status").textContent = "Building an isolated public snapshot and executing the SELECT…";
      try {
        const response = await request(studioForm, { sql: $("#studio-sql").value });
        renderSQL($("#studio-result"), await response.json());
        $("#studio-status").textContent = "Query executed on a disposable public snapshot.";
      } catch (error) { showError($("#studio-error"), error.message); $("#studio-status").textContent = "Query refused. No application state was changed."; }
      finally { busy(studioForm, false); }
    });
  }

  // A standard n8n document is embedded so downloads also work on Pages.
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
      $("#workflow-status").textContent = "Pipeline selected, not executed.";
      selectBlueprint();
    });
    workflowForm.addEventListener("submit", async event => {
      event.preventDefault();
      if (readingCopy) return;
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
      try {
        const response = await request(workflowForm, { slug, inputs }, "application/x-ndjson");
        await eventsFrom(response, event => {
          if (event.type === "error") throw new Error(event.error);
          if (event.type === "step") {
            renderStep(list, event.step);
            const node = $$("[data-node-id]", graph).find(item => item.dataset.nodeId === event.step.id);
            const state = node && $("[data-node-state]", node);
            if (state) { state.textContent = `succeeded · ${event.step.output.count || 0} items`; state.className = "chip ok"; }
            $("#workflow-status").textContent = `Executed: ${event.step.label}. Waiting for remaining steps…`;
          }
          if (event.type === "complete") {
            completed = true;
            $("#workflow-status").textContent = `${event.result.steps.length} steps executed. No code was judged and no learner state was changed.`;
          }
        });
        if (!completed) throw new Error("The execution stream ended before completion. Partial outputs are shown, not a completed run.");
      } catch (error) { showError($("#workflow-error"), error.message); $("#workflow-status").textContent = "Execution did not complete. No learner state was changed."; }
      finally { busy(workflowForm, false); }
    });
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
      $("#swarm-status").textContent = readingCopy ? "Prompt selected for a self-hosted simulation. No new review was executed here." : "Prompt selected, not executed.";
    }));
    swarmForm.addEventListener("submit", async event => {
      event.preventDefault();
      if (readingCopy) return;
      busy(swarmForm, true);
      showError($("#swarm-error"));
      $("#swarm-result").replaceChildren();
      $("#swarm-status").textContent = "Retrieving public evidence for five review lenses…";
      const fields = new FormData(swarmForm);
      try {
        const response = await request(swarmForm, { prompt: fields.get("prompt"), topic_slug: fields.get("topic_slug"), project_slug: fields.get("project_slug") });
        const result = await response.json();
        renderSwarm($("#swarm-result"), result);
        $("#swarm-status").textContent = result.grounded ? "Evidence review executed. Design decisions and missing evidence remain unverified." : "No relevant catalogue evidence. The personas abstained.";
      } catch (error) { showError($("#swarm-error"), error.message); $("#swarm-status").textContent = "Simulation was not completed."; }
      finally { busy(swarmForm, false); }
    });
  }
})();
