# GatherPlay: an open door with clear boundaries

## Product decisions

GatherPlay is the public identity; `quizzly` remains the installed Frappe package. `/play/` is the invitation and introduction, `/play/explore` is the playable collection, `/play/create` is a private question-pack studio, and `/play/access` explains this site's actual allowance. Embedded entry goes straight to the collection and keeps the host site's authenticated session and validated appearance bridge.

Instead of generic dropdowns, participation and pacing use labelled choice cards, duration uses compact radio choices, and packs use a keyboard-accessible picker with descriptive options. The same controls support mouse, touch, keyboard arrows, Home/End, type-ahead, Escape and focus return.

The next meaningful content investment is original group interaction, rather than increasing the existing 25-format count. This release makes Crowd Compass personal: groups can author, save, reopen, revise and host their own private packs of up to 20 questions. Common Ground continues to provide a complete host-only cooperative alternative. More game mechanics remain a deliberate future investment.

## Site defaults

Open **GatherPlay Settings** in Frappe Desk (`/app/gatherplay-settings`, System Manager only). These are database-backed Single DocType settings, local to each Frappe site.

| Setting | Default and intent |
|---|---|
| Mode | Community: no payment UI or payment requirement |
| Guest joining | Enabled; no account needed to join |
| Guest hosting | Two created game sessions per browser trial |
| Guest authoring | One private Crowd Compass pack; later edits do not consume another pack |
| Trial duration | Seven days; a new session counts when its lobby is created |
| Email | Required after the starter allowance; existing Quiz Host/System Manager accounts are trusted by default |
| Verified community members | Unlimited games and packs when monthly limits are zero |
| Paid mode | Opt-in; requires a positive price and payment instructions |
| Paid plan | Configurable name, currency, amount, duration and monthly game/pack quotas |
| Provisional approval | Enabled by default when paid mode is enabled; first receipt per account per calendar month grants three days |
| Installation | Mobile suggestion enabled, dismissible for seven days |

Brand name, tagline, introduction, public logo and accent are configurable. The existing first-party embed bridge continues to supply contextual theme tokens. Standalone preferences remain separate. Fonts and their open-source licenses now ship with the app; public rendering does not depend on Google Fonts.

## Identity and authorization

A guest browser receives a cryptographically random HttpOnly, SameSite=Lax cookie, with Secure enabled under HTTPS. Only its SHA-256 digest is stored. Guest identity is never inferred from Frappe's shared `Guest` username. A small explicit host-action adapter supports the existing GP and legacy quiz flows; it cannot dispatch arbitrary methods. Host ownership is checked on every action. Cross-origin guest mutations are refused.

Creating sessions or packs runs a database-backed allowance check in document lifecycle hooks, including creation through Frappe's document APIs. A row lock makes concurrent quota consumption transactional. Ordinary account holders cannot publish public/demo packs. Public games can use published packs; private packs require ownership or existing authenticated read permission.

Signing in in the same browser claims trial sessions and packs, transfers ownership, and preserves spent trial allowance. The claimed guest cookie no longer grants access. This is not cross-device guest recovery: keep the same browser until sign-in. Monthly quotas use the site's calendar month; guest/unverified trial counters do not reset each month.

Browser trials are deliberately a low-friction invitation, not a fraud-proof identity. Clearing cookies can create another trial. Guest session creation also has a 12-per-hour IP ceiling, and endpoints have request rate limits. Shared networks can hit that ceiling. For public high-volume launches, add deployment-level abuse monitoring and tune an explicit network policy rather than pretending a cookie identifies a person.

Email links are random, hashed in storage, account-bound, valid for 24 hours and single-use. Verification tokens are in the URL fragment rather than the request path. Open the link while signed into the requesting account. Delivery requires the site's outgoing email service and queue worker; tests intercept mail instead of sending it.

## Optional payment workflow

This is a manual payment-request workflow, not a gateway, invoice, tax or accounting system. Administrators must configure the actual payment destination and instructions before enabling Paid mode.

1. A verified account follows the site's payment instructions and enters its payment reference.
2. It uploads a private PNG, JPEG or PDF receipt, limited to 5 MB. Ownership, privacy, signature, existing attachment and duplicate content/reference are checked.
3. The first submission that month receives bounded provisional access when enabled. Later submissions await review; another receipt does not repeatedly reset provisional access.
4. A System Manager opens **GatherPlay Receipt**, inspects the private proof and changes status to Approved or Rejected. Approval sets the configured access expiry; rejection requires a note. Reviewer, time and document changes are recorded.
5. Entitlements are evaluated from receipt status and expiry, so rejection and expiry immediately affect new game/pack creation. Existing sessions can finish. Community access never consults payment receipts.

Receipts are visible to the submitting account through a limited status API and to System Managers in Desk. Account holders cannot grant or edit their own entitlements. Uploads are not publicly listed. File signatures are checked; a production deployment should provide its standard malware scanning and retention policy. Approval must mean someone checked the real payment, not merely that a file was attached.

## PWA and embedding

The manifest is site-branded, with shipped 192px and 512px maskable-compatible icons. A service worker is restricted to `/play/`. It caches immutable public build assets and a generic offline page, never API responses, session HTML, questions, receipts or uploaded files. It does not claim to make live multiplayer work offline.

A supported mobile browser gets a dismissible installation suggestion outside active play. Installation requires a user tap; iOS receives Add to Home Screen instructions. Embedded pages do not prompt installation or create a new service-worker registration. The standalone app is the installation target.

HTTPS is required for deployed service workers; localhost is allowed for development. Actual native installation is browser/platform dependent. See [MDN installability](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable), [installation prompts](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/How_to/Trigger_install_prompt), and [service-worker scope](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Service-Worker-Allowed).

## Operations and migration

Run `bench --site <site> migrate`, then build the frontend with the supported Node runtime. Existing sessions, content and ownership are preserved; new access links are nullable on historical records. No payment mode is enabled by migration. Background services need reloading when backend code changes.

For this development bench, the frontend runs on 8081 (`gatherplay-web` terminal session), the web server on 18033 (`gatherplay-backend`), and the existing realtime service on 19031. Windows forwards 127.0.0.1:8081 to the same WSL port. The web server is running without automatic reload for stable QA; restart its foreground command after backend edits. This change does not provision or clone a site.

Next priorities: deployment-level abuse telemetry, an administrator-friendly plan catalogue only when multiple real plans exist, receipt retention and review operations, provider-neutral external embedding, accessible user testing, localization, and a tested controller/person/team model for larger gatherings.
