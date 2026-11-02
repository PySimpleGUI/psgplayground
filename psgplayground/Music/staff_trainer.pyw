"""
Staff Trainer  (staff_trainer.pyw)  -  flashcards on a grand staff, answered on the piano; the next card deals itself.

CARD TYPES (the MIX row sets how often each one comes up, 0 = never .. 5 = often):
  Notes            one written note - play it
  Interval written two written notes - play both together
  Interval named   one written note plus a label such as "M6 above" or "P5 below" - play both notes
  Triad written    a written triad (major / minor / diminished / augmented), in root position or an inversion - play it as written
  Written cards show only their kind ("Interval", "Triad" ...) while you work them out - say the answer aloud - and reveal the
  name (m3, "Eb minor, 2nd inversion", "F#4") in green once you have played it.
  Triad named      a chord name such as "F major, 1st inversion" - play it in any octave; the lowest note decides the inversion
  7th written      a written seventh chord (dominant, major, minor, half-diminished, diminished 7th) - play it as written
  7th named        e.g. "G dominant 7th, 3rd inversion" - play it in any octave
  Melody           a short line of written notes - play them in order (each one turns green as you get it)
Right notes = green, then the next card after "Next delay".  A wrong note is drawn in red at its own place on the staff so you can see
how far off you were; keep trying until it is right.  Named cards reveal the notes you played in green.

OPTIONS: Range (treble / bass / both / whole piano), Accidentals (sharps and flats; for chords this means roots with black keys),
Inversions (chord cards may be inverted), Melody notes (2-8), Next delay (seconds the green card stays).
TILES: first-try accuracy, average response time, streak / best, cards done, accuracy per card type, and a miss heat-map keyboard.

TOUCH: every setting is a read-only value box followed by a small pencil mark; tapping the box or the pencil opens a big picker.
TEXT SIZE: one multiplier for every font; changing it rebuilds the window in place (stats and the MIDI connection are kept).
FULL (F11) covers the whole screen with no title bar; F10 hides / shows the control rows; F9 = Start / Pause; SPACE skips the card;
HOME resets the statistics; ESC exits.  Demo checkbox answers the cards by itself (mostly right).
Requires:  pip install PySimpleGUI mido python-rtmidi
Settings persist in SETTINGS_FILE (staff_trainer.json in the PySimpleGUI settings folder) via Window.settings_save() at exit;
the MIDI port, fullscreen and hidden-controls state are saved as they change.  "Demo" is deliberately not saved.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import random
import sys
import time
import tkinter.font as tkfont

import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAABgFBMVEUdGhcAAAD+xDz6+fUiHhn/00AOCwns6eT/yzMnJCH/xDxItP5oUyRkYVwkIRuuq6dK122xiy//qlVNwv7/AAD/uzosTGJGrfX//wBVRSFO5nTyvTr/xTz+yUD/fwAoRistWTRHzGn81XZnZmLGmjPOpDX/xztEumAtNClANR2Yeiz/qjH/wjz/yD7/1yf/10D//1AuUmoybz1iXVeT1/dYV1mFbCm2kjS32e7+0T49sv3Z2+I0d0E4iEk6rv92xPLLpUfZtDnO6vr/mTP/qgD/vzvlvWD/wjz/0kH/4Tz//38mRVhDmcweIB87mFA+olVNSkZcfJFFocx3aClsv/iQwJiOzPK+u7W57f/Fwr3e29bF78r33ZUUIikZNkgoPUsyY4E3dJosdqI9irI6z2A70mJArVtV0P99s9SVgjCc5P+no57D8v/2554AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYEX7rAAAAgHRSTlP/AP7///7//wX/rP////////8D/wEG//8B////df8C/////////zr/////B4PDBlYG////////////////////////BQM4/0ysEQL//////////////////////////////////////////////wAAAAAAAAAAAAAAAAAAAAAAABDZ8NMAAAYwSURBVHja7Ztnd9s2FIZBioQoUYFFSoxFTcuWvLdlyU7t2k6b7WY3TZt07/X/vxbgpjjEAZruOXqd2IkI8j7EuLgGLgCTs8AcIPhSvSFQUqMeH0BW6L6oIscBqMsCw3T3hTIlCftdhhHkekSABnn51b0yy/KUxLLlvVVSDY0oALiQ0n7M4rtoimcftxXt4bMAZEbZYzuUzWsIHXZPYeQZAA2ZebKTgXWDYecJIzfCADDfdmbmNYRtZqoSXABdZqudqX1M0N7CZgIAPmceTBenNAhceoAN+QLIW6vOsnyLHagVClIHbMv14NUt2Q+g/pRxmZcQ4iCgIMghJLkQmKd1HwCZaTvKbG4Q4xwVEYiNTcfD246OaAEo+3b/54cIAAQoijxvaD9/e1+ZBqgzik1YQUDjpij8PFSxLShM3Q3QkIUd66oKAWXzGgKAqmViRzAdEjBnS9sBqBBlYB8TIJuAb5vzPTAawBoBfAWidHXNBTYfghXrNRmjEXQApWuNANz/Mnl/vRXQ0BoJXcUBsMuUTbSU9rm7WAelYAKzosvYqAUgd00fyG+mfP+SWKuJtYOgp3Bg07S02pUtgM+YR8bHrY20AIuiuCjeDQbYaBkAj7BZA6De2C0bn0owpf8hAGItEAD3Q8l41/KuFixrAIxgtEwrtfubBYARjCpgBcYLwN4EAOsBEKwxMOCyB+AG1jgQpgF4FXJZA3BQ5YMBKiB7AFCZA8wB/g8AHEoagBoAfg/Qw5xIADh6SiqgATzzv8ZFroGXK3cSakUkenXkd2mdPD0KQAl8VUgsYv/T+76XVmAkAAQXCkWsECNF1w/3JQ3gxOdasXAnBkBBYwjWJ1j+VwjAvRO/K4WjODVQWAClYGm/tKo+F5A+Cg44v7sijgITAIZMaANcnh/4lfhCH4YQJPcDFgAKBpA6rVZH8gOg4IgiAfBa/DgHmANkDMAlAaA4DEMcEZicsuzpBGToiGa44mW202GX3c55dHJxcfFuRMkVB0w15rSiAziK3B/VRFtUJqNQGQCW3oku0ZiOC18fB0cdx5ek9KVR4mjlj5obIF1AYo2CwLgMmKPAKHEwZd4dkmmLpXFCMtsPBAWeCOgAAGmh5jPRA2AGpciMRJH9T+qOqCR6ZTsiiJawEMzME3LgB699c40Ifztca2KtHQITiX4NvJ7ugeL1z9/rzQ17/aqhfs/wm9QBSq+97w8NU72qpWa1B7LpA5rvdWix9qO10G69/4vei2Y1dhOUUJCsUUB07W6C369LnF4KHlqv34Ogt3YGYw7DEBk1oOk7dw389K3lANZMgDNcJ+vNNRRrMvpmIUQPSemHxn/eOu2//dsq9KXe9rgDEkfwW7W5lNFcUByJ9/AX+XNx4rjzw6/Y/DnuiD38zOfNfmYAWP/8NRqN3r93z0Effmmer0O4dI67MxmPMQGiN0GQcBP013HrI2M8xAKI0QmDlwpIJyQEHDgj3SFWJ5wxDCeOYRgoPAz7zXPslGCPdMXqYdxhiHx2vnQHHxKUukQa/gwsLT2v6mMhvSdE4zfSYCL9OWQjABiu2HSHqV0xnt3HV3gr+hT/7UQBsCejPo3JiOy5ufbBIzQBzekY3zec2tqXoiytpwpIXFGYOp3WYoRkoUoXkrmCUu7KkwshwUjLiUmDUndYfnx56snGuDyOuYQYJyz3eH9vaklrOe4S4kryX82K/3rsd5Y/zpyzKK4TfvQALBfjKtU64WS6Cwyxsy/FVJp1wjE/lRmmJt9BT+CI8IetTsv5/pXEOR7JPCEHxg4/xJMkixutAXKbSiYibSa6GqMUKS7J5wJUkaTJQHozTre/nHg25OzvqVJ8kgPo2SkhKSrUAbLJZaGzYZFMFNcJEymeKy4WC5QVeTJKuW2XfjpOt3FJISBJt3UbGpxxN7B5HRqhzh4FKswskS1SEguFNJ4IBN40HpqJTBHSS9mQTKrWTQD4pHJRTGabad4vmY1mOt/MqcgvnY9mQuNMAN+ERoopnTOTSn1TOvNPaqWY1hveA4PSenNPbM4/tTv35Pb80/vzP+CQ/xGP3A+55H/MJ/+DTvkf9cr/sFv+x/1uwYHH/I985n/o9RYc+70NB5/nZ89vTP8BSKAuBMS2R24AAAAASUVORK5CYII='      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_TITLE = 'Staff Trainer'
SETTINGS_FILE = 'staff_trainer.json'

# ---------- Keys ----------
K_STAFF = '-STAFF-'
K_HEAT = '-HEAT-'
K_PORT = '-PORT-'
K_REFRESH = '-REFRESH-'
K_RANGE = '-RANGE-'
K_ACC = '-ACC-'
K_INV = '-INV-'
K_MELODY = '-MELODY-'
K_NEXT = '-NEXT-'
K_MIX = '-MIX-'
KT_MIX = lambda kind: f'-MIX {kind}-'                  # weight field of one card type (string key: it is stored in the settings file)
K_TEXT_SIZE = '-TEXT SIZE-'
K_REBUILD = '-REBUILD-'                # internal event: fonts changed, rebuild the window
K_RECALC = '-RECALC-'                  # internal event: a setting changed, deal a new card
K_DEMO = '-DEMO-'
K_START = '-START-'
K_SKIP = '-SKIP-'
K_RESET = '-RESET-'
K_FULL = '-FULL-'
K_EXIT = '-EXIT-'
K_STATUS = '-STATUS-'
K_LAST = '-LAST-'
K_BY_TYPE = '-BY TYPE-'
K_PICK_VAL = '-PICK VAL-'
K_PICK_OK = '-PICK OK-'
K_PICK_CANCEL = '-PICK CANCEL-'
K_PICK_SLIDER = '-PICK SLIDER-'
K_EDIT = '-EDIT-'
KT_EDIT = lambda key: (K_EDIT, key)                    # pencil beside a value box: opens the picker for that setting
K_PICK = '-PICK-'
KT_PICK = lambda choice: (K_PICK, choice)              # picker: one button per choice
K_STEP = '-STEP-'
KT_STEP = lambda delta: (K_STEP, delta)                # picker: +/- step button
TAP = ' TAP'                           # suffix added to a field's key when its value box is tapped
K_TILE = '-TILE-'
KT_TILE = lambda name: (K_TILE, name)
K_TILE_SUB = '-TILE SUB-'
KT_TILE_SUB = lambda name: (K_TILE_SUB, name)
K_MIDI_NOTE = '-MIDI NOTE-'            # event from the MIDI callback thread, value = (time, note, velocity, is_on)
K_KEY_ESC = '-KEY ESC-'
K_KEY_F9 = '-KEY F9-'
K_KEY_F10 = '-KEY F10-'
K_KEY_F11 = '-KEY F11-'
K_KEY_HOME = '-KEY HOME-'
K_KEY_SPACE = '-KEY SPACE-'
K_FULLSCREEN = '-FULLSCREEN-'
K_CONTROLS = '-CONTROLS-'
K_CONTROLS_HIDDEN = '-CONTROLS HIDDEN-'
K_EXTRAS = '-EXTRAS-'
K_TOGGLE_CONTROLS = '-TOGGLE CONTROLS-'

# ---------- Colors ----------
C_BG = '#101418'
C_PAPER = '#F4F1E8'
C_INK = '#1B1B1B'
C_STAFF_LINE = '#6B6B6B'
C_PROMPT = '#3B3489'         # named-card prompt text on the paper (dark purple)
C_RIGHT = '#1DA88F'          # green-teal - correct (dark enough to read on paper)
C_RIGHT_TILE = '#2DD4BF'
C_WRONG = '#E53935'          # red - the note actually played
C_GRID = '#2C343C'
C_AXIS_TEXT = '#9AA6B2'
C_STATUS_OK = '#69F0AE'
C_STATUS_BAD = '#FF8A65'
C_PAUSED = '#FFB300'
C_EDIT = '#4DD0E1'
C_ON_TILE = '#000000'
C_TILE_NEUTRAL = '#2C343C'
C_WHITE_KEY = '#E8E8E8'
C_BLACK_KEY = '#202020'
TILE_EASE = 0.35
ACC_STOPS = [(50, (255, 82, 82)), (75, (255, 234, 0)), (100, (0, 230, 118))]
SPEED_STOPS = [(0.6, (0, 230, 118)), (1.5, (255, 234, 0)), (3.0, (255, 82, 82))]

FONT_FAMILY = 'Segoe UI'
MONO_FAMILY = 'Consolas' if sys.platform.startswith('win') else 'DejaVu Sans Mono'
CLEF_FAMILY = 'Segoe UI Symbol' if sys.platform.startswith('win') else 'FreeSerif'
BASE_FONTS = {'FONT_UI': 12, 'FONT_LABEL': 11, 'FONT_BIG': 26, 'FONT_LAST': 14, 'FONT_TYPES': 11, 'FONT_PICK': 20, 'FONT_PICK_VALUE': 48}
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
LETTER_PC = [0, 2, 4, 5, 7, 9, 11]
NOTE_NAMES = ('C', 'C♯', 'D', 'D♯', 'E', 'F', 'F♯', 'G', 'G♯', 'A', 'A♯', 'B')
NOTE_NAMES_FLAT = ('C', 'D♭', 'D', 'E♭', 'E', 'F', 'G♭', 'G', 'A♭', 'A', 'B♭', 'B')
FLAT_ROOTS = {1, 3, 8, 10}
RANGES = {'Treble C4-C6': (60, 84), 'Bass C2-C4': (36, 60), 'Both C2-C6': (36, 84), 'Wide A0-C8': (21, 108)}
RANGE_CHOICES = list(RANGES)
MELODY_CHOICES = list(range(2, 9))
NEXT_CHOICES = [0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]
MIX_CHOICES = [0, 1, 2, 3, 4, 5]
BLACK_PCS = {1, 3, 6, 8, 10}
WRONG_SHOW = 1.2                       # seconds a red (wrong) note stays on the staff
INTERVALS = [(1, 'm2'), (2, 'M2'), (3, 'm3'), (4, 'M3'), (5, 'P4'), (6, 'tritone'), (7, 'P5'), (8, 'm6'), (9, 'M6'), (10, 'm7'), (11, 'M7'), (12, 'P8')]
INTERVAL_STEPS = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5, 9: 5, 10: 6, 11: 6, 12: 7}     # letter steps of each interval (tritone as an augmented 4th)
TRIADS = {'major': (0, 4, 7), 'minor': (0, 3, 7), 'diminished': (0, 3, 6), 'augmented': (0, 4, 8)}
SEVENTHS = {'dominant 7th': (0, 4, 7, 10), 'major 7th': (0, 4, 7, 11), 'minor 7th': (0, 3, 7, 10), 'half-diminished 7th': (0, 3, 6, 10), 'diminished 7th': (0, 3, 6, 9)}
INVERSION_NAMES = ('root position', '1st inversion', '2nd inversion', '3rd inversion')
KIND_NOTE, KIND_INT_W, KIND_INT_N, KIND_TRIAD_W, KIND_TRIAD_N, KIND_7_W, KIND_7_N, KIND_MELODY = 'Notes', 'Int written', 'Int named', 'Triad written', 'Triad named', \
    '7th written', '7th named', 'Melody'
KINDS = (KIND_NOTE, KIND_INT_W, KIND_INT_N, KIND_TRIAD_W, KIND_TRIAD_N, KIND_7_W, KIND_7_N, KIND_MELODY)
MIX_DEFAULT = {KIND_NOTE: 3, KIND_INT_W: 1, KIND_INT_N: 1, KIND_TRIAD_W: 1, KIND_TRIAD_N: 1, KIND_7_W: 0, KIND_7_N: 0, KIND_MELODY: 1}
TT_RANGE = 'Where the cards come from: treble staff, bass staff, both, or the whole piano with ledger lines'
TT_MELODY = 'Notes in a melody card'
TT_NEXT = 'Seconds the green (answered) card stays before the next one'
TT_MIX = 'How often this card type comes up: 0 = never, 5 = most often (weights are relative)'
T_ACC, T_SPEED, T_STREAK, T_CARDS = 'FIRST-TRY ACCURACY', 'AVG RESPONSE', 'STREAK / BEST', 'CARDS DONE'


class Card:
    """kind, notes = exact pitches expected (or the canonical voicing for named chords), written = pitches drawn before answering,
    prompt = text for named cards, seq = play in order, match = 'exact' | 'pcs_bass', prefer_flat = spelling, label = type text"""
    def __init__(self, kind, notes, written, prompt='', seq=False, match='exact', prefer_flat=False, label='', spellings=None, reveal=''):
        self.kind, self.notes, self.written, self.prompt, self.seq, self.match, self.prefer_flat, self.label = kind, notes, written, prompt, seq, match, prefer_flat, label
        self.spellings = spellings or {}                     # pitch -> (step, accidental) when a note must be spelled relative to another (intervals)
        self.reveal = reveal                                 # the answer's name, shown once the card is played (written cards: identify it yourself first)
        self.pcs, self.bass_pc = {p % 12 for p in notes}, min(notes) % 12


class G:                                # program-wide state
    window = None
    port = None
    status = ''
    status_ok = False
    scale = 1.0
    fullscreen = False
    text_px = {}
    tile_target = {}
    tile_now = {}
    running = False
    card = None
    t_shown = 0.0
    first_try = True
    next_at = None
    held = set()
    seq_idx = 0                         # melody cards: how many notes have been played correctly
    reveal = []                         # named cards: the pitches played, drawn in green after the answer
    wrong = []                          # (pitch, prefer_flat, expire time)
    stats = {'cards': 0, 'first': 0, 'times': [], 'streak': 0, 'best': 0}
    by_type = {}                        # kind -> [first-try right, total]
    misses = {}
    next_delay = 0.8
    demo_next_t = 0.0
    demo_card = None
    demo_seq = []
    demo_erred = False


# ---------- Notation helpers ----------
def spell(pitch, prefer_flat):
    """MIDI pitch -> (staff step, accidental).  Step 0 = middle C, +1 per letter name."""
    pc, octave = pitch % 12, pitch // 12 - 1
    if pc in LETTER_PC:
        letter, acc = LETTER_PC.index(pc), ''
    elif prefer_flat:
        letter, acc = LETTER_PC.index(pc + 1), '♭'
    else:
        letter, acc = LETTER_PC.index(pc - 1), '♯'
    return (octave - 4) * 7 + letter, acc


def step_pitch(step):
    """MIDI pitch of the natural note on a staff step (step 0 = middle C)"""
    return 12 * (5 + step // 7) + LETTER_PC[step % 7]


def spell_relative(base, base_step, other, steps):
    """Spell `other` on the letter `steps` above (or below) the base note's letter, if that needs at most one sharp or flat"""
    step = base_step + steps if other > base else base_step - steps
    alter = other - step_pitch(step)
    return (step, {0: '', 1: '♯', -1: '♭'}[alter]) if alter in (-1, 0, 1) else None


