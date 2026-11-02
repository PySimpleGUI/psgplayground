"""
run_snapshots_gui.py

GUI front-end for running the SNAP_*.py screenshot test scripts.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.6  Runs with the PyPI psgdnd (6.0.4 has no enable()) - drag & drop is skipped there instead of crashing at startup
2026-10-29  v1.5  Auto label <YYYY-MM-DD>_<PySimpleGUI version under test> (+ optional Suffix, e.g. VarA) replaces the typed label - version re-probed at run start
2026-10-29  v1.5  Label's folder already has files (same version, same day) -> asks before the run: Empty Folder First / Keep Files / Cancel Run
2026-10-28  v1.4  Visible version number: VERSION constant shown in the header - bump it with every change, alongside this CHANGE LOG
2026-10-28  Manifest probe: full Tcl/Tk patchlevel (8.6.x) and Windows build.revision + release (e.g. 26200.7019 (25H2)) now recorded - catches silent OS/Tk drift between runs
2026-10-28  "Under test:" readout in header - probes Test Python + PySimpleGUI Folder for the version/file that WILL be imported; refreshes at startup and on field change
2026-10-28  PySimpleGUI Folder input: run SNAP scripts / View / manifest probe against a local PySimpleGUI.py via PYTHONPATH (blank = installed package)
2026-09-02  Repack rows: shrinking now clips script list / log Multiline only; buttons, separator, progress and summary rows stay visible
2026-09-02  Amber raised sash on the Pane: sashwidth 8, resize cursor, bigger handle
2026-09-02  Vertical Pane added: script area (top) / log (bottom), handle just above "Log:"
2026-09-02  Root Folder input (same style as compare GUI); all output paths build under it

Usage:
    python run_snapshots_gui.py
"""
import datetime
import glob
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
import PySimpleGUI as sg
import psgdnd

