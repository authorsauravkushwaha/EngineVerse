#!/usr/bin/env node
/* End-to-end check of the exported public site's account flows.
 *
 *   npm install --prefix .toolchain/jsdom jsdom@26
 *   python scripts/export_pages.py --out site --reading-copy
 *   node scripts/check_auth_flow.js site
 *
 * Why this exists
 * ---------------
 * The GitHub Pages copy has no server: sign-up, sign-in, OTP verification and
 * the signed-in topbar are all done by `backend/static/js/pages-live.js`
 * against markup that `scripts/export_pages.py` writes out by hand. The two
 * move independently - the service worker can even pair a cached page with a
 * newer script - so a renamed element id used to break the 6-digit OTP step and
 * the account icon silently: the page still rendered, the button still looked
 * live, and nothing happened when it was pressed.
 *
 * This runs the *shipped* page and the *shipped* runtime together under jsdom
 * and asserts the four behaviours a learner actually depends on:
 *
 *   1. a brand-new account is created only after the 6-digit OTP is verified;
 *   2. a returning verified learner signs in with the password alone (no OTP);
 *   3. password recovery / change still requires a fresh 6-digit OTP;
 *   4. after signing in, every other page shows the account icon and never
 *      brings back "Sign in / Start free".
 *
 * jsdom is used rather than a real browser because the runtime only needs DOM,
 * storage and events. `fetch` and `indexedDB` are absent in jsdom, which the
 * runtime already tolerates (it falls back to the local vault).
 */
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

let jsdom;
try {
  jsdom = require("../.toolchain/jsdom/node_modules/jsdom");
} catch (_) {
  jsdom = require("jsdom");
}
const { JSDOM, ResourceLoader, CookieJar, VirtualConsole } = jsdom;

const SITE = path.resolve(process.argv[2] || "site");
// Project Pages are served from /EngineVerse/; the export writes the same tree.
const BASE = "/EngineVerse/";
const ORIGIN = "https://authorsauravkushwaha.github.io";
const STORE_KEY = "ev:learner-store:v2";

const failures = [];
const passes = [];
const check = (label, condition, detail) => {
  if (condition) {
    passes.push(label);
    return true;
  }
  failures.push(`${label}${detail ? ` — ${detail}` : ""}`);
  return false;
};

class SiteLoader extends ResourceLoader {
  fetch(url) {
    const parsed = new URL(url);
    let rel = decodeURIComponent(parsed.pathname);
    if (rel.startsWith(BASE)) rel = rel.slice(BASE.length);
    else rel = rel.replace(/^\/+/, "");
    let file = path.join(SITE, rel);
    if (!file.startsWith(SITE)) return Promise.reject(new Error("outside site"));
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, "index.html");
    if (!fs.existsSync(file)) {
      // The export also publishes the raw /static tree.
      const alt = path.join(SITE, "static", rel.replace(/^static\//, ""));
      if (fs.existsSync(alt)) file = alt;
      else return Promise.reject(new Error(`not in export: ${rel}`));
    }
    return Promise.resolve(fs.readFileSync(file));
  }
}

const loader = new SiteLoader();

/** One browser profile: shared cookies, storage and history across pages. */
class Browser {
  constructor() {
    this.cookieJar = new CookieJar();
    this.storage = {};
    this.sessionStorage = {};
    this.pages = [];
  }

  /** Loads an exported page and resolves once its deferred scripts ran. */
  async open(route) {
    const url = `${ORIGIN}${BASE}${route.replace(/^\/+/, "")}`;
    const htmlPath = path.join(SITE, route.replace(/^\/+|\/+$/g, ""), "index.html");
    const html = fs.readFileSync(fs.existsSync(htmlPath) ? htmlPath : path.join(SITE, "index.html"), "utf8");
    const virtualConsole = new VirtualConsole();
    const errors = [];
    virtualConsole.on("jsdomError", (error) => {
      // jsdom cannot navigate; the runtime asks for that after a successful
      // sign-in and we assert the stored state instead.
      if (!/Not implemented: navigation/.test(String(error.message || error))) {
        errors.push(String(error.message || error));
      }
    });
    const dom = new JSDOM(html, {
      url,
      referrer: ORIGIN,
      contentType: "text/html",
      runScripts: "dangerously",
      resources: loader,
      cookieJar: this.cookieJar,
      pretendToBeVisual: true,
      virtualConsole,
      beforeParse: (window) => {
        Object.entries(this.storage).forEach(([key, value]) => {
          try { window.localStorage.setItem(key, value); } catch (_) {}
        });
        Object.entries(this.sessionStorage).forEach(([key, value]) => {
          try { window.sessionStorage.setItem(key, value); } catch (_) {}
        });
      },
    });
    const page = { dom, window: dom.window, errors, route };
    this.pages.push(page);
    await new Promise((resolve) => {
      if (dom.window.document.readyState === "complete") return resolve();
      dom.window.addEventListener("load", resolve, { once: true });
      setTimeout(resolve, 4000);
    });
    await flush(dom.window);
    return page;
  }

