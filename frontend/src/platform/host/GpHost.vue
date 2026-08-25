<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<HostBar v-if="!inLiveSession" />

		<!-- No session: pick a game, then set it up -->
		<div
			v-if="!session && !loading"
			class="mx-auto w-full max-w-2xl flex-1 px-5 py-12 sm:px-8"
		>
			<template v-if="!setupGame">
				<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-accent">Host</p>
				<h1 class="mt-2 font-display text-4xl font-extrabold text-paper sm:text-5xl">
					Start a room
				</h1>
				<div class="mt-8 grid gap-5 sm:grid-cols-2">
					<button
						v-for="game in hostableGames"
						:key="game.key"
						class="group flex flex-col rounded-3xl border border-haze bg-dusk p-6 text-left transition hover:border-ember"
						@click="setupGame = game.key"
					>
						<span class="font-display text-2xl font-bold text-paper">{{
							game.title
						}}</span>
						<span class="mt-2 text-sm leading-relaxed text-paper/60">{{
							game.summary
						}}</span>
						<span
							class="mt-4 flex items-center gap-2 font-display text-sm font-bold text-accent transition group-hover:gap-3"
						>
							Set up <span aria-hidden="true">→</span>
						</span>
					</button>
				</div>
				<RouterLink
					class="mt-8 inline-block font-mono text-xs uppercase tracking-[0.22em] text-paper/40 transition hover:text-paper"
					:to="{ name: 'CrowdPackEditor' }"
				>
					Author Crowd Compass packs →
				</RouterLink>
			</template>

			<template v-else>
				<button
					class="font-mono text-xs uppercase tracking-[0.22em] text-paper/40 transition hover:text-paper"
					@click="setupGame = null"
				>
					← Games
				</button>
				<h1 class="mt-6 font-display text-4xl font-extrabold text-paper">
					{{ setupTitle }}
				</h1>

				<!-- CueCast setup -->
				<div v-if="setupGame === 'cuecast'" class="mt-8 flex flex-col gap-6">
					<div class="flex flex-col gap-2">
						<span
							class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
							>Deck</span
						>
						<PackPicker
							v-model="setup.deck"
							:packs="packs"
							@preview="previewPack = $event"
						/>
					</div>
					<div class="grid grid-cols-2 gap-5 sm:grid-cols-3">
						<div class="flex flex-col gap-2">
							<span
								class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
								>Round</span
							>
							<div class="flex gap-2">
								<button
									v-for="s in [30, 60, 90]"
									:key="s"
									type="button"
									class="ctl flex-1"
									:data-on="setup.seconds === s"
									@click="setup.seconds = s"
								>
									{{ s }}s
								</button>
							</div>
						</div>
						<div class="flex flex-col gap-2">
							<span
								class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
								>Teams</span
							>
							<div class="flex gap-2">
								<button
									v-for="n in [2, 3, 4]"
									:key="n"
									type="button"
									class="ctl flex-1"
									:data-on="setup.teams_count === n"
									@click="setup.teams_count = n"
								>
									{{ n }}
								</button>
							</div>
						</div>
						<PremiumToggle
							class="col-span-2 self-end sm:col-span-1"
							v-model="setup.sudden_death"
							label="Sudden death"
							hint="Break a tied game"
						/>
					</div>
				</div>
				<!-- Crowd Compass setup -->
				<div v-else class="mt-8 flex flex-col gap-6">
					<div class="flex flex-col gap-2">
						<span
							class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
							>Pack</span
						>
						<PackPicker
							v-model="setup.pack"
							:packs="packs"
							@preview="previewPack = $event"
						/>
						<button
							class="ctl self-start"
							:data-on="!setup.pack"
							@click="setup.pack = ''"
						>
							Blank room · compose prompts live
						</button>
					</div>
					<p v-if="selectedPackRanked" class="-mt-3 text-sm text-ok">
						Ranked pack: players pick a first and second choice; the room tally is
						weighted 2/1.
					</p>
					<div class="grid grid-cols-2 gap-5 sm:grid-cols-3">
						<div class="flex flex-col gap-2">
							<span
								class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
								>Vote time</span
							>
							<div class="flex gap-2">
								<button
									v-for="s in [10, 15, 20]"
									:key="s"
									type="button"
									class="ctl flex-1"
									:data-on="setup.vote_seconds === s"
									@click="setup.vote_seconds = s"
								>
									{{ s }}s
								</button>
							</div>
						</div>
						<div class="flex flex-col gap-2">
							<span
								class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
								>Predict time</span
							>
							<div class="flex gap-2">
								<button
									v-for="s in [10, 15, 20]"
									:key="s"
									type="button"
									class="ctl flex-1"
									:data-on="setup.prediction_seconds === s"
									@click="setup.prediction_seconds = s"
								>
									{{ s }}s
								</button>
							</div>
						</div>
						<div class="flex flex-col gap-2">
							<span
								class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
								>Scoring</span
							>
							<div class="flex gap-2">
								<button
									type="button"
									class="ctl flex-1"
									:data-on="setup.scoring_mode === 'Individual'"
									@click="setup.scoring_mode = 'Individual'"
								>
									Solo
								</button>
								<button
									type="button"
									class="ctl flex-1"
									:data-on="setup.scoring_mode === 'Team average'"
									@click="setup.scoring_mode = 'Team average'"
								>
									Teams
								</button>
							</div>
						</div>
					</div>
					<div class="grid gap-2 sm:grid-cols-2">
						<PremiumToggle
							v-model="setup.estimation"
							label="Share-estimation bonus"
							hint="Reward close percentage guesses"
						/>
						<PremiumToggle
							v-model="setup.room_match"
							label="Match-the-room +100"
							hint="Reward voting with the majority"
						/>
						<PremiumToggle
							v-if="setup.scoring_mode === 'Team average'"
							v-model="setup.team_match"
							label="Match-your-team +100"
							hint="Reward reading your own team"
						/>
					</div>
					<div class="grid grid-cols-2 gap-5">
						<label class="flex flex-col gap-2">
							<span
								class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
							>
								Rounds
							</span>
							<input
								v-model.number="setup.rounds"
								type="number"
								min="0"
								max="50"
								class="field"
								placeholder="All prompts"
							/>
							<span class="text-xs text-paper/35">0 plays the whole pack</span>
						</label>
						<label class="flex flex-col gap-2">
							<span
								class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
							>
								Vote quorum
							</span>
							<input
								v-model.number="setup.quorum"
								type="number"
								min="1"
								max="100"
								class="field"
							/>
							<span class="text-xs text-paper/35"
								>Below this, the prompt scores nothing</span
							>
						</label>
					</div>
					<div v-if="setup.scoring_mode === 'Team average'" class="flex flex-col gap-2">
						<span
							class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
							>Teams</span
						>
						<div class="flex gap-2">
							<button
								v-for="n in [2, 3, 4]"
								:key="n"
								type="button"
								class="ctl flex-1"
								:data-on="setup.teams_count === n"
								@click="setup.teams_count = n"
							>
								{{ n }}
							</button>
						</div>
					</div>
					<RouterLink
						class="w-fit font-mono text-xs uppercase tracking-[0.22em] text-paper/40 transition hover:text-paper"
						:to="{ name: 'CrowdPackEditor' }"
					>
						Author packs →
					</RouterLink>
				</div>
				<PremiumToggle
					class="mt-6"
					v-model="setup.auto_progress"
					label="Automatic presentation"
					hint="Advance settled results automatically; turn this off to hold them until Next."
				/>

				<button
					class="ctl ctl-go mt-8 self-start px-8"
					:disabled="creating"
					@click="createSession"
				>
					{{ creating ? "Opening…" : "Open the lobby" }}
				</button>
				<p v-if="error" class="mt-4 text-alert">{{ error }}</p>
			</template>
		</div>
		<!-- Lobby -->
		<div
			v-else-if="phase === 'lobby'"
			class="flex min-h-0 flex-1 flex-col justify-center gap-10 p-5 sm:p-10"
		>
			<div class="flex flex-wrap items-center justify-center gap-10">
				<div class="text-center sm:text-left">
					<p class="break-all font-mono text-sm text-accent">
						Join at {{ joinUrl() }}
						<button
							class="ml-1 inline-flex translate-y-1 rounded-md p-1 text-paper/35 transition hover:bg-dusk hover:text-paper"
							:title="copied ? 'Copied' : `Copy ${joinUrl()}`"
							:aria-label="`Copy ${joinUrl()}`"
							@click="copyJoinUrl"
						>
							<svg
								class="size-4"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
							>
								<polyline v-if="copied" points="20 6 9 17 4 12" />
								<template v-else>
									<rect x="9" y="9" width="13" height="13" rx="2" />
									<path
										d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
									/>
								</template>
							</svg>
						</button>
					</p>
					<p
						class="mt-2 font-mono text-7xl font-bold tracking-[0.08em] text-paper sm:text-8xl"
					>
						{{ pin }}
					</p>
					<button class="ctl mt-5" :data-on="lobbyLocked" @click="toggleLock">
						{{ lobbyLocked ? "Lobby locked" : "Lock lobby" }}
					</button>
				</div>
				<button v-if="qrDataUrl" @click="qrFullscreen = true">
					<img
						:src="qrDataUrl"
						alt="Join QR code"
						class="size-44 rounded-2xl bg-card p-2 transition hover:scale-105"
					/>
				</button>
			</div>

			<div v-if="unassigned.length || teams.length" class="flex flex-col gap-5">
				<div
					v-if="unassigned.length"
					class="flex flex-wrap items-center justify-center gap-2"
				>
					<span
						v-for="p in unassigned"
						:key="p.name"
						class="group relative flex items-center gap-2 rounded-full border border-haze bg-dusk py-1 pl-1 pr-4 text-base font-medium text-paper sm:text-lg"
					>
						<AvatarPic :id="p.avatar" :nickname="p.nickname" :size="32" />
						{{ p.nickname }}
						<button
							class="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full bg-haze text-xs leading-none text-paper opacity-0 transition hover:bg-alert group-hover:opacity-100"
							:aria-label="`Remove ${p.nickname}`"
							@click="kick(p)"
						>
							×
						</button>
					</span>
					<span
						v-if="teamCapable"
						class="font-mono text-xs uppercase tracking-wider text-paper/40"
					>
						pick teams below to sort them
					</span>
				</div>

				<div class="grid gap-5" :class="teamCols">
					<div
						v-for="team in teams"
						:key="team.name"
						class="rounded-3xl border bg-dusk/60 p-5"
						:class="teamStyle(team.color).border"
					>
						<div class="flex items-center justify-between gap-2">
							<input
								v-model="team.editName"
								class="min-w-0 border-b border-transparent bg-transparent font-display text-lg font-bold text-paper focus:border-paper focus:outline-none"
								@change="renameTeam(team)"
							/>
							<span class="font-mono text-xs tabular-nums text-paper/40">
								{{ teamMembers(team.name).length }}
							</span>
						</div>
						<div class="mt-3 flex gap-2" aria-label="Team color">
							<button
								v-for="color in teamColors"
								:key="color"
								type="button"
								class="size-5 rounded-full border-2 transition"
								:class="[
									teamStyle(color).fill,
									team.color === color ? 'border-paper' : 'border-transparent',
								]"
								:aria-label="`Use ${color} for ${team.editName}`"
								@click="recolorTeam(team, color)"
							/>
						</div>
						<div class="mt-4 flex min-h-9 flex-wrap gap-2">
							<span
								v-for="p in teamMembers(team.name)"
								:key="p.name"
								class="group relative flex items-center gap-2 rounded-full py-1 pl-1 pr-3 text-sm font-medium"
								:class="[teamStyle(team.color).fill, teamStyle(team.color).text]"
							>
								<AvatarPic :id="p.avatar" :nickname="p.nickname" :size="26" />
								{{ p.nickname }}
								<button
									class="absolute -right-1 -top-1 grid size-5 place-items-center rounded-full bg-haze text-xs leading-none text-paper opacity-0 transition hover:bg-alert group-hover:opacity-100"
									:aria-label="`Remove ${p.nickname}`"
									@click="kick(p)"
								>
									×
								</button>
							</span>
							<span
								v-if="!teamMembers(team.name).length"
								class="text-sm italic text-paper/35"
								>waiting…</span
							>
						</div>
					</div>
				</div>
			</div>
			<p v-else class="text-center text-paper/35">Waiting for the first player…</p>

			<div class="flex flex-wrap items-center justify-center gap-3">
				<button
					v-for="n in teamCapable ? [2, 3, 4] : []"
					:key="n"
					class="ctl"
					@click="balanceTeams(n)"
				>
					{{ n }} teams
				</button>
				<button class="ctl" @click="toggleMute">
					{{ muted ? "Sound off" : "Sound on" }}
				</button>
				<ThemeButton class="ctl" />
				<button class="ctl" @click="end">Exit</button>
				<button
					class="ctl ctl-go"
					:disabled="starting || !participants.length"
					@click="startGame"
				>
					{{ starting ? "Starting…" : `Start · ${participants.length} players` }}
				</button>
			</div>
			<p v-if="error" class="text-center text-alert">{{ error }}</p>
		</div>

		<!-- Live console -->
		<div
			v-else
			class="flex min-h-0 flex-1 flex-col items-center justify-center gap-8 p-6 text-center sm:p-10"
		>
			<component
				:is="live.HostLive"
				v-if="gamePhases.includes(view.phase)"
				:view="view"
				:remaining="remaining"
				:timer-percent="timerPercent"
				:total-turns="totalTurns"
				:mode="mode"
				:solved-count="solvedCount"
				@reassign="reassignPerformer"
				@compose="composer = true"
			/>

			<template v-else-if="view.phase === 'scoreboard'">
				<h2 class="font-display text-3xl font-extrabold text-paper">
					Scoreboard
					<span
						v-if="view.last_voided"
						class="ml-3 font-mono text-sm font-normal uppercase tracking-widest text-alert"
					>
						last prompt voided
					</span>
				</h2>
				<ol class="flex w-full max-w-xl flex-col gap-3">
					<li
						v-for="team in rankedTeams(view.teams || [])"
						:key="team.name"
						class="flex items-center gap-4 rounded-2xl border bg-dusk px-5 py-4"
						:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-6 font-mono text-lg tabular-nums text-paper/40">{{
							team.rank
						}}</span>
						<AvatarPic
							v-if="team.avatar"
							:id="team.avatar"
							:nickname="team.team_name"
							:size="36"
						/>
						<span class="flex-1 text-left font-display text-xl font-bold text-paper">{{
							team.team_name
						}}</span>
						<span
							class="font-display text-2xl font-extrabold tabular-nums text-accent"
							>{{ team.score }}</span
						>
					</li>
				</ol>
			</template>

			<template v-else-if="podium">
				<h1 class="font-display text-5xl font-extrabold text-paper sm:text-6xl">
					Final results
				</h1>
				<ol class="flex w-full max-w-xl flex-col gap-3">
					<li
						v-for="team in podium"
						:key="team.name"
						class="flex items-center gap-4 rounded-2xl border bg-dusk px-5 py-4"
						:class="team.rank === 1 ? 'border-accent' : 'border-haze'"
					>
						<span class="w-6 font-mono text-lg tabular-nums text-paper/40">{{
							team.rank
						}}</span>
						<AvatarPic
							v-if="team.avatar"
							:id="team.avatar"
							:nickname="team.team_name"
							:size="36"
						/>
						<span class="flex-1 text-left font-display text-xl font-bold text-paper">{{
							team.team_name
						}}</span>
						<span
							class="font-display text-2xl font-extrabold tabular-nums text-accent"
							>{{ team.score }}</span
						>
					</li>
				</ol>
				<div class="mt-2 flex flex-wrap justify-center gap-2">
					<button class="ctl ctl-go" @click="newRoom">New room</button>
					<RouterLink class="ctl" :to="{ name: 'HostDashboard' }">Dashboard</RouterLink>
					<RouterLink class="ctl" :to="{ name: 'Catalog' }">All games</RouterLink>
				</div>
			</template>

			<template v-else>
				<p class="font-mono uppercase tracking-[0.28em] text-paper/40">Get ready…</p>
			</template>

			<div
				v-if="!podium && phase !== 'lobby'"
				class="flex flex-wrap items-center justify-center gap-3"
			>
				<button v-if="view.phase !== 'scoreboard'" class="ctl" @click="skipTurn">
					Skip stage
				</button>
				<button class="ctl" :disabled="!canPrevious" @click="previousPresentation">Previous</button>
				<button class="ctl ctl-go" @click="nextPresentation">Next</button>
				<button class="ctl" @click="togglePause">
					{{ paused ? "Resume" : "Pause" }}
				</button>
				<button
					v-if="gameKey === 'cuecast' && view.phase === 'turn_open'"
					class="ctl"
					@click="reassignPerformer"
				>
					Reassign performer
				</button>
				<button
					v-if="
						gameKey === 'crowd-compass' &&
						['reveal', 'scoreboard'].includes(view.phase) &&
						!view.last_voided
					"
					class="ctl ctl-danger"
					@click="voidPrompt"
				>
					Void prompt
				</button>
				<button
					v-if="gameKey === 'crowd-compass'"
					class="ctl ctl-go"
					@click="composer = true"
				>
					+ Live prompt
				</button>
				<button class="ctl ctl-danger" @click="end">End game</button>
				<p v-if="error" class="text-alert">{{ error }}</p>
			</div>
		</div>

		<!-- Live prompt composer -->
		<PackPreviewDrawer
			:pack="previewPack"
			@close="previewPack = null"
			@choose="choosePreviewedPack"
		/>

		<dialog
			ref="composerDialog"
			class="qz-dialog w-[min(92vw,560px)] rounded-3xl border border-haze bg-night p-8"
			@cancel.prevent="composer = false"
			@click.self="composer = false"
		>
			<h2 class="font-display text-2xl font-extrabold text-paper">Compose a live prompt</h2>
			<div class="mt-5 flex flex-col gap-4">
				<label class="flex flex-col gap-2">
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45"
						>Prompt</span
					>
					<input
						v-model="draft.prompt"
						class="field"
						placeholder="Ask the room anything…"
						maxlength="140"
					/>
				</label>
				<div class="grid grid-cols-2 gap-3">
					<input
						v-model="draft.choice_1"
						class="field"
						placeholder="Choice 1 *"
						maxlength="60"
					/>
					<input
						v-model="draft.choice_2"
						class="field"
						placeholder="Choice 2 *"
						maxlength="60"
					/>
					<input
						v-model="draft.choice_3"
						class="field"
						placeholder="Choice 3"
						maxlength="60"
					/>
					<input
						v-model="draft.choice_4"
						class="field"
						placeholder="Choice 4"
						maxlength="60"
					/>
				</div>
				<p class="text-sm text-paper/50">
					It joins the queue after the current prompt. Blank rooms start with these.
				</p>
				<p v-if="error" class="text-alert">{{ error }}</p>
				<div class="mt-2 flex justify-end gap-3">
					<button class="ctl" @click="composer = false">Cancel</button>
					<button class="ctl ctl-go" :disabled="pushing" @click="pushPrompt">
						{{ pushing ? "Pushing…" : "Push to the room" }}
					</button>
				</div>
			</div>
		</dialog>

		<dialog
			ref="qrDialog"
			class="qz-dialog border-0 bg-transparent p-0"
			@cancel.prevent="qrFullscreen = false"
			@click="qrFullscreen = false"
		>
			<img
				v-if="qrDataUrl"
				:src="qrDataUrl"
				alt="Join QR code"
				class="size-[min(78vh,88vw)] rounded-3xl bg-card p-4"
			/>
			<p class="mt-4 text-center font-mono text-2xl tracking-[0.08em] text-paper">
				{{ pin }}
			</p>
		</dialog>
	</div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import QRCode from "qrcode";
