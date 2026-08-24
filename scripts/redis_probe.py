"""One-off: inspect rq registries for stale gp_ticker jobs blocking dedup."""

import redis

r = redis.Redis(host="127.0.0.1", port=18131, decode_responses=True)
QUEUE = "rq:queue:home-minte-projects-training-apps:long"

print("queue len:", r.llen(QUEUE))
for jid in r.lrange(QUEUE, 0, -1)[:20]:
	fn = r.hget(f"rq:job:{jid}", "job_name") or ""
	if "ticker" in str(fn):
		print("QUEUED TICKER:", jid, fn)

for suffix in ("started", "deferred", "scheduled", "failed_job_registry", "finished"):
	reg = f"rq:registry:{QUEUE}:{suffix}" if suffix != "finished" else f"rq:registry:{QUEUE}:finished"
	n = r.zcard(reg)
	print(suffix, n)
	for m in r.zrange(reg, 0, -1)[:10]:
		fn = r.hget(f"rq:job:{m}", "job_name") or ""
		if "ticker" in str(fn) or n < 6:
			print("   ", m, str(fn)[:60])
