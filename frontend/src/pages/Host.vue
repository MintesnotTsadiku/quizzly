<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<template v-if="!session">
			<div class="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-8 p-8">
				<div>
					<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-gold">Host</p>
					<h1 class="mt-2 font-display text-5xl font-extrabold text-paper">
						Pick a quiz
					</h1>
				</div>
				<p v-if="error" class="text-ember">{{ error }}</p>
				<div v-if="quizzes.length" class="flex flex-col gap-2">
					<button
						v-for="(quiz, index) in quizzes"
						:key="quiz.name"
						class="group flex items-center gap-4 rounded-2xl border border-haze bg-dusk px-5 py-4 text-left transition hover:border-ember"
						@click="createSession(quiz.name)"
					>
						<span class="font-mono text-xs tabular-nums text-paper/35">
							{{ String(index + 1).padStart(2, "0") }}
						</span>
						<span class="flex-1 font-display text-xl font-bold text-paper">
							{{ quiz.title }}
						</span>
						<span class="text-paper/25 transition group-hover:text-ember">→</span>
					</button>
				</div>
				<p v-else-if="loaded" class="text-paper/50">
					No quizzes yet. Create a QZ Quiz in Desk, then come back.
				</p>
			</div>
		</template>

		<!-- Lobby -->
		<template v-else-if="phase === 'lobby'">
			<div class="flex flex-1 flex-col justify-center gap-12 p-8">
				<div class="flex flex-wrap items-center justify-center gap-14">
					<div>
						<p class="font-mono text-sm tracking-wide text-gold">
							Join at {{ joinHost }}
						</p>
						<p class="mt-3 font-mono text-8xl font-bold tracking-[0.08em] text-paper">
							{{ session.game_pin }}
						</p>
						<p class="mt-3 text-paper/45">or point a phone camera at the code</p>
					</div>
					<img
						v-if="qrDataUrl"
						:src="qrDataUrl"
						alt="Join QR code"
						class="h-48 w-48 rounded-2xl bg-paper p-2"
					/>
				</div>

				<div class="flex flex-col items-center gap-5">
					<p
						v-if="participants.length"
						class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40"
					>
						{{ participants.length }}
						{{ participants.length === 1 ? "player" : "players" }} in
					</p>
					<div class="flex max-w-5xl flex-wrap justify-center gap-2.5">
						<button
							v-for="participant in participants"
							:key="participant.name"
							class="group flex items-center gap-3 rounded-full border border-haze bg-dusk py-1 pl-1 pr-5 text-xl font-medium text-paper transition hover:border-ember"
							title="Remove this player"
							@click="kick(participant)"
						>
							<AvatarPic
								:id="participant.avatar"
								:nickname="participant.nickname"
								:size="44"
							/>
							<span class="group-hover:line-through">{{
								participant.nickname
							}}</span>
						</button>
					</div>
					<p v-if="!participants.length" class="text-paper/35">
						Waiting for the first player…
					</p>
				</div>

				<div class="flex flex-wrap items-center justify-center gap-3">
					<button class="ctl" :data-on="lobbyLocked" @click="toggleLock">
						{{ lobbyLocked ? "Lobby locked" : "Lock lobby" }}
					</button>
					<button class="ctl" :data-on="autoAdvance" @click="toggleAutoAdvance">
						Auto-advance {{ autoAdvance ? "on" : "off" }}
					</button>
					<button class="ctl" @click="toggleMute">
						{{ muted ? "Sound off" : "Sound on" }}
					</button>
					<button
						class="ctl ctl-go"
						:disabled="starting || !participants.length"
						@click="start"
					>
						{{ starting ? "Starting…" : "Start game" }}
					</button>
				</div>
				<p v-if="error" class="text-center text-ember">{{ error }}</p>
			</div>
		</template>

		<!-- Podium -->
		<template v-else-if="phase === 'podium'">
			<div class="flex flex-1 flex-col items-center justify-center gap-10 p-8">
				<h1 class="font-display text-6xl font-extrabold text-paper">Final results</h1>
				<div class="flex items-end justify-center gap-4">
					<div
						v-for="entry in podiumOrder"
						:key="entry.nickname"
						class="flex w-36 flex-col items-center gap-2"
					>
						<AvatarPic
							:id="entry.avatar"
							:nickname="entry.nickname"
							:size="entry.rank === 1 ? 88 : 64"
						/>
						<span class="font-display text-xl font-bold text-paper">
							{{ entry.nickname }}
						</span>
						<span class="font-mono text-sm tabular-nums text-paper/50">
							{{ entry.score }}
						</span>
						<div
							class="podium-rise flex w-full items-start justify-center rounded-t-2xl pt-3 font-mono text-3xl font-bold text-night"
							:class="PODIUM_FILL[entry.rank]"
							:style="{ height: `${180 - (entry.rank - 1) * 45}px` }"
						>
							{{ entry.rank }}
						</div>
					</div>
				</div>
				<ol class="w-full max-w-md">
					<li
						v-for="entry in leaderboard"
						:key="entry.nickname"
						class="flex items-center justify-between border-b border-haze py-2.5 text-lg text-paper/70"
					>
						<span class="flex items-center gap-3">
							<span class="w-5 font-mono text-xs tabular-nums text-paper/35">
								{{ entry.rank }}
							</span>
							<AvatarPic :id="entry.avatar" :nickname="entry.nickname" :size="28" />
							{{ entry.nickname }}
						</span>
						<span class="font-mono tabular-nums">{{ entry.score }}</span>
					</li>
				</ol>
				<button class="ctl" @click="reset">New game</button>
			</div>
		</template>

		<!-- Read time: question only, no answers yet -->
		<template v-else-if="phase === 'get_ready'">
			<div class="flex flex-1 flex-col items-center justify-center gap-10 p-8 text-center">
				<p class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40">
					Question {{ (question?.q_index ?? 0) + 1 }} of {{ question?.total }}
				</p>
				<h1
					class="max-w-4xl font-display text-6xl font-extrabold leading-tight text-paper"
				>
					{{ question?.question_text }}
				</h1>
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="140"
					color="#FFC43D"
				/>
			</div>
		</template>

		<!-- Question / results -->
		<template v-else>
			<!-- m-auto, not justify-center: a centered flex column clips its top when it overflows -->
			<div class="flex flex-1 flex-col p-8">
				<div class="m-auto flex w-full max-w-6xl flex-col gap-7">
					<div class="flex items-center gap-6">
						<DrainRing
							v-if="phase === 'question'"
							:percent="timerPercent"
							:seconds="Math.ceil(remaining)"
							:size="96"
							:color="remaining <= 5 ? '#FF5A36' : '#17B0BE'"
						/>
						<div class="min-w-0 flex-1">
							<p class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40">
								Question {{ (question?.q_index ?? 0) + 1 }} of
								{{ question?.total }}
							</p>
							<h1
								class="mt-2 font-display text-4xl font-extrabold leading-tight text-paper"
							>
								{{ question?.question_text }}
							</h1>
						</div>
						<p
							v-if="phase === 'question'"
							class="shrink-0 font-mono text-sm tabular-nums text-paper/40"
						>
							{{ answerCount }} answered
						</p>
					</div>

					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
						<div
							v-for="shape in visibleShapes"
							:key="shape.id"
							class="flex items-center gap-5 rounded-2xl px-6 py-7 transition"
							:class="[shape.fill, dimmed(shape.id) ? 'opacity-25' : '']"
						>
							<svg class="h-9 w-9 shrink-0 fill-night/55" viewBox="0 0 24 24">
								<path :d="shape.path" />
							</svg>
							<span class="flex-1 font-display text-2xl font-extrabold text-night">
								{{ question.options[Number(shape.id) - 1] }}
							</span>
							<span
								v-if="phase === 'closed' && shape.id === String(correctOption)"
								class="text-3xl text-night"
								>✓</span
							>
						</div>
					</div>

					<template v-if="phase === 'closed'">
						<div class="flex h-32 w-full items-stretch gap-3">
							<div
								v-for="shape in visibleShapes"
								:key="shape.id"
								class="flex flex-1 flex-col gap-1.5"
							>
								<span
									class="text-center font-mono text-sm tabular-nums text-paper/60"
								>
									{{ distribution[shape.id] || 0 }}
								</span>
								<div class="flex flex-1 flex-col justify-end rounded-t-lg bg-dusk">
									<div
										class="rounded-t-lg transition-[height] duration-500"
										:class="shape.fill"
										:style="{ height: `${barHeight(shape.id)}%` }"
									/>
								</div>
							</div>
						</div>

						<div class="flex flex-wrap items-start justify-between gap-8">
							<ol class="min-w-64 flex-1">
								<li
									v-for="(entry, index) in top5"
									:key="entry.nickname"
									class="flex items-center justify-between border-b border-haze py-2 text-lg text-paper/70"
								>
									<span class="flex items-center gap-3">
										<span
											class="w-5 font-mono text-xs tabular-nums text-paper/35"
										>
											{{ index + 1 }}
										</span>
										<AvatarPic
											:id="entry.avatar"
											:nickname="entry.nickname"
											:size="28"
										/>
										{{ entry.nickname }}
									</span>
									<span class="font-mono tabular-nums">{{ entry.score }}</span>
								</li>
							</ol>
							<ul class="flex-1 space-y-2 text-lg text-paper/70">
								<li
									v-for="entry in streaks"
									:key="entry.nickname"
									class="flex items-center gap-2"
								>
									<AvatarPic
										:id="entry.avatar"
										:nickname="entry.nickname"
										:size="28"
									/>
									🔥 {{ entry.nickname }} is on a {{ entry.streak }} answer
									streak
								</li>
							</ul>
						</div>
					</template>

					<div class="flex flex-wrap items-center gap-3">
						<button v-if="phase === 'question'" class="ctl" @click="skip">Skip</button>
						<button v-if="phase === 'closed'" class="ctl ctl-go" @click="next">
							Next question
						</button>
						<button class="ctl" :data-on="autoAdvance" @click="toggleAutoAdvance">
							Auto-advance {{ autoAdvance ? "on" : "off" }}
						</button>
						<button class="ctl" @click="end">End game</button>
						<p v-if="error" class="text-ember">{{ error }}</p>
					</div>
				</div>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from "vue";
