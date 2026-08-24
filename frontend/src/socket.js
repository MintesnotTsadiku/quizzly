import { io } from "socket.io-client";

export function initSocket() {
	const host = window.location.hostname;
	const siteName = window.site_name || host;
	const port = window.location.port && window.socketio_port ? `:${window.socketio_port}` : "";
	const protocol = port ? "http" : "https";
	const url = `${protocol}://${host}${port}/${siteName}`;

	// No attempt cap: giving up strands the screen on the 20s resync watchdog for the
	// rest of the game, and a quiz outlives most network blips.
	return io(url, { withCredentials: true });
}
