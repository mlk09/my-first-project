#!/bin/bash
# BOLT: The Last Tram at 11:47 – Part 4 ("Her Real Face") + Amazon book promo card before the end screen.
# Usage: make.sh <out_dir>. Each Gemini upload repeats Part 2 for ~30s; the new shot is the last ~10s.
set -e
HERE=$(cd "$(dirname "$0")" && pwd); FONTS=$HERE/../v3/fonts
U=/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1
C1=${C1:-$U/475f2493-vid01.mp4}   # robot army kneels to the girl
C2=${C2:-$U/caed3e1b-vid02.mp4}   # lightning reflection, porcelain face cracks
C3=${C3:-$U/c2f77141-vid03.mp4}   # eagle picks Bolt, run to the tram, girl in the window
O=$1; mkdir -p $O/assets $O/es $O/sfx $O/bk; cd $O; AS=$O/assets; FX=$O/sfx
python3 -I $HERE/captions.py $AS $FONTS
python3 -I $HERE/endscreen.py $O/es $FONTS
python3 -I $HERE/sfx.py $FX
python3 -I $HERE/bookcard.py $HERE/book_endcard.webp $O/bk $FONTS
num(){ echo "$1" | bc -l | sed 's/^\./0./; s/^-\./-0./'; }

# seg name src start out_dur zoomFrom zoomTo speed   (480x864 source; delogo hides the Gemini sparkle)
seg(){ n=$1 src=$2 ss=$3 d=$4 z0=$5 z1=$6 sp=${7:-1}
  sd=$(num "$d*$sp")
  at="atempo=$sp"; [ $(echo "$sp < 0.5" | bc) -eq 1 ] && at="atempo=0.5,atempo=$(num "$sp/0.5")"
  ffmpeg -v error -y -ss $ss -t $sd -i $src -filter_complex "
  [0:v]delogo=x=384:y=765:w=36:h=36,setpts=(PTS-STARTPTS)/$sp,fps=30,hqdn3d=1.5:1.5:3:3,
  scale=w='1080*($z0+($z1-$z0)*t/$d)':h='1920*($z0+($z1-$z0)*t/$d)':eval=frame:flags=lanczos,
  crop=1080:1920,cas=0.6,setsar=1,trim=duration=$d[v];
  [0:a]$at,aresample=48000,atrim=duration=$d,afade=t=in:d=0.04,afade=t=out:st=$(num "$d-0.06"):d=0.06[a]" \
  -map [v] -map [a] -c:v libx264 -preset fast -crf 12 -c:a pcm_s16le $n.mkv
}
seg a $C1 30.6 1.6 1.00 1.08          #  0.0 army comes out of the dark
seg b $C1 32.8 2.2 1.00 1.06          #  1.6 Bolt beside the girl
seg c $C1 35.4 2.2 1.06 1.00          #  3.8 robots bow
seg d $C1 39.2 1.7 1.00 1.10          #  6.0 she raises the ticket
seg e $C2 32.4 1.8 1.00 1.08          #  7.7 lightning: her reflection is a robot
seg f $C2 34.7 3.4 1.00 1.12 0.8      #  9.5 porcelain face cracks, red eye
seg g $C3 31.0 2.4 1.00 1.05          # 12.9 eagle lands on Bolt
seg h $C3 34.7 3.3 1.00 1.06          # 15.3 run for the tram
seg i $C3 38.7 2.2 1.00 1.10          # 18.6 girl alone in the window
ffmpeg -v error -y -f lavfi -i color=c=black:s=1080x1920:r=30:d=5.0 -f lavfi -i anullsrc=r=48000:cl=stereo -t 5.0 \
  -c:v libx264 -preset fast -crf 12 -pix_fmt yuv420p -c:a pcm_s16le bkslot.mkv                # 20.8 book card slot
seg l $C3 39.6 3.6 1.00 1.06 0.38     # 25.8 girl in the window, slow-mo, under the end screen
printf "file '%s'\n" a.mkv b.mkv c.mkv d.mkv e.mkv f.mkv g.mkv h.mkv i.mkv bkslot.mkv l.mkv > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c:v copy -c:a pcm_s16le joined.mkv
TOTAL=29.4; BK=20.8; ES=25.8

T=("0.15 1.55" "1.7 3.75" "3.9 5.95" "6.05 7.6" "7.8 9.4" "9.6 12.8" "13.0 15.2" "15.4 18.5" "18.7 20.7")
IN=""; FC=""; last="g"
for i in $(seq 0 8); do
  set -- ${T[$i]}; d=$(num "$2-$1"); k=$((i+5))
  IN="$IN -loop 1 -framerate 30 -t $d -i $AS/cap$((i+1)).png"
  FC="$FC[$k:v]format=rgba,fade=t=in:d=0.12:alpha=1,fade=t=out:st=$(num "$d-0.15"):d=0.15:alpha=1,setpts=PTS-STARTPTS+$1/TB[c$i];
[$last][c$i]overlay=0:'30*max(0\,1-(t-$1)/0.18)':eval=frame:eof_action=pass[o$i];"
  last="o$i"
