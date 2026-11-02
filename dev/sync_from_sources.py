"""
sync_from_sources.py - refresh the Playground from the working copies of the apps, then update README.md's program tables from catalog.json.

    python dev/sync_from_sources.py            copy every source listed in sync_sources.json (next to this script), then update README.md's program tables
    python dev/sync_from_sources.py --readme   only update README.md's program tables
    python dev/sync_from_sources.py --plan     list what a sync would do, change nothing

sync_sources.json maps repo paths to the local working copies (one PC's paths, so the file is .gitignored):
    {"Widgets/claude_usage_widget.pyw": "D:/Dropbox/2026_PysimpleGUI/Mikes 2026 Demos/claude_usage_widget.pyw",
     "Programming/snap_regression/": {"from": "D:/.../Snap", "glob": "*.py"}}
Repo paths are relative to the psgplayground package folder unless they start with / (then relative to the repo root).
A file entry copies one file.  A folder entry (key ends with /) copies the files matching glob from that folder, minus any "exclude" patterns.
A path (or a folder entry's "from") may be a list: the first one that exists is used - put the PSG_Work copy first and the old location after it.
Only changed files are written (size + contents compared), so a re-run after editing the originals is quick and git sees only real changes.
README.md is yours: a sync only rewrites the What's here tables between its <!-- PROGRAMS START --> and <!-- PROGRAMS END --> comment lines.
Edit everything else right in README.md - a sync leaves it alone.  No comment lines, no README change (the sync lists it as MISSING).
Before a sync changes README.md it copies it to dev/readme_copies/README.<date_time>.md (the newest 20 are kept; .gitignored).  The START comment
carries a stamp of the tables the sync wrote - edit the tables by hand and the next sync lists README.md as EDITED (the GUI asks before replacing them).

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v1.13 README.md is copied to dev/readme_copies before a sync rewrites it, and the START comment carries a stamp of the tables it wrote:
                  tables edited by hand since then show as EDITED (Mike's Music text sat inside them, where the next sync would have replaced it)
2026-11-02  v1.12 README tables: icons 40 px, screenshots shrunk to fit 240 x 150 with width AND height given (64 px icons and 400 px-wide shots made every
                  row huge); paths use the section's own folder from the catalog (System Tray -> Tray/); a section's "warning" shows as a GitHub warning box
2026-11-01  v1.11 README.md is hand-written now: a sync rewrites only the program tables between the PROGRAMS START / END comments
                  (it used to rebuild the whole file and overwrote Mike's edits).  The README's text moved out of this script into README.md
2026-11-01  v1.10 README: each program's screenshot under its description (psgplayground/screenshots/<file>.png, click for full size) when there is one
2026-11-01  v1.9  Repo renamed PySimpleGUI-Playground -> psgplayground (GitHub link + install command in the README)
2026-10-31  v1.8  README icons: links point at psgplayground/icons/ (broke in v1.2), 64 px above the name in the Program cell (own column got squeezed tiny), file path moved under the description; 'past 10 weeks'
2026-10-31  v1.7  Toybox button pictures are embedded into playground.py as base64 (embed step) instead of written as icon files; stray btn_*.png get removed
2026-10-31  v1.6  README rewritten in Mike's voice (first person, no PR invitation); sections are H3 under What's here
2026-10-31  v1.5  Music/Template icons are drawn by draw_icons.py when the sync runs (no 20 KB of base64 to keep in step)
2026-10-31  v1.4  plan() lists what a sync would do without doing it (the GUI shows it before you press Sync); hand-drawn icons come from playground_icons.py
2026-10-31  v1.3  A source may be a list of paths - the first that exists wins (PSG_Work first, old folders as fallback)
2026-10-31  v1.2  Apps, catalog and icons live inside the psgplayground package; README tells users to pip install the zipball
2026-10-31  v1.1  Lives in dev/ now - a tools/ folder collides with the Tools/ app section on Windows (case-insensitive)
2026-10-30  v1.0  First version: copy sources, make missing icons, rebuild README.md from catalog.json
"""
import base64
import binascii
import datetime
import fnmatch
import glob
import hashlib
import io
import json
import os
import re
import shutil
import struct
import sys

