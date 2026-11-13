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
    ≡ or right-click  ->  Check now · Mark all read · Pause · Keep on top · Theme · Brightness · Accent · Size · Snooze · Snap to corner · Settings · Edit Me · Version ·
                          New versions · Restart · Exit
    Restart starts a fresh copy, back at the same place, size, view, theme and accent.  New versions: when a newer copy of this file is saved over it
    (Dropbox brings it to every PC), by default the widget restarts by itself once the mouse has been off it 10 s and none of its windows are open -
    or Ask me first (a small pop-up), or Only say so in this menu ("Restart - x.y.z is ready").  The Version window shows the choice.
    Start with Windows (right-click, Windows only, off to start): a shortcut, GitHub Repo Watch.lnk, in your Startup folder and its icon, GitHub Repo Watch.ico,
    beside the settings file; unticking removes the shortcut.  The Version window names it.
    Accent: the color of the commit charts (sparkline, orb rings, beads, calendar, clock) - GitHub green unless you pick another; remembered.
    Drag it anywhere; its position is remembered.  The faint ✕ in the top-right corner closes it (Tiny has none), and so do Esc and Alt-F4.
    The other windows are moved by their title strip.

    ⇄ (next to ≡) switches to the ISSUES VIEW and back - the choice is remembered:
    PySimpleGUI issues                3 new · 4 waiting
    ● #6918 Table: right-click menu…      COMMENT  40m     dot: green = open · purple = closed
      tablefan · 2 comments · Bug                          badge: NEW / COMMENT / CLOSED = news · WAITING = someone is waiting on you
    Click an issue -> the Issues window, open at that issue.  Click the title to step through the watched repos that have issues;
    Settings picks the repo and how many rows show.

SIZES  (right-click > Size, or Ctrl + mouse wheel over the widget - remembered between runs)
    Tiny     one strip, an orb per repo: its ring is the last 14 days of commits (an arc a day, today just left of the top), its middle what is new -
             green = new commits / branches / tags / PRs, blue = issues with news, red ! = a problem, else the repo's initial.  A blue dot = issue
             news as well, an amber dot = someone is waiting on your reply.  Issues view: a pip per issue (blue news · purple closed · amber waiting ·
             green quiet).  Hover an orb or a pip to see what it says.  No ✕ - right-click > Exit, Esc or Alt-F4 close it.
    Small    a line per repo: the news as symbols, 14 days of beads on a string (bigger and brighter = busier), how long since the last push
    Medium   the classic look shown above
    Large    a card per repo: language, stars / forks / watchers / branches, description, a 5-week calendar (a square a day), a 24-hour clock of when
             the commits land (the amber hand is now), the news a line per kind with the lines the new commits added and removed, the newest commit.
             Issues view: a bar of news / waiting / quiet issues, then a card per issue with its labels and how long it has waited.
             Hover a day, an hour or a news line for its numbers; click a news line to open it.

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

    python github_repo_watch.pyw --demo        made-up data, no token, no network (handy for trying the UI) - with its own settings file,
                                               github_repo_watch_demo.json, so trying things never touches your real settings

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
    1.5.0 06-Nov-2026   The standard widget themes: right-click > Theme (32, as color chips) and Brightness...; every window themed with no OS title
                        bar (moved by its title strip, round corners on Windows 11) and an icon; flat themed menus; Esc closes the widget; --demo has its
                        own settings and never touches the network
    1.6.0 06-Nov-2026   Size: Tiny / Small / Medium / Large (right-click > Size or Ctrl + mouse wheel), each its own way of seeing the news - orbs with
                        activity rings, beads, the classic rows, cards with a calendar and a 24-hour clock - with hover tips on the charts
    1.6.1 11-Nov-2026   Accent (right-click > Accent) colors the commit charts, GitHub green by default; no ✕ in Tiny; a size change keeps the top-left
                        corner and stays on its monitor, Ctrl + wheel keeps the Brightness panel open; Ctrl + Button-4 / 5 only off Windows
    1.6.2 11-Nov-2026   Start with Windows (right-click, Windows only): a shortcut in your Startup folder, off to start - the STARTUP block (recipe section 7); sub-menu arrows
    1.6.3 11-Nov-2026   Restart and New versions (right-click, just above Exit) - the UPDATE block: a newer copy of this file restarts it by itself by default

Needs PySimpleGUI and Pillow - everything else is stdlib.  Settings + unread state live in github_repo_watch.json in PySimpleGUI's
user-settings folder; problems are logged to github_repo_watch.log in the same folder.
"""
import base64
import ctypes
import io
import json
import math
import os
import random
import re
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.font
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from tkinter import colorchooser

import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont

# --- UPDATE: Restart, and a newer version of this file (program standards, 11-Nov-2026, block 2) - paste unchanged ---
# Right-click > Restart starts a fresh copy of this file (same arguments) and this one ends.  While it runs, the program watches its own file:
# a NEWER VERSION saved over it counts once it has sat UPDATE_SETTLE seconds unchanged and compiles (a half-saved or broken file never counts).
# Then right-click > New versions decides (remembered, -NEW VERSIONS-; the program sets Update.default for its kind):
#   'auto'  By itself - hidden in the tray at once, showing once the mouse has been off the window UPDATE_QUIET seconds and nothing of it is open
#   'ask'   Ask me first - a small pop-up, Restart now / Later (Later by itself after 30 s); hidden in the tray it goes by itself
#   'menu'  Only say so here - never by itself; the menu reads "Restart - x.y.z is ready"
# Not the internet: the file itself, which Dropbox brings to every PC.
# Wiring (Tools\update_block.md):  main() start: Update.default = 'auto' / 'ask' / 'menu';   menu, just above Exit: *update_menu(tick)
#   each event: if update_event(event): end the loop if Update.restart, else remake the menu
#   timer (every 2-5 s): if update_tick(window, hidden, busy, colors): remake the menu;  if Update.restart: end the loop
#   the very end of main(), after the window, tray icon and sockets are closed:  if Update.restart: restart_self(['--tray'] if hidden else [])
UPDATE_SETTLE = 60
UPDATE_QUIET = 10
UPDATE_CHOICES = (('auto', "By itself, while I'm not using it"), ('ask', 'Ask me first'), ('menu', 'Only say so in this menu'))


class Update:
    default = 'ask'                   # the program's kind: 'auto' widgets + tray apps, 'ask' other programs that run all day, 'menu' open-and-close
    seen = None                       # (mtime of this file when last looked at, when it changed - None while it is the file this copy started from)
    ready = ''                        # a newer VERSION saved over this file (settled, compiles)
    asked = ''                        # the version the pop-up already asked about - not asked again
    away = None                       # when the mouse left the window (for 'auto')
    restart = False                   # set -> the main loop ends, then restart_self()


def update_mode():
    mode = sg.user_settings_get_entry('-NEW VERSIONS-', Update.default)
    return mode if mode in dict(UPDATE_CHOICES) else Update.default


def update_check():
    """ Returns a newer VERSION the first time one is ready, else ''.  Cheap: one stat() a call, the file is read only after it changed and settled """
    try:
        mtime = os.path.getmtime(os.path.abspath(__file__))
    except OSError:
        return ''
    if Update.seen is None:
        Update.seen = (mtime, None)
    if mtime != Update.seen[0]:
        Update.seen = (mtime, time.time())
        return ''
    if Update.seen[1] is None or time.time() - Update.seen[1] < UPDATE_SETTLE:
        return ''
    Update.seen = (mtime, None)                                           # looked at: wait for the next change
    try:
        with open(os.path.abspath(__file__), encoding='utf-8') as f:
            text = f.read()
        compile(text, __file__, 'exec')
        found = re.search(r"^VERSION = '([0-9.]+)'", text, re.M)
    except (OSError, SyntaxError, ValueError):
        return ''
    newer = found and tuple(int(x) for x in found.group(1).split('.')) > tuple(int(x) for x in VERSION.split('.'))
    if newer and found.group(1) != Update.ready:
        Update.ready = found.group(1)
        return Update.ready
    return ''


def restart_label():
    """ The right-click item: 'Restart', or 'Restart - 1.2.3 is ready' once a newer version waits """
    return f'Restart  -  {Update.ready} is ready' if Update.ready else 'Restart'


def update_menu(tick=None, indent='    '):
    """ The right-click items to put just above Exit: the New versions sub-menu (its choice ticked) and Restart.  tick(on) = the program's own
        check-mark prefix, so the items line up with its other ones """
    tick = tick or (lambda on: '✓ ' if on else indent)
    mode = update_mode()
    return [f'{indent}New versions', [f'{tick(k == mode)}{text}::-NEW VERSIONS {k}-' for k, text in UPDATE_CHOICES], f'{indent}{restart_label()}::Restart']


def update_event(event):
    """ True when the event was one of this block's: Restart (sets Update.restart) or a New versions choice (saved - remake the menu) """
    key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event
    if key == 'Restart':
        Update.restart = True
        return True
    for k, _ in UPDATE_CHOICES:
        if key == f'-NEW VERSIONS {k}-':
            sg.user_settings_set_entry('-NEW VERSIONS-', k)
            return True
    return False


def mouse_away(window):
    """ True once the mouse has been off the window UPDATE_QUIET seconds in a row """
    try:
        root = window.TKroot
        px, py = root.winfo_pointerxy()
        x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
        inside = x <= px < x + w and y <= py < y + h
    except Exception:
        inside = False
    if inside:
        Update.away = None
        return False
    Update.away = Update.away or time.time()
    return time.time() - Update.away >= UPDATE_QUIET


def update_tick(window, hidden=False, busy=False, colors=('#1e2430', '#e6eaf2', '#2a62a8')):
    """ Call on the timer.  hidden = the window is hidden in the tray;  busy = a dialog, panel or edit of the program is open (nothing happens
        then);  colors = (background, text, button) of the pop-up - the program's own theme.  Sets Update.restart when it is time.
        Returns True when the menu should be remade (a version became ready, or the pop-up was answered Later) """
    new = update_check()
    if not Update.ready or Update.restart:
        return bool(new)
    mode = update_mode()
    if mode == 'menu':
        return bool(new)
    if hidden:
        Update.restart = True
        return False
    quiet = mouse_away(window) and not busy
    if mode == 'auto':
        Update.restart = quiet
        return bool(new)
    if Update.asked != Update.ready and not busy:
        Update.asked = Update.ready                                       # once per version
        update_offer(window, Update.ready, colors)
        return not Update.restart
    return bool(new)


def update_offer(window, new, colors=('#1e2430', '#e6eaf2', '#2a62a8')):
    """ Ask once per version: Restart now / Later (Later by itself after 30 s, so a program never waits long).  Sets Update.restart """
    Update.asked = new
    bg, fg, button = colors
    try:
        x, y = window.current_location()
        spot = (x + 20, y + 20)
    except Exception:
        spot = (None, None)
    name = globals().get('APP_NAME') or os.path.splitext(os.path.basename(__file__))[0]
    answer = sg.popup(f'{name} {new} is here  (you run {VERSION})', 'Restart now to use it?', '(Right-click > New versions: by itself, ask, or only say so)',
                      title='New version', custom_text=('Restart now', 'Later'), keep_on_top=True, auto_close=True, auto_close_duration=30, location=spot,
                      background_color=bg, text_color=fg, button_color=('#ffffff', button), font=('Segoe UI', 11), icon=globals().get('ICON'))
    Update.restart = answer == 'Restart now'


def restart_self(extra=()):
    """ Start this file again with the same arguments (pythonw on Windows - no console).  Call it LAST: after the window, the tray icon and any
        socket this program listens on are closed, so a one-copy-at-a-time program's new copy finds the way clear """
    exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    exe = exe if sys.platform.startswith('win') and os.path.isfile(exe) else sys.executable
    args = [a for a in sys.argv[1:] if a != '--tray'] + list(extra)
    subprocess.Popen([exe, os.path.abspath(__file__)] + args, cwd=os.path.dirname(os.path.abspath(__file__)))
# --- end UPDATE ---


APP_NAME = 'GitHub Repo Watch'
VERSION = '1.6.3'
SETTINGS_FILE = 'github_repo_watch.json'
DEMO_SETTINGS_FILE = 'github_repo_watch_demo.json'               # --demo's own settings, so trying things never touches the real ones
LOG_FILE_NAME = 'github_repo_watch.log'
API = 'https://api.github.com'
DEMO = '--demo' in sys.argv
AUTO_OPEN = '--open' in sys.argv
ICON = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAANvUlEQVR42t2bbYwdV3nHf885Z+a+7L17795de5ckhuA6IjjgBExbhzTdCCkJxYSISquGVm1BFagtakUJFaWlslK1Kmqq8qVqq0CbpkEpilUQJDQuKUpcXpJUOBQHxXlxojh+i9fr9a7v+8yc8/TDXC/rEDvseuPdcPbbnZmd8/+f5+385znCq4zJyUm3e/fubPFvW7d+LOpGJ6swz9oYNZJ6s71/167+K8zdA3q2J+Xs/3SHgdt08LB5+7tvvsYqN6roNoENCHXVcz1/gYaggqBoE5XDaPi+Kg926ulDPyZkh4Hbwk9NwNTUlN25c6cHuPLqD3wEkU9Y57ZY6wgh4H1K8J61MxRjHNY5jLEE78my9FnQf2xPJ/+wf/+u/mJM5yTgtMlv3nbTptjIF2xUuE5V6XeboduaD/1eW7I0EQ1e1hADiDHqoljjQllLQzVTLA8bYy1p0v8hIfvYDx/9xv++kjvLK4G/4he3Xxe56D9sFDV67WbWPHnMdFpzJoScQBHDmkJ/2slVUVWMMRSHhkN1ZDyUK3Xns7QfQvrhvY9848svJ0EW2b1l507/tm3vn3TW/aexttw8OZ3NzRx2Pssw1oLI6TexNofkiFQJwWOModZ4gx8enbAoeJ98aO8j3/jyYneQxQFvy7U3XSre/MA6V5ubOeLnZg5bMRYRAV2roM/GRT7n4DOGG+NhZN0GVJUg4d17v/P1x9ixw3DbbcHk+AdmlOndUVyoDVbeGmNzhpYLXs6dZ15bn8jnbFzEqdljZn72qFrnDF7v2XL99UOnZ2gnJyfdgbvu8lu2bf+tuFD+w16nmZ146QUnwrJnLyZ/Tr1CALGCWFnNAEmv0zJRXM5KQ8Ojvqf9Y1/6wsOTk5NOAJmamjJPH+o9EUWFy48feS605k9Y49zSV17y8ODbHhMLdjhCBLJTGaEXsGULTiDoBXcH9RnF8nBYf8llEnw265Luz+3Z89/zDtCnX+xe7QqFt/a6zdBpzVlj7dLBG9C+Ik5Yd/M4tavrxOMFRCCZSWnumWfmgWl822OLFr2QJKgixtLrNk23Pe8rtdHRvup24B4HoIb3Weu025oPwXuz5NWXHLyrO95060aq7xgmJAFNFRSi0Zjqlir1a0c4cPvz9A72sKULTIIIGpROa04rtXUqItuBe8xg/ttCCNLvtUUWUt3SkrA4WQCfzqb4lkd9npd9x5POppQuLXPpn2zC1RwhDRc2QKoiIqT9rvE+FRF559TUlDVbt26NELPBZyk+S2QQ9pcU8Hzb07h+bAG8WMFWLJpp7vtDFnFCdiqj9OYS6z84QeiGPL3+tClNZAWqBMFnqWRpgsDEE8+fWm/apj4sUAvBE7wXWeKyqCoSCbVtdUKS7zdMyXDqsTme/dQ+nvnkk8w+OIMpGhDw3UB1aw037PIsca7pGrsQwNSnID/+bblukOPMUJGhgqFhjLV6PoWXesXVHPFEAU3zIOhbniN3HqJ/pEd2MuPInYdIXkowsUHTQDQaEa2LzuoGIgYIJK1ZQtIjKteIhhqELCFpzaLBI8asQFgQdStRhIsIp2OHiBB8IKQBcYI4QTNFM12ozhbuP0vO9kkPY2M23vBxJt75fkpjGxFj6M6+yPEnvsmBh/6VtHMSV6yg4fx2pe68wQ98O5lJiEYjfNvjao6JWy7iyJ2H0ExZPzVB4eICvuMxBUNyPCE5kSDuzIArkoMvDK/nHR+7g7HN78KnENL8erHeYOzyq7jo53+Vx+/4KK0jT503CW4FzAjf8zS/P0d1SxXf9oReoHH9GJUtVTRTChcVCf0ACqZkae09RTaX4apuUSoUVAPGOq766L8wtvkqenNpbi3WgUDWzUg7SnXDJrb+3pd45G9uJOs28+vLLNfN+WcXxZYNM7uO09nfWQhuoRuIRmPiiQKhF1Cv2CFLejxh+ivHMAWDLpq0GEvaPcWGaz/MuiuuojefYmyEKzuCT/H9Lq7sMC4iaaYMb7iYjTd+gqzXHMQMVoeA3A0MvuU5cPtz9A71cNXcsDRVNMmLIVuyZPMZL9z+HMnRPiY2gEGMQ4wZBDbL+Ds/gE9zYmwRjv3ft/juX/4y3/mLazj47Xuxhdzqsp6yfst7iSujaMhWkQBAg2JLlt6hHs/+8T5O/s8spmjQwZ8pGjr72zzzqX20f9TCVhxgCGmXpDVD1m0BgcrEZZTHLiWkgnGOtN1j372fpX3sOfqnptm387N0j09jYkfIoFh/A8XGJYQsWbYVOFZoaFBc2ZHMJsw/OsfIdQ3oDsw7FrrPdegf7FEYL5G22/i0x/CGtzF+5Y3UN/4C5bE3E1fX4YpV1CtiBA2BkPYxLkJshGYpwaenk0muTIk5L61ixQg4TYI4wZTMmcWk5iSYUkT/1AmG1l3Gpu1/xMS7biauFFAPGiDrB3zSwRZKBO8pVMtc9oFPs2/nn6M+ZdP7bmVo/GKynsdEht7sNL25IxgXoxpWn4AzBbqfrJrS5gwb3vMhrvj1z1Gs10k7kDTzFGaskLbnOPHUbi655oNkHcj6sOHaX2P08vegPmFo/GJ8AqqBqGg5tO9h+vPTxJXGslOhWVHgeQFH6J1Z4Ykx+E6PjTfcytaP/xOuWCdpZouqPlAV4kqDFx/+IvMvPE1ctYQsJet6iiPrKK/LVz5kKVEpontinud3fR4bl5e9+itLgMmBSyxUrqjkld8AYNbtUd/yFi7/jc/gOxC8R6xDg8c4Ia5YxApZv0nSmuUHd3yE1tEDFOsRNraoh5AqNrIUahFJ8wSP3/E7tI8/j42LayAGLNYDPrWRyhVVfMcPpDGF1GEvnuN48gc05v+MiA0EzYiGHJ1jR3nxO3cz+/R36c4exPfapN1TfO9zN7Hxxo8zvuVGCvWLETF0Z1/ixFMPs/+Bv6dz/DmiUu28S2HZvO2GRmSKT6nqupcO7NPgM1nWbkth447LqF41TDqo4LCDrWwWQCzBNIn8pYydvJ24WOPwY/fx5L9/ht7Jw5ioiLERYixiHSFLyHot4sooxcZFiBh6c0fpzx/HxkVsXFoueB3f8BZxcSGVtH/V+ZfCRsiaGetuHj9DDzAlMxBFQi6AdD1G6yTmaXqNBznxrTEev+O3cYUK8fB6CB5F848bIXeRuNJAfUr76LP5u1xEXBlBB/esxHArUQqfTQ84cuchQhqYuOUiGteP4Tsp1tWZb3+NZ77yI2w0hHGFfK//CgqOqgcx2Li08K6VAr4yQXCpekAkECwazSPlNqJRDvJVfEs1DCL9ymuI5rXQA9TrufUA5xDnzit9rQ0CXqYHSCSENCzoAaZoARb0gND3SCSkJxOSmf5P6AGrMdaQHvB6tIAV1ANetwSclx6wBj44r44eMGRX3fRXfC9wWg9IZ1PmH51DokGA0zP1AFdxawb8iu8GX00PkFjWFPiV3w6fUw9Ym+OC6AHIICAOpK6fTQLOogecBl+4qIirukXb5J8lAk7rATXHpr96C2PvW59//TV5iRx6gcrbq1z2t2+lcEkB3107JJiV8vmF/oArh8laWR4HBDB5NvAdT+lNpdXrD3itCPiJ/oCTKWIEUzZoqrkOUDa55LXc/oC1Xgq/Nv0BrwcCXqP+gNffXmBJesCi+9dCEAzey7I7IperB8ylr9gfwIXtrhZVFZeNRq3CKZrG2DExRtXrkvqEXld6wKBfMG/8phNE5s3+Xbv6qnrIOodzseYrIsvUA9p5cMsU3/ZEjZh4PO8M0Wz19QBFsS5S52JUdTr2bzw2iAG6xxircbGsqro0hzhDD3ie3sEuUSPKAXpFU8UUDG4kIpvPOLBaeoAIqkpUKAXrIlUNe/fsuSM1g2sPBO+lOFQzxi79c/OCHnCwx/4/fZpj9x6l/1J/wbzT4wkz90/z7Kf30Vo1PUARhNJQPTdx5YHTmqC0h7Pd5bn+gdLQ8BuL5eHQac0Zs8S+Gw2KKVl8x3P4iwdx9x4lGo3BQHoiJZtLMQWDLa8GeEG9Jy4OablSs2m/1xLpfx3ATE5O2v27dvVVwueNsVIdGQ/GLLPpIChiZSEO9A936b/YRZOAqzokWiU9YODS1ZFx76JYVMM/733kwemFdnl27JDNTz7p3KHu41FcuuLkzCE/N33IGhed30kRWQMagQghS6k2xsPo+Jsky5KZKNLNe3ZvnYXbMIDuAJ7cuTMB85uZT9NaY0KGG+MhZOmPe3WXK4zoaoHP1zZkKUPDo1ofuySgiKh8ZM/u+2empp4UIFiA3bt369TUlH3ov756ZPwNm54xxk6VhmqISOh1W0aDzxsZZG2JGWdtrEZQ9agq1ZH1YWR8gzobuTTtf3Lvo/f92yscmuKMY3Nbrt5+izHx3dZZ127OZc3Zl2yv2xQ93eaKrEEy8tZ81Tzax8UhrY6M+0qt4VAl88mte793/9+d/djcy0i4cttN12DNF6OocLnPUrrted9pzZH0u+KzRDSENbbwBusijQolLQ/VtVSpORfFpGlyJKj//Se+d9/XXvXgJC87Ort582QlrtduVeR3o7gwAeB9ik9TvM/W1tFZ63AuxroIgCxJ5hR/l/f89Y8eu+/YT310dmEMztUBvP2Xto9Ydb+iqu8F2SrChEJ1bR2ZlLZqOA7yQ9BvOmvv3/Ptrx59+VnoJZwez69PTk7axWYzNTVlX5hmXdrtNyBZdeAJEMcxmvn5dt3PLD5CPwB+zsaC/wd2mEnfRf6MtQAAAABJRU5ErkJggg=='          # embedded window icon (a green commit graph with a blue branch) - the title strips show it, launchers find it
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

