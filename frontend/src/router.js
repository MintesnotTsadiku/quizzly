import { createRouter, createWebHistory } from "vue-router";

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

// Hosting needs a real user; guests would otherwise land on an empty host screen.
router.beforeEach((to) => {
	if (
		["GpHost", "CrowdPackEditor", "Host", "Quizzes", "QuizEditor"].includes(to.name) &&
		window.session_user === "Guest"
	) {
		window.location.href = `/login?redirect-to=${encodeURIComponent(`${BASE}${to.fullPath}`)}`;
		return false;
	}
});

export default router;
