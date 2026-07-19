import { onBeforeUnmount, ref } from "vue";

// Kahoot-style answer shapes. Index = canonical option id - 1.
export const SHAPES = [
	{
		id: "1",
		name: "triangle",
		fill: "bg-red-500",
		hover: "hover:bg-red-600",
		path: "M12 3 L22 20 L2 20 Z",
	},
	{
		id: "2",
		name: "diamond",
		fill: "bg-blue-500",
		hover: "hover:bg-blue-600",
		path: "M12 2 L22 12 L12 22 L2 12 Z",
	},
	{
		id: "3",
		name: "circle",
		fill: "bg-amber-500",
		hover: "hover:bg-amber-600",
		path: "M12 2 A10 10 0 1 1 11.99 2 Z",
	},
	{
		id: "4",
		name: "square",
		fill: "bg-green-600",
		hover: "hover:bg-green-700",
		path: "M3 3 H21 V21 H3 Z",
	},
];

export function shapeFor(optionId) {
	return SHAPES[Number(optionId) - 1];
}

// Deterministic per player and question, so a reload keeps the same order.
export function optionOrder(question, seed) {
	const ids = ["1", "2", "3", "4"].filter((id) => question.options[Number(id) - 1]);
	if (!question.randomize_answer_order) return ids;
	const random = mulberry32(hash(`${seed}:${question.question_row}`));
	for (let i = ids.length - 1; i > 0; i--) {
		const j = Math.floor(random() * (i + 1));
		[ids[i], ids[j]] = [ids[j], ids[i]];
	}
	return ids;
}

function hash(text) {
	let value = 2166136261;
	for (let i = 0; i < text.length; i++) {
		value = Math.imul(value ^ text.charCodeAt(i), 16777619);
	}
	return value >>> 0;
}

function mulberry32(seed) {
	return function () {
		seed = (seed + 0x6d2b79f5) | 0;
		let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

/**
 * Subscribe to a session's realtime room.
 *
 * socket.io reconnects on its own but the server-side room membership is gone,
 * so every reconnect has to re-emit qz_join. `resync` then repairs whatever was
 * missed while the socket was down.
 */
export function useSessionRoom(socket, pin, onEvent, resync) {
	const eventName = `qz_session_${pin}`;

	function join() {
		socket.emit("qz_join", pin);
		resync();
	}

	socket.on(eventName, onEvent);
	socket.on("connect", join);
	join();

	onBeforeUnmount(() => {
		socket.off(eventName, onEvent);
		socket.off("connect", join);
		socket.emit("qz_leave", pin);
	});
}

/** Local countdown. Ticks off elapsed wall time, never off the server clock. */
export function useCountdown() {
	const remaining = ref(0);
	const total = ref(0);
	let timer = null;

	function start(seconds) {
		stop();
		total.value = seconds;
		remaining.value = seconds;
		const endsAt = Date.now() + seconds * 1000;
		timer = setInterval(() => {
			remaining.value = Math.max(0, (endsAt - Date.now()) / 1000);
			if (remaining.value === 0) stop();
		}, 100);
	}

	function stop() {
		if (timer) clearInterval(timer);
		timer = null;
	}

	onBeforeUnmount(stop);
	return { remaining, total, start, stop };
}