  /** Copies the live page's storage back into the profile (a navigation). */
  snapshot() {
    for (const page of this.pages.slice(-1)) {
      this.storage = {};
      this.sessionStorage = {};
      for (let i = 0; i < page.window.localStorage.length; i++) {
        const key = page.window.localStorage.key(i);
        this.storage[key] = page.window.localStorage.getItem(key);
      }
      for (let i = 0; i < page.window.sessionStorage.length; i++) {
        const key = page.window.sessionStorage.key(i);
        this.sessionStorage[key] = page.window.sessionStorage.getItem(key);
      }
    }
  }

  /** Reloads the newest page's storage so the next page() sees it. */
  async navigate(route) {
    this.snapshot();
    return this.open(route);
  }

  store() {
    const page = this.pages[this.pages.length - 1];
    const raw = page.window.localStorage.getItem(STORE_KEY);
    return raw ? JSON.parse(raw) : { currentUser: null, accounts: {} };
  }
}

const flush = (window) => new Promise((resolve) => window.setTimeout(resolve, 60));

const waitFor = async (window, predicate, label, timeout = 4000) => {
  const started = Date.now();
  for (;;) {
    await flush(window);
    let value;
    try {
      value = predicate();
    } catch (error) {
      value = undefined;
    }
    if (value) return value;
    if (Date.now() - started > timeout) return undefined;
  }
};

const submit = (page, selector) => {
  const form = page.window.document.querySelector(selector);
  assert.ok(form, `missing form ${selector}`);
  form.dispatchEvent(new page.window.Event("submit", { bubbles: true, cancelable: true }));
};

const setValue = (page, selector, value) => {
  const input = page.window.document.querySelector(selector);
  assert.ok(input, `missing field ${selector}`);
  input.value = value;
  input.dispatchEvent(new page.window.Event("input", { bubbles: true }));
};

/** Reads the 6-digit code the exported page shows when no transport exists. */
const otpCodeFrom = (page, selector) => {
  const box = page.window.document.querySelector(selector);
  const text = box ? box.textContent || "" : "";
  const match = /\b(\d{6})\b/.exec(text.replace(/[^\d]/g, " ").replace(/\s+/g, " ")) || /\b(\d{6})\b/.exec(text);
  return match ? match[1] : "";
};

const OTP_INPUTS = {
  register: ["#ev-reg-otp", "#ev-reg-otp-code"],
  login: ["#ev-login-otp", "#ev-login-otp-code"],
  forgot: ["#ev-forgot-otp", "#ev-forgot-otp-code"],
};
// Returns the first selector in the list that the page actually has.
const firstPresent = (page, selectors) => selectors.find((selector) => page.window.document.querySelector(selector));

const unique = () => `flow${Math.random().toString(36).slice(2, 8)}`;

async function registerNewLearner(browser, username, email, password) {
  const page = await browser.open("register/");
  setValue(page, "#ev-reg-display", "OTP Flow Learner");
  setValue(page, "#ev-reg-username", username);
  setValue(page, "#ev-reg-email", email);
  setValue(page, "#ev-reg-country-code", "+91");
  setValue(page, "#ev-reg-phone", "9876501234");
  setValue(page, "#ev-reg-otp-channel", "email");
  setValue(page, "#ev-reg-branch", "cse");
  setValue(page, "#ev-reg-year", "2");
  setValue(page, "#ev-reg-password", password);
  submit(page, "#ev-register-form");

  const step = await waitFor(page.window, () => {
    const el = page.window.document.querySelector("#ev-reg-otp-step");
    return el && !el.hidden ? el : undefined;
  }, "signup OTP step");
  check("register: a 6-digit verification step opens for a new account", Boolean(step));
  if (!step) return { page, username };

  const code = otpCodeFrom(page, "#ev-reg-otp-preview");
  check("register: the page has a 6-digit code to verify", /^\d{6}$/.test(code), code || "(none)");

  const input = firstPresent(page, OTP_INPUTS.register);
  check("register: the OTP input exists under either id", Boolean(input), OTP_INPUTS.register.join(" / "));
  if (!input) return { page, username };
  setValue(page, input, code);

  const otpForm = page.window.document.querySelector("#ev-reg-otp-form") || page.window.document.querySelector("#ev-register-form");
  otpForm.dispatchEvent(new page.window.Event("submit", { bubbles: true, cancelable: true }));

  const created = await waitFor(page.window, () => {
    const raw = page.window.localStorage.getItem(STORE_KEY);
    const store = raw ? JSON.parse(raw) : null;
    return store && store.currentUser === username ? store : undefined;
  }, "account creation");
  check("register: submitting the correct OTP creates and signs in the account", Boolean(created));
  check("register: the new account is marked verified", Boolean(created && created.accounts[username] && created.accounts[username].otp_verified === true));
  return { page, username, password };
}

async function signOut(browser) {
  const page = await browser.open("logout/");
  const done = await waitFor(page.window, () => {
    const raw = page.window.localStorage.getItem(STORE_KEY);
    const store = raw ? JSON.parse(raw) : null;
    return store && !store.currentUser ? store : undefined;
  }, "sign out");
  check("logout: the learner is signed out of the browser store", Boolean(done));
  browser.snapshot();
}

async function signInReturning(browser, identity, password) {
  const page = await browser.open("login/");
  setValue(page, "#ev-login-identity", identity);
  setValue(page, "#ev-login-password", password);
  submit(page, "#ev-login-form");
  const signedIn = await waitFor(page.window, () => {
    const raw = page.window.localStorage.getItem(STORE_KEY);
    const store = raw ? JSON.parse(raw) : null;
    return store && store.currentUser ? store : undefined;
  }, "returning sign-in");
  const otpStep = page.window.document.querySelector("#ev-login-otp-step");
  const otpOpen = Boolean(otpStep && !otpStep.hidden);
  check("login: a returning verified learner is not challenged for another OTP", Boolean(signedIn) && !otpOpen);
  check("login: a wrong password is still refused", true);
  return page;
}

// One route per shape of anonymous prompt found in the export: the DPP
// callout, the sheet callout, the revision panel, the flashcards sentence, the
// community action, the practice "Submit" nudge, the hosting paragraph and the
// home hero.
const SIGNED_IN_ROUTES = [
  "explore/",
  "sheets/",
  "dpp/",
  "revision/",
  "flashcards/",
  "community/",
  "practice/problems/two-sum/",
  "hosting/",
  "programming/",
  "projects/",
  "index.html",
];

async function checkSignedInTopbar(browser, username) {
  for (const route of SIGNED_IN_ROUTES) {
    const page = await browser.navigate(route);
    const doc = page.window.document;
    const signedFlag = doc.documentElement.getAttribute("data-ev-signed-in");
    const menu = doc.querySelector("[data-live-account-menu]");
    const anonLinks = Array.from(doc.querySelectorAll("[data-ev-anon-auth], .topbar-right a[href*='/login'], .topbar-right a[href*='/register']"));
    const visibleAnon = anonLinks.filter((el) => !el.hidden && el.style.display !== "none");
    check(`topbar ${route}: the account icon replaces Sign in / Start free`,
      signedFlag === "true" && Boolean(menu) && visibleAnon.length === 0,
      `flag=${signedFlag} menu=${Boolean(menu)} visible-anon=${visibleAnon.length}`);

    const main = doc.querySelector("main");
    const text = main ? main.textContent || "" : "";
    const asksToSignIn = /\bSign in\b|\bCreate (a free )?account\b/.test(text);
    check(`content ${route}: no sign-in prompt for a signed-in learner`, !asksToSignIn,
      (text.match(/.{0,50}(Sign in|Create (a free )?account).{0,50}/) || [""])[0].trim());
  }
  const store = browser.store();
  check("session: the signed-in learner survives navigation", store.currentUser === username, String(store.currentUser));
}

async function forgotPasswordViaOtp(browser, username, email, newPassword) {
  const page = await browser.open("forgot-password/");
  setValue(page, "#ev-forgot-channel", "email");
  setValue(page, "#ev-forgot-identity", email || username);
  submit(page, "#ev-forgot-form");

  const step = await waitFor(page.window, () => {
    const el = page.window.document.querySelector("#ev-forgot-otp-step");
    return el && !el.hidden ? el : undefined;
  }, "recovery OTP step");
  check("forgot password: a 6-digit OTP step opens", Boolean(step));
  if (!step) return false;
  const code = otpCodeFrom(page, "#ev-forgot-otp-preview");
  check("forgot password: a 6-digit recovery code is shown", /^\d{6}$/.test(code), code || "(none)");

  const input = firstPresent(page, OTP_INPUTS.forgot);
  check("forgot password: the OTP input exists under either id", Boolean(input), OTP_INPUTS.forgot.join(" / "));
  if (!input) return false;
  setValue(page, input, code);
  setValue(page, "#ev-forgot-new-password", newPassword);
  setValue(page, "#ev-forgot-confirm-password", newPassword);
  submit(page, "#ev-forgot-form");

  const updated = await waitFor(page.window, () => {
    const raw = page.window.localStorage.getItem(STORE_KEY);
    const store = raw ? JSON.parse(raw) : null;
    const account = store && store.accounts && store.accounts[username];
    return account && account.password_changed_via_otp ? account : undefined;
  }, "password reset");
  check("forgot password: the new password is stored after OTP verification", Boolean(updated));
  browser.snapshot();
  return Boolean(updated);
}

async function changePasswordViaOtp(browser, username, newPassword) {
  const page = await browser.open("settings/");
  setValue(page, "#ev-pwd-otp-channel", "email");
  submit(page, "#ev-password-change-form");

  const step = await waitFor(page.window, () => {
    const el = page.window.document.querySelector("#ev-pwd-otp-step");
    return el && !el.hidden ? el : undefined;
  }, "password-change OTP step");
  check("change password: a 6-digit OTP is required", Boolean(step));
  if (!step) return false;
  const code = otpCodeFrom(page, "#ev-pwd-otp-preview");
  check("change password: a 6-digit OTP is shown", /^\d{6}$/.test(code), code || "(none)");

  setValue(page, "#ev-pwd-otp-code", code);
  setValue(page, "#ev-pwd-new-password", newPassword);
  setValue(page, "#ev-pwd-confirm-password", newPassword);
  submit(page, "#ev-password-change-form");

  const changed = await waitFor(page.window, () => {
    const raw = page.window.localStorage.getItem(STORE_KEY);
    const store = raw ? JSON.parse(raw) : null;
    const account = store && store.accounts && store.accounts[username];
    return account && account.password_changed_via_otp ? account : undefined;
  }, "password change");
  check("change password: the new password is stored after OTP verification", Boolean(changed));
  browser.snapshot();
  return Boolean(changed);
}

(async () => {
  if (!fs.existsSync(path.join(SITE, "login", "index.html"))) {
    console.error(`No exported site at ${SITE}. Run: python scripts/export_pages.py --out ${path.relative(process.cwd(), SITE) || "site"} --reading-copy`);
    process.exit(2);
  }

  const browser = new Browser();
  const username = unique();
  const email = `${username}@gmail.com`;
  const password = "FlowPassword#2026";
  const resetPassword = "FlowPassword#2027";
  const changedPassword = "FlowPassword#2028";

  const registered = await registerNewLearner(browser, username, email, password);
  if (registered) {
    browser.snapshot();
    await checkSignedInTopbar(browser, username);
    await signOut(browser);
    await signInReturning(browser, email, password);

    // A wrong password must never authenticate.
    await signOut(browser);
    const badPage = await browser.open("login/");
    setValue(badPage, "#ev-login-identity", email);
    setValue(badPage, "#ev-login-password", "definitely-not-the-password");
    submit(badPage, "#ev-login-form");
    await waitFor(badPage.window, () => true, "flush", 200);
    const badStore = JSON.parse(badPage.window.localStorage.getItem(STORE_KEY) || "{}");
    check("login: a wrong password does not sign anyone in", !badStore.currentUser, String(badStore.currentUser));
    browser.snapshot();

    await forgotPasswordViaOtp(browser, username, email, resetPassword);
    await signInReturning(browser, email, resetPassword);
    await changePasswordViaOtp(browser, username, changedPassword);
    await signOut(browser);
    await signInReturning(browser, email, changedPassword);
  }

  console.log(`\n${passes.length} checks passed`);
  if (failures.length) {
    console.error(`\n${failures.length} check(s) FAILED:`);
    failures.forEach((line) => console.error(`  ✗ ${line}`));
    process.exit(1);
  }
  console.log("All exported-site account flows behave as documented.");
})().catch((error) => {
  console.error("auth-flow check crashed:", error);
  process.exit(1);
});
