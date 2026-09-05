<template>
	<div class="flex w-full flex-col items-center gap-6 text-center">
		<template v-if="view.phase === 'intermission'">
			<p class="font-mono uppercase tracking-[0.28em] text-accent">
				{{ $t("Any second now") }}
			</p>
			<h1 class="font-display text-4xl font-extrabold text-paper">
				{{ $t("The host is writing…") }}
			</h1>
			<p class="text-paper/50">{{ $t("Keep this open — you'll vote right here.") }}</p>
		</template>

		<!-- Voting -->
		<template v-else-if="view.phase === 'prompt_open'">
			<div class="flex w-full items-center justify-between px-2">
				<span class="font-mono text-xs uppercase tracking-[0.22em] text-paper/45">
					{{ view.voted ?? 0 }} {{ $t("voted") }}
				</span>
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="56"
					:color="urgentColor"
				/>
			</div>
			<h1
				class="mt-1 max-w-md font-display text-3xl font-extrabold leading-tight text-paper sm:text-4xl"
			>
				{{ view.prompt }}
			</h1>
			<p v-if="ranked" class="-mt-2 font-mono uppercase tracking-widest text-paper/35">
				{{ $t(secondPick ? "Now your second choice" : "Pick your first choice") }}
			</p>

			<div class="grid w-full max-w-md grid-cols-2 gap-3">
				<button
					v-for="choice in view.choices || []"
					:key="choice.id"
					class="flex min-h-24 flex-col items-center justify-center gap-1 rounded-3xl p-4 font-display text-xl font-extrabold transition active:scale-95"
					:class="voteClasses(choice.id)"
					:disabled="submitting || voteLocked"
					@click="pick(choice.id)"
				>
					<svg class="h-7 w-7" :class="voteSvgFill(choice.id)" viewBox="0 0 24 24">
						<path :d="shapeFor(choice.id).path" />
					</svg>
					{{ choice.text }}
				</button>
			</div>
			<p v-if="voteLocked" class="font-display text-2xl font-extrabold text-ok">
				{{ $t("Vote locked ✓") }}
			</p>
			<p v-if="error" class="text-sm text-alert">{{ $t(error) }}</p>
		</template>

		<!-- Prediction -->
		<template v-else-if="view.phase === 'prediction_open'">
			<div class="flex w-full items-center justify-between px-2">
				<span class="font-mono text-xs uppercase tracking-[0.22em] text-paper/45">
					{{ view.predicted ?? 0 }} {{ $t("predicted") }}
				</span>
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="56"
					:color="urgentColor"
				/>
			</div>
			<h1
				class="mt-1 max-w-md font-display text-3xl font-extrabold leading-tight text-paper sm:text-4xl"
			>
				{{ view.prompt }}
			</h1>
			<p class="-mt-2 font-mono uppercase tracking-widest text-accent">
				{{ $t("Predict the room 👑") }}
			</p>

			<template v-if="!predictLocked">
				<div class="grid w-full max-w-md grid-cols-2 gap-3">
					<button
						v-for="choice in view.choices || []"
						:key="choice.id"
						class="flex min-h-20 items-center justify-center gap-2 rounded-3xl border-2 p-4 font-display text-lg font-bold transition active:scale-95"
						:class="
							predictionPick === choice.id
								? [choiceFill(choice.id), 'border-transparent text-sunk']
								: 'border-haze text-paper/80'
						"
						@click="predictionPick = choice.id"
					>
						{{ choice.text }}
					</button>
				</div>

				<div
					v-if="view.estimation"
					class="w-full max-w-md rounded-3xl border border-haze bg-dusk p-5"
				>
					<div class="flex items-baseline justify-between">
						<span
							class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
						>
							"{{ predictedLabel }} {{ $t('" will take…') }}
						</span>
						<span class="font-display text-2xl font-extrabold tabular-nums text-accent"
							>{{ estimate }}%</span
						>
					</div>
					<input
						v-model.number="estimate"
						type="range"
						min="0"
						max="100"
						step="5"
						class="mt-3 w-full accent-[rgb(var(--accent))]"
					/>
					<p class="mt-1 text-left text-xs text-paper/40">
						{{ $t("Within 3 points scores +300 · 7 → +150 · 12 → +50") }}
					</p>
				</div>

				<button
					class="rounded-2xl bg-ember px-10 py-4 font-display text-xl font-extrabold text-sunk transition active:scale-[0.98]"
					:class="!predictionPick || submitting ? 'opacity-50' : ''"
					:disabled="!predictionPick || submitting"
					@click="submitPrediction"
				>
					{{ $t("Lock prediction") }}
				</button>
			</template>
			<template v-else>
				<p class="font-display text-2xl font-extrabold text-ok">
					{{ $t("Prediction locked ✓") }}
				</p>
				<p class="text-sm text-paper/40">
					{{ $t("You said") }} <b>{{ predictedLabel }}</b>
					<template v-if="view.estimation"> · {{ myEstimate ?? estimate }}%</template>
				</p>
			</template>
			<p v-if="error" class="text-sm text-alert">{{ $t(error) }}</p>
		</template>

		<!-- Reveal -->
		<template v-else-if="view.phase === 'reveal'">
			<h1 class="font-display text-4xl font-extrabold text-paper">{{ headline }}</h1>
			<p v-if="myPoints" class="font-display text-3xl font-bold text-accent">
				+{{ myPoints }} {{ $t("pts") }}
			</p>
			<p v-else class="text-paper/50">
				{{ $t("No points this round — get the next one.") }}
			</p>
			<div class="flex w-full max-w-md flex-col gap-2">
				<div
					v-for="choice in view.choices || []"
					:key="choice.id"
					class="flex items-center justify-between rounded-2xl border px-4 py-3"
					:class="isPlurality(choice.id) ? 'border-accent' : 'border-haze'"
				>
					<span
						class="text-left"
						:class="myVote === choice.id ? 'font-bold text-paper' : 'text-paper/60'"
					>
						{{ $t(isPlurality(choice.id) ? "👑 " : "") }}{{ choice.text }}
						<span v-if="myVote === choice.id" class="ml-1 text-xs text-paper/40">
							{{ $t("· you") }}
						</span>
					</span>
					<span class="font-mono tabular-nums text-paper/60">
						{{ (view.distribution || {})[choice.id] || 0 }}
					</span>
				</div>
			</div>
			<p class="text-sm text-paper/40">
				{{ $t("Scoreboard next — watch the big screen.") }}
			</p>
		</template>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import DrainRing from "@/components/DrainRing.vue";
