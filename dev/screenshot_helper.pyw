"""
screenshot_helper.pyw - take a screenshot of every Playground program, one after another, for the Toybox and the README.

    The list is the catalog.  Green = has a screenshot (psgplayground/screenshots/<program file name>.png), grey = still to do.
    The loop:   Next             closes the program from last time and starts the next one still to do (in demo mode when it has one)
                                 - set it up however you like: open a menu, pick options, play a few notes ...
                Capture window   grabs that program's biggest window and saves it.  Nothing is taken until you press it.
    Capture in 3 s   for any other window (a tray program's window, a second window, a program that isn't in this repo):
                     press it, click the window you want, and keep your hands off for 3 seconds.
    Snip             like the Windows Snipping Tool: the screen freezes (menus and tooltips stay open in the picture) and the window
                     under the mouse lights up - click it to take exactly that window, or drag a rectangle around anything
                     (several windows at once).  It is saved when you let go.  Esc or right-click cancels.
    Snip in 5 s      for what vanishes when you press a key - a tray icon's right-click menu, a tooltip, an open drop-down: press it,
                     open the menu and wait.  The screen freezes with the menu still showing, then click or drag as in Snip.
    Launch / Close app   start or stop the selected program yourself.   Open folder shows the screenshots.
    Delete shot      deletes the selected program's screenshot (it asks first) - for a capture taken on the wrong row.
    A capture replaces the old picture, so take it again until you like it.  The helper hides itself while it captures.
    Keys:  F5 = Launch   F6 = Snip in 5 s   F7 = Snip   F8 = Capture window   F9 = Capture in 3 s   F10 = Next   Del = Delete shot   Up/Down PgUp/PgDn Home/End move in the list   Esc = close
    Windows only (it finds the windows with the Win32 API).  Needs Pillow.

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v1.5  Delete shot (Del): deletes the selected program's screenshot after asking - a capture taken on the wrong row had no way out
2026-11-01  v1.4  Snip in 5 s (F6) - time to open a tray icon's menu (psg_local_tray) or a tooltip, then the screen freezes with it showing.
                  A program's process tree skips older processes whose parent ID Windows reused - Capture/Close could hit another program
2026-11-01  v1.3  Capture window finds the program however it was started (your own copy, the Dock, its working folder) - any Python
                  process running its file (needs psutil); before, only a copy started from here counted (Download Mover 'wasn't running')
2026-11-01  v1.2  Snip (F7) - hover lights up the window under the mouse, click takes exactly that window, drag still takes a rectangle
2026-11-01  v1.1  Drag rectangle (F7): freeze the screen and drag around what to capture - several windows at once, or a program that
                  restarted itself as admin (CPU Cores Widget), which Capture window can't find
2026-11-01  v1.0  First version
"""
import ctypes
import io
import json
import os
import subprocess
import sys
import time
import tkinter as tk
import traceback

import PySimpleGUI as sg

try:
    from PIL import Image, ImageGrab
except ImportError:
    Image = ImageGrab = None

