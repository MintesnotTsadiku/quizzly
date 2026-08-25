import "./index.css";
import "./theme";
import { createApp } from "vue";
import { FrappeUI, setConfig, frappeRequest } from "frappe-ui";
import { loadSpaBoot } from "./boot";

async function bootstrap() {
	if (
		window.location.pathname === "/quizzly" ||
		window.location.pathname.startsWith("/quizzly/")
	) {
		const suffix = window.location.pathname.slice("/quizzly".length);
		window.location.replace(
			`/play/quizzly${suffix}${window.location.search}${window.location.hash}`
		);
		return;
	}

	await loadSpaBoot();

	const [{ default: router }, { default: App }, { initSocket }] = await Promise.all([
		import("./router"),
		import("./App.vue"),
		import("./socket"),
	]);

	setConfig("resourceFetcher", frappeRequest);

	const app = createApp(App);
	// Quizzly owns its realtime connection so it can use the port advertised by
	// the active bench at runtime. Prevent FrappeUI from opening a second socket
	// with its development default (port 9000).
	app.use(FrappeUI, { socketio: false });
	app.use(router);
	app.provide("$socket", initSocket());
	app.mount("#app");
}

bootstrap();