import { call, readError } from "@/api";
import { confirm } from "@/confirm";
import { useCountdown, useSessionRoom } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";
import DrainRing from "@/components/DrainRing.vue";
import HostBar from "@/components/HostBar.vue";
import ThemeButton from "@/components/ThemeButton.vue";
import PackPicker from "@/platform/discovery/PackPicker.vue";
import PackPreviewDrawer from "@/platform/discovery/PackPreviewDrawer.vue";
import PremiumToggle from "@/platform/discovery/PremiumToggle.vue";
import { initSound, muted, playCue, toggleMute } from "@/sound";
import {
	forgetHostedSession,
	gpCall,
	loadHostedSession,
	rememberHostedSession,
	teamStyle,
	TEAM_STYLE,
} from "@/platform/session/gp";
import { GAME_SETUP, liveFor, phasesFor } from "@/games/registry";

const socket = inject("$socket");
const route = useRoute();
const router = useRouter();
const {
	remaining,
	total: windowSeconds,
	start: startCountdown,
	stop: stopCountdown,
} = useCountdown();

const loading = ref(true);
const setupGame = ref(null);
const session = ref(null);
const gameKey = ref("cuecast");
const pin = ref("");
const configuration = ref({});
const phase = ref("lobby");
const participants = ref([]);
const teams = ref([]);
const packs = ref([]);
const previewPack = ref(null);
const lobbyLocked = ref(false);
const view = ref({});
const podium = ref(null);
const starting = ref(false);
const creating = ref(false);
const qrDataUrl = ref("");
const qrFullscreen = ref(false);
const qrDialog = ref(null);
const composer = ref(false);
const composerDialog = ref(null);
const pushing = ref(false);
const draft = ref({ prompt: "", choice_1: "", choice_2: "", choice_3: "", choice_4: "" });
const error = ref("");
let stopRoom = null;
let seqSeen = -1;

