# GatherPlay Implementation Plan

Status: Proposed phased delivery plan
Current product: Quizzly
Related documents: [Product specification](product-spec.md) · [Platform architecture](platform-architecture.md)

## 1. Delivery outcome

Deliver a game-neutral live-session platform inside the existing `quizzly` Frappe app, preserve current Quizzly behavior and data, add a discoverable game home and plain-language how-to pages, and release new modules through tested vertical slices.

Every implemented module ships with exactly three maintained starter experiences:

1. A church/Bible-context demo.
2. A child/family-context demo.
3. A general assembly demo suitable for roughly 50 participants.

Every demo is playable immediately, marked as demo content, safe to duplicate, and idempotently reseedable.

## 2. Entry experience and game discovery

### 2.1 Routes

```text
/play                              Game catalog/home
/play/games/:game                  Game detail and how-to
/play/games/:game/demos/:demo      Demo detail/preview
/play/join                         Guest join
/play/p/:pin                       Mobile player
/play/s/:session/screen            Public projector
/play/host                         Host dashboard
/play/host/session/:session        Private host console
/play/host/content/:game           Content management
/play/tournament/:tournament       Tournament/bracket
```

Keep current `/quizzly`, `/quizzly/join`, `/quizzly/play`, and host URLs working as aliases until migration telemetry shows they can be retired.

### 2.2 Catalog/home

The first authenticated host page is a responsive game catalog, not a quiz record list. It supports search and filters for group size, duration, individual/team/cooperative, content category, accessibility, and required media.

Each card contains:

- Game name, icon/cover, and one-sentence promise.
- Status: Available, Beta, or Coming Soon.
- Minimum/recommended/maximum group size.
- Typical round and game duration.
- Interaction tags such as Quiz, Acting, Drawing, Voting, Audio, Creative, or Tournament.
- Individual/team/cooperative badges.
- Media/equipment warnings.
- Count of available content packs and demo packs.
- Primary action: Learn & Play.

Unavailable modules may appear as Coming Soon only when that supports roadmap communication; they must not imply a playable session.

### 2.3 Game detail/how-to page

Every module contributes a guide manifest or `GP Game Guide` record with:

- Plain-language description.
- “How to play” in three to six short steps.
- What the host does.
- What the active player sees privately.
- What the room sees.
- Recommended group size, teams, duration, and room setup.
- One illustrated example round.
- Scoring summary and tie behavior.
- Accessibility, safety, media, and network notes.
- Three demo cards: Church/Bible, Child/Family, General Assembly.
- Actions: Play demo, create from template, browse packs, and author content.

### 2.4 Future how-to video

Reserve the design and data contract now, but do not make video a launch dependency:

- `video_url` or provider reference.
- Poster/thumbnail.
- Duration.
- Caption file and language.
- Text transcript.
- Consent/licensing metadata.
- Fallback to the complete text guide.

The page shows an illustration or animation placeholder until a video exists. Autoplay is disabled, and the guide remains fully usable without video or sound.

### 2.5 Discovery data source

Extend `GameManifest` with presentation metadata or pair it with translatable guide files:

```python
GameManifest(
    key="cuecast",
    title="CueCast",
    summary="Act, describe, and race through team prompts.",
    min_players=2,
    recommended_players="6–20",
    max_players=30,
    typical_minutes=20,
    interaction_tags=("acting", "teams", "performance"),
    capabilities=("teams", "private_prompt", "timer"),
    guide_key="cuecast",
)
```

The backend manifest determines availability and capability. Vue loads the matching guide, visuals, and module components by the same stable key.

## 3. Demo content system

### 3.1 Storage and seeding

Suggested layout:

```text
quizzly/demo_data/
  quiz/
    church_bible.json
    child_family.json
    general_assembly.json
  cuecast/
  crowd_compass/
  doodle_dash/
  ...
```

