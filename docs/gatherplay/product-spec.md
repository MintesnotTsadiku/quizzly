# GatherPlay Product Specification

Status: Proposed
Product: GatherPlay, with Quizzly as its live quiz module
Audience: Product, design, content, engineering, QA, event hosts, and moderators
Related documents: [Platform architecture](platform-architecture.md) · [Implementation plan](implementation-plan.md)

## 1. Product understanding

Quizzly is an existing live, browser-based multiplayer quiz built on Frappe Framework, Vue 3, Frappe UI, Socket.IO, Redis, and RQ. An authenticated host creates a quiz and starts a session. Guests join without accounts through a QR code or six-digit PIN, use their phones as controllers, and follow a host-led experience on a shared display. Questions are timed, answers are scored on the server, and results and rankings are presented in real time.

The expansion turns that proven host-screen-plus-phone pattern into a collection of independent live group games. Games share session creation and joining, guest identities, teams, realtime delivery, timers, public presentation, scoring, reconnection, moderation, content packs, and tournaments. Each game owns only its rules, content, actions, private roles, state transitions, scoring policy, and views.

The platform must remain effective for one to four people, small teams, and rooms of 100 or more; work without guest accounts; tolerate moderately slow or unreliable networks; keep secret information off public channels; and remain suitable for church, youth, family, classroom, conference, and general community settings.

## 2. Product principles

1. **The room is the product.** Phones support the gathering; they should not isolate participants from it.
2. **Joining is nearly effortless.** QR or PIN, safe nickname, optional avatar, then play.
3. **The projector creates theatre.** It communicates the current beat, builds anticipation, and never exposes private prompts or controls.
4. **The host stays in control.** Every game supports pause, recovery, moderation, adjudication, and an understandable next action.
5. **The server is authoritative.** Deadlines, allowed actions, outcomes, and scores are not trusted to clients.
6. **Every participant has a role.** Large-room games use simultaneous input, voting, guessing, prediction, or rotating representatives rather than long idle queues.
7. **Content is portable and contextual.** The same mechanic supports church/Bible, child/family, educational, and general-event packs.
8. **Failure is recoverable.** Reloading, reconnecting, or a worker restart must not silently corrupt a game.
9. **Safety precedes projection.** Guest-created text, drawings, audio, and photos are moderated before public display.
10. **Accessibility is part of the mechanic.** Games provide alternatives for color, sound, motion, dragging, and fine motor input.

## 3. Game catalog and detailed concepts

### 3.1 Quizzly

- **Core idea:** Timed live quiz questions with bounded answer choices, speed-aware scoring, explanations, rankings, and a final podium.
- **Players:** 1–100+; individual by default, with collaborative-captain and team-average modes planned.
- **Host sees:** Question controls, answer count, timer, distribution, correct answer, explanations, moderation, and standings.
- **Active players see privately:** Question and choices, locked-answer state, personal outcome, score, streak, and rank.
- **Audience sees:** Question, timer, response progress, answer reveal, distribution, leaderboard, and podium.
- **Round:** Ready beat, open question, answer collection, close, score, explanation/statistics, standings, and advance.
- **Scoring/winning:** Correctness, server-received response time, streak, and multiplier; highest total wins.
- **Enjoyment:** A familiar game-show rhythm with learning, competition, and shared reveals.
- **Complexity:** Existing/medium.
- **Special requirements:** Question authoring, answer secrecy, explanations, images later, load-tested submission path.

### 3.2 CueCast

- **Core idea:** A broad charades module supporting acting, verbal description, restricted-word clues, picture prompts, and later prop or sound modes.
- **Players:** 2–30 active; best with 6–20. Cooperative pairs or teams.
- **Host sees:** Team order, current performer, prompt queue, accepted/skipped prompts, timer, adjudication, and upcoming turns.
- **Active players see privately:** The performer sees the prompt, mode, restricted words, ready/correct/pass controls; teammates see a guesser state.
- **Audience sees:** Team, performer, mode, timer, round count, celebrations, and the post-turn prompt review—never the live prompt.
- **Round:** Performer confirms readiness, receives prompts one at a time, gives legal clues, and correct/pass is recorded until time expires.
- **Scoring/winning:** One point per correct prompt; optional skip penalty, difficulty multiplier, perfect-round bonus, equal turns, sudden-death tie.
- **Enjoyment:** Physical comedy, fast teamwork, and very little controller attention once performance begins.
- **Complexity:** Medium.
- **Special requirements:** Private prompts, teams, rotation, prompt decks, adjudication, moderation, optional images.

