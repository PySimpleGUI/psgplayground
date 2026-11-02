"""
Ripples  (ripples.pyw)  -  an ambient visualizer: no numbers, no judgement, every note you play becomes an expanding ring.

WHERE (Style):  keyboard = left to right by pitch between the LOW and HIGH notes (set them to the range of the piece and the
                whole width is used), spiral = around a circle by note name with one turn per octave, rain = anywhere.
SPEED (how fast a ring grows):  fixed = the Speed value;  velocity = harder key = faster (0.4x .. 1.6x Speed);
                pitch = higher note = faster (low notes spread slowly like a big stone);  random = 0.4x .. 1.6x at random.
COLOUR (Palette):
  zones    the keyboard is cut into four ranges, each with its own colour (ZONES row: three top notes and four colours); with
           "Shade by pitch" on, a zone's colour goes from a dark shade at the bottom of the zone to a light tint at the top
  pitch    one hue per note name, laid out around the circle of fifths so neighbouring keys get clearly different colours
  octave   one hue per octave, shaded by pitch inside the octave
  heat     loudness on the 1-10 scale of the Piano Dynamics Monitor: 1-2 pp blue, 3-4 p green, 5-6 mf yellow, 7-8 f orange, 9-10 ff red
  mono     one colour (zone 1's) shaded dark .. light over the whole range
Ring thickness and life come from loudness (LOUDNESS row: Vel@1 / Vel@10 calibrate the 1-10 scale to your touch, as in the Piano
Dynamics Monitor); held notes keep pulsing; the sustain pedal makes rings linger; held notes are joined by
faint threads.  Tapping the picture cycles the palette.  F10 hides the controls and F11 goes full screen for a clean canvas.

TOUCH: every setting is a read-only value box followed by a small pencil mark; tapping the box or the pencil opens a big picker.
TEXT SIZE: one multiplier for every font; changing it rebuilds the window in place (the MIDI connection is kept).
Keys:  ESC = exit    F9 = pause / resume the animation    F11 = fullscreen    F10 = hide / show controls    HOME = clear
Demo checkbox plays slow pedalled arpeggios by itself across the LOW .. HIGH range.
Requires:  pip install PySimpleGUI mido python-rtmidi
Settings persist in SETTINGS_FILE (ripples.json in the PySimpleGUI settings folder) via Window.settings_save() at exit;
the MIDI port, fullscreen and hidden-controls state are saved as they change.  "Demo" is deliberately not saved.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import colorsys
import math
import random
import sys
import time

import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'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'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_TITLE = 'Ripples'
SETTINGS_FILE = 'ripples.json'

# ---------- Keys ----------
K_CANVAS = '-CANVAS-'
K_PORT = '-PORT-'
K_REFRESH = '-REFRESH-'
K_LOW = '-LOW-'
K_HIGH = '-HIGH-'
K_PALETTE = '-PALETTE-'
K_STYLE = '-STYLE-'
K_SPEED_MODE = '-SPEED MODE-'
K_SPEED = '-SPEED-'
K_ZONE_TOP = '-ZONE TOP-'
KT_ZONE_TOP = lambda n: f'-ZONE TOP {n}-'              # highest note of zone n (1..3); zone 4 runs to HIGH
K_ZONE_COLOR = '-ZONE COLOR-'
KT_ZONE_COLOR = lambda n: f'-ZONE COLOR {n}-'          # colour name of zone n (1..4)
K_SHADE = '-SHADE-'
K_VEL_MIN = '-VEL MIN-'
K_VEL_MAX = '-VEL MAX-'
K_TEXT_SIZE = '-TEXT SIZE-'
K_REBUILD = '-REBUILD-'
K_RECALC = '-RECALC-'
K_DEMO = '-DEMO-'
K_CLEAR = '-CLEAR-'
K_PAUSE = '-PAUSE-'
K_FULL = '-FULL-'
K_EXIT = '-EXIT-'
K_STATUS = '-STATUS-'
K_PICK_VAL = '-PICK VAL-'
K_PICK_OK = '-PICK OK-'
K_PICK_CANCEL = '-PICK CANCEL-'
K_PICK_SLIDER = '-PICK SLIDER-'
K_EDIT = '-EDIT-'
KT_EDIT = lambda key: (K_EDIT, key)
K_PICK = '-PICK-'
KT_PICK = lambda choice: (K_PICK, choice)
K_STEP = '-STEP-'
KT_STEP = lambda delta: (K_STEP, delta)
TAP = ' TAP'
K_MIDI_NOTE = '-MIDI NOTE-'            # from the MIDI callback thread: (time, kind, note, value)  kind = 'on' | 'off' | 'pedal'
K_KEY_ESC = '-KEY ESC-'
K_KEY_F9 = '-KEY F9-'
K_KEY_F10 = '-KEY F10-'
K_KEY_F11 = '-KEY F11-'
K_KEY_HOME = '-KEY HOME-'
K_FULLSCREEN = '-FULLSCREEN-'
K_CONTROLS = '-CONTROLS-'
K_CONTROLS_HIDDEN = '-CONTROLS HIDDEN-'
K_TOGGLE_CONTROLS = '-TOGGLE CONTROLS-'

# ---------- Colors ----------
C_BG = '#0B0D12'
C_THREAD = '#2A3350'
C_AXIS_TEXT = '#9AA6B2'
C_STATUS_OK = '#69F0AE'
C_STATUS_BAD = '#FF8A65'
C_PAUSED = '#FFB300'
C_EDIT = '#4DD0E1'
C_ON_TILE = '#000000'
COLORS = {'red': '#FF3B30', 'orange': '#FF8A00', 'yellow': '#FFD600', 'lime': '#9CFF57', 'green': '#00E676', 'teal': '#2DD4BF', 'cyan': '#00E5FF',
          'sky': '#40C4FF', 'blue': '#448AFF', 'indigo': '#7C4DFF', 'violet': '#B388FF', 'magenta': '#FF4FC3', 'pink': '#FF80AB', 'white': '#F5F5F5'}
COLOR_CHOICES = list(COLORS)
ZONE_DEFAULT_TOPS = ('E2', 'C4', 'C6')
ZONE_DEFAULT_COLORS = ('blue', 'teal', 'yellow', 'red')

FONT_FAMILY = 'Segoe UI'
BASE_FONTS = {'FONT_UI': 12, 'FONT_LABEL': 11, 'FONT_PICK': 20, 'FONT_PICK_VALUE': 48}
TEXT_SIZE_CHOICES = ['70%', '85%', '100%', '115%', '130%']


def set_fonts(text_size):
    try:
        mult = int(str(text_size).rstrip('%')) / 100
    except ValueError:
        mult = 1.0
    for name, size in BASE_FONTS.items():
        globals()[name] = (FONT_FAMILY, max(7, round(size * mult)), 'bold')


set_fonts('100%')
WINDOW_FRACTION = 0.85
PALETTES = ['zones', 'pitch', 'octave', 'heat', 'mono']
STYLES = ['keyboard', 'spiral', 'rain']
SPEED_MODES = ['fixed', 'velocity', 'pitch', 'random']
SPEED_CHOICES = list(range(20, 401, 10))       # px per second of ring growth at 96 dpi
STEPS_SPEED = [(-5, '-50'), (-1, '-10'), (1, '+10'), (5, '+50')]
STEPS_NOTE = [(-12, '-oct'), (-1, '-1'), (1, '+1'), (12, '+oct')]
BASE_LIFE = 2.2                        # seconds a ring lives (longer with velocity and pedal)
PULSE_EVERY = 0.55                     # a held note spawns a smaller ring this often
NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
TT_LOW = 'Lowest note of the keyboard layout: it lands at the left edge'
TT_HIGH = 'Highest note of the keyboard layout: it lands at the right edge'
TT_PALETTE = 'Ring colour: zones (your colours per range), pitch (circle of fifths hues), octave, heat (loudness 1-10), mono'
TT_VEL_MIN = 'MIDI velocity that counts as loudness 1 (raise it so your softest notes read 1)'
TT_VEL_MAX = 'MIDI velocity that counts as loudness 10 (lower it if your piano never reaches 127)'
LEVELS = [(1, 2, '#448AFF', 'pp'), (3, 4, '#00E676', 'p'), (5, 6, '#FFEA00', 'mf'), (7, 8, '#FF9100', 'f'), (9, 10, '#FF1744', 'ff')]
VEL_CHOICES = list(range(1, 128))
STEPS_1_10 = [(-10, '-10'), (-1, '-1'), (1, '+1'), (10, '+10')]
TT_STYLE = 'Where a note lands: keyboard = by pitch between Low and High, spiral = by note name around a circle, rain = anywhere'
TT_SPEED_MODE = 'What sets how fast a ring grows: fixed = the Speed value, velocity = harder is faster, pitch = higher is faster, random'
TT_SPEED = 'Ring growth in pixels per second (the base value for the velocity / pitch / random modes)'
TT_ZONE_TOP = 'Highest note of this colour zone (the next zone starts one note above)'
TT_ZONE_COLOR = 'Colour of this zone'


def note_name(n):
    return f'{NOTE_NAMES[n % 12]}{n // 12 - 1}'


NOTE_LIST = [note_name(n) for n in range(21, 109)]         # A0 .. C8
NOTE_NUM = {name: n for n, name in zip(range(21, 109), NOTE_LIST)}


class Ring:
    __slots__ = ('x', 'y', 'born', 'life', 'color', 'vel', 'speed', 'fig', 'dot')

    def __init__(self, x, y, born, life, color, vel, speed):
        self.x, self.y, self.born, self.life, self.color, self.vel, self.speed, self.fig, self.dot = x, y, born, life, color, vel, speed, None, None


class Opts:
    """Everything the drawing code needs, read from the controls once per event"""
    def __init__(self, values):
        self.palette = values.get(K_PALETTE) if values.get(K_PALETTE) in PALETTES else PALETTES[0]
        self.style = values.get(K_STYLE) if values.get(K_STYLE) in STYLES else STYLES[0]
        self.speed_mode = values.get(K_SPEED_MODE) if values.get(K_SPEED_MODE) in SPEED_MODES else SPEED_MODES[0]
        self.speed = ival(values, K_SPEED, 90)
        self.lo = NOTE_NUM.get(values.get(K_LOW), 21)
        self.hi = max(self.lo + 12, NOTE_NUM.get(values.get(K_HIGH), 108))
        self.tops = sorted(NOTE_NUM.get(values.get(KT_ZONE_TOP(n)), NOTE_NUM[ZONE_DEFAULT_TOPS[n - 1]]) for n in (1, 2, 3))
        self.colors = [COLORS.get(values.get(KT_ZONE_COLOR(n)), COLORS[ZONE_DEFAULT_COLORS[n - 1]]) for n in (1, 2, 3, 4)]
        self.shade = bool(values.get(K_SHADE, True))
        self.vel_min = ival(values, K_VEL_MIN, 1)
        self.vel_max = max(self.vel_min + 9, ival(values, K_VEL_MAX, 127))

    def loudness(self, vel):
        """MIDI velocity -> 1..10 using the Vel@1 / Vel@10 calibration"""
        return max(1.0, min(10.0, 1 + 9 * (vel - self.vel_min) / (self.vel_max - self.vel_min)))


class G:                                # program-wide state
    window = None
    port = None
    status = ''
    status_ok = False
    scale = 1.0
    fullscreen = False
    paused = False
    pause_t = 0.0
    rings = []
    held = {}                           # pitch -> [x, y, last pulse time, velocity]
    pedal_down = False
    threads = []
    demo_next_t = 0.0
    demo_seq = []
    demo_release = []


# ---------- Colour helpers ----------
def hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))


def blend(c1, c2, f):
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return '#%02x%02x%02x' % (int(r1 + (r2 - r1) * f), int(g1 + (g2 - g1) * f), int(b1 + (b2 - b1) * f))


def level_color(value):
    """Smooth gradient colour for a 1-10 loudness value through the five level colours"""
    stops = [((lo + hi) / 2, color) for lo, hi, color, name in LEVELS]
    if value <= stops[0][0]:
        return stops[0][1]
    for (v0, c0), (v1, c1) in zip(stops, stops[1:]):
        if value <= v1:
            return blend(c0, c1, (value - v0) / (v1 - v0))
    return stops[-1][1]


def shade(color, f):
    """f = 0 -> a dark shade of color, 0.5 -> color itself, 1 -> a light tint"""
    f = max(0.0, min(1.0, f))
    return blend(blend(color, '#000000', 0.42), color, f * 2) if f < 0.5 else blend(color, '#FFFFFF', (f - 0.5) * 1.4)


def zone_of(pitch, opts):
    """(zone index 0..3, position 0..1 inside the zone) for a pitch"""
    bounds = [opts.lo - 1] + opts.tops + [opts.hi]
    for i in range(4):
        if pitch <= bounds[i + 1] or i == 3:
            lo, hi = bounds[i] + 1, max(bounds[i] + 2, bounds[i + 1])
            return i, max(0.0, min(1.0, (pitch - lo) / (hi - lo)))
    return 3, 1.0


def ring_color(opts, pitch, loud):
    if opts.palette == 'zones':
        zone, f = zone_of(pitch, opts)
        return shade(opts.colors[zone], f) if opts.shade else opts.colors[zone]
    if opts.palette == 'pitch':
        return hsv((pitch * 7 % 12) / 12, 0.9, 1.0)
    if opts.palette == 'octave':
        octave, pc = divmod(pitch, 12)
        return shade(hsv((octave * 3 % 8) / 8, 0.9, 1.0), 0.25 + 0.5 * pc / 11)
    if opts.palette == 'heat':
        return level_color(loud)
    return shade(opts.colors[0], (pitch - opts.lo) / (opts.hi - opts.lo))


def ring_speed(opts, pitch, loud):
    base = opts.speed * G.scale
    if opts.speed_mode == 'velocity':
        return base * (0.4 + 1.2 * (loud - 1) / 9)
    if opts.speed_mode == 'pitch':
        return base * (0.4 + 1.2 * max(0.0, min(1.0, (pitch - opts.lo) / (opts.hi - opts.lo))))
    if opts.speed_mode == 'random':
        return base * random.uniform(0.4, 1.6)
    return base


# ---------- MIDI ----------
def ival(values, key, default):
    try:
        return int(values[key])
    except (TypeError, ValueError, KeyError):
        return default


def midi_ports():
    try:
        return mido.get_input_names() if mido else []
    except Exception:
        return []


def midi_callback(msg):
    if G.window is None:
        return
    if msg.type == 'note_on' and msg.velocity > 0:
        G.window.write_event_value(K_MIDI_NOTE, (time.monotonic(), 'on', msg.note, msg.velocity))
    elif msg.type in ('note_off', 'note_on'):
        G.window.write_event_value(K_MIDI_NOTE, (time.monotonic(), 'off', msg.note, 0))
    elif msg.type == 'control_change' and msg.control == 64:
        G.window.write_event_value(K_MIDI_NOTE, (time.monotonic(), 'pedal', 0, msg.value))


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


# ---------- Rings ----------
def place(graph, opts, pitch, loud):
    """Canvas position (top-left origin) for a note (loud = loudness 1..10)"""
    w, h = graph.get_size()
    if opts.style == 'spiral':
        octave, pc = divmod(pitch, 12)
        a = pc / 12 * 2 * math.pi - math.pi / 2
        r = 40 * G.scale + (octave - 1) * min(w, h) * 0.052
        return w / 2 + r * math.cos(a), h / 2 + r * math.sin(a)
    f = max(0.0, min(1.0, (pitch - opts.lo) / (opts.hi - opts.lo)))
    if opts.style == 'rain':
        return random.uniform(w * 0.05, w * 0.95), h * 0.85 - f * h * 0.7
    return w * 0.04 + f * w * 0.92, h * 0.72 - (loud - 1) / 9 * h * 0.5 + random.uniform(-25, 25) * G.scale


def spawn(graph, opts, pitch, vel, now, small=False):
    tk = graph.Widget
    loud = opts.loudness(vel)                                  # 1..10
    x, y = place(graph, opts, pitch, loud)
    life = (BASE_LIFE + (loud - 1) / 9 * 1.5) * (1.8 if G.pedal_down else 1.0) * (0.5 if small else 1.0)
    ring = Ring(x, y, now, life, ring_color(opts, pitch, loud), (loud - 1) / 9 * (0.5 if small else 1.0), ring_speed(opts, pitch, loud))
    ring.fig = tk.create_oval(x - 4, y - 4, x + 4, y + 4, outline=ring.color, width=2)
    ring.dot = tk.create_oval(x - 6, y - 6, x + 6, y + 6, fill=ring.color, outline='')
    G.rings.append(ring)
    return x, y


def clear_all(graph):
    tk = graph.Widget
    for ring in G.rings:
        tk.delete(ring.fig)
        tk.delete(ring.dot)
    G.rings.clear()
    for fig in G.threads:
        tk.delete(fig)
    G.threads.clear()


def handle_midi(graph, opts, t, kind, note, value):
    if kind == 'on':
        x, y = spawn(graph, opts, note, value, t)
        G.held[note] = [x, y, t, value]
    elif kind == 'off':
        G.held.pop(note, None)
    elif kind == 'pedal':
        G.pedal_down = value >= 64


def animate(graph, opts, now):
    """Grow and fade every ring, pulse held notes, redraw the threads between held notes"""
    tk = graph.Widget
    for pitch, info in G.held.items():
        if now - info[2] > PULSE_EVERY:
            info[2] = now
            spawn(graph, opts, pitch, info[3], now, small=True)
    alive = []
    for ring in G.rings:
        age = now - ring.born
        if age > ring.life:
            tk.delete(ring.fig)
            tk.delete(ring.dot)
            continue
        f = age / ring.life
        r = 6 + age * ring.speed
        color = blend(ring.color, C_BG, f ** 0.8)
        tk.coords(ring.fig, ring.x - r, ring.y - r, ring.x + r, ring.y + r)
        tk.itemconfig(ring.fig, outline=color, width=max(1, (1 + ring.vel * 7) * (1 - f) * G.scale))
        d = max(0.5, 7 * G.scale * (1 - f * 2))
        tk.coords(ring.dot, ring.x - d, ring.y - d, ring.x + d, ring.y + d)
        tk.itemconfig(ring.dot, fill=color)
        alive.append(ring)
    G.rings[:] = alive
    for fig in G.threads:
        tk.delete(fig)
    G.threads.clear()
    pts = sorted((v[0], v[1]) for v in G.held.values())
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        G.threads.append(tk.create_line(x0, y0, x1, y1, fill=C_THREAD, width=1, dash=(3, 5)))
    if G.paused:
        w, h = graph.get_size()
        graph.CanvasSize = (w, h)
        graph.change_coordinates((0, 0), (w, h))
        graph.draw_text('❚❚  PAUSED   (F9 / Resume)', (w / 2, 30 * G.scale), color=C_PAUSED, font=FONT_UI)


def set_paused(window, on, now):
    if on == G.paused:
        return
    G.paused = on
    if on:
        G.pause_t = now
        window[K_PAUSE].update('Resume', button_color=(C_ON_TILE, C_PAUSED))
    else:
        shift = now - G.pause_t
        for ring in G.rings:
            ring.born += shift
        for info in G.held.values():
            info[2] += shift
        G.demo_next_t += shift
        G.demo_release = [(t + shift, p) for t, p in G.demo_release]
        window[K_PAUSE].update('Pause', button_color=sg.theme_button_color())


def demo_tick(graph, opts, now):
    """Slow pedalled arpeggios wandering through a few chords, spread over the Low .. High range"""
    while G.demo_release and G.demo_release[0][0] <= now:
        _, pitch = G.demo_release.pop(0)
        handle_midi(graph, opts, now, 'off', pitch, 0)
    if now < G.demo_next_t:
        return
    if not G.demo_seq:
        root = random.choice((0, 5, 7, 9))
        chord = [p for p in range(opts.lo, opts.hi + 1) if (p - root) % 12 in ((0, 4, 7, 11) if root != 9 else (0, 3, 7, 10))]
        chord = chord[::max(1, len(chord) // 9)][:9]
        G.demo_seq = [(n, random.uniform(0.18, 0.32)) for n in chord + chord[-2:0:-1]]
        handle_midi(graph, opts, now, 'pedal', 0, 127 if random.random() < 0.7 else 0)
    pitch, hold = G.demo_seq.pop(0)
    handle_midi(graph, opts, now, 'on', pitch, random.randint(30, 110))
    G.demo_release.append((now + hold * 0.9, pitch))
    G.demo_next_t = now + hold


# ---------- Touch picker ----------
def touch_pick(title, choices, current, steps, colors=None):
    """Big picker.  steps=None: one button per choice (coloured with colors[choice] when given).  Otherwise a slider and +/- buttons; OK/Cancel"""
    idx = choices.index(current) if current in choices else 0
    if steps is None:
        per_row, width = 5, max(6, max(len(str(c)) for c in choices))
        rows = [[sg.Button(str(c), key=KT_PICK(c), size=(width, 2), font=FONT_PICK, button_color=(C_ON_TILE, colors[c]) if colors and c in colors else None)
                 for c in choices[i:i + per_row]] for i in range(0, len(choices), per_row)]
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
        win[K_PICK_SLIDER].TKScale.configure(sliderlength=int(50 * G.scale))
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


PICKERS = {K_LOW: ('Lowest note (left edge)', NOTE_LIST, STEPS_NOTE),                  # key: (title, choices, steps or None for a button grid[, colours])
           K_HIGH: ('Highest note (right edge)', NOTE_LIST, STEPS_NOTE),
           K_PALETTE: ('Palette', PALETTES, None),
           K_STYLE: ('Style', STYLES, None),
           K_SPEED_MODE: ('Speed follows', SPEED_MODES, None),
           K_SPEED: ('Ring speed (px per second)', SPEED_CHOICES, STEPS_SPEED),
           K_VEL_MIN: ('Velocity that counts as loudness 1', VEL_CHOICES, STEPS_1_10),
           K_VEL_MAX: ('Velocity that counts as loudness 10', VEL_CHOICES, STEPS_1_10),
           K_TEXT_SIZE: ('Text size', TEXT_SIZE_CHOICES, None)}
for _n in (1, 2, 3):
    PICKERS[KT_ZONE_TOP(_n)] = (f'Zone {_n}: highest note', NOTE_LIST, STEPS_NOTE)
for _n in (1, 2, 3, 4):
    PICKERS[KT_ZONE_COLOR(_n)] = (f'Zone {_n}: colour', COLOR_CHOICES, None, COLORS)


def edit_value(window, key, values):
    title, choices, steps, *colors = PICKERS[key]
    current = next((c for c in choices if str(c) == str(values.get(key))), choices[0])
    chosen = touch_pick(title, choices, current, steps, colors[0] if colors else None)
    if chosen is not None and chosen != current:
        window[key].update(str(chosen))
        window.write_event_value(K_REBUILD if key == K_TEXT_SIZE else K_RECALC, key)


def paint_color_fields(window):
    """The four zone-colour value boxes show their colour"""
    for n in (1, 2, 3, 4):
        color = COLORS.get(window[KT_ZONE_COLOR(n)].get(), COLORS[ZONE_DEFAULT_COLORS[n - 1]])
        window[KT_ZONE_COLOR(n)].widget.configure(readonlybackground=color, fg=C_ON_TILE)


def save_settings(window, values):
    window.settings_save({k: v for k, v in values.items() if k in window.key_dict})


def set_fullscreen(window, on):
    G.fullscreen = on
    window.TKroot.attributes('-fullscreen', on)
    window[K_FULL].update('Windowed' if on else 'Full', button_color=(C_ON_TILE, C_PAUSED) if on else sg.theme_button_color())
    sg.user_settings_set_entry(K_FULLSCREEN, on)


def show_controls(window, on):
    window[K_CONTROLS].update(visible=on)
    window[K_TOGGLE_CONTROLS].update('▲' if on else '▼')
    sg.user_settings_set_entry(K_CONTROLS_HIDDEN, not on)


# ---------- Window ----------
def build_window(ports, port):
    sg.set_options(font=FONT_UI)
    P = ((10, 4), 0)
    TAP_TT = '  (tap the value or the pencil for a big picker)'

    def field(default, key, width, tooltip):
        return [sg.Input(str(default), key=key, size=(width, 1), readonly=True, setting=default, justification='c', tooltip=tooltip + TAP_TT),
                sg.Text('\u270E', key=KT_EDIT(key), enable_events=True, text_color=C_EDIT, pad=((0, 4), 0), tooltip='Change: ' + tooltip)]

    top = [sg.Text('MIDI in'), sg.Combo(ports, default_value=port, key=K_PORT, size=(18, 1), readonly=True, enable_events=True), sg.Button('Refresh', key=K_REFRESH),
           sg.Text('Low', pad=P), *field('A0', K_LOW, 4, TT_LOW), sg.Text('High', pad=P), *field('C8', K_HIGH, 4, TT_HIGH),
           sg.Text('Style', pad=P), *field('keyboard', K_STYLE, 9, TT_STYLE),
           sg.Text('Speed', pad=P), *field('velocity', K_SPEED_MODE, 8, TT_SPEED_MODE), *field(90, K_SPEED, 4, TT_SPEED),
           sg.Text('Text', pad=P), *field('100%', K_TEXT_SIZE, 5, 'Size of all text in the program'),
           sg.Push(),
           sg.Button('Full', key=K_FULL, size=(9, 1), tooltip='Full screen on / off (F11): whole screen, no title bar'),
           sg.Button('Pause', key=K_PAUSE, size=(7, 1), tooltip='Freeze the animation (F9)'), sg.Button('Clear', key=K_CLEAR, tooltip='Wipe the canvas (HOME)'),
           sg.Button('Exit', key=K_EXIT)]
    zones = [sg.Text('Palette'), *field('zones', K_PALETTE, 7, TT_PALETTE), sg.Text('Zones', pad=((30, 4), 0))]
    for n in (1, 2, 3, 4):
        if n < 4:
            zones += [sg.Text('\u2264', pad=P), *field(ZONE_DEFAULT_TOPS[n - 1], KT_ZONE_TOP(n), 4, TT_ZONE_TOP)]
        else:
            zones += [sg.Text('above', pad=P)]
        zones += field(ZONE_DEFAULT_COLORS[n - 1], KT_ZONE_COLOR(n), 8, TT_ZONE_COLOR)
    zones += [sg.Checkbox('Shade by pitch', key=K_SHADE, setting=True, pad=P, tooltip='Dark at the bottom of a zone, light at the top'),
              sg.Checkbox('Demo', key=K_DEMO, enable_events=True, pad=P, tooltip='Play slow arpeggios by itself')]
    loud = [sg.Text('Loudness 1-10'), sg.Text('Vel@1', pad=P), *field(1, K_VEL_MIN, 4, TT_VEL_MIN), sg.Text('Vel@10', pad=P), *field(127, K_VEL_MAX, 4, TT_VEL_MAX),
            sg.Text('heat colours, ring thickness and life follow the 1-10 loudness scale', text_color=C_AXIS_TEXT, pad=((20, 0), 0))]
    controls = sg.pin(sg.Column([top, zones, loud], key=K_CONTROLS, expand_x=True, pad=(0, 0)), expand_x=True)
    canvas = sg.Graph((1000, 600), (0, 0), (1, 1), key=K_CANVAS, background_color=C_BG, enable_events=True, expand_x=True, expand_y=True, pad=(0, (6, 0)))
    layout = [[controls], [canvas],
              [sg.Text('', key=K_STATUS, font=FONT_LABEL, size=(60, 1), pad=(0, 0)), sg.Push(),
               sg.Button('\u25B2', key=K_TOGGLE_CONTROLS, font=FONT_LABEL, tooltip='Hide / show the controls (F10)', pad=(0, 0))]]

    window = sg.Window(APP_TITLE, layout, resizable=True, finalize=True, margins=(4, 4), auto_save_location=True, enable_close_attempted_event=True)
    G.window = window
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)
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
    paint_color_fields(window)
    if sg.user_settings_get_entry(K_FULLSCREEN, False):
        set_fullscreen(window, True)
    if sg.user_settings_get_entry(K_CONTROLS_HIDDEN, False):
        show_controls(window, False)
    window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)
    if G.paused:
        window[K_PAUSE].update('Resume', button_color=(C_ON_TILE, C_PAUSED))
    G.rings.clear()
    G.threads.clear()
    window.timer_start(25)
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
            if event == K_KEY_ESC and G.fullscreen:
                set_fullscreen(window, False)
                continue
            save_settings(window, values)
            break
        opts = Opts(values)
        graph = window[K_CANVAS]
        now = time.monotonic()
        if event == sg.EVENT_TIMER:
            if not G.paused:
                if values[K_DEMO]:
                    demo_tick(graph, opts, now)
                animate(graph, opts, now)
        elif event == K_MIDI_NOTE:
            t, kind, note, value = values[K_MIDI_NOTE]
            if not G.paused:
                handle_midi(graph, opts, t, kind, note, value)
        elif event == K_CANVAS:                                                                         # tap on the picture: next palette
            window[K_PALETTE].update(PALETTES[(PALETTES.index(opts.palette) + 1) % len(PALETTES)])
        elif event == K_RECALC:
            paint_color_fields(window)
        elif event in (K_PAUSE, K_KEY_F9):
            set_paused(window, not G.paused, now)
        elif event in (K_CLEAR, K_KEY_HOME):
            clear_all(graph)
        elif event == K_REBUILD:
            save_settings(window, values)
            set_fonts(values[K_TEXT_SIZE])
            window.timer_stop_all()
            window.close()
            window = build_window(ports, values[K_PORT])
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
        elif event in (K_FULL, K_KEY_F11):
            set_fullscreen(window, not G.fullscreen)
        elif event in (K_TOGGLE_CONTROLS, K_KEY_F10):
            show_controls(window, not window[K_CONTROLS].visible)

    window.timer_stop_all()
    close_port()
    window.close()


if __name__ == '__main__':
    main()
