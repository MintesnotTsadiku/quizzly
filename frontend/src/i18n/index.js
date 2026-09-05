import { ref } from "vue";
import am from "./am.json";

export const languages = [
	{ code: "en", label: "English" },
	{ code: "am", label: "አማርኛ" },
];
export const locale = ref("en");
const KEY = "gatherplay-language";
let defaultLocale = "en";
let explicit = false;
let parentLocale;
const valid = (value) => languages.some((item) => item.code === value);
export function initializeLanguage(siteDefault = "en") {
	defaultLocale = valid(siteDefault) ? siteDefault : "en";
	const query = new URLSearchParams(location.search).get("lang");
	let saved;
	try {
		saved = localStorage.getItem(KEY);
	} catch {}
	if (valid(query)) {
		try {
			localStorage.setItem(KEY, query);
		} catch {}
	}
	explicit = valid(query) || valid(saved);
	setLanguage(
		valid(query)
			? query
			: valid(saved)
				? saved
				: valid(parentLocale)
					? parentLocale
					: defaultLocale,
		false,
	);
}
export function setLanguage(value, persist = true) {
	locale.value = valid(value) ? value : defaultLocale;
	document.documentElement.lang = locale.value;
	document.documentElement.dir = "ltr";
	if (persist) {
		explicit = true;
		try {
			localStorage.setItem(KEY, locale.value);
		} catch {}
		const url = new URL(location.href);
		url.searchParams.set("lang", locale.value);
		history.replaceState(history.state, "", url);
	}
}
export function inheritLanguage(value) {
	if (valid(value)) {
		parentLocale = value;
		if (!explicit) setLanguage(value, false);
	}
}
export function languageUrl(value) {
	const url = new URL(value, location.origin);
	url.searchParams.set("lang", locale.value);
	return url.origin === location.origin ? url.pathname + url.search + url.hash : url.href;
}
export function t(value, params = {}) {
	if (typeof value !== "string") return value;
	const key = value.replace(/\s+/g, " ").trim();
	let result = locale.value === "am" && Object.hasOwn(am, key) ? am[key] : value;
	for (const [name, replacement] of Object.entries(params))
		result = result.replaceAll("{" + name + "}", String(replacement));
	return result;
}
export const languagePlugin = {
	install(app) {
		app.config.globalProperties.$t = t;
	},
};
