"""
PySimpleGUI Window RAM + CPU + Location Tagger
- Snapshot on startup: outlines every visible top-level window with a unique
  color and labels it with RAM (red) + CPU % (cyan) + location (gold) + size (goldenrod) + process/title,
  all on a single line above the window. Each of RAM / CPU / Location can be toggled on/off.
- A panel box is drawn on the left side of the Graph element listing
  minimized/cloaked windows plus a RAM/CPU summary.
- Help text and status text are drawn directly on the Graph (top-left) instead
  of using separate Text elements, so the Graph fills 100% of the window.
- HOME = rescan, END = toggle autorefresh, PgUp/PgDn = refresh speed
- F6 / F7 / F8 = toggle RAM / CPU / Location display (saved in user settings)
- ESC: quit
Requires: pip install PySimpleGUI pywin32 keyboard psutil

CHANGE LOG (newest first, 1 line per change):
2026-09-04  Location shown as (x,y) gold + WxH goldenrod; hotkey hook fires only the key just pressed, not every held key
2026-09-04  RAM/CPU/Location displays individually toggleable (F6/F7/F8, persisted); CPU timer+sampling fully off when disabled
"""

import ctypes
import time
from ctypes import wintypes
import tkinter.font as tkfont
import PySimpleGUI as sg
import win32gui
import win32process
import win32api
import keyboard
import psutil

ctypes.windll.shcore.SetProcessDpiAwareness(2)

# --- Key naming convention ---
# K_  = standalone key (not part of a repeated element block)
# K_B_ = lambda that builds a tuple key for elements inside a repeated block

K_ESC = 'esc'                       # Exit
K_REFRESH = 'home'                  # Refresh
K_AUTO_REFRESH = 'end'              # Toggle auto refresh
K_SPEED_UP = 'page up'
K_SPEED_DOWN = 'page down'
K_TOGGLE_RAM = 'f6'                 # Toggle RAM display
K_TOGGLE_CPU = 'f7'                 # Toggle CPU display (also starts/stops the CPU sampling timer)
K_TOGGLE_LOC = 'f8'                 # Toggle window location display
HOTKEYS = (K_ESC, K_REFRESH, K_AUTO_REFRESH, K_SPEED_UP, K_SPEED_DOWN, K_TOGGLE_RAM, K_TOGGLE_CPU, K_TOGGLE_LOC)

K_CPU_SAMPLE = '-CPU SAMPLE-'       # slow timer that samples CPU % independently of the fast redraw timer

K_AUTO_REFRESH_ON = 'refresh is on'         # Used in the settings file, not the window
K_AUTO_REFRESH_SPEED_OFFSET = 'refresh speed offset'
K_SHOW_RAM = 'show ram'
K_SHOW_CPU = 'show cpu'
K_SHOW_LOC = 'show location'


SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

DWMWA_CLOAKED = 14
DWMWA_EXTENDED_FRAME_BOUNDS = 9

FONT_LABEL = ('Any', 14, 'italic')          # process name | title
FONT_RAM_TEXT = ('Consolas', 24, )          # big stat font - used for RAM, CPU and location
FONT_RAM_TEXT_SIDE_PANEL = ('Consolas', 20, )
FONT_PANEL_HEADER = ('Consolas', 14, 'bold')
FONT_PANEL_TEXT = ('Consolas', 12)
FONT_HELP = ('Any', 11, 'bold')
FONT_STATUS = ('Any', 11)

RAM_TEXT_COLOR = 'red'
RAM_TEXT_COLOR_SIDE_PANEL = 'red'
CPU_TEXT_COLOR = 'cyan'
CPU_TEXT_COLOR_SIDE_PANEL = 'cyan'
LOC_TEXT_COLOR = 'gold'                     # window position (x,y)
LOC_TEXT_COLOR_SIDE_PANEL = 'gold'
SIZE_TEXT_COLOR = 'goldenrod'               # window size WxH - darker yellow
SIZE_TEXT_COLOR_SIDE_PANEL = 'goldenrod'

NUM_CPUS = psutil.cpu_count() or 1          # cpu_percent() sums cores (can exceed 100%) - divide so 100% == whole machine
CPU_SAMPLE_MS = 1000                        # how often CPU % is re-measured. Redraws in between just reuse the last sample

