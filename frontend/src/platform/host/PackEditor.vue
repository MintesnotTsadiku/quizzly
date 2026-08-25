<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<HostBar />
		<div class="mx-auto w-full max-w-3xl flex-1 px-5 py-10 sm:px-8">
			<RouterLink
				class="font-mono text-xs uppercase tracking-[0.22em] text-paper/40 transition hover:text-paper"
				:to="{ name: 'GpHost' }"
			>
				← Host console
			</RouterLink>

			<!-- List -->
			<template v-if="!editing">
				<h1 class="mt-6 font-display text-4xl font-extrabold text-paper">Crowd Compass packs</h1>
				<button class="ctl ctl-go mt-6" @click="startNew">New pack</button>
				<div class="mt-8 flex flex-col gap-3">
					<button
						v-for="pack in packs"
						:key="pack.name"
						class="group flex items-center gap-4 rounded-2xl border border-haze bg-dusk px-5 py-4 text-left transition hover:border-ember"
						@click="edit(pack)"
					>
						<span class="flex-1">
							<span class="font-display text-xl font-bold text-paper">{{ pack.title }}</span>
							<span class="ml-3 font-mono text-xs text-paper/40">
								{{ pack.prompt_count }} prompts{{ Number(pack.ranked) ? " · ranked" : "" }}{{ Number(pack.is_demo) ? " · demo" : "" }}
							</span>
						</span>
						<span class="text-paper/25 transition group-hover:text-alert">→</span>
					</button>
					<p v-if="!packs.length && loaded" class="text-paper/50">No packs yet — write your first one.</p>
				</div>
			</template>

			<!-- Editor -->
			<template v-else>
				<h1 class="mt-6 font-display text-4xl font-extrabold text-paper">
					{{ doc.name ? "Edit pack" : "New pack" }}
				</h1>
				<div class="mt-8 flex flex-col gap-6">
					<p
						v-if="Number(doc.is_demo)"
						class="rounded-2xl border border-haze bg-dusk px-5 py-4 text-sm text-paper/60"
					>
						Demo packs are read-only. Duplicate one to make your own version.
					</p>
					<label class="flex flex-col gap-2">
						<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">Title</span>
						<input v-model="doc.title" class="field text-lg" placeholder="Pack title" maxlength="140" :disabled="Number(doc.is_demo)" />
					</label>
					<label class="flex items-center gap-3 text-paper/70">
						<input type="checkbox" v-model="doc.ranked" class="size-4 accent-[rgb(var(--accent))]" :disabled="Number(doc.is_demo)" />
						Ranked — players pick a first and second choice (weighted 2/1)
					</label>

					<div class="flex flex-col gap-4">
						<span class="font-mono text-[11px] uppercase tracking-[0.22em] text-paper/45">
							Prompts · {{ doc.prompts.length }}
						</span>
						<div
							v-for="(prompt, index) in doc.prompts"
							:key="index"
							class="rounded-2xl border border-haze bg-dusk p-5"
						>
							<div class="flex items-start justify-between gap-3">
								<span class="font-mono text-xs tabular-nums text-paper/35">
									{{ String(index + 1).padStart(2, "0") }}
								</span>
								<button
									class="rounded-full border border-haze px-3 py-1 text-xs text-paper/50 transition hover:border-alert hover:text-alert"
									@click="removePrompt(index)"
									:disabled="Number(doc.is_demo)"
								>
									Remove
								</button>
							</div>
							<textarea
								v-model="prompt.prompt_text"
								class="field mt-3"
								rows="2"
								placeholder="Ask the room something…"
								maxlength="200"
								:disabled="Number(doc.is_demo)"
							/>
							<div class="mt-3 grid grid-cols-2 gap-3">
								<input
									v-for="n in 4"
									:key="n"
									v-model="prompt[`choice_${n}`]"
									class="field"
									:class="n > 2 ? 'opacity-80' : ''"
									:placeholder="`Choice ${n}${n <= 2 ? ' *' : ''}`"
									maxlength="60"
									:disabled="Number(doc.is_demo)"
								/>
							</div>
							<div class="mt-3 grid grid-cols-2 gap-2" aria-label="Player choice preview">
								<span
									v-for="(choice, choiceIndex) in promptChoices(prompt)"
									:key="choiceIndex"
									class="rounded-2xl px-3 py-2 text-center font-display text-sm font-bold text-sunk"
									:class="choicePreviewClass(choiceIndex)"
								>
									{{ choice }}
								</span>
							</div>
						</div>
						<button v-if="!Number(doc.is_demo)" class="ctl w-fit" @click="addPrompt">+ Add prompt</button>
					</div>

					<p v-if="error" class="text-alert">{{ error }}</p>
					<div class="flex gap-3">
						<button v-if="!Number(doc.is_demo)" class="ctl ctl-go" :disabled="saving" @click="save">
							{{ saving ? "Saving…" : doc.name ? "Save pack" : "Create pack" }}
						</button>
						<button v-if="doc.name && !Number(doc.is_demo)" class="ctl ctl-danger" :disabled="saving" @click="removePack">
							Delete pack
						</button>
						<button class="ctl" @click="editing = null">Back</button>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { call, readError } from "@/api";
