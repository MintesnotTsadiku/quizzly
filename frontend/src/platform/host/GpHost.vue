<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<HostBar v-if="!inLiveSession" />

		<!-- No session: setup -->
		<div v-if="!session && !loading" class="mx-auto w-full max-w-2xl flex-1 px-5 py-12 sm:px-8">
			<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-accent">Host</p>
			<h1 class="mt-2 font-display text-4xl font-extrabold text-paper sm:text-5xl">Start a room</h1>
			<p class="mt-3 text-paper/50">
				Pick a deck, or start a demo from the
				<RouterLink
					class="text-ok underline decoration-haze hover:decoration-lagoon"
					to="/play/games/cuecast"
				>game page</RouterLink>.
			</p>
			<div class="mt-8 flex flex-col gap-6">
				<label class="flex flex-col gap-2">
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Deck</span>
					<select v-model="setup.deck" class="field text-lg">
						<option value="" disabled>Pick a deck…</option>
						<option v-for="deck in decks" :key="deck.name" :value="deck.name">
							{{ deck.title }} · {{ deck.prompt_count }} prompts{{ Number(deck.is_demo) ? " · demo" : "" }}
						</option>
					</select>
				</label>
				<div class="grid grid-cols-2 gap-5 sm:grid-cols-3">
					<div class="flex flex-col gap-2">
						<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Round</span>
						<div class="flex gap-2">
							<button
								v-for="s in [30, 60, 90]"
								:key="s"
								type="button"
								class="ctl flex-1"
								:data-on="setup.seconds === s"
								@click="setup.seconds = s"
							>{{ s }}s</button>
						</div>
					</div>
					<div class="flex flex-col gap-2">
						<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Teams</span>
						<div class="flex gap-2">
							<button
								v-for="n in [2, 3, 4]"
								:key="n"
								type="button"
								class="ctl flex-1"
								:data-on="setup.teams_count === n"
								@click="setup.teams_count = n"
							>{{ n }}</button>
						</div>
					</div>
					<label class="col-span-2 flex items-center gap-3 self-end text-paper/70 sm:col-span-1">
						<input type="checkbox" v-model="setup.sudden_death" class="size-4 accent-[rgb(var(--accent))]" />
						Sudden death
					</label>
				</div>
				<button class="ctl ctl-go self-start px-8" :disabled="!setup.deck || creating" @click="createSession">
					{{ creating ? "Opening…" : "Open the lobby" }}
				</button>
				<p v-if="error" class="text-alert">{{ error }}</p>
			</div>
		</div>

		<!-- Lobby -->
		<div
			v-else-if="phase === 'lobby'"
			class="flex min-h-0 flex-1 flex-col justify-center gap-10 p-5 sm:p-10"
		>
			<div class="flex flex-wrap items-center justify-center gap-10">
				<div class="text-center sm:text-left">
					<p class="break-all font-mono text-sm text-accent">Join at {{ joinHost }}</p>
					<p class="mt-2 font-mono text-7xl font-bold tracking-[0.08em] text-paper sm:text-8xl">
						{{ pin }}
					</p>
					<button class="ctl mt-5" :data-on="lobbyLocked" @click="toggleLock">
						{{ lobbyLocked ? "Lobby locked" : "Lock lobby" }}
					</button>
				</div>
				<button v-if="qrDataUrl" @click="qrFullscreen = true">
					<img :src="qrDataUrl" alt="Join QR code" class="size-44 rounded-2xl bg-card p-2 transition hover:scale-105" />
				</button>
			</div>

			<!-- Joiners appear unassigned first; balancing is the host's one big pre-game call -->
			<div
				v-if="unassigned.length || teams.length"
				class="flex flex-col gap-5"
			>
				<div v-if="unassigned.length" class="flex flex-wrap items-center justify-center gap-2">
					<span
						v-for="p in unassigned"
						:key="p.name"
						class="group relative flex items-center gap-2 rounded-full border border-haze bg-dusk py-1 pl-1 pr-4 text-base font-medium text-paper sm:text-lg"
					>
						<AvatarPic :id="p.avatar" :nickname="p.nickname" :size="32" />
						{{ p.nickname }}
						<button
							class="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full bg-haze text-xs leading-none text-paper opacity-0 transition hover:bg-alert group-hover:opacity-100"
							:aria-label="`Remove ${p.nickname}`"
							@click="kick(p)"
						>×</button>
					</span>
					<span class="font-mono text-xs uppercase tracking-wider text-paper/40">
						pick teams below to sort them
					</span>
				</div>

				<div class="grid gap-5" :class="teamCols">
					<div
						v-for="team in teams"
						:key="team.name"
						class="rounded-3xl border bg-dusk/60 p-5"
						:class="teamStyle(team.color).border"
					>
						<div class="flex items-center justify-between gap-2">
							<input
								v-model="team.editName"
								class="min-w-0 border-b border-transparent bg-transparent font-display text-lg font-bold text-paper focus:border-paper focus:outline-none"
								@change="renameTeam(team)"
							/>
							<span class="font-mono text-xs tabular-nums text-paper/40">
								{{ teamMembers(team.name).length }}
							</span>
						</div>
						<div class="mt-4 flex min-h-9 flex-wrap gap-2">
							<span
								v-for="p in teamMembers(team.name)"
								:key="p.name"
								class="group relative flex items-center gap-2 rounded-full py-1 pl-1 pr-3 text-sm font-medium"
								:class="[teamStyle(team.color).fill, teamStyle(team.color).text]"
							>
								<AvatarPic :id="p.avatar" :nickname="p.nickname" :size="26" />
								{{ p.nickname }}
								<button
									class="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full bg-haze text-xs leading-none text-paper opacity-0 transition hover:bg-alert group-hover:opacity-100"
									:aria-label="`Remove ${p.nickname}`"
									@click="kick(p)"
								>×</button>
							</span>
							<span v-if="!teamMembers(team.name).length" class="text-sm italic text-paper/35">waiting…</span>
						</div>
					</div>
				</div>
			</div>
			<p v-else class="text-center text-paper/35">Waiting for the first player…</p>

			<div class="flex flex-wrap items-center justify-center gap-3">
				<button v-for="n in [2, 3, 4]" :key="n" class="ctl" @click="balanceTeams(n)">
					{{ n }} teams
				</button>
				<button class="ctl" @click="toggleMute">{{ muted ? "Sound off" : "Sound on" }}</button>
				<ThemeButton class="ctl" />
				<button class="ctl" @click="end">Exit</button>
				<button class="ctl ctl-go" :disabled="starting || !participants.length" @click="startGame">
					{{ starting ? "Starting…" : `Start · ${participants.length} players` }}
				</button>
			</div>
			<p v-if="error" class="text-center text-alert">{{ error }}</p>
		</div>

		<!-- Live console -->
		<div
			v-else
			class="flex min-h-0 flex-1 flex-col items-center justify-center gap-8 p-6 text-center sm:p-10"
		>
			<template v-if="view.phase === 'turn_ready' && view.performer">
				<p class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40">
					Turn {{ (view.turn ?? 0) + 1 }} of {{ totalTurns || "?" }}
				</p>
				<div class="flex items-center gap-5">
					<AvatarPic :id="view.performer.avatar" :nickname="view.performer.nickname" :size="72" />
					<div class="text-left">
						<p class="font-display text-3xl font-extrabold text-paper">{{ view.performer.nickname }}</p>
						<p class="text-paper/50">{{ teamNameOf(view) }} takes the stage</p>
					</div>
				</div>
				<DrainRing :percent="timerPercent" :seconds="Math.ceil(remaining)" :size="110" color="rgb(var(--accent))" />
			</template>

			<template v-else-if="view.phase === 'turn_open' && view.performer">
				<div class="flex items-center justify-center gap-8">
					<DrainRing
						:percent="timerPercent"
						:seconds="Math.ceil(remaining)"
						:size="120"
						:color="remaining <= 5 ? 'rgb(var(--alert))' : 'rgb(var(--ok))'"
					/>
					<div class="text-left">
						<p class="font-display text-4xl font-extrabold text-paper">{{ view.performer.nickname }}</p>
						<p class="mt-1 font-mono uppercase tracking-wider text-paper/50">
							{{ teamNameOf(view) }} · {{ mode }} mode
						</p>
					</div>
				</div>
				<div class="flex w-full max-w-lg items-center justify-between rounded-3xl border border-haze bg-dusk px-8 py-6">
					<span class="font-mono uppercase tracking-widest text-paper/50">Solved</span>
					<span class="font-display text-5xl font-extrabold tabular-nums text-accent">{{ solvedCount }}</span>
				</div>
				<p class="max-w-md text-sm text-paper/40">
					Only {{ view.performer.nickname }}'s phone knows the words. Watch them work.
				</p>
				<button class="ctl" @click="reassignPerformer">Reassign performer</button>
			</template>

			<template v-else-if="view.phase === 'turn_review'">
				<h2 class="font-display text-3xl font-extrabold text-paper sm:text-4xl">
					{{ solvedCount }} solved for {{ teamNameOf(view) }}
				</h2>
				<div class="flex max-w-2xl flex-wrap justify-center gap-2">
					<span
						v-for="(word, index) in view.played || []"
						:key="index"
						class="rounded-xl px-4 py-2 font-medium"
						:class="isSolved(word, index) ? 'bg-lagoon/20 text-ok' : 'bg-dusk text-paper/40 line-through'"
					>
						{{ word }}
					</span>
				</div>
				<p class="text-sm text-paper/40">
					{{ view.passed_count || 0 }} passed · ask the room if any call looked wrong
				</p>
			</template>

			<template v-else-if="view.phase === 'scoreboard'">
				<h2 class="font-display text-3xl font-extrabold text-paper">Scoreboard</h2>
				<ol class="flex w-full max-w-xl flex-col gap-3">
					<li
						v-for="team in rankedTeams(view.teams || [])"
						:key="team.name"
						class="flex items-center gap-4 rounded-2xl border bg-dusk px-5 py-4"
						:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-6 font-mono text-lg tabular-nums text-paper/40">{{ team.rank }}</span>
						<span class="flex-1 text-left font-display text-xl font-bold text-paper">{{ team.team_name }}</span>
						<span class="font-display text-2xl font-extrabold tabular-nums text-accent">{{ team.score }}</span>
					</li>
				</ol>
			</template>

			<template v-else-if="podium">
				<h1 class="font-display text-5xl font-extrabold text-paper sm:text-6xl">Final results</h1>
				<ol class="flex w-full max-w-xl flex-col gap-3">
					<li
						v-for="team in podium"
						:key="team.name"
						class="flex items-center gap-4 rounded-2xl border bg-dusk px-5 py-4"
						:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-6 font-mono text-lg tabular-nums text-paper/40">{{ team.rank }}</span>
						<span class="flex-1 text-left font-display text-xl font-bold text-paper">{{ team.team_name }}</span>
						<span class="font-display text-2xl font-extrabold tabular-nums text-accent">{{ team.score }}</span>
					</li>
				</ol>
				<button class="ctl ctl-go mt-2" @click="newRoom">New room</button>
			</template>

			<template v-else>
				<p class="font-mono uppercase tracking-[0.28em] text-paper/40">Get ready…</p>
			</template>

			<div v-if="!podium && phase !== 'lobby'" class="flex flex-wrap items-center justify-center gap-3">
				<button v-if="view.phase !== 'scoreboard'" class="ctl" @click="skipTurn">Skip turn</button>
				<button class="ctl ctl-danger" @click="end">End game</button>
			</div>
			<p v-if="error" class="text-alert">{{ error }}</p>
		</div>

		<dialog
			ref="qrDialog"
			class="qz-dialog border-0 bg-transparent p-0"
			@cancel.prevent="qrFullscreen = false"
			@click="qrFullscreen = false"
		>
			<img
				v-if="qrDataUrl"
				:src="qrDataUrl"
				alt="Join QR code"
				class="size-[min(78vh,88vw)] rounded-3xl bg-card p-4"
			/>
			<p class="mt-4 text-center font-mono text-2xl tracking-[0.08em] text-paper">{{ pin }}</p>
		</dialog>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import QRCode from "qrcode";
