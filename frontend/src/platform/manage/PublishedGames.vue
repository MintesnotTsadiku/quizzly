<template>
	<div class="gather-ui gp-page">
		<HostBar />
		<main class="gp-container">
			<h1>{{ $t("Published games") }}</h1>
			<p>
				{{
					$t(
						"Choose the games people can discover and host on this site. Existing rooms can finish after a game is unpublished."
					)
				}}
			</p>
			<p v-if="error" class="gp-error" role="alert">{{ $t(error) }}</p>
			<form v-if="loaded" @submit.prevent="save">
				<fieldset class="publication-grid">
					<legend>{{ $t("Installed game formats") }}</legend>
					<label v-for="game in games" :key="game.key" class="publication-choice">
						<input type="checkbox" v-model="selected" :value="game.key" />
						<span
							>{{ $t(game.title) }}
							<small v-if="game.status === 'Beta'">Beta</small></span
						>
					</label>
				</fieldset>
				<p>{{ $t("{count} games published", { count: selected.length }) }}</p>
				<button class="gp-button" :disabled="busy">
					{{ $t(busy ? "Saving…" : "Save publication settings") }}
				</button>
				<p role="status">{{ $t(message) }}</p>
			</form>
		</main>
	</div>
</template>
<script setup>
import { onMounted, ref } from "vue";
import HostBar from "@/components/HostBar.vue";
import { call, readError } from "@/api";
const games = ref([]),
	selected = ref([]),
	error = ref(""),
	message = ref(""),
	busy = ref(false),
	loaded = ref(false);
onMounted(async () => {
	try {
		const data = await call("quizzly.publishing.management");
		games.value = data.games;
		selected.value = data.games.filter((g) => g.published).map((g) => g.key);
		loaded.value = true;
	} catch (e) {
		error.value = readError(e);
	}
});
async function save() {
	busy.value = true;
	error.value = "";
	message.value = "";
	try {
		await call("quizzly.publishing.save", { published: selected.value });
		message.value = "Publication settings saved.";
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
</script>
<style scoped>
.publication-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
	gap: 12px;
	margin: 24px 0;
}
.publication-choice {
	display: flex;
	align-items: center;
	gap: 12px;
	padding: 14px;
	border: 1px solid currentColor;
	border-radius: 12px;
}
.publication-choice input {
	width: 22px;
	height: 22px;
}
</style>