def note_name(pitch, prefer_flat=False):
    return (NOTE_NAMES_FLAT if prefer_flat else NOTE_NAMES)[pitch % 12] + str(pitch // 12 - 1)


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


# ---------- Card factory ----------
def pick_kind(weights):
    kinds = [k for k in KINDS if weights.get(k, 0) > 0] or [KIND_NOTE]
    return random.choices(kinds, [weights.get(k, 1) for k in kinds])[0]


def white_pool(lo, hi, accidentals):
    return [p for p in range(lo, hi + 1) if accidentals or not is_black(p)]


def make_chord(kind, lo, hi, accidentals, inversions):
    """A triad / seventh, written or named.  Roots with black keys only when accidentals are on; inversions only when allowed."""
    table = TRIADS if kind in (KIND_TRIAD_W, KIND_TRIAD_N) else SEVENTHS
    for _ in range(200):
        quality, ivs = random.choice(list(table.items()))
        root = random.randrange(12)
        inv = random.randrange(len(ivs)) if inversions else 0
        voicing = sorted([ivs[(i + inv) % len(ivs)] + (12 if i + inv >= len(ivs) else 0) for i in range(len(ivs))])
        voicing = [v - voicing[0] for v in voicing]                                    # bass = 0
        bass_pc = (root + ivs[inv]) % 12
        if not accidentals and any(is_black(root + iv) for iv in ivs):
            continue
        span = voicing[-1]
        bass_choices = [p for p in range(lo, hi - span + 1) if p % 12 == bass_pc]
        if not bass_choices:
            continue
        bass = random.choice(bass_choices)
        notes = [bass + v for v in voicing]
        prefer_flat = root in FLAT_ROOTS or (root == 6 and random.random() < 0.5)
        name = f'{(NOTE_NAMES_FLAT if prefer_flat else NOTE_NAMES)[root]} {quality}, {INVERSION_NAMES[inv]}'
        if kind in (KIND_TRIAD_W, KIND_7_W):
            return Card(kind, notes, notes, prefer_flat=prefer_flat, label='Triad' if kind == KIND_TRIAD_W else 'Seventh', reveal=name)
        return Card(kind, notes, [], prompt=name, match='pcs_bass', prefer_flat=prefer_flat, label='play it in any octave - the lowest note sets the inversion')
    return make_note(lo, hi, accidentals)


def make_note(lo, hi, accidentals):
    p = random.choice(white_pool(lo, hi, accidentals))
    prefer_flat = random.random() < 0.5
    return Card(KIND_NOTE, [p], [p], prefer_flat=prefer_flat, label='Note', reveal=note_name(p, prefer_flat))


def make_interval(kind, lo, hi, accidentals):
    pool = white_pool(lo, hi, accidentals)
    for _ in range(200):
        base = random.choice(pool)
        semis, name = random.choice(INTERVALS)
        up = random.random() < 0.7
        other = base + semis if up else base - semis
        if other not in pool:
            continue
        prefer_flat = random.random() < 0.5
        base_step, base_acc = spell(base, prefer_flat)
        spelled = spell_relative(base, base_step, other, INTERVAL_STEPS[semis])          # the other note on the interval's own letter: a m3 is never written as an augmented 2nd
        if spelled is None and semis == 6:
            spelled = spell_relative(base, base_step, other, 4)                          # tritone as a diminished 5th instead
        if spelled is None:
            prefer_flat = not prefer_flat                                                # try the base with the other accidental
            base_step, base_acc = spell(base, prefer_flat)
            spelled = spell_relative(base, base_step, other, INTERVAL_STEPS[semis])
        if spelled is None:
            continue
        spellings = {base: (base_step, base_acc), other: spelled}
        if kind == KIND_INT_W:
            return Card(kind, [base, other], [base, other], prefer_flat=prefer_flat, label='Interval', spellings=spellings, reveal=f'Interval:  {name}')
        return Card(kind, [base, other], [base], prompt=f'{name} {"above" if up else "below"}', prefer_flat=prefer_flat, label='play the written note and the named interval',
                    spellings=spellings)
    return make_note(lo, hi, accidentals)


def make_melody(lo, hi, accidentals, n_notes):
    pool = white_pool(lo, hi, accidentals)
    p = random.choice(pool)
    notes = [p]
    for _ in range(n_notes - 1):
        cands = [q for q in pool if 0 < abs(q - p) <= 7]
        p = random.choice(cands) if cands else p
        notes.append(p)
    return Card(KIND_MELODY, notes, notes, seq=True, prefer_flat=random.random() < 0.5, label='Melody · play the notes in order')


def make_card(weights, lo, hi, accidentals, inversions, n_melody):
    kind = pick_kind(weights)
    if kind == KIND_NOTE:
        return make_note(lo, hi, accidentals)
    if kind in (KIND_INT_W, KIND_INT_N):
        return make_interval(kind, lo, hi, accidentals)
    if kind == KIND_MELODY:
        return make_melody(lo, hi, accidentals, n_melody)
    return make_chord(kind, lo, hi, accidentals, inversions)


# ---------- Misc helpers ----------
def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def hexcolor(rgb_tuple):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(c)))) for c in rgb_tuple)


