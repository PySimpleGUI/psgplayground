"""
download_mover.pyw - System-tray watcher for your Downloads folder.

When a new file lands in the watched folder, an "Inbox" window pops up listing the new file(s).
Pick a destination from your remembered list (or browse for a new one) and Move or Copy.
Multiple files can be selected and moved/copied in one go.  Destinations can be removed from the list.
Files can also be dragged out of the list into Explorer or another program.
Files can be put on the clipboard (CLIPBOARD button, Ctrl+C, Ctrl+X) and pasted into Explorer or another program - new downloads can go there automatically.
Right-click > Start with Windows, in the tray: it starts with Windows, quietly in the tray (a shortcut in your Startup folder, run with --tray).
New versions: a newer download_mover.pyw saved over this one (Dropbox brings it) takes over by itself - right-click > New versions to choose (by itself /
ask me first / only say so); Restart starts a fresh copy.  Each update goes into this PC's card log (the Notifications app), and the title says UPDATED
until you look: right-click > What's new..., or click the status line.  A tray click brings a covered Inbox to the front (in view: it hides).
The Inbox keeps its place across updates; a place off every screen (a screen unplugged, or saved while minimized) is dropped and it opens in the middle.

Requirements:  pip install psgtray pystray pillow watchdog tkinterdnd2
    psgtray/pystray - real Windows system tray icon (if missing, the program still runs with the Inbox window visible)
    watchdog        - event-driven folder monitoring (if missing, falls back to a 3-second timer scan)
    tkinterdnd2     - dragging files out of the Inbox (psgdnd uses it too; if missing, no dragging)

CHANGE LOG (newest first, 1 line per change):
2026-11-15  v1.12  FIX: the Inbox could open off every screen, so it never showed (its place was saved while it was minimized) - a place off every
                   screen is dropped and a lost Inbox comes back to the middle;  the Inbox's place now survives updates and the UPDATED tag
2026-11-14  v1.11  New versions + Restart (UPDATE block 3: each update recorded, UPDATED in the title until you look, What's new...);  a tray click brings
                   a covered Inbox to the front;  sub-menu arrows you can see (TRAY block v2)
2026-11-11  v1.10  Right-click > Start with Windows, in the tray (a Startup shortcut, --tray: no balloon at sign-in); menu laid out like every tray app
2026-11-10  v1.9  The right-click / tray menu starts with "Download Mover 1.9" (click it: the Version window); its Version item reads "Version 1.9"
2026-11-10  v1.8  Double-click a file in NEW FILES to open it
2026-11-10  v1.7  CLIPBOARD button / Ctrl+C put the selected files on the clipboard (paste in Explorer copies them, in a chat or e-mail attaches them); Ctrl+X: paste moves them
2026-11-10  v1.7  Right-click toggle "New downloads go on the clipboard": each finished download is put there (several finishing within 5 s go together)
2026-11-10  v1.7  A file deleted, renamed or moved out of the watched folder (e.g. pasted after Ctrl+X) leaves the Inbox too
2026-11-10  v1.6  Folders open in PySimpleGUI's Explorer Program setting when it is set (the standard for every program), else the Files app, else Explorer
2026-11-10  v1.5  Drag files out of NEW FILES into Explorer or another program (tkinterdnd2); the ones that leave the folder leave the Inbox too
2026-11-10  v1.5  Open Folder button under NEW FILES opens the watched folder, like Open Folder under DESTINATIONS
2026-11-10  v1.5  FIX: Open Watched Folder / Open Folder did nothing when the Files app's alias is files-stable - now files or files-stable, else Explorer
2026-11-03  v1.4  Tray like psgsnip (tray_app_recipe.md): click shows/hides the Inbox, right-click = the colored menu, Minimize to tray toggle
2026-10-31  v1.3  Log kept in the PySimpleGUI settings folder (one per PC, outside Dropbox - no sync conflicts); a crash shows a popup instead of vanishing
2026-10-31  v1.2  Inbox window remembers its position (auto_save_location); this change log added
2026-10-29  v1.1  Single instance (localhost port 47321), Delete to the backup folder, Undo, Scan Now, auto-hide toggle, themed tray menu
2026-10-25  v1.0  First version
"""
import os, re, sys, time, shutil, threading, datetime, subprocess, logging, socket, ctypes, struct, base64
import tkinter as tk
import PySimpleGUI as sg

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES                # dragging files out of the Inbox - the package psgdnd uses
except ImportError:
    TkinterDnD = None

VERSION = '1.12'
__version__ = VERSION
APP_NAME = 'Download Mover'                # the Startup shortcut's name
SETTINGS_FILE = 'download_mover.json'
DEFAULT_WATCH = os.path.join(os.path.expanduser('~'), 'Downloads')
PARTIAL_EXTS = ('.crdownload', '.part', '.partial', '.tmp', '.download', '.!ut', '.opdownload')   # browser in-progress downloads
BACKUP_SUBDIR = '_download_mover_backup'   # an overwritten file is moved here (inside the destination folder) with a timestamp before being replaced
UNDO_DEPTH = 20                # how many Move/Copy operations can be undone
STABLE_SECONDS = 1.5           # file size must be unchanged this long before we treat it as "finished"
POLL_MS = 3000                 # fallback scan interval when watchdog is not installed
INSTANCE_PORT = 47321          # localhost port used to make sure only one copy runs: a new launch tells the old one to quit
FILE_MANAGER = ('files', 'files-stable')     # the "Files" app (files.community) opens folders - its alias is either name; () = always Explorer
AUTO_CLIP_SECONDS = 5          # downloads finishing within this many seconds of each other go on the clipboard together
CF_HDROP = 15                  # the Windows clipboard format for a list of files (what Explorer's Ctrl+C puts there)
DROPEFFECT_COPY, DROPEFFECT_MOVE = 1, 2    # its 'Preferred DropEffect': paste copies the files (Ctrl+C) or moves them (Ctrl+X)

