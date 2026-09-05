"""Site-branded install metadata; no account or game responses are cached."""

import json
from pathlib import Path

import frappe
from werkzeug.wrappers import Response


@frappe.whitelist(allow_guest=True, methods=["GET"])
def manifest():
	from quizzly.access import settings

	p = settings()
	return Response(
		json.dumps(
			{
				"id": "/play/",
				"name": p.product_name,
				"short_name": p.product_name[:24],
				"description": p.tagline,
				"start_url": "/play/",
				"scope": "/play/",
				"display": "standalone",
				"background_color": "#faf8f2",
				"theme_color": p.accent_color,
				"icons": [
					{
						"src": f"/assets/quizzly/images/gatherplay-{size}.png",
						"sizes": f"{size}x{size}",
						"type": "image/png",
						"purpose": "any maskable",
					}
					for size in (192, 512)
				],
			}
		),
		mimetype="application/manifest+json",
		headers={"Cache-Control": "no-cache"},
	)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def worker():
	source = (Path(__file__).parent / "public" / "gatherplay-worker.js").read_text()
	return Response(
		source,
		mimetype="application/javascript",
		headers={"Service-Worker-Allowed": "/play/", "Cache-Control": "no-cache"},
	)
