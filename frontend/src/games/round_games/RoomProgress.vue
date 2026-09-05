<template>
	<section v-if="view.escape" class="rounded-2xl border border-haze bg-dusk p-4 text-paper">
		<h2>{{ $t("Escape together") }}</h2>
		<p>{{ $t("Clues collected") }}: {{ view.inventory?.join(" → ") || "—" }}</p>
		<p v-if="view.stage_passed === false">
			{{ $t("The door stayed closed. Compare ideas and try this stage again.") }}
		</p>
		<p v-if="view.stage_passed">{{ $t("Door unlocked!") }}</p>
	</section>
	<p v-if="view.clues?.length" class="rounded-2xl bg-dusk p-4 text-2xl text-paper">
		{{ view.clues.join(" · ") }}
	</p>
	<article
		v-if="view.story?.length"
		class="rounded-3xl border border-haze bg-dusk p-5 text-left text-paper"
	>
		<h2 class="text-xl font-bold">{{ $t("Our story so far") }}</h2>
		<p v-for="(line, i) in view.story" :key="i" class="mt-3">{{ line }}</p>
	</article>
	<ol v-if="view.bracket_history?.length" class="flex flex-wrap justify-center gap-3 text-paper">
		<li
			v-for="(match, i) in view.bracket_history"
			:key="i"
			class="rounded-2xl border border-haze bg-dusk p-3"
		>
			<span>{{ match.contenders.join(" / ") }}</span
			><strong class="block">→ {{ match.winner }}</strong
			><small v-if="match.tie">{{ $t("Tie: first seed advances") }}</small>
		</li>
	</ol>
</template>
<script setup>
defineProps({ view: Object });
</script>