import { shapeFor } from "@/game";

const props = defineProps({
	view: { type: Object, default: () => ({}) },
	remaining: { type: Number, default: 0 },
	timerPercent: { type: Number, default: 0 },
	myVote: { type: String, default: null },
	mySecond: { type: String, default: null },
	myPrediction: { type: String, default: null },
	myEstimate: { type: Number, default: null },
	myPoints: { type: Number, default: 0 },
	submitting: { type: Boolean, default: false },
});

const emit = defineEmits(["vote", "predict"]);

const error = ref("");
const ranked = computed(() => Boolean(props.view.ranked));
const firstPick = ref(null);
const secondPick = ref(null);
const predictionPick = ref(null);
const estimate = ref(50);
const voteLocked = ref(false);
const predictLocked = ref(false);

const urgentColor = computed(() =>
	props.remaining <= 5 ? "rgb(var(--alert))" : "rgb(var(--ok))",
);
const predictedLabel = computed(() => {
	const choice = (props.view.choices || []).find(
		(c) => c.id === (props.myPrediction || predictionPick.value),
	);
	return choice?.text || "";
});
const headline = computed(() => {
	const correct =
		props.myPrediction && (props.view.plurality || []).includes(props.myPrediction);
	if (correct) return "You read the room!";
	if (props.myPrediction) return "The room disagreed";
	return "You sat this one out";
});

function isPlurality(choiceId) {
	return (props.view.plurality || []).includes(choiceId);
}

function voteClasses(choiceId) {
	const shape = shapeFor(choiceId);
	if (props.myVote === choiceId || voteLocked.value) return [shape.fill, "text-sunk"];
	if (firstPick.value === choiceId) return ["border-2 border-accent", "text-paper"];
	if (secondPick.value === choiceId)
		return ["border-2 border-dashed border-accent", "text-paper/80"];
	return ["border-2 border-haze", "text-paper/85", "hover:border-paper"];
}

function voteSvgFill(choiceId) {
	const shape = shapeFor(choiceId);
	if (props.myVote === choiceId || voteLocked.value) return "fill-sunk/55";
	return shape.svgFill;
}

function choiceFill(choiceId) {
	return shapeFor(choiceId).fill;
}

function pick(choiceId) {
	if (voteLocked.value || props.submitting) return;
	error.value = "";
	if (!ranked.value) {
		firstPick.value = choiceId;
		voteLocked.value = true;
		emit("vote", { choice: choiceId });
		return;
	}
	if (!firstPick.value) {
		firstPick.value = choiceId;
		return;
	}
	if (secondPick.value) return;
	if (choiceId === firstPick.value) {
		error.value = "Second choice must differ";
		return;
	}
	secondPick.value = choiceId;
	voteLocked.value = true;
	emit("vote", { choice: firstPick.value, second: choiceId });
}

function submitPrediction() {
	if (!predictionPick.value || props.submitting) return;
	error.value = "";
	predictLocked.value = true;
	emit("predict", {
		choice: predictionPick.value,
		...(props.view.estimation ? { estimate: estimate.value } : {}),
	});
}

// fresh round: clear local picks when the prompt changes
watch(
	() => props.view.turn,
	() => {
		firstPick.value = null;
		secondPick.value = null;
		predictionPick.value = null;
		voteLocked.value = false;
		predictLocked.value = false;
		error.value = "";
	},
);
</script>
