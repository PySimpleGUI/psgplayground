#!/usr/bin/env python
"""
    Task Manager - every running process with its CPU, memory, threads and command line.  Filter, sort, kill.
    A redesign of Demo_psutil_Kill_Processes.py (the 2018 Process Killer): the same jobs, now live, quick and in the widgets' look.

    The list keeps itself up to date (every 2 s) without losing your selection or scroll position - rows are changed in place, not rebuilt.
    A thread does all the measuring, so the window never waits for it.  A process's user and command line are read once, not every time.
    Type anywhere to filter (name, PID, user or command line).  Click a heading to sort, click it again to reverse.
    Kill (or the Delete key) ends the selected processes and everything they started.  Python only: just the python processes; for them the
        Command line column shows the script they run (the details under the list show the whole line).
    Across the top: CPU with its history, every core, memory with its history, and the process count.

    Keys:  Up/Down move   PgUp/PgDn page   Home/End top/bottom   Delete kill   F5 measure now   Ctrl+F filter   Esc exit
    Right-click:  Kill selected | Refresh now | Refresh every | Keep on top | Ask before killing | Theme (16 dark + 16 light) | Brightness... | Edit Me / Version / Exit
    Everything you choose is remembered, with the window's size and place, the sort and the column widths.
    --demo   made-up processes instead of yours (for screenshots, or to try it out): nothing of yours is read or shown, and Kill only takes them off the list.

    Requires:  pip install PySimpleGUI psutil pillow
    Copyright 2018-2026 PySimpleGUI. All rights reserved.

CHANGE LOG (newest first, 1 line per change):
2026-11-03  v1.0.2  Claude: --demo - made-up processes for screenshots and the Playground's Demo button: nothing of yours is read, Kill only takes them off the list
2026-11-03  v1.0.1  Claude: Windows: the taskbar showed tk's feather instead of the icon once - the icon is now tk's default icon too; CPU % wide enough for its arrow
2026-11-03  v1.0.0  Claude: first version - redesign of Demo_psutil_Kill_Processes.py: measured in a thread, a live table changed in place, cards across the top, themes
"""
import base64
import io
import math
import os
import queue
import random
import sys
import tempfile
import threading
import time
import traceback
import tkinter as tk
import tkinter.font as tkfont
from collections import deque
from tkinter import ttk

import PySimpleGUI as sg

try:
    import psutil
    from PIL import Image, ImageDraw, ImageFont
except ImportError as missing:
    sg.popup_error(f'Task Manager needs psutil and Pillow - {missing.name} is not installed.', 'Install them with:', '    python -m pip install psutil pillow',
                   title='Task Manager', keep_on_top=True)
    sys.exit(1)

VERSION = '1.0.2'
APP_NAME = 'Task Manager'
DEMO = '--demo' in sys.argv           # made-up processes, nothing of yours is read or killed - see the top of the file
ICON = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAALuklEQVR4nN2ba4xd11XHf2vv87iv8Vx7JnbqPGgiaNIIJ5gosRMiroACVeOkDug6Qi0f4AsUxJd+Kip0OlApCAjiA0iUl1ADasSt2qh1KI+AMrQ4sVOnzsNuXJO4SRw/JrbHntede8/ee/Hh3JmOJ/O4Y88r/KUjXZ179j57PfZa/73O3tAtBgZMrVaL6vW67brNmuOKMUo3Lbp4aMDAoAI6fWf37nqxmbZTLgHVaxvySiFttsKhQ/86OvtevV63jUbDL9ZuUQXM7mDnT+/9sHp9UIP+AsLtIqYnaEC61PRqQUA1H4MDOQp6SFS+duTG5CCNhmdgwDB4pQHntJ+/34GBARkcHAw7fuqh3UbtH4jwM1GcRKqKdxnBOxBZqN81RD4GEUMUJ4hYvM/QEF4h+MeOPPeNL7OIN8yngBmp7rrvoc+LsZ+N4jhqTU3SHL/spiZHxWVt8S4TkXU1/gwUxYglSpKQFiparPTaQrFHFMV792QQ91uvfPvpkYGBATM4OBhmt50rgQDseODBqg32r6KksC9rt3R05GyYuHzBuqwNAiKCiKy/8WdBAdUACsZaSpVq2NR3vRZKm6xrt76r2v71lw78y5G5SjCzO6nVanmE9+Zv4rS0b2pytP3uO//L5fOnrfcOE0UYEyFi6Ghiw1wigjERJooAGL98wQy/fcKOjQxnNo53CvFXb79nb99gLqq8RwH1et0ODQ25O+/f87k0Lf5yc+JS+9zbJ5JWc0xMFHcsvmAs2SDQzhjBRBHeO86ffj0evTicRUl6SxK5JxkcDNTrM3IbgIGBAdNoNPyOBx6825jos1l7yl8891YcvENsNNPp+wqaB0YRw6V3T8XNiVEXJ8WP7Lhvz2/TaPhpPmMAZtzCm8ejKIlHL55janJcxNoFhF9/l3/PNW88VxBDcBmXzr9jQ3DBiPnDn3jgo9c1Go0AiAyAGYRw5wN7P2SUo95n9txbx+WHaW6u7AbUg/frzADmQAzYGML8vEdDoH/7rb6nep1ttZu/9sqBb/xDrVaLomdrNcPQUMC7X4rSUjR++V3nsnZkonlcXwy0JyAuIz1VCBtkaoigWQsmL0BamWfcgqoyOX6Jnmq/ilIHvjS0datGQ1u3Tj/9s6C568+X4sSg7QnszXeTPPo4prINDTK/l6wlVBEJqE6RffPPyJ7/ElLYlHvprGeMMbSbEybLWiLIfbfd/3D5eKMxFtFohDtq9YpkrQ+7rI3LWkbmMjwRUI8kZZJH/wJ74wfRZu4QGwIKYiGp/zHh1BH8maNIXAKdxXlE8D4T15rSpFjpKfnmbcB3IkCtn4xFot4QXE5x531JQOISUulD2wreQdgoGgC8QjlCitU8DszjxRoC3mVqjInazvYCRADGRkqmC0c1VbAJYfw82f7Pk+z7I6QY51NtAwRCUcBC9uwT+Nf/B0l7FgyG01PWKo5pBdDxokXfEjxSqOAO/SP+1EuY6rZc6xsgBmAEbU0QfvACRElXvEVVhdkK6PplaQ969hju1MsbwvrTEDGQljtu3312Wp4CyGMBcQlJNpD0dIyjoYsHr8TyFUBHCRuEAlwrNlAYXx9cnQeQ1wS6gS4VkBag8GuFZStAOrTSe9dVDszX6TYvVsyGkZxKuzCnH4XIzPxcbSxLASJCu90mjmPK5R46RdHFGuCyjMnJSdI0/aE3iKBNh6QWUy3kipgmn0bwF6fyBWdsVl0JXStgWvgbb7qZhx/ZR7lSIfiwCA/QmZrtf/3HN3nx8EHStIAK6KQjuWMLmz9zL7aaotOLKlUktrS/d5GRxw4SxjKIVrf01pUCRIQQlCRJePiRR/nADTcwNdXELLEYUFWstezZW+fMmVOcO3uWOIqhFLH5M/cQ37YZHc+uXFN4pfiRm/AXm4x84SDS0x2xuVosYwoocRRTKpfJ2m288wRZOu967ymWyhSKxU7RUpHEYnpTtOkgC1fmIq/QDti+wpoQra7SoKpijGV8Ypxn/m0/AMVikTRNSQuF+a+0QJqmFEslnvv2s7x58g2SJEWtEEZajH7xZQCkEiOlCCnFSDFCelPc6QlG//ZVsGbVI2HXHqAaSNMC3z38AmdOv8Om3iphsaqQghhDu9Xi7bd+gLVRHgQVpBQx8fRJ2sdHsFtLeSaYXoJbQ/b6JfxwEylFq150WVYWUFXSNGX43FnOnH5nSQ/Ng7qQzM4AnT+kHJOdvEx2YuQ9aVDSaE2E52p4gKoSxzFxkiztnZJH9nnJUMgFpTDvS9as3HZVTFBVu4tPujgTlMWi+zUGwG4Tx7oxwRki6DTvc7kDWeydQNyp6C/V77owQSMw2VaKsdDfY/O6ynIGsgSCwvCopxjLkvWaNWeCIspES/nJDyb86Sf76O+xOK8rVlhShSQSvnJwgi98bYTELu5da8oEh8+eJYpiygk8/sk+dtycMDoZsGbl7J9/JRY+/bFejp/JeOJbY1RLBr8AZ1tTJhg0EIBSLGyuGCZbgbYHs/xCzqJwnQxy3aZc8MXU25UC5jLBhx/ZR7FYzOf0Qr7bqc0Za69ggkaU82PKY09d4k8+0UdvcWayXDN01hR45tUmT3xrnE1FwS8yB9acCXqFSkF48sAEL7/VZvvmiGylYkDHHqpw+GSLZqakkSyaEteFCWpHCcdPZ7z6dntlK+sddyolZknhWU8mGBSKiVBahe8KOl237YJcrCsTVF3Vpf6CO8AEiFRFQdaRCQpeFR9WmAUtAlUlU8UpXHbiBHSdmKAw4Rxla6kW0jXbgqMa2BJHlCJhx+ZC7xuf+tTmtWeCwLhz7OrbzF/u2sn1aYroyjHBRZFnJiNiKIh+GWOyNWeCNo6pRBF/t2snt2ypQrbA5/hVhYKYCsjaM0FRpWQtfWmCZh7nAyvIhLuEYEU9aHcxYEWZIDDcavG7R47x57t2EidX/XHq6jCdeoy1yDI8YMWYINATRfz9G2/y4sglri8V0dBlWr1WqNLbv10LpR6plc2nf6W/54gA3FX7eJVM31QNm86++ZoG7xZcSIsIWZbhvb/6miBgRZhwniyE+XazrArUB7be9KOh0ttvXjt/YTffe/ZgBBDFibqslYkIYgwscsRgpZigV6UUWYQ1PIASKdU4oSiE3b2VwnP1ujXU6/bwM41RVV6L4pQoSoMusflHVdEQUF3iCmFRJhhUczK0FlcIqLFqktRkLmtmKUel0fCmNjwsgAr+oBFDWiyr6tqxs7VBzl7jtBjiJCWoHr11a3GEgQFjtnY2SgZjGt47LVZ6jVlwj/D7FJJ7banSq0YiVPQrjUbD371/vzWNRsOjKn6k8KJz7e8XSj1SqlRDHuH/P7iBoN6TFEpa6tlisnbL2UifAthz+LA3APV9+8yxY412MPI5FNm05QMhihMIczcvvB+Re3Jv33YfJwUTQvbFI//99Il6vW4HIcxIN32o6M779vxzUijXx0aGs/OnX48Rk2eG992UyEXzrk21f7vfsu1HrMtaJ6fgruM/v3Ni+iTZDJlvNBqBet06bf9m1mq+Uqn2x1uuvyUzxna2z26AjdFdIR+nBo8GT7V/u69ed4P13k162Hf8wNfHOg8qcz6P68Add+ix5//9YgjyiZBlJ3q3bIu33vhjrljuVQ2e4NzSm57WEapKCI7gHHFa1P7tt7ot2262wJhm7jdePfD179TrdcusQ1PvMen0qarb7/m5vjQu/1MUp78YgmNy7LKbHB+RdnPCeJ+JhjDrgN36Q0QwNtI4LYZiparlns1RnBRwWev76t2vvvT804dqtVo0NDR0xfJzfp/OT1sGgDvv//jvGOH3ojjdqqq4rIVrT6lzmW6Yc4OdxVqcFk0Upxhj8VmrpfDXdmr89w8ffubycg5Ozv1Pf3zXQ9tsLB9DZS/K/caYfmOjjWP+jhK8d6MEPSpGvmqD33/4uf2v5f8OGBicd+2+pAnnau7eez+6aTJKPmRFKs65q99pucIIii/0xMde+M+nLkzf64w9rISlZOMfnZ+B1Gq1KLf60vg/mg/ZGW4KF7YAAAAASUVORK5CYII='

