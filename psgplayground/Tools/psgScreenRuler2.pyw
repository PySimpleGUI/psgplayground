"""
PySimpleGUI Screen Ruler + WinSpy-style Window Inspector
- Press T to toggle between MEASURE mode (drag rectangles) and INSPECT mode (WinSpy)
- Press R to drop a Screen-Ruler-style ruler spanning the last measured/inspected rectangle
- Press S to save a screenshot of the last measured/inspected rectangle
- Press C to clear all placed rulers
- ESC: quit
Requires: pip install PySimpleGUI pywin32 keyboard mouse pillow

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.0.1  Claude: S saves into this PC's Screenshots folder (Windows' known folder under Pictures) - one PC's path was built in
"""

import ctypes
from ctypes import wintypes
import time
import PySimpleGUI as sg
import win32gui
import win32api
import win32con
import keyboard
import mouse
from PIL import ImageGrab
from pathlib import Path
import uuid

VERSION = '1.0.1'


ctypes.windll.shcore.SetProcessDpiAwareness(2)

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

KB_ESC = 'esc'
KB_TOGGLE = 't'
KB_RULER = 'r'
KB_CLEAR_RULERS = 'x'
KB_SCREENSHOT = 's'
KB_RULER_COLOR = 'c'

MOUSE_MOVE = 'MOUSE_MOVE'
MOUSE_DOWN = 'MOUSE_DOWN'
MOUSE_UP = 'MOUSE_UP'

RULER_COLORS = ('red', 'yellow', 'dark orchid1', 'white', 'green1')

HELP_TEXT = ('T = toggle mode  |  R = drop ruler  |  S = screenshot rect  |  '
             'C = cycle ruler color  |  X = clear rulers  |  ESC = quit  |  v') + VERSION

FONT_MODE = ('Any', 11, 'bold')
FONT_HELP = ('Any', 10)
FONT_INFO = ('Any', 11)

MODE_COLOR = 'orange'
HELP_COLOR = 'yellow'
INFO_COLOR = 'cyan'

HEADER_X = 10
MODE_Y = 10
HELP_Y = 30
INFO_Y = 50

class G:
    window: sg.Window = None
    ruler_color_offset: int = 0         # Current coloris at this offset in RULER_COLORS

KB_DRAG_MODIFIER = 'shift'
drag_modifier_held = False

def hotkey_callback(event):
    global drag_modifier_held

    try:
        pressed_keys = [e.name.lower() for e in keyboard._pressed_events.values()]
    except AttributeError:
        pressed_keys = []

    is_held_now = KB_DRAG_MODIFIER in pressed_keys
    if is_held_now != drag_modifier_held:
        drag_modifier_held = is_held_now
        G.window.write_event_value(KB_DRAG_MODIFIER, is_held_now)

    for key in pressed_keys:
        if key == KB_ESC:
            G.window.write_event_value(KB_ESC, None)
        elif key == KB_RULER:
            G.window.write_event_value(KB_RULER, None)
        elif key == KB_TOGGLE:
            G.window.write_event_value(KB_TOGGLE, None)
        elif key == KB_CLEAR_RULERS:
            G.window.write_event_value(KB_CLEAR_RULERS, None)
        elif key == KB_SCREENSHOT:
            G.window.write_event_value(KB_SCREENSHOT, None)
        elif key == KB_RULER_COLOR:
            G.window.write_event_value(KB_RULER_COLOR, None)


def mouse_event_callback(event):
    if isinstance(event, mouse.MoveEvent):
        G.window.write_event_value(MOUSE_MOVE, (event.x, event.y))
    elif isinstance(event, mouse.ButtonEvent):
        if event.event_type == mouse.DOWN and event.button == mouse.LEFT:
            G.window.write_event_value(MOUSE_DOWN, mouse.get_position())
        elif event.event_type == mouse.UP and event.button == mouse.LEFT:
            G.window.write_event_value(MOUSE_UP, mouse.get_position())



def set_clickthrough(hwnd, enable: bool):
    style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
    if enable:
        style |= (WS_EX_LAYERED | WS_EX_TRANSPARENT)
    else:
        style &= ~WS_EX_TRANSPARENT
        style |= WS_EX_LAYERED
    win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style)



