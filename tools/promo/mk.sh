set -e
D=/tmp/claude-0/-home-user/fde68c0c-d46d-5e40-9449-283da98b11ce/scratchpad/vid; A=/home/user/nardy/sounds/duduk.m4a; cd "$D"
OV="[1:v]format=rgba,fade=in:st=0:d=0.4:alpha=1,fade=out:st=2.3:d=0.5:alpha=1[t];
[2:v]format=rgba,fade=in:st=3:d=0.4:alpha=1,fade=out:st=6.4:d=0.4:alpha=1[c0];
[3:v]format=rgba,fade=in:st=7.6:d=0.4:alpha=1,fade=out:st=12:d=0.4:alpha=1[c1];
[4:v]format=rgba,fade=in:st=12.8:d=0.4:alpha=1,fade=out:st=17.6:d=0.4:alpha=1[c2];
[5:v]format=rgba,fade=in:st=18.5:d=0.6:alpha=1[en];
[base][t]overlay=shortest=1[v1];[v1][c0]overlay[v2];[v2][c1]overlay[v3];[v3][c2]overlay[v4];[v4][en]overlay,format=yuv420p[v];
[6:a]atrim=0:21.5,afade=t=in:d=1,afade=t=out:st=19.5:d=2,volume=1.3[au]"
for o in h v; do
  if [ $o = h ]; then PRE="[0:v]null[base];"; OUT=nardy-promo-16x9.mp4; else PRE="[0:v]split[s1][s2];[s1]scale=-2:1920,crop=1080:1920,boxblur=24:2,eq=brightness=-0.22[bg];[s2]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2[base];"; OUT=nardy-promo-9x16.mp4; fi
  ffmpeg -nostdin -v error -y -i base_h.mp4 \
    -loop 1 -t 21.5 -i ${o}_title.png -loop 1 -t 21.5 -i ${o}_cap0.png -loop 1 -t 21.5 -i ${o}_cap1.png -loop 1 -t 21.5 -i ${o}_cap2.png -loop 1 -t 21.5 -i ${o}_end.png -i "$A" \
    -filter_complex "$PRE$OV" -map "[v]" -map "[au]" -c:v libx264 -crf 20 -preset medium -r 30 -c:a aac -b:a 160k -t 21.5 -movflags +faststart $OUT
done
for f in 16x9 9x16; do for t in 1 5 10 15 20; do ffmpeg -nostdin -v error -y -ss $t -i nardy-promo-$f.mp4 -frames:v 1 -vf scale=-1:360 p$f-$t.png; done; done
python3 -c "
from PIL import Image
D='$D'
a=[Image.open(f'{D}/p16x9-{t}.png') for t in (1,5,10,15,20)]; b=[Image.open(f'{D}/p9x16-{t}.png') for t in (1,5,10,15,20)]
c=Image.new('RGB',(5*640,720))
for i,im in enumerate(a): c.paste(im,(i*640,0))
for i,im in enumerate(b): c.paste(im,(i*210,360))
c.save(f'{D}/promo-sheet.png')"
ls -la nardy-promo-*
