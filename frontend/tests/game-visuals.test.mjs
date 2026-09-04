import test from "node:test";
import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import { GAME_VISUALS, visualFor } from "../src/platform/discovery/gameVisuals.js";

test("shipped game visuals provide a hero and a worked example", async () => {
	for (const [key, visual] of Object.entries(GAME_VISUALS)) {
		assert.match(visual.hero, new RegExp(`/games/${key}/how-to\\.webp$`));
		assert.match(visual.example, new RegExp(`/games/${key}/example-round\\.webp$`));
		await access(new URL(`../../quizzly/public/images/games/${key}/how-to.webp`, import.meta.url));
		await access(
			new URL(`../../quizzly/public/images/games/${key}/example-round.webp`, import.meta.url)
		);
		assert.ok(visual.exampleAlt.length > 40);
		assert.ok(visual.summary);
		assert.ok(visual.exampleSummary);
		assert.equal(visual.steps.length, 3);
		assert.equal(visual.exampleSteps.length, 3);
	}
});

test("games without shipped visuals keep the existing detail page", () => {
	assert.equal(visualFor("quiz"), null);
	assert.equal(visualFor(), null);
});
