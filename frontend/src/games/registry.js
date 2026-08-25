// Compile-time game registry: the backend manifest is authoritative for what is
// playable; this maps each game key to the live-view components its phases need.
// Shared shells (lobby, scoreboard, podium) stay in the platform.
import CueCastHostLive from "./cuecast/HostLive.vue";
import CueCastScreenLive from "./cuecast/ScreenLive.vue";
import CueCastPlayerLive from "./cuecast/PlayerLive.vue";
import CrowdHostLive from "./crowd_compass/HostLive.vue";
import CrowdScreenLive from "./crowd_compass/ScreenLive.vue";
import CrowdPlayerLive from "./crowd_compass/PlayerLive.vue";

export const GAME_LIVE = {
	cuecast: { HostLive: CueCastHostLive, ScreenLive: CueCastScreenLive, PlayerLive: CueCastPlayerLive },
	"crowd-compass": {
		HostLive: CrowdHostLive,
		ScreenLive: CrowdScreenLive,
		PlayerLive: CrowdPlayerLive,
	},
};

// Phases each game paints itself; everything else (scoreboard, podium, lobby) is
// the platform's.
export const GAME_PHASES = {
	cuecast: ["turn_ready", "turn_open", "turn_review"],
	"crowd-compass": ["intermission", "prompt_open", "prediction_open", "reveal"],
};

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
};
