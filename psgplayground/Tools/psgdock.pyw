import PySimpleGUI as sg
import os
import io
import base64
import re
from typing import Dict
import ast
from PIL import Image, ImageDraw, ImageFont
from typing import List, Any
import psgdnd
import sys
import struct
import math
import urllib.parse
import json


"""
    PSG Dock  -  a small always-on-top dock of icon buttons that launch your programs.   (was MiniLauncher2)

    Borderless and semi-transparent, it sits at a corner of the screen out of the way.  Set it up by dropping programs onto entries in
    its Settings window (the icon is pulled out of the program), drag entries by their ☰ grip to put them in order.

    Changelog
    2.1     29-Oct-2026     Claude: single file (settings window merged in), toolbar + OK/Apply/Cancel settings window, drag-and-drop of
                            images and programs onto entries (icon pulled from the program), drag ☰ to reorder, 3-column layout fix,
                            version number added.
    2.1.1   29-Oct-2026     Claude: drag-to-reorder lifts the entry out as a floating replica (icon, name, path, icon string) with an orange
                            outline and leaves a grey slot where it will land; settings list widens to fit its entries so the trash cans
                            aren't cut off; size grip in the status bar for resizing the (titlebar-less) settings window.
    2.1.2   30-Oct-2026     Claude: the drop slot shown while dragging takes its colour from the theme (lighter shade of the background with a
                            faint outline) instead of fixed grey.
    2.1.3   30-Oct-2026     Claude: "Settings..." added to the right-click menu.
    2.2.18  02-Nov-2026     Claude: Python programs with no icon of their own get one on every system: their icon from the Playground's
                            catalog (a Playground program), else a picture beside them with their name (x.png, x_icon.png, x.ico), else
                            Python's icon on Windows and PySimpleGUI's on Linux / Mac - on Mint they stayed blank (Linux has no program
                            icons to ask for).
    2.2.17  02-Nov-2026     Claude: a drop that arrives without a file name (some Linux drag sources send none) no longer blanks the entry - it
                            says to paste the path instead.
    2.2.16  02-Nov-2026     Claude: a program's icon is pulled out when its path is typed or pasted too, not only when the program is dropped,
                            and Settings fills in the icons of entries that have a path but no icon (OK keeps them) - on Linux they stayed
                            blank.  file:// paths (Linux file managers paste and drop those) and quotes / braces / line ends around a
                            dropped path are cleaned up first.
    2.2.15  02-Nov-2026     Claude: Linux: dragging an entry in Settings no longer makes the whole window jump away from it.
    2.2.14  02-Nov-2026     Claude: Linux / Mac: the Brightness panel has square corners like the dock - only Windows can make corners see-through.
    2.2.13  02-Nov-2026     Claude: faster auto-scroll while dragging an entry in Settings - it was counted in screen pixels, so on a 200%
                            display it moved half as fast as meant; it now grows with the display scaling, and the top speed (pointer at the
                            very edge of the list) is a third higher.
    2.2.12  01-Nov-2026     Claude: right-click > Brightness... - a slider makes any theme darker (down to -80%) or lighter (+50%); the dock and
                            its Settings window follow. The dock changes as you drag; Done or Enter keeps it, Escape puts it back.
    2.2.11  01-Nov-2026     Claude: the 32 themes the new widgets use - 16 dark (colorful, like ForestFloor and CrimsonVelvet) and 16 light - in a
                            two-column Theme menu with a color chip beside each name. The title strip, heading gold and menu colors are worked out
                            from each theme. A theme saved by an older version carries over (Midnight is now Carbon).
    2.2.10  01-Nov-2026     Claude: finds the icon in programs that split it over several lines - b''.join((b'iVBOR...', b'...')) as
                            Player Coach and anything made by make_icons.py do; those got the Python logo. The pieces are joined back up.
    2.2.9   01-Nov-2026     Claude: Settings window no wider than its entries - the status bar showed the whole settings-file path, which made
                            the window wide; it now shows the file name, with the full path in its tooltip. Shorter hint line too.
    2.2.8   01-Nov-2026     Claude: the dock fills a column top to bottom (up to 10 rows) before starting the next one - a short list was being
                            spread over 3 columns of 2, which read left to right. Right-click > Columns: Auto (that), or always 1, 2 or 3.
    2.2.7   01-Nov-2026     Claude: the new widgets' look. The dock is one rounded card drawn with Pillow: a title strip (icon, name, version,
                            gear, x that turns red), rows with each program's icon, name and version, headings in gold, and a bottom line
                            that shows the path of the program under the mouse. A click launches - dragging the dock never does.
                            Right-click: Theme (now 32 - see 2.2.11), Size, Opacity (was Alpha 1-10), Keep on top - remembered.
                            The Settings window has the same title strip as the widgets' Settings and follows the theme. The crimson theme
                            is retired. Sharp on high-DPI displays (dpi aware; Settings pictures are enlarged to match). Linux / Mac:
                            square corners, as only Windows can make the corners see-through.
    2.2.6   01-Nov-2026     Claude: slower, steadier auto-scroll while dragging an entry near the top/bottom of the Settings list - it used to
                            jump a tenth of the list on every mouse movement; now it glides on a timer, faster the closer the pointer is to
                            the edge (about 2 entries a second at the very edge).
    2.2.5   01-Nov-2026     Claude: right-click menus compact and flat (bd=0, activeborderwidth=1) in the dock's own colours, sub-menus too -
                            tk drew the Alpha sub-menu Windows-gray.
    2.2.4   01-Nov-2026     Claude: Headings - "+ Heading" in Settings adds a heading entry (drag it into place like any entry); the dock shows
                            each heading as a gold label with a line under it above the programs that follow it, and never leaves a
                            heading alone at the bottom of a column. + Add / + Heading put the new entry above the first checked one
                            (or at the end), scroll to it and select its name. The check box moved up beside the trash can.
    2.2.3   31-Oct-2026     Claude: Refresh button removed from the title bar (Settings refreshes the dock itself; Refresh stays in the
                            right-click menu for the rare case of a program's version number changing on disk).
    2.2.2   31-Oct-2026     Claude: PSG Dock's own icon - three app tiles on a reflective shelf - beside the title and as the window / taskbar icon
                            of both windows (the old title image was the refresh arrows).
    2.2.1   31-Oct-2026     Claude: right-click menu broke after changing Alpha - the Alpha / Keep-on-top updates used fixed menu positions and
                            "Settings..." had shifted them; they now find their entries by name.
    2.2.0   31-Oct-2026     Claude: renamed PSG Dock (file psgdock.pyw). Settings move to psgdock_entries.json (the app list) and psgdock.json
                            (window settings) - both are copied from the old launcher2.json / MiniLauncher2.json the first time it runs.
    2.1.4   30-Oct-2026     Claude: a dragged entry could be slid off the top/bottom of the window and get stuck floating - the mouse-release
                            landed on the floating copy instead of the grip. The copy now stays inside the list, forwards its own
                            mouse events, and the drop always cleans up.

    Single file - the settings window (list of applications) is in the SETTINGS WINDOW section below.
    Drop an image file onto an entry in the settings window to use it as that entry's icon.
    Drop a program (.exe, .pyw, .lnk, ...) onto an entry and the path, name and icon are filled in from it.
    Drag an entry by its ☰ grip to change the order - it lifts out and floats with the mouse, the orange slot shows where it will land.
    Requires:  PySimpleGUI, pillow, psgdnd  (pip install psgdnd)

    Copyright 2026_PySimpleGUI
"""

version = '2.2.18'
APP_NAME = 'PSG Dock'
ENTRIES_FILENAME = 'psgdock_entries.json'                       # the list of programs (was launcher2.json)
WINDOW_SETTINGS_FILENAME = 'psgdock.json'                       # alpha, keep-on-top, window position (was MiniLauncher2.json, named after the old file)


def migrate_settings():
    """ First run after the rename: copy the old settings files to their new names so nothing is lost """
    import shutil
    for old, new in (('launcher2.json', ENTRIES_FILENAME), ('MiniLauncher2.json', WINDOW_SETTINGS_FILENAME)):
        old_path, new_path = sg.UserSettings(old).get_filename(), sg.UserSettings(new).get_filename()
        if os.path.exists(old_path) and not os.path.exists(new_path):
            shutil.copyfile(old_path, new_path)
__version__ = version.split()[0]


KIND_APP, KIND_HEADING = 'app', 'heading'                          # an entry is a program to launch, or a heading over the programs that follow it


class Block:
    active_blocks = {}  # type:  Dict[int, Block]
    def __init__(self, block_num, name, path, iconb64, kind=KIND_APP):
        self.block_num = block_num
        self.name = name
        self.path= path
        self.iconb64 = iconb64
        self.kind = kind

class G:
    right_click_menu = []
    block_number = 0
    launcher_settings : sg.UserSettings = None
    dirty = False                                       # True while the settings window has unsaved changes
    auto_icon = {}                                      # Settings: block number -> the path its icon was pulled from (a newly typed path may replace that icon)
    theme, size_name, opacity, on_top = 'Toybox', 'Medium', 90, False                   # right-click choices, saved in psgdock.json
    columns = 'Auto'                                    # right-click > Columns: 'Auto', '1', '2' or '3'
    scale = 1.0                                         # dock drawing scale = display scaling x Size
    dpi = 1.0                                           # display scaling (2.0 on a 200% Windows display)
    hover = None                                        # the part of the dock under the mouse: 'gear', 'close', ('app', block_num) or None
    press = None                                        # (x, y, part) of a mouse press on the dock - a click is a press + release that didn't move
    hits = []                                           # [(x0, y0, x1, y1, part)] in design pixels, filled by render()
    fonts = {}
    icon_cache = {}
    swatches = {}                                       # (theme name, brightness) -> PhotoImage of its chip in the Theme menu
    bright = 0                                          # Brightness: -80 (much darker) .. 50 (lighter), 0 = the theme as designed
    tuned = {}                                          # (theme name, brightness) -> the theme's colors at that brightness
    versions = {}                                       # block_num -> version found in the program's source



# Keys using tuples instead of strings... could migrate all keys to this format to make parsing much easier
K_CBOX = '-CBOX-'
K_B_CBOX = lambda num: (K_CBOX, num)
K_DEL = '-DELETE-'                              # Fixed part of key for block deletes
K_B_DEL = lambda num: (K_DEL, num)              # Block delete key

K_BUTTON = '-BUTTON-'
K_B_BUTTON = lambda num: (K_BUTTON, num)

K_SETTINGS = '-SETTINGS-'

K_KEEP_ON_TOP = '-keep on top-'
K_THEME = '-THEME-'                             # settings-file entry, and the prefix of the Theme menu keys
KT_THEME = lambda name: f'{K_THEME}{name}'
K_SIZE = '-SIZE-'
KT_SIZE = lambda name: f'{K_SIZE}{name}'
K_OPACITY = '-OPACITY-'
KT_OPACITY = lambda pct: f'{K_OPACITY}{pct}'
K_COLUMNS = '-COLUMNS-'
KT_COLUMNS = lambda choice: f'{K_COLUMNS}{choice}'
K_REFRESH = '-REFRESH-'
K_IMAGE = '-IMAGE-'                             # the dock is one Image the whole card is drawn into
K_HOVER = '-HOVER-'                             # the mouse moved onto another part of the dock, value = that part
K_CLICK = '-CLICK-'                             # a click (not a drag of the dock) on a part of the dock, value = that part


ICON_SIZE = (30,30)
NUM_COLUMNS = 3
AUTO_ROWS = 10                                  # Columns 'Auto': a column fills to this many rows before the next one starts
COLUMN_CHOICES = ('Auto', '1', '2', '3')

# ---------- Look: the themes the new card widgets share (right-click > Theme) ----------
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
C_HEADING, C_HEADING_LIGHT = '#e8a33d', '#8a5412'   # gold headings - a darker gold on light themes
C_SWATCH_EDGE = '#7c8594'                       # outline of the color chips in the Theme menu - mid gray shows on dark and light menus
C_SELECT = '#2a62a8'                            # menu highlight and the buttons
C_CHECKED = '#1e9bff'                           # outline of a checked entry in Settings
C_CLOSE = '#c0392b'                             # the x becomes a red disc under the mouse
SIZES = {'Small': 0.8, 'Medium': 1.0, 'Large': 1.3}
OPACITIES = (100, 90, 80, 70, 60)
FONT_MENU = ('Segoe UI', 10)
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # bold / regular: Windows first, then Linux
TRANSPARENT = '#010203'                         # Windows colour key: every pixel this colour is see-through and click-through (the rounded corners)
RADIUS, PAD, HEAD_H, FOOT_H = 18, 10, 42, 30    # dock geometry in design pixels (96 dpi, Medium size) - multiplied by the scale when drawn
COL_W, COL_GAP, ROW_H, ICON_PX = 232, 6, 34, 26
BTN_Y, BTN_R = 21, 11                           # gear and x: center height and click radius


def T():
    """ The colours of the chosen theme: the five every card widget shares, plus the dock's own worked out from them - title strip, headings, menu """
    t = theme_colors()                                                  # the theme at the Brightness setting
    light = is_light(t['card'])
    return dict(t, light=light, strip=mix_hex(t['card'], t['border'], 0.4 if light else 0.3), heading=C_HEADING_LIGHT if light else C_HEADING,
                menu=(mix_hex(t['card'], t['text'], 0.04), t['text']))


def is_light(color):
    """ True for a light colour ('#rrggbb') - a light theme gets dark text, a white input background and a darker gold """
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