# ---------------------------------------------------------------- keys
K_FILES = '-FILES-'
K_DESTS = '-DESTS-'
K_MOVE = '-MOVE-'
K_COPY = '-COPY-'
K_BROWSE = '-BROWSE-'
K_REMOVE_DEST = '-REMOVE-DEST-'
K_OPEN_FILE = '-OPEN-FILE-'
K_OPEN_DEST = '-OPEN-DEST-'
K_OPEN_WATCH = '-OPEN-WATCH-'
K_FILES_HEAD = '-FILES-HEAD-'
K_DRAGGED = '-DRAGGED-'          # files were dragged out of the list (the drop's action), or 'recheck' 2 s later
K_CLIPBOARD = '-CLIPBOARD-'      # CLIPBOARD button / Ctrl+C: the selected files go on the clipboard (paste copies them)
K_CUT = '-CUT-'                  # Ctrl+X: the same, but paste in Explorer moves them
K_FILE_GONE = '-FILE-GONE-'      # from watcher thread: a file was deleted, renamed or moved out of the watched folder
K_DOUBLE = '-DOUBLE-CLICK-'      # a file in NEW FILES was double-clicked (value = its path): open it
K_SKIP = '-SKIP-'
K_SCAN = '-SCAN-'
K_DELETE = '-DELETE-'
K_UNDO = '-UNDO-'
K_AUTOHIDE = '-AUTOHIDE-'
K_INFO = '-INFO-'
K_STATUS = '-STATUS-'
K_WATCH = '-WATCH-'
K_ESCAPE = '-ESCAPE-'
K_HOME = '-HOME-'
K_END = '-END-'
K_NEW_FILE = '-NEW-FILE-'        # from watcher thread: a file appeared (may still be downloading)
K_FILE_READY = '-FILE-READY-'    # from stability thread: file finished writing
K_QUIT_REQUEST = '-QUIT-REQUEST-'  # another copy of this program was launched and wants us to exit
K_TRAY = '-TRAY-'                # the tray icon's events
K_TRAY_MENU = '-TRAY MENU-'      # the tray icon was right-clicked
K_MIN_TO_TRAY = '-minimize-to-tray-'   # settings entry and right-click toggle: closing the Inbox minimizes to the tray
K_AUTO_CLIP = '-auto-clipboard-'       # settings entry and right-click toggle: each new download goes on the clipboard
K_PLACE = '-INBOX PLACE-'              # settings entry: the Inbox's last place on a screen (PySimpleGUI's own entry is per title - lost at every update)
K_EXIT = 'Exit'

# ---------------------------------------------------------------- theme (Mike's custom dark theme) + colours
# consistent meaning: blue=files, teal/green=destinations & move, orange=copy, red=remove, grey=skip
CADET_HOUR = {'BACKGROUND': '#101a1c', 'TEXT': '#c4d6d8', 'INPUT': '#1b2a2d', 'TEXT_INPUT': '#dbe9ea', 'SCROLL': '#1b2a2d', 'BUTTON': ('#ffffff', '#38666b'),
              'PROGRESS': ('#549298', '#1b2a2d'), 'BORDER': 1, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0}
sg.theme_add_new('CadetHour', CADET_HOUR)
sg.theme('CadetHour')
C_BG = CADET_HOUR['BACKGROUND']
C_FILES = '#2F7FD6'            # button / header backgrounds (white text)
C_DESTS = '#38666b'
C_COPY = '#B5702A'
C_REMOVE = '#A83A3A'
C_SKIP = '#4F5D60'
C_UNDO = '#5F5AA6'            # purple = undo
C_CLIP = '#3A8A5C'            # green = clipboard
C_FILES_TXT = '#7FBCFF'        # lighter variants for text on the dark background
C_DESTS_TXT = '#7CC9CF'
C_COPY_TXT = '#F2A95C'
C_REMOVE_TXT = '#FF8585'
C_SKIP_TXT = '#8A9A9D'
C_UNDO_TXT = '#B3AEFF'
C_CLIP_TXT = '#7FD6A0'
C_TOGGLE_ON = ('#101a1c', '#7CC9CF')   # lit toggle: dark text on bright teal
C_TOGGLE_OFF = ('#8A9A9D', '#1b2a2d')  # unlit toggle: grey text on input-colour
C_INFO_BG = CADET_HOUR['INPUT']
C_INFO_TXT = CADET_HOUR['TEXT_INPUT']
C_MENU_SEL = '#2a62a8'         # menu highlight (white text) - the same blue in every tray app
FONT_MENU = ('Segoe UI', 10)

TRAY_ICON = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABTklEQVR4nO2aTRKCMAyFg+M5cKGHxBPoIXGhF8FVGeRHwCZ5TvO+lc4w9uVroEUQIYQQQkhUqvShbtrOe/DX/VKtH2XLAR0ADQWgA6ChAHQANNBVwItvq02IDqibtlua4BACEnMSQgkQmUoIJ0DkU0Iv4B+2pQh6ASWvAnOkekOeAkPgAp63M3R8qIBUPFICTMC4aJQEiIClYhESjp6DbSkwHXO6PqzjiIhjB+ydXa9ucBHwazEeEswF5BZhLcFUgFZ4SwlmArRDW0kwEWAV1uJ3VZdBj4uW9jKp1gHemxit8VQEoLaxGuNmC0DfzeWOn30N2Hou/hLUYzsM/z8ADQWgA6ChAHQANBSADoCGAtAB0FAAOgAaCkAHQOP2YMTrQcdewndA2DdEUr3sgOGXKF0wrHPSAaVLGNc3ewqUKmGurtVCS3h7rNQJJYSQbN6nzmEdTxhkOQAAAABJRU5ErkJggg=='

LOG_FILE = os.path.join(os.path.dirname(sg.user_settings_filename()), 'download_mover.log')     # per PC, outside Dropbox: copies on several PCs never share one log
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(threadName)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)
logging.getLogger('PIL').setLevel(logging.WARNING)       # PIL is very chatty at DEBUG level


# ================================================================ helpers
class FileItem:
    """ Wraps a full path so the Listbox displays just the filename (Listbox returns the original objects, so the path is preserved) """
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return os.path.basename(self.path)

    def __eq__(self, other):
        return self.path == getattr(other, 'path', other)

    def __hash__(self):
        return hash(self.path)