Each file contains stable `demo_key`, schema version, locale, title, description, guide summary, configuration, content items, source/license fields, accessibility text, and expected validation counts.

Seeder behavior:

- Runs after installation for implemented modules, or through an explicit setup action if demo seeding is disabled in site settings.
- Uses stable keys and upserts idempotently; repeated runs do not duplicate packs.
- Sets `is_demo = 1`, `is_editable = 0` on the canonical copy, and offers “Duplicate to customize.”
- Never overwrites a host-created duplicate.
- Supports `seed`, `verify`, `repair`, and `hide` operations.
- Validates every pack through the registered module before commit.
- Uses private Frappe `File` records for unrevealed/licensed media.
- Includes only original, public-domain, properly licensed, or attributed media/text.
- Makes translation/version/source explicit, especially for Scripture.

Example administration command:

```bash
bench --site <site> execute quizzly.demo.seed.seed_all
bench --site <site> execute quizzly.demo.seed.verify_all
```

### 3.2 Minimum demo depth

- Quiz: 10 questions.
- Prompt/guessing games: 24–30 prompts.
- Poll/caption/bluff games: 12–15 rounds.
- Audio/image/memory games: 10–12 licensed media rounds.
- Escape game: 5 stages plus finale.
- Bracket: 8 or 16 nominees.
- Closest Call: 12 duel questions.
- Story game: 10 constraints and at least three branch prompts.
- Seek & Show: 10 safe missions.

Each demo targets 12–20 minutes by default and includes a shorter five-minute preview configuration.

## 4. Per-game how-to and three-demo seed catalog

The titles below are initial product copy; content review may refine individual prompts without changing the three required audience categories.

### 4.1 Quizzly

**Simple how-to:** Join, read each question, tap one answer before time expires, learn from the reveal, and finish with the highest score.

- **Church/Bible — Bible Composed Challenge:** Fifteen two-part questions (Part 1 opener, Part 2 follow-up, double points) on Creation, Exodus, kings, prophets, parables, Jesus' ministry, Acts, and Bible structure.
- **General Knowledge — General Knowledge Composed:** Fifteen two-part questions on world geography, science, inventions, languages, history, and culture.
- **Sports / Football — Football Composed Cup:** Fifteen two-part football questions on the World Cup, clubs, African football, Ethiopia's Walias, and the laws of the game.
- **Funny / Warm-up — Twenty Laughs Live:** Twenty clean joke questions with mischievous wrong answers; the last two are worth double points.
- **Amharic riddles — እንቆቅልሽ · ክፍል 1 / 2 / 3:** Three separate 15-question games, not one 45-question run. Part 1 is classic house riddles, Part 2 nature and coffee culture, Part 3 modern and funny.

### 4.2 CueCast

**Simple how-to:** One teammate privately receives a prompt and acts or describes it without saying the answer; the team guesses as many as possible before time runs out.

- **Church/Bible — Bible Characters in Motion:** Moses parting the sea, David facing Goliath, Noah building, Zacchaeus climbing, the lost sheep, and other respectfully phrased scenes.
- **Child/Family — Family Action Basket:** Brushing teeth, sleepy elephant, making a sandwich, flying a kite, birthday surprise, and playful household actions.
- **General Assembly — Big Room Charades:** Airport security, photographer, traffic jam, public speaker, football referee, missed bus, and celebration prompts.

### 4.3 Doodle Dash

**Simple how-to:** The artist sees a secret word, draws it without letters or numbers, and everyone else types guesses before the timer ends.

- **Church/Bible — Symbols and Stories Sketch-Off:** Ark, dove, sling, scroll, fish, lamp, crown, burning bush, shepherd staff, and empty tomb, with accepted aliases.
- **Child/Family — Family Doodle Box:** Cat, ice cream, bicycle, rainbow, tree house, robot, banana, train, and birthday cake.
- **General Assembly — Sketch the Room:** Microphone, bus, landmark, handshake, projector, coffee break, traffic light, suitcase, and celebration.

