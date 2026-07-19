<template>
	<div class="flex h-full flex-col items-center gap-6 overflow-y-auto p-6">
		<template v-if="!session">
			<h1 class="text-2xl font-bold text-ink-gray-9">Host a game</h1>
			<ErrorMessage :message="error" />
			<div v-if="quizzes.length" class="flex w-full max-w-md flex-col gap-2">
				<button
					v-for="quiz in quizzes"
					:key="quiz.name"
					class="rounded-lg border border-outline-gray-2 p-4 text-left text-lg text-ink-gray-8 hover:bg-surface-gray-2"
					@click="startSession(quiz.name)"
				>
					{{ quiz.title }}
				</button>
			</div>
			<p v-else-if="loaded" class="text-ink-gray-6">
				No quizzes yet. Create a QZ Quiz in Desk first.
			</p>
		</template>

		<template v-else>
			<p class="text-sm uppercase tracking-widest text-ink-gray-5">Join at {{ joinUrl }}</p>
			<p class="text-8xl font-black tracking-widest text-ink-gray-9">{{ session.pin }}</p>
			<div class="flex items-center gap-3">
				<Button :variant="lobbyLocked ? 'solid' : 'outline'" @click="toggleLock">
					{{ lobbyLocked ? "Unlock lobby" : "Lock lobby" }}
				</Button>
				<span class="text-ink-gray-6">{{ participants.length }} joined</span>
			</div>
			<div class="flex max-w-2xl flex-wrap justify-center gap-2">
				<button
					v-for="participant in participants"
					:key="participant.name"
					class="rounded-full bg-surface-gray-2 px-4 py-2 text-lg font-medium text-ink-gray-8 hover:bg-surface-red-2 hover:line-through"
					title="Click to kick"
					@click="kick(participant)"
				>
					{{ participant.nickname }}
				</button>
			</div>
			<p v-if="!participants.length" class="text-ink-gray-5">Waiting for players…</p>
			<ErrorMessage :message="error" />
		</template>
	</div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref } from "vue";
import { Button, ErrorMessage } from "frappe-ui";
import { call } from "@/api";

const socket = inject("$socket");

const quizzes = ref([]);
const loaded = ref(false);
const session = ref(null);
const participants = ref([]);
const lobbyLocked = ref(false);
const error = ref("");

const joinUrl = computed(() => `${window.location.origin}/quizzly/join?pin=${session.value.pin}`);

onMounted(async () => {
	try {
		quizzes.value = await call("frappe.client.get_list", {
			doctype: "QZ Quiz",
			fields: ["name", "title"],
			order_by: "modified desc",
		});
		loaded.value = true;
	} catch (e) {
		error.value = "Could not load quizzes. Log into Desk with a Quiz Host account first.";
	}
});

onBeforeUnmount(() => {
	if (!session.value) return;
	socket.off(`qz_session_${session.value.pin}`, onSessionEvent);
	socket.emit("qz_leave", session.value.pin);
});

function onSessionEvent(message) {
	if (message.type === "lobby_update") {
		participants.value = message.participants;
		lobbyLocked.value = Boolean(message.lobby_locked);
	}
}

async function startSession(quiz) {
	error.value = "";
	try {
		const created = await call("quizzly.api.create_session", { quiz });
		session.value = { name: created.session, pin: created.game_pin };
		socket.emit("qz_join", created.game_pin);
		socket.on(`qz_session_${created.game_pin}`, onSessionEvent);
		const lobby = await call("quizzly.api.get_lobby", { session: created.session });
		participants.value = lobby.participants;
		lobbyLocked.value = Boolean(lobby.lobby_locked);
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	}
}

async function toggleLock() {
	const method = lobbyLocked.value ? "quizzly.api.unlock_lobby" : "quizzly.api.lock_lobby";
	const lobby = await call(method, { session: session.value.name });
	lobbyLocked.value = Boolean(lobby.lobby_locked);
}

async function kick(participant) {
	if (!window.confirm(`Kick ${participant.nickname}?`)) return;
	await call("quizzly.api.kick_participant", {
		session: session.value.name,
		participant: participant.name,
	});
}
</script>
