<template>
	<div class="gather-ui gp-stage" :class="{ 'gp-stage-screen': screen }">
		<header class="gp-stage-top">
			<RouterLink class="gp-brand" to="/">✳ {{ site.product_name }}</RouterLink
			><span>Common Ground · {{ screen ? "Shared screen" : "Host view" }}</span
			><a
				v-if="!screen && snapshot.game_pin"
				class="gp-button gp-button-secondary gp-button-small"
				:href="screenUrl"
				target="_blank"
				rel="noopener"
				>Open shared screen ↗</a
			>
		</header>
		<main class="gp-stage-main">
			<p v-if="error" class="gp-error" role="alert">{{ error }}</p>
			<template v-if="!snapshot.status"
				><p role="status">
					{{ error ? "Your room will reconnect automatically." : "Opening your room…" }}
				</p>
				<RouterLink v-if="error" class="gp-button gp-button-secondary" to="/"
					>Explore games</RouterLink
				></template
			>
			<template
				v-else-if="snapshot.status === 'Unknown' || snapshot.game_key !== 'common-ground'"
				><h1>This room isn’t available.</h1>
				<p>Check the shared-screen link with your host.</p>
				<RouterLink class="gp-button" to="/">Explore games</RouterLink></template
			>
			<template v-else-if="snapshot.status === 'Lobby'">
				<GameArtwork game-key="common-ground" color="peach" />
				<p class="gp-eyebrow">Everyone’s already invited</p>
				<h1>Put the phones down.<br />Pull your people closer.</h1>
				<p>
					Make little groups of 2–5. You’ll find surprising things you share, one playful
					prompt at a time.
				</p>
				<p class="gp-stage-support">
					Sit, stand, speak or gesture. Anyone can pass. No sign-ups for players.
				</p>
				<div v-if="!screen" class="gp-stage-actions">
					<button class="gp-button" :disabled="busy || !!error" @click="start">
						{{ busy ? "Getting started…" : "Everyone’s ready · Let’s play" }} →
					</button>
				</div>
				<p v-else class="gp-caption">Your host will start when the room is ready.</p>
			</template>
			<template v-else-if="snapshot.status === 'Ended'">
				<GameArtwork game-key="common-ground" color="lime" />
				<p class="gp-eyebrow">Good company wins</p>
				<h1>A little more<br />in common.</h1>
				<p>Before you go: tell someone one thing you’re glad you discovered about them.</p>
				<div v-if="!screen" class="gp-stage-actions">
					<button class="gp-button" :disabled="busy" @click="replay">
						{{ busy ? "Opening…" : "Play another round" }} ↻</button
					><RouterLink class="gp-button gp-button-secondary" to="/"
						>Find our next game →</RouterLink
					>
				</div>
				<p v-else class="gp-caption">Thanks for playing together.</p>
			</template>
			<template v-else-if="snapshot.view">
				<p class="gp-eyebrow">
					{{
						snapshot.phase === "room_share"
							? "Share a little surprise"
							: "Talk it through together"
					}}
					· {{ snapshot.view.round }} of {{ snapshot.view.rounds }}
				</p>
				<div class="gp-stage-progress" aria-hidden="true">
					<span
						v-for="n in snapshot.view.rounds"
						:key="n"
						:data-done="n <= snapshot.view.round"
					></span>
				</div>
				<h1>
					{{
						snapshot.phase === "room_share"
							? snapshot.view.share
							: snapshot.view.prompt
					}}
				</h1>
				<p>
					{{
						snapshot.phase === "room_share"
							? "Invite a few groups to share. Listening counts as joining in."
							: snapshot.view.instruction
					}}
				</p>
				<p class="gp-stage-support">
					{{
						snapshot.phase === "room_share"
							? "In a big room, hear from two or three groups. Save time for everyone to keep playing."
							: "Take turns. Make space for quieter voices. Anyone can pass."
					}}
				</p>
				<div v-if="!screen" class="gp-stage-actions">
					<button class="gp-button" :disabled="busy || !!error" @click="advance">
						{{
							busy
								? "Moving on…"
								: snapshot.phase === "room_prompt"
									? "We’re ready to share"
									: snapshot.view.round === snapshot.view.rounds
										? "Finish together"
										: "Next conversation"
						}}
						→
					</button>
				</div>
			</template>
			<p v-else role="status">Getting your next prompt…</p>
		</main>
		<footer class="gp-stage-foot">
			<template v-if="snapshot.status === 'Active'"
				>No countdown. Take the time your people need.</template
			><template v-else>One room. Many ways to belong.</template
			><button
				v-if="!screen && ['Lobby', 'Active'].includes(snapshot.status)"
				class="gp-example-next"
				style="margin-left: 20px"
				@click="ending = true"
			>
				End game
			</button>
		</footer>
		<dialog ref="endDialog" @cancel="ending = false" class="gp-end-dialog">
			<h2>Finish this game?</h2>
			<p>You can choose another game or start a fresh round afterwards.</p>
			<div class="gp-stage-actions">
				<button class="gp-button gp-button-secondary" @click="ending = false">
					Keep playing</button
				><button class="gp-button" :disabled="busy" @click="end">Finish game</button>
			</div>
		</dialog>
	</div>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import GameArtwork from "@/platform/discovery/GameArtwork.vue";
