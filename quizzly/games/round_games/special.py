"""Distinct progression for room stories and majority tournaments."""

import time
from collections import Counter

import frappe

from quizzly.games import ActionDecision, Resolution, ScoreDelta, Transition
from quizzly.games.engine import accepted_actions

from .game import RoundGame


class StoryLoomGame(RoundGame):
	key = "story-loom"

	def open_round(self, ctx, ms):
		transition = super().open_round(ctx, ms)
		if not transition.finished and not transition.module_state.get("story"):
			transition.module_state["story"] = [self.item(transition.module_state["item"]).prompt_text]
		return transition

	def reveal(self, ctx, state):
		transition = super().reveal(ctx, state)
		ms = transition.module_state
		rows = ms["reveal"]["results"]
		if rows:
			# Ties keep the earliest submitted continuation, stated at reveal.
			winner = max(enumerate(rows), key=lambda pair: (pair[1]["votes"], -pair[0]))[1]
			ms["story"] = [*ms.get("story", []), winner["value"]]
			ms["reveal"]["selected"] = winner["value"]
			ms["reveal"]["story"] = ms["story"]
		return transition

	def serialize_public_state(self, ctx, state):
		view = super().serialize_public_state(ctx, state)
		view["story"] = state["module_state"].get("story", [])
		if state["phase"] == "round_open":
			view["prompt"] = frappe._(
				"Write the next sentence of your room's story. Tied votes keep the earliest continuation."
			)
		return view


class BracketBashGame(RoundGame):
	key = "bracket-bash"

	def validate_configuration(self, ctx, cfg):
		result = super().validate_configuration(ctx, cfg)
		pack = frappe.get_doc("GP Game Pack", result["pack"])
		entrants = frappe.parse_json(pack.items[0].choices) or []
		if len(entrants) not in (4, 8, 16) or len(set(entrants)) != len(entrants):
			frappe.throw(frappe._("The first round must contain 4, 8 or 16 different tournament entrants."))
		result["entrants"] = entrants
		result["rounds"] = len(entrants) - 1
		return result

	def start_game(self, ctx, participants):
		item = frappe.get_all(
			"GP Game Item",
			filters={"parent": ctx.configuration["pack"], "parenttype": "GP Game Pack"},
			pluck="name",
			order_by="idx asc",
		)[0]
		return self.open_round(
			ctx,
			{
				"items": [item] * ctx.configuration["rounds"],
				"position": 0,
				"round_index": -1,
				"bracket_queue": list(ctx.configuration["entrants"]),
				"bracket_history": [],
			},
		)

	def open_round(self, ctx, ms):
		t = super().open_round(ctx, ms)
		if not t.finished:
			t.module_state["matchup"] = t.module_state["bracket_queue"][:2]
			t.module_state["bracket_queue"] = t.module_state["bracket_queue"][2:]
		return t

	def submit_action(self, ctx, state, participant, action_type, payload):
		if payload.get("value") not in state["module_state"].get("matchup", []):
			return ActionDecision(False, "Choose one of the current contenders.")
		return super().submit_action(ctx, state, participant, action_type, payload)

	def reveal(self, ctx, state):
		ms = dict(state["module_state"])
		actions = [a for a in accepted_actions(ctx.session, ms["round_index"]) if a.action_type == "submit"]
		counts = Counter(a.payload.get("value") for a in actions)
		matchup = ms["matchup"]
		# A deterministic seeded order resolves ties without repeated deadlocked ballots.
		winner = max(matchup, key=lambda name: counts[name])
		tie = counts[matchup[0]] == counts[matchup[1]]
		result = {"contenders": matchup, "winner": winner, "votes": dict(counts), "tie": tie}
		ms["bracket_history"] = [*ms["bracket_history"], result]
		ms["bracket_queue"] = [*ms["bracket_queue"], winner]
		ms["reveal"] = {
			"answer": winner,
			"results": [{"value": name, "votes": counts[name]} for name in matchup],
			"bracket_history": ms["bracket_history"],
			"tie": tie,
			"responses": len(actions),
		}
		return Transition(
			phase="round_reveal",
			next_ts=time.time() + 8,
			ttl=68,
			module_state=ms,
			resolution=Resolution(ms["reveal"]),
			publish={"type": "bracket_bash.revealed", "phase": "round_reveal"},
		)

	def serialize_public_state(self, ctx, state):
		view = super().serialize_public_state(ctx, state)
		ms = state["module_state"]
		view.update(
			choices=ms.get("matchup", []),
			bracket_history=ms.get("bracket_history", []),
			prompt=frappe._(
				"Choose the room's favorite. Majority advances; a tie advances the first seeded contender."
			),
		)
		return view


