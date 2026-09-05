<template>
	<div class="flex w-full max-w-lg flex-col items-center gap-6 text-center">
		<p class="font-mono uppercase tracking-[.24em] text-accent">
			{{ $t("Round") }} {{ view.round }} / {{ view.total }}
		</p>
		<h1 class="font-display text-3xl font-extrabold text-paper">{{ view.prompt }}</h1>
		<template v-if="view.phase === 'round_open' && !locked"
			><div v-if="view.mechanic === 'choice'" class="grid w-full grid-cols-2 gap-3">
				<button
					v-for="c in view.choices || []"
					:key="c"
					class="ctl min-h-20"
					@click="submit(c)"
				>
					{{ c }}
				</button>
			</div>
			<template v-else-if="view.mechanic === 'order'"
				><p class="text-paper/45">{{ $t("Tap the cards in the correct order.") }}</p>
				<div class="flex flex-wrap justify-center gap-2">
					<button
						v-for="c in remainingCards"
						:key="c"
						class="ctl"
						@click="ordered.push(c)"
					>
						{{ c }}
					</button>
				</div>
				<div class="min-h-12 text-paper">{{ $t(ordered.join(" → ")) }}</div>
				<button
					class="ctl ctl-go"
					:disabled="ordered.length !== (view.choices || []).length"
					@click="submit(ordered)"
				>
					{{ $t("Lock order") }}
				</button></template
			>
			<form v-else class="flex w-full flex-col gap-3" @submit.prevent="submit(value)">
				<input
					v-model="value"
					:type="view.mechanic === 'number' ? 'number' : 'text'"
					class="field"
					:placeholder="view.mechanic === 'number' ? 'Your estimate' : 'Your response'"
					maxlength="280"
				/><button class="ctl ctl-go" :disabled="!String(value).trim()">
					{{ $t("Lock response") }}
				</button>
			</form></template
		>
		<p v-else-if="view.phase === 'round_open'" class="font-display text-2xl font-bold text-ok">
			{{ $t("Response locked ✓") }}
		</p>
		<template v-else-if="view.phase === 'vote_open' && !locked"
			><p class="text-paper/55">
				{{ $t("Vote anonymously. Your own response is not shown.") }}
			</p>
			<button
				v-for="c in view.choices || []"
				:key="c.id"
				class="ctl min-h-16 w-full"
				@click="vote(c.id)"
			>
				{{ c.value }}
			</button></template
		>
		<p v-else-if="view.phase === 'vote_open'" class="font-display text-2xl font-bold text-ok">
			{{ $t("Vote locked ✓") }}
		</p>
		<div v-else class="rounded-3xl border border-haze bg-dusk p-6">
			<p class="font-mono uppercase tracking-widest text-paper/40">{{ $t("Reveal") }}</p>
			<p class="mt-2 font-display text-3xl font-extrabold text-paper">
				{{ $t(view.answer || "Every contribution counts") }}
			</p>
		</div>
	</div>
</template>
<script setup>
import { computed, ref, watch } from "vue";
const props = defineProps({ view: { type: Object, default: () => ({}) }, submitting: Boolean });
const emit = defineEmits(["submit"]);
const value = ref("");
const ordered = ref([]);
const locked = ref(false);
const remainingCards = computed(() =>
	(props.view.choices || []).filter((c) => !ordered.value.includes(c)),
);
function submit(v) {
	if (props.submitting) return;
	locked.value = true;
	emit("submit", { value: v });
}
function vote(v) {
	if (props.submitting) return;
	locked.value = true;
	emit("submit", { action_type: "vote", value: v });
}
watch(
	() => [props.view.round, props.view.phase],
	() => {
		value.value = "";
		ordered.value = [];
		locked.value = false;
	},
);
</script>
