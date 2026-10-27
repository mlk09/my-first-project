#!/bin/bash
# Usage: make.sh <out_dir> <assets_dir>   (assets from assets.py)
set -e
U=/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1
A=$U/b70dbb36-gemini_generated_video_75d9d257.mp4   # tram chase
B=$U/272cf377-gemini_generated_video_16a87619.mp4   # robot
O=$1; AS=$2; mkdir -p $O; cd $O
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
seg s7 $B 16.5 1.6 330 330 1.00 1.06 0.75
printf "file '%s'\n" s1.mkv s2.mkv s3.mkv s4.mkv s5.mkv s6.mkv s7.mkv > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy joined.mkv
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.9*sin(2*PI*(42+40*exp(-6*t))*t)*exp(-2.2*t)':s=48000:d=2.5" -ac 2 boom.wav

# caption timings: start end
T=("0.25 2.35" "2.45 4.35" "4.5 6.85" "6.95 8.35" "8.45 10.35" "10.6 13.3")
IN=""; FC=""; last="g"
for i in 0 1 2 3 4 5; do
  set -- ${T[$i]}; d=$(echo "$2-$1"|bc -l); k=$((i+5))
  IN="$IN -loop 1 -framerate 30 -t $d -i $AS/cap$((i+1)).png"
  FC="$FC[$k:v]format=rgba,fade=t=in:d=0.15:alpha=1,fade=t=out:st=$(echo "$d-0.15"|bc -l):d=0.15:alpha=1,setpts=PTS-STARTPTS+$1/TB[c$i];
[$last][c$i]overlay=0:'30*max(0\,1-(t-$1)/0.2)':eval=frame:eof_action=pass[o$i];"
  last="o$i"
done

ffmpeg -v error -y -i joined.mkv -i boom.wav \
  -loop 1 -framerate 30 -t 15 -i $AS/rain_far.png \
  -loop 1 -framerate 30 -t 15 -i $AS/rain_near.png \
  -loop 1 -framerate 30 -t 1.6 -i $AS/endcard.png \
  $IN \
  -f lavfi -t 15 -i "anoisesrc=color=pink:sample_rate=48000:seed=7" \
  -loop 1 -framerate 30 -t 1.25 -i $AS/endcta.png \
  -filter_complex "
[0:v]eq=brightness=0.06:contrast=1.10:saturation=1.22:gamma=1.18,
colorbalance=bs=0.04:rh=0.06:gh=0.02:bh=-0.03,
vignette=PI/7,
eq=brightness='if(between(t,6.9,7.05),0.4,if(between(t,7.05,7.3),0.15,0))':eval=frame,format=yuva420p[base];
[2:v]crop=1080:1920:0:'1920-mod(t*1300,1920)',format=gray[rf];
[3:v]crop=1080:1920:0:'1920-mod(t*2600,1920)',format=gray[rn];
color=c=0xE6EEF5:s=1080x1920:r=30:d=15,format=yuva420p,split[w1][w2];
[w1][rf]alphamerge,colorchannelmixer=aa=0.55[rainf];
[w2][rn]alphamerge,colorchannelmixer=aa=0.45[rainn];
[base][rainf]overlay=0:0[r1];[r1][rainn]overlay=0:0[g];
$FC
[4:v]format=rgba,fade=t=in:d=0.4:alpha=1,setpts=PTS-STARTPTS+13.4/TB[ec];
[$last]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.5:t=fill:enable='gte(t,13.4)'[dim];
[12:v]format=rgba,fade=t=in:d=0.25:alpha=1,setpts=PTS-STARTPTS+13.75/TB[cta];
[dim][ec]overlay=0:0:eof_action=pass[ec2];
[ec2][cta]overlay=0:'40*max(0\,1-(t-13.75)/0.25)':eval=frame:eof_action=pass,fade=t=in:st=0:d=0.4,fade=t=out:st=14.8:d=0.2,format=yuv420p[v];
[11:a]highpass=f=500,lowpass=f=9000,volume=0.16,aformat=channel_layouts=stereo[rain];
[1:a]asplit[b1][b2];[b1]adelay=6900|6900[h1];[b2]adelay=13400|13400,volume=0.8[h2];
[0:a]volume=0.9[orig];[orig][rain][h1][h2]amix=inputs=4:duration=first:normalize=0,alimiter=limit=0.9,afade=t=in:d=0.3,afade=t=out:st=14.4:d=0.6[a]" \
  -map [v] -map [a] -t 15 -r 30 -c:v libx264 -preset slow -crf 16 -maxrate 30M -bufsize 60M -profile:v high -level 4.2 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart final.mp4
