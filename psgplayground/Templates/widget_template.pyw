#!/usr/bin/env python3
"""
widget_template.pyw - a desktop card widget to build on, with the look and settings of the Playground widgets already working.
Copy it, rename it, then change TITLE, read_value() and draw_content() - everything else is done.

    One rounded card drawn with Pillow (antialiased, so it looks the same at every Windows display scaling), shown in a single Image element.
    No title bar: drag it anywhere on the card.  The faint x in the corner (red when hovered) closes it; so does Escape.
    The corners are see-through and click-through on Windows (Linux / Mac get square corners - only Windows can make them see-through).
    Right-click:  Keep on top  |  Theme (16 dark + 16 light, as color chips)  |  Brightness... (darker / lighter)  |  Size  |  Opacity  |  Edit Me / Version / Exit
    Every choice is remembered (PySimpleGUI user settings), and so is the window position.
    The WIDGET THEMES and BRIGHTNESS blocks are the same in every card widget (% CPU, % RAM, Pip Refresh, PSG Dock) - paste them unchanged.

    Your widget:  TITLE is the label at the top of the card, read_value() is called every REFRESH_MS, draw_content() draws the middle of the card.
                  The example is a clock: time, a bar for the seconds, the date.

    Requires:  pip install PySimpleGUI pillow

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v1.0  First version - the card, menus, 32 themes and Brightness from cpu_percent_widget.pyw 1.7, with a clock as the content
"""
import base64
import datetime
import io
import math
import tkinter as tk

import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont

VERSION = '1.0'
APP_NAME = 'Widget Template'          # the window title (the taskbar and Alt-Tab show it) and the Version popup
TITLE = 'CLOCK'                       # the label at the top of the card - your widget's name
REFRESH_MS = 1000                     # how often read_value() is called
ICON = b'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'      # 64 px PNG, base64 - a card with a ring gauge and three theme chips

# ---------- Keys ----------
K_IMAGE = '-IMAGE-'
K_HOVER = '-HOVER-'                   # mouse moved over / off the close x  (value: True / False)
K_CLOSE = '-CLOSE-'                   # close x clicked
K_TOP = '-TOP-'                       # right-click: keep on top toggle (and its settings-file entry)
K_SIZE = '-SIZE-'                     # settings-file entry, and the prefix of the size menu keys
KT_SIZE = lambda name: f'{K_SIZE}{name}'
K_OPACITY = '-OPACITY-'
KT_OPACITY = lambda pct: f'{K_OPACITY}{pct}'
K_THEME = '-THEME-'                   # settings-file entry, and the prefix of the theme menu keys
KT_THEME = lambda name: f'{K_THEME}{name}'
K_EXIT = 'Exit'

# ---------- Look ----------
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
ACCENT = '#1e9bff'                    # the dot by the title and the seconds bar - pick your own
C_CLOSE = '#c0392b'
C_MENU_SEL = '#2a62a8'                # right-click menu highlight (white text); its background and text come from the theme - see menu_colors()
C_SWATCH_EDGE = '#7c8594'             # outline of the theme chips in the Theme menu - mid gray shows on dark and light menus
FONT_MENU = ('Segoe UI', 10)
SIZES = {'Small': 0.8, 'Medium': 1.0, 'Large': 1.3}
OPACITIES = (100, 90, 80, 70, 60)

# card geometry in design pixels (at 96 dpi, Medium); everything is multiplied by the scale when drawn
CARD_W, CARD_H, RADIUS = 184, 132, 18
HEADER_H = 34                         # the dot + TITLE row; draw_content() gets the rest
CLOSE_X, CLOSE_Y, CLOSE_R = CARD_W - 19, 19, 11
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # bold / regular: Windows first, then Linux


