"""
pip_refresh.pyw  -  Pip Refresh: keeps your pip packages fresh from GitHub and PyPI.        (was MiniLauncherPipInstaller.pyw, then Pip Fresh)

    A desktop widget that lists your packages with the version installed on this PC beside the latest release on PyPI and the newest version on GitHub.
    Click a row to pick what to install: GitHub's newest (its zipball - no git needed) or any release on PyPI, each listed with its date.

    The widget:  one rounded card (Toybox palette, or 31 other dark and light themes), no title bar, see-through corners (Windows - square on
        Linux / Mac), drag it anywhere.
        columns:    PACKAGE     INSTALLED (version on this PC)     PYPI (latest release)     GITHUB (newest version on GitHub)     status
        versions:   amber = newer than the one installed     — = not on PyPI / no GitHub repo set     red ? = couldn't be read (hover the row to see why)
        status:     green check = current   amber arrow = update   blue + = not installed   dots = checking   red ! = no version found on GitHub or PyPI
        hover a row and the bottom line says what a click will do.   gear (top right) = Settings,  x = close  (Escape too)
        Versions are checked when it starts, every hour, and from the right-click menu (Check now).
    The picker (click a row):  GitHub's newest at the top, then every PyPI release, newest first, with the date it was uploaded - the installed one and
        PyPI's latest are marked, yanked releases dimmed.  The button says what picking one will do (Install / Upgrade / Downgrade / Reinstall) and the
        pip command is shown under the list.  Enter or a double-click installs, Escape closes.  It checks its package again as it opens.
    Settings:  the package list, laid out like PSG Dock's settings - + Add, - Delete, Clear all, check All / None, drag the grip to reorder,
        OK / Apply / Cancel.  Each entry is a pip package name, its GitHub repo (owner/repo) and the branch.  Paste a GitHub link into the repo
        box and it is split into repo + branch for you; with psgdnd installed you can also drop a link from your browser onto an entry or the list.
        Leave the repo empty for a package that is only on PyPI.
    Right-click:  Check now | Settings... | Keep on top | Theme (16 dark + 16 light) | Brightness... | Size | Opacity | Edit Me / Version / Exit   (remembered)
        Brightness... opens a slider under the card: any theme darker (down to -80%) or lighter (+50%), the card changing as you drag.

    Where the versions come from:  installed = importlib.metadata (pip's direct_url.json says where it came from);  GitHub = the version= line of
        setup.py (or pyproject.toml) on that branch;  PyPI = pypi.org/pypi/<name>/json (the latest release, and every release with its upload date).
    The installs:  GitHub:  python -m pip install --upgrade --no-cache-dir https://github.com/<owner/repo>/zipball/<branch>
                   PyPI:    python -m pip install --upgrade --no-cache-dir <name>==<version>
        --upgrade alone reinstalls a zipball; --force-reinstall would also reinstall every dependency from PyPI.  The same PyPI version again (say
        GitHub's build of 6.1 -> PyPI's 6.1) adds --force-reinstall --no-deps, so only that package is replaced.
    --demo on the command line shows made-up versions and installs nothing (for trying it out).

    Requires:  pip install PySimpleGUI pillow          optional:  psgdnd  (drop GitHub links onto the Settings window)

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v2.0.9  Claude: Linux: the Settings window can no longer jump away while an entry is dragged (grab-anywhere is off during the drag)
2026-11-02  v2.0.8  Claude: fixed 'A version check crashed' (KeyError in importlib.invalidate_caches) - the check threads now take turns calling it
2026-11-02  v2.0.7  Claude: Linux / Mac: square corners - only Windows can make them see-through, elsewhere they showed black; the Brightness panel too
2026-11-01  v2.0.6  Claude: Brightness... in the right-click menu - a slider makes any theme darker (down to -80%) or lighter (+50%), the card changing
                    as you drag
2026-11-01  v2.0.5  Claude: PYPI column (latest release on PyPI); click a row for a picker - GitHub's newest and every PyPI release with its date - with
                    an Install / Upgrade / Downgrade / Reinstall button; a package with no GitHub repo works from PyPI alone
2026-11-01  v2.0.4  Claude: 32 themes - 16 dark (now colorful) and 16 light - as two columns of bigger color chips in the Theme menu;
                    renamed themes carry over
2026-11-01  v2.0.3  Claude: 16 themes, 8 dark + 8 light (was 4), a swatch beside each in the Theme menu; the widget's menu takes the card's colors;
                    status colors darker on every light card (was Paper only)
2026-11-01  v2.0.2  Claude: Settings window no wider than its entries - the status bar showed the whole settings path at a fixed width and the
                    OK / Apply / Cancel buttons had a fixed size; the path is now in the file name's tooltip
2026-11-01  v2.0.1  Claude: renamed Pip Refresh (pip_refresh.pyw; Pip Fresh's settings are taken over); column headings PACKAGE / INSTALLED / GITHUB
                    instead of the '>' between the versions, which read like 'greater than'; hints and the install question name both versions
2026-11-01  v2.0.0  Claude: renamed Pip Fresh with its own icon, rebuilt as a Toybox-style card widget; the package list moved out of the code into a
                    PSG Dock-style Settings window; versions checked in background threads; Alt+F4 no longer crashes it
2026-11-01  v1.0.1  No more force_reinstall: it reinstalled every dependency from PyPI (PySimpleGUI 6.3.19 -> 6.3.0.1). --upgrade alone reinstalls a zipball
"""
import importlib
import importlib.metadata
import base64
import io
import json
import math
import os
import random
import shutil
import re
import sys
import threading
import time
import tkinter as tk
import traceback
import urllib.error
import urllib.request

import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont

try:
    import psgdnd                                                  # optional - drop GitHub links onto the Settings window
except Exception:
    psgdnd = None

VERSION = '2.0.9'
APP_NAME = 'Pip Refresh'
SETTINGS_FILE = 'pip_refresh.json'
OLD_APP_NAME, OLD_SETTINGS_FILE = 'Pip Fresh', 'pip_fresh.json'          # its name for the morning of 1-Nov-2026
DEMO = '--demo' in sys.argv
CHECK_EVERY_MS = 60 * 60 * 1000                                    # automatic version check every hour
CACHE_LOCK = threading.Lock()                                      # one thread at a time in importlib.invalidate_caches() - see local_version()
ICON = b'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'

DEFAULT_PACKAGES = [{'name': 'PySimpleGUI', 'repo': 'PySimpleGUI/PySimpleGUI', 'branch': 'master'},
                    {'name': 'psgdnd', 'repo': 'PySimpleGUI/psgdnd', 'branch': 'main'},
                    {'name': 'psgfiglet', 'repo': 'PySimpleGUI/psgfiglet', 'branch': 'main'},
                    {'name': 'psgdemos', 'repo': 'PySimpleGUI/psgdemos', 'branch': 'main'},
                    {'name': 'psg_pillow', 'repo': 'PySimpleGUI/psg_pillow', 'branch': 'main'},
                    {'name': 'psghotkey', 'repo': 'PySimpleGUI/psghotkey', 'branch': 'main'}]
# --demo:  per package (installed, installed from, GitHub, PyPI), and its PyPI releases with their dates
DEMO_VERSIONS = {'pysimplegui': ('6.3.19', 'GitHub', '6.4', '6.3.0.1'), 'psgdnd': ('6.1', 'GitHub', '6.1', '6.1'), 'psgfiglet': ('6.1', 'PyPI', '6.1', '6.1'),
                 'psgdemos': (None, None, '6.0', '6.0'), 'psg-pillow': ('1.2', 'GitHub', '1.3', None), 'psghotkey': ('6.0.2', 'PyPI', '6.1', '6.0.2')}
DEMO_RELEASES = {'pysimplegui': '6.3.0.1:2026-08-16 6.3:2026-08-02 6.2:2026-06-17 6.0:2026-04-14 5.0.8.3:2025-04-02:yanked 5.0.8.2:2025-03-12:yanked 4.60.5.1:2026-04-03',
                 'psgdnd': '6.1:2026-11-01 6.0.4:2026-06-22 6.0.1:2026-06-17', 'psgfiglet': '6.1:2026-06-17 6.0:2026-04-10 5.0.0:2024-02-13 1.21.0:2022-01-02',
                 'psgdemos': '6.0:2026-04-10 5.1.1:2024-04-08 5.1.0:2024-04-08 5.0.0:2024-02-23', 'psghotkey': '6.0.2:2026-04-12 6.0:2026-04-12 5.0.0:2024-02-26'}

# ---------- Keys: the widget ----------
K_IMAGE = '-IMAGE-'
K_HOVER = '-HOVER-'                   # the mouse moved onto a different part of the card   value: ('row', i) | 'gear' | 'close' | None
K_CLICK = '-CLICK-'                   # a click (not a drag) on a part of the card            value: same as K_HOVER
K_VERSION = '-VERSION-'               # a version-check thread finished one package           value: (generation, package key, versions() dict)
K_THREAD_ERROR = '-THREAD ERROR-'     # a thread crashed                                       value: the traceback text
K_CHECK = '-CHECK-'                   # check all versions now (right-click menu and the hourly timer)
K_SETTINGS = '-SETTINGS-'             # open the Settings window (right-click menu)
K_TOP = '-TOP-'                       # keep on top toggle, also its settings-file entry
K_THEME = '-THEME-'                   # settings-file entry, and the prefix of the theme menu keys
KT_THEME = lambda name: f'{K_THEME}{name}'
K_SIZE = '-SIZE-'
KT_SIZE = lambda name: f'{K_SIZE}{name}'
K_OPACITY = '-OPACITY-'
KT_OPACITY = lambda pct: f'{K_OPACITY}{pct}'
K_PACKAGES = '-PACKAGES-'             # settings-file entry: the package list, [{'name', 'repo', 'branch'}, ...]
K_EXIT = 'Exit'

# ---------- Keys: the Settings window ----------
K_LIST = '-LIST-'                     # the scrolling column of entries
K_ENTRY = '-ENTRY-'
KT_ENTRY = lambda num: (K_ENTRY, num)     # an entry's frame
K_GRIP = '-GRIP-'
KT_GRIP = lambda num: (K_GRIP, num)       # the drag handle
K_NAME = '-NAME-'
KT_NAME = lambda num: (K_NAME, num)
K_REPO = '-REPO-'
KT_REPO = lambda num: (K_REPO, num)
K_BRANCH = '-BRANCH-'
KT_BRANCH = lambda num: (K_BRANCH, num)
K_URL = '-URL-'
KT_URL = lambda num: (K_URL, num)         # the install command shown under the entry
K_CBOX = '-CBOX-'
KT_CBOX = lambda num: (K_CBOX, num)
K_DEL = '-DEL-'
KT_DEL = lambda num: (K_DEL, num)
K_ADD = '-ADD-'
K_DELETE = '-DELETE-'
K_CLEAR = '-CLEAR-'
K_SEL_ALL = '-SELECT ALL-'
K_SEL_NONE = '-SELECT NONE-'
K_OK = '-OK-'
K_APPLY = '-APPLY-'
K_CANCEL = '-CANCEL-'
K_STRIP_CLOSE = '-STRIP CLOSE-'
K_STATUS = '-STATUS-'
K_PAGE_UP, K_PAGE_DOWN, K_HOME, K_END = '-PAGE UP-', '-PAGE DOWN-', '-HOME-', '-END-'
K_DRAG_PRESS = '-DRAG PRESS-'         # from the grip's mouse bindings   value: (entry num, x_root, y_root)
K_DRAG_MOTION = '-DRAG MOTION-'
K_DRAG_RELEASE = '-DRAG RELEASE-'

# ---------- Keys: the release picker ----------
K_PICK_TABLE = '-PICK TABLE-'         # the versions to choose from
K_PICK_INFO = '-PICK INFO-'           # what is installed now
K_PICK_STATUS = '-PICK STATUS-'       # 'checking...' while the picker checks its package again
K_PICK_CMD = '-PICK CMD-'             # the pip command the button will run
K_PICK_GO = '-PICK GO-'               # Install / Upgrade / Downgrade / Reinstall   (Enter, double-click a row)

