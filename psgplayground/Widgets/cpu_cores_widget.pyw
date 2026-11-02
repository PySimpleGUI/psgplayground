#!/usr/bin/env python
import PySimpleGUI as sg
import os
import sys
import time
import atexit
import threading
import ctypes as ct
import psutil

"""
    Desktop floating widget - CPU Cores
    Uses psutil to display CPU usage of each individual core as a scrolling area graph.
    Click any graph to open a live-refreshing window of the processes running on that core.
    How "what's on this core" is found depends on the OS:
        Linux/BSD  - psutil Process.cpu_num()  (core the process last ran on)
        Windows    - ETW kernel context-switch events via the pywintrace package. Every time the kernel switches threads on a core
                     it logs which thread left and which arrived, so the time each process spent on each core can be totalled.
                     Requires:  pip install pywintrace.  The program relaunches itself as Administrator (UAC prompt) if needed
        otherwise  - falls back to showing the top CPU consumers (any of them could be on the core)
    Python processes show the script / module they are running.
    Several process windows can be open at once. Esc closes the one with focus.
    Copyright 2018-2026 PySimpleGUI. All rights reserved.
"""

GRAPH_WIDTH = 60       # each individual graph size in pixels
GRAPH_HEIGHT = 40
TRANSPARENCY = .8       # how transparent the window looks. 0 = invisible, 1 = normal window
NUM_COLS = 32
POLL_FREQUENCY = 1500   # how often to update graphs AND process windows, in milliseconds
SAMPLE_TIME = 0.4       # seconds to wait for the very 1st sample when a process window opens
MAX_PROCS = 60          # max rows in a process window
WINDOW_TITLE = 'CPU Cores Usage Widget'

colors = ('#23a0a0', '#56d856', '#be45be', '#5681d8', '#d34545', '#BE7C29')

K_GRAPH = '-GRAPH-';    KT_GRAPH = lambda rc: (K_GRAPH, rc)     # rc = (row, col)
K_TXT = '-TXT-';        KT_TXT = lambda rc: (K_TXT, rc)
K_TABLE = '-TABLE-'
K_TITLE = '-TITLE-'
K_ESC, K_HOME, K_END, K_PGUP, K_PGDN = '-ESC-', '-HOME-', '-END-', '-PGUP-', '-PGDN-'

NUM_CORES = psutil.cpu_count()
IS_WINDOWS = sys.platform == 'win32'
try:
    import etw
    from etw import evntrace as et
    from etw.common import RETURN_RAW_UNFORMATTED_DATA
    HAS_ETW = IS_WINDOWS
except ImportError:
    HAS_ETW = False
IS_ADMIN = IS_WINDOWS and ct.windll.shell32.IsUserAnAdmin() != 0

# ---- which method will be used to find the processes on a core ----
if hasattr(psutil.Process, 'cpu_num'):
    MODE = 'cpu_num'
elif HAS_ETW and IS_ADMIN:
    MODE = 'etw'
else:
    MODE = 'fallback'


# DashGraph does the drawing of each graph
class DashGraph(object):
    def __init__(self, graph_elem, text_elem, starting_count, color):
        self.graph_current_item = 0
        self.graph_elem = graph_elem        # type: sg.Graph
        self.text_elem = text_elem
        self.prev_value = starting_count
        self.max_sent = 1
        self.color = color
        self.line_list = []                 # list of currently visible lines. Used to delete old figures

    def graph_percentage_abs(self, value):
        self.line_list.append(self.graph_elem.draw_line((self.graph_current_item, 0), (self.graph_current_item, value), color=self.color))
        if self.graph_current_item >= GRAPH_WIDTH:
            self.graph_elem.move(-1, 0)
            self.graph_elem.delete_figure(self.line_list[0])        # delete the oldest line
            self.line_list = self.line_list[1:]                     # remove line id from list of lines
        else:
            self.graph_current_item += 1

    def text_display(self, text):
        self.text_elem.update(text)


