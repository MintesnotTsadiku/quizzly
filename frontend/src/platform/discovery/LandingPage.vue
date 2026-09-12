<template>
	<div class="gather-ui gp-page">
		<HostBar />
		<main>
			<section class="gp-landing-hero gp-container">
				<div>
					<p class="gp-eyebrow">
						<span class="gp-status-dot"></span>
						{{ $t("Less scrolling. More stories.") }}
					</p>
					<h1>{{ siteText("tagline") }}</h1>
					<p class="gp-lead">{{ siteText("intro") }}</p>
					<div class="gp-landing-actions">
						<RouterLink class="gp-button" to="/explore">
							{{ $t("Find your kind of fun ↗") }} </RouterLink
						><RouterLink class="gp-button gp-button-secondary" to="/join">
							{{ $t("I have a game code") }}
						</RouterLink>
					</div>
					<p class="gp-caption">
						{{ $t("Around a table. Across a classroom. All together.") }}
					</p>
					<div class="gp-landing-proof">
						<span
							>◉ <strong> {{ $t("Your people") }} </strong
							><small> {{ $t("Friends, families, teams") }} </small></span
						><span
							>✳ <strong> {{ $t("Your setup") }} </strong
							><small> {{ $t("Phones, a screen, or neither") }} </small></span
						><span
							>↻ <strong> {{ $t("One more round") }} </strong
							><small> {{ $t("Easy to start. Worth repeating.") }} </small></span
						>
					</div>
				</div>
				<div
					class="gp-landing-collage"
					:aria-label="$t('Games for conversation, imagination and connection')"
				>
					<div class="gp-orbit-caption">{{ $t("The people are the main event.") }}</div>
					<RouterLink
						v-if="published.includes('common-ground')"
						to="/games/common-ground"
						class="gp-collage-main"
						><GameArtwork game-key="common-ground" color="peach" /><strong>
							{{ $t("Common") }} <br />
							{{ $t("Ground") }} </strong
						><span> {{ $t("No player phones") }} </span></RouterLink
					><RouterLink
						v-if="published.includes('crowd-compass')"
						to="/games/crowd-compass"
						class="gp-collage-small"
						><GameArtwork game-key="crowd-compass" color="lilac" /><strong>
							{{ $t("Know your crowd?") }}
						</strong></RouterLink
					>
					<div class="gp-collage-sticker">
						{{ $t("Good") }} <br />
						{{ $t("company") }} <br />
						{{ $t("wins ✳") }}
					</div>
				</div>
			</section>
			<section class="gp-landing-strip">
				<span> {{ $t("FOR THE EVERYDAY GET-TOGETHER") }} </span
				><strong> {{ $t("Kitchen tables") }} </strong><span>✳</span
				><strong> {{ $t("Classrooms") }} </strong><span>✳</span
				><strong> {{ $t("Team days") }} </strong><span>✳</span
				><strong> {{ $t("Big rooms") }} </strong>
			</section>
			<section class="gp-container gp-landing-section">
				<div class="gp-section-head">
					<div>
						<p class="gp-eyebrow">{{ $t("Meet your next shared memory") }}</p>
						<h2>
							{{ $t("Different ways to play.") }} <br />
							{{ $t("The same reason to gather.") }}
						</h2>
					</div>
					<RouterLink to="/explore"> {{ $t("Explore the collection →") }} </RouterLink>
				</div>
				<div class="gp-landing-games">
					<RouterLink v-for="g in picks" :key="g.key" :to="'/games/' + g.key"
						><GameArtwork :game-key="g.key" :color="g.color" />
						<p class="gp-eyebrow">{{ $t(g.type) }}</p>
						<h3>{{ $t(g.title) }} ↗</h3>
						<p>{{ $t(g.copy) }}</p></RouterLink
					>
				</div>
			</section>
			<section class="gp-landing-how gp-container">
				<div>
					<p class="gp-eyebrow">{{ $t("No long rulebook required") }}</p>
					<h2>
						{{ $t("From “what now?”") }} <br />
						{{ $t("to “again!”") }}
					</h2>
					<p>
						{{
							$t(
								"See a sample round before you start. Choose a pack. Give everyone a way to join in."
							)
						}}
					</p>
					<RouterLink
						class="gp-button"
						v-if="published.includes('common-ground')"
						to="/games/common-ground"
					>
						{{ $t("Try a little connection →") }}
					</RouterLink>
				</div>
				<ol>
					<li>
						<span>01</span>
						<div>
							<h3>{{ $t("Find a fit for your room.") }}</h3>
							<p>
								{{
									$t(
										"Choose by mood and devices. A room full of people needs more than one way to play."
									)
								}}
							</p>
						</div>
					</li>
					<li>
						<span>02</span>
						<div>
							<h3>{{ $t("Make it easy to belong.") }}</h3>
							<p>
								{{
									$t(
										"Join by code, share a device, or put the phones away. Each game tells you what works."
									)
								}}
							</p>
						</div>
					</li>
					<li>
						<span>03</span>
						<div>
							<h3>{{ $t("Leave room for the good part.") }}</h3>
							<p>
								{{
									$t(
										"The conversation after a reveal. The terrible drawing. The unexpected thing you share."
									)
								}}
							</p>
						</div>
					</li>
				</ol>
			</section>
			<section class="gp-container gp-landing-create">
				<div>
					<p class="gp-eyebrow">{{ $t("Made by you. Played by your people.") }}</p>
					<h2>
						{{ $t("Your inside jokes.") }} <br />
						{{ $t("Your big questions.") }} <br />
						{{ $t("Your next game.") }}
					</h2>
					<p>
						{{
							$t(
								"Create a private question pack in minutes, then host it for your group."
							)
						}}
					</p>
					<RouterLink class="gp-button" to="/create">
						{{ $t("Make something together ↗") }}
					</RouterLink>
				</div>
				<div class="gp-paper-question">
					<span> {{ $t("CROWD COMPASS · YOUR EDITION") }} </span>
					<h3>
						{{ $t("A free afternoon together.") }} <br />
						{{ $t("What are we choosing?") }}
					</h3>
					<p>{{ $t("☀ An adventure outside") }}</p>
					<p>{{ $t("⌂ Something cosy inside") }}</p>
					<small> {{ $t("Choose for yourself. Predict your people.") }} </small>
				</div>
			</section>
			<section class="gp-container gp-landing-faq">
				<h2>{{ $t("A few things, before you gather.") }}</h2>
				<details>
					<summary>{{ $t("Does everyone need a phone?") }}</summary>
					<p>
						{{
							$t(
								"No. Filter the collection for shared devices or just the host’s device. Common Ground works through conversation, with an optional big screen."
							)
						}}
					</p>
				</details>
				<details>
					<summary>{{ $t("Can I try hosting without an account?") }}</summary>
					<p>
						{{
							$t(
								site.allow_guest_host
									? `Yes. This site offers ${site.guest_host_limit} guest-hosted games and ${site.guest_pack_limit} private packs. Sign in in the same browser to keep your work.`
									: "This site asks hosts to sign in first."
							)
						}}
					</p>
				</details>
				<details>
					<summary>{{ $t("Is it free?") }}</summary>
					<p>
						{{
							$t(
								site.access_mode === "Community"
									? "This is a free community site. Your access page explains the hosting allowance."
									: "You can start with the available trial. Your access page shows the local plan, price and receipt process."
							)
						}}
					</p>
					<RouterLink to="/access"> {{ $t("See your access →") }} </RouterLink>
				</details>
				<details>
					<summary>{{ $t("Can I install it on my phone?") }}</summary>
					<p>
						{{
							$t(
								"Yes, on a supported browser. Look for the install suggestion or use Add to Home Screen. Live play needs internet access."
							)
						}}
					</p>
				</details>
			</section>
		</main>
		<footer class="gp-landing-footer">
			<strong>✳ {{ site.product_name }}</strong
			><span> {{ $t("A little play goes a long way.") }} </span
			><RouterLink to="/explore"> {{ $t("Let’s gather →") }} </RouterLink>
		</footer>
	</div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import { listGames } from "@/platform/session/gp";
const published = ref([]);
onMounted(async () => {
	try {
		published.value = (await listGames()).map((g) => g.key);
	} catch {
		published.value = [];
	}
});
const picks = computed(() => PICK_CARDS.filter((g) => published.value.includes(g.key)));
import HostBar from "@/components/HostBar.vue";
import GameArtwork from "./GameArtwork.vue";
import { site, siteText } from "@/platform/site";
const PICK_CARDS = [
	{
		key: "common-ground",
		color: "peach",
		title: "Common Ground",
		type: "Connect · Host device only",
		copy: "Discover the little things you share. No points, no pressure.",
	},
	{
		key: "cuecast",
		color: "lime",
		title: "CueCast",
		type: "Perform · Teams",
		copy: "Big gestures. Wild guesses. Brilliantly bad impressions.",
	},
	{
		key: "doodle-dash",
		color: "rose",
		title: "Doodle Dash",
		type: "Create · Player phones",
		copy: "One brave artist. A room full of wonderfully wrong answers.",
	},
];
</script>
