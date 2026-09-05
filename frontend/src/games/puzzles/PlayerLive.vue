<template>
	<Board
		v-if="view.puzzle"
		:view="view"
		:busy="submitting"
		:error="error"
		@move="$emit('submit', $event)"
	/><Legacy v-else :view="view" :submitting="submitting" @submit="$emit('submit', $event)" />
</template>
<script setup>
import Board from "./Board.vue";
import Legacy from "../round_games/PlayerLive.vue";
defineProps({ view: Object, submitting: Boolean, error: String });
defineEmits(["submit"]);
</script>