# ======================================================================================================================
#   Windows ETW context-switch tracer
# ======================================================================================================================
class CoreTracer:
    """Listens to kernel CSwitch events. Each event says: on core X at time T, thread OLD stopped and thread NEW started.
       Time between switches is charged to OLD on core X. snapshot(core) returns per-process share of that core's time"""
    SYSTEM_TRACE_GUID = '{9e814aab-f7d3-4c30-bf1f-e4fc1a5b6e1a}'
    THREAD_GUID_DATA1 = 0x3d6fa8d1          # first field of {3d6fa8d1-fe05-11d0-9dda-00c04fd7ba7c}, the Thread event GUID
    CSWITCH_OPCODE = 36
    THREAD_QUERY_LIMITED_INFORMATION = 0x0800

    def __init__(self):
        self.lock = threading.Lock()
        self.core_tid_ticks = {}            # core -> {tid: ticks run on that core since last snapshot}
        self.last_ts = {}                   # core -> timestamp of the last context switch seen on that core
        self.tid_pid = {}                   # cache thread id -> process id
        self.pid_info = {}                  # cache pid -> (name, python script)
        self.k32 = ct.windll.kernel32
        self.k32.OpenThread.restype = ct.c_void_p
        self.k32.OpenThread.argtypes = [ct.c_uint32, ct.c_int, ct.c_uint32]
        self.k32.GetProcessIdOfThread.restype = ct.c_uint32
        self.k32.GetProcessIdOfThread.argtypes = [ct.c_void_p]
        self.k32.CloseHandle.argtypes = [ct.c_void_p]
        provider = etw.ProviderInfo('Kernel', etw.GUID(self.SYSTEM_TRACE_GUID), any_keywords=et.EVENT_TRACE_FLAG_CSWITCH)
        self.job = etw.ETW(session_name=et.KERNEL_LOGGER_NAME, providers=[provider], event_callback=self._on_event, callback_data_flag=RETURN_RAW_UNFORMATTED_DATA)
        self.stop_stale_session()           # a previous crash may have left the kernel logger running with different flags
        self.job.start()
        atexit.register(self.stop)

    def stop_stale_session(self):
        try:
            et.ControlTraceW(0, et.KERNEL_LOGGER_NAME, self.job.properties.get(), et.EVENT_TRACE_CONTROL_STOP)
        except Exception:
            pass

    def stop(self):
        try:
            self.job.stop()
        except Exception:
            pass

    def _on_event(self, item):
        """Called from pywintrace's consumer thread for EVERY kernel event, so keep this fast"""
        record = item[1]
        hdr = record.contents.EventHeader
        if hdr.EventDescriptor.Opcode != self.CSWITCH_OPCODE or hdr.ProviderId.Data1 != self.THREAD_GUID_DATA1:
            return
        core = record.contents.BufferContext.ProcessorNumber
        ts = hdr.TimeStamp
        old_tid = ct.cast(record.contents.UserData, ct.POINTER(ct.c_uint32))[1]       # CSwitch UserData: NewThreadId, OldThreadId, ...
        with self.lock:
            last = self.last_ts.get(core)
            self.last_ts[core] = ts
            if last is not None:
                d = self.core_tid_ticks.setdefault(core, {})
                d[old_tid] = d.get(old_tid, 0) + (ts - last)

    def reset(self, core):
        with self.lock:
            self.core_tid_ticks.pop(core, None)

    def tid_to_pid(self, tid):
        if tid == 0:
            return 0                                                # idle thread
        pid = self.tid_pid.get(tid)
        if pid is None:
            h = self.k32.OpenThread(self.THREAD_QUERY_LIMITED_INFORMATION, 0, tid)
            if h:
                pid = self.k32.GetProcessIdOfThread(h)
                self.k32.CloseHandle(h)
            pid = pid or -1                                         # -1 = thread already gone
            self.tid_pid[tid] = pid
        return pid

    def pid_to_info(self, pid):
        info = self.pid_info.get(pid)
        if info is None:
            try:
                p = psutil.Process(pid)
                name = p.name()
                info = (name, python_script(name, p.cmdline()))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, ValueError):
                info = ('(exited)' if pid == -1 else f'pid {pid}', '')
            self.pid_info[pid] = info
        return info

    def snapshot(self, core):
        """Returns (rows, busy_percent). rows = [pid, name, % of this core, num threads, python script], sorted busiest first"""
        with self.lock:
            tid_ticks = self.core_tid_ticks.pop(core, {})
        total = sum(tid_ticks.values())
        if not total:
            return [], 0.0
        if len(self.tid_pid) > 20000:                               # thread ids get recycled. Flush the cache occasionally
            self.tid_pid.clear(); self.pid_info.clear()
        per_pid = {}                                                # pid -> [ticks, thread count]
        for tid, ticks in tid_ticks.items():
            pid = self.tid_to_pid(tid)
            entry = per_pid.setdefault(pid, [0, 0])
            entry[0] += ticks; entry[1] += 1
        idle = per_pid.pop(0, [0, 0])[0]
        rows = []
        for pid, (ticks, nthreads) in per_pid.items():
            name, script = self.pid_to_info(pid)
            rows.append([pid, name, round(100 * ticks / total, 1), nthreads, script])
        rows.sort(key=lambda r: r[2], reverse=True)
        return rows[:MAX_PROCS], round(100 * (total - idle) / total, 1)


