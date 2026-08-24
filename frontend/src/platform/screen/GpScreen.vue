<template>
	<div class="flex h-full flex-col overflow-hidden bg-night">
		<!-- Podium outranks everything: the last thing a room sees must be the winner -->
		<div
			v-if="podium"
			class="flex min-h-0 flex-1 flex-col items-center justify-center gap-10 p-10"
		>
			<h2 class="font-display text-6xl font-extrabold text-paper">Final results</h2>
			<ol
				class="grid w-full max-w-5xl gap-5"
				:class="podium.length > 2 ? 'sm:grid-cols-2' : ''"
			>
				<li
					v-for="team in rankedTeams(podium)"
					:key="team.name"
					class="flex items-center gap-5 rounded-3xl border bg-dusk px-8 py-5"
					:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
				>
					<span class="w-8 font-mono text-2xl tabular-nums text-paper/40">{{ team.rank }}</span>
					<span
						:class="teamStyle(team.color).fill"
						class="grid size-11 place-items-center rounded-full font-display text-lg font-extrabold text-sunk"
					>
						{{ team.rank }}
					</span>
					<span class="min-w-0 flex-1 truncate text-left font-display text-3xl font-bold text-paper">
						{{ team.team_name }}
					</span>
					<span class="font-display text-4xl font-extrabold tabular-nums text-accent">
						{{ team.score }}
					</span>
				</li>
			</ol>
			<p class="font-mono uppercase tracking-[0.3em] text-paper/35">Thanks for playing</p>
		</div>

		<!-- Lobby -->
		<div
			v-else-if="status === 'Lobby'"
			class="flex min-h-0 flex-1 flex-col items-center justify-center gap-10 p-8"
		>
			<p class="break-all text-center font-mono text-xl text-accent">Join at {{ joinHost }}</p>
			<p class="text-center font-mono text-[9rem] font-bold leading-none tracking-[0.06em] text-paper">
				{{ pin }}
			</p>
			<div class="flex w-full max-w-3xl flex-wrap justify-center gap-2.5">
				<span
					v-for="p in publicParticipants"
					:key="p.nickname"
					class="flex items-center gap-2 rounded-full border border-haze bg-dusk py-1.5 pl-1.5 pr-4 text-lg font-medium text-paper"
				>
					<AvatarPic :id="p.avatar" :nickname="p.nickname" :size="32" />
					{{ p.nickname }}
				</span>
			</div>
			<p class="font-mono uppercase tracking-[0.28em] text-paper/40">
				{{ publicParticipants.length }} in the room
			</p>
		</div>

		<!-- Live: the projector is the room's face; prompts and controls live elsewhere -->
		<div
			v-else-if="status === 'Active'"
			class="flex min-h-0 flex-1 flex-col items-center justify-center gap-10 p-10"
		>
			<template v-if="view.phase === 'turn_ready' && view.performer">
				<p class="font-mono text-sm uppercase tracking-[0.3em] text-paper/40">
					Get ready for turn {{ (view.turn ?? 0) + 1 }}
				</p>
				<div class="flex items-center gap-10">
					<AvatarPic
						:id="view.performer.avatar"
						:nickname="view.performer.nickname"
						:size="150"
					/>
					<div class="text-left">
						<h1 class="font-display text-8xl font-extrabold leading-none text-paper">
							{{ view.performer.nickname }}
						</h1>
						<p class="mt-4 font-display text-3xl" :class="teamInkOf(view)">
							{{ teamNameOf(view) }} takes the stage
						</p>
					</div>
					<DrainRing
						:percent="timerPercent"
						:seconds="Math.ceil(remaining)"
						:size="170"
						color="rgb(var(--accent))"
					/>
				</div>
			</template>

			<template v-else-if="view.phase === 'turn_open' && view.performer">
				<div class="flex items-center gap-10">
					<AvatarPic
						:id="view.performer.avatar"
						:nickname="view.performer.nickname"
						:size="130"
					/>
					<div class="text-left">
						<p class="font-mono text-xs uppercase tracking-[0.3em] text-paper/40">
							Now performing
						</p>
						<h1 class="mt-1 font-display text-7xl font-extrabold leading-none text-paper">
							{{ view.performer.nickname }}
						</h1>
						<p class="mt-2 font-display text-2xl" :class="teamInkOf(view)">
							{{ teamNameOf(view) }}
						</p>
					</div>
					<div class="ml-16 flex items-center gap-10">
						<div class="text-center">
							<p class="font-display text-9xl font-extrabold leading-none tabular-nums text-accent">
								{{ solvedCount }}
							</p>
							<p class="mt-1 font-mono text-xs uppercase tracking-[0.3em] text-paper/40">
								solved
							</p>
						</div>
						<DrainRing
							:percent="timerPercent"
							:seconds="Math.ceil(remaining)"
							:size="170"
							:color="remaining <= 5 ? 'rgb(var(--alert))' : 'rgb(var(--ok))'"
						/>
					</div>
				</div>
				<div class="mt-6 grid w-full max-w-6xl gap-6" :class="teamCardCols">
					<div
						v-for="team in view.teams || []"
						:key="team.name"
						class="rounded-3xl border-2 bg-dusk/60 px-8 py-6 text-center"
						:class="
							isStageTeam(team)
								? [teamStyle(team.color).border, 'scale-[1.02]']
								: 'border-haze'
						"
					>
						<p class="truncate font-display text-2xl font-bold text-paper">{{ team.team_name }}</p>
						<p class="mt-2 font-display text-6xl font-extrabold tabular-nums" :class="teamInkOf({ actor_team_name: team.team_name })">
							{{ team.score }}
						</p>
						<p v-if="isStageTeam(team)" class="mt-1 font-mono text-[11px] uppercase tracking-[0.25em] text-paper/45">
							on stage
						</p>
					</div>
				</div>
			</template>

			<template v-else-if="view.phase === 'turn_review'">
				<h2 class="font-display text-5xl font-extrabold text-paper">
					{{ solvedCount }} solved for {{ teamNameOf(view) }}
				</h2>
				<div class="flex max-w-5xl flex-wrap justify-center gap-3">
					<span
						v-for="(word, index) in view.played || []"
						:key="index"
						class="rounded-2xl px-6 py-3 font-display text-2xl font-bold"
						:class="
							isSolved(word, index)
								? 'bg-lagoon/25 text-ok'
								: 'bg-dusk text-paper/35 line-through'
						"
					>
						{{ word }}
					</span>
				</div>
				<p class="font-mono uppercase tracking-widest text-paper/40">
					{{ view.passed_count || 0 }} passed
				</p>
			</template>

			<template v-else-if="view.phase === 'scoreboard'">
				<h2 class="font-display text-5xl font-extrabold text-paper">Scoreboard</h2>
				<ol class="grid w-full max-w-5xl gap-5" :class="(view.teams || []).length > 2 ? 'sm:grid-cols-2' : ''">
					<li
						v-for="team in rankedTeams(view.teams || [])"
						:key="team.name"
						class="flex items-center gap-5 rounded-3xl border bg-dusk px-8 py-5"
						:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-8 font-mono text-2xl tabular-nums text-paper/40">{{ team.rank }}</span>
						<span
							:class="teamStyle(team.color).fill"
							class="grid size-11 place-items-center rounded-full font-display text-lg font-extrabold text-sunk"
						>
							{{ team.rank }}
						</span>
						<span class="min-w-0 flex-1 truncate text-left font-display text-3xl font-bold text-paper">
							{{ team.team_name }}
						</span>
						<span class="font-display text-4xl font-extrabold tabular-nums text-accent">
							{{ team.score }}
						</span>
					</li>
				</ol>
			</template>

			<template v-else>
				<p class="font-mono uppercase tracking-[0.3em] text-paper/40">Here we go…</p>
			</template>
		</div>

		<!-- Ended / unknown pin -->
		<div v-else class="flex min-h-0 flex-1 flex-col items-center justify-center gap-8 p-10">
			<h1 class="font-display text-6xl font-extrabold text-paper">See you next time</h1>
			<p class="text-paper/50">Start the next room from the host console.</p>
		</div>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";
