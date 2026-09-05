<template>
	<canvas
		ref="canvas"
		class="w-full touch-none rounded-3xl bg-white shadow-inner"
		:class="interactive ? 'cursor-crosshair' : ''"
		width="960"
		height="600"
		role="img"
		:aria-label="$t('Live drawing canvas')"
		@pointerdown="start"
		@pointermove="move"
		@pointerup="finish"
		@pointercancel="finish"
	/>
</template>
<script setup>
import { onMounted, ref, watch } from "vue";
const props = defineProps({ strokes: { type: Array, default: () => [] }, interactive: Boolean });
const emit = defineEmits(["batch"]);
const canvas = ref(null);
let active = false,
	last = null,
	batch = [];
function point(e) {
	const r = canvas.value.getBoundingClientRect();
	return { x: (e.clientX - r.left) / r.width, y: (e.clientY - r.top) / r.height };
}
function start(e) {
	if (!props.interactive) return;
	active = true;
	last = point(e);
	batch = [];
	canvas.value.setPointerCapture(e.pointerId);
}
function move(e) {
	if (!active) return;
	const p = point(e),
		s = { x1: last.x, y1: last.y, x2: p.x, y2: p.y };
	batch.push(s);
	draw(s);
	last = p;
}
function finish() {
	if (!active) return;
	active = false;
	if (batch.length) emit("batch", batch.splice(0, 80));
	batch = [];
}
function draw(s) {
	const c = canvas.value?.getContext("2d");
	if (!c) return;
	c.strokeStyle = "#20172c";
	c.lineWidth = 7;
	c.lineCap = "round";
	c.beginPath();
	c.moveTo(s.x1 * 960, s.y1 * 600);
	c.lineTo(s.x2 * 960, s.y2 * 600);
	c.stroke();
}
function render() {
	const c = canvas.value?.getContext("2d");
	if (!c) return;
	c.clearRect(0, 0, 960, 600);
	for (const s of props.strokes) draw(s);
}
watch(() => props.strokes, render, { deep: true });
onMounted(render);
</script>
