"""
Call and Response  (call_response.pyw)  -  an ear and memory game: the piano plays a short phrase (MIDI out), you play it back.

Each round the program plays a diatonic phrase in the current key through the piano.  Play it back note by note: a correct note
turns green, a wrong note turns red with the note you played marked at its own pitch, the phrase replays and you try again.
Three clean rounds in a row = level up (longer phrases, wider leaps, mixed rhythm from level 4); three misses = level down.
The board shows the phrase as circles (height = pitch, width = duration) with a banner: Listen ... / Your turn / Nice! / Not quite.
Note names are hidden ("?") while the phrase plays and while you answer; a circle shows its name once you have played it right, and
the whole phrase is named after a clean round.
Tiles on the right: SCORE, ROUND, CLEAN STREAK, LEVEL.

LEVEL 1-8 (also set by hand), KEY (Random or a fixed key), TEMPO of the playback, CHANNEL the phrase is sent on (1 = the piano voice),
AUTO NEXT deals the next phrase automatically after a clean round.
PLAY (SPACE) starts a new phrase (or repeats the current one while it is your turn); NEW (N) skips to a fresh phrase.

TOUCH: every numeric setting is a read-only value box followed by a small pencil mark; tapping the box or the pencil opens a big picker.
TEXT SIZE: one multiplier for every font; changing it rebuilds the window in place (score and MIDI connections are kept).
FULL (F11) covers the whole screen with no title bar; F10 hides / shows the control rows; HOME resets the score; ESC exits.
Demo checkbox answers the phrases by itself (occasionally wrong).  Without a MIDI out port the phrase is only shown on screen.
Requires:  pip install PySimpleGUI mido python-rtmidi
Settings persist in SETTINGS_FILE (call_response.json in the PySimpleGUI settings folder) via Window.settings_save() at exit;
the MIDI ports, fullscreen and hidden-controls state are saved as they change.  "Demo" is deliberately not saved.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import heapq
import random
import sys
import threading
import time

import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None


ICON = b'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'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

APP_TITLE = 'Call and Response'
SETTINGS_FILE = 'call_response.json'

# ---------- Keys ----------
K_BOARD = '-BOARD-'
K_PORT = '-PORT-'
K_PORT_OUT = '-PORT OUT-'
K_REFRESH = '-REFRESH-'
K_LEVEL = '-LEVEL-'
K_KEYSIG = '-KEYSIG-'
K_TEMPO = '-TEMPO-'
K_CHANNEL = '-CHANNEL-'
K_AUTO = '-AUTO-'
K_TEXT_SIZE = '-TEXT SIZE-'
K_REBUILD = '-REBUILD-'                # internal event: fonts changed, rebuild the window
K_RECALC = '-RECALC-'                  # internal event: a setting changed
K_DEMO = '-DEMO-'
K_PLAY = '-PLAY-'
K_NEW = '-NEW-'
K_RESET = '-RESET-'
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
K_TILE = '-TILE-'
KT_TILE = lambda name: (K_TILE, name)
K_TILE_SUB = '-TILE SUB-'
KT_TILE_SUB = lambda name: (K_TILE_SUB, name)
K_MIDI_NOTE = '-MIDI NOTE-'            # from the MIDI callback thread: (time, note, velocity)
K_OUT = '-OUT-'                        # from the sender thread: (time, note, is_on)
K_KEY_ESC = '-KEY ESC-'
K_KEY_F10 = '-KEY F10-'
K_KEY_F11 = '-KEY F11-'
K_KEY_HOME = '-KEY HOME-'
K_KEY_SPACE = '-KEY SPACE-'
K_KEY_N = '-KEY N-'
K_FULLSCREEN = '-FULLSCREEN-'
K_CONTROLS = '-CONTROLS-'
K_CONTROLS_HIDDEN = '-CONTROLS HIDDEN-'
K_EXTRAS = '-EXTRAS-'
K_TOGGLE_CONTROLS = '-TOGGLE CONTROLS-'

# ---------- Colors ----------
C_BG = '#101418'
C_PENDING = '#4A5266'        # note not yet answered
C_APP = '#A78BFA'            # purple - the piano is playing
C_RIGHT = '#2DD4BF'          # teal   - correct
C_WRONG = '#FF5252'          # red    - wrong
C_GOLD = '#FFD54A'           # score
C_GRID = '#2C343C'
C_AXIS_TEXT = '#9AA6B2'
C_STATUS_OK = '#69F0AE'
C_STATUS_BAD = '#FF8A65'
C_PAUSED = '#FFB300'
C_EDIT = '#4DD0E1'
C_ON_TILE = '#000000'
C_TILE_NEUTRAL = '#2C343C'
TILE_EASE = 0.35

FONT_FAMILY = 'Segoe UI'
BASE_FONTS = {'FONT_UI': 12,             # all controls, status line
              'FONT_LABEL': 11,          # tile labels and sub text
              'FONT_BIG': 26,            # tile numbers
              'FONT_BANNER': 26,         # Listen / Your turn banner on the board
              'FONT_NOTE': 12,           # note names inside the circles, key line
              'FONT_PICK': 20,
              'FONT_PICK_VALUE': 48}
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
NAMES = ['C', 'D♭', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'A♭', 'A', 'B♭', 'B']
KEYS = {'Random': None, 'C major': (0, False), 'G major': (7, False), 'D major': (2, False), 'F major': (5, False), 'B♭ major': (10, False),
        'A minor': (9, True), 'E minor': (4, True), 'D minor': (2, True)}
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]
DURATIONS = [0.5, 1.0, 2.0]
LEVEL_CHOICES = list(range(1, 9))
KEY_CHOICES = list(KEYS)
TEMPO_CHOICES = list(range(40, 181))
CHANNEL_CHOICES = list(range(1, 17))
STEPS_1_10 = [(-10, '-10'), (-1, '-1'), (1, '+1'), (10, '+10')]
STEPS_1_4 = [(-4, '-4'), (-1, '-1'), (1, '+1'), (4, '+4')]
TT_LEVEL = 'Phrase length and range: 1 = 3 notes, small steps ... 8 = 10 notes, wide leaps and mixed rhythm'
TT_KEY = 'Key of the phrases (Random = a new key every phrase)'
TT_TEMPO = 'Playback tempo'
TT_CHANNEL = 'MIDI channel the phrase is sent on (1 = the piano voice)'
T_SCORE, T_ROUND, T_STREAK, T_LEVEL = 'SCORE', 'ROUND', 'CLEAN STREAK', 'LEVEL'
TILES = (T_SCORE, T_ROUND, T_STREAK, T_LEVEL)


class G:                                # program-wide state
    window = None
    port = None
    sender = None
    status = ''
    status_ok = False
    scale = 1.0
    fullscreen = False
    text_px = {}
    tile_target = {}
    tile_now = {}
    key = (0, False)
    phrase = []                         # [(pitch, start_beat, dur_beats)]
    attempt = 0
    state, state_until, banner = 'idle', 0.0, 'press Play'
    marks = []                          # 'right' or ('wrong', pitch) per answered note
    answer_idx = 0
    retried = False
    playing_idx = -1
    score, rounds, clean_streak, misses_in_row = 0, 0, 0, 0
    level = 1
    demo_next_t = 0.0
    demo_attempt = 0
    demo_idx = 0


# ---------- Helpers ----------
def key_name(key):
    return NAMES[key[0]] + (' minor' if key[1] else ' major')


def make_phrase(level, key):
    """[(pitch, start_beat, dur_beats)] - a diatonic random walk in the key, longer and wider with level"""
    steps = MINOR_STEPS if key[1] else MAJOR_STEPS
    scale = [p for p in (60 + key[0] % 12 - 12 + s + 12 * o for o in range(4) for s in steps) if 48 <= p <= 91]
    center = min(range(len(scale)), key=lambda i: abs(scale[i] - 67))
    span, n = 3 + level, 2 + level
    idx = max(0, min(len(scale) - 1, center + random.choice([0, 0, 2, 4]) - 2))
    phrase, beat = [], 0.0
    for i in range(n):
        if i:
            move = random.choice([-2, -1, -1, 1, 1, 2, 3, -3] if level < 4 else [-4, -3, -2, -1, -1, 1, 1, 2, 3, 4, 5])
            if abs(idx + move - center) > span:
                move = -move
            idx = max(0, min(len(scale) - 1, idx + move))
        dur = random.choice(DURATIONS) if level >= 4 else 1.0
        if i == n - 1:
            dur = max(dur, 1.0)
        phrase.append((scale[idx], beat, dur))
        beat += dur
    return phrase


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def hexcolor(rgb_tuple):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(c)))) for c in rgb_tuple)


def mix(c1, c2, f):
    return tuple(a + (b - a) * f for a, b in zip(c1, c2))


def ival(values, key, default):
    try:
        return int(values[key])
    except (TypeError, ValueError, KeyError):
        return default


# ---------- MIDI in / out ----------
def midi_ports(output=False):
    try:
        return (mido.get_output_names() if output else mido.get_input_names()) if mido else []
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
    update_status()


def open_out(name):
    try:
        G.sender.open(name)
    except Exception as e:
        G.status, G.status_ok = f'Cannot open output {name}: {e}', False
    update_status()


def update_status():
    if G.window is not None:
        out = G.sender.name if G.sender and G.sender.port else 'none - phrase shown on screen only'
        G.window[K_STATUS].update(f'{G.status}\nOut: {out}', text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)


class Sender:
    """Time-ordered MIDI output queue; a worker thread sends each message when due and posts K_OUT to the window"""
    def __init__(self):
        self.port, self.name, self.queue, self.seq, self.running = None, '', [], 0, True
        self.cv = threading.Condition()
        self.active = set()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def open(self, name):
        self.close()
        self.name = name or ''
        if name and mido:
            self.port = mido.open_output(name)

    def close(self):
        if self.port:
            self.port.close()
            self.port = None

    def schedule(self, when, note, on, channel):
        with self.cv:
            heapq.heappush(self.queue, (when, self.seq, note, on, channel))
            self.seq += 1
            self.cv.notify()

    def panic(self, channel):
        with self.cv:
            self.queue.clear()
        for ch, note in list(self.active):
            self.send(note, False, ch)
        if self.port:
            try:
                self.port.send(mido.Message('control_change', control=123, value=0, channel=channel))
            except Exception:
                pass

    def send(self, note, on, channel):
        if on:
            self.active.add((channel, note))
        else:
            self.active.discard((channel, note))
        if self.port:
            try:
                self.port.send(mido.Message('note_on' if on else 'note_off', note=note, velocity=84 if on else 0, channel=channel))
            except Exception:
                pass
        if G.window is not None:
            G.window.write_event_value(K_OUT, (time.monotonic(), note, on))

    def run(self):
        while self.running:
            with self.cv:
                while self.running and not self.queue:
                    self.cv.wait()
                if not self.running:
                    return
                when, _, note, on, channel = self.queue[0]
                wait = when - time.monotonic()
                if wait > 0:
                    self.cv.wait(min(wait, 0.05))
                    continue
                heapq.heappop(self.queue)
            self.send(note, on, channel)

    def stop(self):
        with self.cv:
            self.running = False
            self.cv.notify()
        self.thread.join(timeout=1)


# ---------- Game ----------
def set_state(window, new, banner, hold=0.0):
    G.state, G.banner, G.state_until = new, banner, time.monotonic() + hold
    window[K_PLAY].update('Repeat' if new == 'answer' else 'Play')


def new_phrase(window, keysig, bpm, channel):
    G.key = KEYS[keysig] or random.choice([k for k in KEYS.values() if k])
    G.phrase = make_phrase(G.level, G.key)
    G.retried = False
    play_phrase(window, bpm, channel)


def play_phrase(window, bpm, channel):
    G.marks, G.answer_idx, G.playing_idx = [], 0, -1
    G.attempt += 1
    beat = 60.0 / bpm
    t0 = time.monotonic() + 0.4
    for pitch, start, dur in G.phrase:
        G.sender.schedule(t0 + start * beat, pitch, True, channel)
        G.sender.schedule(t0 + (start + dur * 0.85) * beat, pitch, False, channel)
    total = G.phrase[-1][1] + G.phrase[-1][2]
    set_state(window, 'listen', 'Listen …', hold=0.4 + total * beat + 0.3)


def finish_round(window):
    G.rounds += 1
    gained = len(G.phrase) * (10 if not G.retried else 4)
    G.score += gained
    if not G.retried:
        G.clean_streak += 1
        G.misses_in_row = 0
    else:
        G.clean_streak = 0
    text = f'Nice!   +{gained}'
    if G.clean_streak >= 3 and G.level < 8:
        G.level += 1
        G.clean_streak = 0
        text = f'Level up!   +{gained}'
        window[K_LEVEL].update(str(G.level))
    refresh_tiles(window)
    set_state(window, 'success', text, hold=1.3)


def handle_answer(window, pitch):
    if G.state != 'answer' or G.answer_idx >= len(G.phrase):
        return
    expected = G.phrase[G.answer_idx][0]
    if pitch == expected:
        G.marks.append('right')
        G.answer_idx += 1
        if G.answer_idx == len(G.phrase):
            finish_round(window)
        return
    G.marks.append(('wrong', pitch))
    G.retried = True
    G.misses_in_row += 1
    G.clean_streak = 0
    if G.misses_in_row >= 3 and G.level > 1:
        G.level -= 1
        G.misses_in_row = 0
        window[K_LEVEL].update(str(G.level))
        set_state(window, 'wrong', 'Level down - listen again', hold=1.4)
    else:
        set_state(window, 'wrong', f'Not {NAMES[pitch % 12]} - it was {NAMES[expected % 12]}.   Listen again', hold=1.4)
    refresh_tiles(window)


def tick_state(window, now, values, bpm, channel):
    if G.state == 'listen' and now >= G.state_until:
        set_state(window, 'answer', 'Your turn')
    elif G.state == 'success' and now >= G.state_until:
        if values[K_AUTO]:
            new_phrase(window, values[K_KEYSIG], bpm, channel)
        else:
            set_state(window, 'idle', 'press Play for the next phrase')
    elif G.state == 'wrong' and now >= G.state_until:
        play_phrase(window, bpm, channel)


def reset_score(window):
    G.score, G.rounds, G.clean_streak, G.misses_in_row = 0, 0, 0, 0
    refresh_tiles(window)


def demo_tick(window, now, bpm):
    """Answers the phrase in time with an occasional wrong note"""
    if G.state != 'answer':
        return
    if G.demo_attempt != G.attempt:
        G.demo_attempt, G.demo_idx, G.demo_next_t = G.attempt, 0, now + 0.5
    if now < G.demo_next_t or G.demo_idx >= len(G.phrase):
        return
    pitch, start, dur = G.phrase[G.demo_idx]
    G.demo_idx += 1
    G.demo_next_t = now + dur * 60.0 / bpm
    handle_answer(window, pitch + (random.choice([-2, -1, 1, 2]) if random.random() < 0.08 else 0))


# ---------- Display ----------
def paint(window, name, text, color, sub=''):
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
    paint(window, T_SCORE, str(G.score), rgb(C_GOLD), 'points')
    paint(window, T_ROUND, str(G.rounds), rgb(C_TILE_NEUTRAL), 'phrases completed')
    paint(window, T_STREAK, str(G.clean_streak), rgb(C_RIGHT) if G.clean_streak else rgb(C_TILE_NEUTRAL), '3 in a row = level up')
    paint(window, T_LEVEL, str(G.level), rgb(C_APP), f'{2 + G.level} notes per phrase')


def redraw_board(graph):
    w, h = graph.get_size()
    if not w or w < 40 or h < 40:
        return
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, 0), (w, h))
    graph.erase()
    banner_color = {'listen': C_APP, 'answer': '#FFFFFF', 'success': C_RIGHT, 'wrong': C_WRONG}.get(G.state, C_AXIS_TEXT)
    graph.draw_text(G.banner, (w / 2, h - FONT_BANNER[1] * 1.4 * G.scale), color=banner_color, font=FONT_BANNER)
    if not G.phrase:
        return
    total = G.phrase[-1][1] + G.phrase[-1][2]
    lo, hi = min(p for p, _, _ in G.phrase) - 3, max(p for p, _, _ in G.phrase) + 3
    xm, y0, y1 = 60 * G.scale, 40 * G.scale, h - FONT_BANNER[1] * 3.2 * G.scale
    x_of = lambda b: xm + b / total * (w - 2 * xm)
    y_of = lambda p: y0 + (p - lo) / (hi - lo) * (y1 - y0)
    r = 16 * G.scale
    for b in range(int(total) + 1):
        graph.draw_line((x_of(b), y0 - 10), (x_of(b), y1 + 10), color=C_GRID, width=1)
    for i, (pitch, start, dur) in enumerate(G.phrase):
        x, y = x_of(start + dur / 2), y_of(pitch)
        graph.draw_line((x_of(start) + 6, y), (x_of(start + dur) - 6, y), color=C_GRID, width=int(6 * G.scale))
        mark = G.marks[i] if i < len(G.marks) else None
        if mark == 'right':
            graph.draw_circle((x, y), r, fill_color=C_RIGHT, line_color=C_RIGHT)
        elif mark and mark[0] == 'wrong':
            graph.draw_circle((x, y), r, fill_color=None, line_color=C_WRONG, line_width=3)
            graph.draw_circle((x, y_of(mark[1])), r * 0.7, fill_color=C_WRONG, line_color=C_WRONG)
            graph.draw_text(f'you: {NAMES[mark[1] % 12]}', (x, y_of(mark[1]) + (28 if mark[1] > pitch else -28) * G.scale), color=C_WRONG, font=FONT_NOTE)
        elif G.state == 'listen' and i == G.playing_idx:
            graph.draw_circle((x, y), r + 4 * G.scale, fill_color=C_APP, line_color=C_APP)
        elif G.state == 'listen' and i < G.playing_idx:
            graph.draw_circle((x, y), r, fill_color=C_APP, line_color=C_APP)
        else:
            graph.draw_circle((x, y), r, fill_color=None, line_color=C_PENDING, line_width=3)
        lit = mark or (G.state == 'listen' and i <= G.playing_idx)
        label = NAMES[pitch % 12] if (mark or G.state == 'success') else '?'              # names stay hidden while the phrase plays and while you answer
        graph.draw_text(label, (x, y), color=C_ON_TILE if lit else C_PENDING, font=FONT_NOTE)
    graph.draw_text(f'{key_name(G.key)}  ·  {len(G.phrase)} notes', (xm, h - FONT_BANNER[1] * 1.4 * G.scale), color=C_AXIS_TEXT, font=FONT_NOTE,
                    text_location=sg.TEXT_LOCATION_LEFT)


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


PICKERS = {K_LEVEL: ('Level', LEVEL_CHOICES, None),
           K_KEYSIG: ('Key', KEY_CHOICES, None),
           K_TEMPO: ('Tempo (bpm)', TEMPO_CHOICES, STEPS_1_10),
           K_CHANNEL: ('MIDI channel', CHANNEL_CHOICES, STEPS_1_4),
           K_TEXT_SIZE: ('Text size', TEXT_SIZE_CHOICES, None)}


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
           [sg.Text('', key=KT_TILE_SUB(name), font=FONT_LABEL, text_color=C_AXIS_TEXT, size=(24, 1), pad=(0, 0))]]
    return sg.Column(col, pad=(0, 0))


def build_window(ports, port, outs, out):
    sg.set_options(font=FONT_UI)
    P = ((10, 4), 0)
    TAP_TT = '  (tap the value or the pencil for a big picker)'

    def field(default, key, width, tooltip):
        return [sg.Input(str(default), key=key, size=(width, 1), readonly=True, setting=default, justification='c', tooltip=tooltip + TAP_TT),
                sg.Text('\u270E', key=KT_EDIT(key), enable_events=True, text_color=C_EDIT, pad=((0, 4), 0), tooltip='Change: ' + tooltip)]

    top = [sg.Text('MIDI in'), sg.Combo(ports, default_value=port, key=K_PORT, size=(18, 1), readonly=True, enable_events=True),
           sg.Text('out', pad=P), sg.Combo(outs, default_value=out, key=K_PORT_OUT, size=(18, 1), readonly=True, enable_events=True), sg.Button('Refresh', key=K_REFRESH),
           sg.Text('Text', pad=P), *field('100%', K_TEXT_SIZE, 5, 'Size of all text in the program'),
           sg.Push(),
           sg.Button('Full', key=K_FULL, size=(9, 1), tooltip='Full screen on / off (F11): whole screen, no title bar'),
           sg.Button('Play', key=K_PLAY, size=(8, 1), button_color=(C_ON_TILE, C_APP), tooltip='Play a phrase / repeat it (SPACE)'),
           sg.Button('New', key=K_NEW, tooltip='Skip to a fresh phrase (N)'), sg.Button('Reset', key=K_RESET, tooltip='Reset the score (HOME)'), sg.Button('Exit', key=K_EXIT)]
    opts = [sg.Text('Level'), *field(1, K_LEVEL, 3, TT_LEVEL),
            sg.Text('Key', pad=P), *field('Random', K_KEYSIG, 10, TT_KEY),
            sg.Text('Tempo', pad=P), *field(90, K_TEMPO, 4, TT_TEMPO),
            sg.Text('Channel', pad=P), *field(1, K_CHANNEL, 3, TT_CHANNEL),
            sg.Checkbox('Auto next', key=K_AUTO, setting=True, pad=P, tooltip='Deal the next phrase by itself after a clean round')]
    tiles = [[tile(T_SCORE, C_GOLD)], [tile(T_ROUND, C_AXIS_TEXT)], [tile(T_STREAK, C_RIGHT)], [tile(T_LEVEL, C_APP)]]
    extras = [[sg.Text('', key=K_STATUS, font=FONT_LABEL, size=(28, 3), pad=(0, (10, 0)))],
              [sg.Checkbox('Demo answers', key=K_DEMO, enable_events=True, font=FONT_LABEL, pad=(0, (6, 0)))]]
    tiles += [[sg.pin(sg.Column(extras, key=K_EXTRAS, pad=(0, 0)))],
              [sg.Push(), sg.Button('\u25B2', key=K_TOGGLE_CONTROLS, font=FONT_LABEL, tooltip='Hide / show the control rows (F10)')]]
    side = sg.Column(tiles, vertical_alignment='top', pad=((10, 0), 0))
    controls = sg.pin(sg.Column([top, opts], key=K_CONTROLS, expand_x=True, pad=(0, 0)), expand_x=True)
    layout = [[controls], [sg.Graph((900, 480), (0, 0), (1, 1), key=K_BOARD, background_color=C_BG, expand_x=True, expand_y=True, pad=(0, 6)), side]]

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
    window.bind('<space>', K_KEY_SPACE)
    window.bind('<n>', K_KEY_N)
    for key in PICKERS:
        window[key].bind('<Button-1>', TAP)
        window[key].widget.configure(readonlybackground=sg.theme_input_background_color())
    if sg.user_settings_get_entry(K_FULLSCREEN, False):
        set_fullscreen(window, True)
    if sg.user_settings_get_entry(K_CONTROLS_HIDDEN, False):
        show_controls(window, False)
    G.level = ival({K_LEVEL: window[K_LEVEL].get()}, K_LEVEL, 1)
    window[K_PLAY].update('Repeat' if G.state == 'answer' else 'Play')
    update_status()
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
    G.sender = Sender()
    ports, outs = midi_ports(), midi_ports(output=True)
    saved_port, saved_out = sg.user_settings_get_entry(K_PORT, ''), sg.user_settings_get_entry(K_PORT_OUT, '')
    port = saved_port if saved_port in ports else (ports[0] if ports else '')
    out = saved_out if saved_out in outs else (outs[0] if outs else '')
    open_port(port)
    open_out(out)
    window = build_window(ports, port, outs, out)
    if '--demo' in sys.argv:                                   # test hooks:  --demo starts the demo,  --autoclose N exits after N seconds
        window[K_DEMO].update(True)
        window.write_event_value(K_PLAY, None)
    auto_close = time.monotonic() + float(sys.argv[sys.argv.index('--autoclose') + 1]) if '--autoclose' in sys.argv else None

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_EXIT, K_KEY_ESC) or (auto_close and time.monotonic() > auto_close):
            save_settings(window, values)
            break
        bpm, channel = ival(values, K_TEMPO, 90), ival(values, K_CHANNEL, 1) - 1
        now = time.monotonic()
        if event == sg.EVENT_TIMER:
            if values[K_DEMO]:
                demo_tick(window, now, bpm)
            tick_state(window, now, values, bpm, channel)
            ease_tiles(window)
            redraw_board(window[K_BOARD])
        elif event == K_MIDI_NOTE:
            handle_answer(window, values[K_MIDI_NOTE][1])
        elif event == K_OUT:
            t, note, on = values[K_OUT]
            if on and G.state == 'listen':
                G.playing_idx = next((i for i, (p, _, _) in enumerate(G.phrase) if p == note and i > G.playing_idx), G.playing_idx)
        elif event in (K_PLAY, K_KEY_SPACE):
            if G.state in ('idle', 'success'):
                new_phrase(window, values[K_KEYSIG], bpm, channel)
            elif G.state == 'answer':
                play_phrase(window, bpm, channel)
        elif event in (K_NEW, K_KEY_N):
            if G.state != 'listen':
                new_phrase(window, values[K_KEYSIG], bpm, channel)
        elif event in (K_RESET, K_KEY_HOME):
            reset_score(window)
        elif event == K_RECALC:
            if values[K_RECALC] == K_LEVEL:
                G.level = ival(values, K_LEVEL, G.level)
                G.clean_streak = G.misses_in_row = 0
                refresh_tiles(window)
            elif values[K_RECALC] == K_CHANNEL:
                G.sender.panic(channel)
        elif event == K_REBUILD:
            save_settings(window, values)
            set_fonts(values[K_TEXT_SIZE])
            window.timer_stop_all()
            window.close()
            window = build_window(ports, values[K_PORT], outs, values[K_PORT_OUT])
        elif isinstance(event, str) and event.endswith(TAP) and event[:-len(TAP)] in PICKERS:
            edit_value(window, event[:-len(TAP)], values)
        elif isinstance(event, tuple) and event[0] == K_EDIT:
            edit_value(window, event[1], values)
        elif event == K_PORT:
            open_port(values[K_PORT])
            sg.user_settings_set_entry(K_PORT, values[K_PORT])
        elif event == K_PORT_OUT:
            G.sender.panic(channel)
            open_out(values[K_PORT_OUT])
            sg.user_settings_set_entry(K_PORT_OUT, values[K_PORT_OUT])
        elif event == K_REFRESH:
            ports, outs = midi_ports(), midi_ports(output=True)
            port = values[K_PORT] if values[K_PORT] in ports else (ports[0] if ports else '')
            out = values[K_PORT_OUT] if values[K_PORT_OUT] in outs else (outs[0] if outs else '')
            window[K_PORT].update(values=ports, value=port)
            window[K_PORT_OUT].update(values=outs, value=out)
            open_port(port)
            open_out(out)
        elif event in (K_FULL, K_KEY_F11):
            set_fullscreen(window, not G.fullscreen)
        elif event in (K_TOGGLE_CONTROLS, K_KEY_F10):
            show_controls(window, not window[K_CONTROLS].visible)

    window.timer_stop_all()
    G.sender.panic(ival(values, K_CHANNEL, 1) - 1 if values else 0)
    time.sleep(0.05)
    G.sender.stop()
    G.sender.close()
    close_port()
    window.close()


if __name__ == '__main__':
    main()
