# Пишет хеши содержимого картинок (boards/*) в index.html и sw.js (между /*AV*/ и /*/AV*/).
# Запускать перед каждой выкладкой: адрес картинки меняется, только если изменился сам файл.
import hashlib, json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
AV = {}
for f in sorted(os.listdir(os.path.join(ROOT, 'boards'))):
    if f.endswith(('.webp', '.png', '.jpg')):
        AV['boards/' + f] = hashlib.md5(open(os.path.join(ROOT, 'boards', f), 'rb').read()).hexdigest()[:8]
js = '/*AV*/const AV=' + json.dumps(AV, separators=(',', ':')) + ';/*/AV*/'
for name in ('index.html', 'sw.js'):
    p = os.path.join(ROOT, name); s = open(p, encoding='utf-8').read()
    s2, n = re.subn(r'/\*AV\*/.*?/\*/AV\*/', lambda m: js, s, flags=re.S); assert n == 1, name
    open(p, 'w', encoding='utf-8').write(s2)
print(len(AV), 'files stamped')