### 4.4 Bluffline

**Simple how-to:** Invent a believable false answer, then vote for the answer you think is true; score by finding truth and fooling others.

- **Church/Bible — Curious Bible Context:** Reviewed meanings of lesser-known places, objects, customs, and terms; doctrinally contentious prompts are excluded.
- **Child/Family — Silly Word Museum:** Age-appropriate invented definitions for unusual animal, weather, and household words.
- **General Assembly — Unexpected Facts:** Surprising but sourced facts about places, inventions, language, science, and public life.

### 4.5 Crowd Compass

**Simple how-to:** Choose your own answer, predict which choice the room will select most, then watch the room's result appear.

- **Church/Bible — Our Community Compass:** Morning or evening gathering, which Bible journey to witness, favorite service activity, indoor or outdoor fellowship, and discussion-friendly preferences.
- **Child/Family — This or That Together:** Beach or mountains, pancakes or waffles, cats or dogs, story or movie, super speed or flight.
- **General Assembly — Read the Room 50:** Early bird/night owl, aisle/window, presentation/workshop, tea/coffee, plan/improvise, and event-specific icebreakers.

### 4.6 Sequence Sprint

**Simple how-to:** Drag the cards into the correct order, lock the team's answer, and score for exact positions, correct neighbors, and speed.

- **Church/Bible — Bible Timeline Relay:** Reviewed sequences from creation themes, patriarchs, Exodus, kings, exile, Gospel events, and Acts.
- **Child/Family — Put It in Order:** Morning routine, plant growth, sandwich making, seasons, life cycles, and simple stories.
- **General Assembly — Process and History Race:** Event setup, emergency response basics, inventions, communication history, and common workflows.

### 4.7 Picture Peek

**Simple how-to:** Watch a hidden image become clearer and submit a guess; earlier correct answers earn more points.

- **Church/Bible — Symbols, Places, and Scenes:** Original or licensed illustrations of Bible-associated objects, landscapes, symbols, and architecture.
- **Child/Family — What Is Hiding?:** Animals, toys, fruits, household objects, vehicles, and friendly close-up textures.
- **General Assembly — World in Focus:** Landmarks, common technology, foods, transportation, public objects, and venue details.

### 4.8 Sound Snap

**Simple how-to:** Listen to the short clip, choose or type what made the sound, and use as few replays as possible.

- **Church/Bible — Sounds of the Story:** Original sound effects such as wind, storm, sheep, footsteps, water, crowd, trumpet-like horn, and pages, framed as story clues rather than claimed recordings.
- **Child/Family — Home and Animal Sounds:** Dog, cat, cow, rain, kettle, doorbell, bicycle bell, drum, train, and laughter.
- **General Assembly — Soundscape Challenge:** Airport, keyboard, camera shutter, applause, city crossing, microphone feedback, sports whistle, and office sounds.

### 4.9 Caption Clash

**Simple how-to:** Write a wholesome caption for the picture, wait for approval, vote for a finalist other than your own, and reveal the winner.

- **Church/Bible — Modern Parable Moments:** Respectful original illustrations of generosity, patience, welcome, service, and unexpected neighborliness for positive captions.
- **Child/Family — Family Photo Giggles:** Staged animals, toys, food mishaps, and expressive object scenes with child-safe moderation.
- **General Assembly — Conference Caption Cup:** Original staged images of tangled cables, empty podiums, badge mix-ups, coffee queues, and teamwork moments.

### 4.10 Story Loom

**Simple how-to:** Add a short continuation using the secret constraint; the room or host chooses the next branch until the shared story reaches its ending.

- **Church/Bible — Journey of Courage:** A fictional, non-canonical parable-style journey emphasizing compassion, courage, honesty, service, and reconciliation.
- **Child/Family — The Bedtime Adventure Machine:** Friendly creatures, magical objects, safe choices, silly twists, and a cooperative happy ending.
- **General Assembly — Fifty Voices, One City:** Teams shape a fictional city responding to a surprising festival, problem, and community opportunity.