### 3.3 Doodle Dash

- **Core idea:** One participant draws a secret word on a phone while everyone else guesses.
- **Players:** 3–100; best with 8–40. Individual or team aggregation.
- **Host sees:** Artist, secret prompt, guess counts, connection health, invalidation controls, and accepted aliases.
- **Active players see privately:** Artist gets prompt and canvas; guessers get private text entry, rejected guesses, and correct confirmation.
- **Audience sees:** Live drawing, artist/team, timer, correct count, and final reveal.
- **Round:** Artist readies, stroke batches stream to the public canvas, guesses are validated, and the round ends by time or completion threshold.
- **Scoring/winning:** Guessers receive speed-scaled points; artist receives a capped bonus based on correct guessers.
- **Enjoyment:** Every drawing becomes a performance, and imperfect drawings are often the funniest.
- **Complexity:** Medium-high.
- **Special requirements:** Canvas, reliable stroke batching and replay, Redis canvas state, aliases, drawing moderation, touch/orientation support.

### 3.4 Bluffline

- **Core idea:** Players invent believable false answers and then identify the true one.
- **Players:** 4–100; best with 8–30. Individual or teams.
- **Host sees:** Submitted bluffs, similarity/duplicate warnings, moderation queue, approved choices, and truth.
- **Active players see privately:** Bluff entry followed by randomized voting choices that exclude their own bluff.
- **Audience sees:** Prompt, submission progress, approved anonymous choices, vote reveal, and who fooled whom.
- **Round:** Submit bluffs, moderate and mix with truth, vote, then reveal answer and authors.
- **Scoring/winning:** Points for choosing truth and each opponent fooled; duplicate bluffs are consolidated fairly.
- **Enjoyment:** Rewards knowledge, creativity, humor, and social reading.
- **Complexity:** Medium.
- **Special requirements:** Free text, similarity detection, anonymity, moderation, sensitive-content filters.

### 3.5 Crowd Compass

- **Core idea:** Players cast a personal vote and predict which response the room will choose most.
- **Players:** 3–100+; strongest from 15 upward. Individuals or team-average scoring.
- **Host sees:** Response and prediction counts without premature distribution, participation, and invalidation controls.
- **Active players see privately:** Personal vote, then a plurality prediction and locked state.
- **Audience sees:** Prompt, response progress, animated distribution, surprising result, and leaderboard.
- **Round:** Personal voting, prediction phase, lock, distribution reveal, and score.
- **Scoring/winning:** Correct plurality prediction; tied plurality choices all count; optional percentage-estimation bonus.
- **Enjoyment:** The content is the people in the room, so simple questions start conversations.
- **Complexity:** Low-medium.
- **Special requirements:** Voting, hidden aggregation, simultaneous submissions, poll packs.

### 3.6 Sequence Sprint

- **Core idea:** Arrange events, steps, images, verses, processes, or historical moments in the correct order.
- **Players:** 2–40; best with 4–20. Usually teams.
- **Host sees:** Each team's current sequence, locked status, hints, and correct order.
- **Active players see privately:** Draggable cards; collaborative mode synchronizes a team's ordering.
- **Audience sees:** Shuffled elements, progress without exact team choices, and an animated correct order.
- **Round:** Reorder and lock before deadline; server resolves exact and partial correctness.
- **Scoring/winning:** Correct positions, adjacent pairs, full-order and time bonuses; hints reduce score.
- **Enjoyment:** Supports history, Bible timelines, science, training, and narrative logic.
- **Complexity:** Medium.
- **Special requirements:** Drag-and-drop, team synchronization, images, partial-order scoring.

### 3.7 Picture Peek

- **Core idea:** Identify an image as it is progressively uncovered, deblurred, zoomed out, or assembled.
- **Players:** 1–100+; individuals or teams.
- **Host sees:** Reveal controls, accepted answers, image focal point, hints, and adjudication.
- **Active players see privately:** Guess input or choices, attempt state, and personal score.
- **Audience sees:** Reveal stages, timer, correct count, hints, and full image.
- **Round:** Increasingly useful stages appear; players get one guess or multiple penalized attempts.
- **Scoring/winning:** Earlier correct answers score more; incorrect attempts may reduce maximum score.
- **Enjoyment:** Instantly understandable and highly visual across objects, art, landmarks, logos, and Bible scenes.
- **Complexity:** Low-medium.
- **Special requirements:** Images, prepared masks or processing, aliases, licensing.

