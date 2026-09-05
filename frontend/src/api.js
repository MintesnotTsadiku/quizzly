import { frappeRequest } from "frappe-ui";
import { getSiteName } from "./site";

const HOST_ACCESS_ERROR = "Visit Your access to check the hosting options on this site.";

// Preserve actionable policy messages instead of replacing every denial with a role name.
export function readError(e) {
	return e.messages?.[0] || e.message || HOST_ACCESS_ERROR;
}

export function call(method, params = {}) {
	const hostMethods = new Set([
		"create_session",
		"get_host_state",
		"start_session",
		"host_command",
		"end_session",
		"advance_room",
		"set_lobby_locked",
		"lock_lobby",
		"unlock_lobby",
		"kick_participant",
		"get_lobby",
		"set_auto_advance",
		"next_question",
		"skip_question",
		"list_quizzes",
	]);
	if (
		window.session_user === "Guest" &&
		(method.startsWith("quizzly.games.api.") || method.startsWith("quizzly.api.")) &&
		hostMethods.has(method.split(".").at(-1))
	) {
		params = {
			method: method.split(".").at(-1),
			params,
			legacy: method.startsWith("quizzly.api."),
		};
		method = "quizzly.access.guest_host";
	}
	return frappeRequest({
		url: `/api/method/${method}`,
		method: "POST",
		params,
		headers: {
			"X-Frappe-Site-Name": getSiteName(),
		},
	});
}

export async function get(method) {
	const response = await fetch(`/api/method/${method}`, {
		credentials: "same-origin",
		headers: {
			Accept: "application/json",
			"X-Frappe-Site-Name": getSiteName(),
		},
	});
	const payload = await response.json();
	if (!response.ok) {
		throw Object.assign(
			new Error(payload.message || `Request failed (${response.status})`),
			payload,
		);
	}
	return payload.message;
}
