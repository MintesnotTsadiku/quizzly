# Game interface repairs — 6 September 2026

This implements the findings in the [original audit](README.md). The old screenshots and game illustrations are retained. The replacement experiences are running on the local QA site; this is not a production deployment.

## What changed

| Finding | Implemented behavior |
|---|---|
| Dots & Boxes was a text quiz | A shared 3×3 box board with 24 clickable edges, two stable sides, rotating controllers, extra turns for completed boxes, nine territory points and a scored ending. |
| Group Sudoku had no grid | A cooperative 4×4 board with protected givens, 2×2 regions, number controls, notes, erase, conflict rejection and completion. |
| Path Weaver had no route | A persistent route through three checkpoints, blocked cells, adjacency validation, undo and a reachable exit. |
| Hidden Picture had no nonogram | A 5×5 grid with both row and column clues; fill/cross/unknown marks and completion detection. |
| Quilt Puzzle had no pieces | Four distinct patches, rotation previews, placement, removal, overlap/boundary validation and complete coverage. |
| Picture Peek lacked clue images | Original object illustrations appear on host, player and projector, with descriptive alternatives. |
| Memory Mosaic was an ordinary quiz | Ten-second study, hidden-scene recall, then image-and-answer reveal. The question is withheld during study. |
| Sound Snap had no audio | Bundled synthesized listening clips, native play/replay/volume controls and an optional visual pitch pattern. |
| Caption Clash lacked images and payoff | A real picture prompt, anonymous voting and contribution/author/vote/points reveals that survive reload. |
| Bracket Bash was a predetermined quiz | Four-, eight- or sixteen-entry majority tournaments. Winners advance; a disclosed first-seed tie rule prevents deadlocks. The ending names the room’s champion. |
| Signal Spectrum used an unexplained number field | Authored opposite endpoints, a 0–100 slider, hidden authored target and distance-based reveal. |
| Escape Together had no shared objective | Ordered Lantern Library stages, collected clues, majority unlocks and retries after failed attempts. Failed attempts cannot farm points. |
| Story Loom discarded the story | The selected continuation joins the shared story and is carried into the next round. The finished story persists and can be copied. |
| One Word Chorus duplicated a word quiz | A rotating guesser, private target for clue givers, one-word submissions, duplicate-clue removal and a cooperative guessing phase. |
| Seek & Show automatically rewarded all text | A room-showing phase and host acknowledgement before mission points. Describing a find is allowed; no photo upload is required. |
| Ordering answers could not be edited | Remove a selected card or undo before locking. New packs contain actual sequences and phrases. |
| Generic/answer-disclosing content | Additive English and Amharic curated packs for all 15 round formats, including actual connection clues, estimates and bluff prompts. |
| Amharic and symbol answers collapsed to empty | Unicode normalization preserves letters and meaningful symbols. Empty answers cannot accidentally match. Doodle guesses use the same normalization. |
| Response locks vanished on reconnect | Private snapshots report accepted answers/votes/clues. The UI uses those locks; rejected submissions remain editable. Server-derived round input keys prevent concurrent duplicate answers. |
| Creative reveals disappeared after reload | Full contribution results are persisted in round resolution and module snapshots. |
| Doodle lost long stroke tails | Continuous bounded batches, ordered delivery, retained failed batches with retry, an atomic replay marker and serialized canvas updates. The capacity limit rejects further input instead of silently deleting the beginning of a drawing. |
| Guess also emitted an invalid generic submit | Native form propagation is stopped. Browser verification sees one successful guess request. |
| New boards were stale on other devices | Game-specific update events and correct multi-hyphen matching. Public events no longer replace private roles or unmount live drawing/board controls. |
| Availability did not reflect maturity | The five new board formats are explicitly Beta, with playable practice boards and supported device modes. Their current content is one complete starter layout each. |

## Participation and endings

The five puzzles support player devices, a single host-controlled board, and an optional read-only projector. Dots & Boxes assigns X/O sides and rotates controllers within those sides; the other four puzzles are cooperative. Shared-device play starts from the normal lobby without requiring fake participants. The host can help place moves, pause and resume.

The practice pages replay bounded move lists through the same server rules as live games. They create no sessions or participants. Live moves use authenticated roles, revision checks, a session lock and durable round snapshots. Illegal or stale moves cannot overwrite a newer board.

