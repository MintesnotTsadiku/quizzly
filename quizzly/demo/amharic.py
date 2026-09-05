"""Additive Amharic starter packs. English packs and user content are never overwritten."""

import json

import frappe


def choice(prompt, choices, answer=0, **extra):
	return {
		"prompt_text": prompt,
		"choices": json.dumps(choices, ensure_ascii=False),
		"answer": choices[answer],
		**extra,
	}


def text(prompt, answer="", **extra):
	return {"prompt_text": prompt, "answer": answer, **extra}


IMAGE = "/assets/quizzly/images/games/common-ground/gathering-v1.png"
ROUND_PACKS = {
	"bluffline": (
		"እውነት ወይስ ፈጠራ",
		[
			text("'ቀስ በቀስ እንቁላል ...' የሚለውን አባባል የሚጨርስ የሚያሳምን የተሳሳተ መልስ ፍጠሩ።", "በእግሩ ይሄዳል"),
			text("'አንድ እጅ ...' የሚለውን አባባል የሚጨርስ የፈጠራ መልስ ጻፉ።", "አያጨበጭብም"),
			text("'ድር ቢያብር ...' የሚለውን አባባል የሚጨርስ የፈጠራ መልስ ጻፉ።", "አንበሳ ያስር"),
		],
	),
	"sequence-sprint": (
		"የእለት ተእለት ቅደም ተከተል",
		[
			choice("የተክልን እድገት በቅደም ተከተል አስቀምጡ።", ["ዘር", "ቡቃያ", "ተክል", "አበባ"]),
			choice("ቀኑን በቅደም ተከተል አስቀምጡ።", ["ጠዋት", "ቀትር", "ከሰዓት በኋላ", "ማታ"]),
			choice("ቁጥሮቹን ከትንሽ ወደ ትልቅ አስቀምጡ።", ["2", "4", "6", "8"]),
		],
	),
	"phrase-forge": (
		"አባባሎችን እናገናኝ",
		[
			choice("አባባሉን አስተካክሉ።", ["አንድ", "እጅ", "አያጨበጭብም"]),
			choice("ዓረፍተ ነገሩን አስተካክሉ።", ["እኛ", "አብረን", "እንጫወታለን"]),
			choice("አባባሉን አስተካክሉ።", ["ድር", "ቢያብር", "አንበሳ", "ያስር"]),
		],
	),
	"caption-clash": (
		"ሥዕሉ ምን ይላል",
		[
			text("ለዚህ የቤተሰብ ስብሰባ አጭር አስቂኝ መግለጫ ጻፉ።", media_url=IMAGE),
			text("ይህ ቤተሰብ በኋላ ምን ሊያደርግ እንደሚችል አስቂኝ መግለጫ ጻፉ።", media_url=IMAGE),
			text("በዚህ ሥዕል ላይ ያለው ወንበር ቢናገር ምን ይል ነበር?", media_url=IMAGE),
		],
	),
	"story-loom": (
		"አብረን ታሪክ እንፍጠር",
		[
			text("ታሪኩን በአንድ ዓረፍተ ነገር ቀጥሉ፦ ከጠረጴዛው ሥር ትንሽ በር አገኘሁ።"),
			text("ታሪኩን ቀጥሉ፦ ዛሬ ቡናዬ ስሜን ጠራኝ።"),
			text("ታሪኩን ቀጥሉ፦ አውቶቡሱ የቆመው በደመና ላይ ነበር።"),
		],
	),
	"seek-and-show": (
		"በዙሪያችን እንፈልግ",
		[
			text("ከቦታዎ ሳይርቁ ክብ ነገር ፈልጉ። በአጭሩ ግለጹት።"),
			text("ሰማያዊ ነገር ፈልጉ። ምን እንደሆነ ጻፉ።"),
			text("ደስ የሚል ትዝታ የሚያመጣ እቃ ምረጡና ግለጹት።"),
		],
	),
	"common-thread": (
		"አንድ የሚያገናኝ ቃል",
		[
			text("ገጾች፣ ማንበብ፣ ቤተ መጻሕፍት። የሚያገናኛቸው አንድ ቃል ምንድን ነው?", "መጽሐፍ"),
			text("ቅጠል፣ ሥር፣ ጥላ። የሚያገናኛቸው ቃል ምንድን ነው?", "ዛፍ"),
			text("ጎማ፣ ፔዳል፣ መሪ። የሚያገናኛቸው ቃል ምንድን ነው?", "ብስክሌት"),
		],
	),
	"one-word-chorus": (
		"አንድ ቃል እንገምት",
		[
			text("በማታ ሰማይ ይታያል። ትንሽ ብርሃን ያለው ነጥብ ይመስላል። ምንድን ነው?", "ኮከብ"),
			text("ዝናብ ሲዘንብ ከራሳችን በላይ እንይዘዋለን። ምንድን ነው?", "ጃንጥላ"),
			text("ደብዳቤ ለመጻፍ እንጠቀምበታለን። ቀለም ይይዛል። ምንድን ነው?", "ብዕር"),
		],
	),
	"picture-peek": (
		"ሥዕሉን እንመልከት",
		[
			text("በሥዕሉ ላይ የምግብ፣ የሙዚቃና የመንገድ ምልክቶች አሉ። የዜማ ጥበብ ምን ይባላል?", "ሙዚቃ", media_url=IMAGE),
			text("በሥዕሉ ግራ ጎን እና ቀኝ ጎን ያሉት አረንጓዴ ነገሮች ምን ናቸው?", "ተክሎች", media_url=IMAGE),
			text("በሥዕሉ ላይ በማሰሮው ውስጥ ያለው የሚበላ ነገር ምን ይባላል?", "ምግብ", media_url=IMAGE),
		],
	),
	"memory-mosaic": (
		"የሥዕል ትውስታ",
		[
			choice("በሥዕሉ ላይ ስንት ሰዎች አሉ?", ["አራት", "አምስት", "ስድስት", "ሰባት"], 2, media_url=IMAGE),
			choice("በላይ ስንት የሀሳብ አረፋዎች አሉ?", ["ሁለት", "ሦስት", "አራት", "አምስት"], 1, media_url=IMAGE),
			choice("ከታዩት ምልክቶች አንዱ የቱ ነው?", ["አውሮፕላን", "ጊታር", "እግር ኳስ", "መኪና"], 1, media_url=IMAGE),
		],
	),
	"sound-snap": (
		"ድምፁን ከፍንጩ እወቁ",
		[
			choice("'ሚያው' የሚለው የየትኛው እንስሳ ድምፅ ነው?", ["ውሻ", "ድመት", "ላም", "ዶሮ"], 1),
			choice("የቤት መግቢያ ላይ እንግዳ ሲመጣ የሚደወለው ምንድን ነው?", ["ደወል", "ከበሮ", "መለከት", "ፒያኖ"]),
			choice("ዝናብ በቆርቆሮ ላይ ሲወርድ ምን እንሰማለን?", ["ጠብ ጠብ", "ሚያው", "ሙ", "ውው"]),
		],
	),
	"escape-together": (
		"ሦስት ቁልፎች",
		[
			choice("የመቆለፊያው ኮድ፦ 2፣ 4፣ 6፣ ? ቀጣዩ ቁጥር ምንድን ነው?", ["7", "8", "9", "10"], 1),
			choice("ሣጥኑን ለመክፈት ቃሉን በተቃራኒው አንብቡ፦ 123። መልሱ?", ["123", "231", "321", "312"], 2),
			choice("ቁልፉ በክቡ ሥር ነው። የቱን ምልክት ይመርጣሉ?", ["▲", "■", "●", "◆"], 2),
		],
	),
	"bracket-bash": (
		"የትኛው ይመረጥ",
		[
			choice("ዝናብ እየዘነበ ነው። ለደረቅነት የቱ እቃ ይሻላል?", ["ጃንጥላ", "ኳስ", "ማንኪያ", "ወረቀት"]),
			choice("በጨለማ ውስጥ ለማየት የቱ ይረዳል?", ["ትራስ", "የእጅ መብራት", "ጫማ", "ኩባያ"], 1),
			choice("የእግር ኳስ ጨዋታ ለመጫወት የቱ ይረዳል?", ["መጽሐፍ", "ሳህን", "ኳስ", "ብዕር"], 2),
		],
	),
	"closest-call": (
		"ለቁጥሩ እንቅረብ",
		[
			text("በአንድ ሰዓት ውስጥ ስንት ደቂቃዎች አሉ?", "60", target=60),
			text("በአንድ ሳምንት ውስጥ ስንት ቀናት አሉ?", "7", target=7),
			text("በአንድ ሜትር ውስጥ ስንት ሴንቲሜትሮች አሉ?", "100", target=100),
		],
	),
	"signal-spectrum": (
		"በመለኪያው ላይ እንገምት",
		[
			text(
				"0 ፍጹም ጸጥታ፣ 100 በጣም ጫጫታ ነው። የልደት ግብዣን የት ታስቀምጣላችሁ? የዙሩን ድብቅ መለኪያ ገምቱ።",
				"የዙሩ መለኪያ 75 ነው።",
				target=75,
			),
			text("0 ቀላል፣ 100 በጣም ከባድ ነው። አዲስ ቋንቋ መማርን የት ታስቀምጣላችሁ?", "የዙሩ መለኪያ 65 ነው።", target=65),
			text("0 በቤት ውስጥ፣ 100 ከቤት ውጭ ነው። የአትክልት ቦታ ሥራን የት ታስቀምጣላችሁ?", "የዙሩ መለኪያ 90 ነው።", target=90),
		],
	),
	"grid-conquest": (
		"መስመሩን እናጠናቅቅ",
		[
			choice(
				"X X · / O O · / · · · — X የላይኛውን ረድፍ ለማጠናቀቅ የት ይጫወት?", ["ከላይ ቀኝ", "መሀል ቀኝ", "ከታች ግራ", "መሀል"]
			),
			choice(
				"X O · / X O · / · · · — X የግራውን አምድ ለማጠናቀቅ የት ይጫወት?", ["ከታች ግራ", "ከላይ ቀኝ", "ከታች ቀኝ", "መሀል"]
			),
			choice(
				"X O · / O X · / · · · — X የሰያፍ መስመሩን ለማጠናቀቅ የት ይጫወት?",
				["ከታች ቀኝ", "ከላይ ቀኝ", "ከታች ግራ", "መሀል ቀኝ"],
			),
		],
	),
	"dots-and-boxes": (
		"የሚጎድለው ጎን",
		[
			choice("የሳጥኑ ላይ፣ ግራ እና ታች ጎኖች ተሠርተዋል። የሚጎድለው የቱ ነው?", ["ቀኝ", "ግራ", "ላይ", "ታች"]),
			choice("የሳጥኑ ቀኝ፣ ግራ እና ታች ጎኖች ተሠርተዋል። የሚጎድለው የቱ ነው?", ["ላይ", "ቀኝ", "ግራ", "ታች"]),
			choice("የሳጥኑ ላይ፣ ቀኝ እና ግራ ጎኖች ተሠርተዋል። የሚጎድለው የቱ ነው?", ["ታች", "ላይ", "ቀኝ", "ግራ"]),
		],
	),
	"hidden-picture": (
		"የተደበቀው ቅርጽ",
		[
			choice("ፍንጩ 3 ነው። በአንድ ላይ ሦስት የተሞሉ ክፍሎች ያሉት የቱ ነው?", ["■■■··", "■·■■·", "■■·■■", "·■·■·"]),
			choice("ፍንጩ 1፣1 ነው። በክፍተት የተለዩ ሁለት ነጠላ ክፍሎች ያሉት የቱ ነው?", ["■·■··", "■■···", "·■■··", "■■■··"]),
			choice(
				"ፍንጩ 2፣1 ነው። ሁለት ተከታታይ ክፍሎችና ከክፍተት በኋላ አንድ ያለው የቱ ነው?", ["■■·■·", "■■■··", "■·■■·", "·■■■·"]
			),
		],
	),
	"path-weaver": (
		"መንገዱን እንምረጥ",
		[
			choice("ፊት ተዘግቷል። ግራ ወደተጎበኘ ቦታ ይመልሳል። ቀኝ ክፍት ነው። ወዴት እንሂድ?", ["ቀኝ", "ግራ", "ወደ ፊት", "ቁም"]),
			choice("ግራና ቀኝ ተዘግተዋል። ፊት ክፍት ነው። ወዴት እንሂድ?", ["ወደ ፊት", "ቀኝ", "ግራ", "ቁም"]),
			choice("ቀኝ ተዘግቷል። ፊት ወደተጎበኘ ቦታ ይመልሳል። ግራ ወደ መውጫው ክፍት ነው።", ["ግራ", "ቀኝ", "ወደ ፊት", "ቁም"]),
		],
	),
	"quilt-puzzle": (
		"ቅጡን እንቀጥል",
		[
			choice("▲ ● ▲ ● ? — ቀጣዩ ምንድን ነው?", ["▲", "●", "■", "◆"]),
			choice("■ ■ ● ■ ■ ? — ቀጣዩ ምንድን ነው?", ["●", "■", "▲", "◆"]),
			choice("1 2 3 1 2 ? — ቀጣዩ ምንድን ነው?", ["3", "1", "2", "4"]),
		],
	),
	"group-sudoku": (
		"ትንሽ የቁጥር እንቆቅልሽ",
		[
			choice("ከ1–4 ያሉ ቁጥሮች አንድ ጊዜ ብቻ ይገባሉ። ረድፉ 1፣ 2፣ ?፣ 4 ነው። የጎደለው?", ["3", "1", "2", "4"]),  # noqa: RUF001 — intentional numeric range in localized copy
			choice("ረድፉ 3፣ ?፣ 1፣ 4 ነው። ከ1–4 የጎደለው ቁጥር?", ["2", "3", "1", "4"]),  # noqa: RUF001 — intentional numeric range in localized copy
			choice("አምዱ ?፣ 3፣ 2፣ 1 ነው። ከ1–4 የጎደለው ቁጥር?", ["4", "1", "2", "3"]),  # noqa: RUF001 — intentional numeric range in localized copy
		],
	),
}