class OneWordChorusGame(RoundGame):
	key = "one-word-chorus"

	def start_game(self, ctx, participants):
		if len(participants) < 2:
			frappe.throw(frappe._("Join with a guesser and at least one clue giver."))
		self._participants = participants
		return super().start_game(ctx, participants)

	def open_round(self, ctx, ms):
		t = super().open_round(ctx, ms)
		if t.finished:
			return t
		members = frappe.get_all(
			"GP Participant",
			filters={"session": ctx.session, "status": ("!=", "Kicked")},
			pluck="name",
			order_by="joined_at asc, name asc",
		)
		t.module_state["guesser"] = members[t.module_state["round_index"] % len(members)]
		return Transition(
			phase="chorus_clues",
			next_ts=time.time() + ctx.configuration["seconds"],
			ttl=ctx.configuration["seconds"] + 60,
			module_state=t.module_state,
			publish={"type": "one_word_chorus.clues", "phase": "chorus_clues"},
		)

	def advance_state(self, ctx, state, trigger):
		if state["phase"] == "chorus_clues" and trigger.get("command") in ("deadline", "next", "skip_turn"):
			ms = dict(state["module_state"])
			clues = [
				str(a.payload.get("value"))
				for a in accepted_actions(ctx.session, ms["round_index"])
				if a.action_type == "clue"
			]
			counts = Counter(self.norm(c) for c in clues)
			ms["clues"] = [c for c in clues if counts[self.norm(c)] == 1]
			return Transition(
				phase="round_open",
				next_ts=time.time() + ctx.configuration["seconds"],
				ttl=ctx.configuration["seconds"] + 60,
				module_state=ms,
				publish={"type": "one_word_chorus.guess", "phase": "round_open"},
			)
		return super().advance_state(ctx, state, trigger)

	def submit_action(self, ctx, state, participant, action_type, payload):
		ms = state["module_state"]
		if state["phase"] == "chorus_clues":
			if participant["name"] == ms["guesser"] or action_type != "clue":
				return ActionDecision(False, "The guesser waits for clues.")
			value = self.norm(payload.get("value"))
			if not value or len(value.split()) != 1 or len(value) > 60:
				return ActionDecision(False, "Give one word.")
			if self.norm(self.item(ms["item"]).answer) in value:
				return ActionDecision(False, "Give a clue without the secret word.")
			if any(
				a.participant == participant["name"] and a.action_type == "clue"
				for a in accepted_actions(ctx.session, ms["round_index"])
			):
				return ActionDecision(False, "Your clue is locked.")
			return ActionDecision(True, result={"ok": True, "locked": True})
		if participant["name"] != ms["guesser"]:
			return ActionDecision(False, "Let the guesser answer.")
		return super().submit_action(ctx, state, participant, action_type, payload)

	def reveal(self, ctx, state):
		t = super().reveal(ctx, state)
		ms = t.module_state
		success = any(r.get("correct") for r in ms["reveal"]["results"])
		ms["reveal"]["chorus_success"] = success
		if success:
			givers = {
				a.participant
				for a in accepted_actions(ctx.session, ms["round_index"])
				if a.action_type == "clue"
			}
			for person in givers:
				t.resolution.deltas.append(
					ScoreDelta(
						"Participant",
						person,
						1000,
						"cooperative_clue",
						f"chorus:{ms['round_index']}:{person}",
					)
				)
		return t

	def serialize_public_state(self, ctx, state):
		view = super().serialize_public_state(ctx, state)
		view.update(
			prompt=frappe._("One-word clues. Repeated clues disappear. Can your guesser find the secret?"),
			clues=state["module_state"].get("clues", []),
		)
		return view

	def serialize_player_state(self, ctx, state, participant):
		view = super().serialize_player_state(ctx, state, participant)
		ms = state["module_state"]
		view["is_guesser"] = participant["name"] == ms["guesser"]
		if state["phase"] == "chorus_clues" and not view["is_guesser"]:
			view["secret"] = self.item(ms["item"]).answer
			view["locked"] = any(
				a.participant == participant["name"] and a.action_type == "clue"
				for a in accepted_actions(ctx.session, ms["round_index"])
			)
		if state["phase"] == "round_open" and not view["is_guesser"]:
			view["locked"] = True
		return view


