<template>
	<div class="gather-ui gp-page">
		<HostBar />
		<main class="gp-account gp-container">
			<p class="gp-eyebrow">A game only your people could make</p>
			<h1>Put your room<br />in the questions.</h1>
			<p class="gp-lead">
				Make a private Crowd Compass pack. Everyone chooses, predicts the room, and
				discovers something new.
			</p>
			<section v-if="library.length" class="gp-pack-library">
				<h2>Your private packs</h2>
				<div>
					<button
						v-for="pack in library"
						:key="pack.name"
						class="gp-button gp-button-secondary"
						@click="edit(pack.name)"
					>
						{{ pack.title }} · Edit →
					</button>
				</div>
			</section>
			<div class="gp-author-layout">
				<form class="gp-account-card" @submit.prevent="save">
					<label class="gp-field"
						><span>Give your pack a name</span
						><input
							v-model="title"
							required
							maxlength="100"
							placeholder="Our kind of weekend"
					/></label>
					<fieldset v-for="(q, i) in prompts" :key="i" class="gp-question-card">
						<legend>Question {{ i + 1 }}</legend>
						<label class="gp-field"
							><span>Ask something with no wrong answer</span
							><textarea v-model="q.text" required maxlength="300" rows="2" /></label
						><label v-for="(_, j) in q.choices" :key="j" class="gp-field"
							><span>Choice {{ j + 1 }}</span
							><input v-model="q.choices[j]" required maxlength="120" /></label
						><button
							v-if="prompts.length > 1"
							type="button"
							class="gp-text-button"
							@click="prompts.splice(i, 1)"
						>
							Remove question
						</button>
					</fieldset>
					<button
						v-if="prompts.length < 20"
						type="button"
						class="gp-button gp-button-secondary"
						@click="prompts.push({ text: '', choices: ['', ''] })"
					>
						+ Add a question
					</button>
					<p v-if="error" class="gp-error" role="alert">
						{{ error }} <RouterLink to="/access">Your access →</RouterLink>
					</p>
					<p v-if="saved" class="gp-notice" role="status">
						Saved privately. Your room is ready when you are.
					</p>
					<div class="gp-stage-actions">
						<button class="gp-button" :disabled="busy">
							{{
								busy ? "Saving…" : saved ? "Save changes" : "Save my pack"
							}}</button
						><button
							v-if="saved"
							type="button"
							class="gp-button gp-button-secondary"
							:disabled="busy"
							@click="host"
						>
							Host this pack →
						</button>
					</div>
				</form>
				<aside class="gp-account-card gp-author-aside">
					<GameArtwork game-key="crowd-compass" color="lilac" />
					<h2>Make it easy to join in.</h2>
					<p>
						Use short questions, clear choices, and topics everyone can enjoy. Avoid
						asking people to share private or sensitive information.
					</p>
					<p>
						Your pack is only available to you and the games you host. It won’t appear
						in the public catalog.
					</p>
					<RouterLink to="/access">See your allowance →</RouterLink>
				</aside>
			</div>
		</main>
	</div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import HostBar from "@/components/HostBar.vue";
import GameArtwork from "@/platform/discovery/GameArtwork.vue";
import { call, readError } from "@/api";
import { refreshAccess } from "@/platform/site";
import { gpCall, rememberHostedSession } from "@/platform/session/gp";
const library = ref([]);
const router = useRouter(),
	title = ref("Our kind of weekend"),
	prompts = ref([
		{
			text: "A free afternoon together. What are we choosing?",
			choices: ["An adventure outside", "Something cosy inside"],
		},
	]),
	saved = ref(""),
	busy = ref(false),
	error = ref("");
async function save() {
	busy.value = true;
	error.value = "";
	try {
		await refreshAccess();
		const r = await call("quizzly.access.save_pack", {
			title: title.value,
			prompts: prompts.value,
			name: saved.value || undefined,
		});
		saved.value = r.name;
		library.value = await call("quizzly.access.my_packs");
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
async function host() {
	busy.value = true;
	error.value = "";
	try {
		const r = await gpCall("create_session", {
			game_key: "crowd-compass",
			configuration: {
				pack: saved.value,
				rounds: prompts.value.length,
				vote_seconds: 20,
				prediction_seconds: 20,
				auto_progress: 0,
			},
		});
		rememberHostedSession(r.session);
		router.push({ name: "GpHost", query: { session: r.session } });
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
async function edit(name) {
	busy.value = true;
	error.value = "";
	try {
		const pack = await call("quizzly.access.load_pack", { name });
		saved.value = pack.name;
		title.value = pack.title;
		prompts.value = pack.prompts;
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
onMounted(async () => {
	try {
		await refreshAccess();
		library.value = await call("quizzly.access.my_packs");
	} catch (e) {
		error.value = readError(e);
	}
});
</script>
