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
    ≡ or right-click  ->  Refresh · Detail · Pause · Keep on top · Theme · Brightness · Snap to corner · Settings · Sign in · Edit Me · Version · Exit
    Drag it anywhere; its position is remembered.  Esc closes it.  The other windows are moved by their title strip.

WHERE THE NUMBERS COME FROM
    The same undocumented endpoint Claude Code's /usage uses:  GET https://api.anthropic.com/api/oauth/usage
    Two ways to authenticate, chosen in Settings:
      Claude Code   - reads the access token Claude Code already has (%USERPROFILE%\\.claude\\.credentials.json, macOS Keychain,
                      or $CLAUDE_CODE_OAUTH_TOKEN).  Strictly read-only: it never refreshes or rewrites that file, so it can
                      never log Claude Code out.  If the token has expired, run any Claude Code command to refresh it.
      Own sign-in   - this widget does its own OAuth (PKCE) login and keeps its own token pair, refreshing it independently.
                      Menu -> Sign in, open the URL, approve, paste the code back.  Nothing to do with Claude Code's token.

    python claude_usage_widget.pyw --demo      made-up numbers, no token, no network (handy for trying the UI) - with its own settings file,
                                               claude_usage_widget_demo.json, so trying things never touches your real settings

    Anthropic rate-limits this endpoint hard if you hammer it - keep the poll interval at 5 minutes or more.

Needs PySimpleGUI and Pillow - everything else is stdlib.  Settings and history live in claude_usage_widget.json in PySimpleGUI's
user-settings folder; problems are logged to claude_usage_widget.log in the same folder.

