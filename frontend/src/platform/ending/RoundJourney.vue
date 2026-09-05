<template>
	<aside
		v-if="arc?.enabled"
		class="journey"
		:data-finale="arc.chapter === 'finale'"
		:aria-label="$t('Round journey')"
	>
		<div class="journey-heading">
			<strong>{{ $t(chapters[arc.chapter]) }}</strong
			><span>{{
				$t("Round {round} of {total}", {
					round: arc.round,
					total: Math.max(arc.round, arc.planned_rounds),
				})
			}}</span>
		</div>
		<progress
			:value="Math.min(arc.round, arc.planned_rounds)"
			:max="arc.planned_rounds"
			:aria-label="$t('Round progress')"
		/>
		<p>{{ $t("Correct prediction: +{points}", { points: arc.prediction_points }) }}</p>
		<small v-if="arc.chapter !== 'finale' && arc.chapter !== 'encore'">{{
			$t("Final round: +1,000 for reading the room. Other bonuses stay the same.")
		}}</small>
		<small v-else-if="arc.chapter === 'finale'">{{
			$t("One last chance to climb. Other bonuses stay the same.")
		}}</small>
		<small v-else>{{ $t("An extra round from your host. Classic scoring.") }}</small>
	</aside>
</template>
<script setup>
defineProps({ arc: Object });
const chapters = {
	opening: "Find your rhythm",
	build: "Read the room",
	finale: "The final read",
	encore: "Encore",
};
</script>
<style scoped>
.journey {
	width: min(100%, 48rem);
	margin: 0 auto;
	padding: 1rem 1.25rem;
	border: 1px solid rgb(var(--haze));
	border-radius: 1.25rem;
	background: rgb(var(--dusk));
	text-align: left;
	color: rgb(var(--paper));
	flex-shrink: 0;
}
.journey[data-finale="true"] {
	border-color: rgb(var(--accent));
	background: linear-gradient(115deg, rgb(var(--accent) / 0.16), rgb(var(--dusk)));
}
.journey-heading {
	display: flex;
	justify-content: space-between;
	gap: 1rem;
	flex-wrap: wrap;
}
.journey-heading strong {
	font-size: 1.15rem;
}
.journey-heading span,
small {
	opacity: 0.75;
	font-size: 0.85rem;
}
progress {
	width: 100%;
	height: 5px;
	accent-color: rgb(var(--accent));
	display: block;
	margin: 0.75rem 0;
}
p {
	font-weight: 700;
}
small {
	display: block;
	margin-top: 0.2rem;
}
</style>
