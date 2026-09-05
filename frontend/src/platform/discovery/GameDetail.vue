<template>
	<div class="gather-ui gp-page">
		<HostBar />
		<main class="gp-container">
			<RouterLink class="gp-breadcrumb" :to="{ name: 'Catalog' }">
				{{ $t("← Explore games") }}
			</RouterLink>
			<div v-if="loading" role="status" class="gp-state">
				{{ $t("Getting the game ready…") }}
			</div>
			<div v-else-if="!game" class="gp-state">
				<h1>{{ $t("We couldn’t find that game.") }}</h1>
				<p>{{ $t(error || "Choose another game from the collection.") }}</p>
				<RouterLink class="gp-button" :to="{ name: 'Catalog' }">
					{{ $t("Explore games") }}
				</RouterLink>
			</div>
			<template v-else>
				<header class="gp-detail-header">
					<div>
						<p class="gp-eyebrow">
							{{ $t(profile.category) }} ·
							{{ $t(profile.kicker || "A new way to play together") }}
						</p>
						<h1>{{ $t(game.title) }}</h1>
						<p>{{ $t(profile.description) }}</p>
						<div class="gp-detail-tags">
							<span>{{ $t(profile.people) }}</span
							><span> {{ $t("About") }} {{ $t(profile.time) }}</span
							><span>{{ $t(profile.deviceLabel) }}</span>
						</div>
					</div>
				</header>
				<div class="gp-detail-grid">
					<section class="gp-example" :aria-label="$t('Try an example round')">
						<a
							v-if="coverImage"
							class="gp-game-illustration"
							:href="coverImage"
							target="_blank"
							rel="noopener"
							:aria-label="`Open the ${game.title} illustration at full size (new tab)`"
						>
							<img
								:src="coverImage"
								:alt="coverAlt"
								:width="roomGame ? 1536 : 1672"
								:height="roomGame ? 1024 : 941"
								fetchpriority="high"
							/>
							<span>
								{{ $t("Open illustration") }}
								<span aria-hidden="true">↗</span></span
							>
						</a>
						<GameArtwork v-else :game-key="game.key" :color="profile.color" />
						<div class="gp-example-content">
							<p class="gp-eyebrow">
								{{
									$t(
										exampleStep
											? "Here’s what happens next"
											: "Try a little round",
									)
								}}
								{{ $t("· Example only") }}
							</p>
							<h2>{{ $t(profile.sample || game.summary) }}</h2>
							<template v-if="game.key === 'crowd-compass'">
								<p class="gp-caption">
									{{
										$t(
											exampleStep
												? "Now predict the group’s favourite. These are sample results, not a live vote."
												: "First, pick the answer that sounds like you.",
										)
									}}
								</p>
								<div class="gp-example-choices">
									<button
										v-for="(choice, index) in ['A · Outside', 'B · Inside']"
										:key="choice"
										:aria-pressed="sampleChoice === index"
										@click="chooseExample(index)"
									>
										{{ choice }}
									</button>
								</div>
								<div
									v-if="exampleStep === 2"
									class="gp-example-result"
									role="status"
								>
									<strong>
										{{ $t("Outside: 6 votes · Inside: 4 votes") }} </strong
									><br />{{
										$t(
											samplePrediction === 0
												? "You read this sample room!"
												: "A surprise! Outside wins this sample room.",
										)
									}}
									{{ $t("In a real game, the reveal starts the conversation.") }}
								</div>
							</template>
							<template v-else-if="game.key === 'quiz'">
								<div class="gp-example-choices">
									<button
										v-for="(choice, index) in ['A · Venus', 'B · Mars']"
										:key="choice"
										:aria-pressed="sampleChoice === index"
										@click="
											sampleChoice = index;
											exampleStep = 1;
										"
									>
										{{ choice }}
									</button>
								</div>
								<div v-if="exampleStep" class="gp-example-result" role="status">
									<strong>{{
										$t(
											sampleChoice === 1
												? "That’s it!"
												: "Good try! It’s Mars.",
										)
									}}</strong>
									{{ $t("Iron-rich dust gives Mars its reddish colour.") }}
								</div>
							</template>
							<template v-else>
								<button
									class="gp-button gp-button-secondary"
									@click="exampleStep = exampleStep ? 0 : 1"
								>
									{{
										$t(
											exampleStep
												? "Try the prompt again"
												: "Show me how it feels",
										)
									}}
									<span aria-hidden="true">→</span>
								</button>
								<div v-if="exampleStep" class="gp-example-result" role="status">
									{{ exampleReveal }}
								</div>
							</template>
							<button
								v-if="exampleStep && ['crowd-compass', 'quiz'].includes(game.key)"
								class="gp-example-next"
								@click="resetExample"
							>
								{{ $t("Try again") }}
							</button>
							<p class="gp-caption">
								{{
									$t(
										"No account needed to explore. Your example answers aren’t saved.",
									)
								}}
							</p>
						</div>
					</section>
					<section class="gp-setup" aria-labelledby="setup-title">
						<p class="gp-eyebrow">{{ $t("Bring your people") }}</p>
						<h2 id="setup-title">{{ $t("Make it your game") }}</h2>
						<p>
							{{
								$t(
									roomGame
										? "One host device. Everyone else can put theirs away."
										: "Choose your content and how you’ll play. Your lobby opens before the game starts.",
								)
							}}
						</p>
						<GatherChoices
							v-model="participation"
							:label="$t('How will you play?')"
							:options="modes"
						/>
						<p class="gp-setup-note">
							{{
								$t(
									participation === "shared"
										? "Join once per team or household with a group nickname. Agree on one answer; each device gets one score."
										: roomGame
											? "Make small groups of 2–5. Read the prompt aloud, or open it on a shared screen. No one needs to join online."
											: "Players join with a code. Keep private prompts on the right person’s device. A shared screen is optional.",
								)
							}}
						</p>
						<GatherSelect
							v-model="selectedPack"
							:label="
								roomGame
									? 'Pick a conversation pack'
									: 'Choose a ready-to-play pack'
							"
							:options="
								packs.map((p) => ({
									value: p.name,
									label: p.title,
									description: p.prompt_count
										? $t('{count} prompts · ready to play', {
												count: p.prompt_count,
											})
										: 'Three conversations · no timer',
								}))
							"
							:disabled="!packs.length"
						/>
						<button
							v-if="selectedPack && !roomGame"
							class="gp-example-next"
							@click="preview = packs.find((p) => p.name === selectedPack)"
						>
							{{ $t("Preview the prompts →") }}
						</button>
						<template v-if="!roomGame && game.key !== 'quiz'">
							<GatherChoices
								v-model="seconds"
								:label="
									game.key === 'crowd-compass'
										? 'Time to vote and predict'
										: 'Round length'
								"
								compact
								:options="
									times.map((n) => ({
										value: n,
										label: $t('{count} sec', { count: n }),
									}))
								"
							/>
							<GatherChoices
								v-if="game.key === 'crowd-compass'"
								v-model="journey"
								:label="$t('Round journey')"
								:options="[
									{
										value: true,
										label: 'Build to a finale',
										description:
											'+500 per correct prediction. +1,000 in the final round of 3+ pack rounds.',
									},
									{
										value: false,
										label: 'Classic scoring',
										description: '+500 per correct prediction throughout.',
									},
								]"
							/>
							<GatherChoices
								v-if="game.key === 'crowd-compass'"
								v-model="pace"
								:label="$t('Between rounds')"
								:options="[
									{
										value: 'manual',
										label: 'Room to talk',
										description: 'You decide when to move on',
									},
									{
										value: 'auto',
										label: 'Keep it moving',
										description: 'Rounds advance automatically',
									},
								]"
							/>
						</template>
						<p v-if="error" role="alert" class="gp-error">
							{{ $t(error) }}
							<RouterLink to="/access"> {{ $t("Your access →") }} </RouterLink>
						</p>
						<button
							class="gp-button"
							:disabled="creating || !selectedPack"
							@click="host"
						>
							{{
								$t(
									creating
										? "Opening your room…"
										: guest
											? site.allow_guest_host
												? "Try hosting a game"
												: "Sign in to host"
											: roomGame
												? "Set up our room"
												: "Open the lobby",
								)
							}}
							<span aria-hidden="true">→</span>
						</button>
						<p class="gp-setup-note">
							{{
								$t(
									roomGame
										? "Three playful prompts. No countdown. Passing is welcome."
										: "Your site’s allowance applies. Visit Your access to see what’s included.",
								)
							}}
						</p>
						<RouterLink
							v-if="!packs.length && game.key === 'quiz'"
							class="gp-example-next"
							:to="{ name: 'Quizzes' }"
						>
							{{ $t("Create your own quiz →") }}
						</RouterLink>
					</section>
				</div>
				<p v-if="locale === 'am' && coverImage" class="gp-setup-note">
					{{ $t("Illustration in English. Follow the Amharic steps below.") }}
				</p>
				<section class="gp-steps">
					<h2>{{ $t("How to play") }}</h2>
					<ol>
						<li v-for="(step, i) in steps" :key="step">
							<span>{{ i + 1 }}</span
							>{{ $t(step) }}
						</li>
					</ol>
				</section>
				<div class="gp-disclosures">
					<details>
						<summary>{{ $t("Make room for everyone") }}</summary>
						<p>{{ $t(profile.access) }}</p>
						<p v-if="roomGame">
							{{
								$t(
									"In a large gathering, let everyone talk in parallel groups. Invite two or three groups to share instead of asking every person. New arrivals can join any conversation; people can step away at any time.",
								)
							}}
						</p>
					</details>
					<details v-if="!roomGame">
						<summary>{{ $t("Scoring and facilitation") }}</summary>
						<p>{{ $t(guide.scoring) }}</p>
						<p>{{ $t(guide.hostDoes) }}</p>
					</details>
					<details v-if="!roomGame">
						<summary>{{ $t("Full visual guide and room setup") }}</summary>
						<p>{{ $t(guide.setup) }}</p>
						<GameVisualGuide v-if="visual" :game-title="game.title" :visual="visual" />
					</details>
					<details v-if="guideVideo">
						<summary>{{ $t("Watch a real round") }}</summary>
						<video
							controls
							preload="none"
							:poster="guideVideo.poster"
							style="width: 100%; max-width: 900px; margin-top: 16px"
							:src="guideVideo.video"
						>
							{{ $t("Use the full visual guide above to follow each step.") }}
						</video>
					</details>
					<details v-if="roomGame">
						<summary>{{ $t("Connection and privacy") }}</summary>
						<p>
							{{
								$t(
									"Internet is needed to open and advance the session. If the connection drops, keep talking about the visible prompt; reconnect before continuing. No attendee names or spoken answers are recorded. The public screen contains only prompts.",
								)
							}}
						</p>
					</details>
				</div>
			</template>
			<PackPreviewDrawer :pack="preview" @close="preview = null" @choose="choosePack" />
		</main>
	</div>
