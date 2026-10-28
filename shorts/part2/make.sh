#!/bin/bash
# The Last Tram – Part 2 (horror/suspense cut). Usage: make.sh <out_dir>   (SRC=<30s Gemini clip> to override)
set -e
HERE=$(cd "$(dirname "$0")" && pwd); FONTS=$HERE/../v3/fonts
SRC=${SRC:-/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1/f76bcbfd-gemini_generated_video_dd66a4b6.mp4}
O=$1; mkdir -p $O/assets $O/es; cd $O; AS=$O/assets
python3 -I $HERE/captions.py $AS $FONTS
python3 -I $HERE/endscreen.py $O/es $FONTS

# seg name start out_dur zoomFrom zoomTo speed   (source is already 9:16; delogo hides the Gemini sparkle)
seg(){ n=$1 ss=$2 d=$3 z0=$4 z1=$5 sp=${6:-1}
  sd=$(echo "$d*$sp" | bc -l|sed 's/^\./0./')
  at="atempo=$sp"; [ $(echo "$sp < 0.5" | bc) -eq 1 ] && at="atempo=0.5,atempo=$(echo "$sp/0.5" | bc -l|sed 's/^\./0./')"
  ffmpeg -v error -y -ss $ss -t $sd -i $SRC -filter_complex "
  [0:v]delogo=x=570:y=1130:w=60:h=60,setpts=(PTS-STARTPTS)/$sp,fps=30,hqdn3d=1.2:1.2:3:3,
  scale=w='1080*($z0+($z1-$z0)*t/$d)':h='1920*($z0+($z1-$z0)*t/$d)':eval=frame:flags=lanczos,
  crop=1080:1920,cas=0.5,setsar=1,trim=duration=$d[v];
  [0:a]$at,aresample=48000,atrim=duration=$d,afade=t=in:d=0.04,afade=t=out:st=$(echo "$d-0.06"|bc -l|sed 's/^\./0./'):d=0.06[a]" \
  -map [v] -map [a] -c:v libx264 -preset fast -crf 12 -c:a pcm_s16le $n.mkv
}
seg a 0.0  3.0 1.00 1.06          # 0.0  empty tram, eagle outside
seg b 5.0  3.5 1.00 1.12 1.3      # 3.0  push in to the red eyes
seg c 10.0 2.8 1.08 1.00          # 6.5  hunters with the hook
seg d 13.0 2.8 1.00 1.10          # 9.3  eagle dives
seg e 16.0 1.5 1.12 1.00          # 12.1 wings over headlights
seg f 18.0 1.5 1.00 1.06          # 13.6 bikers skid
seg g 21.0 2.8 1.00 1.12          # 15.1 TWIST: eagle takes the driver's seat
seg h 24.0 1.0 1.05 1.00          # 17.9 robot bows, bell
seg i 25.0 2.8 1.00 1.08          # 18.9 tram vanishes
seg j 28.0 5.0 1.00 1.15 0.399    # 21.7 ticket in the puddle (slow motion) + end screen
printf "file '%s'\n" a.mkv b.mkv c.mkv d.mkv e.mkv f.mkv g.mkv h.mkv i.mkv j.mkv > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy joined.mkv
TOTAL=26.7; ES=23.1   # end screen start (3.6s long)

# --- sound design ---
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.9*sin(2*PI*(42+40*exp(-6*t))*t)*exp(-2.2*t)':s=48000:d=2.5" -ac 2 boom.wav
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.5*sin(2*PI*1800*t)*exp(-70*t)+0.3*sin(2*PI*900*t)*exp(-40*t)':s=48000:d=0.15" -ac 2 click.wav
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.9*sin(2*PI*52*t)*exp(-18*mod(t,0.85))+0.7*sin(2*PI*46*t)*exp(-18*(mod(t,0.85)-0.24))*gte(mod(t,0.85),0.24)':s=48000:d=3.6" -ac 2 heart.wav
ffmpeg -v error -y -f lavfi -i "aevalsrc='(0.25*sin(2*PI*44*t)+0.18*sin(2*PI*46.5*t)+0.08*sin(2*PI*131*t))*(0.7+0.3*sin(2*PI*0.25*t))':s=48000:d=$TOTAL" -ac 2 drone.wav
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.5*(t/1.5)^2*sin(2*PI*(200*t+300*t*t))':s=48000:d=1.5" -ac 2 riser.wav
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.35*(sin(2*PI*1046*t)+sin(2*PI*1109*t)+0.6*sin(2*PI*523*t))*exp(-3*t)':s=48000:d=1.8" -ac 2 sting.wav

T=("0.2 2.95" "3.05 6.45" "6.55 9.25" "9.35 12.05" "12.15 15.05" "15.25 17.85" "19.0 21.65" "21.8 23.0")
IN=""; FC=""; last="g"
for i in 0 1 2 3 4 5 6 7; do
  set -- ${T[$i]}; d=$(echo "$2-$1"|bc -l|sed 's/^\./0./'); k=$((i+5))
  IN="$IN -loop 1 -framerate 30 -t $d -i $AS/cap$((i+1)).png"
  FC="$FC[$k:v]format=rgba,fade=t=in:d=0.12:alpha=1,fade=t=out:st=$(echo "$d-0.15"|bc -l|sed 's/^\./0./'):d=0.15:alpha=1,setpts=PTS-STARTPTS+$1/TB[c$i];
