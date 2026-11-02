"""
compare_screenshots_gui.py

GUI version of compare_screenshots.py - pick a BASELINE run and a NEW
run by LABEL, run a pixel-by-pixel regression comparison, and browse
the results.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.3  Runs with the PyPI psgdnd (6.0.4 has no enable()) - drag & drop is skipped there instead of crashing at startup
2026-10-29  v1.2  GitHub issue output: report.md (colored alert box, :emoji: counts, environment, flagged list last) + flagged_screenshots.png
2026-10-29  v1.2  flagged_screenshots.png: Baseline | New side by side, changed area boxed in red, drawn 2x for an 880 px wide comment; Copy Markdown / Copy Image buttons
2026-10-29  v1.1  Label pickers: Baseline/New are read-only dropdowns listing the screenshots_* runs under Root, newest first - no typing; Swap + Refresh List buttons
2026-10-29  v1.1  Release-ready report.html: verdict banner, status counts, Baseline-vs-New environment from each run's manifest.txt, flagged images embedded - one file to post
2026-10-29  v1.1  VERSION constant shown in the header (and in the report footer)

CHANGES from the previous version:
- LABELS instead of folders. You enter ONE root folder (the folder that
  contains the screenshots_<label> subfolders, normally "output") plus
  a Baseline Label and a New Label. Folder names are derived with the
  SAME rule run_snapshots_gui.py / run_all_snapshots.py use:
  <root>/screenshots_<label> (or <root>/screenshots when the label is
  blank). Diffs + reports go to a derived <root>/diffs_<base>_vs_<new>
  folder so different comparisons never overwrite each other.
- A live path preview line shows all three derived folders, flags any
  that don't exist yet, and warns if both labels resolve to the same
  folder. Root, labels, and threshold auto save/restore via "setting".

Usage:
    python compare_screenshots_gui.py

Requires: PySimpleGUI, Pillow
"""
import base64
import csv
import datetime
import html
import io
import os
import platform
import re
import subprocess
import sys
import tempfile
import threading
import psgdnd

import PySimpleGUI as sg

