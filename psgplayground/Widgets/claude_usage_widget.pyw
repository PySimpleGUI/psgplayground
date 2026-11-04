#!/usr/bin/env python3
"""
claude_usage_widget.pyw  -  A small always-on-top widget showing how much of your Claude plan you've used.

THE WIDGET
    Claude  Max (20x)                              ● dot: green ok · amber warn · red near limit · blue checking · grey no data
      Session      ▓▓▓░░░░░░░░░   9%   in 4h 51m   bar: % of that limit used · the thin grey tick is where you'd be at an even pace
      All models   ▓▓░░░░░░░░░░   8%   Mon 3 PM
      Fable        ▓▓▓▓░░░░░░░░  16%   Mon 3 PM
      Credits      ▓▓▓░░░░░░░░░  31%   $103.50 left    the month's usage credits against your monthly limit (green bar)
                   $46.50 of $150.00 spent · about $13.20/day
      [ graph ]    % over time for one limit (0-100 on the Y axis), solid = what happened, dashed = where your current rate leads
      ⚠ Session runs out ~7:40 PM - 1h 23m before its reset
    Click it          ->  Detail window: every limit with its own history graph + forecast, reset time, spend, raw JSON.

THE FORECAST
    Rate = least-squares slope of the recent checks (last 90 min for the session limit, last 24 h for weekly ones); when there aren't
    enough checks yet it falls back to the average rate since the window started.  From that: when 100% would arrive, and whether
    that's before or after the reset.  A finite monthly spend limit gets the same treatment in $/day.
    ≡ or right-click  ->  Refresh · Detail · Pause · Keep on top · Snap to corner · Settings · Sign in · Edit Me · Version · Exit
    Drag it anywhere; its position is remembered.

WHERE THE NUMBERS COME FROM
    The same undocumented endpoint Claude Code's /usage uses:  GET https://api.anthropic.com/api/oauth/usage
    Two ways to authenticate, chosen in Settings:
      Claude Code   - reads the access token Claude Code already has (%USERPROFILE%\\.claude\\.credentials.json, macOS Keychain,
                      or $CLAUDE_CODE_OAUTH_TOKEN).  Strictly read-only: it never refreshes or rewrites that file, so it can
                      never log Claude Code out.  If the token has expired, run any Claude Code command to refresh it.
      Own sign-in   - this widget does its own OAuth (PKCE) login and keeps its own token pair, refreshing it independently.
                      Menu -> Sign in, open the URL, approve, paste the code back.  Nothing to do with Claude Code's token.

    python claude_usage_widget.pyw --demo      made-up numbers, no token, no network (handy for trying the UI)

    Anthropic rate-limits this endpoint hard if you hammer it - keep the poll interval at 5 minutes or more.

Needs only PySimpleGUI - everything else is stdlib.  Settings and history live in claude_usage_widget.json in PySimpleGUI's
user-settings folder; problems are logged to claude_usage_widget.log in the same folder.

CHANGELOG
    1.6.6  03-Nov-2026   Credits get a bar row like the limits - % of the monthly limit, $ left, $ spent and $/day - and count in the
                         forecast line ("Credits reach the $150 limit ~Nov 11").  Detail window: a Credits graph + forecast, and this week's
                         use by app (Cowork / Claude Code / Chats).  Credits can be the widget's graph.  The usage response no longer gives
                         a reset date for credits, so the 1st of next month is used (Claude's settings page shows 'Resets <month> 1')
    1.6.5  01-Nov-2026   Keep on top can be turned off - right-click / ≡ menu (✓ when on) or Settings; remembered between runs
"""
import base64
import ctypes
import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
import tkinter as tk
import traceback
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone

import PySimpleGUI as sg

APP_NAME = 'Claude Usage'
VERSION = '1.6.6'
SETTINGS_FILE = 'claude_usage_widget.json'
LOG_FILE_NAME = 'claude_usage_widget.log'
DEMO = '--demo' in sys.argv
ICON = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAHlElEQVR4nO1bW4wcRxU991Z198zs2qwjxzyU/DjgxSZCdkwUhSDW+UH2B/kA9QbzEAIhjOCHSNgBIWWyPBRICFh8RNgSCQ+B8IyE5S8UKZZthMGKFEfEsTdrO46jBFux4/gxOzvT3VV1+ZgeP3bn4d3ZnRkre6TS7qq7au89VXXrVHVdoAUEoH35ES0CavVev0JuwvamDyWfZxobc/W/3/7xw3daqOFqYu5VTNo4gHm+TZ47nAM0M7IevQL2Jg4emzoxWixaAJAwVJT+Ph0NCZBCqGi0aHd8e723cfmqzRb0NRF5INCc9ZWq1ZJW9PUAUvthnGAqThwRjiqiP1+Kqn9c+/Tuc81ImOHCvvyIfnDsgDm2dfSeAV8/k/H0fbG1qCQWzjkHkJtep89ARFCBVsh5GuXYnDHGPfKxJ/9WmD6qMZ0AyY9oGjtgjm4Nv7kk8LYz8ZLJKDZERAIw9Veft4LUABd4SvtKoRwn24d/uesRKYQKo0VH6Zi56lB9iBzbFn59KJP5QzlOYJxYJqieutIhRMSBSG4fyKjzpeqOjz+16zv1KQ4AjHrAKxbtaz/60iez2numEifOOOdudedRmw8MAb9briTLcv6W8W2j36DRopUwVOlzwD2W59M47UeVyn8GA29tKTK3fM9PhwjEU+yIUHWMdXf99K8n8fjjxO6xvKaxMVetVr9wWy6zthQlpqHzRADxLVJmhioiUGytDPjegIntD4lI9gNMhTBU4Zo1MlEZ3zsYeCOTsXGE6QQQxCYQa3BtDexH1GwjYpDnz3gqAtGKIE7eE86tXvXEc+8SABzPf+UOjuxJgfjW1di62iQxbHUSQ/dvxNL1n4U4B+qZAmqzCIkDiBGdOY1ze34P8gJAbuwsEdihrK8uV+IvDj+56+8aABCZNRlP+5NRIkR0o3dEEGPgf/AO5O66e/59WgBwkK11VOPRKsQkxFgHoEaAQNZ7WhEiY+srw40tMtzUJOxUCeIsiLsYH1PFKc5BBQGIqfkMdA5QDHPpQvP2CGStIwjuAQANACTkNRtc4ixUZgAXD/4Dl17c27lDswQRwUUxBlfeiQ9v2gAY0zDIASkBmQDxqZcBaTNNBT7qBIDaRDUiSBLDxdW5+jFnEDNMuQJ/aBhQDlKNmscgEcARsrcPpTu15m5J6rO+eUsIxDf/+nyBmEFapwGQ0uW4VTCk6XGvJWbn0Wxani+ILOj/7aMdfW+wSECvDeg1uh/VgDSYtXjcxVjTdQKIGWINxDV3krS34MGvjq4TYMslqKXLwNpr/IIIzOULIC8AqYVXnN0jIBVTyzd9GUP3fw7sBTPWcxEBxKE8fhjv7HkWLqrWRsMCojsEMMNVyhi8+z4s37i57etLP7UB5spFvLPnWbA/c1s7n+gKAQSCWIPcytWAuHRL3WR4OwchQnbl6toUWOA40NUYIMakJzbSXM4S1QKlMV2xqbs6oKWG7+DdDvC+F0KLBPTagF6jgyDYP3K2E8yJgH6Ts51gTgT0m5ztBLMjYK5y1utfEm6egE7kbBB0aObC4aYJ6Gc52wlmHQP6Uc52gtnrgD6Us53gfS+EFgnotQG9xiIBvTag11gkoNcG9BqLBPTagF5jkYBeG9BraABgotlv15xrem+vdkUt3Qs02gl2VFdqG7GGdQUkLTZp14HTRjhts+2JhYiA/QClI4eA+pEXc8NCWgPMKB3+Z3oshrnXBcBao3TyTSBOQANZwPeBYGahjA/4PkoTp1KSm8Olt2F1St2rxjqAWhxzigN5AaK3T+GtnT/Bsgc2gYNs2pHXVUtPhK7899+4/OJecCYHsaaDuhbkaUTn38Nbu5/HsrVrwJ5OyZlmLgFXJt7A5WMnwIHfeAQJRNUyH169SoAiOlJJrKV2MUEE5Acojx9Gefyl2rnAjKto6e1M58CZ3PzV9TTKb55B+fT/aqkbzSatuJYfVCVlTQEvA4DO5/O88iNn33jt9UsTOU+vriTWEbUgQgSczV1trRkovd05r3X99p/KqX4u2cR6ReBybCpOyb8AgD9/9qyiLTsTBj2X9TUJpH1OkHO1Is3LDAfmo279mL1FaeE8nMANBj5F1u5f9fNdr+8bGdG8fsdOIwJSNv7T5an4fEYrJYJ+T4yaExRBrHMA4ykBaMP3VggTQTAa8kef3n3OCL7rK0XMsNK/SQFzgogkQ9lAT0Zm++onCvsQhkyjRXstaSpNJDq6NfzNh5bkvn9+smoAUUS3wMFeG4hIclsu412sRIdWrXefKRaBsFB0RJBrBAC0Pz+iHhw7YI4/+vDvlmb8LaUogXXOAKSo1RLZn5DaVBZalstwuZocnIrMQ5/4dfEi0m88aCDHSPJ5orExd+LRzd8KPP5VoPkDpSiBsWJr+Sj9TQQJRABighoMPFgniK3b/sKF49u27HwpEQHRdbfjG6fOphmW41vD4Zzv/cA6eSjn6xVMBNNGYfUSglr+MCAoVZNYET8fi/nt8C8KLyCVEzQtNaBpbxbCUNWTj0/mv7rCt/bTiZF1Rty9DNK271KHBYoIntKvEHDEEg6t/NlfJnDNFzfrbC/J51kKYf9+2WyDQhiqQtja/v8Dz13VURvjRhAAAAAASUVORK5CYII='          # embedded window/taskbar icon (three usage bars) - also what launchers show

USAGE_URL = 'https://api.anthropic.com/api/oauth/usage'
PROFILE_URL = 'https://api.anthropic.com/api/oauth/profile'
AUTHORIZE_URL = 'https://claude.ai/oauth/authorize'
REDIRECT_URI = 'https://console.anthropic.com/oauth/code/callback'
TOKEN_URLS = ('https://platform.claude.com/v1/oauth/token', 'https://console.anthropic.com/v1/oauth/token')
OAUTH_CLIENT_ID = '9d1c250a-e61b-44d9-88ed-5944d1962f5e'         # Claude Code's public OAuth client id
OAUTH_SCOPES = 'user:profile'
BETA_HEADER = 'oauth-2025-04-20'
USER_AGENT = 'claude-code/2.0.31'                                # a claude-code UA is required or the endpoint hands out 429s
MAX_BARS = 6                                                     # limit rows built into the layout; extra buckets are ignored
HISTORY_KEEP = 3000                                              # samples kept in the settings file (~10 days at 5 min)
WINDOW_SECONDS = {'session': 5 * 3600, 'weekly_all': 7 * 86400, 'weekly_scoped': 7 * 86400}
RATE_LOOKBACK = {'session': 90 * 60, 'weekly_all': 24 * 3600, 'weekly_scoped': 24 * 3600, 'spend': 3 * 86400}   # how far back the slope is fitted
MIN_FIT_SECONDS = 15 * 60                                        # a slope needs checks spanning at least this long
GRAPH_CHOICES = ['Favorite model', 'Session', 'All models', 'Credits', 'Most urgent']

