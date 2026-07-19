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

const route = useRoute();
const router = useRouter();

const pin = ref(route.query.pin || "");
const nickname = ref("");
const joining = ref(false);
const error = ref("");

async function join() {
	error.value = "";
	joining.value = true;
	try {
		const result = await call("quizzly.api.join_session", {
			pin: pin.value.trim(),
			nickname: nickname.value.trim(),
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