VERSION = '1.5'
APP_NAME = 'Playground Screenshots'
ICON = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAMAAACdt4HsAAABgFBMVEUbITDn7PQWGCUAAAAdmfsepP/z+P0cXJUdlv8cTnwglv/9xjw7QE4gpf4Cqf8Af/+Bh5KboKuzucIoLTrZ3ucdmv8dnP4bOFcemv0dmfsmymvFy9Mda60uMTtTWWWVmqXb4+kdm/9DSVb/0j7/9tEAAP8bLUQdg9Udmv4A//8bFx80OUhLRDJxd4Ots7z9yEwdjOJN0YdmVzS9ljmkqbOv4szUqDo/v/9dY2+WezeI3LGlhTjtuDwJDh0cYJodc7wdd8MqlP8hof9DPjNMUl97ZTVjaXW7wMnN0tr+3Yb/4ZT/67IcUH4AVf8cjf8foP8eoP8fymYiov9dUDN8go5s153BmjrI6N//2HYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB2GdGRAAAAgHRSTlP///8A9/7//hD+J////gQC//////8sjv+w0////f////9v////Af/8SgH////////+////////BP/////////9/Q4m/////////////gMSrMf/Fv///////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABw6esIAAAM9SURBVHjapZdnf9owEMblsyxIjG32KMshbAhQRnaa2czu/f0/SU82BkxwkdznDfwk7s/pLEv3ENWTdWSqgrKOrMV34o3x6E5UROY1/73lB2B4Zi9foEIq5LMZJ2QJMNVMlhqGJijDoJ8zc4IDsNQ2NTTaKkWEVGpRzaB7LoE48XsYXsoREFWuhIisarkAU20blO4AEGEhYqQZTg5EtTpRqtGcRLiDICONZhodBJhq3sD/J5KCHDUKuAhiqRmqlaTjCem+wxRUk0SxgtILcFJoUl5H8hFX0CJhBFdaQW1gDQqhVoCAiEajWER8BpFwgA8a3Q0ErOyaQMBOMABIOeWpTEAaALGinfZkP96BNKDIFOZJYekUyAGgbCs+xaQBaRYW4NY9tQbo+d7lfwAAKokkl38FykNyqem9h3gNADL1CucX8yk5r+kGQHVz5PpgMgAAMbYe/piIx6vFBWJ2eno6w/EKbAYc+AHsoeIUldQG7sTsDZetsGoAIO4DsPiy8C569pUDfissIQJgPy4I9E8mv076QC7u+ZT9FvVTEcuADYDAiY7a18/W6iuWAW6es319OOSIiX9viQAwARjv60/1+h9OeA+rKQgBDgAm+rBer7/wZRwSOJYEVCB1rusv9fozB+hlqClhAMPnp6EDuIWYJOAYyKG+0HkKapJLiDsPwdMEVrepEKAIUF5m0AcYyAH4GmDsxeNTrMluJH6SQv+Qb8TD7+Acs5I7kSX5q3g7Hvf559Q3lRB7G4s172XsJf0zYgCFKYlKmZDUXVVZmxAE8CPJLhbTr880YYB7KL4elABsVOCBUhEFHEDAxVIUIniX7YZ7oaaw7Qg2P9U3Xm29qb0t3h7UIPhyxTcotkW9xe3qAT75rvftjbbves8g4Ij+R5t3zVtdbDTDAS61AjbbUTUbvtXNY6vrNtvdEM12RNPa2Gy77b58CjyBAno3bjgwhRGRNhwtJwHX8qBlGuW6Mpan22xx02R6piuLputdU9hzQTOCpiuvmo257cMcuO27iuwIKXKJ4Rqajcaq8cxTYd/JneeXthu/Yn13s4LOF71vtr1mfbEOHY652RXQzbf5X/oAOGKpwrLMhvf1L8nNXEG4NEelAAAAAElFTkSuQmCC'      # 64 px PNG, base64 - a camera on the Toybox's blue-edged tile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, 'psgplayground')
CATALOG = os.path.join(PKG, 'catalog.json')
SHOTS = os.path.join(PKG, 'screenshots')
WINDOWS = sys.platform == 'win32'
COUNTDOWN = 3                                   # seconds to click the window for "Capture in 3 s"
SNIP_DELAY = 5                                  # seconds to open a menu before "Snip in 5 s" freezes the screen
PREVIEW = (440, 280)
NUM_ROWS = 18
ONE_COPY_ONLY = ('download_mover', 'psg_local_tray')     # starting these tells your already-running copy to quit
FONT, FONT_SMALL = ('Segoe UI', 11), ('Segoe UI', 9)
C_DONE, C_TODO, C_RUN, C_BAD, C_DIM = '#2ecc71', '#9aa5b1', '#49b4ff', '#ff6b6b', '#8a93a3'
sg.theme('DarkGrey13')

K_TABLE = '-TABLE-'
K_LAUNCH = '-LAUNCH-'
K_CAPTURE = '-CAPTURE-'
K_DELAY = '-DELAY-'
K_AREA = '-AREA-'
K_AREA_DELAY = '-AREA DELAY-'
K_CLOSE_APP = '-CLOSE APP-'
K_NEXT = '-NEXT-'
K_FOLDER = '-FOLDER-'
K_DELETE = '-DELETE-'
K_PREVIEW = '-PREVIEW-'
K_PREVIEW_TEXT = '-PREVIEW TEXT-'
K_STATUS = '-STATUS-'
K_COUNT = '-COUNT-'
K_ESCAPE = '-ESCAPE-'
K_PGUP, K_PGDN, K_HOME, K_END = '+PGUP', '+PGDN', '+HOME', '+END'


