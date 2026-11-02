"""
psg_local_tray.pyw - system tray switch: which PySimpleGUI do programs on this Python import - LOCAL repo copy or pip-INSTALLED?

Tray icon shows the ACTIVE copy for the Python that runs this program:
    green  L  = LOCAL copy  (D:\\python\\GitHub\\PySimpleGUI)
    blue   P  = PIP-installed copy (site-packages)
    red    ?  = PySimpleGUI import fails on this Python right now
Hover = this program's version, the active copy + its PySimpleGUI.py file.   Click (left or right) = menu.   Double-click = status window.
Log (pythonw has no console): psg_local_tray.log in the PySimpleGUI settings folder on each PC; hard crashes go to psg_local_tray_crash.log.

Needs psg_local.py in the same folder (it does the actual switching: a psg_local.pth file in site-packages).
Run it with the Python whose programs you want switched, e.g. a shortcut:  D:\\python\\Python312\\pythonw.exe psg_local_tray.pyw
A switch applies to programs started AFTER it - running ones (this tray included) keep what they loaded.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.5  FIX: own port 47323 - it shared 47322 with psghotkey, so starting either one told the other to quit (both vanished from the tray)
2026-10-29  v1.4  Single instance: a new launch tells the running copy to exit first (localhost port, same scheme as Download Mover / hotkey)
2026-10-29  v1.3  Version shown in the hover tooltip, the menu and the status window; tooltip kept within Windows' 127-char limit (longer = crash)
2026-10-29  v1.3  Log file + crash log in the PySimpleGUI settings folder (events, errors, thread errors, hard crashes); menu placed by its real size
2026-10-29  v1.2  FIX: clicking off the popup menu exited the program (dismissed menu returned None = sg.WIN_CLOSED); switch errors and crashes now shown, not silent
2026-10-29  v1.1  Left click (and right click) open a BlackGold-themed popup menu; BlackGold theme for the status window too
2026-10-29  v1.0  First version: L / P / ? icon, tooltip with version + file, Use LOCAL / Use INSTALLED, status window, re-checks every 5 s
"""
import base64
import faulthandler
import io
import logging
import logging.handlers
import os
import socket
import sys
import threading
import time
import PySimpleGUI as sg
from psgtray import SystemTray
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psg_local

VERSION = '1.5'
CHECK_SECONDS = 5           # how often the tray re-checks which copy is active (cheap: looks at the switch file first)
FULL_PROBE_SECONDS = 60     # how often it starts a fresh interpreter to re-read version + file
INSTANCE_PORT = 47323       # localhost port used to make sure only one copy runs: a new launch tells the old one to quit (Download Mover 47321, psghotkey 47322)
TOOLTIP_MAX = 127           # Windows tray tooltips hold 127 characters - pystray passes longer text straight through and crashes
LOG_PATH = os.path.join(os.path.dirname(sg.user_settings_filename()), 'psg_local_tray.log')   # local to each PC - 5 PCs never share one log

# ---- Key constants (convention: K_NAME = '-NAME-') ----
K_TRAY = '-TRAY-'
K_STATUS = '-STATUS-'
K_COPY = '-COPY-'
K_CLOSE = '-CLOSE-'
K_QUIT_REQUEST = '-QUIT-REQUEST-'  # another copy of this program was launched and wants us to exit

M_LOCAL = 'Use LOCAL copy'
M_INSTALLED = 'Use INSTALLED copy'
M_STATUS = 'Status...'
M_REFRESH = 'Refresh'
MENU = ['', [M_LOCAL, M_INSTALLED, '---', M_STATUS, M_REFRESH, '---', 'Version', 'Edit Me', 'Exit']]
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


def hook_tray_right_click(tray):
    """Windows draws pystray's right-click menu itself (grey, unthemed). Patch the pystray icon so a right click acts like a left click -> our themed menu."""
    WM_RBUTTONUP = 0x0205
    for _ in range(50):                                  # the icon is created in psgtray's thread - wait for it
        if getattr(tray, 'thread_started', False) and getattr(tray, 'tray_icon', None) is not None:
            break
        time.sleep(0.1)
    icon = getattr(tray, 'tray_icon', None)
    if icon is None or not hasattr(icon, '_on_notify'):  # not the Win32 backend
        return False
    original = icon._on_notify

    def patched(wparam, lparam):
        if lparam == WM_RBUTTONUP:
            icon()                                       # pystray "activate" -> psgtray sends EVENT_SYSTEM_TRAY_ICON_ACTIVATED
        else:
            original(wparam, lparam)
    icon._on_notify = patched
    return True