def mix(c1, c2, f):
    return tuple(a + (b - a) * f for a, b in zip(c1, c2))


def gradient(stops, value):
    if value <= stops[0][0]:
        return stops[0][1]
    for (v0, c0), (v1, c1) in zip(stops, stops[1:]):
        if value <= v1:
            return mix(c0, c1, (value - v0) / (v1 - v0))
    return stops[-1][1]


def ival(values, key, default):
    try:
        return int(values[key])
    except (TypeError, ValueError, KeyError):
        return default


def fval(values, key, default):
    try:
        return float(values[key])
    except (TypeError, ValueError, KeyError):
        return default


def midi_ports():
    try:
        return mido.get_input_names() if mido else []
    except Exception:
        return []


def midi_callback(msg):
    if msg.type in ('note_on', 'note_off') and G.window is not None:
        G.window.write_event_value(K_MIDI_NOTE, (time.monotonic(), msg.note, msg.velocity, msg.type == 'note_on' and msg.velocity > 0))


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


# ---------- Game ----------
def new_card(window, opts):
    G.card = make_card(*opts)
    G.t_shown, G.first_try, G.next_at, G.seq_idx = time.monotonic(), True, None, 0
    G.reveal, G.wrong = [], []


def set_running(window, on, opts):
    G.running = on
    window[K_START].update('Pause' if on else 'Start', button_color=(C_ON_TILE, C_PAUSED) if on else (C_ON_TILE, C_STATUS_OK))
    if on:
        new_card(window, opts)
    else:
        G.wrong = []


