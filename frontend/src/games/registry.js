// Compile-time game registry: the backend manifest is authoritative for what is
// playable; this maps each game key to the live-view components its phases need.
// Shared shells (lobby, scoreboard, podium) stay in the platform.
import CueCastHostLive from "./cuecast/HostLive.vue";
import CueCastScreenLive from "./cuecast/ScreenLive.vue";
import CueCastPlayerLive from "./cuecast/PlayerLive.vue";
import CrowdHostLive from "./crowd_compass/HostLive.vue";
import CrowdScreenLive from "./crowd_compass/ScreenLive.vue";
import CrowdPlayerLive from "./crowd_compass/PlayerLive.vue";
import DoodleHostLive from "./doodle_dash/HostLive.vue";
import DoodleScreenLive from "./doodle_dash/ScreenLive.vue";
import DoodlePlayerLive from "./doodle_dash/PlayerLive.vue";
import RoundHostLive from "./round_games/HostLive.vue";
import RoundScreenLive from "./round_games/ScreenLive.vue";
import RoundPlayerLive from "./round_games/PlayerLive.vue";

const ROUND_KEYS = ["bluffline","sequence-sprint","picture-peek","sound-snap","caption-clash","story-loom","signal-spectrum","memory-mosaic","common-thread","escape-together","bracket-bash","closest-call","phrase-forge","seek-and-show","one-word-chorus"];

export const GAME_LIVE = {
	cuecast: { HostLive: CueCastHostLive, ScreenLive: CueCastScreenLive, PlayerLive: CueCastPlayerLive },
	"crowd-compass": {
		HostLive: CrowdHostLive,
		ScreenLive: CrowdScreenLive,
		PlayerLive: CrowdPlayerLive,
	},
	"doodle-dash": { HostLive:DoodleHostLive, ScreenLive:DoodleScreenLive, PlayerLive:DoodlePlayerLive },
};
for (const key of ROUND_KEYS) GAME_LIVE[key] = { HostLive:RoundHostLive, ScreenLive:RoundScreenLive, PlayerLive:RoundPlayerLive };

// Phases each game paints itself; everything else (scoreboard, podium, lobby) is
// the platform's.
export const GAME_PHASES = {
	cuecast: ["turn_ready", "turn_open", "turn_review"],
	"crowd-compass": ["intermission", "prompt_open", "prediction_open", "reveal"],
	"doodle-dash": ["draw_ready", "draw_open", "draw_reveal"],
};
for (const key of ROUND_KEYS) GAME_PHASES[key] = ["round_open","vote_open","round_reveal"];

export function liveFor(gameKey) {
	return GAME_LIVE[gameKey] || GAME_LIVE.cuecast;
}

export function phasesFor(gameKey) {
	return GAME_PHASES[gameKey] || GAME_PHASES.cuecast;
}

// Setup + content metadata per game for the host console and editors.
export const GAME_SETUP = {
	cuecast: {
		contentDoctype: "GP Cue Deck",
		promptDoctype: "GP Cue Prompt",
		contentLabel: "Deck",
		packField: "deck",
		editor: null,
	},
	"crowd-compass": {
		contentDoctype: "GP Crowd Pack",
		promptDoctype: "GP Crowd Prompt",
		contentLabel: "Pack",
		packField: "pack",
		editor: "crowd-compass",
	},
	"doodle-dash": { contentDoctype:"GP Draw Pack", promptDoctype:"GP Draw Prompt", contentLabel:"Pack", packField:"pack", editor:null },
};
for (const key of ROUND_KEYS) GAME_SETUP[key] = { contentDoctype:"GP Game Pack", promptDoctype:"GP Game Item", contentLabel:"Pack", packField:"pack", editor:null };
