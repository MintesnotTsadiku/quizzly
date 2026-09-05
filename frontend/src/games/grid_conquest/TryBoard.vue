<template>
	<div class="gc-demo">
		<p>{{ $t("Try the actual board") }}</p>
		<Board :view="view" @move="move" /><button class="gp-button secondary" @click="reset">
			{{ $t("Reset practice board") }}
		</button>
	</div>
</template>
<script setup>
import { computed, ref } from "vue";
import Board from "./Board.vue";
const board = ref(["X", "X", "", "O", "", "", "O", "", ""]),
	winner = ref(null),
	line = ref([]),
	turn = ref("X"),
	last = ref(null);
const view = computed(() => ({
	board: board.value,
	turn: turn.value,
	winner: winner.value,
	winning_line: line.value,
	board_number: 1,
	wins: { X: Number(winner.value === "X"), O: Number(winner.value === "O") },
	practice: true,
	can_move: !winner.value,
	control_mode: "shared",
	last_cell: last.value,
}));
function reset() {
	board.value = ["X", "X", "", "O", "", "", "O", "", ""];
	winner.value = null;
	line.value = [];
	turn.value = "X";
	last.value = null;
}
function move({ cell }) {
	if (board.value[cell]) return;
	board.value[cell] = turn.value;
	last.value = cell;
	for (const l of [
		[0, 1, 2],
		[3, 4, 5],
		[6, 7, 8],
		[0, 3, 6],
		[1, 4, 7],
		[2, 5, 8],
		[0, 4, 8],
		[2, 4, 6],
	])
		if (l.every((i) => board.value[i] === turn.value)) {
			winner.value = turn.value;
			line.value = l;
			return;
		}
	if (board.value.every(Boolean)) winner.value = "draw";
	turn.value = turn.value === "X" ? "O" : "X";
}
</script>
<style scoped>
.gc-demo {
	padding: clamp(16px, 3vw, 32px);
	background: rgb(var(--night));
	border: 1px solid rgb(var(--haze));
	border-radius: 28px;
	text-align: center;
}
.gc-demo > p {
	font-weight: 700;
	color: rgb(var(--paper));
	margin-bottom: 18px;
}
.gc-demo :deep(.gc-controls) {
	display: none;
}
</style>