### 4.11 Signal Spectrum

**Simple how-to:** The clue-giver sees a hidden point between two opposites, gives one clue, and teammates place a marker where they think it belongs.

- **Church/Bible — Journey and Wisdom Scales:** Wilderness–palace, lament–celebration, hidden–visible, individual–community, immediate–patient, with respectful clue guidance.
- **Child/Family — Silly Family Scales:** Tiny–giant, whisper–roar, ordinary–magical, snack–feast, slow–superfast.
- **General Assembly — Know Your Room:** Formal–casual, planned–spontaneous, familiar–surprising, practical–imaginative, quiet–energetic.

### 4.12 Memory Mosaic

**Simple how-to:** Study the picture carefully, wait for it to disappear, then answer questions about what you saw.

- **Church/Bible — Objects and Journeys Memory:** Reviewed original scenes containing lamps, jars, baskets, boats, scrolls, roads, tents, and symbolic objects; avoids speculative claims.
- **Child/Family — Toy Room Memory:** Colorful toy shelves, picnic scenes, animals, shapes, and sequence grids.
- **General Assembly — Auditorium Snapshot:** Seating, signs, equipment, badges, stage objects, and workplace/event scenes.

### 4.13 Common Thread

**Simple how-to:** New clues appear one at a time; submit the connection as soon as you see it, because fewer clues mean more points.

- **Church/Bible — Connected in Scripture:** Reviewed connections among people, places, symbols, journeys, teachings, and book groupings.
- **Child/Family — What Belongs Together?:** Animals, foods, school objects, stories, seasons, and simple word associations.
- **General Assembly — Mixed Connection Challenge:** Countries, inventions, media, science, workplace objects, and event themes.

### 4.14 Escape Together

**Simple how-to:** Solve each team puzzle, request hints only when needed, unlock the next stage, and complete the final mission before other teams.

- **Church/Bible — The Roadside Message:** A respectful fictional mission using route clues, symbols, reviewed verse references, service choices, and an early-community delivery goal.
- **Child/Family — The Lost Toy Workshop:** Color, shape, ordering, picture, and simple code puzzles to restart a friendly toy workshop.
- **General Assembly — Restore the Conference:** Teams recover a fictional event's power, schedule, room code, speaker notes, and final launch sequence.

### 4.15 Bracket Bash

**Simple how-to:** Vote between two nominees in each matchup, watch the winner advance, and continue until one room favorite remains.

- **Church/Bible — Bible Places Journey:** Matchups among significant reviewed locations, with neutral educational summaries rather than ranking spiritual importance.
- **Child/Family — Ultimate Family Snack:** Familiar snack categories with allergy-safe imagery and customizable local choices.
- **General Assembly — Crowd Favorites Cup:** Travel styles, event activities, harmless foods, fictional mascots, and original visual concepts.

### 4.16 Closest Call

**Simple how-to:** Two players estimate the numeric answer at the same time; the closest wins the point and advances in a best-of duel or bracket.

- **Church/Bible — Numbers and Distances:** Carefully sourced numerical questions about book counts, journeys, objects, and historical context; ambiguous chronologies are excluded.
- **Child/Family — How Many and How Far?:** Everyday estimation of jar items, animal size, household distance, time, and simple quantities.
- **General Assembly — Big Number Face-Off:** Geography, science, population ranges, inventions, venue capacity, and estimation-friendly facts.

### 4.17 Phrase Forge

**Simple how-to:** Drag the word or phrase tiles into the correct order and lock the answer before the timer expires.

- **Church/Bible — Scripture Builder:** Properly licensed or public-domain verses with translation attribution, context note, and phrase-sized difficulty variants.
- **Child/Family — Proverbs and Friendly Sayings:** Public-domain sayings, simple instructions, sentence building, and family-friendly maxims.
- **General Assembly — Quotes, Messages, and Missions:** Public-domain quotes, safety messages, event themes, and common process statements.

