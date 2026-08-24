<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<HostBar />
		<div class="mx-auto w-full max-w-5xl flex-1 px-5 py-10 sm:px-8" v-if="game">
			<RouterLink
				class="font-mono text-xs uppercase tracking-[0.22em] text-paper/40 transition hover:text-paper"
				:to="{ name: 'Catalog' }"
			>
				← All games
			</RouterLink>

			<header class="mt-8 flex flex-wrap items-start justify-between gap-6">
				<div class="min-w-0 max-w-2xl">
					<h1 class="font-display text-5xl font-extrabold leading-none text-paper sm:text-6xl">
						{{ game.title }}
					</h1>
					<p class="mt-4 text-lg text-paper/60">{{ game.summary }}</p>
					<p class="mt-4 flex flex-wrap items-center gap-x-5 gap-y-1 font-mono text-xs uppercase tracking-wide text-paper/45">
						<span>{{ playersLabel(game) }}</span>
						<span v-if="game.recommended_players">best {{ game.recommended_players }}</span>
						<span v-if="game.typical_minutes">~{{ game.typical_minutes }} min</span>
					</p>
				</div>
				<div class="flex shrink-0 flex-col gap-3">
					<button
						v-if="!hosting"
						class="ctl ctl-go"
						@click="hosting = true"
					>
						Host this game
					</button>
					<p v-if="error" class="max-w-56 text-sm text-alert">{{ error }}</p>
				</div>
			</header>

			<!-- Host panel: deck + pacing, or demo shortcut -->
			<section
				v-if="hosting"
				class="mt-8 rounded-3xl border border-haze bg-dusk p-6 sm:p-8"
			>
				<h2 class="font-display text-xl font-bold text-paper">Set up the room</h2>
				<div class="mt-6 grid gap-6 lg:grid-cols-2">
					<label class="flex flex-col gap-2">
						<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Deck</span>
						<select v-model="setup.deck" class="field">
							<option value="" disabled>Pick a deck…</option>
							<option v-for="deck in decks" :key="deck.name" :value="deck.name">
								{{ deck.title }} · {{ deck.prompt_count }} prompts
								{{ Number(deck.is_demo) ? "· demo" : "" }}
							</option>
						</select>
					</label>
					<div class="flex flex-col gap-2">
						<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">
							Round length
						</span>
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
						<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Teams</span>
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
					<div class="flex items-end justify-between gap-4">
						<label class="flex items-center gap-3 text-paper/70">
							<input
								type="checkbox"
								v-model="setup.sudden_death"
								class="size-4 accent-[rgb(var(--accent))]"
							/>
							Sudden-death tiebreaker
						</label>
						<button
							class="ctl ctl-go"
							:disabled="!setup.deck || creating"
							@click="createSession"
						>
							{{ creating ? "Creating…" : "Open the lobby" }}
						</button>
					</div>
				</div>
			</section>

			<section class="mt-12 grid gap-10 lg:grid-cols-2">
				<div>
					<h2 class="font-display text-2xl font-bold text-paper">How to play</h2>
					<ol class="mt-5 flex flex-col gap-4">
						<li
							v-for="(step, index) in guide.howTo"
							:key="index"
							class="flex gap-4 text-paper/70"
						>
							<span class="font-mono text-sm font-bold tabular-nums text-accent">
								{{ String(index + 1).padStart(2, "0") }}
							</span>
							{{ step }}
						</li>
					</ol>
					<h3 class="mt-8 font-display text-base font-bold text-paper">Scoring</h3>
					<p class="mt-2 text-sm leading-relaxed text-paper/60">{{ guide.scoring }}</p>
					<h3 class="mt-6 font-display text-base font-bold text-paper">Room setup</h3>
					<p class="mt-2 text-sm leading-relaxed text-paper/60">{{ guide.setup }}</p>
				</div>
				<div class="flex flex-col gap-6">
					<div class="rounded-2xl border border-haze bg-dusk p-5">
						<h3 class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">The host does</h3>
						<p class="mt-2 text-sm leading-relaxed text-paper/70">{{ guide.hostDoes }}</p>
					</div>
					<div class="rounded-2xl border border-haze bg-dusk p-5">
						<h3 class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Players see</h3>
						<p class="mt-2 text-sm leading-relaxed text-paper/70">{{ guide.playerSees }}</p>
					</div>
					<div class="rounded-2xl border border-haze bg-dusk p-5">
						<h3 class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">The room sees</h3>
						<p class="mt-2 text-sm leading-relaxed text-paper/70">{{ guide.roomSees }}</p>
					</div>
					<div class="rounded-2xl border border-haze bg-dusk p-5">
						<h3 class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Accessibility</h3>
						<p class="mt-2 text-sm leading-relaxed text-paper/70">{{ guide.accessibility }}</p>
					</div>
				</div>
			</section>

			<!-- Demo packs: three audience flavours per module (implementation plan §1) -->
			<section v-if="guide.demos?.length" class="mt-14">
				<h2 class="font-display text-2xl font-bold text-paper">Play a demo</h2>
				<p class="mt-2 text-paper/50">
					Ready-made decks you can host instantly or duplicate and make your own.
				</p>
				<div class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
					<div
						v-for="demo in demoCards(guide.demos)"
						:key="demo.demo_key"
						class="group flex flex-col rounded-3xl border border-haze bg-dusk p-6 transition hover:border-lagoon"
					>
						<span
							class="w-fit rounded-full border border-haze px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-ok"
						>
							{{ demo.audience }}
						</span>
						<h3 class="mt-4 font-display text-xl font-bold text-paper">{{ demo.title }}</h3>
						<p class="mt-2 flex-1 text-sm leading-relaxed text-paper/60">{{ demo.blurb }}</p>
						<p class="mt-4 font-mono text-xs text-paper/40">{{ demo.prompt_count }} prompts</p>
						<button
							class="ctl mt-4 self-start"
							:disabled="creatingDemo === demo.name"
							@click="hostDemo(demo)"
						>
							{{ creatingDemo === demo.name ? "Opening…" : "Host demo" }}
						</button>
					</div>
				</div>
			</section>

			<!-- Reserved video slot: the data contract exists, the video may never be required -->
			<section class="mt-14 rounded-3xl border border-dashed border-haze p-8 text-center">
				<div class="mx-auto grid size-16 place-items-center rounded-2xl bg-dusk">
					<svg class="size-8 fill-paper/30" viewBox="0 0 24 24">
						<path d="M8 5v14l11-7z" />
					</svg>
				</div>
				<p class="mt-4 font-mono text-[11px] uppercase tracking-[0.22em] text-paper/35">
					How-to video coming soon
				</p>
				<p class="mx-auto mt-2 max-w-md text-sm text-paper/45">
					The full written guide above stays the source of truth — captions and a
					transcript will ship with the video.
				</p>
			</section>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import HostBar from "@/components/HostBar.vue";
