#!/bin/bash
# Standalone recut of Part 4 for the Shorts feed: hook on frame one, no part tag, no book card,
# ~19 s, and a last shot that loops back into the first. Usage: make.sh <out_dir>
set -e
HERE=$(cd "$(dirname "$0")" && pwd); FONTS=$HERE/../v3/fonts
U=/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1
C1=${C1:-$U/475f2493-vid01.mp4}   # robot army kneels to the girl
C2=${C2:-$U/caed3e1b-vid02.mp4}   # lightning reflection, porcelain face cracks
C3=${C3:-$U/c2f77141-vid03.mp4}   # eagle picks Bolt, run to the tram, girl in the window
O=$1; mkdir -p $O/assets $O/sfx; cd $O; AS=$O/assets; FX=$O/sfx
python3 -I $HERE/captions.py $AS $FONTS
python3 -I $HERE/sfx.py $FX
num(){ echo "$1" | bc -l | sed 's/^\./0./; s/^-\./-0./'; }
seg(){ n=$1 src=$2 ss=$3 d=$4 z0=$5 z1=$6 sp=${7:-1}
  sd=$(num "$d*$sp")
  ffmpeg -v error -y -ss $ss -t $sd -i $src -filter_complex "
  [0:v]delogo=x=384:y=765:w=36:h=36,setpts=(PTS-STARTPTS)/$sp,fps=30,hqdn3d=1.5:1.5:3:3,
  scale=w='1080*($z0+($z1-$z0)*t/$d)':h='1920*($z0+($z1-$z0)*t/$d)':eval=frame:flags=lanczos,
  crop=1080:1920,cas=0.6,setsar=1,trim=duration=$d[v];
  [0:a]atempo=$sp,aresample=48000,atrim=duration=$d,afade=t=in:d=0.04,afade=t=out:st=$(num "$d-0.06"):d=0.06[a]" \
  -map [v] -map [a] -c:v libx264 -preset fast -crf 12 -c:a pcm_s16le $n.mkv
}
seg a $C2 36.6 1.5 1.10 1.02          #  0.0 HOOK: half-cracked face, red eye
seg b $C1 30.6 1.6 1.00 1.08          #  1.5 army comes out of the dark
seg c $C1 35.4 2.0 1.06 1.00          #  3.1 robots bow
seg d $C1 39.2 1.5 1.00 1.10          #  5.1 she raises the ticket
seg e $C2 32.4 1.8 1.00 1.08          #  6.6 lightning: her reflection is a robot
seg f $C2 35.0 2.4 1.00 1.10 0.8      #  8.4 the face cracks
seg g $C3 31.0 2.0 1.00 1.05          # 10.8 eagle lands on Bolt
seg h $C3 34.7 2.4 1.00 1.06          # 12.8 run for the tram
seg i $C3 38.7 2.2 1.00 1.10          # 15.2 girl alone in the window
seg j $C2 34.75 1.3 1.02 1.12         # 17.4 LOOP: her face just before it cracks -> back to frame one
printf "file '%s'\n" a.mkv b.mkv c.mkv d.mkv e.mkv f.mkv g.mkv h.mkv i.mkv j.mkv > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy joined.mkv
TOTAL=18.7

T=("0.0 1.45" "1.6 3.0" "3.2 5.0" "5.2 6.5" "6.7 8.3" "8.5 10.7" "10.9 12.7" "12.9 15.1" "15.3 17.3" "17.45 18.7")
IN=""; FC=""; last="g"
for i in $(seq 0 9); do
  set -- ${T[$i]}; d=$(num "$2-$1"); k=$((i+4))
  fi="fade=t=in:d=0.12:alpha=1,"; [ $i -eq 0 ] && fi=""      # the hook caption is on the very first frame
  IN="$IN -loop 1 -framerate 30 -t $d -i $AS/cap$((i+1)).png"
  FC="$FC[$k:v]format=rgba,${fi}fade=t=out:st=$(num "$d-0.12"):d=0.12:alpha=1,setpts=PTS-STARTPTS+$1/TB[c$i];
[$last][c$i]overlay=0:'24*max(0\,1-(t-$1)/0.15)*gt($1\,0)':eval=frame:eof_action=pass[o$i];"
  last="o$i"
