import { listGames } from "@/platform/session/gp";

// Roadmap entries: the plan allows Coming Soon cards when they communicate the
// roadmap. They render without any host action.
const COMING_SOON = [];

const ICONS = {
	quiz: "M11 2 L20 6.5 V13 C20 17.5 16 21 11 22 C6 21 2 17.5 2 13 V6.5 Z M10 14.5 L15.5 9 L14 7.5 L10 11.5 L8 9.5 L6.5 11 Z",
	cuecast:
		"M12 1 C5.5 1 2 6 2 11 C2 15 4.5 18 8 19.5 L7 23 L11 20.8 C11.3 20.9 11.6 20.9 12 21 C18.5 21 22 16 22 11 C22 6 18.5 1 12 1 Z M8.5 13 A1.6 1.6 0 1 1 8.5 9.8 A1.6 1.6 0 0 1 8.5 13 Z M12 13 A1.6 1.6 0 1 1 12 9.8 A1.6 1.6 0 0 1 12 13 Z M15.5 13 A1.6 1.6 0 1 1 15.5 9.8 A1.6 1.6 0 0 1 15.5 13 Z",
	"crowd-compass":
		"M12 2 A10 10 0 1 0 12 22 A10 10 0 0 0 12 2 Z M12 6 A6 6 0 1 1 12 18 A6 6 0 0 1 12 6 Z M12 9 A3 3 0 1 0 12 15 A3 3 0 0 0 12 9 Z",
};

export function gameIcon(key) {
	return ICONS[key] || ICONS.quiz;
}

// How-to guides keyed by the backend manifest key. Copy lives here until a
// module count makes Desk records worth it; the shape matches the spec's guide
// manifest so moving it later is mechanical.
const GUIDES = {
	"doodle-dash": {
		contentKey: "pack",
		whyGame: "One person receives a secret word and draws it live. Everyone else races to recognize the sketch; quick correct guesses reward both guesser and artist.",
		howTo: ["The artist privately receives a word.","Draw on the phone canvas without letters or numbers.","Everyone else types guesses while the picture appears live.","Correct guessers score more when they are fast.","Rotate artists and finish on the individual podium."],
		hostDoes: "Chooses a pack and timer, watches the live canvas, advances or pauses the presentation, and can skip an unsuitable round.",
		playerSees: "The artist gets a touch canvas and secret prompt. Guessers see the same canvas with a private guess box and immediate acknowledgement.",
		roomSees: "A clean live canvas, artist name, timer, answer reveal, and standings—never the secret word while drawing is open.",
		scoring: "Correct guessers earn 500–1,000 points by server receipt time. The artist earns 50 points per correct guesser, capped at 500.",
		setup: "Use one projector and one phone per player. Landscape orientation gives the artist more drawing room.",
		accessibility: "Large touch targets, keyboard-ready guess entry, numeric timers, high contrast ink, and a non-colour-dependent reveal.",
		demos: [
			{demo_key:"doodle-dash-church-bible",title:"Symbols and Stories Sketch-Off",blurb:"Familiar Bible symbols and story objects.",audience:"Church / Bible"},
			{demo_key:"doodle-dash-family-general",title:"Family Doodle Box",blurb:"Friendly objects for children and grown-ups.",audience:"Child / Family"},
			{demo_key:"doodle-dash-big-room",title:"Sketch the Room",blurb:"Big-screen prompts for a lively assembly.",audience:"General Assembly"},
		],
	},
	"crowd-compass": {
		contentKey: "pack",
		whyGame:
			"First answer for yourself. Then, before the results appear, predict what everyone else chose. The people who read the room most accurately climb the leaderboard.",
		howTo: [
			"Vote for the choice that fits you — the room cannot see the distribution yet.",
			"Predict which choice the whole room picked most.",
			"Estimate that winning choice's percentage for an extra accuracy bonus.",
			"Watch the distribution reveal and see who read the room best.",
			"Climb the individual or team-average standings across the pack.",
		],
		hostDoes:
			"Picks a pack or opens a blank room, sets timers and scoring options, balances teams, writes live prompts, and can void a resolved prompt without rewriting score history.",
		playerSees:
			"Shape-coloured vote and prediction controls, an optional percentage slider, a private points result, and the standings. Ranked packs ask for distinct first and second choices.",
		roomSees:
			"The prompt and participation counts while voting is open, then an animated distribution and plurality crown only after predictions lock.",
		scoring:
			"+500 for predicting a plurality winner, +100 when your vote matches the room, +100 for matching your team in team mode, plus +300 / +150 / +50 for a correct prediction estimated within 3 / 7 / 12 percentage points.",
		setup: "Use one projector or TV and one phone per player. Choose individual or team mode; a host can also run an entirely live, pack-free room.",
		accessibility:
			"Every choice combines shape, position, and text rather than colour alone; controls are keyboard labelled, countdowns are numeric, and reduced motion is respected.",
		demos: [
			{
				demo_key: "crowd-compass-church-bible",
				title: "Our Community Compass",
				blurb: "Discussion-friendly preferences that get a church community talking.",
				audience: "Church / Bible",
			},
			{
				demo_key: "crowd-compass-family-general",
				title: "This or That Together",
				blurb: "Classic this-or-that choices the whole family can argue about.",
				audience: "Child / Family",
			},
			{
				demo_key: "crowd-compass-big-room",
				title: "Read the Room 50",
				blurb: "Simple, surprising icebreakers tuned for a big assembly.",
				audience: "General Assembly",
				video: "/assets/quizzly/videos/gatherplay/crowd-compass-read-room-50.mp4",
				poster: "/assets/quizzly/videos/gatherplay/crowd-compass-read-room-50-poster.jpg",
			},
		],
	},
	cuecast: {
		contentKey: "deck",
		whyGame:
			"One player performs a secret prompt while their team races to guess it. Every correct answer beats the clock, earns a point, and moves the team closer to the podium.",
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
		scoring:
			"+1 per solved prompt. Host can invalidate one after the turn (−1). Ties go to sudden-death turns.",
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
		hostUrl: "/play/quizzly/host",
		contentKey: "quiz",
		whyGame:
			"Answer correctly before the clock runs out. Faster answers and winning streaks earn more points, turning every question into a race for the podium.",
		howTo: [
			"Join with the PIN on the big screen and pick a face.",
			"Read each question during the read-time countdown.",
			"Tap one of the four shapes before time runs out.",
			"Faster answers score more; streaks stack bonuses.",
			"Finish on the podium.",
		],
		hostDoes:
			"Picks a quiz, locks the lobby, drives between questions or lets auto-advance run.",
		playerSees: "The question, four coloured shapes, then your result, points and rank.",
		roomSees: "Questions, live answer counts, the distribution chart and the top five.",
		scoring:
			"500–1000 base points by speed, +50 per streak step up to 250, times the multiplier.",
		setup: "Projector plus phones. Works from four people to a full hall.",
		accessibility:
			"Shapes carry meaning beyond colour, and every screen respects reduced motion.",
		demos: [
			{
				demo_key: "quiz-church-bible",
				title: "Bible Foundations Live",
				blurb: "Creation, Exodus, Jesus’ ministry, Acts, and Bible foundations.",
				audience: "Church / Bible",
			},
			{
				demo_key: "quiz-family-general",
				title: "Family Fun Mix",
				blurb: "Animals, colours, numbers, riddles, and everyday science.",
				audience: "Child / Family",
			},
			{
				demo_key: "quiz-big-room",
				title: "The Big Room Challenge",
				blurb: "Geography, science, inventions, and culture for a full hall.",
				audience: "General Assembly",
			},
		],
	},
};