VERSION = '1.13'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(ROOT, 'psgplayground')
CATALOG = os.path.join(PKG, 'catalog.json')
README = os.path.join(ROOT, 'README.md')
SOURCES = os.path.join(DEV, 'sync_sources.json')
ICONS = os.path.join(PKG, 'icons')
GITHUB = 'https://github.com/PySimpleGUI/psgplayground'
README_ICON = 40                                                    # px: the icon above each program's name in the README tables
THUMB_BOX = (240, 150)                                              # px: a screenshot in the README tables is shrunk to fit this (click it for full size)
TABLES_START, TABLES_END = '<!-- PROGRAMS START', '<!-- PROGRAMS END'           # README.md's comment lines: a sync rewrites only what is between them
START_LINE = '<!-- PROGRAMS START: a sync writes everything from here to PROGRAMS END from catalog.json - change the catalog, not these tables  (sync {}) -->'
STAMP = re.compile(r'\(sync ([0-9a-f]{12})\)')                     # in the START line: the fingerprint of the tables the last sync wrote
COPIES = os.path.join(DEV, 'readme_copies')                         # README.md as it was before each sync that changed it (.gitignored)
KEEP_COPIES = 20

from playground_icons import ICONS as EMBEDDED_ICONS      # icons that exist only as base64 (chat search)
try:
    import draw_icons                                       # Music + Template icons, drawn with Pillow when the sync runs
    DRAWN_ICONS = draw_icons.ICONS
except ImportError:                                         # no Pillow
    draw_icons, DRAWN_ICONS = None, {}


def same_file(a, b):
    try:
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        with open(a, 'rb') as fa, open(b, 'rb') as fb:
            return fa.read() == fb.read()
    except OSError:
        return False


def resolve_sources():
    """ sync_sources.json -> a list of items {rel, dst, src, candidates}: one per file to copy (folder entries expanded), src None when nothing was found """
    items = []
    if not os.path.isfile(SOURCES):
        return items
    with open(SOURCES, encoding='utf-8') as f:
        sources = json.load(f)
    for rel, src in sources.items():
        if rel.startswith('_'):
            continue
        dst = os.path.join(ROOT if rel.startswith('/') else PKG, rel.strip('/').replace('/', os.sep) + (os.sep if rel.endswith('/') else ''))
        if rel.endswith('/'):
            folder, pattern, exclude = (src['from'], src.get('glob', '*'), src.get('exclude', [])) if isinstance(src, dict) else (src, '*', [])
            folders = folder if isinstance(folder, list) else [folder]
            folder = next((f for f in folders if os.path.isdir(f)), folders[0])                             # a list = first existing folder wins
            files = sorted(p for p in glob.glob(os.path.join(folder, pattern)) if os.path.isfile(p) and not any(fnmatch.fnmatch(os.path.basename(p), x) for x in exclude))
            if not files:
                items.append({'rel': rel, 'dst': None, 'src': None, 'candidates': [f'{f}{os.sep}{pattern}' for f in folders]})
            for p in files:
                items.append({'rel': rel + os.path.basename(p), 'dst': os.path.join(dst, os.path.basename(p)), 'src': p, 'candidates': [p]})
        else:
            candidates = src if isinstance(src, list) else [src]                                              # a list = first existing file wins
            items.append({'rel': rel, 'dst': dst, 'src': next((c for c in candidates if os.path.isfile(c)), None), 'candidates': candidates})
    return items


def icon_bytes(name, catalog):
    """ PNG bytes for an icon that no working folder supplies: the hand-drawn one from playground_icons.py, else a section-coloured stand-in (needs Pillow) """
    if name in EMBEDDED_ICONS:
        try:
            return base64.b64decode(EMBEDDED_ICONS[name], validate=True), 'hand-drawn icon'
        except (binascii.Error, ValueError):
            return None, 'embedded icon in playground_icons.py is corrupt'
    if name in DRAWN_ICONS:
        return draw_icons.png_bytes(DRAWN_ICONS[name]()), 'hand-drawn icon'
    app = next((a for a in catalog['apps'] if a.get('icon') == name + '.png'), None)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None, f'no icon for {app["name"] if app else name} (pip install pillow for a stand-in)'
    colors = {s['name']: s['color'] for s in catalog['sections']}
    im = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, 61, 61), radius=12, fill=colors.get(app['section'] if app else '', '#444444'))
    initials = ''.join(w[0] for w in (app['name'] if app else name).split()[:2]).upper()
    try:
        font = ImageFont.truetype('arial.ttf', 26)
    except OSError:
        font = ImageFont.load_default()
    d.text((32, 32), initials, fill='#ffffff', font=font, anchor='mm')
    bio = io.BytesIO()
    im.save(bio, format='PNG')
    return bio.getvalue(), 'stand-in icon (initials) - replace it when you have a real one'