### 3.8 Sound Snap

- **Core idea:** Identify a sound, song intro, instrument, animal, place, speaker, or spoken clue.
- **Players:** 1–100+; individuals or teams.
- **Host sees:** Cue/replay controls, response progress, fallback clue, and answer.
- **Active players see privately:** Choices or text guess and an accessible alternative where configured.
- **Audience sees:** Audio visualization, timer, category, response count, and reveal.
- **Round:** Clip plays once or twice; players answer before closure.
- **Scoring/winning:** Correctness and speed; replay or hint reduces maximum points.
- **Enjoyment:** Changes the sensory rhythm and supports music, nature, languages, sermons, and effects.
- **Complexity:** Medium.
- **Special requirements:** Audio files, licensing, normalization, captions/accessibility.

### 3.9 Caption Clash

- **Core idea:** Write captions for an image or scenario, then vote anonymously.
- **Players:** 4–100+; individuals or teams.
- **Host sees:** All captions, automated flags, approval/rejection, duplicates, and finalists.
- **Active players see privately:** Caption entry and a ballot excluding their own entry.
- **Audience sees:** Image, finalists, voting animation, result, and author reveal.
- **Round:** Submit, moderate, select finalists, vote, and reveal.
- **Scoring/winning:** Vote points, finalist bonus, and optional host awards such as most wholesome or unexpected.
- **Enjoyment:** Produces room-specific humor and memorable shared artifacts.
- **Complexity:** Medium.
- **Special requirements:** Images, free text, voting, anonymity, strong moderation.

### 3.10 Story Loom

- **Core idea:** Build a collaborative story one sentence, scene, constraint, or audience-selected branch at a time.
- **Players:** 3–20 active writers; audiences to 100 can direct branches.
- **Host sees:** Continuations, author order, moderation, branches, constraints, and pacing.
- **Active players see privately:** Required word/emotion/character/twist and submission area.
- **Audience sees:** Story-so-far, branch choices, selected continuation, and finale.
- **Round:** One author continues or several submit and the audience selects; a new constraint follows.
- **Scoring/winning:** Cooperative completion, votes, constraint use, or host creativity awards.
- **Enjoyment:** Creates a unique artifact that can be silly, educational, reflective, or devotional.
- **Complexity:** Medium-high.
- **Special requirements:** Free text, moderation, voting, export, optional illustrations later.

### 3.11 Signal Spectrum

- **Core idea:** A clue-giver sees a hidden target on a scale such as ancient-modern and gives one clue; teammates estimate its position.
- **Players:** 2–30; best with 4–16. Teams or cooperative pairs.
- **Host sees:** Hidden target, clue, markers, reveal, and score bands.
- **Active players see privately:** Clue-giver sees target; guessers see adjustable spectrum without target.
- **Audience sees:** Scale, clue, marker discussion/movement, and dramatic target reveal.
- **Round:** Clue, team discussion, marker lock, reveal.
- **Scoring/winning:** Distance bands award zero to four; exact-center bonus.
- **Enjoyment:** Tests shared interpretation and how teammates think, not just facts.
- **Complexity:** Medium.
- **Special requirements:** Private target, slider, teams, curated spectrum pairs.

### 3.12 Memory Mosaic

- **Core idea:** Study a scene, grid, or sequence briefly and answer questions after it disappears.
- **Players:** 1–100+; individuals or teams.
- **Host sees:** Scene controls, question queue, progress, and difficulty.
- **Active players see privately:** Answers only after concealment.
- **Audience sees:** Study scene, blackout, question, and annotated reveal.
- **Round:** Study, conceal, answer one or more questions, reveal.
- **Scoring/winning:** Correctness, optional speed, and perfect-scene bonus.
- **Enjoyment:** Accessible to non-experts and rewards collective attention.
- **Complexity:** Low-medium.
- **Special requirements:** Images, timed concealment, annotations, accessible descriptions.

### 3.13 Common Thread

- **Core idea:** Identify the connection among progressively revealed words, images, sounds, verses, people, or clues.
- **Players:** 2–40; best with 4–20. Individuals or teams.
- **Host sees:** Clue schedule, guesses, aliases, and hint controls.
- **Active players see privately:** Guess input and prior rejected attempts.
- **Audience sees:** Clues one at a time and which teams solved, not the answer until reveal.
- **Round:** Add clues over time until solved or exhausted.
- **Scoring/winning:** More points with fewer clues; wrong guesses can lock a team until next clue.
- **Enjoyment:** Delivers strong shared aha moments across many content themes.
- **Complexity:** Low-medium.
- **Special requirements:** Mixed media, aliases, progressive reveal.