PANEL_WIDTH = 420
PANEL_MARGIN = 15
PANEL_LINE_HEIGHT = 20
RAM_LABEL_GAP = 10  # px gap between stat texts and the label/title text that follows

HELP_TEXT = ('Window RAM/CPU Tagger  |  HOME = rescan  |  END = Toggle auto refresh  |  PgUp/PgDn = refresh speed  |  '
             'F6/F7/F8 = Toggle RAM/CPU/Location  |  ESC = quit')
HEADER_X = 10
HEADER_Y = 10
HEADER_GAP = 12
PANEL_TOP_MARGIN = 34  # keeps the side panel below the header line

SPEEDS = (5, 10, 50, 100, 200, 300, 400, 500, 1000)

COLOR_PALETTE = (
    'yellow',
    'chartreuse',
    'orange',
    'dodger blue',
    'magenta',
    'spring green',
    'medium purple1',
    'deep pink',
    'sky blue1',
    'khaki1',
    'turquoise1',      # cool teal, replaces red
    'white',           # crisp neutral, replaces salmon1
)

class G:
    window: sg.Window = None
    cur_speed_offset = 6
    refresh_timer_id = None
    cpu_timer_id = None     # K_CPU_SAMPLE timer. None whenever CPU display is off -> zero CPU-sampling work happens
    show_ram = True
    show_cpu = True
    show_loc = False
    procs = {}          # pid -> psutil.Process. Kept alive between scans so cpu_percent() has a baseline to measure against
    cpu_cache = {}      # pid -> last sampled CPU %. Sampled every CPU_SAMPLE_MS, NOT every redraw, so it's readable at 10 ms refresh rates

def hotkey_callback(event):
    """Fires an event for the key that was just pressed. Only looks at THIS key-down event, never at other keys currently (or stale-ly) held,
    so pressing F6 while END is still down (or stuck in keyboard's pressed table) can't re-toggle autorefresh."""
    name = (event.name or '').lower()
    if event.event_type == keyboard.KEY_DOWN and name in HOTKEYS:
        G.window.write_event_value(name, None)


def get_virtual_screen_rect():
    """Returns (x, y, width, height) of the full virtual desktop spanning all monitors."""
    x = win32api.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = win32api.GetSystemMetrics(SM_YVIRTUALSCREEN)
    w = win32api.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = win32api.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    return x, y, w, h


dwmapi = ctypes.windll.dwmapi


def get_visible_rect(hwnd):
    """Returns (left, top, right, bottom) excluding DWM's invisible shadow/resize border."""
    rect = wintypes.RECT()
    hr = dwmapi.DwmGetWindowAttribute(wintypes.HWND(hwnd), ctypes.c_int(DWMWA_EXTENDED_FRAME_BOUNDS), ctypes.byref(rect), ctypes.sizeof(rect))
    if hr == 0:
        return rect.left, rect.top, rect.right, rect.bottom
    return win32gui.GetWindowRect(hwnd)


def is_cloaked(hwnd):
    """DWM-cloaked windows (e.g. hidden UWP host frames) report IsWindowVisible=True
    but have no actual visible content. Returns True if the window is cloaked."""
    cloaked = wintypes.DWORD(0)
    hr = dwmapi.DwmGetWindowAttribute(wintypes.HWND(hwnd), ctypes.c_int(DWMWA_CLOAKED), ctypes.byref(cloaked), ctypes.sizeof(cloaked))
    if hr == 0:
        return cloaked.value != 0
    return False


def get_process_info(hwnd):
    """Returns (pid, proc_name, ram_mb, cpu_pct). RAM is only read when show_ram; cpu_pct comes from the cache filled by sample_cpu()."""
    pid = None
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = G.procs.get(pid)
        if proc is None:
            proc = psutil.Process(pid)
            G.procs[pid] = proc
            if G.show_cpu:
                proc.cpu_percent(interval=None)     # prime - first call on a fresh Process object always returns 0.0
        proc_name = proc.name()
        ram_mb = proc.memory_info().rss / (1024 * 1024) if G.show_ram else None
        cpu_pct = G.cpu_cache.get(pid, 0.0) if G.show_cpu else None
        return pid, proc_name, ram_mb, cpu_pct
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        G.procs.pop(pid, None)
        G.cpu_cache.pop(pid, None)
        return None, 'unknown', None, None


