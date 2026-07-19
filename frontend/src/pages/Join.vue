<template>
	<div class="flex h-full flex-col items-center justify-center gap-8 p-4">
		<h1 class="text-4xl font-black tracking-tight text-ink-gray-9">Quizzly</h1>
		<form class="flex w-full max-w-xs flex-col gap-4" @submit.prevent="join">
			<FormControl
				v-model="pin"
				label="Game PIN"
				placeholder="123456"
				size="lg"
				inputmode="numeric"
				maxlength="6"
				autocomplete="off"
			/>
			<FormControl
				v-model="nickname"
				label="Nickname"
				placeholder="Your name"
				size="lg"
				maxlength="20"
				autocomplete="off"
			/>
			<div class="flex flex-col gap-2">
				<span class="text-xs text-ink-gray-5">Pick your avatar</span>
				<div class="grid grid-cols-6 gap-2">
					<button
						v-for="option in avatars"
						:key="option.id"
						type="button"
						class="rounded-full outline-none ring-offset-2 transition"
						:class="
							avatar === option.id
								? 'scale-110 ring-2 ring-ink-gray-9'
								: 'opacity-50 hover:opacity-100'
						"
						:aria-label="option.id"
						:aria-pressed="avatar === option.id"
						@click="avatar = option.id"
					>
						<AvatarPic :id="option.id" :size="40" />
					</button>
				</div>
			</div>
			<Button variant="solid" size="lg" type="submit" :loading="joining">Join game</Button>
			<ErrorMessage :message="error" />
		</form>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Button, ErrorMessage, FormControl } from "frappe-ui";
import { call } from "@/api";
import { savePlayer } from "@/player";
import { avatars, randomAvatar } from "@/avatars";
import AvatarPic from "@/components/AvatarPic.vue";

const route = useRoute();
const router = useRouter();

const pin = ref(route.query.pin || "");
const nickname = ref("");
const avatar = ref(randomAvatar());
const joining = ref(false);
const error = ref("");

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
