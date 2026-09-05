"""Versioned additive starter content. Existing packs and illustrations stay intact."""

import json

import frappe

ROOT = "/assets/quizzly/game-clues/"


def row(prompt, answer="", choices=None, media=None, target=0):
	return {
		"prompt_text": prompt,
		"answer": answer,
		"choices": json.dumps(choices or [], ensure_ascii=False),
		"media_url": ROOT + media if media else "",
		"target": target,
	}


def packs(language):
	am = language == "am"
	result = {
		"picture-peek": [
			row("ይህ ምንድን ነው?" if am else "Name the object in the picture.", a if am else e, media=f + ".svg")
			for f, e, a in [
				("umbrella", "umbrella", "ጃንጥላ"),
				("bicycle", "bicycle", "ብስክሌት"),
				("key", "key", "ቁልፍ"),
			]
		],
		"memory-mosaic": [
			row(
				"ስንት ቢጫ ክቦች ነበሩ?" if am else "How many yellow circles were in the scene?",
				"2",
				["1", "2", "3", "4"],
				"memory.svg",
			),
			row(
				"ስንት አረንጓዴ ሦስት ማዕዘኖች ነበሩ?" if am else "How many green triangles were there?",
				"2",
				["1", "2", "3", "4"],
				"memory.svg",
			),
			row(
				"ስንት ቀይ ካሬዎች ነበሩ?" if am else "How many red squares were there?",
				"1",
				["1", "2", "3", "4"],
				"memory.svg",
			),
		],
		"caption-clash": [
			row(p, media="caption.svg")
			for p in (
				["ይህ ወንበር ቢናገር ምን ይላል?", "ለዚህ ሥዕል አስቂኝ ርዕስ ስጡ።", "የወንበሩን ቀጣይ ጀብዱ ግለጹ።"]
				if am
				else [
					"A chair has taken up kite flying. What is it thinking?",
					"Write the headline for this very unusual afternoon.",
					"What does the chair tell its owner when it gets home?",
				]
			)
		],
		"sound-snap": [
			row(
				"ድምፁን አዳምጡ። ዜማው እንዴት ይሄዳል?"
				if am
				else "Listen to the three notes. Which direction does the pitch travel?",
				(["ወደ ላይ", "ወደ ታች", "እኩል"] if am else ["Up", "Down", "Same pitch"])[i],
				["ወደ ላይ", "ወደ ታች", "እኩል"] if am else ["Up", "Down", "Same pitch"],
				name + ".wav",
			)
			for i, name in enumerate(["ascending", "descending", "steady"])
		],
		"signal-spectrum": [
			row("ከዝምታ እስከ ጫጫታ፦ ቤተ መጻሕፍት" if am else "Quiet → Loud: a library reading room", target=8),
			row("ከቀዝቃዛ እስከ ሞቃት፦ ትኩስ ሻይ" if am else "Cold → Hot: a freshly poured cup of tea", target=88),
			row("ከቀላል እስከ ከባድ፦ መኪና" if am else "Light → Heavy: a family car", target=80),
		],
		"common-thread": [
			row(p, a)
			for p, a in (
				[("ገጾች፣ ቤተ መጻሕፍት፣ ማንበብ", "መጽሐፍ"), ("ሥር፣ ቅጠል፣ ጥላ", "ዛፍ"), ("ጎማ፣ ፔዳል፣ መሪ", "ብስክሌት")]
				if am
				else [
					("Pages, chapters, library. What connects them?", "book"),
					("Roots, leaves, shade. What connects them?", "tree"),
					("Pedals, handlebars, two wheels. What connects them?", "bicycle"),
				]
			)
		],
		"closest-call": [
			row(p, str(t), target=t)
			for p, t in (
				[
					("በአንድ ቀን ስንት ደቂቃዎች አሉ?", 1440),
					("አንድ ሜትር ስንት ሚሊሜትር ነው?", 1000),
					("በአንድ ሳምንት ስንት ሰዓቶች አሉ?", 168),
				]
				if am
				else [
					("How many minutes are in one day?", 1440),
					("How many millimetres are in one metre?", 1000),
					("How many hours are in one week?", 168),
				]
			)
		],
		"sequence-sprint": [
			row("በቅደም ተከተል አስቀምጡ።" if am else "Arrange from earliest to latest.", " → ".join(cards), cards)
			for cards in (
				[["ዘር", "ቡቃያ", "ተክል", "አበባ"], ["ጠዋት", "ቀትር", "ከሰዓት", "ማታ"], ["እንቁላል", "ትል", "እጭ", "ቢራቢሮ"]]
				if am
				else [
					["Seed", "Sprout", "Plant", "Flower"],
					["Dawn", "Noon", "Afternoon", "Night"],
					["Egg", "Caterpillar", "Chrysalis", "Butterfly"],
				]
			)
		],
		"phrase-forge": [
			row("ዓረፍተ ነገሩን አስተካክሉ።" if am else "Rebuild the sentence.", " ".join(cards), cards)
			for cards in (
				[["እኛ", "አብረን", "እንጫወታለን"], ["አንድ", "እጅ", "አያጨበጭብም"], ["ድር", "ቢያብር", "አንበሳ", "ያስር"]]
				if am
				else [
					["A journey", "of a thousand miles", "begins", "with a single step."],
					["The best way", "to make a friend", "is", "to be one."],
					["Many hands", "make", "light", "work."],
				]
			)
		],
		"bluffline": [
			row(p, a)
			for p, a in (
				[
					("“አንድ እጅ ...” የሚለውን ለማጠናቀቅ የፈጠራ መልስ ጻፉ።", "አያጨበጭብም"),
					("“ድር ቢያብር ...” የሚለውን ለማጠናቀቅ የፈጠራ መልስ ጻፉ።", "አንበሳ ያስር"),
				]
				if am
				else [
					("Invent a plausible ending: Many hands make ...", "light work"),
					("Invent a plausible ending: A stitch in time saves ...", "nine"),
				]
			)
		],
	}
	result["bracket-bash"] = [
		row(
			"የእረፍት ቀን እቅድ" if am else "The perfect day together",
			choices=["ሽርሽር", "ጨዋታ", "ምግብ ማብሰል", "የፊልም ምሽት"]
			if am
			else ["Picnic", "Games afternoon", "Cook together", "Movie night"],
		)
	]
	result["story-loom"] = [
		row("ከጠረጴዛው ሥር ትንሽ በር አገኘን።" if am else "We found a tiny door beneath the kitchen table.")
		for _ in range(4)
	]
	result["one-word-chorus"] = [
		row("አንድ ቃል ፍንጭ ስጡ።" if am else "Give a one-word clue.", a if am else e)
		for e, a in [("umbrella", "ጃንጥላ"), ("bicycle", "ብስክሌት"), ("star", "ኮከብ")]
	]
	result["seek-and-show"] = [
		row(p)
		for p in (
			["ከቦታዎ ሳይርቁ ክብ ነገር ፈልጉና ያሳዩ።", "ደስ የሚል ትዝታ ያለውን እቃ ያሳዩ ወይም ይግለጹ።", "ሰማያዊ ነገር ያሳዩ።"]
			if am
			else [
				"Show something round within easy reach. Describe it if moving is difficult.",
				"Show or describe an object that brings back a happy memory.",
				"Find something blue within easy reach. Keep everyone safely in the room.",
			]
		)
	]
	result["escape-together"] = [
		row(
			"የቤተ መጻሕፍቱ በር፦ ካሬ=4፣ ሦስት ማዕዘን=3፣ ክብ=0። ኮዱ ካሬ፣ ሦስት ማዕዘን፣ ክብ ነው።"
			if am
			else "The Lantern Library, door 1: square = 4, triangle = 3, circle = 0. The lock shows square, triangle, circle. Find the entrance code.",
			"430",
			["340", "430", "403", "304"],
		),
		row(
			"ወደ ውስጥ ገባችሁ። የመግቢያውን ኮድ አሃዞች ደምሩ። ያ የፍንጩ መደርደሪያ ቁጥር ነው።"
			if am
			else "Inside the library: add the digits of your entrance code (saved below). That sum tells you which shelf holds the final clue.",
			"7",
			["5", "6", "7", "8"],
		),
		row(
			"በመደርደሪያ 7 ላይ የመጨረሻው ፍንጭ፦ 2፣4፣6፣? የሚቀጥለው ቁጥር መውጫውን ይከፍታል።"
			if am
			else "Shelf 7 holds the lantern key: 2, 4, 6, ?. Enter the next number to open the exit and bring the lantern home.",
			"8",
			["7", "8", "9", "10"],
		),
	]

	return result


def seed_curated_starters():
	for language in ["en", "am"]:
		for key, items in packs(language).items():
			demo_key = f"curated-v2-{key}-{language}"
			if frappe.db.exists("GP Game Pack", {"demo_key": demo_key}):
				continue
			doc = frappe.get_doc(
				{
					"doctype": "GP Game Pack",
					"title": f"{key.replace('-', ' ').title()} · "
					+ ("ጀማሪ ጨዋታ" if language == "am" else "Visual starters"),
					"game_key": key,
					"content_language": language,
					"is_demo": 1,
					"demo_key": demo_key,
					"description": "GatherPlay curated starter content · v2",
					"items": items,
				}
			)
			doc.flags.in_demo_seed = True
			doc.insert(ignore_permissions=True)
