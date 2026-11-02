#!/usr/bin/env python3
"""
titlebar_template.pyw - a window with its own title bar, the way the Toybox does it: icon, title and version, minimize / maximize / close.
Copy it, rename it, then put your program in make_body() and the event loop - the title bar is done.

    The window has no OS title bar (no_titlebar=True): the top row is drawn by the program, in its own colors.
    Drag the bar to move the window, double-click it to maximize / restore; the size grip in the bottom-right corner resizes it.
    On Windows the window keeps its taskbar button (a window without a title bar loses it otherwise) and minimizes to it.
    Right-click anywhere:
        Show title bar / Hide title bar   the normal title bar of your OS instead of this one.  That's the default on Linux and Mac, where a window
                                          without one can't always take the keyboard or show in the taskbar.  The window is rebuilt in place
        Rounded corners (Windows 11)      Windows 11 rounds normal windows; this asks it to round this one too (Windows 10 ignores it)
        Edit Me / Version / Exit
    Both choices are remembered, with the window's size and position.  Escape closes.

    Requires:  pip install PySimpleGUI

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v1.0  First version - the Toybox's title bar plus minimize / maximize, the Show title bar switch and Windows 11 rounded corners
"""
import sys

import PySimpleGUI as sg

VERSION = '1.0'
APP_NAME = 'Titlebar Template'
ICON = b'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'      # 64 px PNG, base64 - a window with a blue title bar
ICON_BAR = b'iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAADk0lEQVR42o2UTWwUZRjHf887787M7s6GpSBtjSkKaSHEeJJoUAIaT0piTOylNxJootGo0YSjF08cOXmRxMhBMRw0SqIGhZJg/QgBBA1JiRTa2tKPLZ3u1+zM+3jYrbX1A57Lm3mS9z//mf+HAALo4MmT3sQHp59r1OJHRNSpqnCPEbEa5ku/XPjq+Pd/7QAef+Hgtsbs9EfVpfk9WZp2tvc3Nhdk0YbNn3RvHxj+ZntUt08OvpVfunnt48rM5O5GdSEzpDgnKxTap+o6Zit7h4iRrJUMIabCic9es7o4s78WL+5uxHOZF23xWoWtFGwTIx2cFbaqGNN+aLYc6hwS5KnFs661MJX5YWFo3+Cr79k0aT2cJTU1pQfpe3aYR7c6Lv3RTTMVRNqIipLzDI0kxTkY6C7i/JCu8SvsXRiV968tm2qzEdmm67V41nmuKcnmvRx6aopX9n/IoeMH6dv1Mi890UXmhPNXpzn66WWGnunn9twy27ojSl1lzOwcbz7/NF8fneViLSYQoxYgUyH04ezkTkqjLzJW6+fG1Ttcn6ygKszHDYqlMqNjy9SbKdWkCfMxfUnEzxeus1TswSxXaAEWl6GSI2pN8dOPY4yc20gU/oa6y9xIFQGsZwhyhsnbDmOE2TQjzZRfPccZZ6mnGYEoCWDBgbF41Umy62O0lhaYywAxfxNZUW2rq86Rz+cJw4CmcyTWJ8wFJMYHEuyKFVQ8xI94+8jr9Pb2kCStVXt0Jk1TisUCX3x5mnNnRygUIwSDGgsubfuyA4cATh3ffXuGYrFI5twaf4sIQRiSy+W4NT6OtQZ1WcdWqz61652fYUiddMwtgGKModlocmH0B9JWizAM8X0fVce6j1gHqGCNh7V2DUMxBi9N8XOWfBi2/+W69Pw7oMD8whzxcow6tyZ6IsKOnbuYuH2Ler2OGPOPSK4C6mq8+gd2UN6wkTRL14rSlpk7M9PEcYzN2Xb8pP2yFXALBgSt12LKm3o4f27kf9vFDwKKxVKbgzrCfMRSZRaTCzCppzYIgit+WJT56ZuIGFcoRKKq/1lh6rStbkf6u5U7rhovypaH+me8QvmmoCqP7Tlw4u7c9NDdyjSqet91qIARQ1d3H6VNvW9cGjl1zCJC34HhwxNiF/x8NJimjTJOhHvWrCpGNAgKk4VS+djFkVPH4F2z5tK+wXd6qC723G9bZ566rgcGfv/8+JF4xbR/AizfppTGQa/fAAAAAElFTkSuQmCC'      # the same at 20 px, for the title bar
WINDOWS, LINUX, MAC = sys.platform == 'win32', sys.platform.startswith('linux'), sys.platform == 'darwin'

