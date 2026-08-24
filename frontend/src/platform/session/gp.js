import { computed } from "vue";
import { call } from "@/api";

const PLAYER_KEY = "gp_player";
const SESSION_KEY = "gp_hosted_session";

// Team colors come from one backend constant (games.engine.TEAM_COLORS); every hue
// maps onto the app's fixed answer-ink tokens so nothing here invents a colour.
export const TEAM_STYLE = {
	ember: { fill: "bg-ember", border: "border-ember", text: "text-sunk", ink: "text-alert" },
	lagoon: { fill: "bg-lagoon", border: "border-lagoon", text: "text-sunk", ink: "text-ok" },
	gold: { fill: "bg-gold", border: "border-gold", text: "text-sunk", ink: "text-accent" },
	orchid: { fill: "bg-orchid", border: "border-orchid", text: "text-sunk", ink: "text-orchid" },
};

export function teamStyle(color) {
	return TEAM_STYLE[color] || TEAM_STYLE.ember;
}

export function saveGpPlayer(joinResult) {
	localStorage.setItem(
		PLAYER_KEY,
		JSON.stringify({
			token: joinResult.participant_token,
			participant: joinResult.participant,
			nickname: joinResult.nickname,
			avatar: joinResult.avatar,
			pin: joinResult.game_pin,
			gameKey: joinResult.game_key,
			participants: joinResult.participants,
		})
	);
}

export function loadGpPlayer() {
	try {
		return JSON.parse(localStorage.getItem(PLAYER_KEY));
	} catch {
		return null;
	}
}

export function clearGpPlayer() {
	localStorage.removeItem(PLAYER_KEY);
}

export function rememberHostedSession(name) {
	localStorage.setItem(SESSION_KEY, name);
}

export function forgetHostedSession() {
	localStorage.removeItem(SESSION_KEY);
}

export function loadHostedSession() {
	return localStorage.getItem(SESSION_KEY);
}

/** Envelope guard: drop stale deliveries, surface the payload. */
export function envelope(message) {
	if (!message || typeof message !== "object" || !message.type) return null;
	return message;
}

export function listGames() {
	return call("quizzly.games.api.list_games");
}

export function gpCall(method, params = {}) {
	return call(`quizzly.games.api.${method}`, params);
}

export function formatRemaining(seconds) {
	const s = Math.max(0, Math.ceil(seconds));
	return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}
