<template>
	<section class="gc-game" :class="{ 'gc-projector': screen }">
		<div class="gc-top">
			<span class="gc-label">{{ $t("Grid Conquest") }}</span
			><span>{{ $t("Board {number} of 3", { number: view.board_number }) }}</span>
		</div>
		<p v-if="view.pin && view.control_mode === 'players'" class="gc-board-help">
			{{ $t("Room code: {pin}", { pin: view.pin }) }}
		</p>
		<div class="gc-scores" :aria-label="$t('Match score')">
			<div
				v-for="mark in ['X', 'O']"
				:key="mark"
				class="gc-side"
				:class="{ active: !view.winner && view.turn === mark }"
				:data-mark="mark"
			>
				<span class="gc-symbol">{{ mark }}</span>
				<div>
					<strong>{{ $t("Side {mark}", { mark }) }}</strong
					><small>{{
						$t(view.wins?.[mark] === 1 ? "1 win" : "{count} wins", {
							count: view.wins?.[mark] || 0,
						})
					}}</small>
				</div>
				<span v-if="view.my_mark === mark" class="gc-you">{{ $t("Your side") }}</span>
			</div>
		</div>
		<div class="gc-status" role="status" aria-live="polite">
			<span v-if="view.paused" class="gc-eyebrow">{{ $t("Paused") }}</span>
			<span v-else-if="view.winner" class="gc-eyebrow">{{
				$t(view.match_over ? "Match complete" : "Board complete")
			}}</span>
			<span v-else class="gc-eyebrow">{{
				$t(view.can_move ? "Your move" : "Think together. Take turns.")
			}}</span>
			<h1>{{ headline }}</h1>
			<p v-if="!view.winner">{{ subline }}</p>
			<p v-else>
				{{
					$t(
						view.winner === "draw"
							? "No empty squares. Nobody loses this board."
							: "Three in a row. One point for the side.",
					)
				}}
			</p>
		</div>
		<div
			class="gc-board"
			:data-turn="view.turn"
			role="group"
			:aria-label="$t('X and O board')"
		>
			<button
				v-for="(mark, cell) in view.board"
				:key="cell"
				:ref="(el) => (cells[cell] = el)"
				class="gc-cell"
				:data-cell="cell"
				:data-mark="mark"
				:class="{
					winning: view.winning_line?.includes(cell),
					last: view.last_cell === cell,
				}"
				:aria-label="cellLabel(cell, mark)"
				:aria-disabled="Boolean(mark || !view.can_move || busy || view.winner)"
				@click="play(cell)"
				@keydown="navigate($event, cell)"
			>
				<svg v-if="mark === 'X'" viewBox="0 0 100 100" aria-hidden="true">
					<path d="M26 26 L74 74 M74 26 L26 74" />
				</svg>
				<svg v-else-if="mark === 'O'" viewBox="0 0 100 100" aria-hidden="true">
					<circle cx="50" cy="50" r="30" />
				</svg>
				<span v-else class="gc-cell-hint" aria-hidden="true">{{
					view.can_move ? "+" : "·"
				}}</span>
			</button>
		</div>
		<p class="gc-board-help">
			{{
				$t(
					busy
						? "Placing your mark…"
						: view.winner === "draw"
							? "Nine marks. A shared draw."
							: view.winner
								? "The winning line stays on the board for everyone to see."
								: "Connect three across, down or diagonally. Empty squares only.",
				)
			}}
		</p>
		<p v-if="error" role="alert" class="gc-error">{{ $t(error) }}</p>
		<div v-if="view.is_host" class="gc-controls">
			<button
				v-if="view.winner"
				class="ctl ctl-go"
				:disabled="busy"
				@click="$emit('command', { command: 'next', revision: view.revision })"
			>
				{{ $t(view.match_over ? "See match results" : "Next board") }}
			</button>
			<button
				v-else-if="view.control_mode === 'players' && !view.host_turn"
				class="ctl"
				:disabled="busy || view.paused"
				@click="$emit('command', { command: 'take_over', revision: view.revision })"
			>
				{{ $t("Help play this turn") }}
			</button>
			<button
				v-if="!view.winner"
				class="ctl"
				:disabled="busy"
				@click="
					$emit('command', {
						command: view.paused ? 'resume' : 'pause',
						revision: view.revision,
					})
				"
			>
				{{ $t(view.paused ? "Resume" : "Pause") }}
			</button>
			<button
				class="ctl"
				:disabled="busy"
				@click="$emit('command', { command: 'end', revision: view.revision })"
			>
				{{ $t("End match") }}
			</button>
		</div>
		<p v-else-if="view.winner && !view.practice" class="gc-board-help">
			{{ $t("The host will continue when everyone is ready.") }}
		</p>
	</section>