import QRCode from "qrcode";
import { call } from "@/api";
import { SHAPES, useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";
import DrainRing from "@/components/DrainRing.vue";
import { initSound, muted, playCue, toggleMute } from "@/sound";

const PODIUM_FILL = { 1: "bg-gold", 2: "bg-lagoon", 3: "bg-orchid" };
// remembered so a reload on the podium restores it: get_host_state only auto-finds live sessions
const HOSTED_SESSION_KEY = "qz_hosted_session";

const socket = inject("$socket");
const {
	remaining,
	total: windowSeconds,
	start: startCountdown,
	stop: stopCountdown,
} = useCountdown();

const quizzes = ref([]);
const loaded = ref(false);
const session = ref(null);
const phase = ref("lobby");
const participants = ref([]);
const lobbyLocked = ref(false);
const autoAdvance = ref(false);
const question = ref(null);
const answerCount = ref(0);
const distribution = ref({});
const correctOption = ref(null);
const top5 = ref([]);
const streaks = ref([]);
const leaderboard = ref([]);
const qrDataUrl = ref("");
const starting = ref(false);
const error = ref("");

const joinUrl = computed(
	() => `${window.location.origin}/quizzly/join?pin=${session.value.game_pin}`
);

// The projector shows where to go, not the whole query string.
const joinHost = computed(() => `${window.location.host}/quizzly/join`);

const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
);

