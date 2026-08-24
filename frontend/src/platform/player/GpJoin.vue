<template>
	<div class="relative flex h-full flex-col overflow-y-auto bg-night px-5 py-10">
		<ThemeButton class="absolute right-4 top-4 text-lg leading-none opacity-60 transition hover:opacity-100" />
		<div class="m-auto w-full max-w-sm">
			<p
				class="mb-3 flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.28em] text-accent"
			>
				<svg class="h-3 w-3 fill-gold" viewBox="0 0 24 24">
					<path :d="ICON" />
				</svg>
				GatherPlay
			</p>
			<h1 class="font-display text-5xl font-extrabold leading-none text-paper">Play along</h1>
			<p class="mt-3 text-paper/50">
				Type the PIN on the big screen, pick a face, and you're in.
			</p>

			<form class="mt-9 flex flex-col gap-6" @submit.prevent="join">
				<label class="flex flex-col gap-2">
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Game PIN</span>
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
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Nickname</span>
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
						>{{ suggestion }}</button>
						<button
							type="button"
							class="rounded-full border border-haze px-3 py-1 text-sm text-paper/45 transition hover:border-paper hover:text-paper"
							@click="suggestions = suggestNicknames()"
						>↻ More</button>
					</span>
				</label>

				<div class="flex flex-col gap-3">
					<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Your face</span>
					<div class="-mx-5">
						<div
							ref="scroller"
							class="no-scrollbar flex snap-x snap-mandatory gap-1 overflow-x-auto px-[calc(50%-22px)] py-1.5 motion-safe:scroll-smooth"
							@scroll="queuePick"
						>
							<button
								v-for="option in avatars"
								:key="option.id"
								:data-avatar="option.id"
								type="button"
								class="shrink-0 snap-center"
								:aria-label="option.id"
								:aria-pressed="avatar === option.id"
								@click="select(option.id)"
							>
								<span
									class="block rounded-full p-0.5 transition duration-200"
									:class="avatar === option.id ? 'bg-gold ring-2 ring-gold' : 'scale-[0.62] opacity-55 hover:opacity-100'"
								>
									<AvatarPic :id="option.id" :size="40" />
								</span>
							</button>
						</div>
					</div>
				</div>

				<p v-if="error" class="text-center text-sm text-alert">{{ error }}</p>
				<button
					type="submit"
					class="rounded-2xl bg-ember py-4 font-display text-xl font-extrabold text-sunk transition active:scale-[0.98]"
					:class="!pin || !nickname || joining ? 'opacity-50' : ''"
					:disabled="joining"
				>
					{{ joining ? "Joining…" : "Join the room" }}
				</button>
			</form>
		</div>
	</div>
</template>

<script setup>
import { inject, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import AvatarPic from "@/components/AvatarPic.vue";
import ThemeButton from "@/components/ThemeButton.vue";
import { avatars as avatarRoster, randomAvatar } from "@/avatars";
import { suggestNicknames } from "@/nicknames";
import { gpCall, saveGpPlayer } from "@/platform/session/gp";

const ICON =
	"M12 1 C5.5 1 2 6 2 11 C2 15 4.5 18 8 19.5 L7 23 L11 20.8 C11.3 20.9 11.6 20.9 12 21 C18.5 21 22 16 22 11 C22 6 18.5 1 12 1 Z M8.5 13 A1.6 1.6 0 1 1 8.5 9.8 A1.6 1.6 0 0 1 8.5 13 Z M12 13 A1.6 1.6 0 1 1 12 9.8 A1.6 1.6 0 0 1 12 13 Z M15.5 13 A1.6 1.6 0 1 1 15.5 9.8 A1.6 1.6 0 0 1 15.5 13 Z";

const socket = inject("$socket");
const route = useRoute();
const router = useRouter();

const pin = ref(String(route.query.pin || ""));
const nickname = ref("");
const avatar = ref("");
const avatars = ref(avatarRoster);
const suggestions = ref(suggestNicknames());
const joining = ref(false);
const error = ref("");

let pickTimer = null;
const scroller = ref(null);

function select(id) {
	avatar.value = id;
	clearTimeout(pickTimer);
	pickTimer = setTimeout(scrollToPick, 180);
}

function queuePick() {
	clearTimeout(pickTimer);
	pickTimer = setTimeout(() => {
		const chosen = document.querySelector(`[data-avatar="${avatar.value}"]`);
		if (chosen) chosen.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
	}, 150);
}

function scrollToPick() {
	queuePick();
}

onMounted(() => {
	avatar.value = randomAvatar();
	queuePick();
});

async function join() {
	error.value = "";
	joining.value = true;
	try {
		const result = await gpCall("join_session", {
			pin: pin.value.trim(),
			nickname: nickname.value,
			avatar: avatar.value,
		});
		saveGpPlayer(result);
		router.replace({ name: "GpPlayer", params: { pin: result.game_pin } });
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
		joining.value = false;
	}
}
</script>
