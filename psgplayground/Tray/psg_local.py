"""
psg_local.py - make EVERY program run by a Python interpreter import your LOCAL PySimpleGUI (no PYTHONPATH needed)

    python psg_local.py              status - which PySimpleGUI this interpreter imports
    python psg_local.py on [folder]  use the local copy   (default folder: D:\\python\\GitHub\\PySimpleGUI)
    python psg_local.py off          back to the pip-installed copy

Run it with EACH interpreter you want switched (launcher, .pyw double-click and PyCharm all use these):
    D:\\python\\Python312\\python.exe  D:\\Dropbox\\2026_Tools\\psg_tools\\psg_local.py on
    D:\\python\\pypy3.12-v8.0.0-win64\\pypy.exe  D:\\Dropbox\\2026_Tools\\psg_tools\\psg_local.py on

[folder] = the repo folder that holds the PySimpleGUI package folder (or that package folder itself).

How it works: writes psg_local.pth into the interpreter's site-packages.  Python runs a .pth "import" line at
every startup; this one puts the repo folder on sys.path just AHEAD of site-packages, so `import PySimpleGUI`
finds the repo's PySimpleGUI package before the pip-installed one.
- PYTHONPATH entries still come first, so the regression runner's "PySimpleGUI Folder" override keeps working.
- Repo folder missing (D: not mounted) -> Python silently falls back to the pip-installed copy.
- This script never imports PySimpleGUI, so it still works when the local copy is broken mid-edit.
- .pth "import" lines are deprecated from Python 3.15 but still run through 3.17.

CHANGE LOG (newest first, 1 line per change):
2026-10-29  v1.1  Status now names the PySimpleGUI.py file itself (not the package __init__.py)
2026-10-29  v1.0  First version: on / off / status, venv-aware, user-site fallback, verifies with a fresh interpreter
"""
import os
import site
import subprocess
import sys
import sysconfig
import tempfile

VERSION = '1.1'
DEFAULT_FOLDER = r'D:\python\GitHub\PySimpleGUI'
PTH_NAME = 'psg_local.pth'
PROBE = "import PySimpleGUI as sg, types; m = getattr(sg, 'PySimpleGUI', sg); print(sg.version); print(m.__file__ if isinstance(m, types.ModuleType) else sg.__file__)"


def pth_text(folder):
    """The .pth contents: a comment + ONE import line (a .pth import line must be a single line)."""
    return ('# Written by psg_local.py - programs on this interpreter import the LOCAL PySimpleGUI from the folder below.\n'
            '# Delete this file (or run: psg_local.py off) to go back to the pip-installed copy.\n'
            "import sys; sys.path.insert([s.lower().rstrip('\\\\/').endswith(('site-packages', 'dist-packages')) for s in sys.path + ['site-packages']]"
            f".index(True), {folder!r})\n")


def site_dirs():
    """(this interpreter's site-packages, the user site-packages or None) - in a venv only the venv's own one is used."""
    in_venv = sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
    user = None if in_venv or not site.ENABLE_USER_SITE else site.getusersitepackages()
    return sysconfig.get_paths()['purelib'], user


def find_pths():
    return [os.path.join(d, PTH_NAME) for d in site_dirs() if d and os.path.isfile(os.path.join(d, PTH_NAME))]


def probe():
    """What a freshly started program on this interpreter imports - run from a neutral folder so no local file can shadow it."""
    try:
        r = subprocess.run([sys.executable, '-c', PROBE], capture_output=True, text=True, timeout=60, cwd=tempfile.gettempdir())
        out = r.stdout.strip().splitlines()
        if r.returncode == 0 and len(out) >= 2:
            return out[0], out[1]
        return None, (r.stderr.strip().splitlines() or ['import failed'])[-1]
    except Exception as e:
        return None, str(e)


def normalize_folder(folder):
    """Accepts the repo folder (holds PySimpleGUI\\__init__.py) or the package folder itself; returns the repo folder or None."""
    folder = os.path.abspath(folder)
    if os.path.isfile(os.path.join(folder, 'PySimpleGUI', '__init__.py')):
        return folder
    if os.path.basename(folder).lower() == 'pysimplegui' and os.path.isfile(os.path.join(folder, '__init__.py')):
        return os.path.dirname(folder)
    return None


def report(title):
    version, where = probe()
    pths = find_pths()
    print(f'\n{title}')
    print(f'  Interpreter : {sys.executable}  (Python {sys.version.split()[0]})')
    print(f'  Switch file : {pths[0] if pths else "none - using the pip-installed copy"}')
    print(f'  Imports     : PySimpleGUI {version}  from  {where}' if version else f'  Imports     : FAILED - {where}')
    return version, where


def switch_on(folder):
    repo = normalize_folder(folder)
    if repo is None:
        sys.exit(f'No PySimpleGUI package found in:\n  {folder}\nPass the repo folder that holds PySimpleGUI\\__init__.py')
    for old in find_pths():                         # only ever one switch file per interpreter
        os.remove(old)
    main_dir, user_dir = site_dirs()
    for target in (main_dir, user_dir):
        if not target:
            continue
        try:
            os.makedirs(target, exist_ok=True)
            with open(os.path.join(target, PTH_NAME), 'w', encoding='utf-8') as f:
                f.write(pth_text(repo))
            break
        except OSError as e:
            print(f'  (could not write {target}: {e})')
    else:
        sys.exit('Could not write the switch file - run this from an admin prompt, or use a per-user Python')
    version, where = report('LOCAL copy switched ON')
    ok = version and os.path.normcase(os.path.abspath(where)).startswith(os.path.normcase(repo + os.sep))
    print('  Result      : OK - every program on this interpreter now uses the local copy' if ok else
          '  Result      : WARNING - still not importing the local copy (is PYTHONPATH set, or a PySimpleGUI.py next to the program?)')


def switch_off():
    removed = find_pths()
    for p in removed:
        os.remove(p)
    report('LOCAL copy switched OFF' if removed else 'Was already off')


def main():
    args = sys.argv[1:]
    cmd = args[0].lower() if args else 'status'
    if cmd == 'on':
        switch_on(args[1] if len(args) > 1 else DEFAULT_FOLDER)
    elif cmd == 'off':
        switch_off()
    elif cmd == 'status':
        report(f'psg_local.py v{VERSION} - status')
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
