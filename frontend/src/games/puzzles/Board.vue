<template>
	<section class="puzzle-room" :aria-label="$t(title)" :data-revision="view.revision">
		<header>
			<p>{{ $t("One room. One board.") }}</p>
			<h1>{{ $t(title) }}</h1>
			<p>{{ $t(instruction) }}</p>
		</header>
		<p v-if="view.my_side">
			{{ $t("Your side") }}: <strong>{{ view.my_side }}</strong>
		</p>
		<p v-if="view.paused" role="status">{{ $t("Paused") }}</p>
		<p v-else-if="p.done" class="success" role="status">
			{{ $t("Complete!") }} · {{ p.moves }} {{ $t("moves") }}
		</p>
		<p v-else-if="p.game === 'dots-and-boxes'" role="status">
			{{ p.turn }} · {{ view.controller?.nickname || $t("Shared board") }} · X
			{{ p.scores.X }} : {{ p.scores.O }} O
		</p>
		<p v-if="p.game === 'dots-and-boxes' && p.done" class="success">
			X {{ p.scores.X }} : {{ p.scores.O }} O ·
			{{
				p.scores.X === p.scores.O
					? $t("Draw")
					: (p.scores.X > p.scores.O ? "X" : "O") + " " + $t("wins")
			}}
		</p>
		<button v-if="p.done && !view.is_screen" @click="shareResult">
			{{ $t("Challenge a friend") }}
		</button>
		<p v-if="shareNotice" role="status">{{ $t(shareNotice) }}</p>
		<p v-if="error" role="alert" class="error">{{ error }}</p>
		<div v-if="p.game === 'dots-and-boxes'" class="dots" aria-label="Dots and boxes board">
			<template v-for="r in 7" :key="r"
				><template v-for="c in 7" :key="c">
					<span v-if="r % 2 && c % 2" class="dot">●</span>
					<span
						v-else-if="!(r % 2) && !(c % 2)"
						class="box"
						:data-owner="p.boxes[`${r / 2 - 1}:${c / 2 - 1}`]"
						>{{ p.boxes[`${r / 2 - 1}:${c / 2 - 1}`] || "·" }}</span
					>
					<button
						v-else
						:disabled="disabled || Boolean(p.edges[edge(r, c)])"
						:data-edge="edge(r, c)"
						:class="[
							'edge',
							r % 2 ? 'horizontal' : 'vertical',
							{ taken: p.edges[edge(r, c)] },
						]"
						:aria-label="`${r % 2 ? $t('Horizontal edge') : $t('Vertical edge')} ${Math.floor((r - 1) / 2) + 1}, ${Math.floor((c - 1) / 2) + 1}`"
						@click="send('edge', { edge: edge(r, c) })"
					>
						<span>{{ p.edges[edge(r, c)] || "+" }}</span>
					</button>
				</template></template
			>
		</div>
		<template v-else-if="p.game === 'group-sudoku'">
			<div class="board sudoku">
				<button
					v-for="(value, i) in p.cells"
					:key="i"
					:data-cell="i"
					:class="{ given: p.givens.includes(i), selected: selected === i }"
					:disabled="disabled || p.givens.includes(i)"
					:aria-label="`${$t('Cell')} ${Math.floor(i / 4) + 1}, ${(i % 4) + 1}: ${value || $t('empty')}`"
					@click="selected = i"
				>
					{{ value || (p.notes[String(i)] || []).join(" ") || "·" }}
				</button>
			</div>
			<div class="tools">
				<button
					v-for="n in [1, 2, 3, 4, 0]"
					:key="n"
					:disabled="disabled || selected === null"
					@click="send(notes ? 'note' : 'cell', { cell: selected, value: n })"
				>
					{{ n || $t("Erase") }}</button
				><button :aria-pressed="notes" @click="notes = !notes">
					{{ $t("Notes") }} {{ notes ? "✓" : "" }}
				</button>
			</div>
		</template>
		<template v-else-if="p.game === 'hidden-picture'">
			<div class="nonogram">
				<span></span
				><span v-for="(clue, i) in p.columns" :key="'c' + i" class="clue">{{
					clue.join(" · ")
				}}</span
				><template v-for="(clue, r) in p.rows" :key="r"
					><span class="clue">{{ clue.join(" · ") }}</span
					><button
						v-for="c in 5"
						:key="c"
						:data-cell="r * 5 + c - 1"
						:class="{ filled: p.cells[r * 5 + c - 1] === 1 }"
						:disabled="disabled"
						:aria-label="`${$t('Cell')} ${r + 1}, ${c}: ${p.cells[r * 5 + c - 1] === 1 ? $t('Filled') : p.cells[r * 5 + c - 1] === 2 ? $t('Crossed') : $t('Unknown')}`"
						@click="
							send('cell', {
								cell: r * 5 + c - 1,
								value: (p.cells[r * 5 + c - 1] + 1) % 3,
							})
						"
					>
						{{
							p.cells[r * 5 + c - 1] === 2
								? "×"
								: p.cells[r * 5 + c - 1] === 1
									? "■"
									: "·"
						}}
					</button></template
				>
			</div>
		</template>
		<template v-else-if="p.game === 'path-weaver'">
			<div class="board five">
				<button
					v-for="i in 25"
					:key="i"
					:data-cell="i - 1"
					:disabled="disabled || p.blocked.includes(i - 1)"
					:class="{ filled: p.path.includes(i - 1), blocked: p.blocked.includes(i - 1) }"
					:aria-label="`${$t('Cell')} ${Math.floor((i - 1) / 5) + 1}, ${((i - 1) % 5) + 1}`"
					@click="send('cell', { cell: i - 1 })"
				>
					{{
						i === 1
							? "S"
							: i - 1 === p.exit
								? "⚑"
								: p.blocked.includes(i - 1)
									? "▧"
									: p.checkpoints.includes(i - 1)
										? "★"
										: p.path.includes(i - 1)
											? p.path.indexOf(i - 1) + 1
											: "·"
					}}
				</button>
			</div>
			<button :disabled="disabled || p.path.length < 2" @click="send('undo')">
				{{ $t("Undo") }}
			</button>
		</template>
		<template v-else-if="p.game === 'quilt-puzzle'">
			<div class="board">
				<button
					v-for="i in 16"
					:key="i"
					:data-cell="i - 1"
					:disabled="disabled"
					:class="{ filled: owner(i - 1) !== null }"
					@click="send('place', { piece, rotation, cell: i - 1 })"
					:aria-label="`${$t('Place patch at cell')} ${i}`"
				>
					{{ owner(i - 1) === null ? "·" : Number(owner(i - 1)) + 1 }}
				</button>
			</div>
			<div class="tools">
				<button
					v-for="(shape, i) in p.pieces"
					:key="i"
					:aria-pressed="piece === i"
					@click="piece = i"
				>
					{{ $t("Patch") }} {{ i + 1
					}}<svg viewBox="0 0 4 4" width="44" height="44" aria-hidden="true">
						<rect
							v-for="([x, y], j) in oriented(shape, i)"
							:key="j"
							:x="x"
							:y="y"
							width=".9"
							height=".9"
							fill="currentColor"
						/>
					</svg>
				</button>
			</div>
			<div class="tools">
				<button @click="rotation = (rotation + 1) % 4">
					{{ $t("Rotate") }} {{ rotation * 90 }}°</button
				><button
					:disabled="disabled || !p.placements[String(piece)]"
					@click="send('remove', { piece })"
				>
					{{ $t("Remove patch") }}
				</button>
			</div>
		</template>
		<div v-if="view.is_host && !p.done" class="tools">
			<button
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
		</div>
		<button
			v-if="p.done && view.is_host"
			@click="$emit('command', { command: 'next', revision: view.revision })"
		>
			{{ $t("Finish game") }}
		</button>
		<p v-if="!view.can_move && !p.done">
			{{ $t("Watch the board and help your room decide.") }}
		</p>
	</section>
