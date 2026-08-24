<template>
	<div class="flex h-full flex-col bg-night">
		<header
			v-if="player && phase !== 'kicked'"
			class="flex shrink-0 items-center justify-between gap-3 border-b border-haze px-4 py-2.5"
		>
			<span class="flex min-w-0 items-center gap-2.5">
				<AvatarPic :id="player.avatar" :nickname="player.nickname" :size="30" />
				<span class="truncate font-display text-base font-bold text-paper">{{ player.nickname }}</span>
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
				<ThemeButton class="text-lg leading-none opacity-60 transition hover:opacity-100" />
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

		<main class="flex min-h-0 flex-1 flex-col items-center justify-center gap-6 p-6 text-center">
			<template v-if="phase === 'kicked'">
				<h1 class="font-display text-3xl font-extrabold text-paper">The host removed you</h1>
				<p class="text-paper/50">You can join again with the PIN.</p>
				<button
					class="rounded-2xl bg-ember px-7 py-3 font-display text-lg font-extrabold text-sunk"
					@click="router.replace('/play/join')"
				>Back to join</button>
			</template>

			<!-- Lobby -->
			<template v-else-if="phase === 'lobby'">
				<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-accent">PIN {{ player.pin }}</p>
				<h1 class="font-display text-5xl font-extrabold text-paper">You're in</h1>
				<p v-if="myTeam" class="text-xl">
					<span class="text-paper/60">Team</span>
					<span
						class="ml-2 inline-block rounded-full px-4 py-1 font-display font-bold"
						:class="[teamStyle(myTeam.color).fill, teamStyle(myTeam.color).text]"
					>{{ myTeam.team_name }}</span>
				</p>
				<p class="max-w-xs text-paper/50">
					The host starts when every team has players. Watch the big screen.
				</p>
			</template>

			<!-- Performer ready -->
			<template v-else-if="view.phase === 'turn_ready' && view.is_performer">
				<p class="font-mono uppercase tracking-[0.28em] text-accent">You're up</p>
				<h1 class="font-display text-4xl font-extrabold leading-tight text-paper">
					Get ready to act!
				</h1>
				<p class="text-paper/50">{{ view.mode }} mode · {{ teamName }}</p>
				<div class="relative grid h-40 w-40 place-items-center rounded-full bg-dusk">
					<DrainRing :percent="timerPercent" :seconds="Math.ceil(remaining)" :size="150" color="rgb(var(--accent))" />
					<span class="absolute font-display text-5xl font-extrabold tabular-nums text-paper">
						{{ Math.ceil(remaining) }}
					</span>
				</div>
				<p class="text-sm text-paper/40">Look up — your first word lands in a second.</p>
			</template>

			<!-- Performer live: the only screen that knows the word -->
			<template v-else-if="view.phase === 'turn_open' && view.is_performer">
				<div class="flex w-full items-center justify-between px-2">
					<span class="font-mono text-xs uppercase tracking-[0.22em] text-paper/45">Solved {{ solvedCount }}</span>
					<DrainRing :percent="timerPercent" :seconds="Math.ceil(remaining)" :size="56" :color="urgentColor" />
				</div>
				<p class="mt-2 max-w-md break-words font-display text-5xl font-extrabold leading-tight text-paper sm:text-6xl">
					{{ prompt }}
				</p>
				<p class="-mt-3 font-mono uppercase tracking-widest text-paper/35">{{ view.mode }} mode · no letters!</p>
				<div class="grid w-full max-w-md grid-cols-2 gap-3">
					<button
						class="flex flex-col items-center gap-2 rounded-3xl bg-lagoon py-8 font-display text-2xl font-extrabold text-sunk transition active:scale-95"
						:disabled="submitting"
						@click="act('correct_prompt')"
					>
						<span class="text-4xl">✓</span> Solved it
					</button>
					<button
						class="flex flex-col items-center gap-2 rounded-3xl bg-gold py-8 font-display text-2xl font-extrabold text-sunk transition active:scale-95"
						:disabled="submitting"
						@click="act('pass_prompt')"
					>
						<span class="text-4xl">»</span> Pass
					</button>
				</div>
			</template>

			<!-- On stage but waiting / watching -->
			<template v-else-if="['turn_ready', 'turn_open'].includes(view.phase)">
				<p class="font-mono uppercase tracking-[0.28em] text-accent">
					{{ view.phase === "turn_ready" ? "Get ready" : "On stage" }}
				</p>
				<div class="flex items-center gap-4">
					<AvatarPic :id="view.performer?.avatar" :nickname="view.performer?.nickname" :size="64" />
					<div class="text-left">
						<p class="font-display text-2xl font-bold text-paper">{{ view.performer?.nickname }}</p>
						<p class="text-paper/50">{{ teamName }} is performing</p>
					</div>
				</div>
				<p v-if="view.phase === 'turn_open'" class="font-display text-7xl font-extrabold tabular-nums text-accent">
					{{ solvedCount }}
				</p>
				<p v-if="view.phase === 'turn_open'" class="-mt-3 text-paper/40">solved so far</p>
			</template>

			<!-- Review -->
			<template v-else-if="view.phase === 'turn_review'">
				<h1 class="font-display text-4xl font-extrabold text-paper">
					{{ solvedCount }} solved!
				</h1>
				<p class="max-w-xs text-paper/50">
					Check the big screen for the words — then the scoreboard moves.
				</p>
			</template>

			<!-- Scoreboard -->
			<template v-else-if="view.phase === 'scoreboard' && myTeam">
				<h1 class="font-display text-3xl font-extrabold text-paper">Standings</h1>
				<ol class="w-full max-w-sm flex flex-col gap-2.5">
					<li
						v-for="team in rankedTeams"
						:key="team.name"
						class="flex items-center gap-3 rounded-2xl border bg-dusk px-4 py-3"
						:class="[team.rank === 1 ? 'border-accent' : 'border-haze']"
					>
						<span class="w-5 font-mono tabular-nums text-paper/40">{{ team.rank }}</span>
						<span
							class="min-w-0 flex-1 truncate text-left font-display font-bold"
							:class="team.name === myTeam.name ? 'text-accent' : 'text-paper'"
						>
							{{ team.team_name }}<span v-if="team.name === myTeam.name" class="ml-1">· you</span>
						</span>
						<span class="font-display text-xl font-extrabold tabular-nums text-paper">{{ team.score }}</span>
					</li>
				</ol>
			</template>

			<!-- Podium -->
			<template v-else-if="phase === 'podium'">
				<h1 class="font-display text-5xl font-extrabold leading-tight text-paper">
					{{ headline }}
				</h1>
				<ol class="w-full max-w-sm flex flex-col gap-2.5">
					<li
						v-for="team in rankedTeams"
						:key="team.name"
						class="flex items-center gap-3 rounded-2xl border bg-dusk px-4 py-3"
						:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-5 font-mono tabular-nums text-paper/40">{{ team.rank }}</span>
						<span class="min-w-0 flex-1 truncate text-left font-display font-bold"
							:class="team.name === myTeam?.name ? 'text-accent' : 'text-paper'">
							{{ team.team_name }}<span v-if="team.name === myTeam?.name" class="ml-1">· you</span>
						</span>
						<span class="font-display text-xl font-extrabold tabular-nums text-paper">{{ team.score }}</span>
					</li>
				</ol>
				<button
					class="rounded-full border border-haze px-5 py-2 text-sm text-paper/60 transition hover:border-ember hover:text-alert"
					@click="router.replace('/play/join')"
				>Back to join</button>
			</template>

			<template v-else>
				<p class="font-mono text-sm uppercase tracking-[0.22em] text-paper/40">Hang tight…</p>
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
import DrainRing from "@/components/DrainRing.vue";
import ThemeButton from "@/components/ThemeButton.vue";
import { initSound, muted, playCue, toggleMute } from "@/sound";
import {
	clearGpPlayer,
	gpCall,
	loadGpPlayer,
	saveGpPlayer,
	teamStyle,
} from "@/platform/session/gp";

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
let seqSeen = -1;

