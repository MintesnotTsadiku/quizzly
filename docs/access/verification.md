# Verification and release evidence

5 September 2026 · training.localhost · frontend 8081, backend 18033

## Passing checks

| Evidence | Result |
|---|---|
| `qa/access/browser.mjs` | 10 checks: guest landing, keyboard picker, real host-only completion, isolated ownership, private authoring, quota denial, PWA registration/offline recovery, 390px layout |
| `qa/access/network.mjs` | 4 checks: authenticated host, three isolated guest browsers, two collective household/team entries, votes and private predictions, reconnect, projector reveal and persisted final results |
| `qa/access/extras.mjs` | 4 checks: mobile install suggestion interaction, legacy guest quiz lobby, same-browser sign-in handoff, persistent private pack editing |
| `qa/access/embedded.mjs` | 2 checks: actual authenticated CMS games iframe and 768px dark theme |
| `qa/access/backend.py` | 8 database policy checks: durable quotas, direct-document enforcement, account claim including month-boundary counters, verification, provisional payment access, rejection, approval, stale-cookie denial |
| Final readiness smoke | Verification link preserved through sign-in; restarted site serves Community configuration; landing refreshed at desktop and 390px |
| Focused Python unit tests | 8 passed: Common Ground mechanics, reveal snapshots and shared-branding provider compatibility |
| Production build | Passed with Node 24; build output included in evidence |
| Ruff / whitespace review | Passed for the new Python modules and QA scripts; `git diff --check` clean |

The final Windows-side localhost request returned HTTP 200 on port 8081.

All 20 final browser checks report zero unexpected console/page errors. Intentional permission denials and offline requests are classified separately. An earlier concurrent run encountered connection resets and one host reload timed out; it is not counted as a pass. The complete isolated rerun passed, including host reload and final results on every player and shared screen.

Agent Plane browser run **BSR-2026-00965** independently opened Common Ground, interacted with the new picker and captured a screenshot, with no console/network errors. The screenshot is copied into this evidence folder. Earlier discovery and before-state evidence are in [the first redesign verification](../redesign/verification.md).

## Visual review

Open [the visual review](review.html) for actual landing, setup, mobile, authoring, access and embedded screenshots and a short working-session video. These are captures of the running application, not static design mockups. The preceding [product direction](../redesign/direction.md) and [before/after review](../redesign/review.html) cover the broader gathering-first redesign, taxonomy and participation model. This release adds configurable access and the next coherent experience slice.

`evidence/working-session.webm` follows a guest through setup, cooperative play, private pack creation and trial limits. It contains no login credentials or real payment details. Browser scripts read the existing QA password into memory and never print or record it. Database payment checks use temporary records, intercept email and roll back; payment mode remains Community on the actual site.

## Practical boundaries

- Three simultaneous controllers were exercised. This is not a 100-player load certification. Shared devices currently represent collective entries; independent people behind a controller and late digital joining remain roadmap work.
- Actual native installation was not completed on a physical iPhone/Android device. Manifest, worker scope, offline fallback and a simulated supported-browser install event were checked. Installation requires a user gesture and deployed HTTPS. The iframe suppresses installation suggestions.
- Paid entitlement transitions were tested against the actual database with isolated policy settings. No real money was transferred and no gateway is implemented. Configure payment instructions and administrator review operations before enabling Paid mode.
- Email tokens were tested without sending mail. Configure the site's outgoing email and queue for real delivery.
- Keyboard, responsive layout and theme states were checked; this is not a full assistive-technology certification.
- Cleanup removes only explicitly inventoried browser fixtures; unidentified early trial records are left to expire rather than deleting user data by title or date. Existing user records and unrelated CMS work are preserved.

See [product and operations](product-and-operations.md) for all defaults, configuration, authorization boundaries, rollout steps and next priorities.
