# GatherPlay — a room worth being in

Product and architecture review · 5 September 2026

## Decision

Keep **GatherPlay** as the independent product. Quizzly is its trivia format and the existing technical package name. Promise: **Good company. Great games.** Help a group choose something they understand and can actually play with the devices they have. Optimize for shared attention and a satisfying ten minutes, not the number of games shipped.

This is the first major implementation slice, not a claim that every game is now redesigned.

## Candid current assessment

Reviewed clean baseline `3c526bc`, recent hosting fixes, game additions, guides and shared-branding history; frontend registry, discovery/setup, host/player/screen shells, public/private APIs, manifests, session engine, score ledger, content DocTypes and tests. Agent Plane browser sessions BSR-2026-00948/00949 establish the baseline. Actual Vite listener is 18113 despite its command line saying 8081; backend is 18033 on training.localhost.

Observed in the browser:

- Standalone navigation says **Circle Church**, with Guest and Logout together. Host administration dominates the entry. This hides the independent product and gives guests a nonsensical action.
- Twenty-five alphabetized, visually near-identical cards offer no useful way to choose for time, energy or devices. Most icons repeat. “Everyone's phones” and a big screen are treated as requirements for the entire platform.
- Rich worked guides and real content previews exist, but important decisions and demo starts are buried below repeated explanation. The same voting/prediction setup appears for unrelated formats.
- A real authenticated Crowd Compass family session can be created; a clear PIN/QR lobby and anonymous player joining are valuable foundations.

Source-backed architectural findings:

- A meaningful module contract already separates public/player/host serialization and scoring from orchestration. Redis hot state, persisted rounds and immutable score events deserve retention.
- Twenty-one games share a round engine. Some are sensible variants, but several famous-sounding game promises are reduced to answering a prepared question: Sound Snap has text clues, Bracket Bash has predefined winners, Escape Together has isolated multiple-choice rounds, and One Word Chorus has a complete clue prompt rather than duplicate-cancelled clues. Their current summaries are honest; their names and taxonomy still imply more.
- Backend start requires at least one digital participant for every game. A physical room with only a host cannot play. A participant record is also used as a controller, person and score subject; these concepts need separation.
- Standalone theme storage and automatic CMS branding are directly tied to the church app. The validated same-origin appearance message is a useful boundary; identity inheritance should be explicit.
- One global long-running ticker and polling fallbacks are workable small-deployment foundations, not evidence of tested hundred-person capacity. Control flags can overwrite concurrent host actions; retry keys are not phase-bound in all paths. More games should not be piled on before these contracts are strengthened.

## What changes

| Keep | Refine | Redesign | Retire from prominence | Introduce |
|---|---|---|---|---|
| Anonymous joining; PIN/QR; host ownership; public/private state; content previews; score ledger; CueCast, Crowd Compass, Doodle Dash, Quizzly | Reconnection messaging, lobby readiness, team language, round pacing, accessibility, pack previews | Discovery, independent identity, detail-to-setup flow, no-device participation, cooperative results | The flat 25-game wall; generic game icons; fake tournament/escape expectations; guest admin navigation | Curated collection, device filter, concrete interactive examples, host-only Common Ground, noncompetitive completion and replay |

Existing games and user content stay reachable. “More formats” is a secondary collection with explicit current mechanics. Consolidation is a product roadmap, not destructive data migration.

## Principles

1. The people are the main event. Every round says who does what, what to look at and when to talk.
2. Devices are controllers, not proof that a person belongs. A device-free participant is first-class.
3. Explain by letting someone try. Show one concrete round before asking for setup.
4. Show choices that matter now: devices, group arrangement, pack and pace. Advanced scoring comes later.
5. Respect mixed ages, reading speeds and comfort. Offer seated/verbal alternatives, passing and manual pacing; do not equate speed with ability.
6. Make honest promises. A text-clue quiz is not an audio-identification game. A cooperative finale need not invent a winner.
7. Independent identity, adaptable setting. A church, classroom or company supplies context and packs through an explicit embedding contract.

## Information architecture and journey

**Explore** (curated games → mood/device filters → all formats); **Join** (code → individual or shared-device nickname → ready); authenticated **My sessions** and **Create content**. Hosting starts on a game's explanation, not a second competing catalog.

Discovery → concrete example → choose pack and supported participation → concise room setup → ready check/lobby → practice/first round → short play/reveal/discussion beats → meaningful ending → replay with fresh content or choose a complementary game. Preserve legacy /play/quizzly and embedded links.

In the first slice, Common Ground implements the full cooperative path with the host's device only and an optional public shared screen. Networked formats keep their existing tested live shells while gaining better discovery and explanation. Cross-game rooms and a unified content library remain subsequent work.

## Participation contract

| Arrangement | Current first-slice behavior | Future contract |
|---|---|---|
| Everyone has a phone | Existing private votes/guesses and individual identity | One controller per person, explicit accessible pace |
| One device per team/household | Selected bounded-answer games: join once using a group nickname, agree one answer, one shared score | Controller owns a team ballot; roster and team sizes separate from device count |
| Two parent devices, children without devices | Two collective entries for compatible answer games, or Common Ground without any player devices | Rotating speaker/controller roles without transferring identity |
| Host device only | Common Ground: groups of 2–5 talk locally; host reads or displays prompts; anyone can pass | Offline-capable cached packs and explicit local-only persistence |
| TV/projector | Separate public Common Ground screen; existing game screens | Readability presets, tested remote-control latency, safe late-screen attach |
| Join/leave mid-session | Digital joining currently works only in the lobby; reconnect restores an existing entry. Common Ground allows entering/exiting the physical conversation freely | Explicit spectator, next-round eligibility, frozen round roster, reconnect grace |
| Large room | Parallel small conversations or simultaneous bounded responses; sample a few shares | Capacity budgets per mechanic, aggregated projection, tested 100-controller load |