import { confirm } from "@/confirm";
import HostBar from "@/components/HostBar.vue";

const packs = ref([]);
const loaded = ref(false);
const editing = ref(null);
const doc = ref(blank());
const saving = ref(false);
const error = ref("");

function blank() {
	return { doctype: "GP Crowd Pack", title: "", ranked: false, prompts: [blankPrompt()] };
}

function blankPrompt() {
	return { prompt_text: "", choice_1: "", choice_2: "", choice_3: "", choice_4: "" };
}

onMounted(load);

async function load() {
	try {
		const rows = await call("frappe.client.get_list", {
			doctype: "GP Crowd Pack",
			fields: ["name", "title", "ranked", "is_demo"],
			limit_page_length: 0,
			order_by: "modified desc",
		});
		for (const row of rows) {
			const prompts = await call("frappe.client.get_list", {
				doctype: "GP Crowd Prompt",
				filters: { parenttype: "GP Crowd Pack", parent: row.name },
				limit_page_length: 0,
			});
			row.prompt_count = prompts.length;
		}
		packs.value = rows;
		loaded.value = true;
	} catch (e) {
		error.value = readError(e);
	}
}

async function edit(pack) {
	error.value = "";
	try {
		const loadedDoc = await call("frappe.client.get", { doctype: "GP Crowd Pack", name: pack.name });
		doc.value = loadedDoc.message ?? loadedDoc;
		editing.value = pack.name;
	} catch (e) {
		error.value = readError(e);
	}
}

function startNew() {
	doc.value = blank();
	editing.value = "new";
}

function addPrompt() {
	doc.value.prompts.push(blankPrompt());
}

function removePrompt(index) {
	doc.value.prompts.splice(index, 1);
}

function promptChoices(prompt) {
	return [prompt.choice_1, prompt.choice_2, prompt.choice_3, prompt.choice_4].filter(Boolean);
}

function choicePreviewClass(index) {
	return ["bg-ember", "bg-lagoon", "bg-gold", "bg-orchid"][index] || "bg-haze";
}

async function save() {
	error.value = "";
	saving.value = true;
	try {
		// the framework keeps an idx it is given: rows are sent back without one so
		// order always follows this screen
		const payload = {
			doctype: "GP Crowd Pack",
			name: doc.value.name,
			title: doc.value.title,
			ranked: doc.value.ranked ? 1 : 0,
			prompts: doc.value.prompts.map((p, index) => ({
				prompt_text: p.prompt_text,
				choice_1: p.choice_1,
				choice_2: p.choice_2,
				choice_3: p.choice_3,
				choice_4: p.choice_4,
				idx: index + 1,
			})),
		};
		const method = doc.value.name ? "frappe.client.save" : "frappe.client.insert";
		await call(method, { doc: payload });
		editing.value = null;
		await load();
	} catch (e) {
		error.value = readError(e);
	} finally {
		saving.value = false;
	}
}

async function removePack() {
	if (!(await confirm(`Delete ${doc.value.title}?`, { action: "Delete", danger: true }))) return;
	saving.value = true;
	error.value = "";
	try {
		await call("frappe.client.delete", { doctype: "GP Crowd Pack", name: doc.value.name });
		editing.value = null;
		await load();
	} catch (e) {
		error.value = readError(e);
	} finally {
		saving.value = false;
	}
}
</script>
