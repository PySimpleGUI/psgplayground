#!/usr/bin/env python3
"""
Harmony Wheel  -  real-time chord and key detection on a circle of fifths.

Everything currently sounding (held keys + notes sustained by the pedal) lights up on the wheel, the detected chord is named in
the center, the key you are gravitating toward is shown as a purple ring (Krumhansl profile correlation over a decaying window)
and a tension meter shows how consonant / dissonant the sounding notes are.  Roman numerals are relative to the estimated key.
Spelling follows the key: in a sharp key (G, D, A, E, B major and their relative minors) the wheel's letters and the chord names
use sharps, in a flat key flats, and with no key yet the usual mix (F♯, D♭, A♭, E♭, B♭).  A locked key keeps its spelling.

The window opens at 90% of the screen and can be resized; the wheel and the keyboard strip fill the space left beside the panel.
Full screen button / F11 covers the whole screen with no title bar (remembered between runs).

Touch:  big buttons everywhere.  Hold freezes the display, Lock key stops the key estimate from drifting.
Keys:   Space = hold   L = lock key   R = roman numerals (remembered)   F11 = full screen on / off   Esc = exit

Requires:  PySimpleGUI, mido, python-rtmidi          (Demo button works without a piano or mido)
Settings persist in harmony_wheel.json (PySimpleGUI user settings folder).

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v1.1  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import sys
import math
import time
import random
import threading
import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAABgFBMVEX/qyTb1dyMfFiskEqeoJc+mdVBms+0lDL/4Tz/wjz//3//0kH/7mj13KM9ibZCs1yNb7f90D89Mh0zb2E4eJw+ymFgUCNiTn5hToBS9nv2V1czcz924o91x/+kMS+dQD6Ob8XAnlDOoP8dGhcAAAD+xDwiHhn+00D39vL/yzP/xDxoUyT9W1tJtP2zi/1K1m0PCwz+0mYmIhvv7OgmJST5zWRURSVkYV3+YWL/qlXyvTu8kv5N5HP/AAD/uzpMwv+Sdzb//wBHzGn+4m1GrPNqMS7/xTyVdcssVzNWU06shS7/fwAzODEsTGJTKidDN1DHmzPDl//OojUpRyy6t7Q3NEdtV5CxR0b/xztCNh0qRFU+pVaDajCFgn3GpFTWtVouVWw9jMI7l1BLNyZMSkdtambEwb3/qjH/wjz/yD7/1yf/10D//1CMOzmXlJHS0Mz6y0Y0aYw5fKo4iUpyYTN7YaeKiIOkoZzk29MwZzp+e3WsqaTGTEvWUVHGu7ZXRHO1TmwPAAAAgHRSTlMV/////////xFMAqz///////////////////////////////8A/v/+/wWs//////////////////8D////AQb//wH/////df////8C////////////////Ov//////////////////B4PDBlYG//////////////////////////qo7XgAAApgSURBVHja7Zv3fxq5EsBdUq4kueT63etPuwKMASEWHs2AK8Z23HDvPpdUO45bih3nXz+NtkmUhV3wIz/cfD7Jx/buar47Go2k0WyX0mHp+gug/qWBwUCbZHDAPUAq194XzaXcAAykAooy+TrQ1yYJvJ5UlEBqoEmAQXj5lVd9quprk6hq36sVMMNgMwDsptzYtyp7qp3iU78dy/HGGwGklNwr9aTN6jnCifoqp6QaAAymlK9e3IJ2g+HFV0pq0AmA8T2/NfUc4blSYQQJYFJ5Nnar+hnB2DOmpg5Al9JVeXubBoEkXRVKbfs/WxHv9aXV2USwDZKYVdNSwyvPUrUABr5RJPUTlGKC2iAEUzohISjfDNQASCljwj2FVVCO2yIAsVoQGh8THNECyL22/d83TxGiqI0C7c3b7T9/nasEGFByNmGQIs7d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'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_NAME = 'Harmony Wheel'
VERSION = '1.1'
SETTINGS_FILE = 'harmony_wheel.json'

# ----------------------------------------------------------------------------------------------------------------------
# Keys
# ----------------------------------------------------------------------------------------------------------------------
K_WHEEL = '-WHEEL-'
K_KEYS = '-KEYS-'
K_MIDI = '-MIDI-'                   # (msg, perf_counter time) from the mido callback / demo thread
K_KEY_NAME = '-KEY NAME-'
K_KEY_CONF = '-KEY CONF-'
K_TENSION = '-TENSION-'
K_TENSION_TXT = '-TENSION TXT-'
K_RECENT = '-RECENT-'
K_RECENT_ROMAN = '-RECENT ROMAN-'
K_HOLD = '-HOLD-'
K_LOCK = '-LOCK-'
K_ROMAN = '-ROMAN-'
K_CLEAR = '-CLEAR-'
K_MEMORY = '-MEMORY-'
K_MEMORY_PICK = '-MEMORY PICK-'
K_PORT = '-PORT-'
K_PORT_PICK = '-PORT PICK-'
K_DEMO = '-DEMO-'
K_FULL = '-FULL-'
K_FULLSCREEN = '-FULLSCREEN-'       # settings-file entry only
K_ROMAN_ON = '-ROMAN ON-'           # settings-file entry only: Roman numerals on / off
K_EXIT = '-EXIT-'
K_STATUS = '-STATUS-'
K_TIMER = sg.EVENT_TIMER

# ----------------------------------------------------------------------------------------------------------------------
# Colors (same meaning in all three piano apps)
# ----------------------------------------------------------------------------------------------------------------------
C_BG = '#14161b'
C_PANEL = '#1e222b'
C_NODE = '#262b36'
C_TEXT = '#e6e8ee'
C_MUTED = '#8a91a3'
C_GRID = '#2c3140'
C_ACCENT = '#2dd4bf'                # chord tone / active
C_ACCENT_DIM = '#1a8f83'            # sustained only by the pedal
C_KEY = '#a78bfa'                   # key center (purple)
C_MID = '#ffd54a'
C_WARN = '#ff8a4c'                  # dissonant
C_BTN = '#2b3242'
C_WHITE_KEY = '#e8e8e8'
C_BLACK_KEY = '#202020'

FONT_BTN = ('Helvetica', 14)
FONT_VAL = ('Helvetica', 14, 'bold')
FONT_SMALL = ('Helvetica', 11)
FONT_TITLE = ('Helvetica', 18, 'bold')
FONT_KEY = ('Helvetica', 26, 'bold')
FONT_RECENT = ('Helvetica', 15)
FONT_BIG = ('Helvetica', 36, 'bold')

BTN_SIZE = (13, 1)                  # one text line high: ~50 px on a 200% tablet, still a comfortable finger target
PICK_SIZE = (3, 1)
KB_H = 64                           # keyboard strip height in pixels at 96 dpi (multiplied by the screen scale)
WINDOW_FRACTION = 0.9               # initial window size as a fraction of the screen
BLACK_PCS = {1, 3, 6, 8, 10}
FIFTHS = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]
NAMES_SHARP = ['C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B']
NAMES_FLAT = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B']
NAMES_COMMON = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'A♭', 'A', 'B♭', 'B']
FLAT_KEYS = {5, 10, 3, 8, 1}        # major keys spelled with flats
INTERVALS = {1: 'm2', 2: 'M2', 3: 'm3', 4: 'M3', 5: 'P4', 6: 'tritone', 7: 'P5', 8: 'm6', 9: 'M6', 10: 'm7', 11: 'M7'}
MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
MAJOR_DEGREES = {0: 'I', 2: 'II', 4: 'III', 5: 'IV', 7: 'V', 9: 'VI', 11: 'VII'}
MINOR_DEGREES = {0: 'I', 2: 'II', 3: 'III', 5: 'IV', 7: 'V', 8: 'VI', 10: 'VII'}
IC_TENSION = {0: 0.0, 1: 1.0, 2: 0.55, 3: 0.2, 4: 0.15, 5: 0.1, 6: 0.8}
ROMAN_SUFFIX = {'': '', 'm': '', 'dim': '°', 'aug': '+', '7': '7', 'maj7': 'Δ7', 'm7': '7', 'mMaj7': 'mΔ7', 'dim7': '°7', 'm7b5': 'ø7', '6': '6', 'm6': '6',
                '9': '9', 'maj9': 'Δ9', 'm9': '9', '5': '5'}

# (suffix, intervals from root).  Listed in preference order; no-5th and other partial voicings are further down.
CHORDS = [('', {0, 4, 7}), ('m', {0, 3, 7}), ('dim', {0, 3, 6}), ('aug', {0, 4, 8}), ('sus2', {0, 2, 7}), ('sus4', {0, 5, 7}),
          ('7', {0, 4, 7, 10}), ('maj7', {0, 4, 7, 11}), ('m7', {0, 3, 7, 10}), ('mMaj7', {0, 3, 7, 11}), ('dim7', {0, 3, 6, 9}), ('m7b5', {0, 3, 6, 10}),
          ('6', {0, 4, 7, 9}), ('m6', {0, 3, 7, 9}), ('7sus4', {0, 5, 7, 10}), ('add9', {0, 2, 4, 7}), ('madd9', {0, 2, 3, 7}),
          ('7', {0, 4, 10}), ('maj7', {0, 4, 11}), ('m7', {0, 3, 10}), ('5', {0, 7}),
          ('9', {0, 2, 4, 7, 10}), ('maj9', {0, 2, 4, 7, 11}), ('m9', {0, 2, 3, 7, 10}), ('7♭9', {0, 1, 4, 7, 10}), ('7♯9', {0, 3, 4, 7, 10}), ('6/9', {0, 2, 4, 7, 9}),
          ('9', {0, 2, 4, 10}), ('maj9', {0, 2, 4, 11}), ('m9', {0, 2, 3, 10}), ('7♭9', {0, 1, 4, 10}),
          ('11', {0, 2, 4, 5, 7, 10}), ('m11', {0, 2, 3, 5, 7, 10}), ('m11', {0, 3, 5, 7, 10}), ('13', {0, 2, 4, 7, 9, 10}), ('13', {0, 4, 7, 9, 10}), ('13', {0, 4, 9, 10}),
          ('7♯11', {0, 4, 6, 7, 10}), ('maj7♯11', {0, 4, 6, 7, 11}), ('7♭13', {0, 4, 7, 8, 10})]

sg.theme_add_new('PianoDark', {'BACKGROUND': C_BG, 'TEXT': C_TEXT, 'INPUT': C_PANEL, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_PANEL, 'BUTTON': (C_TEXT, C_BTN),
                               'PROGRESS': (C_ACCENT, C_PANEL), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
sg.theme('PianoDark')
sg.set_options(icon=ICON)


# ----------------------------------------------------------------------------------------------------------------------
# Music theory helpers
# ----------------------------------------------------------------------------------------------------------------------
def note_name(pc, spelling):
    return spelling[pc % 12]


def key_spelling(key):
    """key = (tonic_pc, is_minor) or None -> note name table to use"""
    if key is None:
        return NAMES_COMMON
    tonic = (key[0] + 3) % 12 if key[1] else key[0]
    return NAMES_FLAT if tonic in FLAT_KEYS else NAMES_SHARP if tonic else NAMES_COMMON


def name_chord(pcs, bass_pc, spelling):
    """Returns (name, root_pc, suffix) for a set of pitch classes; root_pc/suffix are None when nothing matched"""
    pcs = set(pcs)
    if not pcs:
        return '', None, None
    if len(pcs) == 1:
        return note_name(bass_pc, spelling), bass_pc, None
    best = None
    for root in range(12):
        rel = {(p - root) % 12 for p in pcs}
        for index, (suffix, ivs) in enumerate(CHORDS):
            if rel == ivs:
                score = (0 if root == bass_pc else 1, index)
                if best is None or score < best[0]:
                    best = (score, root, suffix)
    if best:
        _, root, suffix = best
        name = note_name(root, spelling) + suffix + ('' if bass_pc == root else '/' + note_name(bass_pc, spelling))
        return name, root, suffix
    if len(pcs) == 2:
        other = (pcs - {bass_pc}).pop()
        return '%s – %s   %s' % (note_name(bass_pc, spelling), note_name(other, spelling), INTERVALS[(other - bass_pc) % 12]), None, None
    best = None
    for root in range(12):
        rel = {(p - root) % 12 for p in pcs}
        for index, (suffix, ivs) in enumerate(CHORDS):
            hit = len(rel & ivs)
            if hit >= 3:
                score = (-(hit * 2 - len(rel - ivs) * 3 - len(ivs - rel)), 0 if root == bass_pc else 1, index)
                if best is None or score < best[0]:
                    best = (score, root, suffix)
    if best:
        _, root, suffix = best
        return note_name(root, spelling) + suffix + ' ?', root, suffix
    return ' '.join(note_name(p, spelling) for p in sorted(pcs, key=lambda p: (p - bass_pc) % 12)), None, None


def roman_numeral(root_pc, suffix, key):
    if key is None or root_pc is None or suffix is None:
        return ''
    tonic, minor = key
    semi = (root_pc - tonic) % 12
    degrees = MINOR_DEGREES if minor else MAJOR_DEGREES
    if semi in degrees:
        deg = degrees[semi]
    elif (semi + 1) % 12 in degrees:
        deg = '♭' + degrees[(semi + 1) % 12]
    else:
        deg = '♯' + degrees[(semi - 1) % 12]
    if suffix.startswith(('m', 'dim')) and not suffix.startswith('maj'):
        deg = deg.lower()
    return deg + ROMAN_SUFFIX.get(suffix, suffix.lstrip('m'))


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
    conf = max(0.0, min(0.99, 0.5 + (scores[0][0] - scores[1][0]) * 2.5))
    return scores[0][1], conf


def tension(pcs):
    pcs = sorted(pcs)
    if len(pcs) < 2:
        return 0.0
    total, n = 0.0, 0
    for i in range(len(pcs)):
        for j in range(i + 1, len(pcs)):
            ic = (pcs[j] - pcs[i]) % 12
            total += IC_TENSION[min(ic, 12 - ic)]
            n += 1
    return min(1.0, total / n * 1.6)


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
    return mido.open_input(name, callback=lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter())))


def demo_thread(window, stop_event):
    """ii-V-I progressions in a few keys, with pedal, so the wheel can be seen without a piano"""
    send = lambda msg: window.write_event_value(K_MIDI, (msg, time.perf_counter()))
    progression = [[38, 53, 57, 60, 65], [43, 53, 59, 62, 65], [36, 52, 55, 59, 64], [36, 52, 57, 60, 64]]     # Dm7 G7 Cmaj7 C6
    playing = []
    while not stop_event.is_set():
        for shift in (0, 3, -5):
            for chord in progression:
                send(Msg('control_change', control=64, value=127))
                for note in chord:
                    note += shift
                    send(Msg('note_on', note=note, velocity=random.randint(50, 100)))
                    playing.append(note)
                    if stop_event.wait(random.uniform(0.04, 0.12)):
                        break
                if stop_event.wait(1.3):
                    break
                for note in playing:
                    send(Msg('note_off', note=note, velocity=0))
                playing = []
                send(Msg('control_change', control=64, value=0))
                if stop_event.wait(0.25):
                    break
    for note in playing:
        send(Msg('note_off', note=note, velocity=0))
    send(Msg('control_change', control=64, value=0))


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    auto_demo = '--demo' in sys.argv
    auto_close = float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None

    sw, sh = sg.Window.get_screen_size()

    def value_row(label, key, default, pick_key, unit=''):
        value = value_box(default, key, 7, FONT_VAL)
        return [sg.Text(label, font=FONT_SMALL, text_color=C_MUTED, size=(12, 1)), value, sg.Text(unit, font=FONT_SMALL, text_color=C_MUTED),
                sg.Button('…', key=pick_key, size=PICK_SIZE, font=FONT_BTN)]

    right = [[sg.Text(APP_NAME, font=FONT_TITLE)],
             [sg.Text('Key estimate', font=FONT_SMALL, text_color=C_MUTED)],
             [sg.Text('—', key=K_KEY_NAME, font=FONT_KEY, text_color=C_KEY)],
             [sg.Text('', key=K_KEY_CONF, font=FONT_SMALL, text_color=C_MUTED)],
             [sg.Text('Tension', font=FONT_SMALL, text_color=C_MUTED), sg.Text('', key=K_TENSION_TXT, font=FONT_SMALL, text_color=C_MUTED)],
             [sg.Graph((340, 26), (0, 0), (340, 26), background_color=C_PANEL, key=K_TENSION)],
             [sg.Text('consonant', font=FONT_SMALL, text_color=C_ACCENT), sg.Push(), sg.Text('dissonant', font=FONT_SMALL, text_color=C_WARN)],
             [sg.Text('Recent chords', font=FONT_SMALL, text_color=C_MUTED)],
             [sg.Text('', key=K_RECENT, font=FONT_RECENT, size=(30, 2))],
             [sg.Text('', key=K_RECENT_ROMAN, font=FONT_RECENT, size=(30, 1), text_color=C_KEY)],
             [sg.Button('Hold', key=K_HOLD, size=BTN_SIZE, font=FONT_BTN), sg.Button('Lock key', key=K_LOCK, size=BTN_SIZE, font=FONT_BTN)],
             [sg.Button('Roman: on', key=K_ROMAN, size=BTN_SIZE, font=FONT_BTN), sg.Button('Clear', key=K_CLEAR, size=BTN_SIZE, font=FONT_BTN)],
             value_row('Key memory', K_MEMORY, '6', K_MEMORY_PICK, 's'),
             [sg.Text('MIDI in', font=FONT_SMALL, text_color=C_MUTED, size=(12, 1)),
              value_box('', K_PORT, 14, FONT_SMALL, 'left'),
              sg.Button('…', key=K_PORT_PICK, size=PICK_SIZE, font=FONT_BTN)],
             [sg.VPush()],
             [sg.Button('Demo', key=K_DEMO, size=BTN_SIZE, font=FONT_BTN), sg.Button('Full screen', key=K_FULL, size=BTN_SIZE, font=FONT_BTN)],
             [sg.Button('Exit', key=K_EXIT, size=BTN_SIZE, font=FONT_BTN)]]

    legend = [sg.Text('● chord tone', text_color=C_ACCENT, font=FONT_SMALL), sg.Text('◯ root', text_color=C_TEXT, font=FONT_SMALL),
              sg.Text('◯ in key', text_color=C_KEY, font=FONT_SMALL), sg.Text('● key center', text_color=C_KEY, font=FONT_SMALL),
              sg.Text('   keyboard: bright = held, dim = pedal', text_color=C_MUTED, font=FONT_SMALL),
              sg.Push(), sg.Text('', key=K_STATUS, font=FONT_SMALL, text_color=C_MUTED)]

    wheel_graph = sg.Graph((500, 500), (0, 0), (500, 500), background_color=C_BG, key=K_WHEEL, pad=(0, 0), expand_x=True, expand_y=True)
    keys_graph = sg.Graph((700, KB_H), (0, 0), (700, KB_H), background_color=C_BG, key=K_KEYS, pad=(0, (6, 0)), expand_x=True)
    layout = [[wheel_graph, sg.Column(right, vertical_alignment='top', pad=((16, 0), 0))], [keys_graph], legend]
    window = sg.Window(APP_NAME, layout, finalize=True, enable_close_attempted_event=True, margins=(8, 8), resizable=True, enable_window_config_events=True)
    scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)       # 2.0 on a 200% Windows display: pixel sizes below are multiplied by it
    window[K_KEYS].set_size((None, int(KB_H * scale)))
    window.size = (int(sw * WINDOW_FRACTION), int(sh * WINDOW_FRACTION))
    window.move(int(sw * (1 - WINDOW_FRACTION) / 2), max(0, int(sh * (1 - WINDOW_FRACTION) / 2) - 20))
    window.refresh()
    window.bind('<Escape>', K_EXIT)
    window.bind('<F11>', K_FULL)
    window.bind('<space>', K_HOLD)
    window.bind('<l>', K_LOCK)
    window.bind('<r>', K_ROMAN)
    wheel, keys, tension_bar, status = window[K_WHEEL], window[K_KEYS], window[K_TENSION], window[K_STATUS]

    # ---- state
    geom, kw, kb_h, kb_w, S = {}, 0, 100, 100, 100                 # real sizes come from the finished window (apply_size)
    fullscreen = False
    held, sustained, key_figs = set(), set(), {}
    pedal_down, hold, lock, roman = False, False, False, bool(sg.user_settings_get_entry(K_ROMAN_ON, True))
    window[K_ROMAN].update('Roman: on' if roman else 'Roman: off')
    pc_weight, last_decay = [0.0] * 12, time.perf_counter()
    half_life = float(window[K_MEMORY].get() or 6)
    key, key_conf = None, 0.0
    dirty, last_change = True, 0.0
    pending_name, pending_since, history = None, 0.0, []
    midi_in, demo_stop, demo_thr = None, None, None
    t_start = time.perf_counter()
    cx = cy = R = r = 50.0
    node_font = chord_font = sub_font = ('Helvetica', 11)

    def apply_size():
        """Read the real size of the wheel and keyboard graphs (after the window was sized, resized or went full screen) and rebuild
        the wheel geometry / fonts and the key geometry from it"""
        nonlocal S, cx, cy, R, r, node_font, chord_font, sub_font, kb_w, kb_h, geom, kw
        w, h = wheel.get_size()
        kw_, kh = keys.get_size()
        if not w or w < 40 or h < 40 or (w, h, kw_, kh) == (wheel.CanvasSize[0], wheel.CanvasSize[1], kb_w, kb_h) and geom:
            return
        wheel.CanvasSize, kb_w, kb_h = (w, h), kw_, kh
        wheel.change_coordinates((0, 0), (w, h))
        keys.CanvasSize = (kw_, kh)
        keys.change_coordinates((0, 0), (kw_, kh))
        S = min(w, h)
        cx, cy = w / 2, h / 2
        R, r = S * 0.40, S * 0.062
        node_font = ('Helvetica', max(11, int(S / 26 / scale)), 'bold')          # fonts are in points: divide the pixel size by the dpi scale
        chord_font = ('Helvetica', max(20, int(S / 9 / scale)), 'bold')
        sub_font = ('Helvetica', max(11, int(S / 22 / scale)))
        geom, kw = build_key_geometry(21, 108, kw_)
        key_figs.clear()
        draw_keyboard()
        for p in sustained:
            key_mark(p, C_ACCENT_DIM)
        for p in held:
            key_mark(p, C_ACCENT)
        refresh()

    def set_fullscreen(state):
        """Full screen = the window covers the whole screen with no title bar (tk's -fullscreen attribute); remembered between runs"""
        nonlocal fullscreen
        fullscreen = state
        window.TKroot.attributes('-fullscreen', state)
        window[K_FULL].update('Windowed' if state else 'Full screen', button_color=(C_BG, C_ACCENT) if state else (C_TEXT, C_BTN))
        sg.user_settings_set_entry(K_FULLSCREEN, state)

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

    def key_mark(pitch, color):
        key_unmark(pitch)
        if pitch not in geom:
            return
        x0, x1, black = geom[pitch]
        key_figs[pitch] = keys.draw_rectangle((x0, kb_h), (x1, kb_h * 0.42), fill_color=color, line_color=color) if black else \
            keys.draw_rectangle((x0 + 1, kb_h * 0.38), (x1 - 1, 1), fill_color=color, line_color=color)

    def key_unmark(pitch):
        fig = key_figs.pop(pitch, None)
        if fig is not None:
            keys.delete_figure(fig)

    def decay_weights():
        nonlocal last_decay
        now = time.perf_counter()
        f = 0.5 ** ((now - last_decay) / max(0.5, half_life))
        for i in range(12):
            pc_weight[i] *= f
        last_decay = now

    def node_xy(i):
        a = math.radians(30 * i)
        return cx + R * math.sin(a), cy + R * math.cos(a)

    def draw_wheel():
        sounding = held | sustained
        pcs = {p % 12 for p in sounding}
        bass = min(sounding) % 12 if sounding else None
        spelling = key_spelling(key)
        name, root, suffix = name_chord(pcs, bass, spelling)
        diatonic = set()
        if key:
            scale = [0, 2, 3, 5, 7, 8, 10] if key[1] else [0, 2, 4, 5, 7, 9, 11]
            diatonic = {(key[0] + s) % 12 for s in scale}
        wheel.erase()
        wheel.draw_circle((cx, cy), R, line_color=C_GRID, line_width=2)
        for i, pc in enumerate(FIFTHS):
            x, y = node_xy(i)
            label = spelling[pc]                                 # the wheel is spelled like the chord names: sharps in sharp keys, flats in flat keys
            if key and pc == key[0]:
                wheel.draw_circle((x, y), r + 7, line_color=C_KEY, line_width=4)
            if pc in pcs:
                wheel.draw_circle((x, y), r, fill_color=C_ACCENT, line_color='#ffffff' if pc == root else C_ACCENT, line_width=4 if pc == root else 1)
                wheel.draw_text(label, (x, y), color=C_BG, font=node_font)
            elif pc in diatonic:
                wheel.draw_circle((x, y), r, fill_color=C_NODE, line_color=C_KEY, line_width=2)
                wheel.draw_text(label, (x, y), color=C_TEXT, font=node_font)
            else:
                wheel.draw_circle((x, y), r, fill_color=C_NODE, line_color=C_GRID, line_width=1)
                wheel.draw_text(label, (x, y), color=C_MUTED, font=node_font)
        if name:
            wheel.draw_text(name, (cx, cy + S * 0.02), color=C_TEXT, font=chord_font)
            rn = roman_numeral(root, suffix, key) if roman else ''
            if rn:
                wheel.draw_text('%s in %s' % (rn, key_name(key)), (cx, cy - S * 0.07), color=C_KEY, font=sub_font)
        else:
            wheel.draw_text('play something', (cx, cy), color=C_MUTED, font=sub_font)
        t = tension(pcs)
        tension_bar.erase()
        tension_bar.draw_rectangle((0, 26), (max(2, t * 340), 0), fill_color=C_ACCENT if t < 0.35 else C_MID if t < 0.65 else C_WARN, line_width=0)
        window[K_TENSION_TXT].update('%d%%' % round(t * 100) if pcs else '')
        return name, root, suffix

    def key_name(k):
        return '—' if k is None else note_name(k[0], key_spelling(k)) + (' minor' if k[1] else ' major')

    def update_key_panel():
        window[K_KEY_NAME].update(key_name(key))
        window[K_KEY_CONF].update(('%d%% sure' % round(key_conf * 100) if key else 'listening…') + ('  ·  locked' if lock else ''))

    def update_history():
        window[K_RECENT].update('  ·  '.join(n for n, _ in history[-6:]))
        window[K_RECENT_ROMAN].update('  ·  '.join(rn for _, rn in history[-6:]) if roman else '')

    def refresh():
        nonlocal pending_name, pending_since, dirty
        name, root, suffix = draw_wheel()
        sounding = held | sustained
        if len({p % 12 for p in sounding}) >= 3 and root is not None and not name.endswith('?'):
            if name != pending_name:
                pending_name, pending_since = name, time.perf_counter()
        else:
            pending_name = None
        dirty = False

    def set_status(text):
        status.update(text)

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
        nonlocal pedal_down, dirty, last_change, key, key_conf
        kind = msg.type
        if kind == 'note_on' and msg.velocity == 0:
            kind = 'note_off'
        if kind == 'note_on':
            held.add(msg.note)
            sustained.discard(msg.note)
            key_mark(msg.note, C_ACCENT)
            decay_weights()
            pc_weight[msg.note % 12] += 1.0 + msg.velocity / 127
            if not lock:
                key, key_conf = key_estimate(pc_weight)
                update_key_panel()
        elif kind == 'note_off':
            if msg.note in held:
                held.discard(msg.note)
                if pedal_down:
                    sustained.add(msg.note)
                    key_mark(msg.note, C_ACCENT_DIM)
                else:
                    key_unmark(msg.note)
        elif kind == 'control_change' and msg.control == 64:
            pedal_down = msg.value >= 64
            if not pedal_down:
                for p in sustained:
                    key_unmark(p)
                sustained.clear()
        else:
            return
        dirty, last_change = True, time.perf_counter()

    def tick():
        now = time.perf_counter()
        if dirty and not hold and now - last_change > 0.05:
            refresh()
        if pending_name and now - pending_since > 0.25 and (not history or history[-1][0] != pending_name):
            sounding = held | sustained
            pcs = {p % 12 for p in sounding}
            name, root, suffix = name_chord(pcs, min(sounding) % 12, key_spelling(key))
            history.append((name, roman_numeral(root, suffix, key)))
            del history[:-12]
            update_history()

    # ---- startup
    apply_size()
    update_key_panel()
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
    window.timer_start(25)

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
        elif event == K_FULL:
            set_fullscreen(not fullscreen)
        elif event == K_MIDI:
            handle_midi(values[K_MIDI][0])
        elif event == K_HOLD:
            hold = not hold
            window[K_HOLD].update('Holding' if hold else 'Hold', button_color=(C_BG, C_ACCENT) if hold else (C_TEXT, C_BTN))
            if not hold:
                refresh()
        elif event == K_LOCK:
            lock = not lock
            window[K_LOCK].update('Key locked' if lock else 'Lock key', button_color=(C_BG, C_KEY) if lock else (C_TEXT, C_BTN))
            update_key_panel()
        elif event == K_ROMAN:
            roman = not roman
            window[K_ROMAN].update('Roman: on' if roman else 'Roman: off')
            sg.user_settings_set_entry(K_ROMAN_ON, roman)
            refresh()
            update_history()
        elif event == K_CLEAR:
            history.clear()
            pc_weight = [0.0] * 12
            if not lock:
                key, key_conf = None, 0.0
            update_history()
            update_key_panel()
            refresh()
        elif event == K_MEMORY_PICK:
            new = popup_picker('Key memory (half-life)', half_life, 1, 30, 1, 5, 's')
            if new is not None:
                half_life = new
                window[K_MEMORY].update('%g' % half_life)
        elif event == K_PORT_PICK:
            new = popup_choose('MIDI input port', midi_port_names(), values[K_PORT])
            if new:
                window[K_PORT].update(new)
                stop_demo()
                open_port(new)
        elif event == K_DEMO:
            stop_demo() if demo_stop else start_demo()

    stop_demo()
    if midi_in:
        midi_in.close()
    window.close()


if __name__ == '__main__':
    main()