# ---------- Look: the Toybox palette ----------
BG, C_BAR, C_TITLE, C_DIM, C_ACCENT = '#141821', '#1b2130', '#e6eaf2', '#8a93a3', '#1e9bff'
C_BTN_HOVER, C_CLOSE_HOVER, C_MENU_SEL = '#2f3a4e', '#c0392b', '#2a62a8'
TOYBOX_DARK = {"BACKGROUND": BG, "TEXT": '#d6dbe5', "INPUT": '#1e2430', "TEXT_INPUT": '#e6eaf2', "SCROLL": '#1e2430', "BUTTON": ('#ffffff', '#2a62a8'),
               "PROGRESS": (C_ACCENT, '#1e2430'), "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0}
FONT, FONT_BAR, FONT_BTN, FONT_SMALL, FONT_MENU = ('Segoe UI', 11), ('Segoe UI', 11, 'bold'), ('Segoe UI', 12), ('Segoe UI', 9), ('Segoe UI', 10)
DEFAULT_SIZE = (760, 480)
MIN_SIZE = (420, 240)

# ---------- Keys ----------
K_BAR = '-BAR-'                       # the title bar (a Column) - dragging it moves the window
K_MIN = '-MIN-'
K_MAX = '-MAX-'
K_CLOSE = '-CLOSE-'
K_INPUT = '-INPUT-'
K_GO = '-GO-'
K_LOG = '-LOG-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_ROUND = '-ROUND-'                   # right-click: rounded corners on / off
K_SET_TITLEBAR = '-os title bar-'     # settings-file entries
K_SET_ROUND = '-rounded corners-'
K_SET_SIZE = '-window size-'
MENU_SHOW, MENU_HIDE = 'Show title bar', 'Hide title bar'


class G:                              # program-wide state
    restore_to = None                 # while maximized: the geometry to go back to
    minimized = False                 # minimized from the bar - it has a frame for as long as it's on the taskbar
    drag = None                       # (dx, dy) from the window's corner to the mouse while the bar is being dragged
    rounded = True


# ---------- Win32: the taskbar button, the monitor's work area, rounded corners ----------
if WINDOWS:
    import ctypes
    from ctypes import wintypes

    class MONITORINFO(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT), ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]

    user32, dwmapi = ctypes.WinDLL('user32'), ctypes.WinDLL('dwmapi')       # own copies: setting argtypes here can't change PySimpleGUI's calls
    for name, args, res in (('GetParent', [wintypes.HWND], wintypes.HWND), ('GetWindowLongW', [wintypes.HWND, ctypes.c_int], ctypes.c_long),
                            ('SetWindowLongW', [wintypes.HWND, ctypes.c_int, ctypes.c_long], ctypes.c_long),
                            ('MonitorFromWindow', [wintypes.HWND, wintypes.DWORD], wintypes.HMONITOR),
                            ('GetMonitorInfoW', [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)], wintypes.BOOL)):
        getattr(user32, name).argtypes, getattr(user32, name).restype = args, res
    dwmapi.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]


def hwnd_of(window):
    """The Windows handle of the window itself - tk's winfo_id is a frame inside it"""
    return user32.GetParent(window.TKroot.winfo_id())


