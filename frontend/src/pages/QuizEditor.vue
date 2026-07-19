<template>
	<div class="flex h-full flex-col overflow-y-auto bg-night">
		<div class="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 p-8">
			<div class="flex items-end justify-between gap-4">
				<div class="min-w-0 flex-1">
					<p class="font-mono text-[11px] uppercase tracking-[0.28em] text-gold">
						{{ isNew ? "New quiz" : "Editing" }}
					</p>
					<input
						v-model="title"
						class="field mt-2 font-display text-3xl font-extrabold"
						placeholder="Quiz title"
					/>
				</div>
				<div class="flex shrink-0 items-center gap-2">
					<span v-if="saved" class="font-mono text-xs text-lagoon">Saved</span>
					<button class="ctl ctl-go" :disabled="saving" @click="save">
						{{ saving ? "Saving…" : "Save" }}
					</button>
				</div>
			</div>

			<div class="flex flex-wrap items-center gap-4">
				<label class="flex items-center gap-2 whitespace-nowrap font-mono text-xs text-paper/50">
					Seconds per question
					<input v-model.number="defaultTimeLimit" type="number" class="field w-20" />
				</label>
				<input
					v-model="description"
					class="field flex-1"
					placeholder="Description (optional)"
				/>
			</div>

			<p v-if="error" class="text-ember">{{ error }}</p>

			<div
				v-for="(question, index) in questions"
				:key="index"
				class="flex flex-col gap-4 rounded-2xl border border-haze bg-dusk p-5"
			>
				<div class="flex items-center gap-3">
					<span class="font-mono text-xs uppercase tracking-[0.2em] text-paper/40">
						Question {{ index + 1 }}
					</span>
					<span class="flex-1" />
					<button class="ctl" :disabled="index === 0" @click="move(index, -1)">↑</button>
					<button
						class="ctl"
						:disabled="index === questions.length - 1"
						@click="move(index, 1)"
					>
						↓
					</button>
					<button class="ctl" @click="questions.splice(index, 1)">Remove</button>
				</div>

				<textarea
					v-model="question.question_text"
					rows="2"
					class="field font-display text-xl font-bold"
					placeholder="What do you want to ask?"
				/>

				<div class="flex items-center gap-4">
					<img
						v-if="question.image"
						:src="question.image"
						alt=""
						class="h-24 rounded-xl object-contain"
					/>
					<FileUploader
						file-types="image/*"
						:upload-args="{ private: 0, optimize: true }"
						@success="(file) => (question.image = file.file_url)"
					>
						<template #default="{ openFileSelector, uploading, progress }">
							<button class="ctl" @click="openFileSelector">
								{{
									uploading
										? `Uploading ${progress}%`
										: question.image
											? "Replace image"
											: "Add image"
								}}
							</button>
						</template>
					</FileUploader>
					<button v-if="question.image" class="ctl" @click="question.image = null">
						Remove image
					</button>
				</div>

				<div class="grid gap-2 sm:grid-cols-2">
					<label
						v-for="option in [1, 2, 3, 4]"
						:key="option"
						class="flex items-center gap-3 rounded-xl px-3 py-2"
						:class="SHAPES[option - 1].fill"
					>
						<input
							v-model="question.correct_option"
							type="radio"
							:value="String(option)"
							:name="`correct-${index}`"
							:aria-label="`Option ${option} is correct`"
							class="h-5 w-5 shrink-0 appearance-none rounded-full border-2 border-night/40 bg-transparent checked:border-[6px] checked:border-night"
						/>
						<input
							v-model="question[`option_${option}`]"
							class="w-full border-0 bg-transparent font-display text-lg font-bold text-night placeholder:text-night/40 focus:outline-none"
							:placeholder="`Answer ${option}`"
						/>
					</label>
				</div>

				<div class="flex flex-wrap gap-4">
					<label class="flex items-center gap-2 whitespace-nowrap font-mono text-xs text-paper/50">
						Time limit
						<input
							v-model.number="question.time_limit"
							type="number"
							class="field w-20"
							:placeholder="String(defaultTimeLimit)"
						/>
					</label>
					<label class="flex items-center gap-2 whitespace-nowrap font-mono text-xs text-paper/50">
						Points
						<select v-model="question.points_multiplier" class="field w-32">
							<option value="0">No points</option>
							<option value="1">Normal</option>
							<option value="2">Double</option>
						</select>
					</label>
				</div>
			</div>

			<div class="flex items-center gap-3">
				<button class="ctl" @click="questions.push(blankQuestion())">Add question</button>
				<RouterLink class="font-mono text-xs text-paper/40 hover:text-paper" to="/host/quizzes">
					← All quizzes
				</RouterLink>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { FileUploader } from "frappe-ui";
import { call } from "@/api";
import { SHAPES } from "@/game";

const route = useRoute();
const router = useRouter();

const isNew = computed(() => route.params.name === "new");
const quizName = ref(isNew.value ? null : route.params.name);
const title = ref("");
const description = ref("");
const defaultTimeLimit = ref(20);
const questions = ref([]);
const saving = ref(false);
const saved = ref(false);
const error = ref("");

watch([title, description, defaultTimeLimit, questions], () => (saved.value = false), {
	deep: true,
});

onMounted(async () => {
	if (isNew.value) {
		questions.value = [blankQuestion()];
		return;
	}
	try {
		const quiz = await call("quizzly.api.get_quiz", { quiz: quizName.value });
		title.value = quiz.title;
		description.value = quiz.description || "";
		defaultTimeLimit.value = quiz.default_time_limit || 20;
		// an unset Int comes back as 0; the field should read as empty, not as zero seconds
		questions.value = quiz.questions.map((question) => ({
			...question,
			time_limit: question.time_limit || null,
		}));
		saved.value = true;
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	}
});

function blankQuestion() {
	return {
		question_text: "",
		image: null,
		option_1: "",
		option_2: "",
		option_3: "",
		option_4: "",
		correct_option: "1",
		time_limit: null,
		points_multiplier: "1",
	};
}

function move(index, step) {
	const [question] = questions.value.splice(index, 1);
	questions.value.splice(index + step, 0, question);
}

async function save() {
	error.value = "";
	saving.value = true;
	try {
		const result = await call("quizzly.api.save_quiz", {
			quiz: quizName.value,
			title: title.value,
			description: description.value,
			default_time_limit: defaultTimeLimit.value,
			questions: JSON.stringify(questions.value),
		});
		saved.value = true;
		if (isNew.value) router.replace(`/host/quizzes/${result.quiz}`);
		quizName.value = result.quiz;
	} catch (e) {
		error.value = e.messages?.[0] || e.message;
	} finally {
		saving.value = false;
	}
}
</script>