# ---------------------------------------------------------------- colors ----------------------------------------------------------------
# Every window is drawn with these.  They are never written out here: apply_theme() works them all out from theme_colors() (the chosen theme at its
# Brightness) whenever the theme or the Brightness changes - C_BG card, C_BG2 panes (lifted a touch), C_BG3 chips / buttons / the selected row,
# C_LINE lines, C_TEXT, C_MUTED (= the theme's dim), C_DIM fainter still, C_STRIP title strips.  The meaning colors (commit / branch / tag / issue / PR,
# open / closed / waiting, + / - lines) keep their meaning on every theme: on a light card apply_theme() draws them a shade deeper so they still read.
MEANING_COLORS = {'green': '#3fb950', 'red': '#f85149', 'amber': '#d29922', 'blue': '#58a6ff', 'purple': '#bc8cff', 'pink': '#f778ba'}
C_BG = C_BG2 = C_BG3 = C_LINE = C_TEXT = C_MUTED = C_DIM = C_STRIP = ''                         # set by apply_theme()
C_ACCENT = ''                                                   # the Accent as drawn on this card (accent_on) - the commit charts; set by apply_theme()
C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK = MEANING_COLORS.values()
KIND_COLOR, STATUS_COLOR = {}, {}                                                                 # filled by apply_theme()
C_MENU_SEL = '#2a62a8'                                          # menu highlight, white text on it
C_CLOSE = '#c0392b'                                             # a close x under the mouse
C_SWATCH_EDGE = '#7c8594'                                       # outline of the color chips in the Theme menu
UI_FONT = 'Segoe UI' if sg.running_windows() else 'DejaVu Sans'
MONO_FONT = 'Consolas' if sg.running_windows() else 'DejaVu Sans Mono'
FONT_MENU = (UI_FONT, 10)
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # Pillow fonts (Brightness panel): Windows first, then Linux
TRANSPARENT = '#010203'                                         # Windows color key: the Brightness panel's rounded corners are see-through
RADIUS = 18                                                     # the Brightness panel's corner radius in design pixels - the windows get Windows 11's own round corners
DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND, DWMWA_BORDER_COLOR = 33, 2, 34                    # Windows 11: round a window's corners, color its outline

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
# menu items: make_menu() puts the labels in front ('    Check now::-M CHECK-'); the event is the key after '::'.  The standard 'Edit Me' / 'Version' /
# 'Exit' trio from sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT keeps its plain keys at the bottom
K_M_CHECK = '-M CHECK-'
K_M_READ = '-M READ-'
K_M_VIEW = '-M VIEW-'
K_M_PAUSE = '-M PAUSE-'
K_M_TOP = '-M TOP-'
K_M_SETTINGS = '-M SETTINGS-'
K_M_LOG = '-M LOG-'
K_M_ABOUT = '-M ABOUT-'
SNOOZES = {'-M SNOOZE 1-': 'Hide badges for 1 hour', '-M SNOOZE 4-': 'Hide badges for 4 hours', '-M SNOOZE TOMORROW-': 'Hide badges until tomorrow',
           '-M SNOOZE OFF-': 'Show badges again'}                # key: label
KT_M_SNAP = lambda corner: f'-M SNAP {corner}-'
SNAP_CORNERS = {'TL': 'Top left', 'TR': 'Top right', 'BL': 'Bottom left', 'BR': 'Bottom right'}
SNAP_KEYS = {KT_M_SNAP(corner): corner for corner in SNAP_CORNERS}
K_THEME = '-THEME-'                                             # settings entry for the theme, and the start of the Theme menu's keys
KT_THEME = lambda name: f'{K_THEME}{name}'
# every window but the widget
K_STRIP = '-STRIP-'                                             # the title strip - drag it to move the window
K_STRIP_CLOSE = '-STRIP CLOSE-'                                 # its x
K_ASK_INPUT = '-ASK INPUT-'                                     # the small question card (Choose repos: which account)
K_ASK_OK = '-ASK OK-'
K_SIZE = '-SIZE-'                                               # settings entry: the widget's size, one of SIZES
SIZES = ('Tiny', 'Small', 'Medium', 'Large')
SIZE_FONT_STEP = {'Tiny': -2, 'Small': -1, 'Medium': 0, 'Large': 0}       # each size's text size against the Widget text size setting
KT_M_SIZE = lambda size: f'-M SIZE {size}-'                     # the Size menu's choices
SIZE_KEYS = {KT_M_SIZE(size): size for size in SIZES}
K_SIZE_STEP = '-SIZE STEP-'                                     # Ctrl + mouse wheel over the widget - value +1 = a size bigger, -1 = smaller
K_PIC = '-PIC-';            KT_PIC = lambda row, part: (K_PIC, row, part)   # a picture in a Tiny / Small / Large row - part: orb, counts, beads, cal, clock...
K_AGE = '-AGE-';            KT_AGE = lambda repo: (K_AGE, repo)             # Small: how long since the last push
K_DESC = '-DESC-';          KT_DESC = lambda repo: (K_DESC, repo)           # Large: the repo's description
K_LATEST = '-LATEST-';      KT_LATEST = lambda repo: (K_LATEST, repo)       # Large: the newest commit
K_HEAD = '-HEAD-'                                               # Large: the summary across the top
K_IPIPS = '-IPIPS-'                                             # Tiny issues view: the pips
K_IHEALTH = '-IHEALTH-'                                         # Large issues view: the bar of news / waiting / open
K_ORB = '-ORB-'                                                 # click target (K_ORB, repo): a Tiny orb - What's new, or the Issues window for issue news
K_OPEN_ISSUES = '-OPEN ISSUES-'                                 # click target (K_OPEN_ISSUES, repo): the Issues window

HOURS = ['12 AM'] + [f'{h} AM' for h in range(1, 12)] + ['12 PM'] + [f'{h} PM' for h in range(1, 12)]
INTERVALS = ['1 min', '2 min', '5 min', '10 min', '15 min', '30 min', '60 min']
HISTORIES = ['14 days', '30 days', '60 days', '90 days']
DEFAULTS = {K_REPOS: 'jaynabonne/impulsing_ada', K_TOKEN: '', K_INTERVAL: '5 min', K_HISTORY_DAYS: '30 days', K_OPACITY: 94, K_FONT_SIZE: 11,
            K_MARK_ON_CLOSE: True, K_QUIET_ON: False, K_QUIET_FROM: '10 PM', K_QUIET_TO: '7 AM', K_COLLAPSE: True, K_VIEW: VIEW_REPOS, K_ISSUE_ROWS: 6,
            K_ISSUES_REPO: '', K_KEEP_ON_TOP: True, K_SIZE: 'Medium'}


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
    """Fire K_CLICK with the mapped target when a mouse press/release lands on the same spot (so dragging the widget doesn't count as a click).
    A target can be a function of the click event - a picture with parts works out which part was clicked."""
    pressed = {}

    def on_press(e):
        pressed['at'] = (e.x_root, e.y_root)

    def on_release(e):
        x0, y0 = pressed.get('at', (e.x_root, e.y_root))
        target = widget_map.get(e.widget)
        if target is not None and abs(e.x_root - x0) < 6 and abs(e.y_root - y0) < 6:
            window.write_event_value(K_CLICK, target(e) if callable(target) else target)     # a function works out the target from where the click landed

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


def work_area(window, x, y):
    """The usable part (no taskbar) of the monitor that point x, y is on: left, top, right, bottom  (as in the SIZE STEPS block of the card widgets)"""
    if sg.running_windows():
        try:
            from ctypes import wintypes

            class MONITORINFO(ctypes.Structure):
                _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT), ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]
            user32 = ctypes.WinDLL('user32')
            user32.MonitorFromPoint.argtypes, user32.MonitorFromPoint.restype = (wintypes.POINT, wintypes.DWORD), wintypes.HANDLE
            user32.GetMonitorInfoW.argtypes = (wintypes.HANDLE, ctypes.POINTER(MONITORINFO))
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(info)
            if user32.GetMonitorInfoW(user32.MonitorFromPoint(wintypes.POINT(int(x), int(y)), 2), ctypes.byref(info)):      # 2 = the nearest monitor
                r = info.rcWork
                return r.left, r.top, r.right, r.bottom
        except Exception:
            pass
    root = window.TKroot
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def keep_on_monitor(window):
    """After a size change: the top-left corner stays where it is, unless the card now runs past its monitor's right or bottom edge - then it slides back"""
    window.refresh()
    (x, y), (w, h) = window.current_location(), window.size
    left, top, right, bottom = work_area(window, x, y)
    nx, ny = max(left, min(x, right - w)), max(top, min(y, bottom - h))
    if (nx, ny) != (x, y):
        window.move(nx, ny)


# ================================================================ themes ================================================================
ACCENTS = {'GitHub': '#3fb950', 'Blue': '#1e9bff', 'Green': '#2ecc71', 'Teal': '#2ad4c8', 'Purple': '#c48cff', 'Orange': '#ff7f50', 'Gold': '#e8a33d'}  # GitHub = before 1.6.1
ACCENT_DEFAULT = ACCENTS['GitHub']                              # GitHub's green - what the commit charts were always drawn in


# --- ACCENT: the same block in every card widget (master copy in modern_widget_recipe.md) - right-click > Accent, remembered (-ACCENT-) ---
# The accent colors the dot by the title and the widget's main bar / ring / line; colors that carry meaning (load, status, warnings) stay as they are.
# The program supplies ACCENTS (name -> '#rrggbb', its default first; None = 'Follows load', only where the color can follow a load), ACCENT_DEFAULT,
# G.accent, mix() and is_light(), and imports colorchooser (from tkinter import colorchooser).
ACCENT_ANY = 'Any...'                                             # the last Accent item: the color dialog
K_ACCENT = '-ACCENT-'                                             # settings-file entry ('#rrggbb', None = follows the load), and the start of the Accent menu's keys
KT_ACCENT = lambda name: f'{K_ACCENT}{name}'


def load_accent():
    """The saved accent - ACCENT_DEFAULT the first time, or if what was saved is not a color"""
    c = sg.user_settings_get_entry(K_ACCENT, ACCENT_DEFAULT)
    if c is None:
        return None if None in ACCENTS.values() else ACCENT_DEFAULT
    ok = isinstance(c, str) and len(c) == 7 and c[0] == '#' and all(ch in '0123456789abcdefABCDEF' for ch in c[1:])
    return c if ok else ACCENT_DEFAULT


def accent_on(card, color=None):
    """The accent as drawn on a card of color card (color = what it is right now when it follows the load): a preset - or the load color - a shade
       darker on a light card, like the other status colors; a color picked in the Any... dialog exactly as picked"""
    color = color or G.accent
    return mix(color, '#000000', 0.18) if is_light(card) and G.accent in ACCENTS.values() else color


def accent_menu(tick):
    """The Accent sub-menu for make_menu(): its label and its items - the presets, then Any..., a tick on the one in use"""
    current = next((n for n, c in ACCENTS.items() if c == G.accent), ACCENT_ANY)
    return ['    Accent', [f'{tick(n == current)}{n}::{KT_ACCENT(n)}' for n in list(ACCENTS) + [ACCENT_ANY]]]


def choose_accent(window, menu_key, now):
    """Right-click > Accent > an item: G.accent set and saved.  Any... opens the color dialog on now (the color shown at the moment).  False if cancelled"""
    name = menu_key[len(K_ACCENT):]
    if name == ACCENT_ANY:
        picked = colorchooser.askcolor(color=now, parent=window.TKroot, title='Accent color')[1]
        if not picked:
            return False
        G.accent = picked
    else:
        G.accent = ACCENTS.get(name, ACCENT_DEFAULT)
    sg.user_settings_set_entry(K_ACCENT, G.accent)
    return True
# --- end ACCENT ---


class G:
    """State the shared WIDGET THEMES / BRIGHTNESS / ACCENT blocks and the menus use"""
    theme = 'Toybox'                                            # the chosen theme (settings entry K_THEME)
    bright = 0                                                  # its Brightness level (K_BRIGHT)
    accent = ACCENT_DEFAULT                                     # the Accent (K_ACCENT) - main() loads it; C_ACCENT is it as drawn
    tuned = {}                                                  # (theme, level) -> its five colors at that level
    swatches = {}                                               # (theme, level) -> Theme menu chip - tk keeps an image only while someone holds it
    fonts = {}                                                  # (bold, px) -> Pillow font
    scale = 1.0                                                 # display scale, 2.0 on a 200% screen - the Brightness panel and the x are drawn at it
    window = None                                               # the widget window
    app = None                                                  # the App - redraw() recolors its widget
    zoom = 1.0                                                  # the Widget text size against the usual 11 - the Tiny / Small / Large pictures follow it
    pz = 1.0                                                    # scale * zoom: what those pictures are drawn at