watch(composer, (open) =>
	open ? composerDialog.value?.showModal() : composerDialog.value?.close()
);

const setup = ref({
	deck: "",
	pack: "",
	seconds: 60,
	vote_seconds: 15,
	prediction_seconds: 15,
	teams_count: 2,
	sudden_death: true,
	estimation: true,
	room_match: true,
	team_match: true,
	scoring_mode: "Individual",
	rounds: 0,
	quorum: 1,
	auto_progress: true,
});

const teamColors = Object.keys(TEAM_STYLE);

const hostableGames = [
	{
		key: "cuecast",
		title: "CueCast",
		summary: "Act it or describe it: race through team prompts before the buzzer.",
	},
	{
		key: "crowd-compass",
		title: "Crowd Compass",
		summary: "Vote for yourself, predict the room, and see who reads the crowd best.",
	},
];

const inLiveSession = computed(() => Boolean(session.value));
const copied = ref(false);
const setupTitle = computed(
	() => hostableGames.find((g) => g.key === setupGame.value)?.title || ""
);
const live = computed(() => liveFor(gameKey.value));
const gamePhases = computed(() => phasesFor(gameKey.value));
const mode = computed(() => configuration.value.mode || "Act");
const totalTurns = computed(() => {
	const t = teams.value.length || configuration.value.teams_count || 2;
	return t * (configuration.value.turns_per_team || 1);
});
const solvedCount = computed(() => view.value.solved ?? 0);
const timerPercent = computed(() =>
	windowSeconds.value ? (remaining.value / windowSeconds.value) * 100 : 0
);
const teamCols = computed(() => {
	const count = Math.max(1, teams.value.length);
	return count >= 4 ? "sm:grid-cols-4" : count === 3 ? "sm:grid-cols-3" : "sm:grid-cols-2";
});
const teamCapable = computed(
	() =>
		gameKey.value === "cuecast" ||
		(gameKey.value === "crowd-compass" && configuration.value.scoring_mode === "Team average")
);
const selectedPackRanked = computed(() =>
	Boolean(packs.value.find((p) => p.name === setup.value.pack)?.ranked)
);
const unassigned = computed(() => participants.value.filter((p) => !p.team));
const paused = computed(() => Boolean(view.value.paused));
const canPrevious = computed(() => Boolean(view.value.can_previous));

