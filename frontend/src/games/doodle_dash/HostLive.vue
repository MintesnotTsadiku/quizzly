<template>
	<ScreenLive :view="view" :remaining="remaining" :timer-percent="timerPercent" />
</template>
<script setup>
import ScreenLive from "./ScreenLive.vue";
defineProps({ view: Object, remaining: Number, timerPercent: Number });
</script>