def apply_theme():
    """ The chosen theme as the PySimpleGUI theme (Settings window, popups), and the Settings entry outline colours from it """
    global FRAME_BORDER_COLOR_NOT_SELECTED, FRAME_BORDER_COLOR_SELECTED, COLOR_DIRTY_TEXT
    t = T()
    light = t.get('light', False)
    sg.theme_add_new(f'PSGDock{G.theme}', {'BACKGROUND': t['card'], 'TEXT': mix_hex(t['text'], t['card'], 0.08), 'INPUT': '#ffffff' if light else t['track'], 'TEXT_INPUT': t['text'],
                                          'SCROLL': t['border'] if light else t['track'], 'BUTTON': ('#ffffff', C_SELECT), 'PROGRESS': (C_CHECKED, t['track']), 'BORDER': 1,
                                          'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
    sg.theme(f'PSGDock{G.theme}')
    FRAME_BORDER_COLOR_NOT_SELECTED, FRAME_BORDER_COLOR_SELECTED = t['border'], C_CHECKED
    COLOR_DIRTY_TEXT = '#9a6f00' if light else '#ffc107'                 # the gold 'unsaved' text needs to be darker on white


def menu_colors():
    bg, fg = T()['menu']
    return {'bg': bg, 'fg': fg, 'activebackground': C_SELECT, 'activeforeground': '#ffffff', 'font': FONT_MENU}


def make_menu():
    """ The dock's right-click menu, with check marks on the current choices """
    tick = lambda on: '✓ ' if on else '    '                          # every label starts with a tick or the same width of spaces, so they line up
    return ['', [f'    Settings...::{K_SETTINGS}', '---', f'{tick(G.on_top)}Keep on top::{K_KEEP_ON_TOP}',
                 '    Theme', [f'{tick(n == G.theme)}{n}::{KT_THEME(n)}' for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],   # dark, then light
                 f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
                 '    Size', [f'{tick(n == G.size_name)}{n}::{KT_SIZE(n)}' for n in SIZES],
                 '    Columns', [f'{tick(c == G.columns)}{c}::{KT_COLUMNS(c)}' for c in COLUMN_CHOICES],
                 '    Opacity', [f'{tick(p == G.opacity)}{p}%::{KT_OPACITY(p)}' for p in OPACITIES],
                 '---', f'    Refresh::{K_REFRESH}', '    Edit Me::Edit Me', '    Version::Version', '---', '    Exit::Exit']]


def set_right_click_menu(window:sg.Window, menu):
    for elem in window.element_list():
        elem.set_right_click_menu(menu, propogate_to_window=True)
    style_menus(window)


def style_menus(window:sg.Window):
    """ Compact, flat right-click menus (bd=0, activeborderwidth=1) in the theme's menu colours - sub-menus included, which tk would
        otherwise draw Windows-gray.  Run again after every set_right_click_menu() """
    tk = sg.tk
    colors = menu_colors()
    menus = {id(m): m for m in [window.TKRightClickMenu] + [e.TKRightClickMenu for e in window.element_list()] if m is not None}

    def style(menu):
        try:
            menu.configure(bd=0, relief='flat', activeborderwidth=1, **colors)
        except tk.TclError:                                             # a menu PySimpleGUI has already replaced and destroyed
            return
        first_light = True
        for i in range(menu.index('end') + 1 if menu.index('end') is not None else 0):      # Theme menu: a color chip beside each name, light ones in a 2nd column
            name = menu.entrycget(i, 'label').lstrip('✓ ') if menu.type(i) == 'command' else None
            if name in THEMES:
                menu.entryconfigure(i, image=theme_swatch(window, name), compound='left')
                if first_light and is_light(THEMES[name]['card']):
                    menu.entryconfigure(i, columnbreak=1)
                    first_light = False
        for child in menu.winfo_children():
            if isinstance(child, tk.Menu):
                style(child)

    for top in menus.values():
        style(top)


def theme_swatch(window, name):
    """ A little card in a theme's colours (card, a line of text, a dim line) beside its name in the Theme menu.  Made once and kept - tk drops images nobody holds """
    if (name, G.bright) not in G.swatches:                              # a set per Brightness level: the chips show what you'd get
        t, z = theme_colors(name), G.dpi * 4                            # drawn 4x and shrunk, so the edges are smooth
        im = Image.new('RGBA', (round(34 * z), round(20 * z)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=5 * z, fill=t['card'], outline=C_SWATCH_EDGE, width=round(z))
        d.rounded_rectangle((6 * z, 5.5 * z, 25 * z, 9 * z), radius=1.5 * z, fill=t['text'])
        d.rounded_rectangle((6 * z, 12 * z, 17 * z, 14.5 * z), radius=1.2 * z, fill=t['dim'])
        buf = io.BytesIO()
        im.resize((round(im.width / 4), round(im.height / 4)), Image.LANCZOS).save(buf, 'PNG')
        G.swatches[(name, G.bright)] = sg.tk.PhotoImage(master=window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.swatches[(name, G.bright)]


def load_blocks():
    Block.active_blocks = {}
    saved_blocks = G.launcher_settings.load()
    try:
        for key in saved_blocks.keys():
            if key[0] == K_NAME:
                # saved_block_num = int(key.replace('-NAME', '')[:-1])
                saved_block_num = key[1]
                block_num = G.block_number
                G.block_number += 1
                block = Block(block_num=block_num, name=saved_blocks[K_B_NAME(saved_block_num)], path=saved_blocks[K_B_PATH(saved_block_num)], iconb64=saved_blocks[K_B_ICON64(saved_block_num)],
                              kind=saved_blocks.get(K_B_KIND(saved_block_num), KIND_APP))
                Block.active_blocks[block_num] = block
    except Exception as e:
        sg.popup_error_with_traceback('Error loading saved blocks', e)

def get_version(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines =f.readlines()
            for line in lines:
                line = line.strip()
                m = re.search(r'version\s*=\s*["\'](\d+(?:\.\d+)*)["\']', line)
                if m:
                    return m.group(1)
            return ''
    except Exception as e:
        return ''



def resize_canvas_no_distort_b64(b64_png: str, target_size=ICON_SIZE, fill_color=(0, 0, 0, 0)):
    """
    Decodes a base64 PNG string, pads it onto a target_size canvas without
    resizing/distorting the original image, and returns both the PIL Image
    and a new base64-encoded PNG string.
    """
    img_bytes = base64.b64decode(b64_png)
    img = Image.open(io.BytesIO(img_bytes))

    if img.mode != 'RGBA' and len(fill_color) == 4:
        img = img.convert('RGBA')

    target_w, target_h = target_size
    new_img = Image.new(img.mode, (target_w, target_h), fill_color)

    paste_x = (target_w - img.width) // 2
    paste_y = (target_h - img.height) // 2
    new_img.paste(img, (paste_x, paste_y))

    buffer = io.BytesIO()
    new_img.save(buffer, format='PNG')
    new_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return new_b64



def encode_image_base64(pil_image=None):
    """
    takes either a fjlename or a PIL image.  Image is converted
    to a base64 encoded PNG

    :param pil_image:      PIL Image object.
    :type pil_image:       PIL.Image.Image
    :return:               The base64-encoded PNG bytes of the image.
    :rtype:                bytes
    """
    # Always encode as PNG in memory
    with io.BytesIO() as bio:
        pil_image.save(bio, format="PNG")
        contents = bio.getvalue()
        encoded = base64.b64encode(contents)

    return encoded


#  ███████╗███████╗████████╗████████╗██╗███╗   ██╗ ██████╗ ███████╗    ██╗    ██╗██╗███╗   ██╗██████╗  ██████╗ ██╗    ██╗
#  ██╔════╝██╔════╝╚══██╔══╝╚══██╔══╝██║████╗  ██║██╔════╝ ██╔════╝    ██║    ██║██║████╗  ██║██╔══██╗██╔═══██╗██║    ██║
#  ███████╗█████╗     ██║      ██║   ██║██╔██╗ ██║██║  ███╗███████╗    ██║ █╗ ██║██║██╔██╗ ██║██║  ██║██║   ██║██║ █╗ ██║
#  ╚════██║██╔══╝     ██║      ██║   ██║██║╚██╗██║██║   ██║╚════██║    ██║███╗██║██║██║╚██╗██║██║  ██║██║   ██║██║███╗██║
#  ███████║███████╗   ██║      ██║   ██║██║ ╚████║╚██████╔╝███████║    ╚███╔███╔╝██║██║ ╚████║██████╔╝╚██████╔╝╚███╔███╔╝
#  ╚══════╝╚══════╝   ╚═╝      ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚══╝╚══╝
#
#   The settings window - a scrollable list of "blocks", one per application, each with name / path / base64 icon.
#   Toolbar:   + Add  − Delete | ▲ Up  ▼ Down | ☑ All  ☐ None ......... Save  Reload  Clear all
#   Drop an image file anywhere on a block to make it that entry's icon (fitted to ICON_SIZE, stored as base64 PNG).
#   Keys:  Up/Down = move checked     PgUp/PgDn = scroll a page     Home/End = top/bottom     Ctrl+S = save     Escape = close

SCROLLABLE_COLUMN_SIZE = (None, 800)
FRAME_BORDER_COLOR_NOT_SELECTED = 'gray30'
FRAME_BORDER_COLOR_SELECTED = 'chartreuse'
DRAG_SOURCE_COLOR = '#1E88E5'                                                   # the entry being dragged
DRAG_TARGET_COLOR = '#FFA726'                                                   # outline of the floating copy while dragging


def blend(color, toward, amount):
    """ Mix a colour toward another ('#rrggbb' or a tk colour name) - used to derive the drop-slot shade from the theme background """
    import tkinter as tk
    root = tk._default_root
    def rgb(c):
        r, g, b = root.winfo_rgb(c)
        return r // 256, g // 256, b // 256
    a, b = rgb(color), rgb(toward)
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def slot_colors():
    """ (fill, outline) for the drop slot: a lighter shade of the theme background, outlined faintly in the theme's text colour """
    bg = sg.theme_background_color()
    return blend(bg, 'black' if T().get('light') else 'white', 0.07 if T().get('light') else 0.18), blend(bg, sg.theme_text_color(), 0.45)
DRAG_START = 6                                                                  # pixels the mouse moves before a press on the grip becomes a drag
AUTOSCROLL_EDGE = 40                                                            # dragging within this many pixels of the list's top/bottom scrolls it
AUTOSCROLL_MS = 30                                                              # auto-scroll tick while the pointer is in that edge zone
AUTOSCROLL_MIN_PX, AUTOSCROLL_MAX_PX = 1, 8                                     # pixels per tick - slow just inside the zone, fastest at the very edge
                                                                                # (all three in 96-dpi pixels - multiplied by the display scaling, G.dpi)
FILENAME_INPUT_LENGTH = 80

# Toolbar colours - green = safe/save, gold = unsaved changes, red = destructive
COLOR_SAVE = 'white on #2e7d32'
COLOR_SAVE_DIRTY = 'black on #ffc107'
COLOR_DANGER = 'white on #b71c1c'
COLOR_DIRTY_TEXT = '#ffc107'

# Keys saved in the settings file (one set per application, numbered)
K_BLOCK = '-BLOCK-'
K_B_BLOCK = lambda num: (K_BLOCK, num)
K_ICON64 = '-ICON64-'
K_B_ICON64 = lambda num:  (K_ICON64, num)
K_ICON = '-ICON-'
K_B_ICON = lambda num: (K_ICON, num)
K_NAME = '-NAME-'
K_B_NAME = lambda num:  (K_NAME, num)
K_PATH = '-PATH-'
K_B_PATH = lambda num: (K_PATH, num)
K_KIND = '-KIND-'                               # saved: 'app' or 'heading' (missing = app, so older settings files load unchanged)
K_B_KIND = lambda num: (K_KIND, num)
K_DETAILS = '-DETAILS-'                         # the path + icon rows of an entry - hidden for a heading
K_B_DETAILS = lambda num: (K_DETAILS, num)
K_COLUMN = '-COLUMN-'
K_B_COLUMN = lambda num: (K_COLUMN, num)        # Column elem containing the block's elements. Not used

# Settings window keys
K_ALL_COLS = '-ALL COLS-'
K_MOVE_UP = '-MOVE UP-'
K_MOVE_DOWN = '-MOVE DOWN-'
K_PAGE_UP = '-PAGE UP-'
K_PAGE_DOWN = '-PAGE DOWN-'
K_HOME = '-HOME-'
K_END = '-END-'
K_ESCAPE = '-ESCAPE-'
K_OK = '-OK-'
K_APPLY = '-APPLY-'
K_CANCEL = '-CANCEL-'
K_SEL_ALL = '-SELECT ALL-'
K_ADD_HEADING = '-ADD HEADING-'
K_SEL_NONE = '-SELECT NONE-'
K_STATUS = '-STATUS-'
K_GRIP = '-GRIP-'                               # the ☰ drag handle on each block
K_B_GRIP = lambda num: (K_GRIP, num)
K_DRAG_PRESS = '-DRAG PRESS-'                   # events from the grip's mouse bindings, value = (block_num, x_root, y_root)
K_DRAG_MOTION = '-DRAG MOTION-'
K_DRAG_RELEASE = '-DRAG RELEASE-'


def image_to_icon_b64(img, size=ICON_SIZE) -> str:
    """ Fit a PIL image into a size x size transparent PNG (aspect kept, centered) and return its base64 as the b'...' string the
        Base64 PNG Icon field expects (same format as the saved settings) """
    img = img.convert('RGBA')
    img.thumbnail(size, Image.LANCZOS)
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    canvas.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2), img)
    with io.BytesIO() as bio:
        canvas.save(bio, format='PNG')
        return repr(base64.b64encode(bio.getvalue()))


def image_file_to_icon_b64(filename, size=ICON_SIZE) -> str:
    """ Load an image file and return it as a fitted base64 PNG icon string """
    return image_to_icon_b64(Image.open(filename), size)


IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.tif', '.tiff')


# ------------------------------------------------------------ Getting an icon out of a program ------------------------------------------------------------

PNG_START = re.compile(r"""b(['"])iVBORw0KGgo""")                  # where a base64 PNG literal begins
B64_PIECE = re.compile(r"""b(['"])([A-Za-z0-9+/=\s]*)\1""")       # one bytes literal of base64
PIECE_GAP = re.compile(r"""(?:[\s,]|#[^\n]*)*""")                  # what may sit between the pieces of a split icon


def base64_pngs_in_source(source):
    """ (position, base64) for every PNG in the source written as a bytes literal - on one line, or split over several lines the way
        icon makers write them:  b''.join((b'iVBOR...', b'...'))  or  (b'iVBOR...' b'...').  The pieces are joined while only whitespace,
        commas and comments sit between them; a piece that starts with a new PNG header starts a new image """
    found = []
    for m in PNG_START.finditer(source):
        pieces, pos = [], m.start()
        while True:
            piece = B64_PIECE.match(source, pos)
            if not piece:
                break
            pieces.append(piece.group(2))
            pos = PIECE_GAP.match(source, piece.end()).end()
            if not source.startswith(('b"', "b'"), pos) or PNG_START.match(source, pos):
                break
        found.append((m.start(), ''.join(''.join(pieces).split())))
        if len(found) >= 40:
            break
    return found


def icon_from_python_source(filename):
    """ PySimpleGUI programs usually carry their icon as a base64 PNG in the source (window_icon(), launcher_icon = b'...', etc).
        Returns the first one found as a PIL image (one whose name mentions "icon" is preferred), or None """
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except Exception:
        return None
    widget_words = ('trash', 'arrow', 'refresh', 'blank', 'button', 'check', 'close', 'cursor')      # small images that are toolbar bits, not the program's icon
    best, best_score = None, None
    for start, b64 in base64_pngs_in_source(source):
        before = source[max(0, start - 60):start].lower()
        line_start = source.rfind('\n', 0, start) + 1
        if not source[line_start:start].strip():                       # a split icon's pieces start their own lines - its name is on the line above
            before = source[source.rfind('\n', 0, max(0, line_start - 1)) + 1:line_start].lower() + before
        try:
            img = Image.open(io.BytesIO(base64.b64decode(b64)))
            img.load()
        except Exception:
            continue
        score = ('icon' in before and not any(w in before for w in widget_words), img.width * img.height)      # icon-named first, then the biggest
        if best_score is None or score > best_score:
            best, best_score = img, score
    return best


def resolve_shortcut(filename):
    """ Path a Windows .lnk shortcut points at (via the shell if pywin32 is installed, else a minimal parse of the .lnk file). Returns the .lnk itself if it can't be resolved """
    try:
        import win32com.client                                  # pywin32 - optional
        target = win32com.client.Dispatch('WScript.Shell').CreateShortCut(filename).TargetPath
        if target and os.path.exists(target):
            return target
    except Exception:
        pass
    try:                                                        # minimal .lnk parse: LinkInfo -> LocalBasePath   (MS-SHLLINK)
        with open(filename, 'rb') as f:
            data = f.read()
        flags = struct.unpack_from('<I', data, 0x14)[0]
        pos = 0x4C
        if flags & 0x01:                                        # HasLinkTargetIDList
            pos += 2 + struct.unpack_from('<H', data, pos)[0]
        if flags & 0x02:                                        # HasLinkInfo
            link_info_size, header_size, link_flags = struct.unpack_from('<III', data, pos)
            if link_flags & 0x01:                               # VolumeIDAndLocalBasePath
                if header_size >= 0x24:                         # unicode path offset present
                    off = struct.unpack_from('<I', data, pos + 0x1C)[0]
                    end = data.index(b'\x00\x00', pos + off)
                    end += (end - pos - off) % 2
                    target = data[pos + off:end].decode('utf-16-le', errors='ignore')
                else:
                    off = struct.unpack_from('<I', data, pos + 0x10)[0]
                    target = data[pos + off:data.index(b'\x00', pos + off)].decode('mbcs' if sys.platform == 'win32' else 'latin-1', errors='ignore')
                if target and os.path.exists(target):
                    return target
    except Exception:
        pass
    return filename


def hicon_to_image(hicon):
    """ Windows HICON -> PIL RGBA image (alpha kept), ctypes only.  Returns None if anything goes wrong """
    import ctypes
    from ctypes import wintypes
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32

    class ICONINFO(ctypes.Structure):
        _fields_ = [('fIcon', wintypes.BOOL), ('xHotspot', wintypes.DWORD), ('yHotspot', wintypes.DWORD), ('hbmMask', wintypes.HBITMAP), ('hbmColor', wintypes.HBITMAP)]

    class BITMAP(ctypes.Structure):
        _fields_ = [('bmType', wintypes.LONG), ('bmWidth', wintypes.LONG), ('bmHeight', wintypes.LONG), ('bmWidthBytes', wintypes.LONG), ('bmPlanes', wintypes.WORD), ('bmBitsPixel', wintypes.WORD), ('bmBits', wintypes.LPVOID)]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG), ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG), ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wintypes.DWORD * 3)]

    user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(ICONINFO)]
    user32.GetDC.restype = wintypes.HDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi32.GetObjectW.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID]
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, wintypes.LPVOID, ctypes.POINTER(BITMAPINFO), wintypes.UINT]
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]

    def bitmap_pixels(hbitmap):
        """ 32-bit BGRA pixels of a bitmap, top-down.  Returns (width, height, bytes) """
        bm = BITMAP()
        gdi32.GetObjectW(hbitmap, ctypes.sizeof(BITMAP), ctypes.pointer(bm))
        w, h = bm.bmWidth, bm.bmHeight
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth, bmi.bmiHeader.biHeight, bmi.bmiHeader.biPlanes, bmi.bmiHeader.biBitCount, bmi.bmiHeader.biCompression = w, -h, 1, 32, 0
        buf = ctypes.create_string_buffer(w * h * 4)
        hdc = user32.GetDC(None)
        try:
            lines = gdi32.GetDIBits(hdc, hbitmap, 0, h, buf, ctypes.byref(bmi), 0)
        finally:
            user32.ReleaseDC(None, hdc)
        return (w, h, buf.raw) if lines else (0, 0, b'')

    info = ICONINFO()
    if not user32.GetIconInfo(hicon, ctypes.byref(info)):
        return None
    try:
        if not info.hbmColor:
            return None
        w, h, pixels = bitmap_pixels(info.hbmColor)
        if not w:
            return None
        img = Image.frombuffer('RGBA', (w, h), pixels, 'raw', 'BGRA', 0, 1).copy()
        if not any(img.getdata(band=3)):                        # no alpha channel in this icon -> build it from the AND mask (white = transparent)
            mw, mh, mpixels = bitmap_pixels(info.hbmMask)
            if mw == w and mh >= h:
                mask = Image.frombuffer('L', (w, h), mpixels[:w * h * 4:4], 'raw', 'L', 0, 1).point(lambda v: 0 if v else 255)
                img.putalpha(mask)
        return img
    finally:
        gdi32.DeleteObject(info.hbmColor)
        gdi32.DeleteObject(info.hbmMask)


