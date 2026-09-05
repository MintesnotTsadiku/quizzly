<template>
	<Board
		v-if="view.rules_version === 2"
		:view="view"
		:busy="submitting"
		:error="error"
		@move="$emit('submit', { action_type: 'place_mark', ...$event })"
	/><Legacy
		v-else
		v-bind="$attrs"
		:view="view"
		:submitting="submitting"
		@submit="$emit('submit', $event)"
	/>
</template>
<script setup>
import Board from "./Board.vue";
import Legacy from "../round_games/PlayerLive.vue";
defineProps({ view: Object, submitting: Boolean, error: String });
defineEmits(["submit"]);
</script>