function teamMembers(teamName) {
	return participants.value.filter((p) => p.team === teamName);
}

function rankedTeams(list) {
	return [...list].sort((a, b) => (a.rank || 0) - (b.rank || 0) || b.score - a.score);
}

function onEvent(envelopeMessage) {
	if (!envelopeMessage || typeof envelopeMessage !== "object") return;
	if (typeof envelopeMessage.seq === "number") {
		if (envelopeMessage.seq < seqSeen) return;
		seqSeen = envelopeMessage.seq;
	}
	const type = envelopeMessage.type;
	const payload = envelopeMessage.payload || envelopeMessage;
	if (type === "platform.lobby_updated") {
		participants.value = payload.participants || [];
		teams.value = (payload.teams || []).map((t) => ({ ...t, editName: t.team_name }));
		lobbyLocked.value = Boolean(payload.lobby_locked);
	} else if (
		type === "platform.state_changed" ||
		type.split(".")[0] === gameKey.value.replace("-", "_")
	) {
		if (payload.phase) {
			view.value = payload;
			podium.value = null;
			phase.value = payload.phase;
			playCue(
				payload.phase === "turn_open" || payload.phase === "prompt_open"
					? "submit"
					: "tick"
			);
			stopCountdown();
			if (["turn_ready", "prompt_open", "prediction_open"].includes(payload.phase))
				startCountdown(5);
		}
	} else if (type === "platform.action_progress") {
		if (payload.phase === "prompt_open") view.value = { ...view.value, voted: payload.count };
		else if (payload.phase === "prediction_open")
			view.value = { ...view.value, predicted: payload.count };
		else view.value = { ...view.value, solved: payload.count };
	} else if (type === "platform.scoreboard_updated") {
		view.value = {
			...view.value,
			phase: "scoreboard",
			teams: payload.teams,
			last_voided: payload.last_voided,
		};
		phase.value = "scoreboard";
		stopCountdown();
	} else if (type === "crowd_compass.prompt_queued") {
		composer.value = false;
		draft.value = { prompt: "", choice_1: "", choice_2: "", choice_3: "", choice_4: "" };
	}
}