### 3.14 Escape Together

- **Core idea:** Teams solve a chain or graph of puzzles to unlock a final mission code.
- **Players:** 2–100, normally teams of 3–8.
- **Host sees:** Progress map, attempts, hints, stalled teams, and manual unlock controls.
- **Active players see privately:** Team puzzle, inputs, inventory, and hints.
- **Audience sees:** Mission map and aggregate progress without solutions.
- **Round:** Solve sequential/branching stages until final completion.
- **Scoring/winning:** Completion time plus hint and incorrect-attempt penalties; partial progress ranks unfinished teams.
- **Enjoyment:** Deep cooperation for lessons, retreats, orientation, and conferences.
- **Complexity:** High.
- **Special requirements:** Puzzle authoring, branching state, team secrets, hints, robust recovery.

### 3.15 Bracket Bash

- **Core idea:** Audience votes advance nominees—songs, characters, photos, ideas, performances, or creations—through a knockout bracket.
- **Players:** 2–100+ voters; nominees may be people, teams, or content.
- **Host sees:** Seeds, bracket, vote integrity, match controls, ties, and optional jury score.
- **Active players see privately:** Two-choice ballot and confirmation.
- **Audience sees:** Full bracket, matchup, countdown, winner animation, and next pairing.
- **Round:** Present two nominees, open/lock vote, advance winner.
- **Scoring/winning:** Final survivor wins; owners may earn tournament placement points.
- **Enjoyment:** Knockout structure builds anticipation around almost any subject.
- **Complexity:** Medium.
- **Special requirements:** Bracket, voting, seeding, tie policy, mixed media.

### 3.16 Closest Call

- **Core idea:** A head-to-head estimation duel, expandable into a spectator tournament.
- **Players:** Two active duelists; 2–32 contestants in a bracket; 100+ spectators.
- **Host sees:** Exact answer, locked estimates, duel score, bracket, and adjudication.
- **Active players see privately:** Numeric/range input, optional confidence wager, and lock state.
- **Audience sees:** Question, duelists, estimate reveal, distance to truth, and advancement.
- **Round:** Simultaneous estimates; closest wins the point; exact answer may win immediately.
- **Scoring/winning:** Best of three/five; deterministic tie or sudden-death estimate.
- **Enjoyment:** Gives two-player competition stage presence without network-sensitive reflex tests.
- **Complexity:** Low-medium.
- **Special requirements:** Numeric validation, ranges, brackets, deterministic ties.

### 3.17 Phrase Forge

- **Core idea:** Reconstruct a verse, quote, proverb, definition, process, or sentence from shuffled fragments.
- **Players:** 1–40; best with 2–20. Individual, teams, or cooperative.
- **Host sees:** Progress, hints, and final ordering.
- **Active players see privately:** Draggable word or phrase tiles.
- **Audience sees:** Shuffled fragments, progress bars, and contextualized final phrase.
- **Round:** Order fragments; easier levels use chunks, harder levels use words/distractors.
- **Scoring/winning:** Correct placement, completion speed, no-hint bonus, and streak.
- **Enjoyment:** Mixes memory and reasoning and naturally supports Scripture without requiring it.
- **Complexity:** Medium.
- **Special requirements:** Drag-and-drop, localization-aware tokenization, hints, explanations.

### 3.18 Seek & Show

- **Core idea:** Teams receive safe venue scavenger prompts and submit photo proof.
- **Players:** 4–100; teams of 2–8.
- **Host sees:** Gallery, timestamps, moderation, acceptance, and safety controls.
- **Active players see privately:** Mission, camera/upload, approval status, and next clue.
- **Audience sees:** Approved submissions only, progress, and highlights.
- **Round:** Complete timed missions such as finding a shape or recreating a safe pose.
- **Scoring/winning:** Completion, creativity, speed, and host bonus.
- **Enjoyment:** Adds movement and physical-world interaction.
- **Complexity:** High.
- **Special requirements:** Camera uploads, storage quotas, consent, moderation-before-projection, venue safety.

### 3.19 One Word Chorus

