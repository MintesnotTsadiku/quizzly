"""Doodle Dash: private artist prompt, public stroke batches, exact-alias guesses."""

from __future__ import annotations

import random
import time

import frappe
from frappe import _
from frappe.utils import time_diff_in_seconds

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
from quizzly.games.text import normalize_answer

READY_SECONDS = 3
REVEAL_SECONDS = 8
SCOREBOARD_SECONDS = 6
PHASE_TTL_MARGIN = 60


class DoodleDashGame(GameModule):
	manifest = GameManifest(
		key="doodle-dash",
		title="Doodle Dash",
		version="1.0.0",
		summary="One artist draws a secret word while everyone else races to guess it.",
		min_players=3,
		max_players=100,
		recommended_players="8-40",
		typical_minutes=20,
		interaction_tags=("drawing", "guessing", "creative"),
		status="Available",
		capabilities=("private_prompt", "drawing", "free_text", "timer"),
		host_commands=("skip_turn", "next"),
		frontend_key="doodle-dash",
	)

	def validate_configuration(self, ctx, configuration):
		pack = configuration.get("pack")
		if not pack or not frappe.db.exists("GP Draw Pack", pack):
			frappe.throw(_("Pick a drawing pack"))
		seconds = int(configuration.get("seconds") or 60)
		if seconds not in (30, 60, 90):
			frappe.throw(_("Round length must be 30, 60 or 90 seconds"))
		count = frappe.db.count("GP Draw Prompt", {"parent": pack, "parenttype": "GP Draw Pack"})
		if not count:
			frappe.throw(_("That pack has no prompts"))
		return {
			"pack": pack,
			"seconds": seconds,
			"rounds": max(1, min(int(configuration.get("rounds") or count), count)),
		}

	def start_game(self, ctx, participants):
		prompts = frappe.get_all(
			"GP Draw Prompt",
			filters={"parent": ctx.configuration["pack"], "parenttype": "GP Draw Pack"},
			pluck="name",
		)
		random.shuffle(prompts)
		return self.ready(
			ctx,
			{
				"prompt_ids": prompts,
				"position": 0,
				"round_index": -1,
				"artists": [p["name"] for p in participants],
			},
		)

	def ready(self, ctx, module_state):
		state = dict(module_state)
		if state["position"] >= min(ctx.configuration["rounds"], len(state["prompt_ids"])):
			return Transition(phase="podium", finished=self.finish_game(ctx, {"module_state": state}))
		state["round_index"] += 1
		state["round_key"] = f"drawing-{state['round_index'] + 1}"
		state["prompt_id"] = state["prompt_ids"][state["position"]]
		state["artist"] = state["artists"][state["position"] % len(state["artists"])]
		state["position"] += 1
		return Transition(
			phase="draw_ready",
			next_ts=time.time() + READY_SECONDS,
			ttl=READY_SECONDS + PHASE_TTL_MARGIN,
			module_state=state,
			publish={
				"type": "doodle_dash.artist_ready",
				"phase": "draw_ready",
				"artist": self.participant(state["artist"]),
				"round": state["position"],
				"total": ctx.configuration["rounds"],
			},
		)

	def advance_state(self, ctx, state, trigger):
		if trigger.get("command") not in ("deadline", "skip_turn", "next"):
			return None
		if state["phase"] == "draw_ready":
			return Transition(
				phase="draw_open",
				next_ts=time.time() + ctx.configuration["seconds"],
				ttl=ctx.configuration["seconds"] + PHASE_TTL_MARGIN,
				module_state=dict(state["module_state"]),
				publish={
					"type": "doodle_dash.round_started",
					"phase": "draw_open",
					"artist": self.participant(state["module_state"]["artist"]),
				},
			)
		if state["phase"] == "draw_open":
			return self.reveal(ctx, state)
		if state["phase"] == "draw_reveal":
			return Transition(
				phase="scoreboard",
				next_ts=time.time() + SCOREBOARD_SECONDS,
				ttl=SCOREBOARD_SECONDS + PHASE_TTL_MARGIN,
				module_state=dict(state["module_state"]),
				publish={"type": "platform.scoreboard_updated", "teams": self.standings(ctx)},
			)
		if state["phase"] == "scoreboard":
			return self.ready(ctx, state["module_state"])
		return None

	def submit_action(self, ctx, state, participant, action_type, payload):
		ms = state["module_state"]
		if state["phase"] != "draw_open":
			return ActionDecision(False, "Drawing is closed")
		is_artist = participant["name"] == ms["artist"]
		if action_type == "stroke_batch":
			if not is_artist:
				return ActionDecision(False, "Only the artist can draw")
			strokes = payload.get("strokes") or []
			if len(strokes) > 80 or any(not self.valid_stroke(s) for s in strokes):
				return ActionDecision(False, "Invalid drawing batch")
			if len(self.canvas(ctx, state)) + len(strokes) > 12000:
				return ActionDecision(False, "The canvas is full. Clear it to keep drawing.")
			return ActionDecision(True)
		if action_type == "clear_canvas":
			return ActionDecision(is_artist, None if is_artist else "Only the artist can clear")
		if action_type == "guess":
			if is_artist:
				return ActionDecision(False, "The artist cannot guess")
			guess = self.clean(payload.get("guess"))
			if not guess:
				return ActionDecision(False, "Enter a guess")
			already = any(
				a.participant == participant["name"] and a.action_type == "correct_guess"
				for a in accepted_actions(ctx.session, ms["round_index"])
			)
			if already:
				return ActionDecision(False, "You already solved it")
			correct = guess in self.answers(ms["prompt_id"])
			return ActionDecision(
				True,
				result={"ok": True, "correct": correct, "record_as": "correct_guess" if correct else "guess"},
			)
		return ActionDecision(False, "Unknown action")

	def reveal(self, ctx, state):
		ms = dict(state["module_state"])
		actions = accepted_actions(ctx.session, ms["round_index"])
		correct = [a for a in actions if a.action_type == "correct_guess"]
		# Compatibility with clients sending guess: score server-confirmed exact matches too.
		correct += [
			a
			for a in actions
			if a.action_type == "guess"
			and self.clean(a.payload.get("guess")) in self.answers(ms["prompt_id"])
		]
		seen = set()
		unique = [a for a in correct if not (a.participant in seen or seen.add(a.participant))]
		deltas = []
		for action in unique:
			elapsed = max(
				0,
				time_diff_in_seconds(
					action.received_at,
					frappe.db.get_value(
						"GP Round", {"session": ctx.session, "round_index": ms["round_index"]}, "opened_at"
					),
				),
			)
			points = max(500, round(1000 - 500 * elapsed / ctx.configuration["seconds"]))
			deltas.append(
				ScoreDelta(
					"Participant",
					action.participant,
					points,
					"correct_guess",
					f"draw:{ms['round_index']}:{action.participant}",
					{"seconds": elapsed},
				)
			)
		if unique:
			deltas.append(
				ScoreDelta(
					"Participant",
					ms["artist"],
					min(500, 50 * len(unique)),
					"artist_bonus",
					f"draw:{ms['round_index']}:artist",
				)
			)
		answer = frappe.db.get_value("GP Draw Prompt", ms["prompt_id"], "prompt_text")
		return Transition(
			phase="draw_reveal",
			next_ts=time.time() + REVEAL_SECONDS,
			ttl=REVEAL_SECONDS + PHASE_TTL_MARGIN,
			module_state=ms,
			resolution=Resolution({"answer": answer, "correct": len(unique)}, deltas),
			publish={
				"type": "doodle_dash.answer_revealed",
				"phase": "draw_reveal",
				"answer": answer,
				"correct": len(unique),
				"artists": self.participant(ms["artist"]),
				"strokes": self.canvas(ctx, state),
			},
		)

	def serialize_public_state(self, ctx, state):
		ms = state["module_state"]
		view = {
			"phase": state["phase"],
			"artist": self.participant(ms.get("artist")),
			"round": ms.get("position"),
			"total": ctx.configuration["rounds"],
		}
		if state["phase"] in ("draw_open", "draw_reveal"):
			view["strokes"] = self.canvas(ctx, state)
		if state["phase"] == "draw_reveal":
			view["answer"] = frappe.db.get_value("GP Draw Prompt", ms["prompt_id"], "prompt_text")
		return view

	def serialize_player_state(self, ctx, state, participant):
		view = self.serialize_public_state(ctx, state)
		artist = participant["name"] == state["module_state"].get("artist")
		view["is_artist"] = artist
		if artist and state["phase"] in ("draw_ready", "draw_open"):
			view["prompt"] = frappe.db.get_value(
				"GP Draw Prompt", state["module_state"]["prompt_id"], "prompt_text"
			)
		return view

	def serialize_host_state(self, ctx, state):
		return {**self.serialize_public_state(ctx, state), "configuration": ctx.configuration}

	def is_presentation_phase(self, phase):
		return phase in {"draw_reveal", "scoreboard", "podium"}

	def progress_metric(self, ctx, state):
		if state["phase"] != "draw_open":
			return None
		return {
			"count": len(
				{
					a.participant
					for a in accepted_actions(ctx.session, state["module_state"]["round_index"])
					if a.action_type in ("correct_guess", "guess")
				}
			)
		}

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
		for i, row in enumerate(rows, 1):
			row["rank"] = i
			row["team_name"] = row.nickname
		return [dict(r) for r in rows]

	def canvas(self, ctx, state):
		return frappe.cache.get_value(self.canvas_key(ctx, state)) or []

	def update_canvas(self, ctx, state, action_type, payload):
		key = self.canvas_key(ctx, state)
		with frappe.cache.lock(f"{key}:write", timeout=10):
			canvas = [] if action_type == "clear_canvas" else self.canvas(ctx, state)
			if action_type == "stroke_batch":
				canvas.extend(payload.get("strokes") or [])
				if len(canvas) > 12000:
					frappe.throw("The canvas is full. Clear it to keep drawing.")
			frappe.cache.set_value(key, canvas, expires_in_sec=3600)
		return canvas

	def canvas_key(self, ctx, state):
		round_index = state["module_state"].get("round_index", -1)
		return f"gp:doodle:{ctx.session}:{round_index}:canvas"

	def answers(self, prompt):
		row = frappe.db.get_value("GP Draw Prompt", prompt, ["prompt_text", "aliases"], as_dict=True)
		return {
			self.clean(row.prompt_text),
			*[self.clean(v) for v in (row.aliases or "").split(",") if self.clean(v)],
		}

	def clean(self, value):
		return normalize_answer(value)

	def valid_stroke(self, s):
		return isinstance(s, dict) and all(
			isinstance(s.get(k), (int, float)) and 0 <= s[k] <= 1 for k in ("x1", "y1", "x2", "y2")
		)

	def participant(self, name):
		row = (
			frappe.db.get_value("GP Participant", name, ["name", "nickname", "avatar"], as_dict=True)
			if name
			else None
		)
		return dict(row) if row else None
