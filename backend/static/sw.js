/* EngineVerse service worker.
 * Cache-first for the app shell, network-first with cache fallback for pages,
 * never caches authenticated or mutating requests.
 */
const VERSION = "engineverse-v1";
const SHELL = [
  "/",
  "/static/css/app.css",
  "/static/js/app.js",
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

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!cacheable(request)) return;

  const isStatic = request.destination === "style" || request.destination === "script" ||
                   request.destination === "image" || request.url.includes("/static/");

  if (isStatic) {
    event.respondWith(
      caches.match(request).then((hit) => hit || fetch(request).then((res) => {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(request, copy));
        return res;
      }).catch(() => caches.match("/offline")))
    );
    return;
  }

  // Pages: fresh from the network when possible, cached copy offline.
  event.respondWith(
    fetch(request).then((res) => {
      if (res.ok) {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(request, copy));
      }
      return res;
    }).catch(() => caches.match(request).then((hit) => hit || caches.match("/offline")))
  );
});