const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
);
const urgentColor = computed(() => (remaining.value <= 5 ? "rgb(var(--alert))" : "rgb(var(--ok))"));
const myTeam = computed(() =>
	(view.value.teams || []).find((t) => t.team_name === view.value.actor_team_name)
);
const teamName = computed(() => myTeam.value?.team_name || "");
const rankedTeams = computed(() =>
	[...(view.value.teams || podium.value || [])].sort(
		(a, b) => (a.rank || 99) - (b.rank || 99) || b.score - a.score
	)
);
const headline = computed(() => {
	const mine = rankedTeams.value.find((t) => t.name === player.value?.participant);
	if (!mine) return "Final results";
	if (mine.rank === 1) return "Your team won! 🏆";
	return `You finished #${mine.rank}`;
});

function onEvent(message) {
	if (!message || typeof message !== "object") return;
	const type = message.type;
	const payload = message.payload || {};
	if (type === "platform.lobby_updated") {
		// nothing private in lobby updates for now; teams arrive via state fetches
	} else if (type === "platform.state_changed" || type.startsWith("cuecast.")) {
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
	} else if (type === "platform.participant_removed" && payload.participant === player.value?.participant) {
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
	if (["turn_ready", "turn_open"].includes(state.phase)) {
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
	} catch (e) {
		// late taps happen at the buzzer; resync rather than nagging the performer
		await refreshPrivate().catch(() => {});
	} finally {
		submitting.value = false;
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
