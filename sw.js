// Офлайн-кэш: страница, доски, звуки и шрифты кэшируются при установке.
const V = '138';                 // = APP_VERSION в index.html
const VERSION = 'nardy-v' + V;
// хеши содержимого картинок — те же, что AV в index.html (пишет tools/stamp.py)
/*AV*/const AV={"boards/ararat-thumb.webp":"72ff05c2","boards/ararat.webp":"7c44b1ce","boards/ck-beech.png":"ef00f4f8","boards/ck-bronze.png":"db6b57b9","boards/ck-copper.png":"761c282a","boards/ck-gold.png":"87fddeef","boards/ck-ivory.png":"372b72ce","boards/ck-onyx.png":"bfb41b3a","boards/ck-pearl.png":"83aaf841","boards/ck-pomegranate.png":"73a5236d","boards/ck-silver.png":"18222740","boards/ck-walnut.png":"1857427e","boards/ckside-beech.png":"2e4a01b1","boards/ckside-bronze.png":"700fbb0d","boards/ckside-copper.png":"54a53742","boards/ckside-gold.png":"f3c3b036","boards/ckside-ivory.png":"cce1b2d9","boards/ckside-onyx.png":"3695f6bf","boards/ckside-pearl.png":"d9c5e6f3","boards/ckside-pomegranate.png":"79fe0975","boards/ckside-silver.png":"6d16c666","boards/ckside-walnut.png":"bc0fa647","boards/die-1.png":"2d6046dd","boards/die-2.png":"dba1ef51","boards/die-3.png":"c4754c62","boards/die-4.png":"c26495e1","boards/die-5.png":"49661381","boards/die-6.png":"3d46b683","boards/die-amber-1.png":"105d06f3","boards/die-amber-2.png":"f7695264","boards/die-amber-3.png":"518fcc5b","boards/die-amber-4.png":"82e42d65","boards/die-amber-5.png":"a53a1fed","boards/die-amber-6.png":"6114a46b","boards/die-gold-1.png":"606f1c7a","boards/die-gold-2.png":"68eb7219","boards/die-gold-3.png":"4abf64c2","boards/die-gold-4.png":"7ff8a963","boards/die-gold-5.png":"9f589a63","boards/die-gold-6.png":"f67c180d","boards/die-wood-1.png":"f9fecd23","boards/die-wood-2.png":"dad9e71b","boards/die-wood-3.png":"ebe40557","boards/die-wood-4.png":"f8c4f6d2","boards/die-wood-5.png":"239c202c","boards/die-wood-6.png":"ea05a4a3","boards/glass-thumb.webp":"5db12bdb","boards/glass.webp":"3fe1cddb","boards/goldrev-med-l.webp":"875c719a","boards/goldrev-med-r.webp":"beae367a","boards/goldrev-thumb.webp":"1b2ad914","boards/goldrev.webp":"898ad659","boards/intro-rev-w.webp":"c1e7a4bf","boards/intro-rev.webp":"9627dbfd","boards/leafshade.webp":"8666bd89","boards/lid-plain.webp":"32dbab24","boards/lid.webp":"47f4a845","boards/maple.webp":"c7e0d43c","boards/night-thumb.webp":"61a42599","boards/night.webp":"96cd9880","boards/plaque.webp":"6c60c0b6","boards/pomegranate-thumb.webp":"d5574e56","boards/pomegranate.webp":"a89189f5","boards/prop-beads.webp":"01fd0477","boards/prop-cup.webp":"67e8e539","boards/prop-pack.webp":"a1f55e5d","boards/pt-ararat-long.png":"b706af0c","boards/pt-ararat-short.png":"0d9bdbb6","boards/pt-glass-long.png":"2474d3b3","boards/pt-glass-short.png":"2474d3b3","boards/pt-goldrev-long.png":"b706af0c","boards/pt-goldrev-short.png":"0d9bdbb6","boards/pt-night-long.png":"c9576df0","boards/pt-night-short.png":"c9576df0","boards/pt-pomegranate-long.png":"b706af0c","boards/pt-pomegranate-short.png":"0d9bdbb6","boards/pt-sevan-long.png":"b706af0c","boards/pt-sevan-short.png":"0d9bdbb6","boards/pt-yerevan-long.png":"f28ec383","boards/pt-yerevan-short.png":"78fa0ed8","boards/sevan-thumb.webp":"35db3522","boards/sevan.webp":"56ec51be","boards/table.webp":"d353fc6c","boards/walnut-plank.webp":"3f05219c","boards/yerevan-thumb.webp":"4817779b","boards/yerevan.webp":"64e36c39"};/*/AV*/
const av = p => AV[p] ? p + '?v=' + AV[p] : p;
const SHELL = [
  './',
  'index.html',
  'manifest.webmanifest',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/apple-touch-icon.png',
  ...Object.keys(AV).map(av),
];
const SOUNDS = ['duduk.m4a','duduk-intro.m4a','dice-throw-1.m4a','dice-throw-2.m4a','dice-throw-3.m4a','chip-lay-1.m4a','chip-lay-2.m4a','chip-lay-3.m4a','chips-collide-1.m4a','chips-collide-2.m4a','chips-collide-3.m4a','chips-stack-1.m4a','chips-stack-2.m4a']; // те же файлы, что SOUND_FILES в index.html

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

// Установка новой версии: файл с тем же адресом (тот же хеш — то же содержимое) берём из прежнего кэша,
// из сети качаем только изменившееся. Раньше после каждой выкладки заново скачивались все картинки разом.
async function precache(c) {
  for (const u of SHELL) {
    const fresh = u === './' || u === 'index.html';
    const hit = !fresh && await caches.match(u);
    if (hit) { await c.put(u, hit); continue; }
    try { await c.add(new Request(u, { cache: 'reload' })); } catch (e) { /* догрузится по первому запросу */ }
  }
}
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(VERSION)
      .then(c => precache(c)
        .then(() => Promise.all(SOUNDS.map(f => caches.match('sounds/' + f).then(h => h ? c.put('sounds/' + f, h) : c.add('sounds/' + f)).catch(() => {}))))
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
  // (только сама игра: другие страницы, например privacy.html, не должны подменить её в кэше)
  if (req.mode === 'navigate') {
    const game = /\/(index\.html)?$/.test(url.pathname);
    e.respondWith(
      // no-cache: каждый раз сверяемся с сервером, а не берём страницу из кэша браузера (там она живёт до 10 минут после выкладки)
      fetch(req.url, { cache: 'no-cache', credentials: 'same-origin' }).then(r => { if (game && r.ok) { const copy = r.clone(); caches.open(VERSION).then(c => c.put('index.html', copy)); } return r; })
        .catch(() => game ? caches.match('index.html') : caches.match(req))
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
