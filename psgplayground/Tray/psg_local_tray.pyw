"""
psg_local_tray.pyw - system tray switch: which PySimpleGUI do programs on this Python import - LOCAL repo copy or pip-INSTALLED?

Tray icon shows the ACTIVE copy for the Python that runs this program:
    green  L  = LOCAL copy  (D:\\python\\GitHub\\PySimpleGUI)
    blue   P  = PIP-installed copy (site-packages)
    red    ?  = PySimpleGUI import fails on this Python right now
Hover = this program's version, the active copy + its PySimpleGUI.py file.   Click (left or right) = menu, in BlackGold.   Double-click = status window.
Log (pythonw has no console): psg_local_tray.log in the PySimpleGUI settings folder on each PC; hard crashes go to psg_local_tray_crash.log.

Needs psg_local.py in the same folder (it does the actual switching: a psg_local.pth file in site-packages).
Run it with the Python whose programs you want switched, e.g. a shortcut:  D:\\python\\Python312\\pythonw.exe psg_local_tray.pyw
Right-click > Start with Windows: a shortcut in your Startup folder starts it with Windows - with the same Python it runs on now.
A switch applies to programs started AFTER it - running ones (this tray included) keep what they loaded.
New versions: a newer psg_local_tray.pyw saved over this one (Dropbox brings it) takes over by itself - right-click > New versions to choose; Restart
starts a fresh copy.  Each update goes into this PC's card log (the Notifications app), and the menu's first line says UPDATED until you click it (or
What's new...).

CHANGE LOG (newest first, 1 line per change):
2026-11-14  v1.8  New versions + Restart (UPDATE block 3: each update recorded, UPDATED atop the menu until you look, What's new...);  sub-menu arrows (TRAY v2)
2026-11-11  v1.7  Right-click > Start with Windows (a Startup shortcut, same Python);  the menu laid out like every tray app: name + version on top
2026-11-03  v1.6  A real menu (tray_app_recipe.md's TRAY block): right-click is colored too (the old hook never took), active copy checked
2026-11-01  v1.5  FIX: own port 47323 - it shared 47322 with psghotkey, so starting either one told the other to quit (both vanished from the tray)
2026-10-29  v1.4  Single instance: a new launch tells the running copy to exit first (localhost port, same scheme as Download Mover / hotkey)
2026-10-29  v1.3  Version shown in the hover tooltip, the menu and the status window; tooltip kept within Windows' 127-char limit (longer = crash)
2026-10-29  v1.3  Log file + crash log in the PySimpleGUI settings folder (events, errors, thread errors, hard crashes); menu placed by its real size
2026-10-29  v1.2  FIX: clicking off the popup menu exited the program (dismissed menu returned None = sg.WIN_CLOSED); switch errors and crashes now shown, not silent
2026-10-29  v1.1  Left click (and right click) open a BlackGold-themed popup menu; BlackGold theme for the status window too
2026-10-29  v1.0  First version: L / P / ? icon, tooltip with version + file, Use LOCAL / Use INSTALLED, status window, re-checks every 5 s
"""
import base64
import ctypes
import faulthandler
import io
import logging
import logging.handlers
import os
import re
import socket
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psg_local

VERSION = '1.8'
APP_NAME = 'psg_local_tray'    # the Startup shortcut's name
CHECK_SECONDS = 5           # how often the tray re-checks which copy is active (cheap: looks at the switch file first)
FULL_PROBE_SECONDS = 60     # how often it starts a fresh interpreter to re-read version + file
INSTANCE_PORT = 47323       # localhost port used to make sure only one copy runs: a new launch tells the old one to quit (Download Mover 47321, psghotkey 47322)
TOOLTIP_MAX = 127           # Windows tray tooltips hold 127 characters - pystray passes longer text straight through and crashes
LOG_PATH = os.path.join(os.path.dirname(sg.user_settings_filename()), 'psg_local_tray.log')   # local to each PC - 5 PCs never share one log

# ---- Key constants (convention: K_NAME = '-NAME-') ----
K_TRAY = '-TRAY-'                  # the tray icon's events
K_TRAY_MENU = '-TRAY MENU-'        # the tray icon was right-clicked
K_EXIT = 'Exit'
C_MENU_SEL = '#2a62a8'              # menu highlight (white text) - the same blue in every tray app
FONT_MENU = ('Segoe UI', 10)
K_STATUS = '-STATUS-'
K_COPY = '-COPY-'
K_CLOSE = '-CLOSE-'
K_QUIT_REQUEST = '-QUIT-REQUEST-'  # another copy of this program was launched and wants us to exit

