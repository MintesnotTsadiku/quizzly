<template>
	<div class="flex h-full flex-col bg-night">
		<header
			v-if="player && phase !== 'kicked'"
			class="flex shrink-0 items-center justify-between gap-3 border-b border-haze px-4 py-2.5"
		>
			<span class="flex min-w-0 items-center gap-2.5">
				<AvatarPic :id="player.avatar" :nickname="player.nickname" :size="30" />
				<span class="truncate font-display text-base font-bold text-paper">{{
					player.nickname
				}}</span>
			</span>
			<span class="flex items-center gap-3">
				<button
					type="button"
					class="text-lg leading-none opacity-60 transition hover:opacity-100"
					:aria-label="muted ? 'Turn sound on' : 'Turn sound off'"
					@click="toggleMute"
				>
					{{ muted ? "🔇" : "🔊" }}
				</button>
				<ThemeButton
					class="text-lg leading-none opacity-60 transition hover:opacity-100"
				/>
				<button
					v-if="phase !== 'podium'"
					type="button"
					class="rounded-full border border-haze px-3 py-1 text-xs text-paper/50 transition hover:border-ember hover:text-alert"
					@click="leave"
				>
					Leave
				</button>
			</span>
		</header>

		<main
			class="flex min-h-0 flex-1 flex-col items-center justify-center gap-6 p-6 text-center"
		>
			<template v-if="phase === 'kicked'">
				<h1 class="font-display text-3xl font-extrabold text-paper">
					The host removed you
				</h1>
				<p class="text-paper/50">You can join again with the PIN.</p>
				<button
					class="rounded-2xl bg-ember px-7 py-3 font-display text-lg font-extrabold text-sunk"
					@click="router.replace('/play/join')"
				>
					Back to join
				</button>
			</template>

			<!-- Lobby -->
			<template v-else-if="phase === 'lobby'">
				<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-accent">
					PIN {{ player.pin }}
				</p>
				<h1 class="font-display text-5xl font-extrabold text-paper">You're in</h1>
				<p v-if="myTeam" class="text-xl">
					<span class="text-paper/60">Team</span>
					<span
						class="ml-2 inline-block rounded-full px-4 py-1 font-display font-bold"
						:class="[teamStyle(myTeam.color).fill, teamStyle(myTeam.color).text]"
						>{{ myTeam.team_name }}</span
					>
				</p>
				<p class="max-w-xs text-paper/50">
					The host starts when everyone's in. Watch the big screen.
				</p>
			</template>

			<!-- The game's own phases -->
			<component
				:is="live.PlayerLive"
				v-else-if="gamePhases.includes(view.phase)"
				:view="view"
				:remaining="remaining"
				:timer-percent="timerPercent"
				:prompt="prompt"
				:solved-count="solvedCount"
				:submitting="submitting"
				:my-vote="view.my_vote"
				:my-second="view.my_second"
				:my-prediction="view.my_prediction"
				:my-estimate="view.my_estimate"
				:my-points="view.my_points"
				@act="act"
				@vote="vote"
				@predict="predict"
			/>

			<!-- Scoreboard -->
			<template v-else-if="view.phase === 'scoreboard' && standings.length">
				<h1 class="font-display text-3xl font-extrabold text-paper">Standings</h1>
				<ol class="flex w-full max-w-sm flex-col gap-2.5">
					<li
						v-for="row in standings"
						:key="row.name"
						class="flex items-center gap-3 rounded-2xl border bg-dusk px-4 py-3"
						:class="row.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-5 font-mono tabular-nums text-paper/40">{{
							row.rank
						}}</span>
						<AvatarPic
							v-if="row.avatar"
							:id="row.avatar"
							:nickname="row.team_name"
							:size="26"
						/>
						<span
							class="min-w-0 flex-1 truncate text-left font-display font-bold"
							:class="row.name === myRowId ? 'text-accent' : 'text-paper'"
						>
							{{ row.team_name
							}}<span v-if="row.name === myRowId" class="ml-1">· you</span>
						</span>
						<span
							class="font-display text-xl font-extrabold tabular-nums text-paper"
							>{{ row.score }}</span
						>
					</li>
				</ol>
			</template>

			<!-- Podium -->
			<template v-else-if="phase === 'podium'">
				<h1 class="font-display text-5xl font-extrabold leading-tight text-paper">
					{{ headline }}
				</h1>
				<ol class="flex w-full max-w-sm flex-col gap-2.5">
					<li
						v-for="row in rankedStandings"
						:key="row.name"
						class="flex items-center gap-3 rounded-2xl border bg-dusk px-4 py-3"
						:class="row.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-5 font-mono tabular-nums text-paper/40">{{
							row.rank
						}}</span>
						<AvatarPic
							v-if="row.avatar"
							:id="row.avatar"
							:nickname="row.team_name"
							:size="26"
						/>
						<span
							class="min-w-0 flex-1 truncate text-left font-display font-bold"
							:class="row.name === myRowId ? 'text-accent' : 'text-paper'"
						>
							{{ row.team_name
							}}<span v-if="row.name === myRowId" class="ml-1">· you</span>
						</span>
						<span
							class="font-display text-xl font-extrabold tabular-nums text-paper"
							>{{ row.score }}</span
						>
					</li>
				</ol>
				<button
					class="rounded-full border border-haze px-5 py-2 text-sm text-paper/60 transition hover:border-ember hover:text-alert"
					@click="router.replace('/play/join')"
				>
					Back to join
				</button>
			</template>

			<template v-else>
				<p class="font-mono text-sm uppercase tracking-[0.22em] text-paper/40">
					Hang tight…
				</p>
			</template>
		</main>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call } from "@/api";
import { useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";
import ThemeButton from "@/components/ThemeButton.vue";
import { initSound, muted, playCue, toggleMute } from "@/sound";
import {
	clearGpPlayer,
	gpCall,
	loadGpPlayer,
	saveGpPlayer,
	teamStyle,
} from "@/platform/session/gp";
import { liveFor, phasesFor } from "@/games/registry";

const socket = inject("$socket");
const route = useRoute();
const router = useRouter();
const {
	remaining,
	total: windowSeconds,
	start: startCountdown,
	stop: stopCountdown,
} = useCountdown();

let stopRoom = () => {};

const player = ref(loadGpPlayer());
const phase = ref("lobby");
const view = ref({});
const prompt = ref("");
const solvedCount = ref(0);
const submitting = ref(false);
const podium = ref(null);
let seqSeen = -1;

const gameKey = computed(() => player.value?.gameKey || "cuecast");
const live = computed(() => liveFor(gameKey.value));
const gamePhases = computed(() => phasesFor(gameKey.value));
const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
);
const myRowId = computed(() => player.value?.participant);
const standings = computed(() => view.value.teams || []);
const rankedStandings = computed(() => podium.value || standings.value);
const myTeam = computed(() =>
	(view.value.teams || []).find((t) => t.team_name === view.value.actor_team_name)
);
const headline = computed(() => {
	const mine =
		(podium.value || []).find((row) => row.name === player.value?.participant) ||
		(podium.value || []).find((row) => row.name === myTeam.value?.name);
	if (!mine) return "Final results";
	if (mine.rank === 1) return "You won! 🏆";
	return `You finished #${mine.rank}`;
});

function onEvent(message) {
	if (!message || typeof message !== "object") return;
	const type = message.type;
	const payload = message.payload || {};
	if (
		type === "platform.state_changed" ||
		type.split(".")[0] === gameKey.value.replace("-", "_")
	) {
		if (!payload.phase) return;
		view.value = { ...payload };
		podium.value = null;
		phase.value = payload.phase;
		playCue(payload.is_performer ? "correct" : "tick");
		// the private fetch returns the authoritative deadline for this phase
		stopCountdown();
		if (payload.phase === "turn_ready") startCountdown(3);
		refreshPrivate();
	} else if (type === "platform.action_progress") {
		solvedCount.value = payload.count;
	} else if (type === "platform.scoreboard_updated") {
		view.value = { ...view.value, phase: "scoreboard", teams: payload.teams };
		phase.value = "scoreboard";
		stopCountdown();
	} else if (type === "platform.session_ended") {
		podium.value = payload.teams || [];
		phase.value = "podium";
		stopCountdown();
		playCue("podium");
	} else if (
		type === "platform.participant_removed" &&
		payload.participant === player.value?.participant
	) {
		showKicked();
	}
}