def handle_note(window, t, note, on):
    if on:
        G.held.add(note)
        check_answer(window, t, note)
    else:
        G.held.discard(note)


def card_done(window, t, reveal):
    s, c = G.stats, G.card
    s['cards'] += 1
    s['times'].append(t - G.t_shown)
    del s['times'][:-30]
    stat = G.by_type.setdefault(c.kind, [0, 0])
    stat[1] += 1
    if G.first_try:
        s['first'] += 1
        s['streak'] += 1
        s['best'] = max(s['best'], s['streak'])
        stat[0] += 1
    G.reveal = sorted(reveal)
    window[K_LAST].update(f'Correct   {t - G.t_shown:.2f} s', text_color=C_RIGHT_TILE)
    G.next_at = t + G.next_delay
    refresh_tiles(window)


def card_wrong(window, t, wrong_pitches, message='Not quite - keep trying'):
    c = G.card
    for p in wrong_pitches:
        if all(p != w[0] for w in G.wrong):
            G.wrong.append((p, c.prefer_flat, t + WRONG_SHOW))
    if G.first_try:
        G.first_try = False
        G.stats['streak'] = 0
        for p in c.notes:
            G.misses[p] = G.misses.get(p, 0) + 1
        draw_heat(window[K_HEAT])
        refresh_tiles(window)
    window[K_LAST].update(message, text_color=C_WRONG)