async function refresh() {
	try {
		await applyState(
			await gpCall("get_host_state", session.value ? { session: session.value } : {})
		);
	} catch (e) {
		error.value = readError(e);
	}
}

async function applyState(state) {
	if (!state.session) {
		session.value = null;
		forgetHostedSession();
		return;
	}
	session.value = state.session;
	gameKey.value = state.game_key || "cuecast";
	pin.value = state.game_pin;
	configuration.value = state.configuration || {};
	participants.value = state.participants || [];
	teams.value = (state.teams || []).map((t) => ({
		...t,
		editName: teams.value.find((old) => old.name === t.name)?.editName || t.team_name,
	}));
	lobbyLocked.value = Boolean(state.lobby_locked);
	qrDataUrl.value = await renderQr(joinUrl());
	rememberHostedSession(state.session);

	if (state.status === "Ended" || state.podium) {
		podium.value = state.podium || [];
		phase.value = "podium";
		stopCountdown();
		return;
	}
	if (state.status !== "Active") {
		phase.value = "lobby";
		return;
	}
	podium.value = null;
	phase.value = state.phase || "lobby";
	view.value = state.view || {};
	seqSeen = state.state_version ?? seqSeen;

	if (["turn_ready", "turn_open", "prompt_open", "prediction_open"].includes(state.phase)) {
		startCountdown(Math.max(0.5, state.remaining_seconds));
	} else {
		stopCountdown();
	}
}

