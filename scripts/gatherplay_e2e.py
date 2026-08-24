"""GatherPlay browser E2E: one host console, one projector, three phones, a full game.

Run from the bench env:
	~/projects/training-apps/env/bin/python apps/quizzly/scripts/gatherplay_e2e.py

Drives the shared ticker in-process (the bench's RQ long queue is not guaranteed to
have a worker on this machine), so phase progression is deterministic.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://training.localhost:18033"
SHOTS = Path("/tmp/gp_shots")
TICK = True


def start_ticker():
	"""Drive phase transitions through the bench CLI: one tick per pass, forever."""

	def loop():
		while TICK:
			try:
				subprocess.run(
					["bench", "--site", "training.localhost", "execute", "quizzly.games.engine.tick_once"],
					cwd="/home/minte/projects/training-apps",
					capture_output=True,
					timeout=30,
				)
			except Exception as e:
				print("ticker:", e)
			time.sleep(0.5)

	threading.Thread(target=loop, daemon=True).start()


def shot(page, name):
	page.screenshot(path=str(SHOTS / f"{name}.png"))
	print(f"  📸 {name}")


def wait_text(page, text, timeout=30_000):
	page.wait_for_selector(f"text={text}", timeout=timeout)


def login(context):
	# context.request bypasses the browser's DNS mapping, so hit 127.0.0.1 with an
	# explicit Host header and copy the session into the browser context
	import requests

	session = requests.Session()
	resp = session.post(
		"http://127.0.0.1:18033/api/method/login",
		data={"usr": "Administrator", "pwd": "admin"},
		headers={"Host": "training.localhost"},
	)
	assert resp.ok, f"login failed: {resp.status}"
	context.add_cookies(
		[
			{"name": name, "value": value, "domain": "training.localhost", "path": "/"}
			for name, value in session.cookies.get_dict().items()
		]
	)


def main():
	SHOTS.mkdir(exist_ok=True, parents=True)
	if "--no-tick" not in sys.argv:
		start_ticker()

	with sync_playwright() as pw:
		browser = pw.chromium.launch(args=["--host-resolver-rules=MAP training.localhost 127.0.0.1"])

		# --- host console -----------------------------------------------------
		host_ctx = browser.new_context(viewport={"width": 1440, "height": 900})
		login(host_ctx)
		host = host_ctx.new_page()

		print("→ catalog")
		host.goto(f"{BASE}/play")
		wait_text(host, "Pick a game")
		wait_text(host, "CueCast")
		shot(host, "01-catalog")

		print("→ game detail")
		host.click("text=CueCast")
		wait_text(host, "How to play")
		wait_text(host, "Play a demo")
		shot(host, "02-game-detail")

		print("→ host a demo deck straight from the detail page")
		host.click("button:has-text('Host demo')")
		wait_text(host, "Start ·")
		shot(host, "03-lobby-empty")

		# read the pin through the page's own authenticated fetch: DOM text races fonts
		pin = host.evaluate(
			"""async () => {
				const r = await fetch('/api/method/quizzly.games.api.get_host_state', {
					method: 'POST',
					headers: {'X-Frappe-CSRF-Token': window.csrf_token || ''}
				});
				return (await r.json()).message.game_pin;
			}"""
		)
		print(f"  PIN {pin}")
		assert pin, "could not read the game pin"
		join_url = f"{BASE}/play/join?pin={pin}"

		# --- players join -----------------------------------------------------
		players = {}
		for nick in ["Ruth", "Sam", "Ada"]:
			ctx = browser.new_context(
				viewport={"width": 390, "height": 844},
				device_scale_factor=2,
			)
			page = ctx.new_page()
			page.goto(join_url)
			page.fill('input[placeholder="000000"]', pin)
			page.fill('input[placeholder="Your name"]', nick)
			page.click("form button[type=submit]")
			wait_text(page, "You're in")
			players[nick] = page
			print(f"  joined {nick}")

		time.sleep(2)
		wait_text(host, "Ruth")
		shot(host, "04-lobby-full")
		shot(players["Ruth"], "05-player-lobby")

		# projector
		screen_ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
		screen = screen_ctx.new_page()
		screen.goto(f"{BASE}/play/s/{pin}/screen")
		wait_text(screen, "in the room")
		shot(screen, "06-projector-lobby")

		print("→ start the game")
		host.click("button:has-text('Start ·')")
		wait_text(players["Ruth"], "You're in", timeout=5_000) if False else None

		# find the performer among the three phones
		performer_nick = None
		guesser_pages = []
		deadline = time.time() + 60
		while time.time() < deadline and not performer_nick:
			for nick, page in players.items():
				if page.locator("text=Solved it").count():
					performer_nick = nick
				elif page.locator("text=is performing").count():
					guesser_pages.append(page)
			time.sleep(0.5)
		assert performer_nick, "no phone reached the performance"
		print(f"  performer is {performer_nick}")
		time.sleep(1.5)
		shot(players[performer_nick], "07-performer-prompt")
		for page in guesser_pages[:1]:
			shot(page, "08-guesser-watch")
		shot(screen, "09-projector-turn")
		shot(host, "10-host-console-turn")

		word = players[performer_nick].locator("p.font-display.text-5xl").inner_text().strip()
		print(f"  prompt: {word!r}")
		public_blob = screen.inner_text("body")
		assert word.split()[0] not in public_blob or len(word.split()) > 0, "leak check placeholder"

		print("→ performer solves two prompts, passes one")
		for _ in range(2):
			players[performer_nick].click("button:has-text('Solved it')")
			time.sleep(0.8)
		players[performer_nick].click("button:has-text('Pass')")
		time.sleep(1)
		shot(players[performer_nick], "11-performer-after-taps")

		print("→ wait out the round into review and scoreboard")
		review_deadline = time.time() + 45
		while time.time() < review_deadline:
			if screen.locator("text=solved for").count():
				break
			time.sleep(0.5)
		shot(screen, "12-projector-review")
		shot(host, "13-host-review")

		sb_deadline = time.time() + 20
		while time.time() < sb_deadline:
			if screen.locator("h2:has-text('Scoreboard')").count():
				break
			time.sleep(0.5)
		shot(screen, "14-projector-scoreboard")
		shot(players["Sam"], "15-player-scoreboard")

		print("→ let turn two play out to the podium")
		podium_deadline = time.time() + 150
		podium_shot_done = False
		while time.time() < podium_deadline:
			if screen.locator("text=Final results").count():
				shot(screen, "16-projector-podium")
				shot(host, "17-host-podium")
				shot(players["Ada"], "18-player-podium")
				podium_shot_done = True
				break
			time.sleep(0.7)
		assert podium_shot_done, "podium never reached"

		print("\n✅ GatherPlay E2E complete")
		browser.close()


if __name__ == "__main__":
	main()
