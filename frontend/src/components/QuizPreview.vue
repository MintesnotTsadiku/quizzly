<!-- The quiz on the projector, played from the editor's own state: no session, no players. -->
<template>
	<dialog
		ref="dialog"
		class="qz-dialog h-full max-h-none w-full max-w-none rounded-none border-0 bg-night p-0"
		@cancel.prevent="emit('close')"
		@keydown.left="step(-1)"
		@keydown.right="step(1)"
	>
		<div class="flex h-full flex-col">
			<header
				class="flex shrink-0 items-center gap-4 border-b border-haze px-4 py-3 sm:px-6"
			>
				<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-accent">
					Preview
				</p>
				<p class="ml-auto font-mono text-xs tabular-nums text-paper/40">
					{{ index + 1 }} / {{ beats.length }}
				</p>
				<button class="ctl" @click="emit('close')">Close</button>
			</header>

			<div v-if="beat" class="flex flex-1 flex-col overflow-y-auto p-4 sm:p-8">
				<div class="m-auto flex w-full max-w-6xl flex-col gap-5 sm:gap-7">
					<template v-if="beat.view === 'explanation'">
						<div class="flex flex-col items-center gap-4 text-center sm:gap-6">
							<p class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40">
								Question {{ beat.number }} of {{ questions.length }}
							</p>
							<img
								v-if="beat.question.explanation_image"
								:src="beat.question.explanation_image"
								alt=""
								class="max-h-[28vh] w-full object-contain sm:max-h-[42vh]"
							/>
							<p
								v-if="beat.question.explanation"
								class="max-w-3xl font-display text-xl font-bold leading-snug text-paper sm:text-3xl"
							>
								{{ beat.question.explanation }}
							</p>
						</div>
					</template>

					<template v-else>
						<div class="flex flex-wrap items-center gap-4 sm:gap-6">
							<DrainRing
								v-if="beat.view === 'question'"
								:percent="100"
								:seconds="secondsFor(beat.question)"
								:size="96"
								color="rgb(var(--ok))"
							/>
							<div
								class="order-last w-full min-w-0 sm:order-none sm:w-auto sm:flex-1"
							>
								<p
									class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40"
								>
									Question {{ beat.number }} of {{ questions.length }}
								</p>
								<h1
									class="mt-2 font-display text-2xl font-extrabold leading-tight text-paper sm:text-4xl"
								>
									{{ beat.question.question_text || "Untitled question" }}
								</h1>
							</div>
						</div>

						<img
							v-if="beat.question.image"
							:src="beat.question.image"
							alt=""
							class="max-h-[22vh] w-full object-contain sm:max-h-[40vh]"
						/>

						<AnswerGrid
							:options="optionsOf(beat.question)"
							:correct-option="
								beat.view === 'answer' ? beat.question.correct_option : null
							"
						/>
					</template>
				</div>
			</div>

			<p v-else class="m-auto text-paper/50">
				Nothing to preview yet. Write a question first.
			</p>

			<footer
				class="flex shrink-0 items-center justify-center gap-3 border-t border-haze px-4 py-3"
			>
				<button class="ctl" :disabled="index === 0" @click="step(-1)">← Back</button>
				<button class="ctl ctl-go" :disabled="index >= beats.length - 1" @click="step(1)">
					Next →
				</button>
			</footer>
		</div>
	</dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import AnswerGrid from "@/components/AnswerGrid.vue";
import DrainRing from "@/components/DrainRing.vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	questions: { type: Array, default: () => [] },
	defaultSeconds: { type: Number, default: 20 },
	showExplanation: { type: Boolean, default: false },
	explanationPosition: { type: String, default: "Before Stats" },
});
const emit = defineEmits(["close"]);

const dialog = ref(null);
const index = ref(0);

// Same skip rule as the engine: a question with nothing to explain gets no screen.
const beats = computed(() =>
	props.questions.flatMap((question, position) => {
		const number = position + 1;
		const screens = [{ view: "question", question, number }];
		const explains =
			props.showExplanation && (question.explanation || question.explanation_image);
		if (explains && props.explanationPosition === "Before Stats") {
			screens.push({ view: "explanation", question, number });
		}
		screens.push({ view: "answer", question, number });
		if (explains && props.explanationPosition === "After Stats") {
			screens.push({ view: "explanation", question, number });
		}
		return screens;
	})
);

const beat = computed(() => beats.value[index.value]);

watch(
	() => props.open,
	(open) => {
		if (!open) return dialog.value.close();
		index.value = 0;
		dialog.value.showModal();
	}
);

// An edit that shortens the quiz while the dialog is open must not strand the walk past its end.
watch(beats, (screens) => (index.value = Math.min(index.value, Math.max(0, screens.length - 1))));

const optionsOf = (question) => [1, 2, 3, 4].map((option) => question[`option_${option}`]);

const secondsFor = (question) => question.time_limit || props.defaultSeconds;

function step(by) {
	index.value = Math.min(Math.max(index.value + by, 0), beats.value.length - 1);
}
</script>
