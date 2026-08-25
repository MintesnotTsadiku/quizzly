import { io } from "socket.io-client";

export function initSocket() {
	const host = window.location.hostname;
	const siteName = window.site_name || import.meta.env.VITE_FRAPPE_SITE || "training.localhost";
	if (import.meta.env.DEV) {
		// The plain Vite index has no Jinja-injected socket port. Connect to the
		// site namespace on Vite's own origin; vite.config proxies Engine.IO to
		// the bench Socket.IO service, including websocket upgrades.
		return io(`/${siteName}`, { withCredentials: true });
	}
	const port = window.location.port && window.socketio_port ? `:${window.socketio_port}` : "";
	const protocol = port ? "http" : "https";
	const url = `${protocol}://${host}${port}/${siteName}`;

	// No attempt cap: giving up strands the screen on the 20s resync watchdog for the
	// rest of the game, and a quiz outlives most network blips.
	return io(url, { withCredentials: true });
}
