<template>
	<section
		v-if="view.phase === 'seek_review'"
		class="flex w-full max-w-xl flex-col gap-4 rounded-3xl bg-dusk p-6 text-paper"
	>
		<h1 class="text-3xl font-bold">{{ $t("Show the room") }}</h1>
		<p>
			{{
				$t(
					"Invite each person to show or describe their find. Mark the missions the room has seen, then reveal.",
				)
			}}
		</p>
		<label
			v-for="mission in view.missions"
			:key="mission.participant"
			class="flex items-center gap-3 rounded-xl border border-haze p-4"
			><input type="checkbox" v-model="approved" :value="mission.participant" />{{
				mission.nickname
			}}: {{ mission.value }}</label
		><button
			class="ctl ctl-go"
			:disabled="busy"
			@click="$emit('grid-command', { command: 'confirm_missions', approved })"
		>
			{{ $t("Confirm and reveal") }}
		</button>
	</section>
	<ScreenLive v-else :view="view" :remaining="remaining" :timer-percent="timerPercent" />
</template>
<script setup>
import { ref, watch } from "vue";
import ScreenLive from "./ScreenLive.vue";
const props = defineProps({
	view: Object,
	remaining: Number,
	timerPercent: Number,
	busy: Boolean,
});
defineEmits(["grid-command"]);
const approved = ref([]);
watch(
	() => props.view.round,
	() => (approved.value = []),
);
</script>