def bgr_from_hex(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return win32api.RGB(r, g, b)


def set_fully_opaque_and_solid(hwnd, enable_solid: bool, transparent_color_hex=None):
    style = win32gui.GetWindowLong(hwnd, GWL_EXSTYLE)
    if enable_solid:
        style &= ~WS_EX_LAYERED
        style &= ~WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style)
    else:
        style |= WS_EX_LAYERED
        style |= WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, GWL_EXSTYLE, style)
        if transparent_color_hex:
            color_key = bgr_from_hex(transparent_color_hex)
            win32gui.SetLayeredWindowAttributes(hwnd, color_key, 255, win32con.LWA_COLORKEY)

    win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                           win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                           win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)


def real_child_window_from_point(hwnd, pt):
    point = wintypes.POINT(pt[0], pt[1])
    result = user32.RealChildWindowFromPoint(wintypes.HWND(hwnd), point)
    return result if result else None


def get_deepest_child_at_point(x, y, exclude_hwnd=None):
    hwnd = win32gui.WindowFromPoint((x, y))
    if hwnd == exclude_hwnd:
        return None
    parent = hwnd
    while True:
        try:
            pt = win32gui.ScreenToClient(parent, (x, y))
            child = real_child_window_from_point(parent, pt)
        except Exception:
            break
        if not child or child == parent:
            break
        parent = child
    return parent


dwmapi = ctypes.windll.dwmapi
DWMWA_EXTENDED_FRAME_BOUNDS = 9

def get_visible_rect(hwnd):
    """Returns (left, top, right, bottom) excluding DWM's invisible shadow/resize border."""
    rect = wintypes.RECT()
    hr = dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd),
        ctypes.c_int(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(rect),
        ctypes.sizeof(rect)
    )
    if hr == 0:
        return rect.left, rect.top, rect.right, rect.bottom
    else:
        return win32gui.GetWindowRect(hwnd)  # fallback if DWM call fails



def clear_figure(graph, fig_id):
    if fig_id:
        graph.delete_figure(fig_id)
    return None


def draw_ruler_at(graph, rect):
    # print(f'Drawing rules at {rect=}')
    """Draws a Screen-Ruler-style horizontal + vertical ruler spanning only the given rect.
    rect = (x1, y1, x2, y2) in graph coordinates."""
    x1, y1, x2, y2 = rect
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    w = x2 - x1
    h = y2 - y1
    color = RULER_COLORS[G.ruler_color_offset]
    ids = []

    # Horizontal ruler along the top edge, spanning the rect's width
    ids.append(graph.draw_line((x1, y1), (x2, y1), color=color, width=2))
    for i in range(0, w + 1, 10):
        tick_h = 10 if i % 50 == 0 else 5
        ids.append(graph.draw_line((x1 + i, y1 - tick_h), (x1 + i, y1 + tick_h), color=color, width=1))
        if i % 50 == 0 and i != 0:
            ids.append(graph.draw_text(str(i), (x1 + i, y1 - 18), color=color, font=('Any', 8)))
    ids.append(graph.draw_text(f'{w}px', (x2 - 5, y1 + 12), color='lime', font=('Any', 14), text_location=sg.TEXT_LOCATION_RIGHT))

    # Vertical ruler along the left edge, spanning the rect's height
    ids.append(graph.draw_line((x1, y1), (x1, y2), color=color, width=2))
    for i in range(0, h + 1, 10):
        tick_w = 10 if i % 50 == 0 else 5
        ids.append(graph.draw_line((x1 - tick_w, y1 + i), (x1 + tick_w, y1 + i), color=color, width=1))
        if i % 50 == 0 and i != 0:
            ids.append(graph.draw_text(str(i), (x1 + 14, y1 + i), color=color, font=('Any', 8)))
    ids.append(graph.draw_text(f'{h}px', (x1 - 5, y2 + 12), color='lime', font=('Any', 14)))

    return ids


