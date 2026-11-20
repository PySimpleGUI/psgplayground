"""
psgbounce.pyw  -  PSG Bounce: hundreds to thousands of balls bouncing off each other in a PySimpleGUI window - and a way to see what a
                  computer, its Python and its window system can do.  Windows and Linux (macOS should work too; not tried).

    WHAT YOU SEE    Balls in a box.  They fall, pile up, carry each other's weight, and bounce.  Five scenes (keys 1 - 5):
                    Rain (they fall and settle)   Gas (no gravity, nothing is lost, it never stops)   Pour (a stream from a spout)
                    Shake (gravity turns over every two seconds)   Swarm (they chase a point that wanders through the box)
    THE MOUSE       On the box:  click = a blast there   hold the button = everything is pulled to the pointer
                    wheel = more / fewer balls   Ctrl + wheel = bigger / smaller balls
    THE PANEL       Balls (50 to 20,000), Fill (how much of the box the balls take up - it sets their size), Gravity (down, none or up),
                    Bounce, Accuracy (the small steps the physics takes for each picture: more = firmer piles, and more work), the scenes,
                    Trails, Speed colors (slow = blue ... fast = white-hot), Pause, Full screen.  The lines at its bottom say what the
                    thing under the mouse does.  The line of numbers in the box: balls, frames a second, the milliseconds the physics and
                    the drawing take, and a small chart of the last 120 frames.
    DESKTOP         (Windows)  Desktop (D) takes the box's background away: the balls bounce on top of everything on the screen the
                    window was on, the taskbar is their floor, and the panel floats as a small window of its own.  What is not a ball is
                    not there - a click on it goes to whatever is underneath; a click on a ball is a blast.  The balls keep the size they
                    have in a 1280 x 720 box.  No trails there (a trail is a fade toward the background).  D or Esc brings the window back.
    THE PHYSICS     About 500 lines of plain Python kept in this file as a module of its own (ENGINE_SOURCE, near the end).  Nothing but
                    Python moves the balls; PySimpleGUI and Pillow draw them.
    EXERCISE        "Exercise this computer" (B) measures, in about 20 seconds: the physics alone, the drawing alone,
                    how many balls it keeps at 60 frames a second, and how exact the timer is - under a heading with the system, the
                    processor, Python, tk, PySimpleGUI and Pillow.  Copy puts it on the clipboard: run it on two computers, or on Windows
                    and Linux on the same one, and compare.  It always uses a 1280 x 720 box (or the whole box when that is smaller).
    WHAT IT WRITES  Its settings and nothing else: PySimpleGUI's settings folder - psgbounce.json (the window's place, the panel's values,
                    the last exercise results).  Right-click > Version says where that is and how big.
    KEYS            Space pause    1 - 5 the scenes    R the scene again    + / - more / fewer balls    T trails    C speed colors
                    X a blast at the pointer    F gravity turned over    B exercise this computer
                    D desktop    F11 full screen    Ctrl+= / Ctrl+- / Ctrl+0 bigger / smaller / normal balls
                    Esc ends the exercise, the desktop or full screen, else closes
    --demo          temporary settings, removed on close - for screenshots
    --at X,Y        the window opens with its corner at X,Y (screen pixels) instead of where it was last
    New versions: only said in the menu (a program you open and close).

CHANGE LOG (newest first, 1 line per change):
2026-11-20  v1.0.5  Claude: one engine, plain Python (the compiled one is gone); the panel's bottom lines say what the thing under the mouse does; Small steps is now Accuracy
2026-11-20  v1.0.4  Claude: Clean up comments
2026-11-19  v1.0.3  Claude: in the PySimpleGUI Playground (Programming); clean up comments
2026-11-19  v1.0.2  Claude: the window's X (and Alt-F4) closes the program again - 1.0.1 only obeyed right-click > Exit
2026-11-19  v1.0.1  Claude: Desktop (D, Windows): the box's background gone - the balls bounce over the whole screen, the panel floats beside them
2026-11-19  v1.0.0  Claude: first version
"""
import collections
import ctypes
import datetime
import io
import linecache
import math
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tkinter.font
import traceback
import types

import PySimpleGUI as sg

try:
    import PIL
    from PIL import Image, ImageDraw, ImageFilter, ImageTk, ImageWin
    NO_PILLOW = ''
except ImportError as e:
    Image, NO_PILLOW = None, str(e)

VERSION = '1.0.5'
APP_NAME = 'PSG Bounce'
ICON = b'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'
DEMO = '--demo' in sys.argv[1:]
AT = re.search(r'--at[ =](-?\d+),(-?\d+)', ' '.join(sys.argv[1:]))       # --at X,Y: where the window opens
WIN, MAC = sys.platform == 'win32', sys.platform == 'darwin'

# --- UPDATE: Restart, and a newer version of this file (program standards, 11-Nov-2026, block 3.1 of 15-Nov) - paste unchanged ---
# Right-click > Restart starts a fresh copy of this file (same arguments) and this one ends.  While it runs, the program watches its own file:
# a NEWER VERSION saved over it counts once it has sat UPDATE_SETTLE seconds unchanged and compiles (a half-saved or broken file never counts).
# Then right-click > New versions decides (remembered, -NEW VERSIONS-; the program sets Update.default for its kind):
#   'auto'  By itself - hidden in the tray at once, showing once the mouse has been off the window UPDATE_QUIET seconds and nothing of it is open
#   'ask'   Ask me first - a small pop-up, Restart now / Later (Later by itself after 30 s); hidden in the tray it goes by itself
#   'menu'  Only say so here - never by itself; the menu reads "Restart - x.y.z is ready"
# Not the internet: the file itself - whatever put the newer copy there (a synced folder, pip, a download).
# Block 3: at each start the program compares its VERSION with the one that last ran on this PC (-RAN VERSION-).  Newer = it was updated - by
# itself, from the menu or by hand.  Update.was holds the old version; update_tag() is the version it was updated from until the user has looked
# (-UPDATED FROM-, kept across restarts) - the program shows an UPDATED tag by its version, and clicking it shows update_news(update_tag()) (the
# change-log lines since then) and calls update_tag_seen().  If this PC already has a card-log folder (a notifications program reads it), one line
# goes into it as well - nothing is created on a PC that doesn't have one.
# Wiring (update_block.md):  main() start: Update.default = 'auto' / 'ask' / 'menu';   menu, just above Exit: *update_menu(tick)
#   each event: if update_event(event): end the loop if Update.restart, else remake the menu
#   timer (every 2-5 s): if update_tick(window, hidden, busy, colors): remake the menu;  if Update.restart: end the loop
#   the very end of main(), after the window, tray icon and sockets are closed:  if Update.restart: restart_self(['--tray'] if hidden else [])
UPDATE_SETTLE = 60
UPDATE_QUIET = 10
UPDATE_CHOICES = (('auto', "By itself, while I'm not using it"), ('ask', 'Ask me first'), ('menu', 'Only say so in this menu'))


class Update:
    default = 'ask'                   # the program's kind: 'auto' widgets + tray apps, 'ask' other programs that run all day, 'menu' open-and-close
    seen = None                       # (mtime of this file when last looked at, when it changed - None while it is the file this copy started from)
    ready = ''                        # a newer VERSION saved over this file (settled, compiles)
    asked = ''                        # the version the pop-up already asked about - not asked again
    away = None                       # when the mouse left the window (for 'auto')
    restart = False                   # set -> the main loop ends, then restart_self()
    was = ''                          # block 3: the version that ran before on this PC, when this start is a newer one ('' = not updated)


def update_mode():
    mode = sg.user_settings_get_entry('-NEW VERSIONS-', Update.default)
    return mode if mode in dict(UPDATE_CHOICES) else Update.default


def update_check():
    """ Returns a newer VERSION the first time one is ready, else ''.  Cheap: one stat() a call, the file is read only after it changed and settled """
    try:
        mtime = os.path.getmtime(os.path.abspath(__file__))
    except OSError:
        return ''
    if Update.seen is None:
        Update.seen = (mtime, None)
        update_noted()                                                    # block 3: the first look - an update since the last run?
    if mtime != Update.seen[0]:
        Update.seen = (mtime, time.time())
        return ''
    if Update.seen[1] is None or time.time() - Update.seen[1] < UPDATE_SETTLE:
        return ''
    Update.seen = (mtime, None)                                           # looked at: wait for the next change
    try:
        with open(os.path.abspath(__file__), encoding='utf-8') as f:
            text = f.read()
        compile(text, __file__, 'exec')
        found = re.search(r"^VERSION = '([0-9.]+)'", text, re.M)
    except (OSError, SyntaxError, ValueError):
        return ''
    newer = found and tuple(int(x) for x in found.group(1).split('.')) > tuple(int(x) for x in VERSION.split('.'))
    if newer and found.group(1) != Update.ready:
        Update.ready = found.group(1)
        return Update.ready
    return ''


