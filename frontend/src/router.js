import { createRouter, createWebHistory } from "vue-router";
import { redirectGuestToLogin } from "@/auth";
import { site } from "@/platform/site";
import { embedded } from "@/theme";

// /play is the single product entry. The original quiz remains a first-class
// game, namespaced below it so its established screens keep stable route names.
const BASE = "/play";

const quizRoutes = [
	{ path: "/quizzly/join", name: "Join", component: () => import("@/pages/Join.vue") },
	{ path: "/quizzly/game", name: "Play", component: () => import("@/pages/Play.vue") },
	{ path: "/quizzly/host", name: "Host", component: () => import("@/pages/Host.vue") },
	{
		path: "/host/quizzes",
		alias: "/quizzly/host/quizzes",
		name: "Quizzes",
		component: () => import("@/pages/QuizList.vue"),
	},
	{
		path: "/host/quizzes/:name",
		alias: "/quizzly/host/quizzes/:name",
		name: "QuizEditor",
		component: () => import("@/pages/QuizEditor.vue"),
	},
];

const platformRoutes = [
	{
		path: "/",
		name: "Landing",
		component: () => import("@/platform/discovery/LandingPage.vue"),
	},
	{
		path: "/access",
		name: "Access",
		component: () => import("@/platform/access/AccessPage.vue"),
	},
	{
		path: "/create",
		name: "CreatePack",
		component: () => import("@/platform/access/CreatePack.vue"),
	},
	{
		path: "/room/:session",
		name: "RoomHost",
		component: () => import("@/platform/room/RoomStage.vue"),
	},
	{
		path: "/room-screen/:pin",
		name: "RoomScreen",
		component: () => import("@/platform/room/RoomStage.vue"),
	},
	{
		path: "/explore",
		name: "Catalog",
		component: () => import("@/platform/discovery/CatalogHome.vue"),
	},
	{
		path: "/games/:game",
		name: "GameDetail",
		component: () => import("@/platform/discovery/GameDetail.vue"),
	},
	{
		path: "/join",
		name: "GpJoin",
		component: () => import("@/platform/player/GpJoin.vue"),
	},
	{
		path: "/p/:pin",
		name: "GpPlayer",
		component: () => import("@/platform/player/GpPlayer.vue"),
	},
	{
		path: "/host",
		name: "GpHost",
		component: () => import("@/platform/host/GpHost.vue"),
	},
	{
		path: "/host/dashboard",
		name: "HostDashboard",
		component: () => import("@/platform/host/HostDashboard.vue"),
	},
	{
		path: "/host/content/crowd-compass",
		name: "CrowdPackEditor",
		component: () => import("@/platform/host/PackEditor.vue"),
	},
	{
		path: "/s/:pin/screen",
		name: "GpScreen",
		component: () => import("@/platform/screen/GpScreen.vue"),
	},
];

const routes = [...platformRoutes, ...quizRoutes];

const router = createRouter({
	history: createWebHistory(BASE),
	routes,
});

// Server policy authorizes trial hosting; administration still requires sign-in.
router.beforeEach((to) => {
	if (to.name === "Landing" && embedded) return { name: "Catalog", query: to.query };
	if (["RoomHost", "GpHost", "Host"].includes(to.name) && site.allow_guest_host) return;
	if (
		[
			"RoomHost",
			"GpHost",
			"HostDashboard",
			"CrowdPackEditor",
			"Host",
			"Quizzes",
			"QuizEditor",
		].includes(to.name) &&
		redirectGuestToLogin(`${BASE}${to.fullPath}`)
	) {
		return false;
	}
});

export default router;