def shell_icon_image(filename):
    """ The icon Windows Explorer shows for a file (exe, document, shortcut...) as a PIL image, or None """
    if sys.platform != 'win32':
        return None
    import ctypes
    from ctypes import wintypes

    class SHFILEINFOW(ctypes.Structure):
        _fields_ = [('hIcon', wintypes.HICON), ('iIcon', ctypes.c_int), ('dwAttributes', wintypes.DWORD), ('szDisplayName', wintypes.WCHAR * 260), ('szTypeName', wintypes.WCHAR * 80)]

    SHGFI_ICON, SHGFI_LARGEICON = 0x100, 0x0
    shell32, user32 = ctypes.windll.shell32, ctypes.windll.user32
    shell32.SHGetFileInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(SHFILEINFOW), wintypes.UINT, wintypes.UINT]
    shell32.SHGetFileInfoW.restype = ctypes.c_void_p
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    ctypes.windll.ole32.CoInitialize(None)                      # shortcuts need COM
    info = SHFILEINFOW()
    if not shell32.SHGetFileInfoW(filename, 0, ctypes.byref(info), ctypes.sizeof(info), SHGFI_ICON | SHGFI_LARGEICON) or not info.hIcon:
        return None
    try:
        return hicon_to_image(info.hIcon)
    finally:
        user32.DestroyIcon(info.hIcon)


def playground_catalog_icon(filename):
    """ A PySimpleGUI Playground program: its icon from the Playground's catalog.json and icons folder (a few folders up), or None """
    folder = os.path.dirname(os.path.abspath(filename))
    for _ in range(4):
        catalog = os.path.join(folder, 'catalog.json')
        if os.path.isfile(catalog):
            try:
                with open(catalog, encoding='utf-8') as f:
                    apps = json.load(f).get('apps', [])
                name = os.path.basename(filename).lower()
                app = next((a for a in apps if (a.get('file') or '').lower() == name and a.get('icon')), None)
                if app:
                    img = Image.open(os.path.join(folder, 'icons', app['icon']))
                    img.load()
                    return img
            except Exception:
                pass
            return None
        folder, below = os.path.dirname(folder), folder
        if folder == below:
            break
    return None


def icon_file_beside(filename):
    """ A picture next to the program named after it: x.png, x_icon.png, x.ico or x_icon.ico for x.pyw """
    stem = os.path.splitext(filename)[0]
    for candidate in (stem + '.png', stem + '_icon.png', stem + '.ico', stem + '_icon.ico'):
        if os.path.isfile(candidate):
            try:
                img = Image.open(candidate)
                img.load()
                return img
            except Exception:
                pass
    return None


def program_icon_image(filename):
    """ Best icon for a program file as a PIL image, or None.
        .py/.pyw -> a base64 PNG embedded in the source, else its icon in the Playground's catalog, else a picture beside it named after it, else
                    the Python interpreter's icon (Windows) or PySimpleGUI's (Linux / Mac have no program icons to ask the system for).
        .lnk -> the target's icon.   else -> the shell icon """
    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.py', '.pyw'):
        for find in (icon_from_python_source, playground_catalog_icon, icon_file_beside):
            img = find(filename)
            if img is not None:
                return img
        if sys.platform == 'win32':
            return shell_icon_image(sys.executable)
        return Image.open(io.BytesIO(base64.b64decode(sg.DEFAULT_BASE64_ICON)))
    return shell_icon_image(filename)


def clean_path(text):
    """ A path as typed, pasted or dropped: spaces, quotes and braces off its ends; a file:// URI (Linux file managers paste and drop those)
        made into a plain path """
    path = text.strip().strip('"\'{}').strip()
    if path.lower().startswith('file://'):
        path = urllib.parse.unquote(urllib.parse.urlparse(path).path)
        if sys.platform == 'win32' and re.match(r'/[A-Za-z]:', path):                  # file:///C:/x.pyw -> C:/x.pyw
            path = path[1:]
    return path


def icon_for_typed_path(window:sg.Window, block_num, text):
    """ A path typed or pasted into an entry (or one already saved without an icon): once it names a program that exists, the path is cleaned up,
        the name filled in if it's empty and the program's icon pulled out - what a drop does.  An icon you dropped, pasted or saved yourself is
        kept; one pulled from an earlier path is replaced.  Returns True when an icon was put in """
    block = Block.active_blocks[block_num]
    path = clean_path(text)
    if os.path.splitext(path)[1].lower() == '.lnk':
        path = resolve_shortcut(path)
    if not os.path.isfile(path) or os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS:
        return False
    if path != text:
        window[K_B_PATH(block_num)].update(path)
    block.path = path
    if not block.name.strip():
        block.name = os.path.splitext(os.path.basename(path))[0].replace('_', ' ')
        window[K_B_NAME(block_num)].update(block.name)
    if (block.iconb64.strip() and block_num not in G.auto_icon) or G.auto_icon.get(block_num) == path:
        return False
    try:
        img = program_icon_image(path)
    except Exception:
        img = None
    if img is None:
        return False
    icon_string = image_to_icon_b64(img)
    window[K_B_ICON64(block_num)].update(icon_string)
    window[K_B_ICON(block_num)].update(data=ui_icon(ast.literal_eval(icon_string)))
    block.iconb64 = icon_string
    G.auto_icon[block_num] = path
    return True


def fill_block_from_dropped_file(window:sg.Window, block_num, filename):
    """ A file was dropped on a block.  Image -> just the icon.  Program -> path, name (if empty) and the program's icon. """
    block = Block.active_blocks[block_num]
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        icon_string = image_file_to_icon_b64(filename)
        G.auto_icon.pop(block_num, None)                        # a picture you chose - a path typed later won't replace it
    else:
        if ext == '.lnk':
            filename = resolve_shortcut(filename)
        block.path = filename
        window[K_B_PATH(block_num)].update(filename)
        if not block.name.strip():
            block.name = os.path.splitext(os.path.basename(filename))[0].replace('_', ' ')
            window[K_B_NAME(block_num)].update(block.name)
        try:
            img = program_icon_image(filename)
        except Exception as e:
            print(f'Icon extraction failed for {filename}: {e}')
            img = None
        if img is None:
            return                                              # path/name are filled in - the icon can still be dropped or pasted
        icon_string = image_to_icon_b64(img)
        G.auto_icon[block_num] = filename
    window[K_B_ICON64(block_num)].update(icon_string)
    window[K_B_ICON(block_num)].update(data=ui_icon(ast.literal_eval(icon_string)))
    block.iconb64 = icon_string


# ------------------------------------------------------------ Blocks (one per application) ------------------------------------------------------------

