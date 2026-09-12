# Site publication and content replay

## Publication

The `published_games` field in the site's **GatherPlay Settings** is authoritative. Manage it at `/play/manage/games` (the **Published games** navigation link). Only System Managers can inspect or save the management API; the existing DocType permissions protect direct writes. An absent policy uses the starter selection; an explicit empty list publishes nothing. Missing settings defaults are initialized additively on migration, preserving every saved field.

The six starter formats are Quiz, Common Ground, Crowd Compass, CueCast, Doodle Dash and Sequence Sprint. They cover a familiar quiz, a host-only conversation, room polling, acting, drawing and ordering. All 26 installed modules, illustrations, existing sessions and private packs remain intact. Unpublished formats disappear from standalone and embedded discovery, detail/setup URLs and public pack listings. New sessions—including direct document creation—are rejected. Existing lobbies and active rooms can finish; starting a successor requires the format to remain published.

## Registry audit

| Formats | Content and supported settings |
|---|---|
| Quiz | Random question count; defaults to up to ten in the setup UI. Selected child IDs persist in session order. |
| Common Ground | One to five conversations; defaults to three. Host-paced, about 2½ minutes per conversation plus discussion. English and Amharic use separate history scopes. |
| Crowd Compass | Random pack count, vote/prediction timers, pacing and optional finale. Live prompts are not drawn from a finite pack and do not participate in pack history. |
| CueCast | A random prompt pool, timed team turns and existing team/scoring rules. Prompts no longer wrap or restart between turns. Running out can end a game before every planned turn; exhausted performers see an explanation and disabled input. |
| Doodle Dash | Random word count and drawing timer; artists still rotate. |
| Bluffline, Sequence Sprint, Picture Peek, Sound Snap, Caption Clash, Signal Spectrum, Memory Mosaic, Common Thread, Closest Call, Phrase Forge, Seek & Show, One Word Chorus | Random independent items and existing game-specific timing/input rules. Ordering *within* a Sequence Sprint or Phrase Forge item is unchanged. Media and content validators remain in force. |
| Story Loom | Choose story length; the room builds one connected story. Its later rounds are continuations, not independent pack questions. Replay starts a new story and does not claim unseen prompt coverage. |
| Escape Together | All stages remain in authored order; failed stages retain their retry rules. A short batch cannot produce a false escape. |
| Bracket Bash | Full four-, eight- or sixteen-entry tournament; entrant count determines matches. No random question subset. |
| Grid Conquest | Existing three-board match. |
| Dots & Boxes, Group Sudoku, Path Weaver, Hidden Picture, Quilt Puzzle | Existing complete fixed starter layouts, still Beta. No question-count or unseen-board claim. |

## Durable replay

Each session stores `play_batch`: scope (format, pack, content language), requested size, selected order, preceding history and observed item IDs. Selection is without replacement. IDs enter history when a prompt is shown, including a shown prompt that is skipped; assigned items never reached remain available. Reconnection reads the stored order. Editing interface language does not silently change pack language. Choosing another pack creates a fresh sequence; changing a pack's content language requires an explicit reset. Deleting questions does not reshuffle a room.

An ended room has at most one `next_session`. Replay authorizes the existing host or private browser-trial capability, then reads the current database row under a lock. The current read matters under MariaDB repeatable-read isolation: a plain reload can still see an older successor pointer. The transaction commits before the distributed lock is released. Repeated/concurrent requests return the same successor, including when the first response is lost. The next batch keeps the requested size, or uses all remaining items when fewer remain. Exhaustion requires an explicit group reset or a different pack. Older rooms without a ledger require an explicit reset before claiming non-repeating replay.

Eligible participants are copied with their existing token hashes, new participant rows and reset scores. Kicked participants are not transferred. Authorized old-room snapshots reveal the next room; connected players and projectors follow it. Guests continue through the existing restricted host adapter and retain trial/IP limits. This is a new room code and a new scored session, not a global reset of pack availability. A replay request from an old ending returns its existing successor instead of creating another branch.

## Development environment

Site: `training.localhost`. Frontend: `http://127.0.0.1:8081/play/`. Internal backend/Desk: `http://127.0.0.1:18033/app`. Socket.IO: 19031. Redis cache/queue: 18331 / 18131. Vue uses the existing same-origin API and Socket.IO proxy.

`tmux attach -t training-dev` shows the bench, Vue frontend and two dedicated `bench --site training.localhost worker --queue long` panes. Both Quiz and GatherPlay have long-running ticker jobs; they need concurrent long-queue capacity alongside the general worker. No site clone was made. The Administrator credential was reset and used with explicit user authorization; no secret is stored in the repository. Browser QA accepts its password through `QUIZZLY_ADMIN_PASSWORD`.

## Verification

Browser evidence is in [evidence/](evidence/):

- `browser.json`: Common Ground 3 + 2 exhausts all five prompts; stored order survives reload; projector follows; explicit reset retains the request. Quiz simultaneous replay requests return one successor and its original player token continues. Crowd Compass transfers a guest player to an unseen prompt.
- `publication.json`: the System Manager UI saves; guest management requests fail; catalog, direct detail, API hosting and the authenticated Church Management `/home/games` iframe follow the same policy. An existing unpublished room finishes; a new successor is denied. Saving an empty list publishes nothing.
- `guest-replay.json`: another browser cannot replay a guest room; a retry returns the same room; explicit reset cannot bypass the two-game trial.
- `agent-plane.json`: actual Agent Plane browser verification of Amharic mobile setup, with no console or network errors. Mobile screenshots show the final controls at 390px.
- `native.json`: Doodle Dash strokes/guesses and CueCast private prompts, solved/passed actions and completed sessions.
- `round-games.json`: all fifteen round formats finish through browser inputs, reconnect, reveal and ending. This includes Sequence Sprint, authored Escape stages and a complete Bracket tournament.

The legacy native/round audit runners were reused against the current production build. Their output was redirected to temporary directories so the earlier audit evidence remains unchanged. All formats were temporarily published for those regressions and the six-format policy restored in a `finally` block. No browser console errors were reported. Fifty focused game-rule/recovery tests and both frontend test files pass. The production build passes; Vite retains the existing runtime-resolved font asset warnings.

`bench --site training.localhost run-tests --app quizzly` passes all **189 cases** (1 unit, 136 integration and 52 remaining unit cases), including all 12 new publishing/batch tests. The integration portion took 737.869 seconds because it exercises real timed turns. The complete sanitized output is [bench-tests.txt](evidence/bench-tests.txt). All configured pre-commit hooks pass on the changed files: syntax/JSON checks, Ruff, formatting, Prettier and ESLint. The final production build and both frontend test files pass. A final Bench read confirms the six starter formats are restored.

## Operating limits

Content history belongs to this successor chain, not to a user across unrelated rooms. Starting a separate room intentionally starts an independent group. Players keep identities but scores reset; team games use their existing lobby assignment rules. A host must explicitly reset a legacy room with no observation ledger. Ordered story/tournament/board formats retain their existing rules and do not promise unseen question batches. Administrators can publish additional installed formats, including Beta boards, after reviewing them for their event.

