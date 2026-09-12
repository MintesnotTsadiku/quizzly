# Publishing and replay

Implement one site publication policy in GatherPlay Settings, enforced in discovery and new session creation, including document/API entry points. Existing rooms retain access after unpublishing. Start with Quiz, Common Ground, Crowd Compass, CueCast, Doodle Dash and Sequence Sprint; verify them in the browser before release. All 26 registry formats and their original illustrations remain installed.

Persist random content selection at creation. Independent question/prompt formats support a bounded batch, show available/selected counts, and keep a stable order. Preserve ordered Escape stages, complete Bracket tournaments, Story Loom's story progression, and fixed board layouts. CueCast uses team turns and a timed prompt stream; its settings and exhaustion must be explicit.

Replay is an authorized successor to an ended room, serialized and idempotent per source. Store cumulative history and the selected order in the database, scoped by format, pack and language. Exclude seen content, allow a smaller final batch, and require an explicit reset after exhaustion. Preserve original guest/host identity and entitlement checks. Continuing players retain their credentials and receive the next room; unrelated groups keep independent history.

Verify publication permissions and all entry points, batch validation, durable order, replay authorization, concurrent requests, exhaustion, reset, pack/language boundaries and representative host/player/projector/mobile English/Amharic sessions. Run existing regression suites and a production build. Commit and push develop once reviewed.
