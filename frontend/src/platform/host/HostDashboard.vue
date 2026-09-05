<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<HostBar />
		<main class="mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-8">
			<header class="flex flex-wrap items-end justify-between gap-5">
				<div>
					<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-accent">
						{{ $t("Host overview") }}
					</p>
					<h1 class="mt-2 font-display text-4xl font-extrabold text-paper sm:text-5xl">
						{{ $t("Games dashboard") }}
					</h1>
					<p class="mt-3 max-w-2xl text-paper/50">
						{{
							$t(
								"See what is live now, review every session, and understand how people are playing.",
							)
						}}
					</p>
				</div>
				<button class="ctl" :disabled="loading" @click="load">
					{{ $t(loading ? "Refreshing…" : "Refresh") }}
				</button>
			</header>

			<p v-if="error" class="mt-6 text-alert">{{ $t(error) }}</p>

			<section class="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
				<div v-for="metric in metrics" :key="metric.label" class="metric-card">
					<p class="font-mono text-[10px] uppercase tracking-[0.2em] text-paper/40">
						{{ metric.label }}
					</p>
					<p class="mt-3 font-display text-3xl font-extrabold text-paper">
						{{ metric.value }}
					</p>
				</div>
			</section>

			<section
				v-if="dashboard.by_game?.length"
				class="mt-8 rounded-3xl border border-haze bg-dusk p-6"
			>
				<div class="flex items-center justify-between gap-4">
					<h2 class="font-display text-xl font-bold text-paper">
						{{ $t("Games played") }}
					</h2>
					<span class="font-mono text-[10px] uppercase tracking-wider text-paper/35">
						{{ $t("Sessions · players") }}
					</span>
				</div>
				<div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					<div
						v-for="game in dashboard.by_game"
						:key="game.game"
						class="rounded-2xl border border-haze bg-night/35 p-4"
					>
						<p class="font-display text-lg font-bold text-paper">{{ game.game }}</p>
						<p class="mt-1 font-mono text-xs text-paper/45">
							{{ game.sessions }} {{ $t("sessions ·") }} {{ game.players }}
							{{ $t("players") }}
						</p>
					</div>
				</div>
			</section>

			<section class="mt-10">
				<div class="flex flex-wrap items-end justify-between gap-4">
					<div>
						<h2 class="font-display text-2xl font-bold text-paper">
							{{ $t("Session history") }}
						</h2>
						<p class="mt-1 text-sm text-paper/45">
							{{ $t("Active rooms appear first.") }}
						</p>
					</div>
					<div class="flex gap-2">
						<button
							v-for="option in filters"
							:key="option.value"
							class="ctl"
							:data-on="filter === option.value"
							@click="filter = option.value"
						>
							{{ $t(option.label) }}
						</button>
					</div>
				</div>

				<div
					v-if="visibleSessions.length"
					class="mt-5 overflow-hidden rounded-3xl border border-haze bg-dusk"
				>
					<div
						v-for="session in visibleSessions"
						:key="`${session.game_key}-${session.name}`"
						class="grid gap-3 border-b border-haze px-5 py-4 last:border-b-0 sm:grid-cols-[1.4fr_.7fr_.7fr_.8fr] sm:items-center"
					>
						<div>
							<div class="flex flex-wrap items-center gap-2">
								<p class="font-display text-lg font-bold text-paper">
									{{ session.game_title }}
								</p>
								<span
									class="status-pill"
									:data-status="session.status.toLowerCase()"
								>
									{{ session.status }}
								</span>
							</div>
							<p class="mt-1 font-mono text-xs text-paper/35">
								{{ formatDate(session.created_at) }} {{ $t("· PIN") }}
								{{ session.pin }}
							</p>
						</div>
						<p class="font-mono text-sm text-paper/60">
							{{ session.players }} {{ $t("players") }}
						</p>
						<p class="font-mono text-sm text-paper/60">
							{{ duration(session.duration_seconds) }}
						</p>
						<RouterLink
							v-if="isActive(session) && session.can_open"
							class="ctl justify-self-start sm:justify-self-end"
							:to="resumeLink(session)"
						>
							{{ $t("Open room") }}
						</RouterLink>
						<span
							v-else-if="isActive(session)"
							class="font-mono text-xs text-paper/30 sm:text-right"
						>
							{{ $t("View only") }}
						</span>
						<span v-else class="font-mono text-xs text-paper/30 sm:text-right">{{
							session.status
						}}</span>
					</div>
				</div>
				<p
					v-else-if="!loading"
					class="mt-6 rounded-2xl border border-haze p-8 text-center text-paper/45"
				>
					{{ $t("No sessions in this view yet.") }}
				</p>
			</section>
		</main>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { get, readError } from "@/api";
import HostBar from "@/components/HostBar.vue";

const ACTIVE = new Set(["Lobby", "Active", "Paused"]);
const filters = [
	{ label: "All", value: "all" },
	{ label: "Active", value: "active" },
	{ label: "Completed", value: "completed" },
];

const dashboard = ref({ summary: {}, by_game: [], sessions: [] });
const filter = ref("all");
const loading = ref(false);
const error = ref("");

const metrics = computed(() => [
	{ label: "All sessions", value: dashboard.value.summary.total_sessions || 0 },
	{ label: "Active now", value: dashboard.value.summary.active_sessions || 0 },
	{ label: "Completed", value: dashboard.value.summary.completed_sessions || 0 },
	{ label: "Players joined", value: dashboard.value.summary.total_players || 0 },
	{ label: "Avg. players", value: dashboard.value.summary.average_players || 0 },
]);

const visibleSessions = computed(() => {
	const sessions = [...(dashboard.value.sessions || [])].sort(
		(a, b) => Number(isActive(b)) - Number(isActive(a)),
	);
	if (filter.value === "active") return sessions.filter(isActive);
	if (filter.value === "completed")
		return sessions.filter((session) => session.status === "Ended");
	return sessions;
});

onMounted(load);

async function load() {
	loading.value = true;
	error.value = "";
	try {
		dashboard.value = await get("quizzly.dashboard.get_host_dashboard");
	} catch (e) {
		error.value = readError(e);
	} finally {
		loading.value = false;
	}
}

function isActive(session) {
	return session.is_active ?? ACTIVE.has(session.status);
}

function resumeLink(session) {
	return session.game_key === "quiz"
		? { name: "Host", query: { session: session.name } }
		: { name: "GpHost", query: { session: session.name } };
}

function formatDate(value) {
	return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
		new Date(value),
	);
}

function duration(seconds) {
	if (seconds < 60) return `${seconds}s`;
	const minutes = Math.round(seconds / 60);
	return minutes < 60 ? `${minutes}m` : `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}
</script>

<style scoped>
.metric-card {
	@apply rounded-2xl border border-haze bg-dusk p-5;
}
.status-pill {
	@apply rounded-full border border-haze px-2.5 py-1 font-mono text-[9px] uppercase tracking-wider text-paper/45;
}
.status-pill[data-status="active"],
.status-pill[data-status="lobby"],
.status-pill[data-status="paused"] {
	@apply border-lagoon/40 bg-lagoon/10 text-ok;
}
</style>