def taskbar_style(window):
    """A window with no title bar is a 'tool window' to Windows - no taskbar button, so it gets lost behind others.  Make it an app window"""
    if WINDOWS:
        try:
            GWL_EXSTYLE, WS_EX_APPWINDOW, WS_EX_TOOLWINDOW = -20, 0x00040000, 0x00000080
            hwnd = hwnd_of(window)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW)
        except Exception:
            pass


def set_corners(window, rounded):
    """Windows 11: round (or square) the corners - DWMWA_WINDOW_CORNER_PREFERENCE.  Windows 10 says no; that's fine"""
    if WINDOWS:
        try:
            preference = ctypes.c_int(2 if rounded else 1)                                  # DWMWCP_ROUND / DWMWCP_DONOTROUND
            dwmapi.DwmSetWindowAttribute(hwnd_of(window), 33, ctypes.byref(preference), ctypes.sizeof(preference))
        except Exception:
            pass


def work_area(window):
    """(x, y, width, height) a maximized window gets: on Windows the monitor it's on minus the taskbar, elsewhere the whole screen"""
    if WINDOWS:
        try:
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(user32.MonitorFromWindow(hwnd_of(window), 2), ctypes.byref(info)):        # MONITOR_DEFAULTTONEAREST
                r = info.rcWork
                return r.left, r.top, r.right - r.left, r.bottom - r.top
        except Exception:
            pass
    return 0, 0, window.TKroot.winfo_screenwidth(), window.TKroot.winfo_screenheight()


# ---------- The title bar ----------
def title_bar():
    """Icon, name and version on the left, the three buttons on the right - all on the bar's color"""
    def button(glyph, key, tip):
        return sg.Text(f'  {glyph}  ', key=key, font=FONT_BTN, text_color=C_DIM, background_color=C_BAR, enable_events=True, pad=(0, 0), tooltip=tip)
    return sg.Column([[sg.Image(data=ICON_BAR, background_color=C_BAR, pad=((10, 6), 6)),
                       sg.Text(APP_NAME, font=FONT_BAR, text_color=C_TITLE, background_color=C_BAR, pad=(0, 0)),
                       sg.Text(f'v{VERSION}', font=FONT_SMALL, text_color=C_DIM, background_color=C_BAR, pad=((8, 0), 0)),
                       sg.Push(background_color=C_BAR),
                       button('–', K_MIN, ' Minimize '), button('□', K_MAX, ' Maximize '), button('✕', K_CLOSE, ' Close ')]],
                     key=K_BAR, background_color=C_BAR, expand_x=True, pad=(0, 0))


def wire_bar(window):
    """Dragging the bar moves the window (a maximized one comes back to its own size under the mouse), double-click maximizes / restores,
       and the buttons light up under the mouse - the close button red"""
    root, buttons = window.TKroot, {window[k].Widget: k for k in (K_MIN, K_MAX, K_CLOSE)}

    def press(e):
        G.drag = (e.x_root - root.winfo_x(), e.y_root - root.winfo_y())

    def motion(e):
        if G.drag is None:
            return
        if G.restore_to:                                                                    # dragging a maximized window: back to its own size first,
            w = int(G.restore_to.split('x')[0])                                             # with the mouse at the same spot across the bar
            G.drag = (round(w * G.drag[0] / max(1, root.winfo_width())), G.drag[1])
            root.geometry(G.restore_to.split('+')[0])
            G.restore_to = None
            show_max_button(window)
        root.geometry(f'+{e.x_root - G.drag[0]}+{e.y_root - G.drag[1]}')

    def release(e):
        G.drag = None

    frame = window[K_BAR].Widget
    for w in [frame] + frame.winfo_children() + [c for ch in frame.winfo_children() for c in ch.winfo_children()]:
        if w in buttons:
            hover = C_CLOSE_HOVER if buttons[w] == K_CLOSE else C_BTN_HOVER
            w.bind('<Enter>', lambda e, w=w, c=hover: w.configure(bg=c, fg='#ffffff'), add='+')
            w.bind('<Leave>', lambda e, w=w: w.configure(bg=C_BAR, fg=C_DIM), add='+')
            continue
        w.bind('<ButtonPress-1>', press, add='+')
        w.bind('<B1-Motion>', motion, add='+')
        w.bind('<ButtonRelease-1>', release, add='+')
        w.bind('<Double-Button-1>', lambda e: toggle_maximize(window), add='+')


