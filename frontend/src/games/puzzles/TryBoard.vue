<template>
	<div class="flex flex-col gap-4">
		<p class="gp-eyebrow">{{ $t("Try the actual board") }} · {{ $t("Example only") }}</p>
		<Board
			v-if="puzzle"
			:view="{ puzzle, can_move: true, control_mode: 'shared', revision: actions.length }"
			:busy="busy"
			:error="error"
			@move="move"
		/>
		<p v-else-if="error" role="alert">{{ error }}</p>
		<button class="gp-button secondary" @click="reset" :disabled="busy">
			{{ $t("Reset practice board") }}
		</button>
	</div>
</template>
<script setup>
import { ref, watch } from "vue";
import { call, readError } from "@/api";
import Board from "./Board.vue";
const props = defineProps({ gameKey: String });
const puzzle = ref(null),
	actions = ref([]),
	busy = ref(false),
	error = ref("");
async function load(next) {
	busy.value = true;
	error.value = "";
	try {
		puzzle.value = await call("quizzly.games.puzzles.api.practice", {
			game_key: props.gameKey,
			actions: next,
		});
		actions.value = next;
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
function move({ action_type, revision, ...payload }) {
	load([...actions.value, { action: action_type, payload }]);
}
function reset() {
	load([]);
}
watch(() => props.gameKey, reset, { immediate: true });
</script>