def sample_cpu():
    """Measures CPU % for every cached process since the last call. Runs on its own slow timer (CPU_SAMPLE_MS), only while CPU display is on."""
    for pid, proc in list(G.procs.items()):
        try:
            G.cpu_cache[pid] = proc.cpu_percent(interval=None) / NUM_CPUS
        except Exception:
            G.procs.pop(pid, None)
            G.cpu_cache.pop(pid, None)


def enum_all_windows(exclude_hwnd=None):
    """
    Returns (visible_windows, excluded_windows).
    visible_windows:  list of (hwnd, title, rect, pid, proc_name, ram_mb, cpu_pct)
    excluded_windows: list of (hwnd, title, rect, pid, proc_name, ram_mb, cpu_pct, reason)
                       where rect is the *restored* size for minimized windows,
                       and reason is 'minimized' or 'cloaked'.
    """
    visible = []
    excluded = []

    def callback(hwnd, _):
        if hwnd == exclude_hwnd:
            return True
        if not win32gui.IsWindowVisible(hwnd):
            return True

        title = win32gui.GetWindowText(hwnd)
        if not title.strip():
            return True

        minimized = win32gui.IsIconic(hwnd)
        cloaked = is_cloaked(hwnd)

        if minimized:
            placement = win32gui.GetWindowPlacement(hwnd)
            left, top, right, bottom = placement[4]  # rcNormalPosition (restored size)
        else:
            left, top, right, bottom = get_visible_rect(hwnd)

        w, h = right - left, bottom - top
        if w <= 0 or h <= 0:
            return True

        pid, proc_name, ram_mb, cpu_pct = get_process_info(hwnd)
        entry = (hwnd, title, (left, top, right, bottom), pid, proc_name, ram_mb, cpu_pct)

        if minimized or cloaked:
            reason = 'minimized' if minimized else 'cloaked'
            excluded.append(entry + (reason,))
        else:
            visible.append(entry)
        return True

    win32gui.EnumWindows(callback, None)

    live_pids = {w[3] for w in visible} | {w[3] for w in excluded}     # drop cached Process objects for windows that are gone
    G.procs = {pid: proc for pid, proc in G.procs.items() if pid in live_pids}
    G.cpu_cache = {pid: pct for pid, pct in G.cpu_cache.items() if pid in live_pids}
    return visible, excluded


def fmt_ram(ram_mb):
    return f'{ram_mb:.1f} MB' if ram_mb is not None else 'N/A'


def fmt_cpu(cpu_pct):
    return f'{cpu_pct:.1f}%' if cpu_pct is not None else 'N/A'


def stat_segments(rect, ram_mb, cpu_pct, side_panel=False):
    """Returns (ram_cpu, loc): two lists of enabled (text, color) pairs. loc = [('(x,y)', gold), ('WxH', goldenrod)] when location is on."""
    sp = side_panel
    ram_cpu, loc = [], []
    if G.show_ram: ram_cpu.append((fmt_ram(ram_mb), RAM_TEXT_COLOR_SIDE_PANEL if sp else RAM_TEXT_COLOR))
    if G.show_cpu: ram_cpu.append((fmt_cpu(cpu_pct), CPU_TEXT_COLOR_SIDE_PANEL if sp else CPU_TEXT_COLOR))
    if G.show_loc:
        l, t, r, b = rect
        loc.append((f'({l},{t})', LOC_TEXT_COLOR_SIDE_PANEL if sp else LOC_TEXT_COLOR))
        loc.append((f'{r - l}x{b - t}', SIZE_TEXT_COLOR_SIDE_PANEL if sp else SIZE_TEXT_COLOR))
    return ram_cpu, loc


