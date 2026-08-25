<template>
	<div ref="root" class="relative">
		<button
			type="button"
			class="pack-trigger"
			:aria-expanded="open"
			aria-haspopup="listbox"
			@click="open = !open"
		>
			<span class="grid size-10 shrink-0 place-items-center rounded-xl bg-lagoon/10 text-ok">
				<svg
					class="size-5 fill-none stroke-current"
					viewBox="0 0 24 24"
					stroke-width="1.8"
				>
					<path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5" />
				</svg>
			</span>
			<span class="min-w-0 flex-1 text-left">
				<span v-if="selected" class="block truncate font-display font-bold text-paper">{{
					selected.title
				}}</span>
				<span v-else class="block text-paper/45">Choose a ready-made pack…</span>
				<span
					v-if="selected"
					class="mt-0.5 block font-mono text-[10px] uppercase tracking-wider text-paper/40"
				>
					{{ selected.prompt_count }} prompts
				</span>
			</span>
			<svg
				class="size-4 fill-none stroke-paper/45 transition"
				:class="{ 'rotate-180': open }"
				viewBox="0 0 24 24"
				stroke-width="2"
			>
				<path d="m7 9 5 5 5-5" />
			</svg>
		</button>

		<div v-if="open" class="pack-menu">
			<label class="pack-search">
				<svg
					class="size-4 shrink-0 fill-none stroke-paper/40"
					viewBox="0 0 24 24"
					stroke-width="2"
				>
					<circle cx="11" cy="11" r="7" />
					<path d="m16 16 4 4" />
				</svg>
				<input
					ref="searchInput"
					v-model="query"
					class="min-w-0 flex-1 bg-transparent text-sm text-paper outline-none placeholder:text-paper/30"
					placeholder="Search packs…"
					role="combobox"
					aria-controls="pack-options"
					aria-autocomplete="list"
					:aria-activedescendant="
						filtered[activeIndex] ? `pack-option-${activeIndex}` : undefined
					"
					@keydown="onSearchKeydown"
				/>
			</label>
			<div id="pack-options" class="max-h-80 space-y-1 overflow-y-auto p-2" role="listbox">
				<div
					v-for="(pack, index) in filtered"
					:key="pack.name"
					:id="`pack-option-${index}`"
					class="pack-option"
					:data-selected="pack.name === modelValue"
					:data-active="index === activeIndex"
					role="option"
					:aria-selected="pack.name === modelValue"
				>
					<button
						class="min-w-0 flex-1 px-3 py-2.5 text-left"
						type="button"
						@click="choose(pack)"
					>
						<span class="block truncate font-display text-sm font-bold text-paper">{{
							pack.title
						}}</span>
						<span
							class="mt-1 block font-mono text-[9px] uppercase tracking-wider text-paper/35"
						>
							{{ pack.prompt_count }} prompts
							<template v-if="pack.mode">· {{ pack.mode }}</template>
						</span>
					</button>
					<button
						type="button"
						class="preview-button"
						:aria-label="`Preview ${pack.title}`"
						@click.stop="preview(pack)"
					>
						<svg
							class="size-4 fill-none stroke-current"
							viewBox="0 0 24 24"
							stroke-width="1.8"
						>
							<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z" />
							<circle cx="12" cy="12" r="2.5" />
						</svg>
					</button>
				</div>
				<p v-if="!filtered.length" class="px-4 py-8 text-center text-sm text-paper/40">
					No packs match “{{ query }}”.
				</p>
			</div>
			<p class="border-t border-haze px-4 py-3 text-xs text-paper/35">
				Use the eye button to inspect every prompt before choosing.
			</p>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	modelValue: { type: String, default: "" },
	packs: { type: Array, default: () => [] },
});
const emit = defineEmits(["update:modelValue", "preview"]);
const root = ref(null);
const searchInput = ref(null);
const open = ref(false);
const query = ref("");
const activeIndex = ref(0);
const selected = computed(() => props.packs.find((pack) => pack.name === props.modelValue));
const filtered = computed(() => {
	const needle = query.value.trim().toLowerCase();
	return needle
		? props.packs.filter((pack) =>
				`${pack.title} ${pack.mode || ""}`.toLowerCase().includes(needle)
		  )
		: props.packs;
});