# ---------------------------------------------------------------- the list ----------------------------------------------------------------
def load_apps():
    """ the catalog's programs in catalog order: name, section, file stem (= screenshot name), full path ('' when not in this repo), demo args """
    with open(CATALOG, encoding='utf-8') as f:
        catalog = json.load(f)
    folders = {s['name']: s['folder'] for s in catalog['sections']}
    apps = []
    for a in catalog['apps']:
        if a.get('file'):
            parts = [PKG, folders[a['section']]] + ([a['folder']] if a.get('folder') else []) + [a['file']]
            stem, path = os.path.splitext(a['file'])[0], os.path.join(*parts)
        else:
            stem, path = a['name'].lower().replace(' ', '_'), ''
        apps.append({'name': a['name'], 'section': a['section'], 'stem': stem, 'path': path, 'args': a.get('args_demo', '')})
    return apps


def shot_path(app):
    return os.path.join(SHOTS, app['stem'] + '.png')


def table_rows(apps, running):
    rows, colors = [], []
    for i, app in enumerate(apps):
        done = os.path.isfile(shot_path(app))
        rows.append(['✓' if done else '', app['section'], app['name'] + ('   (running)' if app is running else ''), app['stem'] + '.png'])
        colors.append((i, C_RUN if app is running else C_DONE if done else C_TODO, sg.theme_input_background_color()))
    return rows, colors


# --------------------------------------------------------------- Win32 bits ---------------------------------------------------------------
if WINDOWS:
    from ctypes import wintypes
    user32, kernel32, dwmapi = ctypes.WinDLL('user32'), ctypes.WinDLL('kernel32'), ctypes.WinDLL('dwmapi')     # own copies: setting argtypes can't affect PySimpleGUI's calls
    ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    HWND, LPRECT = wintypes.HWND, ctypes.POINTER(wintypes.RECT)
    for name, args, res in (('EnumWindows', [ENUM_PROC, wintypes.LPARAM], wintypes.BOOL), ('GetWindowThreadProcessId', [HWND, ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD),
                            ('IsWindowVisible', [HWND], wintypes.BOOL), ('IsIconic', [HWND], wintypes.BOOL), ('ShowWindow', [HWND, ctypes.c_int], wintypes.BOOL),
                            ('SetForegroundWindow', [HWND], wintypes.BOOL), ('GetWindowRect', [HWND, LPRECT], wintypes.BOOL), ('GetForegroundWindow', [], HWND),
                            ('PostMessageW', [HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM], wintypes.BOOL),
                            ('GetWindowLongW', [HWND, ctypes.c_int], ctypes.c_long), ('GetWindowTextLengthW', [HWND], ctypes.c_int),
                            ('GetWindowTextW', [HWND, wintypes.LPWSTR, ctypes.c_int], ctypes.c_int), ('GetSystemMetrics', [ctypes.c_int], ctypes.c_int),
                            ('GetLayeredWindowAttributes', [HWND, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(wintypes.DWORD)],
                             wintypes.BOOL)):
        getattr(user32, name).argtypes, getattr(user32, name).restype = args, res
    dwmapi.DwmGetWindowAttribute.argtypes = [HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.argtypes, kernel32.CreateToolhelp32Snapshot.restype = [wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.OpenProcess.argtypes, kernel32.OpenProcess.restype = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE
    kernel32.GetProcessTimes.argtypes, kernel32.GetProcessTimes.restype = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4, wintypes.BOOL

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD), ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD), ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', ctypes.c_long), ('dwFlags', wintypes.DWORD), ('szExeFile', ctypes.c_char * 260)]


def process_tree(pid):
    """ pid and every process it started (a venv's pythonw starts the real one as a child; launchers start programs) """
    parents = {}
    snap = kernel32.CreateToolhelp32Snapshot(0x2, 0)                                           # TH32CS_SNAPPROCESS
    if not snap or snap == wintypes.HANDLE(-1).value:
        return {pid}
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(entry)
    ok = kernel32.Process32First(snap, ctypes.byref(entry))
    while ok:
        parents[entry.th32ProcessID] = entry.th32ParentProcessID
        ok = kernel32.Process32Next(snap, ctypes.byref(entry))
    kernel32.CloseHandle(snap)
    tree, grew = {pid}, True
    while grew:
        grew = False
        for child, parent in parents.items():
            if parent in tree and child not in tree and not started_before(child, parent):
                tree.add(child)
                grew = True
    return tree


def started(pid):
    """ when the process started (100 ns ticks), None when Windows won't say """
    handle = kernel32.OpenProcess(0x1000, False, pid)                                              # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        times = [wintypes.FILETIME() for _ in range(4)]                                            # created, exited, kernel, user
        if not kernel32.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
            return None
        return times[0].dwHighDateTime << 32 | times[0].dwLowDateTime
    finally:
        kernel32.CloseHandle(handle)


def started_before(child, parent):
    """ True when 'child' is older than 'parent': its real parent has exited and Windows gave that process ID to a newer process """
    child_time, parent_time = started(child), started(parent)
    return child_time is not None and parent_time is not None and child_time < parent_time


def window_rect(hwnd):
    """ the window as you see it: DWM's frame bounds (no invisible resize border or shadow), else GetWindowRect """
    rect = wintypes.RECT()
    try:
        if dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)) == 0:                     # DWMWA_EXTENDED_FRAME_BOUNDS
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def windows_of(pids):
    """ visible top-level windows of these processes, biggest first: [(hwnd, rect)] """
    found = []

    def callback(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value in pids and user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            r = window_rect(hwnd)
            if r[2] - r[0] > 60 and r[3] - r[1] > 40:                                          # not tooltips or 1-pixel helpers
                found.append((hwnd, r))
        return True
    user32.EnumWindows(ENUM_PROC(callback), 0)
    return sorted(found, key=lambda w: (w[1][2] - w[1][0]) * (w[1][3] - w[1][1]), reverse=True)


def window_pid(hwnd):
    owner = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
    return owner.value


def grab(window, hwnd):
    """ that window's pixels as a PIL image - the helper hides meanwhile, the window comes to the front """
    window.hide()
    window.refresh()
    try:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)                                                              # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)                                                                             # let it repaint and the helper vanish
        return ImageGrab.grab(bbox=window_rect(hwnd), all_screens=True)
    finally:
        window.un_hide()


