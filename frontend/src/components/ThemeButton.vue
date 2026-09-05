<template>
	<!-- Unstyled on purpose: the host wears this as a `ctl` pill and the players
	     as a bare header icon. Only the glyph and the cycling are shared. -->
	<button
		v-if="!embedded"
		type="button"
		:aria-label="`Theme: ${theme}`"
		:title="`Theme: ${theme}`"
		@click="cycleTheme"
	>
		{{ ICON[theme] }}
	</button>
</template>

<script setup>
import { cycleTheme, theme, embedded } from "@/theme";

const ICON = { auto: "🌗", light: "☀️", dark: "🌙" };
</script>
