# Вырезает элементы гравировки из выпрямленного фото (mask.png, 2 px на «плоский» пиксель) в tools/tex/uzor/*.png
import cv2, numpy as np, os
m=255-cv2.imread('mask.png',0); m=m.astype(np.float32)/255
OUT='/home/user/nardy/tools/tex/uzor'; os.makedirs(OUT,exist_ok=True)
K=2
yy,xx=np.mgrid[0:m.shape[0],0:m.shape[1]]/K
def clean(a,edge=True):
    a=np.clip((a-.22)/.5,0,1)                              # серые разводы фона и кромки арок — прочь
    n,lab,st,_=cv2.connectedComponentsWithStats((a>.3).astype(np.uint8),8)
    keep=np.zeros(n,bool)
    for i in range(1,n):
        x,y,w,h,ar=st[i]
        touch=edge and (x<=1 or y<=1 or x+w>=a.shape[1]-1)
        keep[i]=ar>=6 and not touch and not (edge and y<40 and ar<260)   # обрывки кромки арок у верха вырезки
    m=keep[lab]; m=cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8))>0
    return a*m
def save(name,a,edge=True): cv2.imwrite(f'{OUT}/{name}.png',(clean(a,edge)*255).astype(np.uint8))
for k in range(6):
    ax=200+108*k
    hw=54*(560-yy)/305                                   # полуширина треугольника пункта на высоте y
    inside=np.clip((hw-11-np.abs(xx-ax))/2,0,1)*(yy>232)*(yy<480)
    c=(m*inside)[228*K:480*K,(ax-56)*K:(ax+56)*K]
    save(f'vine{k}',c)
    box=np.clip((26-np.abs(xx-ax))/2,0,1)*np.clip((yy-561)/3,0,1)
    f=(m*box)[556*K:620*K,(ax-28)*K:(ax+28)*K]
    save(f'fin{k}',f)
# ромб: только внутренний узор (контур рисуем сами)
cx,cy,hw_,hv=485,889,209,204.5
d=np.abs(xx-cx)/hw_+np.abs(yy-cy)/hv
save('diamond',(m*np.clip((.93-d)*40,0,1))[int(cy-hv)*K:int(cy+hv)*K,int(cx-hw_)*K:int(cx+hw_)*K])
save('side',m[775*K:985*K,815*K:870*K])
save('side2',m[790*K:1005*K,88*K:140*K])
print('ok')
