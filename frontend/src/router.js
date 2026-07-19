import { createRouter, createWebHistory } from "vue-router";

const routes = [
	{ path: "/", redirect: "/join" },
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

export default createRouter({
	history: createWebHistory("/quizzly"),
	routes,
});
