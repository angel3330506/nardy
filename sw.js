// Офлайн-кэш: страница, доски, звуки и шрифты кэшируются при установке.
const V = '16';                 // = APP_VERSION в index.html
const VERSION = 'nardy-v' + V;
const SHELL = [
  './',
  'index.html',
  'manifest.webmanifest',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/apple-touch-icon.png',
  ...['night', 'ararat', 'glass', 'yerevan'].flatMap(k => [`boards/${k}.webp?v=${V}`, `boards/${k}-thumb.webp?v=${V}`]),
  ...['ivory', 'onyx', 'beech', 'walnut'].map(k => `boards/ck-${k}.png?v=${V}`),
  `boards/table.webp?v=${V}`,
];
const SOUNDS = ['dice-throw-1.m4a','dice-throw-2.m4a','dice-throw-3.m4a','chip-lay-1.m4a','chip-lay-2.m4a','chip-lay-3.m4a','chips-collide-1.m4a','chips-collide-2.m4a','chips-collide-3.m4a','chips-stack-1.m4a','chips-stack-2.m4a']; // те же файлы, что SOUND_FILES в index.html

// Стили Google Fonts — те же адреса, что в <link> в index.html. Файлы шрифтов из них кэшируются при установке.
const FONT_CSS = [
  'https://fonts.googleapis.com/css2?family=Forum&family=Onest:wght@400;500;700&display=swap',
  'https://fonts.googleapis.com/css2?family=Noto+Serif+Armenian:wght@600&text=ՀԱՅՍՏՆՐ&display=swap',
];

async function cacheFonts(c) {
  for (const href of FONT_CSS) {
    try {
      const r = await fetch(href, { mode: 'cors' });
      if (!r.ok) continue;
      await c.put(href, r.clone());
      const urls = [...(await r.text()).matchAll(/url\((https:[^)]+)\)/g)].map(m => m[1]);
      await Promise.all(urls.map(u => c.add(u).catch(() => {})));
    } catch (e) { /* без шрифтов игра работает на системных */ }
  }
}

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(VERSION)
      // cache:'reload' — мимо HTTP-кэша браузера, иначе в новый кэш попадут старые файлы
      .then(c => c.addAll(SHELL.map(u => new Request(u, { cache: 'reload' })))
        .then(() => Promise.all(SOUNDS.map(f => c.add('sounds/' + f).catch(() => {}))))
        .then(() => cacheFonts(c)))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Страница: сначала сеть (чтобы обновления приходили), без сети — кэш
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then(r => { const copy = r.clone(); caches.open(VERSION).then(c => c.put('index.html', copy)); return r; })
        .catch(() => caches.match('index.html'))
    );
    return;
  }
  // Остальное: кэш, затем сеть с сохранением
  if (url.origin === location.origin || url.host.endsWith('fonts.googleapis.com') || url.host.endsWith('fonts.gstatic.com')) {
    e.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(r => {
        if (r.ok || r.type === 'opaque') { const copy = r.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
        return r;
      }))
    );
  }
});
