#!/usr/bin/env bash
set -euo pipefail

RAW="/tmp/gatherplay-video/read-room-50"
ROOT="/home/minte/projects/training-apps/apps/quizzly"
OUT="$ROOT/quizzly/public/videos/gatherplay"
VIDEO="$OUT/crowd-compass-read-room-50.mp4"
POSTER="$OUT/crowd-compass-read-room-50-poster.jpg"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

mkdir -p "$OUT"

ffmpeg -y \
	-i "$RAW/host.webm" \
	-i "$RAW/projector.webm" \
	-i "$RAW/meron.webm" \
	-i "$RAW/meron.webm" \
	-i "$RAW/projector.webm" \
	-i "$RAW/meron.webm" \
	-i "$RAW/dawit.webm" \
	-i "$RAW/hana.webm" \
	-i "$RAW/projector.webm" \
	-i "$RAW/projector.webm" \
	-i "$RAW/projector.webm" \
	-f lavfi -i anullsrc=r=48000:cl=stereo \
	-filter_complex "
		color=c=0x16111F:s=2560x1440:d=4:r=30,
		drawtext=fontfile=${FONT}:text='GATHERPLAY':fontcolor=0xE5B85C:fontsize=42:x=(w-text_w)/2:y=475,
		drawtext=fontfile=${FONT}:text='Crowd Compass':fontcolor=white:fontsize=116:x=(w-text_w)/2:y=555,
		drawtext=fontfile=${FONT}:text='READ THE ROOM 50':fontcolor=0xB9AFC7:fontsize=38:x=(w-text_w)/2:y=720,
		fade=t=in:st=0:d=0.5,fade=t=out:st=3.4:d=0.6,format=yuv420p[title];

		[0:v]trim=start=11.3:end=17.3,setpts=PTS-STARTPTS,fps=30,
		scale=2560:1440:force_original_aspect_ratio=decrease,
		pad=2560:1440:(ow-iw)/2:(oh-ih)/2:0x16111F,
		drawbox=x=0:y=1260:w=2560:h=180:color=0x16111F@0.88:t=fill,
		drawtext=fontfile=${FONT}:text='Selam sets the room in motion.':fontcolor=white:fontsize=48:x=110:y=1315,
		format=yuv420p[host];

		[1:v]trim=start=6.7:end=12.7,setpts=PTS-STARTPTS,fps=30,
		scale=2560:1440:force_original_aspect_ratio=decrease,
		pad=2560:1440:(ow-iw)/2:(oh-ih)/2:0x16111F,
		drawbox=x=0:y=1260:w=2560:h=180:color=0x16111F@0.88:t=fill,
		drawtext=fontfile=${FONT}:text='One PIN brings everyone in.':fontcolor=white:fontsize=48:x=110:y=1315,
		format=yuv420p[lobby];

		color=c=0x16111F:s=2560x1440:d=7:r=30[phonebg];
		[2:v]trim=start=1.5:end=8.5,setpts=PTS-STARTPTS,fps=30,
		scale=620:1340:force_original_aspect_ratio=decrease,
		pad=620:1340:(ow-iw)/2:(oh-ih)/2:0x211A2B[phonejoin];
		[phonebg][phonejoin]overlay=x=970:y=50,
		drawtext=fontfile=${FONT}:text='MERON':fontcolor=0xE5B85C:fontsize=46:x=190:y=430,
		drawtext=fontfile=${FONT}:text='Join from any phone.':fontcolor=white:fontsize=58:x=190:y=510,
		drawtext=fontfile=${FONT}:text='No account needed.':fontcolor=0xB9AFC7:fontsize=38:x=190:y=600,
		format=yuv420p[join];

		color=c=0x16111F:s=2560x1440:d=7:r=30[votebg];
		[3:v]trim=start=35.4:end=42.4,setpts=PTS-STARTPTS,fps=30,
		scale=620:1340:force_original_aspect_ratio=decrease,
		pad=620:1340:(ow-iw)/2:(oh-ih)/2:0x211A2B[phonevote];
		[votebg][phonevote]overlay=x=970:y=50,
		drawtext=fontfile=${FONT}:text='VOTE FOR YOURSELF':fontcolor=0xE5B85C:fontsize=44:x=145:y=470,
		drawtext=fontfile=${FONT}:text='First choice.':fontcolor=white:fontsize=58:x=145:y=555,
		drawtext=fontfile=${FONT}:text='Then a backup.':fontcolor=white:fontsize=58:x=145:y=635,
		format=yuv420p[vote];

		color=c=0x16111F:s=2560x1440:d=11:r=30[gridbg];
		[4:v]trim=start=22.8:end=33.8,setpts=PTS-STARTPTS,fps=30,scale=1450:816[stage];
		[5:v]trim=start=46.3:end=57.3,setpts=PTS-STARTPTS,fps=30,scale=300:650:force_original_aspect_ratio=decrease,pad=300:650:(ow-iw)/2:(oh-ih)/2:0x211A2B[meron];
		[6:v]trim=start=40.2:end=51.2,setpts=PTS-STARTPTS,fps=30,scale=300:650:force_original_aspect_ratio=decrease,pad=300:650:(ow-iw)/2:(oh-ih)/2:0x211A2B[dawit];
		[7:v]trim=start=33.6:end=44.6,setpts=PTS-STARTPTS,fps=30,scale=300:650:force_original_aspect_ratio=decrease,pad=300:650:(ow-iw)/2:(oh-ih)/2:0x211A2B[hana];
		[gridbg][stage]overlay=x=80:y=270[g1];
		[g1][meron]overlay=x=1580:y=440[g2];
		[g2][dawit]overlay=x=1900:y=440[g3];
		[g3][hana]overlay=x=2220:y=440,
		drawtext=fontfile=${FONT}:text='PREDICT THE ROOM':fontcolor=0xE5B85C:fontsize=42:x=80:y=100,
		drawtext=fontfile=${FONT}:text='The crowd stays hidden until everyone locks in.':fontcolor=white:fontsize=52:x=80:y=165,
		drawtext=fontfile=${FONT}:text='MERON':fontcolor=white:fontsize=24:x=1680:y=390,
		drawtext=fontfile=${FONT}:text='DAWIT':fontcolor=white:fontsize=24:x=2000:y=390,
		drawtext=fontfile=${FONT}:text='HANA':fontcolor=white:fontsize=24:x=2325:y=390,
		format=yuv420p[grid];

		[8:v]trim=start=27.5:end=38.5,setpts=PTS-STARTPTS,fps=30,
		scale=2560:1440:force_original_aspect_ratio=decrease,
		pad=2560:1440:(ow-iw)/2:(oh-ih)/2:0x16111F,
		drawbox=x=0:y=1260:w=2560:h=180:color=0x16111F@0.88:t=fill,
		drawtext=fontfile=${FONT}:text='The room reveals itself.':fontcolor=white:fontsize=48:x=110:y=1315,
		format=yuv420p[reveal];

		[9:v]trim=start=39.2:end=47.2,setpts=PTS-STARTPTS,fps=30,
		scale=2560:1440:force_original_aspect_ratio=decrease,
		pad=2560:1440:(ow-iw)/2:(oh-ih)/2:0x16111F,
		drawbox=x=0:y=1260:w=2560:h=180:color=0x16111F@0.88:t=fill,
		drawtext=fontfile=${FONT}:text='Accuracy becomes points.':fontcolor=white:fontsize=48:x=110:y=1315,
		format=yuv420p[score];

		[10:v]trim=start=47.5:end=53.5,setpts=PTS-STARTPTS,fps=30,
		scale=2560:1440:force_original_aspect_ratio=decrease,
		pad=2560:1440:(ow-iw)/2:(oh-ih)/2:0x16111F,
		drawbox=x=0:y=1260:w=2560:h=180:color=0x16111F@0.88:t=fill,
		drawtext=fontfile=${FONT}:text='Who read the room best?':fontcolor=white:fontsize=48:x=110:y=1315,
		format=yuv420p[podium];

		color=c=0x16111F:s=2560x1440:d=4:r=30,
		drawtext=fontfile=${FONT}:text='GATHERPLAY':fontcolor=0xE5B85C:fontsize=48:x=(w-text_w)/2:y=500,
		drawtext=fontfile=${FONT}:text='Bring the room together.':fontcolor=white:fontsize=88:x=(w-text_w)/2:y=600,
		drawtext=fontfile=${FONT}:text='Play Crowd Compass':fontcolor=0xB9AFC7:fontsize=38:x=(w-text_w)/2:y=750,
		fade=t=in:st=0:d=0.5,format=yuv420p[end];

		[title][host][lobby][join][vote][grid][reveal][score][podium][end]concat=n=10:v=1:a=0[outv]
	" \
	-map "[outv]" -map 11:a \
	-c:v libx264 -preset slow -crf 18 -profile:v high -level 5.1 -pix_fmt yuv420p \
	-c:a aac -b:a 192k -movflags +faststart -shortest "$VIDEO"

ffmpeg -y -ss 57 -i "$VIDEO" -frames:v 1 -q:v 2 "$POSTER"

printf '%s\n' "$VIDEO" "$POSTER"
