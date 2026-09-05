<template>
	<Teleport to="body">
		<Transition name="drawer">
			<div v-if="pack" class="fixed inset-0 z-50 flex justify-end" role="presentation">
				<button
					class="absolute inset-0 cursor-default bg-night/80 backdrop-blur-sm"
					:aria-label="$t('Close prompt preview')"
					@click="$emit('close')"
				/>
				<aside
					ref="drawerPanel"
					class="relative flex h-full w-full max-w-xl flex-col border-l border-haze bg-night shadow-2xl"
					role="dialog"
					aria-modal="true"
					aria-labelledby="pack-preview-title"
				>
					<header class="border-b border-haze px-6 py-6 sm:px-8">
						<div class="flex items-start justify-between gap-5">
							<div>
								<p
									class="font-mono text-[10px] uppercase tracking-[0.24em] text-ok"
								>
									{{ $t("Inside this pack") }}
								</p>
								<h2
									id="pack-preview-title"
									class="mt-2 font-display text-3xl font-bold text-paper"
								>
									{{ pack.title }}
								</h2>
								<p class="mt-2 text-sm text-paper/50">
									{{ pack.prompt_count }}
									{{ $t("prompts · shown in play order") }}
								</p>
							</div>
							<button
								ref="closeButton"
								class="drawer-close"
								:aria-label="$t('Close prompt preview')"
								@click="$emit('close')"
							>
								<svg
									viewBox="0 0 24 24"
									class="size-5 fill-none stroke-current"
									stroke-width="2"
								>
									<path d="m6 6 12 12M18 6 6 18" />
								</svg>
							</button>
						</div>
					</header>

					<ol class="flex-1 space-y-3 overflow-y-auto px-6 py-6 sm:px-8">
						<li
							v-for="(prompt, index) in pack.prompts"
							:key="`${index}-${prompt.text}`"
							class="rounded-2xl border border-haze bg-dusk p-5"
						>
							<div class="flex gap-4">
								<span class="prompt-number">{{
									$t(String(index + 1).padStart(2, "0"))
								}}</span>
								<div class="min-w-0 flex-1">
									<p
										class="font-display text-base font-bold leading-snug text-paper"
									>
										{{ prompt.text }}
									</p>
									<div
										v-if="prompt.choices?.length"
										class="mt-4 grid gap-2 sm:grid-cols-2"
									>
										<div
											v-for="(choice, choiceIndex) in prompt.choices"
											:key="choice"
											class="flex items-center gap-2 rounded-xl border border-haze bg-night/45 px-3 py-2 text-sm text-paper/65"
										>
											<span class="choice-shape" :data-shape="choiceIndex" />
											{{ choice }}
										</div>
									</div>
								</div>
							</div>
						</li>
					</ol>

					<footer class="border-t border-haze bg-dusk/70 px-6 py-5 sm:px-8">
						<button class="ctl ctl-go w-full" @click="$emit('choose', pack)">
							{{ $t("Choose this pack") }}
						</button>
					</footer>
				</aside>
			</div>
		</Transition>
	</Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from "vue";

const props = defineProps({ pack: { type: Object, default: null } });
const emit = defineEmits(["close", "choose"]);
const drawerPanel = ref(null);
const closeButton = ref(null);
const previousOverflow = document.body.style.overflow;
let returnFocus = null;

function onKeydown(event) {
	if (!props.pack) return;
	if (event.key === "Escape") {
		emit("close");
		return;
	}
	if (event.key !== "Tab") return;
	const focusable = drawerPanel.value?.querySelectorAll(
		'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])',
	);
	if (!focusable?.length) return;
	const first = focusable[0];
	const last = focusable[focusable.length - 1];
	if (event.shiftKey && document.activeElement === first) {
		event.preventDefault();
		last.focus();
	} else if (!event.shiftKey && document.activeElement === last) {
		event.preventDefault();
		first.focus();
	}
}

watch(
	() => props.pack,
	async (pack, previousPack) => {
		document.body.style.overflow = pack ? "hidden" : previousOverflow;
		if (pack && !previousPack) {
			returnFocus = document.activeElement;
			await nextTick();
			closeButton.value?.focus();
		} else if (!pack && previousPack) {
			returnFocus?.focus?.();
			returnFocus = null;
		}
	},
);
document.addEventListener("keydown", onKeydown);
onBeforeUnmount(() => {
	document.body.style.overflow = previousOverflow;
	document.removeEventListener("keydown", onKeydown);
});
</script>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
	transition: opacity 180ms ease;
}
.drawer-enter-active aside,
.drawer-leave-active aside {
	transition: transform 220ms cubic-bezier(0.22, 1, 0.36, 1);
}
.drawer-enter-from,
.drawer-leave-to {
	opacity: 0;
}
.drawer-enter-from aside,
.drawer-leave-to aside {
	transform: translateX(100%);
}
.drawer-close {
	display: grid;
	place-items: center;
	width: 2.5rem;
	height: 2.5rem;
	border: 1px solid rgb(var(--haze));
	border-radius: 0.85rem;
	color: rgb(var(--paper) / 0.6);
}
.prompt-number {
	display: grid;
	place-items: center;
	flex: 0 0 auto;
	width: 2.25rem;
	height: 2.25rem;
	border-radius: 0.7rem;
	background: rgb(var(--gold) / 0.12);
	font-family: var(--font-mono);
	font-size: 0.7rem;
	font-weight: 700;
	color: rgb(var(--accent));
}
.choice-shape {
	width: 0.55rem;
	height: 0.55rem;
	border-radius: 999px;
	background: rgb(var(--ember));
}
.choice-shape[data-shape="1"] {
	background: rgb(var(--lagoon));
}
.choice-shape[data-shape="2"] {
	background: rgb(var(--gold));
}
.choice-shape[data-shape="3"] {
	background: rgb(var(--orchid));
}
</style>
