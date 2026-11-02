#!/usr/bin/env python3
"""
github_repo_watch.pyw  -  A quiet desktop widget that notices new activity on GitHub repos you care about.

GitHub's "Watch" never emails you about plain commits, so this polls the API for you and shows a small
always-on-top widget instead of nagging you with popups.

THE WIDGET
    ● PySimpleGUI      2 issues  3 new  ▂▃▁▅▂▇▃    dot: green = something new · grey = quiet · amber = checking · red = problem
      PySimpleGUI · pushed 2 hours ago             blue chip: issue news (amber "N waiting" = people waiting on your reply)
                                                   green badge: new commits / branches / tags / releases / PRs
                                                   sparkline: commits per day over the last 14 days
    Click a row       ->  "What's new" window: a plain-English digest, every new commit / branch / tag / release / issue / PR,
                          click any commit for a colored diff peek, a 30-day activity chart and rhythm stats.
    Click the chip    ->  Issues window (see ISSUES below)
    ≡ or right-click  ->  Check now · Mark all read · Pause · Snooze · Snap to corner · Settings · Edit Me · Version · Exit
    Drag it anywhere; its position is remembered.  The faint ✕ in the top-right corner closes it.

    ⇄ (next to ≡) switches to the ISSUES VIEW and back - the choice is remembered:
    PySimpleGUI issues                3 new · 4 waiting
    ● #6918 Table: right-click menu…      COMMENT  40m     dot: green = open · purple = closed
      tablefan · 2 comments · Bug                          badge: NEW / COMMENT / CLOSED = news · WAITING = someone is waiting on you
    Click an issue -> the Issues window, open at that issue.  Click the title to step through the watched repos that have issues;
    Settings picks the repo and how many rows show.

ISSUES  (the support queue)
    Repos with open issues get their conversations checked as well.  News = a new issue, a comment from someone else, or an issue
    closed by someone else.  Your own comments and closes never count, and neither do label changes or edits.  The Issues window lists
        NEW SINCE YOU LOOKED   that news, newest first
        WAITING ON YOU         open issues where someone other than you or a collaborator had the last word, within the
                               "Activity history" setting (30 days by default) - longest wait first
        OPEN                   the rest of the open issues, most recently active first
    Click an issue to read the whole conversation (you and collaborators in green, everyone else in blue, code in grey boxes);
    "Reply on GitHub" opens it in your browser.  "Mark issues read" clears the blue chip without touching the commit news.

ACCOUNTS
    A settings line can be a whole account instead of one repo ("PySimpleGUI" or "PySimpleGUI/*"): every non-archived repo it owns is
    watched, and new repos show up by themselves.  "Choose repos…" in Settings lists an account's repos so you can tick just the ones you want.
    With many repos, the widget shows only the ones with news or problems and folds the rest into one "N quiet repos" line (click it for
    the full list).  Untick "collapse" in Settings if you want a row per repo.

TOKEN
    Settings -> paste a GitHub token that can read the repo (fine-grained: Contents + Metadata + Issues read, or classic 'repo').
    Leave it blank to use the GITHUB_TOKEN / GH_TOKEN environment variable, or your `gh auth login` session.
    Polls use ETag conditional requests, so a quiet repo costs nothing against your API quota.

    python github_repo_watch.pyw --demo        made-up data, no token, no network (handy for trying the UI)

CHANGELOG
    1.0   20-Sep-2026   Commits / branches / tags / releases / issues / PRs, whole accounts, quiet repos fold into one row
    1.1   28-Oct-2026   Faint ✕ in the top-right corner closes the widget (saved as github_repo_watch_v1_1.pyw - never replaced this file)
    1.2   30-Oct-2026   Issues: blue issue chip on each row, Issues window (new / waiting on you / open) with whole conversations;
                        your own comments and closes no longer count as news; the ✕ from 1.1; the mouse wheel scrolls the What's new
                        and Issues lists anywhere over the list; version shown in the Settings title and the status line tooltip
    1.3   30-Oct-2026   Two primary views, switched with the ⇄ next to ≡ (or the menu) and remembered: the repo rows, or a list of one
                        repo's issues - "#142 title / who · comments · labels" with NEW / COMMENT / CLOSED / WAITING badges and an age column;
                        click an issue to read it, click the title to step through the watched repos that have issues
    1.4   01-Nov-2026   Keep on top can be turned off - right-click / ≡ menu (✓ when on) or Settings; remembered between runs.
                        Version popup shows the app's version, and its X closes it

Needs only PySimpleGUI - everything else is stdlib.  Settings + unread state live in github_repo_watch.json in PySimpleGUI's
user-settings folder; problems are logged to github_repo_watch.log in the same folder.
"""
import ctypes
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from collections import Counter
from datetime import date, datetime, timedelta, timezone

import PySimpleGUI as sg

APP_NAME = 'GitHub Repo Watch'
VERSION = '1.4'
SETTINGS_FILE = 'github_repo_watch.json'
LOG_FILE_NAME = 'github_repo_watch.log'
API = 'https://api.github.com'
DEMO = '--demo' in sys.argv
AUTO_OPEN = '--open' in sys.argv
DETAIL_FETCH_LIMIT = 25         # newest new commits whose files + patch are fetched during a poll (older ones fetch when clicked)
MAX_PATCH_LINES = 1500          # diff peek stops here and tells you to open GitHub for the rest
EARLIER_LIMIT = 60              # how many already-seen commits to list under "Earlier"
SPARK_DAYS = 14
OPEN_ISSUE_LIMIT = 60           # open issues listed under "Open" in the Issues window (the rest are a click away on GitHub)
MAX_THREAD_POSTS = 80           # comments shown in the issue reader; a longer conversation says how many more are on GitHub
MAX_POST_CHARS = 6000           # one issue / comment body is cut at this length in the reader
MAINTAINER_ROLES = ('OWNER', 'MEMBER', 'COLLABORATOR')                  # GitHub author_association values whose replies answer an issue
ROLE_TEXT = {'OWNER': 'owner', 'MEMBER': 'member', 'COLLABORATOR': 'collaborator', 'CONTRIBUTOR': 'contributor', 'FIRST_TIME_CONTRIBUTOR': 'first-time contributor',
             'FIRST_TIMER': 'first-timer'}

# ---------------------------------------------------------------- colors (GitHub dark palette) ----------------------------------------------------------------
C_BG, C_BG2, C_BG3, C_LINE = '#0d1117', '#161b22', '#21262d', '#30363d'
C_TEXT, C_MUTED, C_DIM = '#e6edf3', '#8b949e', '#484f58'
C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK = '#3fb950', '#f85149', '#d29922', '#58a6ff', '#bc8cff', '#f778ba'
KIND_COLOR = {'commit': C_GREEN, 'merge': C_GREEN, 'branch': C_AMBER, 'tag': C_PURPLE, 'release': C_PURPLE, 'issue': C_BLUE, 'pr': C_PINK}
STATUS_COLOR = {'added': C_GREEN, 'removed': C_RED, 'modified': C_AMBER, 'renamed': C_BLUE, 'copied': C_BLUE, 'changed': C_AMBER}
UI_FONT = 'Segoe UI' if sg.running_windows() else 'DejaVu Sans'
MONO_FONT = 'Consolas' if sg.running_windows() else 'DejaVu Sans Mono'

# ---------------------------------------------------------------- keys ----------------------------------------------------------------
# widget window
K_STATUS = '-STATUS-'
K_MENU = '-MENU-'
K_CLOSE_X = '-CLOSE X-'
K_CLICK = '-CLICK-'                                             # value = repo (widget) or item index (details window)
K_POLL_BUSY = '-POLL BUSY-'                                     # value = repo being checked right now
K_POLL_RESULT = '-POLL RESULT-'                                 # value = snapshot dict
K_ROW = '-ROW-';            KT_ROW = lambda repo: (K_ROW, repo)
K_DOT = '-DOT-';            KT_DOT = lambda repo: (K_DOT, repo)
K_NAME = '-NAME-';          KT_NAME = lambda repo: (K_NAME, repo)
K_META = '-META-';          KT_META = lambda repo: (K_META, repo)
K_BADGE = '-BADGE-';        KT_BADGE = lambda repo: (K_BADGE, repo)
K_SPARK = '-SPARK-';        KT_SPARK = lambda repo: (K_SPARK, repo)
K_ICHIP = '-ISSUE CHIP-';   KT_ICHIP = lambda repo: (K_ICHIP, repo)             # also what a click on the chip reports
# details window
K_DIGEST = '-DIGEST-'
K_LIST = '-LIST-'
K_ITEM = '-ITEM-';          KT_ITEM = lambda idx: (K_ITEM, idx)
K_ADD = '-ADD-';            KT_ADD = lambda idx: (K_ADD, idx)
K_DEL = '-DEL-';            KT_DEL = lambda idx: (K_DEL, idx)
K_ITEM_META = '-ITEM META-'; KT_ITEM_META = lambda idx: (K_ITEM_META, idx)
K_DETAIL = '-DETAIL-'
K_DETAIL_READY = '-DETAIL READY-'                               # value = (sha, detail dict or error string)
K_FRESH = '-FRESH-'
K_OPEN = '-OPEN-'
K_COPY_SHA = '-COPY SHA-'
K_COPY_LINK = '-COPY LINK-'
K_MARK_READ = '-MARK READ-'
K_REFRESH = '-REFRESH-'
K_OPEN_REPO = '-OPEN REPO-'
K_COPY_DIGEST = '-COPY DIGEST-'
K_ISSUES_BTN = '-ISSUES BTN-'
K_THREAD_READY = '-THREAD READY-'                               # value = (repo, issue number, conversation dict or error string)
# issues window
K_IS_LIST = '-IS LIST-'
K_IS_ITEM = '-IS ITEM-';    KT_IS_ITEM = lambda idx: (K_IS_ITEM, idx)
K_IS_CHIP = '-IS CHIP-';    KT_IS_CHIP = lambda idx: (K_IS_CHIP, idx)
K_IS_THREAD = '-IS THREAD-'
K_IS_DIGEST = '-IS DIGEST-'
K_IS_FRESH = '-IS FRESH-'
K_IS_REPLY = '-IS REPLY-'
K_IS_COPY = '-IS COPY-'
K_IS_READ = '-IS READ-'
K_IS_REFRESH = '-IS REFRESH-'
K_IS_ALL = '-IS ALL-'
K_CLOSE = '-CLOSE-'
K_CHART = '-CHART-'
K_RHYTHM = '-RHYTHM-'
K_KEY_UP = '-K UP-'
K_KEY_DOWN = '-K DOWN-'
K_KEY_PGUP = '-K PGUP-'
K_KEY_PGDN = '-K PGDN-'
K_KEY_HOME = '-K HOME-'
K_KEY_END = '-K END-'
K_KEY_LEFT = '-K LEFT-'
K_KEY_RIGHT = '-K RIGHT-'
K_KEY_ESC = '-K ESC-'
K_KEY_SUP = '-K S UP-'
K_KEY_SDOWN = '-K S DOWN-'
K_KEY_SPGUP = '-K S PGUP-'
K_KEY_SPGDN = '-K S PGDN-'
K_KEY_SHOME = '-K S HOME-'
K_KEY_SEND = '-K S END-'
LIST_KEYS = (K_KEY_UP, K_KEY_DOWN, K_KEY_PGUP, K_KEY_PGDN, K_KEY_HOME, K_KEY_END, K_KEY_LEFT, K_KEY_RIGHT)
PANE_KEYS = (K_KEY_SUP, K_KEY_SDOWN, K_KEY_SPGUP, K_KEY_SPGDN, K_KEY_SHOME, K_KEY_SEND)
KEY_BINDS = (('<Up>', K_KEY_UP), ('<Down>', K_KEY_DOWN), ('<Prior>', K_KEY_PGUP), ('<Next>', K_KEY_PGDN), ('<Home>', K_KEY_HOME), ('<End>', K_KEY_END),
             ('<Left>', K_KEY_LEFT), ('<Right>', K_KEY_RIGHT), ('<Escape>', K_KEY_ESC), ('<Shift-Up>', K_KEY_SUP), ('<Shift-Down>', K_KEY_SDOWN),
             ('<Shift-Prior>', K_KEY_SPGUP), ('<Shift-Next>', K_KEY_SPGDN), ('<Shift-Home>', K_KEY_SHOME), ('<Shift-End>', K_KEY_SEND))
KEYS_HINT = '↑↓ PgUp PgDn Home End scroll the list · Shift+ scrolls this pane · ←→ sideways · Esc closes'
DOT_TIP = 'Grey: quiet · Green: something new · Amber: checking · Red: problem'
ISSUES_HINT = '↑↓ PgUp PgDn Home End scroll the list · Shift+ scrolls the conversation · Esc closes'
CHIP_TIP = 'Issues - click for the Issues window'
# settings window (string keys - these are also the names saved in the settings file)
K_REPOS = '-REPOS-'
K_TOKEN = '-TOKEN-'
K_INTERVAL = '-INTERVAL-'
K_HISTORY_DAYS = '-HISTORY DAYS-'
K_OPACITY = '-OPACITY-'
K_FONT_SIZE = '-FONT SIZE-'
K_MARK_ON_CLOSE = '-MARK ON CLOSE-'
K_QUIET_ON = '-QUIET ON-'
K_QUIET_FROM = '-QUIET FROM-'
K_QUIET_TO = '-QUIET TO-'
K_KEEP_ON_TOP = '-KEEP ON TOP-'
K_SAVE = '-SAVE-'
K_CANCEL = '-CANCEL-'
K_TEST = '-TEST-'
K_TEST_RESULT = '-TEST RESULT-'
K_PICK = '-PICK-'                                               # settings: "Choose repos…" button
K_PICK_READY = '-PICK READY-'                                   # value = (owner, list of repo dicts, or an error string)
K_PICK_ROW = '-PICK ROW-';  KT_PICK_ROW = lambda idx: (K_PICK_ROW, idx)
K_PICK_LIST = '-PICK LIST-'
K_PICK_ALL = '-PICK ALL-'
K_PICK_NONE = '-PICK NONE-'
K_PICK_ACTIVE = '-PICK ACTIVE-'
K_PICK_OK = '-PICK OK-'
K_COLLAPSE = '-COLLAPSE QUIET-'
K_REPOS_RESOLVED = '-REPOS RESOLVED-'                           # value = {account: {'repos': [...], 'error': ''}} for account lines
K_ALL_LIST = '-ALL LIST-'
K_ALL_ROW = '-ALL ROW-';    KT_ALL_ROW = lambda repo: (K_ALL_ROW, repo)
QUIET_ROW = '(quiet)'                                           # pseudo repo id of the widget's "N quiet repos" summary row
K_STATE = '-STATE-'                                             # settings-file entry holding the per-repo unread bookkeeping
# issues view of the widget
K_VIEW = '-VIEW-'                                               # 'repos' or 'issues' - which primary view the widget shows
K_ISSUE_ROWS = '-ISSUE ROWS-'
K_ISSUES_REPO = '-ISSUES REPO-'                                 # repo the issues view shows ('' = the watched repo with the most open issues)
K_VIEW_TOGGLE = '-VIEW TOGGLE-'
K_ITITLE = '-ITITLE-'
K_IUNREAD = '-IUNREAD-'
K_IROW = '-IROW-';          KT_IROW = lambda i: (K_IROW, i)
K_IDOT = '-IDOT-';          KT_IDOT = lambda i: (K_IDOT, i)
K_INAME = '-INAME-';        KT_INAME = lambda i: (K_INAME, i)
K_IMETA = '-IMETA-';        KT_IMETA = lambda i: (K_IMETA, i)
K_IBADGE = '-IBADGE-';      KT_IBADGE = lambda i: (K_IBADGE, i)
K_IAGE = '-IAGE-';          KT_IAGE = lambda i: (K_IAGE, i)
VIEW_REPOS, VIEW_ISSUES = 'repos', 'issues'
ISSUE_ROW_CHOICES = [4, 6, 8, 10, 12, 15]
# menu items (right-click menu returns the whole string, ButtonMenu returns it in values[K_MENU])
M_CHECK = 'Check now::-M CHECK-'
M_READ = 'Mark all as read::-M READ-'
M_PAUSE = 'Pause / resume polling::-M PAUSE-'
M_SNOOZE_1 = 'Hide badges for 1 hour::-M SNOOZE 1-'
M_SNOOZE_4 = 'Hide badges for 4 hours::-M SNOOZE 4-'
M_SNOOZE_TOMORROW = 'Hide badges until tomorrow::-M SNOOZE TOMORROW-'
M_SNOOZE_OFF = 'Show badges again::-M SNOOZE OFF-'
M_SNAP_TL = 'Top left::-M SNAP TL-'
M_SNAP_TR = 'Top right::-M SNAP TR-'
M_SNAP_BL = 'Bottom left::-M SNAP BL-'
M_SNAP_BR = 'Bottom right::-M SNAP BR-'
M_SETTINGS = 'Settings...::-M SETTINGS-'
M_LOG = 'Open log file::-M LOG-'
M_ABOUT = 'About::-M ABOUT-'
M_TOP = 'Keep on top::-M TOP-'                                  # label gets a ✓ while it's on (show_keep_on_top)
MENU_SNOOZE = [M_SNOOZE_1, M_SNOOZE_4, M_SNOOZE_TOMORROW, M_SNOOZE_OFF]
MENU_SNAP = [M_SNAP_TL, M_SNAP_TR, M_SNAP_BL, M_SNAP_BR]
# the standard 'Edit Me' / 'Version' / 'Exit' trio from sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT sits at the bottom of the app's own menu
M_VIEW = 'Switch view  (repos ⇄ issues)::-M VIEW-'
MENU_ITEMS = [M_CHECK, M_READ, M_VIEW, '---', M_PAUSE, M_TOP, 'Snooze', MENU_SNOOZE, 'Snap to corner', MENU_SNAP, '---', M_SETTINGS, M_LOG, M_ABOUT, '---']
MENU = ['', MENU_ITEMS + sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT[1]]

HOURS = ['12 AM'] + [f'{h} AM' for h in range(1, 12)] + ['12 PM'] + [f'{h} PM' for h in range(1, 12)]
INTERVALS = ['1 min', '2 min', '5 min', '10 min', '15 min', '30 min', '60 min']
HISTORIES = ['14 days', '30 days', '60 days', '90 days']
DEFAULTS = {K_REPOS: 'jaynabonne/impulsing_ada', K_TOKEN: '', K_INTERVAL: '5 min', K_HISTORY_DAYS: '30 days', K_OPACITY: 94, K_FONT_SIZE: 11,
            K_MARK_ON_CLOSE: True, K_QUIET_ON: False, K_QUIET_FROM: '10 PM', K_QUIET_TO: '7 AM', K_COLLAPSE: True, K_VIEW: VIEW_REPOS, K_ISSUE_ROWS: 6,
            K_ISSUES_REPO: '', K_KEEP_ON_TOP: True}


# ================================================================ small helpers ================================================================
def cfg(key):
    return sg.user_settings_get_entry(key, DEFAULTS[key])


def log(msg):
    try:
        path = os.path.join(os.path.dirname(sg.user_settings_filename()), LOG_FILE_NAME)
        if os.path.exists(path) and os.path.getsize(path) > 1_000_000:
            os.remove(path)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n')
    except Exception:
        pass


def utcnow():
    return datetime.now(timezone.utc)


