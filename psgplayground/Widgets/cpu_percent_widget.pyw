"""
cpu_percent_widget.pyw / ram_percent_widget.pyw  -  a modern desktop widget showing CPU load (or RAM in use) as a percentage.

    One rounded card (Toybox palette, or 31 other dark and light themes) with no title bar: a ring gauge whose color goes green -> amber -> red with the load, the number big in the
    middle, a sparkline of the last 60 readings underneath and a detail line at the bottom (CPU: core count + the peak in the sparkline; RAM: GB in use / total).
    The corners of the card are see-through (and click-through), so it floats on the desktop like a real widget (Windows - Linux / Mac get square corners).
    The whole card is drawn with Pillow (antialiased) and shown in one Image element, so it looks the same at every Windows display scaling.

    Drag it anywhere on the card.  The faint x in the corner (red when hovered) closes it; so does Escape.
    Right-click:  Keep on top  |  Theme (16 dark + 16 light)  |  Brightness... (darker / lighter)  |  Accent (ring color: follows the load, a preset,
                  or Any... color dialog)  |  Size  |  Opacity  |  Refresh rate  |  Edit Me / Version / Exit    (all remembered; every change shows instantly)
    Brightness:  a panel under the card - drag the knob (or arrow keys / mouse wheel) and the card turns darker (down to -80%) or lighter (+50%) as you go.
                  Done or Enter keeps it, Escape puts it back.  The program does this to its own theme, so every theme has darker and lighter versions.
    The window position is remembered too (auto_save_location).

    The CPU and RAM widgets are the SAME file apart from the METRIC and ICON lines near the top - keep both copies in step when changing one.

    Requires:  pip install PySimpleGUI psutil pillow

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v1.8  Ring gauge: the round ends sat half a ring-width off the arc (a "dog bone" at low readings) - the arcs are centered on the ring now, the glow gets round ends too
2026-11-02  v1.7  Linux / Mac: square corners - only Windows can make them see-through, elsewhere they showed black; the Brightness panel too
2026-11-01  v1.6  Brightness... in the right-click menu: a slider makes any theme darker (down to -80%) or lighter (+50%), the card changing as you drag
2026-11-01  v1.5  32 themes - 16 dark (now colorful) and 16 light - as two columns of bigger color chips in the Theme menu; renamed themes carry over
2026-11-01  v1.4  16 themes, 8 dark + 8 light (was 4), a swatch beside each in the Theme menu; the menu takes the card's colors; load colors darker on light cards
2026-11-01  v1.3  Right-click menu rows compact (activeborderwidth=1, tk's normal padding) - Mike's pick after comparing with roomy rows (6)
2026-11-01  v1.2  Theme sub-menu (Toybox / Midnight / Slate / Paper card colors) and Accent sub-menu (follows load, 6 presets, Any... color dialog)
2026-11-01  v1.1  Right-click menu in the Toybox palette (dark, flat, roomy rows) instead of Windows gray - sub-menus too
2026-11-01  v1.0  First version - replaces Demo_Desktop_Widget_CPU_Square / RAM_Square
"""
import base64
import io
import math
import random
import sys
import tkinter as tk
from collections import deque
from tkinter import colorchooser

import PySimpleGUI as sg
import psutil
from PIL import Image, ImageDraw, ImageFont

VERSION = '1.8'
DEMO = '--demo' in sys.argv                                      # fake readings that wander up and down, for trying the widget out / screenshots
METRIC = 'CPU'                                                   # 'CPU' or 'RAM' - the only line (plus ICON) that differs between the two widget files
ICON = b'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'

# ---------- Keys ----------
K_IMAGE = '-IMAGE-'
K_HOVER = '-HOVER-'                   # mouse moved over / off the close x  (value: True / False)
K_CLOSE = '-CLOSE-'                   # close x clicked
K_TOP = '-TOP-'                       # right-click: keep on top toggle
K_SIZE = '-SIZE-'                     # settings-file entry, and the prefix of the size menu keys
KT_SIZE = lambda name: f'{K_SIZE}{name}'
K_OPACITY = '-OPACITY-'
KT_OPACITY = lambda pct: f'{K_OPACITY}{pct}'
K_REFRESH = '-REFRESH-'
KT_REFRESH = lambda ms: f'{K_REFRESH}{ms}'
K_THEME = '-THEME-'                   # settings-file entry, and the prefix of the theme menu keys
KT_THEME = lambda name: f'{K_THEME}{name}'
K_ACCENT = '-ACCENT-'                 # settings-file entry (None = follows the load, else '#rrggbb'), and the prefix of the accent menu keys
KT_ACCENT = lambda name: f'{K_ACCENT}{name}'
ACCENT_ANY = 'Any...'
K_EXIT = 'Exit'

