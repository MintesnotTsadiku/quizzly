<template>
	<div class="flex w-full flex-col items-center gap-10 text-center">
		<template v-if="view.phase === 'intermission'">
			<p class="font-mono text-sm uppercase tracking-[0.3em] text-accent">
				{{ $t("The floor is open") }}
			</p>
			<h2 class="font-display text-6xl font-extrabold text-paper">
				{{ $t("Waiting for the host") }}
			</h2>
			<p class="text-paper/50">{{ $t("The first prompt lands any second.") }}</p>
		</template>

		<template v-else-if="view.phase === 'prompt_open' || view.phase === 'prediction_open'">
			<p class="font-mono text-sm uppercase tracking-[0.3em] text-paper/40">
				{{ $t(view.phase === "prediction_open" ? "Predictions locked in" : "Votes in") }}
			</p>
			<h2
				class="max-w-6xl font-display text-6xl font-extrabold leading-tight text-paper sm:text-7xl"
			>
				{{ view.prompt }}
			</h2>
			<div class="flex max-w-6xl flex-wrap justify-center gap-4">
				<span
					v-for="choice in view.choices || []"
					:key="choice.id"
					class="rounded-2xl border-2 px-8 py-4 font-display text-3xl font-bold text-paper/85"
					:class="choiceBorder(choice.id)"
				>
					{{ choice.text }}
				</span>
			</div>
			<div class="flex items-center gap-16">
				<div class="text-center">
					<p
						class="font-display text-8xl font-extrabold leading-none tabular-nums text-accent"
					>
						{{
							$t(
								view.phase === "prompt_open"
									? (view.voted ?? 0)
									: (view.predicted ?? 0),
							)
						}}
					</p>
					<p class="mt-1 font-mono text-xs uppercase tracking-[0.3em] text-paper/40">
						{{ $t(view.phase === "prompt_open" ? "voted" : "predicted") }}
					</p>
				</div>
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="170"
					:color="remaining <= 5 ? 'rgb(var(--alert))' : 'rgb(var(--ok))'"
				/>
			</div>
		</template>

		<template v-else-if="view.phase === 'reveal'">
			<h2 class="font-display text-6xl font-extrabold text-paper">
				{{ $t(view.quorum_met ? "The room said:" : "Not enough votes to score") }}
			</h2>
			<div class="w-full max-w-5xl">
				<div v-for="choice in view.choices || []" :key="choice.id" class="mb-5">
					<div class="mb-2 flex items-baseline justify-between text-left">
						<span
							class="font-display text-3xl font-bold"
							:class="isPlurality(choice.id) ? 'text-accent' : 'text-paper/70'"
						>
							{{ $t(isPlurality(choice.id) ? "👑 " : "") }}{{ choice.text }}
						</span>
						<span class="font-mono text-2xl tabular-nums text-paper/50">
							{{ (view.distribution || {})[choice.id] || 0 }}
						</span>
					</div>
					<div class="h-8 w-full rounded-full bg-dusk">
						<div
							class="h-8 rounded-full transition-[width] duration-700"
							:class="choiceFill(choice.id)"
							:style="{ width: `${barWidth(choice.id)}%` }"
						/>
					</div>
				</div>
			</div>
			<p class="font-mono text-sm uppercase tracking-[0.3em] text-paper/40">
				{{ view.votes ?? 0 }} {{ $t("votes ·") }} {{ view.predictions ?? 0 }}
				{{ $t("predictions") }}
			</p>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import DrainRing from "@/components/DrainRing.vue";

const props = defineProps({
	view: { type: Object, default: () => ({}) },
	remaining: { type: Number, default: 0 },
	timerPercent: { type: Number, default: 0 },
});

const plurality = computed(() => props.view.plurality || []);
const maxCount = computed(() => Math.max(1, ...Object.values(props.view.distribution || {})));

function isPlurality(choiceId) {
	return plurality.value.includes(choiceId);
}

function barWidth(choiceId) {
	return Math.max(3, (((props.view.distribution || {})[choiceId] || 0) / maxCount.value) * 100);
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