def check_answer(window, t, note):
    """Compare what is held (or the note just played, for melodies) with the card"""
    c = G.card
    if not G.running or c is None or G.next_at:
        return
    if c.seq:
        if note == c.notes[G.seq_idx]:
            G.seq_idx += 1
            if G.seq_idx == len(c.notes):
                card_done(window, t, c.notes)
        else:
            card_wrong(window, t, [note], f'Not {note_name(note, c.prefer_flat)} - note {G.seq_idx + 1} is {note_name(c.notes[G.seq_idx], c.prefer_flat)}')
        return
    if c.match == 'exact':
        if G.held == set(c.notes):
            card_done(window, t, c.notes)
        elif G.held and not G.held <= set(c.notes):
            card_wrong(window, t, G.held - set(c.notes))
        return
    pcs = {p % 12 for p in G.held}                                                         # named chord: any octave, bass decides the inversion
    if len(G.held) >= len(c.pcs) and pcs == c.pcs and min(G.held) % 12 == c.bass_pc:
        card_done(window, t, G.held)
    elif pcs - c.pcs:
        card_wrong(window, t, [p for p in G.held if p % 12 not in c.pcs])
    elif len(G.held) >= len(c.pcs) and pcs == c.pcs:
        card_wrong(window, t, [min(G.held)], f'Right notes, wrong inversion - the bass should be {(NOTE_NAMES_FLAT if c.prefer_flat else NOTE_NAMES)[c.bass_pc]}')


def reset_stats(window):
    G.stats = {'cards': 0, 'first': 0, 'times': [], 'streak': 0, 'best': 0}
    G.by_type.clear()
    G.misses.clear()
    window[K_LAST].update('')
    draw_heat(window[K_HEAT])
    refresh_tiles(window)


def demo_tick(window, now):
    """Answers the current card after a human-ish delay: 80% right, otherwise off by a step or two; melodies one note at a time"""
    c = G.card
    if not G.running or c is None or G.next_at:
        return
    if c is not G.demo_card:
        G.demo_card, G.demo_next_t, G.demo_erred = c, now + random.uniform(0.7, 1.5), False
    if now < G.demo_next_t:
        return
    err = (not G.demo_erred) and random.random() < 0.2
    G.demo_erred = G.demo_erred or err
    if c.seq:
        n = c.notes[G.seq_idx] + (random.choice([-2, -1, 1, 2]) if err else 0)
        check_answer(window, now, n)
        G.demo_next_t = now + 0.35
        return
    shift = -12 if c.match == 'pcs_bass' and min(c.notes) >= 33 and random.random() < 0.5 else 0          # named chords: any octave will do
    notes = [p + shift for p in c.notes]
    if err:
        notes[random.randrange(len(notes))] += random.choice([-2, -1, 1, 2])
    G.held = set(notes)
    check_answer(window, now, notes[0])
    G.held = set()
    G.demo_next_t = now + 0.8


# ---------- Display ----------
def paint(window, name, text, color, sub=''):
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
    for key, target in G.tile_target.items():
        cur = G.tile_now.get(key, target)
        if cur == target:
            continue
        new = target if all(abs(c - t) < 1.5 for c, t in zip(cur, target)) else mix(cur, target, TILE_EASE)
        G.tile_now[key] = new
        window[KT_TILE(key)].update(background_color=hexcolor(new))


