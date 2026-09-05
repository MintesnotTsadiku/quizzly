# Grid Conquest: a playable board, not a question about one

## Finding

The user's screenshot was accurate. A real local host and two guest browsers reproduced the same experience: an X/O position represented as text, followed by multiple-choice answers such as “Top right.” Nobody could place a mark. Functional question-round tests had not established that this delivered the game promised by the illustration.

This review covers Grid Conquest. It does not certify the remaining games. In particular, the other board-themed question formats still need their own play-through and product review.

## Shipped interaction

- One synchronized 3×3 board. X and O take turns placing marks in empty squares.
- Two sides, up to three boards; first to two wins or the highest score after three. A drawn board awards no point. Equal match scores produce equal ranks and an explicit draw.
- The starting side alternates each board. The host advances only after everyone has seen the winning line or draw.
- **Player devices:** at least two joined entries. One device can represent a person, pair or household. Entries are assigned to two sides, with the active controller rotating within each side. Other players see whose turn it is. Late arrivals join a side without stealing an already allocated turn.
- **One shared board:** the host device places both X and O. Pass the device or let the host place the side's chosen mark. No guest devices need to join.
- A read-only shared screen shows the same moves and highlighted winning cells. The host can explicitly help place one mark when a participant needs assistance; normal control resumes immediately afterward.
- Pause/resume, keyboard navigation and native button activation, responsive cells, English/Amharic copy, and preserved iframe authentication.
- Discovery offers a playable worked board using the live board component. No question pack or countdown is required to start a new match.
- Results survive reload; replay creates a fresh lobby. The replay Start-button state and explicit session-link selection were also corrected.

The strongest fit is two people or two small sides. Larger groups can rotate controllers and discuss moves, but this is not a claim that ordinary tic-tac-toe provides equal engagement for 100 simultaneous players. No forced timer or artificial failure penalty has been added.

## Architecture and safety

`rules_version: 2` distinguishes new board sessions from legacy question sessions. The registered Grid module delegates legacy state handling to the old implementation. Existing packs, records and illustration files are retained. No DocType migration or data regeneration is required for this change.

Moves are server-authoritative. The API verifies the participant token and active controller, checks the expected revision and cell, and serializes commands with a Redis session lock plus a database row lock. The database snapshot uses a **locking read** for mutations: the simultaneous-request test exposed that a plain read could otherwise use an earlier MariaDB repeatable-read snapshot even after waiting for the lock. Only one of two same-revision concurrent requests now succeeds.

Every accepted transition checkpoints its state in the existing GP Round resolution JSON. Read-only recovery never writes an old snapshot back into the hot cache. A lost Redis board value therefore does not lose the match. Board wins use the existing score ledger; equal ranks are preserved. Board sessions do not depend on the quiz ticker, and the recovery watchdog does not enroll them in it.

This deliberately introduces a distinct board module instead of extending the multiple-choice abstraction further. The three live wrappers share one board component and retain the legacy renderer for old sessions.

## Validation and evidence

- Unit/regression suite: 34 passing tests covering all eight winning lines for both marks, legal moves, draws, role boundaries, rotation, late-controller stability, host assistance, match completion, legacy rendering delegation, locked snapshot reads and equal ranks, plus existing recovery/Crowd Compass/Common Ground/reveal/branding checks.
- Keyboard browser check: arrow navigation and Enter complete the practice board; reset works with reduced-motion enabled.
- Production frontend build completed successfully. Frappe serves the existing bundled font stylesheet at runtime; Vite's build-time unresolved font URL notice is expected.
- Agent Plane opened the actual detail page, placed the winning practice mark and captured the page. No browser console or network errors were reported.
- Isolated real browser contexts exercise host, three guest entries, projector and authenticated iframe. The final run uses the production-built local application, not only the Vite preview.
- The network suite verifies complete matches, late join and rotation, out-of-turn and occupied-cell rejection, stale revisions, pause, reload, lost cache recovery, host assistance, replay, host-only play, equal-rank draws, concurrent requests and Amharic mobile layout.

See `evidence/after-results.json`, `evidence/unit-tests.txt`, `evidence/build.txt` and `evidence/agent-plane.jsonl` for recorded results. Representative views are `before-player.png`, `after-player.png`, `after-host.png`, `after-shared-screen.png`, `after-match-results.png`, `after-match-draw.png`, `after-embedded.png` and `after-amharic-mobile.png`. `working-session.mp4` is a short excerpt; `after-session.webm` retains the full run.

QA uses the configured browser-QA account without printing credentials. Test-owned room identifiers are inventoried outside the repository for narrow cleanup; no production server was accessed.

## Deployment and review

Deploy frontend and backend together, build the frontend assets and restart the application processes. Open **a new Grid Conquest room** after deployment: existing rooms deliberately retain their original rules. No game-pack regeneration is needed for this board.

Review this game before applying the pattern to the rest of the catalog. Next, play Dots & Boxes, Path Weaver and the other board-themed entries against their illustrated promises; retain a question format only when the product honestly presents it as a puzzle quiz.
