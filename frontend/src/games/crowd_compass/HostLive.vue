<template>
	<div class="flex w-full flex-col items-center gap-8 text-center">
		<template v-if="view.phase === 'intermission'">
			<p class="font-mono uppercase tracking-[0.28em] text-accent">The floor is open</p>
			<h2 class="font-display text-4xl font-extrabold text-paper">Waiting for the first prompt</h2>
			<p class="max-w-md text-paper/50">
				Compose one below — the room starts the moment you push it.
			</p>
			<button class="ctl ctl-go" @click="$emit('compose')">Compose a prompt</button>
		</template>

		<template v-else-if="view.phase === 'prompt_open' || view.phase === 'prediction_open'">
			<p class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40">
				Prompt {{ (view.turn ?? 0) + 1 }} of {{ view.total || "?" }}
				{{ view.phase === "prediction_open" ? "· predictions" : "· voting" }}
			</p>
			<h2 class="max-w-4xl font-display text-4xl font-extrabold leading-tight text-paper sm:text-5xl">
				{{ view.prompt }}
			</h2>
			<div class="flex max-w-4xl flex-wrap justify-center gap-3">
				<span
					v-for="choice in view.choices || []"
					:key="choice.id"
					class="rounded-2xl border px-5 py-2.5 font-display text-lg font-bold text-paper/80"
					:class="choiceBorder(choice.id)"
				>
					{{ choice.text }}
				</span>
			</div>
			<div class="flex items-center gap-10">
				<div class="text-center">
					<p class="font-display text-5xl font-extrabold tabular-nums text-paper">
						{{ view.phase === "prompt_open" ? view.voted ?? 0 : view.predicted ?? 0 }}
					</p>
					<p class="font-mono text-[11px] uppercase tracking-[0.25em] text-paper/40">
						{{ view.phase === "prompt_open" ? "voted" : "predicted" }}
					</p>
				</div>
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="96"
					:color="remaining <= 5 ? 'rgb(var(--alert))' : 'rgb(var(--ok))'"
				/>
			</div>
			<p class="max-w-md text-sm text-paper/40">
				{{ view.phase === "prediction_open"
					? "The distribution stays sealed until everyone locks in."
					: "Phones out — the reveal stays a surprise." }}
			</p>
		</template>

		<template v-else-if="view.phase === 'reveal'">
			<h2 class="font-display text-4xl font-extrabold text-paper sm:text-5xl">
				{{ view.quorum_met ? "The room said:" : "Not enough votes to score" }}
			</h2>
			<div class="w-full max-w-3xl">
				<div
					v-for="choice in view.choices || []"
					:key="choice.id"
					class="mb-3"
				>
					<div class="mb-1 flex items-baseline justify-between text-left">
						<span class="font-display text-lg font-bold" :class="isPlurality(choice.id) ? 'text-accent' : 'text-paper/70'">
							{{ isPlurality(choice.id) ? "👑 " : "" }}{{ choice.text }}
						</span>
						<span class="font-mono text-sm tabular-nums text-paper/50">
							{{ (view.distribution || {})[choice.id] || 0 }}
						</span>
					</div>
					<div class="h-5 w-full rounded-full bg-dusk">
						<div
							class="h-5 rounded-full transition-[width] duration-700"
							:class="choiceFill(choice.id)"
							:style="{ width: `${barWidth(choice.id)}%` }"
						/>
					</div>
				</div>
			</div>
			<p class="font-mono text-xs uppercase tracking-[0.25em] text-paper/40">
				{{ view.votes ?? 0 }} votes · {{ view.predictions ?? 0 }} predictions
			</p>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import DrainRing from "@/components/DrainRing.vue";
import { teamStyle } from "@/platform/session/gp";

const props = defineProps({
	view: { type: Object, default: () => ({}) },
	remaining: { type: Number, default: 0 },
	timerPercent: { type: Number, default: 0 },
});

defineEmits(["compose"]);

const plurality = computed(() => props.view.plurality || []);
const maxCount = computed(() =>
	Math.max(1, ...Object.values(props.view.distribution || {}))
);

function isPlurality(choiceId) {
	return plurality.value.includes(choiceId);
}

function barWidth(choiceId) {
	return Math.max(3, ((props.view.distribution || {})[choiceId] || 0) / maxCount.value * 100);
}

function choiceFill(choiceId) {
	const index = Number(choiceId) - 1;
	const palette = ["bg-ember", "bg-lagoon", "bg-gold", "bg-orchid"];
	return palette[index] || "bg-haze";
}

function choiceBorder(choiceId) {
	const index = Number(choiceId) - 1;
	const palette = ["border-ember", "border-lagoon", "border-gold", "border-orchid"];
	return palette[index] || "border-haze";
}
</script>