# ---------- Look (Toybox palette) ----------
TRANSPARENT = '#010203'               # window color key: every pixel this color is see-through and click-through (the rounded corners)
SEE_THROUGH = sg.running_windows()    # only Windows can make those corners see-through - Linux / Mac get square corners instead of black ones
# --- WIDGET THEMES: the same block in every card widget (master copy in modern_widget_recipe.md) - change it in all of them at once ---
# card = background, border = outline, track = gauge track / lines, text = main text, dim = labels.   16 dark first, then 16 light: the Theme menu
# shows them as two columns of color chips.  ForestFloor and CrimsonVelvet come from Mike's dark themes; the other colored darks follow their lead.
THEMES = {'Toybox':        {'card': '#141821', 'border': '#2f3a4e', 'track': '#1e2430', 'text': '#e6eaf2', 'dim': '#8a93a3'},
          'Carbon':        {'card': '#121212', 'border': '#2e2e2e', 'track': '#1f1f1f', 'text': '#e0e0e0', 'dim': '#8c8c8c'},
          'Slate':         {'card': '#2a3140', 'border': '#48526a', 'track': '#363e50', 'text': '#eef1f6', 'dim': '#a3acbd'},
          'CrimsonVelvet': {'card': '#5e0d1f', 'border': '#8f1530', 'track': '#781429', 'text': '#f9d276', 'dim': '#d6a7a0'},
          'Ember':         {'card': '#451f11', 'border': '#773c27', 'track': '#5c2f1e', 'text': '#f1e4df', 'dim': '#bd9f93'},
          'Espresso':      {'card': '#2c2016', 'border': '#594331', 'track': '#423224', 'text': '#f1e7df', 'dim': '#bda693'},
          'Bronze':        {'card': '#48310f', 'border': '#7b5823', 'track': '#60441b', 'text': '#f1eadf', 'dim': '#bdac93'},
          'Olive':         {'card': '#2a3013', 'border': '#545f2b', 'track': '#3e4620', 'text': '#eef1df', 'dim': '#b5bd93'},
          'ForestFloor':   {'card': '#101c0e', 'border': '#2a4424', 'track': '#1b2e18', 'text': '#d0e0c8', 'dim': '#83977d'},
          'Jade':          {'card': '#113124', 'border': '#29614a', 'track': '#1e4836', 'text': '#dff1ea', 'dim': '#93bdac'},
          'Lagoon':        {'card': '#0e3434', 'border': '#236767', 'track': '#1a4c4c', 'text': '#dff1f1', 'dim': '#93bdbd'},
          'Petrol':        {'card': '#0f303e', 'border': '#235a71', 'track': '#1b4456', 'text': '#dfecf1', 'dim': '#93b1bd'},
          'Cobalt':        {'card': '#132949', 'border': '#294a7a', 'track': '#20395f', 'text': '#dfe6f1', 'dim': '#93a4bd'},
          'Indigo':        {'card': '#1e1e48', 'border': '#383876', 'track': '#2c2c5d', 'text': '#dfdff1', 'dim': '#9393bd'},
          'Plum':          {'card': '#341c3f', 'border': '#5a376c', 'track': '#472b54', 'text': '#ebdff1', 'dim': '#af93bd'},
          'Mulberry':      {'card': '#3f1731', 'border': '#6e3057', 'track': '#552544', 'text': '#f1dfea', 'dim': '#bd93ae'},
          'Paper':         {'card': '#f5f7fb', 'border': '#c9d1dc', 'track': '#dadfe8', 'text': '#1b2130', 'dim': '#5c6676'},
          'Fog':           {'card': '#dde2e8', 'border': '#b8c0ca', 'track': '#c5ccd5', 'text': '#1b2028', 'dim': '#545d69'},
          'Stone':         {'card': '#e1dedb', 'border': '#b9b5b1', 'track': '#c5c2be', 'text': '#2b2117', 'dim': '#63574b'},
          'Sand':          {'card': '#e7dfcf', 'border': '#c1b6a4', 'track': '#cbc2b3', 'text': '#2b2417', 'dim': '#675942'},
          'Linen':         {'card': '#f7f2e8', 'border': '#dcd1bd', 'track': '#e4dac9', 'text': '#2b2620', 'dim': '#73685a'},
          'Butter':        {'card': '#fbf5dc', 'border': '#e3d7a6', 'track': '#e8ddb1', 'text': '#2e2a18', 'dim': '#766c4c'},
          'Peach':         {'card': '#fce9df', 'border': '#dfbdaa', 'track': '#e6ccbc', 'text': '#2b1e17', 'dim': '#705d51'},
          'Blush':         {'card': '#faedf0', 'border': '#eccad2', 'track': '#efd1d8', 'text': '#321c22', 'dim': '#80606a'},
          'Rose':          {'card': '#ecd5dd', 'border': '#c7a9b3', 'track': '#d1b8c0', 'text': '#2b171e', 'dim': '#70515c'},
          'Orchid':        {'card': '#f4e5f5', 'border': '#d1b6d3', 'track': '#dbc6dc', 'text': '#2a172b', 'dim': '#6e5170'},
          'Lavender':      {'card': '#f0ecfa', 'border': '#d2c9ec', 'track': '#dad3f0', 'text': '#231e33', 'dim': '#665e80'},
          'Periwinkle':    {'card': '#e3e6f7', 'border': '#b2b7d6', 'track': '#c3c7df', 'text': '#171a2b', 'dim': '#515670'},
          'Sky':           {'card': '#e7f0fa', 'border': '#bdd2ea', 'track': '#c7daee', 'text': '#18222f', 'dim': '#53667d'},
          'Aqua':          {'card': '#ddf2f3', 'border': '#aecfd0', 'track': '#bfd9d9', 'text': '#172a2b', 'dim': '#516f70'},
          'Mint':          {'card': '#e8f5ee', 'border': '#bcdccb', 'track': '#c5e1d2', 'text': '#1b2a22', 'dim': '#557064'},
          'Pistachio':     {'card': '#ebf3dd', 'border': '#c4cfaf', 'track': '#cfd9bf', 'text': '#242b17', 'dim': '#657051'}}
OLD_THEME_NAMES = {'Midnight': 'Carbon', 'VoidBlue': 'Carbon', 'DarkSlate': 'Slate', 'MidnightPurple': 'Plum', 'DeepOceanTeal': 'Lagoon'}   # saved by older versions
# --- end WIDGET THEMES ---
STATE_COLORS = {'current': '#2ecc71', 'update': '#e8a33d', 'missing': '#1e9bff', 'error': '#ff6b6b'}
C_CLOSE = '#c0392b'
C_MENU_BG, C_MENU_TEXT, C_MENU_SEL = '#1b2130', '#e6eaf0', '#2a62a8'          # right-click menus: Toybox strip color, light text, blue highlight (widget menu: menu_colors())
C_SWATCH_EDGE = '#7c8594'             # outline of the theme swatches in the Theme menu - mid gray shows on dark and light menus
FONT_MENU = ('Segoe UI', 10)
SIZES = {'Small': 0.8, 'Medium': 1.0, 'Large': 1.3}
OPACITIES = (100, 90, 80, 70, 60)
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # bold / regular: Windows first, then Linux

# card geometry in design pixels (96 dpi, Medium); everything is multiplied by the scale when drawn
CARD_W, RADIUS = 430, 18
HEAD_H, COLS_H, ROW_H, FOOT_H = 42, 22, 30, 34                     # title strip, column headings, one package row, bottom line
ROW_TOP = HEAD_H + COLS_H + 2
GEAR_X, CLOSE_X, BTN_Y, BTN_R = CARD_W - 47, CARD_W - 20, 21, 11
COL_LOCAL_R, COL_PYPI_R, COL_GITHUB_R, COL_STATE = CARD_W - 202, CARD_W - 124, CARD_W - 46, CARD_W - 25    # right edges of INSTALLED, PYPI, GITHUB; status disc

# Settings window (PySimpleGUI elements in the Toybox dark theme)
TOYBOX_DARK = {'BACKGROUND': '#141821', 'TEXT': '#d6dbe5', 'INPUT': '#1e2430', 'TEXT_INPUT': '#e6eaf2', 'SCROLL': '#1e2430', 'BUTTON': ('#ffffff', '#2a62a8'),
               'PROGRESS': ('#1e9bff', '#1e2430'), 'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}
C_STRIP, C_STRIP_TEXT, C_UI_DIM, C_UI_FAINT = '#1b2130', '#e6eaf0', '#8a93a3', '#5c6676'
C_ENTRY_BORDER, C_ENTRY_CHECKED, C_DRAG_OUTLINE, C_SLOT, C_SLOT_OUTLINE = '#2f3a4e', '#1e9bff', '#e8a33d', '#232a38', '#48526a'
COLOR_SAVE, COLOR_SAVE_DIRTY, COLOR_DANGER, COLOR_DIRTY_TEXT = 'white on #2e7d32', 'black on #ffc107', 'white on #b71c1c', '#ffc107'
LIST_HEIGHT = 470
PICK_ROWS = 10                        # rows the release picker shows before it scrolls
DRAG_START = 6                        # pixels the mouse moves before a press on the grip becomes a drag
AUTOSCROLL_EDGE = 30                  # dragging this close to the list's top / bottom scrolls it


class G:                              # program-wide state (the widget)
    window = None
    packages = []                     # [{'name', 'repo', 'branch'}, ...] in display order
    status = {}                       # package key -> what versions() found: local, source, github, reason, pypi, releases, pypi_reason (PENDING till then)
    generation = 0                    # bumped by every check, so late answers from an older check are ignored
    checked_at = None                 # 'HH:MM' of the last complete check
    hover = None                      # part of the card under the mouse
    press = None                      # (x, y, part) where the left button went down
    hits = []                         # [(x0, y0, x1, y1, part)] in design pixels, filled by render()
    scale = 1.0                       # screen dpi / 96 times the Size multiplier
    size_name = 'Medium'
    theme = 'Toybox'
    opacity = 90
    on_top = False
    fonts = {}                        # (bold, px) -> ImageFont
    swatches = {}                     # (theme name, brightness) -> tk.PhotoImage shown in the Theme menu
    bright = 0                        # Brightness: -80 (much darker) .. 50 (lighter), 0 = the theme as designed
    tuned = {}                        # (theme name, brightness) -> the theme's colors at that brightness


# ======================================================================================================================================================
#   Packages and versions
# ======================================================================================================================================================
PENDING = {'pending': True, 'local': None, 'source': None, 'github': None, 'reason': None, 'pypi': None, 'releases': [], 'pypi_reason': None}   # until checked


def pkg_key(name):
    """pip treats PySimpleGUI / pysimplegui and psg_pillow / psg-pillow as the same package"""
    return re.sub(r'[-_.]+', '-', name.strip()).lower()


def zip_url(p):
    return f'https://github.com/{p["repo"]}/zipball/{p["branch"] or "main"}'


def version_key(v):
    """A version as something that compares right: (numbers, 0 = pre-release like 6.4rc1 / 6.4.dev2 - below 6.4, 1 = release, 2 = post-release).
       Trailing zeros dropped, so 6.3 == 6.3.0.  () if there's no version in it"""
    m = re.match(r'\s*v?(\d+(?:\.\d+)*)(.*)', v or '')
    if not m:
        return ()
    nums, rest = [int(x) for x in m.group(1).split('.')], m.group(2).lower().split('+')[0]          # +local is ignored
    while len(nums) > 1 and nums[-1] == 0:
        nums.pop()
    return tuple(nums), 2 if 'post' in rest else 0 if rest.strip('.') else 1


def local_version(name):
    """Version pip installed for the Python running this program, None if it isn't installed"""
    with CACHE_LOCK:                                               # not thread-safe: two check threads in it at once delete the same cache entry -> KeyError
        importlib.invalidate_caches()                              # forget cached folder listings, so a version pip just installed shows up
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def github_version(repo, branch):
    """(version, None) from the version= line of setup.py or pyproject.toml on that branch, or (None, the reason it couldn't be read)"""
    if not repo:
        return None, 'no GitHub repo set - open Settings'
    reason = 'no setup.py or pyproject.toml found - check the repo and branch'
    for filename in ('setup.py', 'pyproject.toml'):
        url = f'https://raw.githubusercontent.com/{repo}/{branch or "main"}/{filename}'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': f'{APP_NAME.replace(" ", "")}/{VERSION}'}), timeout=15) as res:
                text = res.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            return None, f'GitHub answered {e.code}'
        except Exception as e:
            return None, f'could not reach GitHub ({e.__class__.__name__})'
        m = re.search(r'^\s*version\s*=\s*["\']([^"\']+)["\']', text, re.M)
        if m:
            return m.group(1), None
        reason = f'no version = "..." line in {filename}'
    return None, reason


def installed_from(name):
    """Where pip got the installed copy, from the note it leaves when it installs from a link (direct_url.json): 'GitHub', 'a folder' or 'a link'.
       No note = 'PyPI'.  None if it isn't installed"""
    try:
        text = importlib.metadata.distribution(name).read_text('direct_url.json')
        url = json.loads(text).get('url', '') if text else None
    except Exception:
        return None
    return 'PyPI' if url is None else 'GitHub' if 'github' in url.lower() else 'a folder' if url.startswith('file:') else 'a link'


def pypi_versions(name):
    """(latest, releases, reason) from PyPI.  releases = [(version, 'YYYY-MM-DD', yanked)], newest version first.  latest is None when it isn't on PyPI
       (reason 'not on PyPI') or PyPI couldn't be read"""
    url = f'https://pypi.org/pypi/{name}/json'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': f'{APP_NAME.replace(" ", "")}/{VERSION}'}), timeout=15) as res:
            data = json.load(res)
        latest = data['info']['version']
    except urllib.error.HTTPError as e:
        return None, [], 'not on PyPI' if e.code == 404 else f'PyPI answered {e.code}'
    except Exception as e:
        return None, [], f'could not reach PyPI ({e.__class__.__name__})'
    found = data.get('releases') or {latest: data.get('urls', [])}           # PyPI calls 'releases' deprecated - if it goes, the list is just the latest
    releases = [(v, min(f.get('upload_time_iso_8601') or f.get('upload_time') or '' for f in files)[:10], all(f.get('yanked') for f in files))
                for v, files in found.items() if files]
    return latest, sorted(releases, key=lambda r: version_key(r[0]), reverse=True), None


def versions(p):
    """Everything about one package: the installed version and where it came from, GitHub's newest, PyPI's latest and all its releases.
       Slow (network) - runs in a thread"""
    key = pkg_key(p['name'])
    if DEMO:
        time.sleep(random.uniform(0.4, 1.6))
        local, source, github, pypi = DEMO_VERSIONS.get(key, ('1.0', 'PyPI', '1.0', '1.0'))
        releases = sorted(((r.split(':')[0], r.split(':')[1], r.endswith(':yanked')) for r in DEMO_RELEASES.get(key, f'{pypi}:2026-10-01').split()) if pypi else [],
                          key=lambda r: version_key(r[0]), reverse=True)
        return dict(PENDING, pending=False, local=local, source=source, github=github if p['repo'] else None, pypi=pypi, releases=releases,
                    pypi_reason=None if pypi else 'not on PyPI')
    github, reason = github_version(p['repo'], p['branch']) if p['repo'] else (None, None)          # no repo is fine: a package that is only on PyPI
    pypi, releases, pypi_reason = pypi_versions(p['name'])
    return dict(PENDING, pending=False, local=local_version(p['name']), source=installed_from(p['name']), github=github, reason=reason, pypi=pypi,
                releases=releases, pypi_reason=pypi_reason)


def newest(st):
    """The higher of GitHub's and PyPI's version, None when neither is known"""
    found = [v for v in (st['github'], st['pypi']) if v]
    return max(found, key=version_key) if found else None


def problems(p, st):
    """What went wrong checking one package, for the bottom line - [] when nothing did"""
    if st['pending']:
        return []
    found = [f'GitHub: {st["reason"]}'] if p['repo'] and st['reason'] else []
    if st['pypi_reason'] not in (None, 'not on PyPI'):
        found.append(f'PyPI: {st["pypi_reason"]}')
    if not p['repo'] and st['pypi_reason'] == 'not on PyPI':
        found.append('not on PyPI and no GitHub repo - open Settings')
    return found


def package_state(p):
    """'checking' | 'missing' (not installed) | 'error' (no version found on GitHub or PyPI) | 'update' | 'current'"""
    st = G.status.get(pkg_key(p['name']), PENDING)
    if st['pending']:
        return 'checking'
    if st['local'] is None:
        return 'missing' if p['repo'] or st['pypi'] else 'error'                  # error: nothing to install it from
    top = newest(st)
    if top is None:
        return 'error'
    return 'update' if version_key(st['local']) < version_key(top) else 'current'


def check_thread(window, generation, p):
    """One package's versions - installed, GitHub, PyPI - sent back to the event loop.  Runs in its own thread"""
    try:
        window.write_event_value(K_VERSION, (generation, pkg_key(p['name']), versions(p)))
    except Exception:
        window.write_event_value(K_THREAD_ERROR, traceback.format_exc())


def start_check(window):
    """Check every package at once, one thread each; rows show 'checking' dots until their answer arrives"""
    G.generation += 1
    G.status = {pkg_key(p['name']): dict(PENDING) for p in G.packages}
    G.checked_at = None if G.packages else time.strftime('%H:%M')
    for p in G.packages:
        threading.Thread(target=check_thread, args=(window, G.generation, dict(p)), daemon=True).start()
    redraw(window)


def load_packages():
    packages = sg.user_settings_get_entry(K_PACKAGES, None)
    if packages is None:                                           # first run: the list the old program had in its code
        packages = [dict(p) for p in DEFAULT_PACKAGES]
        sg.user_settings_set_entry(K_PACKAGES, packages)
    return [{'name': p.get('name', ''), 'repo': p.get('repo', ''), 'branch': p.get('branch', '') or 'main'} for p in packages if p.get('name')]


# ======================================================================================================================================================
#   Drawing the card
# ======================================================================================================================================================
def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, f):
    """Blend two hex colors, f=0 -> c1, f=1 -> c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(rgb(c1), rgb(c2)))


def is_light(color):
    """True for a light color - a light card gets darker status colors"""
    r, g, b = rgb(color)
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


def state_color(state, T, text=False):
    """A status color for the card's theme: darker on a light card, darker still for text (amber text is hard to read on white)"""
    return mix(STATE_COLORS[state], '#000000', 0.3 if text else 0.18) if is_light(T['card']) else STATE_COLORS[state]


