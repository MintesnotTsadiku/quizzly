import { frappeRequest } from "frappe-ui";
import { getSiteName } from "./site";

const HOST_ACCESS_ERROR = "Log in with a Quiz Host account to write and host quizzes.";

// A host screen that a non-host opens fails on its first call; the framework's own
// message names doctypes and permissions, which means nothing to a teacher.
export function readError(e) {
	return e.exc_type === "PermissionError" ? HOST_ACCESS_ERROR : e.messages?.[0] || e.message;
}

export function call(method, params = {}) {
	return frappeRequest({
		url: `/api/method/${method}`,
		method: "POST",
		params,
		headers: {
			"X-Frappe-Site-Name": getSiteName(),
		},
	});
}
