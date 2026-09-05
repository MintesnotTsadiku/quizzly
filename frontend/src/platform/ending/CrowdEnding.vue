<template>
	<section v-if="ending" class="ending" :aria-label="$t('Your room story')">
		<div
			class="story-card"
			data-testid="room-story"
			:style="{
				borderTop: `6px solid ${/^#[a-f\d]{6}$/i.test(site.accent_color || '') ? site.accent_color : '#745098'}`,
			}"
		>
			<div class="story-brand">
				<span>{{ site.product_name || "GatherPlay" }}</span
				><span>{{ $t("Crowd Compass") }}</span>
			</div>
			<p class="story-kicker">{{ $t("Played together. Remembered together.") }}</p>
			<h2>{{ $t("How well do you know your people?") }}</h2>
			<p class="story-stats">
				{{
					$t("{rounds} rounds · {entries} playing entries", {
						rounds: ending.rounds_completed,
						entries: ending.entries,
					})
				}}
			</p>
			<div v-if="includeMoment && moment" class="story-moment">
				<p>{{ moment.prompt }}</p>
				<strong>{{ moment.choice }}</strong>
				<span>{{
					$t(moment.ranked ? "{percent}% of weighted votes" : "{percent}% of votes", {
						percent: moment.percent,
					})
				}}</span>
			</div>
			<p v-else class="story-invite">
				{{ $t("We chose for ourselves. Then we tried to read the room. Your turn?") }}
			</p>
			<p class="story-foot">{{ $t("Vote. Predict. Reveal.") }}</p>
		</div>
		<template v-if="!screen">
			<label v-if="moment" class="story-consent"
				><input type="checkbox" v-model="includeMoment" />{{
					$t("Include this room moment")
				}}</label
			>
			<p class="story-note">
				{{
					$t(
						"Only the content shown in this preview is included. No player names or room code.",
					)
				}}
			</p>
			<div class="story-actions">
				<button class="ctl ctl-go" :disabled="busy" @click="exportCard(false)">
					{{ $t(busy ? "Preparing…" : "Save results card") }}
				</button>
				<button v-if="canShare" class="ctl" :disabled="busy" @click="exportCard(true)">
					{{ $t("Share with a friend") }}
				</button>
			</div>
			<p v-if="notice" role="status" class="story-note">{{ $t(notice) }}</p>
		</template>
	</section>
</template>
<script setup>
import { computed, ref } from "vue";
import { site } from "@/platform/site";
import { t, locale, languageUrl } from "@/i18n";
import { drawStory } from "./storyCard";
const props = defineProps({ ending: Object, screen: Boolean });
const moment = computed(() => props.ending?.moments?.[0]);
const includeMoment = ref(false),
	busy = ref(false),
	notice = ref("");
const canShare = typeof navigator.share === "function";
async function exportCard(share) {
	busy.value = true;
	notice.value = "";
	try {
		const blob = await drawStory({
			brand: site.product_name || "GatherPlay",
			accent: site.accent_color,
			ending: props.ending,
			moment: includeMoment.value ? moment.value : null,
			locale: locale.value,
		});
		const file = new File([blob], `gatherplay-crowd-compass-${locale.value}.png`, {
			type: "image/png",
		});
		if (share && navigator.canShare?.({ files: [file] })) {
			await navigator.share({
				files: [file],
				title: t("Crowd Compass"),
				text: t("How well do you know your people?"),
				url: new URL(languageUrl("/play/games/crowd-compass"), location.origin).href,
			});
		} else {
			const url = URL.createObjectURL(blob),
				link = document.createElement("a");
			link.href = url;
			link.download = file.name;
			link.click();
			setTimeout(() => URL.revokeObjectURL(url), 30000);
			notice.value = "Your card is ready to send to a friend.";
		}
	} catch (error) {
		if (error.name !== "AbortError")
			notice.value = "Could not share this card. Try saving it instead.";
	} finally {
		busy.value = false;
	}
}
</script>
<style scoped>
.ending {
	width: min(100%, 42rem);
	flex-shrink: 0;
	text-align: left;
}
.story-card {
	border-radius: 1.7rem;
	background: #fff5e5;
	color: #302344;
	padding: clamp(1.3rem, 4vw, 2.5rem);
	box-shadow: 0 12px 40px #00000012;
	border: 1px solid #e8d9c3;
}
.story-brand {
	display: flex;
	justify-content: space-between;
	gap: 1rem;
	font-weight: 800;
	font-size: 0.8rem;
}
.story-brand span:last-child {
	color: #705195;
}
.story-kicker {
	margin-top: 2rem;
	font-size: 0.8rem;
	color: #705195;
	font-weight: 700;
}
.story-card h2 {
	font-size: clamp(1.7rem, 4vw, 2.4rem);
	line-height: 1.25;
	font-weight: 850;
	letter-spacing: -0.035em;
	margin: 0.6rem 0;
}
.story-stats {
	font-size: 0.9rem;
	color: #6e625f;
}
.story-moment {
	margin: 1.5rem 0;
	padding: 1.2rem;
	border-radius: 1rem;
	background: #f1e6da;
}
.story-moment strong,
.story-moment span {
	display: block;
	margin-top: 0.5rem;
}
.story-moment strong {
	font-size: 1.3rem;
}
.story-moment span {
	font-size: 0.85rem;
	color: #705195;
}
.story-invite {
	font-size: 1.1rem;
	line-height: 1.6;
	max-width: 29rem;
	margin: 1.5rem 0;
}
.story-foot {
	border-top: 1px solid #dfd0bd;
	padding-top: 1rem;
	font-size: 0.8rem;
	font-weight: 700;
}
.story-consent {
	display: flex;
	gap: 0.65rem;
	align-items: center;
	margin-top: 1rem;
	color: rgb(var(--paper));
	font-size: 0.9rem;
	min-height: 44px;
}
.story-consent input {
	width: 1.2rem;
	height: 1.2rem;
	accent-color: #745098;
}
.story-actions {
	display: flex;
	gap: 0.6rem;
	flex-wrap: wrap;
	margin-top: 0.8rem;
}
.story-note {
	font-size: 0.8rem;
	line-height: 1.6;
	color: rgb(var(--paper) / 0.7);
	margin-top: 0.5rem;
}
</style>