import { call, readError } from "@/api";
import { confirm } from "@/confirm";
import { useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";
import DrainRing from "@/components/DrainRing.vue";
import HostBar from "@/components/HostBar.vue";
import ThemeButton from "@/components/ThemeButton.vue";
import { initSound, muted, playCue, toggleMute } from "@/sound";
import {
	forgetHostedSession,
	gpCall,
	loadHostedSession,
	rememberHostedSession,
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

const loading = ref(true);
const session = ref(null);
const pin = ref("");
const configuration = ref({});
const phase = ref("lobby");
const participants = ref([]);
const teams = ref([]);
const decks = ref([]);
const lobbyLocked = ref(false);
const view = ref({});
const podium = ref(null);
const starting = ref(false);
const qrDataUrl = ref("");
const qrFullscreen = ref(false);
const qrDialog = ref(null);
const error = ref("");
let stopRoom = null;
let seqSeen = -1;

watch(qrFullscreen, (open) => (open ? qrDialog.value.showModal() : qrDialog.value.close()));

const inLiveSession = computed(() => Boolean(session.value));
const joinHost = computed(() => `${window.location.host}/play/join`);
const mode = computed(() => configuration.value.mode || "Act");
const totalTurns = computed(() => {
	const t = teams.value.length || configuration.value.teams_count || 2;
	return t * (configuration.value.turns_per_team || 1);
});
const solvedCount = computed(() => view.value.solved ?? 0);
const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
);
const teamCols = computed(() => {
	const count = Math.max(1, teams.value.length);
	return count >= 4 ? "sm:grid-cols-4" : count === 3 ? "sm:grid-cols-3" : "sm:grid-cols-2";
});

function teamMembers(teamName) {
	return participants.value.filter((p) => p.team === teamName);
}

const unassigned = computed(() => participants.value.filter((p) => !p.team));

function teamNameOf(v) {
	const team = (v.teams || []).find((t) => t.name === (v.performer?.team || null));
	return team?.team_name || "";
}

function rankedTeams(list) {
	return [...list].sort((a, b) => (a.rank || 0) - (b.rank || 0) || b.score - a.score);
}

function isSolved(word, index) {
	const played = view.value.played || [];
	const passedStart = played.length - (view.value.passed_count || 0);
	return index < passedStart;
}

function onEvent(envelopeMessage) {
	if (!envelopeMessage || typeof envelopeMessage !== "object") return;
	if (typeof envelopeMessage.seq === "number") {
		if (envelopeMessage.seq < seqSeen) return; // stale delivery
		seqSeen = envelopeMessage.seq;
	}
	const type = envelopeMessage.type;
	const payload = envelopeMessage.payload || envelopeMessage;
	if (type === "platform.lobby_updated") {
		participants.value = payload.participants || [];
		teams.value = (payload.teams || []).map((t) => ({ ...t, editName: t.team_name }));
		lobbyLocked.value = Boolean(payload.lobby_locked);
	} else if (type === "platform.state_changed" || type.startsWith("cuecast.")) {
		if (payload.phase) {
			view.value = payload;
			podium.value = null;
			phase.value = payload.phase;
			playCue(payload.phase === "turn_open" ? "submit" : "tick");
		}
	} else if (type === "platform.action_progress") {
		view.value = { ...view.value, solved: payload.count };
	} else if (type === "platform.scoreboard_updated") {
		view.value = { ...view.value, phase: "scoreboard", teams: payload.teams };
		phase.value = "scoreboard";
		stopCountdown();
	} else if (type === "platform.participant_removed") {
		// lobby refresh arrives separately; nothing to do here for hosts
	}
}

async function refresh() {
	try {
		await applyState(await gpCall("get_host_state", session.value ? { session: session.value } : {}));
	} catch (e) {
		error.value = readError(e);
	}
}

async function applyState(state) {
	if (!state.session) {
		session.value = null;
		forgetHostedSession();
		return;
	}
	session.value = state.session;
	pin.value = state.game_pin;
	configuration.value = state.configuration || {};
	participants.value = state.participants || [];
	teams.value = (state.teams || []).map((t) => ({
		...t,
		editName: teams.value.find((old) => old.name === t.name)?.editName || t.team_name,
	}));
	lobbyLocked.value = Boolean(state.lobby_locked);
	qrDataUrl.value = await renderQr(joinUrl());
	rememberHostedSession(state.session);

	if (state.status === "Ended" || state.podium) {
		podium.value = state.podium || [];
		phase.value = "podium";
		stopCountdown();
		return;
	}
	if (state.status !== "Active") {
		phase.value = "lobby";
		return;
	}
	podium.value = null;
	phase.value = state.phase || "lobby";
	view.value = state.view || {};
	seqSeen = state.state_version ?? seqSeen;

	if (["turn_ready", "turn_open"].includes(state.phase)) {
		startCountdown(Math.max(0.5, state.remaining_seconds));
	} else {
		stopCountdown();
	}
}

function joinUrl() {
	return `${window.location.origin}/play/join?pin=${pin.value}`;
}

async function renderQr(url) {
	const canvas = document.createElement("canvas");
	await QRCode.toCanvas(canvas, url, {
		margin: 1,
		width: 800,
		errorCorrectionLevel: "H",
		color: { dark: "#16111F", light: "#F4F0FA" },
	});
	return canvas.toDataURL();
}

onMounted(async () => {
	initSound("host");
	try {
		const decks = await call("frappe.client.get_list", {
			doctype: "GP Cue Deck",
			fields: ["name", "title", "mode", "is_demo", "demo_key"],
			limit_page_length: 0,
			order_by: "is_demo desc, title asc",
		});
		for (const deck of decks) {
			const rows = await call("frappe.client.get_list", {
				doctype: "GP Cue Prompt",
				filters: { parenttype: "GP Cue Deck", parent: deck.name },
				limit_page_length: 0,
			});
			deck.prompt_count = rows.length;
		}
		decks.value = decks;

		const remembered = loadHostedSession();
		let state = null;
		if (remembered) {
			state = await gpCall("get_host_state", { session: remembered }).catch(() => null);
			if (!state || !state.session) forgetHostedSession();
		}
		if (!state) state = await gpCall("get_host_state").catch(() => ({}));
		if (state.session) {
			await applyState(state);
			stopRoom = useSessionRoom(socket, pin.value, onEvent, refresh, "gp");
		} else if (route.query.session) {
			const created = await gpCall("get_host_state", { session: route.query.session });
			if (created.session) {
				await applyState(created);
				stopRoom = useSessionRoom(socket, pin.value, onEvent, refresh, "gp");
			}
		}
		loading.value = false;
	} catch (e) {
		loading.value = false;
		error.value = readError(e);
	}
});

async function hostAction(method, params = {}) {
	error.value = "";
	try {
		return await gpCall(method, { session: session.value, ...params });
	} catch (e) {
		error.value = readError(e);
		await refresh().catch(() => {});
	}
}

async function createSession() {
	error.value = "";
	creating.value = true;
	try {
		const created = await gpCall("create_session", {
			game_key: "cuecast",
			configuration: setup.value,
		});
		await applyState(await gpCall("get_host_state", { session: created.session }));
		stopRoom?.();
		stopRoom = useSessionRoom(socket, pin.value, onEvent, refresh, "gp");
	} catch (e) {
		error.value = readError(e);
	} finally {
		creating.value = false;
	}
}

async function startGame() {
	starting.value = true;
	if (await hostAction("start_session")) {
		await refresh();
	} else {
		starting.value = false;
	}
}

async function toggleLock() {
	const lobby = await hostAction(lobbyLocked.value ? "unlock_lobby" : "lock_lobby");
	if (lobby) lobbyLocked.value = Boolean(lobby.lobby_locked);
}

async function balanceTeams(count) {
	const lobbyState = await hostAction("host_command", { command: "balance_teams", payload: { count } });
	if (lobbyState) await refresh();
}

async function renameTeam(team) {
	await hostAction("host_command", {
		command: "rename_team",
		payload: { team: team.name, team_name: team.editName },
	});
}

async function kick(participant) {
	const ok = await confirm(`Remove ${participant.nickname} from the room?`, {
		action: "Remove",
		danger: true,
	});
	if (!ok) return;
	await hostAction("kick_participant", { participant: participant.name });
}

async function skipTurn() {
	await hostAction("host_command", { command: "skip_turn" });
}

async function reassignPerformer() {
	const members = participants.value.filter(
		(p) => !podium.value && p.team && p.nickname !== view.value.performer?.nickname
	);
	const stageTeamParticipants = participants.value.filter(
		(p) => p.team === (view.value.teams || []).find((t) => t.team_name === teamNameOf(view.value))?.name
	);
	const roster = (stageTeamParticipants.length ? stageTeamParticipants : members).filter(
		(p) => p.nickname !== view.value.performer?.nickname
	);
	if (!roster.length) return;
	const pick = roster[roster.length - 1];
	await hostAction("host_command", {
		command: "reassign_performer",
		payload: { participant: pick.name },
	});
}

async function end() {
	const prompt = phase.value === "lobby" ? "Close this lobby?" : "End the game for everyone?";
	const ok = await confirm(prompt, { action: phase.value === "lobby" ? "Close lobby" : "End game", danger: true });
	if (!ok) return;
	await hostAction("end_session");
	if (phase.value === "lobby") newRoom();
	else await refresh();
}

function newRoom() {
	forgetHostedSession();
	window.location.href = "/play/host";
}
</script>