</template>
<script setup>
import { computed, ref } from "vue";
import { t } from "@/i18n";
const props = defineProps({ view: Object, busy: Boolean, error: String });
const emit = defineEmits(["move", "command"]);
const p = computed(() => props.view.puzzle);
const shareNotice = ref("");
async function shareResult() {
	const result =
		p.value.game === "dots-and-boxes"
			? `X ${p.value.scores.X} : ${p.value.scores.O} O`
			: `${p.value.moves} ${t("moves")}`;
	const text = `${t(title.value)} · ${result}\n${window.location.origin}/play/games/${p.value.game}`;
	try {
		if (navigator.share) await navigator.share({ title: t(title.value), text });
		else {
			await navigator.clipboard.writeText(text);
			shareNotice.value = "Result copied";
		}
	} catch (e) {
		if (e.name !== "AbortError")
			shareNotice.value = "Copy the game link from your browser to share.";
	}
}
const selected = ref(null),
	notes = ref(false),
	piece = ref(0),
	rotation = ref(0);
const disabled = computed(
	() => props.busy || props.view.paused || p.value.done || !props.view.can_move,
);
const names = {
	"dots-and-boxes": [
		"Dots and Boxes",
		"Tap an edge. Complete a box to claim it and play again.",
	],
	"group-sudoku": ["Group Sudoku", "Fill every row, column and region with 1, 2, 3 and 4."],
	"path-weaver": [
		"Path Weaver",
		"Connect S to the flag. Visit every star without crossing your path.",
	],
	"hidden-picture": [
		"Hidden Picture",
		"Numbers show consecutive filled cells. Tap to fill, cross or clear.",
	],
	"quilt-puzzle": [
		"Quilt Puzzle",
		"Cover the quilt with every patch. Rotate pieces; leave no gaps or overlaps.",
	],
};
const title = computed(() => names[p.value.game][0]);
const instruction = computed(() => names[p.value.game][1]);
function edge(r, c) {
	return r % 2 ? `h:${(r - 1) / 2}:${c / 2 - 1}` : `v:${r / 2 - 1}:${(c - 1) / 2}`;
}
function oriented(shape, index) {
	let points = shape.map(([x, y]) => [x, y]);
	if (index === piece.value)
		for (let r = 0; r < rotation.value; r++) points = points.map(([x, y]) => [-y, x]);
	const minx = Math.min(...points.map((p) => p[0])),
		miny = Math.min(...points.map((p) => p[1]));
	return points.map(([x, y]) => [x - minx, y - miny]);
}
function owner(cell) {
	return (
		Object.keys(p.value.placements).find((k) => p.value.placements[k].includes(cell)) ?? null
	);
}
function send(action, payload = {}) {
	if (!disabled.value)
		emit("move", { action_type: action, ...payload, revision: props.view.revision });
}
</script>
<style scoped>
.puzzle-room {
	width: min(100%, 44rem);
	margin: auto;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 1rem;
	color: #f6f0e6;
	text-align: center;
}
.puzzle-room h1 {
	font-size: clamp(1.7rem, 4vw, 3rem);
	font-weight: 850;
}
.puzzle-room header p {
	max-width: 38rem;
	line-height: 1.6;
}
.puzzle-room button {
	min-height: 44px;
	border: 2px solid #737085;
	border-radius: 0.65rem;
	background: #292637;
	color: #fff;
	font-weight: 750;
	padding: 0.6rem;
}
.puzzle-room button:focus-visible {
	outline: 4px solid #ffca73;
	outline-offset: 3px;
}
.puzzle-room button:disabled {
	cursor: default;
}
.board {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	width: min(100%, 26rem);
	gap: 4px;
}
.board button {
	aspect-ratio: 1;
	font-size: 1.5rem;
}
.board.five {
	grid-template-columns: repeat(5, 1fr);
}
.board .given {
	background: #454151;
}
.board .selected {
	outline: 3px solid #ffca73;
}
.sudoku button:nth-child(4n + 2) {
	border-right: 5px solid #ffca73;
}
.sudoku button:nth-child(n + 5):nth-child(-n + 8) {
	border-bottom: 5px solid #ffca73;
}
.tools {
	display: flex;
	flex-wrap: wrap;
	justify-content: center;
	gap: 0.5rem;
}
.tools [aria-pressed="true"] {
	border-color: #ffca73;
}
.nonogram {
	display: grid;
	grid-template-columns: 2.5rem repeat(5, minmax(0, 1fr));
	width: min(100%, 28rem);
	gap: 3px;
}
.nonogram button {
	aspect-ratio: 1;
}
.clue {
	align-self: center;
	font-weight: 800;
}
.puzzle-room .filled {
	background: #4aada8;
	color: #142d30;
}
.puzzle-room .blocked {
	background: #15131d;
	color: #706b80;
}
.dots {
	display: grid;
	grid-template-columns: 18px 1fr 18px 1fr 18px 1fr 18px;
	grid-template-rows: 18px 1fr 18px 1fr 18px 1fr 18px;
	width: min(100%, 28rem);
	aspect-ratio: 1;
	align-items: center;
	justify-items: center;
}
.dots .edge {
	padding: 0;
	min-height: 18px;
	border: 0;
	background: #494357;
}
.dots .horizontal {
	width: 100%;
	height: 18px;
}
.dots .vertical {
	height: 100%;
	width: 18px;
}
.dots .edge span {
	font-size: 12px;
}
.dots .taken {
	background: #ffca73;
	color: #292637;
}
.box {
	font-size: 2rem;
}
.dot {
	color: #fff;
}
.success {
	color: #8ce3b7;
	font-size: 1.5rem;
}
.error {
	background: #612b3a;
	padding: 1rem;
	border-radius: 1rem;
}
</style>
<style scoped>
.puzzle-room {
	background: #211d2c;
	border: 1px solid #62586f;
	border-radius: 1.5rem;
	padding: clamp(1rem, 3vw, 2rem);
	box-sizing: border-box;
}
.dots {
	grid-template-columns: 32px 1fr 32px 1fr 32px 1fr 32px;
	grid-template-rows: 32px 1fr 32px 1fr 32px 1fr 32px;
}
.dots .edge {
	position: relative;
	overflow: visible;
	background: transparent;
}
.dots .edge::before {
	content: "";
	position: absolute;
	inset: -8px;
	z-index: 1;
}
.dots .horizontal {
	background: linear-gradient(transparent 25%, #645871 25%, #645871 75%, transparent 75%);
	height: 32px;
}
.dots .vertical {
	background: linear-gradient(90deg, transparent 25%, #645871 25%, #645871 75%, transparent 75%);
	width: 32px;
}
.dots .horizontal.taken {
	background: linear-gradient(transparent 25%, #ffca73 25%, #ffca73 75%, transparent 75%);
}
.dots .vertical.taken {
	background: linear-gradient(90deg, transparent 25%, #ffca73 25%, #ffca73 75%, transparent 75%);
}
.dots .box[data-owner="X"] {
	color: #ffca73;
}
.dots .box[data-owner="O"] {
	color: #85d7d1;
}
</style>
