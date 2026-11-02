"""
Tempo Widget  (tempo_widget.pyw)  -  a small, always-on-top tempo dial that listens to the piano.

Meant to float over the other programs: no title bar, keeps on top, drag it anywhere by its face, the ✕ (a flat text, top right)
closes it, the gear ⚙ (bottom right, orange while the controls are hidden) shows and hides them, and its place on the screen is remembered.
"on top" (controls) keeps it above other windows - on by default; untick it to let other programs cover it.
ONE-LINE MODE: the ▬ at the bottom left collapses the widget to a single strip - lamp, tempo, verdict, a bar that fills from the
left the faster you play (target in the middle, bracket band around it), loudness · velocity.
It sits over another program; ▣ at the left end of the strip brings the full widget back.  The mode is remembered.
"Size" (controls) shrinks the main display - number, meter, strip and texts - to medium (3/4) or small (just over half); the meter
keeps its face and needle, showing only the end and target figures when small so they stay readable.
"Range" sets how far the meter reaches either side of the target (+- 10 .. 50 %): a narrow range makes the needle swing more
for the small tempo changes inside one piece.  The meter is drawn like the VU meter of a 1970s stereo - a black bezel, a lamp-lit ivory face with paper grain and glass
reflections, a shallow scale across the top with hanging ticks, a red zone for rushing, a faint green band for on tempo - and is
centred on the TARGET tempo (needle straight up): it falls when you drag and rises when you rush.  The face is rendered once
(Pillow); the needle is drawn over it.  The big number turns blue (slow) or coral (fast) outside the +- % bracket, a strong green
inside it.  "Needle" picks the needle's colour - black, red, white, orange, blue, or the tempo colour itself - "Thick" its
thickness, and "shadow" whether it casts one on the face.  A lamp blinks on every note.
Under the dial: the last note's loudness on the 1-10 scale of the Piano Dynamics Monitor and its raw MIDI velocity, e.g. "6 mf · 71".

How the tempo is read without a score: every pair of your last notes (8 s) votes for the beat periods of which their spacing is
a small multiple - an IOI-cluster tempogram, which copes with mixed rhythms (dotted notes, a melody over an accompaniment, rests)
where a simple note-spacing reading fails.  Its strong peaks are the possible metrical levels (16th, 8th, triplet, quarter, half).
"Beat" = auto picks the level nearest the target, helped by your accents (the level whose grid catches the loudest notes) and by
sticking with the level already chosen; set "Beat" to the smallest note value you are playing when you practise far from the
target (half speed, say) and the reading follows that instead.  Chords count once.  When the level is not clear-cut the number is
shown as "≈80".  "Response" is how many seconds of notes the reading rests on: quick (3 s) follows a ritardando within a beat or
two but wobbles more, steady (8 s) is calmer.  A sudden big slow-down in a piece with subdivisions (triplets, 16ths) is best
followed with "Beat" set to that note value - then the reading is simply the note spacing, no level guessing.
After three seconds of silence the reading fades to "-".  (Without numpy the older median-spacing reading is used.)

TEMPO STRIP: "Strip" (controls) adds a strip along the bottom of the full view with the tempo over time, coloured like the number,
with the target line and bracket band; the setting is how much time it shows before it starts scrolling, 10 s to an hour - jump
buttons for the usual spans, a slider and step buttons to fine-tune (off = none).
CONTROLS (the gear, or F10): MIDI in port + ⟳ (look for ports again), Target bpm, +- %, Beat, Text size.
Every setting is a read-only value box with a small pencil; tapping the box or the pencil opens a big touch picker.
On Windows a MIDI input port can usually be opened by one program at a time.  To run this beside Follow Me or the others on
the same piano, use a MIDI splitter (loopMIDI + a router, or MIDI-OX) or a multi-client driver such as Yamaha's USB-MIDI driver.
Right-click: Edit Me / Version / Exit.   ESC also closes.
Requires:  pip install PySimpleGUI mido python-rtmidi pillow numpy
Settings persist in SETTINGS_FILE (tempo_widget.json in the PySimpleGUI settings folder).

CHANGE LOG (newest first, 1 line per change):
2026-11-01  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import io
import math
import sys
import time

import PySimpleGUI as sg

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    Image = None

try:
    import mido
except ImportError:
    mido = None
try:
    import numpy as np
except ImportError:
    np = None

ICON = b'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'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_TITLE = 'Tempo Widget'
SETTINGS_FILE = 'tempo_widget.json'

# ---------- Keys ----------
K_GAUGE = '-GAUGE-'
K_BPM = '-BPM-'
K_STATE = '-STATE-'
K_LOUD = '-LOUD-'
K_DOT = '-DOT-'
K_PORT = '-PORT-'
K_REFRESH = '-REFRESH-'
K_TARGET = '-TARGET-'
K_TOL = '-TOL-'
K_BEAT = '-BEAT-'
K_NEEDLE = '-NEEDLE-'
K_RANGE = '-RANGE-'
K_THICK = '-THICK-'
K_STRIP = '-STRIP-'
K_ON_TOP = '-ON TOP-'
K_STRIP_ROW = '-STRIP ROW-'
K_STRIP_SPAN = '-STRIP SPAN-'
K_RESPONSE = '-RESPONSE-'
RESPONSE_CHOICES = ['quick', 'normal', 'steady']
RESPONSE_WINDOW = {'quick': (3.0, 4), 'normal': (5.0, 5), 'steady': (8.0, 6)}        # seconds of notes the reading is based on, notes needed
TT_RESPONSE = 'How quickly the reading follows a change of tempo: quick uses the last 3 s of notes, normal 5 s, steady 8 s (steadier, slower to follow)'
STRIP_CHOICES = ['off'] + list(range(10, 3601, 10))         # seconds across the strip before it starts scrolling: 10 s .. 1 hour
STRIP_PRESETS = ['off', 30, 60, 120, 300, 600, 1800, 3600]   # the jump buttons of the picker
STRIP_STEPS = [(-30, '-5 min'), (-6, '-1 min'), (-1, '-10 s'), (1, '+10 s'), (6, '+1 min'), (30, '+5 min')]
TT_STRIP = 'A strip along the bottom with the tempo over time: how many seconds it shows before it starts scrolling (off = no strip)'
K_SHADOW = '-SHADOW-'
THICK_CHOICES = [1, 2, 3, 4, 5, 6]
TT_THICK = 'Thickness of the needle in pixels (at 100 %)'
RANGE_CHOICES = [10, 15, 20, 25, 30, 40, 50]
TT_RANGE = 'How far the meter reaches either side of the target, in percent: narrow it so the needle moves more for small changes'
NEEDLE_CHOICES = ['black', 'red', 'white', 'orange', 'blue', 'tempo colour']
NEEDLE_COLOURS = {'black': '#14100C', 'red': '#D01818', 'white': '#F4F1E8', 'orange': '#FF7A00', 'blue': '#1E5BFF'}
TT_NEEDLE = 'Colour of the meter needle; "tempo colour" follows the reading (blue slow, green on target, coral fast)'
K_TEXT_SIZE = '-TEXT SIZE-'
K_FACE_SIZE = '-FACE SIZE-'
FACE_SIZE_CHOICES = ['large', 'medium', 'small']
FACE_MULT = {'large': 1.0, 'medium': 0.75, 'small': 0.55}         # the main display: number, meter, strip, texts
TT_FACE_SIZE = 'Size of the main display (number, meter and strip): large, medium or small'
K_REBUILD = '-REBUILD-'
K_RECALC = '-RECALC-'
K_CLOSE = '-CLOSE-'
K_CLOSE2 = '-CLOSE2-'
K_LINE = '-LINE-'
K_EXPAND = '-EXPAND-'
K_FACE = '-FACE-'
K_LINE_ROW = '-LINE ROW-'
K_LINE_MODE = '-LINE MODE-'          # settings-file entry only
K_BPM2 = '-BPM2-'
K_STATE2 = '-STATE2-'
K_LOUD2 = '-LOUD2-'
K_DOT2 = '-DOT2-'
K_BAR = '-BAR-'
K_TOGGLE_CONTROLS = '-TOGGLE CONTROLS-'
K_CONTROLS = '-CONTROLS-'
K_CONTROLS_HIDDEN = '-CONTROLS HIDDEN-'
K_STATUS = '-STATUS-'
K_MIDI_NOTE = '-MIDI NOTE-'
K_KEY_ESC = '-KEY ESC-'
K_KEY_F10 = '-KEY F10-'
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

# ---------- Colours ----------
C_BG = '#101418'
C_ON = '#22DD44'                      # on target: a strong green
C_SLOW, C_FAST = '#4AA3FF', '#FF8A4C'
C_AXIS_TEXT = '#9AA6B2'
C_TEXT = '#E6E8EE'
C_STATUS_OK = '#69F0AE'
C_STATUS_BAD = '#FF8A65'
C_EDIT = '#4DD0E1'
C_ON_TILE = '#000000'
C_DOT = '#FFC96B'                     # the lamp, lit
C_LAMP_OFF = '#4A4038'                # the lamp, off (same glyph: the width of the row never changes)
C_AMBER = '#F5B342'                   # labels, in the colour of the dial's back-light
C_GEAR_HIDDEN = '#FF8A1F'             # the gear turns orange while the controls are hidden
C_BG_FACE = '#0E1013'
LEVELS = [(1, 2, '#448AFF', 'pp'), (3, 4, '#00E676', 'p'), (5, 6, '#FFEA00', 'mf'), (7, 8, '#FF9100', 'f'), (9, 10, '#FF1744', 'ff')]

FONT_FAMILY = 'Segoe UI'
BASE_FONTS = {'FONT_UI': 11, 'FONT_LABEL': 10, 'FONT_BIG': 44, 'FONT_MID': 13, 'FONT_LINE': 16, 'FONT_SMALL': 9, 'FONT_PICK': 20, 'FONT_PICK_VALUE': 48}
TEXT_SIZE_CHOICES = ['70%', '85%', '100%', '115%', '130%', '150%']


def set_fonts(text_size, face_size='large'):
    """All fonts from the Text size multiplier; the main display's own fonts (FONT_FACE_*) also shrink with its Size.
    Nothing goes below 9 pt, and the tap targets (✕ ⚙ ▬) never below the medium size."""
    try:
        mult = int(str(text_size).rstrip('%')) / 100
    except ValueError:
        mult = 1.0
    for name, size in BASE_FONTS.items():
        globals()[name] = (FONT_FAMILY, max(7, round(size * mult)), 'bold')
    face = FACE_MULT.get(face_size, 1.0)
    globals()['FONT_FACE_BIG'] = (FONT_FAMILY, max(14, round(BASE_FONTS['FONT_BIG'] * mult * face)), 'bold')
    globals()['FONT_FACE_MID'] = (FONT_FAMILY, max(9, round(BASE_FONTS['FONT_MID'] * mult * face)), 'bold')
    globals()['FONT_FACE_LABEL'] = (FONT_FAMILY, max(9, round(BASE_FONTS['FONT_LABEL'] * mult * face)), 'bold')
    globals()['FONT_FACE_TAP'] = (FONT_FAMILY, max(9, round(BASE_FONTS['FONT_MID'] * mult * max(face, 0.75))), 'bold')


set_fonts('100%')
TARGET_CHOICES = list(range(20, 241))
TOL_CHOICES = list(range(2, 31))
BEAT_CHOICES = ['auto', 'quarter', '8th', '8th triplet', '16th']
BEAT_GRAIN = {'quarter': 1.0, '8th': 0.5, '8th triplet': 1 / 3, '16th': 0.25}
STEPS_1_10 = [(-10, '-10'), (-1, '-1'), (1, '+1'), (10, '+10')]
STEPS_1 = [(-1, '-1'), (1, '+1')]
SILENCE = 3.0                           # seconds without a note before the reading fades
TT_TARGET = 'Target tempo, bpm: the centre of the dial'
TT_TOL = 'How far from the target (percent) still counts as on tempo (green); slower = blue, faster = coral'
TT_BEAT = 'The smallest note value in what you are playing (quarter, 8th, 8th triplet, 16th), or auto: the beat level nearest the target'


class G:
    window = None
    port = None
    status, status_ok = '', False
    scale = 1.0
    onsets = []                         # times of the last onsets (a chord counts once) - the fallback estimator
    est = None                          # the TempoEstimator (numpy)
    conf = 1.0                          # how clearly the beat level stood out (below 0.55 the number is shown as approximate)
    bpm = None
    last_note_t = 0.0
    last_loud = None
    last_vel = None
    vel_range = (1, 127)
    dot_until = 0.0
    face_key, frame_key, needle = None, None, []      # what the meter face was rendered for, the last reading drawn, the needle's figures
    target, tol, beat = 92, 5, 'auto'
    face = 1.0                          # the main display's size factor (Size setting)
    needle_colour = 'black'
    range_pct = 50                      # the meter shows target * (1 -+ range)
    thick, shadow = 2, True             # the needle's thickness (px at 100 %) and whether it casts a shadow
    strip_span = None                   # seconds across the tempo strip, None = off
    response = 'normal'
    samples = []                        # (time, bpm) readings for the strip
    strip_t0 = None                     # when the strip's time axis started
    strip_drawn = 0.0
    line_mode = False                   # collapsed to a single line


# ---------- tempo ----------
def loudness(vel):
    vel_min, vel_max = G.vel_range
    return max(1.0, min(10.0, 1 + 9 * (vel - vel_min) / max(1, vel_max - vel_min)))


def level_color(value):
    for lo, hi, color, name in LEVELS:
        if value < hi + 0.5 or hi == 10:
            return color
    return LEVELS[-1][2]


def level_name(value):
    return next(name for lo, hi, color, name in LEVELS if value < hi + 0.5 or hi == 10)


# ---------- the tempo estimator (see the class doc); the median-spacing method remains as a fallback without numpy ----------
WEIGHTS = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.5, 6: 0.3, 8: 0.25}
GRAINS = {'quarter': 1, '8th': 2, '8th triplet': 3, '16th': 4}


class TempoEstimator:
    """Tempo from onsets alone: an IOI-cluster tempogram, the metrical level nearest the target (helped by velocity accents and
    hysteresis) or the level implied by an explicit note value, then the period refined from the intervals on that grid."""
    def __init__(self, target=92.0, window=8.0, min_onsets=6, accent_weight=10.0, expo=0.4, near_sigma=0.6):
        self.target, self.window, self.min_onsets = target, window, min_onsets
        self.accent_weight, self.expo, self.near_sigma = accent_weight, expo, near_sigma
        self.onsets, self.vels = [], []
        self.bpm, self.period, self.conf, self.level = None, None, 0.0, None
        self.grain = 'auto'
        n = 160
        self.cand = 0.25 * 16 ** (np.arange(n) / (n - 1))            # candidate periods as fractions of the target period
        self.kw = np.zeros(9)
        for k, w in WEIGHTS.items():
            self.kw[k] = w

    def reset(self):
        self.onsets, self.vels, self.bpm, self.period, self.conf, self.level = [], [], None, None, 0.0, None

    def note(self, t, vel=80):
        """A note-on at time t; returns the current bpm (or None)"""
        if self.onsets and t - self.onsets[-1] < 0.06:
            self.vels[-1] = max(self.vels[-1], vel)
            return self.bpm
        self.onsets.append(t)
        self.vels.append(vel)
        while self.onsets and t - self.onsets[0] > self.window:
            self.onsets.pop(0)
            self.vels.pop(0)
        if len(self.onsets) < self.min_onsets:
            return self.bpm
        on = np.array(self.onsets)
        d = (on[None, :] - on[:, None])
        d = d[(d > 0.05) & (d < 4.0)]
        if d.size < 3:
            return self.bpm
        tp = 60.0 / self.target
        periods = self.cand * tp
        k = np.rint(d[:, None] / periods[None, :])
        kk = np.clip(k, 0, 8).astype(int)
        w = self.kw[kk] * (k == kk)
        err = (d[:, None] - k * periods[None, :]) / (0.07 * periods[None, :] * np.sqrt(np.maximum(k, 1)))
        score = (w * np.exp(-err * err)).sum(axis=0)
        top = float(score.max())
        if top <= 0:
            return self.bpm
        peaks = [i for i in range(len(periods)) if score[i] >= 0.4 * top and score[i] >= score[max(0, i - 1)] and score[i] >= score[min(len(periods) - 1, i + 1)]]
        if not peaks:
            return self.bpm
        if self.grain in GRAINS:                                      # explicit note value: the finest strong pulse is that value
            finest = min((i for i in peaks if score[i] >= 0.6 * top), default=peaks[0])
            best_i = None
            target_p = periods[finest] * GRAINS[self.grain]
            best_i = min(peaks, key=lambda i: abs(math.log(periods[i] / target_p)))
            if abs(math.log(periods[best_i] / target_p)) > 0.1:      # no peak there (a rest pattern): use the pulse times the multiple
                best_p = target_p
            else:
                best_p = periods[best_i]
        else:
            vels = np.array(self.vels, dtype=float)

            def accent(p):
                best = 0.0
                spread = float(vels.std()) + 1e-6
                for phase_i in range(6):
                    r = ((on - p * phase_i / 6) / p) % 1.0
                    grid = np.minimum(r, 1 - r) < 0.12
                    n_on, n_off = int(grid.sum()), int((~grid).sum())
                    if 0 < n_on < len(on):
                        contrast = float(vels[grid].mean() - vels[~grid].mean())
                        chance = 1.0 * spread * math.sqrt(1 / n_on + 1 / n_off)          # what random loud notes would produce
                        best = max(best, (contrast - chance) / 127)                       # only a contrast beyond chance counts
                return best

            def value(i):
                p = periods[i]
                lp = math.log(p / tp)
                near = math.exp(-lp * lp / (2 * self.near_sigma ** 2)) + 0.25 * math.exp(-lp * lp / (2 * 0.1 ** 2))      # a wide pull plus a bonus right at the target
                stay = 1.0 if self.period is None else math.exp(-(math.log(p / self.period)) ** 2 / (2 * 0.12 ** 2))
                return (score[i] / top) ** self.expo * near * (1 + 0.25 * stay) * (1 + self.accent_weight * accent(p))
            best_i = max(peaks, key=value)
            best_p = periods[best_i]
        k1 = np.rint(d / best_p)
        good = (k1 >= 1) & (k1 <= 4) & (np.abs(d / np.maximum(k1, 1) - best_p) < 0.12 * best_p)
        period = float(np.median(d[good] / k1[good])) if good.any() else float(best_p)
        self.conf = float(score[best_i] / top) if best_i is not None else 0.5
        if self.period is None or abs(math.log(period / self.period)) > 0.15:              # a new metrical level: jump, never blend across levels
            self.period = period
        else:
            self.period = 0.3 * self.period + 0.7 * period
        self.bpm = 60.0 / self.period
        return self.bpm


def note_on(t, vel):
    """One note-on.  With numpy: the tempogram estimator (chords within 60 ms count once).  Without: the median spacing of the last
    onsets read as the chosen note value (auto: the value that lands nearest the target)."""
    G.last_note_t, G.last_loud, G.last_vel, G.dot_until = t, loudness(vel), vel, t + 0.12
    if np is not None:
        window, min_onsets = RESPONSE_WINDOW.get(G.response, RESPONSE_WINDOW['normal'])
        if G.est is None or G.est.target != G.target or G.est.window != window:
            est = TempoEstimator(G.target, window=window, min_onsets=min_onsets)
            if G.est is not None:
                est.onsets, est.vels, est.period, est.bpm = G.est.onsets, G.est.vels, G.est.period, G.est.bpm
            G.est = est
        G.est.grain = G.beat
        bpm = G.est.note(t, vel)
        G.conf = G.est.conf if bpm is not None else 1.0
    else:
        if G.onsets and t - G.onsets[-1] < 0.04:
            return
        G.onsets.append(t)
        G.onsets = [x for x in G.onsets if t - x < 4.0][-12:]
        if len(G.onsets) < 4:
            return
        iois = sorted(b - a for a, b in zip(G.onsets, G.onsets[1:]))
        ioi = iois[len(iois) // 2]
        if ioi <= 0:
            return
        grain = min(BEAT_GRAIN.values(), key=lambda g: abs(60.0 * g / ioi - G.target)) if G.beat == 'auto' else BEAT_GRAIN[G.beat]
        bpm = 60.0 * grain / ioi
        bpm = (bpm if G.bpm is None else 0.6 * G.bpm + 0.4 * bpm) if 15 <= bpm <= 400 else None
    if bpm is not None and 15 <= bpm <= 400:
        G.bpm = bpm
        G.samples.append((t, G.bpm))
        G.samples = G.samples[-20000:]
        if G.strip_t0 is None:
            G.strip_t0 = t


def tempo_state(bpm):
    if bpm is None:
        return None
    lo, hi = G.target * (1 - G.tol / 100), G.target * (1 + G.tol / 100)
    return 'slow' if bpm < lo else 'fast' if bpm > hi else 'ok'


def tempo_color(state):
    return {'slow': C_SLOW, 'ok': C_ON, 'fast': C_FAST}.get(state, C_AXIS_TEXT)


def gauge_frac(bpm):
    """0..1 across the meter: the target in the middle, target * (1 -+ range %) at the ends"""
    return max(0.0, min(1.0, 0.5 + (bpm - G.target) / (G.target * G.range_pct / 100) * 0.5))


SS = 3


def font(px, bold=True, serif=True):
    names = ['DejaVuSerif-Bold.ttf' if bold else 'DejaVuSerif.ttf', 'georgiab.ttf' if bold else 'georgia.ttf'] if serif else ['DejaVuSans-Bold.ttf', 'segoeuib.ttf']
    for name in names:
        try:
            return ImageFont.truetype(name, int(px))
        except OSError:
            continue
    return ImageFont.load_default()


def lerp(c1, c2, f):
    return tuple(int(a + (b - a) * f) for a, b in zip(c1, c2))


def geometry(w, h):
    """Pivot below the face and a large radius: a shallow arc across the top, as on a real meter"""
    W, H = w * SS, h * SS
    cx, cy = W / 2, H * 1.42
    R = H * 1.18
    return W, H, cx, cy, R


def angle_of(frac):
    """Needle angle for a 0..1 reading: -46 deg (left) .. +46 deg (right), measured from straight up"""
    return math.radians(-38 + 76 * frac)


def point(cx, cy, r, ang):
    return cx + r * math.sin(ang), cy - r * math.cos(ang)


def vu_face(w, h, target, tol, lo_f, hi_f, min_px=0):
    """min_px: smallest text height in screen pixels (9 pt) - on the smaller sizes the scale shows fewer, larger figures"""
    W, H, cx, cy, R = geometry(w, h)
    im = Image.new('RGB', (W, H), (20, 18, 16))
    d = ImageDraw.Draw(im)
    # bezel: black plastic with a soft bevel
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=int(H * 0.09), fill=(24, 22, 20))
    d.rounded_rectangle((SS, SS, W - 1 - SS, H - 1 - SS), radius=int(H * 0.085), outline=(58, 54, 50), width=max(1, SS))
    inset = int(H * 0.075)
    win = (inset, inset, W - inset, H - inset)
    # face: ivory paper lit by a lamp at the top centre, darker at the bottom corners
    face = Image.new('RGB', (W, H), (0, 0, 0))
    fd = ImageDraw.Draw(face)
    for y in range(win[1], win[3]):
        fd.line((win[0], y, win[2], y), fill=lerp((248, 232, 190), (222, 190, 128), (y - win[1]) / max(1, win[3] - win[1])))
    glow = Image.new('L', (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gx, gy, gr = W / 2, H * 0.28, W * 0.62
    for k in range(48, 0, -1):
        f = k / 48
        gd.ellipse((gx - gr * f, gy - gr * f * 0.62, gx + gr * f, gy + gr * f * 0.62), fill=int(255 * (1 - f) ** 1.4))
    glow = glow.filter(ImageFilter.GaussianBlur(W * 0.05))
    face = Image.composite(Image.new('RGB', (W, H), (255, 246, 214)), face, glow.point(lambda v: int(v * 0.7)))
    vignette = Image.new('L', (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    vd.rectangle(win, fill=90)
    vd.rounded_rectangle((win[0] + W * 0.05, win[1] - H * 0.2, win[2] - W * 0.05, win[3] - H * 0.05), radius=int(W * 0.25), fill=0)
    face = Image.composite(Image.new('RGB', (W, H), (150, 108, 52)), face, vignette.filter(ImageFilter.GaussianBlur(W * 0.06)))
    grain = Image.effect_noise((W, H), 8).convert('L').point(lambda v: 118 + (v - 128) // 3)      # paper grain
    face = Image.blend(face, Image.merge('RGB', (grain, grain, grain)).point(lambda v: v * 2), 0.06)
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle(win, radius=int(H * 0.045), fill=255)
    im.paste(face, (0, 0), mask)
    d = ImageDraw.Draw(im)
    # the scale: arc near the top, ticks hanging below it, numbers above; red zone on the right; green on-tempo band
    ink = (38, 30, 22)
    red = (188, 34, 28)
    arc_w = max(2, int(SS * 1.6))
    a0, a1 = angle_of(0), angle_of(1)
    box = (cx - R, cy - R, cx + R, cy + R)
    deg = lambda ang: math.degrees(ang) - 90
    d.arc(box, deg(a0), deg(angle_of(hi_f)), fill=ink, width=arc_w)
    d.arc(box, deg(angle_of(hi_f)), deg(a1), fill=red, width=int(arc_w * 1.8))
    band = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.pieslice((cx - R * 0.985, cy - R * 0.985, cx + R * 0.985, cy + R * 0.985), deg(angle_of(lo_f)), deg(angle_of(hi_f)), fill=(40, 190, 70, 120))
    bd.pieslice((cx - R * 0.88, cy - R * 0.88, cx + R * 0.88, cy + R * 0.88), deg(angle_of(lo_f)) - 1, deg(angle_of(hi_f)) + 1, fill=(0, 0, 0, 0))
    inner_mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(inner_mask).pieslice((cx - R * 0.88, cy - R * 0.88, cx + R * 0.88, cy + R * 0.88), deg(angle_of(lo_f)) - 1, deg(angle_of(hi_f)) + 1, fill=255)
    band.putalpha(Image.composite(Image.new('L', (W, H), 0), band.getchannel('A'), inner_mask))
    im = Image.alpha_composite(im.convert('RGBA'), band).convert('RGB')
    d = ImageDraw.Draw(im)
    num_px = max(H * 0.115, min_px * SS)
    f_num = font(num_px)
    few = num_px > H * 0.14                                    # figures had to grow: show only the ends and the target
    for k in range(25):
        f = k / 24
        ang = angle_of(f)
        major = k % 6 == 0
        mid = k % 3 == 0
        length = R * (0.075 if major else 0.05 if mid else 0.032)
        colour = red if f > hi_f + 0.001 else ink
        p1, p2 = point(cx, cy, R * 0.99, ang), point(cx, cy, R * 0.99 - length, ang)
        d.line((p1, p2), fill=colour, width=max(1, int(SS * (1.7 if major else 1.1))))
    r = G.range_pct / 100
    for value, f in ((target * (1 - r), 0.0), (target * (1 - r / 2), 0.25), (target, 0.5), (target * (1 + r / 2), 0.75), (target * (1 + r), 1.0)):
        if few and f in (0.25, 0.75):
            continue
        x, y = point(cx, cy, R * 1.085, angle_of(f))
        anchor = 'lm' if f == 0.0 else 'rm' if f == 1.0 else 'mm'                      # the end figures sit inward of their ticks
        d.text((x + (R * 0.02 if f == 0.0 else -R * 0.02 if f == 1.0 else 0), y), f'{value:.0f}', fill=red if f > hi_f + 0.001 else ink, font=f_num, anchor=anchor)
    xm, ym = point(cx, cy, R * 0.985, angle_of(0.5))
    d.line((xm, ym + R * 0.005, xm, ym - R * 0.02), fill=ink, width=max(2, int(SS * 2.6)))
    d.text((W * 0.06 + inset, H * 0.66), '−', fill=ink, font=font(H * 0.16), anchor='lm')
    d.text((W - W * 0.06 - inset, H * 0.66), '+', fill=red, font=font(H * 0.16), anchor='rm')
    d.text((cx, H * 0.80), 'TEMPO', fill=ink, font=font(max(H * 0.17, min_px * SS)), anchor='mm')
    # glass: two soft reflections and a faint edge shadow inside the bezel
    glass = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.polygon([(win[0], win[1]), (W * 0.55, win[1]), (W * 0.30, win[3]), (win[0], win[3])], fill=(255, 255, 255, 18))
    gd.polygon([(W * 0.62, win[1]), (W * 0.74, win[1]), (W * 0.52, win[3]), (W * 0.40, win[3])], fill=(255, 255, 255, 10))
    glass = glass.filter(ImageFilter.GaussianBlur(SS * 2))
    shadow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle(win, radius=int(H * 0.045), outline=255, width=int(H * 0.05))
    shadow = shadow.filter(ImageFilter.GaussianBlur(H * 0.03)).point(lambda v: int(v * 0.5))
    im = Image.composite(Image.new('RGB', (W, H), (60, 44, 24)), im, Image.composite(shadow, Image.new('L', (W, H), 0), mask))
    im = Image.alpha_composite(im.convert('RGBA'), Image.composite(glass, Image.new('RGBA', (W, H), (0, 0, 0, 0)), mask)).convert('RGB')
    return im.resize((w, h), Image.LANCZOS)




def update_dial(window, bpm):
    """The meter: a photo-realistic face rendered once per size / target / bracket, the needle drawn over it on the Graph"""
    if Image is None:
        return
    graph = window[K_GAUGE]
    w, h = int(210 * G.scale * G.face), int(120 * G.scale * G.face)
    key = (w, h, G.target, G.tol, G.range_pct)
    if G.face_key != key:
        lo_f, hi_f = gauge_frac(G.target * (1 - G.tol / 100)), gauge_frac(G.target * (1 + G.tol / 100))
        buf = io.BytesIO()
        vu_face(w, h, G.target, G.tol, lo_f, hi_f, min_px=12 * G.scale).save(buf, format='PNG')          # 12 px at 96 dpi = 9 pt
        graph.set_size((w, h))
        graph.CanvasSize = (w, h)
        graph.change_coordinates((0, h), (w, 0))
        graph.erase()
        graph.draw_image(data=buf.getvalue(), location=(0, 0))
        G.face_key, G.frame_key, G.needle = key, None, []
    frame_key = (None if bpm is None else round(bpm * 2), G.needle_colour, G.range_pct, G.thick, G.shadow)
    if frame_key == G.frame_key:
        return
    G.frame_key = frame_key
    for fig in G.needle:
        graph.delete_figure(fig)
    G.needle = []
    if bpm is not None:
        W, H, cx, cy, R = geometry(w, h)
        cx, cy, R = cx / SS, cy / SS, R / SS
        ang = angle_of(gauge_frac(bpm))
        tip, base = point(cx, cy, R * 1.03, ang), point(cx, cy, R * 0.25, ang)
        width = max(1, int(round(G.thick * G.scale * max(G.face, 0.6))))
        if G.shadow:                                                                       # a soft shadow on the face, offset down and right
            dx, dy = 3 * G.scale, 4 * G.scale
            G.needle.append(graph.draw_line((base[0] + dx, base[1] + dy), (tip[0] + dx, tip[1] + dy), color='#8A7050', width=width))
        colour = tempo_color(tempo_state(bpm)) if G.needle_colour == 'tempo colour' else NEEDLE_COLOURS.get(G.needle_colour, '#14100C')
        G.needle.append(graph.draw_line(base, tip, color=colour, width=width))


def refresh(window, now):
    if G.bpm is not None and now - G.last_note_t > SILENCE:
        G.bpm, G.onsets = None, []
        if G.est is not None:
            G.est.reset()
    state = tempo_state(G.bpm)
    bpm_text = (f'{G.bpm:.0f}' if G.conf >= 0.55 else f'≈{G.bpm:.0f}') if G.bpm else '-'
    state_text = {'slow': 'slow', 'ok': 'on target', 'fast': 'fast'}.get(state, 'waiting')
    loud = f'{G.last_loud:.0f} {level_name(G.last_loud)}  ·  {G.last_vel}' if G.last_loud else ''
    loud_color = level_color(G.last_loud) if G.last_loud else C_AXIS_TEXT
    lit = now < G.dot_until
    if G.line_mode:
        window[K_BPM2].update(bpm_text, text_color=tempo_color(state))
        window[K_STATE2].update(state_text, text_color=tempo_color(state) if state else C_AXIS_TEXT)
        window[K_LOUD2].update(loud, text_color=loud_color)
        window[K_DOT2].update(text_color=C_DOT if lit else C_LAMP_OFF)
        bar_key = (None if G.bpm is None else round(G.bpm * 2), G.range_pct, G.target, G.tol)
        if G.frame_key != bar_key:
            G.frame_key = bar_key
            draw_bar(window, G.bpm)
        return
    window[K_BPM].update(bpm_text, text_color=tempo_color(state))
    window[K_STATE].update(state_text, text_color=tempo_color(state) if state else C_AXIS_TEXT)
    window[K_LOUD].update(loud, text_color=loud_color)
    window[K_DOT].update(text_color=C_DOT if lit else C_LAMP_OFF)
    update_dial(window, G.bpm)
    if G.strip_span is not None and now - G.strip_drawn > 0.25:
        draw_strip(window, now)


def draw_strip(window, now):
    """The tempo strip: time runs left to right from the first note; once the span is full the last `span` seconds scroll past.
    The target line and its bracket band cross it; readings are coloured like the number and joined where playing was continuous"""
    graph = window[K_STRIP]
    w, h = graph.get_size()
    if not w or w < 40 or G.strip_span is None:
        return
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, h), (w, 0))
    graph.erase()
    span = G.strip_span
    t0 = G.strip_t0 if G.strip_t0 is not None else now
    left = t0 if now - t0 <= span else now - span
    y_of = lambda bpm: h - gauge_frac(bpm) * (h - 4) - 2
    lo, hi = G.target * (1 - G.tol / 100), G.target * (1 + G.tol / 100)
    graph.draw_rectangle((0, y_of(hi)), (w, y_of(lo)), fill_color='#155A22', line_width=0)
    graph.draw_line((0, y_of(G.target)), (w, y_of(G.target)), color=C_ON, width=1)
    small = (FONT_FAMILY, -max(8, int(9 * G.scale)), 'bold')
    graph.draw_text(f'{G.target}', (3, y_of(G.target)), color=C_ON, font=small, text_location=sg.TEXT_LOCATION_LEFT)
    graph.draw_text(f'{G.target * (1 + G.range_pct / 100):.0f}', (3, 2), color=C_AXIS_TEXT, font=small, text_location=sg.TEXT_LOCATION_TOP_LEFT)
    graph.draw_text(f'{G.target * (1 - G.range_pct / 100):.0f}', (3, h - 1), color=C_AXIS_TEXT, font=small, text_location=sg.TEXT_LOCATION_BOTTOM_LEFT)
    graph.draw_text(f'{span // 60}:{span % 60:02d}' if span >= 120 else f'{span} s', (w - 3, 2), color=C_AXIS_TEXT, font=small, text_location=sg.TEXT_LOCATION_TOP_RIGHT)
    pts = [((t - left) / span * w, y_of(bpm), tempo_color(tempo_state(bpm))) for t, bpm in G.samples if t >= left]
    for (x0, y0, c0), (x1, y1, c1) in zip(pts, pts[1:]):
        if x1 - x0 < w / 8:
            graph.draw_line((x0, y0), (x1, y1), color=c1, width=max(2, int(2 * G.scale)))
    r = max(2, int(2 * G.scale))
    for x, y, c in pts:
        graph.draw_circle((x, y), r, fill_color=c, line_color=c)
    G.strip_drawn = now


def show_strip(window):
    on = G.strip_span is not None and not G.line_mode
    window[K_STRIP_ROW].update(visible=on)
    if on:
        window[K_STRIP].set_size((int(360 * G.scale * G.face), int(48 * G.scale * max(G.face, 0.7))))
        G.strip_drawn = 0.0


def draw_bar(window, bpm):
    """One-line mode's meter: a bar that fills from the left - the target sits in the middle, the bracket band around it,
    half the target at the left end and one and a half times it at the right; the fill takes the tempo colour"""
    graph = window[K_BAR]
    w, h = graph.get_size()
    if not w or w < 10:
        return
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, 0), (w, h))
    graph.erase()
    graph.draw_rectangle((0, 0), (w - 1, h - 1), fill_color='#1A1E24', line_color='#3A4048')
    lo_x, hi_x = w * gauge_frac(G.target * (1 - G.tol / 100)), w * gauge_frac(G.target * (1 + G.tol / 100))
    graph.draw_rectangle((lo_x, 1), (hi_x, h - 2), fill_color='#155A22', line_width=0)
    if bpm is not None:
        graph.draw_rectangle((1, 2), (max(2, w * gauge_frac(bpm)), h - 3), fill_color=tempo_color(tempo_state(bpm)), line_width=0)
    graph.draw_line((w / 2, 0), (w / 2, h), color='#FFFFFF', width=max(1, int(G.scale)))


def set_line_mode(window, on):
    """One-line mode: just the lamp, the tempo, its verdict and the loudness in a strip that sits over other programs"""
    G.line_mode = on
    window[K_CONTROLS].update(visible=False)
    window[K_TOGGLE_CONTROLS].update(text_color=C_GEAR_HIDDEN)
    window[K_FACE].update(visible=not on)
    window[K_LINE_ROW].update(visible=on)
    show_strip(window)
    sg.user_settings_set_entry(K_LINE_MODE, on)
    sg.user_settings_set_entry(K_CONTROLS_HIDDEN, True)
    G.frame_key = None
    refresh(window, time.monotonic())


# ---------- MIDI ----------
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
        G.status, G.status_ok = 'No MIDI input - plug in the piano, then tap ⟳', False
    else:
        try:
            G.port = mido.open_input(name, callback=midi_callback)
            G.status, G.status_ok = f'Listening on {name}', True
        except Exception as e:
            G.status, G.status_ok = f'Cannot open {name}: {e}', False
    if G.window is not None:
        G.window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)


# ---------- Touch picker ----------
def label_of(c):
    """How a choice is shown: seconds up to 120 as '90 s', longer as m:ss"""
    if isinstance(c, int):
        return f'{c} s' if c <= 120 else f'{c // 60}:{c % 60:02d}'
    return str(c)


def touch_pick(title, choices, current, steps, presets=None):
    """A big touch picker: a grid of buttons for a list, or a slider with step buttons for a range - and, with `presets`, a row of
    jump buttons above the slider (jump to a common value, then fine-tune with the slider or the steps)"""
    idx = choices.index(current) if current in choices else 0
    if steps is None:
        per_row, width = 5, max(6, max(len(str(c)) for c in choices))
        rows = [[sg.Button(str(c), key=KT_PICK(c), size=(width, 2), font=FONT_PICK) for c in choices[i:i + per_row]] for i in range(0, len(choices), per_row)]
        layout = [[sg.Text(title, font=FONT_PICK)]] + rows + [[sg.Button('Cancel', key=K_PICK_CANCEL, size=(8, 2), font=FONT_PICK)]]
    else:
        slider = sg.Slider((0, len(choices) - 1), default_value=idx, orientation='h', size=(40, 36), enable_events=True, disable_number_display=True, key=K_PICK_SLIDER)
        layout = [[sg.Text(title, font=FONT_PICK)], [sg.Text(label_of(current), key=K_PICK_VAL, font=FONT_PICK_VALUE, size=(7, 1), justification='c')]]
        if presets:
            layout.append([sg.Button(label_of(c), key=KT_PICK(c), size=(6, 2), font=FONT_PICK) for c in presets if c in choices])
        layout += [[sg.Text(label_of(choices[0]), font=FONT_PICK), slider, sg.Text(label_of(choices[-1]), font=FONT_PICK)],
                  [sg.Button(label, key=KT_STEP(delta), size=(max(5, len(label)), 2), font=FONT_PICK) for delta, label in steps],
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
            if steps is None:                                    # list picker: the tap is the answer
                result = event[1]
                break
            idx = choices.index(event[1])                        # slider picker: a preset moves the slider, OK confirms
            win[K_PICK_VAL].update(label_of(choices[idx]))
            win[K_PICK_SLIDER].update(idx)
            continue
        if event == K_PICK_SLIDER:
            idx = int(float(win[K_PICK_SLIDER].TKScale.get()))
            win[K_PICK_VAL].update(label_of(choices[idx]))
        if isinstance(event, tuple) and event[0] == K_STEP:
            idx = max(0, min(len(choices) - 1, idx + event[1]))
            win[K_PICK_VAL].update(label_of(choices[idx]))
            win[K_PICK_SLIDER].update(idx)
    win.close()
    return result


PICKERS = {K_TARGET: ('Target tempo (bpm)', TARGET_CHOICES, STEPS_1_10), K_TOL: ('On-tempo bracket (+- %)', TOL_CHOICES, STEPS_1),
           K_NEEDLE: ('Needle colour', NEEDLE_CHOICES, None), K_RANGE: ('Meter range (+- % of the target)', RANGE_CHOICES, None),
           K_THICK: ('Needle thickness (px)', THICK_CHOICES, STEPS_1), K_STRIP_SPAN: ('Tempo strip: time shown', STRIP_CHOICES, STRIP_STEPS),
           K_RESPONSE: ('How quickly the reading follows', RESPONSE_CHOICES, None),
           K_BEAT: ('Beat value of your notes', BEAT_CHOICES, None), K_TEXT_SIZE: ('Text size', TEXT_SIZE_CHOICES, None),
           K_FACE_SIZE: ('Size of the main display', FACE_SIZE_CHOICES, None)}


def edit_value(window, key, values):
    title, choices, steps = PICKERS[key]
    current = next((c for c in choices if str(c) == str(values.get(key))), choices[0])
    chosen = touch_pick(title, choices, current, steps, presets=STRIP_PRESETS if key == K_STRIP_SPAN else None)
    if chosen is not None and chosen != current:
        window[key].update(str(chosen))
        window.write_event_value(K_REBUILD if key in (K_TEXT_SIZE, K_FACE_SIZE) else K_RECALC, key)


def ival(values, key, default):
    try:
        return int(float(values[key]))
    except (TypeError, ValueError, KeyError):
        return default


def save_settings(window, values):
    window.settings_save({k: v for k, v in values.items() if k in window.key_dict})
    sg.user_settings_set_entry(K_CONTROLS_HIDDEN, not window[K_CONTROLS].visible)


# ---------- Window ----------
def build_window(ports, port):
    sg.set_options(font=FONT_UI)

    def field(default, key, width, tooltip):
        """A read-only value box and a big pencil, with room around them so a finger lands on the right one"""
        return [sg.Input(str(default), key=key, size=(width, 1), readonly=True, setting=default, justification='c', font=FONT_MID, pad=((4, 2), 4),
                         tooltip=tooltip + '  (tap for a big picker)'),
                sg.Text('\u270E', key=KT_EDIT(key), enable_events=True, text_color=C_EDIT, font=FONT_LINE, pad=((0, 18), 0), tooltip='Change: ' + tooltip)]

    label = lambda text: sg.Text(text, size=(7, 1), justification='r', pad=((6, 2), 0))
    controls = [[label('MIDI in'), sg.Combo(ports, default_value=port, key=K_PORT, size=(20, 1), readonly=True, enable_events=True, pad=((4, 2), 6)),
                 sg.Text('⟳', key=K_REFRESH, font=FONT_LINE, text_color=C_EDIT, enable_events=True, pad=((4, 0), 0), tooltip='Look for MIDI ports again')],
                [label('Target'), *field(92, K_TARGET, 5, TT_TARGET), label('±'), *field(5, K_TOL, 4, TT_TOL), sg.Text('%', pad=((0, 6), 0))],
                [label('Beat'), *field('auto', K_BEAT, 12, TT_BEAT), label('Range ±'), *field(50, K_RANGE, 4, TT_RANGE), sg.Text('%', pad=((0, 6), 0))],
                [label('Needle'), *field('black', K_NEEDLE, 12, TT_NEEDLE), label('Thick'), *field(2, K_THICK, 4, TT_THICK),
                 sg.Checkbox('shadow', key=K_SHADOW, default=True, setting=True, pad=((0, 6), 0), tooltip='The needle casts a shadow on the face'),
                 sg.Checkbox('on top', key=K_ON_TOP, default=True, setting=True, enable_events=True, pad=((10, 6), 0), tooltip='Keep the widget above other windows')],
                [label('Text'), *field('100%', K_TEXT_SIZE, 6, 'Size of all text'), label('Strip'), *field('off', K_STRIP_SPAN, 4, TT_STRIP), sg.Text('s', pad=((0, 6), 0))],
                [label('Response'), *field('normal', K_RESPONSE, 8, TT_RESPONSE), label('Size'), *field('large', K_FACE_SIZE, 7, TT_FACE_SIZE)],
                [sg.Text('', key=K_STATUS, font=FONT_LABEL, size=(50, 1), pad=((8, 4), (2, 6)))]]
    face = [[sg.Text('●', key=K_DOT, font=FONT_FACE_MID, size=(1, 1), text_color=C_LAMP_OFF, pad=((8, 0), (4, 0))),
             sg.Text('T E M P O', font=FONT_FACE_LABEL, text_color=C_AMBER, background_color=C_BG_FACE, pad=((4, 0), (4, 0))),
             sg.Push(background_color=C_BG_FACE),
             sg.Text('✕', key=K_CLOSE, font=FONT_FACE_TAP, text_color=C_AXIS_TEXT, enable_events=True, pad=((4, 10), (2, 0)), tooltip='Close (ESC)')],
            [sg.Text('-', key=K_BPM, font=FONT_FACE_BIG, size=(4, 1), justification='c', text_color=C_AXIS_TEXT, pad=((8, 0), 0)),
             sg.Graph((210, 120), (0, 120), (210, 0), key=K_GAUGE, background_color=C_BG_FACE, pad=((6, 10), 0))],
            [sg.Text('▬', key=K_LINE, font=FONT_FACE_TAP, text_color=C_AXIS_TEXT, enable_events=True, pad=((10, 6), (0, 6)), tooltip='Collapse to one line'),
             sg.Text('waiting', key=K_STATE, font=FONT_FACE_MID, text_color=C_AXIS_TEXT, size=(10, 1), pad=((0, 0), (0, 6))),
             sg.Push(background_color=C_BG_FACE), sg.Text('', key=K_LOUD, font=FONT_FACE_MID, text_color=C_AXIS_TEXT, size=(11, 1), justification='r', pad=((0, 6), (0, 6)),
                                tooltip='Last note: loudness 1-10 and its MIDI velocity'),
             sg.Text('⚙', key=K_TOGGLE_CONTROLS, font=FONT_FACE_TAP, text_color=C_AXIS_TEXT, enable_events=True, pad=((4, 10), (0, 6)), tooltip='Settings (F10)')],
            [sg.pin(sg.Column([[sg.Graph((360, 48), (0, 48), (360, 0), key=K_STRIP, background_color='#0B0E12', pad=((8, 8), (0, 8)), expand_x=True)]],
                              key=K_STRIP_ROW, pad=(0, 0), background_color=C_BG_FACE, expand_x=True, visible=False), expand_x=True)]]
    line = [[sg.Text('▣', key=K_EXPAND, font=FONT_MID, text_color=C_AXIS_TEXT, enable_events=True, pad=((8, 4), 3), tooltip='Back to the full widget'),
             sg.Text('●', key=K_DOT2, font=FONT_MID, size=(1, 1), text_color=C_LAMP_OFF, pad=((2, 0), 3)),
             sg.Text('T E M P O', font=FONT_LABEL, text_color=C_AMBER, background_color=C_BG_FACE, pad=((4, 6), 3)),
             sg.Text('-', key=K_BPM2, font=FONT_LINE, size=(4, 1), justification='c', text_color=C_AXIS_TEXT, pad=((0, 4), 3)),
             sg.Text('waiting', key=K_STATE2, font=FONT_MID, size=(9, 1), text_color=C_AXIS_TEXT, pad=((0, 8), 3)),
             sg.Graph((120, 14), (0, 0), (120, 14), key=K_BAR, background_color=C_BG_FACE, pad=((0, 8), 3), tooltip='Tempo bar: fills to the right the faster you play'),
             sg.Text('', key=K_LOUD2, font=FONT_MID, size=(12, 1), justification='r', text_color=C_AXIS_TEXT, pad=((0, 8), 3), tooltip='Last note: loudness and velocity'),
             sg.Text('✕', key=K_CLOSE2, font=FONT_MID, text_color=C_AXIS_TEXT, enable_events=True, pad=((6, 10), 3), tooltip='Close (ESC)')]]
    layout = [[sg.pin(sg.Column(controls, key=K_CONTROLS, pad=(0, 0)))],
              [sg.pin(sg.Column(face, key=K_FACE, pad=(0, 0), expand_x=True, background_color=C_BG_FACE), expand_x=True)],
              [sg.pin(sg.Column(line, key=K_LINE_ROW, pad=(0, 0), expand_x=True, background_color=C_BG_FACE, visible=False), expand_x=True)]]
    window = sg.Window(APP_TITLE, layout, no_titlebar=True, keep_on_top=True, grab_anywhere=True, finalize=True, margins=(0, 0), auto_save_location=True,
                       right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, element_padding=(3, 2), background_color=C_BG_FACE)
    G.window = window
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)
    for key in (K_DOT, K_BPM, K_STATE, K_LOUD, K_TOGGLE_CONTROLS, K_CLOSE, K_LINE, K_DOT2, K_BPM2, K_STATE2, K_LOUD2, K_EXPAND, K_CLOSE2):
        window[key].widget.configure(background=C_BG_FACE)
    window[K_BAR].set_size((int(120 * G.scale), int(14 * G.scale)))
    G.face_key = G.frame_key = None
    update_dial(window, None)
    window.bind('<Escape>', K_KEY_ESC)
    window.bind('<F10>', K_KEY_F10)
    window.keep_on_top_set() if window[K_ON_TOP].get() else window.keep_on_top_clear()
    for key in PICKERS:
        window[key].bind('<Button-1>', TAP)
        window[key].widget.configure(readonlybackground=sg.theme_input_background_color())
    if sg.user_settings_get_entry(K_CONTROLS_HIDDEN, False):
        window[K_CONTROLS].update(visible=False)
        window[K_TOGGLE_CONTROLS].update(text_color=C_GEAR_HIDDEN)
    window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)
    if sg.user_settings_get_entry(K_LINE_MODE, False):
        set_line_mode(window, True)
    window.timer_start(60)
    return window


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    sg.theme('DarkGrey13')
    sg.set_options(font=FONT_UI, dpi_awareness=True, icon=ICON)
    face_size = sg.user_settings_get_entry(K_FACE_SIZE, 'large')
    G.face = FACE_MULT.get(face_size, 1.0)
    set_fonts(sg.user_settings_get_entry(K_TEXT_SIZE, '100%'), face_size)
    ports = midi_ports()
    saved_port = sg.user_settings_get_entry(K_PORT, '')
    port = saved_port if saved_port in ports else (ports[0] if ports else '')
    open_port(port)
    window = build_window(ports, port)
    auto_close = time.monotonic() + float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None
    demo_next, demo_bpm = 0.0, 0
    if '--demo' in sys.argv:
        demo_bpm = float(sys.argv[sys.argv.index('--demo') + 1]) if len(sys.argv) > sys.argv.index('--demo') + 1 and sys.argv[sys.argv.index('--demo') + 1][0].isdigit() else 80
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in (K_CLOSE, K_CLOSE2, K_KEY_ESC, 'Exit') or (auto_close and time.monotonic() > auto_close):
            save_settings(window, values)
            break
        now = time.monotonic()
        G.target, G.tol = ival(values, K_TARGET, 92), ival(values, K_TOL, 5)
        G.beat = values.get(K_BEAT) if values.get(K_BEAT) in BEAT_CHOICES else 'auto'
        G.needle_colour = values.get(K_NEEDLE) if values.get(K_NEEDLE) in NEEDLE_CHOICES else 'black'
        G.response = values.get(K_RESPONSE) if values.get(K_RESPONSE) in RESPONSE_CHOICES else 'normal'
        G.range_pct = ival(values, K_RANGE, 50) if ival(values, K_RANGE, 50) in RANGE_CHOICES else 50
        G.thick, G.shadow = ival(values, K_THICK, 2), bool(values.get(K_SHADOW, True))
        span = None if str(values.get(K_STRIP_SPAN, 'off')) == 'off' else ival(values, K_STRIP_SPAN, 30)
        if span != G.strip_span:
            G.strip_span = span
            show_strip(window)
        if event == sg.EVENT_TIMER:
            if demo_bpm and now >= demo_next:                                              # --demo [bpm]: triplet eighths at that tempo, a little uneven
                import random
                demo_i = getattr(G, 'demo_i', 0)
                G.demo_i = demo_i + 1
                note_on(demo_next or now, random.randint(55, 80) + (14 if demo_i % 3 == 0 else 0))                 # triplets, beats accented
                demo_next = (demo_next or now) + 60.0 / demo_bpm / 3 * random.uniform(0.96, 1.04)
            refresh(window, now)
        elif event == K_MIDI_NOTE:
            note_on(values[K_MIDI_NOTE][0], values[K_MIDI_NOTE][2])
            refresh(window, now)
        elif event == K_RECALC:
            refresh(window, now)
        elif event == K_REBUILD:
            save_settings(window, values)
            G.face = FACE_MULT.get(values.get(K_FACE_SIZE), 1.0)
            set_fonts(values[K_TEXT_SIZE], values.get(K_FACE_SIZE, 'large'))
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
        elif event == K_ON_TOP:
            window.keep_on_top_set() if values[K_ON_TOP] else window.keep_on_top_clear()
        elif event == K_LINE:
            set_line_mode(window, True)
        elif event == K_EXPAND:
            set_line_mode(window, False)
        elif event in (K_TOGGLE_CONTROLS, K_KEY_F10):
            if G.line_mode:
                set_line_mode(window, False)
            on = not window[K_CONTROLS].visible
            window[K_CONTROLS].update(visible=on)
            window[K_TOGGLE_CONTROLS].update(text_color=C_AXIS_TEXT if on else C_GEAR_HIDDEN)
            sg.user_settings_set_entry(K_CONTROLS_HIDDEN, not on)
        elif event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
    window.timer_stop_all()
    close_port()
    window.close()


if __name__ == '__main__':
    main()
