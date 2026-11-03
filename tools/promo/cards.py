import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S='/tmp/claude-0/-home-user/fde68c0c-d46d-5e40-9449-283da98b11ce/scratchpad'
F=lambda n,s: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf' if n=='DEJAVU' else f'{S}/{n}',s)
gold=(243,223,180); soft=(236,214,166)
def shadow_text(im, xy, text, font, fill, anchor='mm', blur=10):
    sh=Image.new('RGBA',im.size,(0,0,0,0)); d=ImageDraw.Draw(sh); d.text((xy[0],xy[1]+4),text,font=font,fill=(0,0,0,230),anchor=anchor)
    sh=sh.filter(ImageFilter.GaussianBlur(blur)); im.alpha_composite(sh); ImageDraw.Draw(im).text(xy,text,font=font,fill=fill,anchor=anchor)
def overlay(w,h,lines,name,dim=None):
    im=Image.new('RGBA',(w,h),(0,0,0,0))
    if dim=='full': im.alpha_composite(Image.new('RGBA',(w,h),(12,8,4,150)))
    elif dim:   # полоса под подписью
        y0,y1=dim; band=Image.new('RGBA',(w,h),(0,0,0,0)); ImageDraw.Draw(band).rectangle([0,y0,w,y1],fill=(12,8,4,150)); im.alpha_composite(band.filter(ImageFilter.GaussianBlur(25)))
    for (x,y,t,fn,sz,col) in lines: shadow_text(im,(x,y),t,F(fn,sz),col)
    im.save(f'{S}/vid/{name}.png')
# горизонтальная 1920x1080
overlay(1920,1080,[(960,470,'Нарды','ForumC.ttf',190,gold),(960,610,'длинные нарды','DEJAVU',46,soft)],'h_title',dim='full')
overlay(1920,1080,[(960,430,'Играй бесплатно','ForumC.ttf',120,gold),(960,565,'angel3330506.github.io/nardy','DEJAVU',50,soft),(960,650,'с компьютером · вдвоём · с другом по сети','DEJAVU',36,soft)],'h_end')
for i,(a,b) in enumerate((('Резные доски','как настоящие'),('Бросай кубики','пальцем'),('Играй с другом','по ссылке'))):
    overlay(1920,1080,[(960,975,a+' · '+b,'ForumC.ttf',72,gold)],f'h_cap{i}',dim=(900,1060))
# вертикальная 1080x1920
overlay(1080,1920,[(540,330,'Нарды','ForumC.ttf',200,gold),(540,470,'длинные нарды','DEJAVU',54,soft)],'v_title')
overlay(1080,1920,[(540,1450,'Играй бесплатно','ForumC.ttf',110,gold),(540,1570,'angel3330506.github.io/nardy','DEJAVU',42,soft)],'v_end')
for i,(a,b) in enumerate((('Резные доски','как настоящие'),('Бросай кубики','пальцем'),('Играй с другом','по ссылке'))):
    overlay(1080,1920,[(540,1430,a,'ForumC.ttf',96,gold),(540,1540,b,'DEJAVU',50,soft)],f'v_cap{i}',dim=(1370,1600))
print('cards ok')
