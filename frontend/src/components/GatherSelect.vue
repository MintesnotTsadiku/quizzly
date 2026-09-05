<template>
	<div ref="root" class="gp-select" @keydown="keydown">
		<span :id="id + '-label'" class="gp-control-label">{{ label }}</span>
		<button
			ref="trigger"
			type="button"
			class="gp-select-trigger"
			role="combobox"
			aria-haspopup="listbox"
			:aria-expanded="open"
			:aria-controls="id"
			:aria-labelledby="id + '-label ' + id + '-value'"
			:disabled="disabled || !options.length"
			@click="toggle"
		>
			<span :id="id + '-value'"
				><strong>{{ chosen?.label || placeholder }}</strong
				><small v-if="chosen?.description">{{ chosen.description }}</small></span
			><span aria-hidden="true" :class="{ rotated: open }">⌄</span>
		</button>
		<ul
			v-if="open"
			:id="id"
			ref="list"
			class="gp-select-list"
			role="listbox"
			:aria-labelledby="id + '-label'"
			tabindex="-1"
			:aria-activedescendant="id + '-' + active"
		>
			<li
				v-for="(option, i) in options"
				:id="id + '-' + i"
				:key="option.value"
				role="option"
				:aria-selected="modelValue === option.value"
				:class="{ active: active === i }"
				@pointermove="active = i"
				@mousedown.prevent
				@click="choose(i)"
			>
				<span
					><strong>{{ option.label }}</strong
					><small v-if="option.description">{{ option.description }}</small></span
				><span v-if="modelValue === option.value" aria-hidden="true">✓</span>
			</li>
		</ul>
	</div>
</template>
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId } from "vue";
const props = defineProps({
	modelValue: [String, Number],
	options: { type: Array, default: () => [] },
	label: String,
	placeholder: { type: String, default: "Choose a pack" },
	disabled: Boolean,
});
const emit = defineEmits(["update:modelValue"]);
const id = useId(),
	root = ref(),
	trigger = ref(),
	list = ref(),
	open = ref(false),
	active = ref(0);
const chosen = computed(() => props.options.find((o) => o.value === props.modelValue));
let typed = "",
	typeTimer;
async function toggle() {
	if (open.value) return close();
	open.value = true;
	active.value = Math.max(
		0,
		props.options.findIndex((o) => o.value === props.modelValue),
	);
	await nextTick();
	list.value?.focus();
}
function close() {
	open.value = false;
	trigger.value?.focus();
}
function choose(i) {
	emit("update:modelValue", props.options[i].value);
	close();
}
function keydown(e) {
	if (e.key === "Escape" && open.value) {
		e.preventDefault();
		close();
		return;
	}
	if (e.key === "Tab") {
		open.value = false;
		return;
	}
	if (!props.options.length || props.disabled) return;
	if (["ArrowDown", "ArrowUp", "Home", "End", "Enter", " "].includes(e.key)) {
		e.preventDefault();
		if (!open.value) {
			toggle();
			return;
		}
		if (e.key === "Enter" || e.key === " ") {
			choose(active.value);
			return;
		}
		active.value =
			e.key === "Home"
				? 0
				: e.key === "End"
					? props.options.length - 1
					: (active.value + (e.key === "ArrowUp" ? -1 : 1) + props.options.length) %
						props.options.length;
	} else if (e.key.length === 1) {
		typed += e.key.toLowerCase();
		clearTimeout(typeTimer);
		typeTimer = setTimeout(() => (typed = ""), 600);
		const i = props.options.findIndex((o) => o.label.toLowerCase().startsWith(typed));
		if (i >= 0) active.value = i;
	}
	nextTick(() =>
		document.getElementById(id + "-" + active.value)?.scrollIntoView({ block: "nearest" }),
	);
}
function outside(e) {
	if (open.value && !root.value?.contains(e.target)) open.value = false;
}
onMounted(() => document.addEventListener("pointerdown", outside));
onBeforeUnmount(() => {
	document.removeEventListener("pointerdown", outside);
	clearTimeout(typeTimer);
});
</script>
