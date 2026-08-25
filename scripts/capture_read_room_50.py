"""Capture synchronized real-browser footage for the Read the Room 50 sales demo.

Run from the bench root while Frappe, Socket.IO and the Vite frontend are running:

	./env/bin/python apps/quizzly/scripts/capture_read_room_50.py

Raw Playwright videos and timeline.json land in /tmp/gatherplay-video/read-room-50.
The capture deliberately drives real UI surfaces and the real GatherPlay APIs.
"""

from __future__ import annotations

import getpass
import json
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

import requests
from playwright.sync_api import BrowserContext, Page, sync_playwright

BASE = "http://localhost:18115"
BENCH = Path("/home/minte/projects/training-apps")
RAW = Path("/tmp/gatherplay-video/read-room-50")
TIMELINE = RAW / "timeline.json"
TICKING = True
START = 0.0
MARKERS: dict[str, float] = {}


def mark(name: str) -> None:
	MARKERS[name] = round(time.monotonic() - START, 3)
	print(f"  {MARKERS[name]:6.2f}s  {name}")


def start_ticker() -> None:
	def loop() -> None:
		while TICKING:
			subprocess.run(
				["bench", "--site", "training.localhost", "execute", "quizzly.games.engine.tick_once"],
				cwd=BENCH,
				capture_output=True,
				timeout=30,
			)
			time.sleep(0.35)

	threading.Thread(target=loop, daemon=True).start()


def login(context: BrowserContext, password: str) -> None:
	session = requests.Session()
	response = session.post(
		"http://127.0.0.1:18033/api/method/login",
		data={"usr": "Administrator", "pwd": password},
		headers={"Host": "training.localhost"},
		timeout=15,
	)
	response.raise_for_status()
	context.add_cookies(
		[
			{"name": name, "value": value, "domain": "localhost", "path": "/"}
			for name, value in session.cookies.get_dict().items()
		]
	)


def new_context(browser, name: str, viewport: dict, authenticated: bool = False, password: str = ""):
	directory = RAW / name
	directory.mkdir(parents=True, exist_ok=True)
	context = browser.new_context(
		viewport=viewport,
		record_video_dir=directory,
		record_video_size=viewport,
		color_scheme="dark",
	)
	if authenticated:
		login(context, password)
	page = context.new_page()
	page.on(
		"console",
		lambda message: (
			print(f"[{name} console] {message.type}: {message.text}") if message.type == "error" else None
		),
	)
	page.on("pageerror", lambda error: print(f"[{name} pageerror] {error}"))
	return context, page


def close_capture(context: BrowserContext, page: Page, output_name: str) -> None:
	video = page.video
	context.close()
	if video:
		video.save_as(RAW / f"{output_name}.webm")


def wait_for(page: Page, text: str, timeout: int = 30_000) -> None:
	page.get_by_text(text, exact=False).first.wait_for(timeout=timeout)


def join_player(browser, pin: str, nickname: str):
	context, page = new_context(browser, nickname.lower(), {"width": 390, "height": 844})
	page.goto(f"{BASE}/play/join?pin={pin}", wait_until="networkidle")
	page.get_by_placeholder("Your name").fill(nickname)
	page.locator("form button[type=submit]").click()
	wait_for(page, "You're in")
	mark(f"{nickname.lower()}_joined")
	return context, page


def click_ranked_vote(page: Page, first: int, second: int) -> None:
	buttons = page.locator("main .grid button")
	buttons.nth(first).click()
	page.wait_for_timeout(450)
	buttons.nth(second).click()
	wait_for(page, "Vote locked")


def make_prediction(page: Page, choice: int, estimate: int) -> None:
	buttons = page.locator("main .grid button")
	buttons.nth(choice).click()
	slider = page.locator('input[type="range"]')
	if slider.count():
		slider.fill(str(estimate))
	page.get_by_role("button", name="Lock prediction").click()
	wait_for(page, "Prediction locked")