def refresh_tiles(window):
    s = G.stats
    cards = s['cards']
    acc = 100 * s['first'] / cards if cards else None
    paint(window, T_ACC, f'{acc:.0f}%' if cards else '', gradient(ACC_STOPS, acc) if cards else None, f'{s["first"]} of {cards} cards' if cards else '')
    avg = sum(s['times']) / len(s['times']) if s['times'] else None
    paint(window, T_SPEED, f'{avg:.2f}' if avg else '', gradient(SPEED_STOPS, avg) if avg else None, 'seconds, last 30 cards' if avg else '')
    paint(window, T_STREAK, f'{s["streak"]} / {s["best"]}', rgb(C_TILE_NEUTRAL), 'first-try in a row / best')
    paint(window, T_CARDS, str(cards), rgb(C_TILE_NEUTRAL), 'this session')
    lines = [f'{kind:<14}{100 * r / n:3.0f}%   {r} / {n}' for kind, (r, n) in G.by_type.items()]
    window[K_BY_TYPE].update('\n'.join(lines) if lines else '-')


def text_px(window, text, font):
    if (text, font) not in G.text_px:
        G.text_px[(text, font)] = tkfont.Font(root=window.TKroot, font=font).measure(text)
    return G.text_px[(text, font)]


def redraw_staff(graph, bass_only, now, lo=36, hi=84):
    """Grand staff on paper; the card (ink), answered notes (green), wrong notes (red), and prompts for named cards.
    The staff size follows the note range: room for the highest and lowest possible note plus the prompt text above."""
    window = graph.ParentForm
    w, h = graph.get_size()
    if not w or w < 40 or h < 40:
        return
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, 0), (w, h))
    graph.erase()
    step_lo, step_hi = spell(lo, False)[0], spell(hi, False)[0]
    top_sp = max(4.5, (step_hi - 2) / 2 + 1.5) + 5.0            # above the treble bottom line: highest note (or staff) + the prompt
    bottom_sp = min(-8.5, -8 + (step_lo + 10) / 2 - 1.5)       # below it: the bass staff or the lowest note
    sp = h / (top_sp - bottom_sp + 2)
    y_tb = (h - (top_sp - bottom_sp) * sp) / 2 - bottom_sp * sp
    y_bb = y_tb - 8 * sp
    x0, x1 = w * 0.08, w * 0.94
    label_font = (FONT_FAMILY, -int(max(14 * G.scale, min(30 * G.scale, 0.9 * sp))), 'bold')          # pixel sizes: readable on any screen
    line_w, stem_w = max(3, int(sp * 0.12)), max(4, int(sp * 0.16))                                    # staff / ledger lines and stems scale with the staff

    def fit_font(text, px, max_width):
        """A bold font of about px pixels, shrunk until the text fits max_width"""
        px = int(px)
        while px > 12 * G.scale and text_px(window, text, (FONT_FAMILY, -px, 'bold')) > max_width:
            px = int(px * 0.9)
        return (FONT_FAMILY, -px, 'bold')

    big = fit_font(G.card.prompt if G.card and G.card.prompt else '', 2.6 * sp, (x1 - x0) * 0.96)

    def step_y(step):
        treble = step > 0 or (step == 0 and not bass_only)
        return (y_tb + (step - 2) * sp / 2, True) if treble else (y_bb + (step + 10) * sp / 2, False)

    def draw_notes(pitches, x, color, prefer_flat, stems=True, spellings=None):
        """A stack of note heads at x (chord) with ledger lines, accidentals and one stem; seconds are offset sideways"""
        pitches = sorted(pitches)
        spelled = {p: (spellings or {}).get(p) or spell(p, prefer_flat) for p in pitches}
        steps = [spelled[p][0] for p in pitches]
        for p, step in zip(pitches, steps):
            y, treble = step_y(step)
            lines = range(0, step - 1, -2) if (treble and step <= 0) else range(12, step + 1, 2) if (treble and step >= 12) else \
                range(0, step + 1, 2) if (not treble and step >= 0) else range(-12, step - 1, -2) if (not treble and step <= -12) else []
            for s in lines:
                graph.draw_line((x - sp * 1.1, step_y(s)[0]), (x + sp * 1.1, step_y(s)[0]), color=C_INK, width=line_w)
        shifted, acc_slot = set(), 0
        for i, (p, step) in enumerate(zip(pitches, steps)):
            y, treble = step_y(step)
            dx = sp * 1.35 if (i and step - steps[i - 1] == 1 and (i - 1) not in shifted) else 0
            if dx:
                shifted.add(i)
            graph.draw_oval((x + dx - sp * 0.7, y + sp * 0.5), (x + dx + sp * 0.7, y - sp * 0.5), fill_color=color, line_color=color)
            acc = spelled[p][1]
            if acc:                                                     # pixel-sized glyph; a flat sits on its bowl, so it is drawn a little higher
                graph.draw_text(acc, (x - sp * (1.5 + 1.1 * (acc_slot % 2)), y + (sp * 0.35 if acc == '♭' else 0)), color=color, font=(CLEF_FAMILY, -int(sp * 2.6)))
                acc_slot += 1
        if stems:
            top_step, bot_step = steps[-1], steps[0]
            y_top, treble = step_y(top_step)
            y_bot = step_y(bot_step)[0]
            up = (top_step + bot_step) / 2 < (6 if treble else -6)
            sx = x + sp * 0.65 if up else x - sp * 0.65
            graph.draw_line((sx, y_bot if up else y_top), (sx, y_top + sp * 3.2 if up else y_bot - sp * 3.2), color=color, width=stem_w)

    for k in range(5):
        graph.draw_line((x0, y_tb + k * sp), (x1, y_tb + k * sp), color=C_STAFF_LINE, width=line_w)
        graph.draw_line((x0, y_bb + k * sp), (x1, y_bb + k * sp), color=C_STAFF_LINE, width=line_w)
    graph.draw_line((x0, y_bb), (x0, y_tb + 4 * sp), color=C_INK, width=stem_w)
    graph.draw_text('\U0001D11E', (x0 + sp * 1.6, y_tb + sp * 1.6), color=C_INK, font=(CLEF_FAMILY, int(sp * 2.6)))
    graph.draw_text('\U0001D122', (x0 + sp * 1.5, y_bb + sp * 2.4), color=C_INK, font=(CLEF_FAMILY, int(sp * 2.0)))
    c = G.card
    if not G.running or c is None:
        hint = 'press Start, then play what you see'
        graph.draw_text(hint, (w / 2, y_tb + (top_sp - 2.5) * sp), color=C_STAFF_LINE, font=fit_font(hint, 1.6 * sp, w * 0.9))
        return
    y_prompt = y_tb + (top_sp - 2.6) * sp                       # named cards: the big prompt above the staff, the hint line above that
    done = G.next_at is not None
    graph.draw_text(c.reveal if done and c.reveal else c.label, (w * 0.5, y_tb + (top_sp - 0.8) * sp), color=C_RIGHT if done and c.reveal else C_STAFF_LINE, font=label_font)
    if c.seq:                                                  # melody: notes left to right, the ones already played in green
        n = len(c.notes)
        xs = [x0 + sp * 6 + (x1 - x0 - sp * 8) * (i + 0.5) / n for i in range(n)]
        for i, (p, x) in enumerate(zip(c.notes, xs)):
            draw_notes([p], x, C_RIGHT if i < G.seq_idx or done else C_INK, c.prefer_flat)
    elif c.written:
        draw_notes(c.written, w * 0.5, C_RIGHT if done else C_INK, c.prefer_flat, spellings=c.spellings)
    if c.prompt:
        if c.kind == KIND_INT_N:
            y_first = step_y(c.spellings.get(c.written[0], spell(c.written[0], c.prefer_flat))[0])[0]
            graph.draw_text(c.prompt, (w * 0.5 + sp * 3, y_first), color=C_PROMPT, font=fit_font(c.prompt, 2.2 * sp, w * 0.4),
                            text_location=sg.TEXT_LOCATION_LEFT)
        else:
            graph.draw_text(c.prompt, (w * 0.5, y_prompt), color=C_PROMPT, font=big)
    if done and c.match == 'pcs_bass' and G.reveal:
        draw_notes(G.reveal, w * 0.5, C_RIGHT, c.prefer_flat)
    if done and c.kind == KIND_INT_N:
        draw_notes(c.notes, w * 0.5, C_RIGHT, c.prefer_flat, spellings=c.spellings)
    wrong_x = (x0 + sp * 6 + (x1 - x0 - sp * 8) * (min(G.seq_idx, len(c.notes) - 1) + 0.5) / len(c.notes) + sp * 1.8) if c.seq else w * 0.5 + sp * 6
    for p, prefer_flat, expire in G.wrong:
        if now < expire:
            draw_notes([p], wrong_x, C_WRONG, prefer_flat)