# ---------------------------------------------------------------- colors (GitHub dark palette, same as github_repo_watch) ----------------------------------------------------------------
C_BG, C_BG2, C_BG3, C_LINE = '#0d1117', '#161b22', '#21262d', '#30363d'
C_TEXT, C_MUTED, C_DIM = '#e6edf3', '#8b949e', '#484f58'
C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK = '#3fb950', '#f85149', '#d29922', '#58a6ff', '#bc8cff', '#f778ba'
C_SESSION, C_WEEKLY, C_MODEL, C_SPEND = C_BLUE, C_PURPLE, C_PINK, C_GREEN                     # one color per category, always next to its label
C_OK, C_WARN, C_CRIT, C_BUSY = C_GREEN, C_AMBER, C_RED, C_AMBER
KIND_COLOR = {'session': C_SESSION, 'weekly_all': C_WEEKLY, 'weekly_scoped': C_MODEL, 'spend': C_SPEND}
UI_FONT = 'Segoe UI' if sg.running_windows() else 'DejaVu Sans'
MONO_FONT = 'Consolas' if sg.running_windows() else 'DejaVu Sans Mono'
SYMBOL = {'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}

# ---------------------------------------------------------------- keys ----------------------------------------------------------------
K_TITLE = '-TITLE-'
K_PLAN = '-PLAN-'
K_DOT = '-DOT-'
K_MENU = '-MENU-'
K_CLOSE_X = '-CLOSE X-'
K_STATUS = '-STATUS-'
K_CLICK = '-CLICK-'
K_SPEND_ROW = '-SPEND ROW-'
K_SPEND_TEXT = '-SPEND TEXT-'
K_SPEND_LABEL = '-SPEND LABEL-'
K_SPEND_BAR = '-SPEND BAR-'
K_SPEND_PCT = '-SPEND PCT-'
K_SPEND_LEFT = '-SPEND LEFT-'
K_GRAPH_ROW = '-GRAPH ROW-'
K_GRAPH = '-GRAPH-'
K_GRAPH_NAME = '-GRAPH NAME-'
K_FORECAST = '-FORECAST-'
K_POLL_BUSY = '-POLL BUSY-'
K_POLL_RESULT = '-POLL RESULT-'                                  # value = snapshot dict from the poller thread
K_ROW = '-ROW-';              KT_ROW = lambda i: (K_ROW, i)
K_LABEL = '-LABEL-';          KT_LABEL = lambda i: (K_LABEL, i)
K_BAR = '-BAR-';              KT_BAR = lambda i: (K_BAR, i)
K_PCT = '-PCT-';              KT_PCT = lambda i: (K_PCT, i)
K_RESET = '-RESET-';          KT_RESET = lambda i: (K_RESET, i)
# detail window
K_D_ROW = '-D ROW-';          KT_D_ROW = lambda i: (K_D_ROW, i)
K_D_LABEL = '-D LABEL-';      KT_D_LABEL = lambda i: (K_D_LABEL, i)
K_D_PCT = '-D PCT-';          KT_D_PCT = lambda i: (K_D_PCT, i)
K_D_BAR = '-D BAR-';          KT_D_BAR = lambda i: (K_D_BAR, i)
K_D_META = '-D META-';        KT_D_META = lambda i: (K_D_META, i)
K_D_GRAPH = '-D GRAPH-';      KT_D_GRAPH = lambda i: (K_D_GRAPH, i)
K_D_CAST = '-D CAST-';        KT_D_CAST = lambda i: (K_D_CAST, i)
K_D_PANE = '-D PANE-'
K_D_HEAD = '-D HEAD-'
K_D_SPEND = '-D SPEND-'
K_D_CRED_PCT = '-D CRED PCT-'
K_D_CRED_BAR = '-D CRED BAR-'
K_D_CRED_GRAPH = '-D CRED GRAPH-'
K_D_CRED_CAST = '-D CRED CAST-'
K_D_BREAKDOWN = '-D BREAKDOWN-'
K_D_ACCOUNT = '-D ACCOUNT-'
K_REFRESH = '-REFRESH-'
K_RAW = '-RAW-'
K_COPY = '-COPY-'
K_CLOSE = '-CLOSE-'
K_KEY_UP = '-K UP-'
K_KEY_DOWN = '-K DOWN-'
K_KEY_PGUP = '-K PGUP-'
K_KEY_PGDN = '-K PGDN-'
K_KEY_HOME = '-K HOME-'
K_KEY_END = '-K END-'
K_KEY_LEFT = '-K LEFT-'
K_KEY_RIGHT = '-K RIGHT-'
K_KEY_ESC = '-K ESC-'
SCROLL_KEYS = (K_KEY_UP, K_KEY_DOWN, K_KEY_PGUP, K_KEY_PGDN, K_KEY_HOME, K_KEY_END, K_KEY_LEFT, K_KEY_RIGHT)
KEY_BINDS = (('<Up>', K_KEY_UP), ('<Down>', K_KEY_DOWN), ('<Prior>', K_KEY_PGUP), ('<Next>', K_KEY_PGDN), ('<Home>', K_KEY_HOME), ('<End>', K_KEY_END),
             ('<Left>', K_KEY_LEFT), ('<Right>', K_KEY_RIGHT), ('<Escape>', K_KEY_ESC))
KEYS_HINT = '↑↓ scroll a line · PgUp/PgDn a page · Home/End jump · ←→ sideways · Esc closes'
# sign-in window
K_URL = '-URL-'
K_OPEN_URL = '-OPEN URL-'
K_COPY_URL = '-COPY URL-'
K_CODE = '-CODE-'
K_FINISH = '-FINISH-'
K_SIGNIN_MSG = '-SIGNIN MSG-'
K_SIGNIN_DONE = '-SIGNIN DONE-'                                  # value = (token dict or None, message)
# settings window (string keys - these are also the names saved in the settings file)
K_AUTH_MODE = '-AUTH MODE-'
K_TOKEN = '-TOKEN-'
K_INTERVAL = '-INTERVAL-'
K_OPACITY = '-OPACITY-'
K_FONT_SIZE = '-FONT SIZE-'
K_WARN = '-WARN-'
K_CRIT = '-CRIT-'
K_SHOW_SPEND = '-SHOW SPEND-'
K_SHOW_PACE = '-SHOW PACE-'
K_SHOW_GRAPH = '-SHOW GRAPH-'
K_GRAPH_OF = '-GRAPH OF-'
K_FAVORITE = '-FAVORITE-'
K_KEEP_ON_TOP = '-KEEP ON TOP-'
K_SAVE = '-SAVE-'
K_CANCEL = '-CANCEL-'
K_OAUTH = '-OAUTH-'                                              # settings entry holding this widget's own token pair
K_HISTORY = '-HISTORY-'                                          # settings entry holding the recorded samples
# menu items ('Edit Me', 'Version' and 'Exit' are the standard right-click entries and keep their plain names)
M_REFRESH = 'Refresh now::-M REFRESH-'
M_DETAIL = 'Detail window::-M DETAIL-'
M_PAUSE = 'Pause / resume polling::-M PAUSE-'
M_SNAP_TL = 'Top left::-M SNAP TL-'
M_SNAP_TR = 'Top right::-M SNAP TR-'
M_SNAP_BL = 'Bottom left::-M SNAP BL-'
M_SNAP_BR = 'Bottom right::-M SNAP BR-'
M_SETTINGS = 'Settings...::-M SETTINGS-'
M_SIGN_IN = 'Sign in to Claude...::-M SIGN IN-'
M_LOG = 'Open log file::-M LOG-'
M_TOP = 'Keep on top::-M TOP-'                                # label gets a ✓ while it's on (show_keep_on_top)
MENU_SNAP = [M_SNAP_TL, M_SNAP_TR, M_SNAP_BL, M_SNAP_BR]
MENU = ['', [M_REFRESH, M_DETAIL, '---', M_PAUSE, M_TOP, 'Snap to corner', MENU_SNAP, '---', M_SETTINGS, M_SIGN_IN, M_LOG, '---', 'Edit Me', 'Version', 'Exit']]

AUTH_CLAUDE_CODE = 'Claude Code token (read-only)'
AUTH_OWN = "This widget's own sign-in"
AUTH_PASTED = 'Pasted token'
AUTH_MODES = [AUTH_CLAUDE_CODE, AUTH_OWN, AUTH_PASTED]
INTERVALS = ['1 min', '2 min', '5 min', '10 min', '15 min', '30 min', '60 min']
DEFAULTS = {K_AUTH_MODE: AUTH_CLAUDE_CODE, K_TOKEN: '', K_INTERVAL: '5 min', K_OPACITY: 94, K_FONT_SIZE: 11, K_WARN: 70, K_CRIT: 90,
            K_SHOW_SPEND: True, K_SHOW_PACE: True, K_SHOW_GRAPH: True, K_GRAPH_OF: 'Favorite model', K_FAVORITE: 'Fable', K_KEEP_ON_TOP: True}


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


def parse_iso(value):
    """resets_at comes back as an ISO string on most accounts and as epoch seconds on some - take either."""
    if value in (None, ''):
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), timezone.utc)
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except Exception:
        return None


def clock(dt):
    return dt.strftime('%I:%M %p').lstrip('0')


def span_text(seconds):
    """A length of time: '51m', '4h 51m', '2d 3h'."""
    s = max(0, int(seconds))
    d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
    if d:
        return f'{d}d {h}h'
    return f'{h}h {m:02d}m' if h else f'{m}m'


def until_text(dt):
    """How long until a limit resets."""
    return '' if dt is None else span_text((dt - utcnow()).total_seconds())


def reset_short(dt):
    """What goes in the widget's narrow last column: a countdown for anything today, a weekday + time beyond that."""
    if dt is None:
        return ''
    if (dt - utcnow()).total_seconds() < 12 * 3600:
        return 'in ' + until_text(dt)
    local = dt.astimezone()
    return f'{local:%a} ' + (clock(local) if local.minute else local.strftime('%I %p').lstrip('0'))


def reset_long(dt):
    if dt is None:
        return 'no reset time given'
    local = dt.astimezone()
    return f'resets {local:%a} {clock(local)} · in {until_text(dt)}'


def day_text(dt):
    """' · resets Oct 1' for the spend line, blank when there's no date."""
    if dt is None:
        return ''
    local = dt.astimezone()
    return f' · resets {local:%b} {local.day}'


def field_of(bucket):
    """Which key a bucket's samples are stored under in the history - per-model buckets each get their own series."""
    return 'scoped:' + (bucket['model'] or bucket['label']) if bucket['kind'] == 'weekly_scoped' else bucket['kind']


def favorites():
    return [x.strip().lower() for x in str(cfg(K_FAVORITE)).replace(',', '\n').splitlines() if x.strip()]


def is_favorite(bucket):
    name = (bucket['model'] or bucket['label']).lower()
    return any(fav in name for fav in favorites())


def when_text(dt):
    """'7:40 PM' if it's within 12 h, else 'Fri 6:15 AM'."""
    local = dt.astimezone()
    return clock(local) if abs((dt - utcnow()).total_seconds()) < 12 * 3600 else f'{local:%a} {clock(local)}'


def time_ticks(t0, t1):
    """(datetime, label) pairs for the X axis: hourly for a few hours, 6-hourly for a couple of days, daily for a week or two, weekly beyond."""
    span = (t1 - t0).total_seconds()
    step = 3600 if span <= 8 * 3600 else 6 * 3600 if span <= 60 * 3600 else 86400 if span <= 16 * 86400 else 7 * 86400
    local = t0.astimezone()
    first = local.replace(minute=0, second=0, microsecond=0)
    if step >= 86400:
        first = first.replace(hour=0)
    elif step == 6 * 3600:
        first = first.replace(hour=first.hour - first.hour % 6)
    while first < local:
        first += timedelta(seconds=step)
    out = []
    while first <= t1.astimezone():
        hour = first.strftime('%I %p').lstrip('0')
        out.append((first, f'{first:%b} {first.day}' if step > 86400 else f'{first:%a}' if step == 86400 else hour if step == 3600 else f'{first:%a} {hour}'))
        first += timedelta(seconds=step)
    return out