import { gameIcon, guideFor } from "@/platform/discovery/games";
import { gpCall, rememberHostedSession } from "@/platform/session/gp";

const router = useRouter();
const game = ref(null);
const guide = ref({ howTo: [], demos: [] });
const decks = ref([]);
const hosting = ref(false);
const creating = ref(false);
const creatingDemo = ref(null);
const error = ref("");
const setup = ref({ deck: "", seconds: 60, teams_count: 2, sudden_death: true });

onMounted(async () => {
	try {
		const games = await gpCall("list_games");
		game.value = games.find((g) => g.key === routeGame()) || games[0];
		if (!game.value || game.value.status !== "Available") {
			router.replace({ name: "Catalog" });
			return;
		}
		guide.value = guideFor(game.value.key);
		decks.value = await gpCall("list_public_decks", { game_key: game.value.key });
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	}
});

function routeGame() {
	return window.location.pathname.split("/games/")[1]?.split("/")[0];
}

function demoCards(demos) {
	return demos
		.map((demo) => ({
			...demo,
			name: decks.value.find((d) => d.demo_key === demo.demo_key)?.name,
			prompt_count:
				decks.value.find((d) => d.demo_key === demo.demo_key)?.prompt_count ?? "—",
		}))
		.filter((demo) => demo.name);
}

async function createSession() {
	error.value = "";
	creating.value = true;
	try {
		const created = await gpCall("create_session", { game_key: game.value.key, configuration: setup.value });
		rememberHostedSession(created.session);
		router.push({ name: "GpHost", query: { session: created.session } });
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	} finally {
		creating.value = false;
	}
}

async function hostDemo(demo) {
	error.value = "";
	creatingDemo.value = demo.name;
	try {
		const created = await gpCall("create_session", {
			game_key: game.value.key,
			configuration: { deck: demo.name, seconds: 60, teams_count: 2 },
		});
		rememberHostedSession(created.session);
		router.push({ name: "GpHost", query: { session: created.session } });
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	} finally {
		creatingDemo.value = null;
	}
}

function playersLabel(game) {
	return game.max_players ? `${game.min_players}–${game.max_players} players` : `${game.min_players}+ players`;
}
</script>
