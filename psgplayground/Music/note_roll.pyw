#!/usr/bin/env python3
"""
Note Roll  -  real-time MIDI note roll for practicing legato, articulation and pedaling.

Notes rise from a keyboard strip as you play.  Bar height = how long the key was held; bar color and the number printed at the
foot of every bar are the note's LOUDNESS on the 1-10 scale used by the Piano Dynamics Monitor:
  loudness = 1 + 9 * (velocity - Vel@1) / (Vel@10 - Vel@1), clipped to 1..10      1-2 pp blue  3-4 p green  5-6 mf yellow  7-8 f orange  9-10 ff red
Vel@1 and Vel@10 are settings: raise Vel@1 so your softest touch reads 1 and lower Vel@10 if your piano never sends 127, then the
whole 1-10 range covers YOUR dynamic range.  The legend under the keyboard shows the bands and the velocity they correspond to.
The narrow lane on the right shows when the sustain pedal is down.
Gaps between bars = detached playing, overlapping bars = legato, a purple lane spanning a chord change = pedal smear.

The window opens at 90% of the screen and can be resized (the roll fills whatever space is left beside the controls; a resize
clears the roll).  Pixel sizes follow the screen DPI, so a 200% tablet gets the same proportions as a 100% monitor.

Touch:  tap the roll to freeze / resume.  All controls are big buttons, numeric settings use a "..." picker.
Keys:   Space = freeze/resume   Up/Down = scroll 1 line (when frozen)   PgUp/PgDn = 1 page   Home/End = oldest/newest
        F11 = full screen on / off (remembered)   Esc = exit

Requires:  PySimpleGUI, mido, python-rtmidi          (Demo button works without a piano or mido)
Settings persist in note_roll.json (PySimpleGUI user settings folder).

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.1  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import sys
import time
import random
import threading
import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAABgFBMVEUdGhf+xDwAAAD+00AsKSQiHhkkIBtJtP5oUyT/yzP/xDz18+7s6eVK1W0zMCkQDQ/+0mb0vTtMwf9HrfX/qlUsTGL/AAD/uzr5zGRO5XT//wBURCL/xTyVdiwtWDRkYV3MoTT/fwD/4WxIz2n/xzushi/GmjM2ao1ANR3/qjH/wjz/yD7/1yf/10D//1BBlcz/0j8rRSzMrFcbGyI7g7VJPib/mTP/qgD/vzv/wjz/zUD/0kH/4Tz//38uRVUzVWc0d0E7mFA4i8Q+o1U1q/1OS0dVWVthXlprwvyLbiqP0vrN4/Dn5N8fIiIoP00+lM08sP9ArltCslxKsmJkTyNtamZ+enWdmpaFx/Slop26uLOn1fPHxL/T0s4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB3tEfNAAAAgHRSTlP//gD+//////8FrP///////////wP/AQb//wH/df////8C//86/////weDwwZWBv////////8FAzhM/6wRAv//////////////////////////////////////////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACUy6/IAAAXESURBVHja7Zvnets2FIZBkABFDUODFWtRiiXHe0uu20wnTTOaNt173f9tFOAAhwCSkgnST6vvly2BOC8P1hFwAGDNAhsA+VfDkVWSRsPVAWyn3Bd17FUAhrYF4ezCapYk62IGoWUPCwKM2MvvnTc1TS9JmtY832NuGBUBoIWc8VONPlWmdO3p2PEqzwOwoXOuPSnZvIfwRDt3oJ0DMLLhs1MF1gOG02fQHmUBUL4TZeY9hBOYckICYAaPx0rtU4LxMTUjAfgMPkoXL2kQJPSIGhIC2Md78bJ6TztwGyXIPdB6iYr3jm0RwPA5TJjfxxgRUIIIwng/gQCfDwUANhzHykyOmHFUihjE0SRW+TjWETmAcxH1f32KAcDL5gHCif8xqxsUIWD1TaP6Ty6cNMAQOhFhgxkXejMtZh/kNBShRVh9uBFZcOAwCTCyrVP+rcseQcB48VFab3eS+oWS0opzxAp5oC43cWqFExIIV8toAnCJ79rLvtlPyvyqldRvrOpp3jCcAp8ARwT6OFzvQdAAfAToDYKBb39gpvX691Y7UutP4tnvZc89vZAAYNLgrwmDRvABnBkfAVPfYez9Rfqav3271XpDi06v8qe/q6nfG2hzTflImDkxgDPYDNEC+4YpUYzgDfUVLjYDY04QOrpJjXIAexbOgfrEtw+Mgdj+919yB/zB2gr3itjvBQC08kloaW9mc4BP4ePg495RDoAZdMR262+vq64McBQ8oD+mZgOA4eisGXy6H/TADIDXf3n2//E71ooAtB/uB+/aPPOCZQ8AWksFpX3ANP1G+NVHXa0PgDiyBZcBYgUP+xL7/Vdv6QBo8zYtMgrCnpVAjgAsPgYOgnJ0/UIygkuEGIBByzDxXpURhEyAV9SvHB3wcWClAXSXBF2QCh2ag2WZlwbeYgBbRqDridbLlDa59kt67kXE1eUADRABUEPGVloGs5sEMJZLpR8y4gCgUQDAd69waaUfG/EmkJVLPIKjJigGkC0fYM34aF0AFIsFvE6IKgYAD2KiAK05wRUCIPJyOyY2EXXWJFgLgNnvxMTm4k5nDlBFAAgk7Xc8D3Q6W+sQrAVAvhABbD8glQF8vgGoG0DUBx5WBwDAvLMMsP2DwnkgWmiCZWSeBmhv/4jTpfK0wmJkpIXmDyN1WEz4k7Gy8B0A4qv+UjygAEDg3Nj6no4HFDRB0XggtQ2hdDkWAbCtgWCfgBRdF8oEwOAm2gS4AbhqAPpzv7vb3fVE/3CLxQflASDgdrsfc3W7bqGHS/TADbXf5aJ/3hR5ujwA0tiN2acEuw1SMUA3CdCtHGDjgZo9APAiOQoWWF08kFxTfAC6nbaIe2CBgMJ4ILkw8+V4wWei7kJ5PCACMJY3AZTFA0tNgJJRQj3xQJU/z2M1+PsDRPylcgAEvnnBAJYPE6huK5kHvuuzDYq+UIe5c9HdAS5Nk3lAsot5SFQDsHMEOQAlyKnirgDeHnIGgPkJUQww2ADUDZDTB/qvFAN45whZHvhWdTzAzhEyAG6R8niAniN4AAORblEF8UB4YCE6GcBVxgNZRwP1xgPiHAYV+wOyk4WsOEE5gDCf4OeoXtUAwnyCK/09n54UA8jyCfRJSKC8CST5BPr7cIApBpCdJesHpCIAyWk6PZffAPw/+oA8n8AtfX9AUkaST+ACJfsDIgnzCdxrRfsDRubJQmrzAFfSBOJ8gv/U/oBSAJeoB8hKYuFpPAoBRGk8wkQmZQCCRCZRKpdCAEEqlyCZTRWAMJlNlM6nCECczidKaFQGIExoFKR0ZgJ8aLc/GOvZF6d0ipJaswDY8b2xnn1JUqsorTejnnc7O+/QWj1QltYrTGyWK0jqXvX9MxKbBandmVUVP6tO/GbMSO0umNy+vvKS24Xp/SUqP72//gsO9V/xqP2SS/3XfOq/6FT/Va/6L7vVf93vHlx4rP/KZ/2XXu/Btd/7cPF5c/e8Mv0LFz8F4LdapIAAAAAASUVORK5CYII='      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_NAME = 'Note Roll'
VERSION = '1.1'
SETTINGS_FILE = 'note_roll.json'

# ----------------------------------------------------------------------------------------------------------------------
# Keys
# ----------------------------------------------------------------------------------------------------------------------
K_ROLL = '-ROLL-'
K_LANE = '-LANE-'
K_KEYS = '-KEYS-'
K_MIDI = '-MIDI-'                   # written from the mido callback / demo thread: value = (msg, perf_counter time)
K_FREEZE = '-FREEZE-'
K_CLEAR = '-CLEAR-'
K_SPEED = '-SPEED-'
K_SPEED_PICK = '-SPEED PICK-'
K_VEL_MIN = '-VEL MIN-'              # velocity that counts as loudness 1
K_VEL_MIN_PICK = '-VEL MIN PICK-'
K_VEL_MAX = '-VEL MAX-'              # velocity that counts as loudness 10
K_VEL_MAX_PICK = '-VEL MAX PICK-'
K_LEGEND = '-LEGEND-'
KT_LEGEND = lambda name: (K_LEGEND, name)             # legend text of one loudness level
K_FULL = '-FULL-'
K_FULLSCREEN = '-FULLSCREEN-'       # settings-file entry only
K_RANGE = '-RANGE-'
K_RANGE_PICK = '-RANGE PICK-'
K_GRID = '-GRID-'
K_PORT = '-PORT-'
K_PORT_PICK = '-PORT PICK-'
K_DEMO = '-DEMO-'
K_EXIT = '-EXIT-'
K_STATUS = '-STATUS-'
K_TIMER = sg.EVENT_TIMER
K_KEY = '-KEY-'
KT_KEY = lambda name: (K_KEY, name)

# ----------------------------------------------------------------------------------------------------------------------
# Colors (same meaning in all three piano apps)
# ----------------------------------------------------------------------------------------------------------------------
C_BG = '#14161b'
C_PANEL = '#1e222b'
C_ROLL_BG = '#161a22'
C_LANE_BG = '#221f33'
C_TEXT = '#e6e8ee'
C_MUTED = '#8a91a3'
C_GRID = '#2c3140'
LEVELS = [(1, 2, '#448AFF', 'pp'), (3, 4, '#00E676', 'p'), (5, 6, '#FFEA00', 'mf'), (7, 8, '#FF9100', 'f'), (9, 10, '#FF1744', 'ff')]   # (low, high, color, name)
C_ON_LEVEL = '#000000'              # text printed on top of a level color
C_PEDAL = '#a78bfa'
C_ACCENT = '#2dd4bf'                # active / primary action
C_BTN = '#2b3242'
C_WHITE_KEY = '#e8e8e8'
C_BLACK_KEY = '#202020'

FONT_BTN = ('Helvetica', 14)
FONT_VAL = ('Helvetica', 14, 'bold')
FONT_SMALL = ('Helvetica', 11)
FONT_TITLE = ('Helvetica', 18, 'bold')
FONT_BIG = ('Helvetica', 36, 'bold')
FONT_BAR = ('Helvetica', 9, 'bold')                # loudness number printed on each bar

BTN_SIZE = (14, 1)                  # one text line high: ~50 px on a 200% tablet, still a comfortable finger target
PICK_SIZE = (3, 1)
LANE_W = 16                         # pedal lane width in pixels at 96 dpi (multiplied by the screen scale)
KB_H = 64                           # keyboard strip height in pixels at 96 dpi
WINDOW_FRACTION = 0.9               # initial window size as a fraction of the screen
KEEP_SCREENS = 3                    # how many screens of history are kept for scrolling back while frozen
LINE_STEP = 24                      # pixels moved by Up/Down when frozen

RANGES = {'88 keys': (21, 108), 'C1-C8': (24, 108), 'C2-C7': (36, 96), 'C3-C6': (48, 84)}
BLACK_PCS = {1, 3, 6, 8, 10}

sg.theme_add_new('PianoDark', {'BACKGROUND': C_BG, 'TEXT': C_TEXT, 'INPUT': C_PANEL, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_PANEL, 'BUTTON': (C_TEXT, C_BTN),
                               'PROGRESS': (C_ACCENT, C_PANEL), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
sg.theme('PianoDark')
sg.set_options(icon=ICON)


# ----------------------------------------------------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------------------------------------------------
def loudness(vel, vel_range):
    """Map a MIDI velocity onto 1..10 using the (Vel@1, Vel@10) floor and ceiling - the Piano Dynamics Monitor scale"""
    vel_min, vel_max = vel_range
    return round(max(1.0, min(10.0, 1 + 9 * (vel - vel_min) / max(1, vel_max - vel_min))), 2)


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, f):
    return tuple(a + (b - a) * f for a, b in zip(c1, c2))


STOPS = [((lo + hi) / 2, rgb(color)) for lo, hi, color, name in LEVELS]     # gradient anchors at the middle of each level


def level_color(value):
    """Smooth gradient color for a 1-10 loudness value: blue .. green .. yellow .. orange .. red"""
    if value <= STOPS[0][0]:
        c = STOPS[0][1]
    else:
        c = STOPS[-1][1]
        for (v0, c0), (v1, c1) in zip(STOPS, STOPS[1:]):
            if value <= v1:
                c = mix(c0, c1, (value - v0) / (v1 - v0))
                break
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(x)))) for x in c)


def is_black(pitch):
    return pitch % 12 in BLACK_PCS


def build_key_geometry(lo, hi, width):
    """Returns ({pitch: (x0, x1, is_black)}, white_key_width) for pitches lo..hi laid out across width pixels."""
    while is_black(lo):
        lo -= 1
    while is_black(hi):
        hi += 1
    n_white = sum(1 for p in range(lo, hi + 1) if not is_black(p))
    kw = width / n_white
    geom, wi = {}, 0
    for p in range(lo, hi + 1):
        if not is_black(p):
            geom[p] = (wi * kw, (wi + 1) * kw, False)
            wi += 1
        else:
            geom[p] = (wi * kw - kw * 0.3, wi * kw + kw * 0.3, True)
    return geom, kw


class Msg:
    """Minimal stand-in for mido.Message used by the demo thread"""
    def __init__(self, type, note=0, velocity=0, control=0, value=0):
        self.type, self.note, self.velocity, self.control, self.value = type, note, velocity, control, value


def value_box(default, key, size, font, justification='center'):
    """Read-only Input used as a touch-friendly value display; persisted via setting="""
    return sg.Input(default, key=key, setting=default, readonly=True, size=(size, 1), font=font, justification=justification, disabled_readonly_text_color=C_TEXT,
                    disabled_readonly_background_color=C_PANEL)


# ----------------------------------------------------------------------------------------------------------------------
# Touch-friendly popups
# ----------------------------------------------------------------------------------------------------------------------
def popup_picker(title, value, lo, hi, step, big_step, unit=''):
    """Big-button numeric picker.  Returns the new value or None if cancelled."""
    K_VAL, K_SL, K_OK, K_CANCEL, K_ADJ = '-PV-', '-PS-', '-POK-', '-PCANCEL-', '-PADJ-'
    KT_ADJ = lambda amt: (K_ADJ, amt)
    fmt = lambda v: '%g %s' % (v, unit)
    layout = [[sg.Text(title, font=FONT_TITLE, expand_x=True, justification='center')],
              [sg.Text(fmt(value), key=K_VAL, font=FONT_BIG, expand_x=True, justification='center', text_color=C_ACCENT)],
              [sg.Slider((lo, hi), value, resolution=step, orientation='h', size=(44, 40), key=K_SL, enable_events=True, disable_number_display=True, expand_x=True)],
              [sg.Button('-%g' % big_step, key=KT_ADJ(-big_step), size=(8, 2), font=FONT_BTN), sg.Button('-%g' % step, key=KT_ADJ(-step), size=(8, 2), font=FONT_BTN),
               sg.Button('+%g' % step, key=KT_ADJ(step), size=(8, 2), font=FONT_BTN), sg.Button('+%g' % big_step, key=KT_ADJ(big_step), size=(8, 2), font=FONT_BTN)],
              [sg.Button('Cancel', key=K_CANCEL, size=(16, 2), font=FONT_BTN), sg.Push(), sg.Button('OK', key=K_OK, size=(16, 2), font=FONT_BTN, button_color=(C_BG, C_ACCENT))]]
    win = sg.Window(title, layout, modal=True, keep_on_top=True, finalize=True, element_justification='center')
    win.bind('<Escape>', K_CANCEL)
    win.bind('<Return>', K_OK)
    result = None
    while True:
        event, values = win.read()
        if event in (sg.WIN_CLOSED, K_CANCEL):
            break
        if event == K_OK:
            result = value
            break
        if event == K_SL:
            value = values[K_SL]
        elif isinstance(event, tuple) and event[0] == K_ADJ:
            value = max(lo, min(hi, value + event[1]))
            win[K_SL].update(value)
        win[K_VAL].update(fmt(value))
    win.close()
    return result


def popup_choose(title, options, current=None):
    """Big stacked buttons.  Returns the chosen option or None."""
    K_OPT, K_CANCEL = '-OPT-', '-CANCEL-'
    KT_OPT = lambda name: (K_OPT, name)
    rows = [[sg.Button(opt, key=KT_OPT(opt), size=(34, 2), font=FONT_BTN, button_color=(C_BG, C_ACCENT) if opt == current else None)] for opt in options]
    if not options:
        rows = [[sg.Text('Nothing to choose from', font=FONT_BTN, text_color=C_MUTED)]]
    layout = [[sg.Text(title, font=FONT_TITLE)], *rows, [sg.Button('Cancel', key=K_CANCEL, size=(16, 2), font=FONT_BTN)]]
    win = sg.Window(title, layout, modal=True, keep_on_top=True, finalize=True, element_justification='center')
    win.bind('<Escape>', K_CANCEL)
    event, _ = win.read()
    win.close()
    return event[1] if isinstance(event, tuple) and event[0] == K_OPT else None


# ----------------------------------------------------------------------------------------------------------------------
# MIDI
# ----------------------------------------------------------------------------------------------------------------------
def midi_port_names():
    try:
        return list(mido.get_input_names()) if mido else []
    except Exception:
        return []


def midi_open(name, window):
    """Opens a mido input whose callback posts (msg, timestamp) into the window's event loop"""
    return mido.open_input(name, callback=lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter())))


