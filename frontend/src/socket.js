import { io } from "socket.io-client";
import { getSiteName } from "./site";

export function initSocket() {
	// API, pages, polling and websocket upgrades all stay on the browser's origin.
	// Vite and the production reverse proxy route /socket.io to Frappe realtime.
	return io(`/${getSiteName()}`, {
		path: "/socket.io",
		withCredentials: true,
	});
}
