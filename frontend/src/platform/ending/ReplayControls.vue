<template>
	<div class="replay-controls">
		<p v-if="batch">
			{{ $t("{count} unseen prompts remain for this group", { count: batch.remaining }) }}
		</p>
		<p>
			{{
				$t(
					"Continue with the same group. Connected players follow the next room automatically."
				)
			}}
		</p>
		<button
			v-if="!batch || (batch.next_count && !batch.scope_changed)"
			class="gp-button ctl ctl-go"
			:disabled="busy"
			@click="replay(false)"
		>
			{{
				batch
					? $t("Play next {count} prompts", { count: batch.next_count })
					: $t("Play again")
			}}
		</button>
		<p v-if="batch && !batch.remaining">
			{{ $t("You have played every prompt in this pack.") }}
		</p>
		<p v-if="batch?.scope_changed">
			{{ $t("The pack language changed. Reset to start a new sequence.") }}
		</p>
		<button
			v-if="batch || error"
			class="gp-button gp-button-secondary ctl"
			:disabled="busy"
			@click="resetting = true"
		>
			{{ $t("Reset this group’s history") }}
		</button>
		<div v-if="resetting" role="group">
			<p>
				{{
					$t(
						"Allow previously played prompts again? This only resets your next sequence."
					)
				}}
			</p>
			<button class="gp-button ctl" :disabled="busy" @click="replay(true)">
				{{ $t("Reset and play again") }}
			</button>
			<button class="gp-button gp-button-secondary ctl" @click="resetting = false">
				{{ $t("Cancel") }}
			</button>
		</div>
		<p v-if="error" role="alert">{{ $t(error) }}</p>
	</div>
</template>
<script setup>
import { ref } from "vue";
import { call, readError } from "@/api";
const props = defineProps({
	session: String,
	quiz: { type: Boolean, default: false },
	batch: Object,
});
const emit = defineEmits(["created"]);
const busy = ref(false),
	error = ref(""),
	resetting = ref(false);
async function replay(reset) {
	if (busy.value) return;
	busy.value = true;
	error.value = "";
	try {
		const created = await call("quizzly.batches.replay", {
			session: props.session,
			quiz: props.quiz,
			reset,
		});
		emit("created", created);
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
</script>
<style scoped>
.replay-controls {
	margin: 16px 0;
	display: flex;
	flex-wrap: wrap;
	gap: 12px;
	align-items: center;
	justify-content: center;
}
.replay-controls p {
	width: 100%;
	margin: 0;
}
</style>