def update_noted():
    """ Block 3, once per start: this VERSION against the one that last ran on this PC (-RAN VERSION-).  Newer: Update.was = the old version, the
        UPDATED tag is set, and - only where a card-log folder already exists - one line goes into it.  Never raises """
    try:
        ran_before = bool(sg.user_settings())                             # a settings file with something in it: it ran here before
        last = str(sg.user_settings_get_entry('-RAN VERSION-', '') or '')
        sg.user_settings_set_entry('-RAN VERSION-', VERSION)
        if not last and not ran_before:                                   # its first run on this PC
            return
        if last and tuple(int(x) for x in last.split('.')) >= tuple(int(x) for x in VERSION.split('.')):
            return
        last = last or 'an earlier version'                               # it ran here before block 3 kept the version
        Update.was = last
        if not sg.user_settings_get_entry('-UPDATED FROM-'):              # not looked at yet since an earlier update: keep the oldest
            sg.user_settings_set_entry('-UPDATED FROM-', last)
        import datetime, json, uuid
        name = globals().get('APP_NAME') or os.path.splitext(os.path.basename(__file__))[0]
        new = next((re.sub(r'^\s*\d{4}-\d\d-\d\d\s+v?' + re.escape(VERSION) + r'\s*(Claude:\s*)?', '', line).strip()
                    for line in (globals().get('__doc__') or '').splitlines() if re.match(r'\s*\d{4}-\d\d-\d\d\s+v?' + re.escape(VERSION) + r'\b', line)), '')
        base = sg.DEFAULT_USER_SETTINGS_WIN_PATH if sys.platform.startswith('win') else sg.DEFAULT_USER_SETTINGS_MAC_PATH if sys.platform == 'darwin' \
            else sg.DEFAULT_USER_SETTINGS_LINUX_PATH
        folder = os.path.join(os.path.expanduser(base), 'Notifications')
        if not os.path.isdir(folder):                                     # no notifications program on this PC: nothing is written
            return
        now = datetime.datetime.now()
        line = {'v': 1, 'id': uuid.uuid4().hex[:12], 'at': now.strftime('%Y-%m-%d %H:%M:%S'), 'program': str(name)[:60], 'title': f'Updated to {VERSION}',
                'text': (f'Was {last}.  ' + new[:1].upper() + new[1:])[:2000].strip(), 'click': None, 'private': False}
        with open(os.path.join(folder, f'cards_{now:%Y-%m}.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(line, ensure_ascii=False) + '\n')
    except Exception:
        pass


def update_tag():
    """ Block 3: the version this program was updated from, until the user has looked ('' = nothing to show).  The program shows an UPDATED tag """
    return str(sg.user_settings_get_entry('-UPDATED FROM-', '') or '')


def update_tag_seen():
    """ Block 3: the user looked (clicked the tag) - the tag goes away """
    sg.user_settings_set_entry('-UPDATED FROM-', '')


def update_news(since=''):
    """ Block 3: the change-log lines of the versions after since, up to this one, newest first, each 'x.y.z  what changed' (a line that goes on
        is joined on).  since = '' or 'an earlier version': all of them """
    try:
        floor = tuple(int(x) for x in since.split('.'))
    except ValueError:
        floor = ()
    top, out, keep = tuple(int(x) for x in VERSION.split('.')), [], False
    for line in (globals().get('__doc__') or '').splitlines():
        found = re.match(r'\s*\d{4}-\d\d-\d\d\s+v?([0-9]+(?:\.[0-9]+)+)\s+(?:Claude:\s*)?(.*)', line)
        if found:
            ver = tuple(int(x) for x in found.group(1).split('.'))
            keep = floor < ver <= top
            if keep:
                out.append(f'{found.group(1)}  {found.group(2).strip()}')
        elif keep and line.startswith((' ', '\t')) and line.strip():
            out[-1] += ' ' + line.strip()
        else:
            keep = False
    return out


def restart_label():
    """ The right-click item: 'Restart', or 'Restart - 1.2.3 is ready' once a newer version waits """
    return f'Restart  -  {Update.ready} is ready' if Update.ready else 'Restart'


def update_menu(tick=None, indent='    '):
    """ The right-click items to put just above Exit: the New versions sub-menu (its choice ticked) and Restart.  tick(on) = the program's own
        check-mark prefix, so the items line up with its other ones """
    tick = tick or (lambda on: '✓ ' if on else indent)
    mode = update_mode()
    return [f'{indent}New versions', [f'{tick(k == mode)}{text}::-NEW VERSIONS {k}-' for k, text in UPDATE_CHOICES], f'{indent}{restart_label()}::Restart']


def update_event(event):
    """ True when the event was one of this block's: Restart (sets Update.restart) or a New versions choice (saved - remake the menu) """
    key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event
    if key == 'Restart':
        Update.restart = True
        return True
    for k, _ in UPDATE_CHOICES:
        if key == f'-NEW VERSIONS {k}-':
            sg.user_settings_set_entry('-NEW VERSIONS-', k)
            return True
    return False


def mouse_away(window):
    """ True once the mouse has been off the window UPDATE_QUIET seconds in a row """
    try:
        root = window.TKroot
        px, py = root.winfo_pointerxy()
        x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
        inside = x <= px < x + w and y <= py < y + h
    except Exception:
        inside = False
    if inside:
        Update.away = None
        return False
    Update.away = Update.away or time.time()
    return time.time() - Update.away >= UPDATE_QUIET


def update_tick(window, hidden=False, busy=False, colors=('#1e2430', '#e6eaf2', '#2a62a8')):
    """ Call on the timer.  hidden = the window is hidden in the tray;  busy = a dialog, panel or edit of the program is open (nothing happens
        then);  colors = (background, text, button) of the pop-up - the program's own theme.  Sets Update.restart when it is time.
        Returns True when the menu should be remade (a version became ready, or the pop-up was answered Later) """
    new = update_check()
    if not Update.ready or Update.restart:
        return bool(new)
    mode = update_mode()
    if mode == 'menu':
        return bool(new)
    if hidden:
        Update.restart = True
        return False
    quiet = mouse_away(window) and not busy
    if mode == 'auto':
        Update.restart = quiet
        return bool(new)
    if Update.asked != Update.ready and not busy:
        Update.asked = Update.ready                                       # once per version
        update_offer(window, Update.ready, colors)
        return not Update.restart
    return bool(new)


def update_offer(window, new, colors=('#1e2430', '#e6eaf2', '#2a62a8')):
    """ Ask once per version: Restart now / Later (Later by itself after 30 s, so a program never waits long).  Sets Update.restart """
    Update.asked = new
    bg, fg, button = colors
    try:
        x, y = window.current_location()
        spot = (x + 20, y + 20)
    except Exception:
        spot = (None, None)
    name = globals().get('APP_NAME') or os.path.splitext(os.path.basename(__file__))[0]
    answer = sg.popup(f'{name} {new} is here  (you run {VERSION})', 'Restart now to use it?', '(Right-click > New versions: by itself, ask, or only say so)',
                      title='New version', custom_text=('Restart now', 'Later'), keep_on_top=True, auto_close=True, auto_close_duration=30, location=spot,
                      background_color=bg, text_color=fg, button_color=('#ffffff', button), font=('Segoe UI', 11), icon=globals().get('ICON'))
    Update.restart = answer == 'Restart now'


def restart_self(extra=()):
    """ Start this file again with the same arguments (pythonw on Windows - no console).  Call it LAST: after the window, the tray icon and any
        socket this program listens on are closed, so a one-copy-at-a-time program's new copy finds the way clear """
    exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    exe = exe if sys.platform.startswith('win') and os.path.isfile(exe) else sys.executable
    args = [a for a in sys.argv[1:] if a != '--tray'] + list(extra)
    subprocess.Popen([exe, os.path.abspath(__file__)] + args, cwd=os.path.dirname(os.path.abspath(__file__)))
# --- end UPDATE ---


# --- SLIDER: a slider drawn with Pillow (program standards, 12-Nov-2026) - paste unchanged ---
# Round glass knob with a shadow, the fill from zero (or the low end) to the knob in the accent color, a zero mark, a glow while dragged.
# Press anywhere on it to put the knob there and drag; the wheel steps one (Ctrl: ten); double-click = the reset value; Left / Right / Home /
# End with the keyboard (Tab reaches it).  It is ONE picture on an sg.Image, drawn at 2x and shrunk (the antialiasing), 3-9 ms a frame, only
# while it is touched.  Chosen by Mike 12-Nov (style "D" of four tried).
# Use:   s = DrawnSlider(K_EXPOSURE, (-3.0, 3.0), 0.0, step=0.05)        ->  [sg.Text('Exposure'), s.element]  in the layout
#        after the window is finalized:  s.bind(window)                  ->  events: event == K_EXPOSURE, the value in values[K_EXPOSURE]
#        from the program:  s.set(1.5) (no event),  s.value,  s.recolor(...) after a theme change,  s.resize(width)
# Needs: PySimpleGUI as sg, Pillow (Image, ImageDraw, ImageFilter), io.
class DrawnSlider:
    def __init__(self, key, range=(0, 100), default=0, step=1, width=300, scale=1.0, reset=None, accent=None, colors=None, pad=(4, 2), tooltip=None):
        self.key, (self.lo, self.hi), self.step, self.w, self.s = key, range, step, int(width), scale
        self.reset = reset if reset is not None else (0 if self.lo <= 0 <= self.hi else self.lo)
        self.hover = self.drag = False
        self.window = None
        self.recolor(accent, colors, redraw=False)
        self.value = self.snap(default)
        self.h = round(28 * scale)
        self.element = sg.Image(data=self.render(), key=key, background_color=self.c['bg'], pad=pad, tooltip=tooltip)

    def recolor(self, accent=None, colors=None, redraw=True):
        """ Colors from the current sg theme - the window's background, a track from it, the accent from the buttons; colors={} overrides
            any of 'bg', 'track', 'fill', 'knob', 'knob_hot', 'mark'.  Call again after the program changes its theme """
        def hex_of(c):
            return c if isinstance(c, str) and c.startswith('#') and len(c) == 7 else '#808080'

        def mix(a, b, t):
            a, b = hex_of(a), hex_of(b)
            return '#%02x%02x%02x' % tuple(round(int(a[i:i + 2], 16) + (int(b[i:i + 2], 16) - int(a[i:i + 2], 16)) * t) for i in (1, 3, 5))
        bg, text = hex_of(sg.theme_background_color()), hex_of(sg.theme_text_color())
        button = sg.theme_button_color()
        accent = hex_of(accent or (button[1] if isinstance(button, (tuple, list)) else None) or '#2f74d8')
        if sum(abs(int(accent[i:i + 2], 16) - int(bg[i:i + 2], 16)) for i in (1, 3, 5)) < 150:     # a button color too near the background: blue
            accent = '#2f74d8'
        light = sum(int(bg[i:i + 2], 16) for i in (1, 3, 5)) > 384
        self.c = {'bg': bg, 'track': mix(bg, text, 0.16), 'fill': accent, 'mark': mix(bg, text, 0.5),
                  'knob': mix(text, '#ffffff', 0.35) if not light else '#ffffff', 'knob_hot': '#ffffff' if not light else mix('#ffffff', accent, 0.15)}
        self.c.update(colors or {})
        self.c['edge'] = mix(self.c['bg'], '#000000', 0.35)
        if redraw:
            if self.element.Widget is not None:
                self.element.Widget.configure(bg=self.c['bg'])
            self.redraw()

    # ---- values
    def snap(self, v):
        v = max(self.lo, min(self.hi, v))
        v = self.lo + round((v - self.lo) / self.step) * self.step
        return round(v, 6) if isinstance(self.step, float) or isinstance(self.lo, float) else int(round(v))

    def r(self):
        return 8 * self.s

    def x_of(self, v):
        r = self.r()
        return r + 2 + (v - self.lo) / ((self.hi - self.lo) or 1) * (self.w - 2 * r - 4)

    def value_at(self, x):
        r = self.r()
        return self.snap(self.lo + (x - r - 2) / max(1, self.w - 2 * r - 4) * (self.hi - self.lo))

    # ---- drawing
    def render(self):
        k, s = 2, self.s
        rgb = lambda c, a=255: tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (a,)
        im = Image.new('RGBA', (self.w * k, self.h * k), rgb(self.c['bg']))
        d = ImageDraw.Draw(im)
        cy, t, r = self.h * k / 2, 3 * s * k, self.r() * k
        x0, x1 = (self.r() + 2) * k, (self.w - self.r() - 2) * k
        d.rounded_rectangle((x0 - t, cy - t, x1 + t, cy + t), radius=t, fill=rgb(self.c['track']))
        base = max(self.lo, min(self.hi, 0))
        xz, xv = self.x_of(base) * k, self.x_of(self.value) * k
        if abs(xv - xz) >= 1:
            d.rounded_rectangle((min(xz, xv), cy - t, max(xz, xv), cy + t), radius=t, fill=rgb(self.c['fill']))
        if self.lo < 0 < self.hi:
            d.line((xz, cy - t - 3 * s * k, xz, cy + t + 3 * s * k), fill=rgb(self.c['mark']), width=max(1, round(1.2 * s * k)))
        layer = Image.new('RGBA', im.size, (0, 0, 0, 0))                  # the glow (dragging) and the knob's shadow, blurred, blended in
        ld = ImageDraw.Draw(layer)
        if self.drag:
            ld.ellipse((xv - r * 1.9, cy - r * 1.9, xv + r * 1.9, cy + r * 1.9), fill=rgb(self.c['fill'], 90))
            im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r * 0.6)))
            layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
        ld.ellipse((xv - r, cy - r + 1.5 * s * k, xv + r, cy + r + 1.5 * s * k), fill=(0, 0, 0, 130))
        im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5 * s * k)))
        d = ImageDraw.Draw(im)
        d.ellipse((xv - r, cy - r, xv + r, cy + r), fill=rgb(self.c['knob_hot'] if self.hover or self.drag else self.c['knob']),
                  outline=rgb(self.c['edge'], 200), width=max(1, round(0.8 * s * k)))
        sheen = Image.new('RGBA', im.size, (0, 0, 0, 0))                  # the glass: on its own layer, blended in (drawn straight on, it punches a hole)
        ImageDraw.Draw(sheen).chord((xv - r * 0.75, cy - r * 0.9, xv + r * 0.75, cy + r * 0.2), 180, 360, fill=(255, 255, 255, 55))
        im.alpha_composite(sheen)
        out = io.BytesIO()
        im.resize((self.w, self.h), Image.LANCZOS).save(out, 'PNG')
        return out.getvalue()

    def redraw(self):
        if self.element.Widget is not None:
            self.element.update(data=self.render())

    # ---- the mouse and the keys
    def bind(self, window):
        """ Call once the window is finalized """
        self.window = window
        w = self.element.Widget
        w.configure(takefocus=1, highlightthickness=1, highlightbackground=self.c['bg'], highlightcolor=self.c['track'], cursor='hand2')
        w.bind('<ButtonPress-1>', lambda e: (setattr(self, 'drag', True), w.focus_set(), self.post(self.value_at(e.x))))
        w.bind('<B1-Motion>', lambda e: self.post(self.value_at(e.x)))
        w.bind('<ButtonRelease-1>', lambda e: (setattr(self, 'drag', False), self.redraw()))
        w.bind('<Double-Button-1>', lambda e: self.post(self.reset))
        w.bind('<Enter>', lambda e: (setattr(self, 'hover', True), self.redraw()))
        w.bind('<Leave>', lambda e: (setattr(self, 'hover', False), self.redraw()))
        w.bind('<MouseWheel>', lambda e: self.post(self.value + (1 if e.delta > 0 else -1) * self.step * (10 if e.state & 0x4 else 1)))
        if not sg.running_windows():                                       # Linux wheel; on Windows Button-4 is the mouse's Back button
            w.bind('<Button-4>', lambda e: self.post(self.value + self.step * (10 if e.state & 0x4 else 1)))
            w.bind('<Button-5>', lambda e: self.post(self.value - self.step * (10 if e.state & 0x4 else 1)))
        w.bind('<Left>', lambda e: self.post(self.value - self.step))
        w.bind('<Right>', lambda e: self.post(self.value + self.step))
        w.bind('<Home>', lambda e: self.post(self.lo))
        w.bind('<End>', lambda e: self.post(self.hi))

    def post(self, v):
        """ From the mouse / keys: the knob moves and the window gets (key, value) """
        v = self.snap(v)
        if v != self.value:
            self.value = v
            if self.window is not None:
                self.window.write_event_value(self.key, v)
        self.redraw()

    # ---- from the program
    def set(self, v):
        """ Move the knob from the program - no event """
        self.value = self.snap(v)
        self.redraw()

    def resize(self, width):
        self.w = max(int(width), int(4 * self.r() + 20))
        self.redraw()
# --- end SLIDER ---


# ============================================================ names ============================================================
UI_FONT = 'Segoe UI' if WIN else 'Helvetica Neue' if MAC else 'DejaVu Sans'
MONO_FONT = 'Consolas' if WIN else 'Menlo' if MAC else 'DejaVu Sans Mono'
F_UI, F_SMALL, F_BOLD, F_HEAD, F_MENU = (UI_FONT, 10), (UI_FONT, 9), (UI_FONT, 10, 'bold'), (UI_FONT, 8, 'bold'), (UI_FONT, 10)
F_TITLE, F_HUD, F_BIG, F_MONO = (UI_FONT, 15, 'bold'), (UI_FONT, 10), (UI_FONT, 22, 'bold'), (MONO_FONT, 10)

C_BG, C_PANEL, C_FIELD = '#0b0e16', '#131824', '#1f2736'                # the box behind the balls, the panel, a button that is off
C_TEXT, C_DIM = '#e6eaf2', '#8791a3'
C_ACCENT, C_GOOD, C_BAD, C_WARN = '#3d8bff', '#4cc38a', '#ff6b6b', '#f0b429'
C_MENU_BG, C_MENU_SEL = '#182030', '#2a62a8'
SKY_TOP, SKY_BOTTOM = (9, 12, 20), (24, 31, 50)                         # the box's background, top to bottom
KEY_COLOR, KEY_RGB = '#010203', (1, 2, 3)                               # Desktop: the one color Windows shows as "not there" - nearly black, so
#                                                                         a ball's edge, mixed with it, is a thin dark rim and not a colored fringe
PALETTE = ('#ff5a5f', '#ff9f1c', '#ffd23f', '#9bde5a', '#2ec4b6', '#3fa7ff', '#6c7bff', '#b56cff', '#ff6fd8', '#f25f9c', '#7ae0c3', '#ffe08a')
HEAT_STOPS = ((48, 84, 214), (40, 176, 232), (62, 212, 126), (240, 222, 64), (250, 142, 44), (242, 62, 52), (255, 242, 232))
HEAT_LEVELS = 16                                                        # Speed colors: this many shades, slow to fast
HEAT_SPEED = 55.0                                                       # ...one shade for every 55 pixels a second

SETTINGS_FILE = 'psgbounce.json'
ENGINE_NAME = 'psgbounce_engine'
COUNTS = (50, 100, 200, 300, 500, 800, 1000, 1500, 2000, 3000, 4000, 5000, 7500, 10000, 15000, 20000)    # the Balls slider's stops
SCENES = (('rain', 'Rain', 'They fall, bounce and settle into a pile'), ('gas', 'Gas', 'No gravity and nothing lost in a bounce: it never stops'),
          ('pour', 'Pour', 'A stream from a spout, color after color'), ('shake', 'Shake', 'Gravity turns over every two seconds'),
          ('swarm', 'Swarm', 'No gravity: they chase a point that wanders through the box'))
SCENE_SET = {'rain': (900, 85), 'gas': (0, 100), 'pour': (900, 60), 'shake': (1400, 70), 'swarm': (0, 90)}    # each scene's gravity and bounce %
FRAME_RATES = (30, 60, 120, 0)                                          # 0 = no limit
MEAN_R2 = 61.1                                                          # the engine's scatter(5, 15): the average of radius squared
SCENE_SIZE = (1280, 720)                                                # the box at the first start, and the exercise's box
BENCH_PHYSICS = ((1000, 120), (4000, 30))                               # the exercise's physics runs: (balls, frames)
BENCH_DRAW = (1000, 4000)
BUDGET_MS = 1000 / 60                                                   # a frame's work has to fit in this for 60 frames a second
HINT = 'In the box:  click = a blast,\nhold = pull,  wheel = more / fewer,\nCtrl + wheel = bigger / smaller.\nPoint at anything here to read about it.'

