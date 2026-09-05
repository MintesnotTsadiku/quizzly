<template>
	<div class="flex w-full max-w-lg flex-col items-center gap-5 text-center">
		<p class="font-mono uppercase tracking-[.24em] text-accent">
			{{ $t("Round") }} {{ view.round }} / {{ view.total }}
		</p>
		<template v-if="view.phase === 'draw_ready'"
			><h1 class="font-display text-4xl font-extrabold text-paper">
				{{ view.is_artist ? "You are the artist!" : `${view.artist?.nickname} is up` }}
			</h1>
			<p
				v-if="view.is_artist"
				class="rounded-2xl bg-dusk px-6 py-4 font-display text-3xl font-bold text-paper"
			>
				{{ view.prompt }}
			</p></template
		><template v-else-if="view.phase === 'draw_open'"
			><div class="flex w-full items-center justify-between">
				<h1 class="font-display text-2xl font-bold text-paper">
					{{ $t(view.is_artist ? view.prompt : "What is it?") }}
				</h1>
				<DrainRing :percent="timerPercent" :seconds="Math.ceil(remaining)" :size="62" />
			</div>
			<DrawingCanvas
				:strokes="view.strokes || []"
				:interactive="view.is_artist"
				@batch="$emit('draw', $event)"
			/><button v-if="view.is_artist" class="ctl" @click="$emit('clear')">
				{{ $t("Clear canvas") }}
			</button>
			<form v-else class="flex w-full gap-2" @submit.prevent="sendGuess">
				<input
					v-model="guess"
					class="field min-w-0 flex-1"
					:placeholder="$t('Type your guess')"
					maxlength="60"
					:aria-label="$t('Your guess')"
				/><button class="ctl ctl-go" :disabled="!guess.trim() || submitting">
					{{ $t("Guess") }}
				</button>
			</form>
			<p v-if="result" :class="result.correct ? 'text-ok' : 'text-paper/45'">
				{{ $t(result.correct ? "Correct — nice one!" : "Not yet. Try again.") }}
			</p></template
		><template v-else
			><h1 class="font-display text-4xl font-extrabold text-paper">{{ view.answer }}</h1>
			<p class="text-paper/50">{{ $t("The answer is revealed.") }}</p></template
		>
	</div>
</template>
<script setup>
import { ref } from "vue";
import DrainRing from "@/components/DrainRing.vue";
import DrawingCanvas from "./DrawingCanvas.vue";
defineProps({
	view: { type: Object, default: () => ({}) },
	remaining: Number,
	timerPercent: Number,
	submitting: Boolean,
});
const emit = defineEmits(["draw", "guess", "clear"]);
const guess = ref("");
const result = ref(null);
function sendGuess() {
	if (!guess.value.trim()) return;
	emit("guess", {
		guess: guess.value,
		done: (r) => {
			result.value = r;
			if (r?.correct) guess.value = "";
		},
	});
}
</script>
