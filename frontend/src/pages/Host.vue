<template>
	<div class="flex h-full flex-col overflow-y-auto bg-surface-white">
		<template v-if="!session">
			<div class="flex flex-1 flex-col items-center gap-6 p-6">
				<h1 class="text-2xl font-bold text-ink-gray-9">Host a game</h1>
				<ErrorMessage :message="error" />
				<div v-if="quizzes.length" class="flex w-full max-w-md flex-col gap-2">
					<button
						v-for="quiz in quizzes"
						:key="quiz.name"
						class="rounded-lg border border-outline-gray-2 p-4 text-left text-lg text-ink-gray-8 hover:bg-surface-gray-2"
						@click="createSession(quiz.name)"
					>
						{{ quiz.title }}
					</button>
				</div>
				<p v-else-if="loaded" class="text-ink-gray-6">
					No quizzes yet. Create a QZ Quiz in Desk first.
				</p>
			</div>
		</template>

		<!-- Lobby -->
		<template v-else-if="phase === 'lobby'">
			<div class="flex flex-1 flex-col items-center justify-center gap-6 p-6">
				<p class="text-lg text-ink-gray-6">
					Join at <span class="font-bold text-ink-gray-9">{{ joinUrl }}</span>
				</p>
				<div class="flex flex-wrap items-center justify-center gap-8">
					<p class="text-8xl font-black tracking-widest text-ink-gray-9">
						{{ session.game_pin }}
					</p>
					<img
						v-if="qrDataUrl"
						:src="qrDataUrl"
						alt="Join QR code"
						class="h-44 w-44 rounded-lg"
					/>
				</div>
				<div class="flex flex-wrap items-center justify-center gap-3">
					<Button :variant="lobbyLocked ? 'solid' : 'outline'" @click="toggleLock">
						{{ lobbyLocked ? "Unlock lobby" : "Lock lobby" }}
					</Button>
					<Button
						:variant="autoAdvance ? 'solid' : 'outline'"
						@click="toggleAutoAdvance"
					>
						Auto-advance {{ autoAdvance ? "on" : "off" }}
					</Button>
					<Button
						variant="solid"
						theme="green"
						:disabled="!participants.length"
						@click="start"
					>
						Start game
					</Button>
					<span class="text-ink-gray-6">{{ participants.length }} joined</span>
				</div>
				<div class="flex max-w-4xl flex-wrap justify-center gap-2">
					<button
						v-for="participant in participants"
						:key="participant.name"
						class="group flex items-center gap-3 rounded-full bg-surface-gray-2 py-1 pl-1 pr-5 text-2xl font-medium text-ink-gray-8 hover:bg-surface-red-2"
						title="Click to kick"
						@click="kick(participant)"
					>
						<AvatarPic
							:id="participant.avatar"
							:nickname="participant.nickname"
							:size="48"
						/>
						<span class="group-hover:line-through">{{ participant.nickname }}</span>
					</button>
				</div>
				<p v-if="!participants.length" class="text-ink-gray-5">Waiting for players…</p>
				<ErrorMessage :message="error" />
			</div>
		</template>

		<!-- Podium -->
		<template v-else-if="phase === 'podium'">
			<div class="flex flex-1 flex-col items-center justify-center gap-8 p-6">
				<h1 class="text-5xl font-black text-ink-gray-9">Final results</h1>
				<div class="flex items-end justify-center gap-4">
					<div
						v-for="entry in podiumOrder"
						:key="entry.nickname"
						class="flex w-32 flex-col items-center gap-2"
					>
						<AvatarPic
							:id="entry.avatar"
							:nickname="entry.nickname"
							:size="entry.rank === 1 ? 88 : 64"
						/>
						<span class="text-xl font-bold text-ink-gray-9">{{ entry.nickname }}</span>
						<span class="text-ink-gray-6">{{ entry.score }}</span>
						<div
							class="flex w-full animate-[grow_0.6s_ease-out] items-start justify-center rounded-t-lg pt-2 text-3xl font-black text-white"
							:class="PODIUM_STYLE[entry.rank]"
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
						class="flex items-center justify-between border-b border-outline-gray-1 py-2 text-lg text-ink-gray-7"
					>
						<span class="flex items-center gap-2">
							<AvatarPic :id="entry.avatar" :nickname="entry.nickname" :size="28" />
							{{ entry.rank }}. {{ entry.nickname }}
						</span>
						<span class="font-bold">{{ entry.score }}</span>
					</li>
				</ol>
				<Button variant="outline" @click="reset">New game</Button>
			</div>
		</template>

		<!-- Question / results -->
		<template v-else>
			<!-- m-auto, not justify-center: a centered flex column clips its top when it overflows -->
			<div class="flex flex-1 flex-col p-6">
				<div class="m-auto flex w-full flex-col gap-6">
					<div class="flex items-center justify-between text-lg text-ink-gray-6">
						<span
							>Question {{ (question?.q_index ?? 0) + 1 }} of
							{{ question?.total }}</span
						>
						<span
							v-if="phase === 'question'"
							class="text-2xl font-black text-ink-gray-9"
						>
							{{ Math.ceil(remaining) }}
						</span>
						<span v-if="phase === 'question'">{{ answerCount }} answered</span>
					</div>

					<div
						v-if="phase === 'question'"
						class="h-3 w-full overflow-hidden rounded-full bg-surface-gray-3"
					>
						<div
							class="h-full rounded-full bg-ink-gray-9 transition-[width] duration-100 ease-linear"
							:style="{ width: `${timerPercent}%` }"
						/>
					</div>

					<h1 class="text-center text-4xl font-bold text-ink-gray-9">
						{{ question?.question_text }}
					</h1>

					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
						<div
							v-for="shape in SHAPES.filter(
								(s) => question?.options[Number(s.id) - 1]
							)"
							:key="shape.id"
							class="flex items-center gap-3 rounded-xl p-5 text-xl font-bold text-white transition"
							:class="[shape.fill, dimmed(shape.id) ? 'opacity-30' : '']"
						>
							<svg class="h-8 w-8 shrink-0 fill-white" viewBox="0 0 24 24">
								<path :d="shape.path" />
							</svg>
							<span class="flex-1">{{
								question.options[Number(shape.id) - 1]
							}}</span>
							<span
								v-if="phase === 'closed' && shape.id === String(correctOption)"
								class="text-2xl"
								>✓</span
							>
						</div>
					</div>

					<template v-if="phase === 'closed'">
						<div class="mx-auto flex h-32 w-full max-w-3xl items-stretch gap-4">
							<div
								v-for="shape in SHAPES.filter(
									(s) => question?.options[Number(s.id) - 1]
								)"
								:key="shape.id"
								class="flex flex-1 flex-col justify-end gap-1"
							>
								<span class="text-center text-lg font-bold text-ink-gray-7">
									{{ distribution[shape.id] || 0 }}
								</span>
								<div
									class="rounded-t transition-[height] duration-500"
									:class="shape.fill"
									:style="{ height: `${barHeight(shape.id)}%` }"
								/>
							</div>
						</div>

						<div class="flex flex-wrap items-start justify-between gap-6">
							<ol class="min-w-64 flex-1">
								<li
									v-for="(entry, index) in top5"
									:key="entry.nickname"
									class="flex items-center justify-between border-b border-outline-gray-1 py-2 text-lg text-ink-gray-7"
								>
									<span class="flex items-center gap-2">
										<AvatarPic
											:id="entry.avatar"
											:nickname="entry.nickname"
											:size="28"
										/>
										{{ index + 1 }}. {{ entry.nickname }}
									</span>
									<span class="font-bold">{{ entry.score }}</span>
								</li>
							</ol>
							<ul class="flex-1 space-y-1 text-lg text-ink-gray-7">
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
						<Button v-if="phase === 'question'" variant="outline" @click="skip"
							>Skip</Button
						>
						<Button v-if="phase === 'closed'" variant="solid" @click="next"
							>Next</Button
						>
						<Button
							:variant="autoAdvance ? 'solid' : 'outline'"
							@click="toggleAutoAdvance"
						>
							Auto-advance {{ autoAdvance ? "on" : "off" }}
						</Button>
						<Button variant="outline" theme="red" @click="end">End game</Button>
						<ErrorMessage :message="error" />
					</div>
				</div>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { Button, ErrorMessage } from "frappe-ui";
import QRCode from "qrcode";
import { call } from "@/api";
import { SHAPES, useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";

const PODIUM_STYLE = { 1: "bg-amber-400", 2: "bg-gray-400", 3: "bg-orange-400" };
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
const error = ref("");

const joinUrl = computed(
	() => `${window.location.origin}/quizzly/join?pin=${session.value.game_pin}`
);

const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
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
	}
}

async function applyState(state) {
	session.value = { name: state.session, game_pin: state.game_pin };
	localStorage.setItem(HOSTED_SESSION_KEY, state.session);
	participants.value = state.participants || [];
	lobbyLocked.value = Boolean(state.lobby_locked);
	autoAdvance.value = Boolean(state.auto_advance);
	top5.value = state.top_5 || [];
	qrDataUrl.value = await QRCode.toDataURL(joinUrl.value, { margin: 1, width: 400 });

	if (state.status === "Lobby") {
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
	if (!window.confirm(`Kick ${participant.nickname}?`)) return;
	await hostCall("quizzly.api.kick_participant", { participant: participant.name });
}

const start = () => hostCall("quizzly.api.start_session");
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

<style>
@keyframes grow {
	from {
		height: 0;
	}
}
</style>