# ---------- Look (Toybox palette: dark card, Segoe UI, one accent that follows the load) ----------
TRANSPARENT = '#010203'               # window color key: anything this color is see-through and click-through (the rounded corners)
SEE_THROUGH = sg.running_windows()    # only Windows can make those corners see-through - Linux / Mac get square corners instead of black ones
# --- WIDGET THEMES: the same block in every card widget (master copy in modern_widget_recipe.md) - change it in all of them at once ---
# card = background, border = outline, track = gauge track / lines, text = main text, dim = labels.   16 dark first, then 16 light: the Theme menu
# shows them as two columns of color chips.  ForestFloor and CrimsonVelvet come from Mike's dark themes; the other colored darks follow their lead.
THEMES = {'Toybox':        {'card': '#141821', 'border': '#2f3a4e', 'track': '#1e2430', 'text': '#e6eaf2', 'dim': '#8a93a3'},
          'Carbon':        {'card': '#121212', 'border': '#2e2e2e', 'track': '#1f1f1f', 'text': '#e0e0e0', 'dim': '#8c8c8c'},
          'Slate':         {'card': '#2a3140', 'border': '#48526a', 'track': '#363e50', 'text': '#eef1f6', 'dim': '#a3acbd'},
          'CrimsonVelvet': {'card': '#5e0d1f', 'border': '#8f1530', 'track': '#781429', 'text': '#f9d276', 'dim': '#d6a7a0'},
          'Ember':         {'card': '#451f11', 'border': '#773c27', 'track': '#5c2f1e', 'text': '#f1e4df', 'dim': '#bd9f93'},
          'Espresso':      {'card': '#2c2016', 'border': '#594331', 'track': '#423224', 'text': '#f1e7df', 'dim': '#bda693'},
          'Bronze':        {'card': '#48310f', 'border': '#7b5823', 'track': '#60441b', 'text': '#f1eadf', 'dim': '#bdac93'},
          'Olive':         {'card': '#2a3013', 'border': '#545f2b', 'track': '#3e4620', 'text': '#eef1df', 'dim': '#b5bd93'},
          'ForestFloor':   {'card': '#101c0e', 'border': '#2a4424', 'track': '#1b2e18', 'text': '#d0e0c8', 'dim': '#83977d'},
          'Jade':          {'card': '#113124', 'border': '#29614a', 'track': '#1e4836', 'text': '#dff1ea', 'dim': '#93bdac'},
          'Lagoon':        {'card': '#0e3434', 'border': '#236767', 'track': '#1a4c4c', 'text': '#dff1f1', 'dim': '#93bdbd'},
          'Petrol':        {'card': '#0f303e', 'border': '#235a71', 'track': '#1b4456', 'text': '#dfecf1', 'dim': '#93b1bd'},
          'Cobalt':        {'card': '#132949', 'border': '#294a7a', 'track': '#20395f', 'text': '#dfe6f1', 'dim': '#93a4bd'},
          'Indigo':        {'card': '#1e1e48', 'border': '#383876', 'track': '#2c2c5d', 'text': '#dfdff1', 'dim': '#9393bd'},
          'Plum':          {'card': '#341c3f', 'border': '#5a376c', 'track': '#472b54', 'text': '#ebdff1', 'dim': '#af93bd'},
          'Mulberry':      {'card': '#3f1731', 'border': '#6e3057', 'track': '#552544', 'text': '#f1dfea', 'dim': '#bd93ae'},
          'Paper':         {'card': '#f5f7fb', 'border': '#c9d1dc', 'track': '#dadfe8', 'text': '#1b2130', 'dim': '#5c6676'},
          'Fog':           {'card': '#dde2e8', 'border': '#b8c0ca', 'track': '#c5ccd5', 'text': '#1b2028', 'dim': '#545d69'},
          'Stone':         {'card': '#e1dedb', 'border': '#b9b5b1', 'track': '#c5c2be', 'text': '#2b2117', 'dim': '#63574b'},
          'Sand':          {'card': '#e7dfcf', 'border': '#c1b6a4', 'track': '#cbc2b3', 'text': '#2b2417', 'dim': '#675942'},
          'Linen':         {'card': '#f7f2e8', 'border': '#dcd1bd', 'track': '#e4dac9', 'text': '#2b2620', 'dim': '#73685a'},
          'Butter':        {'card': '#fbf5dc', 'border': '#e3d7a6', 'track': '#e8ddb1', 'text': '#2e2a18', 'dim': '#766c4c'},
          'Peach':         {'card': '#fce9df', 'border': '#dfbdaa', 'track': '#e6ccbc', 'text': '#2b1e17', 'dim': '#705d51'},
          'Blush':         {'card': '#faedf0', 'border': '#eccad2', 'track': '#efd1d8', 'text': '#321c22', 'dim': '#80606a'},
          'Rose':          {'card': '#ecd5dd', 'border': '#c7a9b3', 'track': '#d1b8c0', 'text': '#2b171e', 'dim': '#70515c'},
          'Orchid':        {'card': '#f4e5f5', 'border': '#d1b6d3', 'track': '#dbc6dc', 'text': '#2a172b', 'dim': '#6e5170'},
          'Lavender':      {'card': '#f0ecfa', 'border': '#d2c9ec', 'track': '#dad3f0', 'text': '#231e33', 'dim': '#665e80'},
          'Periwinkle':    {'card': '#e3e6f7', 'border': '#b2b7d6', 'track': '#c3c7df', 'text': '#171a2b', 'dim': '#515670'},
          'Sky':           {'card': '#e7f0fa', 'border': '#bdd2ea', 'track': '#c7daee', 'text': '#18222f', 'dim': '#53667d'},
          'Aqua':          {'card': '#ddf2f3', 'border': '#aecfd0', 'track': '#bfd9d9', 'text': '#172a2b', 'dim': '#516f70'},
          'Mint':          {'card': '#e8f5ee', 'border': '#bcdccb', 'track': '#c5e1d2', 'text': '#1b2a22', 'dim': '#557064'},
          'Pistachio':     {'card': '#ebf3dd', 'border': '#c4cfaf', 'track': '#cfd9bf', 'text': '#242b17', 'dim': '#657051'}}
