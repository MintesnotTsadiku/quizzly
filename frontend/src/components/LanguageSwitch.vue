<template>
	<div class="gp-language" role="group" :aria-label="$t('Language')">
		<button
			v-for="language in languages"
			:key="language.code"
			type="button"
			:lang="language.code"
			:aria-pressed="locale === language.code"
			@click="setLanguage(language.code)"
		>
			{{ language.label }}
		</button>
	</div>
</template>
<script setup>
import { locale, languages, setLanguage } from "@/i18n";
</script>
<style scoped>
.gp-language {
	display: inline-flex;
	flex-shrink: 0;
	border: 1px solid currentColor;
	border-radius: 999px;
	padding: 3px;
	gap: 2px;
	color: inherit;
	font-size: 12px;
}
button {
	padding: 7px 9px;
	border-radius: 999px;
	min-height: 36px;
	font: inherit;
	white-space: nowrap;
}
button[lang="am"] {
	font-family: "Gather Ethiopic", "Instrument Sans", sans-serif;
}
button[aria-pressed="true"] {
	background: var(--gp-primary, #7355b5);
	color: white;
}
button:focus-visible {
	outline: 2px solid currentColor;
	outline-offset: 2px;
}
</style>