# ---------- keys ----------
K_HEADER = '-HEADER-'                 # the cards across the top - one Pillow image
K_FILTER_LABEL = '-FILTER LABEL-'
K_FILTER = '-FILTER-'                 # filter box
K_CLEAR = '-CLEAR-'                   # the x that empties it
K_PYTHON = '-PYTHON-'                 # Python only toggle, also its settings-file entry
K_PAUSE = '-PAUSE-'                   # Pause / Resume
K_KILL = '-KILL-'                     # Kill button, the Delete key and the right-click item
K_TABLE = '-TABLE-'
K_DETAILS = '-DETAILS-'               # two lines about the selected process
K_STATUS = '-STATUS-'
K_GRIP = '-GRIP-'
K_TICK = '-TICK-'                     # timer: time to measure again
K_SAMPLE = '-SAMPLE-'                 # the sampler thread finished a measurement      value: the sample dict
K_KILLED = '-KILLED-'                 # the sampler thread finished killing             value: (killed, failed)
K_THREAD_ERROR = '-THREAD ERROR-'     # the sampler thread crashed                       value: the traceback text
K_RESIZED = '-RESIZED-'               # the window's width changed and the resizing has settled - redraw the cards      value: the new width
K_PGUP, K_PGDN, K_HOME, K_END = '-PGUP-', '-PGDN-', '-HOME-', '-END-'
K_REFRESH_NOW = '-REFRESH NOW-'       # F5 and the right-click item
K_FIND = '-FIND-'                     # Ctrl+F
K_EXIT = 'Exit'
K_REFRESH = '-REFRESH-'               # settings-file entry (seconds), and the prefix of its menu keys
KT_REFRESH = lambda secs: f'{K_REFRESH}{secs}'
K_TOP = '-TOP-'                       # keep on top
K_CONFIRM = '-CONFIRM-'               # ask before killing
K_THEME = '-THEME-'                   # settings-file entry, and the prefix of the theme menu keys
KT_THEME = lambda name: f'{K_THEME}{name}'
K_SORT = '-SORT-'                     # settings-file entry: [column, biggest first]
K_SIZE = '-WINDOW SIZE-'              # settings-file entry: [width, height]
K_WIDTHS = '-COLUMN WIDTHS-'          # settings-file entry: pixels per column

# ---------- the table ----------
COLUMNS = [('Name', 24, 'l'), ('PID', 7, 'r'), ('CPU %', 9, 'r'), ('Memory', 10, 'r'), ('Threads', 8, 'r'), ('User', 14, 'l'), ('Command line', 52, 'l')]
HEADINGS = [c[0] for c in COLUMNS]
NAME, PID, CPU, MEM, THREADS, USER, CMD, PPID, STARTED, FULL = range(10)      # a process row: the 7 columns, then parent, start time and the whole command line
SORT_KEYS = {NAME: lambda r: r[NAME].lower(), PID: lambda r: r[PID], CPU: lambda r: r[CPU], MEM: lambda r: r[MEM], THREADS: lambda r: r[THREADS],
             USER: lambda r: r[USER].lower(), CMD: lambda r: r[CMD].lower()}
BIG_FIRST = (CPU, MEM, THREADS)       # a first click on these headings sorts biggest first; the others go A to Z

# ---------- look and timing ----------
REFRESHES = (1, 2, 5, 10)             # seconds between measurements, for the right-click menu
HISTORY = 60                          # readings kept for the CPU and memory histories (2 minutes at the usual 2 s)
HEADER_H = 96                         # height of the cards' strip in design pixels (times the screen's scale)
RADIUS = 12                           # corner radius of the cards (design pixels) - the Brightness panel uses it too
WARM, HOT = 5, 25                     # CPU % of the whole machine where a row turns amber / red
NUM_CPUS = psutil.cpu_count() or 1
TRANSPARENT = '#010203'               # color key for the Brightness panel's see-through corners (Windows)
C_SEL = '#2a62a8'                     # selected rows, toggles that are on, the menu highlight - white text on it
C_MENU_SEL = C_SEL
C_KILL, C_KILL_HOVER = '#c0392b', '#d9483a'
C_SWATCH_EDGE = '#7c8594'             # outline of the theme chips in the Theme menu
C_MEMORY = '#c48cff'
C_PYTHON = '#4ea6ff'
LOAD_STOPS = [(0, '#2ecc71'), (45, '#2ecc71'), (72, '#e8a33d'), (100, '#ff6b6b')]      # (percent, color) - blended between these
FONT, FONT_BOLD, FONT_SMALL, FONT_MENU = ('Segoe UI', 10), ('Segoe UI', 10, 'bold'), ('Segoe UI', 9), ('Segoe UI', 10)
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # Pillow: bold / regular, Windows first, then Linux

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


