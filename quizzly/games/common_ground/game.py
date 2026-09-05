"""A cooperative room game: people participate through conversation, not tokens."""

import random
import time

import frappe
from frappe import _

from quizzly.games import GameManifest, GameModule, GameResult, Transition

PACKS = {
	"everyday": {
		"title": "Little things, big connections",
		"prompts": [
			(
				"Find three small things you all enjoy.",
				"Go beyond food and favourite colours. Can you find a sound, a place and a little everyday moment?",
				"Which shared joy was the biggest surprise?",
			),
			(
				"Invent a perfect afternoon together.",
				"Everyone adds one idea. Fit them into a single afternoon, with no money needed.",
				"Give your afternoon a name. Share it with the room.",
			),
			(
				"Find a skill you could teach each other.",
				"It can be tiny: a hand trick, a greeting, a way to fold paper. Let everyone offer something.",
				"Choose one skill and give the group a quick lesson.",
			),
			(
				"Make a team name from something you share.",
				"Find a shared habit, hope or favourite place. Turn it into a name everyone likes.",
				"Introduce your group and tell the story behind its name.",
			),
			(
				"Find an ordinary thing you all see differently.",
				"Try rain, mornings or a long journey. Each person gives one good thing about it.",
				"Which different perspective would you like to borrow?",
			),
		],
	},
	"imagination": {
		"title": "A little imagination",
		"prompts": [
			(
				"Give an ordinary object a new job.",
				"Choose something you can see. Everyone suggests a surprising use; combine two ideas.",
				"Present your invention in one sentence.",
			),
			(
				"Invent an animal that needs all of you.",
				"Each person contributes one ability. Decide where your animal lives and what it likes.",
				"Introduce your animal with a sound, a gesture or a description.",
			),
			(
				"Plan a celebration for absolutely nothing.",
				"Invent a reason, a tiny tradition and a name. Everyone contributes one detail.",
				"Teach the room your new tradition. Joining in is optional.",
			),
			(
				"Build a story one sentence at a time.",
				"Start with: 'Someone left a very small door open.' Take turns. Anyone may pass.",
				"Give your story a title together.",
			),
			(
				"Design a place where everyone belongs.",
				"Everyone adds one thing that would help them feel comfortable. Imaginary things count.",
				"What is one idea you could bring into this room today?",
			),
		],
	},
}


class CommonGroundGame(GameModule):
	manifest = GameManifest(
		key="common-ground",
		title="Common Ground",
		version="1.0.0",
		summary="Find surprising things you share. A little conversation, a lot of connection.",
		min_players=2,
		max_players=None,
		recommended_players="2-5 per conversation group",
		typical_minutes=8,
		interaction_tags=("conversation", "cooperative", "no player devices"),
		capabilities=("host_only", "shared_screen", "manual_pacing"),
		frontend_key="common-ground",
	)

	def validate_configuration(self, ctx, configuration):
		pack = configuration.get("pack", "everyday")
		if pack not in PACKS:
			frappe.throw(_("Choose a Common Ground pack"))
		return {"pack": pack, "auto_progress": False, "participation": "host_only"}

	def start_game(self, ctx, participants):
		# Snapshot content: replay draws fresh prompts; an active room stays stable.
		prompts = random.sample(PACKS[ctx.configuration["pack"]]["prompts"], 3)
		return self._step({"prompts": prompts, "position": 0}, "room_prompt")

	def _step(self, state, phase, resolution=None):
		# Human-paced state lives for a day; advancing renews the lease.
		return Transition(
			phase=phase, next_ts=time.time() + 86400, ttl=86400, module_state=state, resolution=resolution
		)

	def advance_state(self, ctx, state, trigger):
		if trigger.get("command") == "deadline":
			return self._step(state["module_state"], state["phase"])
		if trigger.get("command") != "next":
			return None
		data = dict(state["module_state"])
		if state["phase"] == "room_prompt":
			return self._step(data, "room_share")
		data["position"] += 1
		if data["position"] >= len(data["prompts"]):
			return Transition(phase="podium", finished=self.finish_game(ctx, state))
		return self._step(data, "room_prompt")

	def serialize_public_state(self, ctx, state):
		data = state["module_state"]
		title, instruction, share = data["prompts"][data["position"]]
		return {
			"prompt": title,
			"instruction": instruction,
			"share": share,
			"round": data["position"] + 1,
			"rounds": len(data["prompts"]),
		}

	def serialize_host_state(self, ctx, state):
		return self.serialize_public_state(ctx, state)

	def serialize_player_state(self, ctx, state, participant):
		return self.serialize_public_state(ctx, state)

	def finish_game(self, ctx, state):
		return GameResult(publish={"cooperative": True, "podium": []}, leaderboard=[])
