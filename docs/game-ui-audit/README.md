# Gathering-game interface audit — 5 September 2026

Reviewed application revision: `3ef474d` (the interactive Grid Conquest fix).

**The Grid Conquest problem is not isolated. Five other board/puzzle games still use text questions and answer buttons instead of playable puzzle surfaces. Several additional games have missing content or incomplete game mechanics.** This is an audit, not a claim that these issues are fixed.

## Method and limits

Played a representative English demo round for each of the 20 remaining games registered to the shared round renderer. Each run used a real authenticated host, two isolated guest browser contexts, and a shared screen, against the locally served production build. Players submitted using the rendered controls; creative voting games also went through their ballots. Host progression and reveal snapshots were recorded. Agent Plane separately inspected the illustrated Dots & Boxes and Group Sudoku detail pages.

This establishes the current interaction contract, not exhaustive correctness across every pack, language, group size or complete match. Some manifest minimums exceed the two-entry diagnostic room; the platform permits those starts. That is not a claim that two entries suit every game's design. Native Doodle Dash and CueCast have separate focused checks recorded in `evidence/native.json`. Grid Conquest's full-match verification is in `../grid-conquest/README.md`. Crowd Compass, Common Ground and the original quiz were not given another full regression run here.

No production server was accessed. No product code, existing images, catalog availability, or customer content was changed by this audit.

## Confirmed board mismatches — highest priority

| Game | What actually happens | Required interaction |
|---|---|---|
| Dots & Boxes | Text says which three edges exist; players choose “Top edge”, etc. No dots, edges, boxes or territory ownership. | Tap a real edge; synchronize it; claim completed boxes; grant the completing side its extra turn; rotate controllers; finish on territory score. |
| Group Sudoku | A sentence describes part of a row and column; players select a number. No grid, editable cells, notes or regions to inspect. | A shared 4×4 starting grid; cell selection and symbol keypad; visible givens/regions; conflict feedback; a completed-grid goal. |
| Path Weaver | Choose a word such as RIGHT from four choices after reading route constraints. No persistent route or traversable board. | Visible start, destination and blocked cells; tap neighboring cells to extend a shared path; undo; detect legal completion. |
| Hidden Picture | Choose a text pattern such as `■■■··` for one row clue. No nonogram or evolving picture. | A small grid with row and column clues; fill/cross cells; distinguish tentative marks; reveal the completed picture. |
| Quilt Puzzle | Choose the next color/shape in a text sequence. No quilt or movable patches. | Visible target and patch tray; placement/rotation with touch and keyboard alternatives; overlap/boundary validation; completion feedback. |

All five had zero playable canvases and no actual board surface in the recorded host/player/projector views. A canvas is not required technically—accessible DOM/SVG boards are preferable where appropriate—but actual cells, edges or pieces and authoritative state are required. Replacing their pictures or restyling answer buttons would not solve this.

Screenshots: [Dots & Boxes](evidence/dots-and-boxes-player.png), [Sudoku](evidence/group-sudoku-player.png), [Path Weaver](evidence/path-weaver-player.png), [Hidden Picture](evidence/hidden-picture-player.png), [Quilt Puzzle](evidence/quilt-puzzle-player.png).

## Media and content failures

**Picture Peek, Memory Mosaic and Caption Clash:** all three English demo catalogs have **36 items each, zero with `media_url`** on this site. Live runs confirmed the absence of clue pictures. The Picture Peek prompt even named “courage” in a generic connection clue; it did not present the illustrated animal-identification example. Memory Mosaic asked a generic “Which clue best completes this coffee break challenge?” question.

The Amharic catalogs each have three items with an image URL. However, the shared renderer displays clue media only on the projector, not on host/player views. That can support an explicitly shared-screen game, but cannot fulfill a phone-only mode without another way to see the clue. Memory Mosaic also has no distinct study/hide/recall phases; with media supplied, the same scene remains available while answering.

**Sound Snap:** no audio element, player, or audio-specific round state exists. Current written instructions describe sound-related text clues, so the absence of audio is not a hidden failure of a working audio player. It is an unimplemented listening-game format, compounded by generic English demo questions unrelated to the promised sound example. Either implement licensed sound clips, explicit playback/replay and accessible alternatives, or label the retained text variant honestly.

Required repair: validate content against each game's media requirements when publishing packs, supply matching real content, and show a helpful unavailable-content state rather than silently hosting a different kind of game. Keep old assets; map new validated content explicitly to the rules version it supports.

## Other interaction and game-design gaps

| Game | Assessment |
|---|---|
| Bracket Bash | It is a predefined-answer quiz. No majority ballot determines a winner, no bracket advances, and no tournament state persists. Needs an actual bracket and room voting. Its current detail copy acknowledges the reduced mode; that acknowledgement is not a tournament implementation. |
| Signal Spectrum | Numeric input works, but there is no spectrum/marker control or clear visual endpoints. The tested prompt was “Where should 'scroll' land from 0 to 100?” with no meaningful axis. Needs authored endpoints and target/clue rules before adding a slider; otherwise it duplicates estimation. |
| Escape Together | Independent multiple-choice rounds with generic demo questions; no shared escape objective, linked stages, clue inventory or progress. Needs a coherent scenario and stage state, or an honest puzzle-quiz identity. |
| Story Loom | Submission and anonymous voting work. There is no accumulated story or selection of a continuation that feeds the next round. The tested reveal displayed the seed word “stage,” not the room's finished story. Needs persistent story state and an ending people can read/share. |
| One Word Chorus | Uses the same exact-word guess interface as Common Thread; no individual clue-collection interaction. Keep a distinct identity only if the intended cooperative clue mechanic is implemented. |
| Seek & Show | Real-world activity can appropriately use light screen support, but the implementation accepts a text description and awards the creative base score. There is no room/host acknowledgement of the physical result. Add facilitation/confirmation appropriate to the room rather than automatically requiring photo uploads. |

