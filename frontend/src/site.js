const DEV_SITE = import.meta.env.VITE_FRAPPE_SITE || "training.localhost";

export function getSiteName() {
	return window.site_name || DEV_SITE;
}
