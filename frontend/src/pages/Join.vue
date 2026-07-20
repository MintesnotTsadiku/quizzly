<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night px-5 py-10">
		<div class="m-auto w-full max-w-sm md:max-w-2xl">
			<p
				class="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.28em] text-accent"
			>
				<svg class="h-3 w-3 fill-gold" viewBox="0 0 24 24">
					<path :d="SHAPES[1].path" />
				</svg>
				Live quiz
			</p>
			<h1 class="font-display text-6xl font-extrabold leading-none text-paper">Quizzly</h1>
			<p class="mt-3 text-paper/50">
				Type the PIN on the big screen, pick a face, and you're in.
			</p>

			<form
				class="mt-9 flex flex-col gap-6 md:grid md:grid-cols-2 md:items-start md:gap-x-8"
				@submit.prevent="join"
			>
				<label class="flex flex-col gap-2">
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">
						Game PIN
					</span>
					<input
						v-model="pin"
						class="w-full rounded-2xl border border-haze bg-dusk py-4 text-center font-mono text-4xl font-bold tracking-[0.18em] text-paper placeholder:text-paper/20 focus:border-ember"
						placeholder="000000"
						inputmode="numeric"
						maxlength="6"
						autocomplete="off"
					/>
				</label>

				<label class="flex flex-col gap-2">
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">
						Nickname
					</span>
					<input
						v-model="nickname"
						class="w-full rounded-2xl border border-haze bg-dusk px-4 py-3.5 text-lg font-medium text-paper placeholder:text-paper/25 focus:border-ember"
						placeholder="Your name"
						maxlength="20"
						autocomplete="off"
					/>
					<span class="flex flex-wrap items-center gap-2 pt-1">
						<button
							v-for="suggestion in suggestions"
							:key="suggestion"
							type="button"
							class="rounded-full border border-haze px-3 py-1 text-sm text-paper/70 transition hover:border-lagoon hover:text-ok"
							@click="nickname = suggestion"
						>
							{{ suggestion }}
						</button>
						<button
							type="button"
							class="rounded-full border border-haze px-3 py-1 text-sm text-paper/45 transition hover:border-paper hover:text-paper"
							@click="suggestions = suggestNicknames()"
						>
							↻ More
						</button>
					</span>
				</label>

				<div class="flex flex-col gap-3 md:col-span-2">
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">
						Your face
					</span>
					<!-- Bleeds past the page gutter on a phone so the roster is visibly cut
					     off at the edge, which is what says "this scrolls". -->
					<div
						class="-mx-5 flex snap-x gap-2 overflow-x-auto px-5 pb-1 motion-safe:scroll-smooth md:mx-0 md:px-0"
					>
						<!-- Every slot stays the large size and only the face inside scales,
						     so picking one never reflows the row under the thumb. -->
						<button
							v-for="option in avatars"
							:key="option.id"
							:ref="(el) => option.id === avatar && (selectedButton = el)"
							type="button"
							class="shrink-0 snap-center"
							:aria-label="option.id"
							:aria-pressed="avatar === option.id"
							@click="avatar = option.id"
						>
							<span
								class="block rounded-full p-0.5 transition duration-200"
								:class="
									avatar === option.id
										? 'bg-gold ring-2 ring-gold'
										: 'scale-[0.62] opacity-55 hover:opacity-100'
								"
							>
								<AvatarPic :id="option.id" :size="40" />
							</span>
						</button>
					</div>
				</div>

				<button
					type="submit"
					class="rounded-2xl bg-ember py-4 font-display text-xl font-extrabold text-sunk transition hover:brightness-110 disabled:opacity-50 md:col-span-2"
					:disabled="joining"
				>
					{{ joining ? "Joining…" : "Join game" }}
				</button>
				<p v-if="error" class="text-center text-sm text-alert md:col-span-2">
					{{ error }}
				</p>
			</form>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { call } from "@/api";
import { savePlayer } from "@/player";
import { avatars, randomAvatar } from "@/avatars";
import { suggestNicknames } from "@/nicknames";
import { SHAPES } from "@/game";
import AvatarPic from "@/components/AvatarPic.vue";

const route = useRoute();
const router = useRouter();

const pin = ref(route.query.pin || "");
const nickname = ref("");
const avatar = ref(randomAvatar());
const suggestions = ref(suggestNicknames());
const joining = ref(false);
const error = ref("");
const selectedButton = ref(null);

// The opening pick is random, so it lands anywhere in the roster, and a face
// tapped at the cut-off edge would otherwise stay half off-screen while big.
const centerSelected = () =>
	selectedButton.value?.scrollIntoView({ inline: "center", block: "nearest" });

onMounted(centerSelected);
watch(avatar, centerSelected, { flush: "post" });

async function join() {
	error.value = "";
	joining.value = true;
	try {
		const result = await call("quizzly.api.join_session", {
			pin: pin.value.trim(),
			nickname: nickname.value.trim(),
			avatar: avatar.value,
		});
		savePlayer(result);
		router.push("/play");
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	} finally {
		joining.value = false;
	}
}
</script>