def main() -> None:
	global START, TICKING
	if RAW.exists():
		shutil.rmtree(RAW)
	RAW.mkdir(parents=True)
	START = time.monotonic()
	password = getpass.getpass("Administrator password: ")
	start_ticker()

	with sync_playwright() as playwright:
		browser = playwright.chromium.launch()
		host_context, host = new_context(
			browser,
			"host",
			{"width": 1440, "height": 900},
			authenticated=True,
			password=password,
		)
		host.goto(f"{BASE}/play/host", wait_until="networkidle")
		host.evaluate("localStorage.removeItem('gp_hosted_session')")
		for _ in range(4):
			state = host.evaluate(
				"""async () => {
					const response = await fetch('/api/method/quizzly.games.api.get_host_state', {
						method: 'POST', headers: {'X-Frappe-Site-Name': 'training.localhost'}
					});
					return (await response.json()).message;
				}"""
			)
			if not state.get("session"):
				break
			host.evaluate(
				"""async (session) => fetch('/api/method/quizzly.games.api.end_session', {
					method: 'POST',
					headers: {'Content-Type': 'application/json', 'X-Frappe-Site-Name': 'training.localhost'},
					body: JSON.stringify({session})
				})""",
				state["session"],
			)
			host.wait_for_timeout(1_200)
		host.reload(wait_until="networkidle")
		wait_for(host, "Start a room")
		mark("host_ready")
		host.get_by_role("button", name=re.compile("Crowd Compass")).click()
		wait_for(host, "Vote time")
		mark("setup_open")
		pack_value = host.locator("select option").filter(has_text="Read the Room 50").get_attribute("value")
		assert pack_value, "Read the Room 50 pack is not seeded"
		host.locator("select").select_option(value=pack_value)
		host.wait_for_timeout(1_800)
		host.get_by_role("button", name="Open the lobby").click()
		wait_for(host, "Start ·")
		mark("lobby_open")

		pin = host.evaluate(
			"""async () => {
				const response = await fetch('/api/method/quizzly.games.api.get_host_state', {
					method: 'POST', headers: {'X-Frappe-Site-Name': 'training.localhost'}
				});
				return (await response.json()).message.game_pin;
			}"""
		)
		assert pin, "could not read game PIN"
		print(f"  room PIN {pin}")

		player_contexts = {}
		player_pages = {}
		for name in ("Meron", "Dawit", "Hana"):
			context, page = join_player(browser, pin, name)
			player_contexts[name] = context
			player_pages[name] = page

		screen_context, screen = new_context(browser, "projector", {"width": 1920, "height": 1080})
		screen.goto(f"{BASE}/play/s/{pin}/screen", wait_until="networkidle")
		wait_for(screen, "in the room")
		mark("projector_lobby")
		host.wait_for_timeout(2_500)

		host.get_by_role("button", name=re.compile("Start ·")).click()
		for page in player_pages.values():
			wait_for(page, "Pick your first choice", timeout=45_000)
		mark("vote_open")
		click_ranked_vote(player_pages["Meron"], 0, 1)
		click_ranked_vote(player_pages["Dawit"], 0, 2)
		click_ranked_vote(player_pages["Hana"], 1, 0)
		mark("votes_locked")
		host.wait_for_timeout(2_200)
		host.get_by_role("button", name="Skip stage").click()
		for page in player_pages.values():
			wait_for(page, "Predict the room", timeout=20_000)
		mark("prediction_open")
		make_prediction(player_pages["Meron"], 0, 55)
		make_prediction(player_pages["Dawit"], 0, 60)
		make_prediction(player_pages["Hana"], 1, 35)
		mark("predictions_locked")
		host.wait_for_timeout(2_200)
		host.get_by_role("button", name="Skip stage").click()
		wait_for(screen, "The room said", timeout=20_000)
		mark("reveal")
		screen.wait_for_timeout(6_500)
		wait_for(screen, "Scoreboard", timeout=20_000)
		mark("scoreboard")
		screen.wait_for_timeout(5_500)

		host.get_by_role("button", name="End game").click()
		host.locator("dialog").get_by_role("button", name="End game").click()
		wait_for(screen, "Final results", timeout=20_000)
		mark("podium")
		screen.wait_for_timeout(6_000)
		mark("capture_end")

		close_capture(screen_context, screen, "projector")
		for name, context in player_contexts.items():
			close_capture(context, player_pages[name], name.lower())
		close_capture(host_context, host, "host")
		browser.close()

	TICKING = False
	TIMELINE.write_text(json.dumps({"markers": MARKERS}, indent=2) + "\n")
	print(f"\nCaptured sources in {RAW}")


if __name__ == "__main__":
	main()