M_LOCAL = '-USE LOCAL-'             # menu keys (the menu's items are 'label::key')
M_INSTALLED = '-USE INSTALLED-'
M_STATUS = '-STATUS WINDOW-'
M_REFRESH = '-REFRESH-'
K_ESCAPE = '-ESCAPE-'

black_gold = {"BACKGROUND": "#0a0803", "TEXT": "#e3d7b8", "INPUT": "#171307", "TEXT_INPUT": "#f2ead2", "SCROLL": "#171307", "BUTTON": ("#0a0803", "#c9a227"), "PROGRESS": ("#e6b800", "#171307"), "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0}
sg.theme_add_new('BlackGold', black_gold)
C_MENU_BG, C_MENU_TXT, C_GOLD, C_GOLD_DIM = '#171307', '#e3d7b8', '#c9a227', '#7a6418'      # popup menu: dark rows, gold hover, gold frame

STYLES = {'local': ('#1f8f3a', 'L'), 'installed': ('#2b6fd6', 'P'), 'broken': ('#c0392b', '?')}     # state -> (circle color, letter)


def make_icon(state):
    """64x64 PNG as base64: colored circle + big letter. psgtray takes base64 bytes."""
    color, letter = STYLES[state]
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, 62, 62), fill=color, outline='white', width=3)
    for name in ('arialbd.ttf', 'DejaVuSans-Bold.ttf'):
        try:
            font = ImageFont.truetype(name, 40)
            break
        except OSError:
            font = ImageFont.load_default()
    draw.text((32, 31), letter, fill='white', font=font, anchor='mm')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue())


def current_state():
    """(state, version, file) for the Python running this program - 'local' if the imported file lives under the repo folder."""
    version, where = psg_local.probe()
    if not version:
        return 'broken', None, where
    local = os.path.normcase(os.path.abspath(where)).startswith(os.path.normcase(psg_local.DEFAULT_FOLDER + os.sep))
    return ('local' if local else 'installed'), version, where


def tooltip_for(state, version, where):
    """Hover text: this program's version, the active copy, and its PySimpleGUI.py file (path shortened from the left to fit Windows' limit)."""
    updated = f'  (updated from {update_tag()})' if update_tag() else ''
    head = f'psg_local_tray v{VERSION}{updated}\n' + {'local': f'PySimpleGUI {version} - LOCAL copy', 'installed': f'PySimpleGUI {version} - INSTALLED copy',
                                             'broken': 'PySimpleGUI import FAILS on this Python'}[state] + '\n'
    room = TOOLTIP_MAX - len(head)
    return head + (where if len(where) <= room else '\u2026' + where[-(room - 1):])


# ---- single instance (same reusable pair as download_mover.pyw) ----
def claim_single_instance(port, timeout=5.0):
    """If a previous copy is listening on `port`, tell it to QUIT and wait for it to let go of the port. Returns the listening socket, or None."""
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=1.0) as old:
            old.sendall(b'QUIT')
            old.settimeout(timeout)
            try:
                old.recv(16)                             # the old copy answers OK just before it exits
            except OSError:
                pass
    except OSError:
        pass                                             # nobody listening - we're the only copy
    deadline = time.time() + timeout
    while True:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            srv.bind(('127.0.0.1', port))
            srv.listen(1)
            return srv
        except OSError:
            srv.close()
            if time.time() > deadline:
                return None
            time.sleep(0.2)


def instance_listener(srv, window, key):
    """Thread: when a newer copy connects and says QUIT, send `key` to the window's event loop so it can exit cleanly."""
    while True:
        try:
            conn, _ = srv.accept()
        except OSError:
            return                                       # socket closed - we're exiting
        with conn:
            try:
                if conn.recv(16).startswith(b'QUIT'):
                    conn.sendall(b'OK')
                    window.write_event_value(key, None)
            except OSError:
                pass