### 4.18 Seek & Show

**Simple how-to:** Receive a safe mission, find or create the requested item with your team, submit a photo, and wait for host approval before it appears publicly.

- **Church/Bible — Service and Symbols Hunt:** Find non-personal objects representing welcome, light, service, music, learning, and community; no photographs of people are required.
- **Child/Family — Home or Hall Treasure Hunt:** Safe colors, shapes, soft objects, toy arrangements, and team poses where guardian policy permits.
- **General Assembly — Venue Team Quest:** Signs, room features, branded colors, safe object patterns, and staged team creations within defined boundaries.

### 4.19 One Word Chorus

**Simple how-to:** Everyone except the guesser submits one-word clues; duplicate or illegal clues disappear, and the guesser gets one attempt using what remains.

- **Church/Bible — People, Places, and Symbols:** Reviewed Bible people, locations, objects, and themes with derivative/translation alias rules.
- **Child/Family — Animals and Everyday Things:** Familiar objects, foods, animals, jobs, and places with simple vocabulary.
- **General Assembly — One Word, Big Room:** Travel, technology, culture, event life, common experiences, and accessible global concepts.

## 5. Priority modules after Quizzly

Build order: CueCast, Crowd Compass, then Doodle Dash. Together they prove team/private-role play, mass voting, and creative realtime media.

## 6. CueCast MVP

### Scope

- Text prompt decks; Act and Describe modes.
- Two to six teams, one performer per turn.
- 30/60/90 second rounds.
- Host or performer correct/pass controls.
- Automatic rotation, public round count, team scoreboard.
- Prompt never appears in public state.

Restricted words, images, drawing, and speech detection follow later.

### Flow and screens

1. Host selects deck/mode and creates lobby.
2. Guests join; host balances teams.
3. Private performer-ready screen → three-second public countdown.
4. Private prompt controller and public team/timer screen.
5. Correct/pass continues until deadline.
6. Round-review/adjudication screen.
7. Team scoreboard; rotate equal turns; final podium.

Required screens: setup, team lobby, performer ready, prompt controller, non-performer state, public turn, review, scoreboard/podium, deck editor.

### Data, events, scoring

- Shared: Session, Participant, Team, Membership, Round, Action, Score Event.
- Module: Cue Deck and Cue Prompt.
- Events: lobby/team/state updates, `cuecast.performer_ready`, `cuecast.turn_started`, `cuecast.prompt_count_changed`, `cuecast.turn_ended`, scoreboard, end.
- Correct +1; pass zero by default; invalidation uses compensating −1; equal turns; 30-second sudden-death tie.

### Edge cases

- Performer disconnect after seeing prompt; multiple devices; prompt exhaustion; mid-game team change; one-person team; simultaneous correct/pass; double-tap; unsuitable/already-known prompt; late join; projector reconnect secret leak.

### Development slices

1. Team model and role-aware serializers.
2. One team/turn/private prompt end to end.
3. Multi-team rotation, scoring, reconnect, adjudication.
4. Authoring, review, accessibility, animations, and all three demo packs.

### Testing

- Serializer leak tests; action idempotency races; disconnect/reassignment; equal-turn/tie logic; host/projector/performer/multiple-guesser browser test; 100 spectators with rapid controls; socket-loss snapshot fallback.

### Future

Restricted words, picture prompts, remote mode, difficulty-balanced decks, team-captain adjudication, and tournament matches.

## 7. Crowd Compass MVP

### Scope

- Two to four curated choices.
- Personal vote followed by plurality prediction.
- Individual and team-average scoring.
- Hidden partial distribution, participation threshold, animated reveal.
- No free-text choices in MVP.

### Flow and screens

Pack/setup → lobby → public prompt → private personal vote → private prediction → response-progress host view → lock → animated public distribution → private points → leaderboard.

