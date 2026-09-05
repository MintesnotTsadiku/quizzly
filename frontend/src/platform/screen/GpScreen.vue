<template>
	<div class="flex h-full flex-col overflow-hidden bg-night">
		<div class="flex justify-end px-4 py-2"><LanguageSwitch /></div>
		<RoundJourney v-if="!podium && gameKey === 'crowd-compass'" :arc="view.arc" />
		<!-- Podium outranks everything: the last thing a room sees must be the winner -->
		<div
			v-if="podium"
			class="flex min-h-0 flex-1 flex-col items-center gap-8 overflow-y-auto p-8"
		>
			<CrowdEnding v-if="gameKey === 'crowd-compass'" :ending="ending" screen />
			<GridEnding v-if="ending?.grid" :ending="ending" />
			<h2 v-if="!ending?.grid" class="font-display text-6xl font-extrabold text-paper">
				{{ $t("Final results") }}
			</h2>
			<ol
				v-if="!ending?.grid"
				class="grid w-full max-w-5xl gap-5"
				:class="podium.length > 2 ? 'sm:grid-cols-2' : ''"
			>
				<li
					v-for="team in rankedTeams(podium)"
					:key="team.name"
					class="flex items-center gap-5 rounded-3xl border bg-dusk px-8 py-5"
					:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
				>
					<span class="w-8 font-mono text-2xl tabular-nums text-paper/40">{{
						team.rank
					}}</span>
					<AvatarPic
						v-if="team.avatar"
						:id="team.avatar"
						:nickname="team.team_name"
						:size="44"
					/>
					<span
						v-else
						:class="teamStyle(team.color).fill"
						class="grid size-11 place-items-center rounded-full font-display text-lg font-extrabold text-sunk"
					>
						{{ team.rank }}
					</span>
					<span
						class="min-w-0 flex-1 truncate text-left font-display text-3xl font-bold text-paper"
					>
						{{ team.team_name }}
					</span>
					<span class="font-display text-4xl font-extrabold tabular-nums text-accent">
						{{ team.score }}
					</span>
				</li>
			</ol>
			<p class="font-mono uppercase tracking-[0.3em] text-paper/35">
				{{ $t("Thanks for playing") }}
			</p>
			<div class="flex flex-wrap justify-center gap-3">
				<RouterLink class="ctl ctl-go" :to="{ name: 'GpJoin' }">
					{{ $t("Join another game") }}
				</RouterLink>
				<RouterLink class="ctl" :to="{ name: 'Catalog' }">
					{{ $t("Back to all games") }}
				</RouterLink>
			</div>
		</div>

		<!-- Lobby -->
		<div
			v-else-if="status === 'Lobby'"
			class="flex min-h-0 flex-1 flex-col items-center justify-center gap-10 p-8"
		>
			<div class="flex flex-wrap items-center justify-center gap-8">
				<div class="text-center sm:text-left">
					<p class="max-w-3xl break-all font-mono text-xl text-accent">
						{{ $t("Join at") }} {{ joinUrl }}
						<button
							class="ml-1 inline-flex translate-y-1 rounded-md p-1 text-paper/35 transition hover:bg-dusk hover:text-paper"
							:title="copied ? 'Copied' : `Copy ${joinUrl}`"
							:aria-label="`Copy ${joinUrl}`"
							@click="copyJoinUrl"
						>
							<span v-if="copied">✓</span><span v-else>⧉</span>
						</button>
					</p>
					<p
						class="mt-4 text-center font-mono text-[9rem] font-bold leading-none tracking-[0.06em] text-paper sm:text-left"
					>
						{{ pin }}
					</p>
				</div>
				<img
					v-if="qrDataUrl"
					:src="qrDataUrl"
					:alt="$t('Join QR code')"
					class="size-48 rounded-2xl bg-card p-2"
				/>
			</div>
			<div class="flex w-full max-w-3xl flex-wrap justify-center gap-2.5">
				<span
					v-for="p in publicParticipants"
					:key="p.nickname"
					class="flex items-center gap-2 rounded-full border border-haze bg-dusk py-1.5 pl-1.5 pr-4 text-lg font-medium text-paper"
				>
					<AvatarPic :id="p.avatar" :nickname="p.nickname" :size="32" />
					{{ p.nickname }}
				</span>
			</div>
			<p class="font-mono uppercase tracking-[0.28em] text-paper/40">
				{{ publicParticipants.length }} {{ $t("in the room") }}
			</p>
		</div>

		<!-- Live: the projector is the room's face; prompts and controls live elsewhere -->
		<div
			v-else-if="status === 'Active'"
			class="flex min-h-0 flex-1 flex-col items-center gap-8 overflow-y-auto p-8"
		>
			<component
				:is="live.ScreenLive"
				:pin="pin"
				v-if="gamePhases.includes(view.phase)"
				:view="view"
				:remaining="remaining"
				:timer-percent="timerPercent"
				:solved-count="solvedCount"
			/>

			<template v-else-if="view.phase === 'scoreboard'">
				<h2 class="font-display text-5xl font-extrabold text-paper">
					{{ $t("Scoreboard") }}
				</h2>
				<ol
					class="grid w-full max-w-5xl gap-5"
					:class="(view.teams || []).length > 2 ? 'sm:grid-cols-2' : ''"
				>
					<li
						v-for="team in rankedTeams(view.teams || [])"
						:key="team.name"
						class="flex items-center gap-5 rounded-3xl border bg-dusk px-8 py-5"
						:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-8 font-mono text-2xl tabular-nums text-paper/40">{{
							team.rank
						}}</span>
						<AvatarPic
							v-if="team.avatar"
							:id="team.avatar"
							:nickname="team.team_name"
							:size="44"
						/>
						<span
							v-else
							:class="teamStyle(team.color).fill"
							class="grid size-11 place-items-center rounded-full font-display text-lg font-extrabold text-sunk"
						>
							{{ team.rank }}
						</span>
						<span
							class="min-w-0 flex-1 truncate text-left font-display text-3xl font-bold text-paper"
						>
							{{ team.team_name }}
						</span>
						<span
							class="font-display text-4xl font-extrabold tabular-nums text-accent"
						>
							{{ team.score }}
						</span>
					</li>
				</ol>
				<RouterLink class="ctl" :to="{ name: 'Catalog' }">
					{{ $t("Back to all games") }}
				</RouterLink>
			</template>

			<template v-else>
				<p class="font-mono uppercase tracking-[0.3em] text-paper/40">
					{{ $t("Here we go…") }}
				</p>
			</template>
		</div>

		<!-- Ended / unknown pin -->
		<div v-else class="flex min-h-0 flex-1 flex-col items-center justify-center gap-8 p-10">
			<h1 class="font-display text-6xl font-extrabold text-paper">
				{{ $t("See you next time") }}
			</h1>
			<p class="text-paper/50">{{ $t("Start the next room from the host console.") }}</p>
		</div>
	</div>
