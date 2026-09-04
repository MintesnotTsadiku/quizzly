const ASSET_ROOT = "/assets/quizzly/images/games";

// Each game may ship two complementary visuals: the hero teaches the general
// loop, while the example follows one concrete round from prompt to score.
const GAME_VISUALS = {
	"doodle-dash": {
		hero: `${ASSET_ROOT}/doodle-dash/how-to.webp`,
		example: `${ASSET_ROOT}/doodle-dash/example-round.webp`,
		exampleAlt:
			"Worked Doodle Dash round using the word rocket: three correct guesses at 12, 24, and 48 seconds earn 900, 800, and 600 points; the artist earns a 150-point bonus.",
		summary:
			"One player draws a private word while everyone else watches the shared screen and guesses from their phones.",
		steps: [
			{
				title: "Artist",
				detail: "See the private word and draw it without using letters or numbers.",
			},
			{
				title: "Big screen",
				detail: "Every stroke appears live for the room while the timer runs.",
			},
			{
				title: "Guessers",
				detail: "Keep submitting guesses; faster correct answers earn more points.",
			},
		],
		exampleSummary:
			"In this 60-second example, faster correct guesses earn more points and the artist earns 50 points for every player who solves the drawing.",
		exampleSteps: [
			"Hana privately receives ROCKET and draws it without letters or numbers.",
			"Mimi, Dawit, and Tesfaye solve it after 12, 24, and 48 seconds.",
			"They earn 900, 800, and 600 points; Hana earns a 150-point artist bonus.",
		],
	},
	"crowd-compass": {
		hero: `${ASSET_ROOT}/crowd-compass/how-to.webp`,
		example: `${ASSET_ROOT}/crowd-compass/example-round.webp`,
		exampleAlt:
			"Worked default-mode Crowd Compass round with 20 players: popcorn wins 50 percent of the vote and Mimi earns 500 points for predicting popcorn plus 100 because her own vote matches the room, for 600 total.",
		summary:
			"First choose honestly for yourself. Then predict the room's most popular answer before any results are revealed; percentage estimation is an optional host setting.",
		steps: [
			{
				title: "Vote for you",
				detail: "Privately choose the answer that fits you while the room's distribution stays hidden.",
			},
			{
				title: "Predict the room",
				detail: "Pick the answer you think will be most popular; optionally estimate its percentage.",
			},
			{
				title: "Reveal and score",
				detail: "See the full distribution; accurate predictions and percentage estimates earn points.",
			},
		],
		exampleSummary:
			"This default-mode example separates Mimi's honest personal vote from her prediction. The result stays hidden until the timed voting and prediction stages end.",
		exampleSteps: [
			"Mimi chooses popcorn for herself, then separately predicts that popcorn will be the room's most popular snack.",
			"Among 20 players, popcorn receives 10 votes, so its actual share is 50 percent.",
			"Mimi earns 500 points for the prediction and 100 because her own vote matches the room: 600 total.",
		],
	},
	cuecast: {
		hero: `${ASSET_ROOT}/cuecast/how-to.webp`,
		example: `${ASSET_ROOT}/cuecast/example-round.webp`,
		exampleAlt: "Worked CueCast turn: Hana performs three prompts for Team Blue Nile, solves two and passes one, so the team earns two points.",
		summary: "One performer sees each secret prompt, acts or describes it for their team, and controls Correct or Pass while the room watches the timer.",
		steps: [
			{ title: "Performer", detail: "Privately see each prompt and perform it without spelling the answer." },
			{ title: "Team", detail: "Guess aloud while the shared screen shows only the timer and solved count." },
			{ title: "Keep moving", detail: "The performer taps Correct for one team point or Pass for zero, then receives the next prompt." },
		],
		exampleSummary: "Hana solves two prompts during Team Blue Nile's turn. Only solved prompts add to the team score.",
		exampleSteps: [
			"Hana privately receives BRUSHING YOUR TEETH and performs it for her team.",
			"She marks that prompt Correct, passes SLEEPY ELEPHANT, and solves BIRTHDAY SURPRISE.",
			"Two solved prompts earn Team Blue Nile two points; the passed prompt earns zero.",
		],
	},
	quiz: {
		hero: `${ASSET_ROOT}/quiz/how-to.webp`,
		example: `${ASSET_ROOT}/quiz/example-round.webp`,
		exampleAlt: "Worked Quizzly question: Hana answers Mars after four seconds of a twenty-second window and earns 900 speed points plus a 50-point streak bonus, for 950 total.",
		summary: "Read each question, choose one of four labelled shapes, and earn more for answering correctly, quickly, and consistently.",
		steps: [
			{ title: "Read", detail: "Read the question and all four answers during the countdown." },
			{ title: "Answer", detail: "Tap one labelled shape on your phone before the answer window closes." },
			{ title: "Reveal and score", detail: "Correct answers earn 500–1,000 by speed, with up to 250 extra for a streak." },
		],
		exampleSummary: "The speed score uses elapsed time within the answer window, then adds the new streak step.",
		exampleSteps: [
			"The question asks which planet is known as the Red Planet; Hana selects MARS after 4 of 20 seconds.",
			"Her correct response earns a 900-point speed base.",
			"Her streak increases from one to two and adds 50, for 950 total.",
		],
	},
	bluffline: {
		hero: `${ASSET_ROOT}/bluffline/how-to.webp`,
		example: `${ASSET_ROOT}/bluffline/example-round.webp`,
		exampleAlt: "Worked Bluffline round: Mimi's Festival bluff fools two players for 1,250 points, and she finds the true answer Flamboyance for another 1,000, earning 2,250 total.",
		summary: "Invent a believable false answer, then vote among anonymous answers to find the truth while other players try to spot your bluff.",
		steps: [
			{ title: "Write a bluff", detail: "Submit one concise false answer that could plausibly be true." },
			{ title: "Vote", detail: "Choose from the anonymous ballot; your own response is excluded." },
			{ title: "Reveal and score", detail: "Earn 1,000 for finding the truth; your bluff earns 250 plus 500 per vote." },
		],
		exampleSummary: "Mimi scores both ways: other players believe her bluff, and she identifies the real answer.",
		exampleSteps: [
			"For the flamingo-group prompt, Mimi submits the bluff FESTIVAL.",
			"Mimi votes for the truth, FLAMBOYANCE, while two other players choose FESTIVAL.",
			"Her bluff earns 250 + 1,000 and finding the truth earns 1,000: 2,250 total.",
		],
	},
	"caption-clash": {
		hero: `${ASSET_ROOT}/caption-clash/how-to.webp`,
		example: `${ASSET_ROOT}/caption-clash/example-round.webp`,
		exampleAlt: "Worked Caption Clash round: Hana captions a sleepy dog on a laptop, receives three anonymous votes, and earns a 250-point base plus 1,500 vote points, for 1,750 total.",
		summary: "Everyone writes a wholesome caption for the same image, then votes anonymously for another player's caption.",
		steps: [
			{ title: "See the image", detail: "Study the shared picture and caption prompt." },
			{ title: "Write", detail: "Submit one concise caption before the timer ends." },
			{ title: "Vote and reveal", detail: "Vote for someone else's caption; authors earn 250 plus 500 per vote." },
		],
		exampleSummary: "Hana's caption receives three votes. Voting itself does not add points to the voter.",
		exampleSteps: [
			"Hana writes “I answered one email. Time for a nap.” for the sleepy-dog image.",
			"Her caption appears anonymously on other players' ballots and receives three votes.",
			"The 250 author base plus 1,500 from votes gives Hana 1,750 points.",
		],
	},
	"story-loom": {
		hero: `${ASSET_ROOT}/story-loom/how-to.webp`,
		example: `${ASSET_ROOT}/story-loom/example-round.webp`,
		exampleAlt: "Worked Story Loom round: Selam writes a constrained continuation, receives four anonymous votes, and earns a 250-point base plus 2,000 vote points, for 2,250 total.",
		summary: "Read one shared story opening and constraint, write a continuation, then vote anonymously for another player's line.",
		steps: [
			{ title: "Read the start", detail: "Read the common opening and its writing constraint." },
			{ title: "Continue", detail: "Submit one concise next line before time runs out." },
			{ title: "Vote and reveal", detail: "Vote for another player's line; authors earn 250 plus 500 per vote." },
		],
		exampleSummary: "Selam follows the fifteen-word constraint and receives four votes from the anonymous ballot.",
		exampleSteps: [
			"The story begins with an old radio whispering the narrator's name at midnight.",
			"Selam submits a continuation in fifteen words or fewer, then her line receives four votes.",
			"The 250 author base plus 2,000 from votes gives Selam 2,250 points.",
		],
	},
	"sequence-sprint": {
		hero: `${ASSET_ROOT}/sequence-sprint/how-to.webp`,
		example: `${ASSET_ROOT}/sequence-sprint/example-round.webp`,
		exampleAlt: "Worked Sequence Sprint round: Mimi orders four butterfly life-cycle cards perfectly, earning 400 for exact positions, 300 for adjacent pairs, and a 400 perfect-order bonus, for 1,100 total.",
		summary: "Arrange every shuffled card into one complete order, lock it, and score exact positions, adjacent pairs, and a perfect sequence.",
		steps: [
			{ title: "Read the task", detail: "Study the prompt and every shuffled card." },
			{ title: "Build the order", detail: "Tap all cards into a complete sequence, then lock it." },
			{ title: "Reveal and score", detail: "Earn 100 per exact position, 100 per correct adjacent pair, and 400 for perfection." },
		],
		exampleSummary: "A perfect four-card sequence has four exact positions and three correct adjacent pairs.",
		exampleSteps: [
			"Mimi receives the four butterfly life-cycle cards in a shuffled order.",
			"She locks EGG, CATERPILLAR, CHRYSALIS, BUTTERFLY.",
			"Four exact positions, three pairs, and the perfect bonus earn 400 + 300 + 400: 1,100 total.",
		],
	},
	"picture-peek": {
		hero: `${ASSET_ROOT}/picture-peek/how-to.webp`,
		example: `${ASSET_ROOT}/picture-peek/example-round.webp`,
		exampleAlt: "Worked Picture Peek round: Dawit identifies the projected animal as an Ethiopian wolf and earns 1,000 points for the exact normalized answer match.",
		summary: "Study the projected picture, type one private answer, and compare it with the revealed answer.",
		steps: [
			{ title: "Look closely", detail: "Study the picture and read its question on the shared screen." },
			{ title: "Type one answer", detail: "Enter one private guess and lock it before time runs out." },
			{ title: "Reveal and score", detail: "An exact normalized answer match earns 1,000 points." },
		],
		exampleSummary: "Current play displays the picture for the round and accepts one locked text response per player.",
		exampleSteps: [
			"The screen shows an Ethiopian wolf and asks which animal is pictured.",
			"Dawit types Ethiopian wolf and locks his response once.",
			"The revealed answer matches, so Dawit earns 1,000 points.",
		],
	},
	"sound-snap": {
		hero: `${ASSET_ROOT}/sound-snap/how-to.webp`,
		example: `${ASSET_ROOT}/sound-snap/example-round.webp`,
		exampleAlt: "Worked Sound Snap round: Selam reads which animal says meow, chooses Cat from four choices, and earns 1,000 points.",
		summary: "Read the short sound-related clue, choose one displayed answer, and see the correct choice at reveal.",
		steps: [
			{ title: "Read", detail: "Read the short sound-related clue shown for the round." },
			{ title: "Choose", detail: "Tap one answer choice and lock it before the timer ends." },
			{ title: "Reveal and score", detail: "A correct choice earns 1,000 points; an incorrect choice earns zero." },
		],
		exampleSummary: "The sound-related clue is paired with four choices and one correct answer.",
		exampleSteps: [
			"Selam reads “Which animal says meow?”",
			"She selects CAT and locks the choice.",
			"CAT is revealed as correct, so Selam earns 1,000 points.",
		],
	},
	"memory-mosaic": {
		hero: `${ASSET_ROOT}/memory-mosaic/how-to.webp`,
		example: `${ASSET_ROOT}/memory-mosaic/example-round.webp`,
		exampleAlt: "Worked Memory Mosaic round: Meron remembers that keys were beside the blue mug, selects Keys, and earns 1,000 points.",
		summary: "Inspect the projected scene and use its details to answer one multiple-choice memory question.",
		steps: [
			{ title: "Observe and answer", detail: "Inspect the scene while its question and choices are available." },
			{ title: "Choose an answer", detail: "Read the question and lock one displayed choice." },
			{ title: "Reveal and score", detail: "A correct choice earns 1,000 points; an incorrect choice earns zero." },
		],
		exampleSummary: "Meron uses the tabletop details to answer one locked multiple-choice question.",
		exampleSteps: [
			"The scene contains a blue mug with keys beside it, plus glasses, a plant, and a notebook.",
			"When asked what was beside the blue mug, Meron selects KEYS.",
			"KEYS is revealed as correct, so Meron earns 1,000 points.",
		],
	},
	"common-thread": {
		hero: `${ASSET_ROOT}/common-thread/how-to.webp`,
		example: `${ASSET_ROOT}/common-thread/example-round.webp`,
		exampleAlt: "Worked Common Thread round: Hana connects piano, keyboard, and house with the word Keys and earns 1,000 points for an exact normalized match.",
		summary: "Read the complete clue set, type the word connecting every clue, and lock one response.",
		steps: [
			{ title: "Read all clues", detail: "The full clue set appears together on the big screen." },
			{ title: "Type the link", detail: "Enter the connecting word and lock it before time runs out." },
			{ title: "Reveal and score", detail: "An exact normalized answer match earns 1,000 points." },
		],
		exampleSummary: "Current play shows the full clue set together and accepts one locked text response.",
		exampleSteps: [
			"The clues are PIANO, KEYBOARD, and HOUSE.",
			"Hana identifies KEYS as the word that connects all three and locks it.",
			"The answer matches exactly, so Hana earns 1,000 points.",
		],
	},
	"escape-together": {
		hero: `${ASSET_ROOT}/escape-together/how-to.webp`,
		example: `${ASSET_ROOT}/escape-together/example-round.webp`,
		exampleAlt: "Worked Escape Together round: Dawit solves the keys-and-space riddle by choosing Keyboard and earns 1,000 points.",
		summary: "Read the current puzzle and all displayed choices, lock one answer, and see the predefined solution.",
		steps: [
			{ title: "Read the puzzle", detail: "Study the prompt and every available answer choice." },
			{ title: "Lock one choice", detail: "Choose the answer that solves the current puzzle." },
			{ title: "Reveal and score", detail: "A correct choice earns 1,000 points; an incorrect choice earns zero." },
		],
		exampleSummary: "Current play scores one multiple-choice puzzle per round without hints or attempt penalties.",
		exampleSteps: [
			"The riddle asks what has keys but no locks and space but no room.",
			"Dawit selects KEYBOARD from the four choices.",
			"KEYBOARD is revealed as correct, so Dawit earns 1,000 points.",
		],
	},
	"bracket-bash": {
		hero: `${ASSET_ROOT}/bracket-bash/how-to.webp`,
		example: `${ASSET_ROOT}/bracket-bash/example-round.webp`,
		exampleAlt: "Worked current-mode Bracket Bash round: Meron chooses Lion for the previous-semifinal prompt and earns 1,000 points when Lion is revealed as the predefined answer.",
		summary: "Current play presents one matchup-style prompt with predefined choices and scores each round individually.",
		steps: [
			{ title: "Read the matchup", detail: "Study the prompt and its available contenders." },
			{ title: "Lock one choice", detail: "Select the contender you think matches the prompt." },
			{ title: "Reveal and score", detail: "The predefined correct choice earns 1,000 points." },
		],
		exampleSummary: "The current implementation uses a predefined answer rather than a room-majority tournament vote.",
		exampleSteps: [
			"The prompt asks which animal won the previous semifinal.",
			"Meron chooses LION from the four contenders.",
			"LION is the predefined answer, so Meron earns 1,000 points.",
		],
	},
	"closest-call": {
		hero: `${ASSET_ROOT}/closest-call/how-to.webp`,
		example: `${ASSET_ROOT}/closest-call/example-round.webp`,
		exampleAlt: "Worked Closest Call round: for a target of 149.6 million kilometres, Hana estimates 150 and finishes 0.4 away while Dawit estimates 145 and finishes 4.6 away; Hana earns 1,000 points.",
		summary: "Everyone submits one numeric estimate; the single estimate with the smallest absolute distance from the target wins the round.",
		steps: [
			{ title: "Read the question", detail: "The prompt asks for one numeric estimate." },
			{ title: "Lock your number", detail: "Enter one number before time runs out." },
			{ title: "Compare distance", detail: "The nearest estimate earns 1,000 points and all others earn zero." },
		],
		exampleSummary: "Distance counts equally above or below the target; the nearest submitted estimate ranks first.",
		exampleSteps: [
			"The target is 149.6 million kilometres from Earth to the Sun.",
			"Hana submits 150, which is 0.4 away; Dawit submits 145, which is 4.6 away.",
			"Hana is nearest and earns 1,000 points; Dawit earns zero.",
		],
	},
	"phrase-forge": {
		hero: `${ASSET_ROOT}/phrase-forge/how-to.webp`,
		example: `${ASSET_ROOT}/phrase-forge/example-round.webp`,
		exampleAlt: "Worked Phrase Forge round: Selam rebuilds four proverb fragments perfectly, earning 400 for exact positions, 300 for adjacent pairs, and a 400 perfect-order bonus, for 1,100 total.",
		summary: "Arrange every shuffled phrase fragment into one complete order, lock it, and score positions, adjacent pairs, and perfection.",
		steps: [
			{ title: "Read the task", detail: "Study the prompt and all shuffled phrase fragments." },
			{ title: "Build the phrase", detail: "Tap every fragment into one complete order, then lock it." },
			{ title: "Reveal and score", detail: "Earn 100 per exact position, 100 per adjacent pair, and 400 for a perfect order." },
		],
		exampleSummary: "A perfect four-fragment phrase has four exact positions and three correct adjacent pairs.",
		exampleSteps: [
			"Selam receives NINE, A STITCH, SAVES, and IN TIME in shuffled order.",
			"She locks A STITCH, IN TIME, SAVES, NINE.",
			"Four exact positions, three pairs, and the perfect bonus earn 1,100 total.",
		],
	},
	"seek-and-show": {
		hero: `${ASSET_ROOT}/seek-and-show/how-to.webp`,
		example: `${ASSET_ROOT}/seek-and-show/example-round.webp`,
		exampleAlt: "Worked current-mode Seek and Show round: Hana finds a family dictionary, submits a concise description, and earns the 250-point creative-response score.",
		summary: "Read one safe creative mission, type a concise description of what you found, and compare it with the reference answer at reveal.",
		steps: [
			{ title: "Read the mission", detail: "The big screen presents one bounded creative prompt." },
			{ title: "Describe your find", detail: "Type one concise text response and lock it before time runs out." },
			{ title: "Reveal and score", detail: "The reference answer appears and every valid submission earns 250 points." },
		],
		exampleSummary: "Current play uses text descriptions without photo uploads, voting, speed bonuses, or host approval.",
		exampleSteps: [
			"The mission asks players to find and describe something nearby that helps people learn.",
			"Hana finds a family dictionary and describes the notes left by three generations.",
			"Her valid creative response earns 250 points.",
		],
	},
	"one-word-chorus": {
		hero: `${ASSET_ROOT}/one-word-chorus/how-to.webp`,
		example: `${ASSET_ROOT}/one-word-chorus/example-round.webp`,
		exampleAlt: "Worked current-mode One Word Chorus round: Tesfaye connects sunrise, sunflower, and gold with Yellow and earns 1,000 points for the exact normalized one-word match.",
		summary: "Read the full clue prompt, type one private word, and match the shared answer exactly.",
		steps: [
			{ title: "Read the clue", detail: "The full prompt appears on the big screen." },
			{ title: "Type one word", detail: "Enter one private response and lock it before time runs out." },
			{ title: "Reveal and score", detail: "An exact normalized match earns 1,000 points." },
		],
		exampleSummary: "Current play scores each player independently without clue-givers or duplicate cancellation.",
		exampleSteps: [
			"The clues are SUNRISE, SUNFLOWER, and GOLD, with a request for one connecting colour.",
			"Tesfaye types YELLOW and locks his response once.",
			"YELLOW matches the revealed answer, so Tesfaye earns 1,000 points.",
		],
	},
	"signal-spectrum": {
		hero: `${ASSET_ROOT}/signal-spectrum/how-to.webp`,
		example: `${ASSET_ROOT}/signal-spectrum/example-round.webp`,
		exampleAlt:
			"Worked Signal Spectrum round with a target of 68: markers at 66, 73, 58, and 84 finish 2, 5, 10, and 16 points away and score 1000, 750, 500, and 250 points.",
		summary:
			"Everyone submits one number from 0 to 100. The game compares each estimate with a hidden target and awards more points for being closer.",
		steps: [
			{
				title: "Read the prompt",
				detail: "Read the question on the big screen and decide which number fits best.",
			},
			{
				title: "Enter your estimate",
				detail: "Type one number from 0 to 100 and lock it before time runs out.",
			},
			{
				title: "Score by distance",
				detail: "The game checks the hidden target; closer estimates earn more points.",
			},
		],
		exampleSummary:
			"During live play, each player types a number. This worked diagram expands the server's distance calculation so the scoring is easy to understand.",
		exampleSteps: [
			"The prompt asks how energetic a family game night is; the target remains hidden.",
			"Mimi, Dawit, Selam, and Abebe submit 66, 73, 58, and 84.",
			"The target is 68, so distances of 2, 5, 10, and 16 earn 1,000, 750, 500, and 250 points.",
		],
	},
};

export function visualFor(gameKey) {
	return GAME_VISUALS[gameKey] || null;
}

export { GAME_VISUALS };