def tray_popup_menu(main_window, state, version):
    """BlackGold-themed menu opened by a single click on the tray icon. The active copy is marked. Returns the chosen item text, or None."""
    marks = {M_LOCAL: state == 'local', M_INSTALLED: state == 'installed'}
    items = [i for i in MENU[1] if i != '---']
    header = f'PySimpleGUI {version or "?"}  -  {state.upper()}'
    layout = [[sg.Text(header, text_color=C_GOLD, background_color=C_MENU_BG, font=('Segoe UI', 10, 'bold'), size=(28, 1), pad=((14, 0), (6, 4)))]]
    layout += [[sg.Button(('\u25cf  ' if marks.get(i) else '    ') + i, key=i, size=(28, 1), button_color=(C_MENU_TXT, C_MENU_BG), mouseover_colors=('#0a0803', C_GOLD),
                          border_width=0, pad=(0, 0), font=('Segoe UI', 11))] for i in items]
    layout += [[sg.Text(f'psg_local_tray v{VERSION}', text_color='#b39b4f', background_color=C_MENU_BG, font=('Segoe UI', 9), size=(34, 1), pad=((14, 0), (4, 6)))]]
    x, y = main_window.mouse_location()
    menu = sg.Window('', layout, no_titlebar=True, keep_on_top=True, finalize=True, margins=(2, 2), background_color=C_GOLD_DIM, grab_anywhere=True,
                     alpha_channel=0, location=(x, y))
    for i in items:
        menu[i].widget.configure(anchor='w', padx=14)       # left-align like a real menu
    w, h = menu.size
    menu.move(max(0, x - w), max(0, y - h - 4))             # bottom-right corner at the mouse (measured, so DPI/fonts can't throw it off)
    menu.set_alpha(1)
    menu.bind('<Escape>', K_ESCAPE)
    menu.bind('<FocusOut>', K_ESCAPE)
    menu.force_focus()
    while True:
        event, _ = menu.read()
        if event in (sg.WINDOW_CLOSED, K_ESCAPE):
            event = None
        if event is None or event in items:
            break
    menu.close()
    return event


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
    window = sg.Window('psg_local_tray', [[sg.Text('')]], finalize=True, alpha_channel=0, no_titlebar=True, location=(-5000, -5000))   # hidden event hub
    window.hide()
    if instance_sock:
        threading.Thread(target=instance_listener, args=(instance_sock, window, K_QUIT_REQUEST), daemon=True).start()
    state, version, where = current_state()
    tray = SystemTray(MENU, single_click_events=True, window=window, tooltip=tooltip_for(state, version, where), icon=make_icon(state), key=K_TRAY)
    hook_tray_right_click(tray)
    last_key, ticks = switch_state_key(), 0

    def notify(message):
        try:
            tray.show_message('PySimpleGUI switch', message)
        except Exception:
            pass                                        # notification balloons are not supported on every desktop

    def refresh(force=False):
        nonlocal state, version, where, last_key
        key = switch_state_key()
        if not force and key == last_key:
            return
        last_key = key
        new_state, version, where = current_state()
        if new_state != state:
            tray.change_icon(make_icon(new_state))
            logging.info('active copy now %s  %s  %s', new_state, version, where)
        state = new_state
        tray.set_tooltip(tooltip_for(state, version, where))

    while True:
        event, values = window.read(timeout=CHECK_SECONDS * 1000)
        if event == K_TRAY:
            event = values[event]                       # the tray menu item text, or a click/double-click event
            if event == sg.EVENT_SYSTEM_TRAY_ICON_ACTIVATED:      # single click -> themed popup menu
                refresh()
                event = tray_popup_menu(window, state, version)
                logging.info('menu -> %r', event)
                if event is None:                       # menu dismissed (Esc / clicked elsewhere) - None is ALSO sg.WIN_CLOSED, so don't fall through
                    continue
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
        elif event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)

    tray.close()
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
