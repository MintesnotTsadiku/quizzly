<template>
	<div v-if="view.media_url" class="w-full">
		<template v-if="view.game_key === 'sound-snap'"
			><audio
				controls
				preload="metadata"
				:src="view.media_url"
				class="mx-auto max-w-full"
				:aria-label="$t('Listen to the clue')" />
			<p class="mt-2 text-sm text-paper/70">
				{{ $t("Play or replay the clip. You can adjust your device volume.") }}
			</p>
			<button v-if="pattern" class="ctl mt-3" @click="showPattern = !showPattern">
				{{ $t("Show visual sound pattern") }}
			</button>
			<div
				v-if="showPattern && pattern"
				class="mx-auto mt-3 flex h-28 max-w-xs items-end justify-around rounded-2xl bg-dusk p-3"
				role="img"
				:aria-label="
					pattern
						.map((n) =>
							$t(n === 1 ? 'Low note' : n === 2 ? 'Middle note' : 'High note'),
						)
						.join(', ')
				"
			>
				<span
					v-for="(n, i) in pattern"
					:key="i"
					:style="{ height: `${n * 25}px` }"
					class="w-10 rounded-lg bg-accent"
				></span></div
		></template>
		<img
			v-else
			:src="view.media_url"
			:alt="$t(altText)"
			:data-clue="view.phase === 'memory_study' ? 'study' : 'round'"
			class="mx-auto max-h-[38vh] rounded-3xl object-contain"
		/>
	</div>
</template>
<script setup>
import { computed, ref, watch } from "vue";
const props = defineProps({ view: Object });
const showPattern = ref(false);
const pattern = computed(
	() =>
		({ "ascending.wav": [1, 2, 3], "descending.wav": [3, 2, 1], "steady.wav": [2, 2, 2] })[
			props.view.media_url?.split("/").at(-1)
		],
);
watch(
	() => props.view.media_url,
	() => (showPattern.value = false),
);

const altText = computed(
	() =>
		({
			"memory.svg":
				"One red square at the upper left, two yellow circles at the upper right, and two green triangles below.",
			"umbrella.svg": "A wide domed canopy on a long handle with a curved end.",
			"bicycle.svg":
				"Two large wheels joined by a frame, with pedals, a seat and handlebars.",
			"key.svg": "A metal ring joined to a long shaft with two teeth at the end.",
			"caption.svg": "An empty purple chair holds the string of an orange kite above it.",
		})[props.view.media_url?.split("/").at(-1)] ||
		(props.view.phase === "memory_study" ? "Study this scene" : "Round clue"),
);
</script>
