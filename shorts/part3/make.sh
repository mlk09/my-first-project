#!/bin/bash
# BOLT: The Last Tram at 11:47 – Part 3 ("The 1986 Station"). Usage: make.sh <out_dir>
# Each Gemini upload repeats Part 2 for 0–30s; the new Part 3 shot is the last ~10s of each.
set -e
HERE=$(cd "$(dirname "$0")" && pwd); FONTS=$HERE/../v3/fonts
U=/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1
C1=${C1:-$U/6b872951-gemini_generated_video_468ed55a.mp4}   # station, 11:47 clock, Bolt steps out
C2=${C2:-$U/da7b49e4-gemini_generated_video_37b14ad2.mp4}   # girl in yellow raincoat, eagle on her arm
C3=${C3:-$U/d45b2178-gemini_generated_video_b13eac58.mp4}   # lights die, tunnel of red eyes
O=$1; mkdir -p $O/assets $O/es $O/sfx; cd $O; AS=$O/assets; FX=$O/sfx
python3 -I $HERE/captions.py $AS $FONTS
python3 -I $HERE/endscreen.py $O/es $FONTS
python3 -I $HERE/sfx.py $FX
num(){ echo "$1" | bc -l | sed 's/^\./0./; s/^-\./-0./'; }

# seg name src start out_dur zoomFrom zoomTo speed   (9:16 source; delogo hides the Gemini sparkle)
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
seg a $C1 30.0 2.0 1.10 1.00          #  0.0 tram rolls out of the fog into the 1986 station
seg b $C1 34.0 1.6 1.00 1.10 0.625    #  2.0 clock frozen at 11:47
seg c $C1 36.0 2.5 1.00 1.06          #  3.6 Bolt steps out, eagle on the roof
seg d $C1 39.0 1.4 1.00 1.12 0.7      #  6.1 red eyes close-up
seg e $C2 31.0 1.8 1.00 1.06          #  7.5 the girl with the ticket
seg f $C2 33.0 1.8 1.00 1.05          #  9.3 eagle lands on her arm
seg g $C2 35.0 1.8 1.05 1.00          # 11.1 Bolt and the girl
seg h $C2 37.0 1.8 1.00 1.10          # 12.9 his eyes turn gold
seg i $C2 39.0 1.9 1.00 1.05          # 14.7 she smiles
seg j $C3 31.5 1.6 1.00 1.06          # 16.6 lights die
seg k $C3 35.0 4.0 1.00 1.12          # 18.2 tunnel of red eyes
seg l $C3 37.4 3.6 1.00 1.08 0.4      # 22.2 slow-mo army under the end screen
printf "file '%s'\n" a.mkv b.mkv c.mkv d.mkv e.mkv f.mkv g.mkv h.mkv i.mkv j.mkv k.mkv l.mkv > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy joined.mkv
TOTAL=25.8; ES=22.2; HZ=16.6   # HZ = horror section starts

T=("0.15 1.95" "2.05 3.55" "3.7 6.05" "6.15 7.45" "7.6 9.25" "9.4 11.05" "11.2 14.6" "14.8 16.5" "16.7 18.1" "18.4 20.2" "20.3 22.1")
IN=""; FC=""; last="g"
for i in $(seq 0 10); do
  set -- ${T[$i]}; d=$(num "$2-$1"); k=$((i+5))
  IN="$IN -loop 1 -framerate 30 -t $d -i $AS/cap$((i+1)).png"
  FC="$FC[$k:v]format=rgba,fade=t=in:d=0.12:alpha=1,fade=t=out:st=$(num "$d-0.15"):d=0.15:alpha=1,setpts=PTS-STARTPTS+$1/TB[c$i];
[$last][c$i]overlay=0:'30*max(0\,1-(t-$1)/0.18)':eval=frame:eof_action=pass[o$i];"
  last="o$i"
done
ms(){ echo "$1*1000/1" | bc; }
dl(){ echo "adelay=$(ms $1)|$(ms $1)"; }
ESI=16; AI=17   # input indices: end screen, first sfx
ffmpeg -v error -y -i joined.mkv -i $FX/boom.wav \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_far.png \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_near.png \
  -loop 1 -framerate 30 -t 3.0 -i $AS/tag.png \
  $IN \
  -framerate 30 -i $O/es/es_%03d.png \
  -i $FX/click.wav -i $FX/heart.wav -i $FX/drone.wav -i $FX/sting.wav -i $FX/musicbox.wav -i $FX/tick.wav -i $FX/powerdown.wav -i $FX/clicks.wav \
  -filter_complex "