def setup_logging():
    """pythonw has no console: events + errors go to LOG_PATH, thread errors too; hard crashes (faulthandler) to a separate _crash.log."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=200_000, backupCount=1, encoding='utf-8')
    logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(asctime)s %(levelname)s %(message)s')
    faulthandler.enable(open(LOG_PATH.replace('.log', '_crash.log'), 'a', encoding='utf-8'))
    threading.excepthook = lambda a: logging.error('thread %s crashed', getattr(a.thread, 'name', '?'), exc_info=(a.exc_type, a.exc_value, a.exc_traceback))
    logging.info('---- start v%s  pid %s  %s', VERSION, os.getpid(), sys.executable)


def switch_state_key():
    """Cheap change detector: the switch file(s) and their mtimes."""
    return tuple((p, os.path.getmtime(p)) for p in psg_local.find_pths())


# --- TRAY: the same block in every tray app (master copy in tray_app_template.pyw / tray_app_recipe.md) - v2, 14-Nov-2026 ---
# v2: a tray click brings a covered window to the front (hides it only when it is in view);  sub-menus get an arrow you can see on a dark menu
try:
    from psgtray import SystemTray
except ImportError:                   # no tray icon - closing the window ends the program
    SystemTray = None


class Tray:
    icon = None                       # the psgtray SystemTray while it is shown
    use = True                        # closing the window minimizes to the tray (setting K_MIN_TO_TRAY, and psgtray is installed)


def tray_start(window, icon, tooltip):
    """ the tray icon, made in a thread (psgtray sleeps ~0.4 s while its own thread starts).  Click: window shown/hidden.  Right-click: our menu """
    def make():
        tray = SystemTray(['', [K_EXIT]], icon=icon, tooltip=tooltip[:127], single_click_events=True, window=window, key=K_TRAY)  # tips over 127 crash
        tray.key = K_TRAY                                                                            # psgtray makes it '-TRAY-1', '-TRAY-2'... for every later icon
        handlers = getattr(tray.tray_icon, '_message_handlers', {})                                  # Windows: pystray's own right-click menu is gray - use ours
        for msg, handler in list(handlers.items()):
            if getattr(handler, '__name__', '') == '_on_notify':                                      # the icon's mouse messages; 0x0205 = WM_RBUTTONUP
                handlers[msg] = lambda wparam, lparam, original=handler: window.write_event_value(K_TRAY_MENU, None) if lparam == 0x0205 else original(wparam, lparam)
        Tray.icon = tray
    if SystemTray and Tray.use and not Tray.icon:
        threading.Thread(target=make, daemon=True).start()


def tray_stop():
    """ call before window.close() - otherwise a dead icon sits in the tray until the mouse passes over it """
    if Tray.icon:
        Tray.icon.close()
        Tray.icon = None


def tray_menu(window):
    """ the window's right-click menu at the mouse.  Windows only closes a tray menu on a click elsewhere if its program is in front """
    x, y = window.TKroot.winfo_pointerxy()
    ctypes.windll.user32.SetForegroundWindow(window.TKroot.winfo_id())
    window.TKRightClickMenu.tk_popup(x, y)


def window_hidden(window):
    return window.TKroot.state() == 'withdrawn'


def window_show(window):
    window.un_hide()
    window.bring_to_front()
    window.force_focus()


