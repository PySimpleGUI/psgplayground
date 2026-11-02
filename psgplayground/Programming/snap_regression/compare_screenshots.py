"""
compare_screenshots.py

Compares two folders of PNG screenshots (BASELINE vs NEW) pixel-by-pixel
and produces a pass/fail regression report.

CHANGES from the previous version:
- report.csv now records image dimensions, max per-pixel delta, and the
  bounding box of the changed region - a size regression shows old vs
  new geometry at a glance, and max-delta separates "one pixel of
  antialiasing" from "a color actually changed".
- Writes report.html next to report.csv: for every FAIL/ERROR row it
  embeds baseline | new | amplified-diff thumbnails side by side, so a
  failed run can be reviewed (or attached to a bug report) without any
  GUI tooling.
- Skips manifest.txt and non-PNG files automatically (manifests are now
  written into screenshot folders by the runners).

Usage:
    python compare_screenshots.py <baseline_folder> <new_folder> [--out diffs] [--threshold 0.1] [--no-recursive]
"""
import argparse
import csv
import html
import os
import sys


def find_pngs(folder, recursive=True):
    """Returns {filename: full_path} for every .png in folder (recursive by default)."""
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
    """
    Returns a dict with pct_diff, max_delta, bbox, sizes - or an 'error'
    key. Saves an amplified diff image to diff_path when pixels differ.
    """
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


