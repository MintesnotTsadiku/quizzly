<template>
	<section
		class="w-full rounded-3xl border border-haze bg-dusk p-5 text-paper"
		aria-live="polite"
	>
		<h2 class="font-display text-2xl font-bold">{{ $t("Reveal") }}</h2>
		<p v-if="view.answer && view.mechanic !== 'creative'" class="my-3 text-2xl">
			{{ view.answer }}
		</p>
		<p v-if="view.target != null" class="my-3 text-2xl">
			{{ $t("Target") }}: {{ view.target }}
		</p>
		<p v-if="view.truth" class="my-3">{{ $t("The truth") }}: {{ view.truth }}</p>
		<ol class="flex flex-col gap-3 text-left">
			<li
				v-for="(result, i) in view.results || []"
				:key="i"
				class="rounded-2xl bg-white/5 p-4"
			>
				<p v-if="result.value" class="text-xl">
					{{ Array.isArray(result.value) ? result.value.join(" → ") : result.value }}
				</p>
				<p>
					{{ result.nickname || $t("Player")
					}}<span v-if="result.confirmed != null">
						· {{ $t(result.confirmed ? "Room confirmed" : "Not confirmed") }}</span
					>
					<span v-if="result.votes != null && view.game_key !== 'seek-and-show'"
						>· {{ result.votes }} {{ $t("votes") }}</span
					><span v-if="result.distance != null">
						· {{ $t("Distance") }}: {{ result.distance }}</span
					><span v-if="result.points != null">
						· +{{ result.points }} {{ $t("points") }}</span
					><span v-if="result.correct != null">
						· {{ $t(result.correct ? "Correct" : "Try the next round") }}</span
					>
				</p>
			</li>
		</ol>
	</section>
</template>
<script setup>
defineProps({ view: Object });
</script>