OLD_THEME_NAMES = {'Midnight': 'Carbon', 'VoidBlue': 'Carbon', 'DarkSlate': 'Slate', 'MidnightPurple': 'Plum', 'DeepOceanTeal': 'Lagoon'}   # saved by older versions
# --- end WIDGET THEMES ---
ACCENTS = {'Follows load': None, 'Blue': '#1e9bff', 'Green': '#2ecc71', 'Teal': '#2ad4c8', 'Purple': '#c48cff', 'Orange': '#ff7f50', 'Gold': '#e8a33d'}
C_CLOSE = '#c0392b'
C_MENU_SEL = '#2a62a8'                # right-click menu highlight (white text); its background and text come from the theme - see menu_colors()
C_SWATCH_EDGE = '#7c8594'             # outline of the theme swatches in the Theme menu - mid gray shows on dark and light menus
FONT_MENU = ('Segoe UI', 10)
LOAD_STOPS = [(0, '#2ecc71'), (45, '#2ecc71'), (72, '#e8a33d'), (100, '#ff6b6b')]      # (percent, color) - the accent is blended between these
SIZES = {'Small': 0.8, 'Medium': 1.0, 'Large': 1.3}
OPACITIES = (100, 90, 80, 70, 60)
REFRESHES = ((500, '0.5 s'), (1000, '1 s'), (2000, '2 s'), (5000, '5 s'))
HISTORY = 60                          # readings kept for the sparkline

# card geometry in design pixels (at 96 dpi, Medium); everything is multiplied by the scale when drawn
CARD_W, CARD_H, RADIUS = 184, 212, 18
RING_CX, RING_CY, RING_R, RING_W = CARD_W / 2, 97, 50, 10
SPARK_X0, SPARK_X1, SPARK_Y0, SPARK_Y1 = 18, CARD_W - 18, 158, 184
CLOSE_X, CLOSE_Y, CLOSE_R = CARD_W - 19, 19, 11
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # bold / regular: Windows first, then Linux


class G:                              # program-wide state
    window = None
    scale = 1.0                       # screen dpi / 96 times the Size multiplier
    size_name = 'Medium'
    theme = 'Toybox'                  # key into THEMES
    accent = None                     # None = ring color follows the load, else a fixed '#rrggbb'
    hover = False                     # mouse is over the close x
    press = None                      # (x, y) where the left button went down on the card
    samples = deque(maxlen=HISTORY)
    detail = ''
    demo = 35.0                       # last fake reading in --demo mode
    fonts = {}                        # (bold, px) -> ImageFont
    swatches = {}                     # (theme name, brightness) -> tk.PhotoImage shown in the Theme menu
    bright = 0                        # Brightness: -80 (much darker) .. 50 (lighter), 0 = the theme as designed
    tuned = {}                        # (theme name, brightness) -> the theme's colors at that brightness


# ---------- Readings ----------
def read_metric():
    """Returns the current percent and fills G.detail with the line shown under the sparkline"""
    if DEMO:
        G.demo = max(0.0, min(100.0, (G.samples[-1] if G.samples else 35.0) + random.gauss(0, 6) + (3 if random.random() < 0.08 else 0)))
        G.detail = 'demo readings' if METRIC == 'CPU' else f'{32 * G.demo / 100:.1f} / 32.0 GB in use   (demo)'
        return G.demo
    if METRIC == 'RAM':
        vm = psutil.virtual_memory()
        G.detail = f'{vm.used / 2 ** 30:.1f} / {vm.total / 2 ** 30:.1f} GB in use'
        return vm.percent
    pct = psutil.cpu_percent(interval=None)                      # load since the previous call (the first call is primed in main)
    peak = max(list(G.samples) + [pct])
    G.detail = f'{psutil.cpu_count() or 1} cores   ·   peak {peak:.0f}%'
    return pct


