<template>
	<div class="flex w-full max-w-6xl flex-col items-center gap-8 text-center">
		<p class="font-mono uppercase tracking-[.28em] text-accent">
			{{ $t("Round") }} {{ view.round }} / {{ view.total }}
		</p>
		<h1 class="max-w-5xl font-display text-6xl font-extrabold leading-tight text-paper">
			{{ $t(view.prompt) }}
		</h1>
		<RoomProgress :view="view" /><Media :view="view" />
		<div v-if="view.choices?.length" class="grid w-full max-w-5xl grid-cols-2 gap-4">
			<div
				v-for="choice in view.choices"
				:key="choice.id || choice"
				class="rounded-3xl border border-haze bg-dusk p-6 font-display text-3xl font-bold text-paper"
			>
				{{ choice.value || choice }}
			</div>
		</div>
		<Reveal v-if="view.phase === 'round_reveal'" :view="view" />
		<p v-else-if="view.phase === 'seek_review'">
			{{
				$t("Show or describe your find. The host will acknowledge the completed missions.")
			}}
		</p>
		<div v-else class="flex items-center gap-10">
			<DrainRing :percent="timerPercent" :seconds="Math.ceil(remaining)" :size="120" />
			<p class="font-display text-5xl font-extrabold text-paper">
				{{ view.responses || 0
				}}<span class="block font-mono text-xs uppercase tracking-widest text-paper/40">{{
					$t(view.phase === "vote_open" ? "votes" : "responses")
				}}</span>
			</p>
		</div>
	</div>
</template>
<script setup>
import RoomProgress from "./RoomProgress.vue";
import Media from "./Media.vue";
import Reveal from "./Reveal.vue";
import DrainRing from "@/components/DrainRing.vue";
defineProps({
	view: { type: Object, default: () => ({}) },
	remaining: Number,
	timerPercent: Number,
});
</script>