done
ms(){ echo "$1*1000/1" | bc; }
dl(){ echo "adelay=$(ms $1)|$(ms $1)"; }
BKI=14; ESI=15; AI=16   # input indices: book frames, end screen, first sfx
ffmpeg -v error -y -i joined.mkv -i $FX/boom.wav \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_far.png \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_near.png \
  -loop 1 -framerate 30 -t 3.0 -i $AS/tag.png \
  $IN \
  -framerate 30 -i $O/bk/bk_%03d.png \
  -framerate 30 -i $O/es/es_%03d.png \
  -i $FX/click.wav -i $FX/heart.wav -i $FX/drone.wav -i $FX/sting.wav -i $FX/musicbox.wav -i $FX/clicks.wav \
  -i $FX/ding.wav -i $FX/whoosh.wav -i $FX/thunder.wav -i $FX/crack.wav \
  -filter_complex "
[0:v]format=gbrp,split[gv][gg];
[gg]scale=540:960,geq=r='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),r(X,Y),0)':g='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),g(X,Y)*0.3,0)':b='0',gblur=sigma=14,scale=1080:1920[glow];
[gv][glow]blend=all_mode=screen,format=yuv420p,
eq=contrast=1.14:brightness=-0.02:saturation=0.9:gamma=1.0,
colorbalance=rs=-0.03:bs=0.05:rh=0.05:bh=-0.04,
curves=master='0/0 0.25/0.2 0.6/0.6 1/0.98',
eq=brightness='-if(lt(t,$BK),0.12*gt(random(1),0.87),0)':eval=frame,
eq=brightness='if(between(t,7.75,7.85),0.45,if(between(t,7.85,8.0),0.15,0))+if(between(t,9.5,9.58),0.3,0)+if(between(t,15.3,15.38),0.25,0)':eval=frame,
vignette=PI/4.5,noise=alls=8:allf=t,
rgbashift=rh=14:bh=-14:gv=4:enable='between(t,9.5,9.8)+between(t,15.3,15.5)+between(t,18.6,18.75)',
noise=alls=45:allf=t:enable='between(t,9.5,9.65)+between(t,15.3,15.4)',format=yuva420p[base];
[2:v]crop=1080:1920:0:'1920-mod(t*1300,1920)',format=gray[rf];
[3:v]crop=1080:1920:0:'1920-mod(t*2600,1920)',format=gray[rn];
color=c=0xF0E6D2:s=1080x1920:r=30:d=$TOTAL,format=yuva420p,split[w1][w2];
[w1][rf]alphamerge,colorchannelmixer=aa=0.3[rainf];
[w2][rn]alphamerge,colorchannelmixer=aa=0.24[rainn];
[base][rainf]overlay=0:0[r1];[r1][rainn]overlay=0:0[r2];
[4:v]format=rgba,fade=t=in:st=0:d=0.2:alpha=1,fade=t=out:st=2.6:d=0.4:alpha=1[tag];
[r2][tag]overlay=0:0:eof_action=pass[g];
$FC
[$BKI:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,setpts=PTS-STARTPTS+$BK/TB[bk];
[$last][bk]overlay=0:0:eof_action=pass[withbk];
[$ESI:v]format=rgba,setpts=PTS-STARTPTS+$ES/TB[es];
[withbk]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill:enable='gte(t,$ES)'[dim];
[dim][es]overlay=0:0:eof_action=pass,fade=t=in:st=0:d=0.3,fade=t=out:st=$(num "$TOTAL-0.3"):d=0.3,format=yuv420p[v];
[1:a]asplit=2[b1][b2];[b1]$(dl 9.5)[h1];[b2]$(dl 15.3),volume=0.8[h2];
[$AI:a]asplit[k1][k2];[k1]$(dl $(num "$ES+1.55"))[c1];[k2]$(dl $(num "$ES+2.30"))[c2];
[$((AI+1)):a]atrim=duration=3.2,$(dl 15.3),volume=1.1[hb];
[$((AI+2)):a]atrim=duration=$BK,afade=t=out:st=$(num "$BK-0.6"):d=0.6,volume=0.9[drone];
[$((AI+3)):a]$(dl 9.55),volume=0.75[st];
[$((AI+4)):a]atrim=duration=2.4,afade=t=out:st=1.8:d=0.6,$(dl 18.6),volume=0.8[mb];
[$((AI+5)):a]atrim=duration=3.2,$(dl 15.3)[cl];
[$((AI+6)):a]$(dl $(num "$BK+0.08")),volume=1.0[ding];
[$((AI+7)):a]$(dl $(num "$BK-0.35")),volume=0.8[wh];
[$((AI+8)):a]$(dl 7.75),volume=0.9[th];
[$((AI+9)):a]$(dl 9.5),volume=0.9[cr];
[0:a]volume=0.7[orig];
[orig][drone][hb][st][mb][cl][ding][wh][th][cr][h1][h2][c1][c2]amix=inputs=14:duration=first:normalize=0,alimiter=limit=0.9,afade=t=in:d=0.3,afade=t=out:st=$(num "$TOTAL-0.6"):d=0.6[a]" \
  -map [v] -map [a] -t $TOTAL -r 30 -c:v libx264 -preset slow -crf 18 -maxrate 22M -bufsize 44M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart final.mp4