</template>
<script setup>
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import HostBar from "@/components/HostBar.vue";
import GameArtwork from "./GameArtwork.vue";
import GameVisualGuide from "./GameVisualGuide.vue";
import PackPreviewDrawer from "./PackPreviewDrawer.vue";
import { profileFor } from "./collection";
import { guideFor } from "./games";
import { visualFor } from "./gameVisuals";
import { gpCall, rememberHostedSession } from "@/platform/session/gp";
import { redirectGuestToLogin } from "@/auth";
import { site, refreshAccess } from "@/platform/site";
import GatherSelect from "@/components/GatherSelect.vue";
import GatherChoices from "@/components/GatherChoices.vue";
import { readError } from "@/api";
import { locale, languageUrl } from "@/i18n";
const journey = ref(true);
const route = useRoute(),
	router = useRouter(),
	game = ref(null),
	loading = ref(true),
	error = ref(""),
	packs = ref([]),
	selectedPack = ref(""),
	preview = ref(null),
	creating = ref(false),
	participation = ref("own"),
	seconds = ref(30),
	pace = ref("manual");
const exampleStep = ref(0),
	sampleChoice = ref(null),
	samplePrediction = ref(null);
const guest = !window.session_user || window.session_user === "Guest";
const roomGame = computed(() => game.value?.key === "common-ground");
const profile = computed(() => profileFor(game.value));
const guide = computed(() => (roomGame.value ? {} : guideFor(game.value?.key)));
const guideVideo = computed(() => guide.value.demos?.find((demo) => demo.video));
const visual = computed(() => visualFor(game.value?.key));
const coverImage = computed(() =>
	roomGame.value
		? "/assets/quizzly/images/games/common-ground/how-to-ethiopian-v2.png"
		: game.value?.key === "bluffline"
			? "/assets/quizzly/images/games/bluffline/how-to-ethiopian-v1.png"
			: visual.value?.hero,
);
const coverAlt = computed(() =>
	roomGame.value
		? "Six people of different generations talk in a circle, discovering a shared love of walks, food and music. Only the host needs a device."
		: visual.value?.summary || `${game.value?.title} illustrated guide`,
);
const steps = computed(() =>
	profile.value.steps.length ? profile.value.steps : guide.value.howTo || [],
);
const times = computed(() =>
	game.value?.key === "crowd-compass"
		? [10, 15, 20]
		: ["cuecast", "doodle-dash"].includes(game.value?.key)
			? [30, 60, 90]
			: [15, 30, 45, 60],
);
const modes = computed(() =>
	profile.value.devices.map((value) => ({
		value,
		label: {
			host: "Host device only · play in the room",
			own: "One device per player",
			shared: "One device per team or household",
		}[value],
	})),
);
const exampleReveal = computed(() =>
	locale.value === "am"
		? profile.value.steps.join(" ")
		: {
				"common-ground":
					"“We all like the smell of rain, a quiet walk, and making someone laugh.” Now ask: which answer surprised you?",
				cuecast:
					"One person takes slow, giant steps. A teammate shouts “walking on the moon!” Mark it correct, and try the next prompt.",
				"doodle-dash":
					"Two wobbly circles, a triangle, and handlebars. Someone guesses “bicycle!” The imperfect drawing is half the fun.",
				"sequence-sprint":
					"Talk through what has to happen first, then arrange seed, sprout, plant, flower. Each shared device submits one order.",
			}[game.value?.key] || game.value?.summary,
);
function resetExample() {
	exampleStep.value = 0;
	sampleChoice.value = null;
	samplePrediction.value = null;
}
function chooseExample(i) {
	if (!exampleStep.value) {
		sampleChoice.value = i;
		exampleStep.value = 1;
	} else {
		samplePrediction.value = i;
		exampleStep.value = 2;
	}
}
function choosePack(pack) {
	selectedPack.value = pack.name;
	preview.value = null;
}
let loadId = 0;
watch(
	() => [route.params.game, locale.value],
	async ([key]) => {
		const id = ++loadId;
		loading.value = true;
		error.value = "";
		game.value = null;
		packs.value = [];
		selectedPack.value = "";
		resetExample();
		try {
			const list = await gpCall("list_games");
			if (id !== loadId) return;
			game.value = list.find((g) => g.key === key && g.status === "Available");
			if (!game.value) return;
			participation.value = profile.value.devices[0];
			seconds.value = key === "crowd-compass" ? 20 : 60;
			const result =
				key === "common-ground"
					? [
							{ name: "everyday", title: "Little things, big connections" },
							{ name: "imagination", title: "A little imagination" },
						]
					: await gpCall("list_public_decks", { game_key: key, language: locale.value });
			if (id !== loadId) return;
			packs.value = result.sort(
				(a, b) =>
					Number((a.demo_key || "").includes("church")) -
					Number((b.demo_key || "").includes("church")),
			);
			selectedPack.value = packs.value[0]?.name || "";
		} catch (e) {
			if (id === loadId) error.value = readError(e);
		} finally {
			if (id === loadId) loading.value = false;
		}
	},
	{ immediate: true },
);
async function host() {
	if (guest && !site.allow_guest_host && redirectGuestToLogin()) return;
	creating.value = true;
	error.value = "";
	try {
		const access = await refreshAccess();
		if (access.hosts_remaining === 0) {
			router.push("/access");
			return;
		}
		if (game.value.key === "quiz") {
			window.location.href = languageUrl(
				`/play/quizzly/host?quiz=${encodeURIComponent(selectedPack.value)}`,
			);
			return;
		}
		const configuration = roomGame.value
			? { pack: selectedPack.value, language: locale.value }
			: {
					[guide.value.contentKey || "pack"]: selectedPack.value,
					seconds: seconds.value,
					teams_count: 2,
					auto_progress: pace.value === "auto" ? 1 : 0,
				};
		if (game.value.key === "crowd-compass")
			Object.assign(configuration, {
				vote_seconds: seconds.value,
				prediction_seconds: seconds.value,
				rounds: 5,
				gathering_arc: journey.value,
			});
		const created = await gpCall("create_session", {
			game_key: game.value.key,
			configuration,
		});
		rememberHostedSession(created.session);
		await router.push(
			roomGame.value
				? { name: "RoomHost", params: { session: created.session } }
				: {
						name: "GpHost",
						query: { session: created.session, participation: participation.value },
					},
		);
	} catch (e) {
		error.value = readError(e);
	} finally {
		creating.value = false;
	}
}
</script>
