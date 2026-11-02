#!/usr/bin/env python3
"""
Groove Lane  -  see your timing against a metronome, note by note.

A metronome clicks (visual beat counter everywhere).  Every note you play lands as a dot in the lane:
the dot sits on the nearest grid line when you are on time and is pushed left (early, blue) or right (late, coral) by the
number of milliseconds you missed by.  Dot height = pitch (bass at the bottom).  Stats for the last 16 notes and a per-beat
deviation chart show whether you rush, drag, or are uneven in runs.

Calibrate: tap Calibrate and play 8 notes with the click; the median offset becomes the latency correction (MIDI + audio delay).

CLICK SOUND (bottom row, remembered): "system beep" is the Windows Beep call (the original click, always works); beep, woodblock,
click, cowbell, hi-hat, tick, rim are synthesized here and played as tiny WAVs through the speaker (winsound.PlaySound; if that
fails on a machine the program falls back to a WAV file and then to Beep, and says so in the status line).  "MIDI drums" sends General MIDI percussion (hi / low wood block,
claves on channel 10) and "MIDI piano" sends three short high notes on channel 1, both through the MIDI OUT port - i.e. the click
comes out of the piano's own speakers, which also removes the speaker latency.  Volume scales both.  Test plays 1 trip let 2 trip let.

TRIPLETS (play-along mode, button or R key, remembered): the metronome clicks every triplet - a high click on the beat and two
lower clicks for "trip" and "let" - and the grid switches to 8th triplets.  A row of cue rings appears near the top of the lane,
one per click, labelled 1 trip let, 2 trip let ...; the ring that is sounding right now lights up.  Play along: every note you
play puts a small marker on that row next to its ring (left = early, right = late, teal = inside the tolerance) as well as the
usual dot at pitch height, so the distance from click to note is visible directly.  Turning the mode off restores the grid.

The window opens at 90% of the screen and can be resized; the lane fills the space between the control rows.
Full screen button / F11 covers the whole screen with no title bar (remembered between runs).

Touch:  big buttons everywhere, numeric settings use a "..." picker.
Keys:   Space = start/stop   T = tap tempo   C = calibrate   R = triplets mode   F11 = full screen on / off   Esc = exit

Requires:  PySimpleGUI, mido, python-rtmidi          (Demo button works without a piano or mido)
Settings persist in groove_lane.json (PySimpleGUI user settings folder).

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.1  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import io
import math
import os
import sys
import tempfile
import time
import random
import statistics
import threading
import wave
import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'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'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon
try:
    import winsound
except ImportError:
    winsound = None

APP_NAME = 'Groove Lane'
VERSION = '1.1'
SETTINGS_FILE = 'groove_lane.json'

# ----------------------------------------------------------------------------------------------------------------------
# Keys
# ----------------------------------------------------------------------------------------------------------------------
K_LANE = '-LANE-'
K_CHART = '-CHART-'
K_MIDI = '-MIDI-'                   # (msg, perf_counter time) from the mido callback / demo thread
K_BEAT = '-BEAT-'                   # (beat index, click index inside the beat, click time) from the metronome thread
K_TRIPLETS = '-TRIPLETS-'
K_TRIPLETS_ON = '-TRIPLETS ON-'     # settings-file entry only
K_TEMPO = '-TEMPO-'
K_TEMPO_PICK = '-TEMPO PICK-'
K_START = '-START-'
K_TAP = '-TAP-'
K_GRID = '-GRID-'
K_GRID_PICK = '-GRID PICK-'
K_BPB = '-BPB-'
K_BPB_PICK = '-BPB PICK-'
K_BEAT_NUM = '-BEAT NUM-'
K_MEAN = '-MEAN-'
K_SPREAD = '-SPREAD-'
K_EVEN = '-EVEN-'
K_TOL = '-TOL-'
K_TOL_PICK = '-TOL PICK-'
K_LATENCY = '-LATENCY-'
K_LATENCY_PICK = '-LATENCY PICK-'
K_CALIBRATE = '-CALIBRATE-'
K_PORT = '-PORT-'
K_PORT_PICK = '-PORT PICK-'
K_PORT_OUT = '-PORT OUT-'
K_PORT_OUT_PICK = '-PORT OUT PICK-'
K_SOUND = '-SOUND-'
K_SOUND_PICK = '-SOUND PICK-'
K_VOLUME = '-VOLUME-'
K_VOLUME_PICK = '-VOLUME PICK-'
K_TEST = '-TEST-'
K_DEMO = '-DEMO-'
K_FULL = '-FULL-'
K_FULLSCREEN = '-FULLSCREEN-'       # settings-file entry only
K_EXIT = '-EXIT-'
K_STATUS = '-STATUS-'

# ----------------------------------------------------------------------------------------------------------------------
# Colors (same meaning in all three piano apps)
# ----------------------------------------------------------------------------------------------------------------------
C_BG = '#14161b'
C_PANEL = '#1e222b'
C_LANE_BG = '#161a22'
C_CUR_BEAT = '#1c2230'
C_TEXT = '#e6e8ee'
C_MUTED = '#8a91a3'
C_GRID = '#2c3140'
C_GRID_SUB = '#232837'
C_TOL = '#213a37'
C_EARLY = '#4aa3ff'                 # blue
C_ON = '#2dd4bf'                    # teal (also the primary action color)
C_LATE = '#ff8a4c'                  # coral
C_KEY = '#a78bfa'
C_BTN = '#2b3242'

FONT_BTN = ('Helvetica', 14)
FONT_VAL = ('Helvetica', 14, 'bold')
FONT_SMALL = ('Helvetica', 11)
FONT_TITLE = ('Helvetica', 18, 'bold')
FONT_STAT = ('Helvetica', 22, 'bold')
FONT_BEAT = ('Helvetica', 40, 'bold')
FONT_BIG = ('Helvetica', 36, 'bold')

BTN_SIZE = (12, 1)                  # one text line high: ~50 px on a 200% tablet, still a comfortable finger target
PICK_SIZE = (3, 1)
WINDOW_FRACTION = 0.9               # initial window size as a fraction of the screen
VISIBLE_BEATS = 8
STAT_NOTES = 16
GRIDS = {'quarters': 1, '8ths': 2, '8th triplets': 3, '16ths': 4}

sg.theme_add_new('PianoDark', {'BACKGROUND': C_BG, 'TEXT': C_TEXT, 'INPUT': C_PANEL, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_PANEL, 'BUTTON': (C_TEXT, C_BTN),
                               'PROGRESS': (C_ON, C_PANEL), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
sg.theme('PianoDark')
sg.set_options(icon=ICON)


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
    K_VAL, K_SL, K_OK, K_CANCEL, K_ADJ = '-PV-', '-PS-', '-POK-', '-PCANCEL-', '-PADJ-'
    KT_ADJ = lambda amt: (K_ADJ, amt)
    fmt = lambda v: '%g %s' % (v, unit)
    layout = [[sg.Text(title, font=FONT_TITLE, expand_x=True, justification='center')],
              [sg.Text(fmt(value), key=K_VAL, font=FONT_BIG, expand_x=True, justification='center', text_color=C_ON)],
              [sg.Slider((lo, hi), value, resolution=step, orientation='h', size=(44, 40), key=K_SL, enable_events=True, disable_number_display=True, expand_x=True)],
              [sg.Button('-%g' % big_step, key=KT_ADJ(-big_step), size=(8, 2), font=FONT_BTN), sg.Button('-%g' % step, key=KT_ADJ(-step), size=(8, 2), font=FONT_BTN),
               sg.Button('+%g' % step, key=KT_ADJ(step), size=(8, 2), font=FONT_BTN), sg.Button('+%g' % big_step, key=KT_ADJ(big_step), size=(8, 2), font=FONT_BTN)],
              [sg.Button('Cancel', key=K_CANCEL, size=(16, 2), font=FONT_BTN), sg.Push(), sg.Button('OK', key=K_OK, size=(16, 2), font=FONT_BTN, button_color=(C_BG, C_ON))]]
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
    rows = [[sg.Button(opt, key=KT_OPT(opt), size=(34, 2), font=FONT_BTN, button_color=(C_BG, C_ON) if opt == current else None)] for opt in options]
    if not options:
        rows = [[sg.Text('Nothing to choose from', font=FONT_BTN, text_color=C_MUTED)]]
    layout = [[sg.Text(title, font=FONT_TITLE)], *rows, [sg.Button('Cancel', key=K_CANCEL, size=(16, 2), font=FONT_BTN)]]
    win = sg.Window(title, layout, modal=True, keep_on_top=True, finalize=True, element_justification='center')
    win.bind('<Escape>', K_CANCEL)
    event, _ = win.read()
    win.close()
    return event[1] if isinstance(event, tuple) and event[0] == K_OPT else None


# ----------------------------------------------------------------------------------------------------------------------
# MIDI, metronome, demo
# ----------------------------------------------------------------------------------------------------------------------
def midi_port_names(output=False):
    try:
        return list(mido.get_output_names() if output else mido.get_input_names()) if mido else []
    except Exception:
        return []


def midi_open(name, window):
    return mido.open_input(name, callback=lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter())))


# ---------- Click sounds ----------
SOUNDS = ['system beep', 'beep', 'woodblock', 'click', 'cowbell', 'hi-hat', 'tick', 'rim', 'MIDI drums', 'MIDI piano']
MIDI_CLICKS = {'MIDI drums': (9, {'bar': 76, 'beat': 77, 'sub': 75}),               # channel index, note per click kind (GM: hi / low wood block, claves)
               'MIDI piano': (0, {'bar': 96, 'beat': 91, 'sub': 88})}               # three short high notes through the piano voice
RATE = 22050
KIND_GAIN = {'bar': 1.0, 'beat': 0.8, 'sub': 0.5}


def synth(sound, kind):
    """One click as a list of samples in -1..1.  kind: 'bar' = first beat of the bar, 'beat' = other beats, 'sub' = subdivision click"""
    hi = {'bar': 1.0, 'beat': 0.8, 'sub': 0.62}[kind]                                  # pitch factor: bar highest
    env = lambda t, tau: math.exp(-t / tau)
    if sound == 'beep':
        f, dur = 1400 * hi, 0.03 if kind != 'sub' else 0.018
        return [math.sin(2 * math.pi * f * i / RATE) * min(1.0, (i / RATE) / 0.004, (dur - i / RATE) / 0.006) for i in range(int(RATE * dur))]
    if sound == 'woodblock':
        f, dur = 2100 * hi, 0.07
        tone = lambda i: (math.sin(2 * math.pi * f * i / RATE) + 0.4 * math.sin(2 * math.pi * f * 1.6 * i / RATE)) * env(i / RATE, 0.012) * 0.7
        return [tone(i) + random.gauss(0, 0.3) * env(i / RATE, 0.0015) for i in range(int(RATE * dur))]
    if sound == 'click':
        dur = 0.004 if kind == 'sub' else 0.007
        return [random.gauss(0, 0.7) * env(i / RATE, 0.0012) + 0.3 * math.sin(2 * math.pi * 3000 * hi * i / RATE) * env(i / RATE, 0.002) for i in range(int(RATE * dur))]
    if sound == 'cowbell':
        f, dur = 587 * hi, 0.13 if kind != 'sub' else 0.08
        sq = lambda x: 0.6 * (1 if math.sin(x) >= 0 else -1) + 0.4 * math.sin(x)
        return [(sq(2 * math.pi * f * i / RATE) + sq(2 * math.pi * f * 1.48 * i / RATE)) * 0.4 * env(i / RATE, 0.045) for i in range(int(RATE * dur))]
    if sound == 'hi-hat':
        dur, tau = 0.09, 0.028 if kind != 'sub' else 0.014
        noise = [random.gauss(0, 1) for _ in range(int(RATE * dur) + 1)]
        return [(noise[i + 1] - noise[i]) * 0.5 * env(i / RATE, tau) for i in range(int(RATE * dur))]
    if sound == 'tick':
        dur = 0.006 if kind != 'sub' else 0.004
        return [math.sin(2 * math.pi * 4200 * hi * i / RATE) * env(i / RATE, 0.002) for i in range(int(RATE * dur))]
    if sound == 'rim':
        dur = 0.06
        return [random.gauss(0, 0.6) * env(i / RATE, 0.003) + 0.8 * math.sin(2 * math.pi * 520 * hi * i / RATE) * env(i / RATE, 0.02) for i in range(int(RATE * dur))]
    return []


def to_wav(samples, gain):
    peak = max(1e-6, max(abs(x) for x in samples)) if samples else 1.0
    frames = b''.join(int(max(-1.0, min(1.0, x / peak * gain)) * 32767).to_bytes(2, 'little', signed=True) for x in samples)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(frames)
    return buf.getvalue()


class Clicker:
    """Plays the metronome click: the Windows Beep, a synthesized WAV through winsound (async, cached per sound / kind / volume) or a MIDI note.
    A playback problem is reported once through on_error(text) instead of failing silently."""
    def __init__(self):
        self.sound, self.volume, self.out, self.cache = 'woodblock', 80, None, {}
        self.on_error, self.reported, self.use_file = None, False, False

    def beep(self, kind):
        """The original click: winsound.Beep in its own thread so the metronome is never held up"""
        freq, ms = (1400, 25) if kind == 'bar' else (1000, 25) if kind == 'beat' else (720, 15)
        threading.Thread(target=lambda: winsound.Beep(freq, ms), daemon=True).start()

    def fail(self, text):
        if self.on_error and not self.reported:
            self.reported = True
            self.on_error(text)

    def play(self, kind):
        if self.sound in MIDI_CLICKS:
            channel, notes = MIDI_CLICKS[self.sound]
            if self.out and mido:
                vel = max(1, min(127, int(127 * KIND_GAIN[kind] * self.volume / 100)))
                try:
                    self.out.send(mido.Message('note_on', note=notes[kind], velocity=vel, channel=channel))
                    threading.Timer(0.06, self.out.send, [mido.Message('note_off', note=notes[kind], velocity=0, channel=channel)]).start()
                except Exception:
                    pass
            return
        if winsound is None:
            self.fail('no winsound on this system: clicks are silent (choose MIDI drums / MIDI piano with a MIDI out port)')
            return
        if self.sound == 'system beep':
            self.beep(kind)
            return
        key = (self.sound, kind, self.volume)
        if key not in self.cache:
            self.cache[key] = to_wav(synth(self.sound, kind), KIND_GAIN[kind] * self.volume / 100)
        if not self.use_file:
            try:
                winsound.PlaySound(self.cache[key], winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
                return
            except Exception as e:
                self.use_file = True                       # this machine did not like a WAV from memory: use a file from now on
                self.fail(f'PlaySound from memory failed ({e}); trying a WAV file')
        try:                                               # second try: the same click as a temporary file
            path = os.path.join(tempfile.gettempdir(), f'groove_click_{self.sound}_{kind}_{self.volume}.wav')
            if not os.path.exists(path):
                with open(path, 'wb') as f:
                    f.write(self.cache[key])
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception as e:
            self.fail(f'PlaySound failed ({e}): using the system beep - pick "system beep" as the click sound')
            self.beep(kind)

    def open_out(self, name):
        self.close_out()
        if name and mido:
            self.out = mido.open_output(name)

    def close_out(self):
        if self.out:
            try:
                self.out.close()
            except Exception:
                pass
        self.out = None

    def test(self):
        """1 trip let 2 trip let, in a thread"""
        def run():
            for kind in ('bar', 'sub', 'sub', 'beat', 'sub', 'sub'):
                self.play(kind)
                time.sleep(0.2)
        threading.Thread(target=run, daemon=True).start()


CLICKER = Clicker()


def click(kind):
    CLICKER.play(kind)


COUNTS = {1: ('{n}',), 2: ('{n}', '&'), 3: ('{n}', 'trip', 'let'), 4: ('{n}', 'e', '&', 'a')}     # counting syllables per grid


class Metronome:
    """Posts K_BEAT events on a drift-free schedule computed from t0; clicks with winsound when available.
    clicks = clicks per beat: 1 = beats only, 3 = every triplet (play-along mode)"""
    def __init__(self, window):
        self.window, self.running, self.thread, self.t0, self.period, self.beats_per_bar, self.clicks = window, False, None, 0.0, 0.625, 4, 1

    def start(self, bpm, beats_per_bar, clicks=1):
        self.stop()
        self.period, self.beats_per_bar, self.clicks = 60.0 / bpm, beats_per_bar, clicks
        self.t0 = time.perf_counter() + 0.5
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join(timeout=1)

    def run(self):
        i = 0
        while self.running:
            beat, sub = divmod(i, self.clicks)
            t_next = self.t0 + beat * self.period + sub * self.period / self.clicks
            while self.running and t_next - time.perf_counter() > 0:
                time.sleep(min(0.004, max(0.0, t_next - time.perf_counter())))
            if not self.running:
                return
            self.window.write_event_value(K_BEAT, (beat, sub, t_next))
            click('sub' if sub else 'bar' if beat % self.beats_per_bar == 0 else 'beat')
            i += 1


def demo_thread(window, stop_event, metro, get_subdiv):
    """Plays scale notes near the grid with a slightly late bias so the lane fills up without a piano"""
    send = lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter()))
    scale = [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72]
    idx, direction = 0, 1
    while not stop_event.is_set():
        if not metro.running:
            if stop_event.wait(0.1):
                return
            continue
        slot = metro.period / get_subdiv()
        k = int((time.perf_counter() - metro.t0) / slot) + 1
        t_play = metro.t0 + k * slot + random.gauss(0.008, 0.016)
        if stop_event.wait(max(0.0, t_play - time.perf_counter())):
            return
        note = scale[idx]
        send(Msg('note_on', note=note, velocity=random.randint(60, 110)))
        idx += direction
        if idx in (0, len(scale) - 1):
            direction = -direction
        if stop_event.wait(0.05):
            return
        send(Msg('note_off', note=note, velocity=0))


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    auto_demo = '--demo' in sys.argv
    auto_close = float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None

    sw, sh = sg.Window.get_screen_size()
    lane_w, lane_h = 100, 100                                       # real sizes come from the finished window (apply_size)
    chart_w, chart_h = 320, 96

    def value_row(label, key, default, pick_key, unit='', width=7):
        value = value_box(default, key, width, FONT_VAL)
        return [sg.Text(label, font=FONT_SMALL, text_color=C_MUTED), value, sg.Text(unit, font=FONT_SMALL, text_color=C_MUTED),
                sg.Button('…', key=pick_key, size=PICK_SIZE, font=FONT_BTN)]

    def stat_card(label, key):
        rows = [[sg.Text(label, font=FONT_SMALL, text_color=C_MUTED, background_color=C_PANEL)], [sg.Text('—', key=key, font=FONT_STAT, size=(12, 1), background_color=C_PANEL)]]
        return sg.Column(rows, background_color=C_PANEL, pad=((0, 12), 0))

    top = [sg.Text(APP_NAME, font=FONT_TITLE), sg.Text('   '), *value_row('Tempo', K_TEMPO, '96', K_TEMPO_PICK, 'bpm', 5),
           sg.Button('Start', key=K_START, size=BTN_SIZE, font=FONT_BTN, button_color=(C_BG, C_ON)), sg.Button('Tap tempo', key=K_TAP, size=BTN_SIZE, font=FONT_BTN),
           *value_row('Grid', K_GRID, '8ths', K_GRID_PICK, '', 11), *value_row('Beats/bar', K_BPB, '4', K_BPB_PICK, '', 3),
           sg.Button('Triplets', key=K_TRIPLETS, size=BTN_SIZE, font=FONT_BTN, tooltip='Play-along mode: a click on every triplet, cue rings in the lane (R)'),
           sg.Push(), sg.Text('Beat', font=FONT_SMALL, text_color=C_MUTED),
           sg.Text('–', key=K_BEAT_NUM, font=FONT_BEAT, size=(2, 1), justification='center')]

    chart_col = sg.Column([[sg.Text('Per-beat average', font=FONT_SMALL, text_color=C_MUTED, background_color=C_PANEL)],
                           [sg.Graph((chart_w, chart_h), (0, 0), (chart_w, chart_h), background_color=C_PANEL, key=K_CHART)]], background_color=C_PANEL, pad=(0, 0))
    legend_col = sg.Column([[sg.Text('● early', text_color=C_EARLY, font=FONT_SMALL), sg.Text('● on time', text_color=C_ON, font=FONT_SMALL),
                             sg.Text('● late', text_color=C_LATE, font=FONT_SMALL)],
                            [sg.Text('dot height = pitch · shaded = tolerance', text_color=C_MUTED, font=FONT_SMALL)],
                            [sg.Text('', key=K_STATUS, font=FONT_SMALL, text_color=C_MUTED)]])
    stats = [stat_card('Average (last %d notes)' % STAT_NOTES, K_MEAN), stat_card('Spread', K_SPREAD), stat_card('In tolerance', K_EVEN), chart_col, sg.Push(), legend_col]

    bottom = [*value_row('Tolerance ±', K_TOL, '10', K_TOL_PICK, 'ms', 4), *value_row('Latency', K_LATENCY, '0', K_LATENCY_PICK, 'ms', 4),
              sg.Button('Calibrate', key=K_CALIBRATE, size=BTN_SIZE, font=FONT_BTN), sg.Text('MIDI in', font=FONT_SMALL, text_color=C_MUTED),
              value_box('', K_PORT, 16, FONT_SMALL, 'left'),
              sg.Button('…', key=K_PORT_PICK, size=PICK_SIZE, font=FONT_BTN), sg.Push(),
              sg.Button('Demo', key=K_DEMO, size=BTN_SIZE, font=FONT_BTN), sg.Button('Full screen', key=K_FULL, size=BTN_SIZE, font=FONT_BTN),
              sg.Button('Exit', key=K_EXIT, size=BTN_SIZE, font=FONT_BTN)]
    sound_row = [*value_row('Click sound', K_SOUND, 'woodblock', K_SOUND_PICK, '', 11), *value_row('Volume', K_VOLUME, '80', K_VOLUME_PICK, '%', 4),
                 sg.Button('Test', key=K_TEST, size=(6, 1), font=FONT_BTN, tooltip='Play 1 trip let 2 trip let with the chosen sound'),
                 sg.Text('   MIDI out', font=FONT_SMALL, text_color=C_MUTED), value_box('', K_PORT_OUT, 16, FONT_SMALL, 'left'),
                 sg.Button('…', key=K_PORT_OUT_PICK, size=PICK_SIZE, font=FONT_BTN), sg.Text('(for the MIDI drums / MIDI piano clicks)', font=FONT_SMALL, text_color=C_MUTED)]

    lane_graph = sg.Graph((900, 300), (0, 0), (900, 300), background_color=C_LANE_BG, key=K_LANE, pad=(0, 8), expand_x=True, expand_y=True)
    layout = [top, [lane_graph], stats, bottom, sound_row]
    window = sg.Window(APP_NAME, layout, finalize=True, enable_close_attempted_event=True, margins=(8, 8), resizable=True, enable_window_config_events=True)
    scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)       # 2.0 on a 200% Windows display: pixel sizes below are multiplied by it
    chart_w, chart_h = int(chart_w * scale), int(chart_h * scale)
    window[K_CHART].set_size((chart_w, chart_h))
    window[K_CHART].change_coordinates((0, 0), (chart_w, chart_h))
    window.size = (int(sw * WINDOW_FRACTION), int(sh * WINDOW_FRACTION))
    window.move(int(sw * (1 - WINDOW_FRACTION) / 2), max(0, int(sh * (1 - WINDOW_FRACTION) / 2) - 20))
    window.refresh()
    window.bind('<Escape>', K_EXIT)
    window.bind('<F11>', K_FULL)
    window.bind('<space>', K_START)
    window.bind('<t>', K_TAP)
    window.bind('<c>', K_CALIBRATE)
    window.bind('<r>', K_TRIPLETS)
    lane, chart, status = window[K_LANE], window[K_CHART], window[K_STATUS]

    # ---- state
    fullscreen = False
    triplets, grid_before, cur_sub = False, None, 0
    bpm = float(window[K_TEMPO].get() or 96)
    subdiv = GRIDS.get(window[K_GRID].get(), 2)
    beats_per_bar = int(window[K_BPB].get() or 4)
    tol = float(window[K_TOL].get() or 10)
    latency = float(window[K_LATENCY].get() or 0)
    metro = Metronome(window)
    CLICKER.sound = window[K_SOUND].get() if window[K_SOUND].get() in SOUNDS else 'woodblock'
    CLICKER.on_error = lambda text: window.write_event_value(K_STATUS, text)
    CLICKER.volume = int(float(window[K_VOLUME].get() or 80))
    notes = []                       # dicts: beat, slot, dev (ms, latency-corrected), raw (ms, uncorrected), pitch
    cur_beat = -1
    taps = []
    calibrating = []
    calibrate_mode = False
    midi_in, demo_stop, demo_thr = None, None, None
    t_start = time.perf_counter()

    def dev_color(dev):
        return C_ON if abs(dev) <= tol else C_EARLY if dev < 0 else C_LATE

    def apply_size():
        """Read the real size of the lane graph (after the window was sized, resized or went full screen) and redraw"""
        nonlocal lane_w, lane_h
        w, h = lane.get_size()
        if not w or w < 40 or h < 40 or (w, h) == (lane_w, lane_h):
            return
        lane_w, lane_h = w, h
        lane.CanvasSize = (w, h)
        lane.change_coordinates((0, 0), (w, h))
        draw_lane()

    def set_fullscreen(state):
        """Full screen = the window covers the whole screen with no title bar (tk's -fullscreen attribute); remembered between runs"""
        nonlocal fullscreen
        fullscreen = state
        window.TKroot.attributes('-fullscreen', state)
        window[K_FULL].update('Windowed' if state else 'Full screen', button_color=(C_BG, C_ON) if state else (C_TEXT, C_BTN))
        sg.user_settings_set_entry(K_FULLSCREEN, state)

    def draw_lane():
        lane.erase()
        if cur_beat < 0:
            lane.draw_text('press Start, then play along with the click', (lane_w / 2, lane_h / 2), color=C_MUTED, font=FONT_BTN)
            return
        first = cur_beat + 1 - (VISIBLE_BEATS - 1)
        cw = lane_w / VISIBLE_BEATS
        slot_w = cw / subdiv
        range_ms = min(100.0, metro.period / subdiv * 500)
        ms_scale = (slot_w / 2) / range_ms
        y_cue = lane_h - 40 * scale                                                        # play-along mode: a row of cue rings, one per click
        top_y = y_cue - 40 * scale if triplets else lane_h - 18 * scale                    # slot lines and tolerance bands stop below the cue row
        for c in range(VISIBLE_BEATS):
            b = first + c
            if b < 0:
                continue
            x_col = c * cw
            if b == cur_beat:
                lane.draw_rectangle((x_col, lane_h), (x_col + cw, 0), fill_color=C_CUR_BEAT, line_width=0)
            if b % beats_per_bar == 0:
                lane.draw_line((x_col, 0), (x_col, lane_h), color=C_GRID, width=1)
            for s in range(subdiv):
                xs = x_col + (s + 0.5) * slot_w
                lane.draw_rectangle((xs - tol * ms_scale, top_y), (xs + tol * ms_scale, 18 * scale), fill_color=C_TOL, line_width=0)
                lane.draw_line((xs, 18 * scale), (xs, top_y), color=C_TEXT if s == 0 else C_GRID_SUB, width=2 if s == 0 else 1)
            lane.draw_text(str(b % beats_per_bar + 1), (x_col + 0.5 * slot_w, 9 * scale), color=C_ON if b % beats_per_bar == 0 else C_MUTED, font=FONT_SMALL)
        if triplets:
            syllables = COUNTS.get(subdiv, COUNTS[1])
            for c in range(VISIBLE_BEATS):
                b = first + c
                if b < 0:
                    continue
                for s_ in range(subdiv):
                    xs = c * cw + (s_ + 0.5) * slot_w
                    now_ring = (b, s_) == (cur_beat, cur_sub)
                    lane.draw_circle((xs, y_cue), 12 * scale, fill_color=C_ON if now_ring else None, line_color=C_ON if now_ring else C_MUTED, line_width=2)
                    label = syllables[s_ % len(syllables)].format(n=b % beats_per_bar + 1)
                    lane.draw_text(label, (xs, y_cue - 26 * scale), color=C_ON if s_ == 0 else C_MUTED, font=FONT_SMALL)
        for n in notes:
            c = n['beat'] - first
            if 0 <= c < VISIBLE_BEATS:
                xs = c * cw + (n['slot'] + 0.5) * slot_w
                x = xs + max(-range_ms, min(range_ms, n['dev'])) * ms_scale
                y = 24 * scale + (n['pitch'] - 21) / 87 * (top_y - 30 * scale)
                color = dev_color(n['dev'])
                lane.draw_circle((x, y), 8 * scale, fill_color=color, line_color=color)
                if triplets:                                                               # marker beside the cue ring + thread down to the note
                    lane.draw_line((x, y_cue - 12 * scale), (x, y + 8 * scale), color=C_GRID_SUB, width=1)
                    lane.draw_circle((x, y_cue), 6 * scale, fill_color=color, line_color=color)

    def draw_chart():
        chart.erase()
        mid = chart_h / 2
        chart.draw_line((0, mid), (chart_w, mid), color=C_GRID)
        if cur_beat < 0:
            return
        first = cur_beat + 1 - (VISIBLE_BEATS - 1)
        cw = chart_w / VISIBLE_BEATS
        for c in range(VISIBLE_BEATS):
            devs = [n['dev'] for n in notes if n['beat'] == first + c]
            if not devs:
                continue
            mean = statistics.fmean(devs)
            h = max(-mid + 2, min(mid - 2, mean / 60 * (mid - 2)))
            x0 = c * cw + 4
            chart.draw_rectangle((x0, mid + h if h > 0 else mid), (x0 + cw - 8, mid if h > 0 else mid + h), fill_color=dev_color(mean), line_width=0)

    def update_stats():
        recent = [n['dev'] for n in notes[-STAT_NOTES:]]
        if not recent:
            window[K_MEAN].update('—', text_color=C_TEXT)
            window[K_SPREAD].update('—')
            window[K_EVEN].update('—', text_color=C_TEXT)
            return
        mean = statistics.fmean(recent)
        spread = statistics.pstdev(recent) if len(recent) > 1 else 0.0
        even = 100.0 * sum(1 for d in recent if abs(d) <= tol) / len(recent)
        window[K_MEAN].update(('%+d ms ' % round(mean)) + ('late' if mean > tol else 'early' if mean < -tol else 'on time'), text_color=dev_color(mean))
        window[K_SPREAD].update('± %d ms' % round(spread))
        window[K_EVEN].update('%d%%' % round(even), text_color=C_ON if even >= 75 else C_LATE)

    def redraw_all():
        draw_lane()
        draw_chart()
        update_stats()

    def set_status(text):
        status.update(text)

    def set_triplets(state):
        """Play-along mode: grid = 8th triplets, a click on every triplet, cue rings in the lane.  Off = clicks on beats, grid restored."""
        nonlocal triplets, grid_before, subdiv, notes
        triplets = state
        if state:
            grid_before = window[K_GRID].get()
            window[K_GRID].update('8th triplets')
        elif grid_before in GRIDS:
            window[K_GRID].update(grid_before)
        subdiv = GRIDS.get(window[K_GRID].get(), 3 if state else 2)
        window[K_TRIPLETS].update('Triplets: on' if state else 'Triplets', button_color=(C_BG, C_KEY) if state else (C_TEXT, C_BTN))
        sg.user_settings_set_entry(K_TRIPLETS_ON, state)
        notes = []
        if metro.running:
            set_running(True)
        else:
            redraw_all()

    def set_running(state):
        nonlocal cur_beat, cur_sub, notes
        if state:
            notes = []
            cur_beat, cur_sub = -1, 0
            metro.start(bpm, beats_per_bar, subdiv if triplets else 1)
            set_status('Running at %g bpm' % bpm)
        else:
            metro.stop()
            window[K_BEAT_NUM].update('–', text_color=C_TEXT)
        window[K_START].update('Stop' if state else 'Start', button_color=(C_BG, C_LATE) if state else (C_BG, C_ON))
        redraw_all()

    def set_tempo(new_bpm):
        nonlocal bpm
        bpm = max(30.0, min(240.0, float(new_bpm)))
        window[K_TEMPO].update('%g' % bpm)
        if metro.running:
            set_running(True)

    def open_out(name):
        try:
            CLICKER.open_out(name)
        except Exception as e:
            set_status('Could not open MIDI out %s: %s' % (name, e))

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
        if not metro.running:
            set_running(True)
        demo_stop = threading.Event()
        demo_thr = threading.Thread(target=demo_thread, args=(window, demo_stop, metro, lambda: subdiv), daemon=True)
        demo_thr.start()
        window[K_DEMO].update(button_color=(C_BG, C_ON))
        set_status('Demo playing')

    def handle_note(msg, t):
        nonlocal calibrate_mode, latency
        if msg.type != 'note_on' or msg.velocity == 0 or not metro.running:
            return
        if calibrate_mode:
            slot = metro.period
            k = round((t - metro.t0) / slot)
            calibrating.append(((t - metro.t0) - k * slot) * 1000)
            set_status('Calibrating: %d of 8 notes' % len(calibrating))
            if len(calibrating) >= 8:
                latency = float(round(statistics.median(calibrating)))
                window[K_LATENCY].update('%g' % latency)
                calibrate_mode = False
                window[K_CALIBRATE].update(button_color=(C_TEXT, C_BTN))
                set_status('Latency set to %g ms' % latency)
            return
        slot = metro.period / subdiv
        t_rel = t - metro.t0 - latency / 1000
        k = round(t_rel / slot)
        if k < 0:
            return
        notes.append({'beat': k // subdiv, 'slot': k % subdiv, 'dev': (t_rel - k * slot) * 1000, 'pitch': msg.note})
        del notes[:-400]
        redraw_all()

    # ---- startup
    apply_size()
    if sg.user_settings_get_entry(K_TRIPLETS_ON, False):
        set_triplets(True)
    redraw_all()
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
    if window[K_PORT_OUT].get() in midi_port_names(output=True):
        open_out(window[K_PORT_OUT].get())
    if auto_demo:
        start_demo()
    if auto_close:
        window.timer_start(500)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_EXIT) or (auto_close and time.perf_counter() - t_start > auto_close):
            if values is not None:
                window.settings_save({k: v for k, v in values.items() if k in window.key_dict})
            break
        if event == sg.WINDOW_CONFIG_EVENT:                                                # window resized (or full screen toggled)
            apply_size()
        elif event == K_STATUS:                                                            # a click-sound problem reported by the clicker
            set_status(values[K_STATUS])
        elif event == K_FULL:
            set_fullscreen(not fullscreen)
        elif event == K_MIDI:
            handle_note(*values[K_MIDI])
        elif event == K_BEAT:
            cur_beat, cur_sub, _ = values[K_BEAT]
            if cur_sub == 0:
                window[K_BEAT_NUM].update(str(cur_beat % beats_per_bar + 1), text_color=C_ON if cur_beat % beats_per_bar == 0 else C_TEXT)
                draw_chart()
            draw_lane()
        elif event == K_TRIPLETS:
            set_triplets(not triplets)
        elif event == K_START:
            set_running(not metro.running)
        elif event == K_TAP:
            now = time.perf_counter()
            if taps and now - taps[-1] > 2.5:
                taps.clear()
            taps.append(now)
            del taps[:-6]
            if len(taps) >= 2:
                set_tempo(round(60.0 / statistics.fmean(b - a for a, b in zip(taps, taps[1:]))))
            set_status('Tap %d' % len(taps) if len(taps) < 2 else 'Tapped tempo: %g bpm' % bpm)
        elif event == K_TEMPO_PICK:
            new = popup_picker('Tempo', bpm, 30, 240, 1, 10, 'bpm')
            if new is not None:
                set_tempo(new)
        elif event == K_GRID_PICK:
            new = popup_choose('Grid', list(GRIDS), values[K_GRID])
            if new:
                window[K_GRID].update(new)
                subdiv = GRIDS[new]
                notes = []
                if triplets and metro.running:                                             # play-along clicks follow the new grid
                    set_running(True)
                redraw_all()
        elif event == K_BPB_PICK:
            new = popup_picker('Beats per bar', beats_per_bar, 1, 12, 1, 2)
            if new is not None:
                beats_per_bar = int(new)
                window[K_BPB].update('%d' % beats_per_bar)
                metro.beats_per_bar = beats_per_bar
                redraw_all()
        elif event == K_TOL_PICK:
            new = popup_picker('Tolerance (± ms)', tol, 2, 60, 1, 5, 'ms')
            if new is not None:
                tol = new
                window[K_TOL].update('%g' % tol)
                redraw_all()
        elif event == K_LATENCY_PICK:
            new = popup_picker('Latency correction', latency, -100, 200, 1, 10, 'ms')
            if new is not None:
                latency = new
                window[K_LATENCY].update('%g' % latency)
        elif event == K_CALIBRATE:
            if not metro.running:
                set_running(True)
            calibrate_mode = not calibrate_mode
            calibrating.clear()
            window[K_CALIBRATE].update(button_color=(C_BG, C_KEY) if calibrate_mode else (C_TEXT, C_BTN))
            set_status('Calibrating: play 8 notes exactly on the click' if calibrate_mode else 'Calibration cancelled')
        elif event == K_PORT_PICK:
            new = popup_choose('MIDI input port', midi_port_names(), values[K_PORT])
            if new:
                window[K_PORT].update(new)
                stop_demo()
                open_port(new)
        elif event == K_PORT_OUT_PICK:
            new = popup_choose('MIDI output port (for MIDI clicks)', midi_port_names(output=True), values[K_PORT_OUT])
            if new:
                window[K_PORT_OUT].update(new)
                open_out(new)
        elif event == K_SOUND_PICK:
            new = popup_choose('Click sound', SOUNDS, values[K_SOUND])
            if new:
                window[K_SOUND].update(new)
                CLICKER.sound = new
                CLICKER.test()
        elif event == K_VOLUME_PICK:
            new = popup_picker('Click volume', CLICKER.volume, 0, 100, 5, 20, '%')
            if new is not None:
                CLICKER.volume = int(new)
                window[K_VOLUME].update('%d' % CLICKER.volume)
                CLICKER.test()
        elif event == K_TEST:
            CLICKER.test()
        elif event == K_DEMO:
            stop_demo() if demo_stop else start_demo()

    stop_demo()
    metro.stop()
    CLICKER.close_out()
    if midi_in:
        midi_in.close()
    window.close()


if __name__ == '__main__':
    main()
