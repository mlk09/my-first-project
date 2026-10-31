#!/bin/bash
# BOLT: The Last Tram at 11:47 – Part 5 ("The Workshop") + Amazon book promo card before the end screen.
# Usage: make.sh <out_dir>. Each Gemini upload repeats Part 2 for ~30s; the new shot is the last ~10s.
set -e
HERE=$(cd "$(dirname "$0")" && pwd); FONTS=$HERE/../v3/fonts
U=/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1
C1=${C1:-$U/f323d276-gemini_generated_video_c96d8103.mp4}   # tram at the factory, Bolt walks into the workshop
C2=${C2:-$U/2f21a677-gemini_generated_video_c591c791.mp4}   # inventor photo, tape recorder, eagle finds the red chip
C3=${C3:-$U/e3e903af-gemini_generated_video_bbfa1b65.mp4}   # robots wake, the girl in the doorway
O=$1; mkdir -p $O/assets $O/es $O/sfx $O/bk; cd $O; AS=$O/assets; FX=$O/sfx
python3 -I $HERE/captions.py $AS $FONTS
python3 -I $HERE/endscreen.py $O/es $FONTS
python3 -I $HERE/sfx.py $FX
python3 -I $HERE/bookcard.py $HERE/book_endcard.webp $O/bk $FONTS
num(){ echo "$1" | bc -l | sed 's/^\./0./; s/^-\./-0./'; }

# seg name src start out_dur zoomFrom zoomTo speed   (720x1280 source; delogo hides the Gemini sparkle)
seg(){ n=$1 src=$2 ss=$3 d=$4 z0=$5 z1=$6 sp=${7:-1}
  sd=$(num "$d*$sp")
  at="atempo=$sp"; [ $(echo "$sp < 0.5" | bc) -eq 1 ] && at="atempo=0.5,atempo=$(num "$sp/0.5")"
  ffmpeg -v error -y -ss $ss -t $sd -i $src -filter_complex "
  [0:v]delogo=x=570:y=1130:w=60:h=60,setpts=(PTS-STARTPTS)/$sp,fps=30,hqdn3d=1.2:1.2:3:3,
  scale=w='1080*($z0+($z1-$z0)*t/$d)':h='1920*($z0+($z1-$z0)*t/$d)':eval=frame:flags=lanczos,
  crop=1080:1920,cas=0.5,setsar=1,trim=duration=$d[v];
  [0:a]$at,aresample=48000,atrim=duration=$d,afade=t=in:d=0.04,afade=t=out:st=$(num "$d-0.06"):d=0.06[a]" \
  -map [v] -map [a] -c:v libx264 -preset fast -crf 12 -c:a pcm_s16le $n.mkv
}
seg a $C1 30.6 2.0 1.08 1.00          #  0.0 tram stops at the factory
seg b $C1 33.2 2.0 1.00 1.06          #  2.0 Bolt steps out
seg c $C1 36.0 1.6 1.00 1.08          #  4.0 into the workshop
seg d $C1 38.8 2.2 1.00 1.10          #  5.6 rows of robots like him
seg e $C2 32.0 2.2 1.00 1.12          #  7.8 the inventor's photo
seg f $C2 35.0 2.0 1.06 1.00          # 10.0 tape recorder
seg g $C2 37.6 2.6 1.00 1.10          # 12.0 eagle finds the red chip
seg h $C3 32.0 2.6 1.00 1.08          # 14.6 robots wake up
seg i $C3 37.0 2.0 1.00 1.06          # 17.2 the girl in the doorway
seg j $C3 39.7 2.4 1.00 1.15 0.5      # 19.2 red eyes close-up, slow
ffmpeg -v error -y -f lavfi -i color=c=black:s=1080x1920:r=30:d=5.0 -f lavfi -i anullsrc=r=48000:cl=stereo -t 5.0 \
  -c:v libx264 -preset fast -crf 12 -pix_fmt yuv420p -c:a pcm_s16le bkslot.mkv                # 21.6 book card slot
seg l $C3 39.9 3.6 1.00 1.06 0.3      # 26.6 red eyes under the end screen
printf "file '%s'\n" a.mkv b.mkv c.mkv d.mkv e.mkv f.mkv g.mkv h.mkv i.mkv j.mkv bkslot.mkv l.mkv > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c:v copy -c:a pcm_s16le joined.mkv
TOTAL=30.2; BK=21.6; ES=26.6

T=("0.15 1.95" "2.05 3.95" "4.05 5.5" "5.7 7.7" "7.9 9.9" "10.1 11.9" "12.1 14.5" "14.7 17.1" "17.3 19.1" "19.3 21.5")
IN=""; FC=""; last="g"
for i in $(seq 0 9); do
  set -- ${T[$i]}; d=$(num "$2-$1"); k=$((i+5))
  IN="$IN -loop 1 -framerate 30 -t $d -i $AS/cap$((i+1)).png"
  FC="$FC[$k:v]format=rgba,fade=t=in:d=0.12:alpha=1,fade=t=out:st=$(num "$d-0.15"):d=0.15:alpha=1,setpts=PTS-STARTPTS+$1/TB[c$i];
