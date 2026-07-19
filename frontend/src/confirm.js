import { ref } from "vue";

// One dialog lives in App.vue; anything that needs a yes/no awaits this instead of
// window.confirm, which renders the browser's own chrome over the projector.
export const pendingConfirm = ref(null);

export function confirm(message, { action = "Confirm", danger = false } = {}) {
	return new Promise((resolve) => {
		pendingConfirm.value = {
			message,
			action,
			danger,
			settle(answer) {
				pendingConfirm.value = null;
				resolve(answer);
			},
		};
	});
}
