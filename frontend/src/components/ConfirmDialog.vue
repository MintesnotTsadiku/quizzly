<!-- Native <dialog>: focus trap, Esc, and backdrop come free. -->
<template>
	<dialog
		ref="dialog"
		class="qz-dialog w-[min(26rem,calc(100vw-2rem))] rounded-2xl border border-haze bg-dusk p-6 text-paper"
		@cancel.prevent="pendingConfirm?.settle(false)"
		@click.self="pendingConfirm?.settle(false)"
	>
		<p class="text-lg font-medium">{{ pendingConfirm?.message }}</p>
		<div class="mt-6 flex justify-end gap-3">
			<button class="ctl" @click="pendingConfirm.settle(false)">{{ $t("Cancel") }}</button>
			<button
				ref="confirmButton"
				class="ctl"
				:class="pendingConfirm?.danger ? 'ctl-danger' : 'ctl-go'"
				@click="pendingConfirm.settle(true)"
			>
				{{ pendingConfirm?.action }}
			</button>
		</div>
	</dialog>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import { pendingConfirm } from "@/confirm";

const dialog = ref(null);
const confirmButton = ref(null);

watch(pendingConfirm, async (request) => {
	if (!request) return dialog.value.close();
	dialog.value.showModal();
	await nextTick();
	confirmButton.value?.focus();
});
</script>