[0:v]format=gbrp,split[gv][gg];
[gg]scale=540:960,geq=r='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),r(X,Y),0)':g='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),g(X,Y)*0.3,0)':b='0',gblur=sigma=14,scale=1080:1920[glow];
[gv][glow]blend=all_mode=screen,format=yuv420p,
eq=contrast=1.12:brightness=-0.01:saturation=0.95:gamma=1.0,
colorbalance=rs=-0.03:bs=0.04:rh=0.05:bh=-0.04,
curves=master='0/0 0.25/0.2 0.6/0.6 1/0.98',
eq=brightness='if(gte(t,$HZ),-0.05,0)-if(between(t,16.9,17.4),0.35*gt(random(0),0.5),0)-if(between(t,$HZ,$ES),0.12*gt(random(1),0.86),0)':contrast='if(gte(t,$HZ),1.12,1)':saturation='if(gte(t,$HZ),0.85,1)':eval=frame,
eq=brightness='if(between(t,2.0,2.1),0.25,0)+if(between(t,18.2,18.3),0.3,0)':eval=frame,
vignette=PI/4.5,noise=alls=8:allf=t,
rgbashift=rh=14:bh=-14:gv=4:enable='between(t,$HZ,16.9)+between(t,18.2,18.45)+between(t,7.5,7.62)',
noise=alls=45:allf=t:enable='between(t,$HZ,16.75)+between(t,18.2,18.32)',format=yuva420p[base];
[2:v]crop=1080:1920:0:'1920-mod(t*1300,1920)',format=gray[rf];
[3:v]crop=1080:1920:0:'1920-mod(t*2600,1920)',format=gray[rn];
color=c=0xF0E6D2:s=1080x1920:r=30:d=$TOTAL,format=yuva420p,split[w1][w2];
[w1][rf]alphamerge,colorchannelmixer=aa=0.28[rainf];
[w2][rn]alphamerge,colorchannelmixer=aa=0.22[rainn];
[base][rainf]overlay=0:0[r1];[r1][rainn]overlay=0:0[r2];
[4:v]format=rgba,fade=t=in:st=0:d=0.2:alpha=1,fade=t=out:st=2.6:d=0.4:alpha=1[tag];
[r2][tag]overlay=0:0:eof_action=pass[g];
$FC
[$ESI:v]format=rgba,setpts=PTS-STARTPTS+$ES/TB[es];
[$last]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill:enable='gte(t,$ES)'[dim];
[dim][es]overlay=0:0:eof_action=pass,fade=t=in:st=0:d=0.3,fade=t=out:st=$(num "$TOTAL-0.3"):d=0.3,format=yuv420p[v];
[1:a]asplit=2[b1][b2];[b1]$(dl 16.9)[h1];[b2]$(dl 18.2)[h2];
[$AI:a]asplit[k1][k2];[k1]$(dl $(num "$ES+1.55"))[c1];[k2]$(dl $(num "$ES+2.30"))[c2];
[$((AI+1)):a]$(dl 18.2),volume=1.1[hb];
[$((AI+2)):a]atrim=duration=$(num "$TOTAL-$HZ"),$(dl $HZ),volume=0.9[drone];
[$((AI+3)):a]$(dl 18.35),volume=0.7[st];
[$((AI+4)):a]afade=t=out:st=8.4:d=0.6,$(dl 7.4),volume=1.0[mb];
[$((AI+5)):a]$(dl 2.0)[tk];
[$((AI+6)):a]$(dl 16.85),volume=0.9[pd];
[$((AI+7)):a]$(dl 18.2)[cl];
[0:a]volume=0.7[orig];
[orig][drone][hb][st][mb][tk][pd][cl][h1][h2][c1][c2]amix=inputs=12:duration=first:normalize=0,alimiter=limit=0.9,afade=t=in:d=0.3,afade=t=out:st=$(num "$TOTAL-0.6"):d=0.6[a]" \
  -map [v] -map [a] -t $TOTAL -r 30 -c:v libx264 -preset slow -crf 18 -maxrate 22M -bufsize 44M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart final.mp4