def screenshots_folder():
    """This PC's Screenshots folder - Windows' known folder (Pictures\\Screenshots wherever Pictures lives, OneDrive included), made if missing"""
    folder = Path.home() / 'Pictures' / 'Screenshots'
    try:
        guid = (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID('{b7bede81-df94-4682-a7d8-57a52620b86f}').bytes_le)    # FOLDERID_Screenshots
        path = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0x8000, None, ctypes.byref(path)) == 0:      # 0x8000 = KF_FLAG_CREATE
            folder = Path(path.value)
            ctypes.windll.ole32.CoTaskMemFree(path)
    except Exception:
        pass
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def take_screenshot(hwnd_to_hide, screen_rect):
    """Hides the overlay, grabs a screenshot of screen_rect, restores the overlay, saves PNG."""
    left, top, right, bottom = screen_rect
    left, right = min(left, right), max(left, right)
    top, bottom = min(top, bottom), max(top, bottom)

    win32gui.ShowWindow(hwnd_to_hide, win32con.SW_HIDE)
    time.sleep(0.08)  # let the compositor repaint before capturing
    img = ImageGrab.grab(bbox=(left, top, right, bottom))
    win32gui.ShowWindow(hwnd_to_hide, win32con.SW_SHOW)

    filename = screenshots_folder() / f'screenshot_{time.strftime("%Y%m%d_%H%M%S")}.png'
    img.save(filename)
    return filename


