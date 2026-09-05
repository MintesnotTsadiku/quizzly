<template>
	<section class="w-full max-w-2xl rounded-3xl bg-dusk p-6 text-paper">
		<h2 class="font-display text-3xl font-bold">
			{{
				$t(
					ending.story
						? "Our finished story"
						: ending.bracket_history
							? "The room’s champion"
							: "The Lantern Library",
				)
			}}
		</h2>
		<RoomProgress :view="{ ...ending, escape: Boolean(ending.inventory) }" />
		<p v-if="ending.bracket_history?.length" class="my-4 text-3xl">
			🏆 {{ ending.bracket_history.at(-1).winner }}
		</p>
		<button v-if="ending.story" class="ctl mt-4" @click="copy">{{ $t("Copy story") }}</button>
		<p role="status">{{ $t(notice) }}</p>
	</section>
</template>
<script setup>
import { ref } from "vue";
import RoomProgress from "./RoomProgress.vue";
const props = defineProps({ ending: Object });
const notice = ref("");
async function copy() {
	try {
		await navigator.clipboard.writeText(props.ending.story.join("\n\n"));
		notice.value = "Story copied";
	} catch {
		notice.value = "Select the story text to copy it.";
	}
}
</script>