def plan(catalog, readme_only=False):
    """ What a sync would do, without doing it.  A list of steps {status, rel, src, note, dst, data}:
        status  new / changed / same / MISSING   for the sources, then   icon  for icons to write,  embed  for the Toybox's button pictures (base64 inside playground.py),
        remove  for a stray file, and   readme  if README.md would change """
    steps = []
    supplied = set()
    if not readme_only:
        for it in resolve_sources():
            if it['src'] is None:
                steps.append({'status': 'MISSING', 'rel': it['rel'], 'src': '  |  '.join(it['candidates']), 'note': 'not found', 'dst': None, 'data': None})
                continue
            supplied.add(os.path.normcase(it['dst']))
            status = 'new' if not os.path.exists(it['dst']) else 'same' if same_file(it['src'], it['dst']) else 'changed'
            steps.append({'status': status, 'rel': it['rel'], 'src': it['src'], 'note': '', 'dst': it['dst'], 'data': None})
        wanted = dict.fromkeys(list(EMBEDDED_ICONS) + [n for n in DRAWN_ICONS if not n.startswith('btn_')] + [a['icon'][:-4] for a in catalog['apps'] if a.get('icon', '').endswith('.png')])
        for name in wanted:
            dst = os.path.join(ICONS, name + '.png')
            if os.path.normcase(dst) in supplied:
                continue                                                                                      # a working folder supplies this one
            data, note = icon_bytes(name, catalog)
            if data is None and os.path.exists(dst):
                continue                                                                                      # can't make a fresh one, but the file is there
            if data is None:
                steps.append({'status': 'MISSING', 'rel': f'icons/{name}.png', 'src': '', 'note': note, 'dst': dst, 'data': None})
            elif not os.path.exists(dst):
                steps.append({'status': 'icon', 'rel': f'icons/{name}.png', 'src': '', 'note': note, 'dst': dst, 'data': data})
            elif (name in EMBEDDED_ICONS or name in DRAWN_ICONS) and open(dst, 'rb').read() != data:
                steps.append({'status': 'icon', 'rel': f'icons/{name}.png', 'src': '', 'note': note + ' (replaces the current file)', 'dst': dst, 'data': data})
        steps += button_steps()
    path = README
    old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
    text, problem = readme(catalog, old)
    if problem:
        steps.append({'status': 'MISSING', 'rel': 'README.md', 'src': '', 'note': problem, 'dst': path, 'data': None})
    elif hand_edited(old):
        steps.append({'status': 'EDITED', 'rel': 'README.md', 'src': 'catalog.json', 'dst': path, 'data': text,
                      'note': 'its program tables were edited by hand - a sync replaces them (a copy goes to dev/readme_copies first); section text belongs in catalog.json, '
                              'anything else below PROGRAMS END'})
    elif text != old:
        steps.append({'status': 'readme', 'rel': 'README.md', 'src': 'catalog.json', 'note': 'program tables updated - the rest stays as you wrote it', 'dst': path, 'data': text})
    return steps


BTN_START, BTN_END = '# --- BUTTON_IMAGES:', '# --- end BUTTON_IMAGES ---'
PLAYGROUND_PY = os.path.join(PKG, 'playground.py')


def button_steps():
    """ The Toybox's button pictures live inside playground.py as base64 (one self-contained file).  A step to rewrite that block when the
        drawings changed, plus one per stray icons/btn_*.png left over from before they were embedded """
    steps = []
    if draw_icons is not None and os.path.isfile(PLAYGROUND_PY):
        with open(PLAYGROUND_PY, encoding='utf-8') as f:
            src = f.read()
        a, b = src.find(BTN_START), src.find(BTN_END)
        if a >= 0 and b > a:
            a = src.index('\n', a) + 1                                                                     # keep the marker line itself
            lines = ['BUTTON_IMAGES = {']
            for name, fn in DRAWN_ICONS.items():
                if name.startswith('btn_'):
                    lines.append(f"    '{name}': b'{base64.b64encode(draw_icons.png_bytes(fn())).decode()}',")
            lines.append('}')
            block = '\n'.join(lines) + '\n'
            if src[a:b] != block:
                steps.append({'status': 'embed', 'rel': 'playground.py', 'src': 'dev/draw_icons.py', 'note': 'button pictures embedded as base64', 'dst': PLAYGROUND_PY, 'data': src[:a] + block + src[b:]})
    for p in sorted(glob.glob(os.path.join(ICONS, 'btn_*.png'))):
        steps.append({'status': 'remove', 'rel': f'icons/{os.path.basename(p)}', 'src': '', 'note': 'no longer used - the pictures are inside playground.py', 'dst': p, 'data': None})
    return steps


