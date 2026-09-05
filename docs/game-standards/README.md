# Game standards: a complete Crowd Compass journey

Crowd Compass now builds toward a clearly announced final prediction and finishes with a room story worth sharing. This is a game-specific first implementation, not a claim that all GatherPlay games now have complete progression systems.

## Product decisions

- **Keep:** private voting, room predictions, dramatic reveals, host pacing, team averages and existing score ledger. Common Ground remains cooperative and device-free.
- **Introduce:** opening / build / finale chapters. Normal correct predictions earn 500 points; the final planned round earns 1,000. Match and estimation bonuses stay unchanged. Content remains shuffled, rather than pretending that later questions are inherently harder.
- **Give hosts a choice:** “Build to a finale” is on for new packs with at least three selected rounds. Classic scoring remains available. Short games and blank rooms retain 500-point predictions. Existing stored configurations retain their former rules.
- **Make the stakes stable:** snapshot the initial number of rounds and each round’s reward when voting opens. In finale mode, live host additions become encores after the planned finale, with normal scoring. No mid-vote multiplier changes.
- **End with connection:** a branded results card invites a friend to try reading their own room. The host or participant can save it, or use native sharing where supported. The highest-consensus, untied, scored room response is optional; it requires explicit opt-in in the visible preview. No names, participant tokens or session PINs enter the export.
- **Replay clearly:** the host opens an authorized new room using the same settings and reshuffled pack. Everyone joins its new code. Existing participants are never silently moved and quotas still apply.

## Implementation boundaries

Round rules and scoring live in the Crowd Compass module. The platform continues to own persistence, idempotency, authorization and realtime delivery. Resolved rounds store the public prompt/choices so the ending survives reload and process restarts. Ended snapshots return aggregate recap data to the already-authorized host, participant and PIN-scoped shared screen; there is no public session-sharing endpoint.

A small presentation component shows the round journey across host, player and shared-screen views. A reusable ending component draws the explicitly selected aggregate content into a local PNG. English and Amharic copy and the bundled Ethiopic font are supported. Tenant branding is respected; the standalone product stays independent of the embedding site.

## Further work

Room Quest, progression for other game families, authored difficulty arcs, personal rematches and persistent public result links are not included. Other game models should get their own suitable payoff rather than inheriting Crowd Compass scoring. Late joiners can participate under existing rules, but no catch-up scoring is introduced.

## Verification

See `evidence/live-results.json` and the screenshots/video in `evidence/` for the actual browser run. `qa/game-standards/network.mjs` exercises three isolated guest browsers, authenticated host and projector, three full Amharic rounds, private votes/predictions, reload recovery, exact final totals, optional exports in both languages, fresh replay and a device-free Common Ground regression. The browser harness reads the existing QA password from site configuration without logging it. Cleanup removes only explicitly inventoried QA sessions owned by that account.

`quizzly.tests.test_crowd_progression` checks classic/legacy/short-game behavior, stable finale and encore stakes, prediction-only doubling, stable scoring keys, void reversal, and recap exclusion of ties, voided rounds and private data. Production build and static checks are also recorded below after completion.

### Recorded results

- Eleven rule/regression tests passed, including preservation of team and estimation bonuses in the finale.
- Production Vite build passed (2,206 modules). Existing font-path warnings remain; the bundled font files resolved in the real browser and Amharic PNG exports.
- Agent Plane before/after runs: `BSR-2026-01006`, `BSR-2026-01007`; no console or network errors in the inspected detail page.
- Real multi-browser run passed with no console errors. Three rounds produced exact scores of 2,300 / 2,300 / 2,000, including the 1,000-point finale prediction reward.
- Final visual check passed at 360px and through the authenticated production CMS iframe, including an actual PNG download from inside the iframe. Native OS share-sheet behavior still needs physical-device verification; local PNG downloading is verified.
- Ruff passed for new helpers/tests/API. The existing game file passes with its three pre-existing RUF005/RUF046 findings excluded; this slice does not expand those warnings.

[Before](evidence/before-crowd.png) · [After](evidence/after-crowd.png) · [Final round on a phone](evidence/round-3-player-vote.png) · [Polished mobile ending](evidence/mobile-results-polished-am.png) · [Amharic card](evidence/shared-card-am.png) · [Embedded ending](evidence/embedded-results-am.png) · [One-minute working-session video](evidence/finale-and-replay.webm)

The video records the working session before the final typography and mobile overflow fixes; the polished ending screenshots and downloaded cards show the final visual state. QA fixtures are removed after verification; the recordings contain only QA nicknames and test room codes.
