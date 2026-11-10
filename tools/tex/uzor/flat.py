# Готовит узор для доски «Гравюра» (tools/render_gravura.py): выпрямляет фото настоящих нард по вершинам пунктов и
# выделяет гравировку. Запуск из папки с фото board.jpg (само фото в репозиторий не кладём): python flat.py && python atlas.py
import cv2, numpy as np
im=cv2.imread('board.jpg')
K=2; SP=108*K; X0=200*K; Y0=560*K; DY=660*K
src=np.float32([(1166,603),(1697,605),(1163,1263),(1722,1264)])
dst=np.float32([(X0,Y0),(X0+5*SP,Y0),(X0,Y0+DY),(X0+5*SP,Y0+DY)])
M=cv2.getPerspectiveTransform(src,dst)
Wf,Hf=950*K,1800*K
flat=cv2.warpPerspective(im,M,(Wf,Hf),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
cv2.imwrite('flat.png',flat)
g=flat.min(2).astype(np.float32)
bg=cv2.morphologyEx(g,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41)))
bg=cv2.GaussianBlur(bg,(0,0),12)
m=np.clip((bg-g)/(bg*.30+1e-3),0,1)
m=np.clip((m-.18)/.55,0,1)
cv2.imwrite('mask.png',(255-m*255).astype(np.uint8))
np.save('M.npy',M)
# сетка для разметки
v=cv2.resize(cv2.cvtColor((255-m*255).astype(np.uint8),cv2.COLOR_GRAY2BGR),(Wf//2,Hf//2),interpolation=cv2.INTER_AREA)
for x in range(0,Wf//2,50):
    cv2.line(v,(x,0),(x,Hf//2),(0,0,255) if x%100==0 else (200,200,255),1)
    if x%100==0: cv2.putText(v,str(x),(x+2,10),cv2.FONT_HERSHEY_SIMPLEX,.35,(0,0,255),1)
for y in range(0,Hf//2,50):
    cv2.line(v,(0,y),(Wf//2,y),(255,0,0) if y%100==0 else (255,200,200),1)
    if y%100==0: cv2.putText(v,str(y),(2,y+10),cv2.FONT_HERSHEY_SIMPLEX,.35,(255,0,0),1)
cv2.imwrite('maskgrid.png',v)
