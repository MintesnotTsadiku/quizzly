<template>
	<div class="flex h-full flex-col items-center justify-center gap-4 p-4 text-center">
		<template v-if="kickedMessage">
			<p class="text-lg text-ink-gray-8">{{ kickedMessage }}</p>
			<Button variant="solid" @click="router.replace('/join')">Back to join</Button>
		</template>
		<template v-else-if="player">
			<p class="text-sm uppercase tracking-widest text-ink-gray-5">PIN {{ player.pin }}</p>
			<h1 class="text-3xl font-bold text-ink-gray-9">You're in, {{ player.nickname }}!</h1>
			<p class="text-ink-gray-6">
				See your name on the big screen. Waiting for the host to start…
			</p>
			<p class="text-sm text-ink-gray-5">{{ participants.length }} in the lobby</p>
			<Button variant="outline" @click="leave">Leave game</Button>
		</template>
	</div>
</template>

<script setup>
import { inject, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Button } from "frappe-ui";
import { call } from "@/api";
import { clearPlayer, loadPlayer } from "@/player";

const router = useRouter();
const socket = inject("$socket");

const player = ref(loadPlayer());
// seeded from the join snapshot; realtime lobby_update events replace it
const participants = ref(player.value?.participants || []);
const kickedMessage = ref("");
const eventName = player.value && `qz_session_${player.value.pin}`;

function onSessionEvent(message) {
	if (message.type === "lobby_update") {
		participants.value = message.participants;
	} else if (message.type === "kicked" && message.participant === player.value.participant) {
		clearPlayer();
		kickedMessage.value = "The host removed you from the game.";
	}
}

onMounted(() => {
	if (!player.value) {
		router.replace("/join");
		return;
	}
	socket.emit("qz_join", player.value.pin);
	socket.on(eventName, onSessionEvent);
});

onBeforeUnmount(() => {
	if (!eventName) return;
	socket.off(eventName, onSessionEvent);
	socket.emit("qz_leave", player.value?.pin);
});

async function leave() {
	try {
		await call("quizzly.api.leave_session", {
			pin: player.value.pin,
			token: player.value.token,
		});
	} catch {
		// leaving anyway
	}
	clearPlayer();
	router.replace("/join");
}
</script>
