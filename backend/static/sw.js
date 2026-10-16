/* EngineVerse service worker.
 * Cache-first for the app shell, network-first with cache fallback for pages,
 * never caches authenticated or mutating requests.
 */
// Bumped whenever a cached asset changes behaviour. v6: sign-in became
// compulsory and the practice cards changed, so a v5 app.js must not linger.
// v8: pages-live.js learned to resolve the ids the exported account pages
// actually use (the signup/sign-in/recovery OTP steps, the account icon) and
// stopped throwing on the first page it hydrated. A visitor holding the v7
// runtime would keep seeing the sign-in buttons come back on every tab, so the
// cache name has to change or the fix never reaches them.
const VERSION = "engineverse-v8";
const SHELL = [
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/js/pages-live.js",
  "/static/js/capabilities.js",
  "/static/js/engine3d.js",
  "/static/icons/favicon.svg",
  "/static/offline.html",
  "/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function cacheable(request) {
  if (request.method !== "GET") return false;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return false;
  if (url.pathname.startsWith("/api/")) return false;
  if (url.pathname.startsWith("/settings")) return false;
  if (url.pathname.startsWith("/admin")) return false;
  return true;
}

// The path checks above are not sufficient on their own. The server marks
// authenticated HTML private/no-store. Anonymous HTML is private to HTTP
// caches too (it carries a browser-bound CSRF token), but may be stored in this
// browser's own offline cache when explicitly marked X-Offline-Cache: anonymous.
function storable(response) {
  if (!response || !response.ok) return false;
  const cc = (response.headers.get("Cache-Control") || "").toLowerCase();
  if (cc.includes("no-store")) return false;
  if (cc.includes("private") && response.headers.get("X-Offline-Cache") !== "anonymous") return false;
  return true;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!cacheable(request)) return;

  const isCode = request.destination === "style" || request.destination === "script" ||
                 /\/static\/(js|css)\//.test(new URL(request.url).pathname);
  const isStatic = isCode || request.destination === "image" || request.url.includes("/static/");

  // Scripts and styles: network first, cached copy offline. They are small and
  // served by this same app, and cache-first meant a fixed app.js could sit
  // behind a stale copy until the cache name changed - which is how a broken
  // practice card could outlive its fix.
  if (isCode) {
    event.respondWith(
      fetch(request).then((res) => {
        if (storable(res)) {
          const copy = res.clone();
          caches.open(VERSION).then((c) => c.put(request, copy));
        }
        return res;
      }).catch(() => caches.match(request).then((hit) => hit || Response.error()))
    );
    return;
  }

  if (isStatic) {
    event.respondWith(
      caches.match(request).then((hit) => hit || fetch(request).then((res) => {
        if (storable(res)) {
          const copy = res.clone();
          caches.open(VERSION).then((c) => c.put(request, copy));
        }
        return res;
      }).catch(() => caches.match("/static/offline.html")))
    );
    return;
  }

  // Pages: fresh from the network when possible, cached copy offline. A
  // personalised page is never stored, so there is no cached copy to fall back
  // to - it goes to /offline instead, which is the honest answer.
  event.respondWith(
    fetch(request).then((res) => {
      if (storable(res)) {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(request, copy));
      }
      return res;
    }).catch(() => caches.match(request).then((hit) => hit || caches.match("/static/offline.html")))
  );
});