K_SET_WINDOW, K_SET_BALLS, K_SET_FILL, K_SET_STEPS, K_SET_TRAILS, K_SET_HEAT = '-WINDOW-', '-BALLS-', '-FILL-', '-STEPS-', '-TRAILS-', '-SPEED COLORS-'
K_SET_RATE, K_SET_SCENE, K_SET_RESULTS = '-FRAME RATE-', '-SCENE-', '-LAST RESULTS-'
OLD_SETTINGS = ('-ENGINE-', '-PSG SCRIPTC-')                             # what versions before 1.0.5 kept for a second engine: taken out at the start
K_BOX, K_PANEL, K_KEY = '-BOX-', '-PANEL-', '-KEY-'
K_BALLS, K_FILL, K_GRAVITY, K_BOUNCE, K_STEPS = '-S BALLS-', '-S FILL-', '-S GRAVITY-', '-S BOUNCE-', '-S STEPS-'
KT_VALUE = lambda key: ('-VALUE-', key)
KT_SCENE = lambda name: ('-SCENE-', name)
KT_M_RATE = lambda rate: f'-M RATE {rate}-'
KT_M_SCENE = lambda name: f'-M SCENE {name}-'
KT_HEAD = lambda key: ('-HEAD-', key)
K_AGAIN, K_HELP = '-AGAIN-', '-HELP-'
K_TRAILS, K_HEAT, K_PAUSE, K_FULL, K_BENCH, K_RESULT, K_DESK = '-TRAILS-', '-HEAT-', '-PAUSE-', '-FULL-', '-BENCH-', '-RESULT-', '-DESKTOP-'
K_M_RESULTS, K_M_NEWS, K_CLOSE = '-M RESULTS-', '-M NEWS-', '-CLOSE-'
HELP = {                                                                # the panel's bottom lines: what the thing under the mouse does
    K_BALLS: 'BALLS - how many are in the box.\nKeys + and -, or the mouse wheel over the box.',
    K_FILL: 'FILL - how much of the box the balls take up: more fill = bigger balls.\nCtrl + wheel, or Ctrl with = - 0.',
    K_GRAVITY: 'GRAVITY - right of the mark the balls fall, on the mark they float, left of it they fall up.\nKey F turns it over.',
    K_BOUNCE: 'BOUNCE - how much of its speed a ball keeps when it hits something.\n100% = nothing is lost, it never stops.',
    K_STEPS: 'ACCURACY - for every picture the balls are moved in this many small steps.  More steps: piles stay firm and balls do not sink '
             'into each other.  Fewer: less work, softer piles.',
    K_AGAIN: 'AGAIN - the scene from its start.\nKey R.',
    K_TRAILS: 'TRAILS - each ball leaves a fading trail (not in Desktop).\nKey T.',
    K_HEAT: 'SPEED COLORS - a ball shows its speed: slow = blue ... fast = white-hot.\nKey C.',
    K_PAUSE: 'PAUSE - stop and go.\nSpace.',
    K_FULL: 'FULL SCREEN - the box alone on the whole screen.\nF11; Esc brings the window back.',
    K_DESK: 'DESKTOP - no background: the balls bounce over everything on this screen and this panel floats.\nKey D; Esc brings the window back.',
    K_BENCH: 'EXERCISE - measures the physics, the drawing and the timer of this computer.  About 20 seconds; Esc stops it.\nKey B.'}


# ============================================================ small things ============================================================
def setting(key, default):
    return sg.user_settings_get_entry(key, default)


def mix(c1, c2, f):
    a, b = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (c1, c2)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * f) for x, y in zip(a, b))


def rgb_of(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def heat_color(level):
    """ The color of a speed, level 0 (slow) to HEAT_LEVELS - 1 (fast): blue, cyan, green, yellow, orange, red, nearly white """
    at = level / (HEAT_LEVELS - 1) * (len(HEAT_STOPS) - 1)
    k = min(len(HEAT_STOPS) - 2, int(at))
    return tuple(round(a + (b - a) * (at - k)) for a, b in zip(HEAT_STOPS[k], HEAT_STOPS[k + 1]))


def ui_scale():
    """ The display's scaling, 1.0 = 100% (Windows; elsewhere tk does the fonts itself) """
    try:
        return max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96) if WIN else 1.0
    except Exception:
        return 1.0


def fmt_size(n):
    for unit in ('bytes', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return f'{n:,.0f} {unit}' if unit == 'bytes' else f'{n:,.1f} {unit}'
        n /= 1024


def open_folder(path):
    """ A folder in the file manager PySimpleGUI is set to use, else the system's own """
    try:
        if sg.pysimplegui_user_settings.get('-explorer program-', None):
            sg.execute_file_explorer(f'"{path}"' if ' ' in path else path)
        elif WIN:
            os.startfile(path)
        else:
            subprocess.Popen(['open' if MAC else 'xdg-open', path])
    except Exception as e:
        sg.popup_error(f'The folder could not be opened:\n{path}\n\n{e}', title=APP_NAME, keep_on_top=True)


def descendants(widget):
    out = [widget]
    for child in widget.winfo_children():
        out.extend(descendants(child))
    return out


def menu_arrows(menu, dark):
    """ Windows draws a sub-menu's arrow in Windows' own menu-text color (black, white only on the lit row) whatever the menu's colors, so on a dark
        menu it can't be seen.  This puts a › in the menu's own text color at the right end of each sub-menu's label instead.  Windows and dark
        menus only.  Safe to call again """
    if not (dark and WIN) or menu.index('end') is None:
        return
    f = tkinter.font.Font(root=menu, font=menu.cget('font'))
    labels = {}
    for i in range(menu.index('end') + 1):
        if menu.type(i) in ('command', 'cascade', 'checkbutton', 'radiobutton'):
            label = menu.entrycget(i, 'label')
            labels[i] = label.rstrip('  ›') if menu.type(i) == 'cascade' and label.endswith('›') else label
    cascades = [i for i in labels if menu.type(i) == 'cascade']
    if not cascades:
        return
    end = max(f.measure(text) for text in labels.values()) + f.measure('      ›')
    for i in cascades:
        label = labels[i] + '  '
        while f.measure(label + ' ›') <= end:
            label += ' '
        while f.measure(label + ' ›') <= end:
            label += ' '
        menu.entryconfigure(i, label=label + '›')


def style_menus(window):
    """ tk draws menus Windows-gray: every menu of the window and its sub-menus flat and compact in this program's colors """
    for menu in descendants(window.TKroot):
        if menu.winfo_class() == 'Menu':
            menu.configure(bg=C_MENU_BG, fg=C_TEXT, activebackground=C_MENU_SEL, activeforeground='#ffffff', disabledforeground=C_DIM, bd=0,
                           activeborderwidth=1, relief='flat', font=F_MENU)
            menu_arrows(menu, True)


def set_window_menu(window, menu):
    """ The right-click menu of a whole window, made here and not by PySimpleGUI's right_click_menu=: that gives every element a menu of its
        own - 45 of them made 1.9 seconds of a window's start, and making them again for a moved tick stopped the balls for half a second.
        ONE menu is made (through the first element) and everything in the window, and the window itself, pops that one up """
    elements = [e for e in window.element_list() if e.Widget is not None]
    if not elements:
        return
    window.RightClickMenu = menu
    elements[0].set_right_click_menu(menu, propogate_to_window=True)       # makes the menu (and takes this element's old one away)
    for e in elements[1:]:
        e.TKRightClickMenu = elements[0].TKRightClickMenu
    button = '<ButtonRelease-2>' if MAC else '<ButtonRelease-3>'
    if not getattr(window, 'menu_bound', False):
        window.menu_bound = True
        for e in elements[1:]:
            e.Widget.bind(button, e._RightClickMenuCallback)
        window.TKroot.bind(button, window._RightClickMenuCallback)


def relabel_menu(menu, items):
    """ The labels of a menu (and its sub-menus) set again from its definition - a tick that moved - without making the menu again.
        False when the menu no longer has the definition's shape: then it has to be made again """
    at = k = 0
    last = menu.index('end')
    while k < len(items):
        item = items[k]
        sub = items[k + 1] if k + 1 < len(items) and isinstance(items[k + 1], list) else None
        if isinstance(item, list) or last is None or at > last:
            return False
        kind = menu.type(at)
        if item == '---':
            if kind != 'separator':
                return False
        elif kind != ('cascade' if sub is not None else 'command'):
            return False
        else:
            menu.entryconfigure(at, label=item.split('::')[0])
            if sub is not None and not relabel_menu(menu.nametowidget(menu.entrycget(at, 'menu')), sub):
                return False
        at += 1
        k += 2 if sub is not None else 1
    return at == (last + 1 if last is not None else 0)


def dark_title_bar(window):
    """ A dark title bar to match (Windows 10 / 11) """
    try:
        hwnd = ctypes.windll.user32.GetParent(window.TKroot.winfo_id())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
    except Exception:
        pass


def monitor_work_area(window):
    """ (left, top, right, bottom) of the screen the window is on, without the taskbar - what Desktop covers (Windows) """
    from ctypes import wintypes

    class MONITORINFO(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT), ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]

    root = window.TKroot
    try:
        user32 = ctypes.windll.user32
        user32.GetParent.restype, user32.GetParent.argtypes = wintypes.HWND, [wintypes.HWND]
        user32.MonitorFromWindow.restype, user32.MonitorFromWindow.argtypes = wintypes.HANDLE, [wintypes.HWND, wintypes.DWORD]
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(user32.MonitorFromWindow(user32.GetParent(root.winfo_id()), 2), ctypes.byref(info)):       # 2 = the nearest screen
            return info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom
    except Exception:
        pass
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def window_dc(hwnd, release=None):
    """ The device context to draw on a window with (Windows) - or, given one back, it is released """
    user32 = ctypes.windll.user32
    if release is None:
        user32.GetDC.restype, user32.GetDC.argtypes = ctypes.c_void_p, [ctypes.c_void_p]
        return user32.GetDC(hwnd)
    user32.ReleaseDC.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    user32.ReleaseDC(hwnd, release)


def clip_dc(dc, box):
    """ What is drawn with this device context from now on only lands inside the rectangle (Windows) """
    gdi32 = ctypes.windll.gdi32
    gdi32.IntersectClipRect.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    gdi32.IntersectClipRect(dc, *box)


def fit_min_size(window):
    """ The smallest the window may get: what its rows need at their layout size - so its bottom rows are never cut off """
    root = window.TKroot
    root.update_idletasks()
    window.set_min_size((min(root.winfo_reqwidth(), root.winfo_screenwidth() - 40), min(root.winfo_reqheight(), root.winfo_screenheight() - 80)))


# ============================================================ what this computer is ============================================================
def cpu_name():
    try:
        if WIN:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                return ' '.join(winreg.QueryValueEx(key, 'ProcessorNameString')[0].split())
        if MAC:
            return subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True, timeout=3).stdout.strip()
        with open('/proc/cpuinfo', encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.lower().startswith(('model name', 'hardware')):
                    return ' '.join(line.split(':', 1)[1].split())
    except Exception:
        pass
    return platform.processor() or platform.machine() or 'unknown processor'


def os_name():
    if WIN:
        build = sys.getwindowsversion().build
        return f'Windows {"11" if build >= 22000 else platform.release()} (build {build})'
    if MAC:
        return f'macOS {platform.mac_ver()[0]}'
    try:
        pretty = platform.freedesktop_os_release().get('PRETTY_NAME', 'Linux')
    except (OSError, AttributeError):
        pretty = 'Linux'
    kernel = platform.release()
    return f'{pretty}, kernel {kernel}' + ('  (WSL)' if 'microsoft' in kernel.lower() else '')


def environment(root):
    """ The lines over the exercise results: the system, the processor, and the versions of everything the program stands on.  No names of
        the computer or its user """
    try:
        tk_version = root.tk.call('info', 'patchlevel')
        system = str(root.tk.call('tk', 'windowingsystem'))
        screen = f'{root.winfo_screenwidth()} x {root.winfo_screenheight()}, scaling {round(root.winfo_fpixels("1i") / 96 * 100)}%'
    except Exception:
        tk_version, system, screen = '?', '?', '?'
    session = os.environ.get('XDG_SESSION_TYPE', '')
    in_exe = not os.path.basename(sys.executable).lower().startswith('python')
    return [f'{os_name()}     {cpu_name()}, {os.cpu_count()} threads',
            f'Python {platform.python_version()} ({platform.python_implementation()}, {platform.architecture()[0]})' + ('  running inside an exe' if in_exe else '') +
            f'     tk {tk_version} on {system}' + (f' ({session})' if session and session != system else '') +
            f'     PySimpleGUI {sg.version.split()[0]}     Pillow {PIL.__version__}',
            f'Screen {screen}']


# ============================================================ the physics ============================================================
def python_engine():
    """ ENGINE_SOURCE run as a module of its own.  Its lines show in a traceback as psgbounce_engine.py """
    module = types.ModuleType(ENGINE_NAME)
    module.__file__ = ENGINE_NAME + '.py'
    linecache.cache[module.__file__] = (len(ENGINE_SOURCE), None, ENGINE_SOURCE.splitlines(True), module.__file__)
    exec(compile(ENGINE_SOURCE, module.__file__, 'exec'), module.__dict__)
    return module


# ============================================================ pictures ============================================================
def make_sprite(r, rgb):
    """ A glossy ball of radius r pixels as a see-through picture 2r + 2 wide: drawn several times the size and shrunk, so its edge is smooth """
    size = 2 * r + 2
    z = 4 if r < 28 else 2
    big, c, R = size * z, size * z / 2, r * z
    im = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if r <= 2:                                                             # a dot: no room for a shine
        d.ellipse((c - R, c - R, c + R, c + R), fill=rgb + (255,))
        return im.resize((size, size), Image.LANCZOS)
    dark = tuple(int(v * 0.50) for v in rgb)
    light = tuple(int(v + (255 - v) * 0.38) for v in rgb)
    steps = 10 if r < 8 else 16
    for k in range(steps + 1):                                             # from the dark rim to the lit spot, up and to the left
        f = k / steps
        rr = R * (1 - 0.92 * f)
        x, y = c - R * 0.30 * f, c - R * 0.34 * f
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=tuple(int(dark[i] + (light[i] - dark[i]) * f ** 0.6) for i in range(3)) + (255,))
    edge = im.getchannel('A')
    shine = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(shine).ellipse((c - R * 0.60, c - R * 0.68, c - R * 0.10, c - R * 0.30), fill=(255, 255, 255, 165))
    im.alpha_composite(shine.filter(ImageFilter.GaussianBlur(R * 0.09)))
    im.putalpha(edge)
    return im.resize((size, size), Image.LANCZOS)


