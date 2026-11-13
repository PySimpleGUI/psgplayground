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

CHANGE LOG (newest first, 1 line per change):
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

VERSION = '1.7'
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
    head = f'psg_local_tray v{VERSION}\n' + {'local': f'PySimpleGUI {version} - LOCAL copy', 'installed': f'PySimpleGUI {version} - INSTALLED copy',
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


# --- TRAY: the same block in every tray app (master copy in tray_app_template.pyw / tray_app_recipe.md) ---
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


def tray_event(window, event, values):
    """ handles the tray's own events; True when it did.  Click toggles the window, right-click opens the menu """
    if event == K_TRAY:
        if values[K_TRAY] == sg.EVENT_SYSTEM_TRAY_ICON_ACTIVATED:
            window_show(window) if window_hidden(window) else window.hide()
        elif values[K_TRAY] == K_EXIT:                                                               # pystray's gray menu - only if the right-click hook failed
            window.write_event_value(K_EXIT, None)
        return True
    if event == K_TRAY_MENU:
        tray_menu(window)
        return True
    return False


def style_menus(window):
    """ tk draws menus Windows-gray; recolor every right-click menu (PySimpleGUI makes one per element) and its sub-menus: flat, theme colors """
    def style(widget):
        for child in widget.winfo_children():
            if isinstance(child, tk.Menu):
                child.configure(bg=sg.theme_background_color(), fg=sg.theme_text_color(), activebackground=C_MENU_SEL, activeforeground='#ffffff',
                                disabledforeground='#8a93a3', bd=0, activeborderwidth=1, relief='flat', font=FONT_MENU)
            style(child)
    style(window.TKroot)
# --- end TRAY ---


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
    return ['', [f'    {APP_NAME} {VERSION}::Version', '---',                                     # the same layout in every tray app (tray_app_recipe.md)
                 f'!    PySimpleGUI {version or "?"}  -  {head}', f'{tick(state == "local")}Use LOCAL copy::{M_LOCAL}',
                 f'{tick(state == "installed")}Use INSTALLED copy::{M_INSTALLED}', '---', f'    Status...::{M_STATUS}', f'    Refresh::{M_REFRESH}', '---', *tray, '---',
                 '    Edit Me::Edit Me', f'    Version {VERSION}::Version', f'    Exit::{K_EXIT}']]


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
    sg.theme('BlackGold')
    instance_sock = claim_single_instance(INSTANCE_PORT)       # a previous copy, if any, is told to exit first
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
        if event == sg.TIMEOUT_EVENT:
            ticks += 1
            refresh(force=ticks % max(1, FULL_PROBE_SECONDS // CHECK_SECONDS) == 0)
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
        elif event == 'Edit Me':
            sg.execute_editor(__file__)

    tray_stop()
    window.close()
    if instance_sock:
        instance_sock.close()                            # lets the new copy bind the port right away


if __name__ == '__main__':
    try:
        setup_logging()
        main()
    except Exception as e:                              # pythonw has no console - show the traceback instead of silently vanishing
        logging.exception('main crashed')
        sg.popup_error_with_traceback(f'psg_local_tray v{VERSION} crashed - please send this traceback (also in {LOG_PATH})', e)
