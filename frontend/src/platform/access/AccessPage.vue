<template>
	<div class="gather-ui gp-page">
		<HostBar />
		<main class="gp-account gp-container">
			<p class="gp-eyebrow">{{ $t("More good times, on your terms") }}</p>
			<a
				v-if="site.can_manage"
				class="gp-admin-link"
				href="/app/gatherplay-settings"
				target="_blank"
				rel="noopener"
			>
				{{ $t("Manage this site’s settings ↗") }}
			</a>
			<h1>{{ $t("Your place at the table.") }}</h1>
			<p class="gp-lead">
				{{ $t("Start small. Make it yours. Keep your people playing.") }}
			</p>
			<p v-if="error" class="gp-error" role="alert">{{ $t(error) }}</p>
			<p v-if="notice" class="gp-notice" role="status">{{ $t(notice) }}</p>
			<div class="gp-account-grid">
				<section class="gp-account-card">
					<p class="gp-eyebrow">
						{{
							$t(
								state.guest
									? "Your guest trial"
									: state.verified
										? "Your account"
										: "One more step",
							)
						}}
					</p>
					<h2>
						{{
							$t(
								state.guest
									? "Come as you are."
									: state.verified
										? "Ready when you are."
										: "Make it official.",
							)
						}}
					</h2>
					<p v-if="state.loaded">
						{{
							$t(
								state.hosts_remaining === null
									? "Unlimited"
									: state.hosts_remaining,
							)
						}}
						{{ $t("games ·") }}
						{{
							$t(
								state.packs_remaining === null
									? "unlimited"
									: state.packs_remaining,
							)
						}}
						{{ $t("private packs available") }}
					</p>
					<p v-if="state.guest">
						{{
							$t(
								"Your trial stays in this browser for a limited time. Sign in here to bring your trial games and packs with you.",
							)
						}}
					</p>
					<p v-else-if="!state.verified">
						{{
							$t(
								"Verify your email to continue after your starter allowance. Your existing games can still finish.",
							)
						}}
					</p>
					<a v-if="state.guest" class="gp-button" :href="loginUrl">
						{{ $t("Sign in or create an account →") }}
					</a>
					<button
						v-else-if="!state.verified"
						class="gp-button"
						:disabled="busy"
						@click="sendVerification"
					>
						{{ $t("Email me a verification link") }}
					</button>
					<button
						v-if="verifyToken"
						class="gp-button"
						:disabled="busy || state.guest"
						@click="verify"
					>
						{{ $t("Confirm my email") }}
					</button>
					<div class="gp-account-links">
						<RouterLink to="/explore"> {{ $t("Find a game →") }} </RouterLink
						><RouterLink to="/create"> {{ $t("Make a question pack →") }} </RouterLink>
					</div>
				</section>
				<section
					class="gp-account-card gp-account-plan"
					v-if="site.access_mode === 'Paid'"
				>
					<p class="gp-eyebrow">{{ site.plan_name }}</p>
					<h2>{{ site.currency }} {{ site.price }}</h2>
					<p>
						{{ site.plan_days }} {{ $t("days ·") }} {{ site.paid_host_limit }}
						{{ $t("games and") }} {{ site.paid_pack_limit }}
						{{ $t("packs per calendar month.") }}
					</p>
					<p class="gp-payment-instructions">{{ siteText("payment_instructions") }}</p>
					<p>
						{{
							$t(
								site.optimistic_approval
									? `Your first receipt each month unlocks ${site.provisional_days} days of provisional access while it is reviewed.`
									: "Access begins when your receipt is approved.",
							)
						}}
						{{ $t("Approval grants") }} {{ site.plan_days }}
						{{ $t("days. A rejected receipt removes paid access for new games.") }}
					</p>
					<form v-if="!state.guest && state.verified" @submit.prevent="submit">
						<label class="gp-field"
							><span> {{ $t("Payment reference") }} </span
							><input
								v-model="reference"
								required
								minlength="4"
								maxlength="100"
								:placeholder="$t('Reference from your payment')" /></label
						><label class="gp-field"
							><span>
								{{ $t("Private receipt · PNG, JPEG or PDF, up to 5 MB") }} </span
							><input
								type="file"
								accept="image/png,image/jpeg,application/pdf"
								required
								@change="file = $event.target.files[0]" /></label
						><button class="gp-button" :disabled="busy">
							{{ $t(busy ? "Submitting…" : "Attach receipt and request access") }}
						</button>
					</form>
					<p v-else>
						{{ $t("Sign in and verify your email before attaching a receipt.") }}
					</p>
				</section>
				<section v-else class="gp-account-card gp-account-plan">
					<p class="gp-eyebrow">{{ $t("Community comes first") }}</p>
					<h2>{{ $t("No payment required.") }}</h2>
					<p>
						{{
							$t(
								"This site keeps gathering free. Sign in after your guest trial to continue under the community’s hosting policy.",
							)
						}}
					</p>
					<GameArtwork game-key="common-ground" color="lime" />
				</section>
			</div>
			<section v-if="receipts.length" class="gp-receipts">
				<h2>{{ $t("Your requests") }}</h2>
				<article v-for="r in receipts" :key="r.name">
					<strong>{{ r.reference }}</strong
					><span>{{ $t(r.status) }}</span>
					<p v-if="r.valid_until">
						{{ $t("Access until") }} {{ new Date(r.valid_until).toLocaleDateString() }}
					</p>
					<p v-if="r.review_note">{{ r.review_note }}</p>
				</article>
			</section>
		</main>
	</div>
