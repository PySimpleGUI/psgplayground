# dev/ - my tools for building this repo, not Playground programs

Nothing in this folder is meant to be run by Playground users. These are the tools I use to build the repo:

| File | What it does |
|---|---|
| `sync_gui.pyw` | One-button window: shows what a sync would do, copies the apps in from their working folders, updates the program tables in `README.md` (the rest of it is hand-written) |
| `sync_from_sources.py` | The script behind it (`--plan` lists, `--readme` only updates the README's tables, `--release 1.13` sets the release number) |
| `build.json` | The last build: the version, every file's hash, the apps' versions at the last release and what changed since (see below) |
| `screenshot_helper.pyw` | Takes a screenshot of each program for the Toybox and the README: Next starts the next one still to do, Capture window saves it |
| `draw_icons.py` | Draws the icons that have no PNG of their own (Music, Template) with Pillow |
| `playground_icons.py` | The one icon that exists only as base64 |
| `sync_sources.json` | *Not in the repo* - my local paths, one file per PC |

## The version number

psgplayground's version is the Toybox's `VERSION` in `playground.py` (setup.py reads it from there).  It is **release.build**, for example `1.12.4`:

- **1.12** is the release - the number of the last PyPI release.  Every PyPI release gets the next number (1.12, 1.13, 1.14 - a fix-only release too).  The first number changes only when the Toybox itself breaks old installs (a new PySimpleGUI needed, a new catalog format).
- **.4** is the build - how many syncs have changed something since that release.  Every sync that changes a file in the repo adds one, so a GitHub copy is never called the same as a PyPI copy it differs from, and a Toybox installed from PyPI sees that GitHub is newer.

The sync does the build number by itself: `build.json` remembers every file's hash from the last build (line endings don't count), and it is committed, so every PC agrees.  **Release version...** in the Sync GUI sets the next release number, resets the build to 0 and lists what changed since the previous release - each app's old > new version and the new apps - for the GitHub release notes (kept in `build.json` as `since_last_release`).

So the order is: sync (it builds) > commit + push, as often as you like > **Release version 1.13** > commit + push > build + upload to PyPI.  Sync before every commit, or GitHub gets a changed Toybox with an old number.