carbon_molasses = {"BACKGROUND": '#121110', "TEXT": '#d0c7b8', "INPUT": '#1f1c18', "TEXT_INPUT": '#e0dbcf', "SCROLL": '#1f1c18', "BUTTON": ('#f5ecd8', '#6b4a1e'), "PROGRESS": ('#6b4a1e', '#1f1c18'), "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,}

sg.theme_add_new('CarbonMolasses', carbon_molasses)
sg.theme('CarbonMolasses')



VERSION = '1.6'         # Runner version - bump with every change (see CHANGE LOG)

DEFAULT_SCREENSHOTS_DIR = os.path.join('output', 'screenshots')

MANIFEST_PROBE = r'''
import sys, platform, tkinter
import PySimpleGUI as sg
print('PySimpleGUI:', sg.version)
print('PySimpleGUI file:', sg.__file__)
print('Python:', sys.version.replace(chr(10), ' '))
print('tkinter Tcl/Tk:', tkinter.Tcl().eval('info patchlevel'))
print('OS:', platform.platform())
try:
    import winreg
    k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
    q = lambda name: str(winreg.QueryValueEx(k, name)[0])
    print('Windows build:', q('CurrentBuildNumber') + '.' + q('UBR') + '  (' + q('DisplayVersion') + ')')
except Exception:
    pass
'''

TESTVER_PROBE = "import PySimpleGUI as sg; print(sg.version); print(sg.__file__)"



# ---- Key constants (convention: K_NAME = '-NAME-'; KT_NAME = lambda for repeated keys -> tuple) ----
K_ROOT = '-ROOT-'
K_LABEL = '-LABEL-'
K_LABELPREVIEW = '-LABELPREVIEW-'
K_SUFFIX = '-SUFFIX-'
K_PYTHON = '-PYTHON-'
K_SGFOLDER = '-SGFOLDER-'
K_TESTVER = '-TESTVER-'
K_TESTVER_RESULT = '-TESTVER-RESULT-'
K_TIMEOUT = '-TIMEOUT-'
K_SELALL = '-SELALL-'
K_SELNONE = '-SELNONE-'
K_STOPONFAIL = '-STOPONFAIL-'
K_SCRIPTCOL = '-SCRIPTCOL-'
K_PANE = '-PANE-'
K_SEP2 = '-SEP2-'
K_RUNSEL = '-RUNSEL-'
K_RUNALL = '-RUNALL-'
K_OPENSHOTS = '-OPENSHOTS-'
K_PASSCNT = '-PASSCNT-'
K_FAILCNT = '-FAILCNT-'
K_PBAR = '-PBAR-'
K_PROGRESSTEXT = '-PROGRESSTEXT-'
K_LOG = '-LOG-'
K_SUMMARY = '-SUMMARY-'
K_SCRIPT_START = '-SCRIPT-START-'
K_SCRIPT_DONE = '-SCRIPT-DONE-'
K_ALL_DONE = '-ALL-DONE-'
K_COMPARE = '-COMPARE-'
# "Results folder already used" dialog
K_EMPTY = '-EMPTY-'
K_KEEP = '-KEEP-'
K_CANCELRUN = '-CANCELRUN-'
# Per-script repeated elements (one row per SNAP script)
K_CB = '-CB-'
KT_CB = lambda script: (K_CB, script)
K_STATUS = '-STATUS-'
KT_STATUS = lambda script: (K_STATUS, script)
K_RUNONE = '-RUNONE-'
KT_RUNONE = lambda script: (K_RUNONE, script)
K_VIEW = '-VIEW-'
KT_VIEW = lambda script: (K_VIEW, script)
K_EDIT = '-EDIT-'
KT_EDIT = lambda script: (K_EDIT, script)


def discover_scripts():
    return sorted(glob.glob('SNAP_*.py'))


def sanitize_label(label):
    """Turns a user-typed label like '6.3' or 'my test!' into a safe folder-name suffix."""
    label = label.strip()
    if not label:
        return ''
    return re.sub(r'[^A-Za-z0-9._-]+', '_', label)


def screenshots_dir_for_label(label, root=''):
    """Builds the output folder under `root` (blank root = current folder, the old behavior)."""
    safe = sanitize_label(label)
    subdir = f'{DEFAULT_SCREENSHOTS_DIR}_{safe}' if safe else DEFAULT_SCREENSHOTS_DIR
    return os.path.join(root.strip(), subdir) if root.strip() else subdir


def make_auto_label(version, suffix=''):
    """Auto run label <YYYY-MM-DD>_<PySimpleGUI version>[_<suffix>], e.g. 2026-10-29_6.3.17 or 2026-10-29_6.3.17_VarA ('' while the version is unknown)."""
    if not version:
        return ''
    return sanitize_label('_'.join([datetime.date.today().isoformat(), version] + ([suffix.strip()] if suffix.strip() else [])))


def ask_empty_folder(folder):
    """The label's folder already has files (same version already run today). Asks before the run - returns K_EMPTY, K_KEEP, or None to cancel."""
    pngs = len(glob.glob(os.path.join(folder, '**', '*.png'), recursive=True))
    last_run = ''
    try:
        with open(os.path.join(folder, 'manifest.txt')) as f:
            last_run = next((line.split(':', 1)[1].strip().replace('T', ' ') for line in f if line.startswith('Run date:')), '')
    except OSError:
        pass
    layout = [[sg.Text('This label already has results from an earlier run', font=('Helvetica', 12, 'bold'), text_color='#e8a54a')],
              [sg.Text(os.path.abspath(folder), font=('Courier', 9))],
              [sg.Text(f'{pngs} screenshot(s)' + (f'      last run: {last_run}' if last_run else ''))],
              [sg.Text('Empty the folder first, so it holds ONLY this run?')],
              [sg.Button('Empty Folder First', key=K_EMPTY, button_color=('white', '#8b2e16')), sg.Button('Keep Files (overwrite)', key=K_KEEP),
               sg.Button('Cancel Run', key=K_CANCELRUN)]]
    win = sg.Window('Results folder already used', layout, modal=True, keep_on_top=True, finalize=True)
    win.bind('<Escape>', K_CANCELRUN)
    event, _values = win.read()
    win.close()
    return event if event in (K_EMPTY, K_KEEP) else None


def empty_results_folder(folder):
    """Deletes everything INSIDE a screenshots* results folder - the folder itself stays (fine if Explorer has it open). Returns '' or an error message."""
    if not os.path.basename(os.path.normpath(folder)).startswith('screenshots'):
        return f'Refusing to empty a folder whose name does not start with "screenshots":\n{folder}'
    for entry in list(os.scandir(folder)):
        try:
            if entry.is_dir(follow_symlinks=False):
                shutil.rmtree(entry.path)
            else:
                os.remove(entry.path)
        except OSError as e:
            return f'Could not delete:\n{entry.path}\n\n{e}\n\nRun cancelled - the folder may be partly emptied.'
    return ''


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
        sg.popup_error(f'Could not open folder:\n{e}')


def write_manifest(python_exe, output_dir, label, log, env=None):
    os.makedirs(output_dir, exist_ok=True)
    lines = [f'Run date: {datetime.datetime.now().isoformat(timespec="seconds")}',
             f'Label: {label or "(none)"}',
             f'Test interpreter: {python_exe}']
    try:
        probe = subprocess.run([python_exe, '-c', MANIFEST_PROBE],
                               capture_output=True, text=True, timeout=30, env=env)
        lines.append(probe.stdout.strip() if probe.returncode == 0
                     else f'MANIFEST PROBE FAILED: {probe.stderr.strip()}')
    except Exception as e:
        lines.append(f'MANIFEST PROBE ERROR: {e}')
    with open(os.path.join(output_dir, 'manifest.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    for line in lines:
        log(f'[manifest] {line}')


def get_test_version(python_exe, sg_folder):
    """Asks the TEST interpreter which PySimpleGUI it would import. Returns (version or None, 'Under test: ...' display text)."""
    env = os.environ.copy()
    if sg_folder:
        env['PYTHONPATH'] = sg_folder + os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else sg_folder
    try:
        probe = subprocess.run([python_exe, '-c', TESTVER_PROBE], capture_output=True, text=True, timeout=15, env=env)
        out = probe.stdout.strip().splitlines()
        if probe.returncode == 0 and len(out) >= 2:
            return out[0].strip(), f'Under test: {out[0]}  ({out[1]})'
        err = probe.stderr.strip().splitlines()[-1] if probe.stderr.strip() else 'probe failed'
        return None, f'Under test: ?  ({err})'
    except Exception as e:
        return None, f'Under test: ?  ({e})'


def probe_test_version(python_exe, sg_folder, window, seq):
    """Background probe: report the PySimpleGUI version/file the TEST interpreter would import."""
    version, result = get_test_version(python_exe, sg_folder)
    window.write_event_value(K_TESTVER_RESULT, (seq, result, version))


def run_scripts_worker(scripts, stop_on_failure, output_dir, python_exe, timeout, label, sg_folder, window):
    """
    Runs each script under `python_exe` with SNAP_OUTPUT_DIR set to
    `output_dir`, streaming stdout back to the GUI line by line, with a
    kill-timer per script, and reporting pass/fail for each.
    """
    total = len(scripts)
    results = []

    env = os.environ.copy()
    env['SNAP_OUTPUT_DIR'] = output_dir
    if sg_folder:
        env['PYTHONPATH'] = sg_folder + os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else sg_folder

    write_manifest(python_exe, output_dir, label,
                   lambda line: window.write_event_value(K_LOG, line), env=env)

    for i, script in enumerate(scripts, 1):
        window.write_event_value(K_SCRIPT_START, (script, i, total))
        timed_out = [False]
        try:
            proc = subprocess.Popen(
                [python_exe, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )

            def kill_proc():
                timed_out[0] = True
                proc.kill()

            timer = threading.Timer(timeout, kill_proc)
            timer.start()
            try:
                for line in proc.stdout:
                    window.write_event_value(K_LOG, line.rstrip('\n'))
                proc.wait()
            finally:
                timer.cancel()

            if timed_out[0]:
                window.write_event_value(K_LOG, f'ERROR: {script} exceeded {timeout}s timeout and was killed')
                success = False
            else:
                success = proc.returncode == 0
        except Exception as e:
            window.write_event_value(K_LOG, f'ERROR launching {script}: {e}')
            success = False

        results.append((script, success))
        window.write_event_value(K_SCRIPT_DONE, (script, success, i, total))

        if not success and stop_on_failure:
            window.write_event_value(K_LOG, f'Stopping early - {script} failed and "stop on failure" is checked.')
            break

    window.write_event_value(K_ALL_DONE, (results, output_dir))


def main():
    scripts = discover_scripts()

    if not scripts:
        sg.popup_error(
            'No SNAP_*.py scripts found in the current folder.\n\n'
            'Make sure this launcher is in the same folder as your\n'
            'SNAP_01_text_all_params.py, SNAP_02_input_all_params.py, etc.'
        )
        return

    checkbox_rows = []
    for script in scripts:
        safe_key = script
        checkbox_rows.append([
            sg.Checkbox('', default=True, key=KT_CB(safe_key)),
            sg.Text(script, size=(42, 1)),
            sg.Text('', key=KT_STATUS(safe_key), size=(10, 1)),
            sg.Button('Run Only', key=KT_RUNONE(safe_key), size=(9, 1)),
            sg.Button('View', key=KT_VIEW(safe_key), size=(5, 1),
                      tooltip='Open interactively - no screenshot; close the window when done'),
            sg.Button('Edit', key=KT_EDIT(safe_key), size=(5, 1)),
        ])

    script_list_column = sg.Column(checkbox_rows, scrollable=True, vertical_scroll_only=True, key=K_SCRIPTCOL, expand_x=True, expand_y=True)

    top_pane = sg.Column([
        [sg.Button('Select All', key=K_SELALL), sg.Button('Select None', key=K_SELNONE),
         sg.Checkbox('Stop on first failure', default=False, key=K_STOPONFAIL)],
        [script_list_column],
        [sg.HorizontalSeparator(key=K_SEP2)],
        [sg.Button('Run Selected', key=K_RUNSEL, button_color=('white', 'green')),
         sg.Button('Run All', key=K_RUNALL, button_color=('white', 'darkgreen')),
         sg.Button('Open Screenshots Folder', key=K_OPENSHOTS),
         sg.Button('Launch Compare GUI', key=K_COMPARE),
         sg.Exit(),
         sg.Text('', key=K_PASSCNT, font=('Helvetica', 16, 'bold'), text_color='lime green'),
         sg.Text('', key=K_FAILCNT, font=('Helvetica', 16, 'bold'), text_color='red')],
        [sg.ProgressBar(100, orientation='h', size=(50, 20), key=K_PBAR, visible=False),
         sg.Text('', key=K_PROGRESSTEXT, size=(30, 1))],
    ], expand_x=True, expand_y=True)

    bottom_pane = sg.Column([
        [sg.Text('Log:', font=('Helvetica', 10, 'bold'))],
        [sg.Multiline('', size=(80, 24), key=K_LOG, autoscroll=True, disabled=True,
                       font=('Courier', 9), background_color='black', text_color='lime', expand_y=True, expand_x=True)],
        [sg.Text('', key=K_SUMMARY, font=('Helvetica', 11, 'bold'))],
    ], expand_x=True, expand_y=True)

    layout = [
        [sg.Text('PySimpleGUI Snapshot Test Runner', font=('Helvetica', 14, 'bold')), sg.Text(f'v{VERSION}', font=('Helvetica', 11, 'bold'), text_color='spring green'),
         sg.Text(f'Run GUI: {sg.version}'),
         sg.Text('', key=K_TESTVER, size=(80, 1), font=('Helvetica', 10, 'bold'), text_color='#e8a54a')],
        [sg.Text(f'Found {len(scripts)} SNAP_*.py script(s) in the current folder.', font=('Helvetica', 9))],
        [sg.HorizontalSeparator()],
        [sg.Text('Root Folder:', size=(16, 1)), sg.Input(setting='', key=K_ROOT, size=(100, 1), enable_events=True), sg.FolderBrowse()],
        [sg.Text('Label (auto):', size=(16, 1)),
         sg.Input('', key=K_LABEL, size=(24, 1), readonly=True, text_color='#e8a54a', disabled_readonly_background_color='#1f1c18',
                  tooltip='<date>_<PySimpleGUI version under test> - set automatically'),
         sg.Text('Suffix:'), sg.Input('', key=K_SUFFIX, size=(10, 1), enable_events=True, tooltip='Optional, e.g. VarA for a variant run (not saved between sessions)'),
         sg.Text('', key=K_LABELPREVIEW, font=('Helvetica', 9), text_color='spring green')],
        [sg.Text('Test Python:', size=(16, 1)),
         sg.Input(sys.executable, key=K_PYTHON, size=(45, 1), enable_events=True), sg.FileBrowse(),
         sg.Text('interpreter of the venv with the release under test', font=('Helvetica', 8))],
        [sg.Text('PySimpleGUI Folder:', size=(16, 1)),
         sg.Input(setting='', key=K_SGFOLDER, size=(45, 1), enable_events=True), sg.FolderBrowse(),
         sg.Text('folder with the PySimpleGUI.py to test (blank = installed package)', font=('Helvetica', 8))],
        [sg.Text('Timeout per script (s):', size=(16, 1)), sg.Input('120', key=K_TIMEOUT, size=(8, 1))],
        [sg.HorizontalSeparator()],
        [sg.Pane([top_pane, bottom_pane], orientation='vertical', show_handle=True, handle_size=10, relief=sg.RELIEF_GROOVE, key=K_PANE, expand_x=True, expand_y=True)],
    ]

    window = sg.Window('RUN!  Snapshot Test Runner (GUI)', layout, finalize=True, resizable=(False,True), right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, auto_save_location=True, enable_close_attempted_event=True)

    count = psgdnd.enable(window) if hasattr(psgdnd, 'enable') else 0          # <-- the whole drag & drop integration (enable() is GitHub psgdnd 6.0.5+, not on PyPI yet)


    sg.cprint_set_output_destination(window, K_LOG)
    # Make the split obvious: wide amber sash, raised, resize cursor on hover, bigger grab handle
    window[K_PANE].PanedWindow.configure(sashwidth=8, sashrelief=sg.RELIEF_RAISED, bg='#c9852f', sashcursor='sb_v_double_arrow', showhandle=True, handlesize=14)

    # --- Repack rows so shrinking clips the FLEXIBLE element, never the fixed rows ---
    # tk clips last-packed widgets first.  So: anchor the must-stay-visible rows to the BOTTOM
    # first (reverse visual order), then repack the expanding row LAST so it alone absorbs all
    # grow/shrink.  Applied inside each half of the Pane.
    def repack_shrink_friendly(expand_elem, bottom_elems):
        """bottom_elems: fixed rows in top-to-bottom visual order; expand_elem's row absorbs all resize."""
        for elem in [expand_elem] + bottom_elems:
            elem.ParentRowFrame.pack_forget()
        for elem in reversed(bottom_elems):
            elem.ParentRowFrame.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        expand_elem.ParentRowFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    repack_shrink_friendly(window[K_SCRIPTCOL], [window[K_SEP2], window[K_RUNSEL], window[K_PBAR]])   # top: script list flexes; sep/buttons/progress pinned
    repack_shrink_friendly(window[K_LOG], [window[K_SUMMARY]])                                        # bottom: Multiline flexes; summary pinned

    running = False
    pass_count = 0
    fail_count = 0

    def append_log(text, color=None):
        sg.cprint(text, text_color=color)

    def set_all_checkboxes(value):
        for script in scripts:
            window[KT_CB(script)].update(value)

    def get_selected_scripts():
        return [s for s in scripts if window[KT_CB(s)].get()]

    test_version = [None]       # PySimpleGUI version from the latest "Under test" probe (None = not known yet)

    def refresh_label():
        """Auto label = <today>_<version under test>[_<suffix>], shown read-only in the Label field + the folder preview. Returns the label."""
        label = make_auto_label(test_version[0], window[K_SUFFIX].get())
        window[K_LABEL].update(label)
        window[K_LABELPREVIEW].update(f'-> will save to: {screenshots_dir_for_label(label, window[K_ROOT].get())}' if label else '-> waiting for the version under test...')
        return label

    probe_seq = [0]

    def start_version_probe():
        python_exe = window[K_PYTHON].get().strip() or sys.executable
        sg_folder = window[K_SGFOLDER].get().strip()
        probe_seq[0] += 1
        test_version[0] = None
        refresh_label()
        if not os.path.isfile(python_exe):
            window[K_TESTVER].update('Under test: ?  (Test Python not found)')
            return
        window[K_TESTVER].update('Under test: checking...')
        threading.Thread(target=probe_test_version, args=(python_exe, sg_folder, window, probe_seq[0]), daemon=True).start()

    start_version_probe()

    def start_run(script_list, values):
        nonlocal running, pass_count, fail_count
        if running:
            sg.popup_quick_message('A run is already in progress - please wait for it to finish.')
            return
        if not script_list:
            sg.popup_error('No scripts selected. Check at least one box, or use "Select All".')
            return
        python_exe = values[K_PYTHON].strip() or sys.executable
        if not os.path.isfile(python_exe):
            sg.popup_error(f'Test Python interpreter not found:\n{python_exe}')
            return
        sg_folder = values[K_SGFOLDER].strip()
        if sg_folder and not os.path.isfile(os.path.join(sg_folder, 'PySimpleGUI.py')):
            sg.popup_error(f'PySimpleGUI.py not found in folder:\n{sg_folder}')
            return
        try:
            timeout = float(values[K_TIMEOUT])
        except ValueError:
            sg.popup_error('Timeout must be a number of seconds, e.g. 120')
            return
        # Auto label: re-probe the version NOW (catches a PySimpleGUI.py edited since the last probe); date = today
        probe_seq[0] += 1                       # any background probe still in flight is now stale
        window[K_TESTVER].update('Under test: checking...')
        window.refresh()
        test_version[0], testver_text = get_test_version(python_exe, sg_folder)
        window[K_TESTVER].update(testver_text)
        label_value = refresh_label()
        if not label_value:
            sg.popup_error(f'Could not read the PySimpleGUI version under test - the auto label needs it.\n\n{testver_text}')
            return
        output_dir = screenshots_dir_for_label(label_value, values[K_ROOT])
        emptied = False
        if os.path.isdir(output_dir) and os.listdir(output_dir):      # same version already run today -> ask before mixing two runs in one folder
            choice = ask_empty_folder(output_dir)
            if choice is None:
                return
            if choice == K_EMPTY:
                err = empty_results_folder(output_dir)
                if err:
                    sg.popup_error(err)
                    return
                emptied = True
        running = True
        for s in scripts:
            window[KT_STATUS(s)].update('')
        window[K_LOG].update('')
        window[K_PBAR].update(visible=True, current_count=0)
        window[K_RUNSEL].update(disabled=True)
        window[K_RUNALL].update(disabled=True)
        window[K_SUMMARY].update('')
        pass_count = 0
        fail_count = 0
        window[K_PASSCNT].update('Passed: 0')
        window[K_FAILCNT].update('Failed: 0')
        if emptied:
            append_log('Emptied the results folder first (earlier run of this label removed)')
        append_log(f'Saving screenshots to: {os.path.abspath(output_dir)}')
        append_log(f'Test interpreter: {python_exe}')
        if sg_folder:
            append_log(f'PySimpleGUI override: {os.path.join(sg_folder, "PySimpleGUI.py")}')
        stop_on_failure = window[K_STOPONFAIL].get()
        t = threading.Thread(target=run_scripts_worker,
                             args=(script_list, stop_on_failure, output_dir, python_exe, timeout, label_value, sg_folder, window),
                             daemon=True)
        t.start()

    output_dir = None

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSE_ATTEMPTED_EVENT, sg.WIN_CLOSED, 'Exit'):
            if event != sg.WIN_CLOSED:
                window.settings_save(values)
            if output_dir:
                with open(Path(output_dir)/'log.txt', 'w') as f:
                    f.writelines(window[K_LOG].get())
            break

        if event in (K_SUFFIX, K_ROOT):
            refresh_label()

        if event in (K_PYTHON, K_SGFOLDER):
            start_version_probe()

        if event == K_TESTVER_RESULT:
            seq, text, version = values[event]
            if seq == probe_seq[0]:
                window[K_TESTVER].update(text)
                test_version[0] = version
                refresh_label()

        if event == K_SELALL:
            set_all_checkboxes(True)

        if event == K_SELNONE:
            set_all_checkboxes(False)

        if event == K_RUNSEL:
            start_run(get_selected_scripts(), values)

        if event == K_RUNALL:
            set_all_checkboxes(True)
            start_run(scripts, values)

        if event == K_COMPARE:
            compare_path = Path(os.path.dirname(__file__))
            py_file = r'compare_screenshots_gui.py'
            sg.execute_py_file(str(compare_path/py_file), cwd=compare_path)
        if isinstance(event, tuple) and event[0] == K_RUNONE:      # per-script buttons use tuple keys: (K_RUNONE, script)
            script = event[1]
            start_run([script], values)

        if isinstance(event, tuple) and event[0] == K_VIEW:
            script = event[1]
            python_exe = values[K_PYTHON].strip() or sys.executable
            if not os.path.isfile(python_exe):
                sg.popup_error(f'Test Python interpreter not found:\n{python_exe}')
            else:
                env = os.environ.copy()
                env['SNAP_INTERACTIVE'] = '1'
                sg_folder = values[K_SGFOLDER].strip()
                if sg_folder:
                    env['PYTHONPATH'] = sg_folder + os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else sg_folder
                # Fire and forget - no timeout, no pass/fail, no manifest.
                # The script blocks in window.read() until the user closes it.
                subprocess.Popen([python_exe, script], env=env)
                append_log(f'--- Viewing {script} interactively (no screenshot) - close its window when done ---')

        if isinstance(event, tuple) and event[0] == K_EDIT:
            script = event[1]
            sg.execute_editor(os.path.abspath(script))

        if event == K_OPENSHOTS:
            target_dir = screenshots_dir_for_label(values[K_LABEL], values[K_ROOT])
            if os.path.isdir(target_dir):
                open_in_file_manager(os.path.abspath(target_dir))
            else:
                sg.popup_error(f'Screenshots folder does not exist yet: {target_dir}\nRun at least one script first.')

        if event == K_SCRIPT_START:
            script, i, total = values[event]
            append_log(f'--- [{i}/{total}] Running {script} ---', color='yellow')
            window[KT_STATUS(script)].update('running...', text_color='orange')
            window[K_PROGRESSTEXT].update(f'{i}/{total}: {script}')
            pct = int(((i - 1) / total) * 100) if total else 0
            window[K_PBAR].update(current_count=pct)
            # Auto-scroll the script list so the running row stays visible.
            # Position by the script's row in the FULL displayed list (not its
            # index within this run), so Run Only / subsets don't jump to top.
            try:
                row = scripts.index(script)
                frac = max(0.0, row / len(scripts) - 0.15) if scripts else 0.0
                window[K_SCRIPTCOL].Widget.canvas.yview_moveto(frac)
            except Exception:
                pass   # never let a scroll hiccup break the run

        if event == K_LOG:
            append_log(values[event])

        if event == K_SCRIPT_DONE:
            script, success, i, total = values[event]
            if success:
                window[KT_STATUS(script)].update('OK', text_color='green')
                pass_count += 1
            else:
                window[KT_STATUS(script)].update('FAILED', text_color='red')
                fail_count += 1
            window[K_PASSCNT].update(f'Passed: {pass_count}')
            window[K_FAILCNT].update(f'Failed: {fail_count}')
            pct = int((i / total) * 100) if total else 100
            window[K_PBAR].update(current_count=pct)

        if event == K_ALL_DONE:
            results, output_dir = values[event]
            running = False
            window[K_PBAR].update(visible=False)
            window[K_RUNSEL].update(disabled=False)
            window[K_RUNALL].update(disabled=False)
            ok_count = sum(1 for _, success in results if success)
            n_fail = len(results) - ok_count
            window[K_SUMMARY].update(
                f'Completed: {ok_count} succeeded, {n_fail} failed, {len(results)} total. '
                f'Saved to: {os.path.abspath(output_dir)}'
            )
            append_log(f'=== Run complete: {ok_count} succeeded, {n_fail} failed ===')
            append_log(f'=== Screenshots saved to: {os.path.abspath(output_dir)} ===')
            if n_fail == 0:
                sg.popup_quick_message('All selected scripts ran successfully!', font=('Helvetica', 14))
            else:
                sg.popup_quick_message(f'{n_fail} script(s) failed - check the log for details.', font=('Helvetica', 14))

        if event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), location=window.current_location(use_anchor=sg.WIN_ANCHOR_CENTER), location_anchor=sg.WIN_ANCHOR_CENTER, keep_on_top=True, non_blocking=True)

    window.close()


if __name__ == '__main__':
    main()