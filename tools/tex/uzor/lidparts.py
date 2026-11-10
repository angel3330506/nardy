import cv2, numpy as np, os
r=cv2.imread('lidink.png',cv2.IMREAD_UNCHANGED).astype(np.float32)/255
col,a=r[...,:3],r[...,3]
OUT='/home/user/nardy/tools/tex/uzor'
def part(name,x0,y0,x1,y1,minmean=.45,minarea=25):
    c=col[y0:y1,x0:x1].copy(); m=a[y0:y1,x0:x1].copy()
    m=np.clip((m-.15)/.6,0,1)
    n,lab,st,_=cv2.connectedComponentsWithStats((m>.3).astype(np.uint8),8)
    keep=np.zeros(n,bool)
    for i in range(1,n):
        sel=lab==i; keep[i]=st[i,4]>=minarea and m[sel].mean()>=minmean
    k=cv2.dilate(keep[lab].astype(np.uint8),np.ones((3,3),np.uint8))>0
    m=m*k
    cv2.imwrite(f'{OUT}/{name}.png',np.dstack([c*255,m*255]).clip(0,255).astype(np.uint8))
    return m
part('lid-rider',135,600,890,1225,minmean=.5,minarea=40)
part('lid-corner',40,60,200,240)          # левый верхний уголок; остальные — его зеркала
part('lid-side',40,900,120,1150)
print('ok')
