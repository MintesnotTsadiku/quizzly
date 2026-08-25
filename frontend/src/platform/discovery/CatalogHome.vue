<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<HostBar />
		<div class="mx-auto w-full max-w-5xl flex-1 px-5 py-10 sm:px-8">
			<header class="mb-10">
				<p
					class="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.28em] text-accent"
				>
					<svg class="h-3 w-3 fill-gold" viewBox="0 0 24 24">
						<path :d="gameIcon('cuecast')" />
					</svg>
					GatherPlay
				</p>
				<h1
					class="mt-3 font-display text-5xl font-extrabold leading-none text-paper sm:text-6xl"
				>
					Pick a game
				</h1>
				<p class="mt-4 max-w-xl text-paper/50">
					One PIN, a big screen and everyone's phones. The room is the product — every
					game keeps people looking up, not down.
				</p>
			</header>

			<p v-if="error" class="mb-6 text-alert">{{ error }}</p>

			<div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
				<RouterLink
					v-for="game in games"
					:key="game.key"
					class="group relative flex flex-col rounded-3xl border border-haze bg-dusk p-6 transition hover:border-ember"
					:class="game.status !== 'Available' ? 'pointer-events-none opacity-55' : ''"
					:to="
						game.status === 'Available'
							? { name: 'GameDetail', params: { game: game.key } }
							: {}
					"
				>
					<span class="flex items-start justify-between">
						<span
							class="grid size-12 place-items-center rounded-2xl"
							:class="game.status === 'Available' ? 'bg-ember' : 'bg-haze'"
						>
							<svg class="size-7 fill-sunk" viewBox="0 0 24 24">
								<path :d="gameIcon(game.key)" />
							</svg>
						</span>
						<span
							v-if="game.status !== 'Available'"
							class="rounded-full border border-haze px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-paper/50"
						>
							{{ game.status }}
						</span>
					</span>
					<h2 class="mt-5 font-display text-2xl font-bold text-paper">
						{{ game.title }}
					</h2>
					<p class="mt-2 flex-1 text-sm leading-relaxed text-paper/60">
						{{ game.summary }}
					</p>
					<p
						class="mt-5 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] uppercase tracking-wide text-paper/40"
					>
						<span>{{ playersLabel(game) }}</span>
						<span v-if="game.typical_minutes">~{{ game.typical_minutes }} min</span>
					</p>
					<p class="mt-3 flex flex-wrap gap-1.5">
						<span
							v-for="tag in game.interaction_tags || []"
							:key="tag"
							class="rounded-full border border-haze px-2.5 py-0.5 text-xs text-paper/60"
						>
							{{ tag }}
						</span>
					</p>
					<span
						v-if="game.status === 'Available'"
						class="mt-5 flex items-center gap-2 font-display text-sm font-bold text-accent transition group-hover:gap-3"
					>
						Learn &amp; play <span aria-hidden="true">→</span>
					</span>
				</RouterLink>
			</div>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import HostBar from "@/components/HostBar.vue";
import { catalogGames, gameIcon } from "@/platform/discovery/games";

const games = ref([]);
const error = ref("");

onMounted(async () => {
	try {
		games.value = await catalogGames();
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	}
});

function playersLabel(game) {
	return game.max_players
		? `${game.min_players}–${game.max_players} players`
		: `${game.min_players}+ players`;
}
</script>