tracer = None       # the one CoreTracer, created when the first process window opens (Windows + admin + pywintrace only)


# ======================================================================================================================
#   Process listing
# ======================================================================================================================
def python_script(name, cmdline):
    """If this is a python process, return what it's running (script/module + args). Otherwise empty string"""
    if not name or not name.lower().startswith('python') or not cmdline or len(cmdline) < 2:
        return ''
    return ' '.join(cmdline[1:])


def prime_cpu_percent():
    """cpu_percent(None) always returns 0 the first time it's called on a process. This gets that 1st call out of the way"""
    for p in psutil.process_iter():
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def affinity_str(p):
    """Compact list of cores a process is allowed on, e.g. '0-7, 16'. Empty string if it can run on all cores"""
    try:
        cores = sorted(p.cpu_affinity())
    except (AttributeError, psutil.AccessDenied, psutil.NoSuchProcess):
        return ''
    if len(cores) >= NUM_CORES:
        return ''
    ranges, start = [], cores[0]
    for prev, cur in zip(cores, cores[1:] + [None]):
        if cur != prev + 1:
            ranges.append(str(start) if start == prev else f'{start}-{prev}')
            start = cur
    return ', '.join(ranges)


def get_processes(core):
    """Returns (rows, title). Rows depend on MODE - see COLUMNS. psutil.process_iter() caches Process objects, so cpu_percent(None) measures since the previous refresh"""
    if MODE == 'etw':
        rows, busy = tracer.snapshot(core)
        return rows, f'Core {core}   busy {busy}%   (share of this core\'s time over the last {POLL_FREQUENCY / 1000:.1f} s)'
    rows = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        if p.pid == 0:                                              # skip Windows "System Idle Process"
            continue
        try:
            cpu = p.cpu_percent(None)
            if MODE == 'cpu_num':
                core_col = p.cpu_num()
                if core_col != core:
                    continue
            else:
                core_col = affinity_str(p)
            rows.append([p.pid, p.info['name'] or '', round(cpu, 1), core_col, python_script(p.info['name'], p.info['cmdline'])])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    rows.sort(key=lambda r: r[2], reverse=True)
    if MODE == 'cpu_num':
        title = f'Core {core}   (processes whose main thread last ran here)'
    else:
        why = 'run as Administrator' if HAS_ETW else 'pip install pywintrace and run as Administrator'
        title = f'Core {core}   top CPU consumers - {why} to see per-core processes.  Affinity shown only if restricted'
    return rows[:MAX_PROCS], title


