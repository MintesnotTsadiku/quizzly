#!/usr/bin/env bash
set -euo pipefail

output="quizzly/public/videos/gatherplay"
mkdir -p "$output"

render() {
	local key="$1" source="$2"
	ffmpeg -hide_banner -loglevel error -y -loop 1 -i "$source" -t 8 \
		-vf "scale=2560:1707,crop=2560:1440:0:'min(267,t*22)',fade=t=in:st=0:d=0.35,fade=t=out:st=7.4:d=0.6" \
		-r 30 -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -movflags +faststart -an \
		"$output/$key-overview.mp4"
	ffmpeg -hide_banner -loglevel error -y -ss 0.8 -i "$output/$key-overview.mp4" -frames:v 1 -q:v 2 "$output/$key-overview-poster.jpg"
}

root=/tmp/agent_browser_qa/quizzly
render quiz "$root/quizzly-gatherplay-catalog-20260825T220740Z/play.png"
render cuecast "$root/quizzly-gatherplay-game-detail-20260825T220744Z/play-games-cuecast.png"
render doodle-dash "$root/quizzly-doodle-dash-game-detail-20260825T220752Z/play-games-doodle-dash.png"

creative="$root/quizzly-remaining-game-guides-creative-20260825T220800Z"
render bluffline "$creative/play-games-bluffline.png"
render sequence-sprint "$creative/play-games-sequence-sprint.png"
render picture-peek "$creative/play-games-picture-peek.png"
render sound-snap "$creative/play-games-sound-snap.png"
render caption-clash "$creative/play-games-caption-clash.png"
render story-loom "$creative/play-games-story-loom.png"
render common-thread "$creative/play-games-common-thread.png"

puzzles="$root/quizzly-remaining-game-guides-puzzles-20260825T220810Z"
render signal-spectrum "$puzzles/play-games-signal-spectrum.png"
render memory-mosaic "$puzzles/play-games-memory-mosaic.png"
render escape-together "$puzzles/play-games-escape-together.png"
render phrase-forge "$puzzles/play-games-phrase-forge.png"
render seek-and-show "$puzzles/play-games-seek-and-show.png"

room="$root/quizzly-remaining-game-guides-room-20260825T220818Z"
render bracket-bash "$room/play-games-bracket-bash.png"
render closest-call "$room/play-games-closest-call.png"
render one-word-chorus "$room/play-games-one-word-chorus.png"
