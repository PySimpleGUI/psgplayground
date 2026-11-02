#!/usr/bin/env python3
"""
Duet Partner  -  plays along with you through the piano's own MIDI input, reacting to what you play.

Five reactions, any combination can be on at once:
  Echo      repeats each note after a delay, transposed (a canon partner; repeats > 1 = decaying echoes)
  Harmony   adds a diatonic harmony note in the detected key to every note you play (3rd, 6th, octave, triad ...)
  Drone     holds the tonic + fifth of the detected key underneath you, switching when the key settles somewhere else
  Bass      plays the chord root in a low octave whenever the chord you are holding changes
  Arpeggio  arpeggiates whatever you are holding, an octave up, at a steady rate

Screen: roll + keyboard, teal = you, purple = the app.  Key estimate with lock.  Panic sends all-notes-off.
Loudness: the readout under the keyboard shows your last note on the 1-10 scale of the Piano Dynamics Monitor (plus pp .. ff);
bar brightness follows the same scale.  Vel@1 / Vel@10 calibrate it: raise Vel@1 so your softest touch reads 1, lower Vel@10 if your
piano never sends velocity 127.
Piano setup: the app sends on one channel (default 1 = the piano voice).  If your piano echoes received MIDI back out
(MIDI thru / soft thru) turn that off, or the app will react to its own notes (a 60 ms loop guard limits the damage).

The window opens at 90% of the screen and can be resized; the roll fills the space left beside the controls (a resize clears it).
Pixel sizes follow the screen DPI.  Full screen button / F11 covers the whole screen with no title bar (remembered between runs).

Touch:  big buttons everywhere, numeric settings use a "..." picker.
Keys:   Esc = exit   P = panic   Space = freeze roll   F11 = full screen on / off

Requires:  PySimpleGUI, mido, python-rtmidi          (Demo feeds fake input; output is shown on screen even without a MIDI out port)
Settings persist in duet_partner.json (PySimpleGUI user settings folder).

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.1  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import sys
import math
import time
import heapq
import random
import colorsys
import threading
import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'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'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_NAME = 'Duet Partner'
VERSION = '1.1'
SETTINGS_FILE = 'duet_partner.json'

# ----------------------------------------------------------------------------------------------------------------------
# Keys
# ----------------------------------------------------------------------------------------------------------------------
K_ROLL = '-ROLL-'
K_KEYS = '-KEYS-'
K_MIDI = '-MIDI-'                   # (msg, t) from the mido input callback / demo thread
K_OUT = '-OUT-'                     # (msg, t) posted by the sender thread when a message actually goes out
K_MODE = '-MODE-'
KT_MODE = lambda name: (K_MODE, name)
K_ECHO_DELAY = '-ECHO DELAY-'
K_ECHO_DELAY_PICK = '-ECHO DELAY PICK-'
K_ECHO_TRANS = '-ECHO TRANS-'
K_ECHO_TRANS_PICK = '-ECHO TRANS PICK-'
K_ECHO_REPEATS = '-ECHO REPEATS-'
K_ECHO_REPEATS_PICK = '-ECHO REPEATS PICK-'
K_HARM_INT = '-HARM INT-'
K_HARM_INT_PICK = '-HARM INT PICK-'
K_DRONE_OCT = '-DRONE OCT-'
K_DRONE_OCT_PICK = '-DRONE OCT PICK-'
K_BASS_OCT = '-BASS OCT-'
K_BASS_OCT_PICK = '-BASS OCT PICK-'
K_ARP_RATE = '-ARP RATE-'
K_ARP_RATE_PICK = '-ARP RATE PICK-'
K_ARP_OCT = '-ARP OCT-'
K_ARP_OCT_PICK = '-ARP OCT PICK-'
K_ARP_PATTERN = '-ARP PATTERN-'
K_ARP_PATTERN_PICK = '-ARP PATTERN PICK-'
K_KEY_NAME = '-KEY NAME-'
K_LOCK = '-LOCK-'
K_CHANNEL = '-CHANNEL-'
K_CHANNEL_PICK = '-CHANNEL PICK-'
K_VOICE = '-VOICE-'
K_VOICE_PICK = '-VOICE PICK-'
K_MIX = '-MIX-'
K_MIX_PICK = '-MIX PICK-'
K_VEL_MIN = '-VEL MIN-'
K_VEL_MIN_PICK = '-VEL MIN PICK-'
K_VEL_MAX = '-VEL MAX-'
K_VEL_MAX_PICK = '-VEL MAX PICK-'
K_LOUD = '-LOUD-'                   # readout: your last note's loudness 1-10
K_PORT_IN = '-PORT IN-'
K_PORT_IN_PICK = '-PORT IN PICK-'
K_PORT_OUT = '-PORT OUT-'
K_PORT_OUT_PICK = '-PORT OUT PICK-'
K_PANIC = '-PANIC-'
K_FREEZE = '-FREEZE-'
K_FULL = '-FULL-'
K_FULLSCREEN = '-FULLSCREEN-'       # settings-file entry only
K_DEMO = '-DEMO-'
K_EXIT = '-EXIT-'
K_STATUS = '-STATUS-'
K_TIMER = sg.EVENT_TIMER

# ----------------------------------------------------------------------------------------------------------------------
# Colors (same meaning in all the piano apps)
# ----------------------------------------------------------------------------------------------------------------------
C_BG = '#14161b'
C_PANEL = '#1e222b'
C_ROLL_BG = '#161a22'
C_TEXT = '#e6e8ee'
C_MUTED = '#8a91a3'
C_GRID = '#2c3140'
C_YOU = '#2dd4bf'                   # teal = you
C_APP = '#a78bfa'                   # purple = the app
C_WARN = '#ff8a4c'
C_BTN = '#2b3242'
C_WHITE_KEY = '#e8e8e8'
C_BLACK_KEY = '#202020'

FONT_BTN = ('Helvetica', 14)
FONT_VAL = ('Helvetica', 13, 'bold')
FONT_SMALL = ('Helvetica', 11)
FONT_TITLE = ('Helvetica', 18, 'bold')
FONT_KEY = ('Helvetica', 16, 'bold')
FONT_BIG = ('Helvetica', 36, 'bold')

MODE_SIZE = (10, 1)                 # one text line high: ~50 px on a 200% tablet, still a comfortable finger target
PICK_SIZE = (3, 1)
KB_H = 56                           # keyboard strip height in pixels at 96 dpi (multiplied by the screen scale)
WINDOW_FRACTION = 0.9               # initial window size as a fraction of the screen
ROLL_SPEED = 90                     # px per second
KEEP_SCREENS = 2
LOOP_GUARD = 0.06                   # ignore input note_on this soon after we sent the same pitch
BLACK_PCS = {1, 3, 6, 8, 10}
MODES = ['Echo', 'Harmony', 'Drone', 'Bass', 'Arpeggio']

NAMES = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'A♭', 'A', 'B♭', 'B']
MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]
HARMONIES = {'3rd above': [2], '3rd below': [-2], '6th above': [5], '6th below': [-5], 'octave above': [7], 'octave below': [-7],
             '3rd + 6th below': [-2, -5], 'triad above': [2, 4], 'octave + 3rd below': [-7, -2]}
CHROMATIC_FALLBACK = {2: 4, -2: -3, 4: 7, 5: 9, -5: -8, 7: 12, -7: -12}
ARP_PATTERNS = ['up', 'down', 'up-down', 'random']
CHORDS = [{0, 4, 7}, {0, 3, 7}, {0, 3, 6}, {0, 4, 8}, {0, 2, 7}, {0, 5, 7}, {0, 4, 7, 10}, {0, 4, 7, 11}, {0, 3, 7, 10}, {0, 3, 7, 11}, {0, 3, 6, 9}, {0, 3, 6, 10},
          {0, 4, 7, 9}, {0, 3, 7, 9}, {0, 5, 7, 10}, {0, 2, 4, 7}, {0, 4, 10}, {0, 4, 11}, {0, 3, 10}, {0, 7}, {0, 4}, {0, 3}]

sg.theme_add_new('PianoDark', {'BACKGROUND': C_BG, 'TEXT': C_TEXT, 'INPUT': C_PANEL, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_PANEL, 'BUTTON': (C_TEXT, C_BTN),
                               'PROGRESS': (C_YOU, C_PANEL), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
sg.theme('PianoDark')
sg.set_options(icon=ICON)


# ----------------------------------------------------------------------------------------------------------------------
# Music theory helpers
# ----------------------------------------------------------------------------------------------------------------------
def key_estimate(weights):
    """Krumhansl-Kessler correlation.  Returns ((tonic, is_minor), confidence 0..1) or (None, 0)"""
    if sum(weights) < 2.5:
        return None, 0.0
    mean_w = sum(weights) / 12
    dev_w = [w - mean_w for w in weights]
    var_w = math.sqrt(sum(d * d for d in dev_w)) or 1e-9
    scores = []
    for profile, minor in ((MAJOR_PROFILE, False), (MINOR_PROFILE, True)):
        mean_p = sum(profile) / 12
        dev_p = [p - mean_p for p in profile]
        var_p = math.sqrt(sum(d * d for d in dev_p))
        for tonic in range(12):
            r = sum(dev_w[(i + tonic) % 12] * dev_p[i] for i in range(12)) / (var_w * var_p)
            scores.append((r, (tonic, minor)))
    scores.sort(reverse=True)
    return scores[0][1], max(0.0, min(0.99, 0.5 + (scores[0][0] - scores[1][0]) * 2.5))


def key_name(key):
    return '—' if key is None else NAMES[key[0]] + (' minor' if key[1] else ' major')


def chord_root(pcs, bass_pc):
    """Root pitch class of the chord formed by a set of pitch classes (falls back to the lowest note)"""
    pcs = set(pcs)
    if len(pcs) < 2:
        return bass_pc
    best = None
    for root in range(12):
        rel = {(p - root) % 12 for p in pcs}
        for index, ivs in enumerate(CHORDS):
            if rel == ivs:
                score = (0, 0 if root == bass_pc else 1, index)
            else:
                hit = len(rel & ivs)
                if hit < 2:
                    continue
                score = (1, -(hit * 2 - len(rel - ivs) * 3 - len(ivs - rel)), 0 if root == bass_pc else 1, index)
            if best is None or score < best[0]:
                best = (score, root)
    return best[1] if best else bass_pc


def harmony_pitches(pitch, key, degree_offsets):
    """Diatonic harmony notes for pitch in key; chromatic notes are harmonised as their nearest lower scale degree"""
    result = []
    for off in degree_offsets:
        if key is None:
            result.append(pitch + CHROMATIC_FALLBACK.get(off, 0))
            continue
        steps = MINOR_STEPS if key[1] else MAJOR_STEPS
        rel = (pitch - key[0]) % 12
        i = max(n for n, s in enumerate(steps) if s <= rel)
        oct_shift, j = divmod(i + off, 7)
        result.append(pitch + steps[j] - steps[i] + 12 * oct_shift)
    return [p for p in result if 0 <= p <= 127]


def is_black(pitch):
    return pitch % 12 in BLACK_PCS


def build_key_geometry(lo, hi, width):
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


LEVEL_NAMES = ['pp', 'pp', 'p', 'p', 'mf', 'mf', 'f', 'f', 'ff', 'ff']      # index = round(loudness) - 1


def loudness(vel, vel_range):
    """Map a MIDI velocity onto 1..10 using the (Vel@1, Vel@10) floor and ceiling - the Piano Dynamics Monitor scale"""
    vel_min, vel_max = vel_range
    return round(max(1.0, min(10.0, 1 + 9 * (vel - vel_min) / max(1, vel_max - vel_min))), 2)


def vel_shade(base, value):
    """Lighten/darken a color with the 1-10 loudness so loud notes stand out (1 = dim, 10 = full)"""
    r, g, b = int(base[1:3], 16) / 255, int(base[3:5], 16) / 255, int(base[5:7], 16) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, s, 0.5 + 0.5 * (value - 1) / 9)
    return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))


class Msg:
    """Minimal stand-in for mido.Message used by the demo thread and when mido is missing"""
    def __init__(self, type, note=0, velocity=0, control=0, value=0, channel=0, program=0):
        self.type, self.note, self.velocity, self.control, self.value, self.channel, self.program = type, note, velocity, control, value, channel, program


def mk(type, **kw):
    return mido.Message(type, **kw) if mido else Msg(type, **kw)


def value_box(default, key, size, font, justification='center'):
    """Read-only Input used as a touch-friendly value display; persisted via setting="""
    return sg.Input(default, key=key, setting=default, readonly=True, size=(size, 1), font=font, justification=justification, disabled_readonly_text_color=C_TEXT,
                    disabled_readonly_background_color=C_PANEL)


# ----------------------------------------------------------------------------------------------------------------------
# Touch-friendly popups
# ----------------------------------------------------------------------------------------------------------------------
def popup_picker(title, value, lo, hi, step, big_step, unit=''):
    K_VAL, K_SL, K_OK, K_CANCEL, K_ADJ = '-PV-', '-PS-', '-POK-', '-PCANCEL-', '-PADJ-'
    KT_ADJ = lambda amt: (K_ADJ, amt)
    fmt = lambda v: '%g %s' % (v, unit)
    layout = [[sg.Text(title, font=FONT_TITLE, expand_x=True, justification='center')],
              [sg.Text(fmt(value), key=K_VAL, font=FONT_BIG, expand_x=True, justification='center', text_color=C_YOU)],
              [sg.Slider((lo, hi), value, resolution=step, orientation='h', size=(44, 40), key=K_SL, enable_events=True, disable_number_display=True, expand_x=True)],
              [sg.Button('-%g' % big_step, key=KT_ADJ(-big_step), size=(8, 2), font=FONT_BTN), sg.Button('-%g' % step, key=KT_ADJ(-step), size=(8, 2), font=FONT_BTN),
               sg.Button('+%g' % step, key=KT_ADJ(step), size=(8, 2), font=FONT_BTN), sg.Button('+%g' % big_step, key=KT_ADJ(big_step), size=(8, 2), font=FONT_BTN)],
              [sg.Button('Cancel', key=K_CANCEL, size=(16, 2), font=FONT_BTN), sg.Push(), sg.Button('OK', key=K_OK, size=(16, 2), font=FONT_BTN, button_color=(C_BG, C_YOU))]]
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
    K_OPT, K_CANCEL = '-OPT-', '-CANCEL-'
    KT_OPT = lambda name: (K_OPT, name)
    rows = [[sg.Button(opt, key=KT_OPT(opt), size=(34, 2), font=FONT_BTN, button_color=(C_BG, C_YOU) if opt == current else None)] for opt in options]
    if not options:
        rows = [[sg.Text('Nothing to choose from', font=FONT_BTN, text_color=C_MUTED)]]
    layout = [[sg.Text(title, font=FONT_TITLE)], *rows, [sg.Button('Cancel', key=K_CANCEL, size=(16, 2), font=FONT_BTN)]]
    win = sg.Window(title, layout, modal=True, keep_on_top=True, finalize=True, element_justification='center')
    win.bind('<Escape>', K_CANCEL)
    event, _ = win.read()
    win.close()
    return event[1] if isinstance(event, tuple) and event[0] == K_OPT else None


# ----------------------------------------------------------------------------------------------------------------------
# MIDI in / out
# ----------------------------------------------------------------------------------------------------------------------
def midi_port_names(output=False):
    try:
        return list(mido.get_output_names() if output else mido.get_input_names()) if mido else []
    except Exception:
        return []


class Sender:
    """Time-ordered MIDI output queue.  schedule(when, msg) from any thread; a worker sends when due and posts K_OUT to the window."""
    def __init__(self, window):
        self.window, self.port, self.queue, self.seq, self.running = window, None, [], 0, True
        self.cv = threading.Condition()
        self.active = {}                # (channel, pitch) -> count of note_ons we have sent that are still sounding
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def open(self, name):
        self.close()
        if name and mido:
            self.port = mido.open_output(name)

    def close(self):
        if self.port:
            self.port.close()
            self.port = None

    def schedule(self, when, msg):
        with self.cv:
            heapq.heappush(self.queue, (when, self.seq, msg))
            self.seq += 1
            self.cv.notify()

    def now(self, msg):
        self.schedule(0.0, msg)

    def cancel_all(self):
        with self.cv:
            self.queue.clear()

    def panic(self, channel):
        self.cancel_all()
        for (ch, pitch) in list(self.active):
            self.send(mk('note_off', note=pitch, velocity=0, channel=ch))
        self.active.clear()
        self.send(mk('control_change', control=123, value=0, channel=channel))

    def send(self, msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            self.active[(msg.channel, msg.note)] = self.active.get((msg.channel, msg.note), 0) + 1
        elif msg.type in ('note_off', 'note_on'):
            n = self.active.get((msg.channel, msg.note), 0) - 1
            if n > 0:
                self.active[(msg.channel, msg.note)] = n
            else:
                self.active.pop((msg.channel, msg.note), None)
        if self.port:
            try:
                self.port.send(msg)
            except Exception:
                pass
        self.window.write_event_value(K_OUT, (msg, time.perf_counter()))

    def run(self):
        while self.running:
            with self.cv:
                while self.running and not self.queue:
                    self.cv.wait()
                if not self.running:
                    return
                when, _, msg = self.queue[0]
                wait = when - time.perf_counter()
                if wait > 0:
                    self.cv.wait(min(wait, 0.05))
                    continue
                heapq.heappop(self.queue)
            self.send(msg)

    def stop(self):
        with self.cv:
            self.running = False
            self.cv.notify()
        self.thread.join(timeout=1)


def demo_thread(window, stop_event):
    """A simple tune in C with chords in the left hand, so the reactions can be seen and heard without playing"""
    send = lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter()))
    tune = [(72, 0.4), (74, 0.4), (76, 0.4), (77, 0.4), (79, 0.8), (76, 0.4), (72, 0.4), (74, 0.8), (71, 0.8), (72, 1.2)]
    chords = [[48, 52, 55], [53, 57, 60], [43, 47, 50], [48, 52, 55]]
    while not stop_event.is_set():
        for ci, chord in enumerate(chords):
            for n in chord:
                send(Msg('note_on', note=n, velocity=random.randint(45, 70)))
            for note, dur in tune[ci * 2: ci * 2 + 3] if ci < 3 else tune[6:]:
                send(Msg('note_on', note=note, velocity=random.randint(60, 105)))
                if stop_event.wait(dur * 0.85):
                    return
                send(Msg('note_off', note=note, velocity=0))
                if stop_event.wait(dur * 0.15):
                    return
            for n in chord:
                send(Msg('note_off', note=n, velocity=0))
            if stop_event.wait(0.1):
                return


class Bar:
    """One note bar on the roll"""
    def __init__(self, graph, x0, x1, color, t_on):
        self.graph, self.x0, self.x1, self.color, self.t_on, self.fig = graph, x0, x1, color, t_on, None

    def redraw(self, roll_time):
        if self.fig is not None:
            self.graph.delete_figure(self.fig)
        h = max(2, (roll_time - self.t_on) * ROLL_SPEED)
        self.fig = self.graph.draw_rectangle((self.x0, h), (self.x1, 0), fill_color=self.color, line_color=self.color)
        return h


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    auto_demo = '--demo' in sys.argv
    auto_close = float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None

    sw, sh = sg.Window.get_screen_size()
    roll_w = roll_h = kb_h = 100                                   # real sizes come from the finished window (apply_size)

    def value_row(label, key, default, pick_key, unit='', width=6):
        return [sg.Text(label, font=FONT_SMALL, text_color=C_MUTED), value_box(default, key, width, FONT_VAL), sg.Text(unit, font=FONT_SMALL, text_color=C_MUTED),
                sg.Button('…', key=pick_key, size=PICK_SIZE, font=FONT_BTN)]

    def mode_button(name):
        return sg.Button(name, key=KT_MODE(name), size=MODE_SIZE, font=FONT_BTN)

    modes_col = [[sg.Text(APP_NAME, font=FONT_TITLE)],
                 [sg.Text('Key', font=FONT_SMALL, text_color=C_MUTED), sg.Text('listening…', key=K_KEY_NAME, font=FONT_KEY, text_color=C_APP, size=(20, 1)),
                  sg.Button('Lock key', key=K_LOCK, size=(9, 1), font=FONT_SMALL)],
                 [sg.HorizontalSeparator(color=C_GRID)],
                 [mode_button('Echo'), *value_row('delay', K_ECHO_DELAY, '1', K_ECHO_DELAY_PICK, 's', 4), *value_row('transpose', K_ECHO_TRANS, '12', K_ECHO_TRANS_PICK, 'st', 4)],
                 [sg.Text('', size=(10, 1)), *value_row('repeats', K_ECHO_REPEATS, '1', K_ECHO_REPEATS_PICK, '', 4)],
                 [mode_button('Harmony'), *value_row('interval', K_HARM_INT, '3rd below', K_HARM_INT_PICK, '', 16)],
                 [mode_button('Drone'), *value_row('octave', K_DRONE_OCT, '2', K_DRONE_OCT_PICK, '', 4), sg.Text('tonic + fifth of the key', font=FONT_SMALL, text_color=C_MUTED)],
                 [mode_button('Bass'), *value_row('octave', K_BASS_OCT, '2', K_BASS_OCT_PICK, '', 4), sg.Text('chord root on each change', font=FONT_SMALL, text_color=C_MUTED)],
                 [mode_button('Arpeggio'), *value_row('rate', K_ARP_RATE, '6', K_ARP_RATE_PICK, '/s', 4), *value_row('octaves', K_ARP_OCT, '1', K_ARP_OCT_PICK, '', 4)],
                 [sg.Text('', size=(10, 1)), *value_row('pattern', K_ARP_PATTERN, 'up', K_ARP_PATTERN_PICK, '', 9)],
                 [sg.HorizontalSeparator(color=C_GRID)],
                 [*value_row('Channel', K_CHANNEL, '1', K_CHANNEL_PICK, '', 4), *value_row('Voice', K_VOICE, '0', K_VOICE_PICK, '', 4),
                  *value_row('Mix', K_MIX, '80', K_MIX_PICK, '%', 4)],
                 [*value_row('Vel@1', K_VEL_MIN, '1', K_VEL_MIN_PICK, '', 4), *value_row('Vel@10', K_VEL_MAX, '127', K_VEL_MAX_PICK, '', 4),
                  sg.Text('loudness 1-10 calibration', font=FONT_SMALL, text_color=C_MUTED)],
                 [sg.Text('MIDI in', font=FONT_SMALL, text_color=C_MUTED, size=(7, 1)), value_box('', K_PORT_IN, 20, FONT_SMALL, 'left'),
                  sg.Button('…', key=K_PORT_IN_PICK, size=PICK_SIZE, font=FONT_BTN)],
                 [sg.Text('MIDI out', font=FONT_SMALL, text_color=C_MUTED, size=(7, 1)), value_box('', K_PORT_OUT, 20, FONT_SMALL, 'left'),
                  sg.Button('…', key=K_PORT_OUT_PICK, size=PICK_SIZE, font=FONT_BTN)],
                 [sg.VPush()],
                 [sg.Button('Panic', key=K_PANIC, size=MODE_SIZE, font=FONT_BTN, button_color=(C_BG, C_WARN)), sg.Button('Freeze', key=K_FREEZE, size=MODE_SIZE, font=FONT_BTN),
                  sg.Button('Demo', key=K_DEMO, size=MODE_SIZE, font=FONT_BTN), sg.Button('Full', key=K_FULL, size=MODE_SIZE, font=FONT_BTN),
                  sg.Button('Exit', key=K_EXIT, size=MODE_SIZE, font=FONT_BTN)]]

    legend = [sg.Text('■ you', text_color=C_YOU, font=FONT_SMALL), sg.Text('■ Duet Partner', text_color=C_APP, font=FONT_SMALL),
              sg.Text('   brighter = louder   ', text_color=C_MUTED, font=FONT_SMALL), sg.Text('you: -', key=K_LOUD, font=FONT_VAL, text_color=C_YOU),
              sg.Push(), sg.Text('', key=K_STATUS, font=FONT_SMALL, text_color=C_MUTED)]
    roll_graph = sg.Graph((700, 400), (0, 0), (700, 400), background_color=C_ROLL_BG, key=K_ROLL, enable_events=True, pad=(0, 0), expand_x=True, expand_y=True)
    keys_graph = sg.Graph((700, KB_H), (0, 0), (700, KB_H), background_color=C_BG, key=K_KEYS, pad=(0, (4, 0)), expand_x=True)      # drawn only under the roll
    layout = [[roll_graph, sg.Column(modes_col, vertical_alignment='top', pad=((12, 0), 0))], [keys_graph], legend]
    window = sg.Window(APP_NAME, layout, finalize=True, enable_close_attempted_event=True, margins=(8, 8), resizable=True, enable_window_config_events=True)
    scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)       # 2.0 on a 200% Windows display: pixel sizes below are multiplied by it
    window[K_KEYS].set_size((None, int(KB_H * scale)))
    window.size = (int(sw * WINDOW_FRACTION), int(sh * WINDOW_FRACTION))
    window.move(int(sw * (1 - WINDOW_FRACTION) / 2), max(0, int(sh * (1 - WINDOW_FRACTION) / 2) - 20))
    window.refresh()
    window.bind('<Escape>', K_EXIT)
    window.bind('<F11>', K_FULL)
    window.bind('<p>', K_PANIC)
    window.bind('<space>', K_FREEZE)
    roll, keys, status = window[K_ROLL], window[K_KEYS], window[K_STATUS]

    # ---- state
    getf = lambda key, default: float(window[key].get() or default)
    echo_delay, echo_trans, echo_repeats = getf(K_ECHO_DELAY, 1), int(getf(K_ECHO_TRANS, 12)), int(getf(K_ECHO_REPEATS, 1))
    harm_int = window[K_HARM_INT].get() if window[K_HARM_INT].get() in HARMONIES else '3rd below'
    drone_oct, bass_oct = int(getf(K_DRONE_OCT, 2)), int(getf(K_BASS_OCT, 2))
    arp_rate, arp_oct = getf(K_ARP_RATE, 6), int(getf(K_ARP_OCT, 1))
    arp_pattern = window[K_ARP_PATTERN].get() if window[K_ARP_PATTERN].get() in ARP_PATTERNS else 'up'
    channel, voice, mix = int(getf(K_CHANNEL, 1)) - 1, int(getf(K_VOICE, 0)), getf(K_MIX, 80)
    vel_range = (int(getf(K_VEL_MIN, 1)), int(getf(K_VEL_MAX, 127)))
    modes = {m: m in sg.user_settings_get_entry('-MODES-', ['Harmony']) for m in MODES}
    if '--modes' in sys.argv:
        modes = {m: m in sys.argv[sys.argv.index('--modes') + 1].split(',') for m in MODES}
    geom, kw = {}, 0
    fullscreen = False
    held, sustained, pedal_down = set(), set(), False
    vel_of = {}                        # pitch -> velocity of the user's held note
    pc_weight, last_decay = [0.0] * 12, time.perf_counter()
    key, key_conf, lock = None, 0.0, False
    candidate_key, candidate_since = None, 0.0
    harmony_map = {}                   # user pitch -> [harmony pitches sounding]
    echo_offs = {}                     # user pitch -> [(pitch, delay)] pending note_offs to schedule on release
    drone_notes, bass_note, bass_root = [], None, None
    chord_dirty_at = None
    arp_next, arp_idx = 0.0, 0
    recent_out = {}                    # pitch -> time we last sent note_on (loop guard)
    frozen, roll_time, scroll_total, tick_last = False, 0.0, 0.0, time.perf_counter()
    active_bars, key_figs, old = {}, {}, []
    midi_in, demo_stop, demo_thr = None, None, None
    sender = Sender(window)
    t_start = time.perf_counter()

    # ---- drawing
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

    def apply_size():
        """Read the real size of the roll and keyboard graphs (after the window was sized, resized or went full screen) and rebuild
        the drawing coordinates and key geometry from it.  The roll is cleared because the bars are in pixel coordinates."""
        nonlocal roll_w, roll_h, kb_h, geom, kw
        w, h = roll.get_size()
        kw_, kh = keys.get_size()
        if not w or w < 40 or h < 40 or (w, h, kh) == (roll_w, roll_h, kb_h):
            return
        roll_w, roll_h, kb_h = w, h, kh
        for g, size in ((roll, (w, h)), (keys, (kw_, kh))):
            g.CanvasSize = size
            g.change_coordinates((0, 0), size)
        geom, kw = build_key_geometry(21, 108, w)                       # keyboard is drawn under the roll only (the strip is wider)
        roll.erase()
        keys.erase()
        old.clear()
        key_figs.clear()
        for bar in active_bars.values():
            bar.t_on, bar.fig = roll_time, None
        draw_keyboard()

    def set_fullscreen(state):
        """Full screen = the window covers the whole screen with no title bar (tk's -fullscreen attribute); remembered between runs"""
        nonlocal fullscreen
        fullscreen = state
        window.TKroot.attributes('-fullscreen', state)
        window[K_FULL].update('Windowed' if state else 'Full', button_color=(C_BG, C_YOU) if state else (C_TEXT, C_BTN))
        sg.user_settings_set_entry(K_FULLSCREEN, state)

    def key_mark(pitch, who, color):
        key_unmark(pitch, who)
        if pitch not in geom:
            return
        x0, x1, black = geom[pitch]
        if black:
            top, bottom = (kb_h * 0.82, kb_h * 0.62) if who == 'app' else (kb_h * 0.62, kb_h * 0.42)
        else:
            top, bottom = (kb_h * 0.38, kb_h * 0.2) if who == 'app' else (kb_h * 0.2, 1)
        key_figs[(pitch, who)] = keys.draw_rectangle((x0 + 1, top), (x1 - 1, bottom), fill_color=color, line_color=color)

    def key_unmark(pitch, who):
        fig = key_figs.pop((pitch, who), None)
        if fig is not None:
            keys.delete_figure(fig)

    def bar_start(pitch, who, color):
        bar_end(pitch, who)
        if pitch in geom:
            x0, x1, black = geom[pitch]
            bar = Bar(roll, x0 + 1, x1 - 1, color, roll_time)
            if who == 'app':
                bar.x0, bar.x1 = x0 + (x1 - x0) * 0.5, x1 - 1
            else:
                bar.x1 = x0 + (x1 - x0) * 0.5
            bar.redraw(roll_time)
            active_bars[(pitch, who)] = bar

    def bar_end(pitch, who):
        bar = active_bars.pop((pitch, who), None)
        if bar:
            h = bar.redraw(roll_time)
            old.append((bar.fig, scroll_total, h))

    def set_status(text):
        status.update(text)

    # ---- output helpers
    def vel_out(vel):
        return max(1, min(127, int(vel * mix / 100)))

    def note_on(pitch, vel, when=0.0):
        if 0 <= pitch <= 127:
            sender.schedule(when, mk('note_on', note=pitch, velocity=vel_out(vel), channel=channel))

    def note_off(pitch, when=0.0):
        if 0 <= pitch <= 127:
            sender.schedule(when, mk('note_off', note=pitch, velocity=0, channel=channel))

    def sounding():
        return held | sustained

    # ---- reactions
    def react_note_on(pitch, vel, t):
        if modes['Echo']:
            offs = []
            for r in range(1, echo_repeats + 1):
                p = pitch + echo_trans
                note_on(p, vel * (0.75 ** (r - 1)), t + echo_delay * r)
                offs.append((p, echo_delay * r))
            echo_offs[pitch] = offs
        if modes['Harmony']:
            hs = harmony_pitches(pitch, key, HARMONIES[harm_int])
            harmony_map[pitch] = hs
            for h in hs:
                note_on(h, vel)

    def react_note_off(pitch, t):
        for h in harmony_map.pop(pitch, []):
            note_off(h)
        for p, delay in echo_offs.pop(pitch, []):
            note_off(p, t + delay)

    def update_drone():
        nonlocal drone_notes
        want = [key[0] + 12 * (drone_oct + 1), key[0] + 12 * (drone_oct + 1) + 7] if (modes['Drone'] and key) else []
        if want != drone_notes:
            for p in drone_notes:
                note_off(p)
            for p in want:
                note_on(p, 60)
            drone_notes = want

    def update_bass():
        nonlocal bass_note, bass_root
        notes = sounding()
        if not modes['Bass'] or not notes:
            if bass_note is not None:
                note_off(bass_note)
                bass_note = bass_root = None
            return
        root = chord_root({p % 12 for p in notes}, min(notes) % 12)
        if root != bass_root:
            if bass_note is not None:
                note_off(bass_note)
            bass_root = root
            bass_note = root + 12 * (bass_oct + 1)
            vel = sum(vel_of.values()) / len(vel_of) if vel_of else 70
            note_on(bass_note, vel)

    def arp_step(now):
        nonlocal arp_next, arp_idx
        notes = sorted(sounding())
        if not modes['Arpeggio'] or not notes:
            arp_next = 0.0
            return
        if now < arp_next:
            return
        pool = [p + 12 * (o + 1) for o in range(arp_oct) for p in notes]
        pool = [p for p in pool if p <= 127]
        if arp_pattern == 'random':
            pitch = random.choice(pool)
        else:
            if arp_pattern == 'down':
                seq = pool[::-1]
            elif arp_pattern == 'up-down':
                seq = pool + pool[-2:0:-1] if len(pool) > 2 else pool
            else:
                seq = pool
            arp_idx %= len(seq)
            pitch = seq[arp_idx]
            arp_idx += 1
        note_on(pitch, sum(vel_of.values()) / len(vel_of) if vel_of else 70)
        note_off(pitch, now + 0.8 / arp_rate)
        arp_next = (arp_next if now - arp_next < 0.5 else now) + 1.0 / arp_rate

    def update_key(now):
        nonlocal key, key_conf, candidate_key, candidate_since
        if lock:
            return
        est, conf = key_estimate(pc_weight)
        if est != key and conf > 0.55:
            if est != candidate_key:
                candidate_key, candidate_since = est, now
            elif now - candidate_since > 0.8 or key is None:
                key, key_conf = est, conf
                window[K_KEY_NAME].update('%s  %d%%' % (key_name(key), round(conf * 100)))
                update_drone()
        elif est == key:
            key_conf = conf
            window[K_KEY_NAME].update('%s  %d%%' % (key_name(key), round(conf * 100)))

    def decay_weights():
        nonlocal last_decay
        now = time.perf_counter()
        f = 0.5 ** ((now - last_decay) / 6.0)
        for i in range(12):
            pc_weight[i] *= f
        last_decay = now

    # ---- event handlers
    def handle_in(msg, t):
        nonlocal pedal_down, chord_dirty_at
        kind = msg.type
        if kind == 'note_on' and msg.velocity == 0:
            kind = 'note_off'
        if kind == 'note_on':
            if t - recent_out.get(msg.note, -1) < LOOP_GUARD:
                return
            held.add(msg.note)
            sustained.discard(msg.note)
            vel_of[msg.note] = msg.velocity
            value = loudness(msg.velocity, vel_range)
            key_mark(msg.note, 'you', vel_shade(C_YOU, value))
            bar_start(msg.note, 'you', vel_shade(C_YOU, value))
            window[K_LOUD].update(f'you: {round(value)}  {LEVEL_NAMES[round(value) - 1]}   (vel {msg.velocity})')
            decay_weights()
            pc_weight[msg.note % 12] += 1.0 + msg.velocity / 127
            update_key(t)
            react_note_on(msg.note, msg.velocity, t)
            chord_dirty_at = t
        elif kind == 'note_off':
            if msg.note not in held:
                return
            held.discard(msg.note)
            key_unmark(msg.note, 'you')
            bar_end(msg.note, 'you')
            react_note_off(msg.note, t)
            if pedal_down:
                sustained.add(msg.note)
            else:
                vel_of.pop(msg.note, None)
                chord_dirty_at = t
        elif kind == 'control_change' and msg.control == 64:
            pedal_down = msg.value >= 64
            if not pedal_down:
                for p in sustained:
                    vel_of.pop(p, None)
                sustained.clear()
                chord_dirty_at = t

    def handle_out(msg, t):
        if msg.type == 'note_on' and msg.velocity > 0:
            recent_out[msg.note] = t
            key_mark(msg.note, 'app', vel_shade(C_APP, loudness(msg.velocity, vel_range)))
            bar_start(msg.note, 'app', vel_shade(C_APP, loudness(msg.velocity, vel_range)))
        elif msg.type in ('note_off', 'note_on'):
            if (msg.channel, msg.note) not in sender.active:
                key_unmark(msg.note, 'app')
                bar_end(msg.note, 'app')

    def tick():
        nonlocal roll_time, scroll_total, tick_last, chord_dirty_at
        now = time.perf_counter()
        dt, tick_last = now - tick_last, now
        if chord_dirty_at is not None and now - chord_dirty_at > 0.08:
            chord_dirty_at = None
            update_bass()
        arp_step(now)
        if frozen:
            return
        dy = dt * ROLL_SPEED
        roll_time += dt
        scroll_total += dy
        roll.move(0, dy)
        for bar in active_bars.values():
            bar.redraw(roll_time)
        limit = roll_h * KEEP_SCREENS
        while old and scroll_total - old[0][1] > limit + old[0][2]:
            roll.delete_figure(old.pop(0)[0])

    def set_mode(name, state):
        modes[name] = state
        window[KT_MODE(name)].update(button_color=(C_BG, C_APP) if state else (C_TEXT, C_BTN))
        if name == 'Drone':
            update_drone()
        elif name == 'Bass':
            update_bass()
        elif name == 'Harmony' and not state:
            for p in list(harmony_map):
                for h in harmony_map.pop(p):
                    note_off(h)

    def panic():
        sender.panic(channel)
        harmony_map.clear()
        echo_offs.clear()
        drone_notes.clear()
        for (pitch, who) in list(active_bars):
            if who == 'app':
                bar_end(pitch, who)
                key_unmark(pitch, who)
        set_status('All notes off')

    def open_in(name):
        nonlocal midi_in
        if midi_in:
            midi_in.close()
            midi_in = None
        if not name:
            return
        try:
            midi_in = mido.open_input(name, callback=lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter())))
        except Exception as e:
            set_status('Could not open input %s: %s' % (name, e))

    def open_out(name):
        try:
            sender.open(name)
            if voice:
                sender.now(mk('program_change', program=voice - 1, channel=channel))
        except Exception as e:
            set_status('Could not open output %s: %s' % (name, e))

    def update_status():
        set_status('in: %s   out: %s' % (window[K_PORT_IN].get() or 'none', window[K_PORT_OUT].get() or 'none (on-screen only)') + ('   Demo playing' if demo_stop else ''))

    def stop_demo():
        nonlocal demo_stop, demo_thr
        if demo_stop:
            demo_stop.set()
            demo_thr.join(timeout=2)
            demo_stop = demo_thr = None
            window[K_DEMO].update(button_color=(C_TEXT, C_BTN))
            update_status()

    def start_demo():
        nonlocal demo_stop, demo_thr
        demo_stop = threading.Event()
        demo_thr = threading.Thread(target=demo_thread, args=(window, demo_stop), daemon=True)
        demo_thr.start()
        window[K_DEMO].update(button_color=(C_BG, C_YOU))
        update_status()

    def pick_number(title, key, current, lo, hi, step, big, unit=''):
        new = popup_picker(title, current, lo, hi, step, big, unit)
        if new is not None:
            window[key].update('%g' % new)
        return new

    # ---- startup
    apply_size()
    if sg.user_settings_get_entry(K_FULLSCREEN, False):
        set_fullscreen(True)
    for m in MODES:
        set_mode(m, modes[m])
    ins, outs = midi_port_names(), midi_port_names(output=True)
    if window[K_PORT_IN].get() in ins:
        open_in(window[K_PORT_IN].get())
    elif len(ins) == 1:
        window[K_PORT_IN].update(ins[0])
        open_in(ins[0])
    if window[K_PORT_OUT].get() in outs:
        open_out(window[K_PORT_OUT].get())
    elif len(outs) == 1:
        window[K_PORT_OUT].update(outs[0])
        open_out(outs[0])
    update_status()
    if auto_demo:
        start_demo()
    window.timer_start(15)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_EXIT) or (auto_close and time.perf_counter() - t_start > auto_close):
            if values is not None:
                window.settings_save({k: v for k, v in values.items() if k in window.key_dict})
                sg.user_settings_set_entry('-MODES-', [m for m in MODES if modes[m]])
            break
        if event == K_TIMER:
            tick()
        elif event == sg.WINDOW_CONFIG_EVENT:                                              # window resized (or full screen toggled)
            apply_size()
        elif event == K_FULL:
            set_fullscreen(not fullscreen)
        elif event == K_MIDI:
            handle_in(*values[K_MIDI])
        elif event == K_OUT:
            handle_out(*values[K_OUT])
        elif isinstance(event, tuple) and event[0] == K_MODE:
            set_mode(event[1], not modes[event[1]])
        elif event == K_LOCK:
            lock = not lock
            window[K_LOCK].update('Locked' if lock else 'Lock key', button_color=(C_BG, C_APP) if lock else (C_TEXT, C_BTN))
        elif event in (K_FREEZE, K_ROLL):
            frozen = not frozen
            window[K_FREEZE].update('Resume' if frozen else 'Freeze', button_color=(C_BG, C_YOU) if frozen else (C_TEXT, C_BTN))
        elif event == K_PANIC:
            panic()
        elif event == K_ECHO_DELAY_PICK:
            new = pick_number('Echo delay', K_ECHO_DELAY, echo_delay, 0.1, 4, 0.1, 0.5, 's')
            echo_delay = new if new is not None else echo_delay
        elif event == K_ECHO_TRANS_PICK:
            new = pick_number('Echo transpose (semitones)', K_ECHO_TRANS, echo_trans, -24, 24, 1, 12, 'st')
            echo_trans = int(new) if new is not None else echo_trans
        elif event == K_ECHO_REPEATS_PICK:
            new = pick_number('Echo repeats', K_ECHO_REPEATS, echo_repeats, 1, 4, 1, 1)
            echo_repeats = int(new) if new is not None else echo_repeats
        elif event == K_HARM_INT_PICK:
            new = popup_choose('Harmony interval (diatonic in the key)', list(HARMONIES), harm_int)
            if new:
                harm_int = new
                window[K_HARM_INT].update(new)
        elif event == K_DRONE_OCT_PICK:
            new = pick_number('Drone octave', K_DRONE_OCT, drone_oct, 0, 4, 1, 1)
            if new is not None:
                drone_oct = int(new)
                update_drone()
        elif event == K_BASS_OCT_PICK:
            new = pick_number('Bass octave', K_BASS_OCT, bass_oct, 0, 4, 1, 1)
            if new is not None:
                bass_oct = int(new)
                bass_root = None
                update_bass()
        elif event == K_ARP_RATE_PICK:
            new = pick_number('Arpeggio rate (notes per second)', K_ARP_RATE, arp_rate, 1, 16, 0.5, 2, '/s')
            arp_rate = new if new is not None else arp_rate
        elif event == K_ARP_OCT_PICK:
            new = pick_number('Arpeggio octaves', K_ARP_OCT, arp_oct, 1, 3, 1, 1)
            arp_oct = int(new) if new is not None else arp_oct
        elif event == K_ARP_PATTERN_PICK:
            new = popup_choose('Arpeggio pattern', ARP_PATTERNS, arp_pattern)
            if new:
                arp_pattern = new
                window[K_ARP_PATTERN].update(new)
        elif event == K_CHANNEL_PICK:
            new = pick_number('MIDI channel', K_CHANNEL, channel + 1, 1, 16, 1, 4)
            if new is not None:
                panic()
                channel = int(new) - 1
        elif event == K_VOICE_PICK:
            new = pick_number('Program change (0 = none)', K_VOICE, voice, 0, 128, 1, 8)
            if new is not None:
                voice = int(new)
                if voice:
                    sender.now(mk('program_change', program=voice - 1, channel=channel))
        elif event == K_MIX_PICK:
            new = pick_number('Mix (velocity %)', K_MIX, mix, 10, 150, 5, 20, '%')
            mix = new if new is not None else mix
        elif event == K_VEL_MIN_PICK:                                                       # keep at least 9 velocity steps between 1 and 10
            new = pick_number('Velocity that counts as loudness 1', K_VEL_MIN, vel_range[0], 1, vel_range[1] - 9, 1, 10)
            vel_range = (int(new), vel_range[1]) if new is not None else vel_range
        elif event == K_VEL_MAX_PICK:
            new = pick_number('Velocity that counts as loudness 10', K_VEL_MAX, vel_range[1], vel_range[0] + 9, 127, 1, 10)
            vel_range = (vel_range[0], int(new)) if new is not None else vel_range
        elif event == K_PORT_IN_PICK:
            new = popup_choose('MIDI input port', midi_port_names(), values[K_PORT_IN])
            if new:
                window[K_PORT_IN].update(new)
                stop_demo()
                open_in(new)
                update_status()
        elif event == K_PORT_OUT_PICK:
            new = popup_choose('MIDI output port', midi_port_names(output=True), values[K_PORT_OUT])
            if new:
                window[K_PORT_OUT].update(new)
                panic()
                open_out(new)
                update_status()
        elif event == K_DEMO:
            stop_demo() if demo_stop else start_demo()

    stop_demo()
    sender.panic(channel)
    time.sleep(0.05)
    sender.stop()
    sender.close()
    if midi_in:
        midi_in.close()
    window.close()


if __name__ == '__main__':
    main()
