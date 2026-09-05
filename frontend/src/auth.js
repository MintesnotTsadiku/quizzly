export function redirectGuestToLogin(
	returnTo = `${window.location.pathname}${window.location.search}${window.location.hash}`
) {
	if (window.session_user !== "Guest") return false;
	window.location.href = `/login?redirect-to=${encodeURIComponent(returnTo)}`;
	return true;
}