def draw_window_labels(graph, graph_left, graph_top, windows_info):
    """Draws each window's outline plus a single-line label above it:
    enabled stats (RAM red, CPU cyan, Location gold, Size goldenrod) in the big font, followed by 'proc_name | title'."""
    fig_ids = []
    big_font_measurer = tkfont.Font(font=FONT_RAM_TEXT)

    for i, (hwnd, title, rect, pid, proc_name, ram_mb, cpu_pct) in enumerate(windows_info):
        left, top, right, bottom = rect
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]

        gx1, gy1 = left - graph_left, top - graph_top
        gx2, gy2 = right - graph_left, bottom - graph_top

        fig_ids.append(graph.draw_rectangle((gx1, gy1), (gx2, gy2), line_color=color, line_width=3))

        label_text = f'{proc_name} | {title[:40]}'
        label_y = gy1 - 14
        x = gx1 + 5

        ram_cpu, loc = stat_segments(rect, ram_mb, cpu_pct)
        for text, stat_color in ram_cpu + loc:
            fig_ids.append(graph.draw_text(text, (x, label_y), color=stat_color, font=FONT_RAM_TEXT, text_location=sg.TEXT_LOCATION_LEFT))
            x += big_font_measurer.measure(text) + RAM_LABEL_GAP
        fig_ids.append(graph.draw_text(label_text, (x, label_y), color=color, font=FONT_LABEL, text_location=sg.TEXT_LOCATION_LEFT))
    return fig_ids


def draw_side_panel(graph, panel_top_left, visible, excluded):
    """Draws a bordered box on the Graph with minimized/cloaked window info + summary,
    entirely using graph.draw_rectangle / graph.draw_text (no Multiline).
    Each line is a list of (text, color, font) segments drawn left-to-right so RAM (red) and CPU (cyan) can share a line."""
    fig_ids = []
    px, py = panel_top_left
    measurers = {}

    def measure(text, font):
        if font not in measurers:
            measurers[font] = tkfont.Font(font=font)
        return measurers[font].measure(text)

    total_visible_ram = sum(w[5] for w in visible if w[5] is not None) if G.show_ram else 0
    total_excluded_ram = sum(w[5] for w in excluded if w[5] is not None) if G.show_ram else 0
    total_visible_cpu = sum(w[6] for w in visible if w[6] is not None) if G.show_cpu else 0
    total_excluded_cpu = sum(w[6] for w in excluded if w[6] is not None) if G.show_cpu else 0

    blank = [('', None, FONT_PANEL_TEXT)]
    lines = []  # each item: list of (text, color, font) segments
    lines.append([(f'MINIMIZED / CLOAKED ({len(excluded)})', 'orange', FONT_PANEL_HEADER)])
    lines.append(blank)

    for hwnd, title, rect, pid, proc_name, ram_mb, cpu_pct, reason in excluded:
        lines.append([(f'[{reason.upper()}] {proc_name}', 'yellow', FONT_PANEL_TEXT)])
        ram_cpu, loc = stat_segments(rect, ram_mb, cpu_pct, side_panel=True)
        if ram_cpu: lines.append([(t, c, FONT_RAM_TEXT_SIDE_PANEL) for t, c in ram_cpu])
        if loc: lines.append([(t, c, FONT_RAM_TEXT_SIDE_PANEL) for t, c in loc])       # own line - 4 big stats won't fit in PANEL_WIDTH
        lines.append([(title[:44], 'gray', FONT_PANEL_TEXT)])
        lines.append(blank)

    lines.append([('SUMMARY', 'orange', FONT_PANEL_HEADER)])
    lines.append(blank)
    lines.append([(f'Visible windows  : {len(visible)}', 'white', FONT_PANEL_TEXT)])
    lines.append([(f'Minimized/cloaked: {len(excluded)}', 'white', FONT_PANEL_TEXT)])
    if G.show_ram:
        lines.append([(f'Visible RAM      : {total_visible_ram:.1f} MB', 'white', FONT_PANEL_TEXT)])
        lines.append([(f'Excluded RAM     : {total_excluded_ram:.1f} MB', 'white', FONT_PANEL_TEXT)])
    if G.show_cpu:
        lines.append([(f'Visible CPU      : {total_visible_cpu:.1f}%', 'white', FONT_PANEL_TEXT)])
        lines.append([(f'Excluded CPU     : {total_excluded_cpu:.1f}%', 'white', FONT_PANEL_TEXT)])
    total_segs = []
    if G.show_ram: total_segs.append((f'{total_visible_ram + total_excluded_ram:.1f} MB', RAM_TEXT_COLOR, FONT_RAM_TEXT))
    if G.show_cpu: total_segs.append((f'{total_visible_cpu + total_excluded_cpu:.1f}%', CPU_TEXT_COLOR, FONT_RAM_TEXT))
    if total_segs:
        lines.append(total_segs + [('(TOTAL)', 'white', FONT_PANEL_TEXT)])

    panel_height = PANEL_MARGIN * 2 + len(lines) * PANEL_LINE_HEIGHT + 200
    box_id = graph.draw_rectangle((px, py), (px + PANEL_WIDTH, py + panel_height), line_color='white', fill_color='black', line_width=2)
    fig_ids.append(box_id)

    y = py + PANEL_MARGIN
    for segments in lines:
        x = px + PANEL_MARGIN
        for text, color, font in segments:
            if text:
                fig_ids.append(graph.draw_text(text, (x, y), color=color, font=font, text_location=sg.TEXT_LOCATION_LEFT))
                x += measure(text, font) + RAM_LABEL_GAP
        first_font = segments[0][2]
        y += PANEL_LINE_HEIGHT + (8 if first_font in (FONT_RAM_TEXT, FONT_RAM_TEXT_SIDE_PANEL) else 0)

    return fig_ids