[$last][c$i]overlay=0:'30*max(0\,1-(t-$1)/0.18)':eval=frame:eof_action=pass[o$i];"
  last="o$i"
done
ms(){ echo "$1*1000/1" | bc; }
TL=$(echo "$ES+1.55"|bc -l|sed 's/^\./0./'); TS=$(echo "$ES+2.30"|bc -l|sed 's/^\./0./')
ffmpeg -v error -y -i joined.mkv -i boom.wav \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_far.png \
  -loop 1 -framerate 30 -t $TOTAL -i $AS/rain_near.png \
  -loop 1 -framerate 30 -t 3.0 -i $AS/tag.png \
  $IN \
  -framerate 30 -i $O/es/es_%03d.png \
  -i click.wav -i heart.wav -i drone.wav -i riser.wav -i sting.wav \
  -filter_complex "
[0:v]format=gbrp,split[gv][gg];
[gg]scale=540:960,geq=r='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),r(X,Y),0)':g='if(gt(r(X,Y),165)*lt(g(X,Y),125)*lt(b(X,Y),125),g(X,Y)*0.3,0)':b='0',gblur=sigma=14,scale=1080:1920[glow];
[gv][glow]blend=all_mode=screen,format=yuv420p,
eq=contrast=1.15:brightness=-0.02:saturation=0.88:gamma=0.99,
colorbalance=rs=-0.04:bs=0.05:rm=-0.02:bm=0.02:rh=0.05:bh=-0.04,
curves=master='0/0 0.25/0.18 0.6/0.6 1/0.97',
eq=brightness='if(between(t,0,6.5)+between(t,15.1,18.9),-0.13*gt(random(0),0.86),0)':eval=frame,
eq=brightness='if(between(t,12.1,12.22),0.45,if(between(t,12.22,12.4),0.15,0))+if(between(t,15.1,15.2),0.35,0)':eval=frame,
vignette=PI/4.2,noise=alls=9:allf=t,
rgbashift=rh=14:bh=-14:gv=4:enable='between(t,15.1,15.42)+between(t,18.9,19.2)+between(t,21.65,21.8)',
noise=alls=45:allf=t:enable='between(t,15.1,15.3)+between(t,18.9,19.05)',format=yuva420p[base];
[2:v]crop=1080:1920:0:'1920-mod(t*1300,1920)',format=gray[rf];
[3:v]crop=1080:1920:0:'1920-mod(t*2600,1920)',format=gray[rn];
color=c=0xF0E6D2:s=1080x1920:r=30:d=$TOTAL,format=yuva420p,split[w1][w2];
[w1][rf]alphamerge,colorchannelmixer=aa=0.38[rainf];
[w2][rn]alphamerge,colorchannelmixer=aa=0.32[rainn];
[base][rainf]overlay=0:0[r1];[r1][rainn]overlay=0:0[r2];
[4:v]format=rgba,fade=t=in:st=0:d=0.2:alpha=1,fade=t=out:st=2.6:d=0.4:alpha=1[tag];
[r2][tag]overlay=0:0:eof_action=pass[g];
$FC
[13:v]format=rgba,setpts=PTS-STARTPTS+$ES/TB[es];
[$last]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.6:t=fill:enable='gte(t,$ES)'[dim];
[dim][es]overlay=0:0:eof_action=pass,fade=t=in:st=0:d=0.3,fade=t=out:st=$(echo "$TOTAL-0.3"|bc -l|sed 's/^\./0./'):d=0.3,format=yuv420p[v];
[1:a]asplit=3[b1][b2][b3];[b1]adelay=$(ms 12.1)|$(ms 12.1)[h1];[b2]adelay=$(ms 15.1)|$(ms 15.1)[h2];[b3]adelay=$(ms 18.9)|$(ms 18.9),volume=0.8[h3];
[14:a]asplit[k1][k2];[k1]adelay=$(ms $TL)|$(ms $TL)[c1];[k2]adelay=$(ms $TS)|$(ms $TS)[c2];
[15:a]volume=1.1,asplit[hb1][hb2];[hb1]adelay=$(ms 3.0)|$(ms 3.0)[hb1d];[hb2]atrim=duration=1.5,adelay=$(ms 13.6)|$(ms 13.6)[hb2d];
[16:a]volume=0.8[drone];
[17:a]adelay=$(ms 13.6)|$(ms 13.6)[ris];
[18:a]adelay=$(ms 15.1)|$(ms 15.1),volume=0.7[st];
[0:a]volume=0.75[orig];
[orig][drone][hb1d][hb2d][ris][h1][h2][h3][st][c1][c2]amix=inputs=11:duration=first:normalize=0,alimiter=limit=0.9,afade=t=in:d=0.3,afade=t=out:st=$(echo "$TOTAL-0.6"|bc -l|sed 's/^\./0./'):d=0.6[a]" \
  -map [v] -map [a] -t $TOTAL -r 30 -c:v libx264 -preset slow -crf 17 -maxrate 25M -bufsize 50M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart final.mp4