def dashed(graph, a, b, color, width=2, dash=6, gap=4):
    """Graph.draw_line has no dash option, so lay the dashes down by hand."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = (dx * dx + dy * dy) ** 0.5
    if length < 1:
        return
    ux, uy, pos = dx / length, dy / length, 0.0
    while pos < length:
        end = min(length, pos + dash)
        graph.draw_line((a[0] + ux * pos, a[1] + uy * pos), (a[0] + ux * end, a[1] + uy * end), color=color, width=width)
        pos = end + gap


def next_month_start():
    """Midnight on the 1st of next month, local time - when the monthly credit limit starts over.  The usage response stopped giving a reset date
       for credits (seen 3-Nov-2026); Claude's settings page has always said 'Resets <month> 1'."""
    first = (datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)).replace(day=1)
    return first.astimezone()                                   # local midnight, with that day's UTC offset (daylight saving)


def month_span(resets_at):
    """Seconds from the 1st of the month before resets_at to resets_at - the length of the credits' month"""
    end = resets_at.astimezone()
    start = (end.replace(tzinfo=None) - timedelta(days=1)).replace(day=1)        # naive local time, so a daylight-saving change in between is counted right
    return (end - start.astimezone()).total_seconds()


def span_of(bucket):
    """How long a limit's window is: the credits carry their month's length, the others come from WINDOW_SECONDS"""
    return bucket.get('span') or WINDOW_SECONDS.get(bucket['kind'])


def minor(obj):
    if not isinstance(obj, dict) or obj.get('amount_minor') is None:
        return None
    return obj['amount_minor'] / 10 ** obj.get('exponent', 2)


def money(obj):
    value = minor(obj)
    return None if value is None else f'{SYMBOL.get(obj.get("currency", "USD"), "")}{value:,.2f}'


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


def bind_click(window, widgets, target):
    """Fire K_CLICK when a press and release land on the same spot, so dragging the widget around doesn't count as a click."""
    pressed = {}

    def on_press(e):
        pressed['at'] = (e.x_root, e.y_root)

    def on_release(e):
        x0, y0 = pressed.get('at', (e.x_root, e.y_root))
        if e.widget in widgets and abs(e.x_root - x0) < 6 and abs(e.y_root - y0) < 6:
            window.write_event_value(K_CLICK, target)

    window.TKroot.bind('<ButtonPress-1>', on_press, add='+')
    window.TKroot.bind('<ButtonRelease-1>', on_release, add='+')


# ================================================================ tokens ================================================================
class UsageError(Exception):
    pass


def claude_config_dirs():
    home = os.path.expanduser('~')
    dirs = [os.environ['CLAUDE_CONFIG_DIR']] if os.environ.get('CLAUDE_CONFIG_DIR') else []
    dirs.append(os.path.join(home, '.claude'))
    try:
        dirs += [os.path.join(home, n) for n in os.listdir(home) if n.startswith('.claude') and os.path.isdir(os.path.join(home, n))]
    except Exception:
        pass
    return list(dict.fromkeys(dirs))


def parse_credentials(raw):
    oauth = (json.loads(raw) or {}).get('claudeAiOauth') or {}
    expires = float(oauth.get('expiresAt') or 0) / 1000
    return {'access_token': oauth.get('accessToken'), 'expires_at': expires, 'expired': bool(expires and utcnow().timestamp() > expires)}


def read_claude_code_token():
    """Claude Code's own token, read and never written.  Returns (token, where_from, error)."""
    env = os.environ.get('CLAUDE_CODE_OAUTH_TOKEN', '').strip()
    if env:
        return env, 'CLAUDE_CODE_OAUTH_TOKEN', ''
    expired_seen = False
    for d in claude_config_dirs():
        path = os.path.join(d, '.credentials.json')
        try:
            with open(path, encoding='utf-8') as f:
                cred = parse_credentials(f.read())
        except Exception:
            continue
        if cred['access_token'] and not cred['expired']:
            return cred['access_token'], path, ''
        expired_seen = expired_seen or bool(cred['access_token'])
    if sys.platform == 'darwin':
        try:
            out = subprocess.run(['security', 'find-generic-password', '-s', 'Claude Code-credentials', '-w'], capture_output=True, text=True, timeout=8).stdout.strip()
            cred = parse_credentials(out)
            if cred['access_token'] and not cred['expired']:
                return cred['access_token'], 'macOS Keychain', ''
            expired_seen = expired_seen or bool(cred['access_token'])
        except Exception:
            pass
    if expired_seen:
        return '', '', "Claude Code's token has expired - run any Claude Code command to refresh it, or use Settings -> own sign-in"
    return '', '', 'No Claude Code credentials found - install/log in to Claude Code, or use Settings -> own sign-in'