def make_back(w, h):
    """ The box's background: a dark sky, a little lighter toward the floor """
    column = Image.new('RGB', (1, h))
    column.putdata([tuple(round(a + (b - a) * (y / max(1, h - 1)) ** 1.6) for a, b in zip(SKY_TOP, SKY_BOTTOM)) for y in range(h)])
    return column.resize((w, h))


# ============================================================ the program ============================================================
class App:
    def __init__(self):
        self.eng = python_engine()                                         # the physics: a module of its own, kept in this file
        self.count = setting(K_SET_BALLS, 500) if setting(K_SET_BALLS, 500) in COUNTS else 500
        self.fill = min(70, max(10, int(setting(K_SET_FILL, 30))))        # percent of the box the balls take up
        self.steps = min(8, max(1, int(setting(K_SET_STEPS, 4))))
        self.trails, self.heat = bool(setting(K_SET_TRAILS, True)), bool(setting(K_SET_HEAT, False))
        self.rate = setting(K_SET_RATE, 60) if setting(K_SET_RATE, 60) in FRAME_RATES else 60
        self.scene = setting(K_SET_SCENE, 'rain') if setting(K_SET_SCENE, 'rain') in SCENE_SET else 'rain'
        self.gravity, self.bounce = SCENE_SET[self.scene]                  # pixels / s / s downward; percent
        self.scale = 1.0                                                   # how many times the engine's 5 - 15 pixel radii the balls are now
        self.size = self.seen_size = SCENE_SIZE                            # the box now; the size the window gave it last
        self.paused = self.full = False
        self.desktop, self.work_area = False, None                         # Desktop: the box is a screen, see-through - and that screen's edges
        self.stage = self.source = None                                    # the window the box is in (in Desktop not the panel's); where an event came from
        self.box_canvas, self.was_window = None, None                      # the window's own box; its place, smallest size and state before Desktop
        self.dib, self.drawn, self.exposed, self.max_off = None, None, True, 0     # Desktop: the Windows bitmap the picture is copied to the window from;
        #                                                                    the rectangle drawn in last frame; tk repainted (so: all of it again); the widest ball
        self.window = self.canvas = self.photo = self.frame = self.back = None
        self.sprites = {}                                                  # (radius, color) -> picture
        self.ball_sprite, self.ball_rows, self.ball_off, self.styled = [], [], [], -1
        self.mouse, self.down, self.held = (SCENE_SIZE[0] // 2, SCENE_SIZE[1] // 2), None, False
        self.todo = []                                                     # what the mouse asked for since the last frame
        self.rings = []                                                    # blasts still drawn: [x, y, when]
        self.scene_time, self.pour_left, self.pour_owed = 0.0, 0, 0.0
        self.last = self.due = time.perf_counter()
        self.work = collections.deque(maxlen=120)                          # the last frames' work, milliseconds
        self.phys_ms = self.draw_ms = 0.0
        self.frames, self.fps, self.fps_since, self.contacts = 0, 0.0, time.perf_counter(), 0
        self.said, self.said_until = '', 0.0                               # big words in the middle of the box for a moment
        self.bench = None                                                  # the exercise while it runs (a generator)
        self.bench_words, self.keep = '', None
        self.result = setting(K_SET_RESULTS, '')
        self.slow_tick = time.time()

    # ---------------------------------------------------------------- the window ----------------------------------------------------------------
    def title(self):
        return f'{APP_NAME}  {VERSION}' + ('  -  demo' if DEMO else '') + ('  -  UPDATED' if update_tag() else '')

    def menu(self):
        tick = lambda on: '✓ ' if on else '    '
        scenes = [f'{tick(name == self.scene)}{text}    {n + 1}::{KT_M_SCENE(name)}' for n, (name, text, _) in enumerate(SCENES)]
        rates = [f'{tick(rate == self.rate)}{rate or "No limit"}{" frames a second" if rate else ""}::{KT_M_RATE(rate)}' for rate in FRAME_RATES]
        return ['', [f'{APP_NAME} {VERSION}::Version', '---',
                     f'    Exercise this computer    B::{K_BENCH}', f'    The last results...::{K_M_RESULTS}', '---',
                     '    Scene', scenes, f'    The scene again    R::{K_AGAIN}', '---',
                     f'{tick(self.trails)}Trails    T::{K_TRAILS}', f'{tick(self.heat)}Speed colors    C::{K_HEAT}',
                     f'{tick(self.paused)}Pause    Space::{K_PAUSE}', f'{tick(self.full)}Full screen    F11::{K_FULL}',
                     *([f'{tick(self.desktop)}Desktop    D::{K_DESK}'] if WIN else []), '    Frame rate', rates, '---',
                     '    Edit Me::Edit Me', f'    Version {VERSION}::Version', f"    What's new...::{K_M_NEWS}", *update_menu(tick), '    Exit::Exit']]

    def remake_menu(self):
        """ The right-click menus say what is so now: their labels set again (a tick moved); made again only when an item came or went """
        menu = self.menu()
        for window in {self.window, self.stage}:
            try:
                same = relabel_menu(window.TKRightClickMenu, menu[1])
            except Exception:
                same = False
            if not same:
                set_window_menu(window, menu)
            style_menus(window)

    def make_window(self):
        scale = ui_scale()
        wide = round(236 * scale)
        self.sliders = {
            K_BALLS: DrawnSlider(K_BALLS, (0, len(COUNTS) - 1), COUNTS.index(self.count), 1, wide, scale, reset=COUNTS.index(500)),
            K_FILL: DrawnSlider(K_FILL, (10, 70), self.fill, 5, wide, scale, reset=30),
            K_GRAVITY: DrawnSlider(K_GRAVITY, (-2000, 2000), self.gravity, 50, wide, scale),
            K_BOUNCE: DrawnSlider(K_BOUNCE, (0, 100), self.bounce, 5, wide, scale, reset=85),
            K_STEPS: DrawnSlider(K_STEPS, (1, 8), self.steps, 1, wide, scale, reset=4)}
        self.help = {**HELP, **{KT_SCENE(name): f'{text.upper()} - {tip}.\nKey {n + 1}.' for n, (name, text, tip) in enumerate(SCENES)}}

        def slider(text, key):
            return [[sg.Text(text, key=KT_HEAD(key), font=F_HEAD, text_color=C_DIM, pad=((6, 0), (4, 0))), sg.Push(),
                     sg.Text('', key=KT_VALUE(key), font=F_BOLD, pad=((0, 8), (4, 0)), size=(11, 1), justification='right')],
                    [self.sliders[key].element]]

        def button(text, key, size=(9, 1), color=None):
            return sg.Button(text, key=key, size=size, border_width=0, font=F_UI, pad=((4, 2), (3, 3)), button_color=color or (C_TEXT, C_FIELD),
                             mouseover_colors=('#ffffff', mix(C_FIELD, C_ACCENT, 0.5)), focus=False, disabled_button_color=(mix(C_FIELD, C_DIM, 0.5), C_FIELD))

        scenes = [button(text, KT_SCENE(name), size=(7, 1)) for name, text, _ in SCENES]
        panel = [[sg.Text(APP_NAME, font=F_TITLE, pad=((6, 6), (8, 0))), sg.Text(VERSION, font=F_SMALL, text_color=C_DIM, pad=(0, (14, 0)))],
                 *slider('BALLS', K_BALLS), *slider('FILL', K_FILL), *slider('GRAVITY', K_GRAVITY), *slider('BOUNCE', K_BOUNCE), *slider('ACCURACY', K_STEPS),
                 [sg.Text('SCENES', font=F_HEAD, text_color=C_DIM, pad=((6, 0), (10, 2)))],
                 scenes[:3], scenes[3:] + [button('Again', K_AGAIN, size=(7, 1))],
                 [sg.Text('', font=(UI_FONT, 2), pad=(0, 0))],
                 [button('Trails', K_TRAILS, size=(12, 1)), button('Speed colors', K_HEAT, size=(12, 1))],
                 [button('Pause', K_PAUSE, size=(12, 1)), button('Full screen', K_FULL, size=(12, 1))],
                 *([[button('Desktop', K_DESK, size=(26, 1))]] if WIN else []),
                 [sg.Text('', font=(UI_FONT, 2), pad=(0, 0))],
                 [button('Exercise this computer', K_BENCH, size=(26, 1), color=('#ffffff', C_ACCENT))],
                 [sg.Text('', key=K_RESULT, font=F_SMALL, text_color=C_DIM, size=(36, 3), pad=((6, 0), (2, 0)))],
                 [sg.Text(HINT, key=K_HELP, font=F_SMALL, text_color=C_DIM, size=(36, 5), pad=((6, 0), (4, 8)))]]
        side = sg.Column(panel, key=K_PANEL, pad=(0, 0), vertical_alignment='top', element_justification='left')      # no expand_y here: PySimpleGUI
        #                                                                    would then stretch the row only downward, and the box could not grow sideways
        layout = [[sg.Graph((480, 300), (0, 300), (480, 0), key=K_BOX, background_color=C_BG, expand_x=True, expand_y=True, pad=(0, 0)), side]]
        saved = setting(K_SET_WINDOW, None)
        place = (None, None)
        if AT:
            place, saved = (int(AT.group(1)), int(AT.group(2))), None
        elif isinstance(saved, list) and len(saved) == 4 and all(isinstance(v, int) for v in saved) and not DEMO:
            place = (saved[0], saved[1])
        self.window = self.stage = w = sg.Window(self.title(), layout, icon=ICON, finalize=True, resizable=True, margins=(0, 0), font=F_UI, location=place,
                                                 enable_close_attempted_event=True, background_color=C_PANEL)
        root = w.TKroot
        dark_title_bar(w)
        fit_min_size(w)
        panel_w = w[K_PANEL].Widget.winfo_reqwidth()
        if saved and place != (None, None) and saved[2] >= 300 and saved[3] >= 200:
            root.geometry(f'{saved[2]}x{saved[3]}')
            root.update_idletasks()
            x, y = root.winfo_x() - root.winfo_vrootx(), root.winfo_y() - root.winfo_vrooty()
            if not (80 - saved[2] < x < root.winfo_vrootwidth() - 80 and -20 < y < root.winfo_vrootheight() - 80):
                root.geometry('+60+60')                                    # saved on a screen that is gone
        else:
            fit_w = min(SCENE_SIZE[0] + panel_w, root.winfo_screenwidth() - 80)
            root.geometry(f'{fit_w}x{min(max(SCENE_SIZE[1], root.winfo_reqheight()), root.winfo_screenheight() - 120)}')
        for s in self.sliders.values():
            s.bind(w)
        for key, text in self.help.items():                                # the panel's bottom lines follow the mouse: a control, its heading, its value
            if key in w.AllKeysDict:
                for widget in [w[key].Widget] + ([w[KT_HEAD(key)].Widget, w[KT_VALUE(key)].Widget] if key in self.sliders else []):
                    widget.bind('<Enter>', lambda e, text=text: self.show_help(text), add='+')
                    widget.bind('<Leave>', lambda e: self.show_help(None), add='+')
        for element in w.element_list():                                   # a button never keeps the keyboard: Space is Pause, not "press the last button again"
            if isinstance(element, sg.Button):
                element.Widget.configure(takefocus=0)
                element.Widget.bind('<KeyPress-space>', lambda e: (self.todo.append(('pause', 0)), 'break')[1])
        set_window_menu(w, self.menu())                                    # one menu for the whole window
        style_menus(w)
        w.bind('<KeyPress>', K_KEY)
        w.bind('<F11>', K_FULL)
        root.protocol('WM_DELETE_WINDOW', lambda: self.window.write_event_value(K_CLOSE, None))      # the X and Alt-F4: PySimpleGUI's own "close
        #                                                                    attempted" event is not sent while several windows are read at once
        self.canvas = self.box_canvas = c = w[K_BOX].Widget
        c.configure(highlightthickness=0, bd=0, cursor='crosshair')
        root.update()
        self.seen_size = (max(160, c.winfo_width()), max(120, c.winfo_height()))
        self.img_id = c.create_image(0, 0, anchor='nw')
        self.spark_base = c.create_line(0, 0, 0, 0, fill=mix(C_BG, C_TEXT, 0.25), dash=(2, 4))
        self.spark = c.create_line(0, 0, 0, 0, fill=C_ACCENT, width=max(1, round(scale)))
        self.hud_shadow = c.create_text(13, 11, anchor='nw', fill='#000000', font=F_HUD, text='')
        self.hud = c.create_text(12, 10, anchor='nw', fill=C_TEXT, font=F_HUD, text='')
        self.big_shadow = c.create_text(0, 0, anchor='center', fill='#000000', font=F_BIG, text='', justify='center')
        self.big = c.create_text(0, 0, anchor='center', fill='#ffffff', font=F_BIG, text='', justify='center')
        self.ui = scale if WIN else max(1.0, root.winfo_fpixels('1i') / 96)
        c.bind('<Configure>', lambda e: setattr(self, 'seen_size', (max(160, e.width), max(120, e.height))))
        c.bind('<Expose>', lambda e: setattr(self, 'exposed', True))
        self.bind_mouse(c)
        self.resize_box(*self.seen_size)
        self.show_panel()

    def bind_mouse(self, widget):
        """ The mouse over the box - the canvas, or in Desktop one of the picture's parts """
        widget.bind('<ButtonPress-1>', self.on_press)
        widget.bind('<B1-Motion>', lambda e: setattr(self, 'mouse', self.spot(e)))
        widget.bind('<Motion>', lambda e: setattr(self, 'mouse', self.spot(e)))
        widget.bind('<ButtonRelease-1>', self.on_release)
        if self.desktop:                                                   # no wheel there: it belongs to whatever is being read under the balls
            return
        widget.bind('<MouseWheel>', lambda e: self.todo.append(('fill' if e.state & 0x4 else 'balls', 1 if e.delta > 0 else -1)))
        if not WIN:                                                        # Linux wheel; on Windows Button-4 is the mouse's Back button
            widget.bind('<Button-4>', lambda e: self.todo.append(('fill' if e.state & 0x4 else 'balls', 1)))
            widget.bind('<Button-5>', lambda e: self.todo.append(('fill' if e.state & 0x4 else 'balls', -1)))

    def spot(self, e):
        """ Where in the box a mouse event happened, whichever widget of the box it came from """
        return e.x_root - self.canvas.winfo_rootx(), e.y_root - self.canvas.winfo_rooty()

    def on_press(self, e):
        self.mouse, self.down, self.held = self.spot(e), (time.perf_counter(), e.x_root, e.y_root), True
        self.canvas.focus_set()

    def on_release(self, e):
        """ A click is acted on when the button comes up, and only if the mouse stayed where it went down: a blast there """
        if self.down and time.perf_counter() - self.down[0] < 0.3 and abs(e.x_root - self.down[1]) + abs(e.y_root - self.down[2]) < 6:
            self.todo.append(('blast', self.spot(e)))
        self.down, self.held = None, False

    def set_desktop(self, on):
        """ Into Desktop and back: the windows are made again around the same world - in Desktop a see-through one as big as the screen the
            window was on, and the panel as a small window of its own """
        if on == self.desktop or (on and not WIN) or self.bench is not None:
            return
        if self.full:
            self.toggle('full')
        w, scale = self.window, ui_scale()
        root, box, side = w.TKroot, w[K_BOX].Widget, w[K_PANEL].Widget
        if on:
            self.save_place()
            left, top, right, bottom = self.work_area = monitor_work_area(w)
            state = root.state()
            if state == 'zoomed':
                root.state('normal')
            self.was_window = (root.geometry(), root.minsize(), state)
            wide, high = right - left, bottom - top
            self.stage = sg.Window(APP_NAME, [[sg.Graph((wide, high), (0, high), (wide, 0), key=K_BOX, background_color=KEY_COLOR, pad=(0, 0))]], icon=ICON,
                                   finalize=True, keep_on_top=True, margins=(0, 0), element_padding=(0, 0), alpha_channel=0, location=(left, top), size=(wide, high),
                                   transparent_color=KEY_COLOR, background_color=KEY_COLOR, enable_close_attempted_event=True)
            stage = self.stage.TKroot                                      # its title bar is taken off here, not by PySimpleGUI's no_titlebar: that one
            stage.withdraw()                                               # also takes the keyboard away from whatever program is being typed in
            stage.overrideredirect(True)
            stage.geometry(f'{wide}x{high}+{left}+{top}')
            stage.deiconify()
            stage.attributes('-topmost', True)
            stage.attributes('-alpha', 1.0)
            set_window_menu(self.stage, self.menu())
            self.stage.bind('<KeyPress>', K_KEY)
            stage.protocol('WM_DELETE_WINDOW', lambda: self.window.write_event_value(K_CLOSE, None))
            self.desktop = True
            self.canvas = c = self.stage[K_BOX].Widget
            c.configure(highlightthickness=0, bd=0, cursor='crosshair')
            c.bind('<Expose>', lambda e: setattr(self, 'exposed', True))
            self.bind_mouse(c)
            box.pack_forget()                                              # the window keeps only its panel, small, in a corner of that screen, on top
            root.minsize(1, 1)
            root.resizable(False, False)
            root.update_idletasks()
            root.geometry(f'{side.winfo_reqwidth()}x{side.winfo_reqheight()}+{right - side.winfo_reqwidth() - round(70 * scale)}+{top + round(60 * scale)}')
            root.attributes('-topmost', True)
            stage.update_idletasks()
            root.focus_force()                                             # the keys (D, Esc, Space ...) are the panel's at once, not the unseen window's
            self.seen_size = (wide, high)
            self.resize_box(wide, high)
        else:
            self.stage.close()
            self.stage, self.canvas, self.desktop, self.dib = w, self.box_canvas, False, None
            box.pack(side='left', expand=True, fill='both', before=side)
            root.attributes('-topmost', False)
            root.resizable(True, True)
            root.minsize(*self.was_window[1])
            root.geometry(self.was_window[0])
            if self.was_window[2] == 'zoomed':
                root.state('zoomed')
            root.update()
            self.seen_size = (max(160, box.winfo_width()), max(120, box.winfo_height()))
            self.resize_box(*self.seen_size)
            self.start_scene(keep_panel=True)                              # the box is small again: the scene from its start, not a crush at its walls
        for key in (K_TRAILS, K_FULL):                                     # neither has a meaning over the desktop
            w[key].update(disabled=on)
        self.show_panel()
        self.remake_menu()
        self.work.clear()
        self.last = time.perf_counter()

    def save_place(self):
        root = self.window.TKroot
        try:
            if not DEMO and not self.full and not self.desktop and root.state() == 'normal':
                sg.user_settings_set_entry(K_SET_WINDOW, [root.winfo_x(), root.winfo_y(), root.winfo_width(), root.winfo_height()])
        except Exception:
            pass

    def show_help(self, text):
        """ The lines at the panel's bottom: what the thing under the mouse does - with nothing under it, how the mouse works in the box """
        self.window[K_HELP].update(text or HINT, text_color=C_TEXT if text else C_DIM)

    def say(self, words, seconds=1.6):
        self.said, self.said_until = words, time.perf_counter() + seconds

    def show_panel(self):
        """ The panel's values, and which buttons are lit """
        w = self.window
        on, off = ('#ffffff', C_ACCENT), (C_TEXT, C_FIELD)
        w[KT_VALUE(K_BALLS)].update(f'{self.count:,}')
        w[KT_VALUE(K_FILL)].update(f'{self.fill}%')
        w[KT_VALUE(K_GRAVITY)].update('none' if not self.gravity else f'{abs(self.gravity):,} {"down" if self.gravity > 0 else "up"}')
        w[KT_VALUE(K_BOUNCE)].update(f'{self.bounce}%')
        w[KT_VALUE(K_STEPS)].update(f'{self.steps} step' + ('' if self.steps == 1 else 's'))
        for key, value in ((K_BALLS, COUNTS.index(self.count)), (K_FILL, self.fill), (K_GRAVITY, self.gravity), (K_BOUNCE, self.bounce), (K_STEPS, self.steps)):
            if self.sliders[key].value != value and not self.sliders[key].drag:
                self.sliders[key].set(value)
        for name, _, _ in SCENES:
            w[KT_SCENE(name)].update(button_color=on if name == self.scene else off)
        lights = [(K_HEAT, self.heat), (K_PAUSE, self.paused)]
        lights += [] if self.desktop else [(K_TRAILS, self.trails), (K_FULL, self.full)]                 # in Desktop those two are switched off
        lights += [(K_DESK, self.desktop)] if WIN else []
        for key, lit in lights:
            w[key].update(button_color=on if lit else off)
        w[K_PAUSE].update('Go on' if self.paused else 'Pause')
        if not self.desktop:                                               # in Desktop that place holds the numbers (show_numbers)
            w[K_RESULT].update(self.result_summary())

    def result_summary(self):
        found = re.search(r'^  Most balls at 60 frames a second: +(.*)$', self.result, re.M)
        when = re.search(r'^.*results +(.*)$', self.result.split('\n')[0]) if self.result else None
        if not found:
            return ''
        return f'Last exercise, {when.group(1).strip() if when else "?"}:\n{found.group(1).strip()} balls at 60 frames a second'

    # ---------------------------------------------------------------- the world ----------------------------------------------------------------
    def scale_for(self, n):
        """ How many times the engine's 5 - 15 pixel radii n balls must be to take up the Fill share of the box.  In Desktop the box is a
            whole screen: there the balls keep the size they have in the 1280 x 720 box """
        w, h = SCENE_SIZE if self.desktop else self.size
        return max(0.12, min(3.0, math.sqrt(self.fill / 100 * w * h / (max(1, n) * math.pi * MEAN_R2))))

    def apply_world(self, eng=None):
        """ The box's size and the panel's gravity and bounce into the engine """
        eng = eng or self.eng
        eng.resize(float(self.size[0]), float(self.size[1]))
        eng.set_gravity(float(self.gravity))
        eng.set_bounce(self.bounce / 100)
        eng.set_give(0.5)

    def resize_box(self, w, h):
        """ The box is w x h now: new pictures, the engine told, the balls sized to keep their share of it """
        self.size = (w, h)
        c = self.canvas
        if self.desktop:                                                   # no tk picture there: the frame goes to the window through a Windows bitmap
            self.back = self.photo = None
            self.frame = Image.new('RGB', (w, h), KEY_RGB)
            self.dib = ImageWin.Dib('RGB', (w, h))
            self.dib.paste(self.frame)
            self.drawn, self.exposed = None, True
        else:
            self.back = make_back(w, h)
            self.frame = self.back.copy()
            self.photo = ImageTk.PhotoImage(self.frame)
            c.itemconfigure(self.img_id, image=self.photo)
            c.itemconfigure(self.hud, width=max(100, w - 24))              # a narrow box: the numbers go onto more lines
            c.itemconfigure(self.hud_shadow, width=max(100, w - 24))
            c.coords(self.big, w / 2, h / 2)
            c.coords(self.big_shadow, w / 2 + 2, h / 2 + 2)
        self.apply_world()
        self.fit_balls()

    def fit_balls(self):
        """ The balls get the size that makes them take up the Fill share of the box """
        want = self.scale_for(max(self.count, 1))
        if self.eng.ball_count() and abs(want / self.scale - 1) > 0.001:
            self.eng.grow(want / self.scale)
        self.scale = want
        self.styled = -1

    def set_count(self, n):
        """ More or fewer balls, the others staying as they are (and all of them resized to keep the Fill) """
        n = min(COUNTS[-1], max(COUNTS[0], n))
        self.count = n
        have = self.eng.ball_count() + self.pour_left
        if n < have:
            gone = min(self.pour_left, have - n)
            self.pour_left -= gone
            self.eng.remove_balls(have - n - gone)
        self.fit_balls()
        if n > have and self.scene == 'pour':
            self.pour_left += n - have
        elif n > have:
            self.eng.scatter(n - have, 5 * self.scale, 15 * self.scale, 300.0, len(PALETTE))
        self.styled = -1
        sg.user_settings_set_entry(K_SET_BALLS, n)

    def start_scene(self, name=None, keep_panel=False):
        """ A scene from its start: the box emptied and filled its way.  keep_panel: the panel's gravity and bounce stay as they are """
        self.scene = name or self.scene
        if not keep_panel:
            self.gravity, self.bounce = SCENE_SET[self.scene]
        eng = self.eng
        eng.remove_balls(eng.ball_count())
        eng.set_seed(2026 if DEMO else random.randrange(1, 2 ** 31 - 1))
        self.apply_world()
        self.scale = self.scale_for(self.count)
        self.scene_time, self.pour_left, self.pour_owed = 0.0, 0, 0.0
        if self.scene == 'pour':
            self.pour_left = self.count
        else:
            eng.scatter(self.count, 5 * self.scale, 15 * self.scale, {'gas': 420.0, 'swarm': 120.0}.get(self.scene, 300.0), len(PALETTE))
        self.styled = -1
        self.rings = []
        sg.user_settings_set_entry(K_SET_SCENE, self.scene)

    def scene_forces(self, dt):
        """ What a scene does to the world as it runs """
        eng, (w, h) = self.eng, self.size
        self.scene_time += dt
        t = self.scene_time
        if self.scene == 'pour' and self.pour_left > 0:                    # the spout: up on the left, shooting right; a new color every so often
            self.pour_owed += self.count / 6 * dt
            hue = int(t * 2.5) % len(PALETTE)
            while self.pour_owed >= 1 and self.pour_left > 0:
                r = (5 + 10 * random.random() * random.random()) * self.scale
                eng.add_ball(w * 0.06 + random.uniform(-10, 10), h * 0.12 + random.uniform(-0.07, 0.07) * h, random.uniform(380, 620) * min(1.0, w / 1000),
                             random.uniform(-90, 90), r, hue)
                self.pour_owed -= 1
                self.pour_left -= 1
            self.styled = -1
        elif self.scene == 'shake':
            flipped = -1 if int(t / 2.0) % 2 else 1
            eng.set_gravity(float(self.gravity * flipped))
        elif self.scene == 'swarm':
            eng.pull(w / 2 + 0.34 * w * math.cos(0.83 * t), h / 2 + 0.32 * h * math.sin(1.31 * t), 1500.0, dt)

    def mouse_forces(self, dt):
        for what, value in self.todo:
            if what == 'blast':
                self.eng.burst(float(value[0]), float(value[1]), 1500.0)
                self.rings.append([value[0], value[1], time.perf_counter()])
            elif what == 'balls':
                at = COUNTS.index(self.count) + value
                if 0 <= at < len(COUNTS):
                    self.set_count(COUNTS[at])
                    self.show_panel()
            elif what == 'fill':
                self.set_fill(self.fill + 5 * value)
            elif what == 'pause':
                self.toggle('pause')
        self.todo = []
        if self.held and self.down and time.perf_counter() - self.down[0] > 0.18:
            self.eng.pull(float(self.mouse[0]), float(self.mouse[1]), 2600.0, dt)

    def set_fill(self, percent):
        self.fill = min(70, max(10, int(percent)))
        self.fit_balls()
        sg.user_settings_set_entry(K_SET_FILL, self.fill)
        self.show_panel()

    # ---------------------------------------------------------------- drawing ----------------------------------------------------------------
    def sprite(self, r, color):
        key = (r, color, self.desktop)
        if key not in self.sprites:
            im = make_sprite(r, rgb_of(PALETTE[color % len(PALETTE)]) if isinstance(color, int) else heat_color(int(color[1:])))
            if self.desktop:                                               # no faint outer edge there: mixed with the see-through color it would
                im.putalpha(im.getchannel('A').point(lambda a: 0 if a < 110 else a))       # be a dark halo two pixels wide
            self.sprites[key] = im
        return self.sprites[key]

    def restyle(self):
        """ Each ball's picture, from its size and color - after balls came or went, changed size, or the coloring changed """
        eng = self.eng
        n = eng.ball_count()
        radii, hues = eng.rs, eng.hues
        sizes = [max(1, int(r + 0.5)) for r in radii]
        self.ball_off = [r + 1 for r in sizes]
        self.max_off = max(self.ball_off, default=0)
        if self.heat:
            rows = {r: [self.sprite(r, f'h{level}') for level in range(HEAT_LEVELS)] for r in set(sizes)}
            self.ball_rows = [rows[r] for r in sizes]
        else:
            self.ball_sprite = [self.sprite(r, hue) for r, hue in zip(sizes, hues)]
        self.styled = n

    def balls_now(self):
        """ Where every ball is, and the picture each one is drawn with this frame """
        eng = self.eng
        n = eng.ball_count()
        if self.styled != n:
            self.restyle()
        xs, ys = eng.xs, eng.ys
        if self.heat:
            top = HEAT_LEVELS - 1
            k = 1 / (eng.WORLD[5] * HEAT_SPEED)
            hypot = math.hypot
            sprites = [row[min(top, int(hypot(x - px, y - py) * k))] for row, x, y, px, py in zip(self.ball_rows, xs, ys, eng.pxs, eng.pys)]
        else:
            sprites = self.ball_sprite
        return xs, ys, sprites

    def draw(self):
        """ One frame: the last one faded (trails) or wiped, every ball pasted in, the picture handed to tk and painted now """
        if self.desktop:
            return self.draw_desktop()
        xs, ys, sprites = self.balls_now()
        if self.trails:
            self.frame = Image.blend(self.frame, self.back, 0.30)
        else:
            self.frame.paste(self.back)
        frame = self.frame
        paste = frame.paste
        for x, y, s, off in zip(xs, ys, sprites, self.ball_off):
            paste(s, (int(x) - off, int(y) - off), s)
        if self.rings or self.held:
            self.draw_marks(frame)
        self.photo.paste(frame)
        self.canvas.update_idletasks()

    def draw_desktop(self):
        """ One frame in Desktop.  tk is left out of it: a screen-sized picture is more than it can take 60 times a second (40 ms at 3840 x
            2160), and it has nothing for a see-through one.  The rectangle drawn in last frame is wiped to the see-through color, every ball
            is pasted in, and the one rectangle that holds everything old and new is copied to a Windows bitmap and from there straight onto
            the window - about 1.5 ms for each million pixels of it, so a pile on the floor costs little and balls all over the screen 12 ms """
        xs, ys, sprites = self.balls_now()
        frame, (w, h), was = self.frame, self.size, self.drawn
        if was:
            frame.paste(KEY_RGB, was)
        paste = frame.paste
        for x, y, s, off in zip(xs, ys, sprites, self.ball_off):
            paste(s, (int(x) - off, int(y) - off), s)
        edge = self.max_off + 1
        boxes = [(min(xs) - edge, min(ys) - edge, max(xs) + edge, max(ys) + edge)] if xs else []
        boxes += self.draw_marks(frame) if self.rings or self.held else []
        now = None
        if boxes:
            now = (max(0, int(min(b[0] for b in boxes))), max(0, int(min(b[1] for b in boxes))), min(w, int(max(b[2] for b in boxes)) + 1),
                   min(h, int(max(b[3] for b in boxes)) + 1))
            now = now if now[0] < now[2] and now[1] < now[3] else None
        both = [b for b in (was, now) if b]
        send = (min(b[0] for b in both), min(b[1] for b in both), max(b[2] for b in both), max(b[3] for b in both)) if both else None
        self.canvas.update_idletasks()                                     # tk's own repaint first, if one is waiting: it would paint over this frame
        if self.exposed:                                                   # ...and after one, the whole picture again
            send, self.exposed = (0, 0, w, h), False
        if send:
            if (send[2] - send[0]) * (send[3] - send[1]) > 0.8 * w * h:
                send = (0, 0, w, h)
                self.dib.paste(frame)
            else:
                self.dib.paste(frame.crop(send), send)
            dc = window_dc(self.canvas.winfo_id())
            try:                                                           # always the WHOLE bitmap, cut down to the rectangle by Windows: a part of
                if send != (0, 0, w, h):                                   # the bitmap drawn by itself takes it ten times as long for each pixel
                    clip_dc(dc, send)
                self.dib.draw(ImageWin.HDC(dc), (0, 0, w, h), (0, 0, w, h))
            finally:
                window_dc(self.canvas.winfo_id(), dc)
        self.drawn = now

    def draw_marks(self, frame):
        """ A blast's ring, growing and fading; a small ring at the pointer while it pulls.  Returns the boxes it drew in """
        d = ImageDraw.Draw(frame)
        now, boxes = time.perf_counter(), []
        self.rings = [ring for ring in self.rings if now - ring[2] < 0.45]
        for x, y, when in self.rings:
            f = (now - when) / 0.45
            r = 20 + 280 * f ** 0.6
            shade = 255 if self.desktop else round(255 * (1 - f) ** 1.5)   # over the desktop it thins out instead of going dark
            if shade > 8:
                d.ellipse((x - r, y - r, x + r, y + r), outline=(shade, shade, min(255, shade + 40)), width=max(1, round(3 * (1 - f) * self.ui)))
                boxes.append((x - r - 2, y - r - 2, x + r + 2, y + r + 2))
        if self.held and self.down and now - self.down[0] > 0.18:
            x, y = self.mouse
            r = 9 + 3 * math.sin(now * 9)
            d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255), width=max(1, round(1.5 * self.ui)))
            boxes.append((x - r - 2, y - r - 2, x + r + 2, y + r + 2))
        return boxes

    def show_numbers(self):
        """ The line of numbers in the box and the little chart of the last frames - a few times a second """
        c, n, z = self.canvas, self.eng.ball_count(), self.ui
        text = f'{n:,} balls     {self.fps:.0f} frames a second     physics {self.phys_ms:.1f} ms     drawing {self.draw_ms:.1f} ms'
        if self.paused:
            text += '     paused'
        if self.bench is not None:                                         # while it measures, the big words say what - these numbers would be of no use
            text = ''
        if self.desktop:                                                   # no box to write in: the numbers go into the floating panel
            return self.window[K_RESULT].update(f'On the desktop:  {n:,} balls,  {self.fps:.0f} frames a second\nphysics {self.phys_ms:.1f} ms,  '
                                                f'drawing {self.draw_ms:.1f} ms' + (',  paused' if self.paused else ''))
        c.itemconfigure(self.hud, text=text)
        c.itemconfigure(self.hud_shadow, text=text)
        box = c.bbox(self.hud)
        x0, y0, high, step = 12, (box[3] if box else round(28 * z)) + round(5 * z), round(30 * z), max(1.0, 1.5 * z)    # the chart, under the numbers: 30 px
        #                                                                    tall = 33 ms a frame; the dashed line = 16.7 ms, a 60th of a second
        points = []
        for k, ms in enumerate(self.work):
            points += [x0 + k * step, y0 + high - min(high, ms / (2 * BUDGET_MS) * high)]
        if self.bench is not None or len(points) < 4:
            c.coords(self.spark, 0, 0, 0, 0)
            c.coords(self.spark_base, 0, 0, 0, 0)
        else:
            c.coords(self.spark, *points)
            c.coords(self.spark_base, x0, y0 + high / 2, x0 + 120 * step, y0 + high / 2)
        words = self.bench_words if self.bench else ('PAUSED' if self.paused and time.perf_counter() > self.said_until else
                                                     self.said if time.perf_counter() < self.said_until else '')
        if c.itemcget(self.big, 'text') != words:
            c.itemconfigure(self.big, text=words)
            c.itemconfigure(self.big_shadow, text=words)

    # ---------------------------------------------------------------- one frame ----------------------------------------------------------------
    def tick(self):
        now = time.perf_counter()
        elapsed, self.last = now - self.last, now
        target = 1 / self.rate if self.rate else elapsed
        dt = target if abs(elapsed - target) < 0.3 * target else min(1 / 30, max(1 / 240, elapsed))       # keeping up: even steps; behind: real time
        self.due = now + target if self.rate else now
        if self.bench is not None:
            self.bench_tick()
        else:
            if self.seen_size != self.size:
                self.resize_box(*self.seen_size)
            self.mouse_forces(dt)
            t0 = time.perf_counter()
            if not self.paused:
                self.scene_forces(dt)
                self.contacts = self.eng.step(dt, self.steps)
            t1 = time.perf_counter()
            self.draw()
            t2 = time.perf_counter()
            self.phys_ms += ((t1 - t0) * 1000 - self.phys_ms) * 0.1
            self.draw_ms += ((t2 - t1) * 1000 - self.draw_ms) * 0.1
            self.work.append((t2 - t0) * 1000)
        self.frames += 1
        now = time.perf_counter()
        if now - self.fps_since >= 0.25:
            self.fps += (self.frames / (now - self.fps_since) - self.fps) * (0.5 if self.fps else 1.0)
            self.frames, self.fps_since = 0, now
            self.show_numbers()
        if time.time() - self.slow_tick >= 2:
            self.slow_tick = time.time()
            self.every_two_seconds()

    def every_two_seconds(self):
        """ What needs no hurry: a newer version of the program """
        if update_tick(self.window, False, self.bench is not None or self.held, (C_PANEL, C_TEXT, C_ACCENT)):
            self.remake_menu()

    # ---------------------------------------------------------------- the exercise ----------------------------------------------------------------
    def start_bench(self):
        if self.bench is not None:
            return
        self.set_desktop(False)                                            # it measures in the window: the same box on every computer
        self.keep = (self.trails, self.heat, self.gravity, self.bounce, self.paused)
        self.trails, self.heat, self.paused = True, False, False
        self.bench = self.exercise()
        self.bench_words = 'Exercising this computer'
        self.show_panel()

    def end_bench(self, finished):
        self.bench = None
        self.trails, self.heat, self.gravity, self.bounce, self.paused = self.keep
        self.resize_box(*self.seen_size)
        self.start_scene(keep_panel=True)
        self.work.clear()
        self.show_panel()
        if finished:
            sg.user_settings_set_entry(K_SET_RESULTS, self.result)
            self.show_panel()
            self.results_window()
        else:
            self.say('The exercise was stopped')
        self.last = time.perf_counter()

    def bench_tick(self):
        try:
            self.bench_words = next(self.bench)
        except StopIteration:
            self.end_bench(True)

    def timed_frames(self, n, words):
        """ (generator) The milliseconds a whole frame takes with n balls: 8 frames to get going, then 24 measured """
        eng = self.eng
        self.gravity, self.bounce = 0, 100
        eng.remove_balls(eng.ball_count())
        eng.set_seed(2026)
        self.apply_world(eng)
        self.scale = max(0.12, min(3.0, math.sqrt(0.30 * self.size[0] * self.size[1] / (n * math.pi * MEAN_R2))))
        eng.scatter(n, 5 * self.scale, 15 * self.scale, 420.0, len(PALETTE))
        self.styled = -1
        took = 0.0
        for k in range(32):
            t = time.perf_counter()
            eng.step(1 / 60, 4)
            self.draw()
            if k >= 8:
                took += time.perf_counter() - t
            if k % 4 == 3:
                yield words
        return took / 24 * 1000

    def exercise(self):
        """ (generator, one small piece of work a call; it yields the words to show)  Measures the physics alone, the drawing alone, the most
            balls at 60 frames a second, and the timer; leaves the report in self.result """
        eng, speed = self.eng, {}
        for n, frames in BENCH_PHYSICS:                                    # 1: the physics alone
            eng.set_gravity(900.0)
            eng.set_bounce(0.85)
            eng.set_give(0.5)
            eng.reset(n, 1600.0, 900.0, 2026)
            took, done = 0.0, 0
            while done < frames:
                t = time.perf_counter()
                for _ in range(min(6, frames - done)):
                    eng.step(1 / 60, 4)
                took += time.perf_counter() - t
                done = min(frames, done + 6)
                yield f'Exercising this computer\nthe physics alone: {n:,} balls   {100 * done // frames}%'
            speed[n] = frames / took
        self.resize_box(min(SCENE_SIZE[0], self.seen_size[0]), min(SCENE_SIZE[1], self.seen_size[1]))
        draw = {}
        for n in BENCH_DRAW:                                               # 2: the drawing alone
            yield from self.timed_frames(n, f'Exercising this computer\nthe drawing alone: {n:,} balls')
            took = 0.0
            for k in range(30):
                t = time.perf_counter()
                self.draw()
                took += time.perf_counter() - t
                if k % 5 == 4:
                    yield f'Exercising this computer\nthe drawing alone: {n:,} balls   {100 * (k + 1) // 30}%'
            draw[n] = took / 30 * 1000
        words = 'Exercising this computer\nthe most balls at 60 frames a second'      # 3: everything together - the most balls a frame's time has room for
        good, bad, n = 0, None, 300
        while bad is None and n <= 40000:
            ms = yield from self.timed_frames(n, f'{words}   {n:,}')
            good, bad, n = (n, None, int(n * 1.5)) if ms <= BUDGET_MS else (good, n, n)
        for _ in range(4 if bad else 0):
            n = (good + bad) // 2
            ms = yield from self.timed_frames(n, f'{words}   {n:,}')
            good, bad = (n, bad) if ms <= BUDGET_MS else (good, n)
        eng.remove_balls(eng.ball_count())
        yield 'Exercising this computer\nthe timer'
        t = time.perf_counter()
        for _ in range(20):
            time.sleep(0.001)
        sleep_ms = (time.perf_counter() - t) / 20 * 1000
        self.result = self.report(speed, draw, (good, bad is None), sleep_ms)

    def report(self, speed, draw, most, sleep_ms):
        return '\n'.join([
            f'{APP_NAME} {VERSION} - exercise results     {datetime.datetime.now():%d %b %Y %H:%M}', *environment(self.window.TKroot), '',
            'The physics alone  (frames a second, 4 small steps in each - higher is better)',
            '  ' + '        '.join(f'{n:,} balls  {speed[n]:,.0f}' for n, _ in BENCH_PHYSICS), '',
            f'The drawing alone  (milliseconds a frame in a {self.size[0]} x {self.size[1]} box - lower is better)',
            '  ' + '        '.join(f'{n:,} balls  {draw[n]:.1f} ms' for n in BENCH_DRAW), '',
            'Everything together  (physics, 4 small steps + drawing; balls taking up 30% of the box, no gravity)',
            f'  Most balls at 60 frames a second:   {most[0]:,}{" or more" if most[1] else ""}',
            f'  Timer: a 1 ms sleep takes {sleep_ms:.1f} ms'])

    def results_window(self):
        if not self.result:
            return sg.popup('Nothing measured yet.\n\nExercise this computer (B) takes about 20 seconds.', title=APP_NAME, keep_on_top=True, icon=ICON, font=F_UI,
                            background_color=C_PANEL)
        layout = [[sg.Multiline(self.result, size=(118, 19), font=F_MONO, disabled=True, background_color=C_BG, text_color=C_TEXT, border_width=0, expand_x=True,
                                expand_y=True, no_scrollbar=True)],
                  [sg.Text('Copy it, run this on another computer or system, and compare.', key='-SAID-', font=F_SMALL, text_color=C_DIM), sg.Push(),
                   sg.Button('Copy', border_width=0, size=(9, 1)), sg.Button('Close', border_width=0, size=(9, 1), button_color=(C_TEXT, C_FIELD))]]
        win = sg.Window(f'{APP_NAME}  -  exercise results', layout, icon=ICON, modal=True, finalize=True, font=F_UI, resizable=True, keep_on_top=True,
                        background_color=C_PANEL)
        dark_title_bar(win)
        fit_min_size(win)
        win.bind('<Escape>', 'Close')
        while True:
            event, _ = win.read()
            if event in ('Close', sg.WINDOW_CLOSED):
                break
            if event == 'Copy':
                sg.clipboard_set(self.result)
                win['-SAID-'].update('Copied.', text_color=C_GOOD)
        win.close()
        self.last = time.perf_counter()

    def version_window(self):
        """ The program, and the one place it writes with its size """
        settings = sg.user_settings_filename()
        lines = [f'{APP_NAME}  version {VERSION}', os.path.abspath(__file__), '',
                 f'The physics: {len(ENGINE_SOURCE.splitlines())} lines of Python kept in this file', '',
                 'What this program writes:',
                 f'   settings:    {settings}' + (f'   ({fmt_size(os.path.getsize(settings))})' if os.path.isfile(settings) else '') +
                 ('   - temporary, removed on close' if DEMO else ''),
                 '   nothing else', '',
                 f'New versions: {dict(UPDATE_CHOICES)[update_mode()]}', '', sg.get_versions()]
        layout = [[sg.Multiline('\n'.join(lines), size=(112, 16), font=F_MONO, disabled=True, background_color=C_BG, text_color=C_TEXT, border_width=0, expand_x=True,
                                expand_y=True)],
                  [sg.Button('Open the settings folder', key='-OPEN-', border_width=0), sg.Push(),
                   sg.Button('Close', border_width=0, size=(9, 1), button_color=(C_TEXT, C_FIELD))]]
        win = sg.Window(f'{APP_NAME}  -  version {VERSION}', layout, icon=ICON, modal=True, finalize=True, font=F_UI, resizable=True, keep_on_top=True,
                        background_color=C_PANEL)
        dark_title_bar(win)
        fit_min_size(win)
        win.bind('<Escape>', 'Close')
        while True:
            event, _ = win.read()
            if event in ('Close', sg.WINDOW_CLOSED):
                break
            if event == '-OPEN-':
                open_folder(os.path.dirname(settings))
        win.close()
        self.last = time.perf_counter()

    # ---------------------------------------------------------------- events ----------------------------------------------------------------
    def toggle(self, what):
        if self.desktop and what in ('trails', 'full'):                    # neither has a meaning over the desktop
            return
        if what == 'trails':
            self.trails = not self.trails
            sg.user_settings_set_entry(K_SET_TRAILS, self.trails)
        elif what == 'heat':
            self.heat = not self.heat
            self.styled = -1
            sg.user_settings_set_entry(K_SET_HEAT, self.heat)
        elif what == 'pause':
            self.paused = not self.paused
        elif what == 'full':
            self.full = not self.full
            self.window[K_PANEL].update(visible=not self.full)
            self.window.TKroot.attributes('-fullscreen', self.full)
        self.show_panel()
        self.remake_menu()

    def key(self, e):
        """ A key on the window.  Nothing with Alt held, and with Ctrl only the three size keys """
        if e is None:
            return True
        name, ctrl, alt = e.keysym, bool(e.state & 0x4), bool(e.state & (0x20000 if WIN else 0x8))
        if alt:
            return True
        if ctrl:
            if name in ('equal', 'plus', 'minus', '0'):
                self.set_fill(30 if name == '0' else self.fill + (-5 if name == 'minus' else 5))
            return True
        low = name.lower()
        if name == 'Escape':
            if self.bench is not None:
                self.end_bench(False)
            elif self.desktop:
                self.set_desktop(False)
            elif self.full:
                self.toggle('full')
            else:
                self.save_place()
                return False
        elif self.bench is not None:
            pass
        elif low == 'd':
            self.set_desktop(not self.desktop)
        elif name == 'space':
            self.toggle('pause')
        elif low in ('1', '2', '3', '4', '5'):
            self.start_scene(SCENES[int(low) - 1][0])
            self.show_panel()
            self.remake_menu()
        elif low == 'r':
            self.start_scene(keep_panel=True)
        elif name in ('plus', 'equal', 'KP_Add', 'minus', 'KP_Subtract'):
            self.todo.append(('balls', -1 if name in ('minus', 'KP_Subtract') else 1))
        elif low == 't':
            self.toggle('trails')
        elif low == 'c':
            self.toggle('heat')
        elif low == 'x':
            self.todo.append(('blast', self.mouse))
        elif low == 'f':
            self.gravity = -self.gravity
            self.eng.set_gravity(float(self.gravity))
            self.show_panel()
        elif low == 'b':
            self.start_bench()
        return True

    def handle(self, event, values):
        """ One event.  False ends the program """
        if update_event(event):                                             # Restart, or a New versions choice
            if Update.restart:
                self.save_place()
                return False
            self.remake_menu()
            return True
        if isinstance(event, str) and '::' in event:                        # a menu item: its key is after the ::
            event = event.split('::')[-1]
            if event.startswith('-M SCENE '):
                event = KT_SCENE(event[9:-1])
        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, 'Exit', K_CLOSE):
            self.save_place()
            return False
        if event == sg.WINDOW_CLOSED:
            return False
        if event == K_KEY:
            return self.key((self.source or self.window).user_bind_event)
        if event == K_FULL:
            self.toggle('full')
        elif event == 'Edit Me':
            sg.execute_editor(os.path.abspath(__file__))
        elif event == 'Version':
            self.version_window()
        elif event == K_M_NEWS:
            news = update_news(update_tag()) or update_news()
            sg.popup_scrolled('\n\n'.join(news) or 'Nothing new.', title=f'{APP_NAME}  -  what\'s new', size=(90, 12), font=F_UI, icon=ICON, keep_on_top=True,
                              background_color=C_PANEL)
            update_tag_seen()
            self.window.set_title(self.title())
            self.last = time.perf_counter()
        elif event == K_M_RESULTS:
            self.results_window()
        elif self.bench is not None:
            pass                                                            # while it measures, the panel is left alone
        elif event == K_BALLS:
            self.set_count(COUNTS[int(values[K_BALLS])])
            self.show_panel()
        elif event == K_FILL:
            self.set_fill(values[K_FILL])
        elif event == K_GRAVITY:
            self.gravity = int(values[K_GRAVITY])
            self.eng.set_gravity(float(self.gravity))
            self.show_panel()
        elif event == K_BOUNCE:
            self.bounce = int(values[K_BOUNCE])
            self.eng.set_bounce(self.bounce / 100)
            self.show_panel()
        elif event == K_STEPS:
            self.steps = int(values[K_STEPS])
            sg.user_settings_set_entry(K_SET_STEPS, self.steps)
            self.show_panel()
        elif isinstance(event, tuple) and event[0] == '-SCENE-':
            self.start_scene(event[1])
            self.show_panel()
            self.remake_menu()
        elif event == K_AGAIN:
            self.start_scene(keep_panel=True)
        elif event in (K_TRAILS, K_HEAT, K_PAUSE):
            self.toggle({K_TRAILS: 'trails', K_HEAT: 'heat', K_PAUSE: 'pause'}[event])
        elif event == K_BENCH:
            self.start_bench()
        elif event == K_DESK:
            self.set_desktop(not self.desktop)
        elif isinstance(event, str) and event.startswith('-M RATE '):
            self.rate = int(event[8:-1])
            sg.user_settings_set_entry(K_SET_RATE, self.rate)
            self.remake_menu()
        return True

    def pump(self, wait=0):
        """ Every event that is waiting, from whichever of the program's windows (in Desktop there are two).  False ends the program """
        if getattr(sg.Window, '_timeout_0_counter', 0) >= len(getattr(sg.Window, '_active_windows', ())):
            sg.Window._timeout_0_counter = 0
        window, event, values = sg.read_all_windows(timeout=wait)
        while event != sg.TIMEOUT_EVENT:
            self.source = window
            if not self.handle(event, values):
                return False
            if getattr(sg.Window, '_timeout_0_counter', 0) >= len(getattr(sg.Window, '_active_windows', ())):
                sg.Window._timeout_0_counter = 0                           # the event closed a window: PySimpleGUI's turn-taking would point past the end
            window, event, values = sg.read_all_windows(timeout=0)
        return True

    def close(self):
        for window in {self.window, self.stage}:
            window.close()

    def run(self):
        self.make_window()
        self.start_scene()
        self.show_panel()
        self.last = self.due = time.perf_counter()
        while True:
            if not self.pump(max(0, int((self.due - time.perf_counter()) * 1000)) if self.rate and self.bench is None else 0):
                return self.close()
            while self.rate and self.bench is None and time.perf_counter() < self.due:      # the last fraction of a millisecond
                pass
            self.tick()
            if Update.restart:
                self.save_place()
                return self.close()


