<template>
	<div class="flex w-full flex-col items-center gap-8 text-center">
		<template v-if="view.phase === 'turn_ready' && view.performer">
			<p class="font-mono text-xs uppercase tracking-[0.28em] text-paper/40">
				{{ $t("Turn") }} {{ (view.turn ?? 0) + 1 }} {{ $t("of") }}
				{{ $t(totalTurns || "?") }}
			</p>
			<div class="flex items-center gap-5">
				<AvatarPic
					:id="view.performer.avatar"
					:nickname="view.performer.nickname"
					:size="72"
				/>
				<div class="text-left">
					<p class="font-display text-3xl font-extrabold text-paper">
						{{ view.performer.nickname }}
					</p>
					<p class="text-paper/50">{{ teamName }} {{ $t("takes the stage") }}</p>
				</div>
			</div>
			<DrainRing
				:percent="timerPercent"
				:seconds="Math.ceil(remaining)"
				:size="110"
				color="rgb(var(--accent))"
			/>
		</template>

		<template v-else-if="view.phase === 'turn_open' && view.performer">
			<div class="flex items-center justify-center gap-8">
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="120"
					:color="remaining <= 5 ? 'rgb(var(--alert))' : 'rgb(var(--ok))'"
				/>
				<div class="text-left">
					<p class="font-display text-4xl font-extrabold text-paper">
						{{ view.performer.nickname }}
					</p>
					<p class="mt-1 font-mono uppercase tracking-wider text-paper/50">
						{{ teamName }} · {{ mode }} {{ $t("mode") }}
					</p>
				</div>
			</div>
			<div
				class="flex w-full max-w-lg items-center justify-between rounded-3xl border border-haze bg-dusk px-8 py-6"
			>
				<span class="font-mono uppercase tracking-widest text-paper/50">
					{{ $t("Solved") }}
				</span>
				<span class="font-display text-5xl font-extrabold tabular-nums text-accent">{{
					solvedCount
				}}</span>
			</div>
			<p class="max-w-md text-sm text-paper/40">
				{{ $t("Only") }} {{ view.performer.nickname }}
				{{ $t("'s phone knows the words. Watch them work.") }}
			</p>
			<button v-if="view.performer" class="ctl" @click="$emit('reassign')">
				{{ $t("Reassign performer") }}
			</button>
		</template>

		<template v-else-if="view.phase === 'turn_review'">
			<h2 class="font-display text-3xl font-extrabold text-paper sm:text-4xl">
				{{ solvedCount }} {{ $t("solved for") }} {{ teamName }}
			</h2>
			<div class="flex max-w-2xl flex-wrap justify-center gap-2">
				<span
					v-for="(word, index) in view.played || []"
					:key="index"
					class="rounded-xl px-4 py-2 font-medium"
					:class="
						isSolved(word, index)
							? 'bg-lagoon/20 text-ok'
							: 'bg-dusk text-paper/40 line-through'
					"
				>
					{{ word }}
				</span>
			</div>
			<p class="text-sm text-paper/40">
				{{ view.passed_count || 0 }}
				{{ $t("passed · ask the room if any call looked wrong") }}
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
	totalTurns: { type: Number, default: 0 },
	mode: { type: String, default: "Act" },
	solvedCount: { type: Number, default: 0 },
});

defineEmits(["reassign"]);

const teamName = computed(() => props.view.actor_team_name || "");

function isSolved(word, index) {
	const played = props.view.played || [];
	const passedStart = played.length - (props.view.passed_count || 0);
	return index < passedStart;
}
</script>