def parse_iso(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def clock(dt):
    return dt.strftime('%I:%M %p').lstrip('0')


def local_str(dt):
    """'Thu 3:12 PM' for the last week, 'Sep 3, 3:12 PM' this year, 'Sep 3, 2025' before that - all in the viewer's local time."""
    if dt is None:
        return 'never'
    local = dt.astimezone()
    days = (utcnow() - dt).total_seconds() / 86400
    if days < 6:
        return f'{local:%a} {clock(local)}'
    if local.year == datetime.now().year:
        return f'{local:%b} {local.day}, {clock(local)}'
    return f'{local:%b} {local.day}, {local.year}'


def ago(dt):
    if dt is None:
        return 'never'
    s = int((utcnow() - dt).total_seconds())
    if s < 60:
        return 'just now'
    m, h, d = s // 60, s // 3600, s // 86400
    if m < 60:
        return f'{m} min ago'
    if h < 24:
        return f'{h} hour{"s" if h > 1 else ""} ago'
    if d == 1:
        return 'yesterday'
    if d < 14:
        return f'{d} days ago'
    if d < 60:
        return f'{d // 7} weeks ago'
    return f'{d // 30} months ago'


def n_of(n, word, plural=None):
    return f'{n} {word if n == 1 else (plural or word + "s")}'


def shorten(text, width):
    text = ' '.join(str(text).split())
    return text if len(text) <= width else text[:width - 1].rstrip() + '…'


def top_folder(path):
    return path.split('/')[0] + '/' if '/' in path else '(root)'


def folder_summary(files):
    return ' · '.join(f'{folder} ×{n}' for folder, n in Counter(top_folder(f['name']) for f in files).most_common(3))


def hour12(h):
    return '12 AM' if h == 0 else f'{h} AM' if h < 12 else '12 PM' if h == 12 else f'{h - 12} PM'


def dpi_scale():
    try:
        return ctypes.windll.user32.GetDpiForSystem() / 96
    except Exception:
        return 1.0


def descendants(widget):
    out = [widget]
    for child in widget.winfo_children():
        out.extend(descendants(child))
    return out


def bind_click(window, widget_map):
    """Fire K_CLICK with the mapped target when a mouse press/release lands on the same spot (so dragging the widget doesn't count as a click)."""
    pressed = {}

    def on_press(e):
        pressed['at'] = (e.x_root, e.y_root)

    def on_release(e):
        x0, y0 = pressed.get('at', (e.x_root, e.y_root))
        target = widget_map.get(e.widget)
        if target is not None and abs(e.x_root - x0) < 6 and abs(e.y_root - y0) < 6:
            window.write_event_value(K_CLICK, target)

    window.TKroot.bind('<ButtonPress-1>', on_press, add='+')
    window.TKroot.bind('<ButtonRelease-1>', on_release, add='+')


def clean_entry(line):
    """'https://github.com/owner/name/', 'owner/name', 'owner/*' or 'owner' -> 'owner/name' or 'owner'."""
    return line.strip().strip('/').removeprefix('https://github.com/').removesuffix('/*').strip('/')


def parse_entries(text):
    seen, out = set(), []
    for line in str(text).replace(',', '\n').splitlines():
        e = clean_entry(line)
        if e and e.count('/') <= 1 and ' ' not in e and e.lower() not in seen:
            seen.add(e.lower())
            out.append(e)
    return out


def scroll_canvas(target, key):
    """Keyboard scrolling for a scrollable Column's canvas or a Multiline's text widget."""
    if key in (K_KEY_UP, K_KEY_SUP):
        target.yview_scroll(-1, 'units')
    elif key in (K_KEY_DOWN, K_KEY_SDOWN):
        target.yview_scroll(1, 'units')
    elif key in (K_KEY_PGUP, K_KEY_SPGUP):
        target.yview_scroll(-1, 'pages')
    elif key in (K_KEY_PGDN, K_KEY_SPGDN):
        target.yview_scroll(1, 'pages')
    elif key in (K_KEY_HOME, K_KEY_SHOME):
        target.yview_moveto(0)
    elif key in (K_KEY_END, K_KEY_SEND):
        target.yview_moveto(1)
    elif key == K_KEY_LEFT:
        target.xview_scroll(-4, 'units')
    elif key == K_KEY_RIGHT:
        target.xview_scroll(4, 'units')


def age_short(dt):
    """'40m', '5h', '2d', '3w', '4mo' - how long ago, for tight columns."""
    s = max(0, int((utcnow() - dt).total_seconds()))
    for limit, size, unit in ((3600, 60, 'm'), (86400, 3600, 'h'), (14 * 86400, 86400, 'd'), (60 * 86400, 7 * 86400, 'w')):
        if s < limit:
            return f'{max(1, s // size)}{unit}'
    return f'{s // (30 * 86400)}mo'


def span(dt):
    """'45 minutes', '3 hours', '2 days' - how long since dt, in words."""
    s = max(0, int((utcnow() - dt).total_seconds()))
    for limit, size, unit in ((3600, 60, 'minute'), (86400, 3600, 'hour'), (14 * 86400, 86400, 'day'), (60 * 86400, 7 * 86400, 'week')):
        if s < limit:
            return n_of(max(1, s // size), unit)
    return n_of(s // (30 * 86400), 'month')


def add_close_x(window, event_key):
    """A faint ✕ overlaid in the window's top-right corner - brightens under the pointer, closes the widget when clicked."""
    label = tk.Label(window.TKroot, text='✕', font=(UI_FONT, 9), fg=C_DIM, bg=C_BG, bd=0, cursor='hand2')
    label.place(relx=1.0, x=-3, y=1, anchor='ne')
    label.bind('<Enter>', lambda e: label.config(fg=C_RED))
    label.bind('<Leave>', lambda e: label.config(fg=C_DIM))
    label.bind('<ButtonRelease-1>', lambda e: window.write_event_value(event_key, None))


def show_keep_on_top(window, on):
    """Tick the 'Keep on top' entries in the window's menus (every right-click menu and the ≡ menu) when it's on.
    Only the label changes - the event the item sends stays M_TOP."""
    for w in descendants(window.TKroot):
        if w.winfo_class() != 'Menu' or w.index('end') is None:
            continue
        for i in range(w.index('end') + 1):
            if w.type(i) == 'command' and w.entrycget(i, 'label').lstrip('✓ ') == 'Keep on top':
                w.entryconfigure(i, label=('✓ ' if on else '') + 'Keep on top')


def wheel_scrolls_list(window, column_key):
    """The mouse wheel scrolls a scrollable Column wherever the pointer is over it.  PySimpleGUI hooks the wheel only while the pointer
    is over the bare canvas and drops it as soon as the pointer moves onto a row, so that hook is swapped for one on the window."""
    frame = window[column_key].TKColFrame
    canvas = frame.canvas
    canvas.unbind('<Enter>')
    canvas.unbind('<Leave>')
    frame.unhookMouseWheel(None)

    def on_wheel(e):
        try:
            w = window.TKroot.winfo_containing(*window.TKroot.winfo_pointerxy())
        except Exception:
            return
        while w is not None and w is not canvas:
            w = w.master
        if w is canvas and canvas.yview() != (0.0, 1.0):
            canvas.yview_scroll(-1 if (getattr(e, 'num', 0) == 4 or getattr(e, 'delta', 0) > 0) else 1, 'units')

    for seq in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
        window.TKroot.bind(seq, on_wheel, add='+')


def resolve_token():
    token = str(cfg(K_TOKEN)).strip() or os.environ.get('GITHUB_TOKEN', '').strip() or os.environ.get('GH_TOKEN', '').strip()
    if not token:
        try:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            token = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=10, creationflags=flags).stdout.strip()
        except Exception:
            token = ''
    return token


# ================================================================ GitHub REST client ================================================================
class GitHubError(Exception):
    pass


class GitHub:
    """Tiny urllib client.  Remembers ETags so unchanged pages come back as free 304s, and tracks the rate limit headers."""

    def __init__(self, token):
        self.token = token
        self.etags, self.cache = {}, {}
        self.rate = {'remaining': None, 'limit': None, 'reset': None}
        self._login, self.owner_path = None, {}

    def login(self):
        """The token's own GitHub login ('' when there is no usable token).  Looked up once."""
        if self._login is None:
            try:
                self._login = (self.get('/user').get('login') or '') if self.token else ''
            except GitHubError:
                self._login = ''
        return self._login

    def _rate(self, headers):
        try:
            self.rate = {'remaining': int(headers['X-RateLimit-Remaining']), 'limit': int(headers['X-RateLimit-Limit']), 'reset': int(headers['X-RateLimit-Reset'])}
        except Exception:
            pass

    def get(self, path, params=None):
        url = API + path + ('?' + urllib.parse.urlencode(params) if params else '')
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'github-repo-watch', 'X-GitHub-Api-Version': '2022-11-28'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        if url in self.etags:
            headers['If-None-Match'] = self.etags[url]
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as resp:
                self._rate(resp.headers)
                body = json.loads(resp.read().decode('utf-8'))
                if resp.headers.get('ETag'):
                    self.etags[url], self.cache[url] = resp.headers['ETag'], body
                return body
        except urllib.error.HTTPError as e:
            self._rate(e.headers)
            if e.code == 304:
                return self.cache[url]
            if e.code == 401:
                raise GitHubError('token rejected (401) - check Settings')
            if e.code == 403 and self.rate.get('remaining') == 0:
                raise GitHubError(f'rate limited until {clock(datetime.fromtimestamp(self.rate["reset"]))}')
            if e.code in (403, 404):
                raise GitHubError(f'{"forbidden" if e.code == 403 else "not found"} ({e.code}) - a private repo needs a token that can read it')
            raise GitHubError(f'HTTP {e.code} on {path}')
        except urllib.error.URLError as e:
            raise GitHubError(f'network problem: {getattr(e, "reason", e)}')
        except Exception as e:
            raise GitHubError(f'{type(e).__name__}: {e}')


def list_owner_repos(gh, owner):
    """Every repo an account owns, newest push first.  Your own account includes private repos; other accounts show what the token may see."""
    key = owner.lower()
    if key not in gh.owner_path:
        if gh.login().lower() == key:
            gh.owner_path[key] = ('/user/repos', {'affiliation': 'owner'})
        else:
            try:
                gh.get(f'/orgs/{owner}')
                gh.owner_path[key] = (f'/orgs/{owner}/repos', {'type': 'all'})
            except GitHubError:
                gh.owner_path[key] = (f'/users/{owner}/repos', {})
    path, params = gh.owner_path[key]
    out = []
    for page in range(1, 6):
        chunk = gh.get(path, dict(params, sort='pushed', per_page=100, page=page))
        out.extend({'repo': r['full_name'], 'private': r.get('private', False), 'archived': r.get('archived', False), 'fork': r.get('fork', False),
                    'pushed_at': r.get('pushed_at'), 'description': r.get('description') or ''} for r in chunk)
        if len(chunk) < 100:
            break
    return out


def commit_record(c, branch):
    commit = c.get('commit') or {}
    title, _, body = (commit.get('message') or '').partition('\n')
    who = commit.get('author') or {}
    login = (c.get('author') or {}).get('login')
    when = who.get('date') or (commit.get('committer') or {}).get('date')
    return {'sha': c['sha'], 'short': c['sha'][:7], 'title': title.strip() or '(no message)', 'body': body.strip(), 'author': who.get('name') or login or '?', 'login': login,
            'date': when, 'url': c.get('html_url', ''), 'branch': branch, 'parents': len(c.get('parents') or [])}


def commit_meta(c, det):
    """The grey second line under a commit: author · sha · branch · folders touched."""
    return ' · '.join(x for x in [c['author'], c['short'], c['branch'], folder_summary(det['files']) if det else ''] if x)


def fetch_commit_detail(gh, repo, sha, cache):
    if sha in cache:
        return cache[sha]
    d = gh.get(f'/repos/{repo}/commits/{sha}')
    files = [{'name': f['filename'], 'status': f.get('status', 'modified'), 'add': f.get('additions', 0), 'del': f.get('deletions', 0), 'patch': f.get('patch') or '',
              'prev': f.get('previous_filename')} for f in d.get('files') or []]
    cache[sha] = {'files': files, 'add': (d.get('stats') or {}).get('additions', 0), 'del': (d.get('stats') or {}).get('deletions', 0)}
    return cache[sha]


def speaker(user, assoc, at):
    return {'login': (user or {}).get('login') or '?', 'assoc': assoc or 'NONE', 'at': at}


def is_maintainer(who, me):
    """Owner / member / collaborator, or the token's own account: when one of them had the last word, nobody is waiting on you."""
    return who['assoc'] in MAINTAINER_ROLES or bool(me) and who['login'].lower() == me.lower()


def issue_record(it, last, me, window):
    """One issue the way the Issues window shows it.  'last' = who had the last word (None when that was before the window);
    'waiting' = open, and that last word came from someone other than you or a collaborator, inside the window."""
    spk = last.get(it['number'])
    if spk is None and not it.get('comments'):
        spk = speaker(it.get('user'), it.get('author_association'), it['created_at'])         # nobody has answered yet
    waiting = it['state'] == 'open' and spk is not None and not is_maintainer(spk, me) and parse_iso(spk['at']) >= window
    return {'number': it['number'], 'title': it['title'], 'user': (it.get('user') or {}).get('login', '?'), 'assoc': it.get('author_association') or 'NONE',
            'state': it['state'], 'comments': it.get('comments', 0), 'url': it['html_url'], 'date': it['updated_at'], 'created': it['created_at'],
            'labels': [l['name'] for l in it.get('labels') or []], 'body': it.get('body') or '', 'last': spk, 'waiting': waiting, 'what': '', 'actor': ''}


def poll_issues(gh, repo, rstate, snap, history_days, has_issues, baseline):
    """The issue side of a poll.  snap['open_issues'] gets the open issues with who had the last word on each (so the ones waiting on you
    stand out); snap['new_issues'] / snap['new_prs'] get the activity since you last looked.  Your own comments, closes and new issues are
    never news, and neither are label changes or edits."""
    me = gh.login()
    last_read = parse_iso(rstate.get('last_read_at'))
    issues_read = parse_iso(rstate.get('issues_read_at')) or last_read
    window = utcnow() - timedelta(days=history_days)
    last = {}                                                   # issue number -> the latest comment by a person (bots don't count)
    if has_issues:
        since = (min(window, issues_read) if issues_read else window).strftime('%Y-%m-%dT00:00:00Z')        # same URL all day -> free 304s
        for page in (1, 2, 3):
            chunk = gh.get(f'/repos/{repo}/issues/comments', {'since': since, 'sort': 'created', 'direction': 'desc', 'per_page': 100, 'page': page})
            for c in chunk:
                if (c.get('user') or {}).get('type') != 'Bot':
                    last.setdefault(int(c['issue_url'].rsplit('/', 1)[1]), speaker(c.get('user'), c.get('author_association'), c['created_at']))
            if len(chunk) < 100:
                break
        raw = gh.get(f'/repos/{repo}/issues', {'state': 'open', 'sort': 'updated', 'direction': 'desc', 'per_page': 100})
        snap['open_issues'] = [issue_record(it, last, me, window) for it in raw if 'pull_request' not in it]
        snap['open_issue_total'] = len(snap['open_issues']) if len(raw) < 100 else snap['info']['open_issues']
    if baseline or not last_read:
        return
    since = last_read.strftime('%Y-%m-%dT%H:%M:%SZ')
    for it in gh.get(f'/repos/{repo}/issues', {'state': 'all', 'sort': 'updated', 'direction': 'desc', 'since': since, 'per_page': 100}):
        updated, created, closed = parse_iso(it['updated_at']), parse_iso(it['created_at']), parse_iso(it.get('closed_at'))
        if 'pull_request' in it:
            if updated <= last_read:
                continue
            merged = (it.get('pull_request') or {}).get('merged_at')
            what = 'merged' if merged and parse_iso(merged) > last_read else 'opened' if created > last_read else 'closed' if closed and closed > last_read else 'updated'
            snap['new_prs'].append({'number': it['number'], 'title': it['title'], 'user': (it.get('user') or {}).get('login', '?'), 'state': it['state'],
                                    'comments': it.get('comments', 0), 'url': it['html_url'], 'date': it['updated_at'], 'what': what,
                                    'labels': [l['name'] for l in it.get('labels') or []], 'body': it.get('body') or ''})
            continue
        if not issues_read or updated <= issues_read:
            continue
        spk = last.get(it['number'])
        if created > issues_read:
            what, actor = 'opened', (it.get('user') or {}).get('login', '?')
        elif it['state'] == 'closed' and closed and closed > issues_read:
            what, actor = 'closed', (gh.get(f'/repos/{repo}/issues/{it["number"]}').get('closed_by') or {}).get('login') or '?'
        elif spk and parse_iso(spk['at']) > issues_read:
            what, actor = 'commented', spk['login']
        else:
            continue                                            # a label change or an edit - not news
        if me and actor.lower() == me.lower():
            continue                                            # your own doing
        snap['new_issues'].append(dict(issue_record(it, last, me, window), what=what, actor=actor))


def post_record(x):
    user = x.get('user') or {}
    return {'login': user.get('login') or '?', 'assoc': x.get('author_association') or 'NONE', 'bot': user.get('type') == 'Bot', 'at': x['created_at'],
            'body': x.get('body') or ''}


def fetch_issue_thread(gh, repo, number):
    """An issue and all of its comments, oldest first, for the reader."""
    it = gh.get(f'/repos/{repo}/issues/{number}')
    posts = [post_record(it)]
    for page in range(1, 6):
        chunk = gh.get(f'/repos/{repo}/issues/{number}/comments', {'per_page': 100, 'page': page})
        posts.extend(post_record(c) for c in chunk)
        if len(chunk) < 100:
            break
    return {'number': number, 'title': it['title'], 'state': it['state'], 'reason': it.get('state_reason') or '', 'closed_at': it.get('closed_at'),
            'closed_by': (it.get('closed_by') or {}).get('login'), 'updated': it['updated_at'], 'labels': [l['name'] for l in it.get('labels') or []], 'posts': posts}


MD_COMMENT = re.compile(r'<!--.*?-->', re.S)
MD_IMAGE = re.compile(r'!\[([^\]]*)\]\([^)]*\)|<img\b[^>]*>', re.I)
MD_LINK = re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)')
MD_TAG = re.compile(r'</?(?:details|summary|p|div|span|sub|sup|b|i|em|strong|kbd|code|pre|br|h\d)\b[^>]*>', re.I)


def md_lines(text):
    """Issue / comment markdown -> [(style, line)], style = text / head / quote / check / code.  Just enough to read comfortably."""
    text = MD_COMMENT.sub('', text.replace('\r\n', '\n'))
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = MD_IMAGE.sub(lambda m: f'[image: {m.group(1)}]' if m.group(1) else '[image]', text)
    text = MD_LINK.sub(r'\1 (\2)', MD_TAG.sub('', text))
    out, code = [], False
    for line in text.split('\n'):
        if line.lstrip().startswith('```'):
            code = not code
            continue
        s = line.strip()
        if code:
            out.append(('code', line.rstrip()))
        elif not s:
            if out and out[-1] != ('text', '') and out[-1][0] != 'head':          # no blank line straight under a heading
                out.append(('text', ''))
        elif s.startswith('#'):
            out.append(('head', s.lstrip('#').strip()))
        elif s.startswith('>'):
            out.append(('quote', '│ ' + s[1:].strip()))
        elif re.match(r'[-*] \[[ xX]\]', s):
            out.append(('check', ('☑ ' if s[3] in 'xX' else '☐ ') + s[6:].strip()))
        else:
            out.append(('text', line.rstrip()))
    while out and out[-1] == ('text', ''):
        out.pop()
    return out


def poll_repo(gh, repo, rstate, history_days, commit_cache):
    """One full look at a repo.  Returns a snapshot dict; snapshot['state_update'] is set only on the very first (baseline) look."""
    rstate = json.loads(json.dumps(rstate))                     # private copy - the GUI thread owns the real one
    snap = {'repo': repo, 'ok': True, 'error': '', 'checked_at': utcnow().isoformat(), 'history_days': history_days, 'new_commits': [], 'new_branches': [], 'gone_branches': [],
            'new_tags': [], 'new_releases': [], 'new_issues': [], 'new_prs': [], 'history': [], 'per_day': {}, 'branches': {}, 'tags': [], 'state_update': None,
            'open_issues': [], 'open_issue_total': 0}
    info = gh.get(f'/repos/{repo}')
    default = info.get('default_branch') or 'main'
    snap['info'] = {'description': info.get('description') or '', 'default_branch': default, 'pushed_at': info.get('pushed_at'), 'stars': info.get('stargazers_count', 0),
                    'watchers': info.get('subscribers_count', 0), 'forks': info.get('forks_count', 0), 'open_issues': info.get('open_issues_count', 0),
                    'html_url': info.get('html_url', ''), 'private': info.get('private', False), 'language': info.get('language') or '',
                    'has_issues': info.get('has_issues', True)}
    branches = {b['name']: b['commit']['sha'] for b in gh.get(f'/repos/{repo}/branches', {'per_page': 100})}
    snap['branches'] = branches
    snap['tags'] = [{'name': t['name'], 'sha': t['commit']['sha']} for t in gh.get(f'/repos/{repo}/tags', {'per_page': 30})]
    last_read = parse_iso(rstate.get('last_read_at'))
    if not rstate.get('baselined'):                             # first ever look: everything that exists now counts as already seen
        rstate.update({'baselined': True, 'read_heads': dict(branches), 'known_branches': list(branches), 'known_tags': [t['name'] for t in snap['tags']],
                       'last_read_at': snap['checked_at']})
        snap['state_update'] = rstate
    else:
        read_heads, known_branches = rstate.get('read_heads', {}), rstate.get('known_branches', [])
        seen = set()
        for name in sorted(branches, key=lambda b: (b != default, b)):
            sha = branches[name]
            is_new_branch = name not in known_branches
            base = (branches.get(default) if name != default else None) if is_new_branch else read_heads.get(name)
            commits = []
            if base and base != sha:
                try:
                    commits = [commit_record(c, name) for c in gh.get(f'/repos/{repo}/compare/{base}...{sha}').get('commits', [])]
                except GitHubError:                             # the old head vanished (force push) - fall back to "since you last looked"
                    since = (last_read or utcnow() - timedelta(days=7)).isoformat()
                    commits = [commit_record(c, name) for c in gh.get(f'/repos/{repo}/commits', {'sha': name, 'since': since, 'per_page': 100})]
            commits = [c for c in commits if c['sha'] not in seen]
            seen.update(c['sha'] for c in commits)
            if is_new_branch:
                snap['new_branches'].append({'name': name, 'sha': sha, 'commits': commits, 'default': default})
            snap['new_commits'].extend(commits)
        snap['gone_branches'] = [b for b in known_branches if b not in branches]
        snap['new_tags'] = [t for t in snap['tags'] if t['name'] not in rstate.get('known_tags', [])]
        for r in gh.get(f'/repos/{repo}/releases', {'per_page': 10}):
            when = parse_iso(r.get('published_at') or r.get('created_at'))
            if last_read and when and when > last_read and not r.get('draft'):
                snap['new_releases'].append({'name': r.get('name') or r.get('tag_name'), 'tag': r.get('tag_name'), 'author': (r.get('author') or {}).get('login', '?'),
                                             'date': when.isoformat(), 'prerelease': r.get('prerelease', False), 'body': r.get('body') or '', 'url': r.get('html_url', '')})
    has_issues = snap['info']['has_issues'] and snap['info']['open_issues'] > 0
    try:
        poll_issues(gh, repo, rstate, snap, history_days, has_issues, baseline=bool(snap['state_update']))
    except GitHubError as e:                                    # e.g. a fine-grained token without Issues access - the code news still works
        snap['issues_error'] = str(e)
        log(f'{repo} issues: {e}')
    snap['new_commits'].sort(key=lambda c: c['date'] or '', reverse=True)
    for c in snap['new_commits'][:DETAIL_FETCH_LIMIT]:
        try:
            fetch_commit_detail(gh, repo, c['sha'], commit_cache)
        except GitHubError as e:
            log(f'{repo} detail {c["short"]}: {e}')
    since = (utcnow() - timedelta(days=history_days)).strftime('%Y-%m-%dT00:00:00Z')      # same URL all day -> ETag 304s cost nothing
    for page in (1, 2, 3):
        chunk = gh.get(f'/repos/{repo}/commits', {'sha': default, 'since': since, 'per_page': 100, 'page': page})
        snap['history'].extend(commit_record(c, default) for c in chunk)
        if len(chunk) < 100:
            break
    snap['per_day'] = dict(Counter(parse_iso(c['date']).astimezone().date().isoformat() for c in snap['history'] if c['date']))
    snap['rate'] = dict(gh.rate)
    return snap


# ================================================================ demo data (--demo) ================================================================
DEMO_PATCH = """@@ -112,9 +112,14 @@ package body Impulsing.Scene is
    procedure Load_Node (N : Node_Type) is
    begin
-      Load_Mesh (N.Mesh);
+      if N.Has_Mesh then
+         Load_Mesh (N.Mesh);
+      else
+         --  Empties carry only a transform; register it so children still inherit it
+         Register_Transform (N);
+      end if;
    end Load_Node;
@@ -140,7 +145,6 @@ package body Impulsing.Scene is
    procedure Clear (S : in out Scene) is
    begin
-      S.Dirty := True;
       S.Nodes.Clear;
       S.Conduits.Clear;
    end Clear;"""


def demo_owner_repos(owner):
    now = utcnow()
    fake = [('PySimpleGUI', 'Python GUIs for Humans', 1), ('psgapps', 'Ready-to-run PySimpleGUI applications', 3), ('piano_dynamics_monitor', 'MIDI velocity practice tool', 9),
            ('window_ram_tagger', 'Tags windows with their RAM and CPU use', 21), ('psgdemos', 'Demo programs', 40), ('old_experiments', 'Scratch space', 200)]
    return [{'repo': f'{owner}/{n}', 'private': i % 2 == 0, 'archived': False, 'fork': False, 'pushed_at': (now - timedelta(days=d, hours=2)).isoformat(), 'description': desc}
            for i, (n, desc, d) in enumerate(fake)]


DEMO_6921 = """<!-- Please fill in every section -->
### Type of Issue (Bug, Question, Enhancement, etc)

Bug

### Operating System

macOS 15.1

### Versions

Python 3.12.7 · PySimpleGUI 6.3.5 · tkinter 8.6.15

### Troubleshooting

- [X] Searched the main docs for my problem
- [X] Looked for Demo Programs that are similar to my goal
- [ ] Tried running the code on another OS

### Detailed Description

After a popup is closed, the next `window.read()` never returns.  Clicking the buttons does nothing.

### Code To Duplicate

```python
import PySimpleGUI as sg

window = sg.Window('Hangs', [[sg.Button('Popup')], [sg.Button('Exit')]])
while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    sg.popup('Close me')
window.close()
```

![frozen window](https://example.com/hang.png)"""

DEMO_ISSUES = {     # repo: [(number, title, author, role, opened N minutes ago, labels, body, [(who, role, N minutes ago, comment)], (closed by, N minutes ago) or None)]
    'jaynabonne/impulsing_ada': [
        (7, 'Empties inside a rotated parent lose their transform', 'jaynabonne', 'OWNER', 6 * 60, ['bug'],
         'Repro: load overworld.gltf, rotate the root node 90° - the camera pivot ends up at the origin.',
         [('jaynabonne', 'OWNER', 5 * 60, 'Register_Transform ignores the parent matrix.'), ('jaynabonne', 'OWNER', 4 * 60, 'Fix is on the lighting branch for now.')], None)],
    'PySimpleGUI/PySimpleGUI': [
        (6921, 'Window.read() never returns after closing a popup on macOS 15', 'mac-dev-lena', 'NONE', 190, ['Bug', 'Mac'], DEMO_6921, [], None),
        (6918, 'Table: right-click menu selects the wrong row when the table is sorted', 'tablefan', 'CONTRIBUTOR', 3 * 1440, ['Bug'],
         'Sort a Table by clicking a heading, then right-click a row - the menu acts on the row that was there before sorting.',
         [('PySimpleGUI', 'OWNER', 2 * 1440, 'Thanks for the report.  Can you post a short program that shows it?'),
          ('tablefan', 'CONTRIBUTOR', 40, 'Here you go:\n\n```python\nimport PySimpleGUI as sg\n\nrows = [[3, "c"], [1, "a"], [2, "b"]]\n'
                                          'layout = [[sg.Table(rows, ["n", "name"], key="-T-", enable_click_events=True, right_click_selects=True)]]\n'
                                          'window = sg.Window("Sort me", layout, finalize=True)\n```\n\nClick the "n" heading, then right-click the first row.')], None),
        (6915, 'psgtray icon disappears after Explorer restarts', 'kim-codes', 'NONE', 4 * 1440, ['Question'], 'The tray icon is gone after explorer.exe restarts.',
         [('helper-sam', 'COLLABORATOR', 3 * 1440, 'psgtray re-adds the icon if you call tray.show_icon() when Windows sends TaskbarCreated.'),
          ('kim-codes', 'NONE', 5 * 60, 'That did it - thank you!')], ('kim-codes', 5 * 60)),
        (6914, 'Typo in the Cookbook "Persistent window" recipe', 'docs-reader', 'NONE', 2 * 1440, ['Documentation'], '"recieve" should be "receive".',
         [('PySimpleGUI', 'OWNER', 30, 'Fixed - thanks for the sharp eyes.')], None),
        (6912, 'Multiline.print with colors is slow for 10,000 lines', 'perf-hunter', 'NONE', 6 * 1440, ['Performance'],
         'Printing 10,000 colored lines takes almost a minute.',
         [('PySimpleGUI', 'OWNER', 5 * 1440, 'Are you printing one line per call?  Batching lines of the same color into one call is much faster.'),
          ('perf-hunter', 'NONE', 2 * 1440 + 60, '> Batching lines of the same color\n\nYes, one call per line.  Batching helps, but each color change is still slow.')], None),
        (6909, 'Feature request: Spin element with a float step', 'num-nerd', 'NONE', 6 * 1440 + 300, ['Enhancement'], 'A Spin that steps by 0.25 would be handy.', [], None),
        (6905, 'How do I make a borderless window resizable?', 'newbie-raj', 'FIRST_TIME_CONTRIBUTOR', 2 * 1440 + 200, ['Question'], 'no_titlebar=True loses the edges.',
         [('PySimpleGUI', 'OWNER', 1440, 'Add a sg.Sizegrip() to the bottom-right corner of the layout.')], None),
        (6899, 'Theme previewer crashes on Python 3.14', 'py314-early', 'NONE', 9 * 1440, ['Bug'], 'Traceback when the previewer opens.',
         [('helper-sam', 'COLLABORATOR', 8 * 1440, 'Confirmed - the fix is in 6.3.6 on GitHub.')], None),
        (6801, 'Graph element: drag events lose precision on 4K monitors', 'hidpi-hank', 'NONE', 40 * 1440, ['Enhancement'], 'Coordinates jump in steps of 2 px.',
         [('PySimpleGUI', 'OWNER', 39 * 1440, 'Probably the scaling setting - can you try sg.set_options(scaling=1)?')], None),
        (6766, 'Tab titles cut off with large fonts', 'bigfont-bo', 'NONE', 55 * 1440, ['Bug'], 'Tab titles are clipped at 20 pt.', [], None),
        (6702, 'Right-to-left text in Input and Multiline', 'rtl-ranya', 'NONE', 80 * 1440, ['Enhancement'], 'Hebrew and Arabic need right-to-left entry.',
         [('PySimpleGUI', 'OWNER', 79 * 1440, 'tkinter has limited RTL support - justification="r" is a start.'), ('rtl-ranya', 'NONE', 78 * 1440, 'That helps a little.')], None),
        (6655, 'Combo drop-down list is too short on Linux', 'tux-tom', 'NONE', 120 * 1440, ['Linux'], 'Only 5 items show.', [], None),
        (6590, 'Dark title bar on Windows 11', 'win11-wendy', 'NONE', 150 * 1440, ['Enhancement'], 'The title bar stays white with dark themes.',
         [('PySimpleGUI', 'OWNER', 149 * 1440, 'use_custom_titlebar=True gives you a themed title bar today.')], None),
        (6544, 'Docs: using write_event_value from asyncio', 'async-ash', 'NONE', 200 * 1440, ['Documentation'], 'An asyncio example would help.', [], None)]}


class DemoGitHub:
    """Canned GitHub answers for --demo, served through the same issue code the real API goes through."""
    _shared = None

    @classmethod
    def shared(cls):
        if cls._shared is None:
            cls._shared = cls()
        return cls._shared

    def __init__(self):
        self.now, self.rate = utcnow(), {'remaining': 4988, 'limit': 5000, 'reset': 0}
        self.repos = {repo: [self.issue(repo, *spec) for spec in specs] for repo, specs in DEMO_ISSUES.items()}

    def login(self):
        return 'PySimpleGUI'

    def t(self, minutes):
        return (self.now - timedelta(minutes=minutes)).strftime('%Y-%m-%dT%H:%M:%SZ')

    def issue(self, repo, number, title, author, role, opened, labels, body, comments, closed):
        url = f'https://github.com/{repo}/issues/{number}'
        cmts = [{'user': {'login': who, 'type': 'User'}, 'author_association': r, 'created_at': self.t(m), 'updated_at': self.t(m), 'body': text,
                 'html_url': f'{url}#issuecomment-{number}{i}', 'issue_url': f'{API}/repos/{repo}/issues/{number}'} for i, (who, r, m, text) in enumerate(comments)]
        latest = min([opened] + [c[2] for c in comments] + ([closed[1]] if closed else []))
        return {'number': number, 'title': title, 'user': {'login': author, 'type': 'User'}, 'author_association': role, 'labels': [{'name': l} for l in labels],
                'state': 'closed' if closed else 'open', 'state_reason': 'completed' if closed else None, 'comments': len(cmts), 'body': body, 'html_url': url,
                'created_at': self.t(opened), 'updated_at': self.t(latest), 'closed_at': self.t(closed[1]) if closed else None,
                'closed_by': {'login': closed[0]} if closed else None, '_comments': cmts}

    def get(self, path, params=None):
        params = params or {}
        parts = path.strip('/').split('/')                              # repos / owner / name / issues [/ comments | / number [/ comments]]
        issues = self.repos.get('/'.join(parts[1:3]), [])
        if params.get('page', 1) > 1 or parts[3:4] != ['issues']:
            return []
        since = params.get('since', '')
        if parts[4:] == ['comments']:
            return sorted((c for it in issues for c in it['_comments'] if c['updated_at'] >= since), key=lambda c: c['created_at'], reverse=True)
        if len(parts) == 4:
            state = params.get('state', 'open')
            return sorted((it for it in issues if state in ('all', it['state']) and it['updated_at'] >= since), key=lambda it: it['updated_at'], reverse=True)
        it = next(x for x in issues if x['number'] == int(parts[4]))
        return list(it['_comments']) if parts[5:] == ['comments'] else it


def demo_poll(repo, rstate, history_days, commit_cache):
    rnd = random.Random(7)
    now = utcnow()
    titles = ['Handle nodes without meshes (e.g. empties). Some other clean up', 'Compile material - at least as far as albedo goes.',
              'First steps at turning gltf data into an actual raylib mesh', 'Accessor type and component type', 'Add asset tool and initial storage explorations',
              'First pass over reading gltf file. It just parses at the moment', 'Overworld scene to begin playing with.', 'Pool conduits by ID', 'Fix normals on flipped faces',
              'Test runner tidy-up', 'Camera follows the active node', 'Remove leftover Godot references']
    bodies = ['Empties (nodes with no mesh) used to crash Load_Node.  They now just register their transform.\n\nAlso removed the stale Dirty flag.', '', '']
    files = [('src/impulsing-scene.adb', 'modified'), ('src/impulsing-scene.ads', 'modified'), ('src/impulsing-gltf.adb', 'modified'), ('src/impulsing-material.adb', 'added'),
             ('tests/scene_tests.adb', 'modified'), ('assets/overworld.gltf', 'modified'), ('progress/notes.md', 'modified'), ('src/impulsing-conduit.ads', 'renamed')]
    history = []
    for i in range(38):
        when = now - timedelta(days=rnd.uniform(0, history_days), hours=rnd.uniform(0, 3))
        sha = '%040x' % rnd.getrandbits(160)
        history.append({'sha': sha, 'short': sha[:7], 'title': rnd.choice(titles), 'body': '', 'author': 'Jay Nabonne', 'login': 'jaynabonne', 'date': when.isoformat(),
                        'url': f'https://github.com/{repo}/commit/{sha}', 'branch': 'master', 'parents': 1})
    history.sort(key=lambda c: c['date'], reverse=True)
    for c, minutes, title, body in zip(history[:3], (28, 2 * 1440 + 15, 5 * 1440 + 40), titles[:3], bodies):
        c.update({'date': (now - timedelta(minutes=minutes)).isoformat(), 'title': title, 'body': body})
    for c in history[:3]:
        picks = rnd.sample(files, rnd.randint(2, 4))
        commit_cache[c['sha']] = {'files': [{'name': n, 'status': s, 'add': rnd.randint(4, 90), 'del': rnd.randint(1, 40), 'patch': DEMO_PATCH, 'prev': None} for n, s in picks]}
        commit_cache[c['sha']].update({'add': sum(f['add'] for f in commit_cache[c['sha']]['files']), 'del': sum(f['del'] for f in commit_cache[c['sha']]['files'])})
    branch_sha = '%040x' % rnd.getrandbits(160)
    branch_commits = [{'sha': branch_sha, 'short': branch_sha[:7], 'title': 'Directional light with a simple shadow pass', 'body': '', 'author': 'Jay Nabonne',
                       'login': 'jaynabonne', 'date': (now - timedelta(hours=5)).isoformat(), 'url': f'https://github.com/{repo}/commit/{branch_sha}', 'branch': 'lighting',
                       'parents': 1}]
    commit_cache[branch_sha] = {'files': [{'name': 'src/impulsing-light.adb', 'status': 'added', 'add': 142, 'del': 0, 'patch': DEMO_PATCH, 'prev': None}], 'add': 142, 'del': 0}
    new_commits = sorted(history[:3] + branch_commits, key=lambda c: c['date'], reverse=True)
    info = {'description': 'An Ada implementation of Impulsing, using Raylib', 'default_branch': 'master', 'pushed_at': (now - timedelta(minutes=28)).isoformat(), 'stars': 1,
            'watchers': 1, 'forks': 0, 'open_issues': 1, 'html_url': f'https://github.com/{repo}', 'private': True, 'language': 'Ada', 'has_issues': True}
    state_update = None if rstate.get('baselined') else {'baselined': True, 'read_heads': {'master': history[3]['sha']}, 'known_branches': ['master'], 'known_tags': [],
                                                          'last_read_at': (now - timedelta(days=6, hours=3)).isoformat(),
                                                          'issues_read_at': (now - timedelta(hours=8)).isoformat()}
    snap = {'repo': repo, 'ok': True, 'error': '', 'checked_at': now.isoformat(), 'history_days': history_days, 'new_commits': new_commits, 'gone_branches': [], 'new_tags': [],
            'new_releases': [], 'new_branches': [{'name': 'lighting', 'sha': branch_sha, 'commits': branch_commits, 'default': 'master'}], 'state_update': state_update,
            'history': history,
            'tags': [], 'per_day': dict(Counter(parse_iso(c['date']).astimezone().date().isoformat() for c in history)),
            'branches': {'master': history[0]['sha'], 'lighting': branch_sha},
            'new_issues': [], 'new_prs': [], 'open_issues': [], 'open_issue_total': 0, 'rate': {'remaining': 4988, 'limit': 5000, 'reset': 0}, 'info': info}
    if 'jaynabonne' not in repo:                                # the other demo repos are quiet, each with its own history
        rnd2 = random.Random(repo)
        for k in ('new_commits', 'new_branches', 'new_issues'):
            snap[k] = []
        snap['history'] = [c for c in history if rnd2.random() < 0.4]
        snap['per_day'] = dict(Counter(parse_iso(c['date']).astimezone().date().isoformat() for c in snap['history']))
        snap['branches'] = {'master': history[0]['sha']}
        snap['info'] = dict(info, description=f'Demo repo {repo.split("/")[1]}', pushed_at=(now - timedelta(days=rnd2.randint(1, 60))).isoformat(), private=rnd2.random() < 0.5)
    gh = DemoGitHub.shared()
    snap['info']['open_issues'] = sum(1 for it in gh.repos.get(repo, []) if it['state'] == 'open')
    poll_issues(gh, repo, state_update or rstate, snap, history_days, bool(gh.repos.get(repo)), baseline=False)
    return snap


# ================================================================ background poller ================================================================
class Poller(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
        self.wake, self.quit = threading.Event(), threading.Event()
        self.paused = False
        self.commit_cache, self.thread_cache = {}, {}            # commit sha -> files + patch;  (repo, issue number) -> conversation
        self.gh, self.entries, self.repos, self.state, self.interval, self.history_days = None, [], [], {}, 300, 30
        self.next_check = None

    def configure(self, token, entries, interval, history_days, state):
        self.gh, self.entries, self.interval, self.history_days, self.state = GitHub(token), entries, interval, history_days, state
        self.wake.set()

    def run(self):
        while not self.quit.is_set():
            self.wake.clear()
            if not self.paused and self.entries:
                self.poll_all()
            self.next_check = utcnow() + timedelta(seconds=self.interval)
            self.wake.wait(self.interval)

    def emit(self, key, value):
        err = None
        for _ in range(10):                                      # the widget window may be mid-rebuild for a moment - wait for the new one
            try:
                self.app.widget.write_event_value(key, value)
                return
            except Exception as e:
                err = e
                time.sleep(0.2)
        log(f'emit {key}: {err}')

    def resolve_entries(self):
        """Turn account lines into their repo lists (repeated every poll, so new repos appear on their own)."""
        repos, expanded = [], {}
        for entry in list(self.entries):
            if '/' in entry:
                repos.append(entry)
                continue
            try:
                found = demo_owner_repos(entry) if DEMO else list_owner_repos(self.gh, entry)
                expanded[entry] = {'repos': [r['repo'] for r in found if not r['archived']], 'error': ''}
            except Exception as e:
                expanded[entry] = {'repos': [], 'error': str(e)}
                log(f'{entry}: {e}')
            repos.extend(expanded[entry]['repos'])
        if expanded:
            self.emit(K_REPOS_RESOLVED, expanded)
        self.repos = list(dict.fromkeys(repos))

    def poll_all(self):
        self.resolve_entries()
        for repo in list(self.repos):
            if self.quit.is_set():
                return
            self.emit(K_POLL_BUSY, repo)
            try:
                if DEMO:
                    snap = demo_poll(repo, self.state.get(repo, {}), self.history_days, self.commit_cache)
                else:
                    snap = poll_repo(self.gh, repo, self.state.get(repo, {}), self.history_days, self.commit_cache)
            except Exception as e:
                snap = {'repo': repo, 'ok': False, 'error': str(e), 'checked_at': utcnow().isoformat(), 'rate': dict(self.gh.rate) if self.gh else {}}
                log(f'{repo}: {e}')
                if not isinstance(e, GitHubError):
                    log(traceback.format_exc())
            while len(self.commit_cache) > 400:                     # patches can be big - keep only the most recent few hundred commits
                del self.commit_cache[next(iter(self.commit_cache))]
            self.emit(K_POLL_RESULT, snap)


# ================================================================ the app ================================================================
class App:
    def __init__(self):
        sg.user_settings_filename(filename=SETTINGS_FILE)
        self.state = sg.user_settings_get_entry(K_STATE, {}) or {}
        self.scale = dpi_scale()
        self.snapshots, self.busy = {}, set()
        self.widget, self.details, self.settings_win = None, None, None
        self.details_repo, self.details_items, self.details_sig, self.selected, self.item_widgets = None, [], None, None, {}
        self.title_chars, self.meta_chars = 54, 78
        self.snooze_until, self.dimmed, self.current_alpha = None, False, None
        self.fetching, self.digest_plain, self.auto_opened, self.last_meta_refresh = set(), '', False, datetime.now()
        self.expanded, self.owner_errors, self.widget_rows = {}, {}, []
        self.all_win, self.pick_win, self.pick_repos, self.pick_owner = None, None, [], ''
        self.issues_win, self.issues_repo, self.issues_sig, self.issue_items, self.issue_selected = None, None, None, [], None
        self.is_title_chars, self.is_meta_chars = 58, 80
        self.visible_rows, self.last_geom = [], None
        self.view, self.issue_rows_shown = cfg(K_VIEW), []
        self.poller = None
        self.build_widget()
        self.poller = Poller(self)
        self.reconfigure_poller()
        self.poller.start()

    # ---------------------------------------------------------------- settings plumbing ----------------------------------------------------------------
    def entries(self):
        """Settings lines: 'owner/name' repos and bare 'owner' accounts."""
        return parse_entries(cfg(K_REPOS)) or [DEFAULTS[K_REPOS]]

    def repos(self):
        """Every repo being watched, with account lines expanded to whatever the poller found for them."""
        out = []
        for e in self.entries():
            out.extend([e] if '/' in e else self.expanded.get(e.lower(), []))
        return list(dict.fromkeys(out))

    def reconfigure_poller(self):
        for repo in self.repos():
            self.state.setdefault(repo, {})
        self.poller.configure('' if DEMO else resolve_token(), self.entries(), int(str(cfg(K_INTERVAL)).split()[0]) * 60, int(str(cfg(K_HISTORY_DAYS)).split()[0]), self.state)

    def btn(self, f):
        return dict(font=f['small'], button_color=(C_TEXT, C_BG3), border_width=0, pad=((0, 6), (6, 0)))

    # ---------------------------------------------------------------- which rows the widget shows ----------------------------------------------------------------
    def widget_row_ids(self):
        repos = self.repos()
        if not cfg(K_COLLAPSE) or len(repos) <= 1:
            return repos
        shown = [r for r in repos if self.snapshots.get(r) is not None and (not self.snapshots[r].get('ok') or self.unread_count(self.snapshots[r]))]
        return shown + ([QUIET_ROW] if len(shown) < len(repos) else [])

    def sync_widget(self):
        """Show/hide rows to match the wanted set; rebuild the window only when a repo has no row yet."""
        if self.view == VIEW_ISSUES:
            self.refresh_issue_rows()
            self.keep_on_screen()
            return
        want = self.widget_row_ids()
        if any(r not in self.widget_rows for r in want):
            self.rebuild_widget()
            return
        if want != self.visible_rows:
            for r in self.widget_rows:
                self.widget[KT_ROW(r)].update(visible=r in want)
            self.visible_rows = want
        for r in want:
            self.refresh_row(r)
        self.keep_on_screen()

    def rebuild_widget(self):
        old = self.widget
        self.build_widget()
        self.widget._create_thread_queue()
        while old.thread_queue is not None and not old.thread_queue.empty():        # don't lose poll results that were queued for the old window
            self.widget.thread_queue.put(old.thread_queue.get_nowait())
        old.close()

    def save_state(self):
        sg.user_settings_set_entry(K_STATE, self.state)

    def fonts(self):
        fs = int(cfg(K_FONT_SIZE))
        return {'name': (UI_FONT, fs, 'bold'), 'meta': (UI_FONT, max(fs - 2, 9)), 'badge': (UI_FONT, max(fs - 2, 9), 'bold'), 'dot': (UI_FONT, fs + 3),
                'status': (UI_FONT, max(fs - 2, 9)), 'h1': (UI_FONT, fs + 7, 'bold'), 'body': (UI_FONT, fs), 'small': (UI_FONT, max(fs - 1, 9)), 'title': (UI_FONT, fs, 'bold'),
                'chip': (UI_FONT, max(fs - 2, 9), 'bold'), 'section': (UI_FONT, max(fs - 1, 9), 'bold'), 'mono': (MONO_FONT, fs), 'mono_b': (MONO_FONT, fs, 'bold'),
                'h2': (UI_FONT, fs + 3, 'bold')}

    # ---------------------------------------------------------------- widget window ----------------------------------------------------------------
    def build_widget(self):
        f, sc = self.fonts(), self.scale
        spark_size = (int(SPARK_DAYS * 6 * sc), int(22 * sc))
        rows = []
        self.view = cfg(K_VIEW)
        if self.view == VIEW_ISSUES:
            self.widget_rows, self.visible_rows = [], []
            rows.append([sg.Text('issues', font=f['title'], text_color=C_TEXT, key=K_ITITLE, pad=((8, 6), (3, 2)), tooltip='Click to step through the repos that have issues'),
                         sg.Push(background_color=C_BG), sg.Text('', font=f['badge'], text_color=C_BLUE, key=K_IUNREAD, pad=((0, 16), (5, 2)))])
            for i in range(int(cfg(K_ISSUE_ROWS))):
                row = [sg.Text('●', font=f['dot'], text_color=C_DIM, key=KT_IDOT(i), pad=((8, 4), 0), tooltip='Green: open · Purple: closed'),
                       sg.Column([[sg.Text('', font=f['name'], key=KT_INAME(i), pad=0)],
                                  [sg.Text('', font=f['meta'], text_color=C_MUTED, key=KT_IMETA(i), pad=0)]], pad=(0, 2), background_color=C_BG),
                       sg.Push(background_color=C_BG),
                       sg.Text('', size=(9, 1), font=f['badge'], text_color=C_BG, background_color=C_BG, justification='c', key=KT_IBADGE(i), pad=((6, 2), 0)),
                       sg.Text('', size=(4, 1), font=f['meta'], text_color=C_DIM, justification='r', key=KT_IAGE(i), pad=((0, 8), 0))]
                rows.append([sg.pin(sg.Column([row], key=KT_IROW(i), pad=0, expand_x=True, background_color=C_BG, visible=False), expand_x=True)])
        else:
            self.widget_rows, self.visible_rows = self.repos() + [QUIET_ROW], self.widget_row_ids()
        for repo in self.widget_rows:
            owner, name = repo.split('/') if '/' in repo else ('', 'quiet repos')
            tip = 'Click for the full list of watched repos' if repo == QUIET_ROW else f'https://github.com/{repo}'
            row = [sg.Text('●', font=f['dot'], text_color=C_DIM, key=KT_DOT(repo), pad=((8, 4), 0), tooltip=DOT_TIP),
                   sg.Column([[sg.Text(name, font=f['name'], key=KT_NAME(repo), pad=0, tooltip=tip)],
                              [sg.Text(f'{owner} · checking…', font=f['meta'], text_color=C_MUTED, key=KT_META(repo), pad=0)]], pad=(0, 3), background_color=C_BG),
                   sg.Push(background_color=C_BG),
                   sg.Text('', size=(10, 1), font=f['badge'], text_color=C_BG, background_color=C_BG, justification='c', key=KT_ICHIP(repo), pad=((10, 0), 0), tooltip=CHIP_TIP),
                   sg.Text('', size=(7, 1), font=f['badge'], text_color=C_BG, background_color=C_BG, justification='c', key=KT_BADGE(repo), pad=((6, 8), 0)),
                   sg.Graph(spark_size, (0, 0), spark_size, background_color=C_BG, key=KT_SPARK(repo), pad=((0, 10), 0), tooltip=f'Commits per day, last {SPARK_DAYS} days')]
            row_col = sg.Column([row], key=KT_ROW(repo), pad=0, expand_x=True, background_color=C_BG, visible=repo in self.visible_rows)
            rows.append([sg.pin(row_col, expand_x=True)])          # pinned so a row that goes quiet leaves no gap - the widget shrinks instead
        other = 'issues' if self.view == VIEW_REPOS else 'repos'
        rows.append([sg.Text('starting…', font=f['status'], text_color=C_DIM, key=K_STATUS, pad=((10, 0), (0, 3)), tooltip=f'{APP_NAME} {VERSION}'),
                     sg.Push(background_color=C_BG),
                     sg.Text('⇄', font=f['name'], text_color=C_MUTED, key=K_VIEW_TOGGLE, pad=((0, 10), (0, 2)), tooltip=f'Switch to the {other} view'),
                     sg.ButtonMenu('≡', MENU, key=K_MENU, font=f['name'], button_color=(C_MUTED, C_BG), border_width=0, pad=((0, 6), (0, 2)), tooltip='Menu (or right-click)')])
        first_run = sg.user_settings_get_entry('-LAST WINDOW LOCATION-' + APP_NAME) is None
        self.widget = sg.Window(APP_NAME, rows, no_titlebar=True, keep_on_top=bool(cfg(K_KEEP_ON_TOP)), grab_anywhere=True, alpha_channel=int(cfg(K_OPACITY)) / 100, auto_save_location=True,
                                right_click_menu=MENU, right_click_menu_background_color=C_BG2, right_click_menu_text_color=C_TEXT,
                                right_click_menu_selected_colors=(C_TEXT, C_BG3), margins=(2, 2), background_color=C_BG, finalize=True)
        self.current_alpha = int(cfg(K_OPACITY)) / 100
        widget_map = {}
        for repo in self.widget_rows:
            for w in descendants(self.widget[KT_ROW(repo)].Widget):
                widget_map[w] = repo
            widget_map[self.widget[KT_ICHIP(repo)].Widget] = KT_ICHIP(repo)          # a click on the issue chip opens the Issues window
        if self.view == VIEW_ISSUES:
            for i in range(int(cfg(K_ISSUE_ROWS))):
                for w in descendants(self.widget[KT_IROW(i)].Widget):
                    widget_map[w] = KT_IROW(i)
            widget_map[self.widget[K_ITITLE].Widget] = (K_ITITLE, None)
        widget_map[self.widget[K_VIEW_TOGGLE].Widget] = (K_VIEW_TOGGLE, None)
        bind_click(self.widget, widget_map)
        if self.view == VIEW_ISSUES:
            self.refresh_issue_rows()
        add_close_x(self.widget, K_CLOSE_X)                     # added after the click map, so clicking it can't also open a window
        show_keep_on_top(self.widget, bool(cfg(K_KEEP_ON_TOP)))
        if first_run:
            self.snap_to('TR')
        for repo in self.visible_rows:
            self.refresh_row(repo)
        self.refresh_status()
        self.keep_on_screen()

    def set_keep_on_top(self, on):
        sg.user_settings_set_entry(K_KEEP_ON_TOP, on)
        self.widget.keep_on_top_set() if on else self.widget.keep_on_top_clear()
        show_keep_on_top(self.widget, on)

    def keep_on_screen(self):
        """As the widget changes width (a longer line, a row appearing or going quiet): one sitting against the right edge of the main
        screen stays against it, and one that grew past that edge slides back so all of it shows.  Other monitors are left alone."""
        try:
            self.widget.TKroot.update_idletasks()
            sw, margin = self.widget.get_screen_size()[0], int(12 * self.scale)
            (x, y), w = self.widget.current_location(), self.widget.TKroot.winfo_width()
            last_x, last_w = self.last_geom or (x, w)
            if 0 <= x < sw:
                new_x = x
                if w != last_w and x == last_x and sw - int(40 * self.scale) <= last_x + last_w <= sw:
                    new_x = last_x + last_w - w                 # it was against the right edge - keep it there
                if new_x + w > sw:
                    new_x = max(0, sw - w - margin)
                if new_x != x:
                    self.widget.move(new_x, y)
                    x = new_x
            self.last_geom = (x, w)
        except Exception:
            pass

    def snap_to(self, corner):
        sw, sh = self.widget.get_screen_size()
        self.widget.refresh()
        ww, wh = self.widget.size
        m = int(12 * self.scale)
        self.widget.move(m if 'L' in corner else sw - ww - m, m if 'T' in corner else sh - wh - int(60 * self.scale))

    def unread_count(self, snap):
        return sum(len(snap.get(k, [])) for k in ('new_commits', 'new_branches', 'new_tags', 'new_releases', 'new_issues', 'new_prs')) if snap and snap.get('ok') else 0

    def refresh_row(self, repo):
        if repo not in self.visible_rows:
            return
        if repo == QUIET_ROW:
            self.refresh_summary_row()
            return
        snap, owner = self.snapshots.get(repo), repo.split('/')[0]
        dot, badge, meta, tip = self.widget[KT_DOT(repo)], self.widget[KT_BADGE(repo)], self.widget[KT_META(repo)], ''
        n = self.unread_count(snap)
        if snap is None:
            color, meta_text = C_DIM, f'{owner} · checking…'
        elif not snap.get('ok'):
            color, meta_text, tip = C_RED, f'{owner} · {shorten(snap["error"], 44)}', snap['error']
        else:
            color = C_GREEN if n and not self.snooze_until else C_DIM
            meta_text = f'{owner} · pushed {ago(parse_iso(snap["info"]["pushed_at"]))}'
            tip = snap['info']['description'] or f'https://github.com/{repo}'
        if repo in self.busy:
            color = C_AMBER
        dot.update(text_color=color)
        meta.update(meta_text, text_color=C_RED if snap and not snap.get('ok') else C_MUTED)
        if tip:
            meta.set_tooltip(tip)
        ni, nw = self.issue_counts(snap)
        nc = n - ni                                             # the green badge is code news - issue news has its own blue chip
        if n and self.snooze_until:
            badge.update('zz', text_color=C_MUTED, background_color=C_BG)
        else:
            badge.update(f'{nc} new' if nc else '', text_color=C_BG, background_color=C_GREEN if nc else C_BG)
        self.update_issue_chip(repo, ni, nw, snap.get('open_issue_total', 0) if snap else 0)
        if snap and snap.get('ok'):
            self.draw_spark(self.widget[KT_SPARK(repo)], snap.get('per_day', {}))
        self.refresh_status()

    def refresh_summary_row(self):
        hidden = [r for r in self.repos() if r not in self.visible_rows]
        checked = [r for r in hidden if self.snapshots.get(r)]
        busy = [r for r in hidden if r in self.busy]
        self.widget[KT_NAME(QUIET_ROW)].update(f'{len(hidden)} quiet repo{"s" if len(hidden) != 1 else ""}' if len(checked) == len(hidden) else f'{len(hidden)} repos')
        if busy:
            color, meta = C_AMBER, f'checking {busy[0].split("/")[1]}…'
        elif not checked:
            color, meta = C_DIM, 'first check…'
        else:
            newest = max(checked, key=lambda r: self.snapshots[r]['info']['pushed_at'] or '')
            color, meta = C_DIM, f'newest push: {newest.split("/")[1]} · {ago(parse_iso(self.snapshots[newest]["info"]["pushed_at"]))}'
        self.widget[KT_DOT(QUIET_ROW)].update(text_color=color)
        self.widget[KT_META(QUIET_ROW)].update(meta, text_color=C_MUTED)
        self.widget[KT_BADGE(QUIET_ROW)].update('', background_color=C_BG)
        self.update_issue_chip(QUIET_ROW, 0, sum(self.issue_counts(self.snapshots.get(r))[1] for r in checked), 0)
        per_day = Counter()
        for r in checked:
            per_day.update(self.snapshots[r].get('per_day', {}))
        self.draw_spark(self.widget[KT_SPARK(QUIET_ROW)], per_day)
        self.refresh_status()

    def issue_counts(self, snap):
        """(issues with news, open issues waiting on you) for one repo's snapshot."""
        if not snap or not snap.get('ok'):
            return 0, 0
        return len(snap.get('new_issues', [])), sum(1 for r in snap.get('open_issues', []) if r['waiting'])

    def update_issue_chip(self, row, ni, nw, total):
        """Blue 'N issues' when there's issue news, amber 'N waiting' when people are waiting on a reply, empty otherwise."""
        chip = self.widget[KT_ICHIP(row)]
        if self.snooze_until or not (ni or nw):
            chip.update('', background_color=C_BG)
        elif ni:
            chip.update(n_of(ni, 'issue'), text_color=C_BG, background_color=C_BLUE)
        else:
            chip.update(f'{nw} waiting', text_color=C_AMBER, background_color=C_BG)
        tip = f'{n_of(nw, "issue")} in the quiet repos waiting on you' if row == QUIET_ROW else f'{n_of(ni, "issue")} with news · {nw} waiting on you · {total} open'
        chip.set_tooltip(tip + ' - click for the Issues window')

    # ---------------------------------------------------------------- issues view of the widget ----------------------------------------------------------------
    def issue_view_repos(self):
        """Watched repos that have issues to show, the one with the most open issues first."""
        def count(r):
            snap = self.snapshots.get(r)
            return (snap.get('open_issue_total', 0) + len(snap.get('new_issues', []))) if snap and snap.get('ok') else 0
        return sorted((r for r in self.repos() if count(r)), key=count, reverse=True)

    def issue_view_repo(self):
        wanted = clean_entry(str(cfg(K_ISSUES_REPO)))
        if wanted and any(wanted.lower() == r.lower() for r in self.repos()):
            return next(r for r in self.repos() if r.lower() == wanted.lower())
        candidates = self.issue_view_repos()
        return candidates[0] if candidates else (self.repos()[0] if self.repos() else '')

    def switch_view(self, view=None):
        self.view = view or (VIEW_ISSUES if self.view == VIEW_REPOS else VIEW_REPOS)
        sg.user_settings_set_entry(K_VIEW, self.view)
        self.rebuild_widget()

    def issue_list(self, snap):
        """Open issues plus the closed ones with news, newest activity first, each carrying its news record if it has one."""
        news = {r['number']: r for r in snap.get('new_issues', [])}
        items = [dict(news.get(r['number'], r), waiting=r['waiting'], news=news.get(r['number'])) for r in snap.get('open_issues', [])]
        seen = {r['number'] for r in items}
        items += [dict(r, news=r) for r in snap.get('new_issues', []) if r['number'] not in seen]
        items.sort(key=lambda r: r['date'], reverse=True)
        return items

    def refresh_issue_rows(self):
        repo, n_rows = self.issue_view_repo(), int(cfg(K_ISSUE_ROWS))
        snap = self.snapshots.get(repo)
        name = repo.split('/')[1] if '/' in repo else repo
        items = self.issue_list(snap)[:n_rows] if snap and snap.get('ok') else []
        self.issue_rows_shown = items
        self.widget[K_ITITLE].update(f'{name} issues' if name else 'issues')
        self.widget[K_ITITLE].set_tooltip(f'{repo}\nClick to step through the repos that have issues' if repo else 'No repos yet')
        for i in range(n_rows):
            self.widget[KT_IROW(i)].update(visible=i < len(items))
            if i >= len(items):
                continue
            rec, news = items[i], items[i]['news']
            what = news['what'] if news else ''
            badge, fg, bg = ('', C_BG, C_BG)
            if what:
                badge, fg, bg = {'opened': 'NEW', 'commented': 'COMMENT', 'closed': 'CLOSED'}.get(what, 'NEW'), C_BG, C_PURPLE if what == 'closed' else C_BLUE
            elif rec['waiting']:
                badge, fg, bg = 'WAITING', C_AMBER, C_BG
            parts = [f'{what if what == "closed" else "comment"} by {news["actor"]}'] if what in ('commented', 'closed') else []
            parts += [rec['user'], n_of(rec['comments'], 'comment'), ', '.join(rec['labels'][:2])]
            self.widget[KT_IDOT(i)].update(text_color=C_PURPLE if rec['state'] == 'closed' else C_GREEN)
            self.widget[KT_INAME(i)].update(shorten(f'#{rec["number"]}  {rec["title"]}', 46), text_color=C_TEXT if what or rec['waiting'] else C_MUTED)
            self.widget[KT_INAME(i)].set_tooltip(f'#{rec["number"]} {rec["title"]}\n{rec["state"]} · updated {local_str(parse_iso(rec["date"]))}')
            self.widget[KT_IMETA(i)].update(shorten(' · '.join(x for x in parts if x), 52))
            self.widget[KT_IBADGE(i)].update(badge, text_color=fg, background_color=bg)
            self.widget[KT_IAGE(i)].update(age_short(parse_iso(rec['date'])))
        ni, nw = self.issue_counts(snap)
        if self.snooze_until or not (ni or nw):
            self.widget[K_IUNREAD].update('')
        else:
            self.widget[K_IUNREAD].update(' · '.join(x for x in [f'{ni} new' if ni else '', f'{nw} waiting' if nw else ''] if x), text_color=C_BLUE if ni else C_AMBER)
        self.refresh_status()

    def draw_spark(self, graph, per_day):
        graph.erase()
        w, h = graph.CanvasSize
        today = date.today()
        counts = [per_day.get((today - timedelta(days=i)).isoformat(), 0) for i in range(SPARK_DAYS - 1, -1, -1)]
        peak, bw = max(counts) or 1, w / SPARK_DAYS
        for i, c in enumerate(counts):
            top = max(2, round(c / peak * (h - 2))) if c else 1
            graph.draw_rectangle((i * bw + 1, top), ((i + 1) * bw - 1, 0), fill_color=C_GREEN if c else C_DIM, line_color=C_GREEN if c else C_DIM)

    def refresh_status(self):
        if self.poller is None:
            return
        rate = next((s.get('rate') for s in self.snapshots.values() if s.get('rate', {}).get('remaining') is not None), None)
        api = f' · API {rate["remaining"]:,} left' if rate else ''
        if self.poller.paused:
            text = 'paused' + api
        elif self.snooze_until:
            text = f'badges hidden until {clock(self.snooze_until)}' + api
        else:
            checked = max((s['checked_at'] for s in self.snapshots.values()), default=None)
            nxt = self.poller.next_check
            text = (f'checked {clock(parse_iso(checked).astimezone())}' if checked else 'first check…') + (f' · next {clock(nxt.astimezone())}' if nxt else '') + api
        if self.owner_errors:
            text = ' · '.join(f'{owner}: {shorten(err, 50)}' for owner, err in self.owner_errors.items())
        self.widget[K_STATUS].update(('DEMO · ' if DEMO else '') + text, text_color=C_RED if self.owner_errors else C_DIM)

    def apply_alpha(self):
        alpha = int(cfg(K_OPACITY)) / 100
        if cfg(K_QUIET_ON):
            h, start, end = datetime.now().hour, HOURS.index(cfg(K_QUIET_FROM)), HOURS.index(cfg(K_QUIET_TO))
            quiet = (start <= h < end) if start < end else (h >= start or h < end)
            alpha = round(alpha * 0.45, 2) if quiet else alpha
        if alpha != self.current_alpha:
            self.widget.set_alpha(alpha)
            self.current_alpha = alpha

    # ---------------------------------------------------------------- marking things read ----------------------------------------------------------------
    def mark_read(self, repo, sync=True):
        snap = self.snapshots.get(repo)
        if not snap or not snap.get('ok'):
            return
        now = utcnow().isoformat()
        self.state[repo] = {'baselined': True, 'read_heads': dict(snap['branches']), 'known_branches': list(snap['branches']), 'known_tags': [t['name'] for t in snap['tags']],
                            'last_read_at': now, 'issues_read_at': now}
        self.save_state()
        self.poller.state = self.state
        for k in ('new_commits', 'new_branches', 'gone_branches', 'new_tags', 'new_releases', 'new_issues', 'new_prs'):
            snap[k] = []
        if sync:
            self.sync_widget()

    def mark_issues_read(self, repo):
        """Clear the issue news (the blue chip) without touching the commit news."""
        snap = self.snapshots.get(repo)
        if not snap or not snap.get('ok'):
            return
        self.state.setdefault(repo, {})['issues_read_at'] = utcnow().isoformat()
        self.save_state()
        self.poller.state = self.state
        snap['new_issues'] = []
        self.sync_widget()

    # ---------------------------------------------------------------- "all repos" list (click the quiet-repos row) ----------------------------------------------------------------
    def open_all_repos(self):
        if self.all_win is not None:
            self.all_win.close()
        f, sc = self.fonts(), self.scale
        def order(r):
            snap = self.snapshots.get(r)
            pushed = parse_iso(snap['info']['pushed_at']).timestamp() if snap and snap.get('ok') and snap['info']['pushed_at'] else 0
            return (0 if snap and not snap.get('ok') else 1 if self.unread_count(snap) else 2, -pushed)

        repos = sorted(self.repos(), key=order)
        rows = []
        for repo in repos:
            snap = self.snapshots.get(repo)
            n, bad = self.unread_count(snap), bool(snap and not snap.get('ok'))
            color = C_RED if bad else C_GREEN if n else C_DIM
            pushed = f'pushed {ago(parse_iso(snap["info"]["pushed_at"]))}' if snap and snap.get('ok') else shorten(snap['error'], 40) if bad else 'checking…'
            desc = snap['info']['description'] if snap and snap.get('ok') else ''
            row = [sg.Text('●', font=f['dot'], text_color=color, pad=((6, 4), 0)), sg.Text(repo.split('/')[1], size=(30, 1), font=f['title'], pad=0),
                   sg.Text(f'{n} new' if n else '', size=(7, 1), font=f['badge'], text_color=C_BG, background_color=C_GREEN if n else C_BG, justification='c', pad=((0, 8), 0)),
                   sg.Text(pushed, size=(24, 1), font=f['small'], text_color=C_RED if bad else C_MUTED, pad=0),
                   sg.Text(shorten(desc, 56), size=(56, 1), font=f['small'], text_color=C_MUTED, pad=0)]
            rows.append([sg.Column([row], key=KT_ALL_ROW(repo), pad=0, background_color=C_BG)])
        height = min(int(520 * sc), int(36 * sc) * max(len(rows), 3))
        col = sg.Column(rows, scrollable=True, vertical_scroll_only=True, size=(int(1000 * sc), height), key=K_ALL_LIST, background_color=C_BG, expand_y=True, pad=(0, 4),
                        sbar_background_color=C_LINE, sbar_trough_color=C_BG, sbar_arrow_color=C_MUTED)
        layout = [[sg.Text(f'Watched repos · {len(repos)}', font=f['h1'], text_color=C_BLUE, pad=((6, 6), (6, 0))), sg.Push(background_color=C_BG),
                   sg.Text("click a repo to open What's new", font=f['small'], text_color=C_MUTED, pad=((0, 6), (14, 0)))],
                  [col],
                  [sg.Text('↑↓ PgUp PgDn Home End scroll · Esc closes', font=f['status'], text_color=C_DIM, pad=((6, 0), (6, 4))), sg.Push(background_color=C_BG),
                   sg.Button('Close', key=K_CLOSE, **self.btn(f))]]
        self.all_win = sg.Window(f'{APP_NAME} · watched repos', layout, finalize=True, resizable=True, margins=(4, 4), background_color=C_BG)
        widget_map = {}
        for repo in repos:
            for w in descendants(self.all_win[KT_ALL_ROW(repo)].Widget):
                widget_map[w] = repo
        bind_click(self.all_win, widget_map)
        for seq, key in KEY_BINDS:
            self.all_win.bind(seq, key)
        wheel_scrolls_list(self.all_win, K_ALL_LIST)

    def all_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC):
            self.all_win.close()
            self.all_win = None
        elif event in LIST_KEYS:
            scroll_canvas(self.all_win[K_ALL_LIST].TKColFrame.canvas, event)
        elif event == K_CLICK:
            self.open_details(values[event])

    # ---------------------------------------------------------------- repo picker (Settings -> Choose repos…) ----------------------------------------------------------------
    def pick_fetch_bg(self, token, owner, window):
        try:
            result = demo_owner_repos(owner) if DEMO else list_owner_repos(GitHub(token), owner)
        except Exception as e:
            result = str(e)
        try:
            window.write_event_value(K_PICK_READY, (owner, result))
        except Exception:
            pass

    def open_picker(self, owner, repos, current_text):
        if self.pick_win is not None:
            self.pick_win.close()
        f, sc = self.fonts(), self.scale
        listed = {e.lower() for e in parse_entries(current_text)}
        watch_all = owner.lower() in listed
        self.pick_owner, self.pick_repos = owner, sorted(repos, key=lambda r: r['pushed_at'] or '', reverse=True)
        cutoff, rows = utcnow() - timedelta(days=90), []
        for i, r in enumerate(self.pick_repos):
            flags = ' · '.join(x for x in ['private' if r['private'] else 'public', 'fork' if r['fork'] else '', 'archived' if r['archived'] else ''] if x)
            recent = bool(r['pushed_at']) and parse_iso(r['pushed_at']) > cutoff
            ticked = watch_all or r['repo'].lower() in listed
            rows.append([sg.Checkbox(r['repo'].split('/')[1], key=KT_PICK_ROW(i), default=ticked, font=f['title'], size=(30, 1), pad=((6, 4), 2)),
                         sg.Text(flags, size=(18, 1), font=f['small'], text_color=C_PURPLE if r['private'] else C_MUTED, pad=0),
                         sg.Text(f'pushed {ago(parse_iso(r["pushed_at"]))}', size=(20, 1), font=f['small'], text_color=C_GREEN if recent else C_MUTED, pad=0),
                         sg.Text(shorten(r['description'], 56), size=(56, 1), font=f['small'], text_color=C_MUTED, pad=0)])
        if not rows:
            rows = [[sg.Text('No repos found for that account', font=f['body'], text_color=C_MUTED, pad=(6, 6))]]
        height = min(int(520 * sc), int(36 * sc) * max(len(rows), 3))
        col = sg.Column(rows, scrollable=True, vertical_scroll_only=True, size=(int(1000 * sc), height), key=K_PICK_LIST, background_color=C_BG, expand_y=True, pad=(0, 4),
                        sbar_background_color=C_LINE, sbar_trough_color=C_BG, sbar_arrow_color=C_MUTED)
        layout = [[sg.Text(f'{owner} · {n_of(len(repos), "repo")}', font=f['h1'], text_color=C_BLUE, pad=((6, 6), (6, 0))), sg.Push(background_color=C_BG),
                   sg.Text('tick the repos to watch · ticking every one watches the whole account (new repos included)', font=f['small'], text_color=C_MUTED,
                           pad=((0, 6), (14, 0)))],
                  [col],
                  [sg.Button('All', key=K_PICK_ALL, **self.btn(f)), sg.Button('None', key=K_PICK_NONE, **self.btn(f)),
                   sg.Button('Pushed in last 90 days', key=K_PICK_ACTIVE, **self.btn(f)), sg.Push(background_color=C_BG),
                   sg.Button('Use selected', key=K_PICK_OK, font=f['body'], button_color=(C_BG, C_GREEN), border_width=0, pad=((0, 6), (6, 0))),
                   sg.Button('Cancel', key=K_CANCEL, **self.btn(f))],
                  [sg.Text('↑↓ PgUp PgDn Home End scroll · Esc cancels', font=f['status'], text_color=C_DIM, pad=((6, 0), (6, 4)))]]
        self.pick_win = sg.Window(f'Choose repos · {owner}', layout, finalize=True, keep_on_top=True, resizable=True, margins=(4, 4), background_color=C_BG)
        for seq, key in KEY_BINDS:
            self.pick_win.bind(seq, key)
        wheel_scrolls_list(self.pick_win, K_PICK_LIST)

    def pick_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CANCEL, K_KEY_ESC):
            self.pick_win.close()
            self.pick_win = None
        elif event in LIST_KEYS:
            scroll_canvas(self.pick_win[K_PICK_LIST].TKColFrame.canvas, event)
        elif event in (K_PICK_ALL, K_PICK_NONE, K_PICK_ACTIVE):
            cutoff = utcnow() - timedelta(days=90)
            for i, r in enumerate(self.pick_repos):
                on = event == K_PICK_ALL or (event == K_PICK_ACTIVE and bool(r['pushed_at']) and parse_iso(r['pushed_at']) > cutoff)
                self.pick_win[KT_PICK_ROW(i)].update(on)
        elif event == K_PICK_OK:
            chosen = [r['repo'] for i, r in enumerate(self.pick_repos) if values.get(KT_PICK_ROW(i))]
            if self.pick_repos and len(chosen) == len(self.pick_repos):
                chosen = [self.pick_owner]                      # everything ticked -> watch the account itself, so new repos join automatically
            if self.settings_win is not None:
                mine = lambda line: clean_entry(line).lower() == self.pick_owner.lower() or clean_entry(line).lower().startswith(self.pick_owner.lower() + '/')
                keep = [line.strip() for line in self.settings_win[K_REPOS].get().splitlines() if line.strip() and not mine(line)]
                self.settings_win[K_REPOS].update('\n'.join(keep + chosen))
            self.pick_win.close()
            self.pick_win = None

    # ---------------------------------------------------------------- details ("What's new") window ----------------------------------------------------------------
    def build_items(self, snap):
        items = [{'kind': 'merge' if c['parents'] > 1 else 'commit', 'new': True, 'date': c['date'], 'data': c} for c in snap['new_commits']]
        items += [{'kind': 'branch', 'new': True, 'date': max((c['date'] for c in b['commits']), default=snap['checked_at']), 'data': b} for b in snap['new_branches']]
        items += [{'kind': 'tag', 'new': True, 'date': snap['checked_at'], 'data': t} for t in snap['new_tags']]
        items += [{'kind': 'release', 'new': True, 'date': r['date'], 'data': r} for r in snap['new_releases']]
        items += [{'kind': 'issue', 'new': True, 'date': i['date'], 'data': i} for i in snap['new_issues']]
        items += [{'kind': 'pr', 'new': True, 'date': p['date'], 'data': p} for p in snap['new_prs']]
        items.sort(key=lambda it: it['date'] or '', reverse=True)
        new_shas = {c['sha'] for c in snap['new_commits']}
        earlier = [{'kind': 'merge' if c['parents'] > 1 else 'commit', 'new': False, 'date': c['date'], 'data': c} for c in snap['history'] if c['sha'] not in new_shas]
        earlier.sort(key=lambda it: it['date'] or '', reverse=True)
        return items, earlier[:EARLIER_LIMIT]

    def item_row(self, idx, it, f):
        kind, d, color = it['kind'], it['data'], KIND_COLOR[it['kind']]
        det = self.poller.commit_cache.get(d['sha']) if kind in ('commit', 'merge') else None
        add = dele = ''
        if kind in ('commit', 'merge'):
            title, meta = d['title'], commit_meta(d, det)
            add, dele = (f'+{det["add"]}', f'−{det["del"]}') if det else ('', '')
        elif kind == 'branch':
            title, meta = f"New branch '{d['name']}'", f"{n_of(len(d['commits']), 'commit')} not on {d['default']} · {d['sha'][:7]}"
        elif kind == 'tag':
            title, meta = f'New tag {d["name"]}', f'points at {d["sha"][:7]}'
        elif kind == 'release':
            title, meta = f'Release {d["name"]}', f'{d["tag"]} · by {d["author"]}' + (' · pre-release' if d['prerelease'] else '')
        else:
            title = f'#{d["number"]} {d["title"]}'
            meta = f'{d["what"]} by {d.get("actor") or d["user"]} · {d["state"]} · {n_of(d["comments"], "comment")}' + (' · ' + ', '.join(d['labels']) if d['labels'] else '')
        chip_text = {'commit': 'COMMIT', 'merge': 'MERGE', 'branch': 'BRANCH', 'tag': 'TAG', 'release': 'RELEASE', 'issue': 'ISSUE', 'pr': 'PR'}[kind]
        chip_fg, chip_bg = (C_BG, color) if it['new'] else (C_MUTED, C_BG3)
        chip = sg.Text(f' {chip_text} ', size=(8, 1), justification='c', font=f['chip'], text_color=chip_fg, background_color=chip_bg, pad=((6, 6), (4, 0)))
        tp = (0, (4, 0))
        row1 = [chip, sg.Text(ago(parse_iso(it['date'])), size=(12, 1), font=f['small'], text_color=C_MUTED, pad=tp),
                sg.Text(shorten(title, self.title_chars), size=(self.title_chars, 1), font=f['title'], text_color=C_TEXT if it['new'] else C_MUTED, pad=tp),
                sg.Text(add, size=(6, 1), justification='r', font=f['small'], text_color=C_GREEN, key=KT_ADD(idx), pad=(0, (4, 0))),
                sg.Text(dele, size=(6, 1), justification='r', font=f['small'], text_color=C_RED, key=KT_DEL(idx), pad=((2, 6), (4, 0)))]
        row2 = [sg.Text('', size=(8, 1), font=f['chip'], pad=((6, 6), 0)), sg.Text('', size=(12, 1), font=f['small'], pad=0),
                sg.Text(shorten(meta, self.meta_chars), size=(self.meta_chars, 1), font=f['small'], text_color=C_MUTED, key=KT_ITEM_META(idx), pad=(0, (0, 4)))]
        return sg.Column([row1, row2], key=KT_ITEM(idx), pad=0, expand_x=True, background_color=C_BG)

    def open_details(self, repo, reopen=False):
        snap = self.snapshots.get(repo)
        if not snap or not snap.get('ok'):
            msg = snap['error'] if snap else 'Still doing the first check - try again in a moment.'
            sg.popup(f'{repo}\n\n{msg}', title=repo, keep_on_top=True, background_color=C_BG2, text_color=C_TEXT)
            return
        if self.details is not None and self.details_repo == repo and not reopen:
            self.details.bring_to_front()
            return
        self.close_details(mark=not reopen)
        f, sc, info = self.fonts(), self.scale, snap['info']
        owner, name = repo.split('/')
        sw, sh = self.widget.get_screen_size()
        list_w, list_h = min(int(980 * sc), int(sw * 0.47)), min(int(560 * sc), int(sh * 0.5))
        self.title_chars, self.meta_chars = max(26, int(54 * list_w / (980 * sc))), max(40, int(78 * list_w / (980 * sc)))
        pane_chars = max(50, min(100, int(72 * (sw - list_w) / (sw * 0.5))))
        items, earlier = self.build_items(snap)
        self.details_items = items + earlier
        rows = [[sg.Text(f'NEW · {len(items)}' if items else 'NOTHING NEW', font=f['section'], text_color=C_GREEN if items else C_MUTED, pad=((8, 0), (6, 2)))]]
        rows += [[self.item_row(i, it, f)] for i, it in enumerate(items)]
        if earlier:
            rows.append([sg.Text(f'EARLIER · last {snap["history_days"]} days on {info["default_branch"]}', font=f['section'], text_color=C_MUTED, pad=((8, 0), (12, 2)))])
            rows += [[self.item_row(len(items) + i, it, f)] for i, it in enumerate(earlier)]
        facts = f'{n_of(info["stars"], "star")} · {info["watchers"]} watching · {n_of(info["forks"], "fork")} · {n_of(info["open_issues"], "open issue")}'
        facts += f' · {n_of(len(snap["branches"]), "branch", "branches")}' + (f' · {info["language"]}' if info['language'] else '')
        by = f'by {owner}' + (' · private' if info['private'] else '')
        head = [[sg.Text(name, font=f['h1'], text_color=C_BLUE, pad=((8, 6), (6, 0))), sg.Text(by, font=f['small'], text_color=C_MUTED, pad=(0, (16, 0))),
                 sg.Push(background_color=C_BG), sg.Text(facts, font=f['small'], text_color=C_MUTED, pad=((0, 8), (16, 0)))]]
        if info['description']:
            head.append([sg.Text(info['description'], font=f['body'], text_color=C_MUTED, pad=((8, 0), (0, 2)))])
        head.append([sg.Multiline(size=(150, 3), key=K_DIGEST, font=f['body'], disabled=True, write_only=True, no_scrollbar=True, background_color=C_BG, text_color=C_TEXT,
                                  border_width=0, expand_x=True, pad=((8, 8), (2, 6)))])
        head.append([sg.Text('New activity arrived while this was open · click Refresh to reload', key=K_FRESH, font=f['small'], text_color=C_AMBER, visible=False,
                             pad=((8, 0), (0, 4)))])
        list_col = sg.Column(rows, scrollable=True, vertical_scroll_only=True, size=(list_w, list_h), key=K_LIST, background_color=C_BG, expand_y=True, pad=(0, 0),
                             sbar_background_color=C_LINE, sbar_trough_color=C_BG, sbar_arrow_color=C_MUTED)
        detail = sg.Multiline(size=(pane_chars, 34), key=K_DETAIL, font=f['mono'], disabled=True, write_only=True, horizontal_scroll=True, background_color=C_BG2,
                              text_color=C_TEXT, border_width=0, expand_x=True, expand_y=True, pad=(0, 0), sbar_background_color=C_LINE, sbar_trough_color=C_BG2,
                              sbar_arrow_color=C_MUTED)
        btn = dict(font=f['small'], button_color=(C_TEXT, C_BG3), border_width=0, pad=((0, 6), (6, 0)))
        right = sg.Column([[detail], [sg.Button('Open on GitHub', key=K_OPEN, **btn), sg.Button('Copy SHA', key=K_COPY_SHA, **btn), sg.Button('Copy link', key=K_COPY_LINK, **btn),
                                      sg.Push(background_color=C_BG), sg.Text(KEYS_HINT, font=f['status'], text_color=C_DIM, pad=(0, (6, 0)))]],
                          expand_x=True, expand_y=True, pad=((8, 0), 0), background_color=C_BG)
        chart = sg.Graph((int(700 * sc), int(84 * sc)), (0, 0), (int(700 * sc), int(84 * sc)), background_color=C_BG, key=K_CHART, pad=((8, 8), (4, 4)))
        foot = [[chart, sg.Column([[sg.Text('', key=K_RHYTHM, font=f['small'], text_color=C_MUTED, size=(100, 2))],
                                   [sg.Button('Mark all as read', key=K_MARK_READ, **btn), sg.Button('Refresh now', key=K_REFRESH, **btn),
                                    sg.Button('Issues…', key=K_ISSUES_BTN, **btn), sg.Button('Open repo on GitHub', key=K_OPEN_REPO, **btn),
                                    sg.Button('Copy digest', key=K_COPY_DIGEST, **btn),
                                    sg.Button('Close', key=K_CLOSE, **btn)]], background_color=C_BG, pad=(0, 0))]]
        layout = head + [[list_col, sg.VerticalSeparator(color=C_LINE), right]] + foot
        self.details = sg.Window(f"{name} · What's new", layout, finalize=True, resizable=True, margins=(4, 4), background_color=C_BG, icon=None)
        self.details_repo, self.details_sig, self.selected, self.item_widgets = repo, self.signature(snap), None, {}
        for i in range(len(self.details_items)):
            for w in descendants(self.details[KT_ITEM(i)].Widget):
                self.item_widgets[w] = i
        bind_click(self.details, self.item_widgets)
        for seq, key in KEY_BINDS:
            self.details.bind(seq, key)
        wheel_scrolls_list(self.details, K_LIST)
        self.write_digest(snap)
        self.draw_chart(snap)
        self.details[K_RHYTHM].update(self.rhythm_text(snap))
        if self.details_items:
            self.select_item(0)
        else:
            self.details[K_DETAIL].print('Nothing to show yet.', text_color=C_MUTED)

    def signature(self, snap):
        return tuple(sorted(str(x) for k in ('new_commits', 'new_branches', 'new_tags', 'new_releases', 'new_issues', 'new_prs') for x in snap.get(k, [])))

    def close_details(self, mark=True):
        if self.details is not None:
            if mark and cfg(K_MARK_ON_CLOSE) and self.details_repo:
                self.mark_read(self.details_repo)
            self.details.close()
            self.details, self.details_repo, self.selected, self.item_widgets = None, None, None, {}

    def write_digest(self, snap):
        ml, rstate, cache = self.details[K_DIGEST], self.state.get(snap['repo'], {}), self.poller.commit_cache
        ml.update('')
        last, nc = parse_iso(rstate.get('last_read_at')), snap['new_commits']
        when = local_str(last) if last else 'the start'
        seg = []
        if not self.unread_count(snap):
            seg += [('Nothing new since ', C_TEXT), (when, C_BLUE), ('.  Last push was ', C_TEXT), (ago(parse_iso(snap['info']['pushed_at'])), C_GREEN),
                    (f'.  Below is the last {snap["history_days"]} days for context.', C_TEXT)]
        else:
            seg += [('Since you last looked (', C_TEXT), (when, C_BLUE), ('):  ', C_TEXT)]
            if nc:
                authors, branches = Counter(c['author'] for c in nc), Counter(c['branch'] for c in nc)
                who = authors.most_common(1)[0][0] + ('' if len(authors) == 1 else f' and {n_of(len(authors) - 1, "other")}')
                where = ' and '.join(f"'{b}'" for b in branches) if len(branches) <= 2 else f'{len(branches)} branches'
                seg += [(who, C_TEXT), (' pushed ', C_TEXT), (n_of(len(nc), 'commit'), C_GREEN), (f' to {where}', C_TEXT)]
                dets = [cache[c['sha']] for c in nc if c['sha'] in cache]
                if dets:
                    files = {x['name'] for d in dets for x in d['files']}
                    folders = Counter(top_folder(x['name']) for d in dets for x in d['files'])
                    at_least = 'at least ' if len(dets) < len(nc) else ''
                    seg += [(f', touching {at_least}{n_of(len(files), "file")} (', C_TEXT), (f'+{sum(d["add"] for d in dets)}', C_GREEN), (' ', C_TEXT),
                            (f'−{sum(d["del"] for d in dets)}', C_RED), (')', C_TEXT)]
                    if folders:
                        seg += [(', mostly in ', C_TEXT), (' and '.join(fo for fo, _ in folders.most_common(2)), C_AMBER)]
                seg += [('.  ', C_TEXT)]
            for b in snap['new_branches']:
                seg += [('New branch ', C_TEXT), (f"'{b['name']}'", C_AMBER), (f' with {n_of(len(b["commits"]), "commit")} of its own.  ', C_TEXT)]
            if snap['gone_branches']:
                seg += [(n_of(len(snap['gone_branches']), 'branch', 'branches'), C_AMBER), (' deleted: ' + ', '.join(snap['gone_branches']) + '.  ', C_TEXT)]
            if snap['new_tags']:
                seg += [(n_of(len(snap['new_tags']), 'new tag'), C_PURPLE), (': ' + ', '.join(t['name'] for t in snap['new_tags']) + '.  ', C_TEXT)]
            if snap['new_releases']:
                seg += [(n_of(len(snap['new_releases']), 'release'), C_PURPLE), (' published: ' + ', '.join(r['name'] for r in snap['new_releases']) + '.  ', C_TEXT)]
            for kind, key, color in (('issue', 'new_issues', C_BLUE), ('PR', 'new_prs', C_PINK)):
                whats = Counter(x['what'] for x in snap[key])
                if len(whats) == 1:
                    seg += [(n_of(len(snap[key]), kind), color), (f' {whats.most_common(1)[0][0]}.  ', C_TEXT)]
                elif whats:
                    seg += [(n_of(len(snap[key]), kind), color), (': ' + ', '.join(f'{n} {w}' for w, n in whats.most_common()) + '.  ', C_TEXT)]
            if not snap['new_issues'] and not snap['new_prs']:
                seg += [('No issue or PR activity.', C_MUTED)]
        for text, color in seg:
            ml.print(text, text_color=color, end='')
        self.digest_plain = f'{snap["repo"]} - ' + ''.join(text for text, _ in seg)

    def rhythm_text(self, snap):
        stamps = [parse_iso(c['date']).astimezone() for c in snap['history'] if c['date']]
        if not stamps:
            return f'No commits on {snap["info"]["default_branch"]} in the last {snap["history_days"]} days.'
        days = Counter(s.date() for s in stamps)
        today, streak = date.today(), 0
        d = today if today in days else today - timedelta(days=1)
        while d in days:
            streak, d = streak + 1, d - timedelta(days=1)
        weekday = Counter(s.strftime('%A') for s in stamps).most_common(1)[0][0]
        hours = Counter(s.hour for s in stamps)
        best = max(range(24), key=lambda h: hours[h] + hours[(h + 1) % 24] + hours[(h + 2) % 24])
        per_week = len(days) / (snap['history_days'] / 7)
        streak_text = f'on a {streak}-day streak' if streak else 'no current streak'
        return (f'Rhythm · last {snap["history_days"]} days: {n_of(len(stamps), "commit")} on {n_of(len(days), "day")} (~{per_week:.1f} active days/week) · {streak_text}\n'
                f'Busiest on {weekday}s · usually commits {hour12(best)}–{hour12((best + 3) % 24)} (your time) · last push {ago(parse_iso(snap["info"]["pushed_at"]))}')

    def draw_chart(self, snap):
        g = self.details[K_CHART]
        g.erase()
        w, h = g.CanvasSize
        days, per_day, today = snap['history_days'], snap['per_day'], date.today()
        counts = [(today - timedelta(days=i), per_day.get((today - timedelta(days=i)).isoformat(), 0)) for i in range(days - 1, -1, -1)]
        peak, bw, base, top = max((c for _, c in counts), default=0) or 1, w / days, int(16 * self.scale), h - int(4 * self.scale)
        g.draw_line((0, base), (w, base), color=C_LINE)
        for i, (day, c) in enumerate(counts):
            x0, x1 = i * bw + 1, (i + 1) * bw - 1
            if c:
                g.draw_rectangle((x0, base + c / peak * (top - base)), (x1, base), fill_color=C_GREEN, line_color=C_GREEN)
            if day.weekday() == 0 or days <= 14:
                g.draw_text(f'{day:%b} {day.day}' if day.weekday() == 0 or day == counts[0][0] else str(day.day), ((x0 + x1) / 2, base / 2), color=C_MUTED, font=(UI_FONT, 9))
        g.draw_text(f'{peak}/day', (w - int(24 * self.scale), top - 6), color=C_MUTED, font=(UI_FONT, 9))

    def highlight(self, idx, on):
        bg = C_BG3 if on else C_BG
        for w in descendants(self.details[KT_ITEM(idx)].Widget):
            try:
                if not (isinstance(w, tk.Label) and w.cget('text').strip() in ('COMMIT', 'MERGE', 'BRANCH', 'TAG', 'RELEASE', 'ISSUE', 'PR')):
                    w.configure(background=bg)
            except Exception:
                pass

    def select_item(self, idx):
        if self.selected is not None:
            self.highlight(self.selected, False)
        self.selected = idx
        self.highlight(idx, True)
        it = self.details_items[idx]
        self.details[K_LIST].TKColFrame.canvas.focus_set()
        if it['kind'] in ('commit', 'merge'):
            det = self.poller.commit_cache.get(it['data']['sha'])
            self.render_commit(it['data'], det)
            if det is None and it['data']['sha'] not in self.fetching:
                self.fetching.add(it['data']['sha'])
                threading.Thread(target=self.fetch_detail_bg, args=(self.details_repo, it['data']['sha'], self.details), daemon=True).start()
        elif it['kind'] == 'issue':
            self.show_thread(self.details, K_DETAIL, self.details_repo, it['data'])
        else:
            self.render_other(it)

    def fetch_detail_bg(self, repo, sha, window):
        try:
            det = fetch_commit_detail(self.poller.gh, repo, sha, self.poller.commit_cache)
        except Exception as e:
            det = f'{e}'
        try:
            window.write_event_value(K_DETAIL_READY, (sha, det))
        except Exception:
            pass

    def render_commit(self, c, det):
        ml, f = self.details[K_DETAIL], self.fonts()
        ml.Widget.configure(wrap='none')                        # diffs scroll sideways; issue conversations (render_thread) wrap
        ml.update('')
        ml.print(c['title'], text_color=C_TEXT, font=f['mono_b'])
        if c['body']:
            ml.print(c['body'], text_color=C_MUTED)
        ml.print('')
        when = parse_iso(c['date'])
        ml.print(f'{c["author"]}' + (f' (@{c["login"]})' if c['login'] and c['login'] != c['author'] else ''), text_color=C_TEXT, end='')
        ml.print(f'  ·  {local_str(when)} ({ago(when)})  ·  on {c["branch"]}  ·  {c["short"]}' + ('  ·  merge commit' if c['parents'] > 1 else ''), text_color=C_MUTED)
        if det is None:
            ml.print('\nFetching files and diff…', text_color=C_AMBER)
            return
        ml.print(f'{n_of(len(det["files"]), "file")} changed   ', text_color=C_TEXT, end='')
        ml.print(f'+{det["add"]}', text_color=C_GREEN, end='  ')
        ml.print(f'−{det["del"]}', text_color=C_RED)
        ml.print('')
        for x in det['files']:
            ml.print(f'  {x["status"][:1].upper()}  ', text_color=STATUS_COLOR.get(x['status'], C_MUTED), end='')
            ml.print(f'{x["name"]:<60}', text_color=C_TEXT, end='  ')
            ml.print(f'+{x["add"]:<5}', text_color=C_GREEN, end='')
            ml.print(f'−{x["del"]}', text_color=C_RED)
        lines_left = MAX_PATCH_LINES
        for x in det['files']:
            ml.print('\n' + '─' * 110, text_color=C_LINE)
            ml.print(x['name'] + (f'  (was {x["prev"]})' if x['prev'] else ''), text_color=C_BLUE, font=f['mono_b'])
            if not x['patch']:
                ml.print('  (binary or too large - no text diff)', text_color=C_MUTED)
                continue
            run, run_color = [], None
            for line in x['patch'].splitlines():
                color = C_GREEN if line.startswith('+') else C_RED if line.startswith('-') else C_BLUE if line.startswith('@@') else C_MUTED
                if color != run_color and run:
                    ml.print('\n'.join(run), text_color=run_color)
                    run = []
                run_color = color
                run.append(line)
                lines_left -= 1
                if lines_left <= 0:
                    break
            if run:
                ml.print('\n'.join(run), text_color=run_color)
            if lines_left <= 0:
                ml.print(f'\n… diff cut off at {MAX_PATCH_LINES} lines - use "Open on GitHub" for the rest', text_color=C_AMBER)
                break
        ml.Widget.yview_moveto(0)

    def render_other(self, it):
        ml, f, d, kind = self.details[K_DETAIL], self.fonts(), it['data'], it['kind']
        ml.Widget.configure(wrap='none')
        ml.update('')
        if kind == 'branch':
            ml.print(f"New branch '{d['name']}'", text_color=C_AMBER, font=f['mono_b'])
            ml.print(f'{n_of(len(d["commits"]), "commit")} not on {d["default"]}:\n', text_color=C_MUTED)
            for c in d['commits']:
                ml.print(f'  {c["short"]}  {local_str(parse_iso(c["date"]))}  ', text_color=C_MUTED, end='')
                ml.print(c['title'], text_color=C_TEXT)
        elif kind == 'tag':
            ml.print(f'New tag {d["name"]}', text_color=C_PURPLE, font=f['mono_b'])
            ml.print(f'points at commit {d["sha"][:7]}', text_color=C_MUTED)
        elif kind == 'release':
            ml.print(f'{d["name"]}   ({d["tag"]})' + ('   PRE-RELEASE' if d['prerelease'] else ''), text_color=C_PURPLE, font=f['mono_b'])
            ml.print(f'published {local_str(parse_iso(d["date"]))} by {d["author"]}\n', text_color=C_MUTED)
            ml.print(d['body'] or '(no release notes)', text_color=C_TEXT)
        else:
            ml.print(f'#{d["number"]}  {d["title"]}', text_color=KIND_COLOR[kind], font=f['mono_b'])
            ml.print(f'{"pull request" if kind == "pr" else "issue"} {d["what"]} · {d["state"]} · by {d["user"]} · {n_of(d["comments"], "comment")}', text_color=C_MUTED, end='')
            ml.print(f' · updated {local_str(parse_iso(d["date"]))}', text_color=C_MUTED)
            if d['labels']:
                ml.print('labels: ' + ', '.join(d['labels']), text_color=C_AMBER)
            ml.print('')
            ml.print((d['body'][:4000] + ('\n…' if len(d['body']) > 4000 else '')) or '(no description)', text_color=C_TEXT)
        ml.Widget.yview_moveto(0)

    def selected_url(self):
        if self.selected is None:
            return None, None
        it = self.details_items[self.selected]
        d = it['data']
        if it['kind'] in ('commit', 'merge'):
            return d['url'], d['sha']
        if it['kind'] == 'branch':
            return f'{self.snapshots[self.details_repo]["info"]["html_url"]}/tree/{d["name"]}', d['sha']
        if it['kind'] == 'tag':
            return f'{self.snapshots[self.details_repo]["info"]["html_url"]}/releases/tag/{d["name"]}', d['sha']
        return d['url'], None

    def scroll(self, key):
        list_canvas, text = self.details[K_LIST].TKColFrame.canvas, self.details[K_DETAIL].Widget
        shifted = key in PANE_KEYS
        target = text if shifted or key in (K_KEY_LEFT, K_KEY_RIGHT) or self.details.TKroot.focus_get() is text else list_canvas
        scroll_canvas(target, key)

    # ---------------------------------------------------------------- Issues window (the support queue) ----------------------------------------------------------------
    def me(self):
        """Your GitHub login (the token's account) - your own comments and closes are never news."""
        if DEMO:
            return DemoGitHub.shared().login()
        return (self.poller.gh._login or '') if self.poller is not None and self.poller.gh is not None else ''

    def chip_repo(self, row):
        """The repo a click on a widget row's issue chip opens in the Issues window - None when the chip is empty."""
        if self.snooze_until:
            return None
        if row == QUIET_ROW:
            hidden = [r for r in self.repos() if r not in self.visible_rows]
            best = max(hidden, key=lambda r: self.issue_counts(self.snapshots.get(r))[1], default=None)
            return best if best is not None and self.issue_counts(self.snapshots.get(best))[1] else None
        return row if any(self.issue_counts(self.snapshots.get(row))) else None

    def issue_sections(self, snap):
        """(new since you looked, waiting on you - longest wait first, the other open issues)"""
        new = sorted(snap.get('new_issues', []), key=lambda r: r['date'], reverse=True)
        seen = {r['number'] for r in new}
        waiting = sorted((r for r in snap.get('open_issues', []) if r['waiting'] and r['number'] not in seen), key=lambda r: r['last']['at'])
        rest = [r for r in snap.get('open_issues', []) if not r['waiting'] and r['number'] not in seen]
        return new, waiting, rest

    def issue_signature(self, snap):
        return tuple(sorted((r['number'], r['date'], r['waiting']) for r in snap.get('new_issues', []) + snap.get('open_issues', [])))

    def issue_row(self, idx, section, rec, f):
        role = ROLE_TEXT.get(rec['assoc'], '')
        parts = [f'opened by {rec["user"]}' + (f' ({role})' if role else '') + f' {ago(parse_iso(rec["created"]))}', n_of(rec['comments'], 'comment')]
        parts += [', '.join(rec['labels'])] if rec['labels'] else []
        when, when_color = f'{age_short(parse_iso(rec["date"]))} ago', C_MUTED
        if section == 'new':
            label = {'opened': 'NEW', 'commented': 'COMMENT', 'closed': 'CLOSED'}.get(rec['what'], 'NEW')
            chip_fg, chip_bg = C_BG, C_PURPLE if rec['what'] == 'closed' else C_BLUE
            if rec['what'] != 'opened':
                parts.insert(0, f'{"comment" if rec["what"] == "commented" else "closed"} by {rec["actor"]}')
            if rec['waiting'] and rec['last']:                  # news that is also waiting on you says so in amber
                when, when_color = f'waiting {age_short(parse_iso(rec["last"]["at"]))}', C_AMBER
        elif section == 'waiting':
            label, chip_fg, chip_bg = 'WAITING', C_BG, C_AMBER
            when, when_color = f'waiting {age_short(parse_iso(rec["last"]["at"]))}', C_AMBER
            if rec['comments']:
                parts.insert(0, f'last word: {rec["last"]["login"]} {ago(parse_iso(rec["last"]["at"]))}')
        else:
            label, chip_fg, chip_bg = 'OPEN', C_MUTED, C_BG3
        tp = (0, (4, 0))
        ttext, tcolor = shorten(f'#{rec["number"]}  {rec["title"]}', self.is_title_chars), C_MUTED if section == 'open' else C_TEXT
        chip = sg.Text(f' {label} ', size=(9, 1), justification='c', font=f['chip'], text_color=chip_fg, background_color=chip_bg, key=KT_IS_CHIP(idx), pad=((6, 6), (4, 0)))
        row1 = [chip, sg.Text(when, size=(12, 1), font=f['small'], text_color=when_color, pad=tp),
                sg.Text(ttext, size=(self.is_title_chars, 1), font=f['title'], text_color=tcolor, pad=tp)]
        row2 = [sg.Text('', size=(9, 1), font=f['chip'], pad=((6, 6), 0)), sg.Text('', size=(12, 1), font=f['small'], pad=0),
                sg.Text(shorten(' · '.join(parts), self.is_meta_chars), size=(self.is_meta_chars, 1), font=f['small'], text_color=C_MUTED, pad=(0, (0, 4)))]
        return sg.Column([row1, row2], key=KT_IS_ITEM(idx), pad=0, expand_x=True, background_color=C_BG)

    def open_issues(self, repo, reopen=False, number=None):
        snap = self.snapshots.get(repo)
        if not snap or not snap.get('ok'):
            msg = snap['error'] if snap else 'Still doing the first check - try again in a moment.'
            sg.popup(f'{repo}\n\n{msg}', title=repo, keep_on_top=True, background_color=C_BG2, text_color=C_TEXT)
            return
        if self.issues_win is not None and self.issues_repo == repo and not reopen:
            self.issues_win.bring_to_front()
            return
        self.close_issues(mark=not reopen)
        f, sc = self.fonts(), self.scale
        owner, name = repo.split('/')
        sw, sh = self.widget.get_screen_size()
        list_w, list_h = min(int(900 * sc), int(sw * 0.45)), min(int(600 * sc), int(sh * 0.55))
        self.is_title_chars, self.is_meta_chars = max(26, int(58 * list_w / (900 * sc))), max(40, int(80 * list_w / (900 * sc)))
        pane_chars = max(50, min(96, int(72 * (sw - list_w) / (sw * 0.5))))
        new, waiting, rest = self.issue_sections(snap)
        shown = rest[:OPEN_ISSUE_LIMIT]
        self.issue_items = [('new', r) for r in new] + [('waiting', r) for r in waiting] + [('open', r) for r in shown]
        sections = (('new', 'NEW SINCE YOU LOOKED', C_BLUE, new, 'Nothing new since you last looked.'),
                    ('waiting', 'WAITING ON YOU', C_AMBER, waiting, 'Nobody is waiting on a reply from you.'),
                    ('open', 'OPEN', C_MUTED, shown, 'No other open issues.'))
        rows, idx = [], 0
        for section, title, color, recs, empty in sections:
            count = len(rest) if section == 'open' else len(recs)
            rows.append([sg.Text(f'{title} · {count}', font=f['section'], text_color=color if recs else C_MUTED, pad=((8, 0), (10, 2)))])
            if not recs:
                rows.append([sg.Text(empty, font=f['small'], text_color=C_DIM, pad=((14, 0), (0, 6)))])
            for rec in recs:
                rows.append([self.issue_row(idx, section, rec, f)])
                idx += 1
        more = snap.get('open_issue_total', 0) - len(waiting) - len(shown) - sum(1 for r in new if r['state'] == 'open')
        if more > 0:
            rows.append([sg.Text(f'…and {more} more open on GitHub', font=f['small'], text_color=C_DIM, pad=((14, 0), (4, 8)))])
        n_wait = sum(1 for r in snap.get('open_issues', []) if r['waiting'])
        facts = f'{snap.get("open_issue_total", 0)} open · {n_wait} waiting on you · {len(new)} new'
        plain = dict(disabled=True, write_only=True, border_width=0, expand_x=True)
        sbar = dict(sbar_background_color=C_LINE, sbar_trough_color=C_BG2, sbar_arrow_color=C_MUTED)
        btn = self.btn(f)
        digest = sg.Multiline(size=(150, 2), key=K_IS_DIGEST, font=f['body'], no_scrollbar=True, background_color=C_BG, pad=((8, 8), (2, 4)), **plain)
        fresh = sg.Text('New issue activity arrived while this was open · click Refresh to reload', key=K_IS_FRESH, font=f['small'], text_color=C_AMBER, visible=False)
        head = [[sg.Text(f'{name} · Issues', font=f['h1'], text_color=C_BLUE, pad=((8, 6), (6, 0))), sg.Text(f'by {owner}', font=f['small'], text_color=C_MUTED, pad=(0, (16, 0))),
                 sg.Push(background_color=C_BG), sg.Text(facts, font=f['small'], text_color=C_MUTED, pad=((0, 8), (16, 0)))],
                [digest],
                [fresh]]
        list_col = sg.Column(rows, scrollable=True, vertical_scroll_only=True, size=(list_w, list_h), key=K_IS_LIST, background_color=C_BG, expand_y=True, pad=(0, 0),
                             sbar_background_color=C_LINE, sbar_trough_color=C_BG, sbar_arrow_color=C_MUTED)
        thread = sg.Multiline(size=(pane_chars, 34), key=K_IS_THREAD, font=f['body'], background_color=C_BG2, expand_y=True, pad=(0, 0), **plain, **sbar)
        reply = sg.Button('Reply on GitHub', key=K_IS_REPLY, font=f['small'], button_color=(C_BG, C_GREEN), border_width=0, pad=((0, 6), (6, 0)))
        right = sg.Column([[thread],
                           [reply, sg.Button('Copy link', key=K_IS_COPY, **btn), sg.Push(background_color=C_BG), sg.Text(ISSUES_HINT, font=f['status'], text_color=C_DIM)]],
                          expand_x=True, expand_y=True, pad=((8, 0), 0), background_color=C_BG)
        foot = [[sg.Button('Mark issues read', key=K_IS_READ, **btn), sg.Button('Refresh now', key=K_IS_REFRESH, **btn), sg.Button('All issues on GitHub', key=K_IS_ALL, **btn),
                 sg.Push(background_color=C_BG), sg.Button('Close', key=K_CLOSE, **btn)]]
        layout = head + [[list_col, sg.VerticalSeparator(color=C_LINE), right]] + foot
        self.issues_win = sg.Window(f'{name} · Issues', layout, finalize=True, resizable=True, margins=(6, 4), background_color=C_BG)
        self.issues_repo, self.issues_sig, self.issue_selected = repo, self.issue_signature(snap), None
        widget_map = {}
        for i in range(len(self.issue_items)):
            for w in descendants(self.issues_win[KT_IS_ITEM(i)].Widget):
                widget_map[w] = i
        bind_click(self.issues_win, widget_map)
        for seq, key in KEY_BINDS:
            self.issues_win.bind(seq, key)
        wheel_scrolls_list(self.issues_win, K_IS_LIST)
        self.write_issue_digest(snap)
        if self.issue_items:
            self.select_issue(next((i for i, (_, r) in enumerate(self.issue_items) if r['number'] == number), 0))
        else:
            self.issues_win[K_IS_THREAD].print('No open issues.', text_color=C_MUTED)

    def close_issues(self, mark=True):
        if self.issues_win is not None:
            if mark and cfg(K_MARK_ON_CLOSE) and self.issues_repo:
                self.mark_issues_read(self.issues_repo)
            self.issues_win.close()
            self.issues_win, self.issues_repo, self.issue_selected, self.issue_items = None, None, None, []

    def write_issue_digest(self, snap):
        ml, rstate = self.issues_win[K_IS_DIGEST], self.state.get(snap['repo'], {})
        read = parse_iso(rstate.get('issues_read_at') or rstate.get('last_read_at'))
        new = snap.get('new_issues', [])
        whats = Counter(r['what'] for r in new)
        news = []
        if whats['opened']:
            news.append((n_of(whats['opened'], 'new issue'), C_BLUE))
        if whats['commented']:
            who = ', '.join(dict.fromkeys(r['actor'] for r in new if r['what'] == 'commented'))
            news.append((f'new comments on {n_of(whats["commented"], "issue")} ({who})', C_BLUE))
        if whats['closed']:
            news.append((f'{whats["closed"]} closed', C_PURPLE))
        seg = [('Since you last looked at issues (', C_TEXT), (local_str(read) if read else 'the start', C_BLUE), ('):  ', C_TEXT)]
        if snap.get('issues_error'):
            seg = [(f"Couldn't read this repo's issues ({snap['issues_error']}) - the token needs Issues read access.  ", C_RED)] + seg
        for i, part in enumerate(news or [('nothing new', C_MUTED)]):
            seg += ([(' · ', C_MUTED)] if i else []) + [part]
        waiting = [r for r in snap.get('open_issues', []) if r['waiting']]
        if waiting:
            oldest = min(waiting, key=lambda r: r['last']['at'])
            seg += [('.   ', C_TEXT), (f'{n_of(len(waiting), "issue")} waiting on you', C_AMBER), (f' - the longest for {span(parse_iso(oldest["last"]["at"]))}.', C_TEXT)]
        else:
            seg += [('.   ', C_TEXT), ('Nobody is waiting on a reply from you.', C_GREEN)]
        ml.update('')
        for text, color in seg:
            ml.print(text, text_color=color, end='')

    def select_issue(self, idx):
        if self.issue_selected is not None:
            self.highlight_issue(self.issue_selected, False)
        self.issue_selected = idx
        self.highlight_issue(idx, True)
        self.issues_win[K_IS_LIST].TKColFrame.canvas.focus_set()
        self.show_thread(self.issues_win, K_IS_THREAD, self.issues_repo, self.issue_items[idx][1])

    def highlight_issue(self, idx, on):
        chip = self.issues_win[KT_IS_CHIP(idx)].Widget
        for w in descendants(self.issues_win[KT_IS_ITEM(idx)].Widget):
            if w is not chip:
                try:
                    w.configure(background=C_BG3 if on else C_BG)
                except Exception:
                    pass

    def show_thread(self, window, key, repo, rec):
        """Show an issue conversation: straight from the cache, and fetched in the background when it's new or has changed since."""
        cached = self.poller.thread_cache.get((repo, rec['number']))
        fresh = cached is not None and cached['updated'] >= rec['date']
        self.render_thread(window[key], rec, cached['data'] if cached else None, loading=not fresh)
        if not fresh and (repo, rec['number']) not in self.fetching:
            self.fetching.add((repo, rec['number']))
            threading.Thread(target=self.fetch_thread_bg, args=(repo, rec['number'], rec['date'], window), daemon=True).start()

    def fetch_thread_bg(self, repo, number, stamp, window):
        cache, result = self.poller.thread_cache, None
        try:
            data = fetch_issue_thread(DemoGitHub.shared() if DEMO else self.poller.gh, repo, number)
            cache[(repo, number)] = {'updated': max(stamp, data['updated']), 'data': data}
            result = data
        except Exception as e:
            result = str(e)
        self.fetching.discard((repo, number))
        try:
            while len(cache) > 200:                             # conversations can be long - keep the last couple of hundred
                cache.pop(next(iter(cache)), None)
        except Exception:
            pass
        try:
            window.write_event_value(K_THREAD_READY, (repo, number, result))
        except Exception:
            pass

    def thread_arrived(self, ml, rec, result):
        if isinstance(result, dict):
            self.render_thread(ml, rec, result, loading=False)
        else:
            ml.print(f'\nCould not load the conversation: {result}', text_color=C_RED)

    def render_thread(self, ml, rec, data, loading):
        """An issue conversation: title, where it stands (waiting on you / answered / closed), then every post under its author."""
        f, me = self.fonts(), self.me()
        ml.Widget.configure(wrap='word')
        ml.update('')
        state, labels, title = (data['state'], data['labels'], data['title']) if data else (rec['state'], rec['labels'], rec['title'])
        ml.print(f'#{rec["number"]}  {title}', text_color=C_PURPLE if state == 'closed' else C_BLUE, font=f['h2'])
        role = ROLE_TEXT.get(rec['assoc'], '')
        opened = f'{state} · opened by {rec["user"]}' + (f' ({role})' if role else '') + f' · {local_str(parse_iso(rec["created"]))} · {n_of(rec["comments"], "comment")}'
        ml.print(opened + (' · ' + ', '.join(labels) if labels else ''), text_color=C_MUTED, font=f['small'])
        posts = data['posts'] if data else []
        people = [p for p in posts if not p['bot']]
        last = people[-1] if people else rec['last']
        if state == 'closed':
            when = f' {ago(parse_iso(data["closed_at"]))}' if data and data['closed_at'] else ''
            who = f' by {data["closed_by"]}' if data and data['closed_by'] else ''
            ml.print(f'Closed{when}{who}' + (' - not planned' if data and data['reason'] == 'not_planned' else '') + '.', text_color=C_PURPLE, font=f['title'])
        elif last and not is_maintainer(last, me):
            ml.print(f'Waiting on you for {span(parse_iso(last["at"]))} - {last["login"]} had the last word.', text_color=C_AMBER, font=f['title'])
        elif last:
            who = 'you' if me and last['login'].lower() == me.lower() else last['login']
            ml.print(f'Answered - {who} replied {ago(parse_iso(last["at"]))}.', text_color=C_GREEN, font=f['title'])
        ml.print('─' * 70, text_color=C_LINE, font=f['small'])
        if data is None:
            ml.print('Loading the whole conversation…' if loading else '', text_color=C_AMBER, font=f['small'])
            self.print_markdown(ml, rec['body'], f)
            ml.Widget.yview_moveto(0)
            return
        shown, jump = posts[:MAX_THREAD_POSTS], '1.0'
        for i, post in enumerate(shown):
            if i == len(shown) - 1:
                jump = ml.Widget.index('end-1c')
            mine = bool(me) and post['login'].lower() == me.lower()
            color = C_DIM if post['bot'] else C_GREEN if is_maintainer(post, me) else C_BLUE
            role = 'you' if mine else ROLE_TEXT.get(post['assoc'], '')
            at = parse_iso(post['at'])
            ml.print('\n● ', text_color=color, font=f['body'], end='')
            ml.print(post['login'] + (f' ({role})' if role else ''), text_color=color, font=f['title'], end='')
            ml.print(f'   {local_str(at)} · {ago(at)}' + ('  · opened the issue' if i == 0 else ''), text_color=C_MUTED, font=f['small'])
            self.print_markdown(ml, post['body'] or '(no text)', f)
        if len(posts) > len(shown):
            ml.print(f'\n… {n_of(len(posts) - len(shown), "more comment")} on GitHub', text_color=C_AMBER, font=f['small'])
        if rec.get('what') == 'commented' and len(shown) > 1:
            ml.Widget.yview(jump)                               # news is a new comment - open the reader at it
        else:
            ml.Widget.yview_moveto(0)

    def print_markdown(self, ml, text, f):
        styles = {'text': (f['body'], C_TEXT, None), 'head': (f['title'], C_PURPLE, None), 'quote': (f['body'], C_MUTED, None), 'check': (f['small'], C_MUTED, None),
                  'code': (f['mono'], C_TEXT, C_BG3)}
        lines = md_lines(text[:MAX_POST_CHARS]) + ([('quote', '… cut short - the rest is on GitHub')] if len(text) > MAX_POST_CHARS else [])
        run, run_style = [], None
        for style, line in lines + [(None, None)]:              # the (None, None) sentinel flushes the last run
            if style != run_style and run:
                font, color, bg = styles[run_style]
                ml.print('\n'.join(run), text_color=color, background_color=bg, font=font)
                run = []
            run_style = style
            run.append(line)

    def issues_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC):
            self.close_issues()
        elif event == K_CLICK:
            self.select_issue(values[event])
        elif event == K_THREAD_READY:
            repo, number, result = values[event]
            rec = self.issue_items[self.issue_selected][1] if self.issue_selected is not None else None
            if rec is not None and repo == self.issues_repo and rec['number'] == number:
                self.thread_arrived(self.issues_win[K_IS_THREAD], rec, result)
        elif event in LIST_KEYS + PANE_KEYS:
            thread = self.issues_win[K_IS_THREAD].Widget
            pane = event in PANE_KEYS or self.issues_win.TKroot.focus_get() is thread
            if event not in (K_KEY_LEFT, K_KEY_RIGHT):
                scroll_canvas(thread if pane else self.issues_win[K_IS_LIST].TKColFrame.canvas, event)
        elif event in (K_IS_REPLY, K_IS_COPY):
            if self.issue_selected is not None:
                url = self.issue_items[self.issue_selected][1]['url']
                if event == K_IS_REPLY:
                    webbrowser.open(url)
                else:
                    sg.clipboard_set(url)
        elif event == K_IS_READ:
            self.mark_issues_read(self.issues_repo)
            self.open_issues(self.issues_repo, reopen=True)
        elif event == K_IS_REFRESH:
            self.poller.wake.set()
            self.open_issues(self.issues_repo, reopen=True)
        elif event == K_IS_ALL:
            webbrowser.open(f'https://github.com/{self.issues_repo}/issues')

    # ---------------------------------------------------------------- settings window ----------------------------------------------------------------
    def open_settings(self):
        if self.settings_win is not None:
            self.settings_win.bring_to_front()
            return
        f = self.fonts()
        lbl = dict(font=f['body'], text_color=C_TEXT)
        pick_help = sg.Text('lists an account\'s repos so\nyou can tick the ones to watch', font=f['status'], text_color=C_MUTED, pad=(0, 0))
        layout = [[sg.Text('Repositories to watch  -  owner/name per line, or just an account name to watch every repo it owns', **lbl)],
                  [sg.Multiline(size=(52, 4), key=K_REPOS, setting=DEFAULTS[K_REPOS], font=f['mono'], no_scrollbar=True),
                   sg.Column([[sg.Button('Choose repos…', key=K_PICK, font=f['small'])], [pick_help]], vertical_alignment='top', background_color=C_BG, pad=((8, 0), 0))],
                  [sg.Text('GitHub token', **lbl), sg.Input(key=K_TOKEN, setting=DEFAULTS[K_TOKEN], password_char='•', size=(42, 1), font=f['mono']),
                   sg.Button('Test', key=K_TEST, font=f['small'])],
                  [sg.Text('Blank = use GITHUB_TOKEN / GH_TOKEN, or your gh CLI login.  Needs read access to the repo (private repos especially).', font=f['status'],
                           text_color=C_MUTED)],
                  [sg.Text('', key=K_TEST_RESULT, size=(80, 2), font=f['small'], text_color=C_AMBER)],
                  [sg.Text('Check every', **lbl), sg.Combo(INTERVALS, key=K_INTERVAL, setting=DEFAULTS[K_INTERVAL], readonly=True, font=f['body'], size=(8, 1)),
                   sg.Text('   Activity history', **lbl), sg.Combo(HISTORIES, key=K_HISTORY_DAYS, setting=DEFAULTS[K_HISTORY_DAYS], readonly=True, font=f['body'], size=(9, 1)),
                   sg.Text('   Widget text size', **lbl), sg.Combo(list(range(9, 21)), key=K_FONT_SIZE, setting=DEFAULTS[K_FONT_SIZE], readonly=True, font=f['body'], size=(4, 1))],
                  [sg.Text('Issues view shows', **lbl), sg.Input(key=K_ISSUES_REPO, setting=DEFAULTS[K_ISSUES_REPO], size=(32, 1), font=f['mono']),
                   sg.Text('(owner/name · blank = the repo with the most open issues)', font=f['status'], text_color=C_MUTED),
                   sg.Text('   rows', **lbl), sg.Combo(ISSUE_ROW_CHOICES, key=K_ISSUE_ROWS, setting=DEFAULTS[K_ISSUE_ROWS], readonly=True, font=f['body'], size=(4, 1))],
                  [sg.Text('Widget opacity', **lbl),
                   sg.Slider((40, 100), key=K_OPACITY, setting=DEFAULTS[K_OPACITY], orientation='h', size=(40, 18), font=f['small'], enable_events=True)],
                  [sg.Checkbox('Mark things read when I close the "What\'s new" or Issues window', key=K_MARK_ON_CLOSE, setting=DEFAULTS[K_MARK_ON_CLOSE], font=f['body'])],
                  [sg.Checkbox('Widget shows only repos with news or problems; the rest collapse into one "quiet repos" line', key=K_COLLAPSE, setting=DEFAULTS[K_COLLAPSE],
                               font=f['body'])],
                  [sg.Checkbox('Keep the widget on top of other windows', key=K_KEEP_ON_TOP, setting=DEFAULTS[K_KEEP_ON_TOP], font=f['body'])],
                  [sg.Checkbox('Quiet hours - dim the widget from', key=K_QUIET_ON, setting=DEFAULTS[K_QUIET_ON], font=f['body']),
                   sg.Combo(HOURS, key=K_QUIET_FROM, setting=DEFAULTS[K_QUIET_FROM], readonly=True, font=f['body'], size=(7, 1)), sg.Text('to', **lbl),
                   sg.Combo(HOURS, key=K_QUIET_TO, setting=DEFAULTS[K_QUIET_TO], readonly=True, font=f['body'], size=(7, 1))],
                  [sg.Text(f'Settings & log folder: {os.path.dirname(sg.user_settings_filename())}', font=f['status'], text_color=C_DIM)],
                  [sg.Button('Save', key=K_SAVE, font=f['body'], button_color=(C_BG, C_GREEN)), sg.Button('Cancel', key=K_CANCEL, font=f['body'])]]
        self.settings_win = sg.Window(f'{APP_NAME} {VERSION} · Settings', layout, finalize=True, keep_on_top=True, margins=(12, 10), background_color=C_BG)
        self.settings_win.bind('<Escape>', K_CANCEL)

    def test_token_bg(self, token, repos, window):
        gh, lines = GitHub(token), []
        try:
            lines.append(f'token OK - logged in as {gh.get("/user").get("login")}' if token else 'no token found - only public repos will work')
        except GitHubError as e:
            lines.append(f'token problem: {e}')
        for repo in repos:
            try:
                if '/' in repo:
                    info = gh.get(f'/repos/{repo}')
                    lines.append(f'{repo}: OK ({"private" if info.get("private") else "public"}, default branch {info.get("default_branch")})')
                else:
                    found = list_owner_repos(gh, repo)
                    lines.append(f'{repo}: account OK - {n_of(len([r for r in found if not r["archived"]]), "repo")} to watch ({len([r for r in found if r["private"]])} private)')
            except GitHubError as e:
                lines.append(f'{repo}: {e}')
        try:
            window.write_event_value(K_TEST_RESULT, '\n'.join(lines))
        except Exception:
            pass

    def save_settings(self, values):
        old_entries, old_font, old_collapse = self.entries(), cfg(K_FONT_SIZE), cfg(K_COLLAPSE)
        self.settings_win.settings_save(values)
        self.settings_win.close()
        self.settings_win = None
        if self.pick_win is not None:
            self.pick_win.close()
            self.pick_win = None
        if self.entries() != old_entries or cfg(K_FONT_SIZE) != old_font or cfg(K_COLLAPSE) != old_collapse or self.view == VIEW_ISSUES:
            self.close_details()
            self.owner_errors = {}
            self.rebuild_widget()
        self.set_keep_on_top(bool(cfg(K_KEEP_ON_TOP)))
        self.current_alpha = None
        self.apply_alpha()
        self.reconfigure_poller()

    # ---------------------------------------------------------------- event loop ----------------------------------------------------------------
    def run(self):
        while True:
            window, event, values = sg.read_all_windows(timeout=2000)
            if event == sg.TIMEOUT_EVENT:
                if self.snooze_until and datetime.now() >= self.snooze_until:
                    self.snooze_until = None
                    self.sync_widget()
                self.apply_alpha()
                self.refresh_status()
                if (datetime.now() - self.last_meta_refresh).total_seconds() > 30:          # keep "pushed 28 min ago" honest
                    self.last_meta_refresh = datetime.now()
                    self.sync_widget()
                self.keep_on_screen()
                continue
            if window is None or (window is self.widget and event in ('Exit', sg.WINDOW_CLOSED)):
                break
            if window not in (self.widget, self.details, self.settings_win, self.pick_win, self.all_win, self.issues_win):
                if event == sg.WIN_CLOSED:
                    window.close()                      # a non-blocking popup's X (Version): read_all_windows reports it, the app has to close it
                continue
            if window is self.widget:
                if self.widget_event(event, values) is False:
                    break
            elif window is self.details:
                self.details_event(event, values)
            elif window is self.settings_win:
                self.settings_event(event, values)
            elif window is self.pick_win:
                self.pick_event(event, values)
            elif window is self.all_win:
                self.all_event(event, values)
            elif window is self.issues_win:
                self.issues_event(event, values)
        self.poller.quit.set()
        self.poller.wake.set()
        self.close_details()
        self.close_issues()
        for w in (self.settings_win, self.pick_win, self.all_win):
            if w is not None:
                w.close()
        self.widget.close()

    def widget_event(self, event, values):
        item = values.get(K_MENU) if event == K_MENU else event
        if event == K_POLL_BUSY:
            self.busy.add(values[event])
            self.refresh_row(values[event])
            self.refresh_row(QUIET_ROW)
        elif event == K_REPOS_RESOLVED:
            for owner, found in values[event].items():
                self.expanded[owner.lower()] = found['repos']
                if found['error']:
                    self.owner_errors[owner] = found['error']
                else:
                    self.owner_errors.pop(owner, None)
            for repo in self.repos():
                self.state.setdefault(repo, {})
            self.sync_widget()
        elif event == K_POLL_RESULT:
            snap = values[event]
            repo = snap['repo']
            self.busy.discard(repo)
            if snap.get('state_update'):
                self.state[repo] = snap['state_update']
                self.save_state()
                self.poller.state = self.state
            if repo in self.repos():
                self.snapshots[repo] = snap
                self.sync_widget()
                if self.details is not None and self.details_repo == repo and snap.get('ok') and self.signature(snap) != self.details_sig:
                    self.details[K_FRESH].update(visible=True)
                if self.issues_win is not None and self.issues_repo == repo and snap.get('ok') and self.issue_signature(snap) != self.issues_sig:
                    self.issues_win[K_IS_FRESH].update(visible=True)
            if AUTO_OPEN and not self.auto_opened and snap.get('ok') and 'jaynabonne' in repo:
                self.auto_opened = True
                self.open_details(repo)
        elif event == K_CLICK:
            target = values[event]
            if target == (K_VIEW_TOGGLE, None):
                self.switch_view()
                return True
            if target == (K_ITITLE, None):                      # step the issues view through the repos that have issues
                cands = self.issue_view_repos()
                if cands:
                    sg.user_settings_set_entry(K_ISSUES_REPO, cands[(cands.index(self.issue_view_repo()) + 1) % len(cands)] if self.issue_view_repo() in cands else cands[0])
                    self.refresh_issue_rows()
                    self.keep_on_screen()
                return True
            if isinstance(target, tuple) and target[0] == K_IROW:
                if target[1] < len(self.issue_rows_shown):
                    self.open_issues(self.issue_view_repo(), number=self.issue_rows_shown[target[1]]['number'])
                return True
            if isinstance(target, tuple):                       # the issue chip: the Issues window when the chip shows something, else a row click
                repo = self.chip_repo(target[1])
                if repo is not None:
                    self.open_issues(repo)
                    return True
                target = target[1]
            if target == QUIET_ROW:
                self.open_all_repos()
            else:
                self.open_details(target)
        elif item == M_CHECK:
            self.poller.wake.set()
        elif item == M_VIEW:
            self.switch_view()
        elif item == M_READ:
            for repo in self.repos():
                self.mark_read(repo, sync=False)
            self.sync_widget()
        elif item == M_PAUSE:
            self.poller.paused = not self.poller.paused
            self.poller.wake.set()
            self.refresh_status()
        elif item in (M_SNOOZE_1, M_SNOOZE_4, M_SNOOZE_TOMORROW, M_SNOOZE_OFF):
            tomorrow = datetime.combine(date.today() + timedelta(days=1), datetime.min.time()).replace(hour=7)
            until = {M_SNOOZE_1: datetime.now() + timedelta(hours=1), M_SNOOZE_4: datetime.now() + timedelta(hours=4), M_SNOOZE_TOMORROW: tomorrow, M_SNOOZE_OFF: None}
            self.snooze_until = until[item]
            self.sync_widget()
        elif item in (M_SNAP_TL, M_SNAP_TR, M_SNAP_BL, M_SNAP_BR):
            self.snap_to({M_SNAP_TL: 'TL', M_SNAP_TR: 'TR', M_SNAP_BL: 'BL', M_SNAP_BR: 'BR'}[item])
        elif item == M_SETTINGS:
            self.open_settings()
        elif item == M_TOP:
            self.set_keep_on_top(not cfg(K_KEEP_ON_TOP))
        elif item == M_LOG:
            path = os.path.join(os.path.dirname(sg.user_settings_filename()), LOG_FILE_NAME)
            if not os.path.exists(path):
                log('log created')
            os.startfile(path) if hasattr(os, 'startfile') else webbrowser.open('file://' + path)
        elif item == M_ABOUT:
            sg.popup(f'{APP_NAME} {VERSION}\n\n{__doc__.strip()}', title='About', keep_on_top=True, font=(MONO_FONT, 10), background_color=C_BG2, text_color=C_TEXT, line_width=140)
        elif item == 'Version':
            sg.popup_scrolled(f'{APP_NAME} {VERSION}', __file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif item == 'Edit Me':
            sg.execute_editor(__file__)
        elif item in ('Exit', K_CLOSE_X):                       # the ≡ ButtonMenu's Exit or the ✕; the right-click 'Exit' is caught with WINDOW_CLOSED in run()
            return False
        return True

    def details_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC):
            self.close_details()
        elif event == K_CLICK:
            self.select_item(values[event])
        elif event == K_DETAIL_READY:
            sha, det = values[event]
            self.fetching.discard(sha)
            for idx, it in enumerate(self.details_items):
                if it['kind'] in ('commit', 'merge') and it['data']['sha'] == sha and isinstance(det, dict):
                    self.details[KT_ADD(idx)].update(f'+{det["add"]}')
                    self.details[KT_DEL(idx)].update(f'−{det["del"]}')
                    self.details[KT_ITEM_META(idx)].update(shorten(commit_meta(it['data'], det), self.meta_chars))
            if self.selected is not None and self.details_items[self.selected]['kind'] in ('commit', 'merge') and self.details_items[self.selected]['data']['sha'] == sha:
                if isinstance(det, dict):
                    self.render_commit(self.details_items[self.selected]['data'], det)
                else:
                    self.details[K_DETAIL].print(f'\nCould not fetch the diff: {det}', text_color=C_RED)
        elif event in LIST_KEYS + PANE_KEYS:
            self.scroll(event)
        elif event == K_OPEN:
            url, _ = self.selected_url()
            if url:
                webbrowser.open(url)
        elif event == K_COPY_SHA:
            _, sha = self.selected_url()
            if sha:
                sg.clipboard_set(sha)
        elif event == K_COPY_LINK:
            url, _ = self.selected_url()
            if url:
                sg.clipboard_set(url)
        elif event == K_MARK_READ:
            self.mark_read(self.details_repo)
            self.open_details(self.details_repo, reopen=True)
        elif event == K_REFRESH:
            self.poller.wake.set()
            self.open_details(self.details_repo, reopen=True)
        elif event == K_OPEN_REPO:
            webbrowser.open(self.snapshots[self.details_repo]['info']['html_url'])
        elif event == K_COPY_DIGEST:
            sg.clipboard_set(self.digest_plain)
        elif event == K_ISSUES_BTN:
            self.open_issues(self.details_repo)
        elif event == K_THREAD_READY:
            repo, number, result = values[event]
            it = self.details_items[self.selected] if self.selected is not None else None
            if it is not None and it['kind'] == 'issue' and repo == self.details_repo and it['data']['number'] == number:
                self.thread_arrived(self.details[K_DETAIL], it['data'], result)

    def settings_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CANCEL):
            self.settings_win.close()
            self.settings_win = None
        elif event == K_OPACITY:
            self.widget.set_alpha(int(values[K_OPACITY]) / 100)
            self.current_alpha = int(values[K_OPACITY]) / 100
        elif event == K_TEST:
            self.settings_win[K_TEST_RESULT].update('testing…')
            token = values[K_TOKEN].strip() or resolve_token()
            threading.Thread(target=self.test_token_bg, args=(token, parse_entries(values[K_REPOS]), self.settings_win), daemon=True).start()
        elif event == K_TEST_RESULT:
            self.settings_win[K_TEST_RESULT].update(values[event])
        elif event == K_PICK:
            token = values[K_TOKEN].strip() or resolve_token()
            default = next((e for e in parse_entries(values[K_REPOS]) if '/' not in e), '') or ('PySimpleGUI' if DEMO else GitHub(token).login())
            owner = sg.popup_get_text('Account (user or organization) whose repos to list:', title='Choose repos', default_text=default, keep_on_top=True,
                                      background_color=C_BG2, text_color=C_TEXT)
            if owner and owner.strip():
                owner = clean_entry(owner).split('/')[0]
                self.settings_win[K_TEST_RESULT].update(f'listing repos for {owner}…')
                threading.Thread(target=self.pick_fetch_bg, args=(token, owner, self.settings_win), daemon=True).start()
        elif event == K_PICK_READY:
            owner, result = values[event]
            if isinstance(result, str):
                self.settings_win[K_TEST_RESULT].update(f'{owner}: {result}')
            else:
                self.settings_win[K_TEST_RESULT].update('')
                self.open_picker(owner, result, values[K_REPOS])
        elif event == K_SAVE:
            self.save_settings(values)


def main():
    sg.theme_add_new('RepoWatch', {'BACKGROUND': C_BG, 'TEXT': C_TEXT, 'INPUT': C_BG2, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_LINE, 'BUTTON': (C_TEXT, C_BG3),
                                   'PROGRESS': (C_BLUE, C_BG2), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
    sg.theme('RepoWatch')
    sg.set_options(dpi_awareness=True, font=(UI_FONT, 11), tooltip_font=(UI_FONT, 10))
    try:
        App().run()
    except Exception:
        log(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