class G:                              # program-wide state
    window = None
    scale = 1.0                       # screen dpi / 96 times the Size multiplier
    size_name = 'Medium'
    theme = 'Toybox'                  # key into THEMES
    value = None                      # what read_value() returned last
    hover = False                     # mouse is over the close x
    press = None                      # (x, y) where the left button went down on the card
    fonts = {}                        # (bold, px) -> ImageFont
    swatches = {}                     # (theme name, brightness) -> tk.PhotoImage shown in the Theme menu
    bright = 0                        # Brightness: -80 (much darker) .. 50 (lighter), 0 = the theme as designed
    tuned = {}                        # (theme name, brightness) -> the theme's colors at that brightness


# ---------- Your widget: what it reads and what it draws ----------
def read_value():
    """Called every REFRESH_MS - return whatever draw_content() needs.  The example: the time now"""
    return datetime.datetime.now()


def draw_content(d, k, T, now):
    """Draw the middle of the card on ImageDraw d.  k = image pixels per design pixel - multiply every coordinate and size by it.
       T = the theme's colors at the Brightness setting: card, border, track, text, dim.  The card is CARD_W x CARD_H design pixels, the header above HEADER_H"""
    cx = CARD_W / 2 * k
    big, small = font(True, round(34 * k)), font(True, round(14 * k))
    hm, ampm = now.strftime('%I:%M').lstrip('0'), now.strftime('%p')
    wb, ws = d.textlength(hm, font=big), d.textlength(ampm, font=small)
    x0, base = cx - (wb + 4 * k + ws) / 2, 76 * k                                     # the time and a small AM / PM after it, centered as a group
    d.text((x0, base), hm, font=big, fill=T['text'], anchor='ls')
    d.text((x0 + wb + 4 * k, base), ampm, font=small, fill=T['dim'], anchor='ls')
    x0, x1, y = 18 * k, (CARD_W - 18) * k, 91 * k                                     # the seconds: a bar that fills up every minute
    d.rounded_rectangle((x0, y - 2 * k, x1, y + 2 * k), radius=2 * k, fill=T['track'])
    if now.second:
        d.rounded_rectangle((x0, y - 2 * k, x0 + (x1 - x0) * now.second / 59, y + 2 * k), radius=2 * k, fill=ACCENT)
    d.text((cx, 112 * k), f'{now:%A}  {now.day} {now:%B}', font=font(False, round(12 * k)), fill=T['dim'], anchor='mm')


# ---------- Drawing ----------
def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, f):
    """Blend two hex colors, f=0 -> c1, f=1 -> c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(rgb(c1), rgb(c2)))


def is_light(color):
    """True for a light color - the Theme menu puts the light themes in a column of their own"""
    r, g, b = rgb(color)
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


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


def render():
    """Draw the whole card and return it as PNG bytes.  Drawn at 2x and shrunk, so every edge is antialiased"""
    s = G.scale
    k = s * 2
    W, H = round(CARD_W * k), round(CARD_H * k)
    T = theme_colors()                                                # the theme at the Brightness setting
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=(RADIUS if SEE_THROUGH else 0) * k, fill=T['card'], outline=T['border'], width=max(1, round(k)))
    d.ellipse((12 * k, 15 * k, 20 * k, 23 * k), fill=ACCENT)                          # header: a colored dot and the title, the close x in the corner
    d.text((27 * k, 19 * k), TITLE, font=font(True, round(13 * k)), fill=T['dim'], anchor='lm')
    cx, cy, r = CLOSE_X * k, CLOSE_Y * k, 4.5 * k
    if G.hover:
        d.ellipse((cx - CLOSE_R * k, cy - CLOSE_R * k, cx + CLOSE_R * k, cy + CLOSE_R * k), fill=C_CLOSE)
    xc = T['text'] if G.hover else mix(T['dim'], T['card'], 0.35)
    d.line((cx - r, cy - r, cx + r, cy + r), fill=xc, width=max(1, round(1.6 * k)))
    d.line((cx - r, cy + r, cx + r, cy - r), fill=xc, width=max(1, round(1.6 * k)))
    draw_content(d, k, T, G.value)
    im = im.resize((round(CARD_W * s), round(CARD_H * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return buf.getvalue()


def refresh(window):
    G.value = read_value()
    redraw(window)


def redraw(window):
    """The card again - after a new reading or a change of look"""
    window[K_IMAGE].update(data=render())


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
def make_menu(on_top, opacity):
    """Right-click menu with a check mark on the current choices"""
    tick = lambda on: '✓ ' if on else '    '
    theme = lambda n: f'{tick(n == G.theme)}{n}::{KT_THEME(n)}'
    return ['', [f'{tick(on_top)}Keep on top::{K_TOP}',                # every label starts with a tick or the same width of spaces, so they line up
                 '    Theme', [theme(n) for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],
                 f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
                 '    Size', [f'{tick(n == G.size_name)}{n}::{KT_SIZE(n)}' for n in SIZES],
                 '    Opacity', [f'{tick(p == opacity)}{p}%::{KT_OPACITY(p)}' for p in OPACITIES],
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
    """tk draws menus Windows-gray; recolor the right-click menu and its sub-menus in the card's colors, flat and compact, with a chip beside each theme name"""
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


