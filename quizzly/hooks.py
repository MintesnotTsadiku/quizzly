app_name = "quizzly"
app_title = "Quizzly"
app_publisher = "Gajendra Nishad"
app_description = "Real-time multiplayer quiz platform"
app_email = "gajendra@bwh.tech"
app_license = "mit"
app_logo_url = "/assets/quizzly/images/quizzly-logo.svg"

add_to_apps_screen = [
	{
		"name": "quizzly",
		"logo": app_logo_url,
		"title": "Quizzly",
		"route": "/play",
	}
]

website_context = {"favicon": app_logo_url}

# Send non-GET requests for this app's endpoints as native `application/json`
# bodies instead of form-encoded, per-key JSON-stringified values.
use_json_request_body = True

fixtures = [{"dt": "Role", "filters": [["name", "in", ["Quiz Host"]]]}]

website_route_rules = [
	{"from_route": "/quizzly/<path:app_path>", "to_route": "quizzly"},
	{"from_route": "/play/<path:app_path>", "to_route": "quizzly"},
	# the bare catalog home
	{"from_route": "/play", "to_route": "quizzly"},
]

website_redirects = [
	{"source": "/quizzly", "target": "/play"},
	{
		"source": r"/quizzly/(.*)",
		"target": r"/play/quizzly/\1",
		"forward_query_parameters": True,
	},
]

export_python_type_annotations = True
require_type_annotated_api_methods = True

doc_events = {
	**{dt: {"before_insert": "quizzly.access.before_create"} for dt in ("GP Session", "QZ Session")},
	**{
		dt: {"before_insert": "quizzly.access.before_create", "validate": "quizzly.access.protect_pack"}
		for dt in ("QZ Quiz", "GP Crowd Pack", "GP Cue Deck", "GP Draw Pack", "GP Game Pack")
	},
}

# GatherPlay game modules; the registry loads these once per worker (docs/gatherplay)
quizzly_game_modules = [
	"quizzly.games.common_ground.game.CommonGroundGame",
	"quizzly.games.quiz.game.QuizGame",
	"quizzly.games.cuecast.game.CueCastGame",
	"quizzly.games.crowd_compass.game.CrowdCompassGame",
	"quizzly.games.doodle_dash.game.DoodleDashGame",
	"quizzly.games.round_games.game.BlufflineGame",
	"quizzly.games.round_games.game.SequenceSprintGame",
	"quizzly.games.round_games.game.PicturePeekGame",
	"quizzly.games.round_games.game.SoundSnapGame",
	"quizzly.games.round_games.game.CaptionClashGame",
	"quizzly.games.round_games.special.StoryLoomGame",
	"quizzly.games.round_games.game.SignalSpectrumGame",
	"quizzly.games.round_games.game.MemoryMosaicGame",
	"quizzly.games.round_games.game.CommonThreadGame",
	"quizzly.games.round_games.special.EscapeTogetherGame",
	"quizzly.games.round_games.special.BracketBashGame",
	"quizzly.games.round_games.game.ClosestCallGame",
	"quizzly.games.round_games.game.PhraseForgeGame",
	"quizzly.games.round_games.special.SeekAndShowGame",
	"quizzly.games.round_games.special.OneWordChorusGame",
	"quizzly.games.grid_conquest.game.GridConquestGame",
	"quizzly.games.puzzles.game.DotsAndBoxesGame",
	"quizzly.games.puzzles.game.HiddenPictureGame",
	"quizzly.games.puzzles.game.PathWeaverGame",
	"quizzly.games.puzzles.game.QuiltPuzzleGame",
	"quizzly.games.puzzles.game.GroupSudokuGame",
]

# Additive starter content: an existing demo key is never rewritten.
after_migrate = [
	"quizzly.publishing.initialize",
	"quizzly.demo.amharic.seed_amharic_starters",
	"quizzly.demo.curated.seed_curated_starters",
]

# Recover failed/timed-out game jobs and retire rooms whose temporary state expired.
scheduler_events = {
	"cron": {"* * * * *": ["quizzly.recovery.recover_game_loops"]},
}
