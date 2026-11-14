# Страницы для поиска: правила длинных и коротких нард (статический HTML, без скриптов) + sitemap.xml.
# python3 tools/seo/build.py  → dlinnye-nardy.html, korotkie-nardy.html, sitemap.xml в корне сайта
import os, json, datetime
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SITE = 'https://angel3330506.github.io/nardy/'
CSS = """:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#120e0a radial-gradient(ellipse 120% 60% at 50% 0,#2b1a0e,#120e0a 70%) no-repeat;color:#efe6d4;font:17px/1.65 "Onest",system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:760px;margin:0 auto;padding:28px 18px 70px}
nav{font-size:14px;margin-bottom:22px}nav a{color:#d9c49b}
h1{font-family:"Forum",Georgia,serif;font-weight:400;color:#f3d993;font-size:clamp(34px,7vw,48px);line-height:1.1;margin:0 0 12px}
h2{font-family:"Forum",Georgia,serif;font-weight:400;color:#f3d993;font-size:28px;margin:38px 0 8px}
h3{font-size:18px;color:#f3d993;margin:22px 0 4px;font-weight:600}
p,li{color:#e6dccb}b{color:#fff3d6;font-weight:600}
a{color:#f3cf78}
ul,ol{padding-left:22px}li{margin:4px 0}
figure{margin:22px 0}figure img{width:100%;height:auto;border-radius:12px;border:1px solid #6b5132;display:block}
figcaption{font-size:14px;color:#b9a888;margin-top:6px}
.lead{font-size:19px;color:#efe6d4}
.cta{display:inline-block;margin:10px 0 4px;padding:13px 26px;border-radius:999px;background:linear-gradient(180deg,#f6dc96,#c9a05a);color:#2a170b;font-weight:700;text-decoration:none;box-shadow:0 6px 18px rgba(0,0,0,.4)}
.box{background:rgba(255,240,210,.05);border:1px solid rgba(243,217,147,.22);border-radius:14px;padding:4px 18px;margin:18px 0}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:16px}td,th{border-bottom:1px solid rgba(243,217,147,.18);padding:7px 6px;text-align:left}th{color:#f3d993;font-weight:500}
footer{margin-top:50px;font-size:14px;color:#9d8c70}footer a{color:#d9c49b}"""