COLUMNS = {'etw':      (['PID', 'Name', '% of core', 'Threads', 'Python script'], [7, 22, 8, 7, 60]),
           'cpu_num':  (['PID', 'Name', 'CPU %', 'Core', 'Python script'], [7, 22, 6, 5, 60]),
           'fallback': (['PID', 'Name', 'CPU %', 'Affinity', 'Python script'], [7, 22, 6, 10, 60])}


class ProcWindow:
    """A live-refreshing window listing the processes for one core"""
    def __init__(self, core, location):
        global tracer
        self.core = core
        if MODE == 'etw':
            if tracer is None:
                tracer = CoreTracer()
            tracer.reset(core)
        else:
            prime_cpu_percent()
        time.sleep(SAMPLE_TIME)
        rows, title = get_processes(core)
        headings, widths = COLUMNS[MODE]
        layout = [[sg.Text(title, font='Helvetica 9', key=K_TITLE)],
                  [sg.Table(rows, headings=headings, col_widths=widths, auto_size_columns=False, justification='l', num_rows=min(20, max(len(rows), 8)), key=K_TABLE, expand_x=True, expand_y=True)],
                  [sg.Text('Esc closes   ↑↓ PgUp PgDn Home End scroll', font='Helvetica 8', text_color='gray')]]
        self.window = sg.Window(f'Core {core} processes', layout, keep_on_top=True, grab_anywhere=True, finalize=True, location=location, resizable=True, auto_save_location=True)
        self.window.bind('<Escape>', K_ESC)
        self.window.bind('<Home>', K_HOME)
        self.window.bind('<End>', K_END)
        self.window.bind('<Prior>', K_PGUP)
        self.window.bind('<Next>', K_PGDN)
        self.tree = self.window[K_TABLE].Widget                     # tkinter Treeview. Up/Down arrows are built in
        self.tree.focus_set()
        self.select_first()

    def select_first(self):
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0]); self.tree.focus(children[0])

    def refresh(self):
        rows, title = get_processes(self.core)
        yview = self.tree.yview()[0]                                # remember scroll position and selected PID
        selected = self.tree.selection()
        sel_pid = self.tree.item(selected[0])['values'][0] if selected else None
        self.window[K_TITLE].update(title)
        self.window[K_TABLE].update(values=rows)
        self.tree.yview_moveto(yview)                               # restore scroll position
        for iid in self.tree.get_children():                        # restore selection by PID (row may have moved)
            if self.tree.item(iid)['values'][0] == sel_pid:
                self.tree.selection_set(iid); self.tree.focus(iid)
                break

    def handle_event(self, event):
        """Returns True if the window should be closed"""
        if event in (sg.WIN_CLOSED, K_ESC):
            return True
        elif event == K_HOME:
            self.tree.yview_moveto(0)
        elif event == K_END:
            self.tree.yview_moveto(1)
        elif event == K_PGUP:
            self.tree.yview_scroll(-1, 'pages')
        elif event == K_PGDN:
            self.tree.yview_scroll(1, 'pages')
        return False

    def close(self):
        self.window.close()


def stop_tracer_if_unused(proc_windows):
    """Kernel tracing costs CPU, so only run it while a process window is open"""
    global tracer
    if tracer is not None and not proc_windows:
        tracer.stop()
        tracer = None


