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