# ---------- Drawing ----------
def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, f):
    """Blend two hex colors, f=0 -> c1, f=1 -> c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(rgb(c1), rgb(c2)))


def is_light(color):
    """True for a light color - a light card gets darker accents"""
    r, g, b = rgb(color)
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


def load_color(pct):
    """Accent color for a percentage: green up to 45, amber around 72, red at 100 (smooth in between)"""
    for (p0, c0), (p1, c1) in zip(LOAD_STOPS, LOAD_STOPS[1:]):
        if pct <= p1:
            return mix(c0, c1, (pct - p0) / (p1 - p0))
    return LOAD_STOPS[-1][1]


def font(bold, px):
    """A Segoe UI (Windows) / DejaVu (Linux) font of px pixels, cached"""
    key = (bold, px)
    if key not in G.fonts:
        f = None
        for name in FONT_NAMES[bold]:
            try:
                f = ImageFont.truetype(name, px)
                break
            except OSError:
                continue
        if f is None:
            try:
                f = ImageFont.load_default(size=px)
            except TypeError:
                f = ImageFont.load_default()
        G.fonts[key] = f
    return G.fonts[key]


def render(pct):
    """Draw the whole card for the current reading and return it as PNG bytes.  Drawn at 2x and shrunk, so every edge is antialiased"""
    s = G.scale
    k = s * 2
    W, H = round(CARD_W * k), round(CARD_H * k)
    T = theme_colors()                                                # the theme at the Brightness setting
    C_CARD, C_BORDER, C_TRACK, C_TEXT, C_DIM = T['card'], T['border'], T['track'], T['text'], T['dim']
    accent = G.accent or load_color(pct)
    if is_light(C_CARD) and G.accent in ACCENTS.values():
        accent = mix(accent, '#000000', 0.18)                     # load colors and presets a shade darker on a light card (an Any... color is used as picked)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=(RADIUS if SEE_THROUGH else 0) * k, fill=C_CARD, outline=C_BORDER, width=max(1, round(k)))
    # header: colored dot + metric name, close x in the corner
    d.ellipse((16 * k - 4 * k, 19 * k - 4 * k, 16 * k + 4 * k, 19 * k + 4 * k), fill=accent)
    d.text((27 * k, 19 * k), METRIC, font=font(True, round(13 * k)), fill=C_DIM, anchor='lm')
    cx, cy, r = CLOSE_X * k, CLOSE_Y * k, 4.5 * k
    if G.hover:
        d.ellipse((cx - CLOSE_R * k, cy - CLOSE_R * k, cx + CLOSE_R * k, cy + CLOSE_R * k), fill=C_CLOSE)
    xc = C_TEXT if G.hover else mix(C_DIM, C_CARD, 0.35)
    d.line((cx - r, cy - r, cx + r, cy + r), fill=xc, width=max(1, round(1.6 * k)))
    d.line((cx - r, cy + r, cx + r, cy - r), fill=xc, width=max(1, round(1.6 * k)))
    # ring gauge: 270 degree track from bottom-left clockwise, the value arc on top with round ends, a soft glow behind it
    cx, cy, r, w = RING_CX * k, RING_CY * k, RING_R * k, round(RING_W * k)
    box = lambda width: (cx - r - width / 2, cy - r - width / 2, cx + r + width / 2, cy + r + width / 2)    # Pillow draws a wide arc inward from the box edge: this centers it on r
    end = 135 + 270 * max(0.0, min(100.0, pct)) / 100
    cap = lambda a, color, width=w: d.ellipse((cx + r * math.cos(math.radians(a)) - width / 2, cy + r * math.sin(math.radians(a)) - width / 2,
                                               cx + r * math.cos(math.radians(a)) + width / 2, cy + r * math.sin(math.radians(a)) + width / 2), fill=color)
    d.arc(box(w), 135, 405, fill=C_TRACK, width=w)
    cap(135, C_TRACK), cap(405, C_TRACK)                                                            # round ends on the track
    if pct > 0:
        if end - 135 > 15:
            glow, gw = mix(accent, C_CARD, 0.82), round(w * 1.7)                                     # soft glow behind the value arc, round ends too
            d.arc(box(gw), 135, end, fill=glow, width=gw)
            cap(135, glow, gw), cap(end, glow, gw)
        d.arc(box(w), 135, end, fill=accent, width=w)
        cap(135, accent), cap(end, accent)
    # the number, with a small % after it, centered as a group
    big, small = font(True, round(36 * k)), font(True, round(15 * k))
    num = f'{pct:.0f}'
    wn, wp = d.textlength(num, font=big), d.textlength('%', font=small)
    x0 = cx - (wn + 3 * k + wp) / 2
    base = cy + 13 * k
    d.text((x0, base), num, font=big, fill=C_TEXT, anchor='ls')
    d.text((x0 + wn + 3 * k, base), '%', font=small, fill=C_DIM, anchor='ls')
    # sparkline of the last readings, newest at the right, filled underneath
    x0, x1, y0, y1 = SPARK_X0 * k, SPARK_X1 * k, SPARK_Y0 * k, SPARK_Y1 * k
    d.line((x0, y1, x1, y1), fill=C_TRACK, width=max(1, round(k)))
    pts = list(G.samples)
    if len(pts) > 1:
        step = (x1 - x0) / (HISTORY - 1)
        xy = [(x1 - (len(pts) - 1 - i) * step, y1 - (y1 - y0) * min(100, max(0, p)) / 100) for i, p in enumerate(pts)]
        d.polygon([(xy[0][0], y1)] + xy + [(xy[-1][0], y1)], fill=mix(accent, C_CARD, 0.78))
        d.line(xy, fill=accent, width=max(1, round(1.5 * k)), joint='curve')
    d.text((CARD_W * k / 2, 198 * k), G.detail, font=font(False, round(12 * k)), fill=C_DIM, anchor='mm')
    im = im.resize((round(CARD_W * s), round(CARD_H * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return buf.getvalue()


def refresh(window):
    pct = read_metric()
    G.samples.append(pct)
    window[K_IMAGE].update(data=render(pct))


def redraw(window):
    """The card again with the last reading - after a change of look"""
    window[K_IMAGE].update(data=render(G.samples[-1]))


def keep_going(window, event, values):
    """While the Brightness panel is open the card keeps updating and hovering; anything else closes the panel and goes to the main loop"""
    if event == sg.EVENT_TIMER:
        refresh(window)
    elif event == K_HOVER:
        G.hover = values[K_HOVER]
        redraw(window)
    else:
        return False
    return True


# ---------- Window ----------
def make_menu(on_top, opacity, refresh_ms):
    """Right-click menu with a check mark on the current choices"""
    tick = lambda on: '✓ ' if on else '    '
    accent_name = next((n for n, c in ACCENTS.items() if c == G.accent), ACCENT_ANY)
    theme = lambda n: f'{tick(n == G.theme)}{n}::{KT_THEME(n)}'
    return ['', [f'{tick(on_top)}Keep on top::{K_TOP}',                # every label starts with a tick or the same width of spaces, so they line up
                 '    Theme', [theme(n) for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],
                 f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
                 '    Accent', [f'{tick(n == accent_name)}{n}::{KT_ACCENT(n)}' for n in list(ACCENTS) + [ACCENT_ANY]],
                 '    Size', [f'{tick(n == G.size_name)}{n}::{KT_SIZE(n)}' for n in SIZES],
                 '    Opacity', [f'{tick(p == opacity)}{p}%::{KT_OPACITY(p)}' for p in OPACITIES],
                 '    Refresh', [f'{tick(ms == refresh_ms)}{label}::{KT_REFRESH(ms)}' for ms, label in REFRESHES],
                 '---', '    Edit Me::Edit Me', '    Version::Version', f'    Exit::{K_EXIT}']]


def menu_colors():
    """Right-click menu background and text: the card's own colors (background lifted a touch), so the menu matches the theme"""
    T = theme_colors()
    return mix(T['card'], T['text'], 0.04), T['text']