Shared-controller compatibility does not mean every private-role game supports it. Do not recommend it for a game where a secret would be exposed. Group sizes describe facilitation recommendations, not backend guarantees. Common Ground has no digital roster and does not collect attendee names.

## Taxonomy and portfolio

Primary categories are the desired social activity: **Connect**, **Perform**, **Create**, **Think**, **Compete**. Devices, duration, reading/typing demands, pace, facilitation and audience size are independent facets. Content audience (family, classroom, community, faith, workplace) belongs to packs, not the game's identity.

Launch collection: Common Ground (connect), Crowd Compass (connect/predict), CueCast (perform), Doodle Dash (create), Quizzly (compete/learn), Sequence Sprint (think). Keep remaining formats accessible with honest mechanics. Consolidate grid/line/path/quilt/sudoku into a **Puzzle Table** collection over reusable puzzle packs. Consolidate text-based Sound Snap into trivia until licensed audio and visual equivalents exist. Rebuild Bracket Bash as actual audience progression before promoting it. Defer photo-based Seek & Show until consent, moderation and storage boundaries are designed.

| Recommended concept | Interaction | Suitable group/device arrangement | Value and reason to include |
|---|---|---|---|
| **Common Ground** — implemented | Small groups find shared answers under playful constraints, share one surprise, then remix | 2+ people; best conversations in 2–5-person clusters; host device only, optional display | Low reading burden, no winner/loser, turns strangers into conversation partners; fills the largest access gap |
| **Tiny Adventures** | Teams act out a three-part miniature story using an everyday object; audience chooses the next constraint | 4–30 active, larger audience; host only or one controller/team | Imagination and improvisation; seated alternative; replaces repetitive quiz variants with physical social play |
| **Room Relay** | Each team solves a different clue, then trades information to finish one common mission | 8–60 in teams, larger via duplicate stations; one device/team or printed cards | Genuine interdependence and learning through explanation; eventual successor to isolated Escape Together questions |
| **Two Sides** | Choose a position on a spectrum verbally/by gesture, hear another reason, then predict change | 4–100+; host only with sampled counts or individual controllers | Perspective taking; replay value comes from the group; no forced disclosure or physical movement |

These are curated recommendations, not claims of completed implementations beyond Common Ground.

## Visual direction / key-screen proposal

Warm paper, deep aubergine ink, saturated violet actions, apricot/lime/lilac illustrated game boards, generous editorial headings and compact plain-language metadata. Use friendly abstract pieces rather than culture-specific characters. Illustration should demonstrate the mechanic: a compass, speech bubbles, reordered tiles, a drawing. Ship these as code-native SVG/CSS assets. Respect system theme; tenant tokens apply only when embedded.

Key screens: an editorial Explore page with an illustrated featured game and a device-first chooser; a split detail page with interactive sample on the left and pack/setup on the right; a minimal cooperative room stage with one large prompt, visible progress and no countdown pressure; a completion screen celebrating the conversation and offering replay. The implemented screens and before/after evidence serve as high-fidelity proposals, with remaining journey boundaries explicitly listed here.

## Architecture direction

Retain one app and deepen modules, not one app per game. Add a manifest capability for host-only sessions so zero digital participants is intentional and isolated from digital games. New Common Ground uses the existing authorized session, public serializer and transition engine; it does not create fake participants or expose host commands to the shared screen.

Next: separate **gathering**, **game run**, **participant/person**, **controller**, **team**, **role assignment** and **score subject**. A gathering holds several runs; a controller may represent several people and roles may rotate by round. Add a server-validated supported participation schema per module; client catalog must not infer capabilities from names. Version content snapshots at run creation. Put scoring/facilitation options into game-owned setup definitions. Introduce expected-version/idempotency host commands and phase-bound actions, lease-based ticker ownership, room-specific wakeups and durable recovery snapshots. Derive catalogs/guides/setup from versioned manifests without forcing game mechanics into one template.

Embedding: keep origin/source/version checks; retain a compatibility CMS adapter; add a provider-neutral appearance/context contract later. Standalone uses GatherPlay identity and its own preference key. Future tenant selection must be authorized by server context, never by an arbitrary tenant query string. No external-origin embedding is enabled by this slice.

Content: pack metadata includes language, reading demand, age guidance, sensitive topics, media licensing, accessibility alternatives and publication status. Authors preview all roles before publication. Never project raw free text/uploads before moderation.

## Prioritized delivery

1. **This slice:** independent identity; curated responsive discovery and filters; understandable detail/setup with examples; new host-only Common Ground from setup to replay and shared screen; guest nav/join language; browser evidence and regression checks.
2. **Next:** module-owned setup for all formats; controller/roster separation and true household/team policies; explicit reconnect/late-join/leave states; reusable room across games; content library beyond quiz-only authoring.
3. **Then:** cooperative puzzle collection, real brackets and private-role variants; multi-locale pack delivery; WCAG audit with assistive technology; automated load and impaired-network tests; event operations and moderation.
4. **After proof:** Tiny Adventures and Room Relay; persisted offline room support and cross-tenant content licensing.

Quality gate: verify guest/host authorization, real sessions and shared controllers, no-controller Common Ground, shared-screen recovery, repeat play, unknown/ended rooms, responsive widths, same-origin embed, production build and relevant backend tests. Document observed limits rather than treating a smoke test as capacity or full accessibility certification.