## Shared controls that can remain

- **Sequence Sprint / Phrase Forge:** selecting cards in order is a legitimate ordering interaction. Both accepted orders and revealed results. They need edit/undo/reorder before locking and stronger content; the sampled Phrase Forge pack reused the same four generic action cards as Sequence Sprint.
- **Closest Call:** one numeric estimate is appropriate; it does not need a board. Improve content and show distances clearly at reveal.
- **Common Thread:** a text guess is appropriate for a connection puzzle. The sample prompt disclosed its own answer (“The clues point toward ...”), so the content needs repair.
- **Bluffline:** text submissions and anonymous voting are the right basic controls. Improve believable questions, truth reveal, attribution and score explanation.
- **Caption Clash:** submission and voting controls are appropriate once real visual prompts are supplied. It does not need a separate board engine.

“Appropriate controls” means the input model fits the game. It does not mean the game's content, replayability, accessibility or full session is approved for release.

## Purpose-built interfaces checked

- **Doodle Dash:** a real artist canvas, live spectator drawing and guess input exist. A short drawn stroke synchronized, and the other player correctly guessed the private prompt. However, a continuous stroke with 120 pointer segments transmitted only 80. Every tested Guess click also emitted an extra generic `submit` request, rejected with HTTP 417 / “Unknown action”, alongside the successful `guess` request. The shared shell's undeclared submit listener falls through to the drawing component's native form. The request-level reproduction is retained in `evidence/doodle-probe.json`. The canvas sends `batch.splice(0, 80)` at pointer-up and drops the remainder, so long strokes lose their tail for everyone else and after repaint. It has the right interaction model but needs this synchronization fix before approval.
- **CueCast:** the designated performer saw the secret prompt; the other player and public snapshot did not. Solved and Pass buttons advanced prompts. Its role-specific interface fits the acting/description game. This was not a full match or large-group certification.

## Cross-cutting findings

1. **Shared exact-answer normalization destroys Amharic text and symbol-only answers.** `RoundGame.norm` strips every character outside ASCII letters, digits and spaces. Two different Amharic words both normalize to an empty string; the scoring comparison therefore treats them as equal. Different Hidden Picture options such as `■■■··` and `■·■■·` also both become empty, making incorrect patterns compare equal to the answer. This applies to shared choice/text scoring and needs a Unicode-safe comparison that preserves meaningful symbols, plus language and puzzle regression cases. The independent probe is recorded in `evidence/content.json`.
2. **Locked responses are not represented in private snapshots.** The shared player component stores a local `locked` flag, while `serialize_player_state` does not return whether the player has already answered. Reload/reconnect can therefore present a new response form even though the server rejects a second submission. This is a source-confirmed issue, not a reconnect test claim for every game here.
3. **Generic creative reveals discard the social payoff.** API event payloads include some results, but the shared renderer mainly displays the predefined `answer`; snapshots do not reconstruct the full response/results presentation. Story and caption games need to celebrate actual contributions.
4. **Catalog availability overstates completion.** Shared profiles are marked Available despite missing distinct mechanics and inadequate seed content. Define release criteria per game and participation mode. Keep incomplete formats explicitly in preview until those criteria pass.

## Recommended implementation order

1. Fix Unicode scoring, Doodle Dash's dropped stroke segments and duplicate submit event, and the missing-media publishing guard, because these affect correctness across games.
2. Implement Dots & Boxes and Group Sudoku as the next two real board experiences. Reuse Grid Conquest's authentication, versioned command and durable-state foundations, but give each game its own legal moves, completion rules and scoring.
3. Implement Path Weaver, Hidden Picture and Quilt Puzzle with appropriate board state and accessible input models.
4. Build the media lifecycle for Picture Peek, Memory Mosaic and Sound Snap; ship real clue assets and validated packs.
5. Add Bracket Bash's real voting progression and Story Loom's accumulated story. Reclassify or consolidate weak quiz variants while improving the remaining authored content.

For each game, acceptance must include: a concrete worked guide using the real component; legal and illegal actions; host/player/shared-screen agreement; the supported device arrangement; reload/reconnect; completion and replay; English/Amharic scoring; and actual content that matches the guide. An API round advancing successfully is not enough.

## Evidence

`evidence/audit.json` records the actual pack, prompt, input mechanic, controls, submitted round and reveal for each shared-renderer game. `evidence/content.json` contains demo-media coverage and the Unicode probe. `evidence/agent-plane.jsonl` records the separate browser-guide inspection. The `*-player.png` and `*-screen.png` files capture representative live input states. `audit-excerpt.mp4` contains a short working-session excerpt. Expected findings are product defects, not successful product acceptance simply because HTTP requests returned successfully.
