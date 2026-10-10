/* Visitor clock, browser streak, and the reading-copy tutor.
   The self-hosted app keeps its own accounts and tutor. This file only takes
   over the tutor when the static export injected #ev-live. */
(function () {
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var STOP = { the: 1, and: 1, for: 1, with: 1, from: 1, that: 1, this: 1, what: 1, when: 1, where: 1, how: 1, why: 1, does: 1, did: 1, are: 1, was: 1, were: 1, explain: 1, about: 1, into: 1, your: 1, you: 1, not: 1, can: 1, its: 1 };
  var STORE = "ev-reading-progress-v1";
  var cfg = {};
  var configNode = document.getElementById("ev-live");
  if (configNode) {
    try { cfg = JSON.parse(configNode.textContent || "{}"); } catch (error) { cfg = {}; }
  }
  var pool = Array.isArray(cfg.dpp) ? cfg.dpp.slice() : [];
  var readingCopy = Boolean(cfg.tutor || pool.length);

  function localISO(date) {
    var y = date.getFullYear();
    var m = String(date.getMonth() + 1).padStart(2, "0");
    var d = String(date.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + d;
  }

  function shift(days) {
    var date = new Date();
    date.setHours(12, 0, 0, 0);
    date.setDate(date.getDate() - days);
    return localISO(date);
  }

  function titleFor(iso) {
    var parts = String(iso || "").split("-");
    if (parts.length !== 3) return "";
    var month = MONTHS[Number(parts[1]) - 1];
    if (!month) return "";
    return "Daily Practice - " + Number(parts[2]) + " " + month + " " + parts[0];
  }

  function pretty(iso) {
    return titleFor(iso).replace("Daily Practice - ", "");
  }

  function ordinal(iso) {
    var parts = iso.split("-").map(Number);
    return Math.floor(Date.UTC(parts[0], parts[1] - 1, parts[2]) / 86400000);
  }

  function collectPool() {
    if (pool.length) return;
    document.querySelectorAll('a[href*="/dpp/"]').forEach(function (link) {
      var href = link.getAttribute("href") || "";
      var clean = href.split("?")[0];
      if (/\/dpp\/\d{4}-\d{2}-\d{2}\/?$/.test(clean) && pool.indexOf(clean) < 0) pool.push(clean);
    });
  }

  function setUrl(iso) {
    collectPool();
    if (pool.length) {
      var exact = "";
      pool.forEach(function (href) {
        if (!exact && href.indexOf("/dpp/" + iso) !== -1) exact = href.split("?")[0];
      });
      var base = exact || pool[Math.abs(ordinal(iso)) % pool.length].split("?")[0];
      return base + (base.indexOf("?") >= 0 ? "&" : "?") + "day=" + encodeURIComponent(iso);
    }
    return "/dpp/" + iso;
  }

  function askedDay() {
    var params = new URLSearchParams(location.search);
    var queryDay = params.get("day");
    if (queryDay && /^\d{4}-\d{2}-\d{2}$/.test(queryDay)) return queryDay;
    var pathDay = (location.pathname.match(/\/dpp\/(\d{4}-\d{2}-\d{2})\/?/) || [])[1];
    return pathDay || "";
  }

  function rewriteDates() {
    var today = shift(0);
    document.querySelectorAll("[data-practice-today]").forEach(function (node) {
      node.textContent = titleFor(today);
    });
    document.querySelectorAll("[data-practice-title]").forEach(function (node) {
      if (node.hasAttribute("data-practice-today")) return;
      var iso = askedDay() || today;
      var title = titleFor(iso);
      if (title) node.textContent = title;
    });
    document.querySelectorAll("[data-local-date]").forEach(function (node) {
      node.textContent = pretty(today);
    });
    var start = document.querySelector("[data-practice-start]");
    if (start) start.setAttribute("href", setUrl(today));
    var host = document.querySelector("[data-recent-sets]");
    if (!host) return;
    var asCards = host.classList.contains("grid");
    host.textContent = "";
    for (var i = 0; i < 14; i += 1) {
      var iso = shift(i);
      var link = document.createElement("a");
      link.href = setUrl(iso);
      if (asCards) {
        link.className = "card";
        var title = document.createElement("span");
        title.className = "title";
        title.textContent = pretty(iso);
        var desc = document.createElement("span");
        desc.className = "desc";
        desc.textContent = i === 0 ? "Today's calendar day" : "Opens a set for this day";
        link.appendChild(title);
        link.appendChild(desc);
      } else {
        link.className = "small";
        link.textContent = pretty(iso);
      }
      host.appendChild(link);
    }
  }

  function loadProgress() {
    try {
      var parsed = JSON.parse(localStorage.getItem(STORE) || "");
      if (!parsed || typeof parsed !== "object") throw new Error("empty");
      parsed.days = parsed.days || {};
      parsed.topics = parsed.topics || {};
      parsed.checks = parsed.checks || 0;
      parsed.pages = parsed.pages || 0;
      parsed.longest = parsed.longest || 0;
      return parsed;
    } catch (error) {
      return { days: {}, topics: {}, checks: 0, pages: 0, longest: 0 };
    }
  }

  function saveProgress(progress) {
    try { localStorage.setItem(STORE, JSON.stringify(progress)); } catch (error) { /* private mode */ }
  }

  function currentStreak(progress) {
    if (!progress.days[shift(0)] && !progress.days[shift(1)]) return 0;
    var start = progress.days[shift(0)] ? 0 : 1;
    var count = 0;
    for (var i = start; i < 400; i += 1) {
      if (!progress.days[shift(i)]) break;
      count += 1;
    }
    return count;
  }

  function studyDays(progress) {
    return Object.keys(progress.days).length;
  }

  function paintProgress(progress) {
    var streak = currentStreak(progress);
    var longest = Math.max(progress.longest || 0, streak);
    var topics = Object.keys(progress.topics).length;
    var days = studyDays(progress);
    document.querySelectorAll("[data-streak]").forEach(function (node) {
      var key = node.getAttribute("data-streak");
      var value = 0;
      if (key === "current") value = streak;
      else if (key === "longest") value = longest;
      else if (key === "days") value = days;
      else if (key === "topics") value = topics;
      else if (key === "checks") value = progress.checks || 0;
      node.textContent = String(value);
    });
    var note = document.querySelector("[data-streak-note]");
    if (note) {
      note.textContent = days
        ? "Counted on this device. A day counts when you open a topic, a practice set, a language module, or a project."
        : "No study day on this device yet. Open today's set or any topic and this counter moves off zero.";
    }
    var heat = document.querySelector("[data-streak-heat]");
    if (heat) {
      heat.textContent = "";
      for (var i = 27; i >= 0; i -= 1) {
        var cell = document.createElement("span");
        cell.className = "hm" + (progress.days[shift(i)] ? " l3" : "");
        cell.title = pretty(shift(i));
        heat.appendChild(cell);
      }
    }
    if (document.querySelector(".topbar-right .streak")) return;
    var slot = document.querySelector(".topbar-right");
    if (!slot) return;
    var chip = document.getElementById("ev-streak-chip");
    if (!chip) {
      chip = document.createElement("a");
      chip.id = "ev-streak-chip";
      chip.className = "streak";
      chip.href = cfg.streaks || "/streaks";
      chip.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M12 2s5 5 5 9a5 5 0 0 1-10 0c0-1.5.7-2.9 1.5-4 .2 1.6 1 2.5 2 2.5 1.4 0 2-1.3 1.5-3-.3-1.6-.5-3.2 0-4.5z"/></svg><span></span>';
      slot.insertBefore(chip, slot.firstChild);
    }
    var label = chip.querySelector("span");
    if (label) label.textContent = streak ? String(streak) : "Start";
    chip.title = streak ? streak + " day streak on this browser" : "Open a topic or today's set to start a streak";
  }

  function pageKind() {
    var path = location.pathname;
    if (/\/topics\/[^/]+/.test(path)) return "topic";
    if (/\/dpp(\/|$)/.test(path) || /\/practice(\/|$)/.test(path)) return "practice";
    if (/\/programming\//.test(path)) return "code";
    if (/\/projects\//.test(path)) return "project";
    if (/\/subjects\//.test(path) || /\/branches\//.test(path)) return "read";
    return "";
  }

  function mark(kind, id) {
    var progress = loadProgress();
    var today = shift(0);
    var before = progress.days[today] || 0;
    progress.days[today] = before + 1;
    if (kind === "topic" && id) progress.topics[id] = today;
    if (kind === "check") progress.checks += 1;
    if (!before) progress.pages += 1;
    var streak = currentStreak(progress);
    if (streak > (progress.longest || 0)) progress.longest = streak;
    saveProgress(progress);
    paintProgress(progress);
  }

  function tokens(value) {
    return String(value || "").toLowerCase().replace(/[^a-z0-9+#]+/g, " ").split(/\s+/).filter(function (word) {
      return word.length > 2 && !STOP[word];
    });
  }

  function hasWord(hay, term) {
    var padded = " " + hay + " ";
    if (padded.indexOf(" " + term + " ") !== -1) return true;
    if (term.length > 3 && padded.indexOf(" " + term + "s ") !== -1) return true;
    if (term.length > 4 && term.charAt(term.length - 1) === "s" && padded.indexOf(" " + term.slice(0, -1) + " ") !== -1) return true;
    return false;
  }

  function scoreEntry(entry, terms) {
    var title = (entry.title + " " + (entry.subject || "")).toLowerCase();
    var body = (entry.text || "").toLowerCase();
    var score = 0;
    terms.forEach(function (term) {
      if (hasWord(title, term)) score += 4;
      else if (hasWord(body, term)) score += 1;
    });
    return score;
  }

  function addParagraph(parent, label, text) {
    if (!text) return;
    var paragraph = document.createElement("p");
    if (label) {
      var strong = document.createElement("strong");
      strong.textContent = label + " ";
      paragraph.appendChild(strong);
    }
    paragraph.appendChild(document.createTextNode(text));
    parent.appendChild(paragraph);
  }

  function showTutor(entry, also, refused) {
    var result = document.getElementById("tutor-result");
    var answer = document.getElementById("tutor-answer");
    var sources = document.getElementById("tutor-sources");
    var list = document.getElementById("tutor-source-list");
    var empty = document.getElementById("tutor-empty");
    var message = document.getElementById("tutor-message");
    if (!result || !answer) return;
    answer.textContent = "";
    if (list) list.textContent = "";
    if (empty) empty.hidden = true;
    result.hidden = false;
    if (message) {
      message.hidden = false;
      message.textContent = refused
        ? "The library on this copy has no note that matches. Nothing was invented to fill the gap."
        : "Assembled from notes on this copy. It is not a general chatbot, and it does not know anything outside those notes.";
    }
    if (refused) {
      if (sources) sources.hidden = true;
      return;
    }
    var heading = document.createElement("h2");
    heading.textContent = entry.title;
    answer.appendChild(heading);
    addParagraph(answer, "", entry.simple);
    addParagraph(answer, "Definition.", entry.definition);
    addParagraph(answer, "Why it works.", entry.intuition);
    addParagraph(answer, "Worked example.", entry.example);
    addParagraph(answer, "Common mistakes.", entry.mistakes);
    if (sources && list) {
      sources.hidden = false;
      also.forEach(function (item) {
        var line = document.createElement("li");
        var link = document.createElement("a");
        link.href = item.url;
        link.textContent = item.title + (item.subject ? " — " + item.subject : "");
        line.appendChild(link);
        list.appendChild(line);
      });
    }
  }

  var corpus = null;
  function loadCorpus() {
    if (corpus) return Promise.resolve(corpus);
    if (!cfg.tutor) return Promise.resolve([]);
    return fetch(cfg.tutor).then(function (response) {
      if (!response.ok) throw new Error("corpus");
      return response.json();
    }).then(function (rows) {
      corpus = rows.map(function (row) {
        row.text = [row.title, row.subject, row.simple, row.definition, row.intuition, row.example, row.mistakes, row.points].join(" ");
        return row;
      });
      return corpus;
    });
  }

  function answerQuestion(question) {
    var terms = tokens(question);
    var message = document.getElementById("tutor-message");
    if (!terms.length) {
      showTutor(null, [], true);
      if (message) message.textContent = "Ask about a topic, formula, or idea that might be in the notes.";
      return;
    }
    if (message) {
      message.hidden = false;
      message.textContent = "Looking through the notes on this copy…";
    }
    loadCorpus().then(function (rows) {
      var ranked = rows.map(function (row) {
        return { row: row, score: scoreEntry(row, terms) };
      }).filter(function (item) { return item.score > 0; });
      ranked.sort(function (a, b) { return b.score - a.score; });
      if (!ranked.length) {
        showTutor(null, [], true);
        return;
      }
      var best = ranked[0];
      var enough = best.score >= 2 || (best.score >= 1 && terms.length === 1);
      if (!enough) {
        showTutor(null, [], true);
        return;
      }
      showTutor(ranked[0].row, ranked.slice(0, 3).map(function (item) { return item.row; }), false);
    }).catch(function () {
      showTutor(null, [], true);
      if (message) message.textContent = "The note index did not load, so no answer was invented.";
    });
  }

  function bindTutor() {
    if (!readingCopy) return;
    var form = document.getElementById("tutor-form");
    if (!form || form.dataset.liveTutor) return;
    form.dataset.liveTutor = "1";
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      event.stopPropagation();
      var input = document.getElementById("tutor-question");
      answerQuestion(input ? input.value : "");
      mark("tutor", "");
    }, true);
    var limit = document.getElementById("tutor-limit");
    if (limit) {
      limit.textContent = "On this reading copy the tutor runs in your browser and answers only from these notes. It does not call a server.";
    }
  }

  rewriteDates();
  var kind = pageKind();
  if (kind) {
    var slug = (location.pathname.match(/\/topics\/([^/]+)/) || [])[1] || "";
    mark(kind, decodeURIComponent(slug));
  } else {
    paintProgress(loadProgress());
  }
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (form && form.closest && form.closest("[data-quiz]")) mark("check", "");
  }, true);
  bindTutor();
})();
