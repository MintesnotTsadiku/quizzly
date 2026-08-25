"""Reusable authoritative round engine for GatherPlay's bounded-input games."""

from __future__ import annotations

import random
import re
import time
from itertools import pairwise

import frappe
from frappe import _

from quizzly.games import (
	ActionDecision,
	GameManifest,
	GameModule,
	GameResult,
	Resolution,
	ScoreDelta,
	Transition,
)
from quizzly.games.engine import accepted_actions

PROFILES = {
	"bluffline": (
		"Bluffline",
		"Invent a believable answer, spot the truth, and fool the room.",
		"creative",
		("bluffing", "voting"),
		3,
		100,
	),
	"sequence-sprint": (
		"Sequence Sprint",
		"Put every card in the right order before the clock runs out.",
		"order",
		("ordering", "teams"),
		2,
		100,
	),
	"picture-peek": (
		"Picture Peek",
		"Identify the hidden picture before the final reveal.",
		"text",
		("image", "guessing"),
		1,
		100,
	),
	"sound-snap": (
		"Sound Snap",
		"Listen closely and identify each sound with as few clues as possible.",
		"choice",
		("audio", "quiz"),
		1,
		100,
	),
	"caption-clash": (
		"Caption Clash",
		"Write a wholesome caption and win the room's vote.",
		"creative",
		("creative", "voting"),
		3,
		100,
	),
	"story-loom": (
		"Story Loom",
		"Add a constrained continuation and weave one shared story.",
		"creative",
		("story", "cooperative"),
		3,
		100,
	),
	"signal-spectrum": (
		"Signal Spectrum",
		"Place your marker between two opposites and match the hidden target.",
		"number",
		("teams", "deduction"),
		2,
		40,
	),
	"memory-mosaic": (
		"Memory Mosaic",
		"Study the scene, then prove what you remember.",
		"choice",
		("memory", "image"),
		1,
		100,
	),
	"common-thread": (
		"Common Thread",
		"Find the connection that links every clue.",
		"text",
		("word", "cooperative"),
		1,
		100,
	),
	"escape-together": (
		"Escape Together",
		"Solve each stage as a room and unlock the finale.",
		"choice",
		("puzzle", "cooperative"),
		2,
		100,
	),
	"bracket-bash": (
		"Bracket Bash",
		"Vote through head-to-head matchups until one champion remains.",
		"choice",
		("voting", "tournament"),
		2,
		100,
	),
	"closest-call": (
		"Closest Call",
		"Make the nearest estimate without going over—or missing by much.",
		"number",
		("estimation", "duel"),
		2,
		100,
	),
	"phrase-forge": (
		"Phrase Forge",
		"Rebuild the phrase from shuffled fragments.",
		"order",
		("ordering", "word"),
		1,
		40,
	),
	"seek-and-show": (
		"Seek & Show",
		"Complete a safe room mission and share what your team found.",
		"creative",
		("mission", "teams"),
		2,
		100,
	),
	"one-word-chorus": (
		"One Word Chorus",
		"Give one legal clue and help the guesser find the secret.",
		"text",
		("word", "teams"),
		3,
		100,
	),
}
VOTE_GAMES = {"bluffline", "caption-clash", "story-loom"}