def theme_swatch(name):
    """A tiny card in a theme's colors (card, a line of text, a dim line) shown beside its name in the Theme menu.  Made once and kept - tk drops images nobody holds"""
    if (name, G.bright) not in G.swatches:                                                      # a set per Brightness level: the chips show what you'd get
        T, z = theme_colors(name), max(1.0, G.window.TKroot.winfo_fpixels('1i') / 96) * 4           # drawn 4x and shrunk, so the edges are smooth
        im = Image.new('RGBA', (round(34 * z), round(20 * z)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=5 * z, fill=T['card'], outline=C_SWATCH_EDGE, width=round(z))
        d.rounded_rectangle((6 * z, 5.5 * z, 25 * z, 9 * z), radius=1.5 * z, fill=T['text'])
        d.rounded_rectangle((6 * z, 12 * z, 17 * z, 14.5 * z), radius=1.2 * z, fill=T['dim'])
        buf = io.BytesIO()
        im.resize((round(im.width / 4), round(im.height / 4)), Image.LANCZOS).save(buf, 'PNG')
        G.swatches[(name, G.bright)] = tk.PhotoImage(master=G.window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.swatches[(name, G.bright)]


def style_menus(window):
    """tk draws menus Windows-gray; recolor the right-click menu and its sub-menus in the card's colors, flat and compact, with a swatch beside each theme name"""
    bg, fg = menu_colors()

    def style(menu):
        menu.configure(bg=bg, fg=fg, activebackground=C_MENU_SEL, activeforeground='#ffffff', bd=0, activeborderwidth=1, relief='flat', font=FONT_MENU)
        first_light = True
        for i in range(menu.index('end') + 1 if menu.index('end') is not None else 0):
            name = menu.entrycget(i, 'label').lstrip('✓ ') if menu.type(i) == 'command' else None
            if name in THEMES:
                menu.entryconfigure(i, image=theme_swatch(name), compound='left')
                if first_light and is_light(THEMES[name]['card']):
                    menu.entryconfigure(i, columnbreak=1)                     # the light themes get a column of their own
                    first_light = False
        for child in menu.winfo_children():
            if isinstance(child, tk.Menu):
                style(child)
    style(window.TKRightClickMenu)


def apply_menu(window, on_top, opacity, refresh_ms):
    window[K_IMAGE].set_right_click_menu(make_menu(on_top, opacity, refresh_ms), propogate_to_window=True)
    style_menus(window)


def bind_mouse(window):
    """Hover highlight and click on the close x.  grab_anywhere already handles dragging; these bindings are added alongside it"""
    widget = window[K_IMAGE].Widget

    def over_close(e):
        return math.hypot(e.x - CLOSE_X * G.scale, e.y - CLOSE_Y * G.scale) <= CLOSE_R * G.scale

    def motion(e):
        if over_close(e) != G.hover:
            window.write_event_value(K_HOVER, over_close(e))

    def press(e):
        G.press = (e.x, e.y)

    def release(e):
        if G.press and over_close(e) and math.hypot(e.x - G.press[0], e.y - G.press[1]) < 4:        # a click, not a drag that ended on the x
            window.write_event_value(K_CLOSE, None)
        G.press = None

    widget.bind('<Motion>', motion, add='+')
    widget.bind('<Leave>', lambda e: window.write_event_value(K_HOVER, False) if G.hover else None, add='+')
    widget.bind('<ButtonPress-1>', press, add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')


# --- BRIGHTNESS: the same block in every card widget (master copy in modern_widget_recipe.md) - the program darkens or lightens its own theme ---
# Right-click > Brightness... opens a small panel under the card with a slider, and the card changes as the knob moves.  theme_colors() is what the card,
# its menu and the Theme chips are drawn with: the theme at the chosen level, its text kept readable.  The program supplies redraw(window),
# font(bold, px), is_light(), RADIUS, TRANSPARENT, THEMES and G.theme / G.scale / G.bright / G.tuned.
BRIGHT_LEVELS = list(range(-80, 51, 5))                           # the slider's stops, darkest first: -80 = much darker, 0 = as designed, 50 = lighter
K_BRIGHT = '-BRIGHTNESS-'                                         # settings-file entry, and the right-click item that opens the panel
K_PANEL_IMAGE, K_PANEL_VALUE, K_PANEL_STEP = '-PANEL IMAGE-', '-PANEL VALUE-', '-PANEL STEP-'      # values: the new level / +1 or -1 stop
K_PANEL_HOVER, K_PANEL_CLICK = '-PANEL HOVER-', '-PANEL CLICK-'   # values: 'track' | 'reset' | 'done' | None
K_PANEL_DONE, K_PANEL_CANCEL = '-PANEL DONE-', '-PANEL CANCEL-'   # Enter / Escape
PANEL_W, PANEL_H = 270, 114                                       # the panel, in design pixels
TRACK_X0, TRACK_X1, TRACK_Y, TRACK_H = 20, PANEL_W - 20, 52, 10
PILL_W, PILL_H, PILL_Y = 70, 24, 90                               # Reset (left) and Done (right); PILL_Y is their middle
C_PANEL_DONE = '#2a62a8'                                          # the Done button


def channels(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def shade(c1, c2, f):
    """c1 moved f of the way toward c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(channels(c1), channels(c2)))


def tune(color, level, light, line=False):
    """A card / border / track color at a Brightness level.  Dark themes: the brightness is scaled - darker is deeper, lighter more vivid, the hue kept;
       lines darken less, so the border and the gauge track still show at -80.  Light themes: darker turns gently gray (at most 32%), lighter fades to white"""
    if light and level > 0:
        return shade(color, '#ffffff', level / 100)
    f = 1 + level / (250 if light else 100)
    if line and level < 0 and not light:
        f **= 0.6
    return '#%02x%02x%02x' % tuple(min(255, round(v * f)) for v in channels(color))


def luminance(color):
    """WCAG relative luminance, 0 = black .. 1 = white"""
    return sum(w * (v / 3294.6 if v <= 10.31 else ((v / 255 + 0.055) / 1.055) ** 2.4) for w, v in zip((0.2126, 0.7152, 0.0722), channels(color)))


def readable(fg, bg, ratio, pole):
    """fg moved toward pole (white on a dark card, black on a light one) just far enough to have ratio contrast with bg"""
    lb = luminance(bg)
    for i in range(26):
        c = shade(fg, pole, i / 25)
        lf = luminance(c)
        if (max(lf, lb) + 0.05) / (min(lf, lb) + 0.05) >= ratio:
            return c
    return pole


def theme_colors(name=None):
    """A theme's five colors at the Brightness setting (the chosen theme if no name) - text keeps 7:1 contrast with the card, dim 4.5:1"""
    name = name if name in THEMES else G.theme if G.theme in THEMES else 'Toybox'
    if (name, G.bright) not in G.tuned:
        T = THEMES[name]
        if G.bright:
            light, level = is_light(T['card']), G.bright
            card, pole = tune(T['card'], level, light), '#000000' if light else '#ffffff'
            T = {'card': card, 'border': tune(T['border'], level, light, True), 'track': tune(T['track'], level, light, True),
                 'text': readable(T['text'], card, 7, pole), 'dim': readable(T['dim'], card, 4.5, pole)}
        G.tuned[(name, G.bright)] = T
    return G.tuned[(name, G.bright)]


def bright_text(level):
    return 'as designed' if level == 0 else f'{level:+d}%'.replace('-', '\u2212')


def knob_x(level):
    """Design-pixel x of the knob at a level: the middle of that level's band on the track"""
    return TRACK_X0 + (BRIGHT_LEVELS.index(level) + 0.5) * (TRACK_X1 - TRACK_X0) / len(BRIGHT_LEVELS)


def level_at(x):
    """The level whose band is under panel pixel x"""
    i = int((x / G.scale - TRACK_X0) / (TRACK_X1 - TRACK_X0) * len(BRIGHT_LEVELS))
    return BRIGHT_LEVELS[max(0, min(len(BRIGHT_LEVELS) - 1, i))]


def panel_part(x, y):
    """'track', 'reset', 'done' or None at panel pixel (x, y)"""
    x, y = x / G.scale, y / G.scale
    if TRACK_X0 - 10 <= x <= TRACK_X1 + 10 and abs(y - TRACK_Y) <= 14:
        return 'track'
    if abs(y - PILL_Y) <= PILL_H / 2:
        if 18 <= x <= 18 + PILL_W:
            return 'reset'
        if PANEL_W - 18 - PILL_W <= x <= PANEL_W - 18:
            return 'done'
    return None


def render_panel(hover):
    """The Brightness panel, drawn like the card and in its colors (so it changes too).  The track shows the card's own color at every level, darkest
       on the left; the knob sits on the one in use, the tick under the track marks 'as designed'"""
    s = G.scale
    k = s * 2
    T, base = theme_colors(), THEMES.get(G.theme, THEMES['Toybox'])
    light = is_light(base['card'])
    W, H = round(PANEL_W * k), round(PANEL_H * k)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=(RADIUS if sg.running_windows() else 0) * k, fill=T['card'], outline=T['border'], width=max(1, round(k)))
    d.text((18 * k, 20 * k), 'BRIGHTNESS', font=font(True, round(13 * k)), fill=T['dim'], anchor='lm')
    d.text(((PANEL_W - 18) * k, 20 * k), bright_text(G.bright), font=font(True, round(13 * k)), fill=T['text'], anchor='rm')
    x0, x1, y0, y1 = TRACK_X0 * k, TRACK_X1 * k, (TRACK_Y - TRACK_H / 2) * k, (TRACK_Y + TRACK_H / 2) * k
    strip = Image.new('RGBA', (round(x1 - x0), round(y1 - y0)))                       # a band per level, in the card color at that level
    band = strip.width / len(BRIGHT_LEVELS)
    for i, level in enumerate(BRIGHT_LEVELS):
        ImageDraw.Draw(strip).rectangle((round(i * band), 0, round((i + 1) * band), strip.height), fill=tune(base['card'], level, light))
    mask = Image.new('L', strip.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, strip.width - 1, strip.height - 1), radius=strip.height / 2, fill=255)
    im.paste(strip, (round(x0), round(y0)), mask)
    d.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) / 2, outline=T['dim'] if hover == 'track' else T['border'], width=max(1, round(k)))
    zx = knob_x(0) * k
    d.line((zx, y1 + 3 * k, zx, y1 + 7 * k), fill=T['dim'], width=max(1, round(1.2 * k)))
    kx, ky, r = knob_x(G.bright) * k, TRACK_Y * k, 9 * k                                # the knob, filled with the color in use
    d.ellipse((kx - r, ky - r, kx + r, ky + r), fill=T['card'], outline=T['text'], width=max(1, round(2 * k)))
    small = font(False, round(11 * k))
    d.text((x0, (TRACK_Y + 17) * k), 'darker', font=small, fill=T['dim'], anchor='lm')
    d.text((x1, (TRACK_Y + 17) * k), 'lighter', font=small, fill=T['dim'], anchor='rm')
    for part, px, fill, color in (('reset', 18, T['track'], T['text'] if G.bright else T['dim']), ('done', PANEL_W - 18 - PILL_W, C_PANEL_DONE, '#ffffff')):
        if hover == part:
            fill = shade(fill, '#ffffff', 0.15) if part == 'done' else shade(T['text'], T['card'], 0.78)
        d.rounded_rectangle((px * k, (PILL_Y - PILL_H / 2) * k, (px + PILL_W) * k, (PILL_Y + PILL_H / 2) * k), radius=PILL_H / 2 * k, fill=fill)
        d.text(((px + PILL_W / 2) * k, PILL_Y * k), part.capitalize(), font=font(True, round(12 * k)), fill=color, anchor='mm')
    im = im.resize((round(PANEL_W * s), round(PANEL_H * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return buf.getvalue()


def brightness_panel(card, keep_going):
    """Right-click > Brightness...: the panel under the card.  The card and the panel change as the knob moves (drag, click, arrow keys, mouse wheel,
       Home / End).  Done or Enter keeps the level, Escape puts back the one it had.  keep_going(card, event, values) handles the card's own events
       meanwhile (its timer, hover...) and returns False for one that should close the panel - a menu choice, the close x.  That event is returned so the
       main loop can handle it; None otherwise"""
    start = G.bright
    x, y = card.current_location()
    below, height = y + card.size[1] + 6, round(PANEL_H * G.scale)
    py = below if below + height <= card.TKroot.winfo_screenheight() else max(0, y - height - 6)    # under the card, or above it near the bottom
    panel = sg.Window('Brightness', [[sg.Image(data=render_panel(None), key=K_PANEL_IMAGE, background_color=TRANSPARENT, pad=(0, 0))]], no_titlebar=True,
                      keep_on_top=True, margins=(0, 0), element_padding=(0, 0), background_color=TRANSPARENT, location=(x, py), finalize=True,
                      transparent_color=TRANSPARENT if sg.running_windows() else None)  # no grab_anywhere: it would move the panel as the knob is dragged
    widget, mouse = panel[K_PANEL_IMAGE].Widget, {'drag': False, 'press': None, 'hover': None}

    def press(e):
        part = panel_part(e.x, e.y)
        if part == 'track':                                                             # the knob jumps to the mouse and follows it
            mouse['drag'] = True
            panel.write_event_value(K_PANEL_VALUE, level_at(e.x))
        else:
            mouse['press'] = (e.x_root, e.y_root, part, panel.TKroot.winfo_x(), panel.TKroot.winfo_y())

    def drag(e):
        p = mouse['press']
        if mouse['drag']:
            panel.write_event_value(K_PANEL_VALUE, level_at(e.x))
        elif p:                                                                         # anywhere off the track drags the panel
            panel.TKroot.geometry(f'+{p[3] + e.x_root - p[0]}+{p[4] + e.y_root - p[1]}')

    def release(e):
        if mouse['drag']:
            mouse['drag'] = False
            return
        p, mouse['press'] = mouse['press'], None
        if p and p[2] in ('reset', 'done') and math.hypot(e.x_root - p[0], e.y_root - p[1]) < 4:        # a click, not a drag of the panel
            panel.write_event_value(K_PANEL_CLICK, p[2])

    def hover(part):
        if part != mouse['hover']:
            mouse['hover'] = part
            panel.write_event_value(K_PANEL_HOVER, part)

    widget.bind('<ButtonPress-1>', press, add='+')
    widget.bind('<B1-Motion>', drag, add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')
    widget.bind('<Motion>', lambda e: hover(panel_part(e.x, e.y)), add='+')
    widget.bind('<Leave>', lambda e: hover(None), add='+')
    widget.bind('<MouseWheel>', lambda e: panel.write_event_value(K_PANEL_STEP, 1 if e.delta > 0 else -1), add='+')   # Windows
    widget.bind('<Button-4>', lambda e: panel.write_event_value(K_PANEL_STEP, 1), add='+')                            # Linux wheel
    widget.bind('<Button-5>', lambda e: panel.write_event_value(K_PANEL_STEP, -1), add='+')
    for seq, n in (('<Left>', -1), ('<Down>', -1), ('<Right>', 1), ('<Up>', 1)):
        panel.TKroot.bind(seq, lambda e, n=n: panel.write_event_value(K_PANEL_STEP, n))
    panel.TKroot.bind('<Home>', lambda e: panel.write_event_value(K_PANEL_VALUE, BRIGHT_LEVELS[0]))
    panel.TKroot.bind('<End>', lambda e: panel.write_event_value(K_PANEL_VALUE, BRIGHT_LEVELS[-1]))
    panel.bind('<Return>', K_PANEL_DONE)
    panel.bind('<Escape>', K_PANEL_CANCEL)
    panel.force_focus()
    pending = None
    while True:
        win, event, values = sg.read_all_windows()
        if win is card:                                                                 # the card keeps going while the panel is open
            if keep_going(card, event, values):
                continue
            pending = (event, values)
            break
        if event in (sg.WINDOW_CLOSED, K_PANEL_CANCEL):
            G.bright = start
            break
        if event == K_PANEL_DONE or (event == K_PANEL_CLICK and values[event] == 'done'):
            break
        level = G.bright
        if event == K_PANEL_VALUE:
            level = values[event]
        elif event == K_PANEL_STEP:
            level = BRIGHT_LEVELS[max(0, min(len(BRIGHT_LEVELS) - 1, BRIGHT_LEVELS.index(G.bright) + values[event]))]
        elif event == K_PANEL_CLICK and values[event] == 'reset':
            level = 0
        if level != G.bright:
            G.bright = level
            redraw(card)
        panel[K_PANEL_IMAGE].update(data=render_panel(mouse['hover']))
    panel.close()
    redraw(card)
    return pending
# --- end BRIGHTNESS ---


def main():
    sg.set_options(dpi_awareness=True)
    G.size_name = sg.user_settings_get_entry(K_SIZE, 'Medium')
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')           # a renamed theme (Midnight -> VoidBlue) or an unknown one
    G.accent = sg.user_settings_get_entry(K_ACCENT, None)
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    on_top = sg.user_settings_get_entry(K_TOP, False)
    refresh_ms = sg.user_settings_get_entry(K_REFRESH, 1000)
    opacity = sg.user_settings_get_entry(K_OPACITY, 90)
    if METRIC == 'CPU':
        psutil.cpu_percent(interval=None)                                          # prime: the first reading is always 0
    pct = read_metric()
    G.samples.append(pct)
    layout = [[sg.Image(data=render(pct), key=K_IMAGE, background_color=TRANSPARENT, pad=(0, 0))]]
    menu_bg, menu_text = menu_colors()
    window = sg.Window(f'{METRIC} %', layout, no_titlebar=True, grab_anywhere=True, keep_on_top=on_top, margins=(0, 0), element_padding=(0, 0), background_color=TRANSPARENT,
                       transparent_color=TRANSPARENT if SEE_THROUGH else None, alpha_channel=opacity / 100, auto_save_location=True, icon=ICON, finalize=True,
                       right_click_menu=make_menu(on_top, opacity, refresh_ms), right_click_menu_background_color=menu_bg, right_click_menu_text_color=menu_text,
                       right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU)
    G.window = window
    style_menus(window)
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96) * SIZES.get(G.size_name, 1.0)       # 2.0 on a 200% Windows display
    window[K_IMAGE].update(data=render(pct))
    bind_mouse(window)
    window.bind('<Escape>', K_EXIT)
    window.timer_start(refresh_ms)

    pending = None                                                                         # a card event that came in while the Brightness panel was open
    while True:
        event, values = pending or window.read()
        pending = None
        menu_key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event             # right-click items come back as 'label::key'
        if menu_key in (K_EXIT, sg.WINDOW_CLOSED, K_CLOSE):
            break
        if event == sg.EVENT_TIMER:
            refresh(window)
        elif event == K_HOVER:
            G.hover = values[K_HOVER]
            window[K_IMAGE].update(data=render(G.samples[-1]))
        elif menu_key == K_TOP:
            on_top = not on_top
            window.keep_on_top_set() if on_top else window.keep_on_top_clear()
            sg.user_settings_set_entry(K_TOP, on_top)
            apply_menu(window, on_top, opacity, refresh_ms)
        elif isinstance(menu_key, str) and menu_key.startswith(K_SIZE):
            G.size_name = menu_key[len(K_SIZE):]
            G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96) * SIZES[G.size_name]
            sg.user_settings_set_entry(K_SIZE, G.size_name)
            window[K_IMAGE].update(data=render(G.samples[-1]))
            apply_menu(window, on_top, opacity, refresh_ms)
        elif isinstance(menu_key, str) and menu_key.startswith(K_THEME):
            G.theme = menu_key[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            window[K_IMAGE].update(data=render(G.samples[-1]))
            apply_menu(window, on_top, opacity, refresh_ms)
        elif isinstance(menu_key, str) and menu_key.startswith(K_ACCENT):
            name = menu_key[len(K_ACCENT):]
            if name == ACCENT_ANY:                                                                      # system color dialog; Cancel keeps the current accent
                chosen = colorchooser.askcolor(color=G.accent or load_color(G.samples[-1]), parent=window.TKroot, title='Accent color')[1]
                if not chosen:
                    continue
                G.accent = chosen
            else:
                G.accent = ACCENTS[name]
            sg.user_settings_set_entry(K_ACCENT, G.accent)
            window[K_IMAGE].update(data=render(G.samples[-1]))
            apply_menu(window, on_top, opacity, refresh_ms)
        elif isinstance(menu_key, str) and menu_key.startswith(K_OPACITY):
            opacity = int(menu_key[len(K_OPACITY):])
            window.set_alpha(opacity / 100)
            sg.user_settings_set_entry(K_OPACITY, opacity)
            apply_menu(window, on_top, opacity, refresh_ms)
        elif isinstance(menu_key, str) and menu_key.startswith(K_REFRESH):
            refresh_ms = int(menu_key[len(K_REFRESH):])
            window.timer_stop_all()
            window.timer_start(refresh_ms)
            sg.user_settings_set_entry(K_REFRESH, refresh_ms)
            apply_menu(window, on_top, opacity, refresh_ms)
        elif menu_key == K_BRIGHT:
            pending = brightness_panel(window, keep_going)
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            redraw(window)
            apply_menu(window, on_top, opacity, refresh_ms)
        elif menu_key == 'Version':
            sg.popup_scrolled(__file__, f'{METRIC} percent widget v{VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif menu_key == 'Edit Me':
            sg.execute_editor(__file__)
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback('Crash', e)