def human_size(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024 or unit == 'TB':
            return f'{n:,.0f} {unit}' if unit == 'B' else f'{n:,.1f} {unit}'
        n /= 1024


def is_partial(path):
    return path.lower().endswith(PARTIAL_EXTS) or os.path.basename(path).startswith(('~$', '.'))


def backup_existing(target):
    """ If `target` exists, move it into the destination's backup folder with a timestamp. Returns the backup path, or None if there was nothing to back up """
    if not os.path.exists(target):
        return None
    backup_dir = os.path.join(os.path.dirname(target), BACKUP_SUBDIR)
    os.makedirs(backup_dir, exist_ok=True)
    stem, ext = os.path.splitext(os.path.basename(target))
    backup = os.path.join(backup_dir, f'{stem}.{datetime.datetime.now():%Y%m%d_%H%M%S}{ext}')
    shutil.move(target, backup)
    return backup


def open_folder(path):
    """ Open a folder in PySimpleGUI's global Explorer Program when that is set (the standard for every program, 10-Nov), else in the Files app
        (FILE_MANAGER - shutil.which finds its alias), else in Explorer.  PySimpleGUI 6.4 opens nothing when that setting is empty, and passes the folder unquoted """
    sg.pysimplegui_user_settings.load()                                                              # another program may have just changed it
    if str(sg.pysimplegui_user_settings.get('-explorer program-', '') or '').strip():
        sg.execute_file_explorer(f'"{path}"' if ' ' in path else path)
        return
    app = next((shutil.which(name) for name in FILE_MANAGER if shutil.which(name)), None)
    if app:
        try:
            subprocess.Popen([app, path])
            return
        except OSError as e:
            log.info(f'{app} did not start ({e}) - using Explorer')
    open_file(path)


def open_file(path):
    try:
        os.startfile(path)
    except Exception as e:
        sg.popup_error(f'Could not open:\n{path}\n\n{e}', keep_on_top=True)


def load_dests():
    """ Destinations are stored as a dict {path: {'count': n, 'last': timestamp}} and shown most-recently-used first """
    return sg.user_settings_get_entry('-destinations-', {})


def save_dests(dests):
    sg.user_settings_set_entry('-destinations-', dests)


def sorted_dests(dests):
    return sorted(dests, key=lambda p: dests[p].get('last', 0), reverse=True)


def touch_dest(dests, path):
    entry = dests.setdefault(path, {'count': 0, 'last': 0})
    entry['count'] += 1
    entry['last'] = time.time()
    save_dests(dests)


# ================================================================ single instance (reusable: copy claim_single_instance + instance_listener into any app)
def claim_single_instance(port, timeout=5.0):
    """ If a previous copy of this program is listening on `port`, tell it to QUIT and wait for it to let go of the port.
        Returns the listening socket this copy now owns (pass it to instance_listener), or None if the port couldn't be claimed. """
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
    """ Thread: when a newer copy of the program connects and says QUIT, send `key` to the window's event loop so it can exit cleanly """
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


# ================================================================ folder watching
class _WatchHandler(FileSystemEventHandler if Observer else object):
    def __init__(self, window):
        self.window = window

    def on_created(self, event):
        log.debug(f'watchdog created: {event.src_path}')
        if not event.is_directory:
            self.window.write_event_value(K_NEW_FILE, event.src_path)

    def on_moved(self, event):                       # browsers rename x.crdownload -> x.pdf when done
        log.debug(f'watchdog moved: {event.src_path} -> {event.dest_path}')
        if not event.is_directory:
            self.window.write_event_value(K_FILE_GONE, event.src_path)
            self.window.write_event_value(K_NEW_FILE, event.dest_path)

    def on_deleted(self, event):                     # deleted, or moved out of the folder (Explorer pasting after Ctrl+X, a drag out)
        if not event.is_directory:
            self.window.write_event_value(K_FILE_GONE, event.src_path)

    def on_modified(self, event):                    # an existing file overwritten (Save As over the old name)
        if not event.is_directory:
            self.window.write_event_value(K_NEW_FILE, event.src_path)


def start_watcher(window, folder):
    """ Returns a watchdog Observer, or None if watchdog isn't installed (then a timer scan is used) """
    if Observer is None:
        log.info('watchdog not installed - using timer scan')
        return None
    log.info(f'watchdog observer starting on {folder}')
    observer = Observer()
    observer.schedule(_WatchHandler(window), folder, recursive=False)
    observer.daemon = True
    observer.start()
    return observer


def wait_until_stable(window, path):
    """ Thread: wait for the file to stop growing (download finished) and then tell the GUI it is ready """
    last = -1
    log.debug(f'waiting for stable size: {path}')
    while True:
        try:
            size = os.path.getsize(path)
        except OSError as e:
            log.debug(f'vanished while waiting ({e}): {path}')
            return                                   # vanished (renamed from .crdownload etc.) - the rename produces its own event
        if size == last:
            break
        last = size
        time.sleep(STABLE_SECONDS)
    log.debug(f'stable at {last} bytes, partial={is_partial(path)}, isfile={os.path.isfile(path)}: {path}')
    if not is_partial(path) and os.path.isfile(path):
        window.write_event_value(K_FILE_READY, path)


# ================================================================ GUI
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
    window.TKroot.after(200, lambda: into_view(window))


def on_screen(spot):
    """ True when spot = (x, y), a window's top-left corner, has its title bar on one of this PC's screens.  Windows parks a minimized window at
        -32000, -32000 - PySimpleGUI's auto_save_location saved that place once (15-Nov) and the Inbox opened off every screen from then on """
    try:
        x, y = int(spot[0]), int(spot[1])
    except (TypeError, ValueError, IndexError):
        return False
    if sys.platform.startswith('win'):
        try:
            import ctypes.wintypes
            user32 = ctypes.WinDLL('user32')
            user32.MonitorFromPoint.restype = ctypes.c_void_p
            user32.MonitorFromPoint.argtypes = [ctypes.wintypes.POINT, ctypes.c_uint]
            return bool(user32.MonitorFromPoint(ctypes.wintypes.POINT(x + 60, y + 12), 0))      # 0 = MONITOR_DEFAULTTONULL: None when no screen is there
        except Exception:
            pass
    w, h = sg.Window.get_screen_size()
    return -40 <= x < w - 60 and 0 <= y + 12 < h


def place_inbox(title):
    """ Before the Inbox is made: give PySimpleGUI's auto_save_location (it reads '-LAST WINDOW LOCATION-' + title) the Inbox's last place that is
        on a screen - K_PLACE, else that title's own entry.  A place off every screen is forgotten (the Inbox opens in the middle), and so are the
        entries of older titles (one per version and per UPDATED tag) """
    key = '-LAST WINDOW LOCATION-' + title
    spot = next((list(s) for s in (sg.user_settings_get_entry(K_PLACE), sg.user_settings_get_entry(key)) if on_screen(s)), None)
    for old in [k for k in sg.user_settings() if k.startswith('-LAST WINDOW LOCATION-Download Mover') and k != key]:
        sg.user_settings_delete_entry(old)
    if spot:
        sg.user_settings_set_entry(K_PLACE, spot)
        sg.user_settings_set_entry(key, spot)
    elif sg.user_settings_get_entry(key) is not None:
        log.info(f'the Inbox\'s saved place {sg.user_settings_get_entry(key)} is off every screen - it opens in the middle')
        sg.user_settings_delete_entry(key)


def keep_place(window):
    """ On the 3 s tick and before the Inbox closes: where it is -> K_PLACE, when it is showing (not minimized, maximized or hidden) and on a screen """
    try:
        if window.TKroot.state() != 'normal':
            return
        spot = list(window.current_frame_location())
    except Exception:
        return
    if on_screen(spot) and spot != sg.user_settings_get_entry(K_PLACE):
        sg.user_settings_set_entry(K_PLACE, spot)


def into_view(window):
    """ Just shown and off every screen (a screen unplugged, or a place saved while minimized): the Inbox moves to the middle of the main screen """
    try:
        if window.TKroot.state() != 'normal' or on_screen(window.current_frame_location()):
            return
        (sw, sh), (w, h) = window.get_screen_size(), window.size
        window.move(max(0, (sw - w) // 2), max(0, (sh - h) // 3))
        log.info('the Inbox was off every screen - moved to the middle')
    except Exception as e:
        log.warning(f'into_view: {e}')


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


K_UPDATE_TICK = '-UPDATE TICK-'                                   # New versions' look, every 3 s


def news_colors():
    """ the New versions pop-up and What's new in the Inbox's colors: (background, text, button) """
    return sg.theme_background_color(), sg.theme_text_color(), C_DESTS


def title_text():
    """ the title bar: name + version, and UPDATED until the user has looked (UPDATE block 3) """
    return f'Download Mover {__version__} - Inbox' + ('  -  UPDATED' if update_tag() else '')


def updated_status(window):
    """ the status line says it was updated, until the user has looked - a click on it shows what changed """
    if update_tag():
        window[K_STATUS].update(f"Updated from {update_tag()}  -  click here (or right-click > What's new...) to see what changed", text_color=C_CLIP_TXT)


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


class Clip:
    auto = False                      # each new download goes on the clipboard (setting K_AUTO_CLIP)
    batch = []                        # the downloads put there automatically, AUTO_CLIP_SECONDS or less apart
    when = 0.0                        # when the last of them was put there


def hdrop_bytes(paths):
    """ CF_HDROP data: a DROPFILES header (pFiles = 20, pt = 0,0, fNC = 0, fWide = 1), then each full path in UTF-16 ending in a null, then one more null """
    return struct.pack('<IiiII', 20, 0, 0, 0, 1) + ''.join(os.path.abspath(p) + '\0' for p in paths).encode('utf-16-le') + b'\0\0'


def files_to_clipboard(window, paths, move=False):
    """ Puts files on the Windows clipboard the way Explorer's Ctrl+C (Ctrl+X when move) does: CF_HDROP + 'Preferred DropEffect'.
        Paste in Explorer copies them (moves them when move), paste in a chat or e-mail attaches them.  Returns '' or why it failed """
    if not hasattr(ctypes, 'windll'):
        return 'files go on the clipboard on Windows only'
    k32, u32 = ctypes.WinDLL('kernel32', use_last_error=True), ctypes.WinDLL('user32', use_last_error=True)    # own copies: argtypes set here stay here
    k32.GlobalAlloc.restype, k32.GlobalAlloc.argtypes = ctypes.c_void_p, (ctypes.c_uint, ctypes.c_size_t)
    k32.GlobalLock.restype, k32.GlobalLock.argtypes = ctypes.c_void_p, (ctypes.c_void_p,)
    k32.GlobalUnlock.argtypes = k32.GlobalFree.argtypes = (ctypes.c_void_p,)
    u32.OpenClipboard.argtypes = (ctypes.c_void_p,)
    u32.SetClipboardData.restype, u32.SetClipboardData.argtypes = ctypes.c_void_p, (ctypes.c_uint, ctypes.c_void_p)
    u32.RegisterClipboardFormatW.restype, u32.RegisterClipboardFormatW.argtypes = ctypes.c_uint, (ctypes.c_wchar_p,)

    def put(fmt, data):
        handle = k32.GlobalAlloc(0x0002, len(data))                     # GMEM_MOVEABLE - the clipboard owns it once SetClipboardData succeeds
        pointer = k32.GlobalLock(handle) if handle else None
        if not pointer:
            raise ctypes.WinError(ctypes.get_last_error())
        ctypes.memmove(pointer, data, len(data))
        k32.GlobalUnlock(handle)
        if not u32.SetClipboardData(fmt, handle):
            k32.GlobalFree(handle)
            raise ctypes.WinError(ctypes.get_last_error())

    for _ in range(20):                                                  # another program may have the clipboard open for a moment
        if u32.OpenClipboard(window.TKroot.winfo_id()):                  # an owner window: with none, EmptyClipboard makes SetClipboardData fail
            break
        time.sleep(0.05)
    else:
        return 'busy - another program has it open'
    try:
        u32.EmptyClipboard()
        put(CF_HDROP, hdrop_bytes(paths))
        put(u32.RegisterClipboardFormatW('Preferred DropEffect'), struct.pack('<I', DROPEFFECT_MOVE if move else DROPEFFECT_COPY))
        return ''
    except OSError as e:
        return str(e)
    finally:
        u32.CloseClipboard()


def clip_selected(window, items, move):
    """ CLIPBOARD button, Ctrl+C, Ctrl+X: the selected files go on the clipboard.  True when they did """
    paths = [item.path for item in items if os.path.isfile(item.path)]
    if not paths:
        window[K_STATUS].update('Select one or more files first' if not items else 'The selected file(s) are gone from the folder', text_color=C_REMOVE_TXT)
        return False
    error = files_to_clipboard(window, paths, move)
    if error:
        window[K_STATUS].update(f'Clipboard: {error}', text_color=C_REMOVE_TXT)
        return False
    what = os.path.basename(paths[0]) if len(paths) == 1 else f'{len(paths)} files'
    window[K_STATUS].update(f'Cut: {what}  -  paste in Explorer moves it' if move else f'On the clipboard: {what}', text_color=C_CLIP_TXT)
    log.info(f'{"cut" if move else "copied"} to the clipboard: {paths}')
    return True


def auto_clip(window, path):
    """ 'New downloads go on the clipboard': puts this download there, with the ones that finished just before it.  Returns text for the status line """
    if not Clip.auto:
        return ''
    if time.time() - Clip.when > AUTO_CLIP_SECONDS:
        Clip.batch = []
    Clip.batch = [p for p in Clip.batch if p != path and os.path.isfile(p)] + [path]
    Clip.when = time.time()
    error = files_to_clipboard(window, Clip.batch)
    if error:
        log.info(f'new download not put on the clipboard: {error}')
        return f'  -  clipboard: {error}'
    return '  -  on the clipboard' + (f' with {len(Clip.batch) - 1} more' if len(Clip.batch) > 1 else '')


def make_menu():
    """ the Inbox's right-click menu - the tray icon's right-click opens the same one """
    tick = lambda on: '✓ ' if on else '    '
    tray = [f'{tick(Tray.use)}Minimize to tray when closed::{K_MIN_TO_TRAY}'] if SystemTray else []
    tray += [f'{tick(startup_on())}Start with Windows, in the tray::{K_STARTUP}'] if SystemTray and sg.running_windows() else []
    clip = [f'    Copy to Clipboard   (Ctrl+C)::{K_CLIPBOARD}', f'    Cut to Clipboard   (Ctrl+X)::{K_CUT}', f'{tick(Clip.auto)}New downloads go on the clipboard::{K_AUTO_CLIP}']
    return ['', [f'    Download Mover {__version__}::Version', '---',                     # from the tray there's nothing else saying what this menu belongs to
                 '    Scan Now::Scan Now', '---', *clip, '---', '    Change Watched Folder...::Change Watched Folder...', '    Open Watched Folder::Open Watched Folder',
                 '    Show Log::Show Log', '---', *tray, '---', '    Edit Me::Edit Me', f'    Version {__version__}::Version',
                 f"    What's new...::{K_NEWS}", *update_menu(tick), f'    Exit::{K_EXIT}']]


def apply_menu(window):
    menu = make_menu()
    for element in window.element_list():
        element.set_right_click_menu(menu, propogate_to_window=True)
    style_menus(window)


def file_info_text(paths):
    if len(paths) == 1:
        p = paths[0].path
        try:
            st = os.stat(p)
            mod = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            return f'{os.path.basename(p)}\nSize: {human_size(st.st_size)}      Modified: {mod}      Type: {os.path.splitext(p)[1] or "(none)"}'
        except OSError:
            return f'{os.path.basename(p)}\n(file no longer exists)'
    total = sum(os.path.getsize(p.path) for p in paths if os.path.exists(p.path))
    return f'{len(paths)} files selected\nTotal size: {human_size(total)}'


def set_toggle(window, key, on, label):
    window[key].update(('☑  ' if on else '☐  ') + label, button_color=C_TOGGLE_ON if on else C_TOGGLE_OFF)


class Drag:
    paths = ()                        # the files of the drag in progress / just ended
    press = None                      # pressed on a file that was already selected: becomes a click on it if no drag follows
    keep = False                      # that press kept the other files selected - the Listbox's own motion is skipped until the release


def enable_drag_out(window):
    """ Files can be dragged out of NEW FILES into Explorer or another program (tkinterdnd2's drag source).  False when tkinterdnd2 isn't there.
        A press on a file that's already selected keeps the rest selected, so several can be dragged; let go without dragging and just that one is selected """
    if not TkinterDnD:
        return False
    try:
        TkinterDnD._require(window.TKroot)
    except Exception as e:
        log.info(f'dragging out is off - tkdnd did not load: {e}')
        return False
    box = window[K_FILES].widget
    distance = round(4 * max(1.0, window.TKroot.winfo_fpixels('1i') / 96))                         # Windows' 4 px drag distance, scaled
    window.TKroot.tk.eval(f'set ::tkdnd::_dx {distance}; set ::tkdnd::_dy {distance}')

    def start(event):
        Drag.press = None                                                                            # a drag, not a click
        Drag.paths = tuple(item.path for item in window[K_FILES].get() if os.path.isfile(item.path))
        log.debug(f'drag out: {Drag.paths}')
        return (('copy', 'move'), DND_FILES, Drag.paths) if Drag.paths else 'refuse_drop'

    def press(event):
        i = box.nearest(event.y)
        row = box.bbox(i)
        Drag.press, Drag.keep = None, False
        if event.state & 0x0005 or not row or not row[1] <= event.y < row[1] + row[3] or not box.selection_includes(i) or len(box.curselection()) < 2:
            return None                                                                              # Shift / Ctrl, not on a selected file, or just one: the usual click
        Drag.press, Drag.keep = i, True
        box.focus_set()
        return 'break'                                                                               # skips the Listbox's own press, which would drop the others

    def motion(event):
        return 'break' if Drag.keep else None

    def release(event):
        if Drag.press is not None:                                                                   # pressed on a selected file and let go without dragging
            i, Drag.press = Drag.press, None
            box.selection_clear(0, 'end')
            box.selection_set(i)
            box.selection_anchor(i)
            box.activate(i)
            box.event_generate('<<ListboxSelect>>')
        Drag.keep = False

    box.drag_source_register(1, DND_FILES)
    box.dnd_bind('<<DragInitCmd>>', start)
    box.dnd_bind('<<DragEndCmd>>', lambda event: window.write_event_value(K_DRAGGED, event.action))
    tags = list(box.bindtags())
    at = tags.index('Listbox')
    box.bindtags(tuple(tags[:at] + ['DragKeepsSelection'] + tags[at:]))                             # after tkdnd's own tag, before the Listbox's
    for sequence, handler in (('<ButtonPress-1>', press), ('<B1-Motion>', motion), ('<ButtonRelease-1>', release)):
        box.bind_class('DragKeepsSelection', sequence, handler)
    return True


def bind_double_click(window):
    """ Double-click a file in NEW FILES = open it: the row under the mouse, not the space below the last one, not with Shift / Ctrl held """
    box = window[K_FILES].widget

    def double(event):
        i = box.nearest(event.y)
        row = box.bbox(i)
        if row and row[1] <= event.y < row[1] + row[3] and not event.state & 0x0005:
            window.write_event_value(K_DOUBLE, window[K_FILES].get_list_values()[i].path)
    box.bind('<Double-Button-1>', double, add='+')


def make_window(watch_folder, dests, pending, autohide):
    font = ('Segoe UI', 11)
    sg.set_options(font=font)
    files_col = [[sg.Text('NEW FILES  (Ctrl/Shift-click for several)', key=K_FILES_HEAD, text_color='white', background_color=C_FILES, expand_x=True, pad=(0, (0, 4)))],
                 [sg.Listbox(pending, key=K_FILES, size=(45, 14), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED, enable_events=True, expand_x=True, expand_y=True, highlight_background_color=C_FILES, highlight_text_color='white')],
                 [sg.Button('Open File', key=K_OPEN_FILE, button_color=('white', C_FILES), tooltip='Open the selected file - or double-click it'),
                  sg.Button('Open Folder', key=K_OPEN_WATCH, button_color=('white', C_FILES), tooltip='Open the watched folder (shown at the top)'),
                  sg.Button('Leave in Downloads', key=K_SKIP, button_color=('white', C_SKIP), tooltip='Remove from this list but leave the file where it is'),
                  sg.Button('Delete', key=K_DELETE, button_color=('white', C_REMOVE), tooltip=f'Delete the selected file(s) - they go to {BACKUP_SUBDIR} inside the watched folder, so Undo can bring them back'),
                  sg.Push(), sg.Button('Scan Now', key=K_SCAN, button_color=('white', C_FILES), tooltip='Check the watched folder now for new or overwritten files')]]
    dests_col = [[sg.Text('DESTINATIONS  (most recent first)', text_color='white', background_color=C_DESTS, expand_x=True, pad=(0, (0, 4)))],
                 [sg.Listbox(sorted_dests(dests), key=K_DESTS, size=(55, 14), enable_events=True, expand_x=True, expand_y=True, highlight_background_color=C_DESTS, highlight_text_color='white')],
                 [sg.Button('Browse for New Folder...', key=K_BROWSE, button_color=('white', C_DESTS)), sg.Button('Open Folder', key=K_OPEN_DEST, button_color=('white', C_DESTS)), sg.Button('Remove from List', key=K_REMOVE_DEST, button_color=('white', C_REMOVE))]]
    layout = [[sg.Text(f'Watching: {watch_folder}', key=K_WATCH, text_color=C_FILES_TXT, font=('Segoe UI', 10)), sg.Push(), sg.Text(f'Download Mover v{__version__}', text_color=C_SKIP_TXT, font=('Segoe UI', 10))],
              [sg.Text('', key=K_INFO, size=(80, 2), background_color=C_INFO_BG, text_color=C_INFO_TXT, pad=(4, 6), expand_x=True)],
              [sg.Column(files_col, expand_x=True, expand_y=True, pad=(0, 0)), sg.VSeparator(), sg.Column(dests_col, expand_x=True, expand_y=True, pad=(0, 0))],
              [sg.Button('MOVE  ➜', key=K_MOVE, button_color=('white', C_DESTS), font=('Segoe UI', 12, 'bold'), size=(12, 1), bind_return_key=True),
               sg.Button('COPY  ➜', key=K_COPY, button_color=('white', C_COPY), font=('Segoe UI', 12, 'bold'), size=(12, 1)),
               sg.Button('CLIPBOARD', key=K_CLIPBOARD, button_color=('white', C_CLIP), font=('Segoe UI', 12, 'bold'), size=(12, 1),
                         tooltip='Put the selected file(s) on the clipboard (Ctrl+C) - paste in Explorer copies them, in a chat or email attaches them.  Ctrl+X: paste moves them'),
               sg.Button('Undo', key=K_UNDO, button_color=('white', C_UNDO), size=(10, 1), disabled=True, tooltip='Reverse the last Move/Copy (restores overwritten files from the backup folder)'),
               sg.Button(('☑  ' if autohide else '☐  ') + 'Auto-hide after Move/Copy', key=K_AUTOHIDE, button_color=C_TOGGLE_ON if autohide else C_TOGGLE_OFF, border_width=0, tooltip='When lit, the window hides itself as soon as a Move/Copy/Clipboard finishes without errors'),
               sg.Text('', key=K_STATUS, text_color=C_DESTS_TXT, expand_x=True, enable_events=True), sg.Text('Esc hides', text_color=C_SKIP_TXT, font=('Segoe UI', 9))]]
    place_inbox(title_text())
    window = sg.Window(title_text(), layout, finalize=True, resizable=True, keep_on_top=True, right_click_menu=make_menu(), right_click_menu_background_color=sg.theme_background_color(), right_click_menu_text_color=sg.theme_text_color(),
                       right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU, enable_close_attempted_event=True, icon=TRAY_ICON, auto_save_location=True)
    style_menus(window)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Home>', K_HOME)
    window.bind('<End>', K_END)
    for sequence, key in (('<Control-c>', K_CLIPBOARD), ('<Control-C>', K_CLIPBOARD), ('<Control-x>', K_CUT), ('<Control-X>', K_CUT)):
        window.bind(sequence, key)                                       # capital C / X too, for Caps Lock
    bind_double_click(window)
    window.set_min_size((900, 420))
    return window


def refresh_files(window, pending):
    window[K_FILES].update(values=pending)
    window[K_INFO].update(file_info_text(pending[:1]) if pending else 'Inbox is empty - waiting for new downloads...')
    if pending:
        window[K_FILES].update(set_to_index=[0])


def refresh_dests(window, dests, select=None):
    items = sorted_dests(dests)
    window[K_DESTS].update(values=items)
    if select in items:
        window[K_DESTS].update(set_to_index=[items.index(select)])
    elif items:
        window[K_DESTS].update(set_to_index=[0])


def do_delete(window, values, pending, known, undo_stack):
    """ 'Delete' the selected files: they are moved into the watched folder's backup subfolder (timestamped) so Undo can restore them """
    files = values[K_FILES]
    if not files:
        window[K_STATUS].update('Select one or more files first', text_color=C_REMOVE_TXT)
        return
    ok, errors, ops = 0, [], []
    for item in files:
        src = item.path
        try:
            backup_dir = os.path.join(os.path.dirname(src), BACKUP_SUBDIR)
            os.makedirs(backup_dir, exist_ok=True)
            stem, ext = os.path.splitext(os.path.basename(src))
            trash = os.path.join(backup_dir, f'{stem}.{datetime.datetime.now():%Y%m%d_%H%M%S}{ext}')
            shutil.move(src, trash)
            pending.remove(item)
            known.pop(src, None)
            ops.append((src, trash, None, True))        # same shape as a move: undo moves it back from the backup folder
            log.info(f'deleted {src} -> {trash}')
            ok += 1
        except Exception as e:
            errors.append(f'{os.path.basename(src)}: {e}')
    if ops:
        undo_stack.append(ops)
        del undo_stack[:-UNDO_DEPTH]
        window[K_UNDO].update(f'Undo ({len(undo_stack)})', disabled=False)
    refresh_files(window, pending)
    window[K_STATUS].update(f'Deleted {ok} file(s) (kept in {BACKUP_SUBDIR} - Undo restores)' + (f'   ({len(errors)} failed)' if errors else ''), text_color=C_REMOVE_TXT)
    if errors:
        sg.popup_error('\n'.join(errors), title='Some files failed', keep_on_top=True)


def undo_last(window, pending, known, undo_stack):
    """ Reverse the most recent Move/Copy: put moved files back in the watched folder, delete copies, restore any overwritten originals from backup """
    if not undo_stack:
        return
    ops, errors, restored = undo_stack.pop(), [], 0
    for src, target, backup, move in reversed(ops):
        try:
            if move:
                shutil.move(target, src)
                if FileItem(src) not in pending:
                    pending.append(FileItem(src))
                known[src] = mtime(src)
            else:
                os.remove(target)
            if backup:
                shutil.move(backup, target)
            restored += 1
        except Exception as e:
            errors.append(f'{os.path.basename(target)}: {e}')
    log.info(f'undo: {restored} reversed, {len(errors)} failed')
    refresh_files(window, pending)
    window[K_UNDO].update(f'Undo ({len(undo_stack)})' if undo_stack else 'Undo', disabled=not undo_stack)
    window[K_STATUS].update(f'Undone: {restored} file(s) put back' + (f'   ({len(errors)} failed)' if errors else ''), text_color=C_REMOVE_TXT if errors else C_UNDO_TXT)
    if errors:
        sg.popup_error('\n'.join(errors), title='Undo problems', keep_on_top=True)


def do_transfer(window, values, pending, dests, known, undo_stack, move):
    files = values[K_FILES]
    dest = values[K_DESTS][0] if values[K_DESTS] else None
    if not files:
        window[K_STATUS].update('Select one or more files first', text_color=C_REMOVE_TXT)
        return False
    if not dest:
        window[K_STATUS].update('Select a destination folder first', text_color=C_REMOVE_TXT)
        return False
    if not os.path.isdir(dest):
        window[K_STATUS].update(f'Destination no longer exists: {dest}', text_color=C_REMOVE_TXT)
        return False
    ok, errors, ops = 0, [], []
    for item in files:
        src = item.path
        try:
            target = os.path.join(dest, os.path.basename(src))
            backup = backup_existing(target)             # overwrite, but keep the old file in the backup folder
            if move:
                shutil.move(src, target)
                pending.remove(item)
                known.pop(src, None)
            else:
                shutil.copy2(src, target)
            ops.append((src, target, backup, move))
            log.info(f'{"moved" if move else "copied"} {src} -> {target}' + (f' (old file backed up to {backup})' if backup else ''))
            ok += 1
        except Exception as e:
            errors.append(f'{os.path.basename(src)}: {e}')
    if ops:
        undo_stack.append(ops)
        del undo_stack[:-UNDO_DEPTH]
        window[K_UNDO].update(f'Undo ({len(undo_stack)})', disabled=False)
    touch_dest(dests, dest)
    refresh_files(window, pending)
    refresh_dests(window, dests, select=dest)
    verb = 'Moved' if move else 'Copied'
    overwrote = sum(1 for op in ops if op[2])
    window[K_STATUS].update(f'{verb} {ok} file(s) to {dest}' + (f'  -  {overwrote} overwritten (backup kept)' if overwrote else '') + (f'   ({len(errors)} failed)' if errors else ''), text_color=C_REMOVE_TXT if errors else (C_DESTS_TXT if move else C_COPY_TXT))
    if errors:
        sg.popup_error('\n'.join(errors), title='Some files failed', keep_on_top=True)
    return ok > 0 and not errors


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def is_new_or_changed(path, known):
    """ True if the file wasn't there before, or has been overwritten since we last saw it (known maps path -> mtime) """
    m = mtime(path)
    return m is not None and known.get(path) != m


def scan_folder(folder, known):
    """ Return files that are new or modified since last seen, and record their mtimes in known. Used at startup, by the timer fallback and Scan Now """
    found = []
    try:
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if os.path.isfile(path) and not is_partial(path) and is_new_or_changed(path, known):
                known[path] = mtime(path)
                found.append(path)
    except OSError:
        pass
    return found


# ================================================================ main
def main():
    Update.default = 'auto'                                    # a tray app: new versions by itself
    instance_sock = claim_single_instance(INSTANCE_PORT)       # a previous copy, if any, is told to exit first
    sg.user_settings_filename(filename=SETTINGS_FILE)
    update_check()                                             # UPDATE block 3's first look now: UPDATED in the first title
    watch_folder = sg.user_settings_get_entry('-watch-folder-', DEFAULT_WATCH)
    if not os.path.isdir(watch_folder):
        watch_folder = sg.popup_get_folder('Choose the folder to watch for new files', default_path=DEFAULT_WATCH, keep_on_top=True) or DEFAULT_WATCH
        sg.user_settings_set_entry('-watch-folder-', watch_folder)
    dests = load_dests()
    pending = []                                 # files waiting for a decision (shown in the Inbox)
    known = {}                                   # path -> mtime of every file seen; only NEW or OVERWRITTEN files are offered
    waiting = set()                              # files currently in a "wait until download finished" thread
    undo_stack = []                              # list of operations (one entry per Move/Copy click), newest last
    scan_folder(watch_folder, known)             # prime "known" so files already there at startup are ignored

    autohide = sg.user_settings_get_entry('-autohide-', True)
    Tray.use = bool(SystemTray) and sg.user_settings_get_entry(K_MIN_TO_TRAY, True)
    Clip.auto = sg.user_settings_get_entry(K_AUTO_CLIP, False)
    window = make_window(watch_folder, dests, pending, autohide)
    refresh_files(window, pending)
    refresh_dests(window, dests)
    if enable_drag_out(window):
        window[K_FILES_HEAD].update('NEW FILES  (Ctrl/Shift-click for several, drag them out)')
    tray_start(window, TRAY_ICON, f'Download Mover {__version__} - watching {watch_folder}')
    observer = start_watcher(window, watch_folder)
    if observer is None:
        window.timer_start(POLL_MS, repeating=True)
    if instance_sock:
        threading.Thread(target=instance_listener, args=(instance_sock, window, K_QUIT_REQUEST), daemon=True).start()
    else:
        log.warning('could not claim the single-instance port - a previous copy may still be running')
    if Tray.use:
        window.hide()                            # live in the tray until something arrives
        window.TKroot.after(8000, lambda: window_show(window) if window_hidden(window) and not Tray.icon else None)   # no icon came: the Inbox shows
        for _ in range(0 if START_IN_TRAY else 30):     # the icon is made in a thread - give it a moment for the balloon (none at sign-in)
            if Tray.icon:
                Tray.icon.show_message('Download Mover', f'Watching {watch_folder}')
                break
            time.sleep(0.1)

    def show():
        window.un_hide()
        window.bring_to_front()
        window[K_FILES].set_focus()
        window.TKroot.after(200, lambda: into_view(window))

    log.info(f'started - watching {watch_folder}, tray={"yes" if Tray.use else "NO (psgtray/pystray not available, or turned off)"}, watcher={"watchdog" if observer else "timer"}, {len(known)} existing files ignored')
    window[K_STATUS].update(f'Watcher: {"watchdog" if observer else "timer scan"}   Tray: {"on" if Tray.use else "off"}', text_color=C_SKIP_TXT)
    updated_status(window)
    window.timer_start(3000, key=K_UPDATE_TICK, repeating=True)
    timer_seen = False
    while True:
        event, values = window.read()
        if isinstance(event, str) and '::' in event:                     # right-click menu items come back as 'label::key'
            event = event.split('::')[-1]
        if tray_event(window, event, values):                            # tray click shows/hides the Inbox, right-click opens the menu
            continue
        if update_event(event):                                          # right-click > Restart, or a New versions choice
            if Update.restart:
                break
            apply_menu(window)
            continue
        if event == K_UPDATE_TICK:
            keep_place(window)
            if update_tick(window, window_hidden(window), False, news_colors()):
                apply_menu(window)                                       # 'Restart - x.y is ready'
            if Update.restart:
                break
            continue
        if event not in (sg.EVENT_TIMER, K_FILES, K_DESTS):
            log.debug(f'event: {event!r}' + (f'  value: {values.get(event)!r}' if isinstance(values, dict) and event in values else ''))
        if event in (sg.WINDOW_CLOSED, 'Exit', K_QUIT_REQUEST):
            if event == K_QUIT_REQUEST:
                log.info('a new copy was launched - exiting so it can take over')
            break
        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_ESCAPE):
            if Tray.use:
                window.hide()
            else:
                break
        elif event == K_MIN_TO_TRAY:
            Tray.use = not Tray.use
            sg.user_settings_set_entry(K_MIN_TO_TRAY, Tray.use)
            tray_start(window, TRAY_ICON, f'Download Mover {__version__} - watching {watch_folder}') if Tray.use else tray_stop()
            if window_hidden(window):
                show()                                                   # never hidden with no tray icon to bring it back
            window[K_STATUS].update(f'Minimize to tray: {"on" if Tray.use else "off"}', text_color=C_DESTS_TXT)
            apply_menu(window)
        elif event == K_STARTUP:
            error = set_startup(not startup_on(), TRAY_ICON)
            log.info(f'start with Windows: {"on" if startup_on() else "off"} {error}')
            window[K_STATUS].update(f'Start with Windows, in the tray: {"on" if startup_on() else "off"}' if not error else f'Start with Windows: {error}'[:90],
                                    text_color=C_REMOVE_TXT if error else C_DESTS_TXT)
            apply_menu(window)
        elif event == 'Version':
            sg.popup_scrolled(f'Download Mover {__version__}', __file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == K_NEWS or (event == K_STATUS and update_tag()):    # right-click > What's new..., or a click on the status line
            show_whats_new(news_colors())
            window.set_title(title_text())
            window[K_STATUS].update('')
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        # ---------------- new file arrived (watchdog thread, or timer scan)
        elif event == K_NEW_FILE:
            path = values[event]
            if os.path.isfile(path) and not is_partial(path) and path not in waiting and is_new_or_changed(path, known):
                waiting.add(path)
                threading.Thread(target=wait_until_stable, args=(window, path), daemon=True).start()
        elif event == sg.EVENT_TIMER:
            if not timer_seen:
                timer_seen = True
                log.info('timer scan is running')
            for path in scan_folder(watch_folder, known):
                if path not in waiting:
                    log.debug(f'timer scan found: {path}')
                    waiting.add(path)
                    threading.Thread(target=wait_until_stable, args=(window, path), daemon=True).start()
            for item in pending:
                if not os.path.exists(item.path):
                    window.write_event_value(K_FILE_GONE, item.path)
        elif event == K_FILE_GONE:                   # deleted, renamed or moved out of the folder (pasted after Ctrl+X, say): it leaves the Inbox too
            path = values[event]
            if FileItem(path) in pending and not os.path.exists(path):
                pending.remove(FileItem(path))
                known.pop(path, None)
                refresh_files(window, pending)
                window[K_STATUS].update(f'Gone from the folder: {os.path.basename(path)}', text_color=C_SKIP_TXT)
        elif event == K_FILE_READY:
            path = values[event]
            log.info(f'READY: {path}')
            waiting.discard(path)
            known[path] = mtime(path)
            if os.path.isfile(path):
                fresh = FileItem(path) not in pending                        # not already in the Inbox (Scan Now got it first)
                if fresh:
                    pending.append(FileItem(path))
                refresh_files(window, pending)
                clipped = auto_clip(window, path) if fresh else ''
                window[K_STATUS].update(f'New: {os.path.basename(path)}' + clipped, text_color=C_REMOVE_TXT if 'clipboard:' in clipped else C_CLIP_TXT if clipped else C_FILES_TXT)
                if Tray.icon:
                    Tray.icon.show_message('New download', os.path.basename(path) + clipped)
                show()
        elif event in ('Scan Now', K_SCAN):          # pick up anything new or overwritten that hasn't been offered yet
            added = 0
            for path in scan_folder(watch_folder, known):
                if path not in waiting and FileItem(path) not in pending:
                    pending.append(FileItem(path))
                    added += 1
            log.info(f'scan now: {added} file(s) added')
            refresh_files(window, pending)
            window[K_STATUS].update(f'Scan: {added} new file(s), {len(pending)} in Inbox', text_color=C_FILES_TXT)
            show()
        # ---------------- file list
        elif event == K_FILES:
            window[K_INFO].update(file_info_text(values[K_FILES]) if values[K_FILES] else '')
        elif event == K_OPEN_FILE:
            for p in values[K_FILES][:1]:
                open_file(p.path)
        elif event == K_DOUBLE:
            open_file(values[event])
        elif event in (K_CLIPBOARD, K_CUT):         # CLIPBOARD button / Ctrl+C: paste copies the files.  Ctrl+X: paste in Explorer moves them
            if clip_selected(window, values[K_FILES], move=(event == K_CUT)) and autohide and Tray.use:
                window.hide()                        # out of the way of where it's pasted
        elif event == K_AUTO_CLIP:
            Clip.auto, Clip.batch = not Clip.auto, []
            sg.user_settings_set_entry(K_AUTO_CLIP, Clip.auto)
            window[K_STATUS].update(f'New downloads go on the clipboard: {"on" if Clip.auto else "off"}', text_color=C_CLIP_TXT)
            apply_menu(window)
        elif event == K_SKIP:
            for p in values[K_FILES]:
                pending.remove(p)
            refresh_files(window, pending)
        elif event == K_HOME:
            for key in (K_FILES, K_DESTS):
                if window[key].widget == window.TKroot.focus_get() and window[key].get_list_values():
                    window[key].update(set_to_index=[0])
                    window[key].widget.see(0)
        elif event == K_END:
            for key in (K_FILES, K_DESTS):
                n = len(window[key].get_list_values())
                if window[key].widget == window.TKroot.focus_get() and n:
                    window[key].update(set_to_index=[n - 1])
                    window[key].widget.see(n - 1)
        # ---------------- destinations
        elif event == K_BROWSE:
            folder = sg.popup_get_folder('Choose a destination folder', keep_on_top=True, no_window=True)
            if folder:
                folder = os.path.normpath(folder)
                dests.setdefault(folder, {'count': 0, 'last': time.time()})
                save_dests(dests)
                refresh_dests(window, dests, select=folder)
        elif event == K_REMOVE_DEST and values[K_DESTS]:
            dests.pop(values[K_DESTS][0], None)
            save_dests(dests)
            refresh_dests(window, dests)
        elif event == K_OPEN_DEST and values[K_DESTS]:
            open_folder(values[K_DESTS][0])
        elif event == K_DRAGGED:                     # files dragged out: the ones that left the folder (Explorer moved them) leave the Inbox too
            gone = [p for p in Drag.paths if not os.path.exists(p)]
            for p in gone:
                known.pop(p, None)
                if FileItem(p) in pending:
                    pending.remove(FileItem(p))
            if gone:
                refresh_files(window, pending)
                window[K_STATUS].update(f'Dragged out: {len(gone)} file(s) moved', text_color=C_DESTS_TXT)
                if values[K_DRAGGED] != 'recheck' and len(gone) == len(Drag.paths) and autohide and Tray.use:
                    window.hide()
            elif values[K_DRAGGED] in ('copy', 'move', 'link'):
                window[K_STATUS].update('Dragged out: copied - the file is still here', text_color=C_COPY_TXT)
            if values[K_DRAGGED] not in ('recheck', 'refuse_drop') and len(gone) < len(Drag.paths):
                window.TKroot.after(2000, lambda: window.write_event_value(K_DRAGGED, 'recheck'))   # a move to another drive may still be going
        elif event == K_DELETE:
            do_delete(window, values, pending, known, undo_stack)
        elif event == K_UNDO:
            undo_last(window, pending, known, undo_stack)
        elif event in (K_MOVE, K_COPY):
            if do_transfer(window, values, pending, dests, known, undo_stack, move=(event == K_MOVE)) and autohide and Tray.use:
                window.hide()                        # smooth flow: popup -> pick files -> Move -> gone
        elif event == K_AUTOHIDE:
            autohide = not autohide
            sg.user_settings_set_entry('-autohide-', autohide)
            set_toggle(window, K_AUTOHIDE, autohide, 'Auto-hide after Move/Copy')
        # ---------------- watched folder
        elif event == 'Change Watched Folder...':
            folder = sg.popup_get_folder('Folder to watch for new files', default_path=watch_folder, keep_on_top=True, no_window=True)
            if folder and os.path.isdir(folder):
                if observer:
                    observer.stop()
                watch_folder = os.path.normpath(folder)
                sg.user_settings_set_entry('-watch-folder-', watch_folder)
                known.clear()
                scan_folder(watch_folder, known)
                observer = start_watcher(window, watch_folder)
                window[K_WATCH].update(f'Watching: {watch_folder}')
                if Tray.icon:
                    Tray.icon.set_tooltip(f'Download Mover {__version__} - watching {watch_folder}'[:127])
        elif event in ('Open Watched Folder', K_OPEN_WATCH):
            open_folder(watch_folder)
        elif event == 'Show Log':
            try:
                text = open(LOG_FILE).read()[-6000:]
            except OSError as e:
                text = str(e)
            sg.popup_scrolled(text, title=LOG_FILE, size=(110, 30), keep_on_top=True, non_blocking=True)

    keep_place(window)
    if observer:
        observer.stop()
    hidden = window_hidden(window)
    tray_stop()
    if instance_sock:
        instance_sock.close()
    window.close()
    if Update.restart:                                           # UPDATE block: a fresh copy, as it was
        restart_self(['--tray'] if hidden else [])


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback('Download Mover crashed', e)
