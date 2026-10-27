# Превью отрендеренных досок и шашек для проверки глазами.
import sys, os
from PIL import Image
OUT = os.path.join(os.path.dirname(__file__), '..', '.preview')
B = os.path.join(os.path.dirname(__file__), '..', 'boards')
for name in sys.argv[1:]:
    im = Image.open(os.path.join(B, name + '.webp')); bg = Image.new('RGB', im.size, (20, 16, 12)); bg.paste(im, mask=im.split()[3])
    bg.resize((1100, 700), Image.LANCZOS).save(os.path.join(OUT, name + '.png'))
    bg.crop((0, 0, 1200, 760)).save(os.path.join(OUT, name + '-crop.png'))
cks = [Image.open(os.path.join(B, f'ck-{k}.png')) for k in ('ivory', 'onyx', 'beech', 'walnut')]
c = Image.new('RGB', (560, 140), (90, 55, 28))
for i, k in enumerate(cks): c.paste(k, (10 + i * 138, 6), k)
c.save(os.path.join(OUT, 'checkers.png'))
