"""Compatibility adapter: the shipped quiz, registered as a GatherPlay module.

Quizzly predated the platform and its flow (QZ Session, quizzly.engine, /quizzly
screens) is untouched on purpose -- twelve phases of tested behavior stay exactly as
they are. This module exists so the discovery home lists the game, the how-to guide
renders from the same manifest shape as every other module, and deep links land in the
live quiz. Historical QZ rows are not migrated.
"""

from __future__ import annotations

from quizzly.games import ActionDecision, GameManifest, GameModule, GameResult, Transition


class QuizGame(GameModule):
	manifest = GameManifest(
		key="quiz",
		title="Quizzly",
		version="1.0.0",
		summary="Timed live quiz questions, speed-aware scoring, streaks and a podium.",
		min_players=1,
		max_players=None,
		recommended_players="4-100+",
		typical_minutes=15,
		interaction_tags=("quiz",),
		status="Available",
		capabilities=("timer", "private_answer", "streaks", "explanations"),
		host_commands=(),
		frontend_key="quiz",
	)

	def validate_configuration(self, ctx, configuration: dict) -> dict:
		return {}

	def start_game(self, ctx, participants: list[dict]) -> Transition:
		raise NotImplementedError("the quiz runs through its own QZ Session flow")

	def submit_action(self, ctx, state, participant, action_type: str, payload: dict) -> ActionDecision:
		raise NotImplementedError("the quiz runs through its own QZ Session flow")

	def advance_state(self, ctx, state, trigger) -> Transition | None:
		raise NotImplementedError("the quiz runs through its own QZ Session flow")

	def finish_game(self, ctx, state) -> GameResult:
		raise NotImplementedError("the quiz runs through its own QZ Session flow")