def write_html_report(path, rows, baseline_map, new_map, out_dir):
    """rows: list of dicts with file/status/details/diff_path keys."""
    def img_tag(p):
        if p and os.path.exists(p):
            rel = os.path.relpath(p, os.path.dirname(path))
            return f'<a href="{html.escape(rel)}"><img src="{html.escape(rel)}" style="max-width:380px;max-height:260px;border:1px solid #999"></a>'
        return '<i>missing</i>'

    lines = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>Screenshot Regression Report</title>',
             '<style>body{font-family:sans-serif} td,th{padding:6px;vertical-align:top;text-align:left}',
             '.PASS{background:#d4f7d4}.FAIL{background:#f7d4d4}.ERROR{background:#f0b0b0}',
             '.MISSING_IN_NEW,.MISSING_IN_BASELINE{background:#f7ecd4}</style></head><body>',
             '<h1>PySimpleGUI Screenshot Regression Report</h1>']

    counts = {}
    for r in rows:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    lines.append('<p>' + '  '.join(f'<b>{html.escape(k)}</b>: {v}' for k, v in sorted(counts.items())) + '</p>')

    lines.append('<table border="1" cellspacing="0"><tr><th>File</th><th>Status</th><th>Details</th>'
                 '<th>Baseline</th><th>New</th><th>Diff (5x amplified)</th></tr>')
    for r in rows:
        show_images = r['status'] not in ('PASS',)
        lines.append(f'<tr class="{html.escape(r["status"])}"><td>{html.escape(r["file"])}</td>'
                     f'<td>{html.escape(r["status"])}</td><td>{html.escape(r["details"])}</td>')
        if show_images:
            lines.append(f'<td>{img_tag(baseline_map.get(r["file"]))}</td>'
                         f'<td>{img_tag(new_map.get(r["file"]))}</td>'
                         f'<td>{img_tag(r.get("diff_path"))}</td>')
        else:
            lines.append('<td colspan="3"><i>identical (within threshold)</i></td>')
        lines.append('</tr>')
    lines.append('</table></body></html>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description='Compare two screenshot folders for PySimpleGUI regression testing')
    parser.add_argument('baseline', help='Folder with known-good baseline screenshots')
    parser.add_argument('new', help='Folder with new screenshots to test')
    parser.add_argument('--out', default='diffs', help='Folder to save diff images and reports (default: diffs)')
    parser.add_argument('--threshold', type=float, default=0.1, help='Percent pixel difference threshold to flag as FAIL (default: 0.1)')
    parser.add_argument('--no-recursive', action='store_true', help='Only scan the top level of each folder')
    args = parser.parse_args()

    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print('ERROR: Pillow is required. Run: pip install Pillow')
        sys.exit(2)

    if not os.path.isdir(args.baseline):
        print(f'ERROR: baseline folder not found: {args.baseline}')
        sys.exit(2)
    if not os.path.isdir(args.new):
        print(f'ERROR: new folder not found: {args.new}')
        sys.exit(2)

    recursive = not args.no_recursive
    baseline_map = find_pngs(args.baseline, recursive=recursive)
    new_map = find_pngs(args.new, recursive=recursive)

    print(f'Found {len(baseline_map)} PNG(s) in baseline folder: {args.baseline}')
    print(f'Found {len(new_map)} PNG(s) in new folder: {args.new}')

    if len(baseline_map) == 0 or len(new_map) == 0:
        print()
        print('ERROR: One or both folders have 0 PNG files - refusing to write an empty report.')
        print('Check that you pointed at the folder that (directly or in a subfolder) contains')
        print('the .png screenshots, and that you actually ran the snapshot suite in both first.')
        sys.exit(2)

    baseline_files = set(baseline_map.keys())
    new_files = set(new_map.keys())

    only_baseline = baseline_files - new_files
    only_new = new_files - baseline_files
    common = baseline_files & new_files

    if len(common) == 0:
        print()
        print('ERROR: 0 matching filenames between the two folders - refusing to write an empty report.')
        print(f'Baseline files sample: {sorted(baseline_files)[:5]}')
        print(f'New files sample: {sorted(new_files)[:5]}')
        sys.exit(2)

    rows = []
    for fname in sorted(common):
        diff_path = os.path.join(args.out, fname)
        res = compare_pair(baseline_map[fname], new_map[fname], diff_path)
        if 'error' in res:
            rows.append({'file': fname, 'status': 'ERROR', 'details': res['error'],
                         'baseline_size': res.get('baseline_size'), 'new_size': res.get('new_size'),
                         'max_delta': '', 'bbox': '', 'diff_path': None})
        else:
            status = 'FAIL' if res['pct_diff'] > args.threshold else 'PASS'
            rows.append({'file': fname, 'status': status,
                         'details': f'{res["pct_diff"]:.4f}% pixel difference',
                         'baseline_size': res['baseline_size'], 'new_size': res['new_size'],
                         'max_delta': res['max_delta'], 'bbox': res['bbox'],
                         'diff_path': diff_path if status == 'FAIL' else None})

    for fname in sorted(only_baseline):
        rows.append({'file': fname, 'status': 'MISSING_IN_NEW', 'details': 'File exists in baseline but not in new',
                     'baseline_size': '', 'new_size': '', 'max_delta': '', 'bbox': '', 'diff_path': None})
    for fname in sorted(only_new):
        rows.append({'file': fname, 'status': 'MISSING_IN_BASELINE', 'details': 'File exists in new but not in baseline',
                     'baseline_size': '', 'new_size': '', 'max_delta': '', 'bbox': '', 'diff_path': None})

    os.makedirs(args.out, exist_ok=True)
    report_path = os.path.join(args.out, 'report.csv')
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'status', 'details', 'baseline_size', 'new_size', 'max_pixel_delta', 'changed_bbox'])
        for r in rows:
            writer.writerow([r['file'], r['status'], r['details'],
                             r['baseline_size'] or '', r['new_size'] or '', r['max_delta'], r['bbox'] or ''])

    html_path = os.path.join(args.out, 'report.html')
    write_html_report(html_path, rows, baseline_map, new_map, args.out)

    passed = sum(1 for r in rows if r['status'] == 'PASS')
    failed = sum(1 for r in rows if r['status'] != 'PASS')

    print('=' * 70)
    print('PySimpleGUI Screenshot Regression Report')
    print('=' * 70)
    for r in rows:
        print(f'[{r["status"]:20}] {r["file"]:45} {r["details"]}')
    print('=' * 70)
    print(f'PASSED: {passed}   FAILED/FLAGGED: {failed}   TOTAL: {len(rows)}')
    print(f'CSV report:  {report_path}')
    print(f'HTML report: {html_path}  (open in a browser for side-by-side images)')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