function joinUrl() {
	return `${window.location.origin}/play/join?pin=${pin.value}`;
}

async function copyJoinUrl() {
	try {
		await navigator.clipboard.writeText(joinUrl());
		copied.value = true;
		setTimeout(() => (copied.value = false), 1500);
	} catch {
		error.value = `Copy failed. The link is ${joinUrl()}`;
	}
}

async function renderQr(url) {
	const canvas = document.createElement("canvas");
	await QRCode.toCanvas(canvas, url, {
		margin: 1,
		width: 800,
		errorCorrectionLevel: "H",
		color: { dark: "#16111F", light: "#F4F0FA" },
	});
	return canvas.toDataURL();
}

async function loadPacks(game) {
	const meta = GAME_SETUP[game];
	if (!meta) return;
	try {
		const rows = await call("frappe.client.get_list", {
			doctype: meta.contentDoctype,
			fields: [
				"name",
				"title",
				"is_demo",
				"demo_key",
				game === "crowd-compass" ? "ranked" : "mode",
			],
			limit_page_length: 0,
			order_by: "is_demo desc, title asc",
		});
		for (const row of rows) {
			const promptFields =
				game === "crowd-compass"
					? ["prompt_text", "choice_1", "choice_2", "choice_3", "choice_4"]
					: ["prompt_text"];
			const prompts = await call("frappe.client.get_list", {
				doctype: meta.promptDoctype,
				filters: { parenttype: meta.contentDoctype, parent: row.name },
				fields: promptFields,
				limit_page_length: 0,
				order_by: "idx asc",
			});
			row.prompt_count = prompts.length;
			row.prompts = prompts.map((prompt) => ({
				text: prompt.prompt_text,
				choices: [
					prompt.choice_1,
					prompt.choice_2,
					prompt.choice_3,
					prompt.choice_4,
				].filter(Boolean),
			}));
		}
		packs.value = rows;
	} catch (e) {
		error.value = readError(e);
	}
}

