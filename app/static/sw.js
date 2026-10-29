// Minimal service worker: makes the app installable and keeps the shell available offline.
// API calls are never cached.
const CACHE = "mr-shell-v31";
// Complete shell: every asset index.html and the manifest need. addAll below is atomic - if any
// fetch fails, install fails, this worker never activates, and the previous worker and its cache
// keep serving, so a half-downloaded update can never leave the app broken offline.
const SHELL = [
  "/",
  "/static/app.js",
  "/static/card.js",
  "/static/hub.js",
  "/static/hubdata.js",
  "/static/sessions.js",
  "/static/practice-pack.json",
  "/static/coding-problems.json",
  "/static/bank-common.json",
  "/static/manifest.webmanifest",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/maskable-512.png",
  "/static/icons/apple-touch-icon.png",
  "/static/offline.html",
  "/static/offline.js",
  "/favicon.ico",
];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => {
  // Runs only after a successful install, so the new cache is complete before old ones are purged.
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin || u.pathname.startsWith("/api/") || u.pathname === "/health") return;
  e.respondWith(
    fetch(e.request).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r; })
      .catch(() => caches.match(e.request).then(m => m ||
        (e.request.mode === "navigate" ? caches.match("/").then(h => h || caches.match("/static/offline.html")) : new Response("", { status: 503, statusText: "Offline" }))))
  );
});