def draw_heat(graph):
    w, h = graph.get_size()
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, 0), (w, h))
    graph.erase()
    geom, kw = build_key_geometry(21, 108, w)
    top = max(G.misses.values()) if G.misses else 1
    for p, (x0, x1, black) in geom.items():
        if not black:
            graph.draw_rectangle((x0, h), (x1, 0), fill_color=C_WHITE_KEY, line_color='#777777')
    for p, (x0, x1, black) in geom.items():
        if black:
            graph.draw_rectangle((x0, h), (x1, h * 0.44), fill_color=C_BLACK_KEY, line_color='#000000')
    for p, n in G.misses.items():
        if p in geom:
            x0, x1, black = geom[p]
            red = '#%02x3030' % (60 + int(195 * n / top))
            graph.draw_rectangle((x0 + 1, h if black else h * 0.4), (x1 - 1, h * 0.48 if black else 1), fill_color=red, line_color=red)


# ---------- Touch picker ----------
def touch_pick(title, choices, current, steps):
    idx = choices.index(current) if current in choices else 0
    if steps is None:
        per_row, width = 5, max(6, max(len(str(c)) for c in choices))
        rows = [[sg.Button(str(c), key=KT_PICK(c), size=(width, 2), font=FONT_PICK) for c in choices[i:i + per_row]] for i in range(0, len(choices), per_row)]
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


PICKERS = {K_RANGE: ('Note range', RANGE_CHOICES, None),
           K_MELODY: ('Notes in a melody card', MELODY_CHOICES, None),
           K_NEXT: ('Next card after (seconds)', NEXT_CHOICES, None),
           K_TEXT_SIZE: ('Text size', TEXT_SIZE_CHOICES, None)}
for _kind in KINDS:
    PICKERS[KT_MIX(_kind)] = (f'{_kind}: how often', MIX_CHOICES, None)


def edit_value(window, key, values):
    title, choices, steps = PICKERS[key]
    current = next((c for c in choices if str(c) == str(values.get(key))), choices[0])
    chosen = touch_pick(title, choices, current, steps)
    if chosen is not None and chosen != current:
        window[key].update(str(chosen))
        window.write_event_value(K_REBUILD if key == K_TEXT_SIZE else K_RECALC, key)


def save_settings(window, values):
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


# ---------- Window ----------
def tile(name, color, width=7):
    col = [[sg.Text(name, font=FONT_LABEL, text_color=color, pad=(0, (6, 0)))],
           [sg.Text('-', key=KT_TILE(name), font=FONT_BIG, text_color=C_AXIS_TEXT, size=(width, 1), justification='c', background_color=C_TILE_NEUTRAL, pad=(0, 0))],
           [sg.Text('', key=KT_TILE_SUB(name), font=FONT_LABEL, text_color=C_AXIS_TEXT, size=(30, 1), pad=(0, 0))]]
    return sg.Column(col, pad=(0, 0))