def make_a_block(image=None) -> sg.Frame:
    block_num = G.block_number
    Block.active_blocks[G.block_number] = Block(block_num=G.block_number, name='', path='', iconb64='')
    G.block_number += 1

    block_layout = [[sg.T('☰', k=K_B_GRIP(block_num), font='_ 14', text_color=T()['dim'], p=((2, 6), 0), tooltip='Drag to change the order'), sg.Image(data=image, k=K_B_ICON(block_num), enable_events=True, p=0, tooltip='Drop the program here (path, name and icon fill in) or an image file (icon only)'), sg.Push(), sg.Input(k=K_B_NAME(block_num), justification='c',enable_events=True, placeholder='Application name', placeholder_justification='c', placeholder_background_color=sg.theme_input_background_color(), font='_ 12 bold', s=FILENAME_INPUT_LENGTH-20, p=0), sg.Checkbox('', k=K_B_CBOX(block_num), enable_events=True, tooltip='Check to delete, or to choose where + Add / + Heading put the new entry'), sg.B(image_source=ui_icon(trash), mouseover_image_source=ui_icon(trash_red), button_color=f'red on {sg.theme_background_color()}', border_width=0, k=K_B_DEL(block_num), tooltip='Delete this entry')],
                   [sg.pin(sg.Column([[sg.Input(k=K_B_PATH(block_num), justification='r', enable_events=True,  placeholder='Path to application', placeholder_background_color=sg.theme_input_background_color(), placeholder_justification='c', p=0, s=FILENAME_INPUT_LENGTH)],
                                      [sg.Input(k=K_B_ICON64(block_num), justification='r', change_submits=True, placeholder='Base64 PNG Icon   (or drop the program / an image file on this entry)', placeholder_justification='c', placeholder_background_color=sg.theme_input_background_color(), p=0, s=FILENAME_INPUT_LENGTH)]], k=K_B_DETAILS(block_num), pad=0), shrink=True)],
                    ]

    block =sg.Frame('', [[sg.Column(block_layout, k=K_B_COLUMN(block_num), expand_x=False, pad=0 )]], k=K_B_BLOCK(block_num), border_width_no_relief=3, border_color=FRAME_BORDER_COLOR_NOT_SELECTED, expand_x=True, p=0)
    return block


def add_block(window):
    window.extend_layout(window[K_ALL_COLS], [[make_a_block()]])
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()
    block_num = G.block_number - 1
    for key in (K_B_BLOCK(block_num), K_B_ICON(block_num), K_B_ICON64(block_num)):          # drop an image file anywhere on the block
        psgdnd.register_element_dnd(window[key], window, psgdnd.DROP_TYPE_FILES)
    grip = window[K_B_GRIP(block_num)].Widget
    def grip_event(key, n):                                # 'break' stops the window's grab_anywhere binding from also dragging the window
        def handler(e):
            window.write_event_value(key, (n, e.x_root, e.y_root))
            return 'break'
        return handler
    grip.bind('<ButtonPress-1>', grip_event(K_DRAG_PRESS, block_num))
    grip.bind('<B1-Motion>', grip_event(K_DRAG_MOTION, block_num))
    grip.bind('<ButtonRelease-1>', grip_event(K_DRAG_RELEASE, block_num))
    grip.configure(cursor='hand2')

    return  block_num


def del_block(window, block_num):
    try:
        block_to_delete = int(block_num)
        key_to_delete = K_B_BLOCK(block_to_delete)
    except Exception:
        return None
    if key_to_delete in window.key_dict.keys():
        del_an_elem(window, window[key_to_delete])
        window.refresh()
        window[K_ALL_COLS].contents_changed()
    try:
        del Block.active_blocks[block_to_delete]
    except Exception as e:
        sg.popup_error_with_traceback(f'Error deleting block {block_to_delete}', e)

    return key_to_delete


def del_all_blocks(window:sg.Window):
    for key in list(Block.active_blocks.keys()):
        del_block(window, key)


def del_checked_blocks(window:sg.Window):
    for key in list(Block.active_blocks.keys()):
        if window[K_B_CBOX(key)].get():
            del_block(window, key)


def check_all_blocks(window:sg.Window, checked):
    for key in Block.active_blocks:
        window[K_B_CBOX(key)].update(checked)
        set_block_border(window, key)


def num_checked_blocks(window:sg.Window):
    return sum(1 for key in Block.active_blocks if window[K_B_CBOX(key)].get())


def update_status(window:sg.Window):
    """ Refresh the status bar and the Save button colour (gold = unsaved changes) """
    headings = sum(1 for b in Block.active_blocks.values() if b.kind == KIND_HEADING)
    num = len(Block.active_blocks) - headings
    state = 'UNSAVED CHANGES' if G.dirty else 'saved'
    window[K_STATUS].update(f'{num} application{"s" if num != 1 else ""}  ·  {headings} heading{"s" if headings != 1 else ""}  ·  {num_checked_blocks(window)} checked  ·  {state}',
                            text_color=COLOR_DIRTY_TEXT if G.dirty else sg.theme_text_color())
    window[K_APPLY].update(button_color=COLOR_SAVE_DIRTY if G.dirty else sg.theme_button_color())


def name_style(elem:sg.Input, heading):
    """ (text colour, background colour, font) for an entry's name field - a heading's is left-aligned, theme-coloured text on the window
        background so it reads as a heading.  Also sets the field's placeholder text and justification to match. """
    if not hasattr(elem, 'app_style'):                                  # remember how an application entry's name field looks, to switch back
        elem.app_style = (elem.placeholder, elem.TextColor, elem.BackgroundColor, elem.tk_justify, elem.Widget.cget('font'))
    placeholder, text_color, background_color, justify, font = elem.app_style
    if heading:                                                         # same font and width, so the check boxes and trash cans stay lined up
        placeholder, text_color, background_color, justify = 'Heading name', T()['heading'], sg.theme_background_color(), 'left'
    elem.placeholder, elem.tk_justify = placeholder, justify
    return text_color, background_color, font


def update_block_elements(window:sg.Window, b:Block):
    heading = b.kind == KIND_HEADING
    name_elem = window[K_B_NAME(b.block_num)]
    text_color, background_color, font = name_style(name_elem, heading)
    name_elem.update(b.name, text_color=text_color, background_color=background_color, font=font)
    window[K_B_DETAILS(b.block_num)].update(visible=not heading)        # a heading has no path or icon
    window[K_B_PATH(b.block_num)].update(b.path)
    window[K_B_ICON64(b.block_num)].update(b.iconb64)
    try:
        base64_icon = ast.literal_eval(b.iconb64) if b.iconb64 else None
    except:
        base64_icon = None
    if heading or base64_icon is None:
        base64_icon = blank_image_30x30                                 # an empty 30x30 keeps a heading's (or an icon-less program's) row as wide as the others
    window[K_B_ICON(b.block_num)].update(ui_icon(base64_icon))


def move_blocks(window:sg.Window, move_up=True):
    block_keys_to_move = [key for key in Block.active_blocks.keys() if window[K_B_CBOX(key)].get()]
    prev_key = None
    keys = Block.active_blocks.keys() if move_up else reversed(Block.active_blocks.keys())
    for key in keys:
        value = Block.active_blocks[key]
        if key in block_keys_to_move:
            if prev_key is not None:            # if can move higher
                b = Block.active_blocks[prev_key]
                prev_cb = window[K_B_CBOX(prev_key)].get()
                # Swap the blocks values except for the block number (this will automatically renumber the items)
                b.name, value.name = value.name, b.name
                b.path, value.path = value.path, b.path
                b.iconb64, value.iconb64 = value.iconb64, b.iconb64
                update_block_elements(window, b)
                update_block_elements(window, value)
                window[K_B_CBOX(b.block_num)].update(True)                # Set checkbox on the item moved up
                window[K_B_CBOX(value.block_num)].update(prev_cb)         # Copy over the checkbox value when moving
                prev_key = value.block_num
        else:
            prev_key = key
    first_checked_block_position = None
    last_checked_blocked_position = None
    for position, key in enumerate(Block.active_blocks.keys()):
        block_num = Block.active_blocks[key].block_num
        if window[K_B_CBOX(block_num)].get():
            window[K_B_BLOCK(block_num)].update(border_color=FRAME_BORDER_COLOR_SELECTED)
            if first_checked_block_position is None:
                last_checked_blocked_position = position
            first_checked_block_position = position
        else:
            window[K_B_BLOCK(block_num)].update(border_color=FRAME_BORDER_COLOR_NOT_SELECTED)

    if last_checked_blocked_position is not None:
        desired_visible_area_start = last_checked_blocked_position/len(Block.active_blocks.keys())
        top_fraction, bottom_fraction = window[K_ALL_COLS].widget.canvas.yview()
        if not top_fraction < desired_visible_area_start < bottom_fraction:
            window[K_ALL_COLS].set_vscroll_position(desired_visible_area_start)

    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()


# ------------------------------------------------------------ Settings window load / save ------------------------------------------------------------

# ------------------------------------------------------------ Drag to reorder ------------------------------------------------------------

def drag_lift(window:sg.Window, drag, y_root):
    """ The press has become a drag: lift the entry out of the list as a floating copy that follows the mouse, and leave an orange slot where it was """
    tk = sg.tk
    src_row = window[K_B_BLOCK(drag['src'])].Widget.master                  # the row frame PySimpleGUI packed the block into
    parent = src_row.master
    siblings = parent.pack_slaves()
    drag['row'], drag['parent'] = src_row, parent
    drag['next_row'] = siblings[siblings.index(src_row) + 1] if siblings.index(src_row) + 1 < len(siblings) else None
    info = src_row.pack_info()
    info.pop('in', None)
    drag['pack_info'] = info
    drag['pads'] = {'padx': info.get('padx', 0), 'pady': info.get('pady', 0)}
    w, h = src_row.winfo_width(), src_row.winfo_height()
    drag['grab_dy'] = y_root - src_row.winfo_rooty()
    drag['x'] = src_row.winfo_rootx()
    fill, outline = slot_colors()
    gap = tk.Frame(parent, width=w, height=h, bg=fill, highlightthickness=2, highlightbackground=outline, highlightcolor=outline)      # the slot the entry will land in - starts where it was
    gap.pack_propagate(False)
    gap.pack(before=src_row, fill='x', **drag['pads'])
    window.grab_any_where_off()                                             # the window stays put while an entry is dragged (back on at the drop)
    src_row.pack_forget()
    drag['gap'], drag['index'] = gap, None
    b = Block.active_blocks[drag['src']]
    top = tk.Toplevel(window.TKroot)                                        # the floating copy
    top.overrideredirect(True)
    top.attributes('-topmost', True)
    try:
        top.attributes('-alpha', 0.9)
    except tk.TclError:
        pass
    icon = window[K_B_ICON(drag['src'])].Widget.cget('image')
    bg, fg, field_bg, field_fg = sg.theme_background_color(), sg.theme_text_color(), sg.theme_input_background_color(), sg.theme_input_text_color()
    body = tk.Frame(top, bg=bg, highlightthickness=3, highlightbackground=DRAG_TARGET_COLOR, highlightcolor=DRAG_TARGET_COLOR)      # a replica of the entry with an orange outline
    body.pack(fill='both', expand=True)
    row1 = tk.Frame(body, bg=bg)
    row1.pack(fill='x', padx=4, pady=(3, 0))
    (tk.Label(row1, image=icon, bg=bg, width=round(30 * G.dpi), height=round(30 * G.dpi)) if icon else tk.Label(row1, text='   ', bg=bg)).pack(side='left')      # pixels with an image, characters without
    if b.kind == KIND_HEADING:                                              # a heading: just its name, styled like it is in the list
        tk.Label(row1, text=b.name.strip() or '(heading)', bg=bg, fg=fg, font=('Helvetica', 12, 'bold'), anchor='w').pack(side='left', fill='x', expand=True, padx=(8, 0), pady=(0, 3))
    else:
        tk.Label(row1, text=b.name.strip() or '(no name)', bg=field_bg, fg=field_fg, font=('Helvetica', 12, 'bold')).pack(side='left', fill='x', expand=True, padx=(8, 0))
        tk.Label(body, text=b.path, bg=field_bg, fg=field_fg, anchor='e', font=('Helvetica', 9)).pack(fill='x', padx=4, pady=2)
        tk.Label(body, text=(b.iconb64[:90] + '…') if len(b.iconb64) > 90 else (b.iconb64 or 'Base64 PNG Icon'), bg=field_bg, fg=field_fg, anchor='w', font=('Helvetica', 9)).pack(fill='x', padx=4, pady=(0, 3))
    top.update_idletasks()
    top.geometry(f'{w}x{body.winfo_reqheight()}+{drag["x"]}+{y_root - drag["grab_dy"]}')       # as wide as the entry, as tall as the replica needs
    drag['top'] = top
    n = drag['src']                                                         # the copy sits under the pointer, so it may get the mouse events instead of the grip
    top.bind('<B1-Motion>', lambda e: window.write_event_value(K_DRAG_MOTION, (n, e.x_root, e.y_root)))
    top.bind('<ButtonRelease-1>', lambda e: window.write_event_value(K_DRAG_RELEASE, (n, e.x_root, e.y_root)))
    try:                                                                    # Linux: unmapping the grip's row ended its hold on the mouse, so the moves went to the
        top.update()                                                        # window instead (it jumped away, and the drop was lost) - the copy takes every mouse event
        top.grab_set()
    except tk.TclError:
        pass
    window.set_cursor('fleur')
    drag_motion(window, drag, drag['x'], y_root)


def drag_motion(window:sg.Window, drag, x_root, y_root):
    """ Every mouse movement while the grip is held: move the floating copy, move the slot to where the entry would land, scroll near the edges """
    if not drag['moved']:
        if abs(y_root - drag['y']) < DRAG_START:
            return
        drag['moved'] = True
        drag_lift(window, drag, y_root)
        return
    column = window[K_ALL_COLS].widget
    low, high = column.winfo_rooty(), column.winfo_rooty() + column.winfo_height() - drag['top'].winfo_height()
    drag['top'].geometry(f'+{drag["x"]}+{min(max(y_root - drag["grab_dy"], low), high)}')         # the copy never leaves the list area
    drag['pointer_y'] = y_root
    if autoscroll_speed(window, y_root) and drag.get('after') is None:      # in the edge zone: start the scroll timer (it stops itself)
        autoscroll_tick(window, drag)
    move_slot(window, drag, y_root)