- **Core idea:** Everyone except a guesser submits one-word clues; duplicates cancel, leaving only unique clues for one guess.
- **Players:** 3–30 active; larger rooms rotate teams or watch.
- **Host sees:** Secret word, clues, duplicate/derivative detection, invalidation, and guesser order.
- **Active players see privately:** Clue-givers see secret and submit one word; guesser waits until approved clues appear.
- **Audience sees:** Duplicate-cancellation animation, unique clues, timer, and final guess.
- **Round:** Submit simultaneously, remove duplicates/illegal derivatives, reveal survivors, guess once.
- **Scoring/winning:** Cooperative correct-guess points; difficulty and few-surviving-clue bonuses.
- **Enjoyment:** Players must anticipate one another; duplicate cancellations create tension and laughter.
- **Complexity:** Medium.
- **Special requirements:** Private roles, normalization, derivative detection, moderation, cooperative scoring.

## 4. Group-size analysis

| Setting | Strongest concepts | Best mechanics |
| --- | --- | --- |
| 1–4 | Quizzly, Closest Call, Signal Spectrum, CueCast, Picture Peek, Sequence Sprint, Phrase Forge, Escape Together | Alternating turns, cooperative puzzles, best-of series, private information, shared-device fallback |
| 5–15 | CueCast, Doodle Dash, Bluffline, Signal Spectrum, One Word Chorus, Caption Clash, Story Loom | Everyone can create or perform; short turns; socially coherent teams |
| 16–40 | Quizzly, Doodle Dash, Crowd Compass, Sequence Sprint, Common Thread, Caption Clash, Bracket Bash, Memory Mosaic | Simultaneous phone input, rotating representatives, three to six teams, audience voting |
| 40–100+ | Quizzly, Crowd Compass, Picture Peek, Sound Snap, Bracket Bash, Memory Mosaic, Doodle Dash, Closest Call tournament | One-tap response, one performer with mass guessing, bounded choices, public progress instead of raw submissions |

### Mechanics that scale well

- One-tap voting and bounded multiple choice.
- All-player guessing against one public performance.
- A few stage representatives while everyone predicts or votes.
- Team aggregation with one captain or a fixed eligible roster.
- Local countdowns derived from one server deadline.
- Progressive reveal and batch resolution.
- Short brackets and public response counts.

### Mechanics that become difficult at scale

- Sequential 30–60 second turns for every participant.
- Unmoderated free text or immediate display of every submission.
- Simultaneous photo/audio uploads from the whole room.
- Multi-author collaborative canvases.
- Open voice interaction in poor room acoustics.
- Raw team sums that reward larger rosters.
- Reflex games where network/device variance dominates skill.
- Projecting every answer instead of finalists, clusters, or samples.

For 40–100+, every round should either request one bounded action from everyone or use a small number of representatives while the rest of the room guesses, predicts, or votes.

## 5. Discovery and learning experience

The platform begins at a game-discovery home rather than dropping a host into a quiz list.

Each game card shows title, icon/visual, one-sentence promise, group-size range, typical duration, individual/team/cooperative tags, required capabilities, and available demo packs. Selecting a card opens a detail page containing:

- Plain-language description.
- “How to play” in three to six steps.
- What the host, active player, and audience do.
- Recommended player count, time, and room setup.
- Example round illustrated with static placeholders.
- Accessibility and equipment notes.
- Demo packs grouped as Church/Bible, Child/Family, and General Assembly.
- Host actions: Play a demo, create from template, browse packs, or author content.
- Reserved video area with thumbnail/poster, duration, captions, transcript, and a future video URL—without making video required for launch.

The public catalog may be browsed by guests, but creating or hosting requires an authenticated Quiz Host role.

## 6. Product and brand direction

Recommended umbrella brand: **GatherPlay**.

Brand hierarchy:

```text
GatherPlay
  ├── Quizzly
  ├── CueCast
  ├── Crowd Compass
  ├── Doodle Dash
  └── future games
```

Quizzly remains the established quiz module and is presented as “Quizzly, a GatherPlay game.” Existing package names, QZ DocTypes, and `/quizzly` links remain compatible.

Keep one Frappe app for the foreseeable future. Shared sessions, Redis state, ticker, guest identity, teams, moderation, content, and mixed-game tournaments make separate apps costly and fragile. Strong internal registration boundaries should still allow an independently maintained Frappe app to contribute a game module later.

Split a module into a separate app only for genuinely independent release ownership, licensing, deployment, or heavy optional dependencies—not merely because it is a different game.