All host endings offer a fresh room with the same settings. Puzzle endings retain the completed board and offer a friend-challenge link without player names or a room code. Story endings retain the written story. Bracket and Escape endings emphasize the shared outcome instead of an artificial individual ranking.

## Architecture and deployment

- `quizzly/games/board_session.py` now owns durable human-paced sessions; the old Grid Conquest import path remains a compatibility shim. Existing snapshot storage stays readable.
- `quizzly/games/puzzles/rules.py` contains pure game-specific legal moves and completion rules. `puzzles/game.py` adapts them to the existing authentication, event and score systems.
- The round engine retains bounded-input games. Story, bracket, chorus, mission and escape progression have dedicated adapters in `round_games/special.py`.
- Media requirements are enforced when saving content and when hosting. Invalid old media packs produce an actionable error instead of silently running a different game. Curated packs are listed first.
- `quizzly/demo/curated.py` adds versioned starter packs without overwriting existing packs. It runs after migration and from the existing full-demo seed command. Original assets stay in place; new SVG and WAV clues ship with the app.
- No database schema change or church-system dependency was introduced. Existing site access policy, authentication, tenant branding, language selection and embedding boundaries remain in use.

On another server, deploy the code, run the normal site migration and frontend production build, then restart its services. The migration adds the curated packs; there is no need to delete or regenerate existing content. The exact production service configuration remains the server operator’s responsibility.

## Verification

- **52 regression tests:** legal/illegal board actions, full solutions, Unicode/symbol comparisons, private response locks, persisted creative reveals, media lifecycle and validation, bracket progression, story accumulation, chorus roles, mission acknowledgement, escape retry behavior and atomic replay markers, alongside existing Grid/Crowd/Common Ground/recovery tests.
- **15 complete round-game browser sessions:** authenticated host, two isolated guest players and a projector; rendered input controls, ordering edit, media playback, voting, reconnect locks, persisted reveals and endings. Story and Chorus ran multiple rounds; Bracket and Escape completed their progression. [Results](evidence/after/sessions.json).
- **Five complete two-player puzzle sessions:** pause/resume, full solutions, projector agreement, mobile reload and durable endings. Dots additionally verifies a rejected out-of-turn command and all nine points. Its one expected HTTP 417 is recorded; it is not an unexpected application failure. [Results](evidence/after/puzzles.json).
- **Five host-only UI starts:** each starts with no joined participants, accepts a move and survives reload. [Results](evidence/after/shared-device.json).
- **Doodle and CueCast:** 12 short and 120 long drawing segments synchronized, the correct guess sent one request, and performer secrets stayed private. [Results](evidence/after/native.json).
- **Grid Conquest regression:** all 15 existing browser checks pass, including lost-cache recovery, late joins, concurrent moves, replay, host-only ties, authenticated iframe controls and a 360px Amharic layout.
- **Amharic:** correct and distinct incorrect words scored differently through real mobile controls and survived reload. [Results](evidence/after/amharic.json).
- **Agent Plane:** interacted with the actual Dots practice board and Amharic Sudoku guide; no console or network errors. [Record](evidence/after/agent-plane.jsonl).
- Additive migration seed rerun: all 30 English/Amharic curated packs remain present with no duplicates or replacements.
- Production frontend build and changed-file lint checks pass. Build-time font URL notices refer to runtime-served bundled fonts; browser requests load them successfully.

Representative screens: [Dots completed](evidence/after/dots-and-boxes-complete-player.png), [Sudoku completed](evidence/after/group-sudoku-complete-player.png), [memory study](evidence/after/memory-mosaic-study.png), [caption reveal](evidence/after/caption-clash-reveal.png), [Amharic scoring](evidence/after/amharic-scoring.png), [interactive practice](evidence/after/dots-and-boxes-practice.png).

[90-second working-session video](evidence/after/working-session.mp4). Raw recordings remain local; the reviewed excerpt ships with the repository.

### Release criteria and limits

Each enabled participation mode must have real input controls, authoritative legal actions, a worked guide, host/player/screen agreement, reload behavior and an ending. These criteria are now exercised for the starter experiences above. The new puzzle layouts are fixed starters, not a procedural puzzle library. Browser checks use small QA rooms; they are not a 100-player load test or exhaustive validation of customer-authored packs. Amharic has content and browser coverage, not an independent linguistic review. Existing common platform flows retain their regression coverage; no production server was accessed.
