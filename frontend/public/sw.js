// Service worker minimale: rende la PWA installabile e dà un fallback offline
// per l'app shell. Le chiamate API vanno sempre in rete.
const CACHE = "reel-shell-v1";
const SHELL = ["/", "/index.html", "/manifest.webmanifest", "/icons/icon-192.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  // Non intercettare chiamate cross-origin (API backend, font, ecc.)
  if (url.origin !== self.location.origin) return;

  // Navigazioni (incluso /share, /archive, ...): network-first con fallback shell
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).catch(() => caches.match("/index.html"))
    );
    return;
  }

  // Asset statici: cache-first
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req))
  );
});