[$last][c$i]overlay=0:'30*max(0\,1-(t-$1)/0.18)':eval=frame:eof_action=pass[o$i];"
  last="o$i"
done
ms(){ echo "$1*1000/1" | bc; }
dl(){ echo "adelay=$(ms $1)|$(ms $1)"; }
BKI=15; ESI=16; AI=17   # input indices: book frames, end screen, first sfx
ffmpeg -v error -y -i joined.mkv -i $FX/boom.wav \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_far.png \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_near.png \
  -loop 1 -framerate 30 -t 3.0 -i $AS/tag.png \
  $IN \
  -framerate 30 -i $O/bk/bk_%03d.png \
  -framerate 30 -i $O/es/es_%03d.png \
  -i $FX/click.wav -i $FX/heart.wav -i $FX/drone.wav -i $FX/sting.wav -i $FX/musicbox.wav -i $FX/clicks.wav \
  -i $FX/ding.wav -i $FX/whoosh.wav -i $FX/thunder.wav -i $FX/crack.wav -i $FX/tape.wav -i $FX/powerup.wav \
  -filter_complex "
[0:v]format=gbrp,split[gv][gg];
[gg]scale=540:960,geq=r='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),r(X,Y),0)':g='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),g(X,Y)*0.3,0)':b='0',gblur=sigma=14,scale=1080:1920[glow];
[gv][glow]blend=all_mode=screen,format=gbrp,split[bv][bb];
[bb]scale=540:960,gblur=sigma=18,scale=1080:1920[bloom];
[bv][bloom]blend=all_mode=screen:all_opacity=0.22,format=yuv420p,
eq=contrast=1.16:brightness=-0.02:saturation=1.0:gamma=1.0,
colorbalance=rs=-0.06:gs=0.0:bs=0.08:rm=0.02:bm=-0.02:rh=0.08:gh=0.03:bh=-0.07,
curves=master='0/0 0.25/0.2 0.6/0.6 1/0.98',
eq=brightness='-if(lt(t,$BK),0.12*gt(random(1),0.87),0)':eval=frame,
eq=brightness='if(between(t,14.6,14.7),0.45,if(between(t,14.7,14.85),0.15,0))+if(between(t,17.2,17.28),0.3,0)+if(between(t,19.2,19.28),0.3,0)':eval=frame,
vignette=PI/4.5,noise=alls=8:allf=t,
rgbashift=rh=14:bh=-14:gv=4:enable='between(t,10.0,10.25)+between(t,17.2,17.45)+between(t,19.2,19.4)',
noise=alls=45:allf=t:enable='between(t,17.2,17.32)+between(t,19.2,19.3)',format=yuva420p[base];
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
[1:a]asplit=2[b1][b2];[b1]$(dl 14.6)[h1];[b2]$(dl 19.2),volume=0.85[h2];
[$AI:a]asplit[k1][k2];[k1]$(dl $(num "$ES+1.55"))[c1];[k2]$(dl $(num "$ES+2.30"))[c2];
[$((AI+1)):a]atrim=duration=3.2,$(dl 7.8),volume=1.0[hb];
[$((AI+2)):a]atrim=duration=$BK,afade=t=out:st=$(num "$BK-0.6"):d=0.6,volume=0.9[drone];
[$((AI+3)):a]$(dl 19.25),volume=0.75[st];
[$((AI+4)):a]atrim=duration=2.0,afade=t=out:st=1.4:d=0.6,$(dl 17.2),volume=0.7[mb];
[$((AI+5)):a]atrim=duration=2.6,$(dl 14.6)[cl];
[$((AI+6)):a]$(dl $(num "$BK+0.08")),volume=1.0[ding];
[$((AI+7)):a]asplit=3[w0][w1][w2];[w0]$(dl $(num "$BK-0.35")),volume=0.8[wh];[w1]$(dl 5.35),volume=0.5[wh1];[w2]$(dl 11.75),volume=0.5[wh2];
[$((AI+8)):a]$(dl 14.6),volume=0.8[th];
[$((AI+9)):a]$(dl 19.2),volume=0.7[cr];
[$((AI+10)):a]$(dl 10.0),volume=1.0[tp];
[$((AI+11)):a]$(dl 14.6),volume=0.9[pu];
[0:a]volume=0.7[orig];
[orig][drone][hb][st][mb][cl][ding][wh][wh1][wh2][th][cr][tp][pu][h1][h2][c1][c2]amix=inputs=18:duration=first:normalize=0,alimiter=limit=0.9,afade=t=in:d=0.3,afade=t=out:st=$(num "$TOTAL-0.6"):d=0.6[a]" \
  -map [v] -map [a] -t $TOTAL -r 30 -c:v libx264 -preset slow -crf 18 -maxrate 22M -bufsize 44M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart final.mp4
