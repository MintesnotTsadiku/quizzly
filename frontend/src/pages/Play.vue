<template>
	<div class="flex h-full flex-col bg-surface-white">
		<header
			v-if="player && phase !== 'kicked'"
			class="flex items-center justify-between border-b border-outline-gray-1 px-4 py-2"
		>
			<span class="flex min-w-0 items-center gap-2">
				<AvatarPic :id="player.avatar" :nickname="player.nickname" :size="32" />
				<span class="truncate text-base font-semibold text-ink-gray-8">{{
					player.nickname
				}}</span>
			</span>
			<span class="flex items-center gap-2">
				<button
					type="button"
					class="text-lg leading-none text-ink-gray-6 hover:text-ink-gray-9"
					:aria-label="muted ? 'Unmute sound' : 'Mute sound'"
					@click="toggleMute"
				>
					{{ muted ? "🔇" : "🔊" }}
				</button>
				<span
					class="rounded-full bg-surface-gray-3 px-3 py-1 text-sm font-bold text-ink-gray-8"
				>
					{{ score }}
				</span>
			</span>
		</header>

		<main class="flex flex-1 flex-col items-center justify-center gap-6 p-4 text-center">
			<template v-if="phase === 'kicked'">
				<p class="text-2xl font-bold text-ink-gray-8">
					The host removed you from the game.
				</p>
				<Button variant="solid" size="lg" @click="router.replace('/join')"
					>Back to join</Button
				>
			</template>

			<template v-else-if="phase === 'lobby'">
				<p class="text-sm uppercase tracking-widest text-ink-gray-5">
					PIN {{ player.pin }}
				</p>
				<h1 class="text-4xl font-black text-ink-gray-9">You're in!</h1>
				<p class="text-ink-gray-6">
					See your name on the big screen. Waiting for the host…
				</p>
				<p class="text-sm text-ink-gray-5">{{ participants.length }} in the lobby</p>
				<Button variant="outline" @click="leave">Leave game</Button>
			</template>

			<template v-else-if="phase === 'get_ready'">
				<p class="text-sm uppercase tracking-widest text-ink-gray-5">
					Question {{ (qIndex ?? 0) + 1 }} of {{ total }}
				</p>
				<h1 class="max-w-xl text-2xl font-bold text-ink-gray-9">{{ questionText }}</h1>
				<div
					class="flex h-24 w-24 items-center justify-center rounded-full bg-surface-gray-3 text-5xl font-black text-ink-gray-9"
				>
					{{ Math.ceil(remaining) }}
				</div>
				<p class="text-ink-gray-6">Get ready…</p>
			</template>

			<template v-else-if="phase === 'question'">
				<div class="w-full max-w-2xl">
					<div class="mb-2 flex items-baseline justify-between text-sm text-ink-gray-5">
						<span>Question {{ qIndex + 1 }} of {{ total }}</span>
						<span class="font-bold text-ink-gray-8">{{ Math.ceil(remaining) }}s</span>
					</div>
					<div class="h-2 w-full overflow-hidden rounded-full bg-surface-gray-3">
						<div
							class="h-full rounded-full bg-ink-gray-9 transition-[width] duration-100 ease-linear"
							:style="{ width: `${timerPercent}%` }"
						/>
					</div>
				</div>
				<h1 class="max-w-2xl text-2xl font-bold text-ink-gray-9">
					{{ question.question_text }}
				</h1>
				<div class="grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
					<button
						v-for="optionId in orderedOptions"
						:key="optionId"
						class="flex items-center gap-3 rounded-xl p-4 text-left text-lg font-bold text-white shadow-sm transition active:scale-95"
						:class="[shapeFor(optionId).fill, shapeFor(optionId).hover]"
						@click="answer(optionId)"
					>
						<svg class="h-7 w-7 shrink-0 fill-white" viewBox="0 0 24 24">
							<path :d="shapeFor(optionId).path" />
						</svg>
						<span>{{ question.options[Number(optionId) - 1] }}</span>
					</button>
				</div>
				<ErrorMessage :message="error" />
			</template>

			<template v-else-if="phase === 'locked'">
				<svg
					v-if="selected"
					class="h-24 w-24"
					:class="shapeFor(selected).fill.replace('bg-', 'fill-')"
					viewBox="0 0 24 24"
				>
					<path :d="shapeFor(selected).path" />
				</svg>
				<h1 class="text-3xl font-black text-ink-gray-9">Locked in!</h1>
				<p class="text-ink-gray-6">Look up at the big screen.</p>
			</template>

			<template v-else-if="phase === 'result'">
				<div
					class="flex h-24 w-24 items-center justify-center rounded-full text-5xl"
					:class="result.is_correct ? 'bg-surface-green-3' : 'bg-surface-red-3'"
				>
					{{ result.is_correct ? "✓" : "✕" }}
				</div>
				<h1 class="text-3xl font-black text-ink-gray-9">
					{{ result.is_correct ? "Correct!" : result.answered ? "Wrong" : "No answer" }}
				</h1>
				<p v-if="result.points" class="text-2xl font-bold text-ink-green-3">
					+{{ result.points }}
				</p>
				<p v-if="result.streak > 1" class="text-ink-gray-6">
					{{ result.streak }} answer streak 🔥
				</p>
				<p class="text-ink-gray-6">Rank {{ result.rank }} · {{ result.score }} points</p>
				<ul class="w-full max-w-xs text-left">
					<li
						v-for="(entry, index) in result.top_5"
						:key="entry.nickname"
						class="flex items-center justify-between border-b border-outline-gray-1 py-1 text-sm"
						:class="
							entry.nickname === player.nickname
								? 'font-bold text-ink-gray-9'
								: 'text-ink-gray-6'
						"
					>
						<span class="flex items-center gap-2">
							<AvatarPic :id="entry.avatar" :nickname="entry.nickname" :size="24" />
							{{ index + 1 }}. {{ entry.nickname }}
						</span>
						<span>{{ entry.score }}</span>
					</li>
				</ul>
			</template>

			<template v-else-if="phase === 'podium'">
				<h1 class="text-4xl font-black text-ink-gray-9">
					{{ myRank === 1 ? "You won! 🏆" : `You finished #${myRank}` }}
				</h1>
				<p class="text-2xl font-bold text-ink-gray-8">{{ score }} points</p>
				<ul class="w-full max-w-xs text-left">
					<li
						v-for="entry in leaderboard.slice(0, 5)"
						:key="entry.nickname"
						class="flex items-center justify-between border-b border-outline-gray-1 py-1"
						:class="
							entry.nickname === player.nickname
								? 'font-bold text-ink-gray-9'
								: 'text-ink-gray-6'
						"
					>
						<span class="flex items-center gap-2">
							<AvatarPic :id="entry.avatar" :nickname="entry.nickname" :size="24" />
							{{ entry.rank }}. {{ entry.nickname }}
						</span>
						<span>{{ entry.score }}</span>
					</li>
				</ul>
				<Button variant="outline" @click="playAgain">Back to join</Button>
			</template>

			<template v-else>
				<p class="text-lg text-ink-gray-6">Hang tight…</p>
			</template>
		</main>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Button, ErrorMessage } from "frappe-ui";
