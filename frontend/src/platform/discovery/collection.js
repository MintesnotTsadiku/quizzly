import { locale, t } from "@/i18n";
import { gameAm, accessAm } from "@/i18n/games-am";
// Editorial facets are intentionally separate from the server's playable registry.
// Sharing means one collective answer/score, not several private player identities.
export const featuredKeys = [
	"common-ground",
	"crowd-compass",
	"cuecast",
	"doodle-dash",
	"quiz",
	"sequence-sprint",
];
export const categories = ["All games", "Connect", "Perform", "Create", "Think", "Compete"];
const profiles = {
	"grid-conquest": {
		category: "Compete",
		devices: ["own", "shared", "host"],
		deviceLabel: "Player devices or one shared board",
		people: "2 sides · rotate players or share devices",
		time: "5 min",
		color: "butter",
		kicker: "X and O, together.",
		description:
			"Take turns on one real board. Make a line, block a rival and cheer your side.",
		sample: "Tap the square that completes X’s row.",
		steps: [
			"Join as two sides, X and O, or use one shared host device.",
			"On your turn, tap an empty square. Connect three across, down or diagonally.",
			"A win earns one point. Play up to three boards; the starting side alternates.",
		],
		access: "No speed bonus or countdown. Use touch, mouse, or arrow keys and Enter. X/O shapes and spoken square labels accompany colour. The host can help place a move.",
	},
	"common-ground": {
		category: "Connect",
		devices: ["host"],
		deviceLabel: "Just the host’s device",
		people: "2+ people · split into small groups",
		time: "8 min",
		color: "peach",
		kicker: "A little less scrolling. A lot more talking.",
		description: "Find surprising things you share. No phones, no points — just good company.",
		sample: "Find three small things you all enjoy.",
		steps: [
			"Gather in groups of 2–5. The host reads a playful prompt.",
			"Take turns and find an answer together. Anyone can pass.",
			"Share a surprise, then try something new. Three prompts, no timer.",
		],
		access: "Play seated, speak or gesture, or ask someone to share for you. Passing is always welcome. No reading or device needed for players.",
	},
	"crowd-compass": {
		category: "Connect",
		devices: ["own", "shared"],
		deviceLabel: "Own phones or shared by a group",
		people: "3+ entries · great for a big room",
		time: "15 min",
		color: "lilac",
		kicker: "How well do you know your people?",
		description: "Choose for yourself. Predict the crowd. Discover what makes your room tick.",
		sample: "Your ideal afternoon: outside or inside?",
		steps: [
			"Choose the answer that fits you. Keep it private.",
			"Predict the room’s most popular answer before the reveal.",
			"See the results, collect points and ask someone why.",
		],
		access: "Choices use text and shapes. With shared phones, agree on one group vote and prediction; each device gets one score. A host and internet connection are required.",
	},
	cuecast: {
		category: "Perform",
		devices: ["own"],
		deviceLabel: "Player phones · secret performer prompts",
		people: "4–30 people · teams",
		time: "20 min",
		color: "lime",
		kicker: "Big gestures. Brilliantly bad impressions.",
		description: "Act it out or describe it. Get your team guessing before the buzzer.",
		sample: "Act this out: walking on the moon.",
		steps: [
			"Join teams. The performer gets a secret prompt on their phone.",
			"Act or describe it while your teammates call out guesses.",
			"Mark correct or pass, then rotate performers and cheer each other on.",
		],
		access: "Choose describing instead of acting where needed. Keep the performer’s phone private; a shared controller is not offered for this mode.",
	},
	"doodle-dash": {
		category: "Create",
		devices: ["own"],
		deviceLabel: "Player phones · optional big screen",
		people: "3–100 people · rotating artist",
		time: "20 min",
		color: "rose",
		kicker: "Bad drawings make great memories.",
		description: "One secret word. One brave artist. A room full of wild guesses.",
		sample: "Could you draw a bicycle in 30 seconds?",
		steps: [
			"One artist sees a secret word and draws on their phone.",
			"Everyone else watches and types their guesses.",
			"Reveal the word, celebrate the drawing and switch artists.",
		],
		access: "Touch drawing and typed guesses require vision and dexterity. Pair up with a helper when needed; Common Ground is a lower-device alternative.",
	},
	quiz: {
		category: "Compete",
		devices: ["own", "shared"],
		deviceLabel: "Own phones or shared by a team",
		people: "1+ entries · individuals or groups",
		time: "15 min",
		color: "butter",
		kicker: "A friendly battle of “I knew that!”",
		description: "Bring your favourite facts. Let the whole room have a go.",
		sample: "Which planet is known as the Red Planet?",
		steps: [
			"The host picks a quiz and everyone joins using its code.",
			"Choose an answer before time runs out; fast correct answers score more.",
			"See what you learned, then celebrate the final standings.",
		],
		access: "Text, position and shape distinguish answers. Shared phones get one collective answer and score. Timed reading can be challenging; preview your pack first.",
	},
	"sequence-sprint": {
		category: "Think",
		devices: ["own", "shared"],
		deviceLabel: "Own phones or shared by a team",
		people: "2–100 entries · great in pairs",
		time: "15 min",
		color: "sky",
		kicker: "Put your heads — and the pieces — together.",
		description: "Sort the shuffled cards. Talk it through and find the right order.",
		sample: "Seed → sprout → plant → flower. Can you put it in order?",
		steps: [
			"Look at the shuffled cards on your device.",
			"Move them into order. A shared team agrees on one arrangement.",
			"Lock the sequence, compare with the answer and try the next challenge.",
		],
		access: "Use the reorder buttons as an alternative to dragging. Shared phones get one score. Choose a pack matched to the group’s language and knowledge.",
	},
};
function originalProfileFor(game) {
	return (
		profiles[game?.key] || {
			category: "Think",
			devices: ["own"],
			deviceLabel: "One device per entry",
			people: `${game?.min_players || 1}+ entries`,
			time: `${game?.typical_minutes || 15} min`,
			color: "lilac",
			description: game?.summary,
			steps: [],
			access: "Preview the guide and content for reading, input and equipment requirements.",
		}
	);
}
export function matchesDevice(game, device) {
	return device === "any" || profileFor(game).devices.includes(device);
}

export function profileFor(game) {
	const profile = originalProfileFor(game),
		copy = gameAm[game?.key];
	return locale.value === "am" && copy
		? {
				...profile,
				access: accessAm[game?.key] || t(profile.access),
				description: copy.description,
				steps: copy.steps,
				kicker: copy.title,
				sample: copy.steps[0],
				time: t("{count} min", { count: game?.typical_minutes || 15 }),
				people: profiles[game?.key]
					? t(profile.people)
					: t("{count}+ entries", { count: game?.min_players || 1 }),
			}
		: profile;
}