def visible_windows():
    """ every window you could click on right now, top of the pile first: [((left, top, right, bottom), title)].  Leaves out hidden and
        minimized windows, cloaked ones (other virtual desktops, suspended Store apps), click-through and fully transparent ones (overlays such
        as the RAM / CPU tagger draws) and this program's own """
    if not WINDOWS:
        return []
    found = []

    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd) or window_pid(hwnd) == os.getpid():
            return True
        ex_style = user32.GetWindowLongW(hwnd, -20)                                            # GWL_EXSTYLE
        if ex_style & 0x20:                                                                    # WS_EX_TRANSPARENT - clicks go through it
            return True
        if ex_style & 0x80000:                                                                 # WS_EX_LAYERED - skip it when it is invisible (alpha 0)
            key, alpha, flags = wintypes.DWORD(), ctypes.c_ubyte(), wintypes.DWORD()
            if user32.GetLayeredWindowAttributes(hwnd, ctypes.byref(key), ctypes.byref(alpha), ctypes.byref(flags)) and flags.value & 2 and alpha.value == 0:
                return True
        cloaked = wintypes.DWORD()
        if dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0 and cloaked.value:     # DWMWA_CLOAKED
            return True
        rect = window_rect(hwnd)
        if rect[2] - rect[0] < 20 or rect[3] - rect[1] < 20:
            return True
        title = ctypes.create_unicode_buffer(user32.GetWindowTextLengthW(hwnd) + 1)
        user32.GetWindowTextW(hwnd, title, len(title))
        found.append((rect, title.value))
        return True
    user32.EnumWindows(ENUM_PROC(callback), 0)                                                 # EnumWindows goes from the top of the pile down
    return found