const visibleShapes = computed(() =>
	SHAPES.filter((shape) => question.value?.options[Number(shape.id) - 1])
);

watch(
	() => Math.ceil(remaining.value),
	(secondsLeft) => {
		if (phase.value === "question" && secondsLeft > 0 && secondsLeft <= 5) playCue("tick");
	}
);

// tallest bar fills the chart; the rest scale against it
const barHeight = (optionId) => {
	const counts = Object.values(distribution.value);
	const max = Math.max(1, ...counts);
	// keep a sliver visible so an empty bar still reads as a bar
	return Math.max(3, ((distribution.value[optionId] || 0) / max) * 100);
};

const dimmed = (optionId) => phase.value === "closed" && optionId !== String(correctOption.value);

// 2nd, 1st, 3rd — the winner stands in the middle
const podiumOrder = computed(() =>
	[leaderboard.value[1], leaderboard.value[0], leaderboard.value[2]].filter(Boolean)
);

function onSessionEvent(message) {
	if (message.type === "lobby_update") {
		participants.value = message.participants;
		lobbyLocked.value = Boolean(message.lobby_locked);
	} else if (message.type === "get_ready") {
		phase.value = "get_ready";
		question.value = { ...message, options: [] };
		startCountdown(message.seconds);
	} else if (message.type === "question") {
		question.value = message;
		answerCount.value = 0;
		correctOption.value = null;
		phase.value = "question";
		startCountdown(message.window_ms / 1000);
	} else if (message.type === "answer_count") {
		answerCount.value = message.count;
	} else if (message.type === "question_closed") {
		stopCountdown();
		distribution.value = message.distribution;
		correctOption.value = message.correct_option;
		top5.value = message.top_5;
		streaks.value = message.streaks;
		phase.value = "closed";
	} else if (message.type === "podium") {
		stopCountdown();
		leaderboard.value = message.leaderboard;
		phase.value = "podium";
		playCue("podium");
	}
}

