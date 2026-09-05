<template>
	<header class="gp-nav" :class="{ 'gp-nav-embedded': embedded }">
		<RouterLink class="gp-brand" to="/" :aria-label="$t('GatherPlay home')">
			<img v-if="site.logo" :src="site.logo" alt="" width="32" height="32" /><svg
				v-else
				width="32"
				height="32"
				viewBox="0 0 32 32"
				aria-hidden="true"
			>
				<path d="M5 4h9v9H5zM18 4h9v9h-9zM5 17h9v9H5z" fill="currentColor" />
				<circle cx="22.5" cy="21.5" r="6" fill="currentColor" />
			</svg>
			<span
				>{{ site.product_name
				}}<span v-if="embedded" class="gp-tenant">{{
					$t(
						brand.short_name !== "GatherPlay"
							? brand.short_name
							: "Games for your community",
					)
				}}</span></span
			>
		</RouterLink>
		<nav :aria-label="$t('GatherPlay navigation')">
			<RouterLink
				to="/explore"
				:aria-current="route.name === 'Catalog' ? 'page' : undefined"
			>
				{{ $t("Explore") }}
			</RouterLink>
			<RouterLink
				v-if="!guest"
				to="/host/dashboard"
				:aria-current="route.name === 'HostDashboard' ? 'page' : undefined"
			>
				{{ $t("My sessions") }}
			</RouterLink>
			<RouterLink class="gp-nav-content" to="/create">
				{{ $t("Create a pack") }}
			</RouterLink>
			<RouterLink to="/access"> {{ $t("Your access") }} </RouterLink>
		</nav>
		<div class="gp-nav-actions">
			<LanguageSwitch />
			<ThemeButton v-if="!embedded" class="gp-theme" />
			<RouterLink class="gp-button gp-button-small" to="/join">
				{{ $t("Join a game") }} <span aria-hidden="true">↗</span></RouterLink
			>
			<button v-if="guest" class="gp-login" @click="login">{{ $t("Sign in") }}</button>
			<button v-else-if="!embedded" class="gp-login" @click="logout">
				{{ $t("Sign out") }}
			</button>
		</div>
	</header>
</template>
<script setup>
import { useRoute } from "vue-router";
import { call } from "@/api";
import { redirectGuestToLogin } from "@/auth";
import { brand, embedded } from "@/theme";
import LanguageSwitch from "@/components/LanguageSwitch.vue";
import ThemeButton from "@/components/ThemeButton.vue";
import { site } from "@/platform/site";
const route = useRoute();
const guest = !window.session_user || window.session_user === "Guest";
function login() {
	redirectGuestToLogin();
}
async function logout() {
	await call("logout");
	window.location.href = "/play/";
}
</script>