def snip(window):
    """ Freeze the whole screen (every monitor) and show it dimmed.  The window under the mouse is shown bright with a gold edge - a click takes
        exactly that window; a drag takes the rectangle.  Returns that part of the frozen screen (PIL image), or None when cancelled """
    from PIL import ImageEnhance, ImageTk
    window.hide()
    window.refresh()
    time.sleep(0.4)                                                                             # let the helper vanish from the screen first
    full = ImageGrab.grab(all_screens=True) if WINDOWS else ImageGrab.grab()
    left, top_y = (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)) if WINDOWS else (0, 0)    # SM_XVIRTUALSCREEN / SM_YVIRTUALSCREEN
    wins = [((r[0] - left, r[1] - top_y, r[2] - left, r[3] - top_y), t) for r, t in visible_windows()]  # in canvas coordinates
    top = tk.Toplevel(window.TKroot)
    top.overrideredirect(True)
    top.geometry(f'{full.width}x{full.height}+{left}+{top_y}')
    top.attributes('-topmost', True)
    canvas = tk.Canvas(top, width=full.width, height=full.height, highlightthickness=0, cursor='crosshair', bg='black')
    canvas.pack()
    dimmed = ImageTk.PhotoImage(ImageEnhance.Brightness(full).enhance(0.55), master=top)
    canvas.create_image(0, 0, image=dimmed, anchor='nw')
    mx, my = top.winfo_pointerx() - left, top.winfo_pointery() - top_y                          # the hint goes where you are looking
    hint = 'Click a window to take it, or drag a rectangle  -  Esc or right-click cancels'
    hint_id = canvas.create_text(mx, max(24, my - 60), text=hint, fill='#ffc53d', font=('Segoe UI', 14, 'bold'), tags='hint')
    x0, y0, x1, y1 = canvas.bbox(hint_id)
    canvas.tag_lower(canvas.create_rectangle(x0 - 10, y0 - 4, x1 + 10, y1 + 4, fill='#1b2130', outline='#ffc53d', tags='hint'), hint_id)      # readable over anything
    sel = {'start': None, 'dragging': False, 'box': None, 'hover': None, 'photo': None}

    def label(x, y, text, tag):
        """ gold text on a dark tab, above (x, y) when there is room, else below it """
        t = canvas.create_text(x + 6, y - 4 if y > 26 else y + 4, text=text, anchor='sw' if y > 26 else 'nw', fill='#ffc53d', font=('Segoe UI', 11, 'bold'), tags=tag)
        x0, y0, x1, y1 = canvas.bbox(t)
        canvas.tag_lower(canvas.create_rectangle(x0 - 6, y0 - 2, x1 + 6, y1 + 2, fill='#1b2130', outline='', tags=tag), t)

    def hover(e):
        if sel['start'] is not None:
            return
        hit = next((w for w in wins if w[0][0] <= e.x < w[0][2] and w[0][1] <= e.y < w[0][3]), None)
        if hit is sel['hover']:
            return
        sel['hover'] = hit
        canvas.delete('hover')
        if hit:
            (x0, y0, x1, y1), title = hit
            box = (max(0, x0), max(0, y0), min(full.width, x1), min(full.height, y1))           # the part that is on screen
            sel['photo'] = ImageTk.PhotoImage(full.crop(box), master=top)
            canvas.create_image(box[0], box[1], image=sel['photo'], anchor='nw', tags='hover')
            canvas.create_rectangle(*box, outline='#ffc53d', width=3, tags='hover')
            label(box[0], box[1], f'{title or "(window without a title)"}    {box[2] - box[0]} x {box[3] - box[1]}', 'hover')
        canvas.tag_raise('hint')

    def press(e):
        sel['start'], sel['dragging'], sel['box'] = (e.x, e.y), False, None

    def drag(e):
        if sel['start'] is None:
            return
        (x0, y0), (x1, y1) = sel['start'], (e.x, e.y)
        if not sel['dragging'] and abs(x1 - x0) < 6 and abs(y1 - y0) < 6:                     # still a click - a hand is never perfectly still
            return
        if not sel['dragging']:
            sel['dragging'] = True
            canvas.delete('hover')
        sel['box'] = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        canvas.delete('sel')
        canvas.create_rectangle(*sel['box'], outline='#ffc53d', width=2, tags='sel')
        label(sel['box'][0], sel['box'][1], f'{sel["box"][2] - sel["box"][0]} x {sel["box"][3] - sel["box"][1]}', 'sel')

    def release(e):
        if sel['dragging']:
            box = sel['box']
            if box and box[2] - box[0] >= 20 and box[3] - box[1] >= 20:
                top.destroy()
                return
        elif sel['hover']:                                                                     # a click: the window under the mouse
            x0, y0, x1, y1 = sel['hover'][0]
            sel['box'] = (max(0, x0), max(0, y0), min(full.width, x1), min(full.height, y1))
            top.destroy()
            return
        sel['start'], sel['dragging'], sel['box'], sel['hover'] = None, False, None, None      # a tiny drag, or a click on nothing - try again
        canvas.delete('sel')
        hover(e)

    def cancel(e=None):
        sel['box'] = None
        top.destroy()
    canvas.bind('<Motion>', hover)
    canvas.bind('<ButtonPress-1>', press)
    canvas.bind('<B1-Motion>', drag)
    canvas.bind('<ButtonRelease-1>', release)
    canvas.bind('<ButtonPress-3>', cancel)
    top.bind('<Escape>', cancel)
    top.focus_force()
    try:
        window.TKroot.wait_window(top)
    finally:
        window.un_hide()
    return full.crop(sel['box']) if sel['box'] else None