import { call } from "@/api";
import { clearPlayer, loadPlayer } from "@/player";
import { optionOrder, shapeFor, useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";
import { initSound, muted, playCue, toggleMute } from "@/sound";

const router = useRouter();
const socket = inject("$socket");
const {
	remaining,
	total: windowSeconds,
	start: startCountdown,
	stop: stopCountdown,
} = useCountdown();

const player = ref(loadPlayer());
const phase = ref("lobby");
const participants = ref(player.value?.participants || []);
const question = ref(null);
const questionText = ref("");
const qIndex = ref(0);
const total = ref(0);
const selected = ref(null);
const score = ref(0);
const result = ref({});
const leaderboard = ref([]);
const myRank = ref(0);
const error = ref("");

watch(
	() => Math.ceil(remaining.value),
	(secondsLeft) => {
		if (phase.value === "question" && secondsLeft > 0 && secondsLeft <= 5) playCue("tick");
	}
);

const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
);

const orderedOptions = computed(() =>
	question.value ? optionOrder(question.value, player.value.token) : []
);

function onSessionEvent(message) {
	if (message.type === "lobby_update") {
		participants.value = message.participants;
	} else if (message.type === "kicked" && message.participant === player.value.participant) {
		clearPlayer();
		stopCountdown();
		phase.value = "kicked";
	} else if (message.type === "get_ready") {
		showGetReady(message.question_text, message.q_index, message.total, message.seconds);
	} else if (message.type === "question") {
		showQuestion(message, message.window_ms / 1000);
	} else if (message.type === "question_closed") {
		showResult(message);
	} else if (message.type === "podium") {
		showPodium(message.leaderboard);
	} else if (message.type === "session_ended") {
		phase.value = "waiting";
	}
}