DEMO_DIR = os.path.join(tempfile.gettempdir(), 'psgbounce_demo')


def drop_old_settings():
    """ What versions before 1.0.5 kept for a second engine, and results measured with it: out of the settings """
    for key in OLD_SETTINGS:
        if sg.user_settings_get_entry(key, None) is not None:
            sg.user_settings_delete_entry(key)
    if 'Python engine' in str(sg.user_settings_get_entry(K_SET_RESULTS, '')):
        sg.user_settings_delete_entry(K_SET_RESULTS)

ENGINE_SOURCE = r'''"""
psgbounce_engine.py  -  the physics of PSG Bounce: balls in a box, gravity, and balls bouncing off each other.

    Plain Python and nothing else - no imports beyond math and time - so it runs anywhere Python runs.  PSG Bounce carries this text inside
    itself and runs it as a module of its own.

    HOW IT IS KEPT
        The world is plain lists, one number per ball in each, and every function takes and returns plain numbers.  The few single values
        of the world (its size, gravity ...) sit in two small lists too, WORLD and STATE.
    HOW IT MOVES
        A ball is where it is now and where it was one small step ago; its speed is the difference.  A step moves every ball on by that
        difference plus gravity, then puts right what went wrong: a ball outside the box is put back at the wall, two balls that overlap are
        moved apart (the lighter one gives way more).  Because speed is only "now minus before", putting a ball back also changes its speed -
        that is what lets a pile come to rest and carry its own weight.  A hard hit bounces: the "before" of both balls is moved so that they
        part again with the share of their speed that the bounce setting allows.
    HOW IT STAYS FAST
        A grid: each ball is filed under the square it is in, and is only tested against the balls in its own and the neighbouring squares.
        Every function that loops first takes the lists it needs into names of its own (x = xs ...): Python reads a name of the function
        quicker than one of the module.

    Units: pixels and seconds.  y grows downward, like the screen.

CHANGE LOG (newest first, 1 line per change):
2026-11-19  v1.0.0  Claude: first version
"""
import math
import time

WORLD: list[float] = [1280.0, 720.0, 900.0, 0.85, 1.0, 1.0 / 240.0, 0.5]
#   0 the box's width      1 its height      2 gravity (pixels / s / s, downward)      3 the share of its speed a ball keeps in a bounce
#   4 the largest radius (the grid's squares are twice that)      5 the length of one small step, seconds
#   6 how much of being pushed apart turns into speed when two balls were merely pressed together (1 = all of it: springy, 0 = none: dead)
STATE: list[int] = [12345, 0]   # the random numbers' state; the contacts settled in the last step

xs: list[float] = []            # per ball: where it is now,
ys: list[float] = []
pxs: list[float] = []           # where it was one small step ago,
pys: list[float] = []
rs: list[float] = []            # its radius,
ms: list[float] = []            # its mass (radius squared),
hues: list[int] = []            # and a number the display turns into its color
cell_of: list[int] = []         # per ball: the grid square it is in
order: list[int] = []           # the balls sorted by square
starts: list[int] = []          # per square: where its balls begin in order (one more entry than squares)
fills: list[int] = []           # per square: the next free place while order is filled


def version() -> int:
    """ 100 * major + minor """
    return 100


def next_random() -> float:
    """ The next random number, 0 to just under 1 - the same sequence on every computer """
    STATE[0] = (STATE[0] * 1103515245 + 12345) % 2147483648
    return STATE[0] / 2147483648.0


def ball_count() -> int:
    return len(xs)


def ball_x(i: int) -> float:
    return xs[i]


def ball_y(i: int) -> float:
    return ys[i]


def ball_r(i: int) -> float:
    return rs[i]


def ball_hue(i: int) -> int:
    return hues[i]


def ball_vx(i: int) -> float:
    """ Its speed to the right, pixels a second """
    return (xs[i] - pxs[i]) / WORLD[5]


def ball_vy(i: int) -> float:
    """ Its speed downward, pixels a second """
    return (ys[i] - pys[i]) / WORLD[5]


def ball_speed(i: int) -> float:
    """ Pixels a second """
    dx: float = xs[i] - pxs[i]
    dy: float = ys[i] - pys[i]
    return math.sqrt(dx * dx + dy * dy) / WORLD[5]


def set_seed(seed: int) -> None:
    """ The random numbers start again from here: the same seed gives the same world """
    STATE[0] = seed


def last_contacts() -> int:
    return STATE[1]


def set_gravity(g: float) -> None:
    WORLD[2] = g


def set_bounce(b: float) -> None:
    WORLD[3] = b


def set_give(g: float) -> None:
    WORLD[6] = g


def resize(w: float, h: float) -> None:
    """ The box gets a new size; balls now outside are brought back in by the next step """
    WORLD[0] = w
    WORLD[1] = h


def add_ball(x: float, y: float, vx: float, vy: float, r: float, hue: int) -> int:
    """ One more ball at x, y moving at vx, vy pixels a second; returns its number """
    xs.append(x)
    ys.append(y)
    pxs.append(x - vx * WORLD[5])
    pys.append(y - vy * WORLD[5])
    rs.append(r)
    ms.append(r * r)
    hues.append(hue)
    cell_of.append(0)
    order.append(0)
    if r > WORLD[4]:
        WORLD[4] = r
    return len(xs) - 1


def remove_balls(n: int) -> None:
    """ The n newest balls go """
    k: int = 0
    while k < n and len(xs) > 0:
        xs.pop()
        ys.pop()
        pxs.pop()
        pys.pop()
        rs.pop()
        ms.pop()
        hues.pop()
        cell_of.pop()
        order.pop()
        k = k + 1
    if len(xs) == 0:
        WORLD[4] = 1.0


def grow(factor: float) -> None:
    """ Every ball gets factor times as big (below 1: smaller); the next steps move apart the ones that now overlap """
    radius: list[float] = rs
    mass: list[float] = ms
    count: int = len(radius)
    i: int = 0
    while i < count:
        radius[i] = radius[i] * factor
        mass[i] = radius[i] * radius[i]
        i = i + 1
    WORLD[4] = WORLD[4] * factor


def scatter(n: int, r_min: float, r_max: float, speed: float, colors: int) -> None:
    """ n more balls at random places in the box, with random sizes (more small ones than big), directions and colors """
    width: float = WORLD[0]
    height: float = WORLD[1]
    k: int = 0
    while k < n:
        r: float = r_min + (r_max - r_min) * next_random() * next_random()
        x: float = r + (width - 2.0 * r) * next_random()
        y: float = r + (height - 2.0 * r) * next_random()
        dx: float = 2.0 * next_random() - 1.0           # a direction without sine and cosine: those can differ in the last digit
        dy: float = 2.0 * next_random() - 1.0           # from one computer's maths library to the next, plus, times and root never do
        d: float = math.sqrt(dx * dx + dy * dy)
        if d < 0.001:
            dx = 1.0
            dy = 0.0
            d = 1.0
        v: float = speed * (0.3 + 0.7 * next_random())
        add_ball(x, y, v * dx / d, v * dy / d, r, int(next_random() * colors))
        k = k + 1


def reset(n: int, w: float, h: float, new_seed: int) -> None:
    """ A fresh world: n balls in a w by h box, from a seed """
    STATE[0] = new_seed
    remove_balls(len(xs))
    resize(w, h)
    WORLD[5] = 1.0 / 240.0          # the small step every fresh world starts from: only then does the same seed give the same numbers to the last digit
    scatter(n, 5.0, 15.0, 420.0, 12)


def burst(x: float, y: float, power: float) -> None:
    """ A blast at a point: every ball near it is thrown away from it (power = pixels a second right at the point) """
    bx: list[float] = xs
    by: list[float] = ys
    px: list[float] = pxs
    py: list[float] = pys
    reach: float = 300.0
    step_len: float = WORLD[5]
    count: int = len(bx)
    i: int = 0
    while i < count:
        dx: float = bx[i] - x
        dy: float = by[i] - y
        d2: float = dx * dx + dy * dy
        if d2 < reach * reach:
            d: float = math.sqrt(d2) + 0.001
            push: float = power * (1.0 - d / reach) * step_len
            px[i] = px[i] - dx / d * push
            py[i] = py[i] - dy / d * push
        i = i + 1


def pull(x: float, y: float, power: float, dt: float) -> None:
    """ Every ball is drawn toward a point for dt seconds (hold the mouse button) """
    bx: list[float] = xs
    by: list[float] = ys
    px: list[float] = pxs
    py: list[float] = pys
    step_len: float = WORLD[5]
    count: int = len(bx)
    i: int = 0
    while i < count:
        dx: float = x - bx[i]
        dy: float = y - by[i]
        d: float = math.sqrt(dx * dx + dy * dy) + 30.0
        px[i] = px[i] - dx / d * power * dt * step_len
        py[i] = py[i] - dy / d * power * dt * step_len
        i = i + 1


def energy() -> float:
    """ The movement energy of all balls together """
    bx: list[float] = xs
    by: list[float] = ys
    px: list[float] = pxs
    py: list[float] = pys
    mass: list[float] = ms
    total: float = 0.0
    step_len: float = WORLD[5]
    count: int = len(bx)
    i: int = 0
    while i < count:
        vx: float = (bx[i] - px[i]) / step_len
        vy: float = (by[i] - py[i]) / step_len
        total = total + 0.5 * mass[i] * (vx * vx + vy * vy)
        i = i + 1
    return total


def checksum() -> float:
    """ Every position added up - a single number that shows two engines did exactly the same work """
    bx: list[float] = xs
    by: list[float] = ys
    total: float = 0.0
    count: int = len(bx)
    i: int = 0
    while i < count:
        total = total + bx[i] + 2.0 * by[i]
        i = i + 1
    return total


def move() -> None:
    """ Every ball goes on as it was going, plus gravity, for one small step """
    bx: list[float] = xs
    by: list[float] = ys
    px: list[float] = pxs
    py: list[float] = pys
    fall: float = WORLD[2] * WORLD[5] * WORLD[5]
    count: int = len(bx)
    i: int = 0
    while i < count:
        x: float = bx[i]
        y: float = by[i]
        bx[i] = x + (x - px[i])
        by[i] = y + (y - py[i]) + fall
        px[i] = x
        py[i] = y
        i = i + 1


def walls() -> None:
    """ Every ball is kept inside the box; one that hits a wall hard bounces off it, a slow one just stays there """
    bx: list[float] = xs
    by: list[float] = ys
    px: list[float] = pxs
    py: list[float] = pys
    radius: list[float] = rs
    width: float = WORLD[0]
    height: float = WORLD[1]
    bounce: float = WORLD[3]
    rest: float = WORLD[2] * WORLD[5] * WORLD[5] * 2.5 + 40.0 * WORLD[5]      # slower than this (per small step) is resting, not bouncing
    count: int = len(bx)
    i: int = 0
    while i < count:
        r: float = radius[i]
        x: float = bx[i]
        y: float = by[i]
        v: float = x - px[i]
        if x < r:
            bx[i] = r
            if v < -rest:
                px[i] = r + v * bounce
            elif v < 0.0:
                px[i] = r
        elif x > width - r:
            bx[i] = width - r
            if v > rest:
                px[i] = width - r + v * bounce
            elif v > 0.0:
                px[i] = width - r
        v = y - py[i]
        if y < r:
            by[i] = r
            if v < -rest:
                py[i] = r + v * bounce
            elif v < 0.0:
                py[i] = r
        elif y > height - r:
            by[i] = height - r
            if v > rest:
                py[i] = height - r + v * bounce
            elif v > 0.0:
                py[i] = height - r
        i = i + 1


def touch() -> int:
    """ Every pair of balls that overlap is settled: moved apart, and if they met hard they bounce.  The grid keeps it quick: a ball is only
        tested against the rest of its own square, the square to its right, and the three squares below - so each pair is looked at once.
        Returns the contacts found """
    bx: list[float] = xs
    by: list[float] = ys
    px: list[float] = pxs
    py: list[float] = pys
    radius: list[float] = rs
    mass: list[float] = ms
    cells: list[int] = cell_of
    sorted_balls: list[int] = order
    first: list[int] = starts
    free: list[int] = fills
    width: float = WORLD[0]
    height: float = WORLD[1]
    spring: float = WORLD[3]
    hard: float = -60.0 * WORLD[5]                      # closing faster than 60 pixels a second (per small step) is a hit, not a press
    give: float = WORLD[6]
    soft: float = 120.0 * WORLD[5]                      # the most speed (per small step) a press may turn into: 120 pixels a second
    size: float = WORLD[4] * 2.0
    if size < 8.0:
        size = 8.0
    cols: int = int(width / size) + 1
    rows: int = int(height / size) + 1
    squares: int = cols * rows
    count: int = len(bx)
    while len(first) < squares + 2:
        first.append(0)
        free.append(0)
    c: int = 0
    while c <= squares:
        first[c] = 0
        c = c + 1
    cx: int = 0
    cy: int = 0
    i: int = 0
    while i < count:                                    # which square each ball is in, and how many each square holds
        cx = int(bx[i] / size)
        cy = int(by[i] / size)
        if cx < 0:
            cx = 0
        elif cx >= cols:
            cx = cols - 1
        if cy < 0:
            cy = 0
        elif cy >= rows:
            cy = rows - 1
        c = cy * cols + cx
        cells[i] = c
        first[c + 1] = first[c + 1] + 1
        i = i + 1
    c = 0
    while c < squares:                                  # running totals: where each square's balls begin
        first[c + 1] = first[c + 1] + first[c]
        free[c] = first[c]
        c = c + 1
    i = 0
    while i < count:                                    # the balls, sorted by square
        c = cells[i]
        sorted_balls[free[c]] = i
        free[c] = free[c] + 1
        i = i + 1
    found: int = 0
    a: int = 0
    b: int = 0
    j: int = 0
    last: int = 0
    lo: int = 0
    hi: int = 0
    part: int = 0
    xi: float = 0.0
    yi: float = 0.0
    ri: float = 0.0
    mi: float = 0.0
    mj: float = 0.0
    dx: float = 0.0
    dy: float = 0.0
    reach: float = 0.0
    d2: float = 0.0
    d: float = 0.0
    nx: float = 0.0
    ny: float = 0.0
    share_i: float = 0.0
    share_j: float = 0.0
    overlap: float = 0.0
    closing: float = 0.0
    after: float = 0.0
    extra: float = 0.0
    a = 0
    while a < count:
        i = sorted_balls[a]
        c = cells[i]
        cx = c % cols
        cy = c // cols
        xi = bx[i]
        yi = by[i]
        ri = radius[i]
        mi = mass[i]
        part = 0
        while part < 2:
            if part == 0:                               # the rest of its own square and the square to the right: they follow each other
                b = a + 1
                if cx + 1 < cols:
                    last = first[c + 2]
                else:
                    last = first[c + 1]
            else:                                       # the three squares below: they follow each other too
                if cy + 1 >= rows:
                    b = 0
                    last = 0
                else:
                    lo = cx - 1
                    if lo < 0:
                        lo = 0
                    hi = cx + 1
                    if hi >= cols:
                        hi = cols - 1
                    b = first[c + cols - cx + lo]
                    last = first[c + cols - cx + hi + 1]
            while b < last:
                j = sorted_balls[b]
                dx = bx[j] - xi
                dy = by[j] - yi
                reach = ri + radius[j]
                d2 = dx * dx + dy * dy
                if d2 < reach * reach:
                    d = math.sqrt(d2)
                    if d < 0.0001:                      # exactly on top of each other: any direction will do
                        dx = 1.0
                        dy = 0.0
                        d = 1.0
                    nx = dx / d
                    ny = dy / d
                    mj = mass[j]
                    share_i = mj / (mi + mj)            # the lighter ball gives way more
                    share_j = mi / (mi + mj)
                    overlap = reach - d
                    closing = ((bx[j] - px[j]) - (xi - px[i])) * nx + ((by[j] - py[j]) - (yi - py[i])) * ny    # below 0 = approaching
                    xi = xi - nx * overlap * share_i
                    yi = yi - ny * overlap * share_i
                    bx[j] = bx[j] + nx * overlap * share_j
                    by[j] = by[j] + ny * overlap * share_j
                    after = closing + overlap           # how fast they part now, just from having been moved apart
                    if closing < hard:
                        extra = -spring * closing - after             # a hit: they part with the bounce's share of the speed they met at
                    elif after > 0.0:                                 # a press: only part of the push becomes speed, or a pile would never
                        extra = give * after                          # rest - and never much, or two balls made on top of each other would
                        if extra > soft:                              # shoot apart
                            extra = soft
                        extra = extra - after
                    else:
                        extra = 0.0
                    if extra != 0.0:
                        px[i] = px[i] + nx * extra * share_i
                        py[i] = py[i] + ny * extra * share_i
                        px[j] = px[j] - nx * extra * share_j
                        py[j] = py[j] - ny * extra * share_j
                    found = found + 1
                b = b + 1
            part = part + 1
        bx[i] = xi
        by[i] = yi
        a = a + 1
    return found


def set_step(seconds: float) -> None:
    """ The length of one small step changes: every ball's "before" is moved so that it keeps its speed """
    old: float = WORLD[5]
    if seconds == old or seconds <= 0.0:
        return
    bx: list[float] = xs
    by: list[float] = ys
    px: list[float] = pxs
    py: list[float] = pys
    ratio: float = seconds / old
    count: int = len(bx)
    i: int = 0
    while i < count:
        px[i] = bx[i] - (bx[i] - px[i]) * ratio
        py[i] = by[i] - (by[i] - py[i]) * ratio
        i = i + 1
    WORLD[5] = seconds


def step(dt: float, parts: int) -> int:
    """ The world moves on by dt seconds, in parts small steps (more parts = harder, steadier piles).  Returns the contacts settled """
    set_step(dt / parts)
    found: int = 0
    k: int = 0
    while k < parts:
        move()
        walls()
        found = found + touch()
        walls()
        k = k + 1
    STATE[1] = found
    return found


def bench(n: int, frames: int) -> float:
    """ How fast this engine is here: a world of n balls stepped frames times (each a 60th of a second in 4 small steps).
        Returns the frames a second it managed - higher is better """
    reset(n, 1600.0, 900.0, 2026)
    start: float = time.perf_counter()
    k: int = 0
    while k < frames:
        step(1.0 / 60.0, 4)
        k = k + 1
    took: float = time.perf_counter() - start
    if took <= 0.0:
        return 0.0
    return frames / took
'''