def pids_running(app):
    """ processes running this program however they were started (from here, the Dock, its working folder): Python processes whose command
        line names its file.  Needs psutil (set() without it).  An admin process won't show its command line, so it is never found here """
    if not app['path']:
        return set()
    try:
        import psutil
    except ImportError:
        return set()
    name, found = os.path.basename(app['path']).lower(), set()
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if (proc.info['name'] or '').lower().startswith('python') and any(os.path.basename(arg).lower() == name for arg in proc.info['cmdline'] or []):
                found.add(proc.pid)
        except (psutil.Error, OSError):
            pass
    return found


# ------------------------------------------------------------ running programs ------------------------------------------------------------
def launch(app):
    exe = sys.executable
    if WINDOWS and os.path.basename(exe).lower() == 'python.exe':
        exe = os.path.join(os.path.dirname(exe), 'pythonw.exe')                                  # no console window behind the program
    return subprocess.Popen([exe, app['path']] + app['args'].split(), cwd=os.path.dirname(app['path']))


def close_app(proc):
    """ ask its windows to close (programs save their settings), then make sure the whole process tree is gone """
    if proc is None or proc.poll() is not None:
        return
    if WINDOWS:
        pids = process_tree(proc.pid)
        for hwnd, _ in windows_of(pids):
            user32.PostMessageW(hwnd, 0x0010, 0, 0)                                                 # WM_CLOSE
        for _ in range(20):
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        if proc.poll() is None:
            subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], capture_output=True, creationflags=0x08000000)    # CREATE_NO_WINDOW
    else:
        proc.terminate()


# ------------------------------------------------------------------ window -----------------------------------------------------------------
def preview_data(img):
    im = img.copy()
    im.thumbnail(PREVIEW)
    bio = io.BytesIO()
    im.save(bio, format='PNG')
    return bio.getvalue()


def blank_preview():
    """ an empty picture the size of the preview, so the window keeps its shape before there is a screenshot to show """
    bio = io.BytesIO()
    Image.new('RGB', PREVIEW, '#14171c').save(bio, format='PNG')
    return bio.getvalue()


def make_window(apps):
    rows, colors = table_rows(apps, None)
    table = sg.Table(rows, headings=['', 'Section', 'Program', 'Screenshot file'], key=K_TABLE, col_widths=[2, 11, 30, 30], auto_size_columns=False,
                     justification='left', num_rows=NUM_ROWS, font=FONT, row_colors=colors, enable_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                     expand_x=True, expand_y=True)
    preview = [[sg.Image(data=blank_preview(), key=K_PREVIEW, background_color='#14171c')],
               [sg.Text('', key=K_PREVIEW_TEXT, font=FONT_SMALL, text_color=C_DIM, size=(56, 2))]]
    buttons = [sg.Button('Next  F10', key=K_NEXT, button_color=('white', '#2a62a8')), sg.Button('Capture window  F8', key=K_CAPTURE, button_color=('white', '#1f7a4a')),
               sg.Button('Capture in 3 s  F9', key=K_DELAY), sg.Button('Snip  F7', key=K_AREA, tooltip=' Click a window, or drag a rectangle '),
               sg.Button(f'Snip in {SNIP_DELAY} s  F6', key=K_AREA_DELAY, tooltip=' Open a menu meanwhile (right-click a tray icon) - the screen freezes with it showing '),
               sg.Button('Launch  F5', key=K_LAUNCH), sg.Button('Close app', key=K_CLOSE_APP),
               sg.Button('Open folder', key=K_FOLDER), sg.Button('Delete shot  Del', key=K_DELETE, tooltip=' Delete the selected program\'s screenshot - it asks first ')]
    layout = [[sg.Text('Playground Screenshots', font=('Segoe UI', 14, 'bold'), text_color='#1e9bff'), sg.Text(f'v{VERSION}', text_color=C_DIM), sg.Push(),
               sg.Text('', key=K_COUNT, font=('Segoe UI', 11, 'bold'))],
              buttons,
              [sg.Column([[table]], expand_x=True, expand_y=True, pad=0), sg.Column(preview, vertical_alignment='top', pad=((8, 0), 0))],
              [sg.Text('', key=K_STATUS, expand_x=True), sg.Sizegrip()]]
    window = sg.Window(APP_NAME, layout, font=FONT, finalize=True, resizable=True, keep_on_top=True, auto_save_location=True, icon=ICON,
                       right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, enable_close_attempted_event=True)
    for key, ev in (('<F5>', K_LAUNCH), ('<F6>', K_AREA_DELAY), ('<F7>', K_AREA), ('<F8>', K_CAPTURE), ('<F9>', K_DELAY), ('<F10>', K_NEXT), ('<Delete>', K_DELETE), ('<Escape>', K_ESCAPE)):
        window.bind(key, ev)
    for key, ev in (('<Prior>', K_PGUP), ('<Next>', K_PGDN), ('<Home>', K_HOME), ('<End>', K_END)):
        window[K_TABLE].bind(key, ev, propagate=False)
    return window