def autoscroll_speed(window:sg.Window, y_root):
    """ Pixels to scroll per tick for a pointer at y_root: 0 away from the edges, negative = up.  Gets faster the deeper into the edge zone """
    column = window[K_ALL_COLS].widget
    top, bottom = column.winfo_rooty(), column.winfo_rooty() + column.winfo_height()
    edge = AUTOSCROLL_EDGE * G.dpi                                      # the list is drawn G.dpi times bigger on a scaled display
    if y_root < top + edge:
        depth, direction = top + edge - y_root, -1
    elif y_root > bottom - edge:
        depth, direction = y_root - (bottom - edge), 1
    else:
        return 0
    depth = min(1.0, depth / edge)
    return direction * round((AUTOSCROLL_MIN_PX + (AUTOSCROLL_MAX_PX - AUTOSCROLL_MIN_PX) * depth) * G.dpi)


def autoscroll_tick(window:sg.Window, drag):
    """ Timer: scroll the list a few pixels while the pointer stays near its top/bottom edge, moving the slot along with it """
    drag['after'] = None
    if drag.get('done'):
        return
    speed = autoscroll_speed(window, drag['pointer_y'])
    if not speed:
        return
    column = window[K_ALL_COLS].widget
    first = column.canvas.yview()[0]
    column.canvas.yview_moveto(first + speed / max(1, column.TKFrame.winfo_height()))
    move_slot(window, drag, drag['pointer_y'])
    drag['after'] = window.TKroot.after(AUTOSCROLL_MS, lambda: autoscroll_tick(window, drag))


def move_slot(window:sg.Window, drag, y_root):
    """ Put the slot where the dragged entry would land if dropped with the pointer at y_root """
    entry_rows = {window[K_B_BLOCK(k)].Widget.master for k in Block.active_blocks if K_B_BLOCK(k) in window.key_dict}
    rows = [r for r in drag['parent'].pack_slaves() if r in entry_rows]              # the other entries, top to bottom (skips the gap and any empty spacer rows)
    index = len(rows)
    for i, row in enumerate(rows):
        if y_root < row.winfo_rooty() + row.winfo_height() / 2:
            index = i
            break
    if index != drag['index']:
        drag['gap'].pack_forget()
        if index < len(rows):
            drag['gap'].pack(before=rows[index], fill='x', **drag['pads'])
        else:
            drag['gap'].pack(fill='x', **drag['pads'])
        drag['index'] = index
        window[K_ALL_COLS].contents_changed()


def drag_release(window:sg.Window, drag):
    """ Drop: put the entry's row back, then move its contents to the slot's position.  Returns True if the order changed """
    drag['done'] = True                                                     # stops the auto-scroll timer
    if drag.get('after') is not None:
        window.TKroot.after_cancel(drag['after'])
        drag['after'] = None
    if not drag['moved']:
        return False
    try:
        window.set_cursor('')
        next_row = drag['next_row']
        if next_row is not None and next_row.winfo_exists():
            drag['row'].pack(before=next_row, **drag['pack_info'])
        else:
            drag['row'].pack(**drag['pack_info'])
    finally:                                                                # whatever happens, the floating copy and the slot go away
        window.grab_any_where_on()
        for key in ('top', 'gap'):
            try:
                drag[key].destroy()
            except Exception:
                pass
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    keys = list(Block.active_blocks.keys())
    src_index = keys.index(drag['src'])
    if drag['index'] is None or drag['index'] == src_index:
        return False
    move_block_to_index(window, drag['src'], drag['index'])
    return True


def set_block_border(window:sg.Window, block_num):
    """ Border colour from the checkbox - and a heading is outlined in the theme's text colour """
    if window[K_B_CBOX(block_num)].get():
        color = FRAME_BORDER_COLOR_SELECTED
    else:
        color = mix_hex(T()['heading'], T()['card'], 0.35) if Block.active_blocks[block_num].kind == KIND_HEADING else FRAME_BORDER_COLOR_NOT_SELECTED
    window[K_B_BLOCK(block_num)].update(border_color=color)


def move_block_to_index(window:sg.Window, src, index):
    """ Move entry `src` so it becomes entry number `index` (counting the other entries only); the entries in between shift.
        The blocks keep their numbers, their CONTENTS move - same trick the old Up/Down buttons used """
    keys = list(Block.active_blocks.keys())
    contents = [(Block.active_blocks[k].name, Block.active_blocks[k].path, Block.active_blocks[k].iconb64, Block.active_blocks[k].kind, window[K_B_CBOX(k)].get()) for k in keys]
    item = contents.pop(keys.index(src))
    contents.insert(index, item)
    for key, (name, path, iconb64, kind, checked) in zip(keys, contents):
        b = Block.active_blocks[key]
        b.name, b.path, b.iconb64, b.kind = name, path, iconb64, kind
        update_block_elements(window, b)
        window[K_B_CBOX(key)].update(checked)
        set_block_border(window, key)
    window.refresh()


def load_blocks_into_window(window:sg.Window):
    saved_blocks = G.launcher_settings.load()
    del_all_blocks(window)
    try:
        for key in saved_blocks.keys():
            if key[0] == K_NAME:
                saved_block_num = key[1]
                block_num = add_block(window)
                b = Block.active_blocks[block_num]
                b.name = saved_blocks[K_B_NAME(saved_block_num)]
                b.path = saved_blocks[K_B_PATH(saved_block_num)].strip('"')
                b.iconb64 = saved_blocks[K_B_ICON64(saved_block_num)].strip('"')
                b.kind = saved_blocks.get(K_B_KIND(saved_block_num), KIND_APP)
                update_block_elements(window, b)
                set_block_border(window, block_num)
    except Exception as e:
        sg.popup_error_with_traceback('Error loading saved blocks - erasing saved data', e)
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()


def save_blocks(window:sg.Window):
    G.launcher_settings.write_new_dictionary({})
    for key in Block.active_blocks.keys():
        if K_B_BLOCK(key) in window.key_dict.keys():
            G.launcher_settings.set(K_B_ICON64(key), window[K_B_ICON64(key)].get().strip('"'))
            G.launcher_settings.set(K_B_NAME(key), window[K_B_NAME(key)].get().strip('"'))
            G.launcher_settings.set(K_B_PATH(key), window[K_B_PATH(key)].get().strip('"'))
            G.launcher_settings.set(K_B_KIND(key), Block.active_blocks[key].kind)
    headings = sum(1 for b in Block.active_blocks.values() if b.kind == KIND_HEADING)
    sg.popup_quick_message(f'Saved {len(Block.active_blocks) - headings} applications and {headings} headings', font='_ 20', text_color='white', background_color='dark green')


# ------------------------------------------------------------ Delete an element from a window ------------------------------------------------------------

def del_an_elem(window:sg.Window, elem:sg.Element):
    elem.update(visible=False)
    widget = elem.Widget
    widget.pack_forget()
    widget.destroy()
    if hasattr(widget, 'image'):
        del widget.image
    del widget

    if elem.TKStringVar is not None:
        del elem.TKStringVar
    if elem.TKIntVar is not None:
        del elem.TKIntVar
    if elem.TKText is not None:
        del elem.TKText
    if elem.TKEntry is not None:
        del elem.TKEntry
    if elem.TKImage is not None:
        del elem.TKImage

    rowframe_children = elem.ParentRowFrame.winfo_children()
    if len(rowframe_children) == 0:
        elem.ParentRowFrame.destroy()
        del elem.ParentRowFrame
    remove_elem_from_nested(elem.ParentContainer.Rows, elem)
    del elem.ParentContainer
    del window.AllKeysDict[elem.key]


def remove_elem_from_nested(container, target):
    if isinstance(container, list):
        i = 0
        while i < len(container):
            item = container[i]
            if item is target:
                del container[i]          # remove this slot
                continue                  # don't advance i; next item shifts here
            remove_elem_from_nested(item, target)  # recurse into nested lists/tuples
            i += 1


# ------------------------------------------------------------ Settings window title strip (same as the new widgets' Settings) ------------------------------------------------------------

def title_strip(title, close_key):
    """ The strip across the top:  [icon] title  v1.0 ............ x   (drag the window by it).  The x turns red under the mouse (bound after finalize) """
    t = T()
    row = [sg.Image(data=ui_icon(launcher_icon), background_color=t['strip'], p=((10, 6), 6)),
           sg.Text(title, font=('Segoe UI', 13, 'bold'), text_color=t['text'], background_color=t['strip'], p=(0, 6)),
           sg.Text(f'v{version}', font=('Segoe UI', 9), text_color=t['dim'], background_color=t['strip'], p=((6, 0), (10, 4))),
           sg.Push(background_color=t['strip']),
           sg.Text('  ✕  ', key=close_key, font=('Segoe UI', 12), text_color=t['dim'], background_color=t['strip'], enable_events=True, p=0, tooltip='Close (Escape)')]
    return [sg.Column([row], background_color=t['strip'], expand_x=True, p=0)]


def ui_icon(b64):
    """ A picture for the Settings window, enlarged by the display scaling - the program is dpi aware, so tk shows pictures pixel for pixel.  base64 in, base64 out """
    if not b64 or G.dpi < 1.05:
        return b64
    key = ('ui', b64, G.dpi)
    if key not in G.icon_cache:
        try:
            im = Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGBA')
            im = im.resize((round(im.width * G.dpi), round(im.height * G.dpi)), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, 'PNG')
            G.icon_cache[key] = base64.b64encode(buf.getvalue())
        except Exception:
            G.icon_cache[key] = b64
    return G.icon_cache[key]


# ------------------------------------------------------------ The settings window ------------------------------------------------------------

def confirm(window:sg.Window, question, title='Confirm') -> bool:
    """ Yes/No question that is guaranteed to appear ON TOP of the settings window.  The settings window is keep-on-top, so a plain popup
        can come up behind it and look as if the button did nothing.  Drops keep-on-top for the moment and places the popup over the window. """
    window.keep_on_top_clear()
    x, y = window.current_location()
    answer = sg.popup_yes_no(question, title=title, keep_on_top=True, modal=True, location=(x + 120, y + 120))
    window.keep_on_top_set()
    window.bring_to_front()
    return answer == 'Yes'


def insert_new_block(window:sg.Window, kind):
    """ + Add / + Heading: a new entry goes above the first checked entry (or at the end if none is checked); the list scrolls to it and its
        name is selected, ready to type over """
    checked = [k for k in Block.active_blocks if window[K_B_CBOX(k)].get()]
    new = add_block(window)
    b = Block.active_blocks[new]
    b.kind = kind
    b.name = 'New heading' if kind == KIND_HEADING else ''
    update_block_elements(window, b)
    set_block_border(window, new)
    keys = list(Block.active_blocks.keys())
    target = new
    if checked:
        index = keys.index(checked[0])
        move_block_to_index(window, new, index)
        target = keys[index]                                            # the contents moved there - the block numbers stay put
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()
    inner = window[K_ALL_COLS].widget.TKFrame
    row = window[K_B_BLOCK(target)].Widget.master
    window[K_ALL_COLS].widget.canvas.yview_moveto(max(0, row.winfo_y() - 40) / max(1, inner.winfo_height()))
    window[K_B_NAME(target)].set_focus()
    window[K_B_NAME(target)].update(select=True)
    style_menus(window)                                                 # the new entry's elements came with their own menus


def fit_list_width(window:sg.Window):
    """ Make the scrolling list as wide as its entries need, so nothing (the trash cans!) is cut off on the right.  Measured from the widgets, so it follows font and DPI """
    column = window[K_ALL_COLS].widget
    window.refresh()
    needed = column.TKFrame.winfo_reqwidth()
    if needed > column.canvas.winfo_width():
        column.canvas.configure(width=needed)
        window.refresh()
        window[K_ALL_COLS].contents_changed()


