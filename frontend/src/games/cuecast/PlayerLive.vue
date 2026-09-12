<template>
	<div class="flex w-full flex-col items-center gap-6 text-center">
		<!-- Performer ready -->
		<template v-if="view.phase === 'turn_ready' && view.is_performer">
			<p class="font-mono uppercase tracking-[0.28em] text-accent">{{ $t("You're up") }}</p>
			<h1 class="font-display text-4xl font-extrabold leading-tight text-paper">
				{{ $t("Get ready to act!") }}
			</h1>
			<p class="text-paper/50">{{ view.mode }} {{ $t("mode") }}</p>
			<div class="relative grid h-40 w-40 place-items-center rounded-full bg-dusk">
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="150"
					color="rgb(var(--accent))"
				/>
				<span
					class="absolute font-display text-5xl font-extrabold tabular-nums text-paper"
				>
					{{ Math.ceil(remaining) }}
				</span>
			</div>
			<p class="text-sm text-paper/40">
				{{ $t("Look up — your first word lands in a second.") }}
			</p>
		</template>

		<!-- Performer live: the only screen that knows the word -->
		<template v-else-if="view.phase === 'turn_open' && view.is_performer">
			<div class="flex w-full items-center justify-between px-2">
				<span class="font-mono text-xs uppercase tracking-[0.22em] text-paper/45">
					{{ $t("Solved") }} {{ solvedCount }}</span
				>
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="56"
					:color="urgentColor"
				/>
			</div>
			<p
				class="mt-2 max-w-md break-words font-display text-5xl font-extrabold leading-tight text-paper sm:text-6xl"
			>
				{{ prompt || $t("No prompts remain. Wait for this turn to finish.") }}
			</p>
			<p class="-mt-3 font-mono uppercase tracking-widest text-paper/35">
				{{ view.mode }} {{ $t("mode · no letters!") }}
			</p>
			<div class="grid w-full max-w-md grid-cols-2 gap-3">
				<button
					class="flex flex-col items-center gap-2 rounded-3xl bg-lagoon py-8 font-display text-2xl font-extrabold text-sunk transition active:scale-95"
					:disabled="submitting || !prompt"
					@click="$emit('act', 'correct_prompt')"
				>
					<span class="text-4xl">✓</span> {{ $t("Solved it") }}
				</button>
				<button
					class="flex flex-col items-center gap-2 rounded-3xl bg-gold py-8 font-display text-2xl font-extrabold text-sunk transition active:scale-95"
					:disabled="submitting || !prompt"
					@click="$emit('act', 'pass_prompt')"
				>
					<span class="text-4xl">»</span> {{ $t("Pass") }}
				</button>
			</div>
		</template>

		<!-- On stage but watching -->
		<template v-else-if="['turn_ready', 'turn_open'].includes(view.phase)">
			<p class="font-mono uppercase tracking-[0.28em] text-accent">
				{{ $t(view.phase === "turn_ready" ? "Get ready" : "On stage") }}
			</p>
			<div class="flex items-center gap-4">
				<AvatarPic
					:id="view.performer?.avatar"
					:nickname="view.performer?.nickname"
					:size="64"
				/>
				<div class="text-left">
					<p class="font-display text-2xl font-bold text-paper">
						{{ view.performer?.nickname }}
					</p>
					<p class="text-paper/50">
						{{ view.actor_team_name }} {{ $t("is performing") }}
					</p>
				</div>
			</div>
			<p
				v-if="view.phase === 'turn_open'"
				class="font-display text-7xl font-extrabold tabular-nums text-accent"
			>
				{{ solvedCount }}
			</p>
			<p v-if="view.phase === 'turn_open'" class="-mt-3 text-paper/40">
				{{ $t("solved so far") }}
			</p>
		</template>

		<!-- Review -->
		<template v-else-if="view.phase === 'turn_review'">
			<h1 class="font-display text-4xl font-extrabold text-paper">
				{{ solvedCount }} {{ $t("solved!") }}
			</h1>
			<p class="max-w-xs text-paper/50">
				{{ $t("Check the big screen for the words — then the scoreboard moves.") }}
			</p>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import AvatarPic from "@/components/AvatarPic.vue";
import DrainRing from "@/components/DrainRing.vue";

const props = defineProps({
	view: { type: Object, default: () => ({}) },
	remaining: { type: Number, default: 0 },
	timerPercent: { type: Number, default: 0 },
	prompt: { type: String, default: "" },
	solvedCount: { type: Number, default: 0 },
	submitting: { type: Boolean, default: false },
});

defineEmits(["act"]);

const urgentColor = computed(() =>
	props.remaining <= 5 ? "rgb(var(--alert))" : "rgb(var(--ok))"
);
</script>