import { gpCall, rememberHostedSession, forgetHostedSession } from "@/platform/session/gp";
import { site } from "@/platform/site";
import { readError } from "@/api";
const route = useRoute(),
	router = useRouter();
const screen = computed(() => route.name === "RoomScreen");
const snapshot = ref({}),
	error = ref(""),
	busy = ref(false),
	ending = ref(false),
	endDialog = ref(null);
const screenUrl = computed(
	() => router.resolve({ name: "RoomScreen", params: { pin: snapshot.value.game_pin } }).href,
);
let timer,
	stopped = false,
	failures = 0;
watch(ending, async (open) => {
	await nextTick();
	if (open) endDialog.value?.showModal();
	else endDialog.value?.close();
});
async function refresh() {
	try {
		const state = await gpCall(
			screen.value ? "get_public_state" : "get_host_state",
			screen.value ? { pin: route.params.pin } : { session: route.params.session },
		);
		if (stopped) return;
		snapshot.value = Object.keys(state).length ? state : { status: "Unknown" };
		error.value = "";
		failures = 0;
	} catch (e) {
		if (stopped) return;
		failures++;
		error.value = snapshot.value.status
			? "Connection interrupted. Keep talking — reconnecting before the next prompt."
			: readError(e);
	}
}
async function poll() {
	await refresh();
	if (!stopped) timer = setTimeout(poll, failures ? Math.min(15000, 3000 * failures) : 3000);
}
onMounted(poll);
onBeforeUnmount(() => {
	stopped = true;
	clearTimeout(timer);
});
async function act(method, args) {
	if (busy.value) return;
	busy.value = true;
	error.value = "";
	try {
		await gpCall(method, args);
		await refresh();
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
function start() {
	return act("start_session", { session: route.params.session });
}
function advance() {
	return act("advance_room", {
		session: route.params.session,
		expected_version: snapshot.value.state_version,
	});
}
async function end() {
	ending.value = false;
	await act("end_session", { session: route.params.session });
	if (snapshot.value.status === "Unknown") {
		forgetHostedSession();
		router.push("/");
	}
}
async function replay() {
	busy.value = true;
	try {
		const created = await gpCall("create_session", {
			game_key: "common-ground",
			configuration: { pack: snapshot.value.configuration?.pack || "everyday" },
		});
		rememberHostedSession(created.session);
		await router.push({ name: "RoomHost", params: { session: created.session } });
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
watch(
	() => route.params.session,
	() => {
		snapshot.value = {};
		refresh();
	},
);
watch(
	() => snapshot.value.status,
	(status) => {
		if (status === "Ended" && !screen.value) forgetHostedSession();
	},
);
</script>
<style scoped>
.gp-end-dialog {
	max-width: 440px;
	width: calc(100% - 40px);
	padding: 30px;
	border-radius: 20px;
	border: 1px solid var(--gp-line);
	background: var(--gp-card);
	color: var(--gp-ink);
}
.gp-end-dialog::backdrop {
	background: #201329aa;
}
.gp-end-dialog h2 {
	font-size: 27px;
	margin-bottom: 14px;
}
.gp-end-dialog p {
	font-size: 14px;
	line-height: 1.7;
}
</style>
