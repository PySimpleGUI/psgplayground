"""
run_all_snapshots.py - Runs every SNAP_*.py test script in this folder
sequentially and collects all screenshots into a labeled output folder.

CHANGES from the previous version:
- No PySimpleGUI import. The harness must not depend on the very
  package it is testing: previously a broken release under test would
  also break this runner (and sg.Print / the final popup made it
  non-headless). Pure stdlib now; safe to run from a separate tools venv.
- --python lets you point at the interpreter of the venv that has the
  PySimpleGUI release under test, so the tools venv and the
  version-under-test venv stay separate.
- --label NAME saves to output/screenshots_NAME/ (sets SNAP_OUTPUT_DIR,
  same mechanism the GUI runner's Label field uses) so runs per version
  don't overwrite each other.
- --timeout N kills any SNAP script that hangs (default 120s) so one
  stuck window can't stall the whole suite.
- Writes manifest.txt into the output folder recording the PySimpleGUI/
  Python/tkinter/OS versions that produced the screenshots - queried
  from the TEST interpreter, not this one.

Usage:
    python run_all_snapshots.py [--label 6.3.2] [--python /path/to/venv/python] [--timeout 120] [--stop-on-fail]
"""
import argparse
import datetime
import glob
import os
import re
import subprocess
import sys

DEFAULT_SCREENSHOTS_DIR = os.path.join('output', 'screenshots')

MANIFEST_PROBE = (
    "import sys, platform, tkinter;"
    "import PySimpleGUI as sg;"
    "print('PySimpleGUI:', sg.version);"
    "print('Python:', sys.version.replace(chr(10), ' '));"
    "print('tkinter Tcl/Tk:', tkinter.TkVersion);"
    "print('OS:', platform.platform())"
)


def sanitize_label(label):
    label = (label or '').strip()
    if not label:
        return ''
    return re.sub(r'[^A-Za-z0-9._-]+', '_', label)


def output_dir_for_label(label):
    safe = sanitize_label(label)
    return f'{DEFAULT_SCREENSHOTS_DIR}_{safe}' if safe else DEFAULT_SCREENSHOTS_DIR


def write_manifest(python_exe, output_dir, label):
    os.makedirs(output_dir, exist_ok=True)
    lines = [f'Run date: {datetime.datetime.now().isoformat(timespec="seconds")}',
             f'Label: {label or "(none)"}',
             f'Test interpreter: {python_exe}']
    try:
        probe = subprocess.run([python_exe, '-c', MANIFEST_PROBE],
                               capture_output=True, text=True, timeout=60)
        lines.append(probe.stdout.strip() if probe.returncode == 0
                     else f'MANIFEST PROBE FAILED:\n{probe.stderr.strip()}')
    except Exception as e:
        lines.append(f'MANIFEST PROBE ERROR: {e}')
    path = os.path.join(output_dir, 'manifest.txt')
    with open(path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'Manifest written to {path}:')
    for line in lines:
        print(f'  {line}')


def main():
    parser = argparse.ArgumentParser(description='Run all SNAP_*.py snapshot tests')
    parser.add_argument('--label', default='', help='Tag this run: screenshots go to output/screenshots_<label>/')
    parser.add_argument('--python', default=sys.executable,
                        help='Interpreter with the PySimpleGUI release under test (default: this one)')
    parser.add_argument('--timeout', type=float, default=120,
                        help='Seconds before a hung SNAP script is killed (default: 120)')
    parser.add_argument('--stop-on-fail', action='store_true', help='Stop the suite at the first failing script')
    args = parser.parse_args()

    scripts = sorted(glob.glob('SNAP_*.py'))
    if not scripts:
        print('ERROR: No SNAP_*.py scripts found in the current directory.')
        sys.exit(2)

    output_dir = output_dir_for_label(args.label)
    env = os.environ.copy()
    env['SNAP_OUTPUT_DIR'] = output_dir

    print(f'Found {len(scripts)} snapshot test scripts.')
    print(f'Screenshots will be saved to: {os.path.abspath(output_dir)}')
    write_manifest(args.python, output_dir, args.label)

    failures = []
    for script in scripts:
        print(f'Running {script} ...', flush=True)
        try:
            result = subprocess.run([args.python, script], env=env, timeout=args.timeout)
            ok = result.returncode == 0
            if not ok:
                print(f'  WARNING: {script} exited with code {result.returncode}')
        except subprocess.TimeoutExpired:
            print(f'  WARNING: {script} exceeded {args.timeout}s timeout and was killed')
            ok = False
        if not ok:
            failures.append(script)
            if args.stop_on_fail:
                print('Stopping early (--stop-on-fail).')
                break

    print()
    print(f'Done. {len(scripts) - len(failures)}/{len(scripts)} scripts completed cleanly.')
    if failures:
        print('Scripts that failed or timed out:')
        for f in failures:
            print(f'  - {f}')
    print(f'Screenshots saved to {os.path.abspath(output_dir)}')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
