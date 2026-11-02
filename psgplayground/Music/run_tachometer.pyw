"""
Run Tachometer  (run_tachometer.pyw)  -  evenness of scales, arpeggios, runs and trills WITHOUT a metronome.

Every note you play is an onset; the gap between one onset and the next is what matters.  The program measures the last N gaps
(the "Window" setting) and shows:
  DIAL      - notes per second (1 / median gap) on a big semicircular dial, with the equivalent tempo underneath
              (e.g. 9.4 notes/s = 16ths at 141 bpm = 8ths at 282 bpm = triplet 8ths at 188 bpm)
  GAP STRIP - one bar per gap, height = milliseconds, newest at the right.  The shaded band is the median gap +/- Tolerance;
              bars inside it are teal (even), bars above it are coral (too long = a hesitation), bars below it are blue
              (too short = a rushed note).  Uneven bars are labelled with the two note names so you know exactly where the hiccup is.
              A thin vertical line marks a rest (gap longer than "Rest gap"): gaps across a rest are never counted.
  TILES     - NOTES/SEC, MEDIAN GAP, EVENNESS (share of gaps inside the band), WORST (biggest deviation, which notes), RUN (notes in
              the current run and its span), FASTEST (best notes/sec this session) and DETECTED (what the run looks like:
              "D major scale up 2 oct", "C minor arpeggio down", "trill E4-F4", "chromatic" ...)
Chords: notes struck within "Chord ms" of each other count as ONE onset (so chord runs and octaves measure correctly).

TOUCH: every numeric setting is a read-only value box followed by a small pencil mark; tapping the box or the pencil opens a big picker:
a slider plus +/- step buttons (or one button per choice for short lists), OK/Cancel.
TEXT SIZE: one multiplier for every font in the program; changing it rebuilds the window in place (notes and MIDI connection are kept).
FULL (F11) covers the whole screen with no title bar; F10 hides / shows the control rows; F9 pauses; HOME resets; ESC exits.
Demo checkbox plays scale runs, an arpeggio and a trill by itself with a few deliberate hiccups.
Requires:  pip install PySimpleGUI mido python-rtmidi
Settings persist in SETTINGS_FILE (run_tachometer.json in the PySimpleGUI settings folder) via Window.settings_save() at exit;
the MIDI port, fullscreen and hidden-controls state are saved as they change.  "Demo" is deliberately not saved.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import math
import random
import sys
import statistics
import time
import tkinter.font as tkfont
from collections import deque

import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAABgFBMVEXsoZ/+b2blz8j/mF/75pIeGxcAAAD+xDz/00BJ1WwiHhn/yzP/xDxoUyQlIhr9W1sQCw739fL+0mZN5HPu6+f/qlX/AAD/uzr8zWQtVzP//wDyvTtVRSI7mFBHzGj/xTz+YWIqSCz/fwCVeDGuiC9NSUe4uLNBsFvHmjP/xzv6yUyJhoI0eUM81GRBNR3MojVpMi7p5dYqJyNAq1qsqaT/qjH/wjz/yD7/1yf/10D//1DGxcD/4m0+pFVIOCRy3IqzRkWEazAxbDxDu2BsaWSQPDqmop6v5rnMrFf7TVT/mTP/qgD/vzv+tmX/wjz/0kH/4Tz//39YLCmAfXjJTU3Ewr3G6cz+X2D65rJTUExvZ1d7eHWYgEOCgHuCwY+E35mX4aWqjEm2lEnWt1vb0mjQ8dT/0T733qQZIBwcSyU/NB0/NiM1cD4ytVI5yl431V9egUZf24NjLyxgXVltXmN9cFdw0lxu0WqcXT+YlJCUvpqb1GqK4Z66mjS87cTXUlKMJbQwAAAAgHRSTlP///////8A/v7//wWs//////////8DAQb//wH/////df//Av///////zr//////////////weDwwZWBv///////////////////wUDOP9MrBEC/////////////////////////////////////////////////////////////xuVIDEAAAcmSURBVHja7ZuHd9pIEIe5shIsZtkF0YvBNrgEHEPsOPa5xLETO3dxes+lX5Lrvdd//WaFykoIkLBk5d15krw8QNrfp9nZ0daIFLJFTgAG/5Qtxn2yYtY7QCbn74PmMl4Aspm4JE2txyd8svj6lCTFM1mXAEX+8PNrE7Ic9clkeWJtnruh6AYALspNXpPhLj8tKl+bzKmFjwLISLk1ecFneRVhQV7LSZkRAMWMdH01AHWNYfW6lCkOAwC+s4HJqwhnJZsTLABT0spkoPpAMLkCMgMAPpKu2C/3qRFY7AoIOQJkVubFa6Mlea6c8MHKc3LJUvD8SsYJIHtDssjPEIIp8sEoJmTGgiDdyDoAZKRJ4ZrpRS6OfTEOsTgtFD4pBKIBkFs34z96miBEkI/Gyzttln92PWcHyEo5kzBBkMrto0F5JGEq5KSs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'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_TITLE = 'Run Tachometer'
SETTINGS_FILE = 'run_tachometer.json'

# ---------- Keys ----------
K_DIAL = '-DIAL-'
K_STRIP = '-STRIP-'
K_PORT = '-PORT-'
K_REFRESH = '-REFRESH-'
K_WINDOW = '-WINDOW-'
K_TOL = '-TOL-'
K_CHORD_MS = '-CHORD MS-'
K_REST = '-REST-'
K_DIAL_MAX = '-DIAL MAX-'
K_TEXT_SIZE = '-TEXT SIZE-'
K_REBUILD = '-REBUILD-'                # internal event: fonts changed, rebuild the window
K_RECALC = '-RECALC-'                  # internal event: a setting changed, recompute the stats
K_DEMO = '-DEMO-'
K_RESET = '-RESET-'
K_PAUSE = '-PAUSE-'
K_FULL = '-FULL-'
K_EXIT = '-EXIT-'
K_STATUS = '-STATUS-'
K_PICK_VAL = '-PICK VAL-'
K_PICK_OK = '-PICK OK-'
K_PICK_CANCEL = '-PICK CANCEL-'
K_PICK_SLIDER = '-PICK SLIDER-'
K_EDIT = '-EDIT-'
KT_EDIT = lambda key: (K_EDIT, key)                    # "pencil" beside a value box: opens the picker for that setting
K_PICK = '-PICK-'
KT_PICK = lambda choice: (K_PICK, choice)              # picker: one button per choice
K_STEP = '-STEP-'
KT_STEP = lambda delta: (K_STEP, delta)                # picker: +/- step button
TAP = ' TAP'                           # suffix added to a field's key when its value box is tapped
K_TILE = '-TILE-'
KT_TILE = lambda name: (K_TILE, name)                  # big number of a tile
K_TILE_LABEL = '-TILE LABEL-'
KT_TILE_LABEL = lambda name: (K_TILE_LABEL, name)      # label above a tile number
K_TILE_SUB = '-TILE SUB-'
KT_TILE_SUB = lambda name: (K_TILE_SUB, name)          # small text under a tile number
K_MIDI_NOTE = '-MIDI NOTE-'            # event from the MIDI callback thread, value = (time, note, velocity)
K_KEY_ESC = '-KEY ESC-'
K_KEY_F9 = '-KEY F9-'
K_KEY_F10 = '-KEY F10-'
K_KEY_F11 = '-KEY F11-'
K_KEY_HOME = '-KEY HOME-'
K_FULLSCREEN = '-FULLSCREEN-'          # settings-file entry only
K_CONTROLS = '-CONTROLS-'
K_CONTROLS_HIDDEN = '-CONTROLS HIDDEN-'   # settings-file entry only
K_EXTRAS = '-EXTRAS-'
K_TOGGLE_CONTROLS = '-TOGGLE CONTROLS-'

# ---------- Colors (dark background, high contrast; every color is paired with a text label) ----------
C_BG = '#101418'
C_EVEN = '#2DD4BF'           # teal  - gap inside the tolerance band
C_LONG = '#FF8A4C'           # coral - gap too long (hesitation)
C_SHORT = '#4AA3FF'          # blue  - gap too short (rushed)
C_BAND = '#183833'           # tolerance band fill on the strip
C_MEDIAN = '#9AA6B2'         # median line
C_REST = '#6B7A8A'           # rest marker line
C_DIAL = '#2C343C'           # dial arc background
C_DIAL_TICK = '#9AA6B2'
C_GRID = '#2C343C'
C_AXIS_TEXT = '#9AA6B2'
C_STATUS_OK = '#69F0AE'
C_STATUS_BAD = '#FF8A65'
C_PAUSED = '#FFB300'
C_EDIT = '#4DD0E1'           # pencil mark beside each value box
C_ON_TILE = '#000000'        # text color used on top of a tile color
C_TILE_NEUTRAL = '#2C343C'   # tile background when the value has no color meaning
C_DETECT = '#A78BFA'         # purple - detected scale / arpeggio text
TILE_EASE = 0.35             # fraction of the remaining color difference a tile moves per 100 ms tick (1.0 = instant)
EVEN_STOPS = [(50, (255, 82, 82)), (75, (255, 234, 0)), (100, (0, 230, 118))]                 # evenness % -> rgb anchors (red, yellow, green)
SPEED_STOPS = [(0.0, (68, 138, 255)), (0.5, (0, 230, 118)), (0.75, (255, 234, 0)), (1.0, (255, 23, 68))]   # fraction of dial max -> rgb

FONT_FAMILY = 'Segoe UI'
BASE_FONTS = {'FONT_UI': 12,             # all controls, status line
              'FONT_LABEL': 11,          # tile labels and sub text
              'FONT_BIG': 26,            # tile numbers
              'FONT_DIAL': 44,           # notes/sec in the middle of the dial
              'FONT_DIAL_SUB': 14,       # tempo equivalents under the dial number
              'FONT_TICK': 11,           # dial tick labels, strip axis labels
              'FONT_NOTE': 11,           # note-name labels on uneven bars
              'FONT_PICK': 20,           # touch picker buttons
              'FONT_PICK_VALUE': 48}     # touch picker current value
TEXT_SIZE_CHOICES = ['70%', '85%', '100%', '115%', '130%']


def set_fonts(text_size):
    """Define every FONT_* global from the base point sizes times the Text size setting ('100%' etc.); all fonts are bold"""
    try:
        mult = int(str(text_size).rstrip('%')) / 100
    except ValueError:
        mult = 1.0
    for name, size in BASE_FONTS.items():
        globals()[name] = (FONT_FAMILY, max(7, round(size * mult)), 'bold')


set_fonts('100%')
WINDOW_FRACTION = 0.85                                                             # initial window size as a fraction of the screen
HISTORY = 400                                                                      # onsets kept
NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
WINDOW_CHOICES = list(range(4, 65))
TOL_CHOICES = list(range(5, 51))
CHORD_MS_CHOICES = [0, 10, 20, 30, 40, 50, 60, 80]
REST_CHOICES = [0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0]
DIAL_MAX_CHOICES = [8, 12, 16, 20, 24]
STEPS_1_10 = [(-10, '-10'), (-1, '-1'), (1, '+1'), (10, '+10')]
STEPS_1_4 = [(-4, '-4'), (-1, '-1'), (1, '+1'), (4, '+4')]
TT_WINDOW = 'How many of the most recent gaps are measured (a 2-octave scale = 28 notes)'
TT_TOL = 'Gaps within this percentage of the median gap count as even'
TT_CHORD = 'Notes struck closer together than this count as one chord (0 = every note is an onset)'
TT_REST = 'A gap longer than this is a rest: it ends the run and is never counted as uneven'
TT_DIAL = 'Top of the dial in notes per second'
T_NPS, T_GAP, T_EVEN, T_WORST, T_RUN, T_FASTEST, T_DETECT = 'NOTES / SEC', 'MEDIAN GAP', 'EVENNESS', 'WORST GAP', 'RUN', 'FASTEST', 'DETECTED'
TILES = (T_NPS, T_GAP, T_EVEN, T_WORST, T_RUN, T_FASTEST, T_DETECT)

SCALES = [('major scale', (0, 2, 4, 5, 7, 9, 11)), ('natural minor scale', (0, 2, 3, 5, 7, 8, 10)), ('harmonic minor scale', (0, 2, 3, 5, 7, 8, 11)),
          ('melodic minor scale', (0, 2, 3, 5, 7, 9, 11)), ('major pentatonic', (0, 2, 4, 7, 9)), ('minor pentatonic', (0, 3, 5, 7, 10)),
          ('blues scale', (0, 3, 5, 6, 7, 10)), ('whole-tone scale', (0, 2, 4, 6, 8, 10)), ('chromatic scale', tuple(range(12)))]
ARPEGGIOS = [('major arpeggio', (0, 4, 7)), ('minor arpeggio', (0, 3, 7)), ('dim arpeggio', (0, 3, 6)), ('aug arpeggio', (0, 4, 8)),
             ('dom 7 arpeggio', (0, 4, 7, 10)), ('major 7 arpeggio', (0, 4, 7, 11)), ('minor 7 arpeggio', (0, 3, 7, 10)), ('dim 7 arpeggio', (0, 3, 6, 9)),
             ('half-dim arpeggio', (0, 3, 6, 10))]


class Onset:
    __slots__ = ('t', 'notes', 'vel')

    def __init__(self, t, note, vel):
        self.t, self.notes, self.vel = t, [note], vel


class G:                                # program-wide state
    window = None
    port = None
    status = ''
    status_ok = False
    onsets = deque()
    fastest = 0.0
    fullscreen = False
    paused = False
    pause_t = 0.0
    scale = 1.0                         # screen dpi / 96, applied to pixel-based drawing sizes
    text_px = {}
    tile_target = {}
    tile_now = {}
    stats = None                        # last computed statistics dict (kept while a new run is starting)
    demo_next_t = 0.0
    demo_seq = []                       # notes the demo still has to play
    demo_gap = 0.11


# ---------- Helpers ----------
def note_name(n):
    return f'{NOTE_NAMES[n % 12]}{n // 12 - 1}'


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def hexcolor(rgb_tuple):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(c)))) for c in rgb_tuple)


def mix(c1, c2, f):
    """Blend two rgb tuples, f=0 -> c1, f=1 -> c2"""
    return tuple(a + (b - a) * f for a, b in zip(c1, c2))


def gradient(stops, value):
    """rgb along a list of (value, rgb) anchors"""
    if value <= stops[0][0]:
        return stops[0][1]
    for (v0, c0), (v1, c1) in zip(stops, stops[1:]):
        if value <= v1:
            return mix(c0, c1, (value - v0) / (v1 - v0))
    return stops[-1][1]


def fval(values, key, default):
    try:
        return float(values[key])
    except (TypeError, ValueError, KeyError):
        return default


def ival(values, key, default):
    return int(fval(values, key, default))


def midi_ports():
    try:
        return mido.get_input_names() if mido else []
    except Exception:
        return []


def midi_callback(msg):
    if msg.type == 'note_on' and msg.velocity > 0 and G.window is not None:
        G.window.write_event_value(K_MIDI_NOTE, (time.monotonic(), msg.note, msg.velocity))


def close_port():
    if G.port is not None:
        try:
            G.port.close()
        except Exception:
            pass
    G.port = None


def open_port(name):
    close_port()
    if mido is None:
        G.status, G.status_ok = 'mido not installed:  pip install mido python-rtmidi', False
    elif not name:
        G.status, G.status_ok = 'No MIDI input found - plug in the piano, then Refresh', False
    else:
        try:
            G.port = mido.open_input(name, callback=midi_callback)
            G.status, G.status_ok = f'Listening on {name}', True
        except Exception as e:
            G.status, G.status_ok = f'Cannot open {name}: {e}', False
    if G.window is not None:
        G.window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)


# ---------- Data ----------
def add_note(t, note, vel, chord_sec):
    """A note becomes a new onset, or joins the previous onset if it arrived within the chord window"""
    if G.onsets and t - G.onsets[-1].t < chord_sec:
        G.onsets[-1].notes.append(note)
        return False
    G.onsets.append(Onset(t, note, vel))
    while len(G.onsets) > HISTORY:
        G.onsets.popleft()
    return True


def gaps_of(onsets, rest_sec):
    """[(gap_sec, from_onset, to_onset, is_rest)] between consecutive onsets"""
    return [(b.t - a.t, a, b, b.t - a.t > rest_sec) for a, b in zip(onsets, onsets[1:])]


def direction_of(pitches):
    steps = [b - a for a, b in zip(pitches, pitches[1:]) if b != a]
    if not steps:
        return ''
    up, down = sum(1 for s in steps if s > 0), sum(1 for s in steps if s < 0)
    return 'up' if down == 0 else 'down' if up == 0 else 'up-down' if steps[0] > 0 else 'down-up'


def detect(onsets):
    """Name what the run looks like from the pitches of the recent single-note onsets: trill, scale, arpeggio, octaves ..."""
    pitches = [o.notes[0] for o in onsets if len(o.notes) == 1]
    if len(pitches) < 4:
        if onsets and all(len(o.notes) == 2 and abs(o.notes[0] - o.notes[1]) == 12 for o in onsets[-4:]) and len(onsets) >= 4:
            return 'octaves ' + direction_of([min(o.notes) for o in onsets[-8:]])
        return ''
    distinct = sorted(set(pitches))
    if len(distinct) == 2:
        alternating = all(a != b for a, b in zip(pitches, pitches[1:]))
        name = 'trill' if distinct[1] - distinct[0] <= 2 else 'tremolo'
        return f'{name} {note_name(distinct[0])}-{note_name(distinct[1])}' if alternating else f'{note_name(distinct[0])} / {note_name(distinct[1])}'
    steps = [abs(b - a) for a, b in zip(pitches, pitches[1:]) if b != a]
    pcs = {p % 12 for p in pitches}
    lowest_pc, first_pc = min(pitches) % 12, pitches[0] % 12
    families = ARPEGGIOS if steps and min(steps) >= 3 else SCALES
    best = None
    for root in range(12):
        for name, ivs in families:
            if pcs <= {(root + i) % 12 for i in ivs}:
                score = (len(ivs), 0 if root == lowest_pc else 1 if root == first_pc else 2)
                if best is None or score < best[0]:
                    best = (score, root, name)
    span = (max(pitches) - min(pitches)) // 12
    span_text = f'  {span} oct' if span >= 1 else ''
    if best is None:
        return 'run ' + direction_of(pitches) + span_text
    _, root, name = best
    return f'{NOTE_NAMES[root]} {name} {direction_of(pitches)}{span_text}'


def compute(window_n, tol_pct, rest_sec):
    """Statistics over the last window_n gaps (gaps across a rest are excluded).  Returns None when there is nothing to measure."""
    onsets = list(G.onsets)[-(window_n + 1):]
    gaps = [g for g in gaps_of(onsets, rest_sec) if not g[3]]
    if len(gaps) < 2:
        return None
    secs = [g[0] for g in gaps]
    median = statistics.median(secs)
    lo, hi = median * (1 - tol_pct / 100), median * (1 + tol_pct / 100)
    even = [lo <= s <= hi for s in secs]
    worst = max(gaps, key=lambda g: abs(g[0] - median) / median)
    nps = 1 / median
    run_start = next((i for i in range(len(onsets) - 1, 0, -1) if onsets[i].t - onsets[i - 1].t > rest_sec), 0)
    run = onsets[run_start:]
    run_pitches = [p for o in run for p in o.notes]
    return {'nps': nps, 'median': median, 'even_pct': 100 * sum(even) / len(even), 'gaps': gaps, 'lo': lo, 'hi': hi,
            'worst_pct': 100 * (worst[0] - median) / median, 'worst_names': f'{note_name(worst[1].notes[0])}\u2192{note_name(worst[2].notes[0])}',
            'run_len': len(run), 'run_span': (max(run_pitches) - min(run_pitches)) if run_pitches else 0, 'detected': detect(run[-24:])}


def reset(window):
    G.onsets.clear()
    G.fastest, G.stats = 0.0, None
    refresh_tiles(window)


def demo_tick(window, now, params):
    """Scale runs, an arpeggio and a trill with a few deliberate hiccups; a rest between runs"""
    rest_sec = params[2]
    if now < G.demo_next_t:
        return
    if not G.demo_seq:
        root = random.choice((60, 62, 65, 67))
        kind = random.random()
        if kind < 0.5:
            scale = [root + i for i in (0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24)]
            G.demo_seq = scale + scale[-2::-1]
        elif kind < 0.8:
            arp = [root + i for i in (0, 4, 7, 12, 16, 19, 24)]
            G.demo_seq = arp + arp[-2::-1]
        else:
            G.demo_seq = [root, root + 1] * 10
        G.demo_gap = random.uniform(0.09, 0.16)
        G.demo_next_t = now + rest_sec + 0.5
        return
    while G.demo_seq and G.demo_next_t <= now:                 # notes are stamped with their scheduled time, so gaps stay exact between 100 ms ticks
        note = G.demo_seq.pop(0)
        handle_note(window, G.demo_next_t, note, random.randint(50, 100), params)
        wobble = random.choice((1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.55, 0.6))
        G.demo_next_t += G.demo_gap * wobble * random.uniform(0.94, 1.06)


def handle_note(window, t, note, vel, params):
    """params = (window_n, tol_pct, rest_sec, chord_sec, dial_max) as read from the controls by the main loop"""
    if add_note(t, note, vel, params[3]):
        recalc(window, params)


def recalc(window, params):
    window_n, tol, rest_sec, chord_sec, dial_max = params
    stats = compute(window_n, tol, rest_sec)
    if stats is not None:
        G.stats = stats
        G.fastest = max(G.fastest, stats['nps'])
    refresh_tiles(window, dial_max)


# ---------- Display ----------
def paint(window, name, text, color, sub=''):
    """Show a tile: big number (background eases toward color) with sub text underneath"""
    if color is None:
        window[KT_TILE(name)].update('-', background_color=C_TILE_NEUTRAL, text_color=C_AXIS_TEXT)
        window[KT_TILE_SUB(name)].update(sub)
        G.tile_target.pop(name, None)
        G.tile_now.pop(name, None)
        return
    G.tile_target[name] = color
    if name not in G.tile_now:
        G.tile_now[name] = color
        window[KT_TILE(name)].update(text, background_color=hexcolor(color), text_color=C_ON_TILE)
    else:
        window[KT_TILE(name)].update(text, text_color=C_ON_TILE)
    window[KT_TILE_SUB(name)].update(sub)


def ease_tiles(window):
    """Called every timer tick: move each tile background part of the way toward its target color"""
    for key, target in G.tile_target.items():
        cur = G.tile_now.get(key, target)
        if cur == target:
            continue
        new = target if all(abs(c - t) < 1.5 for c, t in zip(cur, target)) else mix(cur, target, TILE_EASE)
        G.tile_now[key] = new
        window[KT_TILE(key)].update(background_color=hexcolor(new))


def refresh_tiles(window, dial_max=16):
    s = G.stats
    if s is None:
        for name in TILES:
            paint(window, name, '', None, '')
        window[KT_TILE(T_DETECT)].update('-', background_color=C_TILE_NEUTRAL, text_color=C_AXIS_TEXT)
        return
    speed_rgb = gradient(SPEED_STOPS, s['nps'] / dial_max)
    even_rgb = gradient(EVEN_STOPS, s['even_pct'])
    paint(window, T_NPS, f"{s['nps']:.1f}", speed_rgb, f"{len(s['gaps'])} gaps measured")
    paint(window, T_GAP, f"{s['median'] * 1000:.0f}", speed_rgb, 'ms between notes')
    paint(window, T_EVEN, f"{s['even_pct']:.0f}%", even_rgb, 'gaps inside the band')
    worst_rgb = rgb(C_LONG) if s['worst_pct'] > 0 else rgb(C_SHORT)
    paint(window, T_WORST, f"{s['worst_pct']:+.0f}%", worst_rgb, s['worst_names'] + ('  too long' if s['worst_pct'] > 0 else '  too short'))
    paint(window, T_RUN, str(s['run_len']), rgb(C_TILE_NEUTRAL), f"notes  ·  span {s['run_span'] // 12} oct {s['run_span'] % 12} st")
    paint(window, T_FASTEST, f'{G.fastest:.1f}', gradient(SPEED_STOPS, G.fastest / dial_max), 'notes / sec this session')
    window[KT_TILE(T_DETECT)].update(s['detected'] or '-', background_color=C_TILE_NEUTRAL, text_color=C_DETECT if s['detected'] else C_AXIS_TEXT)


def text_px(window, text, font):
    """Pixel width of text in a font at the current screen dpi (cached)"""
    if (text, font) not in G.text_px:
        G.text_px[(text, font)] = tkfont.Font(root=window.TKroot, font=font).measure(text)
    return G.text_px[(text, font)]


def redraw_dial(graph, dial_max):
    w, h = graph.get_size()
    if not w or w < 40 or h < 40:
        return
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, 0), (w, h))
    graph.erase()
    s = G.stats
    cx, cy = w / 2, h * 0.30
    r = min(w / 2, h * 0.62) - 24 * G.scale
    thick = max(8, r * 0.14)
    box = ((cx - r, cy + r), (cx + r, cy - r))
    graph.draw_arc(*box, extent=180, start_angle=0, style='arc', arc_color=C_DIAL, line_width=thick)
    if s:
        frac = max(0.0, min(1.0, s['nps'] / dial_max))
        color = hexcolor(gradient(SPEED_STOPS, frac))
        if frac > 0.002:
            graph.draw_arc(*box, extent=-180 * frac, start_angle=180, style='arc', arc_color=color, line_width=thick)
    step = 1 if dial_max <= 12 else 2
    for n in range(0, dial_max + 1, step):
        a = math.pi * (1 - n / dial_max)
        x0, y0 = cx + (r - thick / 2 - 2) * math.cos(a), cy + (r - thick / 2 - 2) * math.sin(a)
        x1, y1 = cx + (r + thick / 2 + 2) * math.cos(a), cy + (r + thick / 2 + 2) * math.sin(a)
        graph.draw_line((x0, y0), (x1, y1), color=C_DIAL_TICK if n % (2 * step) == 0 else C_GRID, width=2)
        if n % (2 * step) == 0:
            graph.draw_text(str(n), (cx + (r + thick / 2 + 14 * G.scale) * math.cos(a), cy + (r + thick / 2 + 14 * G.scale) * math.sin(a)), color=C_AXIS_TEXT, font=FONT_TICK)
    if s:
        a = math.pi * (1 - min(1.0, s['nps'] / dial_max))
        graph.draw_line((cx, cy), (cx + (r - thick) * math.cos(a), cy + (r - thick) * math.sin(a)), color='#FFFFFF', width=3)
        graph.draw_circle((cx, cy), 6 * G.scale, fill_color='#FFFFFF', line_color='#FFFFFF')
        graph.draw_text(f"{s['nps']:.1f}", (cx, cy + r * 0.42), color='#FFFFFF', font=FONT_DIAL)
        graph.draw_text('notes / sec', (cx, cy + r * 0.42 - FONT_DIAL[1] * 1.3 * G.scale), color=C_AXIS_TEXT, font=FONT_TICK)
        bpm = s['nps'] * 60
        tempo_text = f'16ths {bpm / 4:.0f} bpm  ·  triplet 8ths {bpm / 3:.0f}  ·  8ths {bpm / 2:.0f}'
        graph.draw_text(tempo_text, (cx, cy - FONT_DIAL_SUB[1] * 1.5 * G.scale), color=C_AXIS_TEXT, font=FONT_DIAL_SUB)
    else:
        graph.draw_text('play a run', (cx, cy + r * 0.42), color=C_AXIS_TEXT, font=FONT_DIAL_SUB)
    if G.paused:
        graph.draw_text('❚❚  PAUSED   (F9 / Resume)', (cx, h - FONT_UI[1] * 1.5 * G.scale), color=C_PAUSED, font=FONT_UI)


def redraw_strip(graph, window_n, rest_sec):
    window = graph.ParentForm
    w, h = graph.get_size()
    if not w or w < 40 or h < 40:
        return
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, 0), (w, h))
    graph.erase()
    s = G.stats
    onsets = list(G.onsets)[-(window_n + 1):]
    gaps = gaps_of(onsets, rest_sec)
    left, right, bottom, top = 46 * G.scale, w - 12 * G.scale, 22 * G.scale, h - 26 * G.scale
    graph.draw_line((left, bottom), (right, bottom), color=C_GRID)
    graph.draw_text('gap before each note (ms)  ·  newest at the right  ·  band = median ± tolerance', (left, h - 12 * G.scale), color=C_AXIS_TEXT, font=FONT_TICK,
                    text_location=sg.TEXT_LOCATION_LEFT)
    if not gaps or s is None:
        return
    max_ms = max(s['hi'] * 1000 * 1.6, max(g[0] for g in gaps if not g[3]) * 1000 * 1.15) if any(not g[3] for g in gaps) else s['hi'] * 2000
    y_of = lambda ms: bottom + (top - bottom) * min(1.0, ms / max_ms)
    slot = (right - left) / window_n
    graph.draw_rectangle((left, y_of(s['hi'] * 1000)), (right, y_of(s['lo'] * 1000)), fill_color=C_BAND, line_color=C_BAND)
    graph.draw_line((left, y_of(s['median'] * 1000)), (right, y_of(s['median'] * 1000)), color=C_MEDIAN, width=1)
    graph.draw_text(f"{s['median'] * 1000:.0f}", (left - 6 * G.scale, y_of(s['median'] * 1000)), color=C_MEDIAN, font=FONT_TICK, text_location=sg.TEXT_LOCATION_RIGHT)
    for ms in (50, 100, 150, 200, 300, 400, 500, 750, 1000):
        if ms < max_ms:
            graph.draw_line((left, y_of(ms)), (right, y_of(ms)), color=C_GRID)
            if abs(y_of(ms) - y_of(s['median'] * 1000)) > FONT_TICK[1] * 1.6 * G.scale:            # keep clear of the median label
                graph.draw_text(str(ms), (left - 6 * G.scale, y_of(ms)), color=C_AXIS_TEXT, font=FONT_TICK, text_location=sg.TEXT_LOCATION_RIGHT)
    x = right - slot * len(gaps)
    for gap_sec, a, b, is_rest in gaps:
        xc = x + slot / 2
        if is_rest:
            graph.draw_line((xc, bottom), (xc, top), color=C_REST, width=1)
            graph.draw_text('rest', (xc, top - 8 * G.scale), color=C_REST, font=FONT_TICK)
        else:
            ms = gap_sec * 1000
            color = C_EVEN if s['lo'] <= gap_sec <= s['hi'] else C_LONG if gap_sec > s['hi'] else C_SHORT
            graph.draw_rectangle((x + slot * 0.18, y_of(ms)), (x + slot * 0.82, bottom), fill_color=color, line_color=color)
            if color != C_EVEN and slot >= FONT_NOTE[1] * 1.3 * G.scale:                            # which two notes: written upward beside the bar top
                label = f'{note_name(a.notes[0])}\u2192{note_name(b.notes[0])}'
                half = text_px(window, label, FONT_NOTE) / 2 + 6 * G.scale
                outside = y_of(ms) + 2 * half < top
                graph.draw_text(label, (xc, y_of(ms) + half if outside else y_of(ms) - half), color=color if outside else C_ON_TILE, font=FONT_NOTE, angle=90)
        x += slot


# ---------- Touch picker ----------
def touch_pick(title, choices, current, steps):
    """Big picker for a touch screen.  steps=None: one button per choice (tap = choose).  Otherwise a slider and +/- buttons step through choices; OK/Cancel"""
    idx = choices.index(current) if current in choices else 0
    if steps is None:
        per_row = 5
        rows = [[sg.Button(str(c), key=KT_PICK(c), size=(6, 2), font=FONT_PICK) for c in choices[i:i + per_row]] for i in range(0, len(choices), per_row)]
        layout = [[sg.Text(title, font=FONT_PICK)]] + rows + [[sg.Button('Cancel', key=K_PICK_CANCEL, size=(8, 2), font=FONT_PICK)]]
    else:
        slider = sg.Slider((0, len(choices) - 1), default_value=idx, orientation='h', size=(40, 36), enable_events=True, disable_number_display=True, key=K_PICK_SLIDER)
        layout = [[sg.Text(title, font=FONT_PICK)], [sg.Text(str(current), key=K_PICK_VAL, font=FONT_PICK_VALUE, size=(6, 1), justification='c')],
                  [sg.Text(str(choices[0]), font=FONT_PICK), slider, sg.Text(str(choices[-1]), font=FONT_PICK)],
                  [sg.Button(label, key=KT_STEP(delta), size=(5, 2), font=FONT_PICK) for delta, label in steps],
                  [sg.Button('OK', key=K_PICK_OK, size=(8, 2), font=FONT_PICK, button_color=(C_ON_TILE, C_STATUS_OK)),
                   sg.Button('Cancel', key=K_PICK_CANCEL, size=(8, 2), font=FONT_PICK)]]
    win = sg.Window(title, layout, modal=True, keep_on_top=True, finalize=True, element_justification='c', margins=(20, 16))
    win.bind('<Escape>', K_PICK_CANCEL)
    if steps is not None:
        win[K_PICK_SLIDER].TKScale.configure(sliderlength=int(50 * G.scale))                       # fat handle for a finger
    result = None
    while True:
        event, _ = win.read()
        if event in (sg.WIN_CLOSED, K_PICK_CANCEL):
            break
        if event == K_PICK_OK:
            result = choices[idx]
            break
        if isinstance(event, tuple) and event[0] == K_PICK:
            result = event[1]
            break
        if event == K_PICK_SLIDER:
            idx = int(float(win[K_PICK_SLIDER].TKScale.get()))
            win[K_PICK_VAL].update(str(choices[idx]))
        if isinstance(event, tuple) and event[0] == K_STEP:
            idx = max(0, min(len(choices) - 1, idx + event[1]))
            win[K_PICK_VAL].update(str(choices[idx]))
            win[K_PICK_SLIDER].update(idx)
    win.close()
    return result


PICKERS = {K_WINDOW: ('Gaps measured', WINDOW_CHOICES, STEPS_1_10),                  # key: (picker title, allowed values, +/- steps or None for a button grid)
           K_TOL: ('Tolerance (% of the median gap)', TOL_CHOICES, STEPS_1_4),
           K_CHORD_MS: ('Chord window (ms)', CHORD_MS_CHOICES, None),
           K_REST: ('Rest gap (seconds)', REST_CHOICES, None),
           K_DIAL_MAX: ('Dial maximum (notes / sec)', DIAL_MAX_CHOICES, None),
           K_TEXT_SIZE: ('Text size', TEXT_SIZE_CHOICES, None)}


def edit_value(window, key, values):
    """Open the touch picker for one setting and, if a new value was chosen, put it in the value box and recompute"""
    title, choices, steps = PICKERS[key]
    current = next((c for c in choices if str(c) == str(values.get(key))), choices[0])
    chosen = touch_pick(title, choices, current, steps)
    if chosen is not None and chosen != current:
        window[key].update(str(chosen))
        window.write_event_value(K_REBUILD if key == K_TEXT_SIZE else K_RECALC, key)


def save_settings(window, values):
    """Write every element that was created with setting= to the user settings file (skips timer / thread-event keys that are not elements)"""
    window.settings_save({k: v for k, v in values.items() if k in window.key_dict})


def set_fullscreen(window, on):
    G.fullscreen = on
    window.TKroot.attributes('-fullscreen', on)
    window[K_FULL].update('Windowed' if on else 'Full', button_color=(C_ON_TILE, C_PAUSED) if on else sg.theme_button_color())
    sg.user_settings_set_entry(K_FULLSCREEN, on)


def show_controls(window, on):
    window[K_CONTROLS].update(visible=on)
    window[K_EXTRAS].update(visible=on)
    window[K_TOGGLE_CONTROLS].update('▲' if on else '▼')
    sg.user_settings_set_entry(K_CONTROLS_HIDDEN, not on)


def set_paused(window, on, now):
    if on == G.paused:
        return
    G.paused = on
    if on:
        G.pause_t = now
        window[K_PAUSE].update('Resume', button_color=(C_ON_TILE, C_PAUSED))
    else:
        shift = now - G.pause_t
        for o in G.onsets:
            o.t += shift
        G.demo_next_t += shift
        window[K_PAUSE].update('Pause', button_color=sg.theme_button_color())


# ---------- Window ----------
def tile(name, color, width=6):
    """Label, big number with colored background, sub text - stacked"""
    col = [[sg.Text(name, key=KT_TILE_LABEL(name), font=FONT_LABEL, text_color=color, pad=(0, (6, 0)))],
           [sg.Text('-', key=KT_TILE(name), font=FONT_BIG, text_color=C_AXIS_TEXT, size=(width, 1), justification='c', background_color=C_TILE_NEUTRAL, pad=(0, 0))],
           [sg.Text('', key=KT_TILE_SUB(name), font=FONT_LABEL, text_color=C_AXIS_TEXT, size=(26, 1), pad=(0, 0))]]
    return sg.Column(col, pad=(0, 0))


def build_window(ports, port):
    sg.set_options(font=FONT_UI)
    P = ((10, 4), 0)
    TAP_TT = '  (tap the value or the pencil for a big picker)'

    def field(default, key, width, tooltip):
        return [sg.Input(str(default), key=key, size=(width, 1), readonly=True, setting=default, justification='c', tooltip=tooltip + TAP_TT),
                sg.Text('\u270E', key=KT_EDIT(key), enable_events=True, text_color=C_EDIT, pad=((0, 4), 0), tooltip='Change: ' + tooltip)]

    top = [sg.Text('MIDI in'), sg.Combo(ports, default_value=port, key=K_PORT, size=(20, 1), readonly=True, enable_events=True), sg.Button('Refresh', key=K_REFRESH),
           sg.Text('Text', pad=P), *field('100%', K_TEXT_SIZE, 5, 'Size of all text in the program'),
           sg.Push(),
           sg.Button('Full', key=K_FULL, size=(9, 1), tooltip='Full screen on / off (F11): whole screen, no title bar'),
           sg.Button('Pause', key=K_PAUSE, size=(7, 1)), sg.Button('Reset', key=K_RESET), sg.Button('Exit', key=K_EXIT)]
    opts = [sg.Text('Window'), *field(24, K_WINDOW, 3, TT_WINDOW),
            sg.Text('Tolerance %', pad=P), *field(15, K_TOL, 3, TT_TOL),
            sg.Text('Chord ms', pad=P), *field(30, K_CHORD_MS, 3, TT_CHORD),
            sg.Text('Rest gap s', pad=P), *field(0.6, K_REST, 4, TT_REST),
            sg.Text('Dial max', pad=P), *field(16, K_DIAL_MAX, 3, TT_DIAL),
            sg.Text('  ● even', text_color=C_EVEN, pad=((30, 0), 0)), sg.Text('● too long', text_color=C_LONG), sg.Text('● too short', text_color=C_SHORT)]
    tiles = [[tile(T_NPS, C_EVEN)], [tile(T_GAP, C_AXIS_TEXT)], [tile(T_EVEN, C_EVEN)], [tile(T_WORST, C_LONG)], [tile(T_RUN, C_AXIS_TEXT)], [tile(T_FASTEST, C_AXIS_TEXT)],
             [tile(T_DETECT, C_DETECT, width=24)]]
    extras = [[sg.Text('', key=K_STATUS, font=FONT_LABEL, size=(28, 2), pad=(0, (10, 0)))],
              [sg.Checkbox('Demo runs', key=K_DEMO, enable_events=True, font=FONT_LABEL, pad=(0, (6, 0)))]]
    tiles += [[sg.pin(sg.Column(extras, key=K_EXTRAS, pad=(0, 0)))],
              [sg.Push(), sg.Button('\u25B2', key=K_TOGGLE_CONTROLS, font=FONT_LABEL, tooltip='Hide / show the control rows (F10)')]]
    side = sg.Column(tiles, vertical_alignment='top', pad=((10, 0), 0))
    controls = sg.pin(sg.Column([top, opts], key=K_CONTROLS, expand_x=True, pad=(0, 0)), expand_x=True)
    left = sg.Column([[sg.Graph((700, 360), (0, 0), (1, 1), key=K_DIAL, background_color=C_BG, expand_x=True, expand_y=True, pad=(0, (6, 4)))],
                      [sg.Graph((700, 240), (0, 0), (1, 1), key=K_STRIP, background_color=C_BG, expand_x=True, expand_y=True, pad=(0, (4, 0)))]],
                     expand_x=True, expand_y=True, pad=(0, 0))
    layout = [[controls], [left, side]]

    window = sg.Window(APP_TITLE, layout, resizable=True, finalize=True, margins=(8, 6), auto_save_location=True, enable_close_attempted_event=True)
    G.window = window
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)
    G.text_px.clear()
    sw, sh = sg.Window.get_screen_size()
    window.refresh()
    cw, ch = window.size
    nw, nh = max(cw, int(sw * WINDOW_FRACTION)), max(ch, int(sh * WINDOW_FRACTION))
    if (nw, nh) != (cw, ch):
        window.size = (nw, nh)
        window.move((sw - nw) // 2, max(0, (sh - nh) // 2 - 20))
    window.bind('<Escape>', K_KEY_ESC)
    window.bind('<F11>', K_KEY_F11)
    window.bind('<Home>', K_KEY_HOME)
    window.bind('<F10>', K_KEY_F10)
    window.bind('<F9>', K_KEY_F9)
    for key in PICKERS:
        window[key].bind('<Button-1>', TAP)
        window[key].widget.configure(readonlybackground=sg.theme_input_background_color())
    if sg.user_settings_get_entry(K_FULLSCREEN, False):
        set_fullscreen(window, True)
    if sg.user_settings_get_entry(K_CONTROLS_HIDDEN, False):
        show_controls(window, False)
    window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)
    if G.paused:
        window[K_PAUSE].update('Resume', button_color=(C_ON_TILE, C_PAUSED))
    G.tile_now.clear()
    G.tile_target.clear()
    refresh_tiles(window)
    window.timer_start(100)
    return window


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    sg.theme('DarkGrey13')
    sg.set_options(font=FONT_UI, dpi_awareness=True, icon=ICON)
    set_fonts(sg.user_settings_get_entry(K_TEXT_SIZE, '100%'))
    ports = midi_ports()
    saved_port = sg.user_settings_get_entry(K_PORT, '')
    port = saved_port if saved_port in ports else (ports[0] if ports else '')
    open_port(port)
    window = build_window(ports, port)
    if '--demo' in sys.argv:                                   # test hooks:  --demo starts the demo,  --autoclose N exits after N seconds
        window[K_DEMO].update(True)
    auto_close = time.monotonic() + float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_EXIT, K_KEY_ESC) or (auto_close and time.monotonic() > auto_close):
            save_settings(window, values)
            break
        window_n, tol, dial_max = ival(values, K_WINDOW, 24), fval(values, K_TOL, 15), ival(values, K_DIAL_MAX, 16)
        chord_sec, rest_sec = ival(values, K_CHORD_MS, 30) / 1000, fval(values, K_REST, 0.6)
        params = (window_n, tol, rest_sec, chord_sec, dial_max)
        now = time.monotonic()
        if event == sg.EVENT_TIMER:
            if values[K_DEMO] and not G.paused:
                demo_tick(window, now, params)
            ease_tiles(window)
            redraw_dial(window[K_DIAL], dial_max)
            redraw_strip(window[K_STRIP], window_n, rest_sec)
        elif event == K_MIDI_NOTE:
            t, note, vel = values[K_MIDI_NOTE]
            if not G.paused:
                handle_note(window, t, note, vel, params)
        elif event == K_RECALC:
            recalc(window, params)
        elif event in (K_PAUSE, K_KEY_F9):
            set_paused(window, not G.paused, now)
        elif event == K_REBUILD:
            save_settings(window, values)
            set_fonts(values[K_TEXT_SIZE])
            window.timer_stop_all()
            window.close()
            window = build_window(ports, values[K_PORT])
            refresh_tiles(window, dial_max)
        elif isinstance(event, str) and event.endswith(TAP) and event[:-len(TAP)] in PICKERS:
            edit_value(window, event[:-len(TAP)], values)
        elif isinstance(event, tuple) and event[0] == K_EDIT:
            edit_value(window, event[1], values)
        elif event == K_PORT:
            open_port(values[K_PORT])
            sg.user_settings_set_entry(K_PORT, values[K_PORT])
        elif event == K_REFRESH:
            ports = midi_ports()
            port = values[K_PORT] if values[K_PORT] in ports else (ports[0] if ports else '')
            window[K_PORT].update(values=ports, value=port)
            open_port(port)
        elif event in (K_RESET, K_KEY_HOME):
            reset(window)
        elif event in (K_FULL, K_KEY_F11):
            set_fullscreen(window, not G.fullscreen)
        elif event in (K_TOGGLE_CONTROLS, K_KEY_F10):
            show_controls(window, not window[K_CONTROLS].visible)

    window.timer_stop_all()
    close_port()
    window.close()


if __name__ == '__main__':
    main()