def main():
    Update.default = 'menu'                             # a program you open and close: a newer version is only said in the menu
    if Image is None:
        return sg.popup(f'{APP_NAME} draws with Pillow, and this Python does not have all of it  ({NO_PILLOW}).\n\nInstall it with:   pip install pillow\n'
                        'On Debian / Ubuntu with the system\'s Python:   sudo apt install python3-pil python3-pil.imagetk', title=APP_NAME)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # sharp text on scaled displays
        ctypes.windll.winmm.timeBeginPeriod(1)          # waits as short as a millisecond (Windows ticks every 15.6 ms otherwise)
    except Exception:
        pass
    sg.set_options(dpi_awareness=True, icon=ICON, tooltip_font=F_SMALL)
    sg.theme_add_new(APP_NAME, {'BACKGROUND': C_PANEL, 'TEXT': C_TEXT, 'INPUT': C_FIELD, 'TEXT_INPUT': C_TEXT, 'SCROLL': C_FIELD, 'BUTTON': ('#ffffff', C_ACCENT),
                                'PROGRESS': (C_ACCENT, C_FIELD), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
    sg.theme(APP_NAME)
    if DEMO:                                            # its own, empty, temporary settings - the real file is never even read: PySimpleGUI
        shutil.rmtree(DEMO_DIR, ignore_errors=True)     # would carry every value of it over into the demo's
        sg.user_settings_filename(filename=SETTINGS_FILE, path=DEMO_DIR)
        sg.user_settings_set_entry('-RAN VERSION-', VERSION)               # made-up settings are no update: no UPDATED tag in a screenshot
    else:
        sg.user_settings_filename(filename=SETTINGS_FILE)
        update_check()                                  # the UPDATE block's first look, before this run saves a setting: it tells a first run
        #                                                 from an update by whether the settings hold anything yet
        drop_old_settings()
    try:
        App().run()
    finally:
        try:
            ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:
            pass
        if DEMO:
            shutil.rmtree(DEMO_DIR, ignore_errors=True)
    if Update.restart:
        restart_self()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())