const ROUND_GUIDES = {
	bluffline:["Curious Bible Context","Silly Word Museum","Unexpected Facts"],
	"sequence-sprint":["Bible Timeline Relay","Put It in Order","Process and History Race"],
	"picture-peek":["Symbols, Places, and Scenes","What Is Hiding?","World in Focus"],
	"sound-snap":["Sounds of the Story","Home and Animal Sounds","Soundscape Challenge"],
	"caption-clash":["Modern Parable Moments","Family Photo Giggles","Conference Caption Cup"],
	"story-loom":["Journey of Courage","The Bedtime Adventure Machine","Fifty Voices, One City"],
	"signal-spectrum":["Journey and Wisdom Scales","Silly Family Scales","Know Your Room"],
	"memory-mosaic":["Objects and Journeys Memory","Toy Room Memory","Auditorium Snapshot"],
	"common-thread":["Threads Through Scripture","Family Connection Box","Big Room Connections"],
	"escape-together":["The Lamp and the Locked Library","The Friendly Castle Escape","The Assembly Code"],
	"bracket-bash":["Bible Story Bracket","Family Favorites Cup","Big Room Championship"],
	"closest-call":["Bible Numbers Duel","Family Guess-Off","Assembly Estimation Arena"],
	"phrase-forge":["Words of Encouragement","Silly Sentence Factory","Conference Phrase Forge"],
	"seek-and-show":["Service and Symbols Hunt","Home or Hall Treasure Hunt","Venue Team Quest"],
	"one-word-chorus":["People, Places, and Symbols","Animals and Everyday Things","One Word, Big Room"],
};
for (const [key,titles] of Object.entries(ROUND_GUIDES)) {
	const title=key.split("-").map(w=>w[0].toUpperCase()+w.slice(1)).join(" ");
	GUIDES[key]={contentKey:"pack",whyGame:`${title} turns one clear room challenge into timed rounds, private responses, shared reveals, and a live race up the scoreboard.`,howTo:["Join the room from your phone.","Read the shared prompt and submit privately before time runs out.","Watch the room reveal the result.","Score through the game's own challenge.","Repeat until the final podium."],hostDoes:"Chooses a themed pack and timing, starts the room, pauses or advances presentation beats, and keeps the room moving.",playerSees:"A private, accessible response control suited to this game, a locked confirmation, reveal, score, and rank.",roomSees:"The current challenge, response count, timer, reveal, standings, and final podium.",scoring:"The server validates every response and applies this game's correctness, proximity, ordering, or contribution scoring.",setup:"One shared screen plus a phone per player. Works in a family room or a large assembly.",accessibility:"Text labels accompany every control; keyboard input, numeric timers, reduced motion, and high contrast are supported.",demos:titles.map((demoTitle,index)=>({demo_key:`${key}-${["church-bible","family-general","big-room"][index]}`,title:demoTitle,blurb:`A ready-to-play ${demoTitle} experience.`,audience:["Church / Bible","Child / Family","General Assembly"][index]}))};
}

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