def font(bold, px):
    """A Segoe UI (Windows) / DejaVu (Linux) font of px pixels, cached"""
    key = (bold, px)
    if key not in G.fonts:
        f = None
        for name in FONT_NAMES[bold]:
            try:
                f = ImageFont.truetype(name, px)
                break
            except OSError:
                continue
        if f is None:
            try:
                f = ImageFont.load_default(size=px)
            except TypeError:
                f = ImageFont.load_default()
        G.fonts[key] = f
    return G.fonts[key]


def fit(d, text, fnt, width):
    """text shortened with an ellipsis so it fits in width pixels"""
    if d.textlength(text, font=fnt) <= width:
        return text
    while text and d.textlength(text + '…', font=fnt) > width:
        text = text[:-1]
    return text + '…'


def card_height():
    return ROW_TOP + max(1, len(G.packages)) * ROW_H + 6 + FOOT_H


def summary():
    """The bottom line when the mouse isn't over anything"""
    n = len(G.packages)
    if not n:
        return 'No packages yet - click the gear to add some'
    if G.checked_at is None:
        return 'checking GitHub and PyPI…'
    updates = sum(1 for p in G.packages if package_state(p) == 'update')
    return f'{n} package{"s" * (n != 1)}   ·   {updates} update{"s" * (updates != 1)}   ·   checked {G.checked_at}'


def hint(part):
    """What a click will do - shown in the bottom line while the mouse is over that part"""
    if part == 'gear':
        return 'Settings - add, remove and order packages'
    if part == 'close':
        return f'Close {APP_NAME}'
    if isinstance(part, tuple) and part[1] < len(G.packages):
        p = G.packages[part[1]]
        st, state = G.status.get(pkg_key(p['name']), PENDING), package_state(p)
        trouble = problems(p, st)
        if trouble:                                                    # why there's a red ? (the bottom line shortens it to fit)
            return '   ·   '.join(trouble)
        if state == 'update':
            return f'Click to upgrade {p["name"]} to {newest(st)} - or pick another version'
        if state == 'missing':
            return f'Click to install {p["name"]} - pick a version'
        if state == 'current':
            return f'{p["name"]} {st["local"]} is the newest - click to pick another version'
        return f'checking {p["name"]}…'
    return summary()


def draw_gear(d, cx, cy, r, color, hole):
    """8-tooth gear: a star-shaped polygon with flat tooth tops, and a hole in the middle"""
    pts = []
    for i in range(32):
        a = math.radians(i * 360 / 32)
        rr = r if (i % 4) in (0, 1) else r * 0.72
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color)
    d.ellipse((cx - r * 0.33, cy - r * 0.33, cx + r * 0.33, cy + r * 0.33), fill=hole)


def draw_state(d, state, cx, cy, r, T, k, hover):
    """The status disc at the end of a row: colored disc with a white glyph (dots in a grey disc while checking)"""
    w = max(1, round(1.8 * k))
    if state == 'checking':
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=T['track'])
        for dx in (-4.5, 0, 4.5):
            d.ellipse((cx + dx * k - 1.4 * k, cy - 1.4 * k, cx + dx * k + 1.4 * k, cy + 1.4 * k), fill=T['dim'])
        return
    color = state_color(state, T)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color if hover else mix(color, T['card'], 0.12))
    dot = lambda x, y: d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill='white')
    if state == 'current':                                             # check mark
        pts = [(cx - 4 * k, cy + 0.3 * k), (cx - 1.2 * k, cy + 3.2 * k), (cx + 4.2 * k, cy - 3 * k)]
        d.line(pts, fill='white', width=w, joint='curve')
        dot(*pts[0]), dot(*pts[-1])
    elif state == 'update':                                            # up arrow
        d.line((cx, cy + 4.5 * k, cx, cy - 4 * k), fill='white', width=w)
        d.line((cx - 3.8 * k, cy - 0.3 * k, cx, cy - 4.3 * k, cx + 3.8 * k, cy - 0.3 * k), fill='white', width=w, joint='curve')
        dot(cx, cy + 4.5 * k), dot(cx - 3.8 * k, cy - 0.3 * k), dot(cx + 3.8 * k, cy - 0.3 * k)
    elif state == 'missing':                                           # plus
        d.line((cx - 4 * k, cy, cx + 4 * k, cy), fill='white', width=w)
        d.line((cx, cy - 4 * k, cx, cy + 4 * k), fill='white', width=w)
    else:                                                              # error: exclamation mark
        d.line((cx, cy - 4.5 * k, cx, cy + 1 * k), fill='white', width=w)
        dot(cx, cy - 4.5 * k), dot(cx, cy + 1 * k)
        d.ellipse((cx - w * 0.7, cy + 3.8 * k - w * 0.7, cx + w * 0.7, cy + 3.8 * k + w * 0.7), fill='white')


def version_cell(st, version, absent, T):
    """Text and color of a PYPI or GITHUB cell:  … checking,  — not there (not on PyPI / no repo set),  red ? couldn't be read,  amber = newer than installed"""
    if st['pending']:
        return '…', T['text']
    if version is None:
        return ('—', T['dim']) if absent else ('?', state_color('error', T, text=True))
    newer = st['local'] is not None and version_key(version) > version_key(st['local'])
    return version, state_color('update', T, text=True) if newer else T['text']


