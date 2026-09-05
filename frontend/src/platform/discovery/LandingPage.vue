<template>
	<div class="gather-ui gp-page">
		<HostBar />
		<main>
			<section class="gp-landing-hero gp-container">
				<div>
					<p class="gp-eyebrow">
						<span class="gp-status-dot"></span> Less scrolling. More stories.
					</p>
					<h1>{{ site.tagline }}</h1>
					<p class="gp-lead">{{ site.intro }}</p>
					<div class="gp-landing-actions">
						<RouterLink class="gp-button" to="/explore"
							>Find your kind of fun ↗</RouterLink
						><RouterLink class="gp-button gp-button-secondary" to="/join"
							>I have a game code</RouterLink
						>
					</div>
					<p class="gp-caption">Around a table. Across a classroom. All together.</p>
					<div class="gp-landing-proof">
						<span
							>◉ <strong>Your people</strong
							><small>Friends, families, teams</small></span
						><span
							>✳ <strong>Your setup</strong
							><small>Phones, a screen, or neither</small></span
						><span
							>↻ <strong>One more round</strong
							><small>Easy to start. Worth repeating.</small></span
						>
					</div>
				</div>
				<div
					class="gp-landing-collage"
					aria-label="Games for conversation, imagination and connection"
				>
					<div class="gp-orbit-caption">The people are the main event.</div>
					<RouterLink to="/games/common-ground" class="gp-collage-main"
						><GameArtwork game-key="common-ground" color="peach" /><strong
							>Common<br />Ground</strong
						><span>No player phones</span></RouterLink
					><RouterLink to="/games/crowd-compass" class="gp-collage-small"
						><GameArtwork game-key="crowd-compass" color="lilac" /><strong
							>Know your crowd?</strong
						></RouterLink
					>
					<div class="gp-collage-sticker">Good<br />company<br />wins ✳</div>
				</div>
			</section>
			<section class="gp-landing-strip">
				<span>FOR THE EVERYDAY GET-TOGETHER</span><strong>Kitchen tables</strong
				><span>✳</span><strong>Classrooms</strong><span>✳</span><strong>Team days</strong
				><span>✳</span><strong>Big rooms</strong>
			</section>
			<section class="gp-container gp-landing-section">
				<div class="gp-section-head">
					<div>
						<p class="gp-eyebrow">Meet your next shared memory</p>
						<h2>Different ways to play.<br />The same reason to gather.</h2>
					</div>
					<RouterLink to="/explore">Explore the collection →</RouterLink>
				</div>
				<div class="gp-landing-games">
					<RouterLink v-for="g in picks" :key="g.key" :to="'/games/' + g.key"
						><GameArtwork :game-key="g.key" :color="g.color" />
						<p class="gp-eyebrow">{{ g.type }}</p>
						<h3>{{ g.title }} ↗</h3>
						<p>{{ g.copy }}</p></RouterLink
					>
				</div>
			</section>
			<section class="gp-landing-how gp-container">
				<div>
					<p class="gp-eyebrow">No long rulebook required</p>
					<h2>From “what now?”<br />to “again!”</h2>
					<p>
						See a sample round before you start. Choose a pack. Give everyone a way to
						join in.
					</p>
					<RouterLink class="gp-button" to="/games/common-ground"
						>Try a little connection →</RouterLink
					>
				</div>
				<ol>
					<li>
						<span>01</span>
						<div>
							<h3>Find a fit for your room.</h3>
							<p>
								Choose by mood and devices. A room full of people needs more than
								one way to play.
							</p>
						</div>
					</li>
					<li>
						<span>02</span>
						<div>
							<h3>Make it easy to belong.</h3>
							<p>
								Join by code, share a device, or put the phones away. Each game
								tells you what works.
							</p>
						</div>
					</li>
					<li>
						<span>03</span>
						<div>
							<h3>Leave room for the good part.</h3>
							<p>
								The conversation after a reveal. The terrible drawing. The
								unexpected thing you share.
							</p>
						</div>
					</li>
				</ol>
			</section>
			<section class="gp-container gp-landing-create">
				<div>
					<p class="gp-eyebrow">Made by you. Played by your people.</p>
					<h2>Your inside jokes.<br />Your big questions.<br />Your next game.</h2>
					<p>Create a private question pack in minutes, then host it for your group.</p>
					<RouterLink class="gp-button" to="/create"
						>Make something together ↗</RouterLink
					>
				</div>
				<div class="gp-paper-question">
					<span>CROWD COMPASS · YOUR EDITION</span>
					<h3>A free afternoon together.<br />What are we choosing?</h3>
					<p>☀ An adventure outside</p>
					<p>⌂ Something cosy inside</p>
					<small>Choose for yourself. Predict your people.</small>
				</div>
			</section>
			<section class="gp-container gp-landing-faq">
				<h2>A few things, before you gather.</h2>
				<details>
					<summary>Does everyone need a phone?</summary>
					<p>
						No. Filter the collection for shared devices or just the host’s device.
						Common Ground works through conversation, with an optional big screen.
					</p>
				</details>
				<details>
					<summary>Can I try hosting without an account?</summary>
					<p>
						{{
							site.allow_guest_host
								? `Yes. This site offers ${site.guest_host_limit} guest-hosted games and ${site.guest_pack_limit} private packs. Sign in in the same browser to keep your work.`
								: "This site asks hosts to sign in first."
						}}
					</p>
				</details>
				<details>
					<summary>Is it free?</summary>
					<p>
						{{
							site.access_mode === "Community"
								? "This is a free community site. Your access page explains the hosting allowance."
								: "You can start with the available trial. Your access page shows the local plan, price and receipt process."
						}}
					</p>
					<RouterLink to="/access">See your access →</RouterLink>
				</details>
				<details>
					<summary>Can I install it on my phone?</summary>
					<p>
						Yes, on a supported browser. Look for the install suggestion or use Add to
						Home Screen. Live play needs internet access.
					</p>
				</details>
			</section>
		</main>
		<footer class="gp-landing-footer">
			<strong>✳ {{ site.product_name }}</strong
			><span>A little play goes a long way.</span
			><RouterLink to="/explore">Let’s gather →</RouterLink>
		</footer>
	</div>
</template>
<script setup>
import HostBar from "@/components/HostBar.vue";
import GameArtwork from "./GameArtwork.vue";
import { site } from "@/platform/site";
const picks = [
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