def mix(c1, c2, f):
    """Blend two hex colors, f=0 -> c1, f=1 -> c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(channels(c1), channels(c2)))


def is_light(color):
    """True for a light color - a light card gets deeper meaning colors"""
    r, g, b = channels(color)
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


def font(bold, px):
    """A Segoe UI (Windows) / DejaVu (Linux) Pillow font of px pixels, cached"""
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


def palette():
    """Every color apply_theme() sets, in a fixed order - redraw() swaps each for its new value"""
    return (C_BG, C_BG2, C_BG3, C_LINE, C_TEXT, C_MUTED, C_DIM, C_STRIP, C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK, C_ACCENT)


def apply_theme():
    """Work out every color from the chosen theme at its Brightness (theme_colors), and make it the PySimpleGUI theme too, so buttons, text boxes,
       combos, sliders and check boxes follow it.  Windows built after this use the new colors"""
    global C_BG, C_BG2, C_BG3, C_LINE, C_TEXT, C_MUTED, C_DIM, C_STRIP, C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK, C_ACCENT
    t = theme_colors()
    light = is_light(t['card'])
    C_BG, C_BG2, C_BG3, C_LINE, C_TEXT, C_MUTED = t['card'], mix(t['card'], t['text'], 0.04), t['track'], t['border'], t['text'], t['dim']
    C_DIM, C_STRIP = mix(t['dim'], t['card'], 0.4), mix(t['card'], t['border'], 0.4 if light else 0.3)
    C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK = (mix(c, '#000000', 0.3) if light else c for c in MEANING_COLORS.values())
    C_ACCENT = accent_on(t['card'])
    KIND_COLOR.update({'commit': C_GREEN, 'merge': C_GREEN, 'branch': C_AMBER, 'tag': C_PURPLE, 'release': C_PURPLE, 'issue': C_BLUE, 'pr': C_PINK})
    STATUS_COLOR.update({'added': C_GREEN, 'removed': C_RED, 'modified': C_AMBER, 'renamed': C_BLUE, 'copied': C_BLUE, 'changed': C_AMBER})
    sg.theme_add_new('RepoWatch', {'BACKGROUND': C_BG, 'TEXT': C_TEXT, 'INPUT': '#ffffff' if light else C_BG3, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_LINE,
                                   'BUTTON': (C_TEXT, C_BG3), 'PROGRESS': (C_BLUE, C_BG2), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
    sg.theme('RepoWatch')


def sbar(trough=None):
    """Scrollbars in the theme's colors, flat - for every window's and list's sbar_ arguments"""
    return dict(sbar_trough_color=trough or C_BG2, sbar_background_color=C_LINE, sbar_arrow_color=C_MUTED, sbar_frame_color=trough or C_BG2, sbar_relief=sg.RELIEF_FLAT)


def recolor(window, swap):
    """Swap colors in place in a built window: every tk widget's colors and every canvas drawing's, old -> new (swap = {old: new})"""
    for w in descendants(window.TKroot):
        if w.winfo_class() == 'Menu':
            continue
        for opt in ('background', 'foreground', 'activebackground', 'activeforeground', 'highlightbackground', 'selectcolor'):
            try:
                value = str(w.cget(opt)).lower()
            except tk.TclError:
                continue
            if value in swap:
                w.configure(**{opt: swap[value]})
        if w.winfo_class() == 'Canvas':
            for item in w.find_all():
                for opt in ('fill', 'outline'):
                    try:
                        value = str(w.itemcget(item, opt)).lower()
                    except tk.TclError:
                        continue
                    if value in swap:
                        w.itemconfigure(item, **{opt: swap[value]})


def round_corners(window):
    """Windows 11 rounds the window's corners and draws its 1-px outline in the theme's border color.  Windows 10, Linux and Mac keep square corners"""
    if not sg.running_windows():
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(window.TKroot.winfo_id())
        r, g, b = channels(C_LINE)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 4)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR, ctypes.byref(ctypes.c_uint(r | g << 8 | b << 16)), 4)     # 0x00BBGGRR
    except Exception:
        pass


def title_strip(title):
    """The strip across the top of every window but the widget: icon, title, version, x (red under the mouse).  Drag it to move the window"""
    row = [sg.Image(data=ICON, subsample=2, background_color=C_STRIP, pad=((10, 6), 5)),
           sg.Text(title, font=(UI_FONT, 12, 'bold'), text_color=C_TEXT, background_color=C_STRIP, pad=(0, 5)),
           sg.Text(f'v{VERSION}', font=(UI_FONT, 9), text_color=C_MUTED, background_color=C_STRIP, pad=((6, 0), (8, 4))),
           sg.Push(background_color=C_STRIP),
           sg.Text('  ✕  ', key=K_STRIP_CLOSE, font=(UI_FONT, 12), text_color=C_MUTED, background_color=C_STRIP, enable_events=True, pad=0, tooltip='Close (Escape)')]
    return [sg.Column([row], key=K_STRIP, background_color=C_STRIP, expand_x=True, pad=0)]


def framed(title, layout, pad):
    """A window's layout under its title strip - pad = the margin the window used to have around it"""
    return [title_strip(title), [sg.Column(layout, pad=pad, background_color=C_BG, expand_x=True, expand_y=True)]]


def drag_by_strip(window, strip, skip=None):
    """Move a window by dragging its title strip (any of it but `skip`, the close x) - the rest of the window stays put, as in Pip Refresh's Packages window"""
    start = {}

    def press(e):
        start['p'] = (e.x_root, e.y_root, window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty())

    def motion(e):
        p = start.get('p')
        if p:
            window.TKroot.geometry(f'+{round(p[2] + e.x_root - p[0])}+{round(p[3] + e.y_root - p[1])}')

    def release(e):
        start.pop('p', None)

    def bind(w):
        if w is skip:
            return
        w.bind('<ButtonPress-1>', press, add='+')
        w.bind('<B1-Motion>', motion, add='+')
        w.bind('<ButtonRelease-1>', release, add='+')
        for child in w.winfo_children():
            bind(child)

    bind(strip)


def dress(window, escape_key):
    """What every window but the widget gets once it is built: moved by its title strip, its x red under the mouse, Escape, round corners on Windows 11"""
    close, strip = window[K_STRIP_CLOSE].Widget, C_STRIP
    close.bind('<Enter>', lambda e: close.configure(bg=C_CLOSE, fg='#ffffff'))
    close.bind('<Leave>', lambda e: close.configure(bg=strip, fg=C_MUTED))
    drag_by_strip(window, window[K_STRIP].Widget, skip=close)
    window.bind('<Escape>', escape_key)
    round_corners(window)


def ask_text(title, message, default):
    """A small themed question card with a text box (the Choose repos account) - returns the text, or None for Cancel, Escape, the x or Alt-F4"""
    layout = framed(title, [[sg.Text(message, font=(UI_FONT, 11), pad=(4, (4, 6)))],
                            [sg.Input(default, key=K_ASK_INPUT, size=(40, 1), font=(UI_FONT, 12), pad=(4, 4))],
                            [sg.Push(background_color=C_BG), sg.Button('OK', key=K_ASK_OK, size=(8, 1), button_color=(C_BG, C_GREEN), border_width=0, pad=(4, (8, 4))),
                             sg.Button('Cancel', key=K_CANCEL, size=(8, 1), pad=(4, (8, 4)))]], (10, 8))
    card = sg.Window(title, layout, no_titlebar=True, keep_on_top=True, modal=True, finalize=True, margins=(0, 0), background_color=C_BG)
    dress(card, K_CANCEL)
    card.bind('<Return>', K_ASK_OK)
    card[K_ASK_INPUT].set_focus()
    card[K_ASK_INPUT].Widget.select_range(0, 'end')
    event, values = card.read()
    card.close()
    return values[K_ASK_INPUT] if event == K_ASK_OK and values else None


def tk_menu(master, items, window):
    """A tk menu from a PySimpleGUI-style menu list ('label::key', '---', 'label' followed by its sub-list).  A choice sends its key as the window's event"""
    menu, i = tk.Menu(master, tearoff=0), 0
    while i < len(items):
        item = items[i]
        if item == '---':
            menu.add_separator()
        elif i + 1 < len(items) and isinstance(items[i + 1], list):
            menu.add_cascade(label=item, menu=tk_menu(menu, items[i + 1], window))
            i += 1
        else:
            label, _, key = item.partition('::')
            menu.add_command(label=label, command=lambda k=key or label: window.write_event_value(k, None))
        i += 1
    return menu


def menu_colors():
    """Right-click menu background and text: the card's own colors (background lifted a touch), so the menu matches the theme"""
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


def menu_arrows(menu, dark):
    """ Windows draws a sub-menu's arrow in Windows' own menu-text color (black, white only on the lit row) whatever the menu's colors, so on a dark
        menu it can't be seen (Mike, 10-Nov).  This puts a › in the menu's own text color at the right end of each sub-menu's label instead.  Windows
        and dark menus only - a light menu shows Windows' arrow, and Linux / Mac draw theirs in the menu's colors.  Safe to call again """
    if not (dark and sg.running_windows()) or menu.index('end') is None:
        return
    f = tk.font.Font(root=menu, font=menu.cget('font'))
    labels = {}
    for i in range(menu.index('end') + 1):
        if menu.type(i) in ('command', 'cascade', 'checkbutton', 'radiobutton'):
            label = menu.entrycget(i, 'label')
            labels[i] = label.rstrip(' \u2009›') if menu.type(i) == 'cascade' and label.endswith('›') else label
    cascades = [i for i in labels if menu.type(i) == 'cascade']
    if not cascades:
        return
    end = max(f.measure(text) for text in labels.values()) + f.measure('      ›')       # the arrows line up a little past the longest label
    for i in cascades:
        label = labels[i] + '  '
        while f.measure(label + ' ›') <= end:
            label += ' '
        while f.measure(label + '\u2009›') <= end:                                       # thin spaces for the last few pixels
            label += '\u2009'
        menu.entryconfigure(i, label=label + '›')


def style_menus(window):
    """tk draws menus Windows-gray and PySimpleGUI colors only the top level: recolor every menu of the window - the right-click menu, the ≡ menu and
       their sub-menus - flat and compact in the theme's colors, with a chip beside each theme name (the lights in a column of their own)"""
    bg, fg = menu_colors()
    for menu in descendants(window.TKroot):
        if menu.winfo_class() != 'Menu':
            continue
        menu.configure(bg=bg, fg=fg, activebackground=C_MENU_SEL, activeforeground='#ffffff', bd=0, activeborderwidth=1, relief='flat', font=FONT_MENU)
        first_light = True
        for i in range(menu.index('end') + 1 if menu.index('end') is not None else 0):
            name = menu.entrycget(i, 'label').lstrip('✓ ') if menu.type(i) == 'command' else None
            if name in THEMES:
                menu.entryconfigure(i, image=theme_swatch(name), compound='left')
                if first_light and is_light(THEMES[name]['card']):
                    menu.entryconfigure(i, columnbreak=1)                     # the light themes get a column of their own
                    first_light = False
        menu_arrows(menu, not is_light(bg))                                   # sub-menu arrows you can see on a dark menu


