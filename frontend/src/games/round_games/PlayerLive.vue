<template>
	<div class="flex w-full max-w-lg flex-col items-center gap-6 text-center">
		<p class="font-mono uppercase tracking-[.24em] text-accent">
			{{ $t("Round") }} {{ view.round }} / {{ view.total }}
		</p>
		<h1 class="font-display text-3xl font-extrabold text-paper">{{ $t(view.prompt) }}</h1>
		<p v-if="error" role="alert" class="rounded-xl bg-red-900 p-3 text-white">{{ error }}</p>
		<RoomProgress :view="view" /><Media :view="view" />
		<template v-if="view.phase === 'chorus_clues'"
			><p v-if="view.is_guesser">
				{{ $t("You are guessing. Wait for your room’s clues.") }}
			</p>
			<template v-else
				><p>
					{{ $t("Secret word") }}: <strong>{{ view.secret }}</strong>
				</p>
				<form
					v-if="!locked"
					@submit.prevent="emit('submit', { action_type: 'clue', value })"
				>
					<input
						v-model="value"
						class="field"
						:aria-label="$t('One-word clue')"
						maxlength="60"
					/><button class="ctl ctl-go" :disabled="submitting || !value.trim()">
						{{ $t("Lock clue") }}
					</button>
				</form>
				<p v-else>{{ $t("Clue locked") }}</p></template
			></template
		>
		<p v-else-if="view.phase === 'memory_study'" role="status">
			{{ $t("Look closely. The question comes next.") }}
		</p>
		<template v-else-if="view.phase === 'round_open' && !locked"
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
				<ol class="flex flex-wrap gap-2">
					<li v-for="(card, index) in ordered" :key="index">
						<button
							class="ctl"
							@click="ordered.splice(index, 1)"
							:aria-label="$t('Remove') + ' ' + card"
						>
							{{ index + 1 }}. {{ card }} ×
						</button>
					</li>
				</ol>
				<button v-if="ordered.length" class="ctl" @click="ordered.pop()">
					{{ $t("Undo") }}
				</button>
				<button
					class="ctl ctl-go"
					:disabled="ordered.length !== (view.choices || []).length"
					@click="submit(ordered)"
				>
					{{ $t("Lock order") }}
				</button></template
			>
			<form
				v-else-if="view.game_key === 'signal-spectrum'"
				class="w-full rounded-3xl border border-haze bg-dusk p-5"
				@submit.prevent="submit(value || 50)"
			>
				<p class="mb-4">
					{{ $t("Place your marker. Try to match the pack author’s hidden position.") }}
				</p>
				<div class="flex justify-between gap-4">
					<span>{{ view.axis?.[0] || "0" }}</span
					><span>{{ view.axis?.[1] || "100" }}</span>
				</div>
				<input
					v-model="value"
					type="range"
					min="0"
					max="100"
					step="1"
					class="my-6 w-full"
					:aria-label="$t('Your position')"
				/><output class="block text-3xl">{{ value || 50 }}</output
				><button class="ctl ctl-go mt-4" :disabled="submitting">
					{{ $t("Lock position") }}
				</button>
			</form>
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
		<p v-else-if="view.phase === 'seek_review'">
			{{
				$t("Show or describe your find. The host will acknowledge the completed missions.")
			}}
		</p>
		<Reveal v-else :view="view" />
	</div>
</template>
<script setup>
import RoomProgress from "./RoomProgress.vue";
import Media from "./Media.vue";
import Reveal from "./Reveal.vue";
import { computed, ref, watch } from "vue";
const props = defineProps({
	view: { type: Object, default: () => ({}) },
	submitting: Boolean,
	error: String,
});
const emit = defineEmits(["submit"]);
const value = ref("");
const ordered = ref([]);
const locked = computed(() => Boolean(props.view.locked || props.submitting));
const remainingCards = computed(() =>
	(props.view.choices || []).filter((c) => !ordered.value.includes(c)),
);
function submit(v) {
	if (props.submitting) return;
	emit("submit", { value: v });
}
function vote(v) {
	if (props.submitting) return;
	emit("submit", { action_type: "vote", value: v });
}
watch(
	() => `${props.view.round}:${props.view.phase}`,
	() => {
		value.value = "";
		ordered.value = [];
	},
);
</script>
