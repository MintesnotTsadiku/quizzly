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
	"quizzly.games.round_games.game.StoryLoomGame",
	"quizzly.games.round_games.game.SignalSpectrumGame",
	"quizzly.games.round_games.game.MemoryMosaicGame",
	"quizzly.games.round_games.game.CommonThreadGame",
	"quizzly.games.round_games.game.EscapeTogetherGame",
	"quizzly.games.round_games.game.BracketBashGame",
	"quizzly.games.round_games.game.ClosestCallGame",
	"quizzly.games.round_games.game.PhraseForgeGame",
	"quizzly.games.round_games.game.SeekAndShowGame",
	"quizzly.games.round_games.game.OneWordChorusGame",
	"quizzly.games.round_games.game.GridConquestGame",
	"quizzly.games.round_games.game.DotsAndBoxesGame",
	"quizzly.games.round_games.game.HiddenPictureGame",
	"quizzly.games.round_games.game.PathWeaverGame",
	"quizzly.games.round_games.game.QuiltPuzzleGame",
	"quizzly.games.round_games.game.GroupSudokuGame",
]
