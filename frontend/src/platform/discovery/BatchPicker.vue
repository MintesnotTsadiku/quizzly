<template>
	<div class="batch-picker">
		<label
			>{{ $t("Prompts to play") }}
			<input
				type="number"
				:value="modelValue"
				min="1"
				:max="available"
				step="1"
				@input="$emit('update:modelValue', Number($event.target.value))"
			/>
		</label>
		<p>{{ $t("{selected} of {available} available", { selected: modelValue, available }) }}</p>
		<p>
			{{ $t("Selected randomly without replacement. Reconnecting keeps the same order.") }}
		</p>
		<p>
			{{
				$t("About {minutes} minutes, plus time to talk", {
					minutes: Math.max(1, Math.ceil(minutes ?? (modelValue * seconds) / 60)),
				})
			}}
		</p>
	</div>
</template>
<script setup>
defineProps({
	modelValue: Number,
	available: Number,
	minutes: { type: Number, default: null },
	seconds: { type: Number, default: 60 },
});
defineEmits(["update:modelValue"]);
</script>
<style scoped>
.batch-picker {
	margin: 16px 0;
}
.batch-picker label {
	display: flex;
	gap: 14px;
	align-items: center;
	font-weight: 600;
}
.batch-picker input {
	width: 90px;
	padding: 10px;
	border: 1px solid currentColor;
	border-radius: 8px;
	background: transparent;
	color: inherit;
}
.batch-picker p {
	font-size: 14px;
	margin: 8px 0;
	opacity: 0.8;
}
</style>
