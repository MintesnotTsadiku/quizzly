<template>
	<div class="flex w-full flex-col items-center gap-10 text-center">
		<template v-if="view.phase === 'turn_ready' && view.performer">
			<p class="font-mono text-sm uppercase tracking-[0.3em] text-paper/40">
				{{ $t("Get ready for turn") }} {{ (view.turn ?? 0) + 1 }}
			</p>
			<div class="flex items-center gap-10">
				<AvatarPic
					:id="view.performer.avatar"
					:nickname="view.performer.nickname"
					:size="150"
				/>
				<div class="text-left">
					<h1 class="font-display text-8xl font-extrabold leading-none text-paper">
						{{ view.performer.nickname }}
					</h1>
					<p class="mt-4 font-display text-3xl text-paper/60">
						{{ view.actor_team_name }} {{ $t("takes the stage") }}
					</p>
				</div>
				<DrainRing
					:percent="timerPercent"
					:seconds="Math.ceil(remaining)"
					:size="170"
					color="rgb(var(--accent))"
				/>
			</div>
		</template>

		<template v-else-if="view.phase === 'turn_open' && view.performer">
			<div class="flex items-center gap-10">
				<AvatarPic
					:id="view.performer.avatar"
					:nickname="view.performer.nickname"
					:size="130"
				/>
				<div class="text-left">
					<p class="font-mono text-xs uppercase tracking-[0.3em] text-paper/40">
						{{ $t("Now performing") }}
					</p>
					<h1 class="mt-1 font-display text-7xl font-extrabold leading-none text-paper">
						{{ view.performer.nickname }}
					</h1>
					<p class="mt-2 font-display text-2xl text-paper/60">
						{{ view.actor_team_name }}
					</p>
				</div>
				<div class="ml-16 flex items-center gap-10">
					<div class="text-center">
						<p
							class="font-display text-9xl font-extrabold leading-none tabular-nums text-accent"
						>
							{{ solvedCount }}
						</p>
						<p class="mt-1 font-mono text-xs uppercase tracking-[0.3em] text-paper/40">
							{{ $t("solved") }}
						</p>
					</div>
					<DrainRing
						:percent="timerPercent"
						:seconds="Math.ceil(remaining)"
						:size="170"
						:color="remaining <= 5 ? 'rgb(var(--alert))' : 'rgb(var(--ok))'"
					/>
				</div>
			</div>
			<div class="mt-6 grid w-full max-w-6xl gap-6" :class="teamCardCols">
				<div
					v-for="team in view.teams || []"
					:key="team.name"
					class="rounded-3xl border-2 bg-dusk/60 px-8 py-6 text-center"
					:class="
						isStageTeam(team)
							? [teamStyle(team.color).border, 'scale-[1.02]']
							: 'border-haze'
					"
				>
					<p class="truncate font-display text-2xl font-bold text-paper">
						{{ team.team_name }}
					</p>
					<p
						class="mt-2 font-display text-6xl font-extrabold tabular-nums text-paper/85"
					>
						{{ team.score }}
					</p>
					<p
						v-if="isStageTeam(team)"
						class="mt-1 font-mono text-[11px] uppercase tracking-[0.25em] text-paper/45"
					>
						{{ $t("on stage") }}
					</p>
				</div>
			</div>
		</template>

		<template v-else-if="view.phase === 'turn_review'">
			<h2 class="font-display text-5xl font-extrabold text-paper">
				{{ solvedCount }} {{ $t("solved for") }} {{ view.actor_team_name }}
			</h2>
			<div class="flex max-w-5xl flex-wrap justify-center gap-3">
				<span
					v-for="(word, index) in view.played || []"
					:key="index"
					class="rounded-2xl px-6 py-3 font-display text-2xl font-bold"
					:class="
						isSolved(word, index)
							? 'bg-lagoon/25 text-ok'
							: 'bg-dusk text-paper/35 line-through'
					"
				>
					{{ word }}
				</span>
			</div>
			<p class="font-mono uppercase tracking-widest text-paper/40">
				{{ view.passed_count || 0 }} {{ $t("passed") }}
			</p>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import AvatarPic from "@/components/AvatarPic.vue";
import DrainRing from "@/components/DrainRing.vue";
import { teamStyle } from "@/platform/session/gp";

const props = defineProps({
	view: { type: Object, default: () => ({}) },
	remaining: { type: Number, default: 0 },
	timerPercent: { type: Number, default: 0 },
	solvedCount: { type: Number, default: 0 },
});

const teamCardCols = computed(() =>
	(props.view.teams || []).length >= 4
		? "sm:grid-cols-4"
		: (props.view.teams || []).length === 3
			? "sm:grid-cols-3"
			: "grid-cols-2",
);

function isStageTeam(team) {
	return team.team_name === (props.view.actor_team_name || "");
}

function isSolved(word, index) {
	const played = props.view.played || [];
	const passedStart = played.length - (props.view.passed_count || 0);
	return index < passedStart;
}
</script>