dimmed_repo = {"BACKGROUND": '#22272e', "TEXT": '#c9d1d9', "INPUT": '#2d333b', "TEXT_INPUT": '#dbe2e9', "SCROLL": '#2d333b', "BUTTON": ('#ffffff', '#3d6a9e'), "PROGRESS": ('#5c9bd6', '#2d333b'), "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,}

sg.theme_add_new('DimmedRepo', dimmed_repo)
sg.theme('DimmedRepo')

seafoam_shade = {"BACKGROUND": '#0f1c18', "TEXT": '#c6dcd4', "INPUT": '#1a2e27', "TEXT_INPUT": '#dcece6', "SCROLL": '#1a2e27', "BUTTON": ('#0f1c18', '#6bb39a'), "PROGRESS": ('#6bb39a', '#1a2e27'), "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,}

sg.theme_add_new('SeafoamShade', seafoam_shade)
sg.theme('SeafoamShade')

# ---- Key constants (convention: K_NAME = '-NAME-'; KT_NAME = lambda for repeated/grid keys -> tuple) ----
# Main window
K_ROOT = '-ROOT-'
K_BASELABEL = '-BASELABEL-'
K_NEWLABEL = '-NEWLABEL-'
K_SWAP = '-SWAP-'
K_REFRESH = '-REFRESH-'
K_RUNCOUNT = '-RUNCOUNT-'
K_COPYMD = '-COPYMD-'
K_COPYIMG = '-COPYIMG-'
K_THRESH = '-THRESH-'
K_RECURSIVE = '-RECURSIVE-'
K_PATHS = '-PATHS-'
K_SCAN = '-SCAN-'
K_RUN = '-RUN-'
K_OPENDIFFS = '-OPENDIFFS-'
K_OPENHTML = '-OPENHTML-'
K_BROWSEALL = '-BROWSEALL-'
K_PASSCNT = '-PASSCNT-'
K_FAILCNT = '-FAILCNT-'
K_SCANINFO = '-SCANINFO-'
K_PBAR = '-PBAR-'
K_SUMMARY = '-SUMMARY-'
K_TABLE = '-TABLE-'
K_PV_BASE = '-PV-BASE-'
K_PV_NEW = '-PV-NEW-'
K_PV_DIFF = '-PV-DIFF-'
K_MAGNIFY = '-MAGNIFY-'
K_PREVIEWTEXT = '-PREVIEWTEXT-'
K_PROGRESS = '-PROGRESS-'
K_DONE = '-DONE-'

# Magnify window
K_ZIN = '-ZIN-'
K_ZOUT = '-ZOUT-'
K_ZFIT = '-ZFIT-'
K_Z100 = '-Z100-'
K_ZLABEL = '-ZLABEL-'
K_MAGCLOSE = '-MAGCLOSE-'
K_MAGSCROLL = '-MAGSCROLL-'
K_MSCR_UP = '-MSCR-UP-'
K_MSCR_DN = '-MSCR-DN-'
K_MSCR_LT = '-MSCR-LT-'
K_MSCR_RT = '-MSCR-RT-'
K_MSCR_PGUP = '-MSCR-PGUP-'
K_MSCR_PGDN = '-MSCR-PGDN-'
K_MAGIMG = '-MAGIMG-'
KT_MAGIMG = lambda num: (K_MAGIMG, num)          # one image panel per Baseline/New/Diff

# Browse All window
K_BZIN = '-BZIN-'
K_BZOUT = '-BZOUT-'
K_BSCALE = '-BSCALE-'
K_BINCPASS = '-BINCPASS-'
K_BCLOSE = '-BCLOSE-'
K_BACOL = '-BACOL-'
K_BSCR_UP = '-BSCR-UP-'
K_BSCR_DN = '-BSCR-DN-'
K_BSCR_LT = '-BSCR-LT-'
K_BSCR_RT = '-BSCR-RT-'
K_BSCR_PGUP = '-BSCR-PGUP-'
K_BSCR_PGDN = '-BSCR-PGDN-'
K_BAIMG = '-BAIMG-'
KT_BAIMG = lambda num, panel: (K_BAIMG, num, panel)   # one image per (result row, panel name)


PREVIEW_MAX = (330, 240)

VERSION = '1.3'          # Compare GUI version - bump with every change (see CHANGE LOG); shown in the header and the report footer
NO_LABEL = '(no label)'  # picker entry for the plain <root>/screenshots folder (a run made with a blank label)
EMBED_MAX_FLAGGED = 60   # flagged rows whose images get embedded in report.html - keeps a badly broken run's report a sane size
ENV_KEYS = ('PySimpleGUI', 'Python', 'tkinter Tcl/Tk', 'OS', 'Windows build', 'Run date')    # manifest.txt lines in the report - local paths left out (it gets posted)
FLAGGED_IMAGE_NAME = 'flagged_screenshots.png'
FLAGGED_IMAGE_MAX = 20   # flagged rows drawn into flagged_screenshots.png - ONE image for a GitHub issue, so keep it postable
MD_ICON = {'PASS': ':green_circle:', 'FAIL': ':red_circle:', 'ERROR': ':no_entry:', 'MISSING_IN_NEW': ':yellow_circle:', 'MISSING_IN_BASELINE': ':yellow_circle:'}
MD_NAME = {'PASS': 'PASS', 'FAIL': 'FAIL', 'ERROR': 'ERROR', 'MISSING_IN_NEW': 'Missing in new', 'MISSING_IN_BASELINE': 'New screenshot'}


def sanitize_label(label):
    """Same rule as run_snapshots_gui.py / run_all_snapshots.py so a label always maps to the same folder name."""
    label = (label or '').strip()
    return re.sub(r'[^A-Za-z0-9._-]+', '_', label) if label else ''


def screenshots_dir_for_label(root, label):
    """<root>/screenshots_<label>, or <root>/screenshots when the label is blank - matches the snapshot runners."""
    safe = sanitize_label(label)
    return os.path.join(root, f'screenshots_{safe}' if safe else 'screenshots')


def diffs_dir_for_labels(root, base_label, new_label):
    """Derived diff/report output folder: <root>/diffs_<base>_vs_<new> so each label pairing gets its own folder."""
    return os.path.join(root, f'diffs_{sanitize_label(base_label) or "default"}_vs_{sanitize_label(new_label) or "default"}')


def read_manifest(folder):
    """Parses <folder>/manifest.txt ('Key: value' lines written by run_snapshots_gui.py) into a dict - {} when the run has none."""
    info = {}
    try:
        with open(os.path.join(folder, 'manifest.txt'), encoding='utf-8', errors='replace') as f:
            for line in f:
                key, sep, value = line.partition(':')
                if sep and key.strip() and key.strip() not in info:
                    info[key.strip()] = value.strip()
    except OSError:
        pass
    return info


def list_labels(root):
    """Labels of all run folders (screenshots_<label>, plus plain screenshots as NO_LABEL) under root - newest run first (manifest 'Run date', else folder time)."""
    runs = []
    try:
        entries = [e for e in os.scandir(root) if e.is_dir() and (e.name == 'screenshots' or e.name.startswith('screenshots_'))]
    except OSError:
        return []
    for entry in entries:
        when = read_manifest(entry.path).get('Run date') or datetime.datetime.fromtimestamp(entry.stat().st_mtime).isoformat(timespec='seconds')
        runs.append((when, entry.name[len('screenshots_'):] or NO_LABEL))
    return [label for _when, label in sorted(runs, reverse=True)]


def find_pngs(folder, recursive=True):
    """Returns {filename: full_path} for all .png files (recursive by default)."""
    found = {}
    if recursive:
        for root, _dirs, files in os.walk(folder):
            for fname in files:
                if fname.lower().endswith('.png'):
                    if fname in found:
                        print(f'WARNING: duplicate filename {fname} found in multiple subfolders - using first match')
                        continue
                    found[fname] = os.path.join(root, fname)
    else:
        for fname in os.listdir(folder):
            if fname.lower().endswith('.png'):
                found[fname] = os.path.join(folder, fname)
    return found


def compare_pair(baseline_path, new_path, diff_path):
    """Returns dict with pct_diff/max_delta/bbox/sizes, or an 'error' key."""
    from PIL import Image, ImageChops
    try:
        img1 = Image.open(baseline_path).convert('RGB')
        img2 = Image.open(new_path).convert('RGB')
    except Exception as e:
        return {'error': f'Error opening images: {e}'}

    if img1.size != img2.size:
        return {'error': f'Size mismatch: baseline={img1.size} new={img2.size}',
                'baseline_size': img1.size, 'new_size': img2.size}

    diff = ImageChops.difference(img1, img2)
    bbox = diff.getbbox()
    hist = diff.histogram()
    total_diff = sum(i * v for i, v in enumerate(hist[0:256]))
    total_diff += sum(i * v for i, v in enumerate(hist[256:512]))
    total_diff += sum(i * v for i, v in enumerate(hist[512:768]))
    max_possible = 255 * img1.width * img1.height * 3
    pct_diff = (total_diff / max_possible) * 100 if max_possible else 0.0
    max_delta = max(diff.getextrema(), key=lambda ch: ch[1])[1]

    if bbox:
        os.makedirs(os.path.dirname(diff_path) or '.', exist_ok=True)
        diff_amplified = diff.point(lambda p: min(255, p * 5))
        diff_amplified.save(diff_path)

    return {'pct_diff': pct_diff, 'max_delta': max_delta, 'bbox': bbox,
            'baseline_size': img1.size, 'new_size': img2.size}


REPORT_CSS = '''
body{font:14px/1.45 "Segoe UI",-apple-system,Helvetica,Arial,sans-serif;color:#1f2328;background:#fff;max-width:1500px;margin:20px auto;padding:0 20px}
h1{font-size:24px;margin:0}
h2{font-size:18px;margin:26px 0 8px;padding-bottom:4px;border-bottom:2px solid #d0d7de}
header{border-left:6px solid #8250df;padding:4px 0 4px 14px;margin-bottom:14px}
.vs{font-size:19px;margin-top:4px}.vs b{margin:0 8px;color:#57606a;font-weight:400}
.base{color:#0969da}.new{color:#8250df}.diff{color:#bc4c00}
.verdict{font-size:20px;font-weight:700;padding:12px 16px;border-radius:8px;margin:10px 0}
.verdict.ok{background:#dafbe1;color:#116329;border:1px solid #4ac26b}
.verdict.bad{background:#ffebe9;color:#a40e26;border:1px solid #ff8182}
.chip{display:inline-block;padding:2px 9px;border-radius:12px;font-size:12px;font-weight:700;margin:2px 4px 2px 0;white-space:nowrap}
.chip.PASS{background:#dafbe1;color:#116329}.chip.FAIL{background:#ffebe9;color:#a40e26}.chip.ERROR{background:#a40e26;color:#fff}
.chip.MISSING_IN_NEW,.chip.MISSING_IN_BASELINE{background:#fff8c5;color:#7d4e00}.chip.zero{opacity:.4}
.facts{color:#57606a;font-size:13px;margin:6px 0}
table{border-collapse:collapse}th,td{padding:5px 12px;text-align:left;vertical-align:top;border-bottom:1px solid #d8dee4}
table.env th{white-space:nowrap}table.env tr.chg td{background:#fff8c5}.lbl{font-weight:400;font-size:13px}
.tag{background:#9a6700;color:#fff;border-radius:10px;padding:1px 8px;font-size:12px;font-weight:700}
.card{border:1px solid #d0d7de;border-left:6px solid #cf222e;border-radius:6px;padding:10px 12px;margin:12px 0}
.card.ERROR{border-left-color:#a40e26}.card.MISSING_IN_NEW,.card.MISSING_IN_BASELINE{border-left-color:#d4a72c}
.card b,table.res td:first-child{font-family:Consolas,Menlo,monospace;font-size:13px}.det{color:#57606a;font-size:13px;margin-left:6px}
.imgs{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:8px}
figure{margin:0}figcaption{font-weight:700;font-size:13px;margin-bottom:3px}
figure img{max-width:100%;height:auto;border:1px solid #d0d7de;cursor:zoom-in}.none{color:#6e7781;font-style:italic;padding:16px 0}
.okline{color:#116329;font-weight:700}.note{color:#9a6700;font-weight:700}
details{margin:20px 0}summary{cursor:pointer;font-weight:700;font-size:16px}
footer{margin-top:28px;padding-top:8px;border-top:1px solid #d0d7de;color:#57606a;font-size:12px}
#lb{display:none;position:fixed;inset:0;background:rgba(0,0,0,.88);overflow:auto;z-index:9;cursor:zoom-out}
#lb img{display:block;margin:6px auto 30px;max-width:none;image-rendering:pixelated}#lbcap{color:#fff;font-size:13px;text-align:center;padding-top:10px}
@media print{#lb{display:none!important}.card{break-inside:avoid}}
'''

REPORT_JS = '''
var lb = document.getElementById('lb'), lbimg = document.getElementById('lbimg'), lbcap = document.getElementById('lbcap');
document.querySelectorAll('.imgs img').forEach(function (img) { img.onclick = function () {     // full size, whole-number zoom (max 4x) so pixels stay crisp
    var z = Math.max(1, Math.min(4, Math.floor(Math.min((innerWidth - 60) / img.naturalWidth, (innerHeight - 90) / img.naturalHeight))));
    lbimg.src = img.src; lbimg.style.width = img.naturalWidth * z + 'px';
    lbcap.textContent = img.alt + '  -  ' + img.naturalWidth + ' x ' + img.naturalHeight + ' px, shown ' + z + 'x  -  click or Esc to close';
    lb.style.display = 'block'; }; });
lb.onclick = function () { lb.style.display = 'none'; };
document.addEventListener('keydown', function (e) { if (e.key === 'Escape') lb.style.display = 'none'; });
window.addEventListener('beforeprint', function () { document.querySelectorAll('details').forEach(function (d) { d.open = true; }); });
'''


def write_html_report(path, results, counts, baseline_dir, new_dir, threshold, baseline_count, new_count):
    """
    Writes a SELF-CONTAINED report.html meant to be posted with a release: verdict banner, status counts,
    Baseline-vs-New test environment (from each run's manifest.txt), and every flagged screenshot with its
    Baseline / New / Diff images embedded (base64), so the single file works anywhere. Click an image = full size.
    """
    esc = html.escape
    base_m, new_m = read_manifest(baseline_dir), read_manifest(new_dir)
    run_label = lambda d: os.path.basename(os.path.normpath(d))[len('screenshots_'):] or NO_LABEL
    base_label, new_label = run_label(baseline_dir), run_label(new_dir)
    base_ver, new_ver = base_m.get('PySimpleGUI') or base_label, new_m.get('PySimpleGUI') or new_label
    flagged = [r for r in results if r['status'] != 'PASS']
    total, compared = len(results), sum(counts.get(s, 0) for s in ('PASS', 'FAIL', 'ERROR'))
    chip = lambda status: f'<span class="chip {esc(status)}">{esc(status.replace("_", " "))}</span>'

    def data_uri(p):
        try:
            with open(p, 'rb') as f:
                return 'data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii')
        except (OSError, TypeError):
            return ''

    def env_value(manifest, key):
        value = manifest.get(key, '')
        if key == 'Python' and value:           # '3.13.1 (tags/v3.13.1:0671451, Dec  3 2024, 19:06:28) [MSC v.1942 64 bit (AMD64)]' -> '3.13.1  64 bit (AMD64)'
            bits = re.search(r'\d+ bit \(\w+\)', value)
            value = value.split()[0] + (f'  {bits.group(0)}' if bits else '')
        return value.replace('T', ' ') if key == 'Run date' else value

    env_rows = []
    for key in ENV_KEYS:
        b, n = env_value(base_m, key), env_value(new_m, key)
        if b or n:
            changed = b != n and key != 'Run date'
            tag = '<span class="tag">changed</span>' if changed else ''
            env_rows.append(f'<tr class="{"chg" if changed else ""}"><th>{esc(key.replace("tkinter ", ""))}</th>'
                            f'<td>{esc(b) or "&mdash;"}</td><td>{esc(n) or "&mdash;"}</td><td>{tag}</td></tr>')
    no_manifest = ' <span class="lbl">(no manifest.txt)</span>'

    if not total:
        verdict = '<div class="verdict bad">No screenshots were compared</div>'
    elif not flagged:
        verdict = f'<div class="verdict ok">&#10004; PASS &mdash; all {total} screenshots match the baseline</div>'
    else:
        verdict = f'<div class="verdict bad">&#10006; {len(flagged)} of {total} screenshots flagged for review</div>'
    chips = ' '.join(f'<span class="chip {s}{"" if counts.get(s) else " zero"}">{s.replace("_", " ")} {counts.get(s, 0)}</span>'
                     for s in ('PASS', 'FAIL', 'ERROR', 'MISSING_IN_NEW', 'MISSING_IN_BASELINE'))

    cards = []
    for i, r in enumerate(flagged):
        facts = ' &middot; '.join(esc(str(x)) for x in (r['details'], f'max delta {r["max_delta"]}' if r['max_delta'] != '' else '') if x)
        head = f'<div class="cardhead">{chip(r["status"])} <b>{esc(r["file"])}</b><span class="det">{facts}</span></div>'
        figs = ''
        if i < EMBED_MAX_FLAGGED:
            for cls, caption, p in (('base', 'Baseline', r.get('baseline_path')), ('new', 'New', r.get('new_path')), ('diff', 'Diff (5x amplified)', r.get('diff_path'))):
                uri = data_uri(p)
                none = '(not in this run)' if cls != 'diff' else '(no diff image)'
                body = f'<img src="{uri}" alt="{caption} - {esc(r["file"])}" title="Click for full size">' if uri else f'<div class="none">{none}</div>'
                figs += f'<figure><figcaption class="{cls}">{caption}</figcaption>{body}</figure>'
            figs = f'<div class="imgs">{figs}</div>'
        cards.append(f'<div class="card {esc(r["status"])}">{head}{figs}</div>')
    if len(flagged) > EMBED_MAX_FLAGGED:
        cards.append(f'<p class="note">Images are embedded for the first {EMBED_MAX_FLAGGED} flagged files only - open the rest from the Compare GUI / diffs folder.</p>')
    rows = ''.join(f'<tr><td>{esc(r["file"])}</td><td>{chip(r["status"])}</td><td>{esc(r["details"])}</td><td>{esc(str(r["size"]))}</td><td>{esc(str(r["max_delta"]))}</td></tr>'
                   for r in results)

    title = f'PySimpleGUI {new_ver} vs {base_ver} - Screenshot Regression Report'
    page = ['<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
            f'<title>{esc(title)}</title><style>{REPORT_CSS}</style></head><body>',
            '<header><h1>PySimpleGUI Screenshot Regression Report</h1>',
            f'<div class="vs"><span class="new">New: <strong>{esc(new_ver)}</strong></span><b>vs</b>'
            f'<span class="base">Baseline: <strong>{esc(base_ver)}</strong></span></div></header>',
            verdict,
            f'<div>{chips}</div>',
            f'<div class="facts">Fail threshold: <b>{threshold:g}%</b> mean pixel difference &middot; PNGs: baseline <b>{baseline_count}</b>, new <b>{new_count}</b> &middot; '
            f'pairs compared <b>{compared}</b></div>',
            '<h2>Test environment</h2>',
            f'<table class="env"><tr><th></th><th class="base">Baseline<br><span class="lbl">{esc(base_label)}</span>{"" if base_m else no_manifest}</th>'
            f'<th class="new">New<br><span class="lbl">{esc(new_label)}</span>{"" if new_m else no_manifest}</th><th></th></tr>{"".join(env_rows)}</table>',
            f'<h2>Flagged screenshots ({len(flagged)})</h2>',
            ''.join(cards) or '<p class="okline">None - every screenshot matches the baseline.</p>',
            f'<details><summary>All {total} results</summary><table class="res">'
            f'<tr><th>File</th><th>Status</th><th>Details</th><th>Size</th><th>Max &Delta;</th></tr>{rows}</table></details>',
            f'<footer>FILE: report.html &nbsp;({esc(os.path.basename(os.path.dirname(os.path.abspath(path))))}) &middot; {esc(title)} &middot; '
            f'Generated {datetime.datetime.now():%Y-%m-%d %H:%M} &middot; compare_screenshots_gui.py v{VERSION}</footer>',
            f'<div id="lb" title="Click or Esc to close"><div id="lbcap"></div><img id="lbimg" alt=""></div><script>{REPORT_JS}</script>',
            '</body></html>\n']
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(page))


