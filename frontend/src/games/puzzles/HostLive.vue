<template>
	<Board
		v-if="view.puzzle"
		:view="view"
		:busy="busy"
		:error="error"
		@move="move"
		@command="$emit('grid-command', $event)"
	/><Legacy v-else :view="view" />
</template>
<script setup>
import Board from "./Board.vue";
import Legacy from "../round_games/HostLive.vue";
defineProps({ view: Object, busy: Boolean, error: String });
const emit = defineEmits(["grid-command"]);
function move({ action_type, ...payload }) {
	emit("grid-command", { command: action_type, ...payload });
}
</script>