Required screens: pack picker, lobby, host progress/control, personal vote, prediction, public poll, reveal, result card, leaderboard, prompt editor.

### Data, events, scoring

- Module: Crowd Pack and Crowd Prompt; votes/predictions are typed shared Actions.
- Events: `crowd_compass.vote_opened`, action progress, prediction opened, poll closed, distribution revealed, scoreboard.
- Correct plurality prediction +500; optional own-choice/plurality match +100; tied plurality choices count; team result is average eligible score.

### Edge cases

- Insufficient quorum; exact tie; vote submitted but prediction disconnected; late join; unequal teams; skipped sensitive prompt; localization canonical IDs; resync leaking partial distribution.

### Development slices

1. Reuse bounded quiz input for personal vote.
2. Two-stage state and hidden aggregation.
3. Score/team/reconnect/animated reveal.
4. Authoring, analytics, localization, and three demos.

### Testing

- No early result leakage; ties; action uniqueness; retry; averages/nonresponse; mobile browser widths; socket-off fallback; 100 simultaneous votes and predictions; distribution count reconciliation.

### Future

Percentage estimation, rank-choice polls, match-your-team, privacy-safe opt-in comparisons, and host-created live prompts.

## 8. Doodle Dash MVP

### Scope

- One artist, fixed canvas/palette/brush, undo/clear.
- Text prompt with accepted aliases; everyone else guesses.
- Batched canonical strokes, public canvas recovery.
- Speed-scaled guess points, capped artist bonus, host invalidation.
- No multi-artist canvas, photo background, or custom guest prompt in MVP.

### Flow and screens

Deck/setup → lobby → select/rotate artist → private ready/prompt → public countdown → private mobile canvas/public live canvas/private guesses → completion/deadline → answer reveal → scores → next artist.

Required screens: deck setup, lobby, artist ready, canvas, guesser, projector canvas, host moderation, result/scoreboard, prompt/alias editor.

### Data, events, scoring

- Module: Draw Deck, Draw Prompt, aliases; final stroke log is a private File linked to Round; hot strokes remain Redis-only.
- Events: artist selected, round started, bounded stroke batch, canvas reset, correct-count change, resolution.
- HTTP actions: artist ready, drawing batch, clear, guess, host invalidate; each batch has sequence and idempotency key.
- Correct guesser 500–1,000 by server receipt; artist +50 per correct guesser capped 500; invalidated round zero; tie by total correct then median response.

### Edge cases

- Artist disconnect; missing/out-of-order/duplicate strokes; clear racing a batch; written answer; alias/case/plural; unsafe fuzzy match; 100 simultaneous guesses; mid-round projector snapshot; phone rotation; inappropriate/identifying drawing; token in two tabs.

### Development slices

1. Local canvas and normalized coordinates.
2. Reliable artist-to-projector tracer with sequence recovery.
3. Prompts, guesses, aliases, scoring, rotation.
4. Moderation, reconnection, performance, authoring, and three demos.

### Testing

- Stroke sanitization; ordering/duplicate/gap/reset; snapshot reconstruction; alias false positives; secret serialization; touch/orientation browser tests; latency/loss/reconnect; one 10 Hz artist + 100 viewers + simultaneous guesses; assert no DB write per stroke.

### Future

Team relay, brushes/stamps, picture prompts, draw-and-pass telephone, replay animation, and optional assistive answer recognition.

## 9. Phased platform roadmap

### Phase 0 — Baseline and characterization

- Preserve and test existing QZ flows, APIs, routes, scoring, event payloads, and data.
- Add public-secret regression tests.
- Record performance at 1, 4, 15, 40, and 100 players.
- Make existing demo quiz seeding idempotent and add the three Quizzly demos.

### Phase 1 — Platform kernel and discovery tracer