def write_md_report(path, results, counts, baseline_dir, new_dir, threshold, baseline_count, new_count, has_image):
    """
    Writes report.md for a GitHub issue / release notes: verdict as a colored alert box, :emoji: status counts, test environment,
    all results (collapsed), and the flagged list LAST - so right after pasting it, the cursor sits where flagged_screenshots.png belongs.
    Emoji are GitHub :shortcodes: (plain ASCII), so nothing on the clipboard can mangle them.
    """
    base_m, new_m = read_manifest(baseline_dir), read_manifest(new_dir)
    run_label = lambda d: os.path.basename(os.path.normpath(d))[len('screenshots_'):] or NO_LABEL
    base_label, new_label = run_label(baseline_dir), run_label(new_dir)
    base_ver, new_ver = base_m.get('PySimpleGUI') or base_label, new_m.get('PySimpleGUI') or new_label
    flagged = [r for r in results if r['status'] != 'PASS']
    total, compared = len(results), sum(counts.get(s, 0) for s in ('PASS', 'FAIL', 'ERROR'))
    cell = lambda text: str(text).replace('|', '\\|')

    def env_value(manifest, key):
        value = manifest.get(key, '')
        if key == 'Python' and value:           # '3.12.10 (tags/..., Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]' -> '3.12.10 64 bit (AMD64)'
            bits = re.search(r'\d+ bit \(\w+\)', value)
            value = value.split()[0] + (f' {bits.group(0)}' if bits else '')
        return value.replace('T', ' ')[:16] if key == 'Run date' else ' '.join(value.split())

    lines = [f'## :test_tube: PySimpleGUI {new_ver} — Screenshot Regression Results', '']
    if flagged:
        lines += ['> [!CAUTION]', f'> **{len(flagged)} of {total} screenshots flagged for review** — New **{new_ver}** vs Baseline **{base_ver}**', '']
    else:
        lines += ['> [!TIP]', f'> **:white_check_mark: PASS — all {total} screenshots match the baseline** — New **{new_ver}** vs Baseline **{base_ver}**', '']
    statuses = ('PASS', 'FAIL', 'ERROR', 'MISSING_IN_NEW', 'MISSING_IN_BASELINE')
    lines += ['| ' + ' | '.join(f'{MD_ICON[s]} {MD_NAME[s]}' for s in statuses) + ' |', '|' + ':-:|' * len(statuses),
              '| ' + ' | '.join(f'**{counts[s]}**' if counts.get(s) else '0' for s in statuses) + ' |', '',
              f'Fail threshold **{threshold:g} %** mean pixel difference · PNGs: baseline **{baseline_count}**, new **{new_count}** · pairs compared **{compared}**'
              f' · <sub>compare_screenshots_gui.py v{VERSION} · {datetime.datetime.now():%Y-%m-%d %H:%M}</sub>', '',
              '### Test environment', '',
              f'| | Baseline `{base_label}`{"" if base_m else " _(no manifest.txt)_"} | New `{new_label}`{"" if new_m else " _(no manifest.txt)_"} |', '|---|---|---|']
    changed_any = False
    for key in ENV_KEYS:
        b, n = env_value(base_m, key), env_value(new_m, key)
        if b or n:
            changed = b != n and key != 'Run date'
            changed_any = changed_any or changed
            lines.append(f'| {key.replace("tkinter ", "")} | {cell(b) or "—"} | {f"**{cell(n)}** :small_orange_diamond:" if changed else (cell(n) or "—")} |')
    if changed_any:
        lines += ['', ':small_orange_diamond: = changed since the baseline run']
    lines += ['', f'<details><summary>All {total} results</summary>', '', '| File | Status | Details |', '|---|---|---|']
    lines += [f'| `{cell(r["file"])}` | {MD_ICON[r["status"]]} {MD_NAME[r["status"]]} | {cell(r["details"])} |' for r in results]
    lines += ['', '</details>', '']
    if flagged:
        lines += [f'### Flagged screenshots ({len(flagged)})', '', '| Status | File | Details |', '|---|---|---|']
        for r in flagged:
            details = r['details'] + (f' · max Δ {r["max_delta"]}' if r['max_delta'] != '' else '')
            lines.append(f'| {MD_ICON[r["status"]]} **{MD_NAME[r["status"]]}** | `{cell(r["file"])}` | {cell(details)} |')
        lines.append('')
        if has_image and len(flagged) > FLAGGED_IMAGE_MAX:
            lines += [f'_The image shows the first {FLAGGED_IMAGE_MAX} flagged screenshots - the full set is in report.html._', '']
        if has_image:
            lines += [f'<!-- paste (Ctrl+V) or drag {FLAGGED_IMAGE_NAME} here -->', '']
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def write_flagged_image(path, results, title):
    """
    Draws the flagged rows into ONE png for a GitHub issue: Baseline | New side by side, the changed area boxed in red on both.
    Drawn at 2x for an 880 px wide comment (crisp on hi-dpi screens). Screenshots are never enlarged - pixel-exact when they fit.
    Returns True when written; when nothing is flagged it removes a stale image from an earlier run and returns False.
    """
    from PIL import Image, ImageDraw, ImageFont
    flagged = [r for r in results if r['status'] != 'PASS']
    if not flagged:
        if os.path.exists(path):
            os.remove(path)
        return False

    S = 2                                                                   # canvas scale: GitHub shows it 880 px wide
    W, PAD, GAP, INNER, BAR = 880 * S, 12 * S, 12 * S, 12 * S, 6 * S
    col_w = (W - 2 * PAD - BAR - 2 * INNER - GAP) // 2
    TXT, GREY, BORDER, RED = '#1f2328', '#57606a', '#d0d7de', '#cf222e'
    CHIP = {'FAIL': ('#ffebe9', '#a40e26'), 'ERROR': ('#a40e26', '#ffffff'), 'MISSING_IN_NEW': ('#fff8c5', '#7d4e00'), 'MISSING_IN_BASELINE': ('#fff8c5', '#7d4e00')}
    BAR_COLOR = {'FAIL': '#cf222e', 'ERROR': '#a40e26', 'MISSING_IN_NEW': '#d4a72c', 'MISSING_IN_BASELINE': '#d4a72c'}

    def font(names, size):
        for name in names:
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                pass
        return ImageFont.load_default(size)

    f_text, f_bold = font(('segoeui.ttf', 'DejaVuSans.ttf'), 13 * S), font(('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), 13 * S)
    f_chip, f_mono = font(('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), 12 * S), font(('consolab.ttf', 'DejaVuSansMono-Bold.ttf'), 13 * S)
    f_ital, f_foot = font(('segoeuii.ttf', 'DejaVuSans-Oblique.ttf'), 13 * S), font(('segoeui.ttf', 'DejaVuSans.ttf'), 12 * S)
    line_h = 22 * S
    measure = ImageDraw.Draw(Image.new('RGB', (1, 1)))

    def fit(text, fnt, width):
        if measure.textlength(text, font=fnt) <= width:
            return text
        while text and measure.textlength(text + '…', font=fnt) > width:
            text = text[:-1]
        return text + '…'

    cards = []
    for r in flagged[:FLAGGED_IMAGE_MAX]:
        shots = [Image.open(p).convert('RGB') if p and os.path.exists(p) else None for p in (r.get('baseline_path'), r.get('new_path'))]
        box = None
        if r['status'] == 'FAIL' and r.get('diff_path') and os.path.exists(r['diff_path']):
            with Image.open(r['diff_path']) as d:
                box = d.getbbox()                                          # where the pixels differ
        widest = max(im.width for im in shots if im)
        scale = min(1.0, col_w / widest)                                    # same scale on both sides so the red boxes line up
        for i, im in enumerate(shots):
            if im is None:
                continue
            if scale < 1:
                im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
            if box:
                m = 4 * S
                x0, y0, x1, y1 = (round(v * scale) for v in box)
                ImageDraw.Draw(im).rectangle((max(0, x0 - m), max(0, y0 - m), min(im.width - 1, x1 + m), min(im.height - 1, y1 + m)), outline=RED, width=2 * S)
            shots[i] = im
        body_h = max([im.height for im in shots if im] + [line_h])
        card_h = INNER + line_h + 6 * S + line_h + body_h + INNER
        card = Image.new('RGB', (W - 2 * PAD, card_h), 'white')
        dr = ImageDraw.Draw(card)
        dr.rounded_rectangle((0, 0, card.width - 1, card_h - 1), radius=6 * S, outline=BORDER, width=S)
        dr.rectangle((0, 0, BAR - 1, card_h - 1), fill=BAR_COLOR[r['status']])
        x, y = BAR + INNER, INNER
        label = r['status'].replace('_', ' ')
        chip_w = round(dr.textlength(label, font=f_chip)) + 18 * S
        bg, fg = CHIP[r['status']]
        dr.rounded_rectangle((x, y, x + chip_w, y + line_h), radius=line_h // 2, fill=bg)
        dr.text((x + chip_w // 2, y + line_h // 2), label, font=f_chip, fill=fg, anchor='mm')
        x += chip_w + 8 * S
        dr.text((x, y + line_h // 2), r['file'], font=f_mono, fill=TXT, anchor='lm')
        x += round(dr.textlength(r['file'], font=f_mono)) + 10 * S
        details = r['details'] + (f' · max Δ {r["max_delta"]}' if r['max_delta'] != '' else '')
        dr.text((x, y + line_h // 2), fit(details, f_text, card.width - INNER - x), font=f_text, fill=GREY, anchor='lm')
        y += line_h + 6 * S
        for i, (caption, color, missing) in enumerate((('Baseline', '#0969da', '(not in the baseline run)'), ('New', '#8250df', '(not in the new run)'))):
            cx = BAR + INNER + i * (col_w + GAP)
            dr.text((cx, y), caption, font=f_bold, fill=color)
            if i == 1 and box:
                dr.text((cx + dr.textlength(caption + '  ', font=f_bold), y), '(red box = changed area)', font=f_text, fill=GREY)
            if shots[i] is None:
                dr.text((cx, y + line_h + 6 * S), missing, font=f_ital, fill='#6e7781')
            else:
                card.paste(shots[i], (cx, y + line_h))
                dr.rectangle((cx - 1, y + line_h - 1, cx + shots[i].width, y + line_h + shots[i].height), outline=BORDER, width=1)
        cards.append(card)

    notes = [f'+ {len(flagged) - FLAGGED_IMAGE_MAX} more flagged screenshots - see report.html'] if len(flagged) > FLAGGED_IMAGE_MAX else []
    folder = os.path.basename(os.path.dirname(os.path.abspath(path)))
    footer = [f'FILE: {os.path.basename(path)}  ({folder})', f'{title}  ·  Generated {datetime.datetime.now():%Y-%m-%d %H:%M}  ·  compare_screenshots_gui.py v{VERSION}']
    height = PAD + sum(c.height + GAP for c in cards) + len(notes) * line_h + 10 * S + len(footer) * 18 * S + PAD
    canvas = Image.new('RGB', (W, height), 'white')
    dr = ImageDraw.Draw(canvas)
    y = PAD
    for c in cards:
        canvas.paste(c, (PAD, y))
        y += c.height + GAP
    for note in notes:
        dr.text((PAD, y), note, font=f_bold, fill='#9a6700')
        y += line_h
    dr.line((PAD, y, W - PAD, y), fill=BORDER, width=S)
    y += 8 * S
    for text in footer:
        dr.text((PAD, y), fit(text, f_foot, W - 2 * PAD), font=f_foot, fill=GREY)
        y += 18 * S
    canvas.save(path, optimize=True)
    return True


def copy_png_to_clipboard(png_path):
    """Puts the png on the Windows clipboard (DIB + PNG formats) so Ctrl+V in a GitHub comment uploads it. Returns '' or an error message."""
    try:
        import win32clipboard
        from PIL import Image
        bmp = io.BytesIO()
        with Image.open(png_path) as im:
            im.convert('RGB').save(bmp, 'BMP')
        with open(png_path, 'rb') as f:
            png = f.read()
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp.getvalue()[14:])      # BMP minus its 14-byte file header = DIB
            win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat('PNG'), png)
        finally:
            win32clipboard.CloseClipboard()
        return ''
    except Exception as e:
        return f'{type(e).__name__}: {e}'


def run_comparison(baseline_dir, new_dir, out_dir, threshold, recursive, window):
    """Runs the full comparison and sends progress/done events back to the GUI."""
    baseline_map = find_pngs(baseline_dir, recursive=recursive)
    new_map = find_pngs(new_dir, recursive=recursive)

    baseline_files = set(baseline_map.keys())
    new_files = set(new_map.keys())

    only_baseline = baseline_files - new_files
    only_new = new_files - baseline_files
    common = baseline_files & new_files

    results = []
    total = len(common) + len(only_baseline) + len(only_new)
    done = 0

    for fname in sorted(common):
        diff_path = os.path.join(out_dir, fname)
        res = compare_pair(baseline_map[fname], new_map[fname], diff_path)
        base = {'file': fname, 'baseline_path': baseline_map[fname], 'new_path': new_map[fname]}
        if 'error' in res:
            results.append({**base, 'status': 'ERROR', 'details': res['error'],
                            'size': f'{res.get("baseline_size", "")}/{res.get("new_size", "")}',
                            'max_delta': '', 'diff_path': None})
        else:
            status = 'FAIL' if res['pct_diff'] > threshold else 'PASS'
            results.append({**base, 'status': status,
                            'details': f'{res["pct_diff"]:.4f}% pixel difference',
                            'size': f'{res["baseline_size"][0]}x{res["baseline_size"][1]}',
                            'max_delta': res['max_delta'],
                            'diff_path': diff_path if status == 'FAIL' else None})
        done += 1
        window.write_event_value(K_PROGRESS, (done, max(total, 1)))

    for fname in sorted(only_baseline):
        results.append({'file': fname, 'status': 'MISSING_IN_NEW', 'details': 'Exists in baseline but not in new',
                        'size': '', 'max_delta': '', 'diff_path': None,
                        'baseline_path': baseline_map[fname], 'new_path': None})
        done += 1
        window.write_event_value(K_PROGRESS, (done, max(total, 1)))

    for fname in sorted(only_new):
        results.append({'file': fname, 'status': 'MISSING_IN_BASELINE', 'details': 'Exists in new but not in baseline',
                        'size': '', 'max_delta': '', 'diff_path': None,
                        'baseline_path': None, 'new_path': new_map[fname]})
        done += 1
        window.write_event_value(K_PROGRESS, (done, max(total, 1)))

    counts = {}
    for r in results:
        counts[r['status']] = counts.get(r['status'], 0) + 1

    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, 'report.csv')
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'status', 'details', 'size', 'max_pixel_delta'])
        for r in results:
            writer.writerow([r['file'], r['status'], r['details'], r['size'], r['max_delta']])

    html_path = os.path.join(out_dir, 'report.html')
    write_html_report(html_path, results, counts, baseline_dir, new_dir, threshold, len(baseline_files), len(new_files))
    try:                                            # GitHub issue output - a problem here must never cost the comparison itself
        title = f'PySimpleGUI {read_manifest(new_dir).get("PySimpleGUI", "?")} vs {read_manifest(baseline_dir).get("PySimpleGUI", "?")} - flagged screenshots'
        has_image = write_flagged_image(os.path.join(out_dir, FLAGGED_IMAGE_NAME), results, title)
    except Exception as e:
        print(f'{FLAGGED_IMAGE_NAME} not written: {e}')
        has_image = False
    try:
        write_md_report(os.path.join(out_dir, 'report.md'), results, counts, baseline_dir, new_dir, threshold, len(baseline_files), len(new_files), has_image)
    except Exception as e:
        print(f'report.md not written: {e}')

    scan_info = {'baseline_count': len(baseline_files), 'new_count': len(new_files)}
    window.write_event_value(K_DONE, (results, counts, report_path, html_path, scan_info))


STATUS_COLORS = {
    'PASS': ('black', '#d4f7d4'),
    'FAIL': ('black', '#f7d4d4'),
    'ERROR': ('white', '#a00000'),
    'MISSING_IN_NEW': ('black', '#f7ecd4'),
    'MISSING_IN_BASELINE': ('black', '#f7ecd4'),
}


def open_in_file_manager(path):
    try:
        system = platform.system()
        if system == 'Windows':
            os.startfile(path)
        elif system == 'Darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])
    except Exception as e:
        sg.popup_error(f'Could not open:\n{e}')


def make_preview_file(image_path, max_size=PREVIEW_MAX):
    """Creates a resized temp copy of image_path for preview display."""
    from PIL import Image
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size)
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(tmp.name)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f'Preview error: {e}')
        return None


def make_scaled_file(image_path, scale):
    """Creates a temp copy of image_path resized by `scale`. Uses NEAREST
    when enlarging so individual pixels stay crisp for diff inspection."""
    from PIL import Image
    try:
        img = Image.open(image_path)
        new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
        resample = Image.NEAREST if scale >= 1.0 else Image.LANCZOS
        img = img.resize(new_size, resample)
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(tmp.name)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f'Magnify scale error: {e}')
        return None


MAG_MAX_WINDOW = (3000, 1700)   # hard ceiling; also clamped to the actual screen
MAG_SCALE_LIMITS = (0.1, 8.0)
RESIZE_DEBUG = False             # print [rescale_*] window-fit debug lines for both viewer windows


def show_magnify_window(result):
    """
    Opens a large window (up to 3000x1700, clamped to the screen) showing
    the selected row's BASELINE | NEW | DIFF images enlarged side by side.
    All panels share ONE scale factor so they stay directly comparable.
    Zoom In/Out (x1.5), Fit, and 100% controls re-render at the new scale;
    the image row lives in a both-axis scrollable column so any zoom level
    remains navigable. Enlargement uses NEAREST resampling - pixels stay
    crisp, which is what you want when hunting a 1-2 pixel regression.

    rescale_magnify() also explicitly resizes the WINDOW to fit the zoomed
    content (clamped to win_w/win_h) and prints debug info so we can see
    what size it computed vs what the window actually became.
    """
    from PIL import Image

    panels = [(label, path) for label, path in
              (('Baseline', result.get('baseline_path')),
               ('New', result.get('new_path')),
               ('Diff (5x amplified)', result.get('diff_path')))
              if path and os.path.exists(path)]
    if not panels:
        sg.popup_error('No images available for this row (missing files on both sides?).')
        return

    sizes = []
    for _label, path in panels:
        try:
            with Image.open(path) as im:
                sizes.append(im.size)
        except Exception as e:
            sg.popup_error(f'Could not open {path}:\n{e}')
            return

    screen_w, screen_h = sg.Window.get_screen_size()
    win_w = min(MAG_MAX_WINDOW[0], screen_w - 40)
    win_h = min(MAG_MAX_WINDOW[1], screen_h - 80)
    n = len(panels)
    pane_w = (win_w - 60 * n) // n          # room for padding + scrollbar
    pane_h = win_h - 170                    # room for header, buttons, labels

    def fit_scale():
        s = min(min(pane_w / w, pane_h / h) for w, h in sizes)
        return max(MAG_SCALE_LIMITS[0], min(MAG_SCALE_LIMITS[1], s))

    scale = fit_scale()
    temp_files = []

    def render(current_scale):
        files = []
        for _label, path in panels:
            f = make_scaled_file(path, current_scale)
            if f:
                temp_files.append(f)
            files.append(f)
        return files

    image_cols = []
    initial_files = render(scale)
    for i, ((label, _path), f) in enumerate(zip(panels, initial_files)):
        image_cols.append(sg.Column([
            [sg.Text(label, font=('Helvetica', 11, 'bold'))],
            [sg.Image(filename=f or '', key=KT_MAGIMG(i), expand_x=True, expand_y=True)],], vertical_alignment='top'))

    orig_w, orig_h = sizes[0]
    layout = [
        [sg.Text(f"{result['file']}  -  {result['status']}  -  {result['details']}  (original {orig_w}x{orig_h})",
                 font=('Helvetica', 11, 'bold'))],
        [sg.Button('Zoom In (x1.5)', key=K_ZIN), sg.Button('Zoom Out', key=K_ZOUT),
         sg.Button('Fit', key=K_ZFIT), sg.Button('100%', key=K_Z100),
         sg.Text('', key=K_ZLABEL, font=('Helvetica', 10)),
         sg.Push(), sg.Button('Close', key=K_MAGCLOSE)],
        [sg.Text('Keys:  + / -  zoom      F or Home  fit      1  100%      arrows  scroll      PgUp / PgDn  page      Esc  close', font=('Helvetica', 8))],
        [sg.Column([image_cols], scrollable=True, expand_x=True, expand_y=True, key=K_MAGSCROLL)],
    ]

    mag = sg.Window(f'Magnified: {result["file"]}', layout, finalize=True, resizable=True, modal=True, keep_on_top=False)
    mag[K_ZLABEL].update(f'scale: {scale:.2f}x')

    # Keyboard navigation: +/= zoom in, - zoom out, F/Home fit, 1 = 100%, arrows/PgUp/PgDn scroll, Esc close
    for keysym, evt in (('<Key-plus>', K_ZIN), ('<Key-equal>', K_ZIN), ('<KP_Add>', K_ZIN), ('<Key-minus>', K_ZOUT), ('<KP_Subtract>', K_ZOUT),
                        ('<Key-f>', K_ZFIT), ('<Key-F>', K_ZFIT), ('<Home>', K_ZFIT), ('<Key-1>', K_Z100), ('<Escape>', K_MAGCLOSE),
                        ('<Up>', K_MSCR_UP), ('<Down>', K_MSCR_DN), ('<Left>', K_MSCR_LT), ('<Right>', K_MSCR_RT), ('<Prior>', K_MSCR_PGUP), ('<Next>', K_MSCR_PGDN)):
        mag.bind(keysym, evt)

    def scroll_mag(dx=0, dy=0, pages=0):
        canvas = mag[K_MAGSCROLL].Widget.canvas
        if pages:
            canvas.yview_scroll(pages, 'pages')
        if dy:
            canvas.yview_scroll(dy, 'units')
        if dx:
            canvas.xview_scroll(dx, 'units')

    def rescale_magnify(new_scale):
        """MAGNIFY window zoom: re-render images at new_scale, then resize the window to fit (clamped), with debug prints."""
        nonlocal scale
        scale = max(MAG_SCALE_LIMITS[0], min(MAG_SCALE_LIMITS[1], new_scale))
        files = render(scale)
        for i, f in enumerate(files):
            if f:
                mag[KT_MAGIMG(i)].update(filename=f)
        mag[K_ZLABEL].update(f'scale: {scale:.2f}x')
        mag.refresh()
        try:
            mag[K_MAGSCROLL].contents_changed()
        except Exception as e:
            sg.popup_error_with_traceback('Error calling contents_changed on Column elem', e)
        # --- explicitly size the window to the zoomed content, clamped to win_w/win_h ---
        content_w = sum(int(w * scale) for w, h in sizes) + 30 * len(sizes) + 30      # images + per-panel padding + v-scrollbar
        content_h = max(int(h * scale) for w, h in sizes) + 160                       # tallest image + header/buttons/labels/h-scrollbar
        target = (min(content_w, win_w), min(content_h, win_h))
        if RESIZE_DEBUG: print(f'[rescale_magnify] scale={scale:.2f} sizes={sizes} content=({content_w},{content_h}) clamp=({win_w},{win_h}) target={target} state={mag.TKroot.state()} before={mag.size}')
        if mag.TKroot.state() == 'zoomed':
            mag.TKroot.state('normal')      # a maximized window ignores size changes
        mag.size = target
        mag.TKroot.update_idletasks()
        if RESIZE_DEBUG: print(f'[rescale_magnify] after={mag.size}')
        mag.refresh()

    while True:
        ev, _vals = mag.read()
        if ev in (sg.WIN_CLOSED, K_MAGCLOSE):
            break
        if ev == K_ZIN:
            rescale_magnify(scale * 1.5)
        elif ev == K_ZOUT:
            rescale_magnify(scale / 1.5)
        elif ev == K_ZFIT:
            rescale_magnify(fit_scale())
        elif ev == K_Z100:
            rescale_magnify(1.0)
        elif ev == K_MSCR_UP:
            scroll_mag(dy=-3)
        elif ev == K_MSCR_DN:
            scroll_mag(dy=3)
        elif ev == K_MSCR_LT:
            scroll_mag(dx=-3)
        elif ev == K_MSCR_RT:
            scroll_mag(dx=3)
        elif ev == K_MSCR_PGUP:
            scroll_mag(pages=-1)
        elif ev == K_MSCR_PGDN:
            scroll_mag(pages=1)

    mag.close()
    for tmp in temp_files:
        try:
            os.remove(tmp)
        except Exception:
            pass


BROWSE_MAX_WINDOW = (1900, 1100)
BROWSE_SCALE_LIMITS = (0.1, 4.0)


def show_browse_all_window(results):
    """
    Opens a large window with ONE both-axis scrollable column containing every
    flagged result: a header line per file plus BASELINE | NEW | DIFF images
    side by side. Zoom In/Out re-render every thumbnail at a shared scale
    (NEAREST when enlarging, same as the Magnify viewer). An "Include PASS
    rows" checkbox rebuilds the window with all results included.
    """
    from PIL import Image

    scale = 0.4
    include_pass = False
    temp_files = []

    def build_rows(include_pass_rows, current_scale):
        """Builds the layout rows. Also returns row_sizes: per shown result, a list of (w, h) original image sizes (None for missing panels) used for window fitting."""
        shown = [r for r in results if include_pass_rows or r['status'] != 'PASS']
        layout_rows, image_keys, row_sizes = [], [], []
        for idx, r in enumerate(shown):
            layout_rows.append([sg.Text(f"{r['file']}  -  {r['status']}  -  {r['details']}", font=('Helvetica', 10, 'bold'))])
            img_row, sizes_this_row = [], []
            for label, path in (('Baseline', r.get('baseline_path')), ('New', r.get('new_path')), ('Diff (5x amplified)', r.get('diff_path'))):
                if path and os.path.exists(path):
                    try:
                        with Image.open(path) as im:
                            sizes_this_row.append(im.size)
                    except Exception:
                        sizes_this_row.append((300, 200))
                    f = make_scaled_file(path, current_scale)
                    if f:
                        temp_files.append(f)
                    key = KT_BAIMG(idx, label)
                    image_keys.append((key, path))
                    img_row.append(sg.Column([[sg.Text(label, font=('Helvetica', 8))], [sg.Image(filename=f or '', key=key)]], vertical_alignment='top'))
                else:
                    sizes_this_row.append(None)
                    img_row.append(sg.Column([[sg.Text(label, font=('Helvetica', 8))], [sg.Text('(no image)')]], vertical_alignment='top'))
            layout_rows.append(img_row)
            layout_rows.append([sg.HorizontalSeparator()])
            row_sizes.append(sizes_this_row)
        return layout_rows, image_keys, row_sizes, len(shown)

    screen_w, screen_h = sg.Window.get_screen_size()
    win_w = min(BROWSE_MAX_WINDOW[0], screen_w - 40)
    win_h = min(BROWSE_MAX_WINDOW[1], screen_h - 80)

    while True:                                        # outer loop: rebuild when "Include PASS rows" toggles
        rows_layout, image_keys, row_sizes, n_shown = build_rows(include_pass, scale)
        if n_shown == 0:
            sg.popup_quick_message('Nothing flagged - everything passed! Check "Include PASS rows" to see them all.', font=('Helvetica', 12))
            rows_layout = [[sg.Text('No flagged results.', font=('Helvetica', 12))]]
        layout = [
            [sg.Button('Zoom In (x1.5)', key=K_BZIN), sg.Button('Zoom Out', key=K_BZOUT),
             sg.Text('', key=K_BSCALE, font=('Helvetica', 10)),
             sg.Checkbox('Include PASS rows', default=include_pass, key=K_BINCPASS, enable_events=True),
             sg.Text(f'{n_shown} result(s) shown', font=('Helvetica', 10)),
             sg.Push(), sg.Button('Close', key=K_BCLOSE)],
            [sg.Text('Keys: + / -  zoom      arrows: scroll      PgUp / PgDn: page      Esc: close', font=('Helvetica', 8))],
            [sg.Column(rows_layout, scrollable=True, expand_x=True, expand_y=True, key=K_BACOL)],
        ]
        win = sg.Window('Browse All Results', layout, size=(win_w, win_h), finalize=True, resizable=(False, True), modal=True, keep_on_top=True)
        win[K_BSCALE].update(f'scale: {scale:.2f}x')

        def fit_browse_window():
            """Resizes the Browse All window to fit the zoomed content, clamped to win_w/win_h - same behavior as the Magnify window."""
            if not row_sizes:
                return
            content_w = max(sum((int(s[0] * scale) if s else 120) for s in row) + 30 * len(row) + 30 for row in row_sizes)      # widest row: images + per-panel padding + v-scrollbar
            content_h = sum(max((int(s[1] * scale) if s else 30) for s in row) + 60 for row in row_sizes) + 90                   # each row: tallest image + header/label/separator; + toolbar/h-scrollbar
            target = (min(content_w, win_w), min(content_h, win_h))
            if RESIZE_DEBUG: print(f'[rescale_browse] scale={scale:.2f} rows={len(row_sizes)} content=({content_w},{content_h}) clamp=({win_w},{win_h}) target={target} state={win.TKroot.state()} before={win.size}')
            if win.TKroot.state() == 'zoomed':
                win.TKroot.state('normal')      # a maximized window ignores size changes
            win.size = target
            win.TKroot.update_idletasks()
            if RESIZE_DEBUG: print(f'[rescale_browse] after={win.size}')
            win.refresh()

        def rescale_browse(new_scale):
            """BROWSE ALL window zoom: re-render every thumbnail at new_scale, then resize the window to fit (clamped)."""
            nonlocal scale
            scale = max(BROWSE_SCALE_LIMITS[0], min(BROWSE_SCALE_LIMITS[1], new_scale))
            for key, path in image_keys:
                f = make_scaled_file(path, scale)
                if f:
                    temp_files.append(f)
                    win[key].update(filename=f)
            win[K_BSCALE].update(f'scale: {scale:.2f}x')
            win.refresh()
            try:
                win[K_BACOL].contents_changed()
            except Exception as e:
                pass
                # sg.popup_error_with_traceback('Error calling contents_changed on Column elem', e)
            fit_browse_window()

        fit_browse_window()     # fit on open / rebuild too, not just on zoom

        # Keyboard navigation: +/= zoom in, - zoom out, arrows/PgUp/PgDn scroll, Esc close (same bindings as Magnify)
        for keysym, evt in (('<Key-plus>', K_BZIN), ('<Key-equal>', K_BZIN), ('<KP_Add>', K_BZIN), ('<Key-minus>', K_BZOUT), ('<KP_Subtract>', K_BZOUT),
                            ('<Escape>', K_BCLOSE), ('<Up>', K_BSCR_UP), ('<Down>', K_BSCR_DN), ('<Left>', K_BSCR_LT), ('<Right>', K_BSCR_RT),
                            ('<Prior>', K_BSCR_PGUP), ('<Next>', K_BSCR_PGDN)):
            win.bind(keysym, evt)

        def scroll_browse(dx=0, dy=0, pages=0):
            canvas = win[K_BACOL].Widget.canvas
            if pages:
                canvas.yview_scroll(pages, 'pages')
            if dy:
                canvas.yview_scroll(dy, 'units')
            if dx:
                canvas.xview_scroll(dx, 'units')

        rebuild = False
        while True:
            ev, vals = win.read()
            if ev in (sg.WIN_CLOSED, K_BCLOSE):
                break
            if ev == K_BZIN:
                rescale_browse(scale * 1.5)
            elif ev == K_BZOUT:
                rescale_browse(scale / 1.5)
            elif ev == K_BSCR_UP:
                scroll_browse(dy=-3)
            elif ev == K_BSCR_DN:
                scroll_browse(dy=3)
            elif ev == K_BSCR_LT:
                scroll_browse(dx=-3)
            elif ev == K_BSCR_RT:
                scroll_browse(dx=3)
            elif ev == K_BSCR_PGUP:
                scroll_browse(pages=-1)
            elif ev == K_BSCR_PGDN:
                scroll_browse(pages=1)
            elif ev == K_BINCPASS:
                include_pass = vals[K_BINCPASS]
                rebuild = True
                break
        win.close()
        if not rebuild:
            break

    for tmp in temp_files:
        try:
            os.remove(tmp)
        except Exception:
            pass


def main():
    preview_row = [
        sg.Column([[sg.Text('Baseline', font=('Helvetica', 10, 'bold'))],
                   [sg.Image(key=K_PV_BASE, size=PREVIEW_MAX, background_color='white')]]),
        sg.Column([[sg.Text('New', font=('Helvetica', 10, 'bold'))],
                   [sg.Image(key=K_PV_NEW, size=PREVIEW_MAX, background_color='white')]]),
        sg.Column([[sg.Text('Diff (5x amplified)', font=('Helvetica', 10, 'bold'))],
                   [sg.Image(key=K_PV_DIFF, size=PREVIEW_MAX, background_color='white')]]),
    ]

    layout = [
        [sg.Text('PySimpleGUI Screenshot Regression Comparator', font=('Helvetica', 14, 'bold')),
         sg.Text(f'v{VERSION}', font=('Helvetica', 11, 'bold'), text_color='spring green')],
        [sg.Text('Compares two labeled screenshot runs pixel-by-pixel and reports PASS/FAIL.', font=('Helvetica', 9))],
        [sg.HorizontalSeparator()],
        [sg.Text('Root Folder:', size=(16, 1)), sg.Input(setting='output', key=K_ROOT, size=(100, 1), enable_events=True), sg.FolderBrowse()],
        [sg.Text('Baseline Label:', size=(16, 1)), sg.Combo([], setting='', key=K_BASELABEL, size=(26, 15), auto_size_text=False, readonly=True, enable_events=True),
         sg.Text('New Label:'), sg.Combo([], setting='', key=K_NEWLABEL, size=(26, 15), auto_size_text=False, readonly=True, enable_events=True),
         sg.Button('Swap', key=K_SWAP, tooltip='Swap Baseline and New'), sg.Button('Refresh List', key=K_REFRESH, tooltip='Re-scan Root for run folders (after a new run)'),
         sg.Text('', key=K_RUNCOUNT, font=('Helvetica', 9))],
        [sg.Text('Fail Threshold (%):', size=(16, 1)), sg.Input(setting='0.1', key=K_THRESH, size=(10, 1)),
         sg.Checkbox('Search subfolders recursively', default=True, key=K_RECURSIVE)],
        [sg.Text('', key=K_PATHS, font=('Helvetica', 9))],
        [sg.Button('Scan Folders (preview counts)', key=K_SCAN),
         sg.Button('Run Comparison', key=K_RUN, button_color=('white', 'green')),
         sg.Button('Open Diffs Folder', key=K_OPENDIFFS),
         sg.Button('Open HTML Report', key=K_OPENHTML),
         sg.Button('Browse All (scrolling)', key=K_BROWSEALL, disabled=True),
         sg.Exit(),
         sg.Text('', key=K_PASSCNT, font=('Helvetica', 16, 'bold'), text_color='lime green'),
         sg.Text('', key=K_FAILCNT, font=('Helvetica', 16, 'bold'), text_color='red')],
        [sg.Text('GitHub issue:', font=('Helvetica', 10, 'bold')),
         sg.Button('Copy Markdown', key=K_COPYMD, disabled=True, tooltip='Copies report.md - paste it into the GitHub issue'),
         sg.Button('Copy Image', key=K_COPYIMG, disabled=True, tooltip=f'Copies {FLAGGED_IMAGE_NAME} - paste it right after the Markdown'),
         sg.Text('1) Copy Markdown, paste into the issue   2) Copy Image, paste right after it   (all PASS = no image)', font=('Helvetica', 9))],
        [sg.Text('', key=K_SCANINFO, font=('Helvetica', 9), text_color='blue')],
        [sg.pin(sg.ProgressBar(100, orientation='h', size=(50, 20), key=K_PBAR, visible=False))],
        [sg.Text('', size=(80, 3), key=K_SUMMARY, font=('Helvetica', 11, 'bold'))],
        [sg.HorizontalSeparator()],
        [sg.Text('Results (click a row for side-by-side preview):')],
        [sg.Table(values=[], headings=['File', 'Status', 'Details', 'Size', 'MaxDelta'], key=K_TABLE,
                   auto_size_columns=False, col_widths=[35, 16, 28, 10, 8], num_rows=25,
                   justification='left', enable_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                   row_height=24, expand_x=True, expand_y=True)],
        preview_row,
        [sg.Button('Magnify (large window)', key=K_MAGNIFY, disabled=True),
         sg.Text('', key=K_PREVIEWTEXT, font=('Helvetica', 9))],
    ]

    window = sg.Window('COMPARE!  Screenshot Regression Comparator (GUI)', layout, finalize=True, resizable=True, enable_close_attempted_event=True, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, auto_save_location=True)

    count = psgdnd.enable(window) if hasattr(psgdnd, 'enable') else 0          # <-- the whole drag & drop integration (enable() is GitHub psgdnd 6.0.5+, not on PyPI yet)

    # Repack so the two bottom rows own the bottom edge and the Table (packed last) gives up space first when the window shrinks in Y.
    # tk's packer steals space from the LAST-packed widget first, so PSG's normal top-to-bottom packing clips the bottom rows on shrink.
    # (Same technique as dark_theme_preview view_all(). No wheel/scrollbar fixup needed here - the Table's scrollbar and mousewheel
    # bindings live on the Treeview widget itself, unlike a scrollable Column whose wheel hook hangs off Enter/Leave of its canvas.)
    # Note: K_PV_BASE sits inside a Column, so its ParentRowFrame is a row INSIDE that Column - hop up via ParentContainer (the Column) to get the window-level row.
    table_row, prev_row, mag_row = window[K_TABLE].ParentRowFrame, window[K_PV_BASE].ParentContainer.ParentRowFrame, window[K_MAGNIFY].ParentRowFrame
    table_row.pack_forget(), prev_row.pack_forget(), mag_row.pack_forget()
    mag_row.pack(side='bottom', fill='x')
    prev_row.pack(side='bottom', fill='x')
    table_row.pack(side='top', fill='both', expand=True)
    window.set_min_size((window.size[0] // 2, window.size[1] - 21 * 24))    # allow shrinking the 25-row table down to ~4 visible rows, no further

    all_results = []
    report_path = None
    html_path = None
    preview_temp_files = []
    selected_idx = None

    def resolve_dirs(values):
        """Turns root + labels into (baseline_dir, new_dir, out_dir). Returns (dirs, None) or (None, error_message)."""
        root = values[K_ROOT].strip()
        if not root:
            return None, 'Root folder not set.'
        if not values[K_BASELABEL] or not values[K_NEWLABEL]:
            return None, 'Pick a Baseline Label and a New Label from the lists.'
        base_label, new_label = ('' if values[k] == NO_LABEL else values[k] for k in (K_BASELABEL, K_NEWLABEL))
        b_dir = screenshots_dir_for_label(root, base_label)
        n_dir = screenshots_dir_for_label(root, new_label)
        out_dir = diffs_dir_for_labels(root, base_label, new_label)
        return (b_dir, n_dir, out_dir), None

    def update_paths_preview(values):
        """Live line under the inputs showing the three derived folders, flagging missing ones and identical labels."""
        dirs, err = resolve_dirs(values)
        if err:
            window[K_PATHS].update(err)
            return
        b_dir, n_dir, out_dir = dirs
        mark = lambda d: '' if os.path.isdir(d) else '  [MISSING]'
        same = '    <-- SAME FOLDER - labels are identical!' if os.path.normpath(b_dir) == os.path.normpath(n_dir) else ''
        window[K_PATHS].update(f'Baseline: {b_dir}{mark(b_dir)}\nNew: {n_dir}{mark(n_dir)}{same}\nDiffs -> {out_dir}')

    def scan_counts(values):
        dirs, err = resolve_dirs(values)
        if err:
            return None, None, err
        b_dir, n_dir, _out = dirs
        if not os.path.isdir(values[K_ROOT].strip()):
            return None, None, f'Root folder does not exist: {values[K_ROOT].strip()}'
        if not os.path.isdir(b_dir):
            return None, None, f'Baseline folder does not exist: {b_dir}  (run the snapshot suite with that label first)'
        if not os.path.isdir(n_dir):
            return None, None, f'New folder does not exist: {n_dir}  (run the snapshot suite with that label first)'
        recursive = values[K_RECURSIVE]
        return len(find_pngs(b_dir, recursive)), len(find_pngs(n_dir, recursive)), None

    def set_preview(image_key, path):
        if path and os.path.exists(path):
            pv = make_preview_file(path)
            if pv:
                preview_temp_files.append(pv)
                window[image_key].update(filename=pv)
                return
        window[image_key].update(filename='')

    def refresh_label_lists():
        """Re-lists the run folders under Root into both pickers (newest first), keeping the current picks that still exist."""
        labels = list_labels(window[K_ROOT].get().strip())
        for key in (K_BASELABEL, K_NEWLABEL):
            current = window[key].get()
            window[key].update(values=labels, value=current if current in labels else '')
        window[K_RUNCOUNT].update(f'{len(labels)} run(s) under Root')

    refresh_label_lists()
    update_paths_preview({k: window[k].get() for k in (K_ROOT, K_BASELABEL, K_NEWLABEL)})

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSE_ATTEMPTED_EVENT, sg.WIN_CLOSED, 'Exit'):
            window.settings_save(values)
            break

        if event in (K_ROOT, K_REFRESH):        # Root changed / new runs made -> re-list the run folders in both pickers
            refresh_label_lists()
            values[K_BASELABEL], values[K_NEWLABEL] = window[K_BASELABEL].get(), window[K_NEWLABEL].get()

        if event == K_SWAP:
            values[K_BASELABEL], values[K_NEWLABEL] = values[K_NEWLABEL], values[K_BASELABEL]
            window[K_BASELABEL].update(value=values[K_BASELABEL])
            window[K_NEWLABEL].update(value=values[K_NEWLABEL])

        update_paths_preview(values)        # refresh derived-path line on every event (picking a label fires events)

        if event == K_SCAN:
            b_count, n_count, err = scan_counts(values)
            if err:
                window[K_SCANINFO].update(err, text_color='red')
            else:
                window[K_SCANINFO].update(
                    f'Found {b_count} PNG(s) in baseline, {n_count} PNG(s) in new.'
                    + ('  WARNING: one or both are 0 - check your root folder and labels!' if (b_count == 0 or n_count == 0) else ''),
                    text_color='red' if (b_count == 0 or n_count == 0) else sg.theme_text_color()
                )

        if event == K_RUN:
            dirs, err = resolve_dirs(values)
            if err:
                sg.popup_error(err)
                continue
            baseline_dir, new_dir, out_dir = dirs
            recursive = values[K_RECURSIVE]
            try:
                threshold = float(values[K_THRESH])
            except ValueError:
                sg.popup_error('Threshold must be a number, e.g. 0.1')
                continue

            if not os.path.isdir(baseline_dir):
                sg.popup_error(f'Baseline folder does not exist:\n{baseline_dir}\n\nRun the snapshot suite with that label first.')
                continue
            if not os.path.isdir(new_dir):
                sg.popup_error(f'New folder does not exist:\n{new_dir}\n\nRun the snapshot suite with that label first.')
                continue
            if os.path.normpath(baseline_dir) == os.path.normpath(new_dir):
                sg.popup_error('Baseline and New labels resolve to the SAME folder - nothing to compare.\nUse two different labels.')
                continue

            try:
                import PIL  # noqa: F401
            except ImportError:
                sg.popup_error('Pillow is required. Run: pip install Pillow')
                continue

            # Pre-flight: validate BEFORE running instead of writing an empty report.
            b_count, n_count, err = scan_counts(values)
            if b_count == 0 or n_count == 0:
                sg.popup_error(
                    f'No comparison run - found {b_count} PNG(s) in baseline and {n_count} PNG(s) in new.\n\n'
                    'Double check the root folder and labels, and that you actually ran\n'
                    'the snapshot suite with both labels first.'
                )
                continue

            window[K_TABLE].update(values=[])
            selected_idx = None
            window[K_MAGNIFY].update(disabled=True)
            window[K_BROWSEALL].update(disabled=True)
            window[K_COPYMD].update(disabled=True)
            window[K_COPYIMG].update(disabled=True)
            window[K_PASSCNT].update('')
            window[K_FAILCNT].update('')
            window[K_SUMMARY].update('Running comparison...')
            window[K_PBAR].update(visible=True, current_count=0)
            window[K_RUN].update(disabled=True)
            window.refresh()

            t = threading.Thread(target=run_comparison, args=(baseline_dir, new_dir, out_dir, threshold, recursive, window), daemon=True)
            t.start()

        if event == K_PROGRESS:
            done, total = values[event]
            pct = int((done / total) * 100) if total else 0
            window[K_PBAR].update(current_count=pct)

        if event == K_DONE:
            all_results, counts, report_path, html_path, scan_info = values[event]
            window[K_PBAR].update(visible=False)
            window[K_RUN].update(disabled=False)

            table_data = [[r['file'], r['status'], r['details'], r['size'], r['max_delta']] for r in all_results]
            row_colors = []
            for i, r in enumerate(all_results):
                colors = STATUS_COLORS.get(r['status'])
                if colors:
                    row_colors.append((i, colors[0], colors[1]))
            window[K_TABLE].update(values=table_data, row_colors=row_colors)

            passed = counts.get('PASS', 0)
            failed = sum(v for k, v in counts.items() if k != 'PASS')
            window[K_PASSCNT].update(f'Passed: {passed}')
            window[K_FAILCNT].update(f'Failed: {failed}')
            window[K_BROWSEALL].update(disabled=False)
            window[K_COPYMD].update(disabled=not os.path.exists(os.path.join(os.path.dirname(html_path), 'report.md')))
            window[K_COPYIMG].update(disabled=not os.path.exists(os.path.join(os.path.dirname(html_path), FLAGGED_IMAGE_NAME)))
            total_n = passed + failed
            summary = f'PASSED: {passed}   FAILED/FLAGGED: {failed}   TOTAL: {total_n}\n' + \
                       f'(baseline had {scan_info["baseline_count"]} PNGs, new had {scan_info["new_count"]} PNGs)\n' + \
                       f'Reports: {report_path} / {html_path}'
            window[K_SUMMARY].update(summary)

            if total_n == 0:
                sg.popup_error('No matching files were compared. Check the root folder and labels and try "Scan Folders" first.')
            elif failed == 0:
                sg.popup_quick_message('All screenshots match! No regressions detected.', font=('Helvetica', 14))
            else:
                sg.popup_quick_message(f'{failed} screenshot(s) flagged - review the table below.', font=('Helvetica', 14))

        if event == K_TABLE:
            if values[K_TABLE]:
                selected_idx = values[K_TABLE][0]
                r = all_results[selected_idx]
                set_preview(K_PV_BASE, r.get('baseline_path'))
                set_preview(K_PV_NEW, r.get('new_path'))
                set_preview(K_PV_DIFF, r.get('diff_path'))
                extra = '' if r.get('diff_path') else '  (no diff image - identical or missing file)'
                window[K_PREVIEWTEXT].update(f"{r['file']}  -  {r['status']}  -  {r['details']}{extra}")
                window[K_MAGNIFY].update(disabled=False)

        if event == K_MAGNIFY:
            if selected_idx is not None and selected_idx < len(all_results):
                show_magnify_window(all_results[selected_idx])
            else:
                sg.popup_error('Select a result row first, then Magnify.')

        if event == K_BROWSEALL:
            if all_results:
                show_browse_all_window(all_results)
            else:
                sg.popup_error('No results yet - run a comparison first.')

        if event == K_OPENDIFFS:
            dirs, err = resolve_dirs(values)
            if err:
                sg.popup_error(err)
            elif os.path.isdir(dirs[2]):
                open_in_file_manager(os.path.abspath(dirs[2]))
            else:
                sg.popup_error(f'Diffs folder does not exist yet: {dirs[2]}\nRun a comparison first.')

        if event == K_COPYMD and html_path:
            with open(os.path.join(os.path.dirname(html_path), 'report.md'), encoding='utf-8') as f:
                sg.clipboard_set(f.read())
            has_img = os.path.exists(os.path.join(os.path.dirname(html_path), FLAGGED_IMAGE_NAME))
            sg.popup_quick_message('Markdown copied - paste it into the GitHub issue' + ('\nthen click Copy Image and paste again' if has_img else ''), font=('Helvetica', 12))

        if event == K_COPYIMG and html_path:
            img = os.path.join(os.path.dirname(html_path), FLAGGED_IMAGE_NAME)
            err = copy_png_to_clipboard(img)
            if not err:
                sg.popup_quick_message('Image copied - paste it (Ctrl+V) right after the Markdown in the issue', font=('Helvetica', 12))
            else:
                if platform.system() == 'Windows':
                    subprocess.Popen(f'explorer /select,"{os.path.abspath(img)}"')    # folder opens with the image selected - drag it in
                else:
                    open_in_file_manager(os.path.dirname(os.path.abspath(img)))
                sg.popup_error(f'Could not put the image on the clipboard:\n{err}\n\nDrag {FLAGGED_IMAGE_NAME} from the folder that just opened into the issue instead.')

        if event == K_OPENHTML:
            if html_path and os.path.exists(html_path):
                open_in_file_manager(os.path.abspath(html_path))
            else:
                sg.popup_error('No HTML report yet - run a comparison first.')

        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), location=window.current_location(use_anchor=sg.WIN_ANCHOR_UPPER_LEFT), location_anchor=sg.WIN_ANCHOR_LOWER_RIGHT, keep_on_top=True, non_blocking=True, size=(70,10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)

    for tmp in preview_temp_files:
        try:
            os.remove(tmp)
        except Exception:
            pass

    window.close()


if __name__ == '__main__':
    main()