import { watch, reactive } from "vue";
import { call, get } from "@/api";
import { initializeLanguage, locale, t } from "@/i18n";

export const site = reactive({
	product_name: "GatherPlay",
	tagline: "Good company. Great games.",
	allow_guest_host: false,
	enable_install: false,
});
export const accessState = reactive({ loaded: false });
export async function loadSite() {
	try {
		Object.assign(site, await get("quizzly.access.configuration"));

		document.title = `${site.product_name} · ${siteText("tagline")}`;
		if (/^#[a-f\d]{6}$/i.test(site.accent_color))
			document.documentElement.style.setProperty("--gp-site-accent", site.accent_color);
	} catch {
		/* Safe defaults keep hosting closed if policy cannot load. */
	} finally {
		initializeLanguage(site.default_language);
	}
}
export async function refreshAccess() {
	Object.assign(accessState, await call("quizzly.access.my_access"), { loaded: true });
	return accessState;
}

watch(locale, () => {
	document.title = `${site.product_name} · ${siteText("tagline")}`;
});

export function siteText(key) {
	return locale.value === "am" && site[key + "_am"] ? site[key + "_am"] : t(site[key]);
}
