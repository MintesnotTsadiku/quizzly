<template>
	<button
		type="button"
		class="premium-toggle"
		role="switch"
		:aria-checked="modelValue"
		@click="$emit('update:modelValue', !modelValue)"
	>
		<span class="toggle-track" :data-on="modelValue"><span class="toggle-thumb" /></span>
		<span class="text-left">
			<span class="block text-sm font-semibold text-paper">{{ label }}</span>
			<span v-if="hint" class="mt-0.5 block text-xs text-paper/40">{{ hint }}</span>
		</span>
	</button>
</template>

<script setup>
defineProps({
	modelValue: { type: Boolean, default: false },
	label: { type: String, required: true },
	hint: { type: String, default: "" },
});
defineEmits(["update:modelValue"]);
</script>

<style scoped>
.premium-toggle {
	display: flex;
	align-items: center;
	gap: 0.85rem;
	border-radius: 1rem;
	padding: 0.65rem 0.75rem;
	transition: background 150ms ease;
}
.premium-toggle:hover {
	background: rgb(var(--night) / 0.35);
}
.toggle-track {
	position: relative;
	flex: 0 0 auto;
	width: 2.75rem;
	height: 1.55rem;
	border: 1px solid rgb(var(--haze));
	border-radius: 999px;
	background: rgb(var(--night));
	transition: 180ms ease;
}
.toggle-track[data-on="true"] {
	border-color: rgb(var(--lagoon));
	background: rgb(var(--lagoon) / 0.85);
	box-shadow: 0 0 0 3px rgb(var(--lagoon) / 0.1);
}
.toggle-thumb {
	position: absolute;
	top: 0.19rem;
	left: 0.2rem;
	width: 1.05rem;
	height: 1.05rem;
	border-radius: 999px;
	background: rgb(var(--paper));
	box-shadow: 0 2px 7px rgb(0 0 0 / 0.35);
	transition: transform 180ms cubic-bezier(0.22, 1, 0.36, 1);
}
.toggle-track[data-on="true"] .toggle-thumb {
	transform: translateX(1.15rem);
}
</style>