def show_max_button(window):
    window[K_MAX].update('  ❐  ' if G.restore_to else '  □  ')
    window[K_MAX].set_tooltip(' Restore ' if G.restore_to else ' Maximize ')


def toggle_maximize(window):
    """Fill the work area, or go back to the size and place it had.  Done by hand: a window without a title bar can't use the OS's maximize"""
    root = window.TKroot
    if G.restore_to:
        root.geometry(G.restore_to)
        G.restore_to = None
    else:
        G.restore_to = root.geometry()
        x, y, w, h = work_area(window)
        root.geometry(f'{w}x{h}+{x}+{y}')
    show_max_button(window)


def minimize(window):
    """tk can't minimize a window without a frame, so it gets one for as long as it's on the taskbar (restored() takes it off again).
       PySimpleGUI makes a no-title-bar window a 'dock' on Linux - those can't be minimized either, so it's a normal window meanwhile"""
    root = window.TKroot
    G.minimized = True
    if LINUX:
        root.wm_attributes('-type', 'normal')
    else:
        root.wm_overrideredirect(False)
    root.iconify()


def restored(window, event):
    """Back from the taskbar: the frame comes off again.  On Windows tk makes the window over when the frame goes on or off, so the taskbar
       style and the corners go on again too.  Events still queued from the minimize arrive while it's iconic - those are skipped"""
    root = window.TKroot
    if not G.minimized or event.widget is not root or root.state() == 'iconic':
        return
    G.minimized = False
    root.withdraw()
    if LINUX:
        root.wm_attributes('-type', 'dock')
    else:
        root.wm_overrideredirect(True)
        taskbar_style(window)
    root.deiconify()
    set_corners(window, G.rounded)


# ---------- The window ----------
def make_body():
    """Your program: an ordinary PySimpleGUI layout under the title bar"""
    return [[sg.Text('Your program goes here', font=('Segoe UI', 14, 'bold'), text_color=C_ACCENT)],
            [sg.Text('Everything under the title bar is an ordinary PySimpleGUI layout.  Right-click for the title bar choices.', text_color=C_DIM)],
            [sg.Text('Name:'), sg.Input(key=K_INPUT, expand_x=True, focus=True), sg.Button('Say hi', key=K_GO, bind_return_key=True)],
            [sg.Multiline('', key=K_LOG, size=(60, 8), disabled=True, autoscroll=True, expand_x=True, expand_y=True)]]


def make_menu(custom):
    tick = '✓ ' if G.rounded else '    '
    corners = [f'{tick}Rounded corners (Windows 11)::{K_ROUND}'] if WINDOWS else []
    return ['', [MENU_SHOW if custom else MENU_HIDE] + corners + ['---', 'Edit Me', 'Version', 'Exit']]          # offers the other way round


def style_menus(window):
    """tk draws menus Windows-gray: give the right-click menu (and any sub-menu) the window's colors, flat and compact"""
    def style(menu):
        menu.configure(bg=C_BAR, fg=C_TITLE, activebackground=C_MENU_SEL, activeforeground='#ffffff', bd=0, activeborderwidth=1, relief='flat', font=FONT_MENU)
        for child in menu.winfo_children():
            style(child)
    style(window.TKRightClickMenu)