done
ms(){ echo "$1*1000/1" | bc; }
dl(){ echo "adelay=$(ms $1)|$(ms $1)"; }
AI=14
ffmpeg -v error -y -i joined.mkv -i $FX/boom.wav \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_far.png \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_near.png \
  $IN \
  -i $FX/heart.wav -i $FX/drone.wav -i $FX/sting.wav -i $FX/musicbox.wav -i $FX/clicks.wav -i $FX/whoosh.wav -i $FX/thunder.wav -i $FX/crack.wav \
  -filter_complex "
[0:v]format=gbrp,split[gv][gg];
[gg]scale=540:960,geq=r='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),r(X,Y),0)':g='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),g(X,Y)*0.3,0)':b='0',gblur=sigma=14,scale=1080:1920[glow];
[gv][glow]blend=all_mode=screen,format=gbrp,split[bv][bb];
[bb]scale=540:960,gblur=sigma=18,scale=1080:1920[bloom];
[bv][bloom]blend=all_mode=screen:all_opacity=0.2,format=yuv420p,
eq=contrast=1.15:brightness=-0.01:saturation=0.95:gamma=1.0,
colorbalance=rs=-0.05:bs=0.07:rh=0.07:gh=0.03:bh=-0.06,
curves=master='0/0 0.25/0.2 0.6/0.6 1/0.98',
eq=brightness='-0.1*gt(random(1),0.88)':eval=frame,
eq=brightness='if(between(t,6.6,6.7),0.45,if(between(t,6.7,6.85),0.15,0))+if(between(t,8.4,8.48),0.3,0)+if(between(t,12.8,12.86),0.25,0)':eval=frame,
vignette=PI/4.5,noise=alls=8:allf=t,
rgbashift=rh=14:bh=-14:gv=4:enable='between(t,0,0.25)+between(t,8.4,8.7)+between(t,12.8,13.0)+between(t,17.4,17.55)',
noise=alls=45:allf=t:enable='between(t,0,0.12)+between(t,8.4,8.55)',format=yuva420p[base];
[2:v]crop=1080:1920:0:'1920-mod(t*1300,1920)',format=gray[rf];
[3:v]crop=1080:1920:0:'1920-mod(t*2600,1920)',format=gray[rn];
color=c=0xF0E6D2:s=1080x1920:r=30:d=$TOTAL,format=yuva420p,split[w1][w2];
[w1][rf]alphamerge,colorchannelmixer=aa=0.3[rainf];
[w2][rn]alphamerge,colorchannelmixer=aa=0.24[rainn];
[base][rainf]overlay=0:0[r1];[r1][rainn]overlay=0:0[g];
$FC
[$last]format=yuv420p[v];
[1:a]asplit=3[b0][b1][b2];[b0]volume=0.9[h0];[b1]$(dl 8.4)[h1];[b2]$(dl 12.8),volume=0.8[h2];
[$AI:a]atrim=duration=2.4,$(dl 12.8),volume=1.1[hb];
[$((AI+1)):a]atrim=duration=$TOTAL,volume=0.9[drone];
[$((AI+2)):a]asplit[s0][s1];[s0]volume=0.6[st0];[s1]$(dl 8.45),volume=0.75[st];
[$((AI+3)):a]atrim=duration=3.4,afade=t=out:st=2.6:d=0.8,$(dl 15.2),volume=0.8[mb];
[$((AI+4)):a]atrim=duration=2.4,$(dl 12.8)[cl];
[$((AI+5)):a]asplit=2[w1a][w2a];[w1a]$(dl 1.3),volume=0.5[wh1];[w2a]$(dl 10.55),volume=0.5[wh2];
[$((AI+6)):a]$(dl 6.6),volume=0.9[th];
[$((AI+7)):a]asplit[k0][k1];[k0]volume=0.8[cr0];[k1]$(dl 8.4),volume=0.9[cr];
[0:a]volume=0.7[orig];
[orig][drone][hb][st0][st][mb][cl][wh1][wh2][th][cr0][cr][h0][h1][h2]amix=inputs=15:duration=first:normalize=0,alimiter=limit=0.9[a]" \
  -map [v] -map [a] -t $TOTAL -r 30 -c:v libx264 -preset slow -crf 18 -maxrate 22M -bufsize 44M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart final.mp4
