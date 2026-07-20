import "./index.css";
import "./theme";
import { createApp } from "vue";
import { FrappeUI, setConfig, frappeRequest } from "frappe-ui";
import router from "./router";
import App from "./App.vue";
import { initSocket } from "./socket";

setConfig("resourceFetcher", frappeRequest);

const app = createApp(App);
app.use(FrappeUI);
app.use(router);
app.provide("$socket", initSocket());
app.mount("#app");
