# Desk navigation: Quizzly

Frappe v17 Desk. This file lists what the app ships for the Desk: the apps-screen tile, the dock, the sidebar and the workspace.

## Users

- Hosts run quizzes and games in the play app (`/play`). The Desk is for content and records.
- Users who can read QZ Quiz (Quiz Host, System Manager) see the tile (`quizzly.permissions.has_app_permission`). This matters on sites where Quizzly runs next to another app.

## Decisions

- The tile still opens `/play`. The tile also shows "Open in Desk" (`desk_route`), which opens the Quizzly workspace.
- One module, one sidebar, one workspace, one dock row.
- Order: quizzes and game sessions, then game content, players and teams, access, logs (answers, rounds, score events, player actions).
- The GatherPlay DocTypes (GP, GatherPlay) were not reachable from the Desk before. They are now.

## Exemptions

None. Child tables are not listed.

## Dock

The first row is where the apps-screen tile lands.

| Order | Title | Opens | Icon |
|---|---|---|---|
| 1 | Quizzly | Sidebar `Quizzly` | `zap` |

## Sidebars

### Quizzly

Module `Quizzly`, header icon `zap`.

| Item | Opens | Icon |
|---|---|---|
| Home | Workspace `Quizzly` | `house` |
| Open Play | URL `/play` | `gamepad-2` |
| Quizzes | DocType `QZ Quiz` | `circle-question-mark` |
| Quiz Sessions | DocType `QZ Session` | `presentation` |
| Game Sessions | DocType `GP Session` | `party-popper` |
| Game Packs | DocType `GP Game Pack` | `package` |
| **Game content** (section) | | `layers` |
| &nbsp;&nbsp;Crowd Packs | DocType `GP Crowd Pack` | `users` |
| &nbsp;&nbsp;Cue Decks | DocType `GP Cue Deck` | `layers` |
| &nbsp;&nbsp;Draw Packs | DocType `GP Draw Pack` | `pencil` |
| **Players and teams** (section) | | `users-round` |
| &nbsp;&nbsp;Quiz Participants | DocType `QZ Participant` | `user-round` |
| &nbsp;&nbsp;Game Participants | DocType `GP Participant` | `user` |
| &nbsp;&nbsp;Teams | DocType `GP Team` | `users-round` |
| &nbsp;&nbsp;Team Memberships | DocType `GP Team Membership` | `user-check` |
| **Access** (section) | | `ticket` |
| &nbsp;&nbsp;Access Passes | DocType `GatherPlay Access` | `ticket` |
| &nbsp;&nbsp;Receipts | DocType `GatherPlay Receipt` | `receipt` |
| &nbsp;&nbsp;GatherPlay Settings | DocType `GatherPlay Settings` | `settings` |
| **Logs** (section) | | `scroll-text` |
| &nbsp;&nbsp;Quiz Answers | DocType `QZ Answer` | `list-checks` |
| &nbsp;&nbsp;Game Rounds | DocType `GP Round` | `repeat` |
| &nbsp;&nbsp;Score Events | DocType `GP Score Event` | `trophy` |
| &nbsp;&nbsp;Player Actions | DocType `GP Action` | `mouse-pointer-click` |

## Workspaces

### Quizzly

Icon `zap`. Roles: everyone with module access.

- Shortcuts: Open Play (`gamepad-2`), Quizzes (`circle-question-mark`), Quiz Sessions (`presentation`), Game Sessions (`party-popper`), Game Packs (`package`)
- Card Game content: Game Packs, Crowd Packs, Cue Decks, Draw Packs
- Card Players and teams: Quiz Participants, Game Participants, Teams, Team Memberships
- Card Access: Access Passes, Receipts, GatherPlay Settings

## Checks

- Icons: `ops/bin/check-desk-icons <bench>/apps quizzly` must report 0 problems.
- Coverage: `check-desk-coverage <repo> --exempt docs/desk-navigation.md` must report 0 missing.
  Every non-child DocType, Report and Page of the app must be an item in a Sidebar.
- To change navigation, edit the Sidebar or Workspace on a developer-mode site (it re-exports the file), or edit the JSON. Keep this document in step.
