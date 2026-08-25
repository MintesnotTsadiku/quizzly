import { getSiteName } from "./site";

function hasBootData() {
	return (
		window.csrf_token &&
		window.csrf_token !== "{{ csrf_token }}" &&
		window.site_name &&
		window.session_user
	);
}

export async function loadSpaBoot() {
	if (hasBootData()) return;

	const response = await fetch("/api/method/quizzly.api.get_spa_boot", {
		method: "GET",
		credentials: "same-origin",
		headers: {
			Accept: "application/json",
			"X-Frappe-Site-Name": getSiteName(),
		},
	});
	if (!response.ok) throw new Error(`Unable to initialize Quizzly (${response.status})`);
	const payload = await response.json();
	Object.assign(window, payload.message || {});
}
