<template>
	<Board v-if="view.rules_version === 2" :view="{ ...view, pin }" screen /><Legacy
		v-else
		v-bind="$attrs"
		:view="view"
	/>
</template>
<script setup>
import Board from "./Board.vue";
import Legacy from "../round_games/ScreenLive.vue";
defineProps({ view: Object, pin: String });
</script>
