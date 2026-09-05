"""Round stakes are fixed when voting opens, including when live prompts are appended."""


def round_arc(enabled, round_number, planned_rounds):
	active = bool(enabled and planned_rounds >= 3)
	chapter = (
		"encore"
		if round_number > planned_rounds
		else "finale"
		if round_number == planned_rounds
		else "opening"
		if round_number == 1
		else "build"
	)
	return {
		"enabled": active,
		"chapter": chapter if active else "classic",
		"round": round_number,
		"planned_rounds": planned_rounds,
		"prediction_points": 1000 if active and chapter == "finale" else 500,
	}


def recap_from_rounds(rounds):
	"""Keep only aggregate information already revealed to the room; no player IDs."""
	moments = []
	completed = 0
	for summary in rounds:
		if summary.get("voided") is not None or "tally" not in summary:
			continue
		completed += 1
		if not summary.get("quorum_met") or not summary.get("votes"):
			continue
		choices = {c["id"]: c["text"] for c in summary.get("choices", [])}
		tally = summary["tally"]
		total = sum(tally.values())
		winners = summary.get("plurality", [])
		if len(winners) != 1 or not total or winners[0] not in choices:
			continue
		moments.append(
			{
				"prompt": summary.get("prompt", ""),
				"choice": choices[winners[0]],
				"percent": round(100 * tally[winners[0]] / total),
				"ranked": bool(summary.get("ranked")),
			}
		)
	return {
		"rounds_completed": completed,
		"moments": sorted(moments, key=lambda m: m["percent"], reverse=True)[:3],
	}