</template>

<script setup>
import RoundJourney from "@/platform/ending/RoundJourney.vue";
import GridEnding from "@/games/grid_conquest/Ending.vue";
import CrowdEnding from "@/platform/ending/CrowdEnding.vue";
import LanguageSwitch from "@/components/LanguageSwitch.vue";
import { locale } from "@/i18n";
import { computed, inject, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import QRCode from "qrcode";
import { useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";
import DrainRing from "@/components/DrainRing.vue";
import { initSound, playCue } from "@/sound";
import { gpCall, teamStyle } from "@/platform/session/gp";
import { liveFor, phasesFor } from "@/games/registry";

const socket = inject("$socket");
const route = useRoute();
const router = useRouter();
const {
	remaining,
	total: windowSeconds,
	start: startCountdown,
	stop: stopCountdown,
} = useCountdown();

// The screen knows a PIN and nothing else: every byte it renders is public state.
const pin = route.params.pin;
const status = ref("");
const gameKey = ref("cuecast");
const view = ref({});
const podium = ref(null);
const ending = ref(null);
const publicParticipants = ref([]);
const copied = ref(false);
const qrDataUrl = ref("");
let seqSeen = -1;
let stopRoom = null;
onBeforeUnmount(() => stopRoom?.());

const live = computed(() => liveFor(gameKey.value));
const gamePhases = computed(() => phasesFor(gameKey.value));
const joinUrl = `${window.location.origin}/play/join?pin=${pin}&lang=${locale.value}`;
const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0,
);
const solvedCount = computed(() => view.value.solved ?? 0);

function rankedTeams(list) {
	return [...list].sort((a, b) => (a.rank || 0) - (b.rank || 0) || b.score - a.score);
}

async function copyJoinUrl() {
	try {
		await navigator.clipboard.writeText(joinUrl);
		copied.value = true;
		setTimeout(() => (copied.value = false), 1500);
	} catch {
		copied.value = false;
	}
}

function onEvent(message) {
	if (!message || typeof message !== "object" || !message.type) return;
	if (typeof message.seq === "number") {
		if (message.seq < seqSeen) return;
		seqSeen = message.seq;
	}
	const type = message.type;
	const payload = message.payload || {};
	if (
		type === "platform.state_changed" ||
		type.split(".")[0] === gameKey.value.replace(/-/g, "_")
	) {
		status.value = "Active";
		if (payload.phase) {
			gameKey.value = message.game || gameKey.value;
			view.value = { ...view.value, ...payload };
			podium.value = null;
			playCue(payload.phase === "turn_open" ? "submit" : "tick");
			if (payload.phase === "turn_ready") startCountdown(3);
			else stopCountdown();
		}
		refresh();
	} else if (type === "platform.action_progress") {
		view.value = { ...view.value, solved: payload.count };
	} else if (type === "platform.scoreboard_updated") {
		view.value = {
			...view.value,
			phase: "scoreboard",
			arc: payload.arc || view.value.arc,
			teams: payload.teams,
		};
		stopCountdown();
	} else if (type === "platform.session_ended") {
		refresh();
		podium.value = payload.teams || [];
		status.value = "Ended";
		stopCountdown();
		playCue("podium");
	} else if (type === "platform.lobby_updated") {
		publicParticipants.value = payload.participants || [];
	}
}

async function refresh() {
	try {
		const state = await gpCall("get_public_state", { pin });
		applyState(state);
	} catch {
		status.value = "Unknown";
	}
}

function applyState(state) {
	if (state.game_key === "common-ground") {
		gameKey.value = state.game_key;
		router.replace({ name: "RoomScreen", params: { pin } });
		return;
	}
	if (state.participants) publicParticipants.value = state.participants;
	seqSeen = Math.max(seqSeen, state.state_version ?? 0);
	gameKey.value = state.game_key || gameKey.value;
	status.value = state.status;
	if (state.podium) {
		podium.value = state.podium;
		ending.value = state.ending || null;
	}
	if (state.view) view.value = { ...view.value, ...state.view };
	if (
		status.value === "Active" &&
		[
			"turn_ready",
			"turn_open",
			"prompt_open",
			"prediction_open",
			"draw_ready",
			"draw_open",
			"round_open",
		].includes(state.phase)
	) {
		startCountdown(Math.max(0.5, state.remaining_seconds));
	} else {
		stopCountdown();
	}
}

onMounted(async () => {
	initSound("host");
	qrDataUrl.value = await QRCode.toDataURL(joinUrl, {
		margin: 1,
		width: 800,
		errorCorrectionLevel: "H",
		color: { dark: "#16111F", light: "#F4F0FA" },
	});
	await refresh();
	if (gameKey.value === "common-ground") return;
	stopRoom = useSessionRoom(socket, pin, onEvent, refresh, "gp");
});
</script>