</template>
<script setup>
import { computed, ref } from "vue";
import { t } from "@/i18n";
const props = defineProps({ view: Object, busy: Boolean, error: String, screen: Boolean });
const emit = defineEmits(["move", "command"]);
const cells = ref([]);
const names = [
	"Top left",
	"Top middle",
	"Top right",
	"Middle left",
	"Centre",
	"Middle right",
	"Bottom left",
	"Bottom middle",
	"Bottom right",
];
const headline = computed(() =>
	props.view.paused
		? t("A moment to think")
		: props.view.winner === "draw"
			? t("A well-played draw")
			: props.view.winner
				? t("{mark} wins this board!", { mark: props.view.winner })
				: t("{mark} to play", { mark: props.view.turn }),
);
const subline = computed(() =>
	props.view.host_turn
		? t("The host is helping with this move.")
		: props.view.control_mode === "shared"
			? t("Pass the device to the next side. Tap an empty square.")
			: props.view.can_move
				? t("Tap an empty square. Your side is counting on you.")
				: props.view.controller_name
					? t("{name} is placing the next mark.", { name: props.view.controller_name })
					: t("Waiting for a player. The host can help with this turn."),
);
function cellLabel(cell, mark) {
	return `${t(names[cell])} · ${mark || t("Empty square")}`;
}
function play(cell) {
	if (!props.view.can_move || props.view.board[cell] || props.busy || props.view.winner) return;
	emit("move", { cell, revision: props.view.revision });
}
function navigate(e, cell) {
	const delta = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: 3, ArrowUp: -3 }[e.key];
	if (delta) {
		e.preventDefault();
		cells.value[(cell + delta + 9) % 9]?.focus();
	}
}
</script>
<style scoped>
.gc-game {
	width: min(100%, 660px);
	margin: auto;
	color: rgb(var(--paper));
	text-align: center;
}
.gc-top {
	display: flex;
	justify-content: space-between;
	gap: 12px;
	align-items: center;
	font-size: 0.78rem;
	color: rgb(var(--paper) / 0.65);
	margin-bottom: 1rem;
}
.gc-label {
	font-weight: 800;
	letter-spacing: 0.05em;
}
.gc-scores {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 12px;
}
.gc-side {
	display: flex;
	align-items: center;
	gap: 12px;
	border: 2px solid transparent;
	border-radius: 20px;
	background: rgb(var(--dusk));
	padding: 12px 16px;
	text-align: left;
	transition: border-color 0.2s;
}
.gc-side.active[data-mark="X"] {
	border-color: #f07859;
}
.gc-side.active[data-mark="O"] {
	border-color: #39aeb8;
}
.gc-symbol {
	font-size: 2rem;
	line-height: 1;
	font-weight: 900;
	color: #e56e4e;
}
.gc-side[data-mark="O"] .gc-symbol {
	color: #279ca7;
}
.gc-side strong,
.gc-side small {
	display: block;
}
.gc-side small {
	font-size: 0.8rem;
	color: rgb(var(--paper) / 0.65);
}
.gc-you {
	font-size: 0.7rem;
	margin-left: auto;
	font-weight: 700;
}
.gc-status {
	padding: 22px 0 18px;
	min-height: 130px;
}
.gc-eyebrow {
	font-size: 0.7rem;
	letter-spacing: 0.12em;
	text-transform: uppercase;
	color: rgb(var(--paper) / 0.6);
	font-weight: 750;
}
.gc-status h1 {
	font-weight: 850;
	font-size: clamp(1.8rem, 4vw, 2.65rem);
	line-height: 1.15;
	margin: 7px 0;
}
.gc-status p {
	font-size: 0.9rem;
	color: rgb(var(--paper) / 0.7);
	line-height: 1.6;
}
.gc-board {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 10px;
	max-width: 410px;
	margin: 0 auto;
	padding: 12px;
	border-radius: 28px;
	background: rgb(var(--paper) / 0.07);
	box-shadow: inset 0 0 0 1px rgb(var(--paper) / 0.1);
}
.gc-cell {
	aspect-ratio: 1;
	position: relative;
	display: grid;
	place-items: center;
	background: rgb(var(--dusk));
	border: 2px solid rgb(var(--haze));
	border-radius: 17px;
	color: #e56e4e;
	transition:
		background 0.18s,
		transform 0.18s,
		border-color 0.18s;
}
.gc-cell[aria-disabled="false"] {
	cursor: pointer;
}
.gc-cell[aria-disabled="false"]:hover {
	transform: translateY(-2px);
	border-color: rgb(var(--accent));
	background: rgb(var(--accent) / 0.08);
}
.gc-cell[aria-disabled="true"] {
	cursor: default;
}
.gc-board[data-turn="O"] .gc-cell[data-mark=""],
.gc-cell[data-mark="O"] {
	color: #279ca7;
}
.gc-cell svg {
	width: 80%;
	height: 80%;
	fill: none;
	stroke: currentColor;
	stroke-width: 10;
	stroke-linecap: round;
	animation: gc-place 0.18s ease-out;
}
.gc-cell.last {
	border-color: currentColor;
}
.gc-cell.winning {
	background: #e4f3df;
	border-color: #60914d;
	color: #376a29;
	box-shadow: 0 0 0 1px #60914d;
}
.gc-cell-hint {
	font-size: 2rem;
	opacity: 0.18;
	font-weight: 800;
}
.gc-cell[aria-disabled="false"]:hover .gc-cell-hint {
	opacity: 0.6;
}
.gc-board-help {
	font-size: 0.78rem;
	color: rgb(var(--paper) / 0.65);
	line-height: 1.6;
	margin: 14px auto;
	max-width: 430px;
}
.gc-controls {
	display: flex;
	justify-content: center;
	gap: 8px;
	flex-wrap: wrap;
	margin-top: 15px;
}
.gc-error {
	padding: 10px;
	border-radius: 12px;
	background: rgb(var(--alert) / 0.1);
	color: rgb(var(--alert));
	font-size: 0.85rem;
}
.gc-projector {
	max-width: 850px;
}
.gc-projector .gc-board {
	max-width: 510px;
}
.gc-projector .gc-status h1 {
	font-size: 3rem;
}
.gc-projector .gc-status p {
	font-size: 1.2rem;
}
@keyframes gc-place {
	from {
		transform: scale(0.8);
		opacity: 0.2;
	}
	to {
		transform: scale(1);
		opacity: 1;
	}
}
@media (prefers-reduced-motion: reduce) {
	.gc-cell,
	.gc-cell svg,
	.gc-side {
		transition: none;
		animation: none;
	}
}
@media (max-width: 400px) {
	.gc-side {
		padding: 10px;
		gap: 8px;
	}
	.gc-you {
		font-size: 0.6rem;
	}
	.gc-board {
		gap: 7px;
		padding: 9px;
		border-radius: 22px;
	}
	.gc-cell {
		border-radius: 13px;
	}
	.gc-status {
		min-height: 120px;
	}
}
</style>