async function applyState(state) {
	session.value = { name: state.session, game_pin: state.game_pin };
	localStorage.setItem(HOSTED_SESSION_KEY, state.session);
	participants.value = state.participants || [];
	lobbyLocked.value = Boolean(state.lobby_locked);
	autoAdvance.value = Boolean(state.auto_advance);
	top5.value = state.top_5 || [];
	qrDataUrl.value = await QRCode.toDataURL(joinUrl.value, {
		margin: 1,
		width: 400,
		color: { dark: "#16111F", light: "#F4F0FA" },
	});

	if (state.status === "Lobby") {
		starting.value = false;
		phase.value = "lobby";
	} else if (state.leaderboard) {
		leaderboard.value = state.leaderboard;
		phase.value = "podium";
	} else if (state.phase === "question") {
		question.value = state.question;
		correctOption.value = null;
		answerCount.value = state.answer_count;
		phase.value = "question";
		startCountdown(state.remaining_seconds);
	} else if (state.phase === "closed") {
		question.value = state.question;
		distribution.value = state.distribution || {};
		correctOption.value = state.question.correct_option;
		phase.value = "closed";
	} else {
		phase.value = "get_ready";
		// options stay hidden during read time, same as the live get_ready event
		question.value = { ...state.question, options: [] };
		startCountdown(state.remaining_seconds);
	}
}

async function refresh() {
	await applyState(await loadHostState());
}

async function loadHostState() {
	const remembered = localStorage.getItem(HOSTED_SESSION_KEY);
	if (remembered) {
		try {
			return await call("quizzly.api.get_host_state", { session: remembered });
		} catch {
			localStorage.removeItem(HOSTED_SESSION_KEY);
		}
	}
	return await call("quizzly.api.get_host_state");
}

onMounted(async () => {
	initSound("host");
	try {
		const state = await loadHostState();
		if (state.session) {
			await applyState(state);
			useSessionRoom(socket, state.game_pin, onSessionEvent, refresh);
			return;
		}
		quizzes.value = await call("frappe.client.get_list", {
			doctype: "QZ Quiz",
			fields: ["name", "title"],
			order_by: "modified desc",
		});
		loaded.value = true;
	} catch (e) {
		error.value = "Could not load quizzes. Log into Desk with a Quiz Host account first.";
	}
});

async function createSession(quiz) {
	error.value = "";
	try {
		const created = await call("quizzly.api.create_session", { quiz });
		await applyState(await call("quizzly.api.get_host_state", { session: created.session }));
		useSessionRoom(socket, session.value.game_pin, onSessionEvent, refresh);
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	}
}

async function hostCall(method, params = {}) {
	error.value = "";
	try {
		return await call(method, { session: session.value.name, ...params });
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
		// the screen is out of step with the server (a missed event, a stale tab): repair it
		await refresh().catch(() => {});
	}
}

async function toggleLock() {
	const lobby = await hostCall(
		lobbyLocked.value ? "quizzly.api.unlock_lobby" : "quizzly.api.lock_lobby"
	);
	if (lobby) lobbyLocked.value = Boolean(lobby.lobby_locked);
}

async function toggleAutoAdvance() {
	const result = await hostCall("quizzly.api.set_auto_advance", {
		enabled: autoAdvance.value ? 0 : 1,
	});
	if (result) autoAdvance.value = Boolean(result.auto_advance);
}

async function kick(participant) {
	if (!window.confirm(`Remove ${participant.nickname} from the game?`)) return;
	await hostCall("quizzly.api.kick_participant", { participant: participant.name });
}

// the lobby only clears when the worker's first event lands, so the button has to
// stay down until then: a second start_session throws "Session has already started"
async function start() {
	starting.value = true;
	if (!(await hostCall("quizzly.api.start_session"))) starting.value = false;
}
const next = () => hostCall("quizzly.api.next_question");
const skip = () => hostCall("quizzly.api.skip_question");

async function end() {
	if (!window.confirm("End the game for everyone?")) return;
	await hostCall("quizzly.api.end_session");
}

function reset() {
	localStorage.removeItem(HOSTED_SESSION_KEY);
	window.location.reload();
}
</script>
