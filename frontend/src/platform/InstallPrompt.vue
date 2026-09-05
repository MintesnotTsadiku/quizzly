<template>
	<aside v-if="visible" class="gather-ui gp-install" aria-label="Install GatherPlay">
		<div>
			<strong>A little more play, one tap away.</strong>
			<p>
				{{
					ios
						? "In Safari, tap Share, then Add to Home Screen."
						: "Add " + site.product_name + " to your home screen."
				}}
			</p>
		</div>
		<button v-if="prompt" class="gp-button gp-button-small" @click="install">Install</button
		><button
			class="gp-install-dismiss"
			aria-label="Dismiss installation suggestion"
			@click="dismiss"
		>
			×
		</button>
	</aside>
</template>
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { site } from "./site";
const route = useRoute(),
	prompt = ref(null),
	dismissed = ref(false),
	installed = ref(matchMedia("(display-mode: standalone)").matches || navigator.standalone),
	mobile = matchMedia("(max-width: 760px)").matches,
	ios =
		/iPad|iPhone|iPod/.test(navigator.userAgent) ||
		(navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
try {
	dismissed.value =
		Date.now() - Number(localStorage.getItem("gp-install-dismissed") || 0) < 7 * 86400000;
} catch {}
const visible = computed(
	() =>
		site.enable_install &&
		window.parent === window &&
		mobile &&
		!installed.value &&
		!dismissed.value &&
		(prompt.value || ios) &&
		["Landing", "Catalog", "Access"].includes(route.name),
);
function capture(e) {
	e.preventDefault();
	prompt.value = e;
}
function dismiss() {
	dismissed.value = true;
	try {
		localStorage.setItem("gp-install-dismissed", String(Date.now()));
	} catch {}
}
function done() {
	installed.value = true;
	prompt.value = null;
}
async function install() {
	if (!prompt.value) return;
	await prompt.value.prompt();
	const result = await prompt.value.userChoice;
	prompt.value = null;
	if (result.outcome !== "accepted") dismiss();
}
onMounted(() => {
	window.addEventListener("beforeinstallprompt", capture);
	window.addEventListener("appinstalled", done);
	if (
		site.enable_install &&
		"serviceWorker" in navigator &&
		window.isSecureContext &&
		window.parent === window
	) {
		navigator.serviceWorker
			.register("/api/method/quizzly.pwa.worker", { scope: "/play/" })
			.catch(() => {});
	}
});
onBeforeUnmount(() => {
	window.removeEventListener("beforeinstallprompt", capture);
	window.removeEventListener("appinstalled", done);
});
</script>