function showGetReady(text, index, questionTotal, seconds) {
	questionText.value = text;
	qIndex.value = index;
	total.value = questionTotal;
	phase.value = "get_ready";
	startCountdown(seconds);
}

function showQuestion(payload, remainingSeconds) {
	question.value = payload;
	qIndex.value = payload.q_index;
	total.value = payload.total;
	selected.value = null;
	error.value = "";
	phase.value = "question";
	startCountdown(remainingSeconds);
}

async function showResult(closedMessage) {
	stopCountdown();
	result.value = await call("quizzly.api.get_result", {
		pin: player.value.pin,
		token: player.value.token,
		question_row: closedMessage.question_row,
	});
	score.value = result.value.score;
	phase.value = "result";
	playCue(result.value.is_correct ? "correct" : "wrong");
}

function showPodium(entries) {
	stopCountdown();
	leaderboard.value = entries || [];
	myRank.value =
		leaderboard.value.find((entry) => entry.nickname === player.value.nickname)?.rank || 0;
	phase.value = "podium";
	playCue("podium");
}

async function answer(optionId) {
	selected.value = optionId;
	phase.value = "locked";
	stopCountdown();
	playCue("submit");
	try {
		await call("quizzly.api.submit_answer", {
			pin: player.value.pin,
			token: player.value.token,
			question_row: question.value.question_row,
			selected_option: optionId,
		});
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
		selected.value = null;
	}
}

async function restore() {
	const state = await call("quizzly.api.get_state", {
		pin: player.value.pin,
		token: player.value.token,
	});
	score.value = state.score;
	if (state.status === "Lobby") {
		participants.value = state.participants;
		phase.value = "lobby";
		return;
	}
	if (state.status === "Ended") {
		showPodium(state.leaderboard);
		return;
	}
	if (state.phase === "get_ready") {
		showGetReady(
			state.question.question_text,
			state.q_index,
			state.total,
			state.remaining_seconds
		);
	} else if (state.phase === "question") {
		showQuestion(state.question, state.remaining_seconds);
		if (state.answered) {
			phase.value = "locked";
			stopCountdown();
		}
	} else if (state.phase === "closed") {
		await showResult({ question_row: state.question.question_row });
	} else {
		phase.value = "waiting";
	}
}

onMounted(() => {
	initSound("player");
	if (!player.value) {
		router.replace("/join");
		return;
	}
	useSessionRoom(socket, player.value.pin, onSessionEvent, safeRestore);
});

async function safeRestore() {
	try {
		await restore();
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	}
}

async function leave() {
	try {
		await call("quizzly.api.leave_session", {
			pin: player.value.pin,
			token: player.value.token,
		});
	} catch {
		// leaving anyway
	}
	playAgain();
}

function playAgain() {
	clearPlayer();
	router.replace("/join");
}
</script>