def settings(location=(None, None), anchor=None):
    """ The application-list settings window.  Returns when the window is closed. """
    if G.launcher_settings is None:
        G.launcher_settings = sg.UserSettings(ENTRIES_FILENAME)
    Block.active_blocks = {}
    G.auto_icon = {}
    col_layouts = [[]]
    col_layouts += [[make_a_block()]]       # add a dummy block so that the column width is set correctly

    #  Toolbar - grouped left to right:  list editing | ordering | selection ......... file
    toolbar = [sg.B('+ Add', k='Add', tooltip='Add a program - above the first checked entry, or at the end'),
               sg.B('+ Heading', k=K_ADD_HEADING, tooltip='Add a heading to group the programs under it - above the first checked entry, or at the end'),
               sg.B('− Delete', k='Delete', button_color=COLOR_DANGER, tooltip='Delete the checked entries'),
               sg.B('Clear all', k='Clear', button_color=COLOR_DANGER, tooltip='Remove every entry from the list   (nothing is written until OK or Apply)'),
               sg.VerticalSeparator(p=(8, 2)),
               sg.B('☑ All', k=K_SEL_ALL, tooltip='Check every entry'),
               sg.B('☐ None', k=K_SEL_NONE, tooltip='Uncheck every entry'),
               sg.Push(),
               sg.B('OK', k=K_OK, button_color=COLOR_SAVE, s=7, tooltip='Save and close   (Enter, Ctrl+S)'),
               sg.B('Apply', k=K_APPLY, s=7, tooltip='Save but stay open'),
               sg.B('Cancel', k=K_CANCEL, s=7, tooltip='Close without saving   (Escape)')]
    list_height = min(round(SCROLLABLE_COLUMN_SIZE[1] * G.dpi), sg.Window.get_screen_size()[1] - round(260 * G.dpi))
    all_columns = sg.Column(col_layouts, size=(None, list_height), k=K_ALL_COLS, vertical_scroll_only=True, scrollable=True, expand_y=True, expand_x=True, p=(6, 2))
    status_bar = [sg.T('', k=K_STATUS, font='_ 10'), sg.Push(),                                  # file name only - the full path is in its tooltip, so the bar stays narrow
                  sg.T(os.path.basename(G.launcher_settings.get_filename()), font='_ 9', text_color=T()['dim'], tooltip=f'The list is saved in\n{G.launcher_settings.get_filename()}'), sg.Sizegrip()]
    hint = 'Drag ☰ to reorder.   Drop a program or a picture onto an entry.'
    body = [title_strip(f'{APP_NAME} Settings', 'Exit'),                                        # the strip's x sends 'Exit', handled like Cancel
            [sg.Column([toolbar], expand_x=True, p=(8, (8, 2)))],
            [sg.Text(hint, font='_ 9', text_color=T()['dim'], p=(12, (2, 4)))],
            [all_columns],
            [sg.Column([status_bar], expand_x=True, p=(8, (2, 4)))]]
    layout = [[sg.Frame('', body, border_width_no_relief=1, border_color=T()['border'], p=0, expand_x=True, expand_y=True)]]
    m_bg, m_fg = T()['menu']
    window = sg.Window(f'{APP_NAME} Settings  v{version}', layout, no_titlebar=True, grab_anywhere=True, keep_on_top=True, finalize=True, margins=(0, 0), icon=dock_icon_64, resizable=True,
                       use_min_size=True, location=location, location_anchor=anchor, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, right_click_menu_background_color=m_bg,
                       right_click_menu_text_color=m_fg, right_click_menu_selected_colors=('#ffffff', C_SELECT), right_click_menu_font=FONT_MENU)
    close = window['Exit'].Widget
    close.bind('<Enter>', lambda e: close.configure(bg=C_CLOSE, fg='#ffffff'))
    close.bind('<Leave>', lambda e: close.configure(bg=T()['strip'], fg=T()['dim']))

    del col_layouts
    load_blocks_into_window(window)
    fit_list_width(window)
    style_menus(window)

    drag = None                                                         # state of a grip drag in progress
    window.bind('<Prior>', K_PAGE_UP)
    window.bind('<Next>', K_PAGE_DOWN)
    window.bind('<Home>', K_HOME)
    window.bind('<End>', K_END)
    window.bind('<Escape>', K_CANCEL)
    window.bind('<Return>', K_OK)
    window.bind('<Control-s>', K_OK)
    scroll_canvas = window[K_ALL_COLS].widget.canvas
    G.dirty = any([icon_for_typed_path(window, n, b.path) for n, b in list(Block.active_blocks.items())          # entries saved with a path but
                   if b.kind == KIND_APP and b.path.strip() and not b.iconb64.strip()])                       # no icon get it now - OK saves
    update_status(window)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in ('Exit', K_CANCEL):
            if not G.dirty or confirm(window, 'Discard your unsaved changes?', 'Unsaved changes'):
                break
            continue
        if event == K_OK:
            save_blocks(window)
            break
        window.refresh()

        if psgdnd.is_drop_event(event):                 # file dropped onto a block: image -> icon,  program -> path + name + its icon
            block_num = event.key[1]
            if block_num in Block.active_blocks and Block.active_blocks[block_num].kind == KIND_HEADING:
                sg.popup_quick_message('Drop programs onto an application entry - this one is a heading', font='_ 14', text_color='white', background_color='#b71c1c')
            elif event.drop_type == psgdnd.DROP_TYPE_FILES and block_num in Block.active_blocks:
                filename = clean_path(values[event].split(',')[0])
                if not filename:                        # the drop came without a file name - don't blank the entry, say what to do instead
                    sg.popup_quick_message('That drop came without the file\'s name.\nCopy the program in your file manager, then paste it\n'
                                           'into the path box - its name and icon fill in.', font='_ 13', text_color='white', background_color='#b71c1c', keep_on_top=True,
                                           auto_close_duration=6)
                    continue
                try:
                    fill_block_from_dropped_file(window, block_num, filename)
                    G.dirty = True
                except Exception as e:
                    sg.popup_error(f'Could not use that file:\n{filename}', e, keep_on_top=True)
        elif event == 'Version':
            sg.popup_scrolled(f'{__file__}\n{APP_NAME} version {version}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event in ('Add', K_ADD_HEADING):
            insert_new_block(window, KIND_HEADING if event == K_ADD_HEADING else KIND_APP)
            G.dirty = True
        elif event == 'Delete':
            if num_checked_blocks(window):
                del_checked_blocks(window)
                G.dirty = True
        elif event == K_APPLY:
            save_blocks(window)
            G.dirty = False
        elif event == 'Clear':
            if Block.active_blocks and confirm(window, 'Remove every entry from the list?'):
                del_all_blocks(window)
                G.dirty = True
        elif event == K_DRAG_PRESS:
            block_num, x_root, y_root = values[event]
            if block_num in Block.active_blocks:
                drag = {'src': block_num, 'y': y_root, 'moved': False}
        elif event == K_DRAG_MOTION:
            if drag is not None:
                drag_motion(window, drag, *values[event][1:])
        elif event == K_DRAG_RELEASE:
            if drag is not None:
                if drag_release(window, drag):
                    G.dirty = True
                drag = None
        elif event in (K_SEL_ALL, K_SEL_NONE):
            check_all_blocks(window, event == K_SEL_ALL)
        elif event == K_PAGE_UP:
            scroll_canvas.yview_scroll(-1, 'pages')
        elif event == K_PAGE_DOWN:
            scroll_canvas.yview_scroll(1, 'pages')
        elif event == K_HOME:
            scroll_canvas.yview_moveto(0)
        elif event == K_END:
            scroll_canvas.yview_moveto(1)
        elif isinstance(event, tuple):              # events from the elements inside a block
            block_num = event[1]
            if block_num not in Block.active_blocks:    # a stale event from a block that's been deleted
                continue
            if event[0] == K_DEL:
                del_block(window, block_num)
                window.refresh()
                window[K_ALL_COLS].contents_changed()
                G.dirty = True
            elif event[0] == K_ICON64:
                G.auto_icon.pop(block_num, None)                # an icon string you typed or pasted - a new path won't replace it
                try:
                    image_bytes = ast.literal_eval(values[event])
                except:
                    image_bytes = None
                window[K_B_ICON(block_num)].update(data=ui_icon(image_bytes) if isinstance(image_bytes, bytes) else ui_icon(blank_image_30x30))
                Block.active_blocks[block_num].iconb64 = values[event]
                G.dirty = True
            elif event[0] == K_NAME:
                Block.active_blocks[block_num].name = values[event]
                G.dirty = True
            elif event[0] == K_PATH:
                Block.active_blocks[block_num].path = values[event]
                G.dirty = True
                icon_for_typed_path(window, block_num, values[event])          # typed or pasted: the icon comes in like a drop
            elif event[0] == K_CBOX:
                set_block_border(window, block_num)
            elif event[0] == K_ICON:                # click the icon = launch it (handy for testing the path)
                launch_file = Block.active_blocks[block_num].path
                if not launch_file:
                    continue
                if launch_file.endswith(('.py', '.pyw')):
                    sg.execute_py_file(launch_file, cwd=os.path.dirname(launch_file))
                else:
                    sg.execute_command_subprocess(launch_file)
        update_status(window)
    window.close()


# Settings window images - 25 x 25
trash_red = b'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAMAAADzN3VRAAAASFBMVEUAAAD/AAD/AADrAAD/AAD/AADcAAD/AADtAAD3AADYAAD/AAD/AADwAADuAADuAAD6AADrAAD/AADOAAD/AACmAACtAAD/AADCW8QwAAAAF3RSTlMA/fnH2GWN3bGkhVru1Mq6uZOISjcaGe/TegUAAACDSURBVHiczZHtCsMgDEWTOKvWfrfbff83HYngHF3/bbCDYLjHqCjRb9huyvYeLiGEIFBEy6WawUJWrBqqOUZLuUgej9d2DmWxtcI1BzkIkp8x+wQ5mUw9esofjKcOHfm/NPny1useEff1ZK5eZ2JhHWWaGpNqh5Iac4/2oYX4aMy3eALVGAyXRSQ2kQAAAABJRU5ErkJggg=='

trash_amber = b'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAMAAADzN3VRAAAAXVBMVEUAAADJoibJoifJoSbJoibIoiXKoCXJoibKoCbOpijIoibJoSfJoibJoibJoibIoSbWrSrIoSbJoSfNpijHoSXIoCjEnCfMoyjTqSnYrSrQqCjPpijmuSzJoifesytghzcEAAAAGHRSTlMA+cf92I1lhVjQzaOVy/Lf2LKvq0ozGhkawlE6AAAAnklEQVR4nM2RSQ6DMAxFbRLIwDy1xia5/zERSAUK6q6V+qR44SfFyTfAbzCN1rox783cld5XJCxUeV+6fDd1FKagVgKxxHo3oxPc2mtBceNxXUIqMIkS4qAoOQ1KCKmwbWxtQXg1kwUzG7DT3WSQzilkf2nsp1dTMXSxG+4/VUFItnNJh1HhGiqiQi7PC4rCLyQe6wF49Pqgf57Mt1gAAwEOREh/iwwAAAAASUVORK5CYII='

trash = trash_amber


#  ███╗   ███╗ █████╗ ██╗  ██╗███████╗    ██╗    ██╗██╗███╗   ██╗██████╗  ██████╗ ██╗    ██╗
#  ████╗ ████║██╔══██╗██║ ██╔╝██╔════╝    ██║    ██║██║████╗  ██║██╔══██╗██╔═══██╗██║    ██║
#  ██╔████╔██║███████║█████╔╝ █████╗      ██║ █╗ ██║██║██╔██╗ ██║██║  ██║██║   ██║██║ █╗ ██║
#  ██║╚██╔╝██║██╔══██║██╔═██╗ ██╔══╝      ██║███╗██║██║██║╚██╗██║██║  ██║██║   ██║██║███╗██║
#  ██║ ╚═╝ ██║██║  ██║██║  ██╗███████╗    ╚███╔███╔╝██║██║ ╚████║██████╔╝╚██████╔╝╚███╔███╔╝
#  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚══╝╚══╝
sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT


def mix_hex(color, toward, amount):
    """ Mix two '#rrggbb' colours (no Tk needed - the dock builds its layout before any window exists).  Anything else comes back unchanged """
    try:
        a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(toward[i:i + 2], 16) for i in (1, 3, 5)]
    except (ValueError, TypeError, IndexError):
        return color
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def dock_columns(entries):
    """ Split the entries (programs and headings) into columns, filled top to bottom.  Columns 'Auto': a column takes up to AUTO_ROWS rows
        before the next starts (more once all NUM_COLUMNS are full); '1' / '2' / '3': that many columns of about equal height.
        A heading is never left as the last row of a column - it moves to the top of the next one, with its programs """
    num_columns = NUM_COLUMNS if G.columns == 'Auto' else int(G.columns)
    per_col = max(1, -(-len(entries) // num_columns))
    if G.columns == 'Auto':
        per_col = max(per_col, AUTO_ROWS)
    columns = [[]]
    for entry in entries:
        current = columns[-1]
        full = len(current) >= per_col
        orphan = entry.kind == KIND_HEADING and current and len(current) >= per_col - 1
        if (full or orphan) and len(columns) < num_columns:
            columns.append([])
        columns[-1].append(entry)
    return [c for c in columns if c]


def font(bold, px):
    """ Segoe UI (Windows) / DejaVu Sans (Linux) at px pixels, cached """
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


def fit(d, text, fnt, width, keep_end=False):
    """ text shortened with an ellipsis so it fits in width pixels - at the start instead when keep_end (paths: the file name matters most) """
    if d.textlength(text, font=fnt) <= width:
        return text
    while text and d.textlength('…' + text if keep_end else text + '…', font=fnt) > width:
        text = text[1:] if keep_end else text[:-1]
    return '…' + text if keep_end else text + '…'


def icon_image(b64, px):
    """ An entry's icon (the base64 PNG as saved, b'...' text or bytes) as an RGBA image fitted in px x px, cached.  None if it isn't a picture """
    key = (b64, px)
    if key not in G.icon_cache:
        try:
            data = ast.literal_eval(b64) if isinstance(b64, str) else b64
            im = Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA')
            f = px / max(im.size)
            G.icon_cache[key] = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)
        except Exception:
            G.icon_cache[key] = None
    return G.icon_cache[key]


def draw_gear(d, cx, cy, r, color, hole):
    """ 8-tooth gear: a star-shaped polygon with flat tooth tops, and a hole in the middle """
    pts = []
    for i in range(32):
        a = math.radians(i * 360 / 32)
        rr = r if (i % 4) in (0, 1) else r * 0.72
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color)
    d.ellipse((cx - r * 0.33, cy - r * 0.33, cx + r * 0.33, cy + r * 0.33), fill=hole)


def card_layout():
    """ Where everything goes, in design pixels:  (width, height, [(kind, block, x, y, w, h)], y of the bottom line) """
    columns = dock_columns(list(Block.active_blocks.values())) or [[]]
    items, bottom = [], HEAD_H + 6
    for c, entries in enumerate(columns):
        x, y = PAD + c * (COL_W + COL_GAP), HEAD_H + 6
        for i, b in enumerate(entries):
            if b.kind == KIND_HEADING:
                y += 8 if i else 0
                items.append((KIND_HEADING, b, x, y, COL_W, 28))
                y += 28
            else:
                items.append((KIND_APP, b, x, y, COL_W, ROW_H))
                y += ROW_H
        bottom = max(bottom, y)
    if not Block.active_blocks:
        bottom += ROW_H
    width = max(2 * PAD + len(columns) * COL_W + (len(columns) - 1) * COL_GAP, 300)
    return width, bottom + 6 + FOOT_H, items, bottom + 6


def hint(part):
    """ The bottom line: what's under the mouse (a program's path), else a summary """
    if part == 'gear':
        return 'Settings - add, remove and order the programs'
    if part == 'close':
        return f'Close {APP_NAME}'
    if isinstance(part, tuple) and part[1] in Block.active_blocks:
        return Block.active_blocks[part[1]].path or 'No program set for this entry - add one in Settings'
    n = sum(1 for b in Block.active_blocks.values() if b.kind != KIND_HEADING)
    return f'{n} program{"s" * (n != 1)}   ·   right-click for options' if n else 'No programs yet - click the gear to add some'