import DrainRing from "@/components/DrainRing.vue";
import { initSound, playCue } from "@/sound";
import { gpCall, teamStyle } from "@/platform/session/gp";

const socket = inject("$socket");
const route = useRoute();
const {
	remaining,
	total: windowSeconds,
	start: startCountdown,
	stop: stopCountdown,
} = useCountdown();

// The screen knows a PIN and nothing else: every byte it renders is public state.
const pin = route.params.pin;
const status = ref("");
const view = ref({});
const podium = ref(null);
const publicParticipants = ref([]);
let seqSeen = -1;
let stopRoom = null;

const joinHost = `${window.location.host}/play/join`;
const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
);
const solvedCount = computed(() => view.value.solved ?? 0);

function teamNameOf(v) {
	return v.actor_team_name || "";
}

function teamInkOf(v) {
	const team = (v.teams || []).find((t) => t.team_name === v.actor_team_name);
	return teamStyle(team?.color).ink;
}

function isStageTeam(team) {
	return team.team_name === (view.value.actor_team_name || "");
}

const teamCardCols = computed(() =>
	(view.value.teams || []).length >= 4 ? "sm:grid-cols-4" : (view.value.teams || []).length === 3 ? "sm:grid-cols-3" : "grid-cols-2"
);

function rankedTeams(list) {
	return [...list].sort((a, b) => (a.rank || 0) - (b.rank || 0) || b.score - a.score);
}