def window_in_view(window):
    """ showing and nothing covers it (Windows: the window under 5 of its points is ours).  Elsewhere: showing.  Program standards, 11-Nov: a plain
        show / hide toggle needs two clicks for a window lost behind others - so a tray click brings a covered window to the front """
    if window_hidden(window):
        return False
    if not sg.running_windows():
        return True
    try:
        import ctypes.wintypes
        user32 = ctypes.WinDLL('user32')
        user32.WindowFromPoint.restype = ctypes.c_void_p
        user32.WindowFromPoint.argtypes = [ctypes.wintypes.POINT]
        user32.GetAncestor.restype = ctypes.c_void_p
        user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        root = window.TKroot
        mine = user32.GetAncestor(root.winfo_id(), 2)
        x0, y0, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
        points = [(x0 + w // 2, y0 + h // 2), (x0 + 20, y0 + 20), (x0 + w - 20, y0 + 20), (x0 + 20, y0 + h - 20), (x0 + w - 20, y0 + h - 20)]
        return all(user32.GetAncestor(user32.WindowFromPoint(ctypes.wintypes.POINT(px, py)), 2) == mine for px, py in points)
    except Exception:
        return True


def tray_event(window, event, values):
    """ handles the tray's own events; True when it did.  Click: a hidden or covered window comes to the front, one in view hides.  Right-click: the menu """
    if event == K_TRAY:
        if values[K_TRAY] == sg.EVENT_SYSTEM_TRAY_ICON_ACTIVATED:
            window.hide() if window_in_view(window) else window_show(window)
        elif values[K_TRAY] == K_EXIT:                                                               # pystray's gray menu - only if the right-click hook failed
            window.write_event_value(K_EXIT, None)
        return True
    if event == K_TRAY_MENU:
        tray_menu(window)
        return True
    return False


MENU_ARROWS = {}                      # menu_arrows: (font, labels) -> {index: the label with its arrow} - worked out once


def menu_arrows(menu, dark):
    """ Windows draws a sub-menu's arrow in Windows' own menu-text color (black, white only on the lit row) whatever the menu's colors, so on a dark
        menu it can't be seen (Mike, 10-Nov).  This puts a › in the menu's own text color at the right end of each sub-menu's label instead.  Windows
        and dark menus only - a light menu shows Windows' arrow, and Linux / Mac draw theirs in the menu's colors.  Safe to call again """
    if not (dark and sg.running_windows()) or menu.index('end') is None:
        return
    kinds = ('command', 'cascade', 'checkbutton', 'radiobutton')
    sig = (str(menu.cget('font')), tuple(menu.entrycget(i, 'label') if menu.type(i) in kinds else menu.type(i) for i in range(menu.index('end') + 1)))
    if sig not in MENU_ARROWS:
        import tkinter.font
        f, done = tkinter.font.Font(root=menu, font=menu.cget('font')), {}
        labels = {i: menu.entrycget(i, 'label') for i in range(menu.index('end') + 1) if menu.type(i) in kinds}
        labels = {i: text.rstrip('  ›') if menu.type(i) == 'cascade' and text.endswith('›') else text for i, text in labels.items()}
        cascades = [i for i in labels if menu.type(i) == 'cascade']
        if cascades:
            end = max(f.measure(text) for text in labels.values()) + f.measure('      ›')     # the arrows line up a little past the longest label
            for i in cascades:
                label = labels[i] + '  '
                while f.measure(label + ' ›') <= end:
                    label += ' '
                while f.measure(label + ' ›') <= end:                                     # thin spaces for the last few pixels
                    label += '\u2009'
                done[i] = label + '›'
        MENU_ARROWS[sig] = done
    for i, label in MENU_ARROWS[sig].items():
        menu.entryconfigure(i, label=label)


def style_menus(window):
    """ tk draws menus Windows-gray; recolor every right-click menu (PySimpleGUI makes one per element) and its sub-menus: flat, theme colors, arrows """
    bg = sg.theme_background_color()
    dark = sum(int(bg[i:i + 2], 16) for i in (1, 3, 5)) < 384 if isinstance(bg, str) and len(bg) == 7 else True

    def style(widget):
        for child in widget.winfo_children():
            if isinstance(child, tk.Menu):
                child.configure(bg=bg, fg=sg.theme_text_color(), activebackground=C_MENU_SEL, activeforeground='#ffffff',
                                disabledforeground='#8a93a3', bd=0, activeborderwidth=1, relief='flat', font=FONT_MENU)
                menu_arrows(child, dark)
            style(child)
    style(window.TKroot)
# --- end TRAY ---


# --- UPDATE: Restart, and a newer version of this file (program standards, 11-Nov-2026, block 3 of 14-Nov) - paste unchanged ---
# Right-click > Restart starts a fresh copy of this file (same arguments) and this one ends.  While it runs, the program watches its own file:
# a NEWER VERSION saved over it counts once it has sat UPDATE_SETTLE seconds unchanged and compiles (a half-saved or broken file never counts).
# Then right-click > New versions decides (remembered, -NEW VERSIONS-; the program sets Update.default for its kind):
#   'auto'  By itself - hidden in the tray at once, showing once the mouse has been off the window UPDATE_QUIET seconds and nothing of it is open
#   'ask'   Ask me first - a small pop-up, Restart now / Later (Later by itself after 30 s); hidden in the tray it goes by itself
#   'menu'  Only say so here - never by itself; the menu reads "Restart - x.y.z is ready"
# Not the internet: the file itself, which Dropbox brings to every PC.
# Block 3: at each start the program compares its VERSION with the one that last ran on this PC (-RAN VERSION-).  Newer = it was updated - by
# itself, from the menu or by hand: a line goes into this PC's card log, so the Notifications tray app lists "<program>  Updated to x.y.z" with
# the change-log line, and Update.was holds the old version for the program's own window.  Mike, 14-Nov: "It just seems like sort of a creepy
# thing ... it's upgraded itself.  I mean, it's really cool, but some sort of record of that would be nice."
# And on the program's own window, for people without the Notifications app: update_tag() is the version it was updated from until the user
# has looked (-UPDATED FROM-, kept across restarts) - the program shows an UPDATED tag by its version; clicking it shows update_news(update_tag())
# (the change-log lines since then) and calls update_tag_seen().  Mike: "if someone's away and they come back and it's been updated, looking at
# their window itself is all they would need to do to see that this program's been changed."
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
    was = ''                          # block 3: the version that ran before on this PC, when this start is a newer one ('' = not updated)


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
        update_noted()                                                    # block 3: the first look - an update since the last run?
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


def update_noted():
    """ Block 3, once per start: this VERSION against the one that last ran on this PC (-RAN VERSION-).  Newer: one line in this PC's card log (the
        CARD LOG format, Tools\\card_log.md) - the Notifications tray app lists it - and Update.was = the old version.  Never raises """
    try:
        ran_before = bool(sg.user_settings())                             # a settings file with something in it: it ran here before
        last = str(sg.user_settings_get_entry('-RAN VERSION-', '') or '')
        sg.user_settings_set_entry('-RAN VERSION-', VERSION)
        if not last and not ran_before:                                   # its first run on this PC
            return
        if last and tuple(int(x) for x in last.split('.')) >= tuple(int(x) for x in VERSION.split('.')):
            return
        last = last or 'an earlier version'                               # it ran here before block 3 kept the version
        Update.was = last
        if not sg.user_settings_get_entry('-UPDATED FROM-'):              # not looked at yet since an earlier update: keep the oldest
            sg.user_settings_set_entry('-UPDATED FROM-', last)
        import datetime, json, uuid
        name = globals().get('APP_NAME') or os.path.splitext(os.path.basename(__file__))[0]
        new = next((re.sub(r'^\s*\d{4}-\d\d-\d\d\s+v?' + re.escape(VERSION) + r'\s*(Claude:\s*)?', '', line).strip()
                    for line in (globals().get('__doc__') or '').splitlines() if re.match(r'\s*\d{4}-\d\d-\d\d\s+v?' + re.escape(VERSION) + r'\b', line)), '')
        base = sg.DEFAULT_USER_SETTINGS_WIN_PATH if sys.platform.startswith('win') else sg.DEFAULT_USER_SETTINGS_MAC_PATH if sys.platform == 'darwin' \
            else sg.DEFAULT_USER_SETTINGS_LINUX_PATH
        folder = os.path.join(os.path.expanduser(base), 'Notifications')
        os.makedirs(folder, exist_ok=True)
        now = datetime.datetime.now()
        line = {'v': 1, 'id': uuid.uuid4().hex[:12], 'at': now.strftime('%Y-%m-%d %H:%M:%S'), 'program': str(name)[:60], 'title': f'Updated to {VERSION}',
                'text': (f'Was {last}.  ' + new[:1].upper() + new[1:])[:2000].strip(), 'click': None, 'private': False}
        with open(os.path.join(folder, f'cards_{now:%Y-%m}.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(line, ensure_ascii=False) + '\n')
    except Exception:
        pass


def update_tag():
    """ Block 3: the version this program was updated from, until the user has looked ('' = nothing to show).  The program shows an UPDATED tag """
    return str(sg.user_settings_get_entry('-UPDATED FROM-', '') or '')


def update_tag_seen():
    """ Block 3: the user looked (clicked the tag) - the tag goes away """
    sg.user_settings_set_entry('-UPDATED FROM-', '')


def update_news(since=''):
    """ Block 3: the change-log lines of the versions after since, up to this one, newest first, each 'x.y.z  what changed' (a line that goes on
        is joined on).  since = '' or 'an earlier version': all of them """
    try:
        floor = tuple(int(x) for x in since.split('.'))
    except ValueError:
        floor = ()
    top, out, keep = tuple(int(x) for x in VERSION.split('.')), [], False
    for line in (globals().get('__doc__') or '').splitlines():
        found = re.match(r'\s*\d{4}-\d\d-\d\d\s+v?([0-9]+(?:\.[0-9]+)+)\s+(?:Claude:\s*)?(.*)', line)
        if found:
            ver = tuple(int(x) for x in found.group(1).split('.'))
            keep = floor < ver <= top
            if keep:
                out.append(f'{found.group(1)}  {found.group(2).strip()}')
        elif keep and line.startswith((' ', '\t')) and line.strip():
            out[-1] += ' ' + line.strip()
        else:
            keep = False
    return out


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


# --- NEWS: the UPDATED tag + What's new (UPDATE block 3, Tools\update_block.md) - the same in every tray app ---
TAG_BG, TAG_FG = '#f5c542', '#241a02'                                  # yellow, dark text - the word carries the meaning, not the color
K_NEWS = "-WHAT'S NEW-"                                                # right-click > What's new..., and a click on the UPDATED tag


def news_hint():
    return f'Updated from {update_tag()} - click UPDATED to see what changed'


def show_whats_new(colors=('#1e2430', '#e6eaf2', '#2a62a8'), font=('Segoe UI', 11), lines=None):
    """ Right-click > What's new... or a click on the UPDATED tag: the change-log lines since the version it was updated from (the whole log when
        there is no tag), newest first, in the program's own colors.  Esc / Enter / OK closes it - and the tag goes.  lines: a program whose change
        log isn't in the block's format gives its own """
    since, (bg, fg, button) = update_tag(), colors
    lines = update_news(since) if lines is None else lines
    head = f'Updated from {since} to {VERSION}' if since else f'{APP_NAME} {VERSION}  -  what changed'
    rows = min(18, max(5, sum(1 + len(line) // 96 for line in lines)))
    layout = [[sg.Text(head, font=(font[0], font[1] + 1, 'bold'), background_color=bg, text_color=fg, pad=(10, (10, 6)))],
              [sg.Multiline('\n'.join(lines) or '(no change-log lines found)', size=(96, rows), font=font, disabled=True, background_color=bg, text_color=fg,
                            border_width=0, no_scrollbar=rows < 18, pad=(10, 0), key='-NEWS TEXT-')],
              [sg.Push(background_color=bg), sg.Button('OK', button_color=('#ffffff', button), font=font, size=(8, 1), pad=(10, 10))]]
    win = sg.Window(f"{APP_NAME} - what's new", layout, background_color=bg, keep_on_top=True, modal=True, icon=globals().get('ICON'), finalize=True,
                    return_keyboard_events=False)
    win.bind('<Escape>', 'OK')
    win.bind('<Return>', 'OK')
    win.read(close=True)
    update_tag_seen()
# --- end NEWS ---


def news_colors():
    """ the New versions pop-up and What's new in BlackGold: (background, text, button) """
    return sg.theme_background_color(), sg.theme_text_color(), C_MENU_SEL


# --- STARTUP: start with Windows, hidden in the tray - the same block in every tray app (master copy in tray_app_template.pyw / tray_app_recipe.md) ---
# The program supplies APP_NAME (the shortcut's name) and its icon (PNG base64) to set_startup().  Off to start: the user ticks it once per PC.
START_IN_TRAY = '--tray' in sys.argv[1:]                          # started by the Startup shortcut: stay hidden in the tray
K_STARTUP = '-START WITH WINDOWS-'                                # right-click toggle: the shortcut in this user's Startup folder


def startup_link():
    """ the shortcut in this user's Startup folder that starts the program with Windows, hidden in the tray """
    return os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', f'{APP_NAME}.lnk')


def startup_on():
    return sg.running_windows() and os.path.exists(startup_link())


def set_startup(on, icon=None):
    """ right-click > Start with Windows, in the tray: make the shortcut (pythonw "<this file>" --tray) or remove it.  icon = the program's PNG
        (base64): it goes beside the program's settings as <APP_NAME>.ico, because a shortcut takes its icon from a file.  Returns '' or why it failed """
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
        ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(path)}');$s.TargetPath='{q(exe)}';$s.Arguments='\"{q(script)}\" --tray';"
              f"$s.WorkingDirectory='{q(os.path.dirname(script))}';" + (f"$s.IconLocation='{q(ico)}';" if ico else '') + '$s.Save()')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], creationflags=0x08000000, timeout=30, check=True, capture_output=True)   # no window
        return '' if os.path.exists(path) else 'Windows did not make the shortcut'
    except Exception as e:
        return str(e) or type(e).__name__
# --- end STARTUP ---


def make_menu(state, version):
    """ the menu for the tray icon (click or right-click): the active copy at the top, a check mark on it """
    tick = lambda on: '✓ ' if on else '    '
    head = {'local': 'LOCAL', 'installed': 'INSTALLED', 'broken': 'import FAILS'}[state]
    tray = [f'{tick(startup_on())}Start with Windows, in the tray::{K_STARTUP}'] if sg.running_windows() else []     # no window: no Minimize to tray
    top = f"    {APP_NAME} {VERSION}   -   UPDATED: see what's new::{K_NEWS}" if update_tag() else f'    {APP_NAME} {VERSION}::Version'   # UPDATE block 3's tag
    return ['', [top, '---',                                                                         # the same layout in every tray app (tray_app_recipe.md)
                 f'!    PySimpleGUI {version or "?"}  -  {head}', f'{tick(state == "local")}Use LOCAL copy::{M_LOCAL}',
                 f'{tick(state == "installed")}Use INSTALLED copy::{M_INSTALLED}', '---', f'    Status...::{M_STATUS}', f'    Refresh::{M_REFRESH}', '---', *tray, '---',
                 '    Edit Me::Edit Me', f'    Version {VERSION}::Version', f"    What's new...::{K_NEWS}", *update_menu(tick), f'    Exit::{K_EXIT}']]


def apply_menu(window, state, version):
    menu = make_menu(state, version)
    for element in window.element_list():
        element.set_right_click_menu(menu, propogate_to_window=True)
    style_menus(window)


def show_status(state, version, where):
    pths = psg_local.find_pths()
    color = STYLES[state][0]
    text = (f'Python      : {sys.executable}\n'
            f'Active copy : {state.upper()}\n'
            f'Version     : {version or "-"}\n'
            f'File        : {where}\n'
            f'Switch file : {pths[0] if pths else "(none - pip-installed copy)"}')
    layout = [[sg.Text(f'PySimpleGUI {version or "?"}  -  {state.upper()}', font=('Helvetica', 14, 'bold'), text_color=color), sg.Push(),
               sg.Text(f'psg_local_tray v{VERSION}', font=('Helvetica', 10, 'bold'), text_color=C_GOLD)],
              [sg.Multiline(text, size=(110, 6), font=('Courier', 9), disabled=True, no_scrollbar=True)],
              [sg.Text('A switch applies to programs started after it. Programs already running keep the copy they loaded.', font=('Helvetica', 9))],
              [sg.Button('Copy', key=K_COPY, tooltip='Copy the text above to the clipboard'), sg.Button('Close', key=K_CLOSE)]]
    win = sg.Window(f'psg_local_tray v{VERSION} - status', layout, finalize=True, keep_on_top=True, modal=True)
    win.bind('<Escape>', K_CLOSE)
    while True:
        event, _ = win.read()
        if event in (sg.WIN_CLOSED, K_CLOSE):
            break
        if event == K_COPY:
            sg.clipboard_set(text)
    win.close()


def main():
    Update.default = 'auto'                                    # a tray app: new versions by itself
    sg.theme('BlackGold')
    instance_sock = claim_single_instance(INSTANCE_PORT)       # a previous copy, if any, is told to exit first
    update_check()                                             # UPDATE block 3's first look now: UPDATED atop the first menu
    if instance_sock is None:
        logging.warning('could not claim the single-instance port - a previous copy may still be running')
    state, version, where = current_state()
    window = sg.Window('psg_local_tray', [[sg.Text('')]], finalize=True, alpha_channel=0, no_titlebar=True, location=(-5000, -5000),   # hidden event hub
                       right_click_menu=make_menu(state, version), right_click_menu_background_color=sg.theme_background_color(),
                       right_click_menu_text_color=sg.theme_text_color(), right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU)
    window.hide()
    style_menus(window)
    if instance_sock:
        threading.Thread(target=instance_listener, args=(instance_sock, window, K_QUIT_REQUEST), daemon=True).start()
    tray_start(window, make_icon(state), tooltip_for(state, version, where))
    last_key, ticks = switch_state_key(), 0

    def notify(message):
        try:
            Tray.icon.show_message('PySimpleGUI switch', message)
        except Exception:
            pass                                        # notification balloons are not supported on every desktop

    def refresh(force=False):
        nonlocal state, version, where, last_key
        key = switch_state_key()
        if not force and key == last_key:
            return
        last_key = key
        new_state, version, where = current_state()
        if new_state != state and Tray.icon:
            Tray.icon.change_icon(make_icon(new_state))
            logging.info('active copy now %s  %s  %s', new_state, version, where)
        if new_state != state:
            apply_menu(window, new_state, version)
        state = new_state
        if Tray.icon:
            Tray.icon.set_tooltip(tooltip_for(state, version, where)[:TOOLTIP_MAX])

    while True:
        event, values = window.read(timeout=CHECK_SECONDS * 1000)
        if event == K_TRAY:
            event = values[event]                       # a click/double-click, or Exit from pystray's gray menu (only if the right-click hook failed)
        if event in (sg.EVENT_SYSTEM_TRAY_ICON_ACTIVATED, K_TRAY_MENU):  # click or right-click -> the menu (no window to show - this app is all menu)
            refresh()
            tray_menu(window)
            continue
        if isinstance(event, str) and '::' in event:    # menu items come back as 'label::key'
            event = event.split('::')[-1]
            logging.info('menu -> %r', event)
        if update_event(event):                         # right-click > Restart, or a New versions choice
            if Update.restart:
                break
            apply_menu(window, state, version)
            continue
        if event == sg.TIMEOUT_EVENT:
            ticks += 1
            refresh(force=ticks % max(1, FULL_PROBE_SECONDS // CHECK_SECONDS) == 0)
            if update_tick(window, True, False, news_colors()):         # all menu, no window: a newer version takes over at once (By itself)
                apply_menu(window, state, version)
            if Update.restart:
                logging.info('a newer version (%s) is here - restarting', Update.ready)
                break
        elif event in (sg.WIN_CLOSED, 'Exit', K_QUIT_REQUEST):
            logging.info('exit (%r)%s', event, ' - a new copy was launched and is taking over' if event == K_QUIT_REQUEST else '')
            break
        elif event == M_LOCAL:
            try:
                psg_local.switch_on(psg_local.DEFAULT_FOLDER)
            except (SystemExit, Exception) as e:                    # psg_local reports problems with sys.exit(); file errors raise OSError
                sg.popup_error(f'Could not switch:\n{e}', keep_on_top=True)
            refresh(force=True)
            notify(f'LOCAL copy is now active: {version}' if state == 'local' else 'Switch failed - see Status')
        elif event == M_INSTALLED:
            try:
                psg_local.switch_off()
            except Exception as e:
                sg.popup_error(f'Could not switch:\n{e}', keep_on_top=True)
            refresh(force=True)
            notify(f'INSTALLED copy is now active: {version}' if state == 'installed' else 'Switch failed - see Status')
        elif event in (M_STATUS, sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED):
            refresh(force=True)
            show_status(state, version, where)
        elif event == M_REFRESH:
            refresh(force=True)
        elif event == K_STARTUP:
            error = set_startup(not startup_on(), make_icon(state))
            logging.info('start with Windows: %s %s', 'on' if startup_on() else 'off', error)
            if error:
                sg.popup_error(f'Start with Windows:\n{error}', keep_on_top=True)
            else:
                notify(f'psg_local_tray {"starts" if startup_on() else "no longer starts"} with Windows')
            apply_menu(window, state, version)
        elif event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == K_NEWS:
            show_whats_new(news_colors())
            apply_menu(window, state, version)
            if Tray.icon:
                Tray.icon.set_tooltip(tooltip_for(state, version, where)[:TOOLTIP_MAX])
        elif event == 'Edit Me':
            sg.execute_editor(__file__)

    tray_stop()
    window.close()
    if instance_sock:
        instance_sock.close()                            # lets the new copy bind the port right away
    if Update.restart:                                   # UPDATE block: a fresh copy (--tray: no balloon)
        restart_self(['--tray'])


if __name__ == '__main__':
    try:
        setup_logging()
        main()
    except Exception as e:                              # pythonw has no console - show the traceback instead of silently vanishing
        logging.exception('main crashed')
        sg.popup_error_with_traceback(f'psg_local_tray v{VERSION} crashed - please send this traceback (also in {LOG_PATH})', e)