def page(slug, title, desc, h1, body, faq):
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc, "inLanguage": "ru",
           "image": SITE + 'img/' + ('long-board.webp' if 'dlin' in slug else 'short-board.webp'), "url": SITE + slug,
           "author": {"@type": "Organization", "name": "Нарды"}},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}]
    faq_html = ''.join(f'<h3>{q}</h3><p>{a}</p>' for q, a in faq)
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE}{slug}">
<meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{SITE}{slug}"><meta property="og:image" content="{SITE}og.jpg"><meta property="og:locale" content="ru_RU">
<link rel="icon" type="image/png" href="icons/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Forum&family=Onest:wght@400;600;700&display=swap">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<main>
<nav><a href="./">Нарды — играть онлайн</a> · <a href="dlinnye-nardy.html">Правила длинных нард</a> · <a href="korotkie-nardy.html">Правила коротких нард</a></nav>
<h1>{h1}</h1>
{body}
<h2>Частые вопросы</h2>
{faq_html}
<p><a class="cta" href="./">Играть в нарды бесплатно</a></p>
<footer>«Нарды» — бесплатная игра в браузере: с компьютером, вдвоём на одном телефоне или с другом по ссылке. Без регистрации. · <a href="privacy.html">Конфиденциальность</a></footer>
</main>
</body>
</html>
"""

LONG_BODY = """<p class="lead">Длинные нарды — самый популярный вариант игры на Кавказе и в Армении. Бить шашки здесь нельзя: побеждает тот, кто умнее строит заборы и быстрее приводит шашки домой. Ниже — все правила простыми словами и советы для начинающих.</p>
<p><a class="cta" href="./">Сыграть онлайн бесплатно</a></p>
<figure><img src="img/long-board.webp" width="1200" height="552" alt="Партия в длинные нарды на резной доске «Аревахач»" loading="lazy"><figcaption>Длинные нарды в игре «Нарды»: подсвечены шашка и пункты, куда она может пойти.</figcaption></figure>
<h2>Доска и расстановка</h2>
<p>Доска состоит из 24 пунктов (треугольников), по 6 в каждой четверти. У каждого игрока <b>15 шашек</b>, и в начале все они стоят на одном пункте — на <b>«голове»</b>. Белые начинают справа снизу, чёрные — слева сверху, то есть по диагонали друг от друга.</p>
<p>Обе стороны ходят <b>против часовой стрелки</b> и проходят всю доску по кругу. <b>Дом</b> белых — правая верхняя четверть, дом чёрных — левая нижняя.</p>
<h2>Как ходить</h2>
<ol>
<li>Игроки по очереди бросают два кубика. Каждое число — это ход одной шашки на столько пунктов вперёд.</li>
<li>Числа кубиков играются <b>отдельно</b>: одной шашкой на одно число, другой — на другое. Можно сыграть оба числа одной шашкой подряд, если промежуточный пункт свободен.</li>
<li><b>Дубль</b> (одинаковые числа) играется <b>четыре раза</b>: при 3‑3 — четыре хода по 3.</li>
<li>Если можно сыграть оба кубика — играть обязательно оба. Если только один — нужно сыграть больший. Если ходов нет — ход пропадает.</li>
</ol>
<h2>Главные запреты</h2>
<div class="box">
<h3>Бить нельзя</h3><p>На пункт, где стоит хотя бы одна чужая шашка, вставать нельзя — он закрыт.</p>
<h3>С головы — одна шашка за ход</h3><p>Исключение — самый первый бросок: при 6‑6, 4‑4 или 3‑3 с головы можно снять две шашки, потому что иначе дубль не сыграть.</p>
<h3>Нельзя глухой забор из шести</h3><p>Нельзя ставить заграждение из 6 занятых пунктов подряд, если впереди него нет ни одной шашки соперника: это полностью запирало бы его.</p>
</div>
<h2>Выброс и победа</h2>
<p>Когда все 15 шашек в доме, их можно <b>выбрасывать</b> с доски: шашку с пункта, номер которого выпал на кубике (считая от края доски). Если выпало больше, чем нужно самой дальней шашке, можно выбросить её.</p>
<table><tr><th>Итог</th><th>Когда</th><th>Очки</th></tr>
<tr><td>Победа</td><td>вы выбросили все шашки первым</td><td>1</td></tr>
<tr><td>Марс</td><td>у соперника к этому моменту не выброшено ни одной шашки</td><td>2</td></tr></table>
<figure><img src="img/mars.webp" width="1200" height="552" alt="Марс в нардах — двойная победа" loading="lazy"><figcaption>Марс — двойная победа: соперник не успел выбросить ни одной шашки.</figcaption></figure>
<h2>Как называют броски</h2>
<p>Во дворах Еревана и Тбилиси броски называют по-персидски: <b>ек</b> (1), <b>ду</b> (2), <b>се</b> (3), <b>джахар</b> (4), <b>беш</b> (5), <b>шеш</b> (6). Отсюда «<b>шеш-беш</b>» — 6 и 5, «<b>ду-шеш</b>» — две шестёрки, «<b>се-ек</b>» — 3 и 1.</p>
<h2>Советы начинающим</h2>
<ul>
<li><b>Не держите всё на голове.</b> Чем раньше шашки разойдутся по доске, тем больше вариантов хода.</li>
<li><b>Стройте заборы перед соперником.</b> Три-четыре занятых пункта подряд на его пути сильно тормозят его шашки.</li>
<li><b>Занимайте свой «шестой» пункт.</b> Пункт рядом с домом соперника — удобная опора для перехода.</li>
<li><b>Считайте дорогу.</b> Сумма пунктов, которые осталось пройти всем шашкам, подскажет, кто впереди в гонке.</li>
</ul>
<figure><img src="img/gravura.webp" width="1200" height="552" alt="Доска «Гравюра» — белый акрил с гравировкой" loading="lazy"><figcaption>Доска «Гравюра» — по настоящим нардам из белого акрила.</figcaption></figure>"""
LONG_FAQ = [
 ("Можно ли бить шашки в длинных нардах?", "Нет. В длинных нардах шашки не бьют: пункт, где стоит хотя бы одна шашка соперника, закрыт для хода."),
 ("Сколько шашек можно снять с головы?", "Одну за ход. Исключение — первый бросок 6‑6, 4‑4 или 3‑3: тогда можно снять две."),
 ("Что такое марс в нардах?", "Марс — двойная победа: вы выбросили все 15 шашек, а соперник не успел выбросить ни одной."),
 ("Что делать, если ход невозможен?", "Если ни одним кубиком сыграть нельзя, ход пропадает. Если можно сыграть только один — играется больший."),
 ("Где сыграть в длинные нарды онлайн бесплатно?", "В игре «Нарды» — прямо в браузере на телефоне или компьютере, без регистрации: с компьютером (шесть соперников разной силы), вдвоём на одном телефоне или с другом по ссылке."),
]
SHORT_BODY = """<p class="lead">Короткие нарды — классический вариант, известный во всём мире как backgammon. В отличие от длинных, здесь шашки <b>бьют</b>, поэтому партия острее и быстрее. Вот правила по порядку.</p>
<p><a class="cta" href="./">Сыграть онлайн бесплатно</a></p>
<figure><img src="img/short-board.webp" width="1200" height="552" alt="Партия в короткие нарды на доске «Севан»" loading="lazy"><figcaption>Короткие нарды в игре «Нарды»: доска «Севан», ночь.</figcaption></figure>
<h2>Расстановка</h2>
<p>У каждого 15 шашек, и они сразу расставлены на доске: <b>2 + 5 + 3 + 5</b>. Две шашки стоят в самом дальнем пункте, пять — в середине пути, три — у входа в дом и пять — в своём доме. Игроки идут <b>навстречу</b> друг другу.</p>
<h2>Ход</h2>
<ul>
<li>Два кубика — два хода, на каждое число отдельно или одной шашкой подряд.</li>
<li>Дубль играется четыре раза.</li>
<li>Если можно сыграть оба кубика — обязательно оба; если только один — больший.</li>
</ul>
<h2>Бой и бар</h2>
<div class="box">
<h3>Закрытый пункт</h3><p>Пункт, где стоят <b>две и больше</b> чужих шашки, закрыт.</p>
<h3>Одиночная шашка — под боем</h3><p>Если на пункте стоит <b>одна</b> чужая шашка, на него можно встать — она <b>сбита</b> и уходит на <b>бар</b> (середину доски).</p>
<h3>Ввод с бара</h3><p>Пока у вас есть шашка на баре, другими ходить нельзя: сначала её нужно ввести в дом соперника на пункт по числу кубика. Если он закрыт — ход пропадает.</p>
</div>
<h2>Выброс и счёт</h2>
<p>Выбрасывать можно, когда все 15 шашек в доме. Если вашу шашку сбили во время выброса — сначала её нужно вернуть домой.</p>
<table><tr><th>Итог</th><th>Когда</th><th>Очки</th></tr>
<tr><td>Победа</td><td>вы выбросили все шашки первым</td><td>1</td></tr>
<tr><td>Марс</td><td>у соперника ничего не выброшено</td><td>2</td></tr>
<tr><td>Кокс</td><td>у соперника ничего не выброшено, и его шашка ещё на баре или в вашем доме</td><td>3</td></tr></table>
<h2>Советы начинающим</h2>
<ul>
<li><b>Не оставляйте шашки по одной</b> там, где соперник может до них дойти: одиночку собьют.</li>
<li><b>Закрывайте пункты в своём доме.</b> Чем больше закрыто, тем труднее сбитой шашке соперника войти.</li>
<li><b>Бейте, когда это безопасно.</b> Сбитая шашка соперника теряет весь пройденный путь.</li>
<li><b>Уходите вперёд с дальних шашек.</b> Две шашки в самом дальнем пункте — главная мишень, выводите их вовремя.</li>
</ul>
<figure><img src="img/puzzle.webp" width="1200" height="552" alt="Задача дня в нардах: найдите лучший ход" loading="lazy"><figcaption>Задача дня — каждый день новая позиция: найдите лучший ход.</figcaption></figure>"""
SHORT_FAQ = [
 ("Чем короткие нарды отличаются от длинных?", "В коротких шашки сразу расставлены по доске, игроки идут навстречу и могут бить одиночные шашки соперника. В длинных все шашки стартуют с головы, а бить нельзя."),
 ("Что такое бар?", "Бар — середина доски. Туда уходит сбитая шашка; пока она там, другими шашками ходить нельзя — сначала её нужно ввести обратно."),
 ("Что такое кокс?", "Кокс — тройная победа в коротких нардах: у соперника не выброшено ни одной шашки, и при этом его шашка ещё на баре или в вашем доме."),
 ("Где сыграть в короткие нарды онлайн?", "В игре «Нарды» — в браузере на телефоне или компьютере, бесплатно и без регистрации: с компьютером, вдвоём или с другом по ссылке."),
]
pages = [('dlinnye-nardy.html', 'Длинные нарды — правила игры простыми словами | Нарды',
          'Правила длинных нард: расстановка, ход, голова, дубли, запрет заграждения, выброс и марс. Советы начинающим и бесплатная игра онлайн.',
          'Длинные нарды: правила игры', LONG_BODY, LONG_FAQ),
         ('korotkie-nardy.html', 'Короткие нарды — правила игры: бой, бар, марс и кокс | Нарды',
          'Правила коротких нард (backgammon): расстановка 2+5+3+5, бой одиночных шашек, бар, выброс, марс и кокс. Советы и бесплатная игра онлайн.',
          'Короткие нарды: правила игры', SHORT_BODY, SHORT_FAQ)]
for slug, *rest in pages:
    open(os.path.join(ROOT, slug), 'w').write(page(slug, *rest))
today = datetime.date.today().isoformat()
urls = ['', 'dlinnye-nardy.html', 'korotkie-nardy.html']
open(os.path.join(ROOT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod><priority>{"1.0" if not u else "0.8"}</priority></url>\n' for u in urls) + '</urlset>\n')
print('seo ok')