def make_window(custom, location=(None, None), size=None):
    """custom = draw our own title bar (no_titlebar), else the OS's.  Rebuilt from scratch when that changes"""
    status = [sg.Text('', key=K_STATUS, font=FONT_SMALL, text_color=C_DIM, expand_x=True, pad=((12, 0), (2, 6)))]
    layout = ([[title_bar()]] if custom else []) + \
             [[sg.Column(make_body(), expand_x=True, expand_y=True, pad=((12, 12), (10, 4)))],
              status + ([sg.Sizegrip(background_color=BG)] if custom else [])]
    window = sg.Window(f'{APP_NAME}  v{VERSION}', layout, no_titlebar=custom, margins=(0, 0), resizable=True, finalize=True, font=FONT, icon=ICON,
                       location=location, size=size or DEFAULT_SIZE, auto_save_location=True, enable_close_attempted_event=True,
                       right_click_menu=make_menu(custom), right_click_menu_background_color=C_BAR, right_click_menu_text_color=C_TITLE,
                       right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU)
    window.set_min_size(MIN_SIZE)
    style_menus(window)
    window.bind('<Escape>', K_ESCAPE)
    text = window[K_LOG].Widget                                                             # keyboard scrolling of the read-only log
    text.bind('<Button-1>', lambda e: text.focus_set(), add='+')
    for seq, amount, unit in (('<Up>', -1, 'units'), ('<Down>', 1, 'units'), ('<Prior>', -1, 'pages'), ('<Next>', 1, 'pages')):
        text.bind(seq, lambda e, a=amount, u=unit: (text.yview_scroll(a, u), 'break')[1])
    text.bind('<Home>', lambda e: (text.yview_moveto(0), 'break')[1])
    text.bind('<End>', lambda e: (text.yview_moveto(1), 'break')[1])
    if custom:
        wire_bar(window)
        window.TKroot.bind('<Map>', lambda e: restored(window, e), add='+')
        window.TKroot.bind('<Expose>', lambda e: restored(window, e), add='+')
        if WINDOWS:
            taskbar_style(window)
            window.TKroot.withdraw()                                                        # the taskbar only notices the new style when the window shows again
            window.TKroot.after(10, window.TKroot.deiconify)
    window.TKroot.after(30, lambda: set_corners(window, G.rounded))
    return window


def saved_size():
    size = sg.user_settings_get_entry(K_SET_SIZE, None)
    return tuple(size) if isinstance(size, (list, tuple)) and len(size) == 2 and all(isinstance(v, int) and v > 100 for v in size) else None


def main():
    sg.set_options(dpi_awareness=True)
    sg.theme_add_new('ToyboxDark', TOYBOX_DARK)
    sg.theme('ToyboxDark')
    sg.user_settings_filename(filename='titlebar_template.json')                          # rename with your program
    custom = not sg.user_settings_get_entry(K_SET_TITLEBAR, LINUX or MAC)                  # the OS title bar by default on Linux and Mac
    G.rounded = sg.user_settings_get_entry(K_SET_ROUND, True)
    window = make_window(custom, size=saved_size())
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, sg.WINDOW_CLOSED, K_CLOSE, K_ESCAPE, 'Exit'):
            break
        if event == K_MIN:
            minimize(window)
        elif event == K_MAX:
            toggle_maximize(window)
        elif event in (MENU_SHOW, MENU_HIDE):                                               # rebuild in the same place, the other way round
            custom = event == MENU_HIDE
            sg.user_settings_set_entry(K_SET_TITLEBAR, not custom)
            location, size = window.current_location(), (window.size if not G.restore_to else None)
            G.restore_to = None
            window.close()
            window = make_window(custom, location, size or saved_size())
        elif isinstance(event, str) and event.endswith(K_ROUND):
            G.rounded = not G.rounded
            sg.user_settings_set_entry(K_SET_ROUND, G.rounded)
            set_corners(window, G.rounded)
            window.set_right_click_menu(make_menu(custom))
            style_menus(window)
        elif event == K_GO:
            window[K_LOG].print(f'Hi {values[K_INPUT] or "there"}!')
            window[K_STATUS].update(f'Said hi to {values[K_INPUT] or "nobody"}')
        elif event == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME}  version {VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
    if not window.was_closed() and not G.restore_to:
        sg.user_settings_set_entry(K_SET_SIZE, list(window.size))                           # the size for next time (not the maximized one)
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e)
