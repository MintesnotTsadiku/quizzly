# Meaningful game depth and explanatory artwork

## Product recommendation

Progression, tension, scoring, failure, polish and a reason to invite a friend form a useful quality bar. They are not a separate game category, and they should not be mandatory mechanics on every format.

- **Progression:** each short session has an opening, rising challenge and a satisfying finish. Prefer better rounds to account-level grinding or daily obligations.
- **Tension:** create curiosity before a reveal, a choice with a consequence, or a shared goal. Timers are optional where accessibility or group confidence requires room to think.
- **Scoring:** reward the skill the game promises. Prediction accuracy fits Crowd Compass; arbitrary points for personal disclosures do not fit Common Ground.
- **Failure:** a missed prediction or unfinished group challenge should lead to a quick recovery or replay. Avoid elimination, public humiliation and long spectator waits.
- **Polish:** readable room screens, clear feedback, smooth pacing, quieter controls during conversation, reliable reconnection and a finish that recognises what happened.
- **Invitation:** give people a specific story or challenge to send. An opt-in result card can say “We predicted only 2 of 5 room favourites. Can your group do better?” Do not share private answers or names by default.

First deepen Crowd Compass with a deliberate round arc and a shareable group result. Keep Common Ground's welcoming conversation mode. Prototype one new cooperative format before expanding the catalog again.

## Proposed new format: Room Quest

An 8–12 minute gathering adventure: five short missions, a collective target of three completions, and two chances to pass or switch a challenge. Missions can mix observation, matching, discussion and optional movement, always with a seated/verbal alternative. A host records outcomes; the room can play without participant devices. Optional household/team controllers can enhance the same experience later.

Start with 4–30 people; larger gatherings use parallel groups and a shared summary instead of serial turns. Everyone stays involved until the finish. Progress is visible, a missed mission creates a setback, and remaining missions allow a comeback. Replay changes the pack. A voluntary “Can your room beat our quest?” card provides a concrete invitation.

This is a proposed game concept, not an implemented game or a promise of event-scale capacity. Validate facilitator effort, participation and replay interest with real groups before building a general mission engine.

## Artwork diagnosis and implemented fix

GameDetail used compact symbolic artwork as its main illustration, while the existing explanatory images were hidden inside a closed full-guide disclosure. Common Ground had no such images. The assets were not missing from disk.

The main detail panel now shows each existing game's actual teaching image, uncropped, with a keyboard-accessible full-size link. The full guide and worked-example dialog remain available. Common Ground receives a new text-free editorial illustration that fits the current cream, peach, lavender, lime and plum palette. Compact vector symbols continue to give catalog cards consistent identities.

The older images use dark photography, neon accents and baked-in text. Keep them available during a staged replacement. Future illustrations should show real participation and devices appropriate to the game, with instructional text in accessible HTML so it can resize and translate. Use this Common Ground illustration as the first visual reference; do not generate 25 replacements before validating the direction.

Asset: `quizzly/public/images/games/common-ground/gathering-v1.png`. Generated with the built-in image tool. No existing image was overwritten. The generation prompt is recorded alongside this document.

Verification: Agent Plane run BSR-2026-00966 inspected the preceding live detail. `qa/access/artwork.mjs` checks visible images, keyboard full-size links, retained worked-example dialog, 390px layout and presence of every registered guide asset. Results and actual page captures are in `evidence/`. No game rules or user data changed in this patch.
