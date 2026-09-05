# GatherPlay: Amharic release and product decisions

## Shipped in this slice

- English/አማርኛ switch in discovery, hosting, joining, players and shared screens.
- Per-site `GatherPlay Settings → Default language` (`en` or `am`). Explicit visitor choices override the default. Invite URLs carry language, and a chosen language survives navigation and reload.
- Optional Amharic site tagline, introduction and manual-payment instructions. Product names and user content are not machine-translated.
- Locally bundled, OFL-licensed Noto Sans Ethiopic; no third-party font request. Bilingual offline reconnect page.
- Amharic explanations for all 26 registered games. Twenty-five separate Amharic starter packs, plus ten Common Ground conversation prompts from which each session snapshots three.
- Content-language metadata for quiz, crowd, cue, drawing and round-game packs; language-filtered discovery. Existing English and private packs remain intact. `seed_amharic_starters` is additive and skips existing demo keys, including on migration.
- The newer Ethiopian-family Common Ground and Bluffline illustrations are selected on game detail pages. Original images and original worked examples are preserved.

Text inside existing illustrations and videos remains English. Amharic instructions are available as accessible page text. Translating the remaining artwork is a separate production task; it must use versioned assets, never overwrite originals. This is an initial Amharic localization; editorial review should include regional word choices and the longer authoring/help copy. The underlying Frappe Desk and CMS have their own localization systems.

## Language boundaries

The UI locale is browser-level. A pack's language belongs to the content; changing UI language during a game never translates answers or changes the scoring identifiers. Common Ground stores the selected language and sampled prompts in its session snapshot. A reconnect returns those same prompts.

Embedding uses the existing same-origin parent validation. A trusted `cms:appearance` message may include `language: "am"` or `"en"`; an explicit visitor preference takes precedence. No new authentication bypass, cross-origin cookie bridge or permissive message handler was introduced.

The frontend dictionary is `frontend/src/i18n/am.json`; game explanations are `games-am.js`. The server starter content is `quizzly/demo/amharic.py`. Language codes are validated against the explicit allow-list. Adding another locale requires translations, content and font coverage, not just an extra selector option.

## What was already implemented

The preceding access release added per-site branding and theme settings, guest joining, bounded guest hosting and private question creation, member allowances, email-verification gating, PWA installation suggestions, and optional manual payments. Community mode has no payment gate. Paid mode accepts a receipt/reference, grants time-bounded provisional access when optimistic approval is enabled, and lets an administrator approve or reject it. The UI and server enforce the same policy. Payment-provider automation is not implemented.

The site remains in Community mode. Adding a language does not switch on payment or change existing allowances. Open `/app/gatherplay-settings` as a System Manager to configure the site.

## Game-design decision

The existing competitive foundations include timers, private submissions, reveals, scoring, leaderboards and replay. Common Ground intentionally provides a different, cooperative loop: three conversations and three share moments, with passing allowed and no countdown or ranking.

Crowd Compass now has opening/build/finale progression, a higher-value final prediction, optional shareable results cards and a fresh-room replay action. See [the game standards implementation](../game-standards/README.md). Room Quest and progression for other game families remain recommendations; the artwork itself does not imply new gameplay or payment features.

The direction is:

1. Make the loop understandable before hosting, with a concrete example and visible device requirements.
2. Give competitive games clear stakes, suspense before reveal and a satisfying finish. Give cooperative games shared progress and discovery; do not impose failure on conversation games.
3. Focus first on Common Ground, Crowd Compass, CueCast, Doodle Dash, Quiz and Sequence Sprint. Several of the other registered formats currently share simple question/answer mechanics; their names should not promise board-game or escape-room systems that do not exist.
4. Make results worth sharing because they capture a group's funny discovery or creation. Share only with a deliberate user action and participant privacy considered.
5. Improve one complete game loop before expanding the catalog again.

## Artwork task handoff

Requested orchestration model was “GPT 5.6.4, Lite reasoning”, which is not an available model/reasoning combination. Offered supported choices: GPT-5.4-mini with Low reasoning, or GPT-5.6-luna with Low reasoning. Creation of that separate task is pending the user's choice; no substitute has silently been selected.

The task should inspect the actual mechanics, use the two latest Ethiopian-family illustrations as references, and create versioned English and Amharic teaching assets for remaining games. People should be ordinary contemporary Ethiopian families/friends with varied ages and skin tones, wearing everyday clothing. Device ownership, secret information, speaking/acting/drawing and the reveal must be visually accurate. Use a short three-step explanation. Preserve all existing assets. Produce a manifest with outputs and review notes; avoid concurrent application edits.

## Development services

Frontend: `http://127.0.0.1:8081/play/` (Vite).
Frappe backend/Desk: `http://127.0.0.1:18033/app/gatherplay-settings`, site `training.localhost`.
The existing dedicated development backend uses `gatherplay-backend`; Vite uses `gatherplay-web`. Live timers require a worker consuming the bench's long queue. A missing worker was detected during browser QA; `gatherplay-worker` restores that service. Do not mistake successful page loading for a working timer service.

## Verification

Reproducible checks are in `qa/localization/`. Browser evidence and the working-session video are in `evidence/`. Agent Plane inspection: BSR-2026-00998 (Amharic detail page, selector, screenshot, zero console/network errors).

Final validation passed: 7 unit tests, 8 access-policy regression checks, additive seed/language/session integration checks, responsive standalone and keyboard checks, authenticated CMS embedding, private authoring, and real multiplayer plus device-free sessions. All four browser reports contain zero page errors. Production build and Python lint passed. The 76-second `working-session.webm` records the completed session. Seven inventoried test records were removed; public starters and user data were retained.
