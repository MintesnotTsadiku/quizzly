"""Validate media games at save and host boundaries."""

from urllib.parse import urlsplit

import frappe
from frappe import _

MEDIA_GAMES = {"picture-peek", "memory-mosaic", "caption-clash", "sound-snap"}


def validate_items(key, items):
	if not items:
		frappe.throw(_("Add at least one playable round."))
	for number, item in enumerate(items, 1):
		if key in MEDIA_GAMES:
			url = str(item.get("media_url") or "")
			parsed = urlsplit(url)
			if (
				not url
				or (parsed.scheme not in ("", "https"))
				or (not parsed.scheme and (not url.startswith("/") or bool(parsed.netloc)))
			):
				frappe.throw(
					_(
						"Round {0} needs a valid clue media URL. Choose a visual starter pack or add the missing media."
					).format(number)
				)
			if key == "sound-snap" and not parsed.path.lower().endswith((".wav", ".mp3", ".ogg", ".m4a")):
				frappe.throw(_("Sound Snap needs an audio clip for every round."))

		if key == "signal-spectrum":
			prompt = item.get("prompt_text") or ""
			if "→" not in prompt and "እስከ" not in prompt:
				frappe.throw(
					_("Signal Spectrum needs two axis endpoints, followed by a clue. Use Low → High: clue.")
				)