function isSolved(word, index) {
	const played = view.value.played || [];
	const passedStart = played.length - (view.value.passed_count || 0);
	return index < passedStart;
}

function onEvent(message) {
	if (!message || typeof message !== "object" || !message.type) return;
	if (typeof message.seq === "number") {
		if (message.seq < seqSeen) return;
		seqSeen = message.seq;
	}
	const type = message.type;
	const payload = message.payload || {};
	if (type === "platform.state_changed" || type.startsWith("cuecast.")) {
		status.value = "Active";
		if (payload.phase) {
			view.value = { ...view.value, ...payload };
			podium.value = null;
			playCue(payload.phase === "turn_open" ? "submit" : "tick");
			if (payload.phase === "turn_ready") startCountdown(3);
			else stopCountdown();
		}
	} else if (type === "platform.action_progress") {
		view.value = { ...view.value, solved: payload.count };
	} else if (type === "platform.scoreboard_updated") {
		view.value = { ...view.value, phase: "scoreboard", teams: payload.teams };
		stopCountdown();
	} else if (type === "platform.session_ended") {
		podium.value = payload.teams || [];
		status.value = "Ended";
		stopCountdown();
		playCue("podium");
	} else if (type === "platform.lobby_updated") {
		publicParticipants.value = payload.participants || [];
	}
}

async function refresh() {
	try {
		const state = await gpCall("get_public_state", { pin });
		applyState(state);
	} catch {
		status.value = "Unknown";
	}
}

function applyState(state) {
	seqSeen = Math.max(seqSeen, state.state_version ?? 0);
	status.value = state.status;
	if (state.podium) podium.value = state.podium;
	if (state.view) view.value = { ...view.value, ...state.view };
	if (status.value === "Active" && ["turn_ready", "turn_open"].includes(state.phase)) {
		startCountdown(Math.max(0.5, state.remaining_seconds));
	} else {
		stopCountdown();
	}
}

onMounted(async () => {
	initSound("host");
	await refresh();
	stopRoom = useSessionRoom(socket, pin, onEvent, refresh, "gp");
});
</script>
