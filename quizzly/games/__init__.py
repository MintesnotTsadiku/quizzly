"""GatherPlay game-module contract and registry.

A module owns its rules, content semantics, phases, allowed actions and serializers.
It never publishes realtime events, mints tokens or mutates materialized totals: every
method returns plain values and value objects, and the platform orchestrator
(quizzly.games.engine) persists state, records rounds, writes score events and
broadcasts on the module's behalf.

Modules register through the ``quizzly_game_modules`` hook as dotted paths to their
GameModule subclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import frappe


@dataclass(frozen=True)
class GameManifest:
	key: str
	title: str
	version: str
	summary: str
	min_players: int
	max_players: int | None
	# discovery metadata for the /play catalog and how-to pages
	recommended_players: str = ""
	typical_minutes: int = 0
	interaction_tags: tuple[str, ...] = ()
	status: str = "Available"  # Available | Beta | Coming Soon
	capabilities: tuple[str, ...] = ()
	host_commands: tuple[str, ...] = ()
	frontend_key: str = ""


@dataclass(frozen=True)
class GameContext:
	"""Everything a module may read about the session it is playing in."""

	session: str
	pin: str
	game_key: str
	configuration: dict


@dataclass(frozen=True)
class ScoreDelta:
	subject_type: str  # Participant | Team
	subject: str
	points: int
	category: str
	idempotency_key: str
	raw_metric: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Resolution:
	"""A settled round: the public reveal payload plus the ledger entries it earned."""

	summary: dict
	deltas: list[ScoreDelta] = field(default_factory=list)


@dataclass(frozen=True)
class GameResult:
	"""Final standings. `publish` paints every podium; `leaderboard` is persisted."""

	publish: dict
	leaderboard: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class Transition:
	"""One state-machine step for the orchestrator to persist and broadcast.

	`resolution` settles the round that is closing with this step (round row marked,
	score events written). `finished` ends the game instead of parking a next phase.
	"""

	phase: str
	next_ts: float | None = None
	ttl: float | None = None
	module_state: dict = field(default_factory=dict)
	publish: dict | None = None
	resolution: Resolution | None = None
	finished: GameResult | None = None


class UnsupportedCommand(Exception):
	pass


class GameModule:
	manifest: GameManifest

	def validate_configuration(self, ctx: GameContext, configuration: dict) -> dict:
		"""Raise on a broken setup; return the normalized configuration snapshot."""
		raise NotImplementedError

	def start_game(self, ctx: GameContext, participants: list[dict]) -> Transition:
		"""Lobby -> first phase. Receives the joined participants (name, nickname, avatar)."""
		raise NotImplementedError

	def submit_action(
		self, ctx: GameContext, state: dict, participant: dict, action_type: str, payload: dict
	) -> "ActionDecision":
		raise NotImplementedError

	def advance_state(self, ctx: GameContext, state: dict, trigger: dict) -> Transition | None:
		"""Walk one tick. `trigger` is ``{"command": "deadline"}`` or a popped host
		control ``{"command": ..., **payload}``. None means nothing to do yet."""
		raise NotImplementedError

	def handle_host_command(
		self, ctx: GameContext, state: dict, command: str, payload: dict
	) -> Transition | None:
		raise UnsupportedCommand(command)

	def serialize_public_state(self, ctx: GameContext, state: dict) -> dict:
		"""Safe for everyone who knows the PIN: this paints the projector."""
		return {}

	def serialize_player_state(self, ctx: GameContext, state: dict, participant: dict) -> dict:
		"""One player's private view. Secrets stay scoped to the role they belong to."""
		return {}

	def serialize_host_state(self, ctx: GameContext, state: dict) -> dict:
		return {}

	def progress_metric(self, ctx: GameContext, state: dict) -> dict | None:
		"""Live counter for the projector, or None when this phase has none."""
		return None

	def finish_game(self, ctx: GameContext, state: dict) -> GameResult:
		"""Forced ending (host end command, abandoned session). The default ranks
		teams by their materialized score; participant games override it."""
		teams = frappe.get_all(
			"GP Team",
			filters={"session": ctx.session},
			fields=["name", "team_name", "color", "score"],
			order_by="score desc",
		)
		leaderboard = [
			{
				"subject_type": "Team",
				"name": team.name,
				"team_name": team.team_name,
				"color": team.color,
				"score": team.score,
			}
			for team in teams
		]
		return GameResult(publish={"phase": "podium", "leaderboard": leaderboard}, leaderboard=leaderboard)


@dataclass(frozen=True)
class ActionDecision:
	accepted: bool
	reason: str | None = None
	# private result handed back to the acting player only (e.g. their next prompt)
	result: dict | None = None


def load_module(dotted_path: str) -> GameModule:
	target = frappe.get_attr(dotted_path)
	instance = target() if isinstance(target, type) else target
	if not isinstance(instance, GameModule):
		raise TypeError(f"{dotted_path} is not a GameModule")
	return instance


_REGISTRY: dict[str, GameModule] | None = None


def registry(refresh: bool = False) -> dict[str, GameModule]:
	"""game_key -> module instance, discovered once per worker from the hooks."""
	global _REGISTRY
	if _REGISTRY is None or refresh:
		registry_map: dict[str, GameModule] = {}
		for dotted_path in frappe.get_hooks("quizzly_game_modules") or []:
			module = load_module(dotted_path)
			key = module.manifest.key
			if key in registry_map:
				raise ValueError(f"Duplicate game module key: {key}")
			registry_map[key] = module
		_REGISTRY = registry_map
	return _REGISTRY


def get_game_module(game_key: str) -> GameModule:
	try:
		return registry()[game_key]
	except KeyError:
		frappe.throw(f"Unknown game: {game_key}")


def manifests() -> list[GameManifest]:
	return [module.manifest for module in registry().values()]
