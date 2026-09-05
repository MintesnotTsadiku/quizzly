<template>
	<Board v-if="view.puzzle" :view="{ ...view, is_screen: true }" /><Legacy v-else :view="view" />
</template>
<script setup>
import Board from "./Board.vue";
import Legacy from "../round_games/ScreenLive.vue";
defineProps({ view: Object });
</script>
