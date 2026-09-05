<template>
	<Board
		v-if="view.rules_version === 2"
		:view="{ ...view, pin }"
		:busy="busy"
		:error="error"
		@move="$emit('grid-command', { command: 'place_mark', ...$event })"
		@command="$emit('grid-command', $event)"
	/><Legacy v-else v-bind="$attrs" :view="view" />
</template>
<script setup>
import Board from "./Board.vue";
import Legacy from "../round_games/HostLive.vue";
defineProps({ view: Object, pin: String, busy: Boolean, error: String });
defineEmits(["grid-command"]);
</script>
