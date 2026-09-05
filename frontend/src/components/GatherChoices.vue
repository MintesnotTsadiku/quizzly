<template>
	<fieldset class="gp-choice-field">
		<legend>{{ $t(label) }}</legend>
		<div class="gp-choice-grid" :class="{ compact }">
			<label
				v-for="option in options"
				:key="option.value"
				class="gp-choice-card"
				:class="{ selected: modelValue === option.value }"
				><input
					type="radio"
					:name="id"
					:value="option.value"
					:checked="modelValue === option.value"
					@change="$emit('update:modelValue', option.value)" /><span
					><strong>{{ $t(option.label) }}</strong
					><small v-if="option.description">{{ $t(option.description) }}</small></span
				><span v-if="!compact" class="gp-choice-dot" aria-hidden="true"></span
			></label>
		</div>
	</fieldset>
</template>
<script setup>
import { useId } from "vue";
defineProps({ modelValue: [String, Number], label: String, options: Array, compact: Boolean });
defineEmits(["update:modelValue"]);
const id = useId();
</script>