class State:
    def __init__(self, apps):
        self.apps = apps
        self.sel = 0
        self.proc = None                # the program this helper started
        self.running = None             # ... and which app it is
        self.countdown = 0              # seconds left of "Capture in 3 s"
        self.countdown_snip = False     # ... ending in a Snip ("Snip in 5 s") instead of taking the window in front


def refresh(window, state, status=None, color=None):
    """ redraw the list (✓ marks, running) keeping the selection, the count, and the preview of the selected program """
    if state.proc is not None and state.proc.poll() is not None:
        state.proc, state.running = None, None
    rows, colors = table_rows(state.apps, state.running)
    window[K_TABLE].update(values=rows, row_colors=colors, select_rows=[state.sel])
    window[K_TABLE].Widget.see(str(state.sel + 1))
    done = sum(os.path.isfile(shot_path(a)) for a in state.apps)
    window[K_COUNT].update(f'{done} of {len(state.apps)} done', text_color=C_DONE if done == len(state.apps) else C_TODO)
    app = state.apps[state.sel]
    if os.path.isfile(shot_path(app)):
        try:
            with Image.open(shot_path(app)) as im:
                im.load()
                window[K_PREVIEW].update(data=preview_data(im))
                window[K_PREVIEW_TEXT].update(f'{app["stem"]}.png   {im.width} x {im.height}')
        except Exception as e:
            window[K_PREVIEW].update(data=blank_preview())
            window[K_PREVIEW_TEXT].update(f'Could not read {app["stem"]}.png: {e}')
    else:
        window[K_PREVIEW].update(data=blank_preview())
        window[K_PREVIEW_TEXT].update(f'No screenshot yet for {app["name"]}')
    if status is not None:
        window[K_STATUS].update(status, text_color=color)


def countdown_text(state):
    """ the status line while counting down """
    if state.countdown_snip:
        return f'Open what you want in the picture (right-click the tray icon for its menu) ...  the screen freezes in {state.countdown}'
    return f'Click the window to capture ...  {state.countdown}'


def start(window, state, app):
    if not app['path']:
        refresh(window, state, f'{app["name"]} isn\'t in this repo - start it yourself, then Capture in 3 s', C_TODO)
        return
    close_app(state.proc)
    state.proc, state.running = launch(app), app
    hint = f' (demo: {app["args"]})' if app['args'] else ''
    if app['stem'] in ONE_COPY_ONLY:
        hint += ' - it closes your own running copy: start that again afterwards'
    refresh(window, state, f'Started {app["name"]}{hint} - set it up, then Capture window', C_RUN)


def capture(window, state, hwnd=None):
    """ grab hwnd (or, with no hwnd, a rectangle dragged on the frozen screen), save it as the selected program's screenshot, show it """
    app = state.apps[state.sel]
    try:
        img = grab(window, hwnd) if hwnd else snip(window)
        if img is None:
            refresh(window, state, 'Snip cancelled', C_TODO)
            return
        os.makedirs(SHOTS, exist_ok=True)
        img.save(shot_path(app), optimize=True)
    except Exception as e:
        refresh(window, state, f'Capture failed: {e}', C_BAD)
        return
    refresh(window, state, f'Saved {app["stem"]}.png  ({img.width} x {img.height}) - Next when you\'re happy, or capture again', C_DONE)