def render():
    """Draw the whole card and return it as PNG bytes.  Drawn at 2x and shrunk, so every edge is antialiased.  Also fills G.hits"""
    s = G.scale
    k = s * 2
    T = theme_colors()                                                 # the theme at the Brightness setting
    H = card_height()
    W_px, H_px = round(CARD_W * k), round(H * k)
    im = Image.new('RGBA', (W_px, H_px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_px - 1, H_px - 1), radius=(RADIUS if SEE_THROUGH else 0) * k, fill=T['card'], outline=T['border'], width=max(1, round(k)))
    hits = []
    # ---- header: state dot, name, version | gear, close
    states = [package_state(p) for p in G.packages]
    trouble = any(problems(p, G.status.get(pkg_key(p['name']), PENDING)) for p in G.packages)
    dot = state_color('update' if 'update' in states else 'error' if 'error' in states or trouble else 'current', T)
    dot = T['dim'] if 'checking' in states or not states else dot
    d.ellipse((12 * k, 17 * k, 20 * k, 25 * k), fill=dot)
    title_font = font(True, round(13 * k))
    d.text((27 * k, BTN_Y * k), APP_NAME.upper(), font=title_font, fill=T['dim'], anchor='lm')
    version_x = 27 * k + d.textlength(APP_NAME.upper(), font=title_font) + 7 * k
    d.text((version_x, (BTN_Y + 1) * k), f'v{VERSION}', font=font(False, round(12 * k)), fill=mix(T['dim'], T['card'], 0.4), anchor='lm')
    for part, cx in (('gear', GEAR_X), ('close', CLOSE_X)):
        hits.append((cx - BTN_R, BTN_Y - BTN_R, cx + BTN_R, BTN_Y + BTN_R, part))
        hot = G.hover == part
        if hot:
            d.ellipse(((cx - BTN_R) * k, (BTN_Y - BTN_R) * k, (cx + BTN_R) * k, (BTN_Y + BTN_R) * k), fill=C_CLOSE if part == 'close' else mix(T['text'], T['card'], 0.82))
        color = T['text'] if hot else mix(T['dim'], T['card'], 0.25)
        if part == 'gear':
            draw_gear(d, cx * k, BTN_Y * k, 6.5 * k, color, mix(T['text'], T['card'], 0.82) if hot else T['card'])
        else:
            r = 4.5 * k
            d.line((cx * k - r, BTN_Y * k - r, cx * k + r, BTN_Y * k + r), fill=color, width=max(1, round(1.6 * k)))
            d.line((cx * k - r, BTN_Y * k + r, cx * k + r, BTN_Y * k - r), fill=color, width=max(1, round(1.6 * k)))
    d.line((14 * k, HEAD_H * k, (CARD_W - 14) * k, HEAD_H * k), fill=T['track'], width=max(1, round(k)))
    # ---- column headings, so it's clear which version is which
    name_font, ver_font, head_font = font(True, round(13 * k)), font(False, round(12 * k)), font(True, round(12 * k))
    head_y, head_color = (HEAD_H + COLS_H / 2 + 2) * k, mix(T['dim'], T['card'], 0.2)
    d.text((18 * k, head_y), 'PACKAGE', font=head_font, fill=head_color, anchor='lm')
    d.text((COL_LOCAL_R * k, head_y), 'INSTALLED', font=head_font, fill=head_color, anchor='rm')
    d.text((COL_PYPI_R * k, head_y), 'PYPI', font=head_font, fill=head_color, anchor='rm')
    d.text((COL_GITHUB_R * k, head_y), 'GITHUB', font=head_font, fill=head_color, anchor='rm')
    # ---- one row per package
    if not G.packages:
        d.text((CARD_W / 2 * k, (ROW_TOP + ROW_H / 2) * k), 'No packages', font=ver_font, fill=T['dim'], anchor='mm')
    for i, p in enumerate(G.packages):
        y0 = ROW_TOP + i * ROW_H
        yc = (y0 + ROW_H / 2) * k
        part = ('row', i)
        hits.append((8, y0, CARD_W - 8, y0 + ROW_H, part))
        hot = G.hover == part
        if hot:
            d.rounded_rectangle((8 * k, (y0 + 1) * k, (CARD_W - 8) * k, (y0 + ROW_H - 1) * k), radius=7 * k, fill=mix(T['text'], T['card'], 0.9))
        st, state = G.status.get(pkg_key(p['name']), PENDING), package_state(p)
        local = '…' if st['pending'] else (st['local'] or 'not installed')
        local_w = d.textlength(local, font=ver_font)
        d.text((18 * k, yc), fit(d, p['name'], name_font, COL_LOCAL_R * k - local_w - 32 * k), font=name_font, fill=T['text'], anchor='lm')
        d.text((COL_LOCAL_R * k, yc), local, font=ver_font, fill=T['dim'], anchor='rm')
        for right, version, absent in ((COL_PYPI_R, st['pypi'], st['pypi_reason'] == 'not on PyPI'), (COL_GITHUB_R, st['github'], not p['repo'])):
            text, color = version_cell(st, version, absent, T)
            d.text((right * k, yc), fit(d, text, ver_font, (COL_GITHUB_R - COL_PYPI_R - 16) * k), font=ver_font, fill=color, anchor='rm')
        draw_state(d, state, COL_STATE * k, yc, 9 * k, T, k, hot)
    # ---- bottom line: summary, or what a click on the part under the mouse will do
    foot_y = ROW_TOP + max(1, len(G.packages)) * ROW_H + 6
    d.line((14 * k, foot_y * k, (CARD_W - 14) * k, foot_y * k), fill=T['track'], width=max(1, round(k)))
    text = hint(G.hover) if G.hover else summary()
    d.text((CARD_W / 2 * k, (foot_y + FOOT_H / 2 - 1) * k), fit(d, text, ver_font, (CARD_W - 28) * k), font=ver_font, fill=T['text'] if G.hover else T['dim'], anchor='mm')
    G.hits = hits
    im = im.resize((round(CARD_W * s), round(H * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return buf.getvalue()


def redraw(window):
    window[K_IMAGE].update(data=render())


# ======================================================================================================================================================
#   The widget window
# ======================================================================================================================================================
def make_menu():
    """Right-click menu with check marks on the current choices"""
    tick = lambda on: '✓ ' if on else '    '                   # every label starts with a tick or the same width of spaces, so they line up
    theme = lambda n: f'{tick(n == G.theme)}{n}::{KT_THEME(n)}'
    return ['', [f'    Check now::{K_CHECK}', f'    Settings...::{K_SETTINGS}', '---', f'{tick(G.on_top)}Keep on top::{K_TOP}',
                 '    Theme', [theme(n) for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],
                 f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
                 '    Size', [f'{tick(n == G.size_name)}{n}::{KT_SIZE(n)}' for n in SIZES],
                 '    Opacity', [f'{tick(p == G.opacity)}{p}%::{KT_OPACITY(p)}' for p in OPACITIES],
                 '---', '    Edit Me::Edit Me', '    Version::Version', f'    Exit::{K_EXIT}']]


def menu_colors():
    """The widget's right-click menu background and text: the card's own colors (background lifted a touch), so the menu matches the theme"""
    T = theme_colors()
    return mix(T['card'], T['text'], 0.04), T['text']


def theme_swatch(name):
    """A tiny card in a theme's colors (card, a line of text, a dim line) shown beside its name in the Theme menu.  Made once and kept - tk drops images nobody holds"""
    if (name, G.bright) not in G.swatches:                                                      # a set per Brightness level: the chips show what you'd get
        T, z = theme_colors(name), max(1.0, G.window.TKroot.winfo_fpixels('1i') / 96) * 4           # drawn 4x and shrunk, so the edges are smooth
        im = Image.new('RGBA', (round(34 * z), round(20 * z)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=5 * z, fill=T['card'], outline=C_SWATCH_EDGE, width=round(z))
        d.rounded_rectangle((6 * z, 5.5 * z, 25 * z, 9 * z), radius=1.5 * z, fill=T['text'])
        d.rounded_rectangle((6 * z, 12 * z, 17 * z, 14.5 * z), radius=1.2 * z, fill=T['dim'])
        buf = io.BytesIO()
        im.resize((round(im.width / 4), round(im.height / 4)), Image.LANCZOS).save(buf, 'PNG')
        G.swatches[(name, G.bright)] = tk.PhotoImage(master=G.window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.swatches[(name, G.bright)]


def style_menus(menu, bg=C_MENU_BG, fg=C_MENU_TEXT):
    """tk draws menus Windows-gray: recolor a right-click menu and all its sub-menus (Toybox colors unless given), flat and compact; theme names get a swatch"""
    menu.configure(bg=bg, fg=fg, activebackground=C_MENU_SEL, activeforeground='#ffffff', bd=0, activeborderwidth=1, relief='flat', font=FONT_MENU)
    first_light = True
    for i in range(menu.index('end') + 1 if menu.index('end') is not None else 0):
        name = menu.entrycget(i, 'label').lstrip('✓ ') if menu.type(i) == 'command' else None
        if name in THEMES:
            menu.entryconfigure(i, image=theme_swatch(name), compound='left')
            if first_light and is_light(THEMES[name]['card']):
                menu.entryconfigure(i, columnbreak=1)                         # the light themes get a column of their own
                first_light = False
    for child in menu.winfo_children():
        if isinstance(child, tk.Menu):
            style_menus(child, bg, fg)


def apply_menu(window):
    window[K_IMAGE].set_right_click_menu(make_menu(), propogate_to_window=True)
    style_menus(window.TKRightClickMenu, *menu_colors())


def part_at(x, y):
    """The part of the card at widget pixel (x, y): ('row', i), 'gear', 'close' or None"""
    x, y = x / G.scale, y / G.scale
    for x0, y0, x1, y1, part in G.hits:
        if part in ('gear', 'close'):
            if math.hypot(x - (x0 + x1) / 2, y - (y0 + y1) / 2) <= BTN_R:
                return part
        elif x0 <= x <= x1 and y0 <= y <= y1:
            return part
    return None


def bind_mouse(window):
    """Hover highlight and clicks.  grab_anywhere already drags the window; these bindings are added alongside it (add='+')"""
    widget = window[K_IMAGE].Widget

    def motion(e):
        part = part_at(e.x, e.y)
        if part != G.hover:
            window.write_event_value(K_HOVER, part)

    def press(e):
        G.press = (e.x, e.y, part_at(e.x, e.y))

    def release(e):
        if G.press and G.press[2] is not None and math.hypot(e.x - G.press[0], e.y - G.press[1]) < 4 and part_at(e.x, e.y) == G.press[2]:
            window.write_event_value(K_CLICK, G.press[2])              # a click - not a drag of the window that happened to end on a row
        G.press = None

    widget.bind('<Motion>', motion, add='+')
    widget.bind('<Leave>', lambda e: window.write_event_value(K_HOVER, None) if G.hover else None, add='+')
    widget.bind('<ButtonPress-1>', press, add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')


def make_window():
    layout = [[sg.Image(data=render(), key=K_IMAGE, background_color=TRANSPARENT, pad=(0, 0))]]
    menu_bg, menu_text = menu_colors()
    window = sg.Window(APP_NAME, layout, no_titlebar=True, grab_anywhere=True, keep_on_top=G.on_top, margins=(0, 0), element_padding=(0, 0), background_color=TRANSPARENT,
                       transparent_color=TRANSPARENT if SEE_THROUGH else None, alpha_channel=G.opacity / 100, auto_save_location=True, icon=ICON, finalize=True,
                       right_click_menu=make_menu(),
                       right_click_menu_background_color=menu_bg, right_click_menu_text_color=menu_text, right_click_menu_selected_colors=('#ffffff', C_MENU_SEL),
                       right_click_menu_font=FONT_MENU)
    G.window = window
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96) * SIZES.get(G.size_name, 1.0)          # 2.0 on a 200% Windows display
    style_menus(window.TKRightClickMenu, menu_bg, menu_text)
    bind_mouse(window)
    window.bind('<Escape>', K_EXIT)
    return window


def beside(window):
    """(location, anchor) for a window opened from the widget: over it, growing away from the nearer side of the screen"""
    x, y = window.current_location()
    right_half = x + window.size[0] / 2 > sg.Window.get_screen_size()[0] / 2       # widget on the right of the screen: open leftward
    return ((x + window.size[0], y), sg.WIN_ANCHOR_UPPER_RIGHT) if right_half else ((x, y), sg.WIN_ANCHOR_UPPER_LEFT)


def install(window, p):
    """Click on a row: the release picker, then pip install what was picked (PySimpleGUI shows pip's output in a window)"""
    G.hover = None
    redraw(window)
    choice, st = pick_window(p, *beside(window))
    if choice is None:
        redraw(window)                                                 # the picker checked the package again - show what it found
        return
    target, st = pip_target(p, choice, st['local']), dict(st)
    if DEMO:
        sg.popup_quick_message(f'Demo - nothing was installed\npip install --upgrade {target}', font=('Segoe UI', 14), text_color='white', background_color='#2a62a8',
                               keep_on_top=True)
        st['local'], st['source'] = (st['github'] if choice[0] == 'GitHub' else choice[1]), choice[0]
    else:
        try:
            sg.execute_pip_install_package(target)                     # --upgrade (always added) reinstalls a zipball; force_reinstall would also reinstall its dependencies
        except Exception as e:
            sg.popup_error_with_traceback(f'Error trying to pip install {p["name"]}', e)
        st['local'], st['source'] = local_version(p['name']), installed_from(p['name'])
    G.status[pkg_key(p['name'])] = dict(st, pending=False)
    redraw(window)


def got_version(window, values):
    """A version check answered for one package - answers from an older check are dropped"""
    generation, key, st = values[K_VERSION]
    if generation == G.generation:
        G.status[key] = st
        if not any(s['pending'] for s in G.status.values()):
            G.checked_at = time.strftime('%H:%M')
        redraw(window)


def keep_going(window, event, values):
    """While the Brightness panel is open the card keeps hovering and checking versions; anything else closes the panel and goes to the main loop"""
    if event == K_HOVER:
        G.hover = values[K_HOVER]
        redraw(window)
    elif event == K_VERSION:
        got_version(window, values)
    elif event == K_CHECK:
        start_check(window)
    else:
        return False
    return True


def migrate_settings():
    """First run as Pip Refresh: take over the settings file Pip Fresh saved - the package list, look, and the window position (saved under the old title)"""
    new_file, old_file = sg.UserSettings(SETTINGS_FILE).get_filename(), sg.UserSettings(OLD_SETTINGS_FILE).get_filename()
    if os.path.exists(new_file) or not os.path.exists(old_file):
        return
    shutil.copyfile(old_file, new_file)
    sg.user_settings_filename(SETTINGS_FILE)
    sg.user_settings_load()
    old_location = sg.user_settings_get_entry('-LAST WINDOW LOCATION-' + OLD_APP_NAME, None)
    if old_location is not None:
        sg.user_settings_set_entry('-LAST WINDOW LOCATION-' + APP_NAME, old_location)


# --- BRIGHTNESS: the same block in every card widget (master copy in modern_widget_recipe.md) - the program darkens or lightens its own theme ---
# Right-click > Brightness... opens a small panel under the card with a slider, and the card changes as the knob moves.  theme_colors() is what the card,
# its menu and the Theme chips are drawn with: the theme at the chosen level, its text kept readable.  The program supplies redraw(window),
# font(bold, px), is_light(), RADIUS, TRANSPARENT, THEMES and G.theme / G.scale / G.bright / G.tuned.
BRIGHT_LEVELS = list(range(-80, 51, 5))                           # the slider's stops, darkest first: -80 = much darker, 0 = as designed, 50 = lighter
K_BRIGHT = '-BRIGHTNESS-'                                         # settings-file entry, and the right-click item that opens the panel
K_PANEL_IMAGE, K_PANEL_VALUE, K_PANEL_STEP = '-PANEL IMAGE-', '-PANEL VALUE-', '-PANEL STEP-'      # values: the new level / +1 or -1 stop
K_PANEL_HOVER, K_PANEL_CLICK = '-PANEL HOVER-', '-PANEL CLICK-'   # values: 'track' | 'reset' | 'done' | None
K_PANEL_DONE, K_PANEL_CANCEL = '-PANEL DONE-', '-PANEL CANCEL-'   # Enter / Escape
PANEL_W, PANEL_H = 270, 114                                       # the panel, in design pixels
TRACK_X0, TRACK_X1, TRACK_Y, TRACK_H = 20, PANEL_W - 20, 52, 10
PILL_W, PILL_H, PILL_Y = 70, 24, 90                               # Reset (left) and Done (right); PILL_Y is their middle
C_PANEL_DONE = '#2a62a8'                                          # the Done button


def channels(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def shade(c1, c2, f):
    """c1 moved f of the way toward c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(channels(c1), channels(c2)))


def tune(color, level, light, line=False):
    """A card / border / track color at a Brightness level.  Dark themes: the brightness is scaled - darker is deeper, lighter more vivid, the hue kept;
       lines darken less, so the border and the gauge track still show at -80.  Light themes: darker turns gently gray (at most 32%), lighter fades to white"""
    if light and level > 0:
        return shade(color, '#ffffff', level / 100)
    f = 1 + level / (250 if light else 100)
    if line and level < 0 and not light:
        f **= 0.6
    return '#%02x%02x%02x' % tuple(min(255, round(v * f)) for v in channels(color))


def luminance(color):
    """WCAG relative luminance, 0 = black .. 1 = white"""
    return sum(w * (v / 3294.6 if v <= 10.31 else ((v / 255 + 0.055) / 1.055) ** 2.4) for w, v in zip((0.2126, 0.7152, 0.0722), channels(color)))


def readable(fg, bg, ratio, pole):
    """fg moved toward pole (white on a dark card, black on a light one) just far enough to have ratio contrast with bg"""
    lb = luminance(bg)
    for i in range(26):
        c = shade(fg, pole, i / 25)
        lf = luminance(c)
        if (max(lf, lb) + 0.05) / (min(lf, lb) + 0.05) >= ratio:
            return c
    return pole


def theme_colors(name=None):
    """A theme's five colors at the Brightness setting (the chosen theme if no name) - text keeps 7:1 contrast with the card, dim 4.5:1"""
    name = name if name in THEMES else G.theme if G.theme in THEMES else 'Toybox'
    if (name, G.bright) not in G.tuned:
        T = THEMES[name]
        if G.bright:
            light, level = is_light(T['card']), G.bright
            card, pole = tune(T['card'], level, light), '#000000' if light else '#ffffff'
            T = {'card': card, 'border': tune(T['border'], level, light, True), 'track': tune(T['track'], level, light, True),
                 'text': readable(T['text'], card, 7, pole), 'dim': readable(T['dim'], card, 4.5, pole)}
        G.tuned[(name, G.bright)] = T
    return G.tuned[(name, G.bright)]


def bright_text(level):
    return 'as designed' if level == 0 else f'{level:+d}%'.replace('-', '\u2212')


def knob_x(level):
    """Design-pixel x of the knob at a level: the middle of that level's band on the track"""
    return TRACK_X0 + (BRIGHT_LEVELS.index(level) + 0.5) * (TRACK_X1 - TRACK_X0) / len(BRIGHT_LEVELS)


def level_at(x):
    """The level whose band is under panel pixel x"""
    i = int((x / G.scale - TRACK_X0) / (TRACK_X1 - TRACK_X0) * len(BRIGHT_LEVELS))
    return BRIGHT_LEVELS[max(0, min(len(BRIGHT_LEVELS) - 1, i))]


def panel_part(x, y):
    """'track', 'reset', 'done' or None at panel pixel (x, y)"""
    x, y = x / G.scale, y / G.scale
    if TRACK_X0 - 10 <= x <= TRACK_X1 + 10 and abs(y - TRACK_Y) <= 14:
        return 'track'
    if abs(y - PILL_Y) <= PILL_H / 2:
        if 18 <= x <= 18 + PILL_W:
            return 'reset'
        if PANEL_W - 18 - PILL_W <= x <= PANEL_W - 18:
            return 'done'
    return None


def render_panel(hover):
    """The Brightness panel, drawn like the card and in its colors (so it changes too).  The track shows the card's own color at every level, darkest
       on the left; the knob sits on the one in use, the tick under the track marks 'as designed'"""
    s = G.scale
    k = s * 2
    T, base = theme_colors(), THEMES.get(G.theme, THEMES['Toybox'])
    light = is_light(base['card'])
    W, H = round(PANEL_W * k), round(PANEL_H * k)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=(RADIUS if sg.running_windows() else 0) * k, fill=T['card'], outline=T['border'], width=max(1, round(k)))
    d.text((18 * k, 20 * k), 'BRIGHTNESS', font=font(True, round(13 * k)), fill=T['dim'], anchor='lm')
    d.text(((PANEL_W - 18) * k, 20 * k), bright_text(G.bright), font=font(True, round(13 * k)), fill=T['text'], anchor='rm')
    x0, x1, y0, y1 = TRACK_X0 * k, TRACK_X1 * k, (TRACK_Y - TRACK_H / 2) * k, (TRACK_Y + TRACK_H / 2) * k
    strip = Image.new('RGBA', (round(x1 - x0), round(y1 - y0)))                       # a band per level, in the card color at that level
    band = strip.width / len(BRIGHT_LEVELS)
    for i, level in enumerate(BRIGHT_LEVELS):
        ImageDraw.Draw(strip).rectangle((round(i * band), 0, round((i + 1) * band), strip.height), fill=tune(base['card'], level, light))
    mask = Image.new('L', strip.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, strip.width - 1, strip.height - 1), radius=strip.height / 2, fill=255)
    im.paste(strip, (round(x0), round(y0)), mask)
    d.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) / 2, outline=T['dim'] if hover == 'track' else T['border'], width=max(1, round(k)))
    zx = knob_x(0) * k
    d.line((zx, y1 + 3 * k, zx, y1 + 7 * k), fill=T['dim'], width=max(1, round(1.2 * k)))
    kx, ky, r = knob_x(G.bright) * k, TRACK_Y * k, 9 * k                                # the knob, filled with the color in use
    d.ellipse((kx - r, ky - r, kx + r, ky + r), fill=T['card'], outline=T['text'], width=max(1, round(2 * k)))
    small = font(False, round(11 * k))
    d.text((x0, (TRACK_Y + 17) * k), 'darker', font=small, fill=T['dim'], anchor='lm')
    d.text((x1, (TRACK_Y + 17) * k), 'lighter', font=small, fill=T['dim'], anchor='rm')
    for part, px, fill, color in (('reset', 18, T['track'], T['text'] if G.bright else T['dim']), ('done', PANEL_W - 18 - PILL_W, C_PANEL_DONE, '#ffffff')):
        if hover == part:
            fill = shade(fill, '#ffffff', 0.15) if part == 'done' else shade(T['text'], T['card'], 0.78)
        d.rounded_rectangle((px * k, (PILL_Y - PILL_H / 2) * k, (px + PILL_W) * k, (PILL_Y + PILL_H / 2) * k), radius=PILL_H / 2 * k, fill=fill)
        d.text(((px + PILL_W / 2) * k, PILL_Y * k), part.capitalize(), font=font(True, round(12 * k)), fill=color, anchor='mm')
    im = im.resize((round(PANEL_W * s), round(PANEL_H * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return buf.getvalue()


def brightness_panel(card, keep_going):
    """Right-click > Brightness...: the panel under the card.  The card and the panel change as the knob moves (drag, click, arrow keys, mouse wheel,
       Home / End).  Done or Enter keeps the level, Escape puts back the one it had.  keep_going(card, event, values) handles the card's own events
       meanwhile (its timer, hover...) and returns False for one that should close the panel - a menu choice, the close x.  That event is returned so the
       main loop can handle it; None otherwise"""
    start = G.bright
    x, y = card.current_location()
    below, height = y + card.size[1] + 6, round(PANEL_H * G.scale)
    py = below if below + height <= card.TKroot.winfo_screenheight() else max(0, y - height - 6)    # under the card, or above it near the bottom
    panel = sg.Window('Brightness', [[sg.Image(data=render_panel(None), key=K_PANEL_IMAGE, background_color=TRANSPARENT, pad=(0, 0))]], no_titlebar=True,
                      keep_on_top=True, margins=(0, 0), element_padding=(0, 0), background_color=TRANSPARENT, location=(x, py), finalize=True,
                      transparent_color=TRANSPARENT if sg.running_windows() else None)  # no grab_anywhere: it would move the panel as the knob is dragged
    widget, mouse = panel[K_PANEL_IMAGE].Widget, {'drag': False, 'press': None, 'hover': None}

    def press(e):
        part = panel_part(e.x, e.y)
        if part == 'track':                                                             # the knob jumps to the mouse and follows it
            mouse['drag'] = True
            panel.write_event_value(K_PANEL_VALUE, level_at(e.x))
        else:
            mouse['press'] = (e.x_root, e.y_root, part, panel.TKroot.winfo_x(), panel.TKroot.winfo_y())

    def drag(e):
        p = mouse['press']
        if mouse['drag']:
            panel.write_event_value(K_PANEL_VALUE, level_at(e.x))
        elif p:                                                                         # anywhere off the track drags the panel
            panel.TKroot.geometry(f'+{p[3] + e.x_root - p[0]}+{p[4] + e.y_root - p[1]}')

    def release(e):
        if mouse['drag']:
            mouse['drag'] = False
            return
        p, mouse['press'] = mouse['press'], None
        if p and p[2] in ('reset', 'done') and math.hypot(e.x_root - p[0], e.y_root - p[1]) < 4:        # a click, not a drag of the panel
            panel.write_event_value(K_PANEL_CLICK, p[2])

    def hover(part):
        if part != mouse['hover']:
            mouse['hover'] = part
            panel.write_event_value(K_PANEL_HOVER, part)

    widget.bind('<ButtonPress-1>', press, add='+')
    widget.bind('<B1-Motion>', drag, add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')
    widget.bind('<Motion>', lambda e: hover(panel_part(e.x, e.y)), add='+')
    widget.bind('<Leave>', lambda e: hover(None), add='+')
    widget.bind('<MouseWheel>', lambda e: panel.write_event_value(K_PANEL_STEP, 1 if e.delta > 0 else -1), add='+')   # Windows
    widget.bind('<Button-4>', lambda e: panel.write_event_value(K_PANEL_STEP, 1), add='+')                            # Linux wheel
    widget.bind('<Button-5>', lambda e: panel.write_event_value(K_PANEL_STEP, -1), add='+')
    for seq, n in (('<Left>', -1), ('<Down>', -1), ('<Right>', 1), ('<Up>', 1)):
        panel.TKroot.bind(seq, lambda e, n=n: panel.write_event_value(K_PANEL_STEP, n))
    panel.TKroot.bind('<Home>', lambda e: panel.write_event_value(K_PANEL_VALUE, BRIGHT_LEVELS[0]))
    panel.TKroot.bind('<End>', lambda e: panel.write_event_value(K_PANEL_VALUE, BRIGHT_LEVELS[-1]))
    panel.bind('<Return>', K_PANEL_DONE)
    panel.bind('<Escape>', K_PANEL_CANCEL)
    panel.force_focus()
    pending = None
    while True:
        win, event, values = sg.read_all_windows()
        if win is card:                                                                 # the card keeps going while the panel is open
            if keep_going(card, event, values):
                continue
            pending = (event, values)
            break
        if event in (sg.WINDOW_CLOSED, K_PANEL_CANCEL):
            G.bright = start
            break
        if event == K_PANEL_DONE or (event == K_PANEL_CLICK and values[event] == 'done'):
            break
        level = G.bright
        if event == K_PANEL_VALUE:
            level = values[event]
        elif event == K_PANEL_STEP:
            level = BRIGHT_LEVELS[max(0, min(len(BRIGHT_LEVELS) - 1, BRIGHT_LEVELS.index(G.bright) + values[event]))]
        elif event == K_PANEL_CLICK and values[event] == 'reset':
            level = 0
        if level != G.bright:
            G.bright = level
            redraw(card)
        panel[K_PANEL_IMAGE].update(data=render_panel(mouse['hover']))
    panel.close()
    redraw(card)
    return pending
# --- end BRIGHTNESS ---


def main():
    sg.theme_add_new('ToyboxDark', TOYBOX_DARK)
    sg.theme('ToyboxDark')
    sg.set_options(dpi_awareness=True)
    migrate_settings()
    sg.user_settings_filename(SETTINGS_FILE)
    G.size_name = sg.user_settings_get_entry(K_SIZE, 'Medium')
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')           # a renamed theme (Midnight -> VoidBlue) or an unknown one
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    G.opacity = sg.user_settings_get_entry(K_OPACITY, 90)
    G.on_top = sg.user_settings_get_entry(K_TOP, False)
    G.packages = load_packages()
    window = make_window()
    start_check(window)
    window.timer_start(CHECK_EVERY_MS, key=K_CHECK)

    pending = None                                                     # a card event that came in while the Brightness panel was open
    while True:
        event, values = pending or window.read()
        pending = None
        if event in (K_EXIT, sg.WINDOW_CLOSED):
            break
        menu_key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event       # right-click items come back as 'label::key'
        if menu_key == K_EXIT:
            break
        if event == K_HOVER:
            G.hover = values[K_HOVER]
            redraw(window)
        elif event == K_CLICK:
            part = values[K_CLICK]
            if part == 'close':
                break
            if part == 'gear':
                menu_key = K_SETTINGS                                  # handled just below
            elif isinstance(part, tuple) and part[1] < len(G.packages):
                install(window, G.packages[part[1]])
        elif event == K_VERSION:
            got_version(window, values)
        elif event == K_THREAD_ERROR:
            sg.popup_error_with_traceback('A version check crashed', values[K_THREAD_ERROR])
        elif menu_key == K_CHECK:
            start_check(window)
        elif menu_key == K_TOP:
            G.on_top = not G.on_top
            window.keep_on_top_set() if G.on_top else window.keep_on_top_clear()
            sg.user_settings_set_entry(K_TOP, G.on_top)
            apply_menu(window)
        elif isinstance(menu_key, str) and menu_key.startswith(K_THEME):
            G.theme = menu_key[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            redraw(window)
            apply_menu(window)
        elif isinstance(menu_key, str) and menu_key.startswith(K_SIZE):
            G.size_name = menu_key[len(K_SIZE):]
            G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96) * SIZES[G.size_name]
            sg.user_settings_set_entry(K_SIZE, G.size_name)
            redraw(window)
            apply_menu(window)
        elif isinstance(menu_key, str) and menu_key.startswith(K_OPACITY):
            G.opacity = int(menu_key[len(K_OPACITY):])
            window.set_alpha(G.opacity / 100)
            sg.user_settings_set_entry(K_OPACITY, G.opacity)
            apply_menu(window)
        elif menu_key == K_BRIGHT:
            pending = brightness_panel(window, keep_going)
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            redraw(window)
            apply_menu(window)
        elif menu_key == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME} v{VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10), icon=ICON)
        elif menu_key == 'Edit Me':
            sg.execute_editor(__file__)
        if menu_key == K_SETTINGS:
            G.hover = None
            redraw(window)
            if settings_window(*beside(window)):                       # saved: reload the list and check it
                G.packages = load_packages()
                start_check(window)
    window.close()


# ======================================================================================================================================================
#   RELEASE PICKER - click a row: GitHub's newest and every PyPI release; pick one and install it
# ======================================================================================================================================================
def same(a, b):
    """Two version strings for the same version"""
    return bool(a and b) and version_key(a) == version_key(b)


def choices(p, st):
    """The picker's rows: [source, version, released, note] - GitHub's newest first (when a repo is set), then PyPI's releases, newest first"""
    rows = []
    if p['repo']:
        if st['pending']:
            note = 'checking…'
        elif st['github']:
            note = f'newest  ·  {p["branch"]} branch' + ('  ·  installed' if same(st['github'], st['local']) and st['source'] == 'GitHub' else '')
        else:
            note = st['reason'] or 'version unknown'
        rows.append(['GitHub', st['github'] or '?', '', note])
    for version, date, yanked in st['releases']:
        notes = ['latest'] * (version == st['pypi']) + ['installed'] * (same(version, st['local']) and st['source'] == 'PyPI') + ['yanked'] * yanked
        rows.append(['PyPI', version, date, '  ·  '.join(notes)])
    return rows


def row_color(row, st):
    """A picker row's text: green = installed, amber = newer than installed, dimmed = yanked, red = GitHub's version unknown"""
    if row[1] == '?':
        return STATE_COLORS['error']
    if 'yanked' in row[3]:
        return C_UI_FAINT
    if 'installed' in row[3]:
        return STATE_COLORS['current']
    if st['local'] and version_key(row[1]) > version_key(st['local']):
        return STATE_COLORS['update']
    return TOYBOX_DARK['TEXT_INPUT']


def verb(version, local):
    """What installing version does to the installed one: Install (none, or the version is unknown) / Upgrade / Downgrade / Reinstall (the same)"""
    if local is None or not version_key(version or ''):
        return 'Install'
    new, old = version_key(version), version_key(local)
    return 'Upgrade' if new > old else 'Downgrade' if new < old else 'Reinstall'


def pip_target(p, row, local):
    """What goes after 'pip install --upgrade' for a picker row.  The same PyPI version again needs --force-reinstall (pip would say it's there
       already) and --no-deps (else its dependencies are replaced with PyPI's too - PySimpleGUI from GitHub would go back to PyPI's)"""
    if row[0] == 'GitHub':
        return zip_url(p)
    return f'{p["name"]}=={row[1]}' + (' --force-reinstall --no-deps' if verb(row[1], local) == 'Reinstall' else '')


def fresh_thread(p, slot):
    """The picker checks its package again as it opens, so the list is up to the minute.  The answer is left in slot for the picker to collect -
       not sent as an event, because the picker may be closed by then"""
    try:
        slot['st'] = versions(p)
    except Exception:
        slot['error'] = traceback.format_exc()


def pick_window(p, location=(None, None), anchor=None):
    """The release picker for one package.  Returns (the row picked or None, the package's latest status)"""
    key = pkg_key(p['name'])
    st, rows = G.status.get(key, PENDING), []
    count = len(choices(p, st))
    shown = PICK_ROWS if st['pending'] else max(3, min(count, PICK_ROWS))
    dpi = max(1.0, G.window.TKroot.winfo_fpixels('1i') / 96)
    table = sg.Table([['', '', '', '']], headings=['SOURCE', 'VERSION', 'RELEASED', ''], col_widths=[7, 11, 10, 28], auto_size_columns=False, justification='left',
                     num_rows=shown, row_height=round(26 * dpi), font=('Segoe UI', 11), select_mode=sg.TABLE_SELECT_MODE_BROWSE, enable_events=True, k=K_PICK_TABLE,
                     text_color=TOYBOX_DARK['TEXT_INPUT'], background_color=TOYBOX_DARK['INPUT'], header_font=('Segoe UI', 9, 'bold'), header_text_color=C_UI_DIM,
                     header_background_color=C_STRIP, header_relief=sg.RELIEF_FLAT, selected_row_colors=('#ffffff', C_MENU_SEL), border_width=0,
                     sbar_trough_color=TOYBOX_DARK['INPUT'], sbar_background_color=C_SLOT_OUTLINE, sbar_arrow_color=C_UI_DIM, sbar_frame_color=C_STRIP,
                     sbar_relief=sg.RELIEF_FLAT, hide_vertical_scroll=not st['pending'] and count <= PICK_ROWS, expand_x=True, expand_y=True, p=(10, 4))
    body = [title_strip(p['name'], K_STRIP_CLOSE, 'pick a version to install'),
            [sg.Text('', k=K_PICK_INFO, font=('Segoe UI', 11), p=(14, (10, 2))), sg.Push(),
             sg.Text('', k=K_PICK_STATUS, font=('Segoe UI', 9), text_color=C_UI_DIM, p=(14, (10, 2)))],
            [table],
            [sg.Text('', k=K_PICK_CMD, font=('Consolas', 10), text_color=C_UI_DIM, p=(14, (4, 2)))],
            [sg.Push(), sg.Button('Install', k=K_PICK_GO, button_color=COLOR_SAVE, s=10, tooltip='Install the one picked   (Enter, or double-click it)'),
             sg.Button('Cancel', k=K_CANCEL, tooltip='Close   (Escape)', p=((4, 12), (6, 10)))]]
    layout = [[sg.Frame('', body, border_width_no_relief=1, border_color=C_ENTRY_BORDER, p=0, expand_x=True, expand_y=True)]]
    window = sg.Window(f'{APP_NAME} - {p["name"]}', layout, no_titlebar=True, grab_anywhere=True, keep_on_top=True, finalize=True, margins=(0, 0), icon=ICON,
                       location=location, location_anchor=anchor)
    tree, close = window[K_PICK_TABLE].Widget, window[K_STRIP_CLOSE].Widget
    close.bind('<Enter>', lambda e: close.configure(bg=C_CLOSE, fg='#ffffff'))
    close.bind('<Leave>', lambda e: close.configure(bg=C_STRIP, fg=C_UI_DIM))
    tree.bind('<Double-Button-1>', lambda e: window.write_event_value(K_PICK_GO, None) if tree.identify_region(e.x, e.y) in ('cell', 'tree') else None, add='+')
    for k, seq in ((K_PAGE_UP, '<Prior>'), (K_PAGE_DOWN, '<Next>'), (K_HOME, '<Home>'), (K_END, '<End>'), (K_CANCEL, '<Escape>'), (K_PICK_GO, '<Return>')):
        window.bind(seq, k)

    def describe(i):
        """The button and the pip command for row i"""
        what = verb(rows[i][1], st['local'])
        window[K_PICK_GO].update(what, button_color=COLOR_SAVE_DIRTY if what == 'Downgrade' else COLOR_SAVE)
        window[K_PICK_CMD].update(f'pip install --upgrade {pip_target(p, rows[i], st["local"])}', text_color=C_UI_DIM)

    def select(i):
        i = max(0, min(len(rows) - 1, i))
        window[K_PICK_TABLE].update(select_rows=[i])
        tree.focus(i + 1)
        tree.see(i + 1)
        describe(i)

    def show(new_st, keep=None):
        """Fill the list from a status; select the row with keep = (source, version), else the newest version"""
        nonlocal st, rows
        st, rows = new_st, choices(p, new_st)
        local = st['local']
        window[K_PICK_INFO].update((f'Installed:  {local}' + (f'   from {st["source"]}' if st['source'] else '')) if local else 'Not installed on this PC')
        window[K_PICK_TABLE].update(values=rows, row_colors=[(i, row_color(r, st), TOYBOX_DARK['INPUT']) for i, r in enumerate(rows)])
        window[K_PICK_GO].update(disabled=not rows)
        if rows:
            top = newest(st)
            i = next((i for i, r in enumerate(rows) if keep and (r[0], r[1]) == keep), None)
            select(i if i is not None else next((i for i, r in enumerate(rows) if same(r[1], top)), 0))
        else:
            window[K_PICK_CMD].update('checking…' if st['pending'] else 'Not on PyPI and no GitHub repo - set one in Settings',
                                      text_color=C_UI_DIM if st['pending'] else state_color('error', THEMES['Toybox']))

    slot = {}
    threading.Thread(target=fresh_thread, args=(dict(p), slot), daemon=True).start()
    window[K_PICK_STATUS].update('checking GitHub and PyPI…')
    show(st)
    window.force_focus()                                                               # keys go to the list straight away
    tree.focus_set()
    chosen = None
    while True:
        event, values = window.read(timeout=None if 'done' in slot else 100)          # look for the fresh check's answer until it comes
        if event in (sg.WIN_CLOSED, K_CANCEL, K_STRIP_CLOSE):
            break
        picked = values[K_PICK_TABLE][0] if values[K_PICK_TABLE] and rows else 0
        if event == sg.TIMEOUT_EVENT:
            if 'st' in slot:
                fresh, slot['done'] = slot.pop('st'), True
                G.status[key] = fresh
                show(fresh, (rows[picked][0], rows[picked][1]) if rows else None)
                window[K_PICK_STATUS].update(f'checked {time.strftime("%H:%M")}')
            elif 'error' in slot:
                error, slot['done'] = slot.pop('error'), True
                window[K_PICK_STATUS].update('')
                sg.popup_error_with_traceback('Checking the versions crashed', error)
        elif event == K_PICK_TABLE and values[K_PICK_TABLE] and rows:
            describe(picked)
        elif event == K_PICK_GO and rows:
            chosen = rows[picked]
            break
        elif event in (K_PAGE_UP, K_PAGE_DOWN) and rows:
            select(picked + (shown - 1) * (1 if event == K_PAGE_DOWN else -1))
        elif event in (K_HOME, K_END) and rows:
            select(0 if event == K_HOME else len(rows) - 1)
    window.close()
    return chosen, st


# ======================================================================================================================================================
#   SETTINGS WINDOW - the package list, laid out like PSG Dock's settings
# ======================================================================================================================================================
class Entry:
    def __init__(self, num):
        self.num = num
        self.name, self.repo, self.branch = '', '', 'main'


class S:                              # Settings window state
    entries = {}                      # num -> Entry, in list order.  Reordering moves the CONTENTS between entries, the entries keep their numbers
    next_num = 0
    dirty = False
    drag = None                       # state of a grip drag in progress
    dnd = False                       # psgdnd drops are working


def parse_github(text):
    """A GitHub link (or owner/repo) -> (owner/repo, branch or None).  None if it isn't one.
       Takes  https://github.com/owner/repo  .../tree/branch  .../blob/branch/file  git@github.com:owner/repo.git  raw.githubusercontent.com/owner/repo/branch/..."""
    text = text.strip().strip('"\'<>').split('?')[0].split('#')[0]
    for host, branch_at in (('raw.githubusercontent.com', 2), ('github.com', 3)):
        i = text.find(host)
        if i >= 0:
            parts = [x for x in re.split(r'[/:]', text[i + len(host):]) if x]
            if len(parts) < 2:
                return None
            repo = f'{parts[0]}/{re.sub(r"[.]git$", "", parts[1])}'
            if host == 'github.com':
                branch = parts[3] if len(parts) > 3 and parts[2] in ('tree', 'blob', 'zipball', 'commits') else None
            else:
                branch = parts[2] if len(parts) > 2 else None
            return repo, branch
    m = re.fullmatch(r'([\w.-]+)/([\w.-]+)', text)
    return (text, None) if m else None


def make_entry(num):
    """One package in the list:   grip  name ...................  check  trash
                                        GitHub  owner/repo           branch  main
                                        pip install --upgrade https://github.com/owner/repo/zipball/main"""
    S.entries[num] = Entry(num)
    ph = dict(placeholder_text_color=C_UI_FAINT, placeholder_background_color=TOYBOX_DARK['INPUT'])
    row1 = [sg.Text('☰', k=KT_GRIP(num), font=('Segoe UI', 14), text_color=C_UI_DIM, p=((4, 8), 0), tooltip='Drag to change the order'),
            sg.Input(k=KT_NAME(num), enable_events=True, placeholder='pip package name', font=('Segoe UI', 12, 'bold'), s=26, p=(0, (4, 2)), **ph),
            sg.Push(),
            sg.Checkbox('', k=KT_CBOX(num), enable_events=True, p=((8, 0), 0), tooltip='Check to delete, or to choose where + Add puts the new entry'),
            sg.Button(image_data=TRASH, mouseover_image_source=TRASH_RED, button_color=(TOYBOX_DARK['BACKGROUND'], TOYBOX_DARK['BACKGROUND']), border_width=0,
                      k=KT_DEL(num), p=((2, 4), 0), tooltip='Delete this entry')]
    row2 = [sg.Text('GitHub', font=('Segoe UI', 10), text_color=C_UI_DIM, s=7, p=((32, 0), 2)),
            sg.Input(k=KT_REPO(num), enable_events=True, placeholder='owner/repo   or paste a GitHub link', font=('Segoe UI', 10), s=34, p=0,
                     tooltip='owner/repo - or paste / drop a GitHub link and it is split into repo and branch', **ph),
            sg.Text('branch', font=('Segoe UI', 10), text_color=C_UI_DIM, p=((10, 4), 2)),
            sg.Input(k=KT_BRANCH(num), enable_events=True, placeholder='main', font=('Segoe UI', 10), s=10, p=((0, 4), 0), **ph)]
    row3 = [sg.Text('', k=KT_URL(num), font=('Segoe UI', 9), text_color=C_UI_FAINT, p=((32, 4), (2, 4)))]
    return sg.Frame('', [row1, row2, row3], k=KT_ENTRY(num), border_width_no_relief=2, border_color=C_ENTRY_BORDER, expand_x=True, p=(4, 3))


def wire_entry(window, num):
    """After an entry exists in the window: grip drag bindings, and drop targets when psgdnd is installed"""
    grip = window[KT_GRIP(num)].Widget

    def grip_event(key):                                   # 'break' stops grab_anywhere from dragging the whole window at the same time
        def handler(e):
            window.write_event_value(key, (num, e.x_root, e.y_root))
            return 'break'
        return handler
    grip.bind('<ButtonPress-1>', grip_event(K_DRAG_PRESS))
    grip.bind('<B1-Motion>', grip_event(K_DRAG_MOTION))
    grip.bind('<ButtonRelease-1>', grip_event(K_DRAG_RELEASE))
    grip.configure(cursor='hand2')
    if S.dnd:
        for key in (KT_ENTRY(num), KT_NAME(num), KT_REPO(num), KT_BRANCH(num)):
            try:
                psgdnd.register_element_dnd(window[key], window, psgdnd.DROP_TYPE_ALL)
            except Exception:
                pass


def show_entry(window, num):
    """Put an entry's contents into its elements"""
    e = S.entries[num]
    window[KT_NAME(num)].update(e.name)
    window[KT_REPO(num)].update(e.repo)
    window[KT_BRANCH(num)].update(e.branch)
    show_url(window, num)


def show_url(window, num):
    e = S.entries[num]
    window[KT_URL(num)].update(f'pip install --upgrade {zip_url({"repo": e.repo, "branch": e.branch})}' if e.repo else 'no GitHub repo - PyPI releases only')


def set_border(window, num):
    window[KT_ENTRY(num)].update(border_color=C_ENTRY_CHECKED if window[KT_CBOX(num)].get() else C_ENTRY_BORDER)


def checked(window):
    return [n for n in S.entries if window[KT_CBOX(n)].get()]


def list_changed(window):
    """The scroll region goes stale when entries come and go - refresh it"""
    window.refresh()
    window[K_LIST].contents_changed()
    window.refresh()


def add_entry(window, name='', repo='', branch='main'):
    """New entry at the end of the list; returns its number"""
    num = S.next_num
    S.next_num += 1
    window.extend_layout(window[K_LIST], [[make_entry(num)]])
    list_changed(window)
    wire_entry(window, num)
    e = S.entries[num]
    e.name, e.repo, e.branch = name, repo, branch
    show_entry(window, num)
    return num


def delete_entry(window, num):
    """Remove an entry's elements from the window (PySimpleGUI has no element delete, so the tk widgets are destroyed and the bookkeeping cleaned)"""
    elem = window[KT_ENTRY(num)]
    for key in [k for k in window.key_dict if isinstance(k, tuple) and len(k) == 2 and k[1] == num]:
        if key != KT_ENTRY(num):
            del window.AllKeysDict[key]
    row_frame = elem.ParentRowFrame
    elem.Widget.destroy()
    if not row_frame.winfo_children():
        row_frame.destroy()
    remove_from_rows(elem.ParentContainer.Rows, elem)
    del window.AllKeysDict[KT_ENTRY(num)]
    del S.entries[num]
    list_changed(window)


def remove_from_rows(rows, target):
    for row in rows:
        if isinstance(row, list):
            if target in row:
                row.remove(target)
            else:
                remove_from_rows(row, target)


def move_entry_to_index(window, src, index):
    """Entry src becomes number `index` in the list (counting the other entries); the ones in between shift.  The contents move, the entries stay"""
    nums = list(S.entries)
    contents = [(S.entries[n].name, S.entries[n].repo, S.entries[n].branch, window[KT_CBOX(n)].get()) for n in nums]
    contents.insert(index, contents.pop(nums.index(src)))
    for n, (name, repo, branch, is_checked) in zip(nums, contents):
        e = S.entries[n]
        e.name, e.repo, e.branch = name, repo, branch
        show_entry(window, n)
        window[KT_CBOX(n)].update(is_checked)
        set_border(window, n)


def scroll_to(window, num):
    window.refresh()
    inner = window[K_LIST].widget.TKFrame
    row = window[KT_ENTRY(num)].Widget.master
    window[K_LIST].widget.canvas.yview_moveto(max(0, row.winfo_y() - 30) / max(1, inner.winfo_height()))


def insert_entry(window, name='', repo='', branch='main'):
    """+ Add (or a dropped link): the new entry goes above the first checked entry, or at the end; the list scrolls to it and its name is selected"""
    first_checked = checked(window)[:1]
    num = add_entry(window, name, repo, branch)
    target = num
    if first_checked:
        index = list(S.entries).index(first_checked[0])
        move_entry_to_index(window, num, index)
        target = list(S.entries)[index]
    scroll_to(window, target)
    window[KT_NAME(target)].set_focus()
    window[KT_NAME(target)].update(select=True)
    return target


def fill_from_link(window, num, text):
    """A GitHub link pasted or dropped onto an entry: split it into repo + branch, and name the package after the repo if it has no name yet"""
    found = parse_github(text)
    if not found:
        return False
    e = S.entries[num]
    e.repo, branch = found
    e.branch = branch or e.branch or 'main'
    if not e.name.strip():
        e.name = e.repo.split('/')[-1]
    show_entry(window, num)
    return True


# ---------- drag the grip to reorder (from PSG Dock) ----------
def drag_lift(window, drag, y_root):
    """The press has become a drag: lift the entry out as a floating copy that follows the mouse, and leave a slot where it was"""
    src_row = window[KT_ENTRY(drag['src'])].Widget.master                       # the row frame PySimpleGUI packed the entry into
    parent = src_row.master
    siblings = parent.pack_slaves()
    i = siblings.index(src_row)
    drag['row'], drag['parent'] = src_row, parent
    drag['next_row'] = siblings[i + 1] if i + 1 < len(siblings) else None
    info = src_row.pack_info()
    info.pop('in', None)
    drag['pack_info'] = info
    drag['pads'] = {'padx': info.get('padx', 0), 'pady': info.get('pady', 0)}
    w, h = src_row.winfo_width(), src_row.winfo_height()
    drag['grab_dy'] = y_root - src_row.winfo_rooty()
    drag['x'] = src_row.winfo_rootx()
    gap = tk.Frame(parent, width=w, height=h, bg=C_SLOT, highlightthickness=2, highlightbackground=C_SLOT_OUTLINE, highlightcolor=C_SLOT_OUTLINE)     # where it will land
    gap.pack_propagate(False)
    gap.pack(before=src_row, fill='x', **drag['pads'])
    window.grab_any_where_off()                                                 # the window stays put while an entry is dragged (back on at the drop)
    src_row.pack_forget()
    drag['gap'], drag['index'] = gap, None
    e = S.entries[drag['src']]
    top = tk.Toplevel(window.TKroot)                                            # the floating copy
    top.overrideredirect(True)
    top.attributes('-topmost', True)
    try:
        top.attributes('-alpha', 0.92)
    except tk.TclError:
        pass
    bg, field = TOYBOX_DARK['BACKGROUND'], TOYBOX_DARK['INPUT']
    body = tk.Frame(top, bg=bg, highlightthickness=2, highlightbackground=C_DRAG_OUTLINE, highlightcolor=C_DRAG_OUTLINE)
    body.pack(fill='both', expand=True)
    tk.Label(body, text=e.name.strip() or '(no name)', bg=field, fg=TOYBOX_DARK['TEXT_INPUT'], font=('Segoe UI', 12, 'bold'), anchor='w').pack(fill='x', padx=(34, 8), pady=(6, 2))
    tk.Label(body, text=e.repo or 'no GitHub repo', bg=bg, fg=C_UI_DIM, font=('Segoe UI', 10), anchor='w').pack(fill='x', padx=(34, 8), pady=(0, 6))
    top.update_idletasks()
    top.geometry(f'{w}x{body.winfo_reqheight()}+{drag["x"]}+{y_root - drag["grab_dy"]}')
    drag['top'] = top
    n = drag['src']                                                             # the copy is under the pointer, so it may get the mouse events
    top.bind('<B1-Motion>', lambda ev: window.write_event_value(K_DRAG_MOTION, (n, ev.x_root, ev.y_root)))
    top.bind('<ButtonRelease-1>', lambda ev: window.write_event_value(K_DRAG_RELEASE, (n, ev.x_root, ev.y_root)))
    try:                                        # the grip's row was just unmapped, which ends the mouse capture: grab every mouse event for the copy instead,
        top.update()                            # or a pointer that leaves the list would drag the whole window (grab_anywhere) and the release would be lost
        top.grab_set()
    except tk.TclError:
        pass
    window.set_cursor('fleur')
    drag_motion(window, drag, drag['x'], y_root)


def drag_motion(window, drag, x_root, y_root):
    """Mouse moved with the grip held: move the floating copy, move the slot to where the entry would land, scroll near the edges"""
    if not drag['moved']:
        if abs(y_root - drag['y']) < DRAG_START:
            return
        drag['moved'] = True
        drag_lift(window, drag, y_root)
        return
    column = window[K_LIST].widget
    low, high = column.winfo_rooty(), column.winfo_rooty() + column.winfo_height() - drag['top'].winfo_height()
    drag['top'].geometry(f'+{drag["x"]}+{min(max(y_root - drag["grab_dy"], low), high)}')       # the copy never leaves the list
    top, bottom = column.winfo_rooty(), column.winfo_rooty() + column.winfo_height()
    if y_root < top + AUTOSCROLL_EDGE:
        column.canvas.yview_scroll(-1, 'units')
    elif y_root > bottom - AUTOSCROLL_EDGE:
        column.canvas.yview_scroll(1, 'units')
    entry_rows = {window[KT_ENTRY(n)].Widget.master for n in S.entries}
    rows = [r for r in drag['parent'].pack_slaves() if r in entry_rows]          # the other entries, top to bottom
    index = len(rows)
    for i, row in enumerate(rows):
        if y_root < row.winfo_rooty() + row.winfo_height() / 2:
            index = i
            break
    if index != drag['index']:
        drag['gap'].pack_forget()
        if index < len(rows):
            drag['gap'].pack(before=rows[index], fill='x', **drag['pads'])
        else:
            drag['gap'].pack(fill='x', **drag['pads'])
        drag['index'] = index
        window[K_LIST].contents_changed()


def drag_release(window, drag):
    """Drop: put the entry's row back, then move its contents to the slot's position.  Returns True if the order changed"""
    if not drag['moved']:
        return False
    try:
        window.set_cursor('')
        next_row = drag['next_row']
        if next_row is not None and next_row.winfo_exists():
            drag['row'].pack(before=next_row, **drag['pack_info'])
        else:
            drag['row'].pack(**drag['pack_info'])
    finally:                                                                    # whatever happens, the floating copy and the slot go away
        window.grab_any_where_on()
        for key in ('top', 'gap'):
            try:
                drag[key].destroy()
            except Exception:
                pass
    list_changed(window)
    if drag['index'] is None or drag['index'] == list(S.entries).index(drag['src']):
        return False
    move_entry_to_index(window, drag['src'], drag['index'])
    return True


# ---------- the window ----------
def title_strip(title, close_key, note=f'v{VERSION}'):
    """Toybox-style strip across the top:  [icon] title  v1.0 ............ x   (drag the window by it).  note = the small text after the title"""
    row = [sg.Image(data=ICON, subsample=2, background_color=C_STRIP, p=((10, 6), 6)),
           sg.Text(title, font=('Segoe UI', 13, 'bold'), text_color=C_STRIP_TEXT, background_color=C_STRIP, p=(0, 6)),
           sg.Text(note, font=('Segoe UI', 9), text_color=C_UI_DIM, background_color=C_STRIP, p=((6, 0), (10, 4))),
           sg.Push(background_color=C_STRIP),
           sg.Text('  ✕  ', key=close_key, font=('Segoe UI', 12), text_color=C_UI_DIM, background_color=C_STRIP, enable_events=True, p=0, tooltip='Close (Escape)')]
    return [sg.Column([row], background_color=C_STRIP, expand_x=True, p=0)]


def confirm(window, question, title='Confirm'):
    """Yes / No that is sure to appear ON TOP of the keep-on-top settings window"""
    window.keep_on_top_clear()
    x, y = window.current_location()
    answer = sg.popup_yes_no(question, title=title, keep_on_top=True, modal=True, location=(x + 120, y + 120), font=('Segoe UI', 11), icon=ICON)
    window.keep_on_top_set()
    window.bring_to_front()
    return answer == 'Yes'


def update_status(window):
    """Status bar and the Apply button color (gold = unsaved changes)"""
    n = len(S.entries)
    window[K_STATUS].update(f'{n} package{"s" * (n != 1)}  ·  {len(checked(window))} checked  ·  {"UNSAVED CHANGES" if S.dirty else "saved"}',
                            text_color=COLOR_DIRTY_TEXT if S.dirty else TOYBOX_DARK['TEXT'])
    window[K_APPLY].update(button_color=COLOR_SAVE_DIRTY if S.dirty else sg.theme_button_color())


def save_entries(window):
    packages = []
    for n, e in S.entries.items():
        found = parse_github(e.repo) if 'github' in e.repo.lower() else None            # a link that was typed rather than pasted
        if found:
            e.repo, e.branch = found[0], found[1] or e.branch
        if e.name.strip() or e.repo.strip():
            packages.append({'name': e.name.strip() or e.repo.split('/')[-1], 'repo': e.repo.strip(), 'branch': e.branch.strip() or 'main'})
    sg.user_settings_set_entry(K_PACKAGES, packages)
    sg.popup_quick_message(f'Saved {len(packages)} package{"s" * (len(packages) != 1)}', font=('Segoe UI', 16), text_color='white', background_color='#2e7d32', keep_on_top=True)


def settings_window(location=(None, None), anchor=None):
    """The package-list window.  Returns True if anything was saved"""
    S.entries, S.next_num, S.dirty, S.drag = {}, 0, False, None
    packages = load_packages() or [{'name': '', 'repo': '', 'branch': 'main'}]           # an empty list starts with one blank entry to fill in
    toolbar = [sg.Button('+ Add', k=K_ADD, tooltip='Add a package - above the first checked entry, or at the end'),
               sg.Button('− Delete', k=K_DELETE, button_color=COLOR_DANGER, tooltip='Delete the checked entries'),
               sg.Button('Clear all', k=K_CLEAR, button_color=COLOR_DANGER, tooltip='Remove every entry   (nothing is written until OK or Apply)'),
               sg.VerticalSeparator(p=(8, 2)),
               sg.Button('☑ All', k=K_SEL_ALL, tooltip='Check every entry'),
               sg.Button('☐ None', k=K_SEL_NONE, tooltip='Uncheck every entry'),
               sg.Push(),
               sg.Button('  OK  ', k=K_OK, button_color=COLOR_SAVE, tooltip='Save and close   (Ctrl+S)'),
               sg.Button('Apply', k=K_APPLY, tooltip='Save but stay open'),
               sg.Button('Cancel', k=K_CANCEL, tooltip='Close without saving   (Escape)')]
    entries = [[make_entry(n)] for n in range(len(packages))]
    S.next_num = len(packages)
    hint_text = 'Drag ☰ to reorder.   Paste a GitHub link into a repo box' + (' or drop one onto the list.' if psgdnd else '.')
    status_bar = [sg.Text('', k=K_STATUS, font=('Segoe UI', 10)), sg.Push(),                   # file name only - the full path is in its tooltip, so the bar stays narrow
                  sg.Text(os.path.basename(sg.user_settings_filename()), font=('Segoe UI', 9), text_color=C_UI_FAINT, tooltip=sg.user_settings_filename()), sg.Sizegrip()]
    body = [title_strip(f'{APP_NAME} Settings', K_STRIP_CLOSE),
            [sg.Column([toolbar], expand_x=True, p=(8, (8, 2)))],
            [sg.Text(hint_text, font=('Segoe UI', 9), text_color=C_UI_DIM, p=(12, (2, 4)))],
            [sg.Column(entries, k=K_LIST, size=(None, LIST_HEIGHT), scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True, p=(6, 2))],
            [sg.Column([status_bar], expand_x=True, p=(8, (2, 4)))]]
    layout = [[sg.Frame('', body, border_width_no_relief=1, border_color=C_ENTRY_BORDER, p=0, expand_x=True, expand_y=True)]]
    window = sg.Window(f'{APP_NAME} Settings', layout, no_titlebar=True, grab_anywhere=True, keep_on_top=True, finalize=True, margins=(0, 0), icon=ICON, resizable=True,
                       location=location, location_anchor=anchor, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, right_click_menu_background_color=C_MENU_BG,
                       right_click_menu_text_color=C_MENU_TEXT, right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU)
    style_menus(window.TKRightClickMenu)
    scroller = window[K_LIST].widget                                                    # entries stretch to the list's width (the inner frame is a canvas window item)
    scroller.canvas.bind('<Configure>', lambda e: scroller.canvas.itemconfigure(scroller.frame_id, width=e.width), add='+')
    close = window[K_STRIP_CLOSE].Widget
    close.bind('<Enter>', lambda e: close.configure(bg=C_CLOSE, fg='#ffffff'))
    close.bind('<Leave>', lambda e: close.configure(bg=C_STRIP, fg=C_UI_DIM))
    if psgdnd:
        try:
            psgdnd.register_element_dnd(window[K_LIST], window, psgdnd.DROP_TYPE_ALL)       # a link dropped between entries adds a new one
            S.dnd = True
        except Exception:
            S.dnd = False
    for n, p in enumerate(packages):
        wire_entry(window, n)
        e = S.entries[n]
        e.name, e.repo, e.branch = p['name'], p['repo'], p['branch']
        show_entry(window, n)
    list_changed(window)
    scroller.canvas.itemconfigure(scroller.frame_id, width=scroller.canvas.winfo_width())     # the <Configure> binding came after the first layout
    for key, seq in ((K_PAGE_UP, '<Prior>'), (K_PAGE_DOWN, '<Next>'), (K_HOME, '<Home>'), (K_END, '<End>'), (K_CANCEL, '<Escape>'), (K_OK, '<Control-s>')):
        window.bind(seq, key)
    canvas = window[K_LIST].widget.canvas
    saved = False
    update_status(window)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in (K_CANCEL, K_STRIP_CLOSE, 'Exit'):
            if not S.dirty or confirm(window, 'Discard your unsaved changes?', 'Unsaved changes'):
                break
            continue
        if event == K_OK:
            save_entries(window)
            saved = True
            break
        if psgdnd and psgdnd.is_drop_event(event):                                  # a GitHub link dropped from the browser
            text = str(values[event]).split(',')[0]
            num = event.key[1] if isinstance(event.key, tuple) else None
            if num in S.entries and fill_from_link(window, num, text):
                S.dirty = True
            elif num is None and parse_github(text):
                fill_from_link(window, insert_entry(window), text)
                S.dirty = True
            else:
                sg.popup_quick_message('That is not a GitHub link', font=('Segoe UI', 12), text_color='white', background_color='#b71c1c', keep_on_top=True)
        elif event == K_ADD:
            insert_entry(window)
            S.dirty = True
        elif event == K_DELETE:
            for n in checked(window):
                delete_entry(window, n)
                S.dirty = True
        elif event == K_CLEAR:
            if S.entries and confirm(window, 'Remove every package from the list?'):
                for n in list(S.entries):
                    delete_entry(window, n)
                S.dirty = True
        elif event == K_APPLY:
            save_entries(window)
            saved, S.dirty = True, False
        elif event in (K_SEL_ALL, K_SEL_NONE):
            for n in S.entries:
                window[KT_CBOX(n)].update(event == K_SEL_ALL)
                set_border(window, n)
        elif event == K_DRAG_PRESS:
            num, x_root, y_root = values[event]
            if num in S.entries:
                S.drag = {'src': num, 'y': y_root, 'moved': False}
        elif event == K_DRAG_MOTION:
            if S.drag is not None:
                drag_motion(window, S.drag, *values[event][1:])
        elif event == K_DRAG_RELEASE:
            if S.drag is not None:
                if drag_release(window, S.drag):
                    S.dirty = True
                S.drag = None
        elif event == K_PAGE_UP:
            canvas.yview_scroll(-1, 'pages')
        elif event == K_PAGE_DOWN:
            canvas.yview_scroll(1, 'pages')
        elif event == K_HOME:
            canvas.yview_moveto(0)
        elif event == K_END:
            canvas.yview_moveto(1)
        elif event == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME} v{VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10), icon=ICON)
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif isinstance(event, tuple) and event[1] in S.entries:                     # the elements inside an entry
            kind, num = event
            e = S.entries[num]
            if kind == K_DEL:
                delete_entry(window, num)
                S.dirty = True
            elif kind == K_CBOX:
                set_border(window, num)
            elif kind == K_NAME:
                e.name = values[event]
                S.dirty = True
            elif kind == K_BRANCH:
                e.branch = values[event]
                show_url(window, num)
                S.dirty = True
            elif kind == K_REPO:
                new = values[event]
                if len(new) - len(e.repo) > 1 and 'github' in new.lower():       # a pasted link (several characters arrived at once)
                    if not fill_from_link(window, num, new):
                        e.repo = new
                else:
                    e.repo = new
                show_url(window, num)
                S.dirty = True
        update_status(window)
    window.close()
    return saved


# Settings window images - 25 x 25 trash can (amber, red on hover), from PSG Dock
TRASH_RED = b'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAMAAADzN3VRAAAASFBMVEUAAAD/AAD/AADrAAD/AAD/AADcAAD/AADtAAD3AADYAAD/AAD/AADwAADuAADuAAD6AADrAAD/AADOAAD/AACmAACtAAD/AADCW8QwAAAAF3RSTlMA/fnH2GWN3bGkhVru1Mq6uZOISjcaGe/TegUAAACDSURBVHiczZHtCsMgDEWTOKvWfrfbff83HYngHF3/bbCDYLjHqCjRb9huyvYeLiGEIFBEy6WawUJWrBqqOUZLuUgej9d2DmWxtcI1BzkIkp8x+wQ5mUw9esofjKcOHfm/NPny1useEff1ZK5eZ2JhHWWaGpNqh5Iac4/2oYX4aMy3eALVGAyXRSQ2kQAAAABJRU5ErkJggg=='
TRASH = b'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAMAAADzN3VRAAAAXVBMVEUAAADJoibJoifJoSbJoibIoiXKoCXJoibKoCbOpijIoibJoSfJoibJoibJoibIoSbWrSrIoSbJoSfNpijHoSXIoCjEnCfMoyjTqSnYrSrQqCjPpijmuSzJoifesytghzcEAAAAGHRSTlMA+cf92I1lhVjQzaOVy/Lf2LKvq0ozGhkawlE6AAAAnklEQVR4nM2RSQ6DMAxFbRLIwDy1xia5/zERSAUK6q6V+qR44SfFyTfAbzCN1rox783cld5XJCxUeV+6fDd1FKagVgKxxHo3oxPc2mtBceNxXUIqMIkS4qAoOQ1KCKmwbWxtQXg1kwUzG7DT3WSQzilkf2nsp1dTMXSxG+4/VUFItnNJh1HhGiqiQi7PC4rCLyQe6wF49Pqgf57Mt1gAAwEOREh/iwwAAAAASUVORK5CYII='


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback('Crash', e)