def demo_thread(window, stop_event):
    """Plays a chord progression with arpeggios and pedal so the roll can be seen without a piano"""
    send = lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter()))
    chords = [[48, 55, 64, 67, 72], [45, 52, 60, 64, 69], [41, 48, 57, 60, 65], [43, 50, 59, 62, 67]]
    while not stop_event.is_set():
        for chord in chords:
            send(Msg('control_change', control=64, value=127))
            for i, note in enumerate(chord):
                vel = random.randint(30, 110) if i else random.randint(80, 120)
                send(Msg('note_on', note=note, velocity=vel))
                if stop_event.wait(random.uniform(0.15, 0.35)):
                    return
                if i > 0 and random.random() < 0.5:
                    send(Msg('note_off', note=chord[i - 1], velocity=0))
            if stop_event.wait(0.6):
                return
            for note in chord:
                send(Msg('note_off', note=note, velocity=0))
            send(Msg('control_change', control=64, value=0))
            if stop_event.wait(random.uniform(0.05, 0.4)):
                return
    for chord in chords:
        for note in chord:
            send(Msg('note_off', note=note, velocity=0))
    send(Msg('control_change', control=64, value=0))


# ----------------------------------------------------------------------------------------------------------------------
# Roll model
# ----------------------------------------------------------------------------------------------------------------------
class Bar:
    """One note bar (or pedal segment) on the roll; text = loudness number printed at the foot of the bar ('' for the pedal lane)"""
    def __init__(self, graph, x0, x1, color, t_on, text=''):
        self.graph, self.x0, self.x1, self.color, self.t_on, self.text, self.fig, self.label = graph, x0, x1, color, t_on, text, None, None

    def redraw(self, roll_time, speed):
        for fig in (self.fig, self.label):
            if fig is not None:
                self.graph.delete_figure(fig)
        h = max(2, (roll_time - self.t_on) * speed)
        self.fig = self.graph.draw_rectangle((self.x0, h), (self.x1, 0), fill_color=self.color, line_color=self.color)
        self.label = self.graph.draw_text(self.text, ((self.x0 + self.x1) / 2, 9), color=C_ON_LEVEL, font=FONT_BAR) if self.text and h >= 16 else None
        return h


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    auto_demo = '--demo' in sys.argv
    auto_close = float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None

    sw, sh = sg.Window.get_screen_size()
    roll_w = roll_h = kb_h = lane_w = 100                          # real sizes come from the finished window (apply_size)

    def value_row(label, key, default, pick_key):
        value = value_box(default, key, 9, FONT_VAL)
        return [sg.Text(label, font=FONT_SMALL, text_color=C_MUTED, size=(7, 1)), value, sg.Button('…', key=pick_key, size=PICK_SIZE, font=FONT_BTN)]

    controls = [[sg.Text(APP_NAME, font=FONT_TITLE)],
                [sg.Button('Freeze', key=K_FREEZE, size=BTN_SIZE, font=FONT_BTN)],
                [sg.Button('Clear', key=K_CLEAR, size=BTN_SIZE, font=FONT_BTN)],
                value_row('Speed', K_SPEED, '100', K_SPEED_PICK),
                value_row('Range', K_RANGE, '88 keys', K_RANGE_PICK),
                [sg.Checkbox('1-second grid', key=K_GRID, setting=True, font=FONT_SMALL, enable_events=True)],
                [sg.Text('Loudness 1-10 calibration', font=FONT_SMALL, text_color=C_MUTED)],
                value_row('Vel@1', K_VEL_MIN, '1', K_VEL_MIN_PICK),
                value_row('Vel@10', K_VEL_MAX, '127', K_VEL_MAX_PICK),
                [sg.Text('MIDI in', font=FONT_SMALL, text_color=C_MUTED)],
                [value_box('', K_PORT, 11, FONT_SMALL, 'left'),
                 sg.Button('…', key=K_PORT_PICK, size=PICK_SIZE, font=FONT_BTN)],
                [sg.Button('Demo', key=K_DEMO, size=BTN_SIZE, font=FONT_BTN)],
                [sg.Button('Full screen', key=K_FULL, size=BTN_SIZE, font=FONT_BTN)],
                [sg.Button('Exit', key=K_EXIT, size=BTN_SIZE, font=FONT_BTN)]]

    legend = [*[sg.Text('', key=KT_LEGEND(name), text_color=color, font=FONT_SMALL) for lo_l, hi_l, color, name in LEVELS],
              sg.Text('■ pedal down', text_color=C_PEDAL, font=FONT_SMALL),
              sg.Push(), sg.Text('', key=K_STATUS, font=FONT_SMALL, text_color=C_MUTED)]

    roll_graph = sg.Graph((700, 400), (0, 0), (700, 400), background_color=C_ROLL_BG, key=K_ROLL, enable_events=True, pad=(0, 0), expand_x=True, expand_y=True)
    lane_graph = sg.Graph((LANE_W, 400), (0, 0), (LANE_W, 400), background_color=C_LANE_BG, key=K_LANE, pad=((4, 0), 0))     # height follows the roll (apply_size)
    keys_graph = sg.Graph((700, KB_H), (0, 0), (700, KB_H), background_color=C_BG, key=K_KEYS, pad=(0, (4, 0)), expand_x=True)      # drawn only under the roll
    layout = [[roll_graph, lane_graph, sg.Column(controls, vertical_alignment='top', pad=((12, 0), 0))], [keys_graph], legend]
    window = sg.Window(APP_NAME, layout, finalize=True, enable_close_attempted_event=True, margins=(8, 8), resizable=True, enable_window_config_events=True)
    scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)       # 2.0 on a 200% Windows display: pixel sizes below are multiplied by it
    window[K_LANE].set_size((int(LANE_W * scale), None))
    window[K_KEYS].set_size((None, int(KB_H * scale)))
    window.size = (int(sw * WINDOW_FRACTION), int(sh * WINDOW_FRACTION))
    window.move(int(sw * (1 - WINDOW_FRACTION) / 2), max(0, int(sh * (1 - WINDOW_FRACTION) / 2) - 20))
    window.refresh()
    for name, seq in (('up', '<Up>'), ('down', '<Down>'), ('pgup', '<Prior>'), ('pgdn', '<Next>'), ('home', '<Home>'), ('end', '<End>'), ('space', '<space>')):
        window.bind(seq, KT_KEY(name))
    window.bind('<Escape>', K_EXIT)
    window.bind('<F11>', K_FULL)
    roll, lane, keys, status = window[K_ROLL], window[K_LANE], window[K_KEYS], window[K_STATUS]

    # ---- state
    speed = float(window[K_SPEED].get() or 100)
    vel_range = (int(float(window[K_VEL_MIN].get() or 1)), int(float(window[K_VEL_MAX].get() or 127)))
    fullscreen = False
    lo, hi = RANGES.get(window[K_RANGE].get(), RANGES['88 keys'])
    geom, kw = {}, 0
    grid_on = window[K_GRID].get()
    frozen, view_offset = False, 0.0
    roll_time, scroll_total, last_grid_time = 0.0, 0.0, 0.0
    active, key_figs, pedal_bar = {}, {}, None
    old = []                         # finished figures: (graph, fig, scroll_total when finished, height)
    midi_in, demo_stop, demo_thr = None, None, None
    t_start = time.perf_counter()
    tick_last = t_start

    def draw_keyboard():
        keys.erase()
        for p, (x0, x1, black) in geom.items():
            if not black:
                keys.draw_rectangle((x0, kb_h), (x1, 0), fill_color=C_WHITE_KEY, line_color='#777777')
        for p, (x0, x1, black) in geom.items():
            if black:
                keys.draw_rectangle((x0, kb_h), (x1, kb_h * 0.42), fill_color=C_BLACK_KEY, line_color='#000000')
        if kw >= 14 * scale:
            for p, (x0, x1, black) in geom.items():
                if p % 12 == 0:
                    keys.draw_text('C%d' % (p // 12 - 1), ((x0 + x1) / 2, 9 * scale), color='#555555', font=('Helvetica', 9))

    def key_down(pitch, color):
        key_up(pitch)
        x0, x1, black = geom[pitch]
        key_figs[pitch] = keys.draw_rectangle((x0, kb_h), (x1, kb_h * 0.42), fill_color=color, line_color=color) if black else \
            keys.draw_rectangle((x0 + 1, kb_h * 0.38), (x1 - 1, 1), fill_color=color, line_color=color)

    def apply_size():
        """Read the real size of the roll / lane / keyboard graphs (after the window was sized or resized) and rebuild the drawing
        coordinates and key geometry from it.  Everything on the roll is cleared because the bars are in pixel coordinates."""
        nonlocal roll_w, roll_h, kb_h, lane_w, geom, kw
        w, h = roll.get_size()
        kw_, kh = keys.get_size()
        lw = lane.get_size()[0]
        if not w or w < 40 or h < 40 or (w, h, kh) == (roll_w, roll_h, kb_h):
            return
        roll_w, roll_h, kb_h, lane_w = w, h, kh, lw
        lane.set_size((None, h))                                             # the lane is not "expandable" (that would stop the roll growing sideways)
        for g, size in ((roll, (w, h)), (lane, (lw, h)), (keys, (kw_, kh))):
            g.CanvasSize = size
            g.change_coordinates((0, 0), size)
        geom, kw = build_key_geometry(lo, hi, w)                        # keyboard is drawn under the roll only (the strip is wider)
        for p in list(active):
            finish(active.pop(p))
        key_figs.clear()
        draw_keyboard()
        clear_roll()

    def key_up(pitch):
        fig = key_figs.pop(pitch, None)
        if fig is not None:
            keys.delete_figure(fig)

    def finish(bar):
        h = bar.redraw(roll_time, speed)
        old.append((bar.graph, bar.fig, scroll_total, h))
        if bar.label is not None:
            old.append((bar.graph, bar.label, scroll_total, h))

    def clear_roll():
        nonlocal old, last_grid_time
        roll.erase()
        lane.erase()
        old = []
        for bar in active.values():
            bar.t_on, bar.fig = roll_time, None
        if pedal_bar:
            pedal_bar.t_on, pedal_bar.fig = roll_time, None
        last_grid_time = roll_time

    def scroll_view(delta):
        """Shift the frozen view; positive delta reveals older material"""
        nonlocal view_offset
        new = max(0.0, min(roll_h * (KEEP_SCREENS - 1), view_offset + delta))
        roll.move(0, -(new - view_offset))
        lane.move(0, -(new - view_offset))
        view_offset = new

    def set_frozen(state):
        nonlocal frozen
        if state == frozen:
            return
        frozen = state
        if not frozen and view_offset:
            scroll_view(-view_offset)
        window[K_FREEZE].update('Resume' if frozen else 'Freeze', button_color=(C_BG, C_ACCENT) if frozen else (C_TEXT, C_BTN))

    def set_status(text):
        status.update(text)

    def update_legend():
        """Legend: every loudness band with the velocities it corresponds to at the current calibration"""
        vel_min, vel_max = vel_range
        vel_of = lambda value: round(vel_min + (value - 1) / 9 * (vel_max - vel_min))
        for lo_l, hi_l, color, name in LEVELS:
            v_lo, v_hi = (1 if lo_l == 1 else vel_of(lo_l - 0.5)), (127 if hi_l == 10 else vel_of(hi_l + 0.5) - 1)
            window[KT_LEGEND(name)].update(f'■ {name} {lo_l}-{hi_l} (vel {v_lo}-{v_hi})')

    def set_fullscreen(state):
        """Full screen = the window covers the whole screen with no title bar (tk's -fullscreen attribute); remembered between runs"""
        nonlocal fullscreen
        fullscreen = state
        window.TKroot.attributes('-fullscreen', state)
        window[K_FULL].update('Windowed' if state else 'Full screen', button_color=(C_BG, C_ACCENT) if state else (C_TEXT, C_BTN))
        sg.user_settings_set_entry(K_FULLSCREEN, state)

    def open_port(name):
        nonlocal midi_in
        if midi_in:
            midi_in.close()
            midi_in = None
        if not name:
            return
        try:
            midi_in = midi_open(name, window)
            set_status('MIDI: ' + name)
        except Exception as e:
            set_status('Could not open %s: %s' % (name, e))

    def stop_demo():
        nonlocal demo_stop, demo_thr
        if demo_stop:
            demo_stop.set()
            demo_thr.join(timeout=2)
            demo_stop = demo_thr = None
            window[K_DEMO].update(button_color=(C_TEXT, C_BTN))

    def start_demo():
        nonlocal demo_stop, demo_thr
        demo_stop = threading.Event()
        demo_thr = threading.Thread(target=demo_thread, args=(window, demo_stop), daemon=True)
        demo_thr.start()
        window[K_DEMO].update(button_color=(C_BG, C_ACCENT))
        set_status('Demo playing')

    def handle_midi(msg):
        nonlocal pedal_bar
        kind = msg.type
        if kind == 'note_on' and msg.velocity == 0:
            kind = 'note_off'
        if kind == 'note_on':
            if msg.note in active:
                finish(active.pop(msg.note))
            if msg.note in geom:
                value = loudness(msg.velocity, vel_range)
                color = level_color(value)
                key_down(msg.note, color)
                x0, x1, black = geom[msg.note]
                bar = Bar(roll, x0 + (1 if black else 2), x1 - (1 if black else 2), color, roll_time, str(round(value)) if kw >= 14 * scale else '')
                bar.redraw(roll_time, speed)
                active[msg.note] = bar
        elif kind == 'note_off':
            key_up(msg.note)
            if msg.note in active:
                finish(active.pop(msg.note))
        elif kind == 'control_change' and msg.control == 64:
            if msg.value >= 64 and pedal_bar is None:
                pedal_bar = Bar(lane, 1, lane_w - 1, C_PEDAL, roll_time)
                pedal_bar.redraw(roll_time, speed)
            elif msg.value < 64 and pedal_bar is not None:
                finish(pedal_bar)
                pedal_bar = None

    def tick():
        nonlocal roll_time, scroll_total, last_grid_time, tick_last
        now = time.perf_counter()
        dt, tick_last = now - tick_last, now
        if frozen:
            return
        dy = dt * speed
        roll_time += dt
        scroll_total += dy
        roll.move(0, dy)
        lane.move(0, dy)
        if grid_on and roll_time - last_grid_time >= 1.0:
            last_grid_time += 1.0 if roll_time - last_grid_time < 2.0 else roll_time - last_grid_time
            old.append((roll, roll.draw_line((0, 0), (roll_w, 0), color=C_GRID), scroll_total, 0))
        for bar in active.values():
            bar.redraw(roll_time, speed)
        if pedal_bar:
            pedal_bar.redraw(roll_time, speed)
        limit = roll_h * KEEP_SCREENS
        while old and scroll_total - old[0][2] > limit + old[0][3]:
            g, fig, _, _ = old.pop(0)
            g.delete_figure(fig)

    # ---- startup
    apply_size()
    update_legend()
    if sg.user_settings_get_entry(K_FULLSCREEN, False):
        set_fullscreen(True)
    ports = midi_port_names()
    saved_port = window[K_PORT].get()
    if saved_port in ports:
        open_port(saved_port)
    elif len(ports) == 1:
        window[K_PORT].update(ports[0])
        open_port(ports[0])
    else:
        set_status('No MIDI input open - tap the MIDI … button' if ports else 'No MIDI ports found (mido / python-rtmidi installed?) - try Demo')
    if auto_demo:
        start_demo()
    window.timer_start(30)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_EXIT) or (auto_close and time.perf_counter() - t_start > auto_close):
            if values is not None:
                window.settings_save({k: v for k, v in values.items() if k in window.key_dict})
            break
        if event == K_TIMER:
            tick()
        elif event == sg.WINDOW_CONFIG_EVENT:                                              # window resized (or full screen toggled)
            apply_size()
        elif event == K_MIDI:
            handle_midi(values[K_MIDI][0])
        elif event in (K_FREEZE, K_ROLL):
            set_frozen(not frozen)
        elif event == K_CLEAR:
            clear_roll()
        elif event == K_SPEED_PICK:
            new = popup_picker('Scroll speed', speed, 20, 400, 10, 50, 'px/s')
            if new is not None:
                speed = new
                window[K_SPEED].update('%g' % speed)
        elif event in (K_VEL_MIN_PICK, K_VEL_MAX_PICK):                                    # loudness calibration: keep at least 9 velocity steps between 1 and 10
            if event == K_VEL_MIN_PICK:
                new = popup_picker('Velocity that counts as loudness 1', vel_range[0], 1, vel_range[1] - 9, 1, 10)
                vel_range = (int(new), vel_range[1]) if new is not None else vel_range
                window[K_VEL_MIN].update('%d' % vel_range[0])
            else:
                new = popup_picker('Velocity that counts as loudness 10', vel_range[1], vel_range[0] + 9, 127, 1, 10)
                vel_range = (vel_range[0], int(new)) if new is not None else vel_range
                window[K_VEL_MAX].update('%d' % vel_range[1])
            update_legend()
        elif event == K_FULL:
            set_fullscreen(not fullscreen)
        elif event == K_RANGE_PICK:
            new = popup_choose('Keyboard range', list(RANGES), values[K_RANGE])
            if new:
                window[K_RANGE].update(new)
                lo, hi = RANGES[new]
                geom, kw = build_key_geometry(lo, hi, roll_w)
                for p in list(active):
                    finish(active.pop(p))
                key_figs.clear()
                draw_keyboard()
                clear_roll()
        elif event == K_GRID:
            grid_on = values[K_GRID]
        elif event == K_PORT_PICK:
            new = popup_choose('MIDI input port', midi_port_names(), values[K_PORT])
            if new:
                window[K_PORT].update(new)
                stop_demo()
                open_port(new)
        elif event == K_DEMO:
            stop_demo() if demo_stop else start_demo()
        elif isinstance(event, tuple) and event[0] == K_KEY:
            name = event[1]
            if name == 'space':
                set_frozen(not frozen)
            else:
                set_frozen(True)
                steps = {'up': LINE_STEP * scale, 'down': -LINE_STEP * scale, 'pgup': roll_h, 'pgdn': -roll_h, 'home': roll_h * KEEP_SCREENS, 'end': -roll_h * KEEP_SCREENS}
                scroll_view(steps[name])

    stop_demo()
    if midi_in:
        midi_in.close()
    window.close()


if __name__ == '__main__':
    main()