def build_window(ports, port):
    sg.set_options(font=FONT_UI)
    P = ((10, 4), 0)
    TAP_TT = '  (tap the value or the pencil for a big picker)'

    def field(default, key, width, tooltip):
        return [sg.Input(str(default), key=key, size=(width, 1), readonly=True, setting=default, justification='c', tooltip=tooltip + TAP_TT),
                sg.Text('\u270E', key=KT_EDIT(key), enable_events=True, text_color=C_EDIT, pad=((0, 4), 0), tooltip='Change: ' + tooltip)]

    top = [sg.Text('MIDI in'), sg.Combo(ports, default_value=port, key=K_PORT, size=(16, 1), readonly=True, enable_events=True), sg.Button('Refresh', key=K_REFRESH),
           sg.Text('', key=K_LAST, font=FONT_LAST, size=(24, 1), pad=((20, 0), 0)),
           sg.Push(),
           sg.Button('Full', key=K_FULL, size=(9, 1), tooltip='Full screen on / off (F11): whole screen, no title bar'),
           sg.Button('Start', key=K_START, size=(7, 1), button_color=(C_ON_TILE, C_STATUS_OK), tooltip='Start / pause the cards (F9)'),
           sg.Button('Skip', key=K_SKIP, tooltip='Skip this card (SPACE)'), sg.Button('Reset', key=K_RESET, tooltip='Reset the statistics (HOME)'), sg.Button('Exit', key=K_EXIT)]
    opts = [sg.Text('Range'), *field('Both C2-C6', K_RANGE, 12, TT_RANGE),
            sg.Checkbox('Accidentals', key=K_ACC, setting=False, enable_events=True, pad=P, tooltip='Sharps and flats (chords: roots on black keys too)'),
            sg.Checkbox('Inversions', key=K_INV, setting=True, enable_events=True, pad=P, tooltip='Chord cards may be in 1st / 2nd / 3rd inversion'),
            sg.Text('Melody notes', pad=P), *field(4, K_MELODY, 3, TT_MELODY),
            sg.Text('Next delay', pad=P), *field(0.8, K_NEXT, 4, TT_NEXT),
            sg.Text('Text', pad=P), *field('100%', K_TEXT_SIZE, 5, 'Size of all text in the program')]
    mix_row = [sg.Text('Mix')]
    for kind in KINDS:
        mix_row += [sg.Text(kind, pad=P), *field(MIX_DEFAULT[kind], KT_MIX(kind), 2, TT_MIX)]
    tiles = [[tile(T_ACC, C_RIGHT_TILE)], [tile(T_SPEED, C_AXIS_TEXT)], [tile(T_STREAK, C_AXIS_TEXT)], [tile(T_CARDS, C_AXIS_TEXT)],
             [sg.Text('BY CARD TYPE  (first try)', font=FONT_LABEL, text_color=C_AXIS_TEXT, pad=(0, (10, 0)))],
             [sg.Text('-', key=K_BY_TYPE, font=(MONO_FAMILY, FONT_TYPES[1]), size=(30, 8), pad=(0, 0))],
             [sg.Text('MISSES PER NOTE', font=FONT_LABEL, text_color=C_WRONG, pad=(0, (10, 0)))],
             [sg.Graph((int(360 * G.scale), int(50 * G.scale)), (0, 0), (1, 1), key=K_HEAT, background_color=C_BG, pad=(0, 0))]]
    extras = [[sg.Text('', key=K_STATUS, font=FONT_LABEL, size=(28, 2), pad=(0, (10, 0)))],
              [sg.Checkbox('Demo answers', key=K_DEMO, enable_events=True, font=FONT_LABEL, pad=(0, (6, 0)))]]
    tiles += [[sg.pin(sg.Column(extras, key=K_EXTRAS, pad=(0, 0)))],
              [sg.Push(), sg.Button('\u25B2', key=K_TOGGLE_CONTROLS, font=FONT_LABEL, tooltip='Hide / show the control rows (F10)')]]
    side = sg.Column(tiles, vertical_alignment='top', pad=((10, 0), 0))
    controls = sg.pin(sg.Column([top, opts, mix_row], key=K_CONTROLS, expand_x=True, pad=(0, 0)), expand_x=True)
    layout = [[controls], [sg.Graph((900, 500), (0, 0), (1, 1), key=K_STAFF, background_color=C_PAPER, expand_x=True, expand_y=True, pad=(0, 6)), side]]

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
    window.bind('<space>', K_KEY_SPACE)
    for key in PICKERS:
        window[key].bind('<Button-1>', TAP)
        window[key].widget.configure(readonlybackground=sg.theme_input_background_color())
    if sg.user_settings_get_entry(K_FULLSCREEN, False):
        set_fullscreen(window, True)
    if sg.user_settings_get_entry(K_CONTROLS_HIDDEN, False):
        show_controls(window, False)
    window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)
    if G.running:
        window[K_START].update('Pause', button_color=(C_ON_TILE, C_PAUSED))
    G.tile_now.clear()
    G.tile_target.clear()
    refresh_tiles(window)
    draw_heat(window[K_HEAT])
    window.timer_start(100)
    return window


def card_options(values):
    """Everything make_card needs, read from the controls"""
    lo, hi = RANGES.get(values.get(K_RANGE), RANGES['Both C2-C6'])
    weights = {kind: ival(values, KT_MIX(kind), MIX_DEFAULT[kind]) for kind in KINDS}
    return (weights, lo, hi, bool(values.get(K_ACC)), bool(values.get(K_INV)), ival(values, K_MELODY, 4))


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
        window.write_event_value(K_START, None)
    auto_close = time.monotonic() + float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_EXIT, K_KEY_ESC) or (auto_close and time.monotonic() > auto_close):
            save_settings(window, values)
            break
        opts = card_options(values)
        G.next_delay = fval(values, K_NEXT, 0.8)
        now = time.monotonic()
        if event == sg.EVENT_TIMER:
            if values[K_DEMO]:
                demo_tick(window, now)
            if G.next_at and now > G.next_at and G.running:
                new_card(window, opts)
            ease_tiles(window)
            redraw_staff(window[K_STAFF], opts[2] <= 60, now, opts[1], opts[2])
        elif event == K_MIDI_NOTE:
            t, note, vel, on = values[K_MIDI_NOTE]
            handle_note(window, t, note, on)
        elif event in (K_START, K_KEY_F9):
            set_running(window, not G.running, opts)
        elif event in (K_SKIP, K_KEY_SPACE):
            if G.running:
                G.stats['streak'] = 0
                refresh_tiles(window)
                new_card(window, opts)
        elif event in (K_RESET, K_KEY_HOME):
            reset_stats(window)
        elif event in (K_ACC, K_INV, K_RECALC):
            if G.running:
                new_card(window, opts)
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