function choosePreviewedPack(pack) {
	if (setupGame.value === "crowd-compass") setup.value.pack = pack.name;
	else setup.value.deck = pack.name;
	previewPack.value = null;
}

onMounted(async () => {
	initSound("host");
	try {
		const remembered = loadHostedSession();
		let state = null;
		if (remembered) {
			state = await gpCall("get_host_state", { session: remembered }).catch(() => null);
			if (!state || !state.session) forgetHostedSession();
		}
		if (!state) state = await gpCall("get_host_state").catch(() => ({}));
		if (state.session) {
			await applyState(state);
			stopRoom = useSessionRoom(socket, pin.value, onEvent, refresh, "gp");
		} else if (route.query.session) {
			const created = await gpCall("get_host_state", { session: route.query.session });
			if (created.session) {
				await applyState(created);
				stopRoom = useSessionRoom(socket, pin.value, onEvent, refresh, "gp");
			}
		} else {
			await loadPacks("cuecast");
		}
		loading.value = false;
	} catch (e) {
		loading.value = false;
		error.value = readError(e);
	}
});

watch(setupGame, (game) => {
	if (game) loadPacks(game);
});

async function hostAction(method, params = {}) {
	error.value = "";
	try {
		return await gpCall(method, { session: session.value, ...params });
	} catch (e) {
		error.value = readError(e);
		await refresh().catch(() => {});
	}
}