class RoundGame(GameModule):
	key = ""

	@property
	def profile(self):
		return PROFILES[self.key]

	@property
	def manifest(self):
		title, summary, mode, tags, minimum, maximum = self.profile
		return GameManifest(
			self.key,
			title,
			"1.0.0",
			summary,
			minimum,
			maximum,
			"6-50",
			15,
			tags,
			"Available",
			(mode, "timer", "reconnect"),
			("skip_turn", "next"),
			"round-games",
		)

	def validate_configuration(self, ctx, cfg):
		pack = cfg.get("pack")
		if not pack or frappe.db.get_value("GP Game Pack", pack, "game_key") != self.key:
			frappe.throw(_("Pick a pack for this game"))
		seconds = int(cfg.get("seconds") or 30)
		if seconds not in (15, 30, 45, 60):
			frappe.throw(_("Round length must be 15, 30, 45 or 60 seconds"))
		count = frappe.db.count("GP Game Item", {"parent": pack, "parenttype": "GP Game Pack"})
		return {
			"pack": pack,
			"seconds": seconds,
			"rounds": max(1, min(int(cfg.get("rounds") or count), count)),
		}

	def start_game(self, ctx, participants):
		items = frappe.get_all(
			"GP Game Item",
			filters={"parent": ctx.configuration["pack"], "parenttype": "GP Game Pack"},
			pluck="name",
		)
		random.shuffle(items)
		return self.open_round(ctx, {"items": items, "position": 0, "round_index": -1})

	def open_round(self, ctx, ms):
		state = dict(ms)
		if state["position"] >= ctx.configuration["rounds"]:
			return Transition(phase="podium", finished=self.finish_game(ctx, {"module_state": state}))
		state["round_index"] += 1
		state["round_key"] = f"round-{state['round_index'] + 1}"
		state["item"] = state["items"][state["position"]]
		state["position"] += 1
		return Transition(
			phase="round_open",
			next_ts=time.time() + ctx.configuration["seconds"],
			ttl=ctx.configuration["seconds"] + 60,
			module_state=state,
			publish={
				"type": f"{self.key.replace('-', '_')}.round_opened",
				"phase": "round_open",
				**self.public_item(state["item"]),
				"round": state["position"],
				"total": ctx.configuration["rounds"],
			},
		)

	def advance_state(self, ctx, state, trigger):
		if trigger.get("command") not in ("deadline", "skip_turn", "next"):
			return None
		if state["phase"] == "round_open":
			return self.open_vote(ctx, state) if self.key in VOTE_GAMES else self.reveal(ctx, state)
		if state["phase"] == "vote_open":
			return self.reveal(ctx, state)
		if state["phase"] == "round_reveal":
			return Transition(
				phase="scoreboard",
				next_ts=time.time() + 6,
				ttl=66,
				module_state=dict(state["module_state"]),
				publish={"type": "platform.scoreboard_updated", "teams": self.standings(ctx)},
			)
		if state["phase"] == "scoreboard":
			return self.open_round(ctx, state["module_state"])

	def submit_action(self, ctx, state, participant, action_type, payload):
		actions = accepted_actions(ctx.session, state["module_state"]["round_index"])
		if state["phase"] == "vote_open" and self.key in VOTE_GAMES and action_type == "vote":
			if any(a.participant == participant["name"] and a.action_type == "vote" for a in actions):
				return ActionDecision(False, "You already voted")
			candidate = str(payload.get("value") or "")
			allowed = {c["id"] for c in self.candidates(ctx, state["module_state"], participant["name"])}
			if candidate not in allowed:
				return ActionDecision(False, "Choose an available response")
			return ActionDecision(True, result={"ok": True, "locked": True})
		if state["phase"] != "round_open" or action_type != "submit":
			return ActionDecision(False, "Submissions are closed")
		if any(a.participant == participant["name"] and a.action_type == "submit" for a in actions):
			return ActionDecision(False, "You already submitted")
		mode = self.profile[2]
		value = payload.get("value")
		if mode == "number":
			try:
				value = float(value)
			except (TypeError, ValueError):
				return ActionDecision(False, "Enter a number")
		elif mode == "order":
			cards = frappe.parse_json(self.item(state["module_state"]["item"]).choices) or []
			if not isinstance(value, list) or len(value) != len(cards) or sorted(value) != sorted(cards):
				return ActionDecision(False, "Order every card")
		else:
			value = str(value or "").strip()[:280]
			if not value:
				return ActionDecision(False, "Enter a response")
		return ActionDecision(True, result={"ok": True, "locked": True})

	def open_vote(self, ctx, state):
		ms = dict(state["module_state"])
		candidates = self.candidates(ctx, ms)
		return Transition(
			phase="vote_open",
			next_ts=time.time() + ctx.configuration["seconds"],
			ttl=ctx.configuration["seconds"] + 60,
			module_state=ms,
			publish={
				"type": f"{self.key.replace('-', '_')}.vote_opened",
				"phase": "vote_open",
				"prompt": self.item(ms["item"]).prompt_text,
				"choices": candidates,
				"responses": len(candidates),
			},
		)

	def candidates(self, ctx, ms, exclude_participant=None):
		actions = [a for a in accepted_actions(ctx.session, ms["round_index"]) if a.action_type == "submit"]
		rows = [
			{"id": a.name, "value": str(a.payload.get("value") or "")[:280]}
			for a in actions
			if a.participant != exclude_participant
		]
		if self.key == "bluffline":
			rows.append({"id": "truth", "value": self.item(ms["item"]).answer})
		random.Random(f"{ctx.session}:{ms['round_index']}").shuffle(rows)
		return rows

	def reveal(self, ctx, state):
		ms = dict(state["module_state"])
		item = self.item(ms["item"])
		actions = [a for a in accepted_actions(ctx.session, ms["round_index"]) if a.action_type == "submit"]
		mode = self.profile[2]
		deltas = []
		results = []
		if mode == "number":
			target = float(item.target or 0)
			dist = sorted(
				((abs(float(a.payload.get("value")) - target), a) for a in actions),
				key=lambda row: (row[0], row[1].received_at, row[1].name),
			)
			for rank, (distance, a) in enumerate(dist):
				if self.key == "signal-spectrum":
					points = (
						1000
						if distance <= 3
						else 750
						if distance <= 7
						else 500
						if distance <= 12
						else 250
						if distance <= 20
						else 0
					)
				else:
					# Closest Call is a duel: only the nearest estimate wins the point.
					points = 1000 if rank == 0 else 0
				if not points:
					results.append({"participant": a.participant, "distance": distance, "points": 0})
					continue
				deltas.append(
					ScoreDelta(
						"Participant",
						a.participant,
						points,
						"closest",
						f"{self.key}:{ms['round_index']}:{a.participant}",
						{"distance": distance},
					)
				)
				results.append({"participant": a.participant, "distance": distance, "points": points})
		elif mode == "creative":
			votes = [a for a in accepted_actions(ctx.session, ms["round_index"]) if a.action_type == "vote"]
			for a in actions:
				points = 250 + 500 * sum(1 for vote in votes if vote.payload.get("value") == a.name)
				deltas.append(
					ScoreDelta(
						"Participant",
						a.participant,
						points,
						"creative_votes",
						f"{self.key}:{ms['round_index']}:{a.participant}",
					)
				)
				results.append(
					{
						"participant": a.participant,
						"value": a.payload.get("value"),
						"votes": (points - 250) // 500,
					}
				)
			if self.key == "bluffline":
				for vote in votes:
					if vote.payload.get("value") == "truth":
						deltas.append(
							ScoreDelta(
								"Participant",
								vote.participant,
								1000,
								"found_truth",
								f"{self.key}:{ms['round_index']}:truth:{vote.participant}",
							)
						)
		elif mode == "order":
			cards = frappe.parse_json(item.choices) or []
			for a in actions:
				value = a.payload.get("value") or []
				exact = sum(
					1 for index, card in enumerate(value) if index < len(cards) and card == cards[index]
				)
				correct_pairs = set(pairwise(cards))
				adjacent = sum(1 for pair in pairwise(value) if pair in correct_pairs)
				points = exact * 100 + adjacent * 100 + (400 if value == cards else 0)
				if points:
					deltas.append(
						ScoreDelta(
							"Participant",
							a.participant,
							points,
							"ordered",
							f"{self.key}:{ms['round_index']}:{a.participant}",
							{"exact": exact, "adjacent": adjacent},
						)
					)
				results.append(
					{
						"participant": a.participant,
						"correct": value == cards,
						"exact": exact,
						"adjacent": adjacent,
						"points": points,
					}
				)
		else:
			answer = self.norm(item.answer)
			for a in actions:
				value = a.payload.get("value")
				correct = self.norm(value) == answer
				if correct:
					deltas.append(
						ScoreDelta(
							"Participant",
							a.participant,
							1000,
							"correct",
							f"{self.key}:{ms['round_index']}:{a.participant}",
						)
					)
				results.append({"participant": a.participant, "correct": correct})
		return Transition(
			phase="round_reveal",
			next_ts=time.time() + 8,
			ttl=68,
			module_state=ms,
			resolution=Resolution({"answer": item.answer, "responses": len(actions)}, deltas),
			publish={
				"type": f"{self.key.replace('-', '_')}.round_revealed",
				"phase": "round_reveal",
				**self.public_item(ms["item"]),
				"answer": item.answer,
				"results": results,
			},
		)

	def serialize_public_state(self, ctx, state):
		ms = state["module_state"]
		view = {"phase": state["phase"], "round": ms.get("position"), "total": ctx.configuration["rounds"]}
		if ms.get("item"):
			view.update(self.public_item(ms["item"]))
			view["responses"] = len(
				[a for a in accepted_actions(ctx.session, ms.get("round_index")) if a.action_type == "submit"]
			)
		if state["phase"] == "vote_open":
			view["choices"] = self.candidates(ctx, ms)
		if state["phase"] == "round_reveal":
			view["answer"] = self.item(ms["item"]).answer
		return view

	def serialize_player_state(self, ctx, state, participant):
		view = self.serialize_public_state(ctx, state)
		if state["phase"] == "vote_open":
			view["choices"] = self.candidates(ctx, state["module_state"], participant["name"])
		return view

	def serialize_host_state(self, ctx, state):
		return {**self.serialize_public_state(ctx, state), "configuration": ctx.configuration}

	def progress_metric(self, ctx, state):
		return (
			{
				"count": len(
					[
						a
						for a in accepted_actions(ctx.session, state["module_state"].get("round_index"))
						if a.action_type == "submit"
					]
				)
			}
			if state["phase"] == "round_open"
			else None
		)

	def is_presentation_phase(self, phase):
		return phase in {"round_reveal", "scoreboard", "podium"}

	def finish_game(self, ctx, state):
		rows = self.standings(ctx)
		board = [{"subject_type": "Participant", **r} for r in rows]
		return GameResult({"phase": "podium", "teams": board}, board)

	def standings(self, ctx):
		rows = frappe.get_all(
			"GP Participant",
			filters={"session": ctx.session, "status": ("!=", "Kicked")},
			fields=["name", "nickname", "avatar", "score"],
			order_by="score desc, joined_at asc",
		)
		for i, r in enumerate(rows, 1):
			r["rank"] = i
			r["team_name"] = r.nickname
		return [dict(r) for r in rows]

	def item(self, name):
		return frappe.get_doc("GP Game Item", name)

	def public_item(self, name):
		i = self.item(name)
		choices = frappe.parse_json(i.choices) or []
		if self.profile[2] == "order":
			choices = list(choices)
			random.Random(f"{name}:{self.key}").shuffle(choices)
		return {
			"prompt": i.prompt_text,
			"choices": choices,
			"media_url": i.media_url,
			"mechanic": self.profile[2],
		}

	def norm(self, v):
		return re.sub(r"[^a-z0-9 ]+", "", str(v or "").lower()).strip()


def _class(name, key):
	return type(name, (RoundGame,), {"key": key})


BlufflineGame = _class("BlufflineGame", "bluffline")
SequenceSprintGame = _class("SequenceSprintGame", "sequence-sprint")
PicturePeekGame = _class("PicturePeekGame", "picture-peek")
SoundSnapGame = _class("SoundSnapGame", "sound-snap")
CaptionClashGame = _class("CaptionClashGame", "caption-clash")
StoryLoomGame = _class("StoryLoomGame", "story-loom")
SignalSpectrumGame = _class("SignalSpectrumGame", "signal-spectrum")
MemoryMosaicGame = _class("MemoryMosaicGame", "memory-mosaic")
CommonThreadGame = _class("CommonThreadGame", "common-thread")
EscapeTogetherGame = _class("EscapeTogetherGame", "escape-together")
BracketBashGame = _class("BracketBashGame", "bracket-bash")
ClosestCallGame = _class("ClosestCallGame", "closest-call")
PhraseForgeGame = _class("PhraseForgeGame", "phrase-forge")
SeekAndShowGame = _class("SeekAndShowGame", "seek-and-show")
OneWordChorusGame = _class("OneWordChorusGame", "one-word-chorus")