class SeekAndShowGame(RoundGame):
	key = "seek-and-show"

	def advance_state(self, ctx, state, trigger):
		if state["phase"] == "round_open" and trigger.get("command") in ("deadline", "next", "skip_turn"):
			return Transition(
				phase="seek_review",
				next_ts=time.time() + 86400,
				ttl=86400,
				module_state=dict(state["module_state"]),
				publish={"type": "seek_and_show.review", "phase": "seek_review"},
			)
		if state["phase"] == "seek_review":
			if trigger.get("command") != "confirm_missions":
				return None
			approved = trigger.get("approved") or []
			if not isinstance(approved, list):
				frappe.throw(frappe._("Choose the missions the room has seen."))
			allowed = {
				a.participant
				for a in accepted_actions(ctx.session, state["module_state"]["round_index"])
				if a.action_type == "submit"
			}
			if any(p not in allowed for p in approved):
				frappe.throw(frappe._("Unknown mission response."))
			state = {**state, "module_state": {**state["module_state"], "approved": approved}}
			return self.reveal(ctx, state)
		return super().advance_state(ctx, state, trigger)

	def serialize_host_state(self, ctx, state):
		view = super().serialize_host_state(ctx, state)
		if state["phase"] == "seek_review":
			view["missions"] = [
				{
					"participant": a.participant,
					"value": a.payload.get("value"),
					"nickname": frappe.db.get_value("GP Participant", a.participant, "nickname"),
				}
				for a in accepted_actions(ctx.session, state["module_state"]["round_index"])
				if a.action_type == "submit"
			]
		return view


class EscapeTogetherGame(RoundGame):
	key = "escape-together"

	def start_game(self, ctx, participants):
		items = frappe.get_all(
			"GP Game Item",
			filters={"parent": ctx.configuration["pack"], "parenttype": "GP Game Pack"},
			pluck="name",
			order_by="idx asc",
		)
		return self.open_round(
			ctx, {"items": items, "position": 0, "round_index": -1, "inventory": [], "attempts": 0}
		)

	def reveal(self, ctx, state):
		t = super().reveal(ctx, state)
		ms = t.module_state
		results = ms["reveal"]["results"]
		passed = bool(results) and sum(bool(r.get("correct")) for r in results) > len(results) / 2
		ms["reveal"]["stage_passed"] = passed
		# Escape is a shared objective. A failed attempt cannot farm individual points.
		t.resolution.deltas.clear()
		if passed:
			for r in results:
				t.resolution.deltas.append(
					ScoreDelta(
						"Participant",
						r["participant"],
						1000,
						"shared_escape",
						f"escape:{ms['round_index']}:{r['participant']}",
					)
				)
		if passed:
			ms["inventory"] = [*ms.get("inventory", []), self.item(ms["item"]).answer]
			ms["attempts"] = 0
		else:
			ms["position"] -= 1
			ms["attempts"] = ms.get("attempts", 0) + 1
		ms["reveal"]["inventory"] = ms["inventory"]
		return t

	def serialize_public_state(self, ctx, state):
		view = super().serialize_public_state(ctx, state)
		view["inventory"] = state["module_state"].get("inventory", [])
		view["escape"] = True
		view["attempts"] = state["module_state"].get("attempts", 0)
		return view
