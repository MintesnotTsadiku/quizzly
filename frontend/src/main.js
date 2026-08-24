import "./index.css";
import "./theme";
import { createApp } from "vue";
import { FrappeUI, setConfig, frappeRequest } from "frappe-ui";
import router from "./router";
import App from "./App.vue";
import { initSocket } from "./socket";

setConfig("resourceFetcher", frappeRequest);

const app = createApp(App);
// Quizzly owns its realtime connection so it can use the port advertised by
// the active bench at runtime. Prevent FrappeUI from opening a second socket
// with its development default (port 9000).
app.use(FrappeUI, { socketio: false });
app.use(router);
app.provide("$socket", initSocket());
app.mount("#app");
