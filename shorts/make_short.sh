#!/bin/bash
set -e
U=/root/.claude/uploads/9bb01a92-4b29-5707-bc68-0c1f75e3f0c1
A=$U/b70dbb36-gemini_generated_video_75d9d257.mp4   # tram chase
B=$U/272cf377-gemini_generated_video_16a87619.mp4   # robot
O=$1; mkdir -p $O; cd $O
# seg name src start dur x0 x1 zoomFrom zoomTo speed
seg(){ n=$1 src=$2 ss=$3 d=$4 x0=$5 x1=$6 z0=$7 z1=$8 sp=${9:-1}
  sd=$(echo "$d*$sp" | bc -l)
  ffmpeg -v error -y -ss $ss -t $sd -i $src -filter_complex "
  [0:v]setpts=(PTS-STARTPTS)/$sp,fps=30,crop=405:720:'$x0+($x1-$x0)*t/$d':0,
  scale=w='1080*($z0+($z1-$z0)*t/$d)':h='1920*($z0+($z1-$z0)*t/$d)':eval=frame:flags=lanczos,
  crop=1080:1920,setsar=1,trim=duration=$d[v];
  [0:a]atempo=$sp,aresample=48000,atrim=duration=$d,afade=t=in:d=0.04,afade=t=out:st=$(echo "$d-0.06"|bc -l):d=0.06[a]" \
  -map [v] -map [a] -c:v libx264 -preset fast -crf 14 -c:a pcm_s16le $n.mkv
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

# cinematic sub-boom hits
ffmpeg -v error -y -f lavfi -i "aevalsrc='0.9*sin(2*PI*(42+40*exp(-6*t))*t)*exp(-2.2*t)':s=48000:d=2.5" -ac 2 boom.wav

F=/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf
FB=/usr/share/fonts/opentype/inter/Inter-Bold.otf
cap(){ # text start end
  local a="if(lt(t,$2+0.15),(t-$2)/0.15,if(gt(t,$3-0.15),($3-t)/0.15,1))"
  echo "drawtext=fontfile=$F:text='$1':fontsize=66:fontcolor=white:borderw=7:bordercolor=black@0.85:shadowx=0:shadowy=6:shadowcolor=black@0.5:x=(w-tw)/2:y='h*0.64+25*(1-min(1,(t-$2)/0.2))':alpha='$a':enable='between(t,$2,$3)'"
}
VF="eq=contrast=1.08:saturation=0.9:brightness=-0.01,colorbalance=rs=-0.05:bs=0.06:rh=0.07:bh=-0.04,curves=master='0/0.03 0.5/0.48 1/0.97',vignette=PI/4.5,noise=alls=7:allf=t,unsharp=5:5:0.6,
fade=t=in:st=0:d=0.5,
eq=brightness='if(between(t,6.9,7.05),0.35,if(between(t,7.05,7.25),0.12,0))':eval=frame,
$(cap 'EVERY NIGHT AT 11\:47' 0.25 2.35),
$(cap 'THE LAST TRAM ARRIVES' 2.45 4.35),
$(cap 'HE HAS WAITED 40 YEARS' 4.5 6.85),
$(cap 'BUT TONIGHT...' 6.95 8.35),
$(cap 'SOMEONE ELSE WANTS IN' 8.45 10.35),
$(cap 'NOT THIS TIME.' 10.6 13.3),
drawbox=x=0:y=0:w=iw:h=ih:color=black@0.45:t=fill:enable='gte(t,13.4)',
drawtext=fontfile=$F:text='THE LAST TRAM':fontsize=112:fontcolor=white:borderw=4:bordercolor=black@0.6:x=(w-tw)/2:y=h*0.42:alpha='min(1,(t-13.5)/0.4)':enable='gte(t,13.5)',
drawbox=x=(iw-520)/2:y=ih*0.42+150:w=460:h=5:color=0xE8B04A:t=fill:enable='gte(t,13.7)',
drawtext=fontfile=$FB:text='FOLLOW FOR PART 2':fontsize=54:fontcolor=0xE8B04A:x=(w-tw)/2:y=h*0.42+185:alpha='min(1,(t-13.8)/0.4)':enable='gte(t,13.8)',
fade=t=out:st=14.55:d=0.45"
ffmpeg -v error -y -i joined.mkv -i boom.wav -filter_complex "
[0:v]$VF[v];
[1:a]asplit[b1][b2];[b1]adelay=6900|6900[h1];[b2]adelay=13400|13400,volume=0.8[h2];
[0:a]volume=0.9[base];[base][h1][h2]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.9,afade=t=out:st=14.4:d=0.6[a]" \
-map [v] -map [a] -t 15 -c:v libx264 -preset slow -crf 17 -profile:v high -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -movflags +faststart final.mp4
