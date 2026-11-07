# Собирает русские строки из index.html: текст HTML, атрибуты и строки/шаблоны JS (разрезанные по ${…} и HTML-тегам).
# Цифры заменяются на #, чтобы одна запись покрывала «ступень 1 из 4» и «ступень 3 из 4».
import re, json, sys, os
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
CYR = re.compile('[А-Яа-яЁё]')
out = set()
def add(t):
    t = re.sub(r'\s+', ' ', t).strip()
    if not CYR.search(t): return
    out.add(re.sub(r'\d+', '#', t))
def add_html(frag):
    for part in re.split(r'<[^>]*>', frag):
        part = part.replace('&nbsp;', ' ')
        if CYR.search(part): add(part)
# 1. разметка вне <script>/<style>
html = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', '', src)
html_body = re.sub(r'<!--[\s\S]*?-->', '', html)
add_html(html_body)
for a in re.findall(r'(?:title|aria-label|placeholder|alt|content)="([^"]*)"', html_body): add(a)
# 2. строки в скриптах
js = '\n'.join(re.findall(r'<script[^>]*>([\s\S]*?)</script>', src))
js = re.sub(r'(?m)^\s*//.*$', '', js)
js = re.sub(r'/\*[\s\S]*?\*/', '', js)
i = 0; n = len(js)
while i < n:
    c = js[i]
    if c == '/' and i + 1 < n and js[i + 1] == '/':           # комментарий до конца строки
        j = js.find('\n', i); i = n if j < 0 else j; continue
    if c in '\'"':
        j = i + 1; buf = ''
        while j < n and js[j] != c:
            if js[j] == '\\': buf += js[j:j + 2]; j += 2; continue
            buf += js[j]; j += 1
        add_html(buf.replace("\\'", "'").replace('\\"', '"')); i = j + 1; continue
    if c == '`':
        j = i + 1; parts = []; buf = ''
        while j < n and js[j] != '`':
            if js[j] == '\\': buf += js[j:j + 2]; j += 2; continue
            if js[j] == '$' and j + 1 < n and js[j + 1] == '{':
                parts.append(buf); buf = ''; depth = 1; j += 2
                inner_start = j
                while j < n and depth:
                    if js[j] == '{': depth += 1
                    elif js[j] == '}': depth -= 1
                    j += 1
                inner = js[inner_start:j - 1]
                for q in re.findall(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"", inner):   # строки внутри ${…}
                    add_html((q[0] or q[1]))
                for q in re.findall(r'`([^`]*)`', inner): add_html(re.sub(r'\$\{[^}]*\}', ' ', q))
                continue
            buf += js[j]; j += 1
        parts.append(buf)
        for p in parts: add_html(p)
        i = j + 1; continue
    i += 1
res = sorted(out)
json.dump(res, open(os.path.join(os.path.dirname(__file__), 'strings.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(res), 'строк,', sum(len(s) for s in res), 'символов')