def keep_copy(path):
    """ README.md as it is now, copied to dev/readme_copies/README.<date_time>.md before a sync rewrites it - the newest KEEP_COPIES are kept.  Returns the copy """
    os.makedirs(COPIES, exist_ok=True)
    copy = os.path.join(COPIES, f'README.{datetime.datetime.now():%Y%m%d_%H%M%S}.md')
    shutil.copy2(path, copy)
    for old in sorted(glob.glob(os.path.join(COPIES, 'README.*.md')))[:-KEEP_COPIES]:
        os.remove(old)
    return copy


def apply(steps, log):
    """ Do the steps plan() listed """
    for st in steps:
        if st['status'] == 'embed':
            with open(st['dst'], 'w', encoding='utf-8', newline='\n') as f:
                f.write(st['data'])
            log['copied'].append(f'{st["rel"]}  ({st["note"]})')
        elif st['status'] == 'remove':
            os.remove(st['dst'])
            log['copied'].append(f'{st["rel"]}  (removed - {st["note"]})')
        elif st['status'] in ('new', 'changed'):
            os.makedirs(os.path.dirname(st['dst']), exist_ok=True)
            shutil.copy2(st['src'], st['dst'])
            log['copied'].append(st['rel'])
        elif st['status'] == 'icon':
            os.makedirs(os.path.dirname(st['dst']), exist_ok=True)
            with open(st['dst'], 'wb') as f:
                f.write(st['data'])
            log['copied'].append(f'{st["rel"]}  ({st["note"]})')
        elif st['status'] in ('readme', 'EDITED'):
            copy = os.path.basename(keep_copy(st['dst']))
            with open(st['dst'], 'w', encoding='utf-8', newline='\n') as f:
                f.write(st['data'])
            log['copied'].append(f'README.md  (the one before is in dev/readme_copies/{copy})')
            if st['status'] == 'EDITED':
                log['warnings'].append(f'README.md: your hand edits in the program tables were replaced - your version is dev/readme_copies/{copy}')
        elif st['status'] == 'same':
            log['same'] += 1
        elif st['status'] == 'MISSING':
            log['missing'].append(f'{st["rel"]}  <-  {st["src"] or st["note"]}')


def shot_name(app):
    """ the screenshot's file name - <program file name>.png (an app without a file: its name, lower case, _ for spaces) - same rule as the Toybox and screenshot_helper """
    return (os.path.splitext(app['file'])[0] if app.get('file') else app['name'].lower().replace(' ', '_')) + '.png'


def png_size(path):
    """ (width, height) from a PNG's header, or None when it isn't a PNG """
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24]) if head[:8] == b'\x89PNG\r\n\x1a\n' else None


def thumb(shot):
    """ The screenshot as a small picture that opens the full-size one - shrunk to fit THUMB_BOX, never enlarged; width AND height are given, so a tall
        shot can't come out huge.  '' when the program has no screenshot """
    path = os.path.join(PKG, 'screenshots', shot)
    if not os.path.isfile(path):
        return ''
    size = png_size(path)
    f = min(1.0, THUMB_BOX[0] / size[0], THUMB_BOX[1] / size[1]) if size else None
    dims = f'width="{round(size[0] * f)}" height="{round(size[1] * f)}"' if f else f'width="{THUMB_BOX[0]}"'
    return f'<br><a href="psgplayground/screenshots/{shot}"><img src="psgplayground/screenshots/{shot}" {dims}></a>'


def run_line(app, folder):
    """ Where the program is: its section's folder (catalog 'folder', which may differ from the section's name) / its own sub-folder / its file """
    if app.get('link'):
        return f'`pip install {app["pip"]}`' if app.get('pip') else app['link']
    if app.get('folder'):
        folder += '/' + app['folder']
    return f'`{folder}/{app["file"]}`'