class G:                              # program-wide state
    window = None
    scale = 1.0                       # screen dpi / 96 - 2.0 on a 200% Windows display
    theme = 'Toybox'
    bright = 0                        # Brightness: -80 (much darker) .. 50 (lighter), 0 = the theme as designed
    tuned = {}                        # (theme, brightness) -> the theme's colors at that brightness
    swatches = {}                     # (theme, brightness) -> tk.PhotoImage chip for the Theme menu
    fonts = {}                        # (bold, px) -> Pillow font
    colors = {}                       # what ui_colors() worked out for the current theme
    refresh = 2                       # seconds between measurements
    timer = None
    paused = False
    python_only = False
    on_top = False
    confirm = False                   # ask before killing
    sort = [CPU, True]                # [column, biggest first]
    filter = ''
    sampler = None
    busy = False                      # a measurement is on its way
    sample = None                     # the latest measurement
    cpu_hist = deque(maxlen=HISTORY)
    mem_hist = deque(maxlen=HISTORY)
    rows = {}                         # iid -> (cells, tags) as shown, so unchanged rows aren't touched
    order = []                        # iids in the order shown
    shown = 0                         # rows that pass the filter
    details = None                    # what the details lines show now
    message, message_until, message_bad = '', 0, False     # the last kill's result for the status line, until when, and whether it went wrong
    header_w = 0                      # width the cards were last drawn for
    resize_job = None
    row_h = 24
    hover = {}                        # button key -> (normal, hover) background


# ---------- measuring (all psutil calls happen in this thread) ----------
class Sampler(threading.Thread):
    """Jobs come in on a queue - ('sample', None) or ('kill', [pids]) - and the answers go back with write_event_value.
       psutil.process_iter() keeps its Process objects between calls, so cpu_percent() measures since the previous sample"""
    def __init__(self, window):
        super().__init__(daemon=True)
        self.window = window
        self.jobs = queue.Queue()
        self.static = {}                                    # (pid, start time) -> (user, command line shown, whole command line) - they never change
        psutil.cpu_percent(None)                            # prime: a first reading is always 0
        psutil.cpu_percent(None, percpu=True)

    def run(self):
        while True:
            job, arg = self.jobs.get()
            try:
                if job == 'sample':
                    self.window.write_event_value(K_SAMPLE, self.sample())
                elif job == 'kill':
                    self.window.write_event_value(K_KILLED, self.kill(arg))
            except Exception:
                self.window.write_event_value(K_THREAD_ERROR, traceback.format_exc())

    def sample(self):
        procs, seen = {}, set()
        for p in psutil.process_iter(['name', 'ppid', 'memory_info', 'num_threads', 'create_time'], ad_value=None):
            if p.pid == 0:                                  # Windows' System Idle Process - its "CPU" is the idle time
                continue
            try:
                cpu = p.cpu_percent(None) / NUM_CPUS        # psutil counts each core as 100% - divide so 100% is the whole machine
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
            except psutil.AccessDenied:
                cpu = 0.0
            info = p.info
            key = (p.pid, info['create_time'])
            seen.add(key)
            if key not in self.static:                      # new process: its user and command line are the slow reads - once is enough
                self.static[key] = (user_of(p), *command_of(p, info['name']))
            user, shown, full = self.static[key]
            mem = info['memory_info'].rss if info['memory_info'] else 0
            procs[p.pid] = (info['name'] or f'pid {p.pid}', p.pid, cpu, mem, info['num_threads'] or 0, user, shown, info['ppid'], info['create_time'] or 0, full)
        for key in [k for k in self.static if k not in seen]:
            del self.static[key]
        vm = psutil.virtual_memory()
        return {'cpu': psutil.cpu_percent(None), 'cores': psutil.cpu_percent(None, percpu=True), 'mem': (vm.used, vm.total, vm.percent), 'procs': procs}

    @staticmethod
    def kill(pids):
        """Ends each process and everything it started, like the original's kill_proc_tree - asks nicely first, insists after 3 seconds.
           Returns ([(name, pid, how many it had started)], [(pid, name, why not)])"""
        killed, failed = [], []
        for pid in pids:
            try:
                parent = psutil.Process(pid)
                name = parent.name()
                family = [p for p in parent.children(recursive=True) if p.pid != os.getpid()] + [parent]     # never this program, even when it was started by one of them
            except psutil.NoSuchProcess:
                failed.append((pid, f'pid {pid}', 'already gone'))
                continue
            except psutil.AccessDenied:
                failed.append((pid, f'pid {pid}', 'access denied - it needs Administrator'))
                continue
            denied = False
            for p in family:
                try:
                    p.terminate()
                except psutil.NoSuchProcess:
                    pass
                except psutil.AccessDenied:
                    denied = denied or p is parent
            if denied:
                failed.append((pid, name, 'access denied - it needs Administrator'))
                continue
            gone, alive = psutil.wait_procs(family, timeout=3)
            for p in alive:
                try:
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            killed.append((name, pid, len(family) - 1))
        return killed, failed


def user_of(p):
    try:
        return (p.username() or '').split('\\')[-1]                     # DOMAIN\mike -> mike
    except (psutil.Error, OSError):
        return ''


def command_of(p, name):
    """(command line for the table, whole command line).  A python process shows the script it runs, like the CPU Cores widget does"""
    try:
        parts = p.cmdline() or []
    except (psutil.Error, OSError):
        return '', ''
    full = ' '.join(' '.join(parts).split())                       # one line: a command line can hold newlines and tabs
    if name and name.lower().startswith('python') and len(parts) > 1:
        return ' '.join(' '.join(parts[1:]).split()), full
    return full, full


