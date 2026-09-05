<template>
	<div class="gather-ui gp-page">
		<HostBar />
		<main class="gp-container" id="main-content">
			<section class="gp-hero">
				<div class="gp-hero-copy">
					<p class="gp-eyebrow">
						<span class="gp-status-dot"></span> Made for being together
					</p>
					<h1>Good company.<br /><em>Great games.</em></h1>
					<p>
						Turn “what should we do?” into one more round.<br class="gp-desktop" />
						Games for your people, your place, your kind of fun.
					</p>
					<a class="gp-button" href="#games"
						>Find your next game <span aria-hidden="true">↓</span></a
					>
					<div class="gp-hero-foot">
						<span class="gp-faces" aria-hidden="true">● ● ●</span> Friends. Families.
						Classrooms. Everyone’s invited.
					</div>
				</div>
				<RouterLink
					class="gp-feature"
					:to="{ name: 'GameDetail', params: { game: 'common-ground' } }"
				>
					<span class="gp-feature-tag">NEW · NO PLAYER PHONES NEEDED</span>
					<GameArtwork game-key="common-ground" color="peach" />
					<div class="gp-feature-copy">
						<div>
							<p>Start with a little connection</p>
							<h2>Common Ground</h2>
							<span>8 minutes. A few surprises. A room closer together.</span>
						</div>
						<span class="gp-circle-arrow" aria-hidden="true">↗</span>
					</div>
				</RouterLink>
			</section>
			<section class="gp-finder" aria-label="Find games for your devices">
				<div>
					<p class="gp-eyebrow">Your room, your rules</p>
					<h2>What devices do you have?</h2>
				</div>
				<div class="gp-device-options">
					<button
						v-for="option in deviceOptions"
						:key="option.id"
						:aria-pressed="device === option.id"
						@click="device = option.id"
					>
						<span aria-hidden="true">{{ option.icon }}</span
						>{{ option.label }}
					</button>
				</div>
			</section>
			<section id="games" class="gp-collection">
				<div class="gp-section-head">
					<div>
						<p class="gp-eyebrow">Less choosing, more playing</p>
						<h2>Find the room’s next favourite</h2>
					</div>
					<label class="gp-search"
						><span aria-hidden="true">⌕</span
						><input
							v-model="query"
							type="search"
							aria-label="Search games"
							placeholder="Find a game…"
					/></label>
				</div>
				<div class="gp-category-row">
					<div class="gp-categories" aria-label="Game category">
						<button
							v-for="item in categories"
							:key="item"
							:aria-pressed="category === item"
							@click="category = item"
						>
							{{ item }}
						</button>
					</div>
					<span aria-live="polite">{{ filtered.length }} games</span>
				</div>
				<p v-if="loading" role="status" class="gp-state">Finding something fun…</p>
				<div v-else-if="error" class="gp-state" role="alert">
					<p>{{ error }}</p>
					<button class="gp-button" @click="load">Try again</button>
				</div>
				<div v-else-if="!filtered.length" class="gp-state">
					<h3>No games with that combination yet.</h3>
					<p>Try another category or device setup.</p>
					<button class="gp-button" @click="reset">Show all games</button>
				</div>
				<div v-else class="gp-game-grid">
					<RouterLink
						v-for="game in filtered"
						:key="game.key"
						class="gp-game-card"
						:to="{ name: 'GameDetail', params: { game: game.key } }"
					>
						<GameArtwork :game-key="game.key" :color="profileFor(game).color" />
						<div class="gp-card-copy">
							<div class="gp-card-top">
								<span>{{ profileFor(game).category }}</span
								><span>{{ profileFor(game).time }}</span>
							</div>
							<h3>{{ game.title }} <span aria-hidden="true">↗</span></h3>
							<p>{{ profileFor(game).description }}</p>
							<div class="gp-card-meta">{{ profileFor(game).deviceLabel }}</div>
						</div>
					</RouterLink>
				</div>
				<button
					v-if="!showAll && !loading && !error"
					class="gp-more"
					@click="showAll = true"
				>
					Explore all {{ games.length }} formats <span aria-hidden="true">→</span>
				</button>
				<p v-if="showAll" class="gp-caption">
					More formats include focused puzzle and question-based variants. Check each
					guide for its current rules.
				</p>
			</section>
			<section class="gp-room-note">
				<span class="gp-note-star" aria-hidden="true">✳</span>
				<div>
					<h2>The best part isn’t on the screen.</h2>
					<p>
						Make a little room for laughter, a new perspective, or a wonderfully wrong
						answer.
					</p>
				</div>
				<RouterLink :to="{ name: 'GameDetail', params: { game: 'common-ground' } }"
					>Try a game without player phones ↗</RouterLink
				>
			</section>
			<footer class="gp-footer">
				<strong>GatherPlay</strong><span>Good company is all you need to begin.</span
				><RouterLink to="/join">Have a code? Join in →</RouterLink>
			</footer>
		</main>
	</div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import HostBar from "@/components/HostBar.vue";
import GameArtwork from "./GameArtwork.vue";
import { catalogGames } from "./games";
import { categories, featuredKeys, matchesDevice, profileFor } from "./collection";
const games = ref([]),
	loading = ref(true),
	error = ref(""),
	query = ref(""),
	device = ref("any"),
	category = ref("All games"),
	showAll = ref(false);
const deviceOptions = [
	{ id: "any", label: "Any setup", icon: "✳" },
	{ id: "own", label: "Everyone has a phone", icon: "▯" },
	{ id: "shared", label: "We’ll share devices", icon: "▯▯" },
	{ id: "host", label: "Just the host", icon: "☀" },
];
const filtered = computed(() =>
	games.value
		.filter(
			(g) =>
				g.status === "Available" &&
				(showAll.value || query.value || featuredKeys.includes(g.key)),
		)
		.filter(
			(g) =>
				matchesDevice(g, device.value) &&
				(category.value === "All games" || profileFor(g).category === category.value) &&
				`${g.title} ${g.summary}`.toLowerCase().includes(query.value.trim().toLowerCase()),
		)
		.sort(
			(a, b) =>
				(featuredKeys.indexOf(a.key) < 0 ? 99 : featuredKeys.indexOf(a.key)) -
				(featuredKeys.indexOf(b.key) < 0 ? 99 : featuredKeys.indexOf(b.key)),
		),
);
function reset() {
	query.value = "";
	device.value = "any";
	category.value = "All games";
}
async function load() {
	loading.value = true;
	error.value = "";
	try {
		games.value = await catalogGames();
	} catch {
		error.value = "We couldn’t load the games. Check your connection and try again.";
	} finally {
		loading.value = false;
	}
}
onMounted(load);
</script>