def program_tables(catalog):
    """ What's here: a table per catalog section - the only part of README.md a sync writes """
    by_section = {s['name']: [a for a in catalog['apps'] if a['section'] == s['name']] for s in catalog['sections']}
    out = []
    for sec in catalog['sections']:
        apps = by_section[sec['name']]
        out += [f'### {sec["name"]}', '', sec['blurb'], '']
        if sec.get('warning'):
            out += ['> [!WARNING]', f'> {sec["warning"]}', '']                                            # GitHub draws this as a yellow warning box
        if not apps:
            out += ['_Nothing here yet._', '']
            continue
        out += ['| Program | What it does | Needs |', '|---|---|---|']
        for app in apps:
            # the icon goes above the name in the Program cell: in a column of its own GitHub squeezes it to a few pixels, beside the name the text breaks mid-word
            icon = f'<img src="psgplayground/icons/{app["icon"]}" width="{README_ICON}" height="{README_ICON}"><br>' if app.get('icon') else ''
            needs = ', '.join(app.get('requires') or []) or '-'
            if app.get('optional'):
                needs += f' (optional: {", ".join(app["optional"])})'
            plat = '<br>**Windows**' if app.get('platform') == 'win' else ''
            where = run_line(app, sec.get('folder') or sec['name'])                       # under the description: in the narrow Program cell it wrapped under the icon
            out.append(f'| {icon}**{app["name"]}**{plat} | {app["blurb"]}<br>{where}{thumb(shot_name(app))} | {needs} |')
        out.append('')
    return out


def tables_where(text):
    """ (start, line_end, end) in README text: the START comment line runs from start to line_end, the program tables from line_end to end (where the
        END comment line begins).  None when a comment line has gone """
    start = text.find(TABLES_START)
    end = text.find(TABLES_END, start + 1) if start >= 0 else -1
    line_end = text.find('\n', start) if start >= 0 else -1
    return (start, line_end, end) if start >= 0 and end >= 0 and 0 <= line_end < end else None


def tables_stamp(tables):
    """ A short fingerprint of the tables.  Line endings and spaces at the ends of lines don't count, so an editor that changes those isn't 'editing' """
    lines = [line.rstrip() for line in tables.replace('\r\n', '\n').split('\n')]
    return hashlib.sha1('\n'.join(lines).strip('\n').encode('utf-8')).hexdigest()[:12]


def hand_edited(text):
    """ True when the program tables in README text were changed by hand after the last sync wrote them - the START comment carries the stamp of what
        that sync wrote.  A README without a stamp (from sync 1.12 or older) can't tell: False """
    where = tables_where(text) if text else None
    if where is None:
        return False
    start, line_end, end = where
    stamp = STAMP.search(text[start:line_end])
    return stamp is not None and stamp.group(1) != tables_stamp(text[line_end:end])


def readme_edited():
    """ hand_edited() for README.md on disk - the GUI asks before a sync replaces those edits """
    return os.path.isfile(README) and hand_edited(open(README, encoding='utf-8').read())


def readme(catalog, old):
    """ README.md (old) with the program tables between the TABLES_START and TABLES_END lines rewritten - every other line stays as you wrote it.
        The START line gets the new tables' stamp.  Returns (text, None), or (None, what's wrong) when there is no README.md or a comment line has gone """
    if old is None:
        return None, 'no README.md'
    where = tables_where(old)
    if where is None:
        return None, 'its <!-- PROGRAMS START --> / <!-- PROGRAMS END --> comment lines are gone - put them back around the tables (git history has them)'
    start, line_end, end = where
    tables = '\n\n' + '\n'.join(program_tables(catalog)) + '\n'
    return old[:start] + START_LINE.format(tables_stamp(tables)) + tables + old[end:], None


def load_catalog():
    with open(CATALOG, encoding='utf-8') as f:
        return json.load(f)


def main():
    catalog = load_catalog()
    steps = plan(catalog, readme_only='--readme' in sys.argv)
    if not os.path.isfile(SOURCES) and '--readme' not in sys.argv:
        print(f'No {os.path.basename(SOURCES)} - nothing copied (see the docstring for its format)')
    if '--plan' in sys.argv:
        for st in steps:
            print(f'   {st["status"]:8} {st["rel"]}  {st["src"] if st["status"] != "same" else ""}  {st["note"]}')
        return 0
    log = {'copied': [], 'same': 0, 'missing': [], 'warnings': []}
    apply(steps, log)
    print(f'{len(log["copied"])} file(s) written, {log["same"]} unchanged')
    for p in log['copied']:
        print('   wrote   ', p)
    for p in log['missing']:
        print('   MISSING ', p)
    for w in log['warnings']:
        print('   WARNING ', w)
    return 1 if log['missing'] else 0


if __name__ == '__main__':
    sys.exit(main())