async function createSession() {
	error.value = "";
	creating.value = true;
	try {
		const configuration = { ...setup.value };
		delete configuration.deck;
		if (setupGame.value === "cuecast") {
			configuration.deck = setup.value.deck;
			delete configuration.pack;
		} else {
			configuration.pack = setup.value.pack || null;
			delete configuration.deck;
			delete configuration.seconds;
			delete configuration.sudden_death;
			if (configuration.scoring_mode !== "Team average") configuration.teams_count = 2;
		}
		const created = await gpCall("create_session", {
			game_key: setupGame.value,
			configuration,
		});
		await applyState(await gpCall("get_host_state", { session: created.session }));
		stopRoom?.();
		stopRoom = useSessionRoom(socket, pin.value, onEvent, refresh, "gp");
	} catch (e) {
		error.value = readError(e);
	} finally {
		creating.value = false;
	}
}

async function startGame() {
	starting.value = true;
	if (await hostAction("start_session")) {
		await refresh();
	} else {
		starting.value = false;
	}
}

async function toggleLock() {
	const lobby = await hostAction(lobbyLocked.value ? "unlock_lobby" : "lock_lobby");
	if (lobby) lobbyLocked.value = Boolean(lobby.lobby_locked);
}

async function balanceTeams(count) {
	await hostAction("host_command", { command: "balance_teams", payload: { count } });
}

async function renameTeam(team) {
	await hostAction("host_command", {
		command: "rename_team",
		payload: { team: team.name, team_name: team.editName },
	});
}

async function recolorTeam(team, color) {
	await hostAction("host_command", {
		command: "recolor_team",
		payload: { team: team.name, color },
	});
}

async function kick(participant) {
	const ok = await confirm(`Remove ${participant.nickname} from the room?`, {
		action: "Remove",
		danger: true,
	});
	if (!ok) return;
	await hostAction("kick_participant", { participant: participant.name });
}

async function skipTurn() {
	await hostAction("host_command", { command: "skip_turn" });
}

async function previousPresentation() {
	await hostAction("host_command", { command: "previous" });
	await refresh();
}

async function nextPresentation() {
	await hostAction("host_command", { command: "next" });
	await refresh();
}

async function togglePause() {
	await hostAction("host_command", { command: paused.value ? "resume" : "pause" });
	await refresh();
}

async function reassignPerformer() {
	const stageTeam = (view.value.teams || []).find(
		(t) => t.team_name === view.value.actor_team_name
	);
	const roster = participants.value.filter(
		(p) =>
			stageTeam && p.team === stageTeam.name && p.nickname !== view.value.performer?.nickname
	);
	if (!roster.length) return;
	await hostAction("host_command", {
		command: "reassign_performer",
		payload: { participant: roster[roster.length - 1].name },
	});
}

async function voidPrompt() {
	const ok = await confirm(
		"Void the last prompt? Its points are returned and it counts for nothing.",
		{ action: "Void it", danger: true }
	);
	if (!ok) return;
	await hostAction("host_command", { command: "void_prompt" });
}

async function pushPrompt() {
	error.value = "";
	pushing.value = true;
	try {
		await hostAction("host_command", { command: "push_prompt", payload: { ...draft.value } });
	} finally {
		pushing.value = false;
	}
}

async function end() {
	const prompt = phase.value === "lobby" ? "Close this lobby?" : "End the game for everyone?";
	const ok = await confirm(prompt, {
		action: phase.value === "lobby" ? "Close lobby" : "End game",
		danger: true,
	});
	if (!ok) return;
	await hostAction("end_session");
	if (phase.value === "lobby") newRoom();
	else await refresh();
}

function newRoom() {
	forgetHostedSession();
	window.location.href = "/play/host";
}
</script>