- Add registry, manifest, common state envelope, transitions, score deltas, serializers, and game guides.
- Build `/play` catalog and game detail/how-to pages with video placeholders.
- Add shared GP Session/Participant/Team/Round/Action/Score Event incrementally.
- Run Quizzly through a compatibility adapter; do not migrate historical QZ rows yet.
- Add public projector route separate from host console.

### Phase 2 — CueCast

- Prove teams, private roles, performer rotation, adjudication, and prompt secrecy.
- Ship three complete demo packs.

### Phase 3 — Crowd Compass

- Prove two-stage simultaneous input, mass voting, hidden aggregation, and team normalization.
- Ship three complete demo packs.

### Phase 4 — Doodle Dash

- Prove bounded high-frequency realtime deltas, canvas recovery, creative moderation, and free-text guessing.
- Ship three complete demo packs.

### Phase 5 — Content and safety platform

- Pack library, search, duplicate/customize, review workflow, locale/age/license metadata.
- Retention, moderation queue, reports, and child-focused restrictions.
- Implement lower-complexity modules in vertical slices: Picture Peek, Memory Mosaic, Common Thread, Closest Call, Phrase Forge, Sequence Sprint.
- Every module is unavailable until its guide and all three demos validate.

### Phase 6 — Creative and advanced modules

- Bluffline, Caption Clash, Signal Spectrum, One Word Chorus, Sound Snap, Story Loom.
- Escape Together and Seek & Show only after media/privacy and branching recovery mature.

### Phase 7 — Tournament platform

- Persistent entries/rosters, round robin, seeded knockout, groups/finals, mixed-game schedules, and placement scoring.
- Add Bracket Bash and tournament projector views.

### Phase 8 — Scale and operations

- Redis due-session sorted set, worker checkpoint recovery, connection/event telemetry, payload budgets, phase-aware polling, upload quotas, and 100+ load matrix.
- Session archive, analytics, exports, and support diagnostics.

## 10. Cross-cutting test strategy

Every module passes:

- Manifest and configuration schema tests.
- Pure state-transition and scoring tests.
- Role-aware serializer snapshots with explicit secret-deny assertions.
- API authorization, deadline, rate-limit, idempotency, and concurrent-duplicate tests.
- Redis-loss and worker-restart checkpoint recovery.
- Browser matrix: host, public projector, active private role, ordinary player, reconnecting player.
- Narrow mobile widths, touch, orientation, keyboard, screen reader labels, reduced motion, and color-independent cues.
- Socket disconnect, delayed/out-of-order event, snapshot gap, moderate latency, and packet loss.
- Group-size scenarios at supported boundaries.
- Seed verification: stable keys, exact item counts, licenses/sources, aliases, no duplicate seed, and playable preview.
- Load testing proportional to action profile: answer salvos, votes, guesses, drawing stream, or uploads.

Release gate: a module cannot be marked Available unless its how-to guide, three demo categories, serializers, recovery tests, moderation policy, and supported-size load test all pass.

## 11. Repository independence checklist

Local Git remote naming and hosted fork status are separate concerns.

1. Verify the user-owned remote URL and hosted parent metadata.
2. Rename a user-owned local `upstream` remote to `origin`; add a read-only `upstream` only if intentional future synchronization is desired.
3. Preserve commit history, license, and legally required attribution. Making the repository standalone does not erase upstream license obligations.
4. For a public fork under 1 GB with no child forks, use GitHub's self-service **Settings → General → Danger Zone → Leave fork network** action. Read the warning and type the repository name to confirm. The operation is permanent and cannot be reconnected automatically.
5. Leaving the network preserves Git commit metadata but does not retain fork-associated issues, pull requests, wikis, stars, watchers, comments, child forks, or similar hosted metadata.
6. If the self-service action is unavailable, prefer a new standalone repository or GitHub Support. Do not delete/recreate the existing hosted repository without explicit approval because that is destructive and can lose settings, releases, links, and collaboration history.
7. Commit and validate documentation before pushing.
8. Push the documentation branch to the user-owned repository; merge through the user's normal review path.
