<template>
	<section v-if="visual" class="mt-8" aria-labelledby="game-visual-title">
		<div class="mb-4 flex flex-wrap items-end justify-between gap-3">
			<div>
				<p class="font-mono text-[10px] uppercase tracking-[0.24em] text-ok">
					{{ $t("How it works") }}
				</p>
				<h2 id="game-visual-title" class="mt-1 font-display text-2xl font-bold text-paper">
					{{ $t("See a round at a glance") }}
				</h2>
			</div>
			<p class="max-w-xl text-sm leading-relaxed text-paper/55">{{ visual.summary }}</p>
		</div>

		<button
			ref="trigger"
			type="button"
			class="group block w-full overflow-hidden rounded-3xl border border-haze bg-dusk text-left shadow-2xl transition hover:border-ember focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent"
			aria-haspopup="dialog"
			:aria-label="`See a worked ${gameTitle} example`"
			@click="openExample"
		>
			<img
				:src="visual.hero"
				alt=""
				width="1672"
				height="941"
				fetchpriority="high"
				class="aspect-video w-full object-cover"
			/>
			<span
				class="flex items-center justify-between gap-4 border-t border-haze px-5 py-4 sm:px-7"
			>
				<span>
					<span class="block font-display text-lg font-bold text-paper sm:text-xl">
						{{ $t("See a worked example") }}
					</span>
					<span class="mt-0.5 hidden text-sm text-paper/60 sm:block">
						{{ $t("Follow one prompt all the way to the score.") }}
					</span>
				</span>
				<span
					aria-hidden="true"
					class="grid size-10 shrink-0 place-items-center rounded-full bg-ember font-display text-xl font-bold text-sunk transition group-hover:scale-105"
					>↗</span
				>
			</span>
		</button>

		<p v-if="locale === 'am'" class="mt-3 text-sm">
			{{ $t("Illustration in English. Follow the Amharic steps below.") }}
		</p>
		<ol class="mt-4 grid gap-3 sm:grid-cols-3">
			<li
				v-for="(step, index) in visual.steps"
				:key="step.title"
				class="rounded-2xl border border-haze bg-dusk/65 p-4"
			>
				<p class="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-accent">
					{{ $t(String(index + 1).padStart(2, "0")) }} · {{ $t(step.title) }}
				</p>
				<p class="mt-2 text-sm leading-relaxed text-paper/65">{{ $t(step.detail) }}</p>
			</li>
		</ol>

		<dialog
			ref="dialog"
			class="qz-dialog w-[min(96vw,100rem)] max-w-none overflow-hidden rounded-3xl border border-haze bg-night p-0 text-paper shadow-2xl"
			aria-labelledby="game-example-title"
			@click.self="closeExample"
			@close="restoreFocus"
		>
			<header
				class="flex items-start gap-4 border-b border-haze bg-dusk px-5 py-4 sm:items-center sm:px-6"
			>
				<div class="min-w-0 flex-1">
					<p class="font-mono text-[10px] uppercase tracking-[0.24em] text-ok">
						{{ $t("Worked example") }}
					</p>
					<h2
						id="game-example-title"
						class="mt-1 truncate font-display text-xl font-bold"
					>
						{{ gameTitle }} {{ $t("· one complete round") }}
					</h2>
				</div>
				<button type="button" class="ctl shrink-0" @click="closeExample">
					{{ $t("Close") }}
				</button>
			</header>
			<div class="max-h-[calc(100vh-7rem)] overflow-y-auto p-3 sm:p-5">
				<img
					v-if="exampleLoaded"
					:src="visual.example"
					:alt="visual.exampleAlt"
					width="1672"
					height="941"
					class="mx-auto h-auto max-h-[calc(100vh-12rem)] w-full object-contain"
				/>
				<p class="mx-auto max-w-4xl px-2 pb-2 pt-4 text-sm leading-relaxed text-paper/65">
					{{ visual.exampleSummary }}
				</p>
				<ol class="mx-auto mt-2 grid max-w-4xl gap-3 pb-3 sm:grid-cols-3">
					<li
						v-for="(step, index) in visual.exampleSteps"
						:key="step"
						class="rounded-xl border border-haze bg-dusk px-4 py-3 text-sm leading-relaxed text-paper/65"
					>
						<span class="mr-2 font-mono text-xs font-bold text-accent">{{
							index + 1
						}}</span>
						{{ $t(step) }}
					</li>
				</ol>
			</div>
		</dialog>
	</section>
</template>

<script setup>
import { locale } from "@/i18n";
import { ref } from "vue";

defineProps({
	gameTitle: { type: String, required: true },
	visual: { type: Object, default: null },
});

const dialog = ref(null);
const trigger = ref(null);
const exampleLoaded = ref(false);

function openExample() {
	exampleLoaded.value = true;
	dialog.value?.showModal();
}

function closeExample() {
	dialog.value?.close();
}

function restoreFocus() {
	trigger.value?.focus();
}
</script>
