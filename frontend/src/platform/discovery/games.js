import { listGames } from "@/platform/session/gp";

// Roadmap entries: the plan allows Coming Soon cards when they communicate the
// roadmap. They render without any host action.
const COMING_SOON = [
	{
		key: "crowd-compass",
		title: "Crowd Compass",
		summary: "Vote, predict the room's answer, and see who reads the crowd best.",
		min_players: 3,
		max_players: null,
		recommended_players: "15–100+",
		typical_minutes: 15,
		interaction_tags: ["voting", "prediction"],
		status: "Coming Soon",
	},
	{
		key: "doodle-dash",
		title: "Doodle Dash",
		summary: "One artist draws a secret word while everyone else races to guess it.",
		min_players: 3,
		max_players: 100,
		recommended_players: "8–40",
		typical_minutes: 20,
		interaction_tags: ["drawing", "guessing"],
		status: "Coming Soon",
	},
];

const ICONS = {
	quiz:
		"M11 2 L20 6.5 V13 C20 17.5 16 21 11 22 C6 21 2 17.5 2 13 V6.5 Z M10 14.5 L15.5 9 L14 7.5 L10 11.5 L8 9.5 L6.5 11 Z",
	cuecast:
		"M12 1 C5.5 1 2 6 2 11 C2 15 4.5 18 8 19.5 L7 23 L11 20.8 C11.3 20.9 11.6 20.9 12 21 C18.5 21 22 16 22 11 C22 6 18.5 1 12 1 Z M8.5 13 A1.6 1.6 0 1 1 8.5 9.8 A1.6 1.6 0 0 1 8.5 13 Z M12 13 A1.6 1.6 0 1 1 12 9.8 A1.6 1.6 0 0 1 12 13 Z M15.5 13 A1.6 1.6 0 1 1 15.5 9.8 A1.6 1.6 0 0 1 15.5 13 Z",
};

export function gameIcon(key) {
	return ICONS[key] || ICONS.quiz;
}

// How-to guides keyed by the backend manifest key. Copy lives here until a
// module count makes Desk records worth it; the shape matches the spec's guide
// manifest so moving it later is mechanical.
const GUIDES = {
	cuecast: {
		howTo: [
			"Split into teams and pick who performs first.",
			"The performer sees a secret prompt on their phone only.",
			"Act it out (or describe it, in Describe mode) — no letters, no spelling.",
			"Tap Correct for every solved prompt, Pass to skip one.",
			"Beat the buzzer, watch the scoreboard move, and win the podium.",
		],
		hostDoes:
			"Picks a deck and round length, balances teams, starts each turn, and can skip or reassign a stuck performer.",
		playerSees:
			"The performer privately sees the current prompt with Correct and Pass controls; everyone else watches the stage with a live solved counter.",
		roomSees:
			"Team vs team, the timer draining, prompts solved climbing — never the word itself, until the review reveals what was played.",
		scoring: "+1 per solved prompt. Host can invalidate one after the turn (−1). Ties go to sudden-death turns.",
		setup: "One projector or TV for the room; phones for everyone else. Teams gather where they can see the stage.",
		accessibility:
			"Describe mode replaces acting for players who prefer it; timers are colour-independent and every control has a text label.",
		demos: [
			{
				demo_key: "cuecast-church-bible",
				title: "Bible Characters in Motion",
				blurb: "Moses, David, Jonah and friends — respectfully phrased scenes.",
				audience: "Church / Bible",
			},
			{
				demo_key: "cuecast-family-general",
				title: "Family Action Basket",
				blurb: "Sleepy elephants, birthday surprises and everyday silliness.",
				audience: "Child / Family",
			},
			{
				demo_key: "cuecast-big-room",
				title: "Big Room Charades",
				blurb: "Airport chaos, coffee rushes and stadium waves for ~50 people.",
				audience: "General Assembly",
			},
		],
	},
	quiz: {
		howTo: [
			"Join with the PIN on the big screen and pick a face.",
			"Read each question during the read-time countdown.",
			"Tap one of the four shapes before time runs out.",
			"Faster answers score more; streaks stack bonuses.",
			"Finish on the podium.",
		],
		hostDoes: "Picks a quiz, locks the lobby, drives between questions or lets auto-advance run.",
		playerSees: "The question, four coloured shapes, then your result, points and rank.",
		roomSees: "Questions, live answer counts, the distribution chart and the top five.",
		scoring: "500–1000 base points by speed, +50 per streak step up to 250, times the multiplier.",
		setup: "Projector plus phones. Works from four people to a full hall.",
		accessibility: "Shapes carry meaning beyond colour, and every screen respects reduced motion.",
	},
};

export function guideFor(key) {
	return GUIDES[key] || GUIDES.quiz;
}

export async function catalogGames() {
	const available = await listGames();
	const soon = COMING_SOON.filter(
		(c) => !available.some((a) => a.title.toLowerCase() === c.title.toLowerCase())
	);
	return [...available, ...soon];
}
