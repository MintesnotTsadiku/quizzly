<template>
	<button
		type="button"
		class="text-lg leading-none opacity-60 transition hover:opacity-100"
		:aria-label="`Theme: ${theme}`"
		:title="`Theme: ${theme}`"
		@click="cycleTheme"
	>
		{{ ICON[theme] }}
	</button>
</template>

<script setup>
import { cycleTheme, theme } from "@/theme";

const ICON = { auto: "🌗", light: "☀️", dark: "🌙" };
</script>
