import test from "node:test";
import assert from "node:assert/strict";
import { access } from "node:fs/promises";
import { GAME_VISUALS, visualFor } from "../src/platform/discovery/gameVisuals.js";

const SHIPPED_GAME_KEYS = [
	"bluffline",
	"bracket-bash",
	"caption-clash",
	"closest-call",
	"common-thread",
	"crowd-compass",
	"cuecast",
	"doodle-dash",
	"escape-together",
	"memory-mosaic",
	"one-word-chorus",
	"phrase-forge",
	"picture-peek",
	"quiz",
	"seek-and-show",
	"sequence-sprint",
	"signal-spectrum",
	"sound-snap",
	"story-loom",
];

test("every shipped game has a visual guide", () => {
	assert.deepEqual(Object.keys(GAME_VISUALS).sort(), SHIPPED_GAME_KEYS);
});

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
	assert.equal(visualFor("not-a-real-game"), null);
	assert.equal(visualFor(), null);
});