watch(open, async (value) => {
	if (value) {
		query.value = "";
		activeIndex.value = 0;
		await nextTick();
		searchInput.value?.focus();
	}
});

watch(query, () => (activeIndex.value = 0));

function choose(pack) {
	emit("update:modelValue", pack.name);
	open.value = false;
}
async function preview(pack) {
	open.value = false;
	await nextTick();
	root.value?.querySelector(".pack-trigger")?.focus();
	emit("preview", pack);
}
function onSearchKeydown(event) {
	if (!filtered.value.length) return;
	if (event.key === "ArrowDown") {
		event.preventDefault();
		activeIndex.value = (activeIndex.value + 1) % filtered.value.length;
	} else if (event.key === "ArrowUp") {
		event.preventDefault();
		activeIndex.value =
			(activeIndex.value - 1 + filtered.value.length) % filtered.value.length;
	} else if (event.key === "Home") {
		event.preventDefault();
		activeIndex.value = 0;
	} else if (event.key === "End") {
		event.preventDefault();
		activeIndex.value = filtered.value.length - 1;
	} else if (event.key === "Enter") {
		event.preventDefault();
		choose(filtered.value[activeIndex.value]);
	}
}
function onDocumentClick(event) {
	if (!root.value?.contains(event.target)) open.value = false;
}
function onKeydown(event) {
	if (event.key === "Escape") open.value = false;
}
onMounted(() => {
	document.addEventListener("click", onDocumentClick);
	document.addEventListener("keydown", onKeydown);
});
onBeforeUnmount(() => {
	document.removeEventListener("click", onDocumentClick);
	document.removeEventListener("keydown", onKeydown);
});
</script>

<style scoped>
.pack-trigger {
	display: flex;
	width: 100%;
	align-items: center;
	gap: 0.85rem;
	min-height: 4.25rem;
	border: 1px solid rgb(var(--haze));
	border-radius: 1rem;
	background: rgb(var(--night) / 0.55);
	padding: 0.7rem 1rem;
	transition: 160ms ease;
}
.pack-trigger:hover,
.pack-trigger[aria-expanded="true"] {
	border-color: rgb(var(--lagoon) / 0.75);
	box-shadow: 0 0 0 3px rgb(var(--lagoon) / 0.08);
}
.pack-menu {
	position: absolute;
	z-index: 30;
	top: calc(100% + 0.55rem);
	width: 100%;
	overflow: hidden;
	border: 1px solid rgb(var(--haze));
	border-radius: 1rem;
	background: rgb(var(--night));
	box-shadow: 0 24px 70px rgb(0 0 0 / 0.45);
}
.pack-search {
	display: flex;
	align-items: center;
	gap: 0.65rem;
	margin: 0.75rem;
	border: 1px solid rgb(var(--haze));
	border-radius: 0.75rem;
	background: rgb(var(--dusk));
	padding: 0.65rem 0.8rem;
}
.pack-option {
	display: flex;
	align-items: center;
	border: 1px solid transparent;
	border-radius: 0.75rem;
	transition: 150ms ease;
}
.pack-option:hover,
.pack-option[data-active="true"],
.pack-option[data-selected="true"] {
	border-color: rgb(var(--haze));
	background: rgb(var(--dusk));
}
.preview-button {
	display: grid;
	place-items: center;
	flex: 0 0 auto;
	width: 2.35rem;
	height: 2.35rem;
	margin-right: 0.45rem;
	border-radius: 0.7rem;
	color: rgb(var(--paper) / 0.45);
}
.preview-button:hover {
	background: rgb(var(--lagoon) / 0.12);
	color: rgb(var(--ok));
}
</style>
