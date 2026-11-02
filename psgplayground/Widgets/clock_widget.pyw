#!/usr/bin/env python3
"""
clock_widget.pyw - the time and the date on a small card, with a bar that fills up every minute.

    One rounded card drawn with Pillow (antialiased, so it looks the same at every Windows display scaling), shown in a single Image element.
    No title bar: drag it anywhere on the card.  The faint x in the corner (red when hovered) closes it; so does Escape.
    The corners are see-through and click-through on Windows (Linux / Mac get square corners - only Windows can make them see-through).
    Right-click:  Keep on top  |  24-hour time  |  Theme (16 dark + 16 light, as color chips)  |  Brightness... (darker / lighter)  |  Size  |  Opacity
                  |  Edit Me / Version / Exit
    Every choice is remembered (PySimpleGUI user settings), and so is the window position.
    Made from Templates/widget_template.pyw - the WIDGET THEMES and BRIGHTNESS blocks are the same in every card widget; paste them unchanged.

    Requires:  pip install PySimpleGUI pillow

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v1.0  First version - the Widget Template's clock as a widget of its own, with a 24-hour choice on the right-click menu
"""
import base64
import datetime
import io
import math
import tkinter as tk

import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont

VERSION = '1.0'
APP_NAME = 'Clock Widget'             # the window title (the taskbar and Alt-Tab show it) and the Version popup
TITLE = 'CLOCK'                       # the label at the top of the card
REFRESH_MS = 1000                     # how often the time is read and the card redrawn
ICON = b'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jydVSOnJW99igz1dP45qDA8PUqtVR5lf4wqCYI9wGccMd3vP2oAgGCM6xhiSOKIaeyq9m4nv/huk4e5KI5HHzJ6HPf4CpDIIyrxDHiCCCcJx1m/k+Ep5iGUd72fBe46hXB4ed/i98oO3wZiGBwH09fXR3NTEsccex8lnnEv12btxT61C5fUYB3CCXXwxKsiBuHdGAVoprLW7ob4miaoopWhta+fST36ac867EOccWmsGBwcZHBwcVcSE7qM1xhgGBgbw3nPxJRfzwAP38S9X/z9aSiVMpkj82A1IrQ6GyiA10IcdjT7seKRWnnBa1JOxStoXHP/F3juSJMZYy6of385N37mevr4dAJTLZa688grOOussent7qVarWGv3wI9dQ8laS6VSYWhoiI6ODm699Ra++63/z5Hz57DhyTXct2olJteE3/oc7qUnUBmVWlwcKtSYI5amBdMEmf2kIFMby67TAKUUSRIjPqWrhUKRF57fiNIa5xzHHnssX/rSXyPiOf3007j++m/y3HPPUyo1E4YZXIPvi8caTRRH9PX1sXDhQq666nNcdNGF5AJ48Jdr+drXvsbatevIFwqIUkhcwf3m59hFS+onUuBBz1uK0jYFyP2pAAWovbiwd65xe0Q8mWwOYwz9/TtZvnwZxWKGgYEKF110EaeffgY33fQ9bv7hj/j91t/SHKapkyBPb7nGzBnT+dRfXc5ll13GnEOn8dwLm/j616/lnnvuoVwu09zcnKZS8RBk8VueqYeBSTtOCajp81D5ViSpjr6/fzygTmH36MX7ZJTeNkIlSWKampq44YZvsXnzFq666nMsWPBumpub+MIXv8j/vegC/v7qa3lgWwu5llb0f/w75x0/l09c8Tned/xCtu0o83f/8K/cfPPNbN26lVKpRKlUGsUVlIIgg/S+igwNooqt4AS8oIptqOI0pO+1OifYTwpo9PB2BUDxPs3/cUQURQBkszlMHSiNMdx11108+ODPufzyy/jYxz7OrJkzKLTNonb+tWR6IAggOPWzXHG25pjpcOud9/PVa65h48aNFAoF2tvbSZIE5xwiwvDwMCIeYwNySR++5yVs62IkEfCgclnUtLlIz4v1jPAOVoNKKaKoxlHvWsj8dy3AOcczT69ne0/PKFdoaWnBOcc113yVH/zwVlZ88bNsW3AB9/1GMSuvkKrQJwF//bMe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'      # 64 px PNG, base64 - a clock face in the widgets' blue ring

# ---------- Keys ----------
K_IMAGE = '-IMAGE-'
K_HOVER = '-HOVER-'                   # mouse moved over / off the close x  (value: True / False)
K_CLOSE = '-CLOSE-'                   # close x clicked
K_TOP = '-TOP-'                       # right-click: keep on top toggle (and its settings-file entry)
K_24H = '-24 HOUR-'                   # right-click: 24-hour time toggle (and its settings-file entry)
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
    hours24 = False                   # 13:05 instead of 1:05 PM
    hover = False                     # mouse is over the close x
    press = None                      # (x, y) where the left button went down on the card
    fonts = {}                        # (bold, px) -> ImageFont
    swatches = {}                     # (theme name, brightness) -> tk.PhotoImage shown in the Theme menu
    bright = 0                        # Brightness: -80 (much darker) .. 50 (lighter), 0 = the theme as designed
    tuned = {}                        # (theme name, brightness) -> the theme's colors at that brightness


# ---------- The clock: what it reads and what it draws ----------
def read_value():
    """Called every REFRESH_MS: the time now"""
    return datetime.datetime.now()


def draw_content(d, k, T, now):
    """Draw the middle of the card on ImageDraw d.  k = image pixels per design pixel - multiply every coordinate and size by it.
       T = the theme's colors at the Brightness setting: card, border, track, text, dim.  The card is CARD_W x CARD_H design pixels, the header above HEADER_H"""
    cx = CARD_W / 2 * k
    big, small = font(True, round(34 * k)), font(True, round(14 * k))
    hm, ampm = (now.strftime('%H:%M'), '') if G.hours24 else (now.strftime('%I:%M').lstrip('0'), now.strftime('%p'))
    wb, ws = d.textlength(hm, font=big), d.textlength(ampm, font=small)
    gap = 4 * k if ampm else 0
    x0, base = cx - (wb + gap + ws) / 2, 76 * k                                       # the time and a small AM / PM after it, centered as a group
    d.text((x0, base), hm, font=big, fill=T['text'], anchor='ls')
    if ampm:
        d.text((x0 + wb + gap, base), ampm, font=small, fill=T['dim'], anchor='ls')
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
                 f'{tick(G.hours24)}24-hour time::{K_24H}',
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
    sg.user_settings_filename(filename='clock_widget.json')
    G.size_name = sg.user_settings_get_entry(K_SIZE, 'Medium')
    G.size_name = G.size_name if G.size_name in SIZES else 'Medium'
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')           # a renamed theme or an unknown one
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    on_top = sg.user_settings_get_entry(K_TOP, False)
    G.hours24 = bool(sg.user_settings_get_entry(K_24H, False))
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
        elif menu_key == K_24H:
            G.hours24 = not G.hours24
            sg.user_settings_set_entry(K_24H, G.hours24)
            redraw(window)
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