def close_x_images():
    """The widget's close x: faint, and a red disc with a white x under the mouse.  Drawn 4x and shrunk, so the edges are smooth"""
    z, size, images = G.scale * 4, 18, []
    for hover in (False, True):
        im = Image.new('RGBA', (round(size * z), round(size * z)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c, r = size / 2 * z, 3.5 * z
        if hover:
            d.ellipse((c - 8 * z, c - 8 * z, c + 8 * z, c + 8 * z), fill=C_CLOSE)
        color = '#ffffff' if hover else C_DIM
        d.line((c - r, c - r, c + r, c + r), fill=color, width=round(1.5 * z))
        d.line((c - r, c + r, c + r, c - r), fill=color, width=round(1.5 * z))
        buf = io.BytesIO()
        im.resize((round(size * G.scale), round(size * G.scale)), Image.LANCZOS).save(buf, 'PNG')
        images.append(tk.PhotoImage(master=G.window.TKroot, data=base64.b64encode(buf.getvalue())))
    return images


def set_close_x(label):
    """The x's pictures in the current theme"""
    label.images = close_x_images()
    label.configure(image=label.images[0], bg=C_BG)


def add_close_x(window, event_key, where='ne'):
    """The close x overlaid on the window's right edge - faint, a red disc under the pointer, closes the widget when clicked.
       where: 'ne' the top-right corner, 'e' the middle of the right end, 'se' the bottom-right corner (Small, beside ≡).  Tiny has none"""
    label = tk.Label(window.TKroot, bd=0, cursor='hand2')
    set_close_x(label)
    rely, y = {'ne': (0.0, round(3 * G.scale)), 'e': (0.5, 0), 'se': (1.0, -round(3 * G.scale))}[where]
    label.place(relx=1.0, rely=rely, x=-round(5 * G.scale), y=y, anchor=where)
    label.bind('<Enter>', lambda e: label.configure(image=label.images[1]))
    label.bind('<Leave>', lambda e: label.configure(image=label.images[0]))
    label.bind('<ButtonRelease-1>', lambda e: window.write_event_value(event_key, None))
    return label


def redraw(window):
    """The Brightness panel moved its knob: the widget in the new colors at once, in place (the panel holds on to it) - each color it was drawn with
       is swapped for the same color at the new level.  The other windows follow when the panel closes"""
    old = palette()
    apply_theme()
    recolor(window, {a: b for a, b in zip(old, palette()) if a != b})
    if G.app.close_x is not None:                               # Tiny has no x
        set_close_x(G.app.close_x)
    G.app.repaint()                                             # Tiny / Small / Large: their pictures drawn again in the new colors
    round_corners(window)


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


# ================================================================ widget sizes: the pictures ================================================================
# Tiny, Small and Large draw their symbols and charts with Pillow (Medium is the classic look: text and a Graph).  Every picture is drawn in the theme's
# colors, at the screen's scale times the Widget text size (G.pz), so a bigger text size makes the pictures bigger too.  HoverTip says what is under the
# pointer on a chart: a day, an hour, an issue.
ORB = 28                                                        # Tiny: a repo's orb (design pixels, square)
BEAD_PITCH, BEAD_H = 6.0, 14                                    # Small: the 14 days of beads
CAL_CELL, CAL_GAP, CAL_WEEKS, CAL_TOP, CAL_EDGE = 9, 2, 5, 11, 1.5    # Large: the calendar - a day's square, the gap, weeks shown, weekday letters, margin
CLOCK, CLOCK_R0, CLOCK_R1 = 74, 6, 25                           # Large: the 24-hour clock - its size, the wedges' inner and outer radius
NEWS_W, NEWS_PITCH = 244, 16                                    # Large: the news list
PIP_W, PIP_H, PIP_GAP, PIP_MAX = 7, 16, 3, 18                   # Tiny issues view: one pip per issue
ISSUE_W = 400                                                   # Large issues view: the health bar and an issue's second line
DIFF_BLOCKS = 5                                                 # Large: the squares after +adds -dels, like GitHub's diffstat
WEEKDAYS = 'MTWTFSS'


def px(pt):
    """A font's point size in design pixels"""
    return pt * 4 / 3


def text_w(s, size, bold=False):
    """How wide text is in design pixels"""
    return font(bold, max(6, round(size * G.pz))).getlength(s) / G.pz


def fit(s, size, bold, width):
    """The text, cut with … so it is no wider than width design pixels"""
    if text_w(s, size, bold) <= width:
        return s
    while s and text_w(s + '…', size, bold) > width:
        s = s[:-1]
    return s.rstrip() + '…'


class Pic:
    """A picture for the widget: shapes drawn 4x and shrunk so their edges are smooth, then the text drawn on at full size so it stays sharp.
       Sizes are design pixels; text is placed by the middle of its capital letters"""
    def __init__(self, w, h, bg):
        self.w, self.h, self.bg, self.s, self.texts = w, h, bg, G.pz, []
        self.k = self.s * 4
        self.im = Image.new('RGB', (max(1, round(w * self.k)), max(1, round(h * self.k))), bg)
        self.d = ImageDraw.Draw(self.im)

    def width(self, width):
        return max(1, round(width * self.k))

    def disc(self, cx, cy, r, fill=None, outline=None, width=1.0):
        k = self.k
        self.d.ellipse(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), fill=fill, outline=outline, width=self.width(width) if outline else 0)

    def ring(self, cx, cy, r, color, width):
        """A circle line centered on radius r"""
        self.disc(cx, cy, r + width / 2, outline=color, width=width)

    def arc(self, cx, cy, r, a0, a1, color, width):
        """Part of a circle line centered on radius r, from angle a0 to a1 (degrees, clockwise from 3 o'clock)"""
        k, big = self.k, r + width / 2
        self.d.arc(((cx - big) * k, (cy - big) * k, (cx + big) * k, (cy + big) * k), a0, a1, fill=color, width=self.width(width))

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1.0, r=0):
        k, r = self.k, max(0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
        self.d.rounded_rectangle((x0 * k, y0 * k, x1 * k, y1 * k), radius=r * k, fill=fill, outline=outline, width=self.width(width) if outline else 0)

    def line(self, points, color, width):
        """A line through the points, with round ends and joints"""
        self.d.line([v * self.k for p in points for v in p], fill=color, width=self.width(width), joint='curve')
        for x, y in (points[0], points[-1]):
            self.disc(x, y, width / 2, fill=color)

    def poly(self, points, fill):
        self.d.polygon([v * self.k for p in points for v in p], fill=fill)

    def text(self, x, y, s, color, size, bold=False, anchor='l'):
        """Text whose capital letters are centered on y; anchor = l, m or r for where x is"""
        self.texts.append((x, y, s, color, size, bold, anchor))

    def png(self):
        """The finished picture, base64 PNG - what sg.Image(data=) and its update(data=) take"""
        im = self.im.resize((max(1, round(self.w * self.s)), max(1, round(self.h * self.s))), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        for x, y, s, color, size, bold, anchor in self.texts:
            f = font(bold, max(6, round(size * self.s)))
            d.text((x * self.s, y * self.s + f.getbbox('H', anchor='ls')[1] / -2), s, fill=color, font=f, anchor=anchor + 's')
        buf = io.BytesIO()
        im.save(buf, 'PNG')
        return base64.b64encode(buf.getvalue())


def blank(w, h, bg):
    """An empty picture of the right size - the layout's placeholder until the first refresh paints it"""
    return Pic(w, h, bg).png()


def icon(p, kind, cx, cy, r, color):
    """A small GitHub-style symbol centered on (cx, cy), r = half its size"""
    w, bg = max(0.9, r * 0.24), p.bg
    if kind == 'commit':                                        # a ring on a line
        p.line([(cx - r, cy), (cx + r, cy)], color, w)
        p.disc(cx, cy, r * 0.48, fill=bg, outline=color, width=w)
    elif kind in ('issue', 'closed', 'waiting', 'check'):       # a ring with a dot / a tick / clock hands
        if kind != 'check':
            p.ring(cx, cy, r * 0.84 - w / 2, color, w)
        if kind == 'issue':
            p.disc(cx, cy, r * 0.24, fill=color)
        elif kind == 'waiting':
            p.line([(cx, cy - r * 0.46), (cx, cy), (cx + r * 0.34, cy + r * 0.2)], color, w)
        else:
            f = 1.25 if kind == 'check' else 1
            p.line([(cx - r * 0.38 * f, cy + r * 0.02 * f), (cx - r * 0.1 * f, cy + r * 0.3 * f), (cx + r * 0.4 * f, cy - r * 0.3 * f)], color, w * f)
    elif kind == 'branch':                                      # a trunk and a branch leaving it
        ax, ty, by, bx, bty = cx - r * 0.42, cy - r * 0.62, cy + r * 0.62, cx + r * 0.46, cy - r * 0.32
        p.line([(ax, ty), (ax, by)], color, w)
        p.line([(bx, bty), (bx, cy + r * 0.02), (ax, cy + r * 0.44)], color, w)
        for x, y in ((ax, ty), (ax, by), (bx, bty)):
            p.disc(x, y, r * 0.25, fill=bg, outline=color, width=w * 0.9)
    elif kind == 'tag':
        pts = [(cx - r * 0.85, cy - r * 0.5), (cx + r * 0.3, cy - r * 0.5), (cx + r * 0.9, cy), (cx + r * 0.3, cy + r * 0.5), (cx - r * 0.85, cy + r * 0.5)]
        p.line(pts + [pts[0]], color, w)
        p.disc(cx - r * 0.42, cy, r * 0.14, fill=color)
    elif kind == 'release':                                     # a four-pointed sparkle
        a, b = r * 0.95, r * 0.26
        p.poly([(cx, cy - a), (cx + b, cy - b), (cx + a, cy), (cx + b, cy + b), (cx, cy + a), (cx - b, cy + b), (cx - a, cy), (cx - b, cy - b)], color)
    elif kind == 'pr':                                          # two commits and the arrow back
        lx, rx, ty, by = cx - r * 0.45, cx + r * 0.45, cy - r * 0.6, cy + r * 0.6
        p.line([(lx, ty), (lx, by)], color, w)
        p.line([(rx, by), (rx, ty), (cx + r * 0.02, ty)], color, w)
        p.poly([(cx - r * 0.18, ty), (cx + r * 0.14, ty - r * 0.26), (cx + r * 0.14, ty + r * 0.26)], color)
        for x, y in ((lx, ty), (lx, by), (rx, by)):
            p.disc(x, y, r * 0.25, fill=bg, outline=color, width=w * 0.9)
    elif kind == 'star':
        p.poly([(cx + (r if i % 2 == 0 else r * 0.42) * math.cos(math.radians(-90 + 36 * i)), cy + (r if i % 2 == 0 else r * 0.42) * math.sin(math.radians(-90 + 36 * i)))
                for i in range(10)], color)
    elif kind == 'fork':                                        # two tines joining
        lx, rx, ty, by = cx - r * 0.46, cx + r * 0.46, cy - r * 0.6, cy + r * 0.64
        p.line([(lx, ty), (lx, cy - r * 0.1), (cx, cy + r * 0.12), (rx, cy - r * 0.1), (rx, ty)], color, w)
        p.line([(cx, cy + r * 0.12), (cx, by)], color, w)
        for x, y in ((lx, ty), (rx, ty), (cx, by)):
            p.disc(x, y, r * 0.25, fill=bg, outline=color, width=w * 0.9)
    elif kind == 'eye':
        p.d.ellipse(((cx - r * 0.95) * p.k, (cy - r * 0.55) * p.k, (cx + r * 0.95) * p.k, (cy + r * 0.55) * p.k), outline=color, width=p.width(w))
        p.disc(cx, cy, r * 0.26, fill=color)
    elif kind == 'comment':                                     # a speech bubble
        p.rect(cx - r * 0.9, cy - r * 0.7, cx + r * 0.9, cy + r * 0.42, outline=color, width=w, r=r * 0.3)
        p.poly([(cx - r * 0.5, cy + r * 0.3), (cx - r * 0.5, cy + r * 0.9), (cx - r * 0.02, cy + r * 0.3)], color)
    elif kind == 'person':                                      # head and shoulders
        p.disc(cx, cy - r * 0.38, r * 0.34, fill=color)
        p.d.chord(((cx - r * 0.75) * p.k, (cy + r * 0.1) * p.k, (cx + r * 0.75) * p.k, (cy + r * 1.3) * p.k), 180, 360, fill=color)
    elif kind == 'alert':                                       # a triangle with a !
        p.poly([(cx, cy - r * 0.9), (cx + r, cy + r * 0.8), (cx - r, cy + r * 0.8)], color)
        p.line([(cx, cy - r * 0.32), (cx, cy + r * 0.2)], bg, w)
        p.disc(cx, cy + r * 0.52, w * 0.6, fill=bg)
    elif kind == 'pause':
        for x in (cx - r * 0.35, cx + r * 0.35):
            p.rect(x - r * 0.18, cy - r * 0.7, x + r * 0.18, cy + r * 0.7, fill=color, r=r * 0.08)


def heat(v, peak, low):
    """A day's (or an hour's) color in the accent: the track color for none, the deeper the busier it was - low = the share of the quietest busy one"""
    return mix(C_BG3, C_ACCENT, low + (1 - low) * v / peak) if v else C_BG3


def day_counts(per_day, n):
    """Commits per day for the last n days, oldest first (today last)"""
    today = date.today()
    return [per_day.get((today - timedelta(days=i)).isoformat(), 0) for i in range(n - 1, -1, -1)]


def day_name(d):
    """'today', 'yesterday', 'Tue 4 Nov'"""
    today = date.today()
    return 'today' if d == today else 'yesterday' if d == today - timedelta(days=1) else d.strftime('%a %d %b').replace(' 0', ' ')


def hour_name(h):
    """'2 PM - 3 PM'"""
    return f'{hour12(h)} - {hour12((h + 1) % 24)}'


# --- Tiny ---
def paint_orb(days, center, text, blue, amber, busy):
    """Tiny: a repo as an orb.  The ring = its last 14 days of commits, one arc a day (oldest at the top, clockwise, today just left of the top);
       the middle = what is new: green with the number of new commits / branches / tags / PRs, blue with the number of issues with news, red ! for a
       problem, else the repo's initial (or the quiet-repos count) on the track color.  Blue dot = issue news as well, amber dot = someone is waiting
       on your reply, amber outline = being checked right now"""
    p, c = Pic(ORB, ORB, C_BG), ORB / 2
    peak, step = max(days) or 1, 360 / len(days)
    for i, v in enumerate(days):
        a0 = -90 + i * step + 3.5
        p.arc(c, c, 11.0, a0, a0 + step - 7, heat(v, peak, 0.45), 2.8)
    fill, ink = {'code': (C_GREEN, C_BG), 'issue': (C_BLUE, C_BG), 'error': (C_RED, C_BG)}.get(center, (C_BG3, C_MUTED))
    p.disc(c, c, 7.8, fill)
    if busy:
        p.ring(c, c, 7.8, C_AMBER, 1.3)
    if text:
        p.text(c, c, text, ink, 10 if len(text) == 1 else 8.8 if len(text) == 2 else 7.5, bold=True, anchor='m')
    for on, color, dy in ((blue, C_BLUE, -1), (amber, C_AMBER, 1)):
        if on:
            p.disc(c + 9, c + 9 * dy, 3.6, C_BG)
            p.disc(c + 9, c + 9 * dy, 2.7, color)
    return p.png()


def paint_pips(colors, extra, ni, nw, bg):
    """Tiny issues view: one pip per issue, most recent activity first - blue = news, purple = closed with news, amber = waiting on you,
       green = open and quiet.  Then the counts: issues with news, waiting"""
    size = px(8.5)
    items = [(k, n, c) for k, n, c in (('issue', ni, C_BLUE), ('waiting', nw, C_AMBER)) if n]
    w = len(colors) * (PIP_W + PIP_GAP) + (text_w(f'+{extra}', px(7.5)) + 4 if extra else 0) + sum(17 + text_w(str(n), size, True) for _, n, _ in items) + 4
    p, cy = Pic(w, ORB, bg), ORB / 2
    x = 1
    for color in colors:
        p.rect(x, cy - PIP_H / 2, x + PIP_W, cy + PIP_H / 2, fill=color, r=2.5)
        x += PIP_W + PIP_GAP
    if extra:
        p.text(x, cy, f'+{extra}', C_DIM, px(7.5))
        x += text_w(f'+{extra}', px(7.5)) + 4
    for kind, n, color in items:
        x += 4
        icon(p, kind, x + 5, cy, 5, color)
        p.text(x + 12, cy, str(n), color, size, True)
        x += 13 + text_w(str(n), size, True)
    return p.png()


def pip_at(x):
    """Which pip (0, 1, ...) is under x, or None"""
    i = int((x - 1) // (PIP_W + PIP_GAP))
    return i if x >= 1 and (x - 1) % (PIP_W + PIP_GAP) <= PIP_W + 1 else None


# --- Small ---
def paint_beads(days, bg):
    """Small: the last 14 days as beads on a string - the busier the day, the bigger and deeper in the accent its bead (today on the right)"""
    w = len(days) * BEAD_PITCH
    p, cy, peak = Pic(w, BEAD_H, bg), BEAD_H / 2, max(days) or 1
    p.line([(BEAD_PITCH / 2, cy), (w - BEAD_PITCH / 2, cy)], mix(bg, C_LINE, 0.85), 0.8)
    for i, v in enumerate(days):
        cx = BEAD_PITCH * (i + 0.5)
        if v:
            p.disc(cx, cy, 1.7 + 1.5 * math.sqrt(v / peak), heat(v, peak, 0.5))
        else:
            p.disc(cx, cy, 1.05, C_DIM)
    return p.png()


def paint_counts(items, note, note_color, bg):
    """Small: the news as symbols and numbers - items = [(icon, number, color)]; note = words instead ('zz' while badges are hidden, 'problem')"""
    size = px(8.5)
    if note:
        w = text_w(note, size, True) + (13 if note_color == C_RED else 0) + 2
        p = Pic(w, 16, bg)
        if note_color == C_RED:
            icon(p, 'alert', 6, 8, 5, note_color)
        p.text(w - 1, 8, note, note_color, size, True, 'r')
        return p.png()
    w = sum(13 + text_w(str(n), size, True) for _, n, _ in items) + 7 * max(0, len(items) - 1) + 2
    p, x = Pic(w, 16, bg), 1
    for kind, n, color in items:
        icon(p, kind, x + 5, 8, 5, color)
        p.text(x + 12.5, 8, str(n), color, size, True)
        x += 13 + text_w(str(n), size, True) + 7
    return p.png()


# --- Large ---
def cal_start():
    """The Monday the calendar starts on: CAL_WEEKS weeks ending with this one"""
    today = date.today()
    return today - timedelta(days=today.weekday() + 7 * (CAL_WEEKS - 1))


def cal_size():
    pitch = CAL_CELL + CAL_GAP
    return 7 * pitch - CAL_GAP + 2 * CAL_EDGE, CAL_TOP + CAL_WEEKS * pitch - CAL_GAP + 2 * CAL_EDGE


def paint_calendar(per_day, history_days, bg):
    """Large: the last 5 weeks as a calendar, a square a day (Monday first, this week at the bottom), deeper accent the more commits - like
       GitHub's contribution chart.  Days before the activity history are outlines; today has a frame"""
    (w, h), pitch, today, start = cal_size(), CAL_CELL + CAL_GAP, date.today(), cal_start()
    p, e = Pic(w, h, bg), CAL_EDGE
    for i, ch in enumerate(WEEKDAYS):
        p.text(e + i * pitch + CAL_CELL / 2, 4.5, ch, C_DIM, 7.5, anchor='m')
    days = [start + timedelta(days=i) for i in range(7 * CAL_WEEKS)]
    peak = max(per_day.get(d.isoformat(), 0) for d in days) or 1
    for i, d in enumerate(days):
        if d > today:
            continue
        x, y, v = e + (i % 7) * pitch, e + CAL_TOP + (i // 7) * pitch, per_day.get(d.isoformat(), 0)
        if (today - d).days >= history_days:
            p.rect(x + 0.5, y + 0.5, x + CAL_CELL - 0.5, y + CAL_CELL - 0.5, outline=C_BG3, width=1, r=2)
        else:
            level = (0.4, 0.6, 0.8, 1.0)[min(3, math.ceil(4 * v / peak) - 1)] if v else 0
            p.rect(x, y, x + CAL_CELL, y + CAL_CELL, fill=mix(C_BG3, C_ACCENT, level) if v else C_BG3, r=2)
        if d == today:
            p.rect(x - 1.2, y - 1.2, x + CAL_CELL + 1.2, y + CAL_CELL + 1.2, outline=C_TEXT, width=1, r=3)
    return p.png()


def cal_day_at(x, y):
    """The calendar day under (x, y), or None"""
    pitch = CAL_CELL + CAL_GAP
    col, row = int((x - CAL_EDGE) // pitch), int((y - CAL_EDGE - CAL_TOP) // pitch)
    if y < CAL_EDGE + CAL_TOP or not (0 <= col < 7 and 0 <= row < CAL_WEEKS):
        return None
    d = cal_start() + timedelta(days=row * 7 + col)
    return d if d <= date.today() else None


def paint_clock(hours, bg):
    """Large: when the commits land - a 24-hour clock (midnight at the top, noon at the bottom), a wedge per hour, longer and deeper the more
       commits in that hour over the activity history.  The amber hand is now"""
    p, c = Pic(CLOCK, CLOCK, bg), CLOCK / 2
    p.ring(c, c, CLOCK_R1 + 1.5, C_BG3, 1)
    peak = max(hours) or 1
    for h, v in enumerate(hours):
        if v:
            a, half = math.radians(h * 15 + 7.5 - 90), math.radians(6.2)
            r = CLOCK_R0 + (CLOCK_R1 - CLOCK_R0) * (0.3 + 0.7 * v / peak)
            p.poly([(c + rr * math.cos(t), c + rr * math.sin(t)) for rr, t in ((CLOCK_R0, a - half), (r, a - half), (r, a + half), (CLOCK_R0, a + half))],
                   heat(v, peak, 0.45))
    for h in (0, 6, 12, 18):
        a = math.radians(h * 15 - 90)
        p.text(c + (CLOCK_R1 + 7) * math.cos(a), c + (CLOCK_R1 + 7) * math.sin(a), str(h), C_DIM, 7.5, anchor='m')
    now = datetime.now()
    a = math.radians((now.hour + now.minute / 60) * 15 - 90)
    p.line([(c, c), (c + (CLOCK_R1 - 1) * math.cos(a), c + (CLOCK_R1 - 1) * math.sin(a))], C_AMBER, 1.3)
    p.disc(c, c, 2.1, C_AMBER)
    return p.png()


def clock_hour_at(x, y):
    """The hour (0-23) of the clock wedge under (x, y), or None"""
    dx, dy = x - CLOCK / 2, y - CLOCK / 2
    if math.hypot(dx, dy) > CLOCK_R1 + 3:
        return None
    return int(((math.degrees(math.atan2(dy, dx)) + 90) % 360) // 15)


def news_height(lines):
    return max(cal_size()[1], NEWS_PITCH * len(lines) + 2)


def paint_news(lines, bg):
    """Large: what is new, a line per kind - its symbol, the number in its color, then the words.  The new commits' line ends with the lines they
       added and removed: '+603 -177' and five squares split green / red, like GitHub's diffstat.  lines from App.news_lines()"""
    p, size, small = Pic(NEWS_W, news_height(lines), bg), px(9.5), px(8.5)
    for i, (kind, n, words, color, _target, churn) in enumerate(lines):
        cy, x = 1 + NEWS_PITCH * (i + 0.5), 2
        if kind:
            icon(p, kind, x + 6, cy, 6, color)
        x += 18
        if n != '':
            p.text(x, cy, str(n), color, size, True)
            x += text_w(str(n), size, True) + 4
        words = fit(words, size, False, NEWS_W - x - 2)
        p.text(x, cy, words, C_TEXT if n != '' else color, size)
        x += text_w(words, size) + 8
        if churn:
            add, dele = churn
            for words, color in ((f'+{add:,}', C_GREEN), (f'−{dele:,}', C_RED)):
                p.text(x, cy, words, color, small, True)
                x += text_w(words, small, True) + 4
            green = round(DIFF_BLOCKS * add / ((add + dele) or 1)) if add + dele else 0
            red = DIFF_BLOCKS - green if add + dele else 0
            for b in range(DIFF_BLOCKS):
                if x + 7 < NEWS_W:
                    p.rect(x + 2, cy - 3.2, x + 8, cy + 3.2, fill=C_GREEN if b < green else C_RED if b < green + red else C_BG3, r=1.2)
                x += 7.5
    return p.png()


def news_line_at(y, lines):
    """Which news line (0, 1, ...) is under y, or None"""
    i = int((y - 1) // NEWS_PITCH)
    return i if 0 <= i < len(lines) and y >= 1 else None


def paint_stats(items, bg):
    """Large: the repo's numbers as symbols - items = [(icon, number)] (stars, forks, watchers, branches)"""
    size = px(8.5)
    widths = [13 + text_w(str(n), size) for _, n in items]
    p, x = Pic(sum(widths) + 9 * (len(items) - 1) + 2, 16, bg), 1
    for (kind, n), wd in zip(items, widths):
        icon(p, kind, x + 5, 8, 5, C_MUTED)
        p.text(x + 12.5, 8, str(n), C_MUTED, size)
        x += wd + 9
    return p.png()


def paint_pill(text, fg, fill, bg, size):
    """A rounded label: NEW / COMMENT / CLOSED filled, WAITING outlined (fill None)"""
    w = text_w(text, size, True) + 14
    p = Pic(w, 17, bg)
    if fill:
        p.rect(0.5, 1.5, w - 0.5, 15.5, fill=fill, r=7)
    else:
        p.rect(0.5, 1.5, w - 0.5, 15.5, outline=fg, width=1, r=7)
    p.text(w / 2, 8.5, text, fg, size, True, 'm')
    return p.png()


def paint_issue_icon(closed, size, bg):
    """An issue's state: green ring and dot = open, purple ring and tick = closed"""
    p = Pic(size, size, bg)
    icon(p, 'closed' if closed else 'issue', size / 2, size / 2, size / 2 - 0.5, C_PURPLE if closed else C_GREEN)
    return p.png()


def paint_health(parts, w, bg):
    """Large issues view: the repo's issues as one bar - news (blue), waiting on you (amber), the rest open (green) - with a legend under it"""
    p, total, size = Pic(w, 28, bg), sum(n for _, n, _ in parts) or 1, px(8)
    p.rect(0, 2, w, 9, fill=C_BG3, r=3.5)
    x = 0
    for _, n, color in parts:
        if n:
            seg = max(4, w * n / total)
            p.rect(x, 2, min(w, x + seg), 9, fill=color, r=3.5)
            x += seg
    x = 0
    for words, n, color in parts:
        p.disc(x + 4, 20, 3.2, color)
        label = f'{n} {words}'
        p.text(x + 10, 20, label, C_MUTED, size)
        x += 10 + text_w(label, size) + 12
    return p.png()


def paint_issue_meta(runs, w, bg):
    """Large issues view: an issue's second line - runs = [(icon or None, words, color, as_pill)]: who opened it, comments, labels as pills,
       how long it has waited"""
    p, x, size = Pic(w, 16, bg), 0, px(8.5)
    for kind, words, color, pill in runs:
        if x > w - 20:
            break
        if kind:
            icon(p, kind, x + 5, 8, 5, color)
            x += 13
        if pill:
            tw = min(text_w(words, px(8)), w - x - 12)
            p.rect(x, 1.5, x + tw + 10, 14.5, fill=C_BG3, r=6.5)
            p.text(x + 5, 8, fit(words, px(8), False, tw + 1), C_MUTED, px(8))
            x += tw + 15
        elif words:
            s = fit(words, size, False, w - x - 2)
            p.text(x, 8, s, color, size)
            x += text_w(s, size) + 10
    return p.png()


class HoverTip:
    """A small themed tip that follows the pointer over a picture with parts - a day of the calendar, an hour of the clock, an issue pip - and says
       which part is under it.  text_at(x, y) gets the pointer in design pixels and returns the words ('' = nothing there)"""
    def __init__(self, widget, text_at):
        self.widget, self.text_at, self.top, self.label = widget, text_at, None, None
        widget.bind('<Motion>', self.move, add='+')
        widget.bind('<Leave>', self.hide, add='+')
        widget.bind('<ButtonPress>', self.hide, add='+')

    def move(self, e):
        try:
            text = self.text_at(e.x / G.pz, e.y / G.pz)
        except Exception:
            text = ''
        if not text:
            self.hide()
            return
        if self.top is None:
            self.top = tk.Toplevel(self.widget)
            self.top.wm_overrideredirect(True)
            self.top.wm_attributes('-topmost', True)
            self.label = tk.Label(self.top, justify='left', bd=0, padx=8, pady=4, font=(UI_FONT, 9), highlightthickness=1)
            self.label.pack()
        self.label.configure(text=text, bg=C_BG3, fg=C_TEXT, highlightbackground=C_LINE)
        self.top.wm_geometry(f'+{e.x_root + 14}+{e.y_root + 18}')

    def hide(self, e=None):
        if self.top is not None:
            try:
                self.top.destroy()
            except tk.TclError:
                pass
            self.top = None


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


def demo_commit_detail(sha, cache):
    """--demo: made-up files and diff for an older commit clicked under Earlier (instead of asking GitHub)"""
    if sha not in cache:
        rnd = random.Random(sha)
        files = [{'name': n, 'status': 'modified', 'add': rnd.randint(2, 60), 'del': rnd.randint(0, 25), 'patch': DEMO_PATCH, 'prev': None}
                 for n in rnd.sample(['src/impulsing-scene.adb', 'src/impulsing-gltf.adb', 'tests/scene_tests.adb', 'progress/notes.md'], rnd.randint(1, 3))]
        cache[sha] = {'files': files, 'add': sum(f['add'] for f in files), 'del': sum(f['del'] for f in files)}
    return cache[sha]


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
# --- STARTUP: start with Windows - the same block in every card widget (master copy in modern_widget_recipe.md) ---
# Tray apps have their own copy that adds --tray (tray_app_recipe.md); the shortcut is made the same way.  The program supplies APP_NAME (the shortcut's
# name) and its icon (PNG base64) to set_startup().  Off to start: the user ticks it once per PC, so each PC's shortcut points at that PC's copy.
K_STARTUP = '-START WITH WINDOWS-'                                # right-click toggle: the shortcut in this user's Startup folder


def startup_link():
    """ the shortcut in this user's Startup folder that starts the program with Windows """
    return os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', f'{APP_NAME}.lnk')


def startup_on():
    return sg.running_windows() and os.path.exists(startup_link())


def set_startup(on, icon=None):
    """ right-click > Start with Windows: make the shortcut (pythonw "<this file>") or remove it.  icon = the program's PNG (base64): it goes beside the
        program's settings as <APP_NAME>.ico, because a shortcut takes its icon from a file.  Returns '' or why it failed """
    path = startup_link()
    try:
        if not on:
            if os.path.exists(path):
                os.remove(path)
            return ''
        exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')                     # no console window
        exe = exe if os.path.isfile(exe) else sys.executable
        script = os.path.abspath(__file__)
        ico = ''
        if icon:
            png = base64.b64decode(icon)
            ico = os.path.join(os.path.dirname(sg.user_settings_filename()), f'{APP_NAME}.ico')
            width, height = struct.unpack('>II', png[16:24])
            os.makedirs(os.path.dirname(ico), exist_ok=True)
            with open(ico, 'wb') as f:                                                           # an .ico may hold the PNG as it is (Windows Vista and later)
                f.write(struct.pack('<HHHBBBBHHII', 0, 1, 1, width % 256, height % 256, 0, 0, 1, 32, len(png), 22) + png)
        q = lambda s: s.replace("'", "''")                                                       # inside a PowerShell '...' string
        ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(path)}');$s.TargetPath='{q(exe)}';$s.Arguments='\"{q(script)}\"';"
              f"$s.WorkingDirectory='{q(os.path.dirname(script))}';" + (f"$s.IconLocation='{q(ico)}';" if ico else '') + '$s.Save()')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], creationflags=0x08000000, timeout=30, check=True, capture_output=True)   # no window
        return '' if os.path.exists(path) else 'Windows did not make the shortcut'
    except Exception as e:
        return str(e) or type(e).__name__
# --- end STARTUP ---


class App:
    def __init__(self):
        sg.user_settings_filename(filename=DEMO_SETTINGS_FILE if DEMO else SETTINGS_FILE)
        G.app, self.close_x, self.menu, self.cards, self.panel_open = self, None, None, [], False
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
        self.wsize, self.pics, self.tips, self.tip_texts, self.news_cache = self.size_choice(), {}, [], {}, {}
        G.scale = max(1.0, self.scale)
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
            if not self.panel_open:                             # the Brightness panel holds on to this window - it is rebuilt when the panel closes
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
        """The widget window at its size (Tiny, Small, Medium or Large) and in its view (repos or issues)"""
        f = self.fonts()
        self.view, self.wsize = cfg(K_VIEW), self.size_choice()
        for tip in self.tips:
            tip.hide()
        self.pics, self.tips, self.tip_texts, self.news_cache = {}, [], {}, {}
        G.zoom = int(cfg(K_FONT_SIZE)) / 11                     # the pictures grow with the Widget text size
        G.pz = G.scale * G.zoom
        if self.view == VIEW_ISSUES:
            self.widget_rows, self.visible_rows = [], []
        else:
            self.widget_rows, self.visible_rows = self.repos() + [QUIET_ROW], self.widget_row_ids()
        rows = {'Tiny': self.tiny_layout, 'Small': self.small_layout, 'Large': self.large_layout}.get(self.wsize, self.medium_layout)(f)
        first_run = sg.user_settings_get_entry('-LAST WINDOW LOCATION-' + APP_NAME) is None
        self.widget = sg.Window(APP_NAME, rows, no_titlebar=True, keep_on_top=bool(cfg(K_KEEP_ON_TOP)), grab_anywhere=True, alpha_channel=int(cfg(K_OPACITY)) / 100,
                                auto_save_location=True, margins=(2, 2), background_color=C_BG, finalize=True)
        G.window, G.scale = self.widget, max(1.0, self.widget.TKroot.winfo_fpixels('1i') / 96)
        G.pz = G.scale * G.zoom
        self.wire_menu()
        round_corners(self.widget)
        self.widget.bind('<Escape>', 'Exit')
        root = self.widget.TKroot                               # Ctrl + mouse wheel steps through the sizes
        root.bind('<Control-MouseWheel>', lambda e: self.widget.write_event_value(K_SIZE_STEP, 1 if e.delta > 0 else -1), add='+')
        if not sg.running_windows():                            # Linux's wheel - on Windows Button-4 / 5 are the mouse's Back / Forward buttons
            root.bind('<Control-Button-4>', lambda e: self.widget.write_event_value(K_SIZE_STEP, 1), add='+')
            root.bind('<Control-Button-5>', lambda e: self.widget.write_event_value(K_SIZE_STEP, -1), add='+')
        self.current_alpha = int(cfg(K_OPACITY)) / 100
        bind_click(self.widget, self.click_map())
        self.add_hover_tips()
        if self.view == VIEW_ISSUES:
            self.refresh_issue_rows()
        self.close_x = None if self.wsize == 'Tiny' else add_close_x(self.widget, K_CLOSE_X, 'se' if self.wsize == 'Small' else 'ne')   # after the click map; none in Tiny
        if first_run:
            self.snap_to('TR')
        for repo in self.visible_rows:
            self.refresh_row(repo)
        self.refresh_status()
        self.keep_on_screen()

    def status_row(self, status_font, glyph_font, right_pad):
        """The bottom line: when it last checked, ⇄ (switch view) and ≡ (the menu)"""
        other = 'issues' if self.view == VIEW_REPOS else 'repos'
        return [sg.Text('starting…', font=status_font, text_color=C_DIM, key=K_STATUS, pad=((10, 0), (0, 3)), tooltip=f'{APP_NAME} {VERSION}'),
                sg.Push(background_color=C_BG),
                sg.Text('⇄', font=glyph_font, text_color=C_MUTED, key=K_VIEW_TOGGLE, pad=((0, 10), (0, 2)), tooltip=f'Switch to the {other} view'),
                sg.ButtonMenu('≡', self.make_menu(), key=K_MENU, font=glyph_font, button_color=(C_MUTED, C_BG), border_width=0, pad=((0, right_pad), (0, 3)),
                              tooltip='Menu (or right-click) · Ctrl + mouse wheel changes the size')]

    def medium_layout(self, f):
        """Medium - the classic widget: two lines per repo with the issue chip, the news badge and a 14-day bar sparkline (or the issues view's rows)"""
        sc = self.scale
        spark_size = (int(SPARK_DAYS * 6 * sc), int(22 * sc))
        rows = []
        if self.view == VIEW_ISSUES:
            rows.append([sg.Text('issues', font=f['title'], text_color=C_TEXT, key=K_ITITLE, pad=((8, 6), (3, 2)), tooltip='Click to step through the repos that have issues'),
                         sg.Push(background_color=C_BG), sg.Text('', font=f['badge'], text_color=C_BLUE, key=K_IUNREAD, pad=((0, 30), (5, 2)))])
            for i in range(int(cfg(K_ISSUE_ROWS))):
                row = [sg.Text('●', font=f['dot'], text_color=C_DIM, key=KT_IDOT(i), pad=((8, 4), 0), tooltip='Green: open · Purple: closed'),
                       sg.Column([[sg.Text('', font=f['name'], key=KT_INAME(i), pad=0)],
                                  [sg.Text('', font=f['meta'], text_color=C_MUTED, key=KT_IMETA(i), pad=0)]], pad=(0, 2), background_color=C_BG),
                       sg.Push(background_color=C_BG),
                       sg.Text('', size=(9, 1), font=f['badge'], text_color=C_BG, background_color=C_BG, justification='c', key=KT_IBADGE(i), pad=((6, 2), 0)),
                       sg.Text('', size=(4, 1), font=f['meta'], text_color=C_DIM, justification='r', key=KT_IAGE(i), pad=((0, 8), 0))]
                rows.append([sg.pin(sg.Column([row], key=KT_IROW(i), pad=0, expand_x=True, background_color=C_BG, visible=False), expand_x=True)])
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
        rows.append(self.status_row(f['status'], f['name'], 8))
        return rows

    def tiny_layout(self, f):
        """Tiny - one strip: an orb and a name per repo (the issues view: the repo's name and a pip per issue), the status sign and ≡; no ✕ (right-click > Exit)"""
        sf = self.size_fonts()
        strip = []
        if self.view == VIEW_ISSUES:
            strip += [sg.Text('issues', key=K_ITITLE, font=sf['label_b'], text_color=C_TEXT, pad=((8, 6), 0), tooltip='Click to step through the repos that have issues'),
                      sg.Image(data=blank(10, ORB, C_BG), key=K_IPIPS, background_color=C_BG, pad=((0, 4), 0))]
        for repo in self.widget_rows:
            tile = [sg.Image(data=blank(ORB, ORB, C_BG), key=KT_PIC(repo, 'orb'), background_color=C_BG, pad=((0, 3), 0)),
                    sg.Text('', key=KT_NAME(repo), font=sf['label'], text_color=C_MUTED, pad=0)]
            strip.append(sg.pin(sg.Column([tile], key=KT_ROW(repo), pad=((6, 4), 1), background_color=C_BG, visible=repo in self.visible_rows)))
        strip += [sg.Text('', key=K_STATUS, font=sf['label_b'], text_color=C_MUTED, pad=((4, 2), 0)),
                  sg.ButtonMenu('≡', self.make_menu(), key=K_MENU, font=sf['glyph'], button_color=(C_MUTED, C_BG), border_width=0, pad=((2, 6), 0))]
        return [strip]

    def small_layout(self, f):
        """Small - a line per repo: dot, name, the news as symbols, 14 days of beads, how long since the last push (or a line per issue)"""
        sf = self.size_fonts()
        rows = []
        if self.view == VIEW_ISSUES:
            rows.append([sg.Text('issues', key=K_ITITLE, font=sf['name'], text_color=C_TEXT, pad=((8, 6), (3, 3)), tooltip='Click to step through the repos that have issues'),
                         sg.Push(background_color=C_BG), sg.Text('', key=K_IUNREAD, font=sf['meta_b'], text_color=C_BLUE, pad=((0, 8), (3, 3)))])
            for i in range(int(cfg(K_ISSUE_ROWS))):
                row = [sg.Image(data=blank(14, 14, C_BG), key=KT_PIC(i, 'icon'), background_color=C_BG, pad=((9, 6), 0)),
                       sg.Text('', key=KT_INAME(i), font=sf['body'], pad=0),
                       sg.Push(background_color=C_BG),
                       sg.Image(data=blank(1, 17, C_BG), key=KT_PIC(i, 'badge'), background_color=C_BG, pad=((10, 4), 0)),
                       sg.Text('', key=KT_IAGE(i), size=(4, 1), font=sf['meta'], text_color=C_DIM, justification='r', pad=((0, 8), 0))]
                rows.append([sg.pin(sg.Column([row], key=KT_IROW(i), pad=(0, 1), expand_x=True, background_color=C_BG, visible=False), expand_x=True)])
        for repo in self.widget_rows:
            row = [sg.Text('●', key=KT_DOT(repo), font=sf['dot'], text_color=C_DIM, pad=((8, 4), 0)),
                   sg.Text(repo.split('/')[1] if '/' in repo else 'quiet repos', key=KT_NAME(repo), font=sf['name'], pad=0),
                   sg.Push(background_color=C_BG),
                   sg.Image(data=blank(1, 16, C_BG), key=KT_PIC(repo, 'counts'), background_color=C_BG, pad=((12, 8), 0)),
                   sg.Image(data=blank(SPARK_DAYS * BEAD_PITCH, BEAD_H, C_BG), key=KT_PIC(repo, 'beads'), background_color=C_BG, pad=((0, 6), 0)),
                   sg.Text('', key=KT_AGE(repo), size=(4, 1), font=sf['meta'], text_color=C_DIM, justification='r', pad=((0, 8), 0))]
            rows.append([sg.pin(sg.Column([row], key=KT_ROW(repo), pad=(0, 1), expand_x=True, background_color=C_BG, visible=repo in self.visible_rows),
                                expand_x=True)])
        rows.append(self.status_row(sf['meta'], sf['glyph'], 26))
        return rows

    def large_layout(self, f):
        """Large - a card per repo: name, language, stars / forks / watchers / branches, description, a 5-week calendar, a 24-hour clock of when the
           commits land, the news a line per kind, the newest commit and its +/- lines (the issues view: a health bar, then a two-line card per issue)"""
        sf, bg = self.size_fonts(), C_BG2
        rows = []
        if self.view == VIEW_ISSUES:
            rows.append([sg.Text('issues', key=K_ITITLE, font=sf['h1'], text_color=C_TEXT, pad=((10, 6), (6, 0)), tooltip='Click to step through the repos that have issues'),
                         sg.Push(background_color=C_BG), sg.Text('', key=K_IUNREAD, font=sf['meta_b'], text_color=C_BLUE, pad=((0, 30), (8, 0)))])
            rows.append([sg.Image(data=blank(ISSUE_W, 28, C_BG), key=K_IHEALTH, background_color=C_BG, pad=((12, 10), (6, 6)))])
            for i in range(int(cfg(K_ISSUE_ROWS))):
                card = [[sg.Image(data=blank(18, 18, bg), key=KT_PIC(i, 'icon'), background_color=bg, pad=((10, 8), (7, 0))),
                         sg.Text('', key=KT_INAME(i), font=sf['body_b'], background_color=bg, pad=(0, (7, 0))),
                         sg.Push(background_color=bg),
                         sg.Image(data=blank(1, 17, bg), key=KT_PIC(i, 'badge'), background_color=bg, pad=((10, 4), (7, 0))),
                         sg.Text('', key=KT_IAGE(i), size=(4, 1), font=sf['meta'], text_color=C_DIM, background_color=bg, justification='r', pad=((0, 8), (7, 0)))],
                        [sg.Image(data=blank(ISSUE_W, 16, bg), key=KT_PIC(i, 'meta'), background_color=bg, pad=((36, 10), (3, 8)))]]
                rows.append([sg.pin(sg.Column(card, key=KT_IROW(i), pad=((8, 8), (0, 6)), expand_x=True, background_color=bg, visible=False), expand_x=True)])
        else:
            rows.append([sg.Image(data=ICON, subsample=4 if G.scale < 1.5 else 2, background_color=C_BG, pad=((12, 6), (7, 4))),
                         sg.Text('Repo Watch', font=sf['body_b'], text_color=C_TEXT, pad=(0, (7, 4))),
                         sg.Text('', key=K_HEAD, font=sf['meta'], text_color=C_MUTED, pad=((10, 34), (8, 4)))])
        for repo in self.widget_rows:
            card = [[sg.Text('●', key=KT_DOT(repo), font=sf['dot'], text_color=C_DIM, background_color=bg, pad=((10, 6), (6, 0))),
                     sg.Text(repo.split('/')[1] if '/' in repo else 'quiet repos', key=KT_NAME(repo), font=sf['h1'], background_color=bg, pad=(0, (6, 0))),
                     sg.Text('', key=KT_META(repo), font=sf['meta'], text_color=C_MUTED, background_color=bg, pad=((10, 0), (11, 0))),
                     sg.Push(background_color=bg),
                     sg.Image(data=blank(1, 16, bg), key=KT_PIC(repo, 'stats'), background_color=bg, pad=((12, 12), (9, 0)))],
                    [sg.Text('', key=KT_DESC(repo), font=sf['meta'], text_color=C_MUTED, background_color=bg, pad=((32, 12), (0, 8)))],
                    [sg.Image(data=blank(*cal_size(), bg), key=KT_PIC(repo, 'cal'), background_color=bg, pad=((30, 14), 0)),
                     sg.Image(data=blank(CLOCK, CLOCK, bg), key=KT_PIC(repo, 'clock'), background_color=bg, pad=((0, 14), 0)),
                     sg.Image(data=blank(NEWS_W, cal_size()[1], bg), key=KT_PIC(repo, 'news'), background_color=bg, pad=((0, 12), 0))],
                    [sg.Text('', key=KT_LATEST(repo), font=sf['meta'], text_color=C_MUTED, background_color=bg, pad=((32, 12), (6, 9)))]]
            rows.append([sg.pin(sg.Column(card, key=KT_ROW(repo), pad=((8, 8), (0, 6)), expand_x=True, background_color=bg, visible=repo in self.visible_rows),
                                expand_x=True)])
        rows.append(self.status_row(sf['meta'], sf['glyph'], 8))
        return rows

    def click_map(self):
        """What a click on each part of the widget opens - bind_click's map.  A function there works the target out from where the click landed"""
        m, w = {}, self.widget
        for repo in self.widget_rows:
            target = (K_ORB, repo) if self.wsize == 'Tiny' else repo
            for wd in descendants(w[KT_ROW(repo)].Widget):
                m[wd] = target
            if self.wsize == 'Medium':
                m[w[KT_ICHIP(repo)].Widget] = KT_ICHIP(repo)          # a click on the issue chip opens the Issues window
            elif self.wsize == 'Small':
                m[w[KT_PIC(repo, 'counts')].Widget] = KT_ICHIP(repo)
            elif self.wsize == 'Large':
                m[w[KT_PIC(repo, 'news')].Widget] = lambda e, repo=repo: self.news_target(repo, e.y / G.pz)
        if self.view == VIEW_ISSUES:
            if self.wsize == 'Tiny':
                m[w[K_IPIPS].Widget] = lambda e: self.pip_target(e.x / G.pz)
            else:
                for i in range(int(cfg(K_ISSUE_ROWS))):
                    for wd in descendants(w[KT_IROW(i)].Widget):
                        m[wd] = KT_IROW(i)
            if self.wsize == 'Large':
                m[w[K_IHEALTH].Widget] = lambda e: (K_OPEN_ISSUES, self.issue_view_repo())
            m[w[K_ITITLE].Widget] = (K_ITITLE, None)
        if K_VIEW_TOGGLE in w.AllKeysDict:
            m[w[K_VIEW_TOGGLE].Widget] = (K_VIEW_TOGGLE, None)
        return m

    def hover(self, key, text_at):
        """A HoverTip on one of the widget's pictures"""
        self.tips.append(HoverTip(self.widget[key].Widget, text_at))

    def add_hover_tips(self):
        """The pictures say what is under the pointer: the day, the hour, the issue, what a number means"""
        for repo in self.widget_rows:
            if self.wsize == 'Tiny':
                self.hover(KT_PIC(repo, 'orb'), lambda x, y, repo=repo: self.orb_text(repo))
            elif self.wsize == 'Small':
                self.hover(KT_PIC(repo, 'beads'), lambda x, y, repo=repo: self.bead_text(repo, x))
                self.hover(KT_PIC(repo, 'counts'), lambda x, y, repo=repo: self.counts_text(repo))
            elif self.wsize == 'Large':
                self.hover(KT_PIC(repo, 'cal'), lambda x, y, repo=repo: self.cal_text(repo, x, y))
                self.hover(KT_PIC(repo, 'clock'), lambda x, y, repo=repo: self.clock_text(repo, x, y))
                self.hover(KT_PIC(repo, 'news'), lambda x, y, repo=repo: self.news_text(repo, y))
                self.hover(KT_PIC(repo, 'stats'), lambda x, y, repo=repo: self.stats_text(repo))
        if self.view == VIEW_ISSUES and self.wsize == 'Tiny':
            self.hover(K_IPIPS, lambda x, y: self.pip_text(x))

    def make_menu(self):
        """The right-click / ≡ menu with a ✓ on the current choices - every label starts with a ✓ or the same width of spaces, so they line up"""
        tick = lambda on: '✓ ' if on else '    '
        theme = lambda n: f'{tick(n == G.theme)}{n}::{KT_THEME(n)}'
        paused = self.poller is not None and self.poller.paused
        return ['', [f'    Check now::{K_M_CHECK}', f'    Mark all as read::{K_M_READ}', f'    Switch view  (repos ⇄ issues)::{K_M_VIEW}', '---',
                     f'{tick(paused)}Pause polling::{K_M_PAUSE}', f'{tick(cfg(K_KEEP_ON_TOP))}Keep on top::{K_M_TOP}',
                     *([f'{tick(startup_on())}Start with Windows::{K_STARTUP}'] if sg.running_windows() and not DEMO else []),
                     '    Theme', [theme(n) for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],
                     f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
                     *accent_menu(tick),
                     '    Size', [f'{tick(size == self.wsize)}{size}::{KT_M_SIZE(size)}' for size in SIZES],
                     '    Snooze', [f'    {label}::{key}' for key, label in SNOOZES.items()],
                     '    Snap to corner', [f'    {name}::{KT_M_SNAP(corner)}' for corner, name in SNAP_CORNERS.items()], '---',
                     f'    Settings...::{K_M_SETTINGS}', f'    Open log file::{K_M_LOG}', f'    About::{K_M_ABOUT}', '---',
                     '    Edit Me::Edit Me', f'    Version {VERSION}::Version', *update_menu(tick), '    Exit::Exit']]

    def wire_menu(self):
        """The right-click menu: ONE menu for the whole widget, popped up from a right-click anywhere on it (PySimpleGUI's right_click_menu would give
           every element - all the rows, hidden ones too - a copy of its own, and with 32 themes in it that gets slow).  Its choices send their keys as events"""
        self.menu = tk_menu(self.widget.TKroot, self.make_menu()[1], self.widget)

        def popup(e):
            self.menu.tk_popup(e.x_root, e.y_root, 0)
            if not sg.running_linux():
                self.menu.grab_release()

        self.widget.TKroot.bind('<ButtonRelease-2>' if sg.running_mac() else '<ButtonRelease-3>', popup, add='+')
        style_menus(self.widget)

    def rebuild_menus(self):
        """After a choice: the right-click menu and the ≡ menu rebuilt (new ✓ marks), then styled"""
        menu = self.make_menu()
        old, self.menu = self.menu, tk_menu(self.widget.TKroot, menu[1], self.widget)
        old.destroy()
        old = self.widget[K_MENU].TKMenu
        self.widget[K_MENU].update(menu_definition=menu, button_color=(C_MUTED, C_BG))     # without button_color, update() puts back the colors it was built with
        old.destroy()
        style_menus(self.widget)

    def set_keep_on_top(self, on):
        sg.user_settings_set_entry(K_KEEP_ON_TOP, on)
        self.widget.keep_on_top_set() if on else self.widget.keep_on_top_clear()
        self.rebuild_menus()                                    # the ✓ beside Keep on top

    def retheme(self):
        """A new theme or Brightness: every color worked out again, the widget rebuilt in them, and every open window reopened in place in the new colors
           (lists keep their selection, Settings what was typed)"""
        apply_theme()
        self.rebuild_widget()
        if self.details is not None:
            spot, repo = self.details.current_location(), self.details_repo
            self.open_details(repo, reopen=True, spot=spot)
        if self.issues_win is not None:
            spot, repo = self.issues_win.current_location(), self.issues_repo
            number = self.issue_items[self.issue_selected][1]['number'] if self.issue_selected is not None else None
            self.open_issues(repo, reopen=True, number=number, spot=spot)
        if self.all_win is not None:
            self.open_all_repos(self.all_win.current_location())
        if self.settings_win is not None:
            spot, values = self.settings_win.current_location(), self.settings_win.read(timeout=0)[1]
            self.settings_win.close()
            self.settings_win = None
            self.open_settings(values, spot)
        if self.pick_win is not None:
            spot, values = self.pick_win.current_location(), self.pick_win.read(timeout=0)[1] or {}
            text = self.settings_win[K_REPOS].get() if self.settings_win is not None else ''
            self.open_picker(self.pick_owner, self.pick_repos, text, spot)
            for i in range(len(self.pick_repos)):
                if KT_PICK_ROW(i) in values:
                    self.pick_win[KT_PICK_ROW(i)].update(values[KT_PICK_ROW(i)])
        old, self.cards = self.cards, []
        for card in old:
            spot = card.current_location()
            card.close()
            self.text_card(card.metadata['title'], card.metadata['text'], card.metadata['size'], spot)

    def keep_going(self, window, event, values):
        """While the Brightness panel is open the widget keeps taking poll results; anything else closes the panel and goes to the main loop.
           Ctrl + mouse wheel there gets the panel back under the new size (widget_event); one past Tiny or Large does nothing"""
        if event in (K_POLL_BUSY, K_POLL_RESULT, K_REPOS_RESOLVED):
            self.widget_event(event, values)
            return True
        return event == K_SIZE_STEP and self.size_after(values[event]) == self.wsize

    def text_card(self, title, text, size, spot=(None, None)):
        """Version, About and messages: the text on a themed card with a title strip, no OS title bar.  The main loop closes it (x, Close, Escape, Alt-F4)"""
        layout = [title_strip(title),
                  [sg.Multiline(text, size=size, font=(MONO_FONT, 10), disabled=True, background_color=C_BG2, text_color=C_TEXT, border_width=0, pad=((10, 10), (8, 4)),
                                expand_x=True, expand_y=True)],
                  [sg.Push(background_color=C_BG), sg.Button('Close', key=K_CLOSE, pad=((0, 4), (4, 10))), sg.Sizegrip(background_color=C_BG)]]
        card = sg.Window(title, layout, no_titlebar=True, keep_on_top=True, finalize=True, margins=(0, 0), resizable=True, location=spot, background_color=C_BG,
                         metadata={'title': title, 'text': text, 'size': size}, **sbar())
        dress(card, K_CLOSE)
        self.cards.append(card)

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
        if self.wsize != 'Medium':
            self.paint_row(repo)
            self.refresh_status()
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
        if self.wsize != 'Medium':
            self.paint_issue_rows()
            return
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

    # ---------------------------------------------------------------- Tiny / Small / Large: what the rows show ----------------------------------------------------------------
    def size_choice(self):
        return cfg(K_SIZE) if cfg(K_SIZE) in SIZES else 'Medium'

    def size_after(self, step):
        """The size one step bigger (+1) or smaller (-1) than now, stopping at Tiny and Large"""
        return SIZES[max(0, min(len(SIZES) - 1, SIZES.index(self.wsize) + step))]

    def set_size(self, size):
        """Right-click > Size, or Ctrl + mouse wheel: the widget rebuilt at the new size, remembered between runs.  Its top-left corner stays where it
           was, and it stays on its monitor (slides back in if it now runs past the right or bottom edge)"""
        if size != self.wsize:
            sg.user_settings_set_entry(K_SIZE, size)
            self.last_geom = None                               # so keep_on_screen() doesn't hold the right edge instead of the corner
            self.rebuild_widget()
            keep_on_monitor(self.widget)

    def size_fonts(self):
        """The Tiny / Small / Large widget's fonts - the Widget text size setting, a step or two smaller for Tiny and Small"""
        fs = int(cfg(K_FONT_SIZE)) + SIZE_FONT_STEP[self.wsize]
        return {'h1': (UI_FONT, fs + 3, 'bold'), 'name': (UI_FONT, fs, 'bold'), 'body': (UI_FONT, fs), 'body_b': (UI_FONT, fs, 'bold'),
                'meta': (UI_FONT, max(fs - 1, 7)), 'meta_b': (UI_FONT, max(fs - 1, 7), 'bold'), 'label': (UI_FONT, fs), 'label_b': (UI_FONT, fs, 'bold'),
                'dot': (UI_FONT, fs + 2), 'glyph': (UI_FONT, fs + 2)}

    def show_pic(self, key, painter, *args, when=None):
        """Draw a picture into its Image element - only when what it shows, the colors or `when` (the day, the hour) changed, so refreshes never flicker"""
        sig = (painter.__name__, repr(args), when, palette(), G.pz)
        if self.pics.get(key) != sig:
            self.pics[key] = sig
            self.widget[key].update(data=painter(*args))

    def set_tip(self, key, text):
        """An element's tooltip, set again only when its text changed"""
        if text and self.tip_texts.get(key) != text:
            self.tip_texts[key] = text
            self.widget[key].set_tooltip(text)

    def repaint(self):
        """The Brightness knob moved: every picture drawn again in the new colors (Medium has none - recolor() changed its colors in place)"""
        if self.wsize == 'Medium':
            return
        for repo in self.visible_rows:
            self.refresh_row(repo)
        if self.view == VIEW_ISSUES:
            self.refresh_issue_rows()

    def hours_of(self, snap):
        """Commits per hour of the day (local time) over the activity history - worked out once and kept with the snapshot"""
        if '_hours' not in snap:
            hours = [0] * 24
            for c in snap.get('history', []):
                if c.get('date'):
                    hours[parse_iso(c['date']).astimezone().hour] += 1
            snap['_hours'] = hours
        return snap['_hours']

    def row_facts(self, repo):
        """What a Tiny / Small / Large row shows about a repo, or about the quiet repos, worked out in one place.  While badges are snoozed the
           numbers are 0 and 'snoozed' says there was something"""
        hist, snooze = int(str(cfg(K_HISTORY_DAYS)).split()[0]), bool(self.snooze_until)
        if repo == QUIET_ROW:
            hidden = [r for r in self.repos() if r not in self.visible_rows]
            ok = [r for r in hidden if (self.snapshots.get(r) or {}).get('ok')]
            per_day, hours = Counter(), [0] * 24
            for r in ok:
                per_day.update(self.snapshots[r].get('per_day', {}))
                hours = [a + b for a, b in zip(hours, self.hours_of(self.snapshots[r]))]
            pushes = sorted(((parse_iso(self.snapshots[r]['info']['pushed_at']), r) for r in ok if self.snapshots[r]['info'].get('pushed_at')), reverse=True)
            busy = next((r for r in hidden if r in self.busy), None)
            nw = sum(self.issue_counts(self.snapshots.get(r))[1] for r in ok)
            name = f'{len(hidden)} quiet repo{"s" if len(hidden) != 1 else ""}' if len(ok) == len(hidden) else f'{len(hidden)} repos'
            return {'repo': repo, 'quiet': True, 'name': name, 'short': 'quiet', 'owner': '', 'count': len(hidden), 'busy_repo': busy,
                    'state': 'busy' if busy else 'quiet' if ok else 'checking', 'dot': C_AMBER if busy else C_DIM, 'snoozed': snooze and bool(nw),
                    'nc': 0, 'ni': 0, 'nw': 0 if snooze else nw, 'news': {}, 'per_day': dict(per_day), 'hours': hours, 'days': day_counts(per_day, SPARK_DAYS),
                    'history_days': hist, 'pushes': pushes, 'pushed': pushes[0][0] if pushes else None, 'error': '', 'info': {}, 'latest': None, 'churn': None,
                    'commits': sum(len(self.snapshots[r].get('history', [])) for r in ok), 'branches': 0}
        snap, (owner, name) = self.snapshots.get(repo), repo.split('/')
        ok, n = bool(snap and snap.get('ok')), self.unread_count(snap)
        ni, nw = self.issue_counts(snap)
        state = 'busy' if repo in self.busy else 'checking' if snap is None else 'error' if not ok else 'news' if n and not snooze else 'quiet'
        x = {'repo': repo, 'quiet': False, 'name': name, 'short': name if len(name) <= 13 else name[:12] + '…', 'owner': owner, 'state': state,
             'dot': {'busy': C_AMBER, 'error': C_RED, 'news': C_GREEN}.get(state, C_DIM), 'snoozed': snooze and bool(n or nw),
             'nc': 0 if snooze else n - ni, 'ni': 0 if snooze else ni, 'nw': 0 if snooze else nw, 'news': {}, 'per_day': {}, 'hours': [0] * 24,
             'days': [0] * SPARK_DAYS, 'history_days': hist, 'pushed': None, 'error': snap.get('error', '') if snap and not ok else '', 'info': {},
             'latest': None, 'churn': None, 'commits': 0, 'branches': 0}
        if ok:
            info = snap['info']
            x.update(info=info, per_day=snap.get('per_day', {}), hours=self.hours_of(snap), days=day_counts(snap.get('per_day', {}), SPARK_DAYS),
                     pushed=parse_iso(info.get('pushed_at')), commits=len(snap.get('history', [])), branches=len(snap.get('branches', {})),
                     news={} if snooze else {'commits': len(snap['new_commits']), 'prs': len(snap['new_prs']), 'branches': len(snap['new_branches']),
                                             'tags': len(snap['new_tags']), 'releases': len(snap['new_releases'])})
            newest = (snap['new_commits'] or snap.get('history') or [None])[0]
            if newest:
                x['latest'] = (newest['title'], newest.get('login') or newest.get('author') or '?', parse_iso(newest['date']), bool(snap['new_commits']))
            found = [self.poller.commit_cache.get(c['sha']) for c in snap['new_commits']] if self.poller is not None else []
            found = [d for d in found if d]
            if found:
                x['churn'] = (sum(d.get('add', 0) for d in found), sum(d.get('del', 0) for d in found), len(found))
        return x

    def paint_row(self, repo):
        """A Tiny / Small / Large row, or the quiet-repos summary, in its pictures and words"""
        x, w = self.row_facts(repo), self.widget
        loud = x['state'] in ('news', 'error') or bool(x['nw'])
        if self.wsize == 'Tiny':
            if x['quiet']:
                center, text = 'quiet', str(x['count'])
            elif x['state'] == 'error':
                center, text = 'error', '!'
            elif x['snoozed']:
                center, text = 'quiet', 'z'
            elif x['nc'] or x['ni']:
                center, n = ('code', x['nc']) if x['nc'] else ('issue', x['ni'])
                text = str(n) if n < 100 else '99+'
            else:
                center, text = 'quiet', x['name'][:1].upper()
            self.show_pic(KT_PIC(repo, 'orb'), paint_orb, x['days'], center, text, bool(x['nc'] and x['ni']), bool(x['nw']), x['state'] == 'busy')
            w[KT_NAME(repo)].update(x['short'], text_color=C_RED if x['state'] == 'error' else C_TEXT if loud else C_MUTED)
            return
        w[KT_DOT(repo)].update(text_color=x['dot'])
        if self.wsize == 'Small':
            w[KT_NAME(repo)].update(x['name'])
            items = [(kind, n, color) for kind, n, color in (('commit', x['nc'], C_GREEN), ('issue', x['ni'], C_BLUE), ('waiting', x['nw'], C_AMBER)) if n]
            note, note_color = ('zz', C_MUTED) if x['snoozed'] and not items else ('problem', C_RED) if x['state'] == 'error' else ('', C_MUTED)
            self.show_pic(KT_PIC(repo, 'counts'), paint_counts, items, note, note_color, C_BG)
            self.show_pic(KT_PIC(repo, 'beads'), paint_beads, x['days'], C_BG, when=date.today())
            w[KT_AGE(repo)].update(age_short(x['pushed']) if x['pushed'] else '…' if x['state'] in ('checking', 'busy') else '')
            self.set_tip(KT_NAME(repo), self.row_tip(x))
            return
        bg, info = C_BG2, x['info']
        w[KT_NAME(repo)].update(x['name'])
        if x['quiet']:
            meta, stats = '', []
            desc = ' · '.join(f'{r.split("/")[1]} {age_short(t)}' for t, r in x['pushes']) or 'first check…'
            latest = f'newest push: {x["pushes"][0][1].split("/")[1]} · {ago(x["pushes"][0][0])}' if x['pushes'] else ''
        else:
            meta = ' · '.join(s for s in (info.get('language'), ('private' if info.get('private') else 'public') if info else '') if s)
            stats = [('star', info.get('stars', 0)), ('fork', info.get('forks', 0)), ('eye', info.get('watchers', 0)), ('branch', x['branches'])] if info else []
            desc = x['error'] or info.get('description') or ('checking…' if not info else 'no description')
            latest = ''
            if x['latest']:
                title, who, when, new = x['latest']
                latest = f'{"newest" if new else "latest"}: {shorten(title, 46)}  ·  {who} · {ago(when) if when else ""}'
        w[KT_META(repo)].update(meta)
        w[KT_DESC(repo)].update(shorten(desc, 74), text_color=C_RED if x['error'] else C_MUTED)
        self.set_tip(KT_DESC(repo), desc if len(desc) > 74 else None)
        w[KT_LATEST(repo)].update(latest)
        if stats:
            self.show_pic(KT_PIC(repo, 'stats'), paint_stats, stats, bg)
        else:
            self.show_pic(KT_PIC(repo, 'stats'), blank, 1, 16, bg)
        self.show_pic(KT_PIC(repo, 'cal'), paint_calendar, x['per_day'], x['history_days'], bg, when=date.today())
        self.show_pic(KT_PIC(repo, 'clock'), paint_clock, x['hours'], bg, when=(datetime.now().hour, datetime.now().minute // 10))
        self.news_cache[repo] = lines = self.news_lines(x)
        self.show_pic(KT_PIC(repo, 'news'), paint_news, lines, bg)

    def row_tip(self, x):
        """A row's tooltip: the repo, its description, when it was pushed - or what went wrong"""
        if x['quiet']:
            return 'Click for the full list of watched repos'
        if x['error']:
            return f'{x["repo"]}\n{x["error"]}'
        parts = [x['repo'], x['info'].get('description', '')]
        return '\n'.join(p for p in parts + ([f'pushed {ago(x["pushed"])}'] if x['pushed'] else []) if p)

    def news_lines(self, x):
        """Large: the news list - (icon, number, words, color, what a click on the line opens, (lines added, removed) for the new commits)"""
        repo, k = x['repo'], x['news']
        plural = lambda n, word, many=None: word if n == 1 else (many or word + 's')
        issues = (K_OPEN_ISSUES, repo)
        history = (None, '', f'{n_of(x["commits"], "commit")} in {x["history_days"]} days', C_DIM, repo, None)
        if x['quiet']:
            lines = [('check', '', 'all quiet', C_MUTED, repo, None)]
            if x['nw']:
                lines.append(('waiting', x['nw'], 'waiting on you', C_AMBER, (K_OPEN_ISSUES, self.chip_repo(QUIET_ROW)), None))
            return lines + [history]
        if x['state'] == 'checking' or (x['state'] == 'busy' and not x['info'] and not x['error']):
            return [('waiting', '', 'first check…', C_DIM, repo, None)]
        if x['error']:
            return [('alert', '', 'GitHub said no - the reason is above', C_RED, repo, None)]
        if x['snoozed']:
            return [('pause', '', 'news hidden while snoozed', C_MUTED, repo, None)]
        lines = []
        if k.get('commits'):
            lines.append(('commit', k['commits'], plural(k['commits'], 'new commit'), C_GREEN, repo, x['churn'][:2] if x['churn'] else None))
        if k.get('prs'):
            lines.append(('pr', k['prs'], plural(k['prs'], 'pull request'), C_PINK, repo, None))
        if x['ni']:
            lines.append(('issue', x['ni'], plural(x['ni'], 'issue with news', 'issues with news'), C_BLUE, issues, None))
        if x['nw']:
            lines.append(('waiting', x['nw'], 'waiting on you', C_AMBER, issues, None))
        refs = [n_of(n, word, many) for n, word, many in ((k.get('branches', 0), 'new branch', 'new branches'), (k.get('tags', 0), 'tag', None),
                                                         (k.get('releases', 0), 'release', None)) if n]
        if refs:
            kind = 'branch' if k.get('branches') else 'tag' if k.get('tags') else 'release'
            lines.append((kind, '', ' · '.join(refs), C_AMBER if kind == 'branch' else C_PURPLE, repo, None))
        if not lines:
            lines.append(('check', '', 'all caught up', C_MUTED, repo, None))
        return lines + [history] if len(lines) < 4 else lines

    def news_target(self, repo, y):
        """What a click on a Large news line opens - its line's target (What's new, or the Issues window)"""
        lines = self.news_cache.get(repo, [])
        i = news_line_at(y, lines)
        return lines[i][4] if i is not None and lines[i][4] else repo

    def pip_target(self, x):
        """What a click on the Tiny issues strip opens - the issue under the pointer, else the Issues window"""
        i = pip_at(x)
        return KT_IROW(i) if i is not None and i < len(self.issue_rows_shown) else (K_OPEN_ISSUES, self.issue_view_repo())

    # --- what the pictures say under the pointer ---
    def orb_text(self, repo):
        x = self.row_facts(repo)
        if x['quiet']:
            lines = [x['name'], f'newest push: {x["pushes"][0][1].split("/")[1]} · {ago(x["pushes"][0][0])}' if x['pushes'] else 'first check…']
            if x['nw']:
                lines.append(f'{n_of(x["nw"], "issue")} waiting on you')
            return '\n'.join(lines + ['ring: their commits per day, last 14 days', 'click for the list'])
        lines = [f'{x["name"]}  ·  {x["owner"]}']
        if x['error']:
            return '\n'.join(lines + [x['error']])
        news = [f'{x["nc"]} new (commits, branches, tags, PRs)' if x['nc'] else '', f'{n_of(x["ni"], "issue")} with news' if x['ni'] else '',
                f'{x["nw"]} waiting on you' if x['nw'] else '']
        lines.append(' · '.join(s for s in news if s) or ('badges hidden (snoozed)' if x['snoozed'] else 'nothing new'))
        if x['pushed']:
            lines.append(f'pushed {ago(x["pushed"])}')
        lines.append(f'ring: commits per day, last 14 days (today {x["days"][-1]})')
        lines.append('click for the Issues window' if not x['nc'] and (x['ni'] or x['nw']) else "click for What's new")
        return '\n'.join(lines)

    def bead_text(self, repo, bx):
        x = self.row_facts(repo)
        i = int(bx // BEAD_PITCH)
        if not 0 <= i < SPARK_DAYS:
            return ''
        return f'{day_name(date.today() - timedelta(days=SPARK_DAYS - 1 - i))}: {n_of(x["days"][i], "commit")}'

    def counts_text(self, repo):
        x = self.row_facts(repo)
        parts = [f'{x["nc"]} new commits / branches / tags / PRs' if x['nc'] else '', f'{n_of(x["ni"], "issue")} with news' if x['ni'] else '',
                 f'{x["nw"]} waiting on your reply' if x['nw'] else '']
        text = '\n'.join(p for p in parts if p)
        return f'{text}\nclick for the Issues window' if x['ni'] or x['nw'] else text

    def cal_text(self, repo, cx, cy):
        x, d = self.row_facts(repo), cal_day_at(cx, cy)
        if d is None:
            return ''
        if (date.today() - d).days >= x['history_days']:
            return f'{day_name(d)}: before the {x["history_days"]}-day activity history'
        return f'{day_name(d)}: {n_of(x["per_day"].get(d.isoformat(), 0), "commit")}'

    def clock_text(self, repo, cx, cy):
        x, h = self.row_facts(repo), clock_hour_at(cx, cy)
        if h is None:
            return ''
        return f'{hour_name(h)}: {n_of(x["hours"][h], "commit")} in the last {x["history_days"]} days'

    def news_text(self, repo, y):
        lines = self.news_cache.get(repo, [])
        i = news_line_at(y, lines)
        if i is None:
            return ''
        kind, n, words, _color, target, churn = lines[i]
        where = 'the Issues window' if isinstance(target, tuple) and target[0] == K_OPEN_ISSUES else 'the list of repos' if repo == QUIET_ROW else "What's new"
        lines_changed = f'\nthey added {churn[0]:,} lines and removed {churn[1]:,}' if churn else ''
        return f'{n} {words}'.strip() + lines_changed + f'\nclick for {where}'

    def stats_text(self, repo):
        x = self.row_facts(repo)
        info = x['info']
        if not info:
            return ''
        return f'{n_of(info.get("stars", 0), "star")} · {n_of(info.get("forks", 0), "fork")} · {info.get("watchers", 0)} watching · {n_of(x["branches"], "branch", "branches")}'

    def pip_text(self, px_x):
        i = pip_at(px_x)
        if i is None or i >= len(self.issue_rows_shown):
            return ''
        rec = self.issue_rows_shown[i]
        badge = self.issue_badge(rec)[0]
        return f'#{rec["number"]}  {shorten(rec["title"], 60)}\n{(badge.lower() + " · ") if badge else ""}{rec["user"]} · {n_of(rec["comments"], "comment")} · ' \
               f'{age_short(parse_iso(rec["date"]))}'

    # --- the issues view at Tiny / Small / Large ---
    def issue_badge(self, rec):
        """An issue's badge, as in the Medium issues view: NEW / COMMENT / CLOSED (news), WAITING (someone waits on you) - (words, text color, fill)"""
        what = rec['news']['what'] if rec['news'] else ''
        if what:
            return {'opened': 'NEW', 'commented': 'COMMENT', 'closed': 'CLOSED'}.get(what, 'NEW'), C_BG, C_PURPLE if what == 'closed' else C_BLUE
        return ('WAITING', C_AMBER, None) if rec['waiting'] else ('', C_BG, None)

    def issue_color(self, rec):
        """A Tiny pip's color: blue = news, purple = closed, amber = waiting on you, green = open and quiet"""
        if rec['news']:
            return C_PURPLE if rec['news']['what'] == 'closed' else C_BLUE
        return C_PURPLE if rec['state'] == 'closed' else C_AMBER if rec['waiting'] else mix(C_BG3, C_GREEN, 0.55)

    def issue_meta_runs(self, rec):
        """Large: an issue's second line - who opened it, comments, the news or how long it has waited, its labels"""
        runs = [('person', rec['user'], C_MUTED, False), ('comment', str(rec['comments']), C_MUTED, False)]
        news = rec['news']
        if news and news['what'] in ('commented', 'closed'):
            runs.append((None, f'{"closed" if news["what"] == "closed" else "comment"} by {news["actor"]}', C_PURPLE if news['what'] == 'closed' else C_BLUE, False))
        elif rec['waiting'] and rec.get('last'):
            runs.append(('waiting', f'waiting {span(parse_iso(rec["last"]["at"]))} · last word {rec["last"]["login"]}', C_AMBER, False))
        return runs + [(None, label, C_MUTED, True) for label in rec['labels'][:3]]

    def paint_issue_rows(self):
        """The issues view at Tiny (a pip per issue), Small (a line per issue) or Large (a health bar and a card per issue)"""
        repo = self.issue_view_repo()
        snap, w = self.snapshots.get(repo), self.widget
        name = repo.split('/')[1] if '/' in repo else repo
        everything = self.issue_list(snap) if snap and snap.get('ok') else []
        ni, nw = (0, 0) if self.snooze_until else self.issue_counts(snap)
        w[K_ITITLE].update(f'{name} issues' if name else 'issues')
        self.set_tip(K_ITITLE, f'{repo}\nClick to step through the repos that have issues' if repo else 'No repos yet')
        if self.wsize == 'Tiny':
            self.issue_rows_shown = everything[:PIP_MAX]
            self.show_pic(K_IPIPS, paint_pips, [self.issue_color(r) for r in self.issue_rows_shown], max(0, len(everything) - PIP_MAX), ni, nw, C_BG)
            self.refresh_status()
            return
        large, n_rows = self.wsize == 'Large', int(cfg(K_ISSUE_ROWS))
        bg = C_BG2 if large else C_BG
        items = self.issue_rows_shown = everything[:n_rows]
        for i in range(n_rows):
            w[KT_IROW(i)].update(visible=i < len(items))
            if i >= len(items):
                continue
            rec = items[i]
            badge, fg, fill = self.issue_badge(rec)
            self.show_pic(KT_PIC(i, 'icon'), paint_issue_icon, rec['state'] == 'closed', 18 if large else 14, bg)
            w[KT_INAME(i)].update(shorten(f'#{rec["number"]}  {rec["title"]}', 54 if large else 40), text_color=C_TEXT if badge else C_MUTED)
            self.set_tip(KT_INAME(i), f'#{rec["number"]} {rec["title"]}\n{rec["state"]} · updated {local_str(parse_iso(rec["date"]))}')
            if badge:
                self.show_pic(KT_PIC(i, 'badge'), paint_pill, badge, fg, fill, bg, px(7.5))
            else:
                self.show_pic(KT_PIC(i, 'badge'), blank, 1, 17, bg)
            w[KT_IAGE(i)].update(age_short(parse_iso(rec['date'])))
            if large:
                self.show_pic(KT_PIC(i, 'meta'), paint_issue_meta, self.issue_meta_runs(rec), ISSUE_W, bg)
        w[K_IUNREAD].update(' · '.join(s for s in [f'{ni} new' if ni else '', f'{nw} waiting' if nw else ''] if s), text_color=C_BLUE if ni else C_AMBER)
        if large:
            news = sum(1 for r in everything if r['news'])
            waiting = sum(1 for r in everything if r['waiting'] and not r['news'])
            rest = sum(1 for r in everything if r['state'] == 'open' and not r['news'] and not r['waiting'])
            self.show_pic(K_IHEALTH, paint_health, [('with news', news, C_BLUE), ('more waiting on you' if news else 'waiting on you', waiting, C_AMBER),
                                                    ('quiet', rest, C_GREEN)], ISSUE_W, C_BG)
        self.refresh_status()

    def refresh_head(self):
        """Large: the line across the top - how many repos, and the news in all of them"""
        snaps = [self.snapshots.get(r) for r in self.repos()]
        nc = sum(self.unread_count(s) - self.issue_counts(s)[0] for s in snaps)
        ni = sum(self.issue_counts(s)[0] for s in snaps)
        nw = sum(self.issue_counts(s)[1] for s in snaps)
        parts = [f'watching {n_of(len(snaps), "repo")}']
        if self.snooze_until:
            parts.append('badges hidden')
        else:
            parts += [f'{nc} new' if nc else '', n_of(ni, 'issue') + ' with news' if ni else '', f'{nw} waiting' if nw else '']
        self.widget[K_HEAD].update(' · '.join(p for p in parts if p))

    def draw_spark(self, graph, per_day):
        graph.erase()
        w, h = graph.CanvasSize
        today = date.today()
        counts = [per_day.get((today - timedelta(days=i)).isoformat(), 0) for i in range(SPARK_DAYS - 1, -1, -1)]
        peak, bw = max(counts) or 1, w / SPARK_DAYS
        for i, c in enumerate(counts):
            top = max(2, round(c / peak * (h - 2))) if c else 1
            graph.draw_rectangle((i * bw + 1, top), ((i + 1) * bw - 1, 0), fill_color=C_ACCENT if c else C_DIM, line_color=C_ACCENT if c else C_DIM)

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
        text, color = ('DEMO · ' if DEMO else '') + text, C_RED if self.owner_errors else C_DIM
        if self.wsize == 'Tiny':                                # Tiny has room for a sign only - the words are in the ≡ tooltip
            sign = '!' if self.owner_errors else '⏸' if self.poller.paused else 'zz' if self.snooze_until else ''
            self.widget[K_STATUS].update(sign, text_color=C_RED if self.owner_errors else C_MUTED)
            self.set_tip(K_MENU, f'{text}\nMenu (or right-click) · Ctrl + mouse wheel changes the size')
            return
        if self.wsize == 'Small':                               # the short form; the whole line is its tooltip
            self.set_tip(K_STATUS, f'{text}\n{APP_NAME} {VERSION}')
            text = text if self.owner_errors else text.replace('checked ', '').split(' · API')[0]
        self.widget[K_STATUS].update(text, text_color=color)
        if self.wsize == 'Large' and self.view == VIEW_REPOS:
            self.refresh_head()

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
    def open_all_repos(self, spot=(None, None)):
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
                        **sbar(C_BG))
        layout = [[sg.Text(f'Watched repos · {len(repos)}', font=f['h1'], text_color=C_BLUE, pad=((6, 6), (6, 0))), sg.Push(background_color=C_BG),
                   sg.Text("click a repo to open What's new", font=f['small'], text_color=C_MUTED, pad=((0, 6), (14, 0)))],
                  [col],
                  [sg.Text('↑↓ PgUp PgDn Home End scroll · Esc closes', font=f['status'], text_color=C_DIM, pad=((6, 0), (6, 4))), sg.Push(background_color=C_BG),
                   sg.Button('Close', key=K_CLOSE, **self.btn(f)), sg.Sizegrip(background_color=C_BG)]]
        self.all_win = sg.Window(f'{APP_NAME} · watched repos', framed(f'{APP_NAME} · watched repos', layout, (4, 4)), no_titlebar=True, finalize=True, resizable=True,
                                 margins=(0, 0), background_color=C_BG, location=spot, **sbar())
        widget_map = {}
        for repo in repos:
            for w in descendants(self.all_win[KT_ALL_ROW(repo)].Widget):
                widget_map[w] = repo
        bind_click(self.all_win, widget_map)
        for seq, key in KEY_BINDS:
            self.all_win.bind(seq, key)
        dress(self.all_win, K_KEY_ESC)
        wheel_scrolls_list(self.all_win, K_ALL_LIST)

    def all_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC, K_STRIP_CLOSE):
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

    def open_picker(self, owner, repos, current_text, spot=(None, None)):
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
                        **sbar(C_BG))
        layout = [[sg.Text(f'{owner} · {n_of(len(repos), "repo")}', font=f['h1'], text_color=C_BLUE, pad=((6, 6), (6, 0))), sg.Push(background_color=C_BG),
                   sg.Text('tick the repos to watch · ticking every one watches the whole account (new repos included)', font=f['small'], text_color=C_MUTED,
                           pad=((0, 6), (14, 0)))],
                  [col],
                  [sg.Button('All', key=K_PICK_ALL, **self.btn(f)), sg.Button('None', key=K_PICK_NONE, **self.btn(f)),
                   sg.Button('Pushed in last 90 days', key=K_PICK_ACTIVE, **self.btn(f)), sg.Push(background_color=C_BG),
                   sg.Button('Use selected', key=K_PICK_OK, font=f['body'], button_color=(C_BG, C_GREEN), border_width=0, pad=((0, 6), (6, 0))),
                   sg.Button('Cancel', key=K_CANCEL, **self.btn(f))],
                  [sg.Text('↑↓ PgUp PgDn Home End scroll · Esc cancels', font=f['status'], text_color=C_DIM, pad=((6, 0), (6, 4))), sg.Push(background_color=C_BG),
                   sg.Sizegrip(background_color=C_BG)]]
        self.pick_win = sg.Window(f'Choose repos · {owner}', framed(f'Choose repos · {owner}', layout, (4, 4)), no_titlebar=True, finalize=True, keep_on_top=True,
                                  resizable=True, margins=(0, 0), background_color=C_BG, location=spot, **sbar())
        for seq, key in KEY_BINDS:
            self.pick_win.bind(seq, key)
        dress(self.pick_win, K_KEY_ESC)
        wheel_scrolls_list(self.pick_win, K_PICK_LIST)

    def pick_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CANCEL, K_KEY_ESC, K_STRIP_CLOSE):
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

    def open_details(self, repo, reopen=False, spot=(None, None)):
        snap = self.snapshots.get(repo)
        if not snap or not snap.get('ok'):
            msg = snap['error'] if snap else 'Still doing the first check - try again in a moment.'
            self.text_card(repo, f'{repo}\n\n{msg}', (60, 4))
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
                             **sbar(C_BG))
        detail = sg.Multiline(size=(pane_chars, 34), key=K_DETAIL, font=f['mono'], disabled=True, write_only=True, horizontal_scroll=True, background_color=C_BG2,
                              text_color=C_TEXT, border_width=0, expand_x=True, expand_y=True, pad=(0, 0), **sbar())
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
        layout = head + [[list_col, sg.VerticalSeparator(color=C_LINE), right]] + foot + [[sg.Push(background_color=C_BG), sg.Sizegrip(background_color=C_BG)]]
        self.details = sg.Window(f"{name} · What's new", framed(f"{name} · What's new", layout, (4, 4)), no_titlebar=True, finalize=True, resizable=True, margins=(0, 0),
                                 background_color=C_BG, location=spot, **sbar())
        self.details_repo, self.details_sig, self.selected, self.item_widgets = repo, self.signature(snap), None, {}
        for i in range(len(self.details_items)):
            for w in descendants(self.details[KT_ITEM(i)].Widget):
                self.item_widgets[w] = i
        bind_click(self.details, self.item_widgets)
        for seq, key in KEY_BINDS:
            self.details.bind(seq, key)
        dress(self.details, K_KEY_ESC)
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
            det = demo_commit_detail(sha, self.poller.commit_cache) if DEMO else fetch_commit_detail(self.poller.gh, repo, sha, self.poller.commit_cache)
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

    def open_issues(self, repo, reopen=False, number=None, spot=(None, None)):
        snap = self.snapshots.get(repo)
        if not snap or not snap.get('ok'):
            msg = snap['error'] if snap else 'Still doing the first check - try again in a moment.'
            self.text_card(repo, f'{repo}\n\n{msg}', (60, 4))
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
        btn = self.btn(f)
        digest = sg.Multiline(size=(150, 2), key=K_IS_DIGEST, font=f['body'], no_scrollbar=True, background_color=C_BG, pad=((8, 8), (2, 4)), **plain)
        fresh = sg.Text('New issue activity arrived while this was open · click Refresh to reload', key=K_IS_FRESH, font=f['small'], text_color=C_AMBER, visible=False)
        head = [[sg.Text(f'{name} · Issues', font=f['h1'], text_color=C_BLUE, pad=((8, 6), (6, 0))), sg.Text(f'by {owner}', font=f['small'], text_color=C_MUTED, pad=(0, (16, 0))),
                 sg.Push(background_color=C_BG), sg.Text(facts, font=f['small'], text_color=C_MUTED, pad=((0, 8), (16, 0)))],
                [digest],
                [fresh]]
        list_col = sg.Column(rows, scrollable=True, vertical_scroll_only=True, size=(list_w, list_h), key=K_IS_LIST, background_color=C_BG, expand_y=True, pad=(0, 0),
                             **sbar(C_BG))
        thread = sg.Multiline(size=(pane_chars, 34), key=K_IS_THREAD, font=f['body'], background_color=C_BG2, expand_y=True, pad=(0, 0), **plain, **sbar())
        reply = sg.Button('Reply on GitHub', key=K_IS_REPLY, font=f['small'], button_color=(C_BG, C_GREEN), border_width=0, pad=((0, 6), (6, 0)))
        right = sg.Column([[thread],
                           [reply, sg.Button('Copy link', key=K_IS_COPY, **btn), sg.Push(background_color=C_BG), sg.Text(ISSUES_HINT, font=f['status'], text_color=C_DIM)]],
                          expand_x=True, expand_y=True, pad=((8, 0), 0), background_color=C_BG)
        foot = [[sg.Button('Mark issues read', key=K_IS_READ, **btn), sg.Button('Refresh now', key=K_IS_REFRESH, **btn), sg.Button('All issues on GitHub', key=K_IS_ALL, **btn),
                 sg.Push(background_color=C_BG), sg.Button('Close', key=K_CLOSE, **btn), sg.Sizegrip(background_color=C_BG)]]
        layout = head + [[list_col, sg.VerticalSeparator(color=C_LINE), right]] + foot
        self.issues_win = sg.Window(f'{name} · Issues', framed(f'{name} · Issues', layout, (6, 4)), no_titlebar=True, finalize=True, resizable=True, margins=(0, 0),
                                    background_color=C_BG, location=spot, **sbar())
        self.issues_repo, self.issues_sig, self.issue_selected = repo, self.issue_signature(snap), None
        widget_map = {}
        for i in range(len(self.issue_items)):
            for w in descendants(self.issues_win[KT_IS_ITEM(i)].Widget):
                widget_map[w] = i
        bind_click(self.issues_win, widget_map)
        for seq, key in KEY_BINDS:
            self.issues_win.bind(seq, key)
        dress(self.issues_win, K_KEY_ESC)
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
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC, K_STRIP_CLOSE):
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
    def open_settings(self, values=None, spot=(None, None)):
        """The settings window.  values = what it showed before it was rebuilt in a new theme (None: the saved settings)"""
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
        self.settings_win = sg.Window(f'{APP_NAME} {VERSION} · Settings', framed(f'{APP_NAME} · Settings', layout, (12, 10)), no_titlebar=True, finalize=True,
                                      keep_on_top=True, margins=(0, 0), background_color=C_BG, location=spot, **sbar())
        dress(self.settings_win, K_CANCEL)
        for key, value in (values or {}).items():               # rebuilt in a new theme: put back what was showing
            try:
                self.settings_win[key].update(value)
            except Exception:
                pass

    def test_token_bg(self, token, repos, window):
        if DEMO:                                                # --demo never touches the network
            window.write_event_value(K_TEST_RESULT, 'demo - no token and no network: every repo answers OK')
            return
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
                if update_tick(self.widget, False, self.update_busy(), (C_BG, C_TEXT, C_PANEL_DONE)):     # a newer version of this file (the UPDATE block)
                    self.rebuild_menus()                        # 'Restart - x.y.z is ready'
                if Update.restart:
                    break
                continue
            if window is None or (window is self.widget and event in ('Exit', sg.WINDOW_CLOSED)):
                break
            if window in self.cards:                            # Version / About / messages
                if event in (sg.WIN_CLOSED, K_CLOSE, K_STRIP_CLOSE):
                    window.close()
                    self.cards.remove(window)
                continue
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
        for w in self.cards + [self.settings_win, self.pick_win, self.all_win]:
            if w is not None:
                w.close()
        self.widget.close()
        if Update.restart:
            self.poller.join(10)                                # done with its repo, so the fresh copy starts clean

    def update_busy(self):
        """Something of the widget is open - What's new, Issues, Settings (and its pickers), a Version / About card, the Brightness panel: no restart then"""
        return self.panel_open or bool(self.cards) or any(w is not None for w in (self.details, self.issues_win, self.settings_win, self.pick_win, self.all_win))

    def widget_event(self, event, values):
        item = values.get(K_MENU) if event == K_MENU else event
        item = item.split('::')[-1] if isinstance(item, str) and '::' in item else item       # a ≡ menu choice arrives as its whole 'label::key'
        if update_event(item):                                  # Restart, or a New versions choice (the UPDATE block)
            if Update.restart:
                return False                                    # the main loop ends; main() starts the fresh copy
            self.rebuild_menus()                                # the ✓ moved
            return True
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
            if isinstance(target, tuple) and target[0] == K_OPEN_ISSUES:
                if target[1]:
                    self.open_issues(target[1])
                return True
            if isinstance(target, tuple) and target[0] == K_ORB:  # Tiny: an orb showing only issue news opens the Issues window, the rest What's new
                repo = target[1]
                target = KT_ICHIP(repo) if repo != QUIET_ROW and not self.row_facts(repo)['nc'] else repo
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
        elif item == K_M_CHECK:
            self.poller.wake.set()
        elif item == K_M_VIEW:
            self.switch_view()
        elif item == K_M_READ:
            for repo in self.repos():
                self.mark_read(repo, sync=False)
            self.sync_widget()
        elif item == K_M_PAUSE:
            self.poller.paused = not self.poller.paused
            self.poller.wake.set()
            self.refresh_status()
            self.rebuild_menus()                                # the ✓ beside Pause polling
        elif item in SNOOZES:
            tomorrow = datetime.combine(date.today() + timedelta(days=1), datetime.min.time()).replace(hour=7)
            until = {'-M SNOOZE 1-': datetime.now() + timedelta(hours=1), '-M SNOOZE 4-': datetime.now() + timedelta(hours=4), '-M SNOOZE TOMORROW-': tomorrow,
                     '-M SNOOZE OFF-': None}
            self.snooze_until = until[item]
            self.sync_widget()
        elif item in SNAP_KEYS:
            self.snap_to(SNAP_KEYS[item])
        elif item == K_M_SETTINGS:
            self.open_settings()
        elif item == K_STARTUP:
            error = set_startup(not startup_on(), ICON)
            if error:
                sg.popup_error(f'Start with Windows did not work:\n{error}', title=APP_NAME, keep_on_top=True, non_blocking=True)
            self.rebuild_menus()
        elif item == K_M_TOP:
            self.set_keep_on_top(not cfg(K_KEEP_ON_TOP))
        elif item in SIZE_KEYS:
            self.set_size(SIZE_KEYS[item])
        elif item == K_SIZE_STEP:
            self.set_size(self.size_after(values[event]))
        elif isinstance(item, str) and item.startswith(K_THEME):
            G.theme = item[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            self.retheme()
        elif isinstance(item, str) and item.startswith(K_ACCENT):
            if choose_accent(self.widget, item, C_ACCENT):
                apply_theme()                                   # C_ACCENT: the new accent as drawn on this card
                for repo in self.visible_rows:                  # the commit charts drawn again in it
                    self.refresh_row(repo)
                self.rebuild_menus()                            # the ✓ in the Accent menu
        elif item == K_BRIGHT:
            while True:
                self.panel_open = True
                try:
                    pending = brightness_panel(self.widget, self.keep_going)
                finally:
                    self.panel_open = False
                if not pending or pending[0] != K_SIZE_STEP:
                    break
                self.widget_event(*pending)                     # Ctrl + mouse wheel over the widget: the new size, then the panel again under it
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            self.retheme()
            if pending:                                         # the widget event that closed the panel (a menu choice, the x...)
                return self.widget_event(*pending)
        elif item == K_M_LOG:
            path = os.path.join(os.path.dirname(sg.user_settings_filename()), LOG_FILE_NAME)
            if not os.path.exists(path):
                log('log created')
            os.startfile(path) if hasattr(os, 'startfile') else webbrowser.open('file://' + path)
        elif item == K_M_ABOUT:
            self.text_card(f'{APP_NAME} - about', f'{APP_NAME} {VERSION}\n\n{__doc__.strip()}', (140, 30))
        elif item == 'Version':
            self.text_card(f'{APP_NAME} - version', '\n'.join([f'{APP_NAME} {VERSION}', __file__,
                                                                               f'Start with Windows:  {startup_link() if startup_on() else "off"}',
                                                                               f'New versions:  {dict(UPDATE_CHOICES)[update_mode()]}', sg.get_versions()]), (70, 10))
        elif item == 'Edit Me':
            sg.execute_editor(__file__)
        elif item in ('Exit', K_CLOSE_X):                       # Exit from either menu, or the ✕
            return False
        return True

    def details_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC, K_STRIP_CLOSE):
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
        if event in (sg.WIN_CLOSED, K_CANCEL, K_STRIP_CLOSE):
            self.settings_win.close()
            self.settings_win = None
        elif event == K_OPACITY:
            self.widget.set_alpha(int(values[K_OPACITY]) / 100)
            self.current_alpha = int(values[K_OPACITY]) / 100
        elif event == K_TEST:
            self.settings_win[K_TEST_RESULT].update('testing…')
            token = '' if DEMO else values[K_TOKEN].strip() or resolve_token()
            threading.Thread(target=self.test_token_bg, args=(token, parse_entries(values[K_REPOS]), self.settings_win), daemon=True).start()
        elif event == K_TEST_RESULT:
            self.settings_win[K_TEST_RESULT].update(values[event])
        elif event == K_PICK:
            token = '' if DEMO else values[K_TOKEN].strip() or resolve_token()
            default = next((e for e in parse_entries(values[K_REPOS]) if '/' not in e), '') or ('PySimpleGUI' if DEMO else GitHub(token).login())
            owner = ask_text('Choose repos', 'Account (user or organization) whose repos to list:', default)
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
    Update.default = 'auto'                                     # a desktop widget: a newer version restarts it by itself (it comes back as it was)
    sg.user_settings_filename(filename=DEMO_SETTINGS_FILE if DEMO else SETTINGS_FILE)
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    G.accent = load_accent()
    sg.set_options(dpi_awareness=True, font=(UI_FONT, 11), tooltip_font=(UI_FONT, 10), icon=ICON)
    apply_theme()
    try:
        App().run()
    except Exception as e:
        log(traceback.format_exc())
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())
    if Update.restart:                                          # Restart, or a newer version: every window is closed and the poller stopped by now
        restart_self()


if __name__ == '__main__':
    main()
