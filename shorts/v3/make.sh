#!/bin/bash
# The Last Tram v3: golden scene, green tram, orange robot with red eyes, animated subscribe end screen.
# Usage: make.sh <out_dir>      (set CLIP_A / CLIP_B to the two source clips if they live elsewhere)
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
U=/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1
A=${CLIP_A:-$U/b70dbb36-gemini_generated_video_75d9d257.mp4}   # tram chase
B=${CLIP_B:-$U/272cf377-gemini_generated_video_16a87619.mp4}   # robot
O=$1; mkdir -p $O/assets $O/es; cd $O
AS=$O/assets
python3 -I $HERE/thumb_recolor.py $HERE/thumb_frame.png $O/thumb_rc.png
python3 -I $HERE/assets.py $AS $HERE/fonts $O/thumb_rc.png
python3 -I $HERE/endscreen.py $O/es $HERE/fonts

# seg name src start dur x0 x1 zoomFrom zoomTo speed
seg(){ n=$1 src=$2 ss=$3 d=$4 x0=$5 x1=$6 z0=$7 z1=$8 sp=${9:-1}
  sd=$(echo "$d*$sp" | bc -l)
  ffmpeg -v error -y -ss $ss -t $sd -i $src -filter_complex "
  [0:v]setpts=(PTS-STARTPTS)/$sp,fps=30,hqdn3d=1.5:1.5:3:3,crop=405:720:'$x0+($x1-$x0)*t/$d':0,
  scale=w='1080*($z0+($z1-$z0)*t/$d)':h='1920*($z0+($z1-$z0)*t/$d)':eval=frame:flags=lanczos,
  crop=1080:1920,cas=0.55,setsar=1,trim=duration=$d[v];
  [0:a]atempo=$sp,aresample=48000,atrim=duration=$d,afade=t=in:d=0.04,afade=t=out:st=$(echo "$d-0.06"|bc -l):d=0.06[a]" \
  -map [v] -map [a] -c:v libx264 -preset fast -crf 10 -c:a pcm_s16le $n.mkv
}
seg s1 $B 0.0  2.4 250 250 1.00 1.08
seg s2 $A 1.5  2.0 380 380 1.10 1.00
seg s3 $B 4.0  2.5 220 220 1.00 1.07
seg s4 $A 4.8  1.5 180 180 1.12 1.00
seg s5 $A 7.0  2.0 120 330 1.00 1.06
seg s6 $B 10.8 3.0 270 440 1.00 1.05
seg s7 $B 16.5 3.6 330 330 1.00 1.10 0.75
printf "file '%s'\n" s1.mkv s2.mkv s3.mkv s4.mkv s5.mkv s6.mkv s7.mkv > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy joined.mkv

# per-frame recolour (golden light, green tram, orange robot + red eyes)
[ -f recolored.mkv ] || python3 -I $HERE/process.py joined.mkv recolored.mkv $DEBUG_DIR

ffmpeg -v error -y -f lavfi -i "aevalsrc='0.9*sin(2*PI*(42+40*exp(-6*t))*t)*exp(-2.2*t)':s=48000:d=2.5" -ac 2 boom.wav
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.5*sin(2*PI*1800*t)*exp(-70*t)+0.3*sin(2*PI*900*t)*exp(-40*t)':s=48000:d=0.15" -ac 2 click.wav

T=("0.25 2.35" "2.45 4.35" "4.5 6.85" "6.95 8.35" "8.45 10.35" "10.6 13.3")
IN=""; FC=""; last="g"
for i in 0 1 2 3 4 5; do
  set -- ${T[$i]}; d=$(echo "$2-$1"|bc -l); k=$((i+4))
  IN="$IN -loop 1 -framerate 30 -t $d -i $AS/cap$((i+1)).png"
  FC="$FC[$k:v]format=rgba,fade=t=in:d=0.15:alpha=1,fade=t=out:st=$(echo "$d-0.15"|bc -l):d=0.15:alpha=1,setpts=PTS-STARTPTS+$1/TB[c$i];
[$last][c$i]overlay=0:'30*max(0\,1-(t-$1)/0.2)':eval=frame:eof_action=pass[o$i];"
  last="o$i"
done
TL=$(echo "13.4+1.55"|bc -l); TS=$(echo "13.4+2.30"|bc -l)
ffmpeg -v error -y -i recolored.mkv -i boom.wav \
  -loop 1 -framerate 30 -t 17 -i $AS/rain_far.png \
  -loop 1 -framerate 30 -t 17 -i $AS/rain_near.png \
  $IN \
  -framerate 30 -i $O/es/es_%03d.png \
  -f lavfi -t 17 -i "anoisesrc=color=pink:sample_rate=48000:seed=7" \
  -i click.wav \
  -filter_complex "
[0:v]eq=brightness=0.05:contrast=1.12:saturation=1.12:gamma=1.10,
colorbalance=rs=0.03:bs=-0.04:rm=0.04:bm=-0.05:rh=0.06:gh=0.03:bh=-0.06,
vignette=PI/7,
eq=brightness='if(between(t,6.9,7.05),0.4,if(between(t,7.05,7.3),0.15,0))':eval=frame,format=yuva420p[base];
[2:v]crop=1080:1920:0:'1920-mod(t*1300,1920)',format=gray[rf];
[3:v]crop=1080:1920:0:'1920-mod(t*2600,1920)',format=gray[rn];
color=c=0xF4EAD8:s=1080x1920:r=30:d=17,format=yuva420p,split[w1][w2];
[w1][rf]alphamerge,colorchannelmixer=aa=0.5[rainf];
[w2][rn]alphamerge,colorchannelmixer=aa=0.4[rainn];
[base][rainf]overlay=0:0[r1];[r1][rainn]overlay=0:0[g];
$FC
[10:v]format=rgba,setpts=PTS-STARTPTS+13.4/TB[es];
[$last]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill:enable='gte(t,13.4)'[dim];
[dim][es]overlay=0:0:eof_action=pass,fade=t=in:st=0:d=0.4,fade=t=out:st=16.7:d=0.3,format=yuv420p[v];
[11:a]highpass=f=500,lowpass=f=9000,volume=0.16,aformat=channel_layouts=stereo[rain];
[1:a]asplit[b1][b2];[b1]adelay=6900|6900[h1];[b2]adelay=13400|13400,volume=0.8[h2];
[12:a]asplit[k1][k2];[k1]adelay=$(echo "$TL*1000"|bc|cut -d. -f1)|$(echo "$TL*1000"|bc|cut -d. -f1)[c1];[k2]adelay=$(echo "$TS*1000"|bc|cut -d. -f1)|$(echo "$TS*1000"|bc|cut -d. -f1)[c2];
[0:a]volume=0.9[orig];[orig][rain][h1][h2][c1][c2]amix=inputs=6:duration=first:normalize=0,alimiter=limit=0.9,afade=t=in:d=0.3,afade=t=out:st=16.4:d=0.6[a]" \
  -map [v] -map [a] -t 17 -r 30 -c:v libx264 -preset slow -crf 17 -maxrate 25M -bufsize 50M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart final.mp4