def main():


    sg.theme('Black')

    TRANSPARENT_COLOR = '#FF00FF'
    TRANSPARENT_COLOR = '#010101'  # near-black, not pure black (avoid clashing with black text backgrounds)
    screen_w, screen_h = sg.Window.get_screen_size()
    canvas_w = screen_w
    canvas_h = screen_h

    MEASURE, INSPECT = 'MEASURE', 'INSPECT'
    mode = INSPECT

    layout = [
        [sg.Graph(canvas_size=(canvas_w, canvas_h), graph_bottom_left=(0, canvas_h), graph_top_right=(canvas_w, 0), key='-GRAPH-', drag_submits=True, background_color=TRANSPARENT_COLOR, enable_events=True, motion_events=True)]
    ]

    window = sg.Window('Ruler + WinSpy', layout, no_titlebar=True, keep_on_top=True, transparent_color=TRANSPARENT_COLOR, location=(0, 0), margins=(0, 0), finalize=True, return_keyboard_events=False, alpha_channel=.9)

    G.window = window

    graph = window['-GRAPH-']
    my_hwnd = int(window.TKroot.frame(), 16)
    set_clickthrough(my_hwnd, enable=(mode == INSPECT))

    start_point = end_point = None
    rect_id = text_id = None
    inspect_rect_id = inspect_text_id = None
    last_hwnd = None
    last_rect = None          # (x1, y1, x2, y2) in graph coords, from MEASURE or INSPECT
    last_screen_rect = None   # (left, top, right, bottom) in screen coords, for screenshots
    rulers = []

    mode_fig_id = None
    info_fig_id = None

    def update_mode(text):
        nonlocal mode_fig_id
        mode_fig_id = clear_figure(graph, mode_fig_id)
        mode_fig_id = graph.draw_text(text, (HEADER_X, MODE_Y), color=MODE_COLOR, font=FONT_MODE,
                                       text_location=sg.TEXT_LOCATION_LEFT)

    def update_info(text):
        nonlocal info_fig_id
        info_fig_id = clear_figure(graph, info_fig_id)
        info_fig_id = graph.draw_text(text, (HEADER_X, INFO_Y), color=INFO_COLOR, font=FONT_INFO,
                                       text_location=sg.TEXT_LOCATION_LEFT)

    graph.draw_text(HELP_TEXT, (HEADER_X, HELP_Y), color=HELP_COLOR, font=FONT_HELP,
                     text_location=sg.TEXT_LOCATION_LEFT)

    update_mode(f'MODE: {mode}')

    keyboard.hook(hotkey_callback)
    mouse.hook(mouse_event_callback)

    while True:
        event, values = window.read(timeout=None)
        if event in (sg.WIN_CLOSED, 'Escape:27', KB_ESC):
            break

        if event == KB_RULER_COLOR:
            G.ruler_color_offset = (G.ruler_color_offset + 1) % len(RULER_COLORS)
            update_info(f'Ruler color changed to: {RULER_COLORS[G.ruler_color_offset]}')
        if event == KB_TOGGLE:
            mode = INSPECT if mode == MEASURE else MEASURE
            update_mode(f'MODE: {mode}')
            set_clickthrough(my_hwnd, enable=(mode == INSPECT))
            rect_id = clear_figure(graph, rect_id)
            text_id = clear_figure(graph, text_id)
            inspect_rect_id = clear_figure(graph, inspect_rect_id)
            inspect_text_id = clear_figure(graph, inspect_text_id)
            start_point = None
            last_hwnd = None
            update_info('')

        if event == KB_RULER:
            # print(f'RULER... {last_rect=}')
            if last_rect:
                rulers.append(draw_ruler_at(graph, last_rect))

        if event == KB_SCREENSHOT:
            if last_screen_rect:
                filename = take_screenshot(my_hwnd, last_screen_rect)
                update_info(f'Saved screenshot: {filename}')
            else:
                update_info('No rectangle to capture yet.')

        if event == KB_CLEAR_RULERS:
            for ids in rulers:
                for fig_id in ids:
                    clear_figure(graph, fig_id)
            rulers = []

        if event == KB_DRAG_MODIFIER:
            holding = values[KB_DRAG_MODIFIER]
            set_fully_opaque_and_solid(my_hwnd, enable_solid=holding, transparent_color_hex=TRANSPARENT_COLOR)

        if mode == MEASURE:
            graph_left = graph.Widget.winfo_rootx()
            graph_top = graph.Widget.winfo_rooty()

            if event == MOUSE_DOWN:
                sx, sy = values[MOUSE_DOWN]
                start_point = (sx - graph_left, sy - graph_top)
                end_point = start_point

            elif event == MOUSE_MOVE and start_point is not None:
                sx, sy = values[MOUSE_MOVE]
                end_point = (sx - graph_left, sy - graph_top)

            elif event == MOUSE_UP:
                start_point = None

            if start_point and end_point:
                rect_id = clear_figure(graph, rect_id)
                text_id = clear_figure(graph, text_id)
                w = abs(end_point[0] - start_point[0])
                h = abs(end_point[1] - start_point[1])
                rect_id = graph.draw_rectangle(start_point, end_point, line_color='red', line_width=2)
                text_id = graph.draw_text(f'{w} x {h} px',
                                          (min(start_point[0], end_point[0]) + 5,
                                           min(start_point[1], end_point[1]) - 10),
                                          color='yellow', font=('Any', 14))
                update_info(f'Rectangle: {w} x {h} px')
                last_rect = (start_point[0], start_point[1], end_point[0], end_point[1])
                last_screen_rect = (start_point[0] + graph_left, start_point[1] + graph_top,
                                    end_point[0] + graph_left, end_point[1] + graph_top)


        if event == MOUSE_MOVE and mode == INSPECT:
            sx, sy = values[MOUSE_MOVE]
            graph_left = graph.Widget.winfo_rootx()
            graph_top = graph.Widget.winfo_rooty()

            hwnd = get_deepest_child_at_point(sx, sy, exclude_hwnd=my_hwnd)
            if hwnd and hwnd != last_hwnd:
                last_hwnd = hwnd
                try:
                    left, top, right, bottom = get_visible_rect(hwnd)
                    cls = win32gui.GetClassName(hwnd)
                    title = win32gui.GetWindowText(hwnd)
                    w, h = right - left, bottom - top

                    gx1, gy1 = left - graph_left, top - graph_top
                    gx2, gy2 = right - graph_left, bottom - graph_top

                    inspect_rect_id = clear_figure(graph, inspect_rect_id)
                    inspect_text_id = clear_figure(graph, inspect_text_id)

                    inspect_rect_id = graph.draw_rectangle((gx1, gy1), (gx2, gy2),
                                                           line_color='lime', line_width=3)
                    inspect_text_id = graph.draw_text(f'{cls} | {w}x{h}px',
                                                      (gx1 + 5, gy1 - 10),
                                                      color='lime', font=('Any', 15))
                    update_info(
                        f'hwnd={hwnd}  class="{cls}"  title="{title}"  rect=({left},{top},{right},{bottom})  size={w}x{h}px'
                    )
                    last_rect = (gx1, gy1, gx2, gy2)
                    last_screen_rect = (left, top, right, bottom)
                except win32gui.error as e:
                    print('** win32gui.error **', e)



    window.close()

if __name__ == '__main__':
    main()