def apply_menu(window, on_top, opacity):
    """A new menu (check marks moved) - and style it again: set_right_click_menu makes fresh, gray tk menus"""
    window[K_IMAGE].set_right_click_menu(make_menu(on_top, opacity), propogate_to_window=True)
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
    sg.user_settings_filename(filename='widget_template.json')                    # your own file in PySimpleGUI's settings folder - rename it with the program
    G.size_name = sg.user_settings_get_entry(K_SIZE, 'Medium')
    G.size_name = G.size_name if G.size_name in SIZES else 'Medium'
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')           # a renamed theme or an unknown one
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    on_top = sg.user_settings_get_entry(K_TOP, False)
    opacity = sg.user_settings_get_entry(K_OPACITY, 100)
    opacity = opacity if opacity in OPACITIES else 100
    G.value = read_value()
    menu_bg, menu_text = menu_colors()
    layout = [[sg.Image(data=render(), key=K_IMAGE, background_color=TRANSPARENT, pad=(0, 0))]]
    window = sg.Window(APP_NAME, layout, no_titlebar=True, grab_anywhere=True, keep_on_top=on_top, margins=(0, 0), element_padding=(0, 0), background_color=TRANSPARENT,
                       transparent_color=TRANSPARENT if SEE_THROUGH else None, alpha_channel=opacity / 100, auto_save_location=True, icon=ICON, finalize=True,
                       right_click_menu=make_menu(on_top, opacity), right_click_menu_background_color=menu_bg, right_click_menu_text_color=menu_text,
                       right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU)
    G.window = window
    style_menus(window)
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96) * SIZES[G.size_name]       # 2.0 on a 200% Windows display
    redraw(window)
    bind_mouse(window)
    window.bind('<Escape>', K_EXIT)
    window.timer_start(REFRESH_MS)

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
            redraw(window)
        elif menu_key == K_TOP:
            on_top = not on_top
            window.keep_on_top_set() if on_top else window.keep_on_top_clear()
            sg.user_settings_set_entry(K_TOP, on_top)
            apply_menu(window, on_top, opacity)
        elif isinstance(menu_key, str) and menu_key.startswith(K_SIZE):
            G.size_name = menu_key[len(K_SIZE):]
            G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96) * SIZES[G.size_name]
            sg.user_settings_set_entry(K_SIZE, G.size_name)
            redraw(window)
            apply_menu(window, on_top, opacity)
        elif isinstance(menu_key, str) and menu_key.startswith(K_THEME):
            G.theme = menu_key[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            redraw(window)
            apply_menu(window, on_top, opacity)
        elif isinstance(menu_key, str) and menu_key.startswith(K_OPACITY):
            opacity = int(menu_key[len(K_OPACITY):])
            window.set_alpha(opacity / 100)
            sg.user_settings_set_entry(K_OPACITY, opacity)
            apply_menu(window, on_top, opacity)
        elif menu_key == K_BRIGHT:
            pending = brightness_panel(window, keep_going)
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            redraw(window)
            apply_menu(window, on_top, opacity)
        elif menu_key == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME}  version {VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif menu_key == 'Edit Me':
            sg.execute_editor(__file__)
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e)