def http_json(url, token=None, payload=None, timeout=25):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/plain, */*', 'User-Agent': USER_AGENT, 'anthropic-beta': BETA_HEADER}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method='POST' if data else 'GET')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = ''
        try:
            body = e.read().decode('utf-8')[:200]
        except Exception:
            pass
        if e.code == 401:
            raise UsageError('token rejected (401) - sign in again')
        if e.code == 429:
            raise UsageError('rate limited (429) - Anthropic throttles this endpoint for a while; poll less often')
        raise UsageError(f'HTTP {e.code} {body}'.strip())
    except urllib.error.URLError as e:
        raise UsageError(f'network problem: {getattr(e, "reason", e)}')
    except Exception as e:
        raise UsageError(f'{type(e).__name__}: {e}')


def token_post(payload):
    last = None
    for url in TOKEN_URLS:
        try:
            return http_json(url, payload=payload)
        except UsageError as e:
            last = e
    raise last


def own_tokens():
    return sg.user_settings_get_entry(K_OAUTH, {}) or {}


def save_own_tokens(tokens):
    sg.user_settings_set_entry(K_OAUTH, tokens)


def refresh_own_token():
    """Refresh this widget's own token pair.  Never touches Claude Code's credentials file."""
    tokens = own_tokens()
    if not tokens.get('refresh_token'):
        raise UsageError('not signed in - use the menu: Sign in to Claude...')
    data = token_post({'grant_type': 'refresh_token', 'refresh_token': tokens['refresh_token'], 'client_id': OAUTH_CLIENT_ID})
    if 'access_token' not in data:
        raise UsageError('refresh failed - sign in again')
    tokens = {'access_token': data['access_token'], 'refresh_token': data.get('refresh_token', tokens['refresh_token']), 'expires_at': utcnow().timestamp() + data.get('expires_in', 3600)}
    save_own_tokens(tokens)
    return tokens


def add_close_x(window, event_key):
    """A faint ✕ overlaid in the window's top-right corner - brightens under the pointer, closes the widget when clicked."""
    label = tk.Label(window.TKroot, text='✕', font=(UI_FONT, 9), fg=C_DIM, bg=C_BG, bd=0, cursor='hand2')
    label.place(relx=1.0, x=-3, y=1, anchor='ne')
    label.bind('<Enter>', lambda e: label.config(fg=C_CRIT))
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


def resolve_token():
    """The access token to use right now, plus a short description of where it came from."""
    mode = cfg(K_AUTH_MODE)
    if mode == AUTH_PASTED:
        token = str(cfg(K_TOKEN)).strip()
        if not token:
            raise UsageError('no token pasted - see Settings')
        return token, 'pasted token'
    if mode == AUTH_OWN:
        tokens = own_tokens()
        if not tokens.get('access_token'):
            raise UsageError('not signed in - use the menu: Sign in to Claude...')
        if utcnow().timestamp() > float(tokens.get('expires_at', 0)) - 60:
            tokens = refresh_own_token()
        return tokens['access_token'], 'own sign-in'
    token, where, error = read_claude_code_token()
    if not token:
        raise UsageError(error)
    return token, where


def pkce_pair():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=')
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    return verifier, challenge


def authorize_url(challenge, state):
    params = {'code': 'true', 'client_id': OAUTH_CLIENT_ID, 'response_type': 'code', 'redirect_uri': REDIRECT_URI, 'scope': OAUTH_SCOPES,
              'code_challenge': challenge, 'code_challenge_method': 'S256', 'state': state}
    return AUTHORIZE_URL + '?' + urllib.parse.urlencode(params)


def exchange_code(raw_code, verifier, state):
    code, _, code_state = raw_code.strip().partition('#')
    data = token_post({'grant_type': 'authorization_code', 'code': code, 'state': code_state or state, 'client_id': OAUTH_CLIENT_ID,
                       'redirect_uri': REDIRECT_URI, 'code_verifier': verifier})
    if 'access_token' not in data:
        raise UsageError('the code was not accepted - try signing in again')
    return {'access_token': data['access_token'], 'refresh_token': data.get('refresh_token', ''), 'expires_at': utcnow().timestamp() + data.get('expires_in', 3600)}


# ================================================================ usage data ================================================================
def plan_label(raw_plan):
    """'default_claude_max_20x' -> 'Max 20x'.  Anything unrecognised is title-cased and shown as-is."""
    text = str(raw_plan or '').replace('default_', '').replace('claude_', '').replace('_', ' ').strip()
    for name in ('enterprise', 'team', 'max', 'pro', 'free'):
        if name in text.lower():
            rest = text.lower().replace(name, '').strip()
            return (name.capitalize() + (' ' + rest if rest else '')).strip()
    return text.title()


def label_for(entry):
    kind, scope = entry.get('kind'), entry.get('scope') or {}
    model, surface = (scope.get('model') or {}).get('display_name'), scope.get('surface')
    name = {'session': 'Session', 'weekly_all': 'All models'}.get(kind) or model or str(kind).replace('_', ' ').title()
    if kind == 'weekly_scoped' and model:
        name = model
    return name + (f' ({surface})' if surface else ''), model, surface


def parse_usage(raw):
    """Turn the endpoint's payload into the buckets the widget draws.  limits[] is the live source; the flat keys are the fallback."""
    buckets = []
    for entry in raw.get('limits') or []:
        if not isinstance(entry, dict) or not entry.get('kind') or entry.get('percent') is None:
            continue
        label, model, surface = label_for(entry)
        buckets.append({'label': label, 'kind': entry['kind'], 'model': model, 'surface': surface, 'percent': float(entry['percent']), 'resets_at': parse_iso(entry.get('resets_at')),
                        'severity': entry.get('severity') or '', 'is_active': entry.get('is_active'), 'group': entry.get('group') or ''})
    if not buckets:
        for key, kind, label in (('five_hour', 'session', 'Session'), ('seven_day', 'weekly_all', 'All models'), ('seven_day_sonnet', 'weekly_scoped', 'Sonnet')):
            node = raw.get(key) or {}
            if node.get('utilization') is not None:
                buckets.append({'label': label, 'kind': kind, 'model': None, 'surface': None, 'percent': float(node['utilization']), 'resets_at': parse_iso(node.get('resets_at')),
                                'severity': '', 'is_active': True, 'group': ''})
    order = {'session': 0, 'weekly_all': 1, 'weekly_scoped': 2}
    buckets.sort(key=lambda b: (0 if b['kind'] == 'weekly_scoped' and is_favorite(b) else 1, order.get(b['kind'], 3), -b['percent']))   # favorites (e.g. Fable 5 / 5.1) on top
    spend = None
    extra, sp = raw.get('extra_usage') or {}, raw.get('spend') or {}
    if sp.get('enabled'):
        spend = {'used': money(sp.get('used')), 'limit': money(sp.get('limit')) or 'Unlimited', 'percent': sp.get('percent'),
                 'resets_at': parse_iso(sp.get('resets_at')) or next_month_start(), 'used_num': minor(sp.get('used')), 'limit_num': minor(sp.get('limit')),
                 'symbol': SYMBOL.get((sp.get('used') or {}).get('currency', 'USD'), ''), 'balance': money(sp.get('balance')), 'severity': sp.get('severity') or ''}
    elif extra.get('is_enabled'):
        div = 10 ** extra.get('decimal_places', 2)
        used, cap = extra.get('used_credits'), extra.get('monthly_limit')
        spend = {'used': f'${used / div:,.2f}' if used is not None else None, 'limit': f'${cap / div:,.2f}' if cap is not None else 'Unlimited',
                 'percent': extra.get('utilization'), 'resets_at': parse_iso(extra.get('resets_at')) or next_month_start(), 'used_num': used / div if used is not None else None,
                 'limit_num': cap / div if cap is not None else None, 'symbol': '$', 'balance': None, 'severity': ''}
    account = raw.get('account') or {}
    plan = account.get('subscription_level') or raw.get('rate_limit_tier') or raw.get('subscription_type') or ''
    rows = (raw.get('seven_day_breakdown') or {}).get('rows') or []
    breakdown = sorted(((r.get('display_name') or r.get('key') or '?', r['percent']) for r in rows if isinstance(r, dict) and (r.get('percent') or 0) > 0),
                       key=lambda x: -x[1])                       # this week's use by app: Cowork / Claude Code / Chats / Other
    return {'buckets': buckets[:MAX_BARS], 'spend': spend, 'plan': plan_label(plan), 'account': account, 'raw': raw, 'at': utcnow(), 'breakdown': breakdown}


def demo_snapshot():
    now = utcnow()
    monday = now + timedelta(days=(0 - now.weekday()) % 7 or 7)
    weekly = monday.replace(hour=19, minute=0, second=0, microsecond=0)
    raw = {'limits': [{'kind': 'session', 'percent': 41, 'resets_at': (now + timedelta(hours=3, minutes=5)).isoformat(), 'severity': 'normal', 'is_active': True, 'group': 'session'},
                      {'kind': 'weekly_all', 'percent': 8, 'resets_at': weekly.isoformat(), 'severity': 'normal', 'is_active': True, 'group': 'weekly'},
                      {'kind': 'weekly_scoped', 'percent': 16, 'resets_at': weekly.isoformat(), 'severity': 'normal', 'is_active': True, 'group': 'weekly',
                       'scope': {'model': {'display_name': 'Fable 5'}}},
                      {'kind': 'weekly_scoped', 'percent': 7, 'resets_at': weekly.isoformat(), 'severity': 'normal', 'is_active': True, 'group': 'weekly',
                       'scope': {'model': {'display_name': 'Fable 5.1'}}}],
           'spend': {'enabled': True, 'percent': 31, 'used': {'amount_minor': 4650, 'currency': 'USD', 'exponent': 2},
                     'limit': {'amount_minor': 15000, 'currency': 'USD', 'exponent': 2}, 'severity': 'normal', 'balance': None},
           'seven_day_breakdown': {'rows': [{'key': 'claude_code', 'display_name': 'Claude Code', 'percent': 64}, {'key': 'chat', 'display_name': 'Chats', 'percent': 21},
                                            {'key': 'cowork', 'display_name': 'Cowork', 'percent': 15}, {'key': 'other', 'display_name': 'Other', 'percent': 0}]},
           'account': {'email': 'you@example.com', 'subscription_level': 'max_20x', 'display_name': 'Demo account'}}
    snap = parse_usage(raw)
    snap['source'] = 'demo data'
    return snap


def demo_history():
    """Three days of made-up checks so --demo has history to graph: the session window began 1h55m ago and is climbing at ~22 %/h."""
    now, out = utcnow(), []
    for i in range(3 * 24 * 12, 0, -1):
        t = now - timedelta(minutes=5 * i)
        ago_h = i / 12
        if ago_h <= 115 / 60:
            session = 41 * (1 - ago_h / (115 / 60)) ** 1.15
        else:
            k = (ago_h - 115 / 60) % 5
            session = 0 if k < 1.5 else min(88.0, (k - 1.5) * 26)
        out.append({'t': t.isoformat(), 'session': round(session, 1), 'weekly_all': round(max(0.0, 8 - ago_h * 0.09), 1), 'scoped:Fable 5': round(max(0.0, 16 - ago_h * 0.2), 1),
                    'scoped:Fable 5.1': round(max(0.0, 7 - ago_h * 0.24), 1), 'spend': round(max(0.0, 46.5 - 0.55 * (ago_h // 4) * 4), 2)})   # credits go up in steps
    return out


# ================================================================ background poller ================================================================
class Poller(threading.Thread):
    def __init__(self, window):
        super().__init__(daemon=True)
        self.window, self.quit, self.wake = window, threading.Event(), threading.Event()
        self.interval, self.paused, self.next_check = 300, False, None

    def run(self):
        while not self.quit.is_set():
            if not self.paused:
                self.poll()
            self.next_check = None if self.paused else datetime.now() + timedelta(seconds=self.interval)
            self.wake.wait(self.interval if not self.paused else 3600)
            self.wake.clear()

    def poll(self):
        self.window.write_event_value(K_POLL_BUSY, True)
        try:
            if DEMO:
                snap = demo_snapshot()
            else:
                token, where = resolve_token()
                snap = parse_usage(http_json(USAGE_URL, token=token))
                snap['source'] = where
            snap['ok'], snap['error'] = True, ''
        except UsageError as e:
            snap = {'ok': False, 'error': str(e), 'at': utcnow(), 'buckets': [], 'spend': None, 'plan': '', 'account': {}, 'raw': {}, 'source': ''}
            log(f'poll failed: {e}')
        except Exception as e:
            snap = {'ok': False, 'error': f'{type(e).__name__}: {e}', 'at': utcnow(), 'buckets': [], 'spend': None, 'plan': '', 'account': {}, 'raw': {}, 'source': ''}
            log('poll crashed: ' + traceback.format_exc())
        self.window.write_event_value(K_POLL_RESULT, snap)


# ================================================================ the app ================================================================
class App:
    def __init__(self):
        self.scale = dpi_scale()
        self.snap, self.busy, self.detail, self.settings_win, self.signin_win, self.snap_pending = None, False, None, None, None, ''
        self.pkce, self.current_alpha, self.last_redraw = ('', '', ''), None, datetime.now()
        self.history = [h for h in (sg.user_settings_get_entry(K_HISTORY, []) or []) if isinstance(h, dict)]
        if DEMO and len(self.history) < 5:
            self.history = demo_history()
        self.build_widget()
        self.poller = Poller(self.widget)
        self.poller.interval = max(60, int(str(cfg(K_INTERVAL)).split()[0]) * 60)
        self.poller.start()

    # ---------------------------------------------------------------- look ----------------------------------------------------------------
    def fonts(self):
        fs = int(cfg(K_FONT_SIZE))
        return {'name': (UI_FONT, fs + 1, 'bold'), 'body': (UI_FONT, fs), 'bold': (UI_FONT, fs, 'bold'), 'small': (UI_FONT, max(fs - 2, 9)), 'dot': (UI_FONT, fs + 2),
                'h1': (UI_FONT, fs + 6, 'bold'), 'h2': (UI_FONT, fs + 2, 'bold'), 'big': (UI_FONT, fs + 4, 'bold'), 'mono': (MONO_FONT, max(fs - 1, 9))}

    def level_color(self, pct):
        if pct is None:
            return C_DIM
        return C_CRIT if pct >= int(cfg(K_CRIT)) else C_WARN if pct >= int(cfg(K_WARN)) else C_OK

    def level_word(self, pct):
        if pct is None:
            return 'no data'
        return 'near limit' if pct >= int(cfg(K_CRIT)) else 'getting high' if pct >= int(cfg(K_WARN)) else 'plenty left'

    def pace(self, bucket):
        """How far through this limit's window we are, 0-100 - the even-pace mark the bar's grey tick shows."""
        span = span_of(bucket)
        if not span or not bucket['resets_at'] or not cfg(K_SHOW_PACE):
            return None
        left = (bucket['resets_at'] - utcnow()).total_seconds()
        return max(0.0, min(100.0, (span - left) / span * 100))

    def projection(self, bucket):
        p = self.pace(bucket)
        if not p or p < 5 or bucket['percent'] <= 0:
            return ''
        return f'on pace for {min(999, round(bucket["percent"] / p * 100))}% by reset'

    def draw_bar(self, graph, pct, color, pace=None):
        graph.erase()
        w, h = graph.CanvasSize
        graph.draw_rectangle((0, h), (w, 0), fill_color=C_BG3, line_color=C_BG3)
        fill = max(0.0, min(100.0, pct or 0)) / 100 * w
        if fill >= 1:
            graph.draw_rectangle((0, h), (fill, 0), fill_color=color, line_color=color)
        if pace is not None:
            x = max(1, min(w - 1, pace / 100 * w))
            graph.draw_line((x, h), (x, 0), color=C_TEXT if abs(x - fill) > 2 else C_BG, width=1)

    # ---------------------------------------------------------------- widget window ----------------------------------------------------------------
    def build_widget(self):
        f, bar = self.fonts(), (int(150 * self.scale), int(10 * self.scale))
        rows = [[sg.Text('●', font=f['dot'], text_color=C_DIM, key=K_DOT, pad=((8, 4), (4, 0)), tooltip='Green ok · amber getting high or checking · red near limit / problem'),
                 sg.Text('Claude', font=f['name'], text_color=C_TEXT, key=K_TITLE, pad=((0, 6), (4, 0))),
                 sg.Text('', font=f['small'], text_color=C_MUTED, key=K_PLAN, pad=((0, 8), (6, 0))),
                 sg.Text('v' + VERSION, font=f['small'], text_color=C_DIM, pad=((0, 16), (6, 0)), tooltip=__file__)]]
        for i in range(MAX_BARS):
            row = [sg.Text('', size=(12, 1), font=f['body'], key=KT_LABEL(i), pad=((10, 6), 1)),
                   sg.Graph(bar, (0, 0), bar, background_color=C_BG3, key=KT_BAR(i), pad=((0, 6), 1)),
                   sg.Text('', size=(4, 1), font=f['bold'], justification='r', key=KT_PCT(i), pad=(0, 1)),
                   sg.Text('', size=(10, 1), font=f['small'], text_color=C_MUTED, key=KT_RESET(i), pad=((6, 8), 1))]
            rows.append([sg.Column([row], key=KT_ROW(i), pad=0, visible=False, background_color=C_BG)])
        rows.append([sg.Column([[sg.Text('Credits', size=(12, 1), font=f['body'], text_color=C_SPEND, key=K_SPEND_LABEL, pad=((10, 6), 1)),
                                 sg.Graph(bar, (0, 0), bar, background_color=C_BG3, key=K_SPEND_BAR, pad=((0, 6), 1)),
                                 sg.Text('', size=(4, 1), font=f['bold'], justification='r', key=K_SPEND_PCT, pad=(0, 1)),
                                 sg.Text('', size=(10, 1), font=f['small'], text_color=C_MUTED, key=K_SPEND_LEFT, pad=((6, 8), 1))],
                                [sg.Text('', font=f['small'], text_color=C_MUTED, key=K_SPEND_TEXT, pad=((10, 8), (0, 3)))]],
                               key=K_SPEND_ROW, pad=0, visible=False, background_color=C_BG)])
        graph_size = (int(280 * self.scale), int(46 * self.scale))
        rows.append([sg.Column([[sg.Text('', size=(12, 1), font=f['small'], key=K_GRAPH_NAME, pad=((10, 6), 1)),
                                 sg.Graph(graph_size, (0, 0), graph_size, background_color=C_BG, key=K_GRAPH, pad=((0, 8), (3, 2)), tooltip='Solid: checks so far · dashed: at the current rate · dotted line: the reset')]],
                               key=K_GRAPH_ROW, pad=0, visible=False, background_color=C_BG)])
        rows.append([sg.Text('', font=f['small'], text_color=C_DIM, key=K_FORECAST, pad=((10, 8), (0, 2)))])
        rows.append([sg.Text('starting…', font=f['small'], text_color=C_DIM, key=K_STATUS, pad=((10, 0), (0, 3))), sg.Push(background_color=C_BG),
                     sg.ButtonMenu('≡', MENU, key=K_MENU, font=f['name'], button_color=(C_MUTED, C_BG), border_width=0, pad=((0, 6), (0, 2)), tooltip='Menu (or right-click anywhere)')])
        self.widget = sg.Window(APP_NAME, rows, no_titlebar=True, keep_on_top=bool(cfg(K_KEEP_ON_TOP)), grab_anywhere=True, alpha_channel=int(cfg(K_OPACITY)) / 100, auto_save_location=True,
                                right_click_menu=MENU, right_click_menu_background_color=C_BG2, right_click_menu_text_color=C_TEXT, right_click_menu_selected_colors=(C_TEXT, C_BG3),
                                margins=(2, 2), background_color=C_BG, finalize=True)
        self.current_alpha = int(cfg(K_OPACITY)) / 100
        bind_click(self.widget, set(descendants(self.widget.TKroot)) - {self.widget[K_MENU].Widget}, 'widget')
        add_close_x(self.widget, K_CLOSE_X)                 # added after the click map, so clicking it can't also open the detail window
        show_keep_on_top(self.widget, bool(cfg(K_KEEP_ON_TOP)))
        self.snap_pending = 'TR' if sg.user_settings_get_entry('-LAST WINDOW LOCATION-' + APP_NAME) is None else ''
        if self.snap_pending:
            self.snap_to(self.snap_pending)

    def snap_to(self, corner):
        sw, sh = self.widget.get_screen_size()
        self.widget.refresh()
        ww, wh = self.widget.size
        m = int(12 * self.scale)
        self.widget.move(m if 'L' in corner else sw - ww - m, m if 'T' in corner else sh - wh - int(60 * self.scale))

    def set_keep_on_top(self, on):
        sg.user_settings_set_entry(K_KEEP_ON_TOP, on)
        self.widget.keep_on_top_set() if on else self.widget.keep_on_top_clear()
        show_keep_on_top(self.widget, on)

    def refresh_widget(self):
        snap, f = self.snap, self.fonts()
        buckets = snap['buckets'] if snap and snap.get('ok') else []
        cb = self.credit_bucket() if cfg(K_SHOW_SPEND) else None
        worst = max([b['percent'] for b in buckets] + ([cb['percent']] if cb else []), default=None)
        self.widget[K_DOT].update(text_color=C_BUSY if self.busy else C_CRIT if snap and not snap.get('ok') else self.level_color(worst))
        self.widget[K_PLAN].update(snap['plan'] if snap and snap.get('ok') and snap['plan'] else ('demo' if DEMO else ''))
        for i in range(MAX_BARS):
            self.widget[KT_ROW(i)].update(visible=i < len(buckets))
            if i >= len(buckets):
                continue
            b = buckets[i]
            color = KIND_COLOR.get(b['kind'], C_WEEKLY)
            self.widget[KT_LABEL(i)].update(b['label'], text_color=color)
            self.widget[KT_PCT(i)].update(f'{round(b["percent"])}%', text_color=self.level_color(b['percent']))
            self.widget[KT_RESET(i)].update(reset_short(b['resets_at']))
            self.draw_bar(self.widget[KT_BAR(i)], b['percent'], color, self.pace(b))
            tip = f'{b["label"]} · {round(b["percent"])}% used ({self.level_word(b["percent"])}) · {reset_long(b["resets_at"])}'
            self.widget[KT_LABEL(i)].set_tooltip(tip + (' · ' + self.projection(b) if self.projection(b) else ''))
        spend = snap.get('spend') if snap and snap.get('ok') else None
        self.widget[K_SPEND_ROW].update(visible=bool(spend) and bool(cfg(K_SHOW_SPEND)))
        if spend:
            fc = self.forecast(cb) if cb else None
            self.widget[K_SPEND_BAR].update(visible=bool(cb))
            self.widget[K_SPEND_PCT].update(visible=bool(cb))
            if cb:
                left = max(0.0, spend['limit_num'] - spend['used_num'])
                self.draw_bar(self.widget[K_SPEND_BAR], cb['percent'], C_SPEND, self.pace(cb))
                self.widget[K_SPEND_PCT].update(f'{round(cb["percent"])}%', text_color=self.level_color(cb['percent']))
                self.widget[K_SPEND_LEFT].update(f'{spend["symbol"]}{left:,.2f} left', text_color=C_CRIT if left <= 0 else C_MUTED)
            else:
                self.widget[K_SPEND_LEFT].update('no limit', text_color=C_MUTED)
            self.widget[K_SPEND_TEXT].update(self.spend_line(spend, fc))
            tip = self.credit_forecast_text(cb, fc) if cb else (self.spend_forecast_text(spend) or 'the spending rate appears after a few checks')
            self.widget[K_SPEND_LABEL].set_tooltip(tip)
            self.widget[K_SPEND_TEXT].set_tooltip(tip)
        self.refresh_forecast()
        if self.snap_pending and buckets:                       # the first snap happened while the rows were still hidden, so the window was narrower
            self.snap_to(self.snap_pending)
            self.snap_pending = ''
        self.refresh_status()

    def refresh_forecast(self):
        """The widget's small graph and its one-line verdict: the first limit that would run out before its reset, or all-clear."""
        buckets = self.snap['buckets'] if self.snap and self.snap.get('ok') else []
        shown = self.widget_bucket()
        self.widget[K_GRAPH_ROW].update(visible=bool(shown) and bool(cfg(K_SHOW_GRAPH)))
        if shown and cfg(K_SHOW_GRAPH):
            self.widget[K_GRAPH_NAME].update(shown['label'], text_color=KIND_COLOR.get(shown['kind'], C_WEEKLY))
            self.draw_graph(self.widget[K_GRAPH], shown, full=False)
        if not buckets:
            self.widget[K_FORECAST].update('')
            return
        cb = self.credit_bucket() if cfg(K_SHOW_SPEND) else None
        casts = [(b, self.forecast(b)) for b in buckets + ([cb] if cb else [])]
        danger = [(b, fc) for b, fc in casts if fc['runs_out'] and fc['hit']]
        if danger:
            b, fc = min(danger, key=lambda x: x[1]['hit'])
            self.widget[K_FORECAST].update('⚠ ' + self.forecast_text(b, fc, short=True), text_color=C_CRIT if (fc['hit'] - utcnow()).total_seconds() < 3600 else C_WARN)
        elif any(fc['rate'] is not None for _, fc in casts):
            worst = max((fc['at_reset'] or 0 for _, fc in casts), default=0)
            self.widget[K_FORECAST].update(f'at this rate nothing runs out before its reset (worst: {round(worst)}%)', text_color=C_OK)
        else:
            self.widget[K_FORECAST].update('forecast after a few more checks', text_color=C_DIM)

    def refresh_status(self):
        snap = self.snap
        if snap and not snap.get('ok'):
            self.widget[K_STATUS].update(snap['error'][:64], text_color=C_CRIT)
            self.widget[K_STATUS].set_tooltip(snap['error'])
            return
        if self.busy:
            text = 'checking…'
        elif self.poller.paused:
            text = 'paused'
        elif snap:
            nxt = self.poller.next_check
            text = f'checked {clock(snap["at"].astimezone())}' + (f' · next {clock(nxt)}' if nxt else '')
        else:
            text = 'first check…'
        self.widget[K_STATUS].update(('DEMO · ' if DEMO else '') + text, text_color=C_DIM)

    # ---------------------------------------------------------------- history ----------------------------------------------------------------
    def record(self, snap):
        sample = {'t': snap['at'].isoformat()}
        for b in snap['buckets']:
            sample[field_of(b)] = round(b['percent'], 2)
        if snap.get('spend') and snap['spend'].get('used_num') is not None:
            sample['spend'] = snap['spend']['used_num']
        self.history.append(sample)
        self.history = self.history[-HISTORY_KEEP:]
        if not DEMO:                                            # demo samples are made up - they never touch the settings file
            sg.user_settings_set_entry(K_HISTORY, self.history)

    def history_since(self, cutoff, field):
        """(time, value) pairs for one field, oldest first, from cutoff onwards."""
        out = []
        for h in self.history:
            if h.get(field) is None:
                continue
            t = parse_iso(h.get('t'))
            if t and t >= cutoff:
                out.append((t, float(h[field])))
        return out

    # ---------------------------------------------------------------- forecast ----------------------------------------------------------------
    def series(self, bucket):
        """This bucket's samples back to the start of its current window - and never past a reset we can see in the data."""
        span = span_of(bucket) or 86400
        start = utcnow() - timedelta(seconds=span)
        if bucket['resets_at']:
            start = max(start, bucket['resets_at'] - timedelta(seconds=span))
        pts = self.history_since(start, field_of(bucket))
        if bucket['kind'] == 'spend':                           # the history keeps dollars; graphs and forecasts work in % of the current limit
            pts = [(t, v / bucket['spend']['limit_num'] * 100) for t, v in pts]
        if not pts and bucket['kind'] == 'weekly_scoped':
            pts = self.history_since(start, 'scoped')           # samples recorded before per-model series existed
        for i in range(len(pts) - 1, 0, -1):
            if pts[i][1] < pts[i - 1][1] - 5:                   # a drop of more than 5 points is the window resetting
                return pts[i:]
        return pts

    @staticmethod
    def slope(pts):
        """Least-squares %/hour through (time, value) points; None when there's too little to go on."""
        if len(pts) < 3 or (pts[-1][0] - pts[0][0]).total_seconds() < MIN_FIT_SECONDS:
            return None
        xs = [(t - pts[0][0]).total_seconds() / 3600 for t, _ in pts]
        ys = [v for _, v in pts]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        den = sum((x - mx) ** 2 for x in xs)
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else None

    def forecast(self, bucket):
        """rate in %/h, when 100% arrives at that rate, and what the reset would find.  'runs_out' is the thing to worry about."""
        now, pct, resets = utcnow(), bucket['percent'], bucket['resets_at']
        pts = self.series(bucket)
        look = RATE_LOOKBACK.get(bucket['kind'], 3600)
        rate = self.slope([(t, v) for t, v in pts if (now - t).total_seconds() <= look])
        basis = f'slope of the last {span_text(look)}'
        if rate is None:
            pace, span = self.pace(bucket), span_of(bucket)
            if pace and pace >= 3 and span:
                rate, basis = pct / (pace / 100 * span / 3600), 'average since the window started'
        out = {'rate': rate, 'basis': basis, 'hit': None, 'runs_out': False, 'at_reset': None, 'points': pts}
        if rate is None or rate <= 0.05 or pct >= 100:
            return out
        out['hit'] = now + timedelta(hours=(100 - pct) / rate)
        if resets:
            out['at_reset'] = min(999.0, pct + rate * max(0.0, (resets - now).total_seconds() / 3600))
        out['runs_out'] = resets is None or out['hit'] < resets
        return out

    def forecast_text(self, bucket, fc, short=False):
        if bucket['kind'] == 'spend':
            return self.credit_forecast_text(bucket, fc, short)
        if fc['rate'] is None:
            return 'no rate yet - needs a few checks' if short else 'not enough checks yet to work out a rate'
        rate = f'{fc["rate"]:.1f}%/h' if fc['rate'] < 10 else f'{fc["rate"]:.0f}%/h'
        if fc['hit'] is None:
            return f'flat at {rate} - nothing to run out of' if short else f'{rate} - no measurable use lately, nothing to run out of'
        if fc['runs_out']:
            head = f'runs out ~{when_text(fc["hit"])} (in {until_text(fc["hit"])})'
            if bucket['resets_at'] and not short:
                head += f', {span_text((bucket["resets_at"] - fc["hit"]).total_seconds())} before the reset'
            return f'{bucket["label"]} {head}' if short else f'{head} at {rate} ({fc["basis"]})'
        reach = f'{round(fc["at_reset"])}% by the reset' if fc['at_reset'] is not None else '100% only after the reset'
        return f'{bucket["label"]} fine - {reach}' if short else f'reset comes first: {reach} at {rate} ({fc["basis"]})'

    def credit_bucket(self):
        """The usage credits as a bucket the bars, graphs and forecasts can use - only when there's a monthly limit to measure them against"""
        spend = self.snap.get('spend') if self.snap and self.snap.get('ok') else None
        if not spend or not spend.get('limit_num') or spend.get('used_num') is None:
            return None
        return {'label': 'Credits', 'kind': 'spend', 'model': None, 'surface': None, 'percent': spend['used_num'] / spend['limit_num'] * 100,
                'resets_at': spend['resets_at'], 'severity': spend.get('severity') or '', 'is_active': True, 'group': 'spend', 'span': month_span(spend['resets_at']),
                'spend': spend}

    def credit_forecast_text(self, bucket, fc, short=False):
        """The forecast in dollars: the rate per day, and whether the monthly limit is reached before the month starts over"""
        sp = bucket['spend']
        sym, limit, day = sp['symbol'], sp['limit_num'], f'{bucket["resets_at"].astimezone():%b} {bucket["resets_at"].astimezone().day}'
        if bucket['percent'] >= 100:
            return f'Credits: the {sym}{limit:,.0f} monthly limit is used up' if short else f'the {sym}{limit:,.2f} monthly limit is used up until {day}'
        if fc['rate'] is None:
            return 'Credits: no spending rate yet' if short else 'not enough checks yet to work out a spending rate'
        rate = f'about {sym}{fc["rate"] / 100 * limit * 24:,.2f}/day'
        fc = dict(fc, basis=fc['basis'].replace('average since the window started', "this month's average"))
        if fc['hit'] is None:
            return f'Credits fine - {rate}' if short else f'{rate} - hardly any spending lately, the limit is nowhere near'
        hit = f'{fc["hit"].astimezone():%b} {fc["hit"].astimezone().day}'
        if fc['runs_out']:
            if short:
                return f'Credits reach the {sym}{limit:,.0f} limit ~{hit} (in {until_text(fc["hit"])})'
            return f'the {sym}{limit:,.2f} limit is reached ~{hit} (in {until_text(fc["hit"])}), before the month starts over on {day} - {rate} ({fc["basis"]})'
        by_reset = min(fc['at_reset'], 100) / 100 * limit
        if short:
            return f'Credits fine - ~{sym}{by_reset:,.0f} of {sym}{limit:,.0f} by {day}'
        return f'the month ends first: ~{sym}{by_reset:,.2f} of the {sym}{limit:,.2f} limit spent by {day} - {rate} ({fc["basis"]})'

    def spend_line(self, spend, fc):
        """The small line under the Credits bar: what's been spent, and how fast"""
        sym = spend['symbol']
        text = f'{spend["used"] or "-"} of {spend["limit"]} spent' if spend.get('limit_num') else f'{spend["used"] or "-"} spent this month'
        if fc and fc['rate']:
            text += f' · about {sym}{fc["rate"] / 100 * spend["limit_num"] * 24:,.2f}/day'
        elif not spend.get('limit_num'):
            rate = self.spend_forecast_text(spend)
            text += f' · {rate}' if rate else ''
        return text + (f' · balance {spend["balance"]}' if spend.get('balance') else '')

    def spend_forecast_text(self, spend):
        """For a finite monthly limit: the $/day rate over the last few days and when the cap would be reached."""
        if not spend or spend.get('used_num') is None:
            return ''
        pts = self.history_since(utcnow() - timedelta(days=3), 'spend')
        if spend['resets_at']:
            pts = [(t, v) for t, v in pts if t >= spend['resets_at'] - timedelta(days=31)]
        for i in range(len(pts) - 1, 0, -1):
            if pts[i][1] < pts[i - 1][1] - 1:
                pts = pts[i:]
                break
        per_hour = self.slope(pts)
        if per_hour is None or per_hour <= 0:
            return ''
        text = f'about {spend["symbol"]}{per_hour * 24:,.2f}/day'
        if spend.get('limit_num') and spend['limit_num'] > spend['used_num']:
            hit = utcnow() + timedelta(hours=(spend['limit_num'] - spend['used_num']) / per_hour)
            if spend['resets_at'] and hit >= spend['resets_at']:
                text += f' - limit not reached before the reset (~{spend["symbol"]}{spend["used_num"] + per_hour * (spend["resets_at"] - utcnow()).total_seconds() / 3600:,.0f})'
            else:
                text += f' - limit reached ~{hit.astimezone():%b} {hit.astimezone().day} {clock(hit.astimezone())}'
        return text

    def widget_bucket(self):
        """Which limit the widget's small graph follows."""
        buckets = self.snap['buckets'] if self.snap and self.snap.get('ok') else []
        if not buckets:
            return None
        want, cb = cfg(K_GRAPH_OF), self.credit_bucket()
        if want == 'Credits':
            if cb:
                return cb
            want = 'Session'
        if want == 'Most urgent':
            urgent = [(fc['hit'], b) for b in buckets + ([cb] if cb else []) for fc in [self.forecast(b)] if fc['runs_out'] and fc['hit']]
            return min(urgent, key=lambda x: x[0])[1] if urgent else max(buckets, key=lambda b: b['percent'])
        if want in ('Favorite model', 'Per-model'):
            scoped = [b for b in buckets if b['kind'] == 'weekly_scoped']
            favs = [b for b in scoped if is_favorite(b)] or scoped
            if favs:
                return max(favs, key=lambda b: b['percent'])
            want = 'Session'
        kind = {'Session': 'session', 'All models': 'weekly_all'}.get(want, 'session')
        return next((b for b in buckets if b['kind'] == kind), buckets[0])

    # ---------------------------------------------------------------- the graph ----------------------------------------------------------------
    def draw_graph(self, graph, bucket, full):
        """% over time.  Solid = checks so far, dashed = where the current rate leads, vertical lines at now and at the reset.
        'full' adds axis labels; the widget's version keeps only what fits."""
        graph.erase()
        w, h = graph.CanvasSize
        now, fc = utcnow(), self.forecast(bucket)
        color, level = KIND_COLOR.get(bucket['kind'], C_WEEKLY), self.level_color(bucket['percent'])
        span, dollars = span_of(bucket) or 86400, bucket['kind'] == 'spend'
        t1 = bucket['resets_at'] or now + timedelta(seconds=span / 4)
        t0 = min(now - timedelta(seconds=span), fc['points'][0][0] if fc['points'] else now)
        if dollars:                                             # the credits' month, from the 1st to the day it starts over
            t0 = bucket['resets_at'] - timedelta(seconds=span)
        yl = (lambda v: f'{bucket["spend"]["symbol"]}{bucket["spend"]["limit_num"] * v / 100:,.0f}') if dollars else (lambda v: f'{v}%')
        left, bottom, top, right = (int((40 if dollars else 30) * self.scale), int(14 * self.scale), 4, 4) if full else (0, 0, 2, 2)
        pw, ph = w - left - right, h - bottom - top
        tx = lambda dt: left + (dt - t0).total_seconds() / max(1, (t1 - t0).total_seconds()) * pw
        ty = lambda v: bottom + max(0.0, min(100.0, v)) / 100 * ph
        small = (UI_FONT, 9)
        graph.draw_rectangle((left, ph + bottom), (left + pw, bottom), fill_color=C_BG3, line_color=C_BG3)
        for v in (25, 50, 75, 100):
            graph.draw_line((left, ty(v)), (left + pw, ty(v)), color=C_LINE if v < 100 else C_DIM, width=1)
            if full and v in (50, 100):
                graph.draw_text(yl(v), (left - 4, ty(v)) if dollars else (left - 14, ty(v)), color=C_MUTED, font=small,
                                text_location=sg.TEXT_LOCATION_RIGHT if dollars else sg.TEXT_LOCATION_CENTER)
        xn = tx(now)
        if full:
            graph.draw_text(yl(0), (left - 4, ty(0) + 5) if dollars else (left - 12, ty(0) + 5), color=C_MUTED, font=small,
                            text_location=sg.TEXT_LOCATION_RIGHT if dollars else sg.TEXT_LOCATION_CENTER)
            for tick, label in time_ticks(t0, t1):
                x = tx(tick)
                graph.draw_line((x, bottom), (x, bottom + 4), color=C_DIM, width=1)
                if abs(x - xn) > 40 * self.scale:                # leave room for the 'now' label on the axis
                    graph.draw_text(label, (x, bottom - 7), color=C_DIM, font=small)
            graph.draw_text('now', (xn, bottom - 7), color=C_TEXT, font=small)
        if bucket['resets_at']:
            x = tx(bucket['resets_at'])
            dashed(graph, (x, bottom), (x, bottom + ph), C_MUTED, width=1, dash=3, gap=3)
            if full:
                local = bucket['resets_at'].astimezone()
                graph.draw_text(f'resets {local:%b} {local.day}' if dollars else 'reset ' + clock(local), (x - 3, bottom + ph - 8), color=C_MUTED, font=small,
                                text_location=sg.TEXT_LOCATION_RIGHT)
        graph.draw_line((xn, bottom), (xn, bottom + ph), color=C_DIM, width=1)
        pts = [(tx(t), ty(v)) for t, v in fc['points']]
        for a, b in zip(pts, pts[1:]):
            graph.draw_line(a, b, color=color, width=2)
        if not pts:
            graph.draw_text('one point per check - collecting…', (left + pw / 2, bottom + ph / 2), color=C_DIM, font=small)
        last = (xn, ty(bucket['percent']))
        graph.draw_circle(last, 3, fill_color=color, line_color=color)
        if fc['hit'] is not None and fc['rate']:
            end_t = fc['hit'] if fc['hit'] <= t1 else t1
            end_v = 100.0 if fc['hit'] <= t1 else bucket['percent'] + fc['rate'] * (t1 - now).total_seconds() / 3600
            dashed(graph, last, (tx(end_t), ty(end_v)), level, width=2)
            if fc['runs_out'] and fc['hit'] <= t1:
                graph.draw_circle((tx(fc['hit']), ty(100)), 4, fill_color=C_CRIT, line_color=C_CRIT)
                if full:                                        # bottom-right corner: a line steep enough to hit 100% is never down there
                    hit = fc['hit'].astimezone()
                    graph.draw_text(f'{yl(100)} ~{hit:%b} {hit.day}' if dollars else f'100% ~{when_text(fc["hit"])}', (left + pw - 6, bottom + 9), color=C_CRIT,
                                    font=(UI_FONT, 9, 'bold'), text_location=sg.TEXT_LOCATION_RIGHT)


    # ---------------------------------------------------------------- detail window ----------------------------------------------------------------
    def open_detail(self):
        if self.detail is not None:
            self.detail.bring_to_front()
            return
        f, bar, chart = self.fonts(), (int(440 * self.scale), int(14 * self.scale)), (int(440 * self.scale), int(150 * self.scale))
        body = [[sg.Text('', font=f['h2'], text_color=C_TEXT, key=K_D_HEAD, pad=((0, 0), (0, 2)), background_color=C_BG2)],
                [sg.Text('', font=f['small'], text_color=C_MUTED, key=K_D_BREAKDOWN, pad=((0, 0), (0, 8)), background_color=C_BG2)]]
        for i in range(MAX_BARS):
            block = [[sg.Text('', font=f['bold'], key=KT_D_LABEL(i), pad=(0, 0), background_color=C_BG2), sg.Push(background_color=C_BG2),
                      sg.Text('', font=f['big'], key=KT_D_PCT(i), pad=(0, 0), background_color=C_BG2)],
                     [sg.Graph(bar, (0, 0), bar, background_color=C_BG3, key=KT_D_BAR(i), pad=(0, 3))],
                     [sg.Text('', font=f['small'], text_color=C_MUTED, size=(60, 2), key=KT_D_META(i), pad=((0, 0), (0, 2)), background_color=C_BG2)],
                     [sg.Graph(chart, (0, 0), chart, background_color=C_BG2, key=KT_D_GRAPH(i), pad=(0, 2))],
                     [sg.Text('', font=f['small'], text_color=C_MUTED, size=(60, 2), key=KT_D_CAST(i), pad=((0, 0), (0, 12)), background_color=C_BG2)]]
            body.append([sg.Column(block, key=KT_D_ROW(i), pad=0, visible=False, background_color=C_BG2, expand_x=True)])
        body.append([sg.Text('Usage credits', font=f['bold'], text_color=C_SPEND, pad=((0, 0), (6, 0)), background_color=C_BG2), sg.Push(background_color=C_BG2),
                     sg.Text('', font=f['big'], key=K_D_CRED_PCT, pad=(0, 0), background_color=C_BG2)])
        body.append([sg.Graph(bar, (0, 0), bar, background_color=C_BG3, key=K_D_CRED_BAR, pad=(0, 3))])
        body.append([sg.Text('', font=f['small'], text_color=C_MUTED, size=(60, 2), key=K_D_SPEND, pad=((0, 0), (0, 2)), background_color=C_BG2)])
        body.append([sg.Graph(chart, (0, 0), chart, background_color=C_BG2, key=K_D_CRED_GRAPH, pad=(0, 2))])
        body.append([sg.Text('', font=f['small'], text_color=C_MUTED, size=(60, 2), key=K_D_CRED_CAST, pad=((0, 0), (0, 12)), background_color=C_BG2)])
        body.append([sg.Text('Account', font=f['bold'], text_color=C_TEXT, pad=((0, 0), (6, 2)), background_color=C_BG2)])
        body.append([sg.Text('', font=f['small'], text_color=C_MUTED, key=K_D_ACCOUNT, pad=((0, 0), (0, 6)), background_color=C_BG2)])
        layout = [[sg.Column(body, key=K_D_PANE, scrollable=True, vertical_scroll_only=True, size=(int(560 * self.scale), int(640 * self.scale)), pad=((10, 4), (10, 4)),
                             background_color=C_BG2, expand_x=True, expand_y=True)],
                  [sg.Text(KEYS_HINT, font=f['small'], text_color=C_DIM, pad=((12, 0), (0, 4)))],
                  [sg.Button('Refresh', key=K_REFRESH, font=f['body']), sg.Button('Raw JSON', key=K_RAW, font=f['body']), sg.Button('Copy JSON', key=K_COPY, font=f['body']),
                   sg.Push(), sg.Button('Close', key=K_CLOSE, font=f['body'], pad=((0, 12), (0, 8)))]]
        self.detail = sg.Window(f'{APP_NAME} - detail', layout, keep_on_top=True, finalize=True, background_color=C_BG, resizable=True, margins=(0, 0))
        for seq, key in KEY_BINDS:
            self.detail.bind(seq, key)
        self.wire_detail_wheel()
        self.refresh_detail()

    def refresh_detail(self):
        if self.detail is None:
            return
        snap = self.snap
        if not snap or not snap.get('ok'):
            self.detail[K_D_HEAD].update(snap['error'] if snap else 'waiting for the first check…', text_color=C_CRIT if snap else C_MUTED)
            for i in range(MAX_BARS):
                self.detail[KT_D_ROW(i)].update(visible=False)
            return
        account = snap.get('account') or {}
        who = ' · '.join(x for x in [snap['plan'] or 'Claude', account.get('email') or account.get('display_name') or '', 'DEMO' if DEMO else ''] if x)
        self.detail[K_D_HEAD].update(who, text_color=C_TEXT)
        parts = ' · '.join(f'{name} {round(pct)}%' for name, pct in snap.get('breakdown') or [])
        self.detail[K_D_BREAKDOWN].update(f'This week\'s use by app: {parts}' if parts else '')
        for i in range(MAX_BARS):
            visible = i < len(snap['buckets'])
            self.detail[KT_D_ROW(i)].update(visible=visible)
            if not visible:
                continue
            b = snap['buckets'][i]
            color, pace = KIND_COLOR.get(b['kind'], C_WEEKLY), self.pace(b)
            self.detail[KT_D_LABEL(i)].update(b['label'], text_color=color)
            self.detail[KT_D_PCT(i)].update(f'{round(b["percent"])}%', text_color=self.level_color(b['percent']))
            self.draw_bar(self.detail[KT_D_BAR(i)], b['percent'], color, pace)
            bits = [self.level_word(b['percent']), reset_long(b['resets_at'])]
            if pace is not None:
                bits.append(f'even pace would be {round(pace)}%')
            if b['severity'] and b['severity'] != 'normal':
                bits.append('severity ' + str(b['severity']))
            self.detail[KT_D_META(i)].update(' · '.join(bits))
            fc = self.forecast(b)
            self.draw_graph(self.detail[KT_D_GRAPH(i)], b, full=True)
            self.detail[KT_D_CAST(i)].update(f'{b["label"]} forecast: ' + self.forecast_text(b, fc), text_color=C_CRIT if fc['runs_out'] else C_MUTED)
        spend, cb = snap.get('spend'), self.credit_bucket()
        for key in (K_D_CRED_BAR, K_D_CRED_GRAPH, K_D_CRED_CAST):
            self.detail[key].update(visible=bool(cb))
        self.detail[K_D_CRED_PCT].update(f'{round(cb["percent"])}%' if cb else '', text_color=self.level_color(cb['percent']) if cb else C_TEXT)
        if cb:
            fc, pace, sym = self.forecast(cb), self.pace(cb), spend['symbol']
            self.draw_bar(self.detail[K_D_CRED_BAR], cb['percent'], C_SPEND, pace)
            bits = [f'{spend["used"]} of the {spend["limit"]} monthly limit spent', f'{sym}{max(0.0, spend["limit_num"] - spend["used_num"]):,.2f} left',
                    f'resets{day_text(spend["resets_at"]).replace(" · resets", "")}']
            if pace is not None:
                bits.append(f'even pace would be {round(pace)}%')
            if spend.get('balance'):
                bits.append(f'balance {spend["balance"]}')
            self.detail[K_D_SPEND].update(' · '.join(bits))
            self.draw_graph(self.detail[K_D_CRED_GRAPH], cb, full=True)
            self.detail[K_D_CRED_CAST].update('Credits forecast: ' + self.credit_forecast_text(cb, fc), text_color=C_CRIT if fc['runs_out'] else C_MUTED)
        elif spend:
            self.detail[K_D_SPEND].update(self.spend_line(spend, None))
        else:
            self.detail[K_D_SPEND].update('usage credits are off for this account')
        self.detail[K_D_ACCOUNT].update(f'token source: {snap.get("source", "?")}\npolling every {cfg(K_INTERVAL)} · warn at {cfg(K_WARN)}% · near-limit at {cfg(K_CRIT)}%')
        self.detail.refresh()                               # let tk lay out the newly-visible rows, then retell the scrollable Column its size
        self.detail[K_D_PANE].contents_changed()            # otherwise the scrollregion stays at the hidden-skeleton size until the window is resized


    def wire_detail_wheel(self):
        """Make the wheel scroll the pane wherever the pointer is.  PySimpleGUI's scrollable Column hooks the wheel on the
        canvas's <Enter>/<Leave>, but the content frame is embedded IN the canvas, so hovering any element fires <Leave>
        and unbinds it - the wheel then only works on the bare strip right of the content.  Binding on the toplevel works
        everywhere because every widget's bindtags include its toplevel."""
        canvas = self.detail[K_D_PANE].Widget.canvas
        canvas.unbind('<Enter>')                                # retire the hover hook (it also bind_all's, which would double-scroll)
        canvas.unbind('<Leave>')

        def wheel(direction):
            if canvas.yview() != (0.0, 1.0):                    # nothing to scroll when the content fits
                canvas.yview_scroll(direction, 'units')
            return 'break'                                      # keep bind_all leftovers from scrolling it a second time

        self.detail.TKroot.bind('<MouseWheel>', lambda e: wheel(-1 if e.delta > 0 else 1))
        self.detail.TKroot.bind('<Button-4>', lambda e: wheel(-1))
        self.detail.TKroot.bind('<Button-5>', lambda e: wheel(1))

    def scroll(self, event):
        canvas = self.detail[K_D_PANE].Widget.canvas
        if event == K_KEY_UP:
            canvas.yview_scroll(-1, 'units')
        elif event == K_KEY_DOWN:
            canvas.yview_scroll(1, 'units')
        elif event == K_KEY_PGUP:
            canvas.yview_scroll(-1, 'pages')
        elif event == K_KEY_PGDN:
            canvas.yview_scroll(1, 'pages')
        elif event == K_KEY_HOME:
            canvas.yview_moveto(0)
        elif event == K_KEY_END:
            canvas.yview_moveto(1)
        elif event == K_KEY_LEFT:
            canvas.xview_scroll(-1, 'units')
        elif event == K_KEY_RIGHT:
            canvas.xview_scroll(1, 'units')

    def close_detail(self):
        if self.detail is not None:
            self.detail.close()
            self.detail = None

    # ---------------------------------------------------------------- sign-in window ----------------------------------------------------------------
    def open_signin(self):
        if self.signin_win is not None:
            self.signin_win.bring_to_front()
            return
        f = self.fonts()
        verifier, challenge = pkce_pair()
        state = secrets.token_urlsafe(32)
        self.pkce = (verifier, state, authorize_url(challenge, state))
        layout = [[sg.Text('Sign this widget in to Claude', font=f['h2'], pad=((10, 10), (10, 2)))],
                  [sg.Text('This creates a token that belongs to the widget alone - it never touches the one Claude Code uses.', font=f['small'], text_color=C_MUTED,
                           pad=((10, 10), (0, 8)))],
                  [sg.Text('1.  Open this URL and approve the request:', font=f['body'], pad=((10, 10), (4, 2)))],
                  [sg.Multiline(self.pkce[2], size=(70, 3), font=f['mono'], key=K_URL, no_scrollbar=True, pad=((10, 10), 2))],
                  [sg.Button('Open in browser', key=K_OPEN_URL, font=f['body'], pad=((10, 6), 4)), sg.Button('Copy URL', key=K_COPY_URL, font=f['body'], pad=(0, 4))],
                  [sg.Text('2.  Paste the code the callback page shows you:', font=f['body'], pad=((10, 10), (10, 2)))],
                  [sg.Input('', size=(60, 1), font=f['mono'], key=K_CODE, pad=((10, 10), 2)), sg.Button('Finish', key=K_FINISH, font=f['body'], bind_return_key=True)],
                  [sg.Text('', font=f['small'], text_color=C_MUTED, key=K_SIGNIN_MSG, size=(70, 2), pad=((10, 10), (6, 10)))]]
        self.signin_win = sg.Window(f'{APP_NAME} - sign in', layout, keep_on_top=True, finalize=True, background_color=C_BG, modal=False)

    def finish_signin_bg(self, code, window):
        try:
            tokens = exchange_code(code, self.pkce[0], self.pkce[1])
            save_own_tokens(tokens)
            sg.user_settings_set_entry(K_AUTH_MODE, AUTH_OWN)
            window.write_event_value(K_SIGNIN_DONE, (True, 'Signed in.  Fetching your usage…'))
        except Exception as e:
            window.write_event_value(K_SIGNIN_DONE, (False, str(e)))

    # ---------------------------------------------------------------- settings window ----------------------------------------------------------------
    def open_settings(self):
        if self.settings_win is not None:
            self.settings_win.bring_to_front()
            return
        f = self.fonts()
        token, where, error = ('', 'demo', '') if DEMO else read_claude_code_token()
        found = f'found: {where}' if token else (error or 'not found')
        layout = [[sg.Text('Where the token comes from', font=f['h2'], pad=((10, 10), (10, 4)))],
                  [sg.Combo(AUTH_MODES, default_value=cfg(K_AUTH_MODE), readonly=True, size=(30, 1), font=f['body'], key=K_AUTH_MODE, pad=((10, 10), 2)),
                   sg.Button('Sign in…', key=M_SIGN_IN, font=f['body'])],
                  [sg.Text(f'Claude Code credentials - {found}', font=f['small'], text_color=C_MUTED if token else C_WARN, size=(64, 2), pad=((10, 10), (0, 6)))],
                  [sg.Text('Pasted token (only used by the "Pasted token" mode)', font=f['small'], text_color=C_MUTED, pad=((10, 10), (4, 0)))],
                  [sg.Input(str(cfg(K_TOKEN)), size=(52, 1), font=f['mono'], password_char='•', key=K_TOKEN, pad=((10, 10), (0, 10)))],
                  [sg.Text('Widget', font=f['h2'], pad=((10, 10), (6, 4)))],
                  [sg.Text('Check every', size=(14, 1), font=f['body'], pad=((10, 4), 2)), sg.Combo(INTERVALS, default_value=cfg(K_INTERVAL), readonly=True, size=(10, 1),
                                                                                                    font=f['body'], key=K_INTERVAL),
                   sg.Text('5 min or more is kind to the endpoint', font=f['small'], text_color=C_MUTED)],
                  [sg.Text('Opacity', size=(14, 1), font=f['body'], pad=((10, 4), 2)), sg.Slider((40, 100), int(cfg(K_OPACITY)), orientation='h', size=(28, 14),
                                                                                                 enable_events=True, key=K_OPACITY, font=f['small'])],
                  [sg.Text('Font size', size=(14, 1), font=f['body'], pad=((10, 4), 2)), sg.Slider((8, 18), int(cfg(K_FONT_SIZE)), orientation='h', size=(28, 14),
                                                                                                   key=K_FONT_SIZE, font=f['small'])],
                  [sg.Text('Amber at', size=(14, 1), font=f['body'], text_color=C_WARN, pad=((10, 4), 2)), sg.Slider((10, 100), int(cfg(K_WARN)), orientation='h', size=(28, 14),
                                                                                                                     key=K_WARN, font=f['small'])],
                  [sg.Text('Red at', size=(14, 1), font=f['body'], text_color=C_CRIT, pad=((10, 4), 2)), sg.Slider((10, 100), int(cfg(K_CRIT)), orientation='h', size=(28, 14),
                                                                                                                   key=K_CRIT, font=f['small'])],
                  [sg.Checkbox('Show the usage-credits line', bool(cfg(K_SHOW_SPEND)), font=f['body'], key=K_SHOW_SPEND, pad=((10, 10), (8, 0)))],
                  [sg.Checkbox('Show the even-pace tick on each bar', bool(cfg(K_SHOW_PACE)), font=f['body'], key=K_SHOW_PACE, pad=((10, 10), (0, 0)))],
                  [sg.Checkbox('Keep the widget on top of other windows', bool(cfg(K_KEEP_ON_TOP)), font=f['body'], key=K_KEEP_ON_TOP, pad=((10, 10), (0, 0)))],
                  [sg.Checkbox('Show a graph in the widget of', bool(cfg(K_SHOW_GRAPH)), font=f['body'], key=K_SHOW_GRAPH, pad=((10, 4), (0, 0))),
                   sg.Combo(GRAPH_CHOICES, default_value=cfg(K_GRAPH_OF), readonly=True, size=(14, 1), font=f['body'], key=K_GRAPH_OF, pad=((0, 10), (0, 0)))],
                  [sg.Text('Favorite models', size=(14, 1), font=f['body'], text_color=C_MODEL, pad=((10, 4), 2)), sg.Input(str(cfg(K_FAVORITE)), size=(24, 1), font=f['body'], key=K_FAVORITE),
                   sg.Text('name matches, comma-separated - they sort to the top', font=f['small'], text_color=C_MUTED)],
                  [sg.Push(), sg.Button('Save', key=K_SAVE, font=f['body']), sg.Button('Cancel', key=K_CANCEL, font=f['body'], pad=((6, 12), (4, 10)))]]
        self.settings_win = sg.Window(f'{APP_NAME} - settings', layout, keep_on_top=True, finalize=True, background_color=C_BG)

    def save_settings(self, values):
        for key in (K_AUTH_MODE, K_TOKEN, K_INTERVAL, K_SHOW_SPEND, K_SHOW_PACE, K_SHOW_GRAPH, K_GRAPH_OF, K_FAVORITE, K_KEEP_ON_TOP):
            sg.user_settings_set_entry(key, values[key])
        for key in (K_OPACITY, K_FONT_SIZE, K_WARN, K_CRIT):
            sg.user_settings_set_entry(key, int(values[key]))
        if int(values[K_CRIT]) < int(values[K_WARN]):
            sg.user_settings_set_entry(K_CRIT, int(values[K_WARN]))
        self.settings_win.close()
        self.settings_win = None
        self.poller.interval = max(60, int(str(cfg(K_INTERVAL)).split()[0]) * 60)
        location = self.widget.current_location()
        self.close_detail()
        self.widget.close()
        self.build_widget()
        self.widget.move(*location)
        self.poller.window = self.widget
        self.refresh_widget()
        self.poller.wake.set()

    # ---------------------------------------------------------------- event loop ----------------------------------------------------------------
    def run(self):
        while True:
            window, event, values = sg.read_all_windows(timeout=1000)
            if event == sg.TIMEOUT_EVENT:
                self.tick()
                continue
            if window is None:
                break
            if window not in (self.widget, self.detail, self.settings_win, self.signin_win):
                if event == sg.WIN_CLOSED:
                    window.close()                      # a non-blocking popup's X: read_all_windows reports it but leaves the destroy to us
                continue
            if window is self.widget:
                if self.widget_event(event, values) is False:
                    break
            elif window is self.detail:
                self.detail_event(event)
            elif window is self.settings_win:
                self.settings_event(event, values)
            elif window is self.signin_win:
                self.signin_event(event, values)
        self.poller.quit.set()
        self.poller.wake.set()
        self.close_detail()
        for win in (self.settings_win, self.signin_win, self.widget):
            if win is not None:
                win.close()

    def tick(self):
        alpha = int(cfg(K_OPACITY)) / 100
        if alpha != self.current_alpha:
            self.widget.set_alpha(alpha)
            self.current_alpha = alpha
        if self.snap and self.snap.get('ok'):                   # keep the countdowns honest between polls
            for i, b in enumerate(self.snap['buckets']):
                self.widget[KT_RESET(i)].update(reset_short(b['resets_at']))
            if datetime.now().second < 1 or (datetime.now() - self.last_redraw).total_seconds() >= 60:
                self.last_redraw = datetime.now()
                self.refresh_forecast()
                self.refresh_detail()
        self.refresh_status()

    def widget_event(self, event, values):
        item = values.get(K_MENU) if event == K_MENU else event
        if item in ('Exit', sg.WINDOW_CLOSED, K_CLOSE_X):
            return False
        if event == K_POLL_BUSY:
            self.busy = True
            self.refresh_widget()
        elif event == K_POLL_RESULT:
            self.busy, self.snap = False, values[event]
            if self.snap.get('ok'):
                self.record(self.snap)
            self.refresh_widget()
            self.refresh_detail()
        elif event == K_CLICK or item == M_DETAIL:
            self.open_detail()
        elif item == M_REFRESH:
            self.poller.wake.set()
        elif item == M_PAUSE:
            self.poller.paused = not self.poller.paused
            self.poller.wake.set()
            self.refresh_status()
        elif item in MENU_SNAP:
            self.snap_to({M_SNAP_TL: 'TL', M_SNAP_TR: 'TR', M_SNAP_BL: 'BL', M_SNAP_BR: 'BR'}[item])
        elif item == M_SETTINGS:
            self.open_settings()
        elif item == M_SIGN_IN:
            self.open_signin()
        elif item == M_TOP:
            self.set_keep_on_top(not cfg(K_KEEP_ON_TOP))
        elif item == M_LOG:
            path = os.path.join(os.path.dirname(sg.user_settings_filename()), LOG_FILE_NAME)
            if not os.path.exists(path):
                log('log created')
            os.startfile(path) if hasattr(os, 'startfile') else webbrowser.open('file://' + path)
        elif item == 'Version':
            sg.popup_scrolled(f'{APP_NAME} {VERSION}', __file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif item == 'Edit Me':
            sg.execute_editor(__file__)
        return True

    def detail_event(self, event):
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC):
            self.close_detail()
        elif event in SCROLL_KEYS:
            self.scroll(event)
        elif event == K_REFRESH:
            self.poller.wake.set()
        elif event == K_RAW:
            sg.popup_scrolled(json.dumps(self.snap.get('raw', {}) if self.snap else {}, indent=2), title='Raw usage response', keep_on_top=True, size=(80, 30), font=(MONO_FONT, 10))
        elif event == K_COPY:
            sg.clipboard_set(json.dumps(self.snap.get('raw', {}) if self.snap else {}, indent=2))

    def settings_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CANCEL):
            self.settings_win.close()
            self.settings_win = None
        elif event == K_OPACITY:
            self.widget.set_alpha(int(values[K_OPACITY]) / 100)
            self.current_alpha = int(values[K_OPACITY]) / 100
        elif event == M_SIGN_IN:
            self.open_signin()
        elif event == K_SAVE:
            self.save_settings(values)

    def signin_event(self, event, values):
        if event == sg.WIN_CLOSED:
            self.signin_win.close()
            self.signin_win = None
        elif event == K_OPEN_URL:
            webbrowser.open(self.pkce[2])
        elif event == K_COPY_URL:
            sg.clipboard_set(self.pkce[2])
            self.signin_win[K_SIGNIN_MSG].update('URL copied.')
        elif event == K_FINISH:
            self.signin_win[K_SIGNIN_MSG].update('exchanging the code…')
            threading.Thread(target=self.finish_signin_bg, args=(values[K_CODE], self.signin_win), daemon=True).start()
        elif event == K_SIGNIN_DONE:
            ok, message = values[event]
            self.signin_win[K_SIGNIN_MSG].update(message, text_color=C_OK if ok else C_CRIT)
            if ok:
                self.signin_win.close()
                self.signin_win = None
                self.poller.wake.set()


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    sg.theme_add_new('ClaudeUsage', {'BACKGROUND': C_BG, 'TEXT': C_TEXT, 'INPUT': C_BG2, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_LINE, 'BUTTON': (C_TEXT, C_BG3),
                                     'PROGRESS': (C_SESSION, C_BG2), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
    sg.theme('ClaudeUsage')
    sg.set_options(dpi_awareness=True, font=(UI_FONT, 11), tooltip_font=(UI_FONT, 10), icon=ICON)
    try:
        App().run()
    except Exception:
        log(traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
