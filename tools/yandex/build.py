# Сборка для Яндекс Игр: архив nardy-yandex.zip (index.html в корне).
#  - подключает SDK (/sdk.js) и включает режим YA в игре (нет игры по ссылке, установки, ссылок наружу, пачки сигарет,
#    полноэкранного режима и service worker; Game Ready после заставки; разметка геймплея; пауза звука)
#  - всё внешнее кладёт внутрь архива: шрифты Google, модули Firebase, html2canvas
# Запуск из корня репозитория: python3 tools/yandex/build.py [папка_вывода]
import os, re, sys, shutil, zipfile, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'yandex'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r: return r.read()

shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
for d in ('boards', 'sounds'): shutil.copytree(os.path.join(ROOT, d), os.path.join(OUT, d))
os.makedirs(os.path.join(OUT, 'icons')); shutil.copy(os.path.join(ROOT, 'icons', 'icon-192.png'), os.path.join(OUT, 'icons'))
V = os.path.join(OUT, 'vendor'); os.makedirs(os.path.join(V, 'firebase')); os.makedirs(os.path.join(V, 'fonts'))

html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
FBV = re.search(r"FBV='([\d.]+)'", html).group(1)
# Firebase: модули ссылаются друг на друга абсолютными адресами gstatic — переписываем на соседние файлы
for m in ('app', 'auth', 'database'):
    js = get(f'https://www.gstatic.com/firebasejs/{FBV}/firebase-{m}.js').decode('utf-8')
    js = js.replace(f'https://www.gstatic.com/firebasejs/{FBV}/', './')
    assert 'gstatic.com' not in js, m
    open(os.path.join(V, 'firebase', f'firebase-{m}.js'), 'w', encoding='utf-8').write(js)
open(os.path.join(V, 'html2canvas.min.js'), 'wb').write(get('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'))
# шрифты: css Google → локальные woff2
css_all = ''
for link in re.findall(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com/[^"]+)">', html):
    css = get(urllib.parse.quote(link.replace('&amp;', '&'), safe=':/?&=;,@+')).decode('utf-8')
    for u in sorted(set(re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+)\)', css))):
        name = re.sub(r'[^A-Za-z0-9._-]', '_', u.split('/s/')[-1])[-80:]
        open(os.path.join(V, 'fonts', name), 'wb').write(get(u)); css = css.replace(u, 'fonts/' + name)
    css_all += css
open(os.path.join(V, 'fonts.css'), 'w', encoding='utf-8').write(css_all)
html = re.sub(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\n', '', html)
html = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/[^"]+">\n', '', html)
html = html.replace('<style>\n', '<link rel="stylesheet" href="vendor/fonts.css">\n<style>\n', 1)
# превью для соцсетей, манифест, иконки «Домой» — не нужны
html = re.sub(r'<!-- превью ссылки.*?<meta name="twitter:image"[^>]*>\n', '', html, flags=re.S)
html = re.sub(r'<meta name="(mobile-web-app-capable|apple-mobile-web-app-[a-z-]+)"[^>]*>\n', '', html)
html = re.sub(r'<link rel="(manifest|apple-touch-icon)"[^>]*>\n', '', html)
# SDK Яндекса и режим YA — первым делом в <head>
html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<script src="/sdk.js"></script>\n<script>window.YA_BUILD=true;</script>', 1)
for bad in ('gstatic.com', 'fonts.googleapis', 'manifest.webmanifest'):
    assert bad not in html.replace("`https://www.gstatic.com/firebasejs/${FBV}", ''), bad
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(html)

zp = os.path.join(os.path.dirname(OUT), 'nardy-yandex.zip')
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(OUT):
        for f in fs: p = os.path.join(dp, f); z.write(p, os.path.relpath(p, OUT))
print('ok', zp, round(os.path.getsize(zp) / 1e6, 1), 'MB')