# ---------- --demo: made-up processes, so a screenshot (or trying it out) never shows your own programs and command lines ----------
DEMO_PROCS = [      # name, PID, parent PID, user ('' = hidden, like a system process), CPU % of the whole machine (about), memory MB, threads, command line
    ('System', 4, 0, '', 0.3, 0.2, 284, ''),
    ('Registry', 156, 4, '', 0.0, 61.0, 4, ''),
    ('smss.exe', 548, 4, '', 0.0, 1.1, 2, ''),
    ('csrss.exe', 812, 788, '', 0.1, 6.3, 13, ''),
    ('wininit.exe', 904, 788, '', 0.0, 6.9, 1, ''),
    ('services.exe', 1004, 904, '', 0.1, 11.4, 7, ''),
    ('lsass.exe', 1036, 904, '', 0.1, 24.6, 9, ''),
    ('svchost.exe', 1180, 1004, 'SYSTEM', 0.2, 31.2, 18, r'C:\Windows\system32\svchost.exe -k DcomLaunch -p'),
    ('svchost.exe', 1288, 1004, 'NETWORK SERVICE', 0.1, 18.7, 11, r'C:\Windows\system32\svchost.exe -k RPCSS -p'),
    ('svchost.exe', 1764, 1004, 'SYSTEM', 0.3, 44.0, 25, r'C:\Windows\system32\svchost.exe -k netsvcs -p -s Schedule'),
    ('svchost.exe', 2216, 1004, 'LOCAL SERVICE', 0.1, 14.2, 8, r'C:\Windows\System32\svchost.exe -k LocalService -p -s EventLog'),
    ('svchost.exe', 2840, 1004, 'SYSTEM', 0.0, 12.5, 5, r'C:\Windows\system32\svchost.exe -k LocalSystemNetworkRestricted -p -s SysMain'),
    ('svchost.exe', 3392, 1004, 'NETWORK SERVICE', 0.1, 21.4, 10, r'C:\Windows\System32\svchost.exe -k NetworkService -p -s Dnscache'),
    ('spoolsv.exe', 3140, 1004, 'SYSTEM', 0.0, 16.3, 9, r'C:\Windows\System32\spoolsv.exe'),
    ('MsMpEng.exe', 3612, 1004, '', 8.0, 214.0, 46, ''),
    ('SearchIndexer.exe', 5128, 1004, 'SYSTEM', 0.4, 37.8, 19, r'C:\Windows\system32\SearchIndexer.exe /Embedding'),
    ('dwm.exe', 1452, 904, 'DWM-1', 1.3, 117.0, 21, r'"dwm.exe"'),
    ('audiodg.exe', 6604, 1764, 'LOCAL SERVICE', 0.6, 13.1, 6, r'C:\Windows\system32\AUDIODG.EXE 0x4f8'),
    ('explorer.exe', 7420, 7312, 'you', 0.8, 163.0, 98, r'C:\Windows\Explorer.EXE'),
    ('sihost.exe', 7004, 1764, 'you', 0.1, 27.9, 14, r'sihost.exe'),
    ('ctfmon.exe', 7600, 7004, 'you', 0.1, 20.8, 12, r'"ctfmon.exe"'),
    ('RuntimeBroker.exe', 8580, 1180, 'you', 0.0, 22.4, 7, r'C:\Windows\System32\RuntimeBroker.exe -Embedding'),
    ('SearchHost.exe', 8460, 1180, 'you', 0.0, 95.6, 33, r'"C:\Windows\SystemApps\MicrosoftWindows.Client.CBS_cw5n1h2txyewy\SearchHost.exe" -ServerName:CortanaUI.AppX'),
    ('SecurityHealthSystray.exe', 9876, 7420, 'you', 0.0, 8.9, 3, r'"C:\Windows\System32\SecurityHealthSystray.exe"'),
    ('chrome.exe', 11240, 7420, 'you', 1.1, 311.0, 52, r'"C:\Program Files\Google\Chrome\Application\chrome.exe"'),
    ('chrome.exe', 11392, 11240, 'you', 0.3, 95.8, 18, r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --type=gpu-process'),
    ('chrome.exe', 11408, 11240, 'you', 0.1, 37.9, 12, r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --type=utility --utility-sub-type=network.mojom.NetworkService'),
    ('chrome.exe', 12016, 11240, 'you', 5.8, 283.0, 24, r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --type=renderer --renderer-client-id=7'),
    ('chrome.exe', 12188, 11240, 'you', 0.4, 141.0, 19, r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --type=renderer --renderer-client-id=9'),
    ('chrome.exe', 12904, 11240, 'you', 0.0, 63.7, 15, r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --type=renderer --renderer-client-id=12'),
    ('Code.exe', 14620, 7420, 'you', 0.9, 187.0, 41, r'"C:\Users\you\AppData\Local\Programs\Microsoft VS Code\Code.exe"'),
    ('Code.exe', 14788, 14620, 'you', 0.4, 401.0, 22, r'"C:\Users\you\AppData\Local\Programs\Microsoft VS Code\Code.exe" --type=renderer'),
    ('Dropbox.exe', 10388, 7420, 'you', 0.3, 232.0, 127, r'"C:\Program Files (x86)\Dropbox\Client\Dropbox.exe" /systemstartup'),
    ('WindowsTerminal.exe', 16044, 7420, 'you', 0.1, 73.5, 25, r'"C:\Program Files\WindowsApps\Microsoft.WindowsTerminal_8wekyb3d8bbwe\WindowsTerminal.exe"'),
    ('powershell.exe', 16236, 16044, 'you', 0.0, 71.8, 13, r'"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"'),
    ('ffmpeg.exe', 17452, 16236, 'you', 27.0, 486.0, 34, r'ffmpeg -i holiday.mov -c:v libx265 -crf 22 -preset slow holiday.mp4'),
    ('python.exe', 19408, 16236, 'you', 3.1, 121.0, 9, r'C:\Python313\python.exe -m pip install --upgrade psgplayground'),
    ('pythonw.exe', 18820, 7420, 'you', 0.4, 57.6, 6, r'C:\Python313\pythonw.exe C:\Users\you\Playground\psgdock.pyw'),
    ('pythonw.exe', 18944, 18820, 'you', 0.6, 40.8, 4, r'C:\Python313\pythonw.exe C:\Users\you\Playground\cpu_cores_widget.pyw'),
    ('pythonw.exe', 19060, 18820, 'you', 0.1, 35.9, 3, r'C:\Python313\pythonw.exe C:\Users\you\Playground\clock_widget.pyw'),
    ('pythonw.exe', 19172, 18820, 'you', 0.2, 46.7, 5, r'C:\Python313\pythonw.exe C:\Users\you\Playground\github_repo_watch.pyw'),
    ('pythonw.exe', 19520, 18820, 'you', 0.9, 63.9, 7, r'C:\Python313\pythonw.exe C:\Users\you\Playground\task_manager.pyw --demo')]
DEMO_MEMORY = 32 * 2 ** 30            # the made-up PC's memory


class DemoSampler(Sampler):
    """--demo: the answers a Sampler gives, about DEMO_PROCS - their CPU wanders a little each time.  Kill only takes them off the list, with what they
       started; a hidden one (a system process) says access denied, as it would without Administrator"""
    def __init__(self, window):
        super().__init__(window)
        self.random = random.Random(2026)
        boot = time.time() - 3 * 3600
        self.procs, self.base = {}, {}
        for i, (name, pid, ppid, user, cpu, mb, threads, full) in enumerate(DEMO_PROCS):
            shown = full.split(' ', 1)[1] if name.lower().startswith('python') and ' ' in full else full      # a python process shows its script, as for real
            started = boot + (i * 37 if user in ('', 'SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE', 'DWM-1') else 900 + i * 211)
            self.procs[pid] = [name, pid, cpu, mb * 2 ** 20, threads, user, shown, ppid, started, full]
            self.base[pid] = cpu

    def sample(self):
        rnd, procs = self.random, {}
        for pid, p in self.procs.items():
            base = self.base[pid]
            p[CPU] = round(base * rnd.uniform(0.6, 1.4), 1) if base >= 0.5 else round(rnd.uniform(0, base * 3), 1) if rnd.random() < 0.35 else 0.0
            p[MEM] = max(2 ** 20, p[MEM] * rnd.uniform(0.995, 1.006))
            procs[pid] = tuple(p)
        total = min(100.0, sum(r[CPU] for r in procs.values()))
        cores = [max(0.0, min(100.0, total + rnd.gauss(0, 9))) for _ in range(NUM_CPUS)]
        cores[rnd.randrange(NUM_CPUS)] = rnd.uniform(78, 96)                      # ffmpeg keeps one core busy
        used = 9.6 * 2 ** 30 + sum(r[MEM] for r in procs.values())
        return {'cpu': total, 'cores': cores, 'mem': (used, DEMO_MEMORY, used / DEMO_MEMORY * 100), 'procs': procs}

    def kill(self, pids):
        killed, failed = [], []
        for pid in pids:
            p = self.procs.get(pid)
            if p is None:
                failed.append((pid, f'pid {pid}', 'already gone'))
            elif not p[USER]:
                failed.append((pid, p[NAME], 'access denied - it needs Administrator'))
            else:
                family, i = [pid], 0
                while i < len(family):                                              # everything it started, and what those started
                    family += [c for c, r in self.procs.items() if r[PPID] == family[i] and c not in family]
                    i += 1
                for q in family:
                    del self.procs[q]
                killed.append((p[NAME], pid, len(family) - 1))
        return killed, failed


def is_python(r):
    return r[NAME].lower().startswith('python')


def request_sample():
    if not G.busy:
        G.busy = True
        G.sampler.jobs.put(('sample', None))


# ---------- colors ----------
def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, f):
    """Blend two hex colors, f=0 -> c1, f=1 -> c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(rgb(c1), rgb(c2)))


def is_light(color):
    r, g, b = rgb(color)
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


def load_color(pct):
    """green up to 45%, amber around 72, red at 100 - smooth in between"""
    for (p0, c0), (p1, c1) in zip(LOAD_STOPS, LOAD_STOPS[1:]):
        if pct <= p1:
            return mix(c0, c1, (pct - p0) / (p1 - p0))
    return LOAD_STOPS[-1][1]


def ui_colors():
    """Every color the window uses, worked out from the theme's five (at the Brightness level) - a light theme gets darker status colors"""
    T = theme_colors()
    light = is_light(T['card'])
    status = lambda c, f=0.25: mix(c, '#000000', f) if light else c
    lift = lambda f: mix(T['card'], T['text'], f)
    return {'bg': T['card'], 'text': T['text'], 'dim': T['dim'], 'border': T['border'], 'track': T['track'], 'light': light,
            'panel': lift(0.045), 'field': lift(0.10), 'stripe': lift(0.035), 'head': lift(0.075), 'button': lift(0.14), 'button_hover': lift(0.22),
            'warm': status('#e8a33d', 0.3), 'hot': status('#ff6b6b', 0.3), 'python': status(C_PYTHON, 0.3), 'memory': status(C_MEMORY), 'status': status}


def apply_psg_theme():
    """Puts the theme's colors into a PySimpleGUI theme, so the window and its popups start out right"""
    sg.theme_add_new('TaskManager', psg_theme())
    sg.theme('TaskManager')


def psg_theme():
    """A PySimpleGUI theme in the same colors, so the window and its popups start out right"""
    C = ui_colors()
    return {'BACKGROUND': C['bg'], 'TEXT': C['text'], 'INPUT': C['field'], 'TEXT_INPUT': C['text'], 'SCROLL': C['button'], 'BUTTON': (C['text'], C['button']),
            'PROGRESS': (C_SEL, C['field']), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}


# ---------- the cards across the top ----------
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


def render_header():
    """CPU with its history, every core, memory with its history and the process count, as four cards - drawn twice the size and shrunk, so edges are smooth"""
    C, s = G.colors, G.scale
    W, H, k = max(300, G.header_w), round(HEADER_H * s), 2
    u = s * k                                                               # one design pixel, in drawing pixels
    im = Image.new('RGB', (W * k, H * k), C['bg'])
    d = ImageDraw.Draw(im)
    margin, gap = 14 * u, 10 * u
    avail = W * k - 2 * margin - 3 * gap
    x = margin
    for share, draw in ((0.30, draw_cpu), (0.27, draw_cores), (0.27, draw_memory), (0.16, draw_processes)):
        box = (x, 10 * u, x + avail * share, H * k - 4 * u)
        d.rounded_rectangle(box, radius=RADIUS * u, fill=C['panel'], outline=C['border'], width=max(1, round(u)))
        draw(d, box, u)
        x += avail * share + gap
    buf = io.BytesIO()
    im.resize((W, H), Image.LANCZOS).save(buf, 'PNG')
    return buf.getvalue()


def card_label(d, box, u, text, color, right=''):
    """colored dot + small caps label at the top of a card, and an optional dim note on the right"""
    x0, y0, x1, _ = box
    cy = y0 + 17 * u
    d.ellipse((x0 + 14 * u, cy - 3.5 * u, x0 + 21 * u, cy + 3.5 * u), fill=color)
    d.text((x0 + 28 * u, cy), text, font=font(True, round(11 * u)), fill=G.colors['dim'], anchor='lm')
    if right:
        d.text((x1 - 14 * u, cy), right, font=font(False, round(11 * u)), fill=G.colors['dim'], anchor='rm')


def big_number(d, x, y, number, unit, u):
    """a big number with a smaller unit after it, on one baseline"""
    f_big = font(True, round(30 * u))
    d.text((x, y), number, font=f_big, fill=G.colors['text'], anchor='ls')
    if unit:
        d.text((x + d.textlength(number, font=f_big) + 2 * u, y), unit, font=font(True, round(14 * u)), fill=G.colors['dim'], anchor='ls')


def detail(d, x, y, text, u):
    d.text((x, y), text, font=font(False, round(11 * u)), fill=G.colors['dim'], anchor='lm')


def sparkline(d, box, values, color, u):
    """the history as a filled line - the newest reading at the right edge"""
    x0, y0, x1, y1 = box
    if x1 - x0 < 20 * u or len(values) < 2:
        return
    step = (x1 - x0) / (HISTORY - 1)
    pts = [(x1 - (len(values) - 1 - i) * step, y1 - max(0.0, min(100.0, v)) / 100 * (y1 - y0)) for i, v in enumerate(values)]
    d.line((x0, y1, x1, y1), fill=G.colors['track'], width=max(1, round(u)))
    d.polygon([(pts[0][0], y1)] + pts + [(pts[-1][0], y1)], fill=mix(color, G.colors['panel'], 0.78))
    d.line(pts, fill=color, width=max(1, round(1.6 * u)), joint='curve')


def draw_cpu(d, box, u):
    x0, y0, x1, y1 = box
    pct = G.sample['cpu'] if G.sample else 0.0
    color = G.colors['status'](load_color(pct))
    card_label(d, box, u, 'CPU', color)
    big_number(d, x0 + 14 * u, y0 + 57 * u, f'{pct:.0f}', '%', u)
    detail(d, x0 + 14 * u, y0 + 71 * u, f'{NUM_CPUS} logical cores', u)
    sparkline(d, (x0 + (x1 - x0) * 0.45, y0 + 26 * u, x1 - 14 * u, y1 - 12 * u), G.cpu_hist, color, u)


def draw_cores(d, box, u):
    x0, y0, x1, y1 = box
    cores = G.sample['cores'] if G.sample else [0.0] * NUM_CPUS
    busiest = max(cores) if cores else 0
    card_label(d, box, u, 'CORES', G.colors['status'](load_color(busiest)), f'busiest {busiest:.0f}%')
    ax0, ax1, ay0, ay1 = x0 + 14 * u, x1 - 14 * u, y0 + 32 * u, y1 - 12 * u
    n = max(1, len(cores))
    gap = max(u, min(4 * u, (ax1 - ax0) / n * 0.3))
    bw = max(u, min(22 * u, (ax1 - ax0 - gap * (n - 1)) / n))      # a few cores get bars of a sensible width, centered
    left = ax0 + (ax1 - ax0 - (n * bw + (n - 1) * gap)) / 2
    for i, pct in enumerate(cores):
        bx = left + i * (bw + gap)
        r = min(bw / 2, 2 * u)
        d.rounded_rectangle((bx, ay0, bx + bw, ay1), radius=r, fill=G.colors['track'])
        top = ay1 - (ay1 - ay0) * max(0.0, min(100.0, pct)) / 100
        if ay1 - top >= u:
            d.rounded_rectangle((bx, top, bx + bw, ay1), radius=min(r, (ay1 - top) / 2), fill=G.colors['status'](load_color(pct)))


def draw_memory(d, box, u):
    x0, y0, x1, y1 = box
    used, total, pct = G.sample['mem'] if G.sample else (0, 1, 0.0)
    color = G.colors['memory']
    card_label(d, box, u, 'MEMORY', color)
    big_number(d, x0 + 14 * u, y0 + 57 * u, f'{pct:.0f}', '%', u)
    detail(d, x0 + 14 * u, y0 + 71 * u, f'{used / 2 ** 30:.1f} of {total / 2 ** 30:.1f} GB', u)
    sparkline(d, (x0 + (x1 - x0) * 0.50, y0 + 26 * u, x1 - 14 * u, y1 - 12 * u), G.mem_hist, color, u)


def draw_processes(d, box, u):
    x0, y0, x1, y1 = box
    procs = G.sample['procs'] if G.sample else {}
    card_label(d, box, u, 'PROCESSES', G.colors['python'])
    big_number(d, x0 + 14 * u, y0 + 57 * u, f'{len(procs)}', '', u)
    detail(d, x0 + 14 * u, y0 + 71 * u, f'{sum(r[THREADS] for r in procs.values()):,} threads', u)


def redraw_header(window):
    window[K_HEADER].update(data=render_header())


# ---------- the table ----------
def fmt_bytes(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f'{n:.0f} {unit}' if unit in ('B', 'KB') else f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} TB'


def cells(r):
    return r[NAME], r[PID], f'{r[CPU]:.1f}' if r[CPU] >= 0.05 else '0', fmt_bytes(r[MEM]) if r[MEM] else '', r[THREADS], r[USER], r[CMD]


def row_tags(r, i):
    tags = ('stripe',) if i % 2 else ()
    if r[CPU] >= HOT:
        return tags + ('hot',)
    if r[CPU] >= WARM:
        return tags + ('warm',)
    return tags + ('python',) if is_python(r) else tags


def matches(r):
    f = G.filter
    return not f or f in r[NAME].lower() or f in r[FULL].lower() or f in r[USER].lower() or f == str(r[PID])


def shown_rows():
    """The rows that pass the filter (and Python only), in the chosen order - ties stay in name order"""
    rows = [r for r in G.sample['procs'].values() if (is_python(r) or not G.python_only) and matches(r)]
    rows.sort(key=lambda r: (r[NAME].lower(), r[PID]))
    rows.sort(key=SORT_KEYS[G.sort[0]], reverse=G.sort[1])
    return rows


def update_table(window):
    """Brings the table up to date IN PLACE: one tree item per process (its iid is the PID), changed only when its cells change.  Rebuilding the whole
       table every refresh is what lost the selection and the scroll position, and made the old Process Killer slow"""
    if not G.sample:
        return
    tree = window[K_TABLE].Widget
    rows = shown_rows()
    want = [str(r[PID]) for r in rows]
    wanted = set(want)
    for iid in [i for i in G.rows if int(i) not in G.sample['procs']]:     # the process has ended
        tree.delete(iid)
        del G.rows[iid]
    hidden = [i for i in tree.get_children('') if i not in wanted]           # still running, but filtered out
    if hidden:
        tree.selection_remove(*hidden)                                       # never kill something you can't see
        tree.detach(*hidden)
    for i, r in enumerate(rows):
        iid, cell, tags = want[i], cells(r), row_tags(r, i)
        if iid not in G.rows:
            tree.insert('', i, iid=iid, values=cell, tags=tags)
        elif G.rows[iid] != (cell, tags):
            tree.item(iid, values=cell, tags=tags)
        G.rows[iid] = (cell, tags)
    if want != G.order or hidden:                                            # put them in order - also brings back rows the filter had hidden
        for i, iid in enumerate(want):
            tree.move(iid, '', i)
        G.order = want
    G.shown = len(want)


def show_headings(window):
    """the sort column's heading gets an arrow"""
    tree = window[K_TABLE].Widget
    col, big_first = G.sort
    for i, h in enumerate(HEADINGS):
        tree.heading(h, text=f'{h}  {"▼" if big_first else "▲"}' if i == col else h, anchor='w' if COLUMNS[i][2] == 'l' else 'e')


def sort_by(window, col):
    G.sort = [col, not G.sort[1]] if col == G.sort[0] else [col, col in BIG_FIRST]
    sg.user_settings_set_entry(K_SORT, G.sort)
    show_headings(window)
    update_table(window)


def selected_pids(window):
    return [int(i) for i in window[K_TABLE].Widget.selection() if i.isdigit()]


def move_selection(window, step):
    """Up / Down in the filter box move through the list"""
    tree = window[K_TABLE].Widget
    items = tree.get_children('')
    if items:
        focus = tree.focus()
        i = items.index(focus) + step if focus in items else (0 if step > 0 else len(items) - 1)
        i = max(0, min(len(items) - 1, i))
        tree.selection_set(items[i])
        tree.focus(items[i])
        tree.see(items[i])
    return 'break'


def show_details(window):
    """Two lines under the list about the selected process: who it is, then its whole command line (select and Ctrl+C to copy)"""
    tree = window[K_TABLE].Widget
    sel = [i for i in tree.selection() if i.isdigit()]
    procs = G.sample['procs'] if G.sample else {}
    rows = [procs[int(i)] for i in sel if int(i) in procs]
    focus = tree.focus()
    r = procs.get(int(focus)) if focus in sel and focus.isdigit() else (rows[0] if rows else None)
    if len(rows) > 1:
        names = ', '.join(f'{x[NAME]} ({x[PID]})' for x in rows[:6]) + (' …' if len(rows) > 6 else '')
        head, tail = f'{len(rows)} selected:  {names}', 'Kill ends them all, with everything they started'
    elif r:
        parent = procs.get(r[PPID])
        started = time.strftime('%a %H:%M:%S', time.localtime(r[STARTED])) if r[STARTED] else '?'
        head = (f'{r[NAME]}    PID {r[PID]}    parent {r[PPID]}{f" ({parent[NAME]})" if parent else ""}    {r[USER] or "user hidden"}    started {started}    '
                f'{r[THREADS]} thread{"" if r[THREADS] == 1 else "s"}    {r[CPU]:.1f}% CPU    {fmt_bytes(r[MEM])}')
        tail = r[FULL] or 'no command line shown - a system process, or one that belongs to another user (run as Administrator to see those)'
    else:
        head, tail = 'Select a process to see its details here', 'Type to filter  ·  click a heading to sort  ·  Delete or Kill ends the selected processes'
    if (head, tail) != G.details:
        G.details = (head, tail)
        text = window[K_DETAILS].Widget
        text.configure(state='normal')
        text.delete('1.0', 'end')
        text.insert('end', head, 'head')
        text.insert('end', '\n' + tail, 'dim')
        text.configure(state='disabled')


def show_status(window):
    total = len(G.sample['procs']) if G.sample else 0
    n_sel = len(window[K_TABLE].Widget.selection())
    parts = [('measuring…' if not G.sample else f'{G.shown} of {total} processes' if G.shown != total else f'{total} processes')]
    if n_sel:
        parts.append(f'{n_sel} selected')
    parts.append('paused' if G.paused else f'updates every {G.refresh} s')
    if DEMO:
        parts.append('demo - made-up processes')
    bad = False
    if G.message and time.time() < G.message_until:
        parts.append(G.message)
        bad = G.message_bad
    window[K_STATUS].update('    ·    '.join(parts), text_color=G.colors['hot'] if bad else G.colors['dim'])


def apply_sample(window, sample):
    G.busy = False
    G.sample = sample
    G.cpu_hist.append(sample['cpu'])
    G.mem_hist.append(sample['mem'][2])
    update_table(window)
    redraw_header(window)
    show_status(window)
    show_details(window)


# ---------- killing ----------
def kill_selected(window):
    pids = [p for p in selected_pids(window) if p != os.getpid()]
    if not pids:
        say(window, 'select a process first', bad=True)
        return
    procs = G.sample['procs'] if G.sample else {}
    names = [procs[p][NAME] if p in procs else f'pid {p}' for p in pids]
    if G.confirm:
        listing = '\n'.join(f'{n}    (PID {p})' for n, p in list(zip(names, pids))[:15]) + (f'\n… and {len(pids) - 15} more' if len(pids) > 15 else '')
        question = f'Kill {"this process" if len(pids) == 1 else f"these {len(pids)} processes"} and everything {"it" if len(pids) == 1 else "they"} started?'
        answer = sg.popup_yes_no(question, listing, title='Kill', keep_on_top=True, font=FONT, icon=ICON)
        window.force_focus()
        if answer != 'Yes':
            return
    say(window, f'killing {", ".join(names[:3])}{" …" if len(names) > 3 else ""}')
    G.sampler.jobs.put(('kill', pids))


def kill_result(window, killed, failed):
    parts = []
    if killed:
        parts.append('killed ' + ', '.join(f'{n} ({p})' + (f' + {c} it started' if c else '') for n, p, c in killed[:3]) + (' …' if len(killed) > 3 else ''))
    if failed:
        parts.append('could not kill ' + ', '.join(f'{n} ({p}): {why}' for p, n, why in failed[:2]) + (' …' if len(failed) > 2 else ''))
    say(window, ';   '.join(parts), bad=bool(failed))
    request_sample()


def say(window, message, bad=False):
    """a message at the end of the status line for 10 seconds"""
    G.message, G.message_until, G.message_bad = message, time.time() + 10, bad
    show_status(window)


# ---------- painting the window ----------
def paint(window):
    """Colors every part of the window from the theme at the Brightness level - when it opens and whenever the theme or the Brightness changes"""
    C = G.colors = ui_colors()

    def walk(w):                                                     # backgrounds of the window and every frame / label in it
        if w.winfo_class() in ('Tk', 'Toplevel', 'Frame', 'Label', 'Canvas'):
            try:
                w.configure(background=C['bg'])
            except tk.TclError:
                pass
        for child in w.winfo_children():
            walk(child)
    walk(window.TKroot)
    window[K_FILTER_LABEL].Widget.configure(foreground=C['text'])
    window[K_FILTER].Widget.configure(background=C['field'], foreground=C['text'], insertbackground=C['text'], selectbackground=C_SEL, selectforeground='#ffffff',
                                      relief='flat', highlightthickness=round(2 * G.scale), highlightbackground=C['field'], highlightcolor=C_SEL)
    for key in (K_CLEAR, K_PYTHON, K_PAUSE, K_KILL):
        paint_button(window, key)
    text = window[K_DETAILS].Widget
    text.configure(background=C['bg'], foreground=C['text'], selectbackground=C_SEL, selectforeground='#ffffff', inactiveselectbackground=C_SEL,
                   highlightthickness=0, relief='flat', insertbackground=C['bg'])
    text.tag_configure('head', foreground=C['text'], font=FONT)
    text.tag_configure('dim', foreground=C['dim'], font=FONT_SMALL)
    style, table = ttk.Style(), window[K_TABLE]
    name = table.table_ttk_style_name
    style.configure(name, background=C['bg'], fieldbackground=C['bg'], foreground=C['text'], borderwidth=0, relief='flat', rowheight=G.row_h)
    style.map(name, background=[('selected', C_SEL)], foreground=[('selected', '#ffffff')])
    style.configure(name + '.Heading', background=C['head'], foreground=C['dim'], relief='flat', borderwidth=0, padding=(6, round(5 * G.scale)))
    style.map(name + '.Heading', background=[('active', C['button'])], foreground=[('active', C['text'])], relief=[('pressed', 'flat'), ('active', 'flat')])
    tree = table.Widget
    tree.tag_configure('stripe', background=C['stripe'])
    tree.tag_configure('warm', foreground=C['warm'])
    tree.tag_configure('hot', foreground=C['hot'])
    tree.tag_configure('python', foreground=C['python'])
    for bar in [getattr(table, 'vsb_style_name', None), getattr(table, 'hsb_style_name', None)]:
        if bar:
            style.configure(bar, troughcolor=C['bg'], background=C['button'], bordercolor=C['bg'], arrowcolor=C['dim'], lightcolor=C['button'], darkcolor=C['button'],
                            relief='flat', gripcount=0)
            style.map(bar, background=[('pressed', C_SEL), ('active', C['button_hover'])], arrowcolor=[('active', C['text'])])
    grip = window[K_GRIP].Widget
    style.configure(grip.cget('style') or 'TSizegrip', background=C['bg'])
    show_status(window)
    G.details = None                                                 # the details redraw in the new colors
    show_details(window)


def paint_button(window, key):
    C = G.colors
    if key == K_KILL:
        bg, fg, hover = C_KILL, '#ffffff', C_KILL_HOVER
    elif (key == K_PYTHON and G.python_only) or (key == K_PAUSE and G.paused):          # a toggle that is on lights up
        bg, fg, hover = C_SEL, '#ffffff', mix(C_SEL, '#ffffff', 0.15)
    else:
        bg, fg, hover = C['button'], C['text'], C['button_hover']
    G.hover[key] = (bg, hover)
    window[key].Widget.configure(background=bg, foreground=fg, activebackground=hover, activeforeground=fg, highlightthickness=0, borderwidth=0, relief='flat',
                                 padx=round(10 * G.scale), pady=round(3 * G.scale))


def python_label():
    return f'{"☑" if G.python_only else "☐"}  Python only'


def pause_label():
    return '▶  Resume' if G.paused else '❚❚  Pause'


# ---------- right-click menu ----------
def make_menu():
    """Right-click menu with a check mark on the current choices - every label starts with a tick or the same width of spaces, so they line up"""
    tick = lambda on: '✓ ' if on else '    '
    theme = lambda n: f'{tick(n == G.theme)}{n}::{KT_THEME(n)}'
    return ['', [f'    Kill selected::{K_KILL}', '---',
                 f'    Refresh now::{K_REFRESH_NOW}', '    Refresh every', [f'{tick(s == G.refresh)}{s} s::{KT_REFRESH(s)}' for s in REFRESHES],
                 f'{tick(G.on_top)}Keep on top::{K_TOP}', f'{tick(G.confirm)}Ask before killing::{K_CONFIRM}', '---',
                 '    Theme', [theme(n) for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],
                 f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
                 '---', '    Edit Me::Edit Me', '    Version::Version', f'    Exit::{K_EXIT}']]


def menu_colors():
    """Right-click menu background and text: the window's own colors (background lifted a touch)"""
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
    """tk draws menus Windows-gray: recolor every right-click menu (PySimpleGUI gives each element its own copy) and their sub-menus in the window's colors,
       flat and compact, with a chip beside each theme name"""
    bg, fg = menu_colors()

    def style(menu):
        menu.configure(bg=bg, fg=fg, activebackground=C_MENU_SEL, activeforeground='#ffffff', bd=0, activeborderwidth=1, relief='flat', font=FONT_MENU)
        first_light = True
        for i in range(menu.index('end') + 1 if menu.index('end') is not None else 0):
            name = menu.entrycget(i, 'label').lstrip('✓ ') if menu.type(i) == 'command' else None
            if name in THEMES:
                menu.entryconfigure(i, image=theme_swatch(name), compound='left')
                if first_light and is_light(THEMES[name]['card']):
                    menu.entryconfigure(i, columnbreak=1)                     # the light themes get a column of their own
                    first_light = False
        for child in menu.winfo_children():
            if isinstance(child, tk.Menu):
                style(child)
    done = set()
    for menu in [window.TKRightClickMenu] + [getattr(e, 'TKRightClickMenu', None) for e in window.element_list()]:
        if menu is not None and str(menu) not in done:
            done.add(str(menu))
            style(menu)


def set_menus(window):
    """Rebuild the right-click menu (check marks, theme chips) on every element that has one, then style them all"""
    menu = make_menu()
    window.RightClickMenu = menu
    first = True
    for e in window.element_list():
        if getattr(e, 'TKRightClickMenu', None) is not None:
            e.set_right_click_menu(menu, propogate_to_window=first)
            first = False
    style_menus(window)


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


def redraw(window):
    """The Brightness panel calls this as the knob moves: everything takes the new colors"""
    paint(window)
    redraw_header(window)


def keep_going(window, event, values):
    """While the Brightness panel is open the list keeps updating - anything else closes the panel and goes back to the main loop"""
    if event == K_TICK:
        request_sample()
    elif event == K_SAMPLE:
        apply_sample(window, values[event])
    elif event == K_RESIZED:
        G.header_w = values[event]
        redraw_header(window)
    else:
        return False
    return True


# ---------- the window ----------
def icon_everywhere(window):
    """Windows: this program's icon becomes tk's default (class) icon as well.  tk's own default is the feather, and the taskbar once showed the
       feather instead of the Task Manager icon while the title bar still had the right one - now the fallback is the same picture"""
    if not sg.running_windows():
        return
    try:
        path = os.path.join(tempfile.gettempdir(), 'task_manager_icon.ico')
        Image.open(io.BytesIO(base64.b64decode(ICON))).save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)])
        window.TKroot.iconbitmap(default=path)
    except Exception:
        pass


def start_size():
    """The size saved last time, kept on the screen - None the first time, so the table's columns decide"""
    size = sg.user_settings_get_entry(K_SIZE, None)
    if not (isinstance(size, (list, tuple)) and len(size) == 2 and all(isinstance(v, int) for v in size)):
        return None, None
    screen_w, screen_h = sg.Window.get_screen_size()
    return min(size[0], screen_w), min(size[1], screen_h - 40)


def make_window():
    C = G.colors = ui_colors()
    apply_psg_theme()
    pad_top = (10, 6)
    toolbar = [sg.Text('Filter', key=K_FILTER_LABEL, font=FONT, pad=((14, 8), pad_top)),
               sg.Input(G.filter, key=K_FILTER, size=(30, 1), font=FONT, enable_events=True, border_width=0, pad=((0, 2), pad_top)),
               sg.Button('✕', key=K_CLEAR, font=FONT, border_width=0, pad=((0, 16), pad_top)),
               sg.Button(python_label(), key=K_PYTHON, font=FONT, border_width=0, pad=((0, 6), pad_top)),
               sg.Button(pause_label(), key=K_PAUSE, font=FONT, border_width=0, pad=((0, 6), pad_top)),
               sg.Push(),
               sg.Button('Kill', key=K_KILL, font=FONT_BOLD, border_width=0, pad=((6, 14), pad_top))]
    table = sg.Table([], headings=HEADINGS, col_widths=[c[1] for c in COLUMNS], cols_justification=[c[2] for c in COLUMNS], auto_size_columns=False, num_rows=18,
                     key=K_TABLE, font=FONT, header_font=FONT_BOLD, justification='left', select_mode=sg.TABLE_SELECT_MODE_EXTENDED, enable_events=True,
                     enable_click_events=True, right_click_selects=True, expand_x=True, expand_y=True, border_width=0, header_relief=sg.RELIEF_FLAT, header_border_width=0,
                     background_color=C['bg'], text_color=C['text'], header_background_color=C['head'], header_text_color=C['dim'], selected_row_colors=('#ffffff', C_SEL),
                     pad=((14, 14), (4, 0)))
    details = sg.Multiline('', key=K_DETAILS, size=(80, 2), font=FONT, disabled=True, no_scrollbar=True, border_width=0, expand_x=True, background_color=C['bg'],
                           text_color=C['text'], pad=((16, 14), (8, 0)))
    status = [sg.Text('measuring…', key=K_STATUS, font=FONT_SMALL, text_color=C['dim'], expand_x=True, pad=((16, 0), (4, 6))), sg.Sizegrip(key=K_GRIP)]
    blank = Image.new('RGB', (8, HEADER_H), C['bg'])
    buf = io.BytesIO()
    blank.save(buf, 'PNG')
    layout = [[sg.Image(data=buf.getvalue(), key=K_HEADER, pad=(0, 0), background_color=C['bg'])],
              toolbar, [table], [details], status]
    menu_bg, menu_fg = menu_colors()
    title = f'{APP_NAME} - demo   v{VERSION}' if DEMO else f'{APP_NAME}   v{VERSION}'
    window = sg.Window(title, layout, icon=ICON, resizable=True, finalize=True, margins=(0, 0), keep_on_top=G.on_top, auto_save_location=True,
                       enable_close_attempted_event=True, size=start_size(), background_color=C['bg'], right_click_menu=make_menu(),
                       right_click_menu_background_color=menu_bg, right_click_menu_text_color=menu_fg, right_click_menu_selected_colors=('#ffffff', C_SEL),
                       right_click_menu_font=FONT_MENU, use_ttk_buttons=False)
    G.window = window
    root = window.TKroot
    icon_everywhere(window)
    G.scale = max(1.0, root.winfo_fpixels('1i') / 96)
    G.row_h = round(tkfont.Font(root=root, font=FONT).metrics('linespace') * 1.45)
    window.set_min_size((round(620 * G.scale), round(420 * G.scale)))
    tree = window[K_TABLE].Widget
    least = round(36 * G.scale)
    for i, h in enumerate(HEADINGS):                                 # only Command line stretches with the window - the numbers keep their width
        tree.column(h, stretch=i == CMD, minwidth=least)
    widths = sg.user_settings_get_entry(K_WIDTHS, None)
    if isinstance(widths, list) and len(widths) == len(HEADINGS) and all(isinstance(w, int) for w in widths):
        for h, w in zip(HEADINGS, widths):
            tree.column(h, width=max(least, w))
    paint(window)
    style_menus(window)
    show_headings(window)
    bind_keys(window)
    root.update_idletasks()
    G.header_w = root.winfo_width() if root.winfo_width() > 1 else root.winfo_reqwidth()
    redraw_header(window)
    if start_size() == (None, None):                                 # first run: keep the size the layout asked for ...
        root.update_idletasks()
        root.geometry(f'{root.winfo_reqwidth()}x{root.winfo_reqheight()}')
    tree.configure(height=5)                                         # ... while the list asks for only a few rows - so a smaller window shrinks the list, not the lines under it
    return window


def bind_keys(window):
    window.bind('<Escape>', K_EXIT)
    window.bind('<Prior>', K_PGUP)
    window.bind('<Next>', K_PGDN)
    window.bind('<Home>', K_HOME)
    window.bind('<End>', K_END)
    window.bind('<F5>', K_REFRESH_NOW)
    window.bind('<Control-f>', K_FIND)
    tree, entry = window[K_TABLE].Widget, window[K_FILTER].Widget
    tree.bind('<Delete>', lambda e: window.write_event_value(K_KILL, None))

    def type_to_filter(e):                                           # a letter typed on the list goes to the filter box
        if e.char and e.char.isprintable() and not e.state & 0x4 and e.keysym not in ('space',):
            entry.focus_set()
            entry.insert('end', e.char)
            window.write_event_value(K_FILTER, entry.get())
            return 'break'
    tree.bind('<Key>', type_to_filter, add='+')
    entry.bind('<Down>', lambda e: move_selection(window, 1))
    entry.bind('<Up>', lambda e: move_selection(window, -1))
    for key in (K_CLEAR, K_PYTHON, K_PAUSE, K_KILL):                 # hover color
        w = window[key].Widget
        w.bind('<Enter>', lambda e, k=key: e.widget.configure(background=G.hover[k][1]), add='+')
        w.bind('<Leave>', lambda e, k=key: e.widget.configure(background=G.hover[k][0]), add='+')

    def configured(e):                                               # redraw the cards once the window stops changing width
        if e.widget is window.TKroot and e.width != G.header_w:
            if G.resize_job:
                window.TKroot.after_cancel(G.resize_job)
            G.resize_job = window.TKroot.after(150, lambda w=e.width: window.write_event_value(K_RESIZED, w))
    window.TKroot.bind('<Configure>', configured, add='+')


def start_timer(window):
    if G.timer is not None:
        window.timer_stop(G.timer)
        G.timer = None
    if not G.paused:
        G.timer = window.timer_start(G.refresh * 1000, key=K_TICK)


def save_window(window):
    try:
        sg.user_settings_set_entry(K_SIZE, list(window.size))
        tree = window[K_TABLE].Widget
        sg.user_settings_set_entry(K_WIDTHS, [tree.column(h, 'width') for h in HEADINGS])
    except Exception:
        pass


def load_settings():
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    G.refresh = sg.user_settings_get_entry(K_REFRESH, 2)
    G.refresh = G.refresh if G.refresh in REFRESHES else 2
    G.python_only = bool(sg.user_settings_get_entry(K_PYTHON, False))
    G.on_top = bool(sg.user_settings_get_entry(K_TOP, False))
    G.confirm = bool(sg.user_settings_get_entry(K_CONFIRM, False))
    sort = sg.user_settings_get_entry(K_SORT, [CPU, True])
    G.sort = list(sort) if isinstance(sort, (list, tuple)) and len(sort) == 2 and sort[0] in SORT_KEYS else [CPU, True]


def main():
    sg.set_options(dpi_awareness=True)
    load_settings()
    window = make_window()
    G.sampler = (DemoSampler if DEMO else Sampler)(window)
    G.sampler.start()
    request_sample()                                                 # the first measurement only sets the CPU baseline ...
    window.timer_start(700, key=K_TICK, repeating=False)             # ... so measure again shortly after, then every G.refresh seconds
    start_timer(window)
    window[K_TABLE].Widget.focus_set()

    pending = None                                                   # an event that came in while the Brightness panel was open
    while True:
        event, values = pending or window.read()
        pending = None
        menu_key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event             # right-click items come back as 'label::key'
        if menu_key in (K_EXIT, sg.WINDOW_CLOSED, sg.WIN_CLOSE_ATTEMPTED_EVENT):
            if event != sg.WINDOW_CLOSED:
                save_window(window)
            break
        if event == K_TICK:
            request_sample()
        elif event == K_SAMPLE:
            apply_sample(window, values[event])
        elif event == K_KILLED:
            kill_result(window, *values[event])
        elif event == K_THREAD_ERROR:
            sg.popup_error_with_traceback('The measuring thread crashed', values[event])
            G.busy = False
        elif event == K_RESIZED:
            G.header_w = values[event]
            redraw_header(window)
        elif menu_key == K_KILL:
            kill_selected(window)
        elif isinstance(event, tuple) and event[0] == K_TABLE:                                  # a click on the table: sort when it was on a heading
            row, col = event[2]
            if row == -1 and col is not None and 0 <= col < len(HEADINGS):
                sort_by(window, col)
            else:                                                                               # a quick click can arrive instead of the selection event
                show_details(window)
                show_status(window)
        elif event == K_TABLE:                                                                  # the selection changed
            show_details(window)
            show_status(window)
        elif event == K_FILTER:
            G.filter = (values[event] or '').strip().lower()
            update_table(window)
            show_status(window)
            show_details(window)
        elif event == K_CLEAR:
            window[K_FILTER].update('')
            G.filter = ''
            update_table(window)
            show_status(window)
            window[K_FILTER].set_focus()
        elif event == K_PYTHON:
            G.python_only = not G.python_only
            sg.user_settings_set_entry(K_PYTHON, G.python_only)
            window[K_PYTHON].update(python_label())
            paint_button(window, K_PYTHON)
            update_table(window)
            show_status(window)
        elif event == K_PAUSE:
            G.paused = not G.paused
            window[K_PAUSE].update(pause_label())
            paint_button(window, K_PAUSE)
            start_timer(window)
            if not G.paused:
                request_sample()
            show_status(window)
        elif event in (K_PGUP, K_PGDN):
            if window.TKroot.focus_get() is not window[K_TABLE].Widget:                        # the list pages itself when it has the focus
                window[K_TABLE].Widget.yview_scroll(-1 if event == K_PGUP else 1, 'pages')
        elif event in (K_HOME, K_END):
            window[K_TABLE].Widget.yview_moveto(0 if event == K_HOME else 1)
        elif event == K_FIND:
            window[K_FILTER].set_focus()
            window[K_FILTER].Widget.select_range(0, 'end')
        elif menu_key == K_REFRESH_NOW:
            request_sample()
        elif isinstance(menu_key, str) and menu_key.startswith(K_REFRESH):
            G.refresh = int(menu_key[len(K_REFRESH):])
            sg.user_settings_set_entry(K_REFRESH, G.refresh)
            start_timer(window)
            show_status(window)
            set_menus(window)
        elif menu_key == K_TOP:
            G.on_top = not G.on_top
            window.keep_on_top_set() if G.on_top else window.keep_on_top_clear()
            sg.user_settings_set_entry(K_TOP, G.on_top)
            set_menus(window)
        elif menu_key == K_CONFIRM:
            G.confirm = not G.confirm
            sg.user_settings_set_entry(K_CONFIRM, G.confirm)
            set_menus(window)
        elif isinstance(menu_key, str) and menu_key.startswith(K_THEME):
            G.theme = menu_key[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            apply_psg_theme()                                                                   # popups follow too
            redraw(window)
            set_menus(window)
        elif menu_key == K_BRIGHT:
            pending = brightness_panel(window, keep_going)
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            apply_psg_theme()
            redraw(window)
            set_menus(window)
        elif menu_key == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME}  v{VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif menu_key == 'Edit Me':
            sg.execute_editor(__file__)
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())
