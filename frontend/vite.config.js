import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import frappeui from "frappe-ui/vite";
import path from "path";

export default defineConfig({
	server: {
		// WSL's inotify/file-descriptor budget is shared by every app in this
		// multi-app bench. Polling keeps HMR reliable when other watchers have
		// exhausted that budget and avoids Vite's EMFILE startup failure.
		watch: {
			usePolling: true,
			interval: 300,
		},
		proxy: {
			// Keep the browser on Vite's origin during development while forwarding
			// Engine.IO polling and websocket upgrades to the bench realtime server.
			"/socket.io": {
				target: process.env.SOCKETIO_URL || "http://127.0.0.1:19031",
				ws: true,
				configure(proxy) {
					const preserveBrowserHost = (proxyRequest, request) => {
						if (request.headers.host)
							proxyRequest.setHeader("host", request.headers.host);
					};
					proxy.on("proxyReq", preserveBrowserHost);
					proxy.on("proxyReqWs", preserveBrowserHost);
				},
			},
		},
	},
	optimizeDeps: {
		// frappe-ui's source exports include its optional TextEditor, whose virtual
		// Lucide modules are resolved by the plugin below (not esbuild's eager
		// dependency scanner). Transform it on demand instead of pre-bundling it.
		exclude: ["frappe-ui"],
		// frappe-ui itself is transformed on demand, but this CommonJS dependency
		// still needs Vite's interop wrapper for its default import.
		include: ["feather-icons"],
	},
	plugins: [
		frappeui({
			frappeProxy: true,
			lucideIcons: true,
			jinjaBootData: true,
			buildConfig: {
				indexHtmlPath: "../quizzly/www/quizzly.html",
				emptyOutDir: true,
				sourcemap: true,
			},
		}),
		vue(),
	],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src"),
		},
	},
});
