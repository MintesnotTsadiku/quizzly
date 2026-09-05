"""Crowd Compass: vote for yourself, predict the room, watch the reveal.

Two-stage rounds with hidden aggregation: the distribution is a reveal-time secret,
public state carries participation counts only. Full scoring depth: plurality
prediction (+500), own-vote-matches-room (+100), team-match (+100), tiered
percentage-estimation bonus, weighted rank-choice prompts (first = 2, second = 1),
live host prompts, voidable rounds and team-average standings.
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
from quizzly.games.crowd_compass.progression import round_arc
from quizzly.games.engine import accepted_actions, create_teams

PROMPT_READY_SECONDS = 4
REVEAL_SECONDS = 9
SCOREBOARD_SECONDS = 6
STAGE_SECONDS = (10, 15, 20)
ESTIMATION_TIERS = ((3, 300), (7, 150), (12, 50))
PHASE_TTL_MARGIN = 60


class CrowdCompassGame(GameModule):
	manifest = GameManifest(
		key="crowd-compass",
		title="Crowd Compass",
		version="1.0.0",
		summary="Vote for yourself, predict the room, and see who reads the crowd best.",
		min_players=3,
		max_players=None,
		recommended_players="15-100+",
		typical_minutes=15,
		interaction_tags=("voting", "prediction", "icebreaker"),
		status="Available",
		capabilities=("voting", "hidden_aggregation", "timer", "teams"),
		host_commands=(
			"balance_teams",
			"rename_team",
			"recolor_team",
			"skip_turn",
			"push_prompt",
			"void_prompt",
		),
		frontend_key="crowd-compass",
	)

	def validate_configuration(self, ctx, configuration: dict) -> dict:
		pack = configuration.get("pack") or None
		ranked = False
		prompt_count = 0
		if pack:
			if not frappe.db.exists("GP Crowd Pack", pack):
				frappe.throw(_("Pick a crowd pack for this game"))
			prompt_count = frappe.db.count("GP Crowd Prompt", {"parent": pack, "parenttype": "GP Crowd Pack"})
			if not prompt_count:
				frappe.throw(_("That pack has no prompts yet"))
			ranked = bool(frappe.db.get_value("GP Crowd Pack", pack, "ranked"))

		def stage(key: str, default: int) -> int:
			try:
				value = int(configuration.get(key) or default)
			except (TypeError, ValueError):
				frappe.throw(_("Stage lengths must be numbers"))
			if value not in STAGE_SECONDS:
				frappe.throw(_("Stage lengths must be 10, 15 or 20 seconds"))
			return value

		try:
			rounds = int(configuration.get("rounds") or 0)
			quorum = int(configuration.get("quorum") or 1)
			teams_count = int(configuration.get("teams_count") or 2)
		except (TypeError, ValueError):
			frappe.throw(_("Round and team counts must be numbers"))

		scoring_mode = configuration.get("scoring_mode") or "Individual"
		if scoring_mode not in ("Individual", "Team average"):
			frappe.throw(_("Unknown scoring mode"))
		room_match = configuration.get("room_match")
		try:
			arc = bool(int(configuration.get("gathering_arc", 1)))
		except (TypeError, ValueError):
			frappe.throw(_("Choose a valid round journey."))
		return {
			"pack": pack,
			"ranked": ranked,
			"vote_seconds": stage("vote_seconds", 15),
			"prediction_seconds": stage("prediction_seconds", 15),
			"estimation": bool(int(configuration.get("estimation") or 0)),
			"scoring_mode": scoring_mode,
			"teams_count": max(2, min(6, teams_count)),
			"room_match": True if room_match is None else bool(int(room_match)),
			"team_match": scoring_mode == "Team average" and bool(int(configuration.get("team_match") or 0)),
			"quorum": max(1, min(100, quorum)),
			"rounds": max(0, min(50, rounds)),
			"prompt_count": prompt_count,
			"gathering_arc": bool(
				arc and pack and min(max(0, min(50, rounds)) or prompt_count, prompt_count) >= 3
			),
		}

	def start_game(self, ctx, participants: list[dict]) -> Transition:
		config = ctx.configuration
		teams = []
		if config["scoring_mode"] == "Team average":
			teams = create_teams(ctx.session, participants, config["teams_count"])
		module_state = {
			"queue": self.build_queue(ctx),
			"position": 0,
			"round_index": -1,
			"teams_mode": bool(teams),
			"voided": [],
		}
		module_state["planned_rounds"] = len(module_state["queue"])
		return self.open_prompt(ctx, module_state)

	def build_queue(self, ctx) -> list[dict]:
		"""Pack prompts shuffled (capped by `rounds`); live prompts append at runtime."""
		config = ctx.configuration
		if not config.get("pack"):
			return []
		rows = frappe.get_all(
			"GP Crowd Prompt",
			filters={"parent": config["pack"], "parenttype": "GP Crowd Pack"},
			fields=["name", "prompt_text", "choice_1", "choice_2", "choice_3", "choice_4"],
			order_by="idx asc",
		)
		prompts = [self.prompt_row_dict(row) for row in rows]
		random.shuffle(prompts)
		if config["rounds"]:
			prompts = prompts[: config["rounds"]]
		return prompts

	def prompt_row_dict(self, row) -> dict:
		return {
			"prompt": row.prompt_text,
			"choices": [
				{"id": str(number), "text": (row.get(f"choice_{number}") or "").strip()}
				for number in range(1, 5)
				if (row.get(f"choice_{number}") or "").strip()
			],
			"live": False,
		}

	# -- state machine ---------------------------------------------------------

	def advance_state(self, ctx, state, trigger) -> Transition | None:
		command = trigger.get("command")
		if command in ("deadline", "skip_turn", "next"):
			return self.on_deadline(ctx, state)
		if command == "push_prompt":
			return self.push_prompt(ctx, state, trigger)
		if command == "void_prompt":
			return self.void_prompt(ctx, state)
		return None

	def on_deadline(self, ctx, state) -> Transition | None:
		phase = state["phase"]
		if phase == "intermission":
			return self.open_prompt(ctx, state["module_state"])
		if phase == "prompt_open":
			return self.open_prediction(ctx, state)
		if phase == "prediction_open":
			return self.reveal(ctx, state)
		if phase == "reveal":
			return self.scoreboard_transition(ctx, state)
		if phase == "scoreboard":
			return self.after_scoreboard(ctx, state)
		return None

	def open_prompt(self, ctx, module_state: dict) -> Transition | None:
		module_state = dict(module_state)
		position = module_state["position"]
		if position >= len(module_state["queue"]):
			if position == 0:
				# blank room: hold an intermission until the host composes a live prompt
				return Transition(
					phase="intermission",
					next_ts=time.time() + 30,
					ttl=60,
					module_state=module_state,
					publish={"type": "crowd_compass.intermission", "phase": "intermission"},
				)
			# finish_game expects the full state envelope, not the bare module state
			return Transition(phase="podium", finished=self.finish_game(ctx, {"module_state": module_state}))
		module_state.update(
			{
				"round_index": module_state["round_index"] + 1,
				"round_key": f"prompt-{position + 1}",
				"current": module_state["queue"][position],
				"position": position + 1,
			}
		)
		module_state["arc"] = round_arc(
			ctx.configuration.get("gathering_arc"),
			position + 1,
			module_state.get("planned_rounds", len(module_state["queue"])),
		)
		public = {
			"type": "crowd_compass.vote_opened",
			"arc": module_state.get("arc"),
			"phase": "prompt_open",
			"turn": position,
			"total": len(module_state["queue"]),
			**self.standings(ctx, module_state, ranked=False),
			"prompt": module_state["current"]["prompt"],
			"choices": module_state["current"]["choices"],
			"ranked": ctx.configuration["ranked"],
			"voted": 0,
		}
		return Transition(
			phase="prompt_open",
			next_ts=time.time() + ctx.configuration["vote_seconds"],
			ttl=ctx.configuration["vote_seconds"] + PHASE_TTL_MARGIN,
			module_state=module_state,
			publish=public,
		)

	def open_prediction(self, ctx, state) -> Transition:
		module_state = dict(state["module_state"])
		public = {
			"type": "crowd_compass.prediction_opened",
			"arc": module_state.get("arc"),
			"phase": "prediction_open",
			"turn": module_state["position"] - 1,
			"total": len(module_state["queue"]),
			**self.standings(ctx, module_state, ranked=False),
			"prompt": module_state["current"]["prompt"],
			"choices": module_state["current"]["choices"],
			"ranked": ctx.configuration["ranked"],
			"estimation": ctx.configuration["estimation"],
			"voted": self.action_count(ctx, state, "cast_vote"),
			"predicted": 0,
		}
		return Transition(
			phase="prediction_open",
			next_ts=time.time() + ctx.configuration["prediction_seconds"],
			ttl=ctx.configuration["prediction_seconds"] + PHASE_TTL_MARGIN,
			module_state=module_state,
			publish=public,
		)

	def reveal(self, ctx, state) -> Transition:
		module_state = dict(state["module_state"])
		votes = [
			a
			for a in accepted_actions(ctx.session, module_state["round_index"])
			if a.action_type == "cast_vote"
		]
		predictions = [
			a
			for a in accepted_actions(ctx.session, module_state["round_index"])
			if a.action_type == "make_prediction"
		]
		choices = module_state["current"]["choices"]
		choice_ids = [c["id"] for c in choices]

		firsts = [self.pick_choice(a.payload) for a in votes]
		seconds = [self.pick_second(a.payload) for a in votes if self.pick_second(a.payload)]
		if ctx.configuration["ranked"]:
			tally = {cid: firsts.count(cid) * 2 + seconds.count(cid) for cid in choice_ids}
		else:
			tally = {cid: firsts.count(cid) for cid in choice_ids}
		total_weight = sum(tally.values()) or 1
		best = max(tally.values()) if tally else 0
		plurality = sorted(cid for cid, count in tally.items() if count == best and count > 0)

		quorum_met = len(votes) >= ctx.configuration["quorum"]
		deltas: list[ScoreDelta] = []
		if quorum_met and plurality:
			for prediction in predictions:
				pick = self.pick_choice(prediction.payload)
				participant = prediction.participant
				if pick in plurality:
					deltas.append(
						ScoreDelta(
							subject_type="Participant",
							subject=participant,
							points=(module_state.get("arc") or {}).get("prediction_points", 500),
							category="correct_prediction",
							idempotency_key=f"r{module_state['round_index']}:{prediction.name}:predict",
						)
					)
					estimate = self.pick_estimate(prediction.payload)
					if estimate is not None and ctx.configuration["estimation"]:
						share = tally.get(pick, 0) / total_weight * 100
						points = self.estimation_bonus(estimate, share)
						if points:
							deltas.append(
								ScoreDelta(
									subject_type="Participant",
									subject=participant,
									points=points,
									category="estimation_bonus",
									idempotency_key=f"r{module_state['round_index']}:{prediction.name}:estimate",
									raw_metric={"estimate": estimate, "actual": round(share, 1)},
								)
							)
			if ctx.configuration["room_match"]:
				for vote in votes:
					if self.pick_choice(vote.payload) in plurality:
						deltas.append(
							ScoreDelta(
								subject_type="Participant",
								subject=vote.participant,
								points=100,
								category="room_match",
								idempotency_key=f"r{module_state['round_index']}:{vote.name}:room",
							)
						)
			if ctx.configuration["team_match"]:
				for vote in votes:
					team_id = self.team_of(ctx.session, vote.participant)
					if not team_id:
						continue
					team_plurality = self.team_plurality(
						votes, team_id, choice_ids, ctx.configuration["ranked"]
					)
					if self.pick_choice(vote.payload) in team_plurality:
						deltas.append(
							ScoreDelta(
								subject_type="Participant",
								subject=vote.participant,
								points=100,
								category="team_match",
								idempotency_key=f"r{module_state['round_index']}:{vote.name}:team",
							)
						)

		distribution = tally
		module_state["plurality"] = plurality
		summary = {
			"prompt": module_state["current"]["prompt"],
			"choices": choices,
			"ranked": ctx.configuration["ranked"],
			"arc": module_state.get("arc"),
			"tally": tally,
			"distribution": distribution,
			"plurality": plurality,
			"quorum_met": quorum_met,
			"votes": len(votes),
			"predictions": len(predictions),
		}
		public = {
			"type": "crowd_compass.revealed",
			"arc": module_state.get("arc"),
			"phase": "reveal",
			"turn": module_state["position"] - 1,
			"total": len(module_state["queue"]),
			**self.standings(ctx, module_state, ranked=False),
			"prompt": module_state["current"]["prompt"],
			"choices": choices,
			"distribution": distribution,
			"plurality": plurality,
			"quorum_met": quorum_met,
			"votes": len(votes),
			"predictions": len(predictions),
			"ranked": ctx.configuration["ranked"],
		}
		return Transition(
			phase="reveal",
			next_ts=time.time() + REVEAL_SECONDS,
			ttl=REVEAL_SECONDS + PHASE_TTL_MARGIN,
			module_state=module_state,
			resolution=Resolution(summary=summary, deltas=deltas),
			publish=public,
		)

	def scoreboard_transition(self, ctx, state) -> Transition:
		module_state = dict(state["module_state"])
		next_ts = time.time() + SCOREBOARD_SECONDS
		standings = self.standings(ctx, module_state, ranked=True)
		voided = module_state.get("voided") or []
		public = {
			"type": "platform.scoreboard_updated",
			"arc": module_state.get("arc"),
			"phase": "scoreboard",
			"turn": module_state["position"] - 1,
			"total": len(module_state["queue"]),
			**standings,
			"voided": voided,
			"last_voided": module_state["round_index"] in voided,
		}
		return Transition(
			phase="scoreboard",
			next_ts=next_ts,
			ttl=SCOREBOARD_SECONDS + PHASE_TTL_MARGIN,
			module_state=module_state,
			publish=public,
		)

	def after_scoreboard(self, ctx, state) -> Transition | None:
		return self.open_prompt(ctx, state["module_state"])

	# -- actions ---------------------------------------------------------------

	def submit_action(self, ctx, state, participant, action_type: str, payload: dict) -> ActionDecision:
		if action_type == "cast_vote":
			return self.cast_vote(ctx, state, participant, payload)
		if action_type == "make_prediction":
			return self.make_prediction(ctx, state, participant, payload)
		return ActionDecision(accepted=False, reason="Unknown action")

	def cast_vote(self, ctx, state, participant, payload: dict) -> ActionDecision:
		if state["phase"] != "prompt_open":
			return ActionDecision(accepted=False, reason="Voting is closed for this prompt")
		choices = state["module_state"]["current"]["choices"]
		first = self.pick_choice(payload, valid=choices)
		if not first:
			return ActionDecision(accepted=False, reason="Pick one of the choices")
		second = None
		if ctx.configuration["ranked"]:
			second = self.pick_choice(payload, key="second", valid=choices)
			if not second:
				return ActionDecision(accepted=False, reason="Rank your first and second choice")
			if second == first:
				return ActionDecision(accepted=False, reason="Pick two different choices")
		if self.already_acted(ctx, state, participant["name"], "cast_vote"):
			return ActionDecision(accepted=False, reason="You already voted on this prompt")
		result = {"ok": True}
		if second:
			result["second"] = second
		return ActionDecision(accepted=True, result=result)

	def make_prediction(self, ctx, state, participant, payload: dict) -> ActionDecision:
		if state["phase"] != "prediction_open":
			return ActionDecision(accepted=False, reason="Predictions are closed")
		choices = state["module_state"]["current"]["choices"]
		pick = self.pick_choice(payload, valid=choices)
		if not pick:
			return ActionDecision(accepted=False, reason="Pick one of the choices")
		estimate = payload.get("estimate")
		if ctx.configuration["estimation"]:
			try:
				estimate = int(round(float(estimate)))
			except (TypeError, ValueError):
				return ActionDecision(accepted=False, reason="Slide in your share estimate")
			estimate = max(0, min(100, estimate))
		else:
			estimate = None
		if self.already_acted(ctx, state, participant["name"], "make_prediction"):
			return ActionDecision(accepted=False, reason="You already predicted on this prompt")
		return ActionDecision(accepted=True, result={"ok": True, "estimate": estimate})

	def already_acted(self, ctx, state, participant: str, action_type: str) -> bool:
		"""Per-round dedupe. The global action unique key is client-idempotency-shaped
		(CueCast taps the same type repeatedly), so the module owns this rule."""
		module_state = state["module_state"]
		round_index = module_state.get("round_index")
		for action in accepted_actions(ctx.session, round_index):
			if action.action_type == action_type and action.participant == participant:
				return True
		return False

	# -- host commands ---------------------------------------------------------

	def handle_host_command(self, ctx, state, command: str, payload: dict) -> Transition | None:
		if command == "push_prompt":
			return self.push_prompt(ctx, state, payload)
		if command == "void_prompt":
			return self.void_prompt(ctx, state)
		return None

	def push_prompt(self, ctx, state, payload: dict) -> Transition | None:
		"""Compose a prompt on the fly and queue it next. Blank-room sessions live
		entirely on these; pushing into an intermission wakes the room at once."""
		text = (payload.get("prompt") or "").strip()
		choices = [
			{"id": str(number), "text": (payload.get(f"choice_{number}") or "").strip()}
			for number in range(1, 5)
		]
		choices = [c for c in choices if c["text"]]
		if not text or len(choices) < 2:
			frappe.throw(_("A live prompt needs text and at least two choices"))
		module_state = dict(state["module_state"])
		queue = list(module_state["queue"])
		prompt = {"prompt": text, "choices": choices, "live": True}
		if ctx.configuration.get("gathering_arc"):
			queue.append(prompt)  # Keep the announced finale in place; extra prompts are encores.
		else:
			queue.insert(module_state["position"], prompt)
		module_state["queue"] = queue
		wake = time.time() + 1 if state["phase"] == "intermission" else state["next_ts"]
		return Transition(
			phase=state["phase"],
			next_ts=wake,
			ttl=max(60.0, (wake - time.time()) + PHASE_TTL_MARGIN),
			module_state=module_state,
			publish={"type": "crowd_compass.prompt_queued", "total": len(queue)},
		)

	def void_prompt(self, ctx, state) -> Transition | None:
		"""Throw out the last resolved prompt: compensating events reverse every delta
		it earned, and the scoreboard says so."""
		module_state = dict(state["module_state"])
		round_index = module_state["round_index"]
		if round_index in (module_state.get("voided") or []):
			return None
		round_name = frappe.db.get_value("GP Round", {"session": ctx.session, "round_index": round_index})
		if not round_name:
			return None
		events = frappe.get_all(
			"GP Score Event",
			filters={"session": ctx.session, "round_index": round_index},
			fields=["name", "subject_type", "subject", "points", "idempotency_key"],
		)
		deltas = [
			ScoreDelta(
				subject_type=event.subject_type,
				subject=event.subject,
				points=-event.points,
				category="void_reversal",
				idempotency_key=f"void:{event.idempotency_key}",
			)
			for event in events
			if event.points
		]
		module_state["voided"] = list(module_state.get("voided") or []) + [round_index]
		return Transition(
			phase=state["phase"],
			next_ts=state["next_ts"],
			ttl=(state["next_ts"] - time.time()) + PHASE_TTL_MARGIN,
			module_state=module_state,
			resolution=Resolution(summary={"voided": round_index}, deltas=deltas),
			publish={"type": "crowd_compass.prompt_voided", "round_index": round_index},
		)

	# -- serializers -----------------------------------------------------------

	def serialize_public_state(self, ctx, state) -> dict:
		module_state = state["module_state"]
		current = module_state.get("current") or {}
		view = {
			"arc": module_state.get("arc"),
			"phase": state["phase"],
			"turn": module_state.get("position", 1) - 1,
			"total": len(module_state.get("queue") or []),
			"ranked": ctx.configuration["ranked"],
			**self.standings(ctx, module_state, ranked=False),
		}
		if state["phase"] in ("prompt_open", "prediction_open", "reveal"):
			view["prompt"] = current.get("prompt")
			view["choices"] = current.get("choices")
		if state["phase"] == "prompt_open":
			view["voted"] = self.action_count(ctx, state, "cast_vote")
		if state["phase"] == "prediction_open":
			view["voted"] = self.action_count(ctx, state, "cast_vote")
			view["predicted"] = self.action_count(ctx, state, "make_prediction")
			view["estimation"] = ctx.configuration["estimation"]
		if state["phase"] == "reveal":
			view.update(self.reveal_view(ctx, state))
		return view

	def serialize_player_state(self, ctx, state, participant) -> dict:
		view = {**self.serialize_public_state(ctx, state)}
		name = participant["name"]
		if state["phase"] in ("prompt_open", "prediction_open", "reveal"):
			vote = self.own_action(ctx, state, name, "cast_vote")
			prediction = self.own_action(ctx, state, name, "make_prediction")
			view["my_vote"] = vote and self.pick_choice(vote.payload)
			view["my_second"] = vote and self.pick_second(vote.payload)
			view["my_prediction"] = prediction and self.pick_choice(prediction.payload)
			view["my_estimate"] = prediction and self.pick_estimate(prediction.payload)
		if state["phase"] == "reveal":
			view["my_points"] = self.round_points(ctx, name, state["module_state"].get("round_index"))
		return view

	def serialize_host_state(self, ctx, state) -> dict:
		view = self.serialize_public_state(ctx, state)
		if state["phase"] == "prediction_open":
			# participation without premature distribution
			view["vote_breakdown_hidden"] = True
		return {**view, "configuration": ctx.configuration}

	def progress_metric(self, ctx, state) -> dict | None:
		if state["phase"] == "prompt_open":
			return {"phase": "prompt_open", "count": self.action_count(ctx, state, "cast_vote")}
		if state["phase"] == "prediction_open":
			return {"phase": "prediction_open", "count": self.action_count(ctx, state, "make_prediction")}
		return None

	def is_presentation_phase(self, phase: str) -> bool:
		return phase in {"reveal", "scoreboard", "podium"}

	def finish_game(self, ctx, state) -> GameResult:
		module_state = state.get("module_state") or {}
		if module_state.get("teams_mode"):
			return self.team_result(ctx)
		return self.individual_result(ctx)

	def individual_result(self, ctx) -> GameResult:
		rows = frappe.get_all(
			"GP Participant",
			filters={"session": ctx.session, "status": ("!=", "Kicked")},
			fields=["name", "nickname", "avatar", "score", "joined_at"],
			order_by="score desc, joined_at asc",
		)
		leaderboard = []
		prev_score = None
		rank = 0
		for position, row in enumerate(rows, start=1):
			if row.score != prev_score:
				rank = position
				prev_score = row.score
			leaderboard.append(
				{
					"subject_type": "Participant",
					"name": row.name,
					"team_name": row.nickname,
					"color": TEAM_COLOR_CYCLE[(position - 1) % len(TEAM_COLOR_CYCLE)],
					"score": row.score,
					"rank": rank,
					"avatar": row.avatar,
				}
			)
		return GameResult(publish={"phase": "podium", "teams": leaderboard}, leaderboard=leaderboard)

	def team_result(self, ctx) -> GameResult:
		"""Team display score = average of member scores; the ledger stays per-player."""
		teams = frappe.get_all(
			"GP Team",
			filters={"session": ctx.session},
			fields=["name", "team_name", "color", "seed"],
			order_by="seed asc",
		)
		rows = []
		for team in teams:
			members = frappe.get_all(
				"GP Participant",
				filters={"session": ctx.session, "team": team.name, "status": ("!=", "Kicked")},
				fields=["score"],
			)
			average = round(sum(m.score for m in members) / len(members)) if members else 0
			rows.append(
				{"name": team.name, "team_name": team.team_name, "color": team.color, "score": average}
			)
		rows.sort(key=lambda r: (-r["score"], r["team_name"]))
		leaderboard = []
		prev_score = None
		rank = 0
		for position, row in enumerate(rows, start=1):
			if row["score"] != prev_score:
				rank = position
				prev_score = row["score"]
			leaderboard.append({"subject_type": "Team", **row, "rank": rank})
		return GameResult(publish={"phase": "podium", "teams": leaderboard}, leaderboard=leaderboard)

	# -- helpers ---------------------------------------------------------------

	def standings(self, ctx, module_state, ranked: bool) -> dict:
		"""Platform-shaped rows for the shells; team average or individual."""
		if module_state.get("teams_mode"):
			teams = frappe.get_all(
				"GP Team",
				filters={"session": ctx.session},
				fields=["name", "team_name", "color", "seed"],
				order_by="seed asc",
			)
			rows = []
			for team in teams:
				members = frappe.get_all(
					"GP Participant",
					filters={"session": ctx.session, "team": team.name, "status": ("!=", "Kicked")},
					fields=["score"],
				)
				average = round(sum(m.score for m in members) / len(members)) if members else 0
				rows.append(
					{"name": team.name, "team_name": team.team_name, "color": team.color, "score": average}
				)
			rows.sort(key=lambda r: (-r["score"], r["team_name"]))
			if ranked:
				prev_score = None
				rank = 0
				for position, row in enumerate(rows, start=1):
					if row["score"] != prev_score:
						rank = position
						prev_score = row["score"]
					row["rank"] = rank
			return {"teams": rows}

		rows = frappe.get_all(
			"GP Participant",
			filters={"session": ctx.session, "status": ("!=", "Kicked")},
			fields=["name", "nickname", "avatar", "score"],
			order_by="joined_at asc",
		)
		rows = sorted(rows, key=lambda r: (-r.score, r.joined_at))
		teams = []
		for position, row in enumerate(rows, start=1):
			teams.append(
				{
					"name": row.name,
					"team_name": row.nickname,
					"color": TEAM_COLOR_CYCLE[(position - 1) % len(TEAM_COLOR_CYCLE)],
					"score": row.score,
					"rank": position,
					"avatar": row.avatar,
				}
			)
		return {"teams": teams[:25], "participants_mode": True}

	def reveal_view(self, ctx, state) -> dict:
		module_state = state["module_state"]
		actions = accepted_actions(ctx.session, module_state["round_index"])
		votes = [a for a in actions if a.action_type == "cast_vote"]
		choices = module_state["current"]["choices"]
		choice_ids = [c["id"] for c in choices]
		firsts = [self.pick_choice(a.payload) for a in votes]
		seconds = [self.pick_second(a.payload) for a in votes if self.pick_second(a.payload)]
		if ctx.configuration["ranked"]:
			distribution = {cid: firsts.count(cid) * 2 + seconds.count(cid) for cid in choice_ids}
		else:
			distribution = {cid: firsts.count(cid) for cid in choice_ids}
		return {
			"distribution": distribution,
			"plurality": module_state.get("plurality") or [],
			"votes": len(votes),
			"predictions": sum(a.action_type == "make_prediction" for a in actions),
			"quorum_met": len(votes) >= ctx.configuration["quorum"],
			"voided": module_state["round_index"] in (module_state.get("voided") or []),
		}

	def action_count(self, ctx, state, action_type: str) -> int:
		module_state = state["module_state"]
		round_index = module_state.get("round_index")
		round_name = frappe.db.get_value("GP Round", {"session": ctx.session, "round_index": round_index})
		if not round_name:
			return 0
		return frappe.db.count("GP Action", {"round": round_name, "action_type": action_type, "accepted": 1})

	def own_action(self, ctx, state, participant: str, action_type: str):
		module_state = state["module_state"]
		for action in accepted_actions(ctx.session, module_state.get("round_index")):
			if action.action_type == action_type and action.participant == participant:
				return action
		return None

	def round_points(self, ctx, participant: str, round_index: int | None) -> int:
		if round_index is None:
			return 0
		rows = frappe.get_all(
			"GP Score Event",
			filters={"session": ctx.session, "round_index": round_index, "subject": participant},
			fields=["points"],
		)
		return sum(row.points for row in rows)

	def team_of(self, session: str, participant: str) -> str | None:
		return frappe.db.get_value("GP Participant", participant, "team")

	def team_plurality(self, votes, team_id: str, choice_ids: list[str], ranked: bool) -> list[str]:
		members = set(frappe.get_all("GP Participant", filters={"team": team_id}, pluck="name"))
		team_votes = [v for v in votes if v.participant in members]
		firsts = [self.pick_choice(v.payload) for v in team_votes]
		seconds = [self.pick_second(v.payload) for v in team_votes if self.pick_second(v.payload)]
		if ranked:
			tally = {cid: firsts.count(cid) * 2 + seconds.count(cid) for cid in choice_ids}
		else:
			tally = {cid: firsts.count(cid) for cid in choice_ids}
		best = max(tally.values()) if tally else 0
		return sorted(cid for cid, count in tally.items() if count == best and count > 0)

	def estimation_bonus(self, estimate: int, actual: float) -> int:
		error = abs(estimate - actual)
		for threshold, points in ESTIMATION_TIERS:
			if error <= threshold:
				return points
		return 0

	def pick_choice(self, payload: dict, key: str = "choice", valid: list | None = None) -> str | None:
		value = str(payload.get(key) or "").strip()
		if valid is not None and value not in [c["id"] for c in valid]:
			return None
		return value or None

	def pick_second(self, payload: dict) -> str | None:
		return self.pick_choice(payload, key="second")

	def pick_estimate(self, payload: dict):
		estimate = payload.get("estimate")
		if estimate in (None, ""):
			return None
		try:
			return int(round(float(estimate)))
		except (TypeError, ValueError):
			return None


TEAM_COLOR_CYCLE = ["ember", "lagoon", "gold", "orchid"]