# ======================================================================================================================
#   Main
# ======================================================================================================================
def main():
    # A couple of "User defined elements" that combine several elements and enable bulk edits
    def Txt(text, **kwargs):
        return sg.Text(text, font=('Helvetica 8'), **kwargs)

    def GraphColumn(name, rc):
        return sg.Column([[Txt(name, size=(10, 1), key=KT_TXT(rc))],
                          [sg.Graph((GRAPH_WIDTH, GRAPH_HEIGHT), (0, 0), (GRAPH_WIDTH, 100), background_color='black', enable_events=True, key=KT_GRAPH(rc))]], pad=(2, 2))

    num_cores = len(psutil.cpu_percent(percpu=True))        # get the number of cores in the CPU

    sg.theme('Black')

    layout = [[sg.Push(), sg.Text('CPU Core Usage  (click a graph for processes)', justification='c', expand_x=True), sg.Push(), sg.Text(sg.SYMBOL_X, enable_events=True, text_color='gray28',background_color='black', font='_ 14', key='Exit')]]

    # add on the graphs
    for rows in range(num_cores // NUM_COLS + 1):
        layout += [[GraphColumn('CPU ' + str(rows * NUM_COLS + cols), (rows, cols)) for cols in range(min(num_cores - rows * NUM_COLS, NUM_COLS))]]

    # ----------------  Create Window  ----------------
    window = sg.Window(WINDOW_TITLE, layout, keep_on_top=True, grab_anywhere=True, no_titlebar=True, return_keyboard_events=True, alpha_channel=TRANSPARENCY, use_default_focus=False, finalize=True,
                       margins=(1, 1), element_padding=(0, 0), border_depth=0, auto_save_location=True, enable_close_attempted_event=True, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT)

    graphs = []
    for rows in range(num_cores // NUM_COLS + 1):
        for cols in range(min(num_cores - rows * NUM_COLS, NUM_COLS)):
            graphs += [DashGraph(window[KT_GRAPH((rows, cols))], window[KT_TXT((rows, cols))], 0, colors[(rows * NUM_COLS + cols) % len(colors)])]

    proc_windows = {}       # sg.Window -> ProcWindow, one per open core window

    # ----------------  main loop  ----------------
    while True:
        win, event, values = sg.read_all_windows(timeout=POLL_FREQUENCY)
        if win == window:                                           # ---- event from the main widget window ----
            if event in (sg.WIN_CLOSE_ATTEMPTED_EVENT, 'Exit', sg.WIN_CLOSED):     # location is auto-saved, nothing to do but leave
                break
            elif event == 'Edit Me':
                sg.execute_editor(__file__)
            elif event == 'Version':
                sg.popup_scrolled(__file__, sg.get_versions(), f'Per-core method: {MODE}', keep_on_top=True, location=window.current_location())
            elif isinstance(event, tuple) and event[0] == K_GRAPH:  # a graph was clicked
                row, col = event[1]
                pw = ProcWindow(row * NUM_COLS + col, window.current_location())
                proc_windows[pw.window] = pw
        elif win in proc_windows:                                   # ---- event from one of the process windows ----
            if proc_windows[win].handle_event(event):
                proc_windows.pop(win).close()
                stop_tracer_if_unused(proc_windows)

        if event == sg.TIMEOUT_EVENT:                               # ---- time to refresh everything ----
            stats = psutil.cpu_percent(percpu=True)                 # read CPU for each core
            for i, util in enumerate(stats):                        # update each graph
                graphs[i].graph_percentage_abs(util)
                graphs[i].text_display('{} CPU {:2.0f}'.format(i, util))
            for pw in proc_windows.values():
                pw.refresh()

    for pw in proc_windows.values():
        pw.close()
    stop_tracer_if_unused({})
    window.close()


def relaunch_as_admin():
    """Windows: if not already admin, re-run this script elevated (UAC prompt) and exit the un-elevated copy.
       If the user declines the UAC prompt, carry on un-elevated (per-core info falls back to top CPU consumers)"""
    if not IS_WINDOWS or IS_ADMIN:
        return
    exe = sys.executable
    pythonw = os.path.join(os.path.dirname(exe), 'pythonw.exe')
    if os.path.exists(pythonw):                                     # use the windowless interpreter so no console appears
        exe = pythonw
    rc = ct.windll.shell32.ShellExecuteW(None, 'runas', exe, f'"{__file__}"', None, 0)     # 'runas' = elevate.  0 = SW_HIDE, in case a console is still involved
    if rc > 32:                                                     # > 32 means the elevated copy launched
        sys.exit(0)


if __name__ == "__main__":
    relaunch_as_admin()
    main()