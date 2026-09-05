<template>
	<section class="gc-ending" aria-live="polite">
		<p class="gc-kicker">{{ $t("Grid Conquest") }} · {{ $t("Match complete") }}</p>
		<h1>
			{{
				ending.winner === "draw"
					? $t("The match is a draw!")
					: $t("{mark} wins the match!", { mark: ending.winner })
			}}
		</h1>
		<div class="gc-final-score" :aria-label="$t('Match score')">
			<div
				v-for="mark in ['X', 'O']"
				:key="mark"
				:class="{ winner: ending.winner === mark }"
			>
				<span>{{ $t("Side {mark}", { mark }) }}</span
				><strong>{{ ending.wins[mark] }}</strong
				><small>{{ $t("{count} wins", { count: ending.wins[mark] }) }}</small>
			</div>
		</div>
		<p>{{ $t("{count} boards completed", { count: ending.boards_played }) }}</p>
		<p>{{ $t("Switch sides. Challenge your friends to a rematch.") }}</p>
	</section>
</template>
<script setup>
defineProps({ ending: Object });
</script>
<style scoped>
.gc-ending {
	width: min(100%, 660px);
	text-align: center;
	color: rgb(var(--paper));
	padding: 24px 0;
}
.gc-kicker {
	font-size: 0.75rem;
	text-transform: uppercase;
	letter-spacing: 0.1em;
	font-weight: 750;
}
h1 {
	font-size: clamp(2rem, 5vw, 3.6rem);
	line-height: 1.1;
	font-weight: 850;
	margin: 16px 0 28px;
}
.gc-final-score {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 16px;
	margin: 0 0 22px;
}
.gc-final-score div {
	border: 2px solid rgb(var(--haze));
	background: rgb(var(--dusk));
	border-radius: 24px;
	padding: 22px 12px;
	display: grid;
	gap: 6px;
}
.gc-final-score .winner {
	border-color: rgb(var(--accent));
}
strong {
	font-size: 4rem;
	line-height: 1.2;
}
small,
p {
	color: rgb(var(--paper) / 0.7);
	line-height: 1.7;
}
</style>
