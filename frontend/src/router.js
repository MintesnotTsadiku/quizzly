import { createRouter, createWebHistory } from "vue-router";

// One SPA serves two route families: the quiz lives under /quizzly, the
// GatherPlay platform under /play. Both prefixes map to this app's www page,
// so the router base is whichever one the browser arrived on.
const BASE = window.location.pathname.startsWith("/play") ? "/play" : "/quizzly";

const quizRoutes = [
	{ path: "/", redirect: () => (window.session_user === "Guest" ? "/join" : "/host") },
	{ path: "/join", name: "Join", component: () => import("@/pages/Join.vue") },
	{ path: "/play", name: "Play", component: () => import("@/pages/Play.vue") },
	{ path: "/host", name: "Host", component: () => import("@/pages/Host.vue") },
	{
		path: "/host/quizzes",
		name: "Quizzes",
		component: () => import("@/pages/QuizList.vue"),
	},
	{
		path: "/host/quizzes/:name",
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
		path: "/s/:pin/screen",
		name: "GpScreen",
		component: () => import("@/platform/screen/GpScreen.vue"),
	},
];

const routes = BASE === "/play" ? [...platformRoutes, ...quizRoutes] : quizRoutes;

const router = createRouter({
	history: createWebHistory(BASE),
	routes,
});

// Hosting needs a real user; guests would otherwise land on an empty host screen.
router.beforeEach((to) => {
	if (to.name === "GpHost" && window.session_user === "Guest") {
		window.location.href = `/login?redirect-to=${encodeURIComponent("/play/host")}`;
		return false;
	}
});

export default router;