</template>
<script setup>
import { onMounted, ref } from "vue";
import HostBar from "@/components/HostBar.vue";
import GameArtwork from "@/platform/discovery/GameArtwork.vue";
import { site, siteText, accessState as state, refreshAccess } from "@/platform/site";
import { call, readError } from "@/api";
const busy = ref(false),
	error = ref(""),
	notice = ref(""),
	reference = ref(""),
	file = ref(null),
	receipts = ref([]),
	verifyToken = ref(new URLSearchParams(location.hash.slice(1)).get("verify") || "");
const loginUrl = "/login?redirect-to=" + encodeURIComponent("/play/access" + location.hash);
async function run(fn) {
	busy.value = true;
	error.value = "";
	try {
		await fn();
		await refreshAccess();
	} catch (e) {
		error.value = readError(e);
	} finally {
		busy.value = false;
	}
}
async function load() {
	await refreshAccess();
	if (!state.guest) receipts.value = await call("quizzly.access.my_receipts");
}
function sendVerification() {
	run(async () => {
		await call("quizzly.access.send_verification");
		notice.value =
			"Verification email queued. Check your inbox; delivery depends on this site’s email service.";
	});
}
function verify() {
	run(async () => {
		await call("quizzly.access.verify_email", { token: verifyToken.value });
		verifyToken.value = "";
		history.replaceState(null, "", location.pathname);
		notice.value = "Email verified. You’re ready to keep playing.";
	});
}
function submit() {
	run(async () => {
		if (!file.value || file.value.size > 5 * 1024 * 1024)
			throw Error("Choose a receipt under 5 MB.");
		const data = new FormData();
		data.append("file", file.value);
		data.append("is_private", "1");
		const r = await fetch("/api/method/upload_file", {
			method: "POST",
			headers: { "X-Frappe-CSRF-Token": window.csrf_token },
			body: data,
		});
		const j = await r.json();
		if (!r.ok) throw Error("Receipt upload failed. Please try again.");
		const result = await call("quizzly.access.submit_receipt", {
			reference: reference.value,
			file_url: j.message.file_url,
		});
		notice.value = `Receipt received: ${result.status}.`;
		await load();
	});
}
onMounted(() => run(load));
</script>
