<template>
	<router-view />
	<ConfirmDialog />
	<InstallPrompt />
</template>

<script setup>
import InstallPrompt from "@/platform/InstallPrompt.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
</script>