async function refreshPrivate() {
	try {
		const state = await gpCall("get_player_state", {
			pin: player.value.pin,
			token: player.value.token,
		});
		applyState(state);
	} catch (e) {
		if (e.exc_type === "DoesNotExistError") {
			clearPlayerAndGo();
		}
	}
}

function applyState(state) {
	if (state.status === "Ended" || state.podium) {
		podium.value = state.podium || [];
		phase.value = "podium";
		stopCountdown();
		return;
	}
	if (state.status !== "Active") return;
	view.value = { ...state.view, teams: state.view?.teams || [] };
	phase.value = state.phase || "lobby";
	prompt.value = state.view?.prompt || "";
	solvedCount.value = state.view?.solved ?? 0;
	seqSeen = Math.max(seqSeen, state.state_version ?? 0);
	if (["turn_ready", "turn_open", "prompt_open", "prediction_open"].includes(state.phase)) {
		startCountdown(Math.max(0.5, state.remaining_seconds));
	} else {
		stopCountdown();
	}
}

function showKicked() {
	stopRoom();
	clearGpPlayer();
	stopCountdown();
	phase.value = "kicked";
}

function clearPlayerAndGo() {
	stopRoom();
	clearGpPlayer();
	router.replace("/play/join");
}

async function safeRestore() {
	try {
		await refreshPrivate();
	} catch (e) {
		if (e.exc_type === "DoesNotExistError") clearPlayerAndGo();
		else if (e.exc_type === "PermissionError") showKicked();
	}
}

onMounted(() => {
	initSound("player");
	if (!player.value || String(player.value.pin) !== String(route.params.pin)) {
		router.replace("/play/join");
		return;
	}
	stopRoom = useSessionRoom(socket, route.params.pin, onEvent, safeRestore, "gp");
	safeRestore();
});

async function act(actionType) {
	submitting.value = true;
	playCue("submit");
	try {
		const result = await call("quizzly.games.api.submit_action", {
			pin: player.value.pin,
			token: player.value.token,
			action_type: actionType,
			idempotency_key: crypto.randomUUID(),
		});
		if (result.next_prompt) prompt.value = result.next_prompt;
		else await refreshPrivate();
		solvedCount.value += actionType === "correct_prompt" ? 1 : 0;
	} catch {
		await refreshPrivate().catch(() => {});
	} finally {
		submitting.value = false;
	}
}

async function vote(payload) {
	submitting.value = true;
	playCue("submit");
	try {
		await call("quizzly.games.api.submit_action", {
			pin: player.value.pin,
			token: player.value.token,
			action_type: "cast_vote",
			idempotency_key: crypto.randomUUID(),
			payload,
		});
	} catch {
		// the resync shows the authoritative locked state
	} finally {
		submitting.value = false;
		await refreshPrivate().catch(() => {});
	}
}

async function predict(payload) {
	submitting.value = true;
	playCue("submit");
	try {
		await call("quizzly.games.api.submit_action", {
			pin: player.value.pin,
			token: player.value.token,
			action_type: "make_prediction",
			idempotency_key: crypto.randomUUID(),
			payload,
		});
	} catch {
	} finally {
		submitting.value = false;
		await refreshPrivate().catch(() => {});
	}
}

async function leave() {
	try {
		await gpCall("leave_session", { pin: player.value.pin, token: player.value.token });
	} catch {
		// leaving anyway
	}
	clearPlayerAndGo();
}
</script>