def seed_amharic_starters():
	frappe.only_for("System Manager")
	from quizzly.demo.seed import upsert
	from quizzly.games.round_games.game import PROFILES

	assert set(ROUND_PACKS) == set(PROFILES)
	results = []
	for key, (title, items) in ROUND_PACKS.items():
		demo_key = f"{key}-am-starter-v1"
		name = frappe.db.exists("GP Game Pack", {"demo_key": demo_key})
		if not name:
			doc = frappe.get_doc(
				{
					"doctype": "GP Game Pack",
					"title": title,
					"game_key": key,
					"description": "የአማርኛ መጀመሪያ ስብስብ",
					"content_language": "am",
					"is_demo": 1,
					"demo_key": demo_key,
					"items": items,
				}
			)
			doc.flags.in_demo_seed = True
			doc.insert(ignore_permissions=True)
			name = doc.name
		results.append({"game": key, "pack": name})
	core = [
		{
			"game_key": "crowd-compass",
			"title": "የእኛ ምርጫዎች",
			"prompts": [
				{"prompt": "አብረን ነፃ ከሰዓት በኋላ ቢኖረን ምን እንምረጥ?", "choices": ["ከቤት ውጭ መራመድ", "ቤት ውስጥ መዝናናት"]},
				{"prompt": "በጉዞ ላይ ምን ይሻላል?", "choices": ["ሙዚቃ ማዳመጥ", "ከጓደኞች ጋር ማውራት", "መልክዓ ምድሩን ማየት"]},
				{"prompt": "ለቡድናችን የትኛው ጨዋታ ይስማማል?", "choices": ["መሳል", "ጥያቄና መልስ", "በምልክት ማሳየት"]},
				{"prompt": "የእረፍት ቀን ምን ያስደስታል?", "choices": ["አብሮ ምግብ ማዘጋጀት", "መጽሐፍ ማንበብ", "ጓደኛ መጠየቅ"]},
				{"prompt": "አዲስ ችሎታ ለመማር ብንመርጥ?", "choices": ["ሙዚቃ", "ሥዕል", "ሌላ ቋንቋ"]},
			],
		},
		{
			"game_key": "cuecast",
			"title": "የቤተሰብ እንቅስቃሴዎች",
			"mode": "Act",
			"prompts": [
				"ጃንጥላ መክፈት",
				"ቡና ማፍላት",
				"እግር ኳስ መጫወት",
				"የከበደ ሳጥን መሸከም",
				"አውቶቡስ መጠበቅ",
				"መጽሐፍ ማንበብ",
				"አበባ ማጠጣት",
				"ብስክሌት መንዳት",
			],
		},
		{
			"game_key": "doodle-dash",
			"title": "ቀላል የሥዕል ቃላት",
			"prompts": ["ቤት", "ዛፍ", "ፀሐይ", "ድመት", "መኪና", "ጃንጥላ", "ኳስ", "አበባ"],
		},
		{
			"game_key": "quiz",
			"title": "የቤተሰብ ጥያቄዎች",
			"default_time_limit": 30,
			"questions": [
				{
					"question_text": "7 + 5 ስንት ነው?",
					"option_1": "10",
					"option_2": "11",
					"option_3": "12",
					"option_4": "13",
					"correct_option": "3",
					"explanation": "ሰባት እና አምስት ሲደመሩ አሥራ ሁለት ይሆናሉ።",
				},
				{
					"question_text": "የምንኖርባት ፕላኔት የትኛዋ ናት?",
					"option_1": "ማርስ",
					"option_2": "ምድር",
					"option_3": "ቬነስ",
					"option_4": "ጁፒተር",
					"correct_option": "2",
					"explanation": "የሰው ልጆች የሚኖሩት በምድር ላይ ነው።",
				},
				{
					"question_text": "በሳምንት ስንት ቀናት አሉ?",
					"option_1": "5",
					"option_2": "6",
					"option_3": "7",
					"option_4": "8",
					"correct_option": "3",
					"explanation": "አንድ ሳምንት ሰባት ቀናት አሉት።",
				},
				{
					"question_text": "ስንት ጎኖች ያሉት ቅርጽ ሦስት ማዕዘን ይባላል?",
					"option_1": "2",
					"option_2": "3",
					"option_3": "4",
					"option_4": "5",
					"correct_option": "2",
					"explanation": "ሦስት ማዕዘን ሦስት ጎኖች አሉት።",
				},
			],
		},
	]
	for data in core:
		data["demo_key"] = f"{data['game_key']}-am-starter-v1"
		dt = {
			"quiz": "QZ Quiz",
			"cuecast": "GP Cue Deck",
			"doodle-dash": "GP Draw Pack",
			"crowd-compass": "GP Crowd Pack",
		}[data["game_key"]]
		name = frappe.db.exists(dt, {"demo_key": data["demo_key"]})
		if not name:
			doc = upsert(data)
			frappe.db.set_value(dt, doc.name, "content_language", "am")
			name = doc.name
		results.append({"game": data["game_key"], "pack": name})
	frappe.db.commit()
	return results