def main():
    if Image is None:
        sg.popup_error('Pillow is needed:   python -m pip install pillow', title=APP_NAME, keep_on_top=True)
        return
    sg.set_options(dpi_awareness=True)                           # window sizes and screen pixels in the same (physical) units
    sg.user_settings_filename(filename='playground_screenshots.json')
    apps = load_apps()
    window = make_window(apps)
    state = State(apps)
    state.sel = next((i for i, a in enumerate(apps) if not os.path.isfile(shot_path(a))), 0)
    first = 'Next starts the first program still to do' if WINDOWS else 'Windows only - the list is shown but nothing can be captured here'
    refresh(window, state, first, None if WINDOWS else C_BAD)
    while True:
        event, values = window.read(timeout=1000 if state.countdown else 2000)
        if event in ('Exit', K_ESCAPE, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, sg.WINDOW_CLOSED):
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME}  version {VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == K_TABLE and values[K_TABLE] and values[K_TABLE][0] != state.sel:         # refresh() re-selects the row, which fires this again
            state.sel = values[K_TABLE][0]
            refresh(window, state)
        elif event in (K_TABLE + K_PGUP, K_TABLE + K_PGDN, K_TABLE + K_HOME, K_TABLE + K_END):
            step = {K_TABLE + K_PGUP: -NUM_ROWS, K_TABLE + K_PGDN: NUM_ROWS, K_TABLE + K_HOME: -len(apps), K_TABLE + K_END: len(apps)}[event]
            state.sel = max(0, min(len(apps) - 1, state.sel + step))
            refresh(window, state)
        elif event == K_FOLDER:
            os.makedirs(SHOTS, exist_ok=True)
            os.startfile(SHOTS) if WINDOWS else subprocess.Popen(['xdg-open', SHOTS])
        elif event == K_DELETE:
            app = apps[state.sel]
            if not os.path.isfile(shot_path(app)):
                refresh(window, state, f'{app["name"]} has no screenshot to delete', C_TODO)
            elif sg.popup_yes_no(f'Delete {app["stem"]}.png?', f'The screenshot of {app["name"]} - you can take it again any time.', title=APP_NAME, keep_on_top=True, font=FONT) == 'Yes':
                try:
                    os.remove(shot_path(app))
                    refresh(window, state, f'Deleted {app["stem"]}.png', C_TODO)
                except OSError as e:
                    refresh(window, state, f'Could not delete {app["stem"]}.png: {e}', C_BAD)
        elif not WINDOWS and event in (K_LAUNCH, K_NEXT, K_CAPTURE, K_DELAY, K_CLOSE_APP):
            refresh(window, state, 'Windows only', C_BAD)
        elif event == K_LAUNCH:
            start(window, state, apps[state.sel])
        elif event == K_CLOSE_APP:
            close_app(state.proc)
            state.proc, state.running = None, None
            refresh(window, state, 'Closed', C_TODO)
        elif event == K_NEXT:
            close_app(state.proc)
            state.proc, state.running = None, None
            todo = [i for i in list(range(state.sel + 1, len(apps))) + list(range(0, state.sel + 1)) if not os.path.isfile(shot_path(apps[i]))]
            if not todo:
                refresh(window, state, 'Every program has a screenshot.  Run Sync, then commit.', C_DONE)
                continue
            state.sel = todo[0]
            start(window, state, apps[state.sel])
        elif event == K_CAPTURE:
            app = apps[state.sel]
            pids = process_tree(state.proc.pid) if state.running is app and state.proc and state.proc.poll() is None else set()
            for pid in pids_running(app):                                                        # started some other way: your own copy, the Dock ...
                pids |= process_tree(pid)
            wins = windows_of(pids) if pids else []
            if wins:
                capture(window, state, wins[0][0])
            elif pids:
                refresh(window, state, f'{app["name"]} is running but shows no window - open it (a tray program: click its icon), or Snip (F7)', C_BAD)
            else:
                refresh(window, state, f'Can\'t find {app["name"]} running - Launch it (F5); if it restarted itself as admin, Snip (F7) it', C_BAD)
        elif event == K_AREA:
            capture(window, state)
        elif event in (K_DELAY, K_AREA_DELAY):
            state.countdown, state.countdown_snip = (SNIP_DELAY, True) if event == K_AREA_DELAY else (COUNTDOWN, False)
            refresh(window, state, countdown_text(state), C_RUN)
        elif event == sg.TIMEOUT_EVENT:
            if state.countdown:
                state.countdown -= 1
                if state.countdown:
                    window[K_STATUS].update(countdown_text(state), text_color=C_RUN)
                    continue
                if state.countdown_snip:
                    capture(window, state)                                                              # frozen with the menu still showing
                    continue
                hwnd = user32.GetForegroundWindow()
                if not hwnd or window_pid(hwnd) == os.getpid():
                    refresh(window, state, 'The helper itself was in front - click the window you want during the countdown', C_BAD)
                else:
                    capture(window, state, hwnd)
            elif state.running is not None and state.proc.poll() is not None:
                refresh(window, state, f'{state.running["name"]} has closed', C_TODO)
    close_app(state.proc)
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())
