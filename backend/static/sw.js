/* EngineVerse service worker.
 * Cache-first for the app shell, network-first with cache fallback for pages,
 * never caches authenticated or mutating requests.
 */
const VERSION = "engineverse-v3";
const SHELL = [
  "/",
  "/static/css/app.css",
  "/static/js/app.js",
  "/static/js/engine3d.js",
  "/static/icons/favicon.svg",
  "/manifest.webmanifest",
  "/offline",
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

// The path checks above are not sufficient on their own: most pages render the
// signed-in user's own data, and a denylist has to be maintained by hand as
// routes are added. The server marks a personalised response with
// `Cache-Control: private, no-store`; honouring that is what actually keeps one
// user's dashboard out of the cache another user can read offline.
function storable(response) {
  if (!response || !response.ok) return false;
  const cc = (response.headers.get("Cache-Control") || "").toLowerCase();
  return !cc.includes("no-store") && !cc.includes("private");
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!cacheable(request)) return;

  const isStatic = request.destination === "style" || request.destination === "script" ||
                   request.destination === "image" || request.url.includes("/static/");

  if (isStatic) {
    event.respondWith(
      caches.match(request).then((hit) => hit || fetch(request).then((res) => {
        if (storable(res)) {
          const copy = res.clone();
          caches.open(VERSION).then((c) => c.put(request, copy));
        }
        return res;
      }).catch(() => caches.match("/offline")))
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
    }).catch(() => caches.match(request).then((hit) => hit || caches.match("/offline")))
  );
});
