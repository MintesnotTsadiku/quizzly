# Load driver: every guest minted by the setup script hammers submit_answer over HTTP,
# one salvo per question, measuring the concurrency-critical path (mark_answered +
# Answer insert + batch scoring at close). Run scripts/loadtest_setup.py first.
#   env/bin/python apps/quizzly/scripts/loadtest.py
#
# Reports per-question and overall submit latency percentiles + error breakdown.

import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ORIGIN = "http://quizzly.localhost:8000"
BASE = f"{ORIGIN}/api/method/quizzly.api"
STATE_FILE = Path("/tmp/quizzly_loadtest.json")


def submit(pin, token, question_row):
	start = time.perf_counter()
	try:
		r = requests.post(
			f"{BASE}.submit_answer",
			json={"pin": pin, "token": token, "question_row": question_row, "selected_option": "1"},
			timeout=30,
		)
		ms = (time.perf_counter() - start) * 1000
		if r.status_code == 200:
			return ms, "ok"
		# frappe surfaces thrown messages in _server_messages; keep it short
		return ms, f"{r.status_code}"
	except requests.RequestException as e:
		return (time.perf_counter() - start) * 1000, type(e).__name__


def poll_state(pin, token):
	r = requests.get(f"{BASE}.get_state", params={"pin": pin, "token": token}, timeout=10)
	r.raise_for_status()
	return r.json()["message"]


def pct(values, p):
	if not values:
		return 0.0
	return statistics.quantiles(values, n=100)[p - 1] if len(values) > 1 else values[0]


def report_salvo(q_index, results):
	lat = sorted(r[0] for r in results)
	ok = sum(1 for r in results if r[1] == "ok")
	errors = {}
	for _, status in results:
		if status != "ok":
			errors[status] = errors.get(status, 0) + 1
	err_str = " ".join(f"{k}={v}" for k, v in errors.items()) or "-"
	print(
		f"  Q{q_index}: {ok}/{len(results)} ok  "
		f"p50={pct(lat, 50):.0f} p95={pct(lat, 95):.0f} p99={pct(lat, 99):.0f} max={max(lat):.0f} ms  "
		f"errors: {err_str}"
	)
	return lat, ok, errors


def main():
	state = json.loads(STATE_FILE.read_text())
	pin, session, tokens = state["pin"], state["session"], state["tokens"]
	probe = tokens[0]
	print(f"session={session} pin={pin} players={len(tokens)}")
	print("polling for questions, driving submits...\n")

	all_lat, total_ok, total_reqs, all_errors, done_rows = [], 0, 0, {}, set()

	pool = ThreadPoolExecutor(max_workers=len(tokens))
	deadline = time.time() + 600
	while time.time() < deadline:
		st = poll_state(pin, probe)
		if st.get("status") == "Ended":
			break
		if st.get("phase") == "question":
			row = st["question"]["question_row"]
			if row not in done_rows:
				done_rows.add(row)
				results = list(pool.map(lambda t: submit(pin, t, row), tokens))
				lat, ok, errors = report_salvo(len(done_rows), results)
				all_lat += lat
				total_ok += ok
				total_reqs += len(results)
				for k, v in errors.items():
					all_errors[k] = all_errors.get(k, 0) + v
		time.sleep(1.3)  # get_state is rate-limited 60/60s; stay under 1/s
	pool.shutdown()

	print("\n=== overall ===")
	print(f"questions driven: {len(done_rows)}  submits: {total_reqs}  ok: {total_ok}")
	if all_lat:
		all_lat.sort()
		print(
			f"latency ms  p50={pct(all_lat, 50):.0f} p95={pct(all_lat, 95):.0f} "
			f"p99={pct(all_lat, 99):.0f} max={max(all_lat):.0f} mean={statistics.mean(all_lat):.0f}"
		)
	print(f"errors: {all_errors or '-'}")
	return 0 if total_ok == total_reqs and done_rows else 1


if __name__ == "__main__":
	sys.exit(main())