def render():
    """ Draw the whole dock and return it as PNG bytes.  Drawn at 2x and shrunk, so every edge is antialiased.  Also fills G.hits """
    s = G.scale
    k = s * 2
    t = T()
    W, H, items, foot_y = card_layout()
    im = Image.new('RGBA', (round(W * k), round(H * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    radius = RADIUS if sg.running_windows() else 0                      # only Windows can make the corners see-through
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=radius * k, fill=t['card'], outline=t['border'], width=max(1, round(k)))
    hits = []
    # ---- title strip: icon, name, version | gear, x
    icon = icon_image(launcher_icon, round(18 * k))
    if icon:
        im.alpha_composite(icon, (round(13 * k), round((BTN_Y - 9) * k)))
    title_font = font(True, round(13 * k))
    d.text((38 * k, BTN_Y * k), APP_NAME.upper(), font=title_font, fill=t['dim'], anchor='lm')
    d.text((38 * k + d.textlength(APP_NAME.upper(), font=title_font) + 7 * k, (BTN_Y + 1) * k), f'v{version}', font=font(False, round(12 * k)), fill=mix_hex(t['dim'], t['card'], 0.4), anchor='lm')
    for part, cx in (('gear', W - 47), ('close', W - 20)):
        hits.append((cx - BTN_R, BTN_Y - BTN_R, cx + BTN_R, BTN_Y + BTN_R, part))
        hot = G.hover == part
        if hot:
            d.ellipse(((cx - BTN_R) * k, (BTN_Y - BTN_R) * k, (cx + BTN_R) * k, (BTN_Y + BTN_R) * k), fill=C_CLOSE if part == 'close' else mix_hex(t['text'], t['card'], 0.82))
        color = ('#ffffff' if part == 'close' else t['text']) if hot else mix_hex(t['dim'], t['card'], 0.25)
        if part == 'gear':
            draw_gear(d, cx * k, BTN_Y * k, 6.5 * k, color, mix_hex(t['text'], t['card'], 0.82) if hot else t['card'])
        else:
            r = 4.5 * k
            d.line((cx * k - r, BTN_Y * k - r, cx * k + r, BTN_Y * k + r), fill=color, width=max(1, round(1.6 * k)))
            d.line((cx * k - r, BTN_Y * k + r, cx * k + r, BTN_Y * k - r), fill=color, width=max(1, round(1.6 * k)))
    d.line((14 * k, HEAD_H * k, (W - 14) * k, HEAD_H * k), fill=t['track'], width=max(1, round(k)))
    # ---- headings and programs
    name_font, small_font, head_font = font(False, round(14 * k)), font(False, round(12 * k)), font(True, round(13 * k))
    if not Block.active_blocks:
        d.text((W / 2 * k, (HEAD_H + 6 + ROW_H / 2) * k), 'No programs', font=small_font, fill=t['dim'], anchor='mm')
    for kind, b, x, y, w, h in items:
        if kind == KIND_HEADING:                                        # gold name with a thin line under it
            d.text(((x + 8) * k, (y + 13) * k), fit(d, b.name, head_font, (w - 16) * k), font=head_font, fill=t['heading'], anchor='lm')
            d.line(((x + 8) * k, (y + 25) * k, (x + w - 8) * k, (y + 25) * k), fill=mix_hex(t['heading'], t['card'], 0.6), width=max(1, round(k)))
            continue
        part = ('app', b.block_num)
        hits.append((x, y, x + w, y + h, part))
        if G.hover == part:
            d.rounded_rectangle((x * k, (y + 1) * k, (x + w) * k, (y + h - 1) * k), radius=7 * k, fill=mix_hex(t['text'], t['card'], 0.88))
        icon = icon_image(b.iconb64, round(ICON_PX * k))
        ix, iy = (x + 6) * k, (y + (h - ICON_PX) / 2) * k
        if icon:
            im.alpha_composite(icon, (round(ix + (ICON_PX * k - icon.width) / 2), round(iy + (ICON_PX * k - icon.height) / 2)))
        else:                                                           # no icon: an empty tile
            d.rounded_rectangle((ix, iy, ix + ICON_PX * k, iy + ICON_PX * k), radius=5 * k, fill=t['track'])
        ver = G.versions.get(b.block_num, '')
        ver_w = d.textlength(ver, font=small_font) + 10 * k if ver else 0
        d.text(((x + 40) * k, (y + h / 2) * k), fit(d, b.name or '(no name)', name_font, (w - 50) * k - ver_w), font=name_font, fill=t['text'], anchor='lm')
        if ver:
            d.text(((x + w - 10) * k, (y + h / 2 + 0.5) * k), ver, font=small_font, fill=t['dim'], anchor='rm')
    # ---- bottom line: the path of the program under the mouse, or a summary
    d.line((14 * k, foot_y * k, (W - 14) * k, foot_y * k), fill=t['track'], width=max(1, round(k)))
    text = hint(G.hover)
    d.text((W / 2 * k, (foot_y + FOOT_H / 2 - 1) * k), fit(d, text, small_font, (W - 28) * k, keep_end=True), font=small_font, fill=t['text'] if G.hover else t['dim'], anchor='mm')
    G.hits = hits
    im = im.resize((round(W * s), round(H * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return buf.getvalue()


def redraw(window):
    window[K_IMAGE].update(data=render())


def part_at(x, y):
    """ The part of the dock at widget pixel (x, y): ('app', block_num), 'gear', 'close' or None """
    x, y = x / G.scale, y / G.scale
    for x0, y0, x1, y1, part in G.hits:
        if part in ('gear', 'close'):
            if math.hypot(x - (x0 + x1) / 2, y - (y0 + y1) / 2) <= BTN_R:
                return part
        elif x0 <= x <= x1 and y0 <= y <= y1:
            return part
    return None


def bind_mouse(window):
    """ Hover and clicks.  grab_anywhere already drags the dock; these are added alongside its bindings (add='+') """
    widget = window[K_IMAGE].Widget

    def motion(e):
        part = part_at(e.x, e.y)
        if part != G.hover:
            widget.configure(cursor='hand2' if part else '')
            window.write_event_value(K_HOVER, part)

    def press(e):
        G.press = (e.x, e.y, part_at(e.x, e.y))

    def release(e):
        if G.press and G.press[2] is not None and math.hypot(e.x - G.press[0], e.y - G.press[1]) < 4 and part_at(e.x, e.y) == G.press[2]:
            window.write_event_value(K_CLICK, G.press[2])              # a click - not a drag of the dock that happened to end on a program
        G.press = None

    widget.bind('<Motion>', motion, add='+')
    widget.bind('<Leave>', lambda e: window.write_event_value(K_HOVER, None) if G.hover else None, add='+')
    widget.bind('<ButtonPress-1>', press, add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')


def keep_going(window, event, values):
    """While the Brightness panel is open the dock keeps hovering; anything else (a click on a program...) closes the panel and goes to the main loop"""
    if event == K_HOVER:
        G.hover = values[K_HOVER]
        redraw(window)
        return True
    return False


def refresh_dock(window):
    """ Reload the list of programs (after Settings, or from the menu) and redraw """
    load_blocks()
    G.versions = {b.block_num: get_version(b.path) for b in Block.active_blocks.values() if b.kind != KIND_HEADING}
    G.hover = None
    redraw(window)


def make_psg_launcher():
    """ The dock window: one Image the whole card is drawn into """
    load_blocks()
    G.versions = {b.block_num: get_version(b.path) for b in Block.active_blocks.values() if b.kind != KIND_HEADING}
    see_through = sg.running_windows()
    bg = TRANSPARENT if see_through else T()['card']
    m_bg, m_fg = T()['menu']
    layout = [[sg.Image(data=render(), key=K_IMAGE, background_color=bg, pad=(0, 0))]]
    window = sg.Window(APP_NAME, layout, icon=dock_icon_64, no_titlebar=True, grab_anywhere=True, keep_on_top=G.on_top, margins=(0, 0), element_padding=(0, 0), background_color=bg,
                       transparent_color=TRANSPARENT if see_through else None, alpha_channel=G.opacity / 100, use_default_focus=False, auto_save_location=True, finalize=True,
                       right_click_menu=make_menu(), right_click_menu_background_color=m_bg, right_click_menu_text_color=m_fg, right_click_menu_selected_colors=('#ffffff', C_SELECT),
                       right_click_menu_font=FONT_MENU)
    G.dpi = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)
    G.scale = G.dpi * SIZES.get(G.size_name, 1.0)
    redraw(window)                                                      # again, at the display's scale
    style_menus(window)
    bind_mouse(window)
    return window


def launch(launch_file):
    """ Start a program from the dock """
    if not launch_file:
        return
    if launch_file.endswith(('.py', '.pyw')):
        sg.execute_py_file(launch_file, cwd=os.path.dirname(launch_file))
    else:
        cmd = launch_file.split()
        sg.execute_command_subprocess(cmd[0], *cmd[1:], cwd=os.path.dirname(__file__))


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


#  ███╗   ███╗ █████╗ ██╗███╗   ██╗
#  ████╗ ████║██╔══██╗██║████╗  ██║
#  ██╔████╔██║███████║██║██╔██╗ ██║
#  ██║╚██╔╝██║██╔══██║██║██║╚██╗██║
#  ██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
#  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝

def main():
    sg.set_options(border_width=0, dpi_awareness=True)
    sg.user_settings_filename(WINDOW_SETTINGS_FILENAME)
    migrate_settings()
    G.launcher_settings = sg.UserSettings(ENTRIES_FILENAME)
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')           # a renamed theme (Midnight -> Carbon) or an unknown one
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    G.size_name = sg.user_settings_get_entry(K_SIZE, 'Medium')
    G.opacity = sg.user_settings_get_entry(K_OPACITY, None)
    if G.opacity not in OPACITIES:                                      # older versions saved an Alpha of 1-10
        G.opacity = min(OPACITIES, key=lambda p: abs(p - sg.user_settings_get_entry('-alpha-', 9) * 10))
    G.on_top = sg.user_settings_get_entry(K_KEEP_ON_TOP, False)
    G.columns = str(sg.user_settings_get_entry(K_COLUMNS, 'Auto'))
    apply_theme()
    window = make_psg_launcher()

    pending = None                                                      # a dock event that came in while the Brightness panel was open
    while True:  # The Event Loop
        event, values = pending or window.read()
        pending = None
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        menu_key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event      # right-click items come back as 'label::key'
        if menu_key == 'Exit':
            break
        if event == K_HOVER:
            G.hover = values[K_HOVER]
            redraw(window)
        elif event == K_CLICK:
            part = values[K_CLICK]
            if part == 'close':
                break
            if part == 'gear':
                menu_key = K_SETTINGS                                   # handled at the bottom
            elif isinstance(part, tuple) and part[1] in Block.active_blocks:
                launch(Block.active_blocks[part[1]].path)
        elif menu_key == K_BRIGHT:
            pending = brightness_panel(window, keep_going)
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            apply_theme()                                               # the Settings window and popups follow the brightness too
            redraw(window)
            set_right_click_menu(window, make_menu())
        elif menu_key == 'Version':
            sg.popup_scrolled(f'{__file__}\n{APP_NAME} version {version}', sg.get_versions(), location=window.current_location(use_anchor=sg.WIN_ANCHOR_UPPER_LEFT), location_anchor=sg.WIN_ANCHOR_LOWER_RIGHT, keep_on_top=True, non_blocking=True, size=(70,10))
        elif menu_key == 'Edit Me':
            sg.execute_editor(__file__)
        elif menu_key in (K_REFRESH, 'Refresh'):
            refresh_dock(window)
        elif menu_key == K_KEEP_ON_TOP:
            G.on_top = not G.on_top
            window.keep_on_top_set() if G.on_top else window.keep_on_top_clear()
            sg.user_settings_set_entry(K_KEEP_ON_TOP, G.on_top)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_THEME):
            G.theme = menu_key[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            apply_theme()
            redraw(window)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_SIZE):
            G.size_name = menu_key[len(K_SIZE):]
            G.scale = G.dpi * SIZES.get(G.size_name, 1.0)
            sg.user_settings_set_entry(K_SIZE, G.size_name)
            redraw(window)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_COLUMNS):
            G.columns = menu_key[len(K_COLUMNS):]
            sg.user_settings_set_entry(K_COLUMNS, G.columns)
            redraw(window)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_OPACITY):
            G.opacity = int(menu_key[len(K_OPACITY):])
            window.set_alpha(G.opacity / 100)
            sg.user_settings_set_entry(K_OPACITY, G.opacity)
            set_right_click_menu(window, make_menu())
        if menu_key in (K_SETTINGS, 'Settings...'):
            G.hover = None
            redraw(window)
            settings(location=window.current_location(use_anchor=sg.WIN_ANCHOR_UPPER_LEFT), anchor=sg.WIN_ANCHOR_LOWER_RIGHT)
            refresh_dock(window)                                        # the list may have changed
    window.close()


blank_image_30x30 = b'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAAGklEQVR4nO3BMQEAAADCoPVP7W8GoAAAAKAzDi4AAXXIMrUAAAAASUVORK5CYII='

launcher_icon = b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAE4UlEQVR4nO1V24uVVRT/rb33dzvnzMW8JOPdUSZx7OagYZlJhvfCQAkkQp/qwYeoByVsknwoUehJEIQgyQd7KAQpBDEHK43OQ46allLqTNnMmTlz5sz5zved79tr9XDmZv4JtWFt9l4/WL+19t7rt4H/x39odIoiAJMNnaIAQKRTPYjQqA+Qzk4Fook4RHXf2PZfNC6AMZAB1CZj80axOw9jzjxA36mvBUA8QdApCgdIWt7ten/6zDlPOTasAECiM9mBvrv5nkNrDl77+sl902dPXSlVNQIAOiOZgZ7+7rYNP3/w0/oX32mZ8ejqiPQwIJQlBD1/99346Juz+0/VyQCs+7jl6cO3LovIy5Ns2+OH73Y9s33dsmr32i6R5FUR2TqKbS1fW3/xyHZnWc9rO7+VsLxDRLaIyCsisql39xuXj82Z0woApn4YCVlGOhRDiY0ZACLrqZQl1aQUoZYg7VcpsoC1MJ6nCJxYB5qsJCgUVNzEpK2FmdKgiDlRrkvjBA3lm1EhkqUrjhY+VbYWAwIxnj8S2Ri3K0XmyhL07jiOKkWkABj2lI3k0lC2uFMPL4r27j0WiVRAUA7gohIGg42N4UQFABSRjcU8IswABIoNCPKXuEwgslBJk9G2CQRAEwQYcKwQDFlj00adpI1EBKMUQBSOxTUAkPWMgrAiTixJIoCAWBNByOiMZo4JKWyakhABmoggBC9wtTBRTYRTIgsiEgixgMRxFEafJN2/mA+t8mri5rTVvrHaN+JmdQqD7ovnKo5OgCy08WG0D4MstGNSunC2v+JwgozWygecADANSussOKne+DGsdwWAPe8dau0abjkVz3vB0zYiALDak6l9PwwvTn+9vnFpfsnmZwtNNlYkAnJ85nOXp5RPdj93beP97se2ctxclXqsDIl8GYqcb1+148TBt3+hI6e+D86dPtl177fujqZccNUYByxCAAugcnAyzZWqlCBcJlUPIiIi0NlcgCkhc0mEy5pAAAkzy0Cp3N7Wuvj6yhWrVpnbNy4tHBzoWzYSpRJzrZ0lGm9PEQF4CFpTM0iNtw0IgAhKRYYi1UyTpIKUgq5FUiz0L/lzaKDNjBTDoUw2V9ZGT2ObyGT5oNGJWUCwD8kXESDgCWIQxLJAacpkcyNptThAANSW1996M4ri/eFIOUeAnpQOoIjYkqQs45omAhhFUFrICsAyQQHAZrKZMOv7h86cOPoJYflyB/l8MLdj8wp/xux5thYqiCJoBS7e46TwBy+YG6iFszyVWK4rm1a42xvLzbs1Oz8XqPmZQFkAsIDvGVsol3rOXLlyCUBIANC2+3hDadGm1eJnNaB5LP1qeaDW+Nmq279/5bWaaY0uwHVMC6GUpus3XL91YuFLC2c0eB5E8Wh5VGErX5Qq3+26cGHIAED/E89TrmozHJessCUA0Iop0Vmz58M9oXFOBmEh0IAVANCwQOC6n+9bF+rTzX4fqg5E1TFiIcd1ts1qpl1j2r/AH65aMYNQWpRxUuX6CSvfBlqKxphiKmbIdVLrepS4HiXaUaxTNVRtHCkaqhVdUewrSRziVBOJsC32DQ6GeODD6RTTlikEgyELAHBGUXt4tXrhwNpUzq8xmJkEsE79MnVC+UocdXTkk/Nr1pj2pqaAPU8AQMUx3entjTry+QQA/gF0+YdyFnDz5wAAAABJRU5ErkJggg=='            # PSG Dock icon, 24 px, beside the title

dock_icon_64 = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAANlklEQVR4nO1afXBc1XX/nXvve7tvV9JKlvwhW7YsgY2xKV82CYZQORA+CkNKQu3pkATP0A6fiYFJk5AZQHFJJ2TSmVBTkgwkIVOgAdvQEkM6qSFU1CYmtmNiQ4SpiZAtf8j61q60u2/fPad/vJUtS7vyytBSqH4zRzurve/cc3/33nPOvecBU5jCFKYwhSlMYQpTmMIUpjCFKUzh/xvoA2ozAvmA9Pxv6ir6DEGEQAolidKAiCpknDRDGU1QCiWJ0QQRqIJWNTcrTQRVohgiNKOwLkzAJI1iraIEtgiADyANIkCOEy4CIoLk21SUMBsKQApAMOrZ8AcicKg7AiBagi4CMICwIVGB9mbcIyIEInFrFy6quvbb91BVw3Jm9iboS6AUtARH/X1bnu157uvfB6kshEnCXuXWVdOvvPEvZ6yZVUVnwrIpRjuBRAxx7yDaNr3Y+yjRoafzJIQMiuDbZ591y5W1s77kAXOsMEGoiDaBUdrv8LNv/MM7e79HBztfL0TCWAIUlOZo5fz6qht+/K/uwkvOcIe6hxKe2s8CXaQfYUD355xl7tyly1S8srbriZvvXi9CSpFd88UZl99/15znqhdEY+iNdEJ5vYDognwSMdgva6gY/vSChuiKSJwcpQ4+IbJSE22w65ae9/WbT2v8bkQrDEe990ibNETUWFUEAIqspIdnLRZcP8+LfYpl95+pQ4d2NQNqLcAntD0+GFEg4ppVDzXHV6z5VnVwdMdLf1X5QFUskhyzLcb2FzzU0r9s3S56wB84oo8+/qUL+cCONyyL85v1izddeFXiylzX6U9T4z89dgJ1BewWwErbl1e5iZ23t24f2r34qj2XGE2D5U5k7tZLm7YvrKioSS6/+DuVa+7cDMAE4SwW0iUB4CbvuO2rVQP9l29s3/+TlVte+2sRISI6vq1OnMxQkamuX8Qi8ueL3H+pikX6OoeDRADEskFQVkDifcNB1V1NldtmRzM7UTYzEmtc1sgsAFAxs8acjh6xqvb+5wygDYbLEGTjJsiWjZG4QTbuAHG34R83oc/pm5agBiAyI7CCc6eVz51mzMzhqPdu5Zo7Xw6y2QSy2Tiy2XiQzZaNFgRBLEgmKwzge5+7fiPYSp3nLQSgHKVk9MSP9wEARMQSmCKGAgBOuWusAcQYU9ARZG1AAFzHOGlABHxsiQlEGJYEsBT253IxPSOzFwDakM4yw4ysFE3EAogyOnPM7kiECw4AgPE8C8BBfsAM4YLtCj4tIIDgKGUBUGBBwQSxN22hKgAoEgbU2Hbh0haHwxVnJ47hga9gYjkg9FhjFJGABIDA9xW0Lk6ktRQYo+C6FggfLNSsIAFEECGN1i5/LoBXKyJwANhifc00JgOA+4bt3NC8YySQCFl4oiWzuxqxxj1ApByjnNDYrmFMhtJ7Z0H5CYAyEYCyI9wAotLpmQAcU14+WHQCAcAYZYD+9DtvL42CIAQuFPYLbwFSpG0Wv27Lrb77xb5MU6O7LxuQLkaB0pAfb09d05VRS5TNAOq4bxFAYIRUz7qvgo8+ClM3ALJqrKowxCixQX8U/U+uRizwAJWKRLLIZgFXRDEo5/jZWYN33PYN97PXrYcxrAvMjAYgjmPtvn2f4Jc335q3o/QVABGCWPiWKze2yjeee7Nfxi/I442FNIlyoTiTj9rHQQDBJ2gMLsDgY9+zPgnReGUcJk2iHQl/yh7LLE/gOiMCp/PIitxjP1oRAEJFBiaARAGCCBBx89t6PIqmiACBSAJl01x88ABARMLQNl1sWQME5AKy1idRVNyXKALZHEngky2eLAEZwAaAqAn8kgIoA7AlCorbPiEBx5zhxG2ON52wHQFEBJrI/Uvof+ikdoWe9uS6AAWRCZ1uSYP7OGOKgA/bgA8bUwR82AZMBCKIjApfhc7z7xeFb12KxMzStR6LCOb9Miz5HIlECh/HSzUp/Bg3rtH20aoN4XdCwPnIP1nGhYiA9ACeWblSe56ngzAHlUnpIggLhJkIrqtWrl+p+wBweI6dnE1EApDk8jdLOeYTSDhhgjZ89xa1cv163bXn17/IDSehTcRALAN8cuGATVmNGu491Drwmyd2rNqwIZ5Op/v+0HrkRRVTBCjFDGYBMxeR/G/CgKoy1H6g599TKb9j56oNZa8d7t7bNdC3pTwaJSsiLBK2n0CsCCsiA7b0+wP7n29uFv7WkiXO6JVAoz5VXV2d29HRkf78jTf9aWviiq8Nzr/qQkVUIzIx6RQyjeH+o+8sPvDUm+ctrK1NpzOO53n2cMfB3ns+szF2/vnuRVDGgRRaiHmMdCPM774ztP2+5z/bOb1uwUx/OKUiXrkdaN11pPlwa8OcROKcMOM+mTKCYTv4b1m74/s1DQ9t/tnDm+rr66Pt7e1B/gghNDL4+vomp729JXPb2of/xo14D7617eWDe/YP/LbmohuSYCiGLZx8CUOZqFC6J9Ctz8dra2deqiJl05itEAGkjN3f1vHaNUuP/vGi87Rhn1Uxm1kAN6r493s5eOY/KmfPrq9vUkpcYYEiRVnmVE/Hu698MW56GhzjZJgnTD8dbfjJtgOxtnlnnNP0qcsWgfnv19176z31TU1Oe0tLDgCHg29qcttbWjK3Na+7XTvuI6/+6nlOpVIq5mrceN2lP0mUl2eCgBVRoaWgADACJjejYgnLnIHYQJEChCEQMo4TS6adrLVO8qTuVQClbKws5sclyA1DwCAFFoYCadKul1IqyY7KqJMEMQbj2ac2rg5SqbhxHNt09ee0VurBR+6/45v19U3R9vYWn5qamkxLS4tc/fmb6hqXfmL3tld+VdbdeQiRqEccJuclRQQRABzkm4+9amQoRVDj7kqK6GKBZQEVmF8RhiYq1axwVxFJLufDi8V5xVXXqb7DRy745x8+sGvp0qXaeJ6nAWTnn33uFYN9vRXdnYds1ItpZh65yinJ64Y3sYVnZGQgXPy8OE5bMbKI1CRDCggi5LoRJAf6pavzMM2aO+c6ADsdpzGi+vvLFQA4jrswlRyQEOPG9lEWID+PRAqDA31QSi8I/3sAKpdL5yeaC5a1Po6QfAkvl8udsMn4FIuIHyVQ3l3xMQIcp1sAqMGB3r0VldMoxIdt5wcPIgURlqrq6eSn03vD/86E2ta9jQHEX9+8qaWsPNE1p75RDw+lrFIqvML5GIhSCpn0EFdPn6Wqp8/039zxn78E4PX2trLBPnBVVaNqfeP1riUXXHLf+cubfhQEgT584D1LpGhMsfcjBcr/YWaZNn2WvvgzV6Ov68h3tvzy2b2JxDy3o2P/UL5aAzcWq0kMD3era1d/+QsNZ/zJN3t7uip7j3aChYsWBf8vY3SiXFk9HTUzatNHD7Y9/MwPHnzEq64O0j09gwCylL9GdwB4kUiiMpsdMHWnLVzyycuuvaK8onoRi/WErZZ8ueSkPYucQNbILJzSKx1jjn7HDi4nUUZEAoEorawik02lBvbt2vrSy/+1Z+fvIpGKIJsd7AcwDCA3cgOr8y8dxFy3vNL3k7H897K8RPIkjU/zxvR9sjFNAqeqayRPCvIvbaQAJAFkXbcs7fupfgBDALIAgpHiI+cfyPp+MgkgqGg4tzpy5jUOGyPiZ3IQCSBcfBVoDdu9T9K7XwhC48Oaje9Dlp1Xpi9fnlB6ElcaW383wK9sTVnXPU6ED8jVtbX6nIqKcZWlEYyUvjURO0pZiDgvdXVh68GDSe2nhgGkAeRGwv6IcgVAoa7OQUeHTlx214yKy+4+S8VqNNQkZk5rDL212e9+dFW3QQ5BEPB9X5lT/rdfm5eAW/rgAQBW6Ic/7Uzefl9bvzFQQQB+avkF1TfMb/AmpUeEkr4vP2vveHvNzp0dtQAfDgmwownIL+0mBbSoOX/XdjGcaI2yvi9celZASoQiFc7Qb598r+fprxz+5Lk1sS0/P+1MKNZ+lqTUFWABaBKKeBo33fne3sd/cWTg3iVLau5dcsbpycAWLdIWNorEiBgWHlq9bcerLxw+7I9K+o7V3vL7piWoX/24gjYxAgeiDMFolCwwgPVRtuAiB0DPHV+YFkDDgRC7LqB1aeJqQCtiMOubr68WAF1/MXeWyrEoTSQmH7pKEhEKAKtIRfO3QYGMuqIbnQoLAMTnX1Dyma0ghEl58QBAZsmCeLaEJ4rCMmh2XdQH4JdH3AlrfBNhpAJcH4uNG9u486s3e8n7DvnK9RgA5sx0J7dcC2DGNGMBIOE61pYShidATSQybmz/I3UBydd24/H3rysaDT8n60NLxTgCdt6CQBNlhEkThIkhpQpEhNlqscEgALT3RIfAYgEQNPGoGF2KhDmVcBIAfFcPWhGCIhGahGjFYFYM+Fi8OIMxBZYTCRAhgCQTmDcBMARR0sotTcSF1p6Q7pxW3dcmAJ316ZaUhX2bwBGyEiHAJV2CAC4TeZzjd2nx9h4R0MNPnX3IaNqvxMYUkVuyCCJkjCbot2jt2mDsmyJF91R9c1tlEPfmacsOVAnHISYKhJOHsnP+iLXhSwkj+XjqD0tr48adBRLyJ1jOJ/4WdNGCHQdG2SkioP5VK+dTLjdNaMLXA0I44RW7Nraj4ucvdBd7XbYQPoY3AoUxwUCFTukIWGBmTrXWSAUsKPay00l1FZn5/wbjepkPMOCMewAAAABJRU5ErkJggg=='            # PSG Dock icon, 64 px, window / taskbar icon

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e)
