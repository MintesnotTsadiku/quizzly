"""CueCast: charades and describe-it teams game, the first native GatherPlay module.

One performer per turn sees the private prompt on their phone; the room watches the
timer. Correct (+1) and pass (0) are typed guest actions resolved against the ledger at
the buzzer. The prompt never enters a public payload or the projector snapshot: players
learn it only through their own token-gated `get_player_state` call.
"""

from __future__ import annotations

import random
import time

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
from quizzly.games.engine import GRACE_SECONDS, accepted_actions, create_teams

READY_SECONDS = 3
REVIEW_SECONDS = 6
SCOREBOARD_SECONDS = 5
SUDDEN_DEATH_SECONDS = 30
TURN_SECONDS = (30, 60, 90)
PHASE_TTL_MARGIN = 60


class CueCastGame(GameModule):
	manifest = GameManifest(
		key="cuecast",
		title="CueCast",
		version="1.0.0",
		summary="Act it or describe it: race through team prompts before the buzzer.",
		min_players=4,
		max_players=30,
		recommended_players="6–20",
		typical_minutes=20,
		interaction_tags=("acting", "teams", "performance"),
		status="Available",
		capabilities=("teams", "private_prompt", "timer"),
		host_commands=("balance_teams", "rename_team", "recolor_team", "skip_turn", "reassign_performer"),
		frontend_key="cuecast",
	)

	def validate_configuration(self, ctx, configuration: dict) -> dict:
		deck = configuration.get("deck")
		if not deck or not frappe.db.exists("GP Cue Deck", deck):
			frappe.throw(_("Pick a cue deck for this game"))
		prompt_count = frappe.db.count("GP Cue Prompt", {"parent": deck, "parenttype": "GP Cue Deck"})
		if not prompt_count:
			frappe.throw(_("That deck has no prompts yet"))
		try:
			seconds = int(configuration.get("seconds") or 60)
		except (TypeError, ValueError):
			frappe.throw(_("Round length must be a number"))
		if seconds not in TURN_SECONDS:
			frappe.throw(_("Round length must be 30, 60 or 90 seconds"))
		try:
			teams_count = int(configuration.get("teams_count") or 2)
			turns = int(configuration.get("turns_per_team") or 1)
		except (TypeError, ValueError):
			frappe.throw(_("Team counts must be numbers"))
		return {
			"deck": deck,
			"mode": frappe.db.get_value("GP Cue Deck", deck, "mode") or "Act",
			"seconds": seconds,
			"teams_count": max(2, min(6, teams_count)),
			"turns_per_team": max(1, min(3, turns)),
			"sudden_death": bool(int(configuration.get("sudden_death") or 0)),
			"prompt_count": prompt_count,
		}

	def start_game(self, ctx, participants: list[dict]) -> Transition:
		config = ctx.configuration
		teams = create_teams(ctx.session, participants, config["teams_count"])
		order = [team["name"] for team in teams]
		random.shuffle(order)
		prompts = frappe.get_all(
			"GP Cue Prompt",
			filters={"parent": config["deck"], "parenttype": "GP Cue Deck"},
			pluck="name",
		)
		random.shuffle(prompts)
		module_state = {
			"teams": [team["name"] for team in teams],
			"team_order": order,
			"sudden_death_teams": [],
			"sudden_death_done": 0,
			"turn_number": -1,
			"prompt_ids": prompts,
			"prompt_pos": 0,
			"turn_start_pos": 0,
		}
		return self.next_turn(ctx, module_state)

	# -- state machine ---------------------------------------------------------

	def advance_state(self, ctx, state, trigger) -> Transition | None:
		command = trigger.get("command")
		if command in ("deadline", "skip_turn"):
			return self.on_deadline(ctx, state)
		if command == "reassign_performer":
			return self.reassign_performer(ctx, state, trigger.get("participant"))
		return None

	def on_deadline(self, ctx, state) -> Transition:
		phase = state["phase"]
		if phase == "turn_ready":
			return self.open_turn(ctx, state)
		if phase == "turn_open":
			return self.close_turn(ctx, state)
		if phase == "turn_review":
			return self.scoreboard_transition(ctx, state)
		if phase == "scoreboard":
			return self.after_scoreboard(ctx, state)
		return None

	def next_turn(self, ctx, module_state: dict) -> Transition:
		module_state = dict(module_state)
		module_state["turn_number"] += 1
		total_regular = len(module_state["team_order"]) * ctx.configuration["turns_per_team"]
		team = module_state["team_order"][module_state["turn_number"] % len(module_state["team_order"])]
		module_state.update(
			{
				"actor_team": team,
				"round_index": module_state["turn_number"],
				"round_key": f"turn-{module_state['turn_number'] + 1}",
				"actor_participant": self.pick_performer(ctx.session, team),
			}
		)
		public = {
			"type": "cuecast.turn_ready",
			"phase": "turn_ready",
			"turn": module_state["turn_number"],
			"total_turns": total_regular,
			**self.team_views(ctx),
			"performer": self.participant_card(module_state["actor_participant"]),
		}
		return Transition(
			phase="turn_ready",
			next_ts=time.time() + READY_SECONDS,
			ttl=READY_SECONDS + PHASE_TTL_MARGIN,
			module_state=module_state,
			publish=public,
		)

	def open_turn(self, ctx, state) -> Transition:
		module_state = dict(state["module_state"])
		module_state["turn_start_pos"] = module_state["prompt_pos"]
		module_state["prompt_pos"] += 1
		seconds = module_state.pop("sudden_death_seconds", None) or ctx.configuration["seconds"]
		public = {
			"type": "cuecast.turn_started",
			"phase": "turn_open",
			"turn": module_state["turn_number"],
			**self.team_views(ctx),
			"performer": self.participant_card(module_state.get("actor_participant")),
			"solved": 0,
		}
		return Transition(
			phase="turn_open",
			next_ts=time.time() + seconds,
			ttl=seconds + PHASE_TTL_MARGIN,
			module_state=module_state,
			publish=public,
		)

	def close_turn(self, ctx, state) -> Transition:
		module_state = dict(state["module_state"])
		actions = accepted_actions(ctx.session, module_state["round_index"])
		solved_rows = [a for a in actions if a.action_type == "correct_prompt"]
		passed_count = sum(1 for a in actions if a.action_type == "pass_prompt")
		deltas = [
			ScoreDelta(
				subject_type="Team",
				subject=module_state["actor_team"],
				points=1,
				category="correct_prompt",
				idempotency_key=f"r{module_state['round_index']}:{action.name}",
			)
			for action in solved_rows
		]
		summary = {
			"team": module_state["actor_team"],
			"played": self.played_prompts(module_state, len(actions)),
			"solved_count": len(solved_rows),
			"passed_count": passed_count,
		}
		public = {
			"type": "cuecast.turn_ended",
			"phase": "turn_review",
			"turn": module_state["turn_number"],
			**summary,
			**self.team_views(ctx),
			"performer": self.participant_card(module_state.get("actor_participant")),
		}
		return Transition(
			phase="turn_review",
			next_ts=time.time() + REVIEW_SECONDS,
			ttl=REVIEW_SECONDS + PHASE_TTL_MARGIN,
			module_state=module_state,
			resolution=Resolution(summary=summary, deltas=deltas),
			publish=public,
		)

	def scoreboard_transition(self, ctx, state) -> Transition:
		next_ts = time.time() + SCOREBOARD_SECONDS
		return Transition(
			phase="scoreboard",
			next_ts=next_ts,
			ttl=SCOREBOARD_SECONDS + PHASE_TTL_MARGIN,
			module_state=dict(state["module_state"]),
			publish={"type": "platform.scoreboard_updated", "teams": self.ranked_teams(ctx)},
		)

	def after_scoreboard(self, ctx, state) -> Transition | None:
		module_state = dict(state["module_state"])
		total_regular = len(module_state["team_order"]) * ctx.configuration["turns_per_team"]
		if module_state["turn_number"] + 1 < total_regular:
			return self.next_turn(ctx, module_state)

		sd_teams = module_state.get("sudden_death_teams") or []
		if not sd_teams and ctx.configuration.get("sudden_death"):
			leaders = self.tied_leaders(ctx)
			if len(leaders) > 1:
				module_state["sudden_death_teams"] = leaders
				sd_teams = leaders
		done = module_state.get("sudden_death_done") or 0
		if done < len(sd_teams):
			team = sd_teams[done]
			module_state["sudden_death_done"] = done + 1
			module_state.update(
				{
					"actor_team": team,
					"round_index": total_regular + done,
					"round_key": f"sudden-death-{done + 1}",
					"actor_participant": self.pick_performer(ctx.session, team),
					"sudden_death_seconds": SUDDEN_DEATH_SECONDS,
				}
			)
			return Transition(
				phase="turn_ready",
				next_ts=time.time() + READY_SECONDS,
				ttl=READY_SECONDS + PHASE_TTL_MARGIN,
				module_state=module_state,
				publish={
					"type": "cuecast.sudden_death",
					"phase": "turn_ready",
					"teams": [self.team_card(team)],
					"performer": self.participant_card(module_state["actor_participant"]),
				},
			)
		return Transition(phase="podium", finished=self.finish_game(ctx, state))

	def tied_leaders(self, ctx) -> list[str]:
		teams = self.ranked_teams(ctx)
		best = teams[0]["score"] if teams else 0
		return [t["name"] for t in teams if t["score"] == best][:4]

	# -- actions ---------------------------------------------------------------

	def submit_action(self, ctx, state, participant, action_type: str, payload: dict) -> ActionDecision:
		if action_type not in ("correct_prompt", "pass_prompt"):
			return ActionDecision(accepted=False, reason="Unknown action")
		if state["phase"] != "turn_open":
			return ActionDecision(accepted=False, reason="No prompt is open right now")
		module_state = state["module_state"]
		if participant.get("name") != module_state.get("actor_participant"):
			return ActionDecision(accepted=False, reason="Only the performer can score prompts")
		if time.time() > state["deadline_ts"] + GRACE_SECONDS:
			return ActionDecision(accepted=False, reason="Time is up")

		already = accepted_actions(ctx.session, module_state["round_index"])
		prompts = module_state["prompt_ids"]
		index = module_state["turn_start_pos"] + len(already) + 1
		next_row = prompts[index % len(prompts)] if prompts else None
		return ActionDecision(accepted=True, result={"ok": True, "next_prompt": self.prompt_text(next_row)})

	# -- host commands ---------------------------------------------------------

	def handle_host_command(self, ctx, state, command: str, payload: dict) -> Transition | None:
		if command == "reassign_performer":
			return self.reassign_performer(ctx, state, payload.get("participant"))
		return None

	def reassign_performer(self, ctx, state, participant: str | None) -> Transition | None:
		if state["phase"] not in ("turn_ready", "turn_open"):
			return None
		module_state = dict(state["module_state"])
		if not participant or frappe.db.get_value(
			"GP Participant", participant, "team"
		) != module_state["actor_team"]:
			frappe.throw(_("Pick a player from the performing team"))
		module_state["actor_participant"] = participant
		return Transition(
			phase=state["phase"],
			next_ts=state["next_ts"],
			ttl=(state["next_ts"] - time.time()) + PHASE_TTL_MARGIN,
			module_state=module_state,
			publish={
				"type": "cuecast.performer_changed",
				"performer": self.participant_card(participant),
			},
		)

	# -- serializers -----------------------------------------------------------

	def serialize_public_state(self, ctx, state) -> dict:
		module_state = state["module_state"]
		view = {
			"phase": state["phase"],
			"turn": module_state.get("turn_number"),
			**self.team_views(ctx),
			"performer": self.participant_card(module_state.get("actor_participant")),
			"solved": self.solved_count(ctx, state),
		}
		if state["phase"] == "turn_review":
			actions = accepted_actions(ctx.session, module_state.get("round_index"))
			view["played"] = self.played_prompts(module_state, len(actions))
			view["solved_count"] = sum(1 for a in actions if a.action_type == "correct_prompt")
			view["passed_count"] = sum(1 for a in actions if a.action_type == "pass_prompt")
		return view

	def serialize_player_state(self, ctx, state, participant) -> dict:
		module_state = state["module_state"]
		view = {
			**self.serialize_public_state(ctx, state),
			"is_performer": participant["name"] == module_state.get("actor_participant"),
			"on_stage": participant.get("team") == module_state.get("actor_team"),
		}
		if state["phase"] == "turn_open" and view["is_performer"]:
			view["mode"] = ctx.configuration["mode"]
			view["seconds"] = module_state.get("sudden_death_seconds") or ctx.configuration["seconds"]
			prompts = module_state["prompt_ids"]
			if prompts:
				position = module_state["turn_start_pos"] + len(
					accepted_actions(ctx.session, module_state.get("round_index"))
				)
				view["prompt"] = self.prompt_text(prompts[position % len(prompts)])
		elif state["phase"] == "turn_ready" and view["is_performer"]:
			view["mode"] = ctx.configuration["mode"]
		return view

	def serialize_host_state(self, ctx, state) -> dict:
		return {**self.serialize_public_state(ctx, state), "configuration": ctx.configuration}

	def progress_metric(self, ctx, state) -> dict | None:
		if state["phase"] != "turn_open":
			return None
		return {"count": self.solved_count(ctx, state)}

	def finish_game(self, ctx, state) -> GameResult:
		ranked = self.ranked_teams(ctx)
		leaderboard = []
		for team in ranked:
			leaderboard.append({"subject_type": "Team", **team})
		return GameResult(publish={"phase": "podium", "teams": leaderboard}, leaderboard=leaderboard)

	# -- helpers ---------------------------------------------------------------

	def pick_performer(self, session: str, team: str) -> str | None:
		members = frappe.get_all(
			"GP Participant",
			filters={"session": session, "team": team, "status": ("!=", "Kicked")},
			fields=["name"],
			order_by="joined_at asc",
		)
		return members[0].name if members else None

	def ranked_teams(self, ctx) -> list[dict]:
		"""Competition ranking: ties share the rank."""
		teams = frappe.get_all(
			"GP Team",
			filters={"session": ctx.session},
			fields=["name", "team_name", "color", "score", "seed"],
			order_by="score desc, seed asc",
		)
		prev_score = None
		rank = 0
		for position, team in enumerate(teams, start=1):
			if team.score != prev_score:
				rank = position
				prev_score = team.score
			team["rank"] = rank
		return [dict(team) for team in teams]

	def team_views(self, ctx) -> dict:
		teams = frappe.get_all(
			"GP Team",
			filters={"session": ctx.session},
			fields=["name", "team_name", "color", "score"],
			order_by="seed asc",
		)
		return {"teams": [dict(team) for team in teams]}

	def team_card(self, team: str) -> dict | None:
		row = frappe.db.get_value("GP Team", team, ["name", "team_name", "color"], as_dict=True)
		return dict(row) if row else None

	def participant_card(self, participant: str | None) -> dict | None:
		if not participant:
			return None
		row = frappe.db.get_value(
			"GP Participant", participant, ["name", "nickname", "avatar"], as_dict=True
		)
		return dict(row) if row else None

	def solved_count(self, ctx, state) -> int:
		module_state = state["module_state"]
		round_name = self.round_name_for(ctx, module_state.get("round_index"))
		if not round_name:
			return 0
		return frappe.db.count(
			"GP Action", {"round": round_name, "action_type": "correct_prompt", "accepted": 1}
		)

	def round_name_for(self, ctx, round_index: int | None) -> str | None:
		if round_index is None:
			return None
		return frappe.db.get_value("GP Round", {"session": ctx.session, "round_index": round_index})

	def prompt_text(self, row_id: str | None) -> str | None:
		if not row_id:
			return None
		return frappe.db.get_value("GP Cue Prompt", row_id, "prompt_text")

	def played_prompts(self, module_state, count: int) -> list[str]:
		start = module_state["turn_start_pos"]
		prompts = module_state["prompt_ids"]
		rows = [prompts[(start + offset) % len(prompts)] for offset in range(max(0, count))]
		texts = frappe.get_all(
			"GP Cue Prompt", filters={"name": ("in", rows)}, fields=["name", "prompt_text"]
		)
		by_row = {row.name: row.prompt_text for row in texts}
		return [by_row.get(row_id, "") for row_id in rows]