def draw_header(graph, help_width_measurer, status_text):
    """Draws the help text (static) and status text on the Graph, side by side,
    replacing the old Text elements. Returns (help_fig_id, status_fig_id)."""
    help_fig_id = graph.draw_text(HELP_TEXT, (HEADER_X, HEADER_Y), color='yellow', font=FONT_HELP, text_location=sg.TEXT_LOCATION_LEFT)
    help_width = help_width_measurer.measure(HELP_TEXT)
    status_fig_id = graph.draw_text(status_text, (HEADER_X + help_width + HEADER_GAP, HEADER_Y), color='yellow', font=FONT_STATUS, text_location=sg.TEXT_LOCATION_LEFT)
    return help_fig_id, status_fig_id


def main():
    G.cur_speed_offset = sg.user_settings_get_entry(K_AUTO_REFRESH_SPEED_OFFSET, G.cur_speed_offset)
    auto_refresh_on = sg.user_settings_get_entry(K_AUTO_REFRESH_ON, False)
    G.show_ram = sg.user_settings_get_entry(K_SHOW_RAM, True)
    G.show_cpu = sg.user_settings_get_entry(K_SHOW_CPU, True)
    G.show_loc = sg.user_settings_get_entry(K_SHOW_LOC, False)
    print(f'startup {auto_refresh_on=} {G.show_ram=} {G.show_cpu=} {G.show_loc=}')
    sg.theme('Black')

    TRANSPARENT_COLOR = '#010101'
    vx, vy, canvas_w, canvas_h = get_virtual_screen_rect()

    layout = [[sg.Graph(canvas_size=(canvas_w, canvas_h), graph_bottom_left=(0, canvas_h), graph_top_right=(canvas_w, 0), key='-GRAPH-',
                        background_color=TRANSPARENT_COLOR, enable_events=True)]]

    window = sg.Window('RAM Tagger', layout, no_titlebar=True, keep_on_top=True, transparent_color=TRANSPARENT_COLOR, location=(vx, vy),
                       margins=(0, 0), finalize=True, alpha_channel=.9)

    G.window = window
    window.refresh()

    graph = window['-GRAPH-']
    my_hwnd = int(window.TKroot.frame(), 16)

    graph_left = graph.Widget.winfo_rootx()
    graph_top = graph.Widget.winfo_rooty()

    help_font_measurer = tkfont.Font(font=FONT_HELP)

    content_fig_ids = []   # window outlines/labels + side panel - cleared on every rescan
    status_fig_id = None   # redrawn only when status text changes
    auto_refresh_timer_id = None

    help_fig_id, status_fig_id = draw_header(graph, help_font_measurer, '')

    def update_status():
        nonlocal status_fig_id
        if status_fig_id:
            graph.delete_figure(status_fig_id)
        onoff = lambda flag: 'ON' if flag else 'OFF'
        text = (f'Autorefresh {onoff(auto_refresh_timer_id is not None)} @ {SPEEDS[G.cur_speed_offset]} ms   |   '
                f'RAM {onoff(G.show_ram)}   CPU {onoff(G.show_cpu)}   LOC {onoff(G.show_loc)}')
        help_width = help_font_measurer.measure(HELP_TEXT)
        status_fig_id = graph.draw_text(text, (HEADER_X + help_width + HEADER_GAP, HEADER_Y), color='yellow', font=FONT_STATUS, text_location=sg.TEXT_LOCATION_LEFT)

    def rescan_and_draw():
        nonlocal content_fig_ids
        for fid in content_fig_ids:
            graph.delete_figure(fid)

        visible, excluded = enum_all_windows(exclude_hwnd=my_hwnd)
        content_fig_ids = draw_window_labels(graph, graph_left, graph_top, visible)
        content_fig_ids += draw_side_panel(graph, (PANEL_MARGIN - 5, PANEL_TOP_MARGIN), visible, excluded)

    def start_cpu_sampling():
        """Primes every cached process so the first timer sample is real, then starts the slow sampling timer."""
        for proc in list(G.procs.values()):
            try: proc.cpu_percent(interval=None)
            except Exception: pass
        G.cpu_timer_id = window.timer_start(CPU_SAMPLE_MS, key=K_CPU_SAMPLE, repeating=True)

    def stop_cpu_sampling():
        if G.cpu_timer_id is not None:
            window.timer_stop(G.cpu_timer_id)
            G.cpu_timer_id = None
        G.cpu_cache.clear()

    if G.show_cpu:
        enum_all_windows(exclude_hwnd=my_hwnd)      # priming pass so the very first drawn CPU values aren't all 0.0%
        time.sleep(0.25)
        sample_cpu()
    rescan_and_draw()
    if G.show_cpu:
        start_cpu_sampling()

    keyboard.hook(hotkey_callback)

    if auto_refresh_on:
        auto_refresh_timer_id = window.timer_start(SPEEDS[G.cur_speed_offset], key=K_REFRESH, repeating=True)
    update_status()

    while True:
        event, values = window.read(timeout=None)
        if event in (sg.WIN_CLOSED, K_ESC):
            break
        if event == K_REFRESH:
            rescan_and_draw()
        elif event == K_CPU_SAMPLE:
            sample_cpu()
            if auto_refresh_timer_id is None:           # autorefresh off -> nothing else will redraw, so show the new CPU numbers now
                rescan_and_draw()
        elif event == K_AUTO_REFRESH:
            if auto_refresh_timer_id is not None:            # if currently autorefreshing
                window.timer_stop(auto_refresh_timer_id)
                auto_refresh_timer_id = None
            else:
                auto_refresh_timer_id = window.timer_start(SPEEDS[G.cur_speed_offset], key=K_REFRESH, repeating=True)
            update_status()
            sg.user_settings_set_entry(K_AUTO_REFRESH_ON, auto_refresh_timer_id is not None)
            sg.user_settings_set_entry(K_AUTO_REFRESH_SPEED_OFFSET, G.cur_speed_offset)
        elif event in (K_SPEED_UP, K_SPEED_DOWN):
            G.cur_speed_offset += 1 if event == K_SPEED_UP else -1
            if G.cur_speed_offset < 0: G.cur_speed_offset = 0
            if G.cur_speed_offset >= len(SPEEDS): G.cur_speed_offset = len(SPEEDS) - 1
            update_status()
            if auto_refresh_timer_id is not None:
                window.timer_stop(auto_refresh_timer_id)
                auto_refresh_timer_id = window.timer_start(SPEEDS[G.cur_speed_offset], key=K_REFRESH, repeating=True)
            sg.user_settings_set_entry(K_AUTO_REFRESH_SPEED_OFFSET, G.cur_speed_offset)
        elif event in (K_TOGGLE_RAM, K_TOGGLE_CPU, K_TOGGLE_LOC):
            if event == K_TOGGLE_RAM:
                G.show_ram = not G.show_ram
            elif event == K_TOGGLE_LOC:
                G.show_loc = not G.show_loc
            else:
                G.show_cpu = not G.show_cpu
                start_cpu_sampling() if G.show_cpu else stop_cpu_sampling()
            sg.user_settings_set_entry(K_SHOW_RAM, G.show_ram)
            sg.user_settings_set_entry(K_SHOW_CPU, G.show_cpu)
            sg.user_settings_set_entry(K_SHOW_LOC, G.show_loc)
            update_status()
            rescan_and_draw()

    window.close()


if __name__ == '__main__':
    main()
