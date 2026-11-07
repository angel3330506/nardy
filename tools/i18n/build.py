# Вставляет словарь tools/i18n/en.json в index.html (между /*EN*/ … /*/EN*/) и показывает, какие тексты,
# встреченные в игре (tools/i18n/harvest.json), перевод ещё не покрывает — тем же алгоритмом, что tr() в игре.
import json, re, os, sys
D = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(D, '..', '..')
EN = json.load(open(os.path.join(D, 'en.json'), encoding='utf-8'))
EN = {re.sub(r'\s+', ' ', k).strip(): v for k, v in EN.items()}
p = os.path.join(ROOT, 'index.html'); s = open(p, encoding='utf-8').read()
s = re.sub(r'/\*EN\*/.*?/\*/EN\*/', lambda m: '/*EN*/const EN=' + json.dumps(EN, ensure_ascii=False, separators=(',', ':')) + ';/*/EN*/', s, flags=re.S)
open(p, 'w', encoding='utf-8').write(s)
CYR = re.compile('[А-Яа-яЁё]')
def core(c):
    k = re.sub(r'\d+', '#', re.sub(r'\s+', ' ', c)); return EN.get(k)
def tr(t):
    t = t.strip()
    r = core(t)
    if r is not None: return r
    parts = re.split(r'(\.\s+|!\s+|\?\s+|:\s+|\s—\s|;\s+|\s·\s)', t)
    return ''.join((core(x) if core(x) is not None else x) if CYR.search(x) else x for x in parts)
hp = os.path.join(D, 'harvest.json')
if os.path.exists(hp):
    miss = sorted({re.sub(r'\d+', '#', h) for h in json.load(open(hp, encoding='utf-8')) if CYR.search(tr(h))})
    json.dump(miss, open(os.path.join(D, 'missing.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('словарь:', len(EN), '· не переведено из встреченного:', len(miss))
