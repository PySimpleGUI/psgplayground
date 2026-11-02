# dev/ - my tools for building this repo, not Playground programs

Nothing in this folder is meant to be run by Playground users. These are the tools I use to build the repo:

| File | What it does |
|---|---|
| `sync_gui.pyw` | One-button window: shows what a sync would do, copies the apps in from their working folders, updates the program tables in `README.md` (the rest of it is hand-written) |
| `sync_from_sources.py` | The script behind it (`--plan` lists, `--readme` only updates the README's tables) |
| `screenshot_helper.pyw` | Takes a screenshot of each program for the Toybox and the README: Next starts the next one still to do, Capture window saves it |
| `draw_icons.py` | Draws the icons that have no PNG of their own (Music, Template) with Pillow |
| `playground_icons.py` | The one icon that exists only as base64 |
| `sync_sources.json` | *Not in the repo* - my local paths, one file per PC |
