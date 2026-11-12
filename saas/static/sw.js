// ReplyInbox service worker: notifications only (no offline caching, so the app is never stale).
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  event.waitUntil((async () => {
    let note = {title: "ReplyInbox", body: "Open ReplyInbox", url: "/app"};
    try {
      const r = await fetch("/api/notifications/latest", {credentials: "include"});
      if (r.ok) note = await r.json();
    } catch (e) {}
    await self.registration.showNotification(note.title, {
      body: note.body, icon: "/static/icon-192.png", badge: "/static/icon-192.png", data: {url: note.url || "/app"}, tag: "replyinbox",
    });
  })());
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/app";
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({type: "window", includeUncontrolled: true});
    for (const c of all) { if (new URL(c.url).origin === self.location.origin) { await c.focus(); return c.navigate(url); } }
    return self.clients.openWindow(url);
  })());
});