CHANGELOG
    1.7.0  06-Nov-2026   The standard widget themes: right-click > Theme (32, as color chips) and Brightness...; every window themed with no OS title
                         bar (moved by its title strip, round corners on Windows 11); flat themed menus; Esc closes the widget; --demo has its own settings
    1.6.6  03-Nov-2026   Credits get a bar row like the limits - % of the monthly limit, $ left, $ spent and $/day - and count in the
                         forecast line ("Credits reach the $150 limit ~Nov 11").  Detail window: a Credits graph + forecast, and this week's
                         use by app (Cowork / Claude Code / Chats).  Credits can be the widget's graph.  The usage response no longer gives
                         a reset date for credits, so the 1st of next month is used (Claude's settings page shows 'Resets <month> 1')
    1.6.5  01-Nov-2026   Keep on top can be turned off - right-click / ≡ menu (✓ when on) or Settings; remembered between runs
"""
import base64
import ctypes
import hashlib
import io
import json
import math
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
from PIL import Image, ImageDraw, ImageFont

APP_NAME = 'Claude Usage'
VERSION = '1.7.0'
SETTINGS_FILE = 'claude_usage_widget.json'
DEMO_SETTINGS_FILE = 'claude_usage_widget_demo.json'             # --demo's own settings, so trying things never touches the real ones
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

# ---------------------------------------------------------------- colors ----------------------------------------------------------------
# The card, text and line colors come from the chosen theme (P() below).  These carry meaning - one per limit kind, ok / amber / red - and keep it on
# every theme: a light card draws them a shade darker (paint() for bars, dots and lines, ink() for text).
C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK = '#3fb950', '#f85149', '#d29922', '#58a6ff', '#bc8cff', '#f778ba'
C_SESSION, C_WEEKLY, C_MODEL, C_SPEND = C_BLUE, C_PURPLE, C_PINK, C_GREEN                     # one color per category, always next to its label
C_OK, C_WARN, C_CRIT, C_BUSY = C_GREEN, C_AMBER, C_RED, C_AMBER
KIND_COLOR = {'session': C_SESSION, 'weekly_all': C_WEEKLY, 'weekly_scoped': C_MODEL, 'spend': C_SPEND}
MEANING = {C_GREEN, C_RED, C_AMBER, C_BLUE, C_PURPLE, C_PINK}  # the colors paint() / ink() deepen on a light card
C_MENU_SEL = '#2a62a8'                                           # menu highlight, white text on it
C_CLOSE = '#c0392b'                                              # a close x under the mouse
C_SWATCH_EDGE = '#7c8594'                                        # outline of the color chips in the Theme menu
UI_FONT = 'Segoe UI' if sg.running_windows() else 'DejaVu Sans'
MONO_FONT = 'Consolas' if sg.running_windows() else 'DejaVu Sans Mono'
FONT_MENU = (UI_FONT, 10)
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # Pillow fonts (Brightness panel): Windows first, then Linux
TRANSPARENT = '#010203'                                          # Windows color key: the Brightness panel's rounded corners are see-through
RADIUS = 18                                                      # the Brightness panel's corner radius in design pixels - the windows get Windows 11's own round corners
DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND, DWMWA_BORDER_COLOR = 33, 2, 34                     # Windows 11: round a window's corners, color its outline
SYMBOL = {'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}

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
K_TITLE = '-TITLE-'
K_VERSION = '-VERSION-'
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
K_THEME = '-THEME-'                                              # settings entry for the theme, and the start of the Theme menu's keys
KT_THEME = lambda name: f'{K_THEME}{name}'
# every extra window (Detail, Settings, Sign in, Version, Raw JSON)
K_STRIP = '-STRIP-'                                              # the title strip - drag it to move the window
K_STRIP_CLOSE = '-STRIP CLOSE-'                                  # its x
# menu items: make_menu() puts the labels in front ('    Refresh now::-M REFRESH-'); the event is the key after '::'.  'Edit Me', 'Version' and 'Exit' keep
# their plain keys, as in sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT
K_M_REFRESH = '-M REFRESH-'
K_M_DETAIL = '-M DETAIL-'
K_M_PAUSE = '-M PAUSE-'
K_M_TOP = '-M TOP-'
K_M_SETTINGS = '-M SETTINGS-'
K_M_SIGN_IN = '-M SIGN IN-'
K_M_LOG = '-M LOG-'
KT_M_SNAP = lambda corner: f'-M SNAP {corner}-'
SNAP_CORNERS = {'TL': 'Top left', 'TR': 'Top right', 'BL': 'Bottom left', 'BR': 'Bottom right'}
SNAP_KEYS = {KT_M_SNAP(corner): corner for corner in SNAP_CORNERS}

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


# ================================================================ themes ================================================================
class G:
    """State the shared WIDGET THEMES / BRIGHTNESS blocks and the menus use"""
    theme = 'Toybox'                                             # the chosen theme (settings entry K_THEME)
    bright = 0                                                   # its Brightness level (K_BRIGHT)
    tuned = {}                                                   # (theme, level) -> its five colors at that level
    swatches = {}                                                # (theme, level) -> Theme menu chip - tk keeps an image only while someone holds it
    fonts = {}                                                   # (bold, px) -> Pillow font
    scale = 1.0                                                  # display scale, 2.0 on a 200% screen - the Brightness panel and the x are drawn at it
    window = None                                                # the widget window
    app = None                                                   # the App - redraw() recolors its widget


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


def P():
    """Every color the windows are drawn with: the theme at the Brightness setting (theme_colors) and what this program works out from it -
       pane = the Detail window's body, a touch lifted; faint = the faintest text; strip = title strips; input = text boxes"""
    t = theme_colors()
    light = is_light(t['card'])
    return dict(t, light=light, pane=mix(t['card'], t['text'], 0.04), faint=mix(t['dim'], t['card'], 0.4), strip=mix(t['card'], t['border'], 0.4 if light else 0.3),
                input='#ffffff' if light else t['track'])


def ink(color):
    """A meaning color as TEXT: a deeper shade on a light card (amber text on white needs it).  Theme colors pass through"""
    return mix(color, '#000000', 0.3) if color in MEANING and P()['light'] else color


def paint(color):
    """A meaning color as a bar, dot or line: a shade darker on a light card.  Theme colors pass through"""
    return mix(color, '#000000', 0.18) if color in MEANING and P()['light'] else color


def sbar():
    """Scrollbars in the theme's colors, flat - for every window's sbar_ arguments"""
    p = P()
    return dict(sbar_trough_color=p['pane'], sbar_background_color=p['border'], sbar_arrow_color=p['dim'], sbar_frame_color=p['pane'], sbar_relief=sg.RELIEF_FLAT)


def apply_theme():
    """The chosen theme as the PySimpleGUI theme too, so buttons, text boxes, combos, sliders and check boxes in every window follow it"""
    p = P()
    sg.theme_add_new('ClaudeUsage', {'BACKGROUND': p['card'], 'TEXT': p['text'], 'INPUT': p['input'], 'TEXT_INPUT': p['text'], 'SCROLL': p['border'],
                                     'BUTTON': (p['text'], p['track']), 'PROGRESS': (paint(C_SESSION), p['pane']), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
    sg.theme('ClaudeUsage')


def round_corners(window):
    """Windows 11 rounds the window's corners and draws its 1-px outline in the theme's border color.  Windows 10, Linux and Mac keep square corners"""
    if not sg.running_windows():
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(window.TKroot.winfo_id())
        r, g, b = channels(P()['border'])
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 4)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_BORDER_COLOR, ctypes.byref(ctypes.c_uint(r | g << 8 | b << 16)), 4)     # 0x00BBGGRR
    except Exception:
        pass


def title_strip(title):
    """The strip across the top of every extra window: icon, title, version, x (red under the mouse).  Drag it to move the window"""
    p = P()
    row = [sg.Image(data=ICON, subsample=2, background_color=p['strip'], pad=((10, 6), 5)),
           sg.Text(title, font=(UI_FONT, 12, 'bold'), text_color=p['text'], background_color=p['strip'], pad=(0, 5)),
           sg.Text(f'v{VERSION}', font=(UI_FONT, 9), text_color=p['dim'], background_color=p['strip'], pad=((6, 0), (8, 4))),
           sg.Push(background_color=p['strip']),
           sg.Text('  ✕  ', key=K_STRIP_CLOSE, font=(UI_FONT, 12), text_color=p['dim'], background_color=p['strip'], enable_events=True, pad=0, tooltip='Close (Escape)')]
    return [sg.Column([row], key=K_STRIP, background_color=p['strip'], expand_x=True, pad=0)]


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
    """What every extra window gets once it is built: moved by its title strip, its x red under the mouse, Escape, round corners on Windows 11"""
    p, close = P(), window[K_STRIP_CLOSE].Widget
    close.bind('<Enter>', lambda e: close.configure(bg=C_CLOSE, fg='#ffffff'))
    close.bind('<Leave>', lambda e: close.configure(bg=p['strip'], fg=p['dim']))
    drag_by_strip(window, window[K_STRIP].Widget, skip=close)
    window.bind('<Escape>', escape_key)
    round_corners(window)


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


def style_menus(window):
    """tk draws menus Windows-gray and PySimpleGUI colors only the top level: recolor every menu of the window - each element's copy of the right-click
       menu, the ≡ menu and their sub-menus - flat and compact in the theme's colors, with a chip beside each theme name (the lights in a column of their own)"""
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


def close_x_images():
    """The widget's close x: faint, and a red disc with a white x under the mouse.  Drawn 4x and shrunk, so the edges are smooth"""
    p, z, size, images = P(), G.scale * 4, 18, []
    for hover in (False, True):
        im = Image.new('RGBA', (round(size * z), round(size * z)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c, r = size / 2 * z, 3.5 * z
        if hover:
            d.ellipse((c - 8 * z, c - 8 * z, c + 8 * z, c + 8 * z), fill=C_CLOSE)
        color = '#ffffff' if hover else p['faint']
        d.line((c - r, c - r, c + r, c + r), fill=color, width=round(1.5 * z))
        d.line((c - r, c + r, c + r, c - r), fill=color, width=round(1.5 * z))
        buf = io.BytesIO()
        im.resize((round(size * G.scale), round(size * G.scale)), Image.LANCZOS).save(buf, 'PNG')
        images.append(tk.PhotoImage(master=G.window.TKroot, data=base64.b64encode(buf.getvalue())))
    return images


def set_close_x(label):
    """The x's pictures in the current theme"""
    label.images = close_x_images()
    label.configure(image=label.images[0], bg=P()['card'])


def add_close_x(window, event_key):
    """The close x overlaid in the window's top-right corner - faint, a red disc under the pointer, closes the widget when clicked"""
    label = tk.Label(window.TKroot, bd=0, cursor='hand2')
    set_close_x(label)
    label.place(relx=1.0, x=-round(5 * G.scale), y=round(3 * G.scale), anchor='ne')
    label.bind('<Enter>', lambda e: label.configure(image=label.images[1]))
    label.bind('<Leave>', lambda e: label.configure(image=label.images[0]))
    label.bind('<ButtonRelease-1>', lambda e: window.write_event_value(event_key, None))
    return label


def redraw(window):
    """The Brightness panel moved its knob: the widget in the new colors at once (the other windows follow when the panel closes)"""
    G.app.recolor_widget()


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
        G.app, self.scale = self, dpi_scale()
        self.snap, self.busy, self.detail, self.settings_win, self.signin_win, self.snap_pending = None, False, None, None, None, ''
        self.pkce, self.current_alpha, self.last_redraw, self.cards, self.close_x = ('', '', ''), None, datetime.now(), [], None
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
            return P()['faint']
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
        p, color = P(), paint(color)
        graph.draw_rectangle((0, h), (w, 0), fill_color=p['track'], line_color=p['track'])
        fill = max(0.0, min(100.0, pct or 0)) / 100 * w
        if fill >= 1:
            graph.draw_rectangle((0, h), (fill, 0), fill_color=color, line_color=color)
        if pace is not None:
            x = max(1, min(w - 1, pace / 100 * w))
            graph.draw_line((x, h), (x, 0), color=p['text'] if abs(x - fill) > 2 else p['card'], width=1)

    # ---------------------------------------------------------------- widget window ----------------------------------------------------------------
    def build_widget(self):
        f, bar, p = self.fonts(), (int(150 * self.scale), int(10 * self.scale)), P()
        rows = [[sg.Text('●', font=f['dot'], text_color=p['faint'], key=K_DOT, pad=((8, 4), (4, 0)), tooltip='Green ok · amber getting high or checking · red near limit / problem'),
                 sg.Text('Claude', font=f['name'], text_color=p['text'], key=K_TITLE, pad=((0, 6), (4, 0))),
                 sg.Text('', font=f['small'], text_color=p['dim'], key=K_PLAN, pad=((0, 8), (6, 0))),
                 sg.Text('v' + VERSION, font=f['small'], text_color=p['faint'], key=K_VERSION, pad=((0, 26), (6, 0)), tooltip=__file__)]]
        for i in range(MAX_BARS):
            row = [sg.Text('', size=(12, 1), font=f['body'], key=KT_LABEL(i), pad=((10, 6), 1)),
                   sg.Graph(bar, (0, 0), bar, background_color=p['track'], key=KT_BAR(i), pad=((0, 6), 1)),
                   sg.Text('', size=(4, 1), font=f['bold'], justification='r', key=KT_PCT(i), pad=(0, 1)),
                   sg.Text('', size=(10, 1), font=f['small'], text_color=p['dim'], key=KT_RESET(i), pad=((6, 8), 1))]
            rows.append([sg.Column([row], key=KT_ROW(i), pad=0, visible=False, background_color=p['card'])])
        rows.append([sg.Column([[sg.Text('Credits', size=(12, 1), font=f['body'], text_color=ink(C_SPEND), key=K_SPEND_LABEL, pad=((10, 6), 1)),
                                 sg.Graph(bar, (0, 0), bar, background_color=p['track'], key=K_SPEND_BAR, pad=((0, 6), 1)),
                                 sg.Text('', size=(4, 1), font=f['bold'], justification='r', key=K_SPEND_PCT, pad=(0, 1)),
                                 sg.Text('', size=(10, 1), font=f['small'], text_color=p['dim'], key=K_SPEND_LEFT, pad=((6, 8), 1))],
                                [sg.Text('', font=f['small'], text_color=p['dim'], key=K_SPEND_TEXT, pad=((10, 8), (0, 3)))]],
                               key=K_SPEND_ROW, pad=0, visible=False, background_color=p['card'])])
        graph_size = (int(280 * self.scale), int(46 * self.scale))
        rows.append([sg.Column([[sg.Text('', size=(12, 1), font=f['small'], key=K_GRAPH_NAME, pad=((10, 6), 1)),
                                 sg.Graph(graph_size, (0, 0), graph_size, background_color=p['card'], key=K_GRAPH, pad=((0, 8), (3, 2)),
                                          tooltip='Solid: checks so far · dashed: at the current rate · dotted line: the reset')]],
                               key=K_GRAPH_ROW, pad=0, visible=False, background_color=p['card'])])
        rows.append([sg.Text('', font=f['small'], text_color=p['faint'], key=K_FORECAST, pad=((10, 8), (0, 2)))])
        rows.append([sg.Text('starting…', font=f['small'], text_color=p['faint'], key=K_STATUS, pad=((10, 0), (0, 3))), sg.Push(background_color=p['card']),
                     sg.ButtonMenu('≡', self.make_menu(), key=K_MENU, font=f['name'], button_color=(p['dim'], p['card']), border_width=0, pad=((0, 8), (0, 3)),
                                   tooltip='Menu (or right-click anywhere)')])
        menu_bg, menu_text = menu_colors()
        self.widget = sg.Window(APP_NAME, rows, no_titlebar=True, keep_on_top=bool(cfg(K_KEEP_ON_TOP)), grab_anywhere=True, alpha_channel=int(cfg(K_OPACITY)) / 100, auto_save_location=True,
                                right_click_menu=self.make_menu(), right_click_menu_background_color=menu_bg, right_click_menu_text_color=menu_text,
                                right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU, margins=(2, 2), background_color=p['card'], finalize=True)
        G.window, G.scale, G.swatches = self.widget, max(1.0, self.widget.TKroot.winfo_fpixels('1i') / 96), {}
        style_menus(self.widget)
        round_corners(self.widget)
        self.current_alpha = int(cfg(K_OPACITY)) / 100
        bind_click(self.widget, set(descendants(self.widget.TKroot)) - {self.widget[K_MENU].Widget}, 'widget')
        self.close_x = add_close_x(self.widget, K_CLOSE_X)  # added after the click map, so clicking it can't also open the detail window
        self.widget.bind('<Escape>', 'Exit')
        self.widget.timer_start(1000)                       # the countdowns tick each second - a timer, so they keep going while the Brightness panel is open
        self.snap_pending = 'TR' if sg.user_settings_get_entry('-LAST WINDOW LOCATION-' + APP_NAME) is None else ''
        if self.snap_pending:
            self.snap_to(self.snap_pending)

    def make_menu(self):
        """The right-click / ≡ menu with a ✓ on the current choices - every label starts with a ✓ or the same width of spaces, so they line up"""
        tick = lambda on: '✓ ' if on else '    '
        theme = lambda n: f'{tick(n == G.theme)}{n}::{KT_THEME(n)}'
        paused = getattr(self, 'poller', None) is not None and self.poller.paused
        return ['', [f'    Refresh now::{K_M_REFRESH}', f'    Detail window::{K_M_DETAIL}', '---',
                     f'{tick(paused)}Pause polling::{K_M_PAUSE}', f'{tick(cfg(K_KEEP_ON_TOP))}Keep on top::{K_M_TOP}',
                     '    Theme', [theme(n) for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],
                     f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
                     '    Snap to corner', [f'    {name}::{KT_M_SNAP(corner)}' for corner, name in SNAP_CORNERS.items()], '---',
                     f'    Settings...::{K_M_SETTINGS}', f'    Sign in to Claude...::{K_M_SIGN_IN}', f'    Open log file::{K_M_LOG}', '---',
                     '    Edit Me::Edit Me', '    Version::Version', '    Exit::Exit']]

    def rebuild_menus(self):
        """After any choice: every element's copy of the right-click menu (PySimpleGUI makes one per element) and the ≡ menu rebuilt - new ✓ marks,
           chips at the new Brightness - then styled"""
        menu, first = self.make_menu(), True
        for element in self.widget.element_list():
            if element.TKRightClickMenu is not None:
                element.set_right_click_menu(menu, propogate_to_window=first)
                first = False
        old, p = self.widget[K_MENU].TKMenu, P()
        self.widget[K_MENU].update(menu_definition=menu, button_color=(p['dim'], p['card']))     # without button_color, update() puts back the colors it was built with
        old.destroy()
        style_menus(self.widget)

    def recolor_widget(self):
        """The widget in the theme at the current Brightness, in place (the Brightness panel holds on to this window): backgrounds, the fixed text colors,
           the x, the outline - refresh_widget() repaints the rest"""
        p, w = P(), self.widget
        for tkw in descendants(w.TKroot):
            if tkw.winfo_class() != 'Menu':
                try:
                    tkw.configure(bg=p['card'])
                except tk.TclError:
                    pass
        for key in [KT_BAR(i) for i in range(MAX_BARS)] + [K_SPEND_BAR]:
            w[key].Widget.configure(bg=p['track'])
        for key, color in [(K_TITLE, p['text']), (K_PLAN, p['dim']), (K_VERSION, p['faint']), (K_SPEND_TEXT, p['dim']), (K_SPEND_LABEL, ink(C_SPEND))] + \
                          [(KT_RESET(i), p['dim']) for i in range(MAX_BARS)]:
            w[key].update(text_color=color)
        w[K_MENU].Widget.configure(fg=p['dim'], activeforeground=p['text'], activebackground=p['card'])
        set_close_x(self.close_x)
        round_corners(w)
        self.refresh_widget()

    def retheme(self):
        """A new theme or Brightness: the PySimpleGUI theme, the widget and its menus at once; open windows reopen in place in the new colors
           (the Detail window keeps its scroll position, Settings and Sign in what was typed)"""
        apply_theme()
        self.recolor_widget()
        self.rebuild_menus()
        self.forget_closed()
        if self.detail is not None:
            spot, top = self.detail.current_location(), self.detail[K_D_PANE].Widget.canvas.yview()[0]
            self.close_detail()
            self.open_detail(spot)
            self.detail[K_D_PANE].Widget.canvas.yview_moveto(top)
        if self.settings_win is not None:
            spot, values = self.settings_win.current_location(), self.settings_win.read(timeout=0)[1]
            self.settings_win.close()
            self.settings_win = None
            self.open_settings(values, spot)
        if self.signin_win is not None:
            spot, code = self.signin_win.current_location(), self.signin_win[K_CODE].get()
            self.signin_win.close()
            self.signin_win = None
            self.open_signin(spot, code)
        old, self.cards = self.cards, []
        for card in old:
            spot = card.current_location()
            card.close()
            self.text_card(card.metadata['title'], card.metadata['text'], card.metadata['size'], spot)

    def forget_closed(self):
        """Let go of windows that were closed while the Brightness panel had the event loop"""
        gone = lambda win: win is not None and win.was_closed()
        if gone(self.detail):
            self.detail = None
        if gone(self.settings_win):
            self.settings_win = None
        if gone(self.signin_win):
            self.signin_win = None
        self.cards = [card for card in self.cards if not gone(card)]

    def keep_going(self, window, event, values):
        """While the Brightness panel is open the widget keeps counting down and taking poll results; anything else closes the panel and goes to the main loop"""
        if event == sg.EVENT_TIMER:
            self.tick()
        elif event in (K_POLL_BUSY, K_POLL_RESULT):
            self.widget_event(event, values)
        else:
            return False
        return True

    def text_card(self, title, text, size, spot=(None, None)):
        """Version and Raw JSON: the text on a themed card with a title strip, no OS title bar.  The main loop closes it (x, Close, Escape, Alt-F4)"""
        p = P()
        layout = [title_strip(title),
                  [sg.Multiline(text, size=size, font=(MONO_FONT, 10), disabled=True, background_color=p['pane'], text_color=p['text'], border_width=0, pad=((10, 10), (8, 4)),
                                expand_x=True, expand_y=True)],
                  [sg.Push(), sg.Button('Close', key=K_CLOSE, pad=((0, 4), (4, 10))), sg.Sizegrip(background_color=p['card'])]]
        card = sg.Window(title, layout, no_titlebar=True, keep_on_top=True, finalize=True, margins=(0, 0), resizable=True, location=spot, background_color=p['card'],
                         metadata={'title': title, 'text': text, 'size': size}, **sbar())
        dress(card, K_CLOSE)
        self.cards.append(card)

    def snap_to(self, corner):
        sw, sh = self.widget.get_screen_size()
        self.widget.refresh()
        ww, wh = self.widget.size
        m = int(12 * self.scale)
        self.widget.move(m if 'L' in corner else sw - ww - m, m if 'T' in corner else sh - wh - int(60 * self.scale))

    def set_keep_on_top(self, on):
        sg.user_settings_set_entry(K_KEEP_ON_TOP, on)
        self.widget.keep_on_top_set() if on else self.widget.keep_on_top_clear()
        self.rebuild_menus()                                # the ✓ beside Keep on top

    def refresh_widget(self):
        snap, f = self.snap, self.fonts()
        buckets = snap['buckets'] if snap and snap.get('ok') else []
        cb = self.credit_bucket() if cfg(K_SHOW_SPEND) else None
        worst = max([b['percent'] for b in buckets] + ([cb['percent']] if cb else []), default=None)
        self.widget[K_DOT].update(text_color=paint(C_BUSY if self.busy else C_CRIT if snap and not snap.get('ok') else self.level_color(worst)))
        self.widget[K_PLAN].update(snap['plan'] if snap and snap.get('ok') and snap['plan'] else ('demo' if DEMO else ''))
        for i in range(MAX_BARS):
            self.widget[KT_ROW(i)].update(visible=i < len(buckets))
            if i >= len(buckets):
                continue
            b = buckets[i]
            color = KIND_COLOR.get(b['kind'], C_WEEKLY)
            self.widget[KT_LABEL(i)].update(b['label'], text_color=ink(color))
            self.widget[KT_PCT(i)].update(f'{round(b["percent"])}%', text_color=ink(self.level_color(b['percent'])))
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
                self.widget[K_SPEND_PCT].update(f'{round(cb["percent"])}%', text_color=ink(self.level_color(cb['percent'])))
                self.widget[K_SPEND_LEFT].update(f'{spend["symbol"]}{left:,.2f} left', text_color=ink(C_CRIT) if left <= 0 else P()['dim'])
            else:
                self.widget[K_SPEND_LEFT].update('no limit', text_color=P()['dim'])
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
            self.widget[K_GRAPH_NAME].update(shown['label'], text_color=ink(KIND_COLOR.get(shown['kind'], C_WEEKLY)))
            self.draw_graph(self.widget[K_GRAPH], shown, full=False)
        if not buckets:
            self.widget[K_FORECAST].update('')
            return
        cb = self.credit_bucket() if cfg(K_SHOW_SPEND) else None
        casts = [(b, self.forecast(b)) for b in buckets + ([cb] if cb else [])]
        danger = [(b, fc) for b, fc in casts if fc['runs_out'] and fc['hit']]
        if danger:
            b, fc = min(danger, key=lambda x: x[1]['hit'])
            self.widget[K_FORECAST].update('⚠ ' + self.forecast_text(b, fc, short=True), text_color=ink(C_CRIT if (fc['hit'] - utcnow()).total_seconds() < 3600 else C_WARN))
        elif any(fc['rate'] is not None for _, fc in casts):
            worst = max((fc['at_reset'] or 0 for _, fc in casts), default=0)
            self.widget[K_FORECAST].update(f'at this rate nothing runs out before its reset (worst: {round(worst)}%)', text_color=ink(C_OK))
        else:
            self.widget[K_FORECAST].update('forecast after a few more checks', text_color=P()['faint'])

    def refresh_status(self):
        snap = self.snap
        if snap and not snap.get('ok'):
            self.widget[K_STATUS].update(snap['error'][:64], text_color=ink(C_CRIT))
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
        self.widget[K_STATUS].update(('DEMO · ' if DEMO else '') + text, text_color=P()['faint'])

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
        now, fc, p = utcnow(), self.forecast(bucket), P()
        color, level = paint(KIND_COLOR.get(bucket['kind'], C_WEEKLY)), paint(self.level_color(bucket['percent']))
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
        graph.draw_rectangle((left, ph + bottom), (left + pw, bottom), fill_color=p['track'], line_color=p['track'])
        for v in (25, 50, 75, 100):
            graph.draw_line((left, ty(v)), (left + pw, ty(v)), color=p['border'] if v < 100 else p['faint'], width=1)
            if full and v in (50, 100):
                graph.draw_text(yl(v), (left - 4, ty(v)) if dollars else (left - 14, ty(v)), color=p['dim'], font=small,
                                text_location=sg.TEXT_LOCATION_RIGHT if dollars else sg.TEXT_LOCATION_CENTER)
        xn = tx(now)
        if full:
            graph.draw_text(yl(0), (left - 4, ty(0) + 5) if dollars else (left - 12, ty(0) + 5), color=p['dim'], font=small,
                            text_location=sg.TEXT_LOCATION_RIGHT if dollars else sg.TEXT_LOCATION_CENTER)
            for tick, label in time_ticks(t0, t1):
                x = tx(tick)
                graph.draw_line((x, bottom), (x, bottom + 4), color=p['faint'], width=1)
                if abs(x - xn) > 40 * self.scale:                # leave room for the 'now' label on the axis
                    graph.draw_text(label, (x, bottom - 7), color=p['faint'], font=small)
            graph.draw_text('now', (xn, bottom - 7), color=p['text'], font=small)
        if bucket['resets_at']:
            x = tx(bucket['resets_at'])
            dashed(graph, (x, bottom), (x, bottom + ph), p['dim'], width=1, dash=3, gap=3)
            if full:
                local = bucket['resets_at'].astimezone()
                graph.draw_text(f'resets {local:%b} {local.day}' if dollars else 'reset ' + clock(local), (x - 3, bottom + ph - 8), color=p['dim'], font=small,
                                text_location=sg.TEXT_LOCATION_RIGHT)
        graph.draw_line((xn, bottom), (xn, bottom + ph), color=p['faint'], width=1)
        pts = [(tx(t), ty(v)) for t, v in fc['points']]
        for a, b in zip(pts, pts[1:]):
            graph.draw_line(a, b, color=color, width=2)
        if not pts:
            graph.draw_text('one point per check - collecting…', (left + pw / 2, bottom + ph / 2), color=p['faint'], font=small)
        last = (xn, ty(bucket['percent']))
        graph.draw_circle(last, 3, fill_color=color, line_color=color)
        if fc['hit'] is not None and fc['rate']:
            end_t = fc['hit'] if fc['hit'] <= t1 else t1
            end_v = 100.0 if fc['hit'] <= t1 else bucket['percent'] + fc['rate'] * (t1 - now).total_seconds() / 3600
            dashed(graph, last, (tx(end_t), ty(end_v)), level, width=2)
            if fc['runs_out'] and fc['hit'] <= t1:
                graph.draw_circle((tx(fc['hit']), ty(100)), 4, fill_color=paint(C_CRIT), line_color=paint(C_CRIT))
                if full:                                        # bottom-right corner: a line steep enough to hit 100% is never down there
                    hit = fc['hit'].astimezone()
                    graph.draw_text(f'{yl(100)} ~{hit:%b} {hit.day}' if dollars else f'100% ~{when_text(fc["hit"])}', (left + pw - 6, bottom + 9), color=ink(C_CRIT),
                                    font=(UI_FONT, 9, 'bold'), text_location=sg.TEXT_LOCATION_RIGHT)


    # ---------------------------------------------------------------- detail window ----------------------------------------------------------------
    def open_detail(self, spot=(None, None)):
        if self.detail is not None:
            self.detail.bring_to_front()
            return
        f, bar, chart, p = self.fonts(), (int(440 * self.scale), int(14 * self.scale)), (int(440 * self.scale), int(150 * self.scale)), P()
        pane = p['pane']
        body = [[sg.Text('', font=f['h2'], text_color=p['text'], key=K_D_HEAD, pad=((0, 0), (0, 2)), background_color=pane)],
                [sg.Text('', font=f['small'], text_color=p['dim'], key=K_D_BREAKDOWN, pad=((0, 0), (0, 8)), background_color=pane)]]
        for i in range(MAX_BARS):
            block = [[sg.Text('', font=f['bold'], key=KT_D_LABEL(i), pad=(0, 0), background_color=pane), sg.Push(background_color=pane),
                      sg.Text('', font=f['big'], key=KT_D_PCT(i), pad=(0, 0), background_color=pane)],
                     [sg.Graph(bar, (0, 0), bar, background_color=p['track'], key=KT_D_BAR(i), pad=(0, 3))],
                     [sg.Text('', font=f['small'], text_color=p['dim'], size=(60, 2), key=KT_D_META(i), pad=((0, 0), (0, 2)), background_color=pane)],
                     [sg.Graph(chart, (0, 0), chart, background_color=pane, key=KT_D_GRAPH(i), pad=(0, 2))],
                     [sg.Text('', font=f['small'], text_color=p['dim'], size=(60, 2), key=KT_D_CAST(i), pad=((0, 0), (0, 12)), background_color=pane)]]
            body.append([sg.Column(block, key=KT_D_ROW(i), pad=0, visible=False, background_color=pane, expand_x=True)])
        body.append([sg.Text('Usage credits', font=f['bold'], text_color=ink(C_SPEND), pad=((0, 0), (6, 0)), background_color=pane), sg.Push(background_color=pane),
                     sg.Text('', font=f['big'], key=K_D_CRED_PCT, pad=(0, 0), background_color=pane)])
        body.append([sg.Graph(bar, (0, 0), bar, background_color=p['track'], key=K_D_CRED_BAR, pad=(0, 3))])
        body.append([sg.Text('', font=f['small'], text_color=p['dim'], size=(60, 2), key=K_D_SPEND, pad=((0, 0), (0, 2)), background_color=pane)])
        body.append([sg.Graph(chart, (0, 0), chart, background_color=pane, key=K_D_CRED_GRAPH, pad=(0, 2))])
        body.append([sg.Text('', font=f['small'], text_color=p['dim'], size=(60, 2), key=K_D_CRED_CAST, pad=((0, 0), (0, 12)), background_color=pane)])
        body.append([sg.Text('Account', font=f['bold'], text_color=p['text'], pad=((0, 0), (6, 2)), background_color=pane)])
        body.append([sg.Text('', font=f['small'], text_color=p['dim'], key=K_D_ACCOUNT, pad=((0, 0), (0, 6)), background_color=pane)])
        layout = [title_strip(f'{APP_NAME} - detail'),
                  [sg.Column(body, key=K_D_PANE, scrollable=True, vertical_scroll_only=True, size=(int(560 * self.scale), int(640 * self.scale)), pad=((10, 4), (10, 4)),
                             background_color=pane, expand_x=True, expand_y=True)],
                  [sg.Text(KEYS_HINT, font=f['small'], text_color=p['faint'], pad=((12, 0), (0, 4)))],
                  [sg.Button('Refresh', key=K_REFRESH, font=f['body'], pad=((12, 4), (0, 10))), sg.Button('Raw JSON', key=K_RAW, font=f['body'], pad=(4, (0, 10))),
                   sg.Button('Copy JSON', key=K_COPY, font=f['body'], pad=(4, (0, 10))), sg.Push(), sg.Button('Close', key=K_CLOSE, font=f['body'], pad=((0, 4), (0, 10))),
                   sg.Sizegrip(background_color=p['card'])]]
        self.detail = sg.Window(f'{APP_NAME} - detail', layout, no_titlebar=True, keep_on_top=True, finalize=True, background_color=p['card'], resizable=True, margins=(0, 0),
                                location=spot, **sbar())
        for seq, key in KEY_BINDS:
            self.detail.bind(seq, key)
        dress(self.detail, K_KEY_ESC)
        self.wire_detail_wheel()
        self.refresh_detail()

    def refresh_detail(self):
        if self.detail is None:
            return
        snap = self.snap
        if not snap or not snap.get('ok'):
            self.detail[K_D_HEAD].update(snap['error'] if snap else 'waiting for the first check…', text_color=ink(C_CRIT) if snap else P()['dim'])
            for i in range(MAX_BARS):
                self.detail[KT_D_ROW(i)].update(visible=False)
            return
        account = snap.get('account') or {}
        who = ' · '.join(x for x in [snap['plan'] or 'Claude', account.get('email') or account.get('display_name') or '', 'DEMO' if DEMO else ''] if x)
        self.detail[K_D_HEAD].update(who, text_color=P()['text'])
        parts = ' · '.join(f'{name} {round(pct)}%' for name, pct in snap.get('breakdown') or [])
        self.detail[K_D_BREAKDOWN].update(f'This week\'s use by app: {parts}' if parts else '')
        for i in range(MAX_BARS):
            visible = i < len(snap['buckets'])
            self.detail[KT_D_ROW(i)].update(visible=visible)
            if not visible:
                continue
            b = snap['buckets'][i]
            color, pace = KIND_COLOR.get(b['kind'], C_WEEKLY), self.pace(b)
            self.detail[KT_D_LABEL(i)].update(b['label'], text_color=ink(color))
            self.detail[KT_D_PCT(i)].update(f'{round(b["percent"])}%', text_color=ink(self.level_color(b['percent'])))
            self.draw_bar(self.detail[KT_D_BAR(i)], b['percent'], color, pace)
            bits = [self.level_word(b['percent']), reset_long(b['resets_at'])]
            if pace is not None:
                bits.append(f'even pace would be {round(pace)}%')
            if b['severity'] and b['severity'] != 'normal':
                bits.append('severity ' + str(b['severity']))
            self.detail[KT_D_META(i)].update(' · '.join(bits))
            fc = self.forecast(b)
            self.draw_graph(self.detail[KT_D_GRAPH(i)], b, full=True)
            self.detail[KT_D_CAST(i)].update(f'{b["label"]} forecast: ' + self.forecast_text(b, fc), text_color=ink(C_CRIT) if fc['runs_out'] else P()['dim'])
        spend, cb = snap.get('spend'), self.credit_bucket()
        for key in (K_D_CRED_BAR, K_D_CRED_GRAPH, K_D_CRED_CAST):
            self.detail[key].update(visible=bool(cb))
        self.detail[K_D_CRED_PCT].update(f'{round(cb["percent"])}%' if cb else '', text_color=ink(self.level_color(cb['percent'])) if cb else P()['text'])
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
            self.detail[K_D_CRED_CAST].update('Credits forecast: ' + self.credit_forecast_text(cb, fc), text_color=ink(C_CRIT) if fc['runs_out'] else P()['dim'])
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
    def open_signin(self, spot=(None, None), code=None):
        """The sign-in window.  code = what was typed in it before it was rebuilt in a new theme - the sign-in URL is kept too"""
        if self.signin_win is not None:
            self.signin_win.bring_to_front()
            return
        f, p = self.fonts(), P()
        if code is None:
            verifier, challenge = pkce_pair()
            state = secrets.token_urlsafe(32)
            self.pkce = (verifier, state, authorize_url(challenge, state))
        layout = [title_strip(f'{APP_NAME} - sign in'),
                  [sg.Text('Sign this widget in to Claude', font=f['h2'], pad=((10, 10), (10, 2)))],
                  [sg.Text('This creates a token that belongs to the widget alone - it never touches the one Claude Code uses.', font=f['small'], text_color=p['dim'],
                           pad=((10, 10), (0, 8)))],
                  [sg.Text('1.  Open this URL and approve the request:', font=f['body'], pad=((10, 10), (4, 2)))],
                  [sg.Multiline(self.pkce[2], size=(70, 3), font=f['mono'], key=K_URL, no_scrollbar=True, pad=((10, 10), 2))],
                  [sg.Button('Open in browser', key=K_OPEN_URL, font=f['body'], pad=((10, 6), 4)), sg.Button('Copy URL', key=K_COPY_URL, font=f['body'], pad=(0, 4))],
                  [sg.Text('2.  Paste the code the callback page shows you:', font=f['body'], pad=((10, 10), (10, 2)))],
                  [sg.Input(code or '', size=(60, 1), font=f['mono'], key=K_CODE, pad=((10, 10), 2)), sg.Button('Finish', key=K_FINISH, font=f['body'], bind_return_key=True)],
                  [sg.Text('', font=f['small'], text_color=p['dim'], key=K_SIGNIN_MSG, size=(70, 2), pad=((10, 10), (6, 10)))]]
        self.signin_win = sg.Window(f'{APP_NAME} - sign in', layout, no_titlebar=True, keep_on_top=True, finalize=True, background_color=p['card'], modal=False,
                                    margins=(0, 0), location=spot, **sbar())
        dress(self.signin_win, K_STRIP_CLOSE)

    def finish_signin_bg(self, code, window):
        try:
            tokens = exchange_code(code, self.pkce[0], self.pkce[1])
            save_own_tokens(tokens)
            sg.user_settings_set_entry(K_AUTH_MODE, AUTH_OWN)
            window.write_event_value(K_SIGNIN_DONE, (True, 'Signed in.  Fetching your usage…'))
        except Exception as e:
            window.write_event_value(K_SIGNIN_DONE, (False, str(e)))

    # ---------------------------------------------------------------- settings window ----------------------------------------------------------------
    def open_settings(self, values=None, spot=(None, None)):
        """The settings window.  values = what it showed before it was rebuilt in a new theme (None: the saved settings)"""
        if self.settings_win is not None:
            self.settings_win.bring_to_front()
            return
        f, p = self.fonts(), P()
        v = lambda key: values[key] if values and key in values else cfg(key)
        token, where, error = ('', 'demo', '') if DEMO else read_claude_code_token()
        found = f'found: {where}' if token else (error or 'not found')
        layout = [title_strip(f'{APP_NAME} - settings'),
                  [sg.Text('Where the token comes from', font=f['h2'], pad=((10, 10), (10, 4)))],
                  [sg.Combo(AUTH_MODES, default_value=v(K_AUTH_MODE), readonly=True, size=(30, 1), font=f['body'], key=K_AUTH_MODE, pad=((10, 10), 2)),
                   sg.Button('Sign in…', key=K_M_SIGN_IN, font=f['body'])],
                  [sg.Text(f'Claude Code credentials - {found}', font=f['small'], text_color=p['dim'] if token else ink(C_WARN), size=(64, 2), pad=((10, 10), (0, 6)))],
                  [sg.Text('Pasted token (only used by the "Pasted token" mode)', font=f['small'], text_color=p['dim'], pad=((10, 10), (4, 0)))],
                  [sg.Input(str(v(K_TOKEN)), size=(52, 1), font=f['mono'], password_char='•', key=K_TOKEN, pad=((10, 10), (0, 10)))],
                  [sg.Text('Widget', font=f['h2'], pad=((10, 10), (6, 4)))],
                  [sg.Text('Check every', size=(14, 1), font=f['body'], pad=((10, 4), 2)), sg.Combo(INTERVALS, default_value=v(K_INTERVAL), readonly=True, size=(10, 1),
                                                                                                    font=f['body'], key=K_INTERVAL),
                   sg.Text('5 min or more is kind to the endpoint', font=f['small'], text_color=p['dim'])],
                  [sg.Text('Opacity', size=(14, 1), font=f['body'], pad=((10, 4), 2)), sg.Slider((40, 100), int(v(K_OPACITY)), orientation='h', size=(28, 14),
                                                                                                 enable_events=True, key=K_OPACITY, font=f['small'])],
                  [sg.Text('Font size', size=(14, 1), font=f['body'], pad=((10, 4), 2)), sg.Slider((8, 18), int(v(K_FONT_SIZE)), orientation='h', size=(28, 14),
                                                                                                   key=K_FONT_SIZE, font=f['small'])],
                  [sg.Text('Amber at', size=(14, 1), font=f['body'], text_color=ink(C_WARN), pad=((10, 4), 2)), sg.Slider((10, 100), int(v(K_WARN)), orientation='h',
                                                                                                                          size=(28, 14), key=K_WARN, font=f['small'])],
                  [sg.Text('Red at', size=(14, 1), font=f['body'], text_color=ink(C_CRIT), pad=((10, 4), 2)), sg.Slider((10, 100), int(v(K_CRIT)), orientation='h',
                                                                                                                        size=(28, 14), key=K_CRIT, font=f['small'])],
                  [sg.Checkbox('Show the usage-credits line', bool(v(K_SHOW_SPEND)), font=f['body'], key=K_SHOW_SPEND, pad=((10, 10), (8, 0)))],
                  [sg.Checkbox('Show the even-pace tick on each bar', bool(v(K_SHOW_PACE)), font=f['body'], key=K_SHOW_PACE, pad=((10, 10), (0, 0)))],
                  [sg.Checkbox('Keep the widget on top of other windows', bool(v(K_KEEP_ON_TOP)), font=f['body'], key=K_KEEP_ON_TOP, pad=((10, 10), (0, 0)))],
                  [sg.Checkbox('Show a graph in the widget of', bool(v(K_SHOW_GRAPH)), font=f['body'], key=K_SHOW_GRAPH, pad=((10, 4), (0, 0))),
                   sg.Combo(GRAPH_CHOICES, default_value=v(K_GRAPH_OF), readonly=True, size=(14, 1), font=f['body'], key=K_GRAPH_OF, pad=((0, 10), (0, 0)))],
                  [sg.Text('Favorite models', size=(14, 1), font=f['body'], text_color=ink(C_MODEL), pad=((10, 4), 2)),
                   sg.Input(str(v(K_FAVORITE)), size=(24, 1), font=f['body'], key=K_FAVORITE),
                   sg.Text('name matches, comma-separated - they sort to the top', font=f['small'], text_color=p['dim'])],
                  [sg.Push(), sg.Button('Save', key=K_SAVE, font=f['body'], pad=(6, (4, 10))), sg.Button('Cancel', key=K_CANCEL, font=f['body'], pad=((6, 12), (4, 10)))]]
        self.settings_win = sg.Window(f'{APP_NAME} - settings', layout, no_titlebar=True, keep_on_top=True, finalize=True, background_color=p['card'], margins=(0, 0),
                                      location=spot, **sbar())
        dress(self.settings_win, K_CANCEL)

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
        self.widget.timer_stop_all()
        self.widget.close()
        self.build_widget()
        self.widget.move(*location)
        self.poller.window = self.widget
        self.refresh_widget()
        self.poller.wake.set()

    # ---------------------------------------------------------------- event loop ----------------------------------------------------------------
    def run(self):
        while True:
            window, event, values = sg.read_all_windows()
            if window is None:
                break
            if window is self.widget and event == sg.EVENT_TIMER:
                self.tick()
                continue
            if window in self.cards:                            # Version / Raw JSON
                if event in (sg.WIN_CLOSED, K_CLOSE, K_STRIP_CLOSE):
                    window.close()
                    self.cards.remove(window)
                continue
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
        for win in self.cards + [self.settings_win, self.signin_win, self.widget]:
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
        key = item.split('::')[-1] if isinstance(item, str) and '::' in item else item       # a menu choice arrives as its whole 'label::key'
        if key in ('Exit', sg.WINDOW_CLOSED, K_CLOSE_X):
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
        elif event == K_CLICK or key == K_M_DETAIL:
            self.open_detail()
        elif key == K_M_REFRESH:
            self.poller.wake.set()
        elif key == K_M_PAUSE:
            self.poller.paused = not self.poller.paused
            self.poller.wake.set()
            self.refresh_status()
            self.rebuild_menus()                            # the ✓ beside Pause polling
        elif key in SNAP_KEYS:
            self.snap_to(SNAP_KEYS[key])
        elif key == K_M_SETTINGS:
            self.open_settings()
        elif key == K_M_SIGN_IN:
            self.open_signin()
        elif key == K_M_TOP:
            self.set_keep_on_top(not cfg(K_KEEP_ON_TOP))
        elif isinstance(key, str) and key.startswith(K_THEME):
            G.theme = key[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            self.retheme()
        elif key == K_BRIGHT:
            pending = brightness_panel(self.widget, self.keep_going)
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            self.retheme()
            if pending:                                     # the widget event that closed the panel (a menu choice, the x...)
                return self.widget_event(*pending)
        elif key == K_M_LOG:
            path = os.path.join(os.path.dirname(sg.user_settings_filename()), LOG_FILE_NAME)
            if not os.path.exists(path):
                log('log created')
            os.startfile(path) if hasattr(os, 'startfile') else webbrowser.open('file://' + path)
        elif key == 'Version':
            self.text_card(f'{APP_NAME} - version', '\n'.join([f'{APP_NAME} {VERSION}', __file__, sg.get_versions()]), (70, 10))
        elif key == 'Edit Me':
            sg.execute_editor(__file__)
        return True

    def detail_event(self, event):
        if event in (sg.WIN_CLOSED, K_CLOSE, K_KEY_ESC, K_STRIP_CLOSE):
            self.close_detail()
        elif event in SCROLL_KEYS:
            self.scroll(event)
        elif event == K_REFRESH:
            self.poller.wake.set()
        elif event == K_RAW:
            self.text_card('Raw usage response', json.dumps(self.snap.get('raw', {}) if self.snap else {}, indent=2), (80, 30))
        elif event == K_COPY:
            sg.clipboard_set(json.dumps(self.snap.get('raw', {}) if self.snap else {}, indent=2))

    def settings_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_CANCEL, K_STRIP_CLOSE):
            self.settings_win.close()
            self.settings_win = None
        elif event == K_OPACITY:
            self.widget.set_alpha(int(values[K_OPACITY]) / 100)
            self.current_alpha = int(values[K_OPACITY]) / 100
        elif event == K_M_SIGN_IN:
            self.open_signin()
        elif event == K_SAVE:
            self.save_settings(values)

    def signin_event(self, event, values):
        if event in (sg.WIN_CLOSED, K_STRIP_CLOSE):
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
            self.signin_win[K_SIGNIN_MSG].update(message, text_color=ink(C_OK if ok else C_CRIT))
            if ok:
                self.signin_win.close()
                self.signin_win = None
                self.poller.wake.set()


def main():
    sg.user_settings_filename(filename=DEMO_SETTINGS_FILE if DEMO else SETTINGS_FILE)
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    sg.set_options(dpi_awareness=True, font=(UI_FONT, 11), tooltip_font=(UI_FONT, 10), icon=ICON)
    apply_theme()
    try:
        App().run()
    except Exception as e:
        log(traceback.format_exc())
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())


if __name__ == '__main__':
    main()
