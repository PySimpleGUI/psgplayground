#!/usr/bin/env python
"""
iD880 Banner - big lettering in any font on this computer, printed on the iD880 two ways:
    Banner   the words run down the strip, as tall as the paper is wide - one long banner
    Across   the words read across the paper, line after line, as wide as the paper

    Flip through the fonts - the list shows your words in every font:
        Up / Down, Left / Right, the mouse wheel over the list, or the ◀ ▶ buttons     previous / next font
        PgUp / PgDn   10 fonts        Home / End   first / last        Alt+Up / Alt+Down   flip even while typing
        Click a font to pick it.  Tab leaves the words box, so the arrow keys flip fonts again.
    Ctrl+F   search the fonts by name (Down or Enter goes back to the list, Esc clears it)
    Ctrl+D   ★ favorite - ★ only shows just your favorites        Del   hide a font you never want (Hidden shows them again)
    Ctrl+R   a random font        Ctrl+P   print        Esc   closes
    Emoji, symbols and other alphabets print too: a letter the chosen font doesn't have is borrowed from a font that has it (Segoe UI Emoji first).
    Size       Fill = as big as the paper allows, or pick how tall the capital letters are in mm (Across wraps long lines at a fixed size)
    Darkness   1-30, starts at Setup's.  Slow prints darker - big black areas (Reverse, thick letters) need it
    Style      Thicker, Spacing, Outline, Shadow, Reverse (white letters on black), Frame, Inside (solid / gray / stripes / dots),
               Direction (banner: which end prints first), Line up (across: left / center / right).  Reset style puts them all back.

Needs id880_lib.py in the same folder (printer connection, language and paper widths come from iD880_Setup.pyw) and Pillow.
Writes only its settings, into the iD880 programs' shared settings file (iD880_thermal_printer.json in PySimpleGUI's settings folder).

CHANGE LOG (newest first, 1 line per change):
2026-11-12  v1.0.1 Claude: emoji and every alphabet - a letter the font lacks comes from a font that has it (Segoe UI Emoji, Segoe UI Symbol, Segoe UI...)
                          instead of a rectangle; Outline with Inside: Solid is hollow (it was only bolder)
2026-11-12  v1.0.0 Claude: first version - every installed font in a flip-through list, banner + across, size, darkness, 8 styles, no Figlet
"""
import bisect
import functools
import os
import random
import sys
import threading
import traceback
import unicodedata

import PySimpleGUI as sg
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, features

import id880_lib as lib

VERSION = '1.0.1'
TITLE = 'iD880 Banner'
ICON = b'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'

BANNER, ACROSS = 'banner', 'across'
PATTERNS = ['Solid', 'Gray', 'Stripes', 'Dots']
ALIGNS = ['Left', 'Center', 'Right']
REGULAR = ('regular', 'normal', 'book', 'roman', 'medium', '')
FONT_EXTENSIONS = ('.ttf', '.otf', '.ttc', '.otc')
DEFAULT_TEXT = 'Happy Birthday!'
FAVORITE_FONTS = ('Arial Black', 'Impact', 'Arial Bold', 'DejaVu Sans Bold')     # the first one found is the font the first time
BITMAP_SIZES = (109, 136, 160, 128, 96, 72, 64, 48, 32)               # the sizes color-bitmap emoji fonts are made in
PROBE_PX = 32                                                       # the size the 'does this font have this letter' check draws at
MISSING = '\U0010fffd'                                              # a private-use character no font has: what a missing letter looks like
JOINERS = '\u200d\ufe0e\ufe0f'                                      # the emoji joiner and the text / emoji style selectors
RAQM = features.check('raqm')                                       # with raqm Pillow joins emoji sequences (families, flags); without, the joiners go
EMOJI_FONTS = ('Segoe UI Emoji', 'Noto Emoji', 'Symbola', 'Segoe UI Symbol', 'Apple Color Emoji', 'Noto Color Emoji')
SYMBOL_FONTS = ('Segoe UI Symbol', 'Cambria Math', 'DejaVu Sans', 'Noto Sans Symbols', 'Noto Sans Symbols 2', 'Symbola', 'Apple Symbols', 'Segoe UI Emoji',
                'Noto Emoji', 'Apple Color Emoji', 'Noto Color Emoji')
TEXT_FONTS = ('Segoe UI', 'Arial', 'Microsoft YaHei', 'Yu Gothic', 'Malgun Gothic', 'Nirmala UI', 'Leelawadee UI', 'Ebrima', 'Gadugi', 'Segoe UI Historic',
              'Microsoft JhengHei', 'SimSun', 'DejaVu Sans', 'Noto Sans', 'Noto Sans CJK JP', 'Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'Droid Sans Fallback',
              'Arial Unicode MS', 'Segoe UI Symbol', 'Segoe UI Emoji', 'Noto Emoji')
FALLBACK = {'byname': {}, 'others': [], 'cache': {}}                # filled in after the font scan (set_fallbacks)

MARGIN = lib.mm_dots(3)                                             # white along each edge of the paper
TOP = lib.mm_dots(4)                                                # white above and below the lettering (Across)
BLOCK_PAD = lib.mm_dots(2.5)                                        # room around the lettering inside a frame or a reverse block
FRAME = lib.mm_dots(1.5)                                            # frame line thickness
REF_PX = 200                                                        # font size the measuring is done at
LONG_PRINT_IN = 24                                                  # ask before printing anything longer than this
TOO_LONG_IN = 240                                                   # not drawn - shorten the words or the size

ROWS, ROW_H, GALLERY_W = 11, 52, 380                                # the font list: rows shown, row height, width (screen pixels)
SAMPLE_PX = 24                                                      # the words' size in the font list
SAMPLE_MAX_H = 30                                                   # the words never taller than this in a row
PREVIEW_W, PREVIEW_H = 900, 380
MAX_SCALE = 0.6                                                     # preview never bigger than this many screen pixels per dot

DEFAULT_OPTIONS = {'mode': BANNER, 'fill': True, 'mm': 25, 'darkness': None, 'slow': True, 'thick': 0, 'spacing': 0, 'outline': False, 'shadow': False,
                   'reverse': False, 'frame': False, 'pattern': 'Solid', 'direction': 'start', 'align': 'Center', 'ends': 10, 'media': lib.RECEIPT}
STYLE_KEYS = ('thick', 'spacing', 'outline', 'shadow', 'reverse', 'frame', 'pattern', 'direction', 'align', 'ends', 'fill', 'mm')

K_TEXT, K_SEARCH, K_COUNT, K_GALLERY, K_SLIDER, K_FONT_NAME = '-TEXT-', '-SEARCH-', '-COUNT-', '-GALLERY-', '-SLIDER-', '-FONT NAME-'
K_FAV_ONLY, K_FAMILY, K_SHOW_HIDDEN = '-FAV ONLY-', '-FAMILY-', '-SHOW HIDDEN-'
K_PREV, K_NEXT, K_FAV, K_RANDOM, K_HIDE = '-PREV-', '-NEXT-', '-FAV-', '-RANDOM-', '-HIDE-'
K_BANNER, K_ACROSS, K_INFO, K_PREVIEW, K_PREVIEW_COL = '-BANNER-', '-ACROSS-', '-INFO-', '-PREVIEW-', '-PREVIEW COL-'
K_FILL, K_MM, K_SIZE_TEXT, K_DARKNESS, K_SLOW = '-FILL-', '-MM-', '-SIZE TEXT-', '-DARKNESS-', '-SLOW-'
K_THICK, K_SPACING, K_OUTLINE, K_SHADOW, K_REVERSE, K_FRAME = '-THICK-', '-SPACING-', '-OUTLINE-', '-SHADOW-', '-REVERSE-', '-FRAME-'
K_PATTERN, K_DIRECTION, K_ALIGN, K_ENDS, K_ENDS_ROW, K_MEDIA, K_COPIES = '-PATTERN-', '-DIRECTION-', '-ALIGN-', '-ENDS-', '-ENDS ROW-', '-MEDIA-', '-COPIES-'
K_PRINT, K_FEED, K_SETUP, K_RESET, K_STATUS = '-PRINT-', '-FEED-', '-SETUP-', '-RESET-', '-STATUS-'
K_SCAN_PROGRESS, K_SCAN_DONE = '-SCAN PROGRESS-', '-SCAN DONE-'
K_UP, K_DOWN, K_PGUP, K_PGDN, K_HOME, K_END = '-UP-', '-DOWN-', '-PGUP-', '-PGDN-', '-HOME-', '-END-'
K_ALT_UP, K_ALT_DOWN, K_CTRL_F, K_CTRL_D, K_CTRL_R, K_DEL, K_ESCAPE = '-ALT UP-', '-ALT DOWN-', '-CTRL F-', '-CTRL D-', '-CTRL R-', '-DEL-', '-ESCAPE-'
K_WHEEL, K_WHEEL_UP, K_WHEEL_DOWN = K_GALLERY + '+WHEEL', K_GALLERY + '+UP', K_GALLERY + '+DOWN'
K_SEARCH_ENTER, K_PREVIEW_RESIZE = K_SEARCH + '+ENTER', K_PREVIEW_COL + '+RESIZE'
STEP = {K_UP: -1, K_DOWN: 1, K_PGUP: -10, K_PGDN: 10, K_ALT_UP: -1, K_ALT_DOWN: 1, K_PREV: -1, K_NEXT: 1, K_WHEEL_UP: -1, K_WHEEL_DOWN: 1}

BG, PANEL, PANEL2, PREVIEW_BG = '#161a22', '#1e2430', '#232a37', '#3c4650'
C_TEXT, C_DIM, C_SEL = '#d6dbe5', '#8a93a6', '#2a62a8'
C_FONTS, C_WORDS, C_SIZE, C_DARK, C_STYLE, C_PAPER = '#7fb2ff', '#e6eaf2', '#4cc38a', '#f0b429', '#c58cff', '#4fd1c5'
C_OK, C_WARN, C_BAD, C_STAR, C_HIDDEN = '#4cc38a', '#f0b429', '#ff6b6b', '#ffd23f', '#6b7385'
ON_COLORS, OFF_COLORS, MODE_OFF = ('#ffffff', C_SEL), ('#c9cfdb', '#2a3140'), ('#c9cfdb', '#2a3140')
PRINT_COLORS = ('#ffffff', '#1f8a55')
sg.theme_add_new('BannerDark', {'BACKGROUND': BG, 'TEXT': C_TEXT, 'INPUT': PANEL2, 'TEXT_INPUT': '#e6eaf2', 'SCROLL': PANEL2, 'BUTTON': OFF_COLORS,
                                'PROGRESS': (C_SEL, PANEL), 'BORDER': 0, 'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
sg.theme('BannerDark')
sg.set_options(icon=ICON)
FONT, BOLD, HEAD, LIST_FONT = ('Segoe UI', 10), ('Segoe UI', 10, 'bold'), ('Segoe UI', 11, 'bold'), ('Segoe UI', 9)
TOGGLES = {K_FAV_ONLY: '★ only', K_FAMILY: 'One per family', K_SHOW_HIDDEN: 'Hidden', K_FILL: 'Fill the paper', K_SLOW: 'Slow - darker',
           K_OUTLINE: 'Outline', K_SHADOW: 'Shadow', K_REVERSE: 'Reverse', K_FRAME: 'Frame'}
OPTION_TOGGLES = {K_FILL: 'fill', K_SLOW: 'slow', K_OUTLINE: 'outline', K_SHADOW: 'shadow', K_REVERSE: 'reverse', K_FRAME: 'frame'}
FILTER_TOGGLES = {K_FAV_ONLY: 'fav_only', K_FAMILY: 'family_only', K_SHOW_HIDDEN: 'show_hidden'}
SLIDERS = {K_MM: 'mm', K_DARKNESS: 'darkness', K_THICK: 'thick', K_SPACING: 'spacing', K_ENDS: 'ends'}

LANCZOS = getattr(Image, 'Resampling', Image).LANCZOS


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Finding the fonts
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def font_folders():
    if sys.platform.startswith('win'):
        windir = os.environ.get('WINDIR', r'C:\Windows')
        return [os.path.join(windir, 'Fonts'), os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')]
    if sys.platform == 'darwin':
        return ['/System/Library/Fonts', '/Library/Fonts', os.path.expanduser('~/Library/Fonts')]
    return ['/usr/share/fonts', '/usr/local/share/fonts', os.path.expanduser('~/.fonts'), os.path.expanduser('~/.local/share/fonts')]


def faces_in(path):
    """How many fonts a file holds - a .ttc collection says so in its header, any other file holds one"""
    try:
        with open(path, 'rb') as f:
            head = f.read(12)
    except OSError:
        return 0
    return min(64, int.from_bytes(head[8:12], 'big')) if head[:4] == b'ttcf' else 1


def text_of(name):
    return name.decode('utf-8', 'replace') if isinstance(name, bytes) else str(name)


def face_name(family, style):
    return family if style.strip().lower() in REGULAR else f'{family} {style.strip()}'


def scan_fonts(window=None):
    """Every font on this computer, one entry per name: {'name', 'family', 'style', 'path', 'index', 'var'} sorted by name.
    A variable font gives one entry per named style (Light, Bold, Condensed...).  Progress goes to the window while it runs."""
    files = []
    for folder in font_folders():
        for root, _, names in os.walk(folder):
            files += [os.path.join(root, n) for n in sorted(names) if n.lower().endswith(FONT_EXTENSIONS)]
    found = {}

    def add(name, family, style, path, index, var, bitmap=False):
        found.setdefault(name.lower(), {'name': name, 'family': family, 'style': style, 'path': path, 'index': index, 'var': var, 'bitmap': bitmap})

    for n, path in enumerate(files):
        if window is not None and n % 40 == 0:
            window.write_event_value(K_SCAN_PROGRESS, (n, len(files)))
        for index in range(faces_in(path)):
            bitmap = False
            try:
                f = ImageFont.truetype(path, 20, index=index)
                family, style = f.getname()
            except Exception:                                       # a color-bitmap emoji font only opens at its own sizes: kept to borrow emoji from
                f, bitmap = bitmap_font(path, index), True
                if f is None:
                    continue
                family, style = f.getname()
            family = text_of(family or os.path.splitext(os.path.basename(path))[0]).strip()
            style = text_of(style or 'Regular').strip()
            try:
                variations = [text_of(v) for v in f.get_variation_names()]
            except Exception:
                variations = []
            if variations:
                for v in variations:
                    add(face_name(family, v), family, v, path, index, v)
            else:
                add(face_name(family, style), family, style, path, index, '', bitmap)
    fonts = sorted(found.values(), key=lambda f: f['name'].lower())
    families = {}
    for f in fonts:                                                 # each family's main face, for One per family
        best = families.get(f['family'])
        if best is None or (f['style'].lower() in REGULAR and best['style'].lower() not in REGULAR):
            families[f['family']] = f
    for f in fonts:
        f['main'] = families[f['family']] is f
    return fonts


def face(fd):
    """A font as one hashable value: (file, index in a collection, variable-font style, color-bitmap font?)"""
    return fd['path'], fd['index'], fd['var'], bool(fd.get('bitmap'))


@functools.lru_cache(maxsize=160)
def scalable_font(path, index, var, px):
    f = ImageFont.truetype(path, max(4, int(px)), index=index)
    if var:
        f.set_variation_by_name(var)
    return f


@functools.lru_cache(maxsize=8)
def bitmap_font(path, index):
    """A color-bitmap emoji font (Noto Color Emoji, Apple Color Emoji) only comes in the sizes it was made in"""
    for size in BITMAP_SIZES:
        try:
            return ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
    return None


def load_face(fc, px):
    """(font, scale): the font for px dots.  A color-bitmap font loads at its own size and scale says how much to shrink or grow what it draws."""
    path, index, var, bitmap = fc
    if bitmap:
        f = bitmap_font(path, index)
        if f is None:
            raise OSError('no size of this font loads')
        return f, px / f.size
    return scalable_font(path, index, var, int(px)), 1.0


def font_at(fd, px):
    return load_face(face(fd), px)[0]


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Letters the font doesn't have - emoji, symbols, other alphabets - come from a font that has them
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def clean_text(text):
    """Emoji typed or pasted into tk can arrive as two halves (surrogates) - made back into one character.  Accents joined to their letters (NFC)."""
    try:
        text = text.encode('utf-16', 'surrogatepass').decode('utf-16')
    except UnicodeError:
        pass
    return unicodedata.normalize('NFC', text)


def glyph_print(f, ch, bitmap):
    """A fingerprint of how a font draws one character"""
    size = int(getattr(f, 'size', PROBE_PX))
    im = Image.new('RGBA' if bitmap else 'L', (size * 3, size * 2), 0)
    ImageDraw.Draw(im).text((size // 2, size // 2), ch, font=f, fill=(255, 255, 255, 255) if bitmap else 255, embedded_color=bitmap)
    return hash(im.tobytes())


@functools.lru_cache(maxsize=1024)
def missing_print(fc):
    f, _ = load_face(fc, PROBE_PX)
    return glyph_print(f, MISSING, fc[3])


@functools.lru_cache(maxsize=50000)
def has_glyph(fc, ch):
    """True when the font really draws ch - not the empty box (or nothing) a font draws for a letter it doesn't have"""
    try:
        f, _ = load_face(fc, PROBE_PX)
        return glyph_print(f, ch, fc[3]) != missing_print(fc)
    except Exception:
        return False


def set_fallbacks(fonts):
    """After the scan: the fonts to borrow letters from, by name - and every other font as the last place to look"""
    FALLBACK['byname'] = {fd['name'].lower(): face(fd) for fd in fonts}
    FALLBACK['others'] = [face(fd) for fd in fonts if fd['main'] and not fd.get('bitmap')] + [face(fd) for fd in fonts if fd.get('bitmap')]
    FALLBACK['cache'] = {}


def fallback_for(ch):
    """The font to borrow ch from - emoji fonts first for emoji, symbol fonts for symbols, text fonts for letters - or None"""
    cache = FALLBACK['cache']
    if ch not in cache:
        cp = ord(ch)
        names = EMOJI_FONTS if cp >= 0x1F000 else SYMBOL_FONTS if 0x2000 <= cp < 0x2C00 else TEXT_FONTS
        chain = [FALLBACK['byname'][n.lower()] for n in names if n.lower() in FALLBACK['byname']]
        cache[ch] = next((fc for fc in chain if has_glyph(fc, ch)), None) or next((fc for fc in FALLBACK['others'] if has_glyph(fc, ch)), None)
    return cache[ch]


def runs_for(fc, text):
    """[(text, font)]: the words cut where the font changes - the chosen font, or for letters it lacks the font they come from"""
    runs = []
    for ch in text:
        cp = ord(ch)
        attached = ch in JOINERS or 0x1F3FB <= cp <= 0x1F3FF or unicodedata.category(ch) in ('Mn', 'Me', 'Cf')
        if attached and runs:
            use = runs[-1][1]                                       # accents, emoji joiners and skin tones go with what came before
        elif attached or ch.isspace() or has_glyph(fc, ch):
            use = fc                                                # spaces always in the chosen font - an emoji font's space is very wide
        else:
            use = fallback_for(ch) or fc
        if runs and runs[-1][1] == use:
            runs[-1][0] += ch
        else:
            runs.append([ch, use])
    if not RAQM:                                                    # without raqm Pillow can't join emoji sequences - the joiners would print as boxes
        runs = [[''.join(c for c in t if c not in JOINERS and not 0x1F3FB <= ord(c) <= 0x1F3FF), f] for t, f in runs]
    return [(t, f) for t, f in runs if t]


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Drawing the lettering
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def run_length(text, fc, px):
    f, scale = load_face(fc, px)
    return f.getlength(text) * scale


def line_width(fc, px, line, spacing):
    runs = runs_for(fc, line)
    if spacing == 0:
        return sum(run_length(t, f, px) for t, f in runs)
    letters = [(c, f) for t, f in runs for c in t]
    return sum(run_length(c, f, px) for c, f in letters) + spacing * max(0, len(letters) - 1)


def wrap_lines(fc, px, text, spacing, width):
    """Word-wrap each typed line to width dots.  A word wider than a whole line stays on its own line (it gets shrunk later)."""
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split(' '):
            trial = f'{line} {word}' if line else word
            if line and line_width(fc, px, trial, spacing) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def place_text(fc, px, lines, spacing, align):
    """[(x, baseline y, text, font)] for every run of every line (every letter, when the spacing is changed), lined up as align says"""
    ascent, descent = load_face(fc, px)[0].getmetrics()
    rows = []
    for line in lines:
        pieces, x = [], 0.0
        for text, rfc in runs_for(fc, line):
            for part in ([text] if spacing == 0 else list(text)):
                pieces.append((x, part, rfc))
                x += run_length(part, rfc, px) + spacing
        rows.append((pieces, x - spacing if pieces else 0))
    block = max((width for _, width in rows), default=0)
    placed = []
    for row, (pieces, width) in enumerate(rows):
        dx = 0 if align == 'Left' else (block - width) / 2 if align == 'Center' else block - width
        placed += [(dx + x, row * (ascent + descent) + ascent, part, rfc) for x, part, rfc in pieces]
    return placed


@functools.lru_cache(maxsize=64)
def bitmap_piece(text, fc, px):
    """A run in a color-bitmap emoji font as ink ('L', 255 = black, the darker the color the more ink), sized for px.
    Also how far its top sits above the baseline and its left edge before x."""
    f, scale = load_face(fc, px)
    ascent, descent = f.getmetrics()
    im = Image.new('RGBA', (int(f.getlength(text)) + 4, ascent + descent + 4), (255, 255, 255, 0))
    ImageDraw.Draw(im).text((2, ascent + 2), text, font=f, embedded_color=True, anchor='ls')
    ink = ImageOps.invert(Image.alpha_composite(Image.new('RGBA', im.size, (255, 255, 255, 255)), im).convert('L'))
    ink = ink.point(lambda v: min(255, int(v * 2.5)))               # darker, so light colors still print on a black-and-white printer
    return ink.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), LANCZOS), round((ascent + 2) * scale), round(2 * scale)


def piece_box(probe, x, y, s, rfc, px, stroke):
    if rfc[3]:
        ink, top, left = bitmap_piece(s, rfc, px)
        return x - left, y - top, x - left + ink.width, y - top + ink.height
    return probe.textbbox((x, y), s, font=load_face(rfc, px)[0], anchor='ls', stroke_width=stroke)


def draw_pieces(m, placed, px, ox, oy, stroke=0, bitmaps=False):
    """Draw the pieces into mask m (255 = ink) moved by ox, oy: the font pieces (stroke = how much fatter), or with bitmaps=True only the
    color-bitmap emoji - those can't be made fatter or outlined, so they go on top as they are"""
    d = ImageDraw.Draw(m)
    for x, y, s, rfc in placed:
        if not s.strip() or rfc[3] != bitmaps:
            continue
        if not bitmaps:
            d.text((x + ox, y + oy), s, font=load_face(rfc, px)[0], fill=255, anchor='ls', stroke_width=stroke, stroke_fill=255)
            continue
        ink, top, left = bitmap_piece(s, rfc, px)
        box = (round(x + ox - left), round(y + oy - top))
        box = box + (box[0] + ink.width, box[1] + ink.height)
        m.paste(ImageChops.lighter(m.crop(box), ink), box)
    return m


@functools.lru_cache(maxsize=4)
def pattern(width, height, name):
    """A fill pattern the size of the lettering: 255 where ink may go.  Built from 8x8 tiles, one row at a time."""
    tiles = {'Gray': lambda x, y: (x + y) % 2 == 0, 'Stripes': lambda x, y: (x + y) % 8 < 3, 'Dots': lambda x, y: x % 4 < 2 and y % 4 < 2}
    tile = tiles[name]
    rows = [(bytes(255 if tile(x, y) else 0 for x in range(8)) * (width // 8 + 1))[:width] for y in range(8)]
    return Image.frombytes('L', (width, height), b''.join(rows[y % 8] for y in range(height)))


def lettering(fd, text, px, o, wrap_width=None):
    """The words in font fd at px: black on white ('L'), cropped to the ink, with Thicker, Spacing, Outline, Shadow and Inside drawn in"""
    fc = face(fd)
    spacing = round(px * o['spacing'] / 100)
    lines = wrap_lines(fc, px, text, spacing, wrap_width) if wrap_width else text.split('\n')
    placed = place_text(fc, px, lines, spacing, o['align'])
    thick = round(px * o['thick'] * 0.012)
    ring = max(2, round(px * 0.045)) if o['outline'] else 0
    shadow = max(2, round(px * 0.08)) if o['shadow'] else 0
    gap = max(1, round(px * 0.025)) if o['shadow'] else 0
    reach = thick + ring + gap
    probe = ImageDraw.Draw(Image.new('L', (1, 1)))
    boxes = [piece_box(probe, x, y, s, rfc, px, reach) for x, y, s, rfc in placed if s.strip()]
    if not boxes:
        return Image.new('L', (1, 1), 255), len(lines)
    x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
    width, height = int(max(b[2] for b in boxes) - x0) + shadow + 6, int(max(b[3] for b in boxes) - y0) + shadow + 6
    if width * height > 60_000_000:
        raise ValueError('too big to draw')
    ox, oy = 3 - x0, 3 - y0

    def mask(stroke, dx=0, dy=0):
        return draw_pieces(Image.new('L', (width, height), 0), placed, px, ox + dx, oy + dy, stroke)

    body = mask(thick)
    inside = None if o['pattern'] == 'Solid' else ImageChops.darker(body, pattern(width, height, o['pattern']))
    if ring:                                                        # Outline: the ring around each letter, hollow - or the pattern inside
        ink = ImageChops.subtract(mask(thick + ring), body)
        ink = ImageChops.lighter(ink, inside) if inside else ink
    else:
        ink = inside or body
    if shadow:
        ink = ImageChops.lighter(ink, ImageChops.subtract(mask(thick + ring, shadow, shadow), mask(reach)))
    if any(rfc[3] for _, _, _, rfc in placed):
        ink = ImageChops.lighter(ink, draw_pieces(Image.new('L', (width, height), 0), placed, px, ox, oy, bitmaps=True))
    box = ink.getbbox()
    return (ImageOps.invert(ink).crop(box) if box else Image.new('L', (1, 1), 255)), len(lines)


def cap_height(fd, px):
    """How tall a capital H is, in dots - what the Size in mm means"""
    box = font_at(fd, REF_PX).getbbox('H')
    ref = box[3] - box[1] if box and box[3] > box[1] else REF_PX * 0.7
    return ref * px / REF_PX


def px_for_mm(fd, mm):
    return max(4, lib.mm_dots(mm) * REF_PX / cap_height(fd, REF_PX))


def framed(art, o):
    """The lettering with room around it, a frame and white-on-black when asked"""
    if not (o['reverse'] or o['frame']):
        return art
    block = Image.new('L', (art.width + 2 * BLOCK_PAD, art.height + 2 * BLOCK_PAD), 255)
    block.paste(art, (BLOCK_PAD, BLOCK_PAD))
    if o['frame']:
        ImageDraw.Draw(block).rectangle((0, 0, block.width - 1, block.height - 1), outline=0, width=FRAME)
    return ImageOps.invert(block) if o['reverse'] else block


def make_print(fd, text, paper_w, o):
    """(paper picture 'L' as it prints, info line, notes, cap height mm).  Banner: the lettering turned to run down the strip."""
    text = text.rstrip() or ' '
    room = 2 * BLOCK_PAD if (o['reverse'] or o['frame']) else 0
    target = paper_w - 2 * MARGIN - room                            # across the paper, for the lettering itself
    notes = []
    banner = o['mode'] == BANNER
    measure = (lambda img: img.height) if banner else (lambda img: img.width)
    wrap = None
    if o['fill']:
        ref, _ = lettering(fd, text, REF_PX, o)
        px = REF_PX * target / max(1, measure(ref))
    else:
        px = px_for_mm(fd, o['mm'])
        wrap = None if banner else target
    estimate = line_width(face(fd), px, max(text.split('\n'), key=len), 0) / lib.DPI
    if banner and estimate > TOO_LONG_IN:
        raise ValueError(f'about {estimate:.0f} inches long - shorten the words or pick a smaller size')
    art, lines = lettering(fd, text, px, o, wrap)
    for attempt in range(3):                                        # a little smaller until it really fits across the paper
        if measure(art) <= target:
            break
        px *= target / measure(art) * 0.995
        art, lines = lettering(fd, text, px, o, wrap)
        if not o['fill'] and attempt == 0:
            notes.append('Shrunk to fit the paper' if banner else 'A word was too wide - shrunk to fit')
    block = framed(art, o)
    if banner:
        block = block.rotate(270 if o['direction'] == 'start' else 90, expand=True)
        ends = lib.mm_dots(o['ends'])
        paper = Image.new('L', (paper_w, block.height + 2 * ends), 255)
        paper.paste(block, ((paper_w - block.width) // 2, ends))
    else:
        x = {'Left': MARGIN, 'Center': (paper_w - block.width) // 2, 'Right': paper_w - MARGIN - block.width}[o['align']]
        paper = Image.new('L', (paper_w, block.height + 2 * TOP), 255)
        paper.paste(block, (max(0, x), TOP))
    cap_mm = cap_height(fd, px) / lib.DOTS_PER_MM
    inches = paper.height / lib.DPI
    if banner:
        info = f'Banner {inches:.1f} in long  -  capitals {cap_mm:.0f} mm tall'
    else:
        info = f'{lines} line{"s" if lines != 1 else ""}  -  capitals {cap_mm:.0f} mm tall  -  {inches:.1f} in of paper'
    if inches > LONG_PRINT_IN:
        notes.append(f'Long - {inches:.0f} in')
    if o['reverse'] and not o['slow']:
        notes.append('Reverse prints a lot of black - turn on Slow')
    return paper, info, notes, cap_mm


def job_bytes(img1, media, copies, darkness, slow):
    """The print job at this darkness and speed (Slow = 2 in/s, else Setup's).  The same commands as id880_lib's jobs."""
    speed = 2 if slow else int(float(lib.setting('speed')))
    darkness, copies = max(0, min(30, int(darkness))), max(1, int(copies))
    offset = lib.media_offset(media)
    if lib.setting('language') == 'TSPL':
        head = [f'SIZE {lib.HEAD_DOTS / lib.DOTS_PER_MM:.1f} mm,{img1.height / lib.DOTS_PER_MM:.1f} mm', 'GAP 0 mm,0 mm', 'DIRECTION 1', f'REFERENCE {offset},0',
                f'DENSITY {round(darkness / 2)}', f'SPEED {speed}', 'SET TEAR ON', 'CLS', f'BITMAP 0,0,{img1.width // 8},{img1.height},0,']
        return '\r\n'.join(head).encode('ascii') + img1.tobytes() + f'\r\nPRINT 1,{copies}\r\n'.encode('ascii')
    lines = [f'~SD{darkness:02d}', '^XA', '^MTD', '^MMT', '^MNN', f'^PW{lib.HEAD_DOTS}', f'^LL{img1.height}', f'^LH{offset},0', f'^PR{speed}',
             '^FO0,0' + lib.zpl_graphic(img1) + '^FS', f'^PQ{copies}', '^XZ']
    return '\n'.join(lines).encode('ascii')


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Pictures for the window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
@functools.lru_cache(maxsize=600)
def sample_png(fc, words):
    """The words in one font (borrowing the letters it lacks), light on clear, for its row in the font list.  None if it can't draw them."""
    try:
        placed = place_text(fc, SAMPLE_PX, [words], 0, 'Left')
        m = draw_pieces(Image.new('L', (GALLERY_W - 16, SAMPLE_PX * 3), 0), placed, SAMPLE_PX, 0, SAMPLE_PX // 2)
        m = draw_pieces(m, placed, SAMPLE_PX, 0, SAMPLE_PX // 2, bitmaps=True)
        box = m.getbbox()
        if not box:
            return None
        m = m.crop((0, box[1], m.width, box[3]))                    # just the ink, top to bottom - tall fonts get shrunk to fit the row
        if m.height > SAMPLE_MAX_H:
            m = m.resize((max(1, round(m.width * SAMPLE_MAX_H / m.height)), SAMPLE_MAX_H), LANCZOS)
        img = Image.new('RGBA', m.size, (230, 234, 242, 0))
        img.putalpha(m)
        return lib.png_bytes(img)
    except Exception:
        return None


def ruler_steps(px_per_inch):
    return next((n for n in (1, 2, 5, 10, 20, 50) if n * px_per_inch >= 44), 100)


def preview_png(paper, o, width):
    """What will print, for the window: a banner turned so it reads left to right, with inch marks along it"""
    banner = o['mode'] == BANNER
    strip = paper.rotate(90 if o['direction'] == 'start' else 270, expand=True) if banner else paper
    scale = min(MAX_SCALE if banner else 1.0, (width - 70) / strip.width)
    small = strip.resize((max(1, round(strip.width * scale)), max(1, round(strip.height * scale))), LANCZOS).convert('RGB')
    inch = lib.DPI * scale
    step = ruler_steps(inch)
    try:
        tick_font = ImageFont.load_default(size=12)
    except TypeError:
        tick_font = None
    if banner:
        img = Image.new('RGB', (small.width + 24, small.height + 40), PREVIEW_BG)
        img.paste(small, (12, 10))
        d = ImageDraw.Draw(img)
        for n in range(int(strip.width / lib.DPI) + 1):
            x = 12 + n * inch
            d.line((x, small.height + 12, x, small.height + (22 if n % step == 0 else 17)), fill='#aab4c3', width=1)
            if n % step == 0:
                d.text((x + 2, small.height + 22), f'{n}"', fill='#aab4c3', font=tick_font)
    else:
        img = Image.new('RGB', (small.width + 54, small.height + 24), PREVIEW_BG)
        img.paste(small, (42, 12))
        d = ImageDraw.Draw(img)
        for n in range(int(strip.height / lib.DPI) + 1):
            y = 12 + n * inch
            d.line((40 - (12 if n % step == 0 else 6), y, 40, y), fill='#aab4c3', width=1)
            if n % step == 0:
                d.text((4, y + 1), f'{n}"', fill='#aab4c3', font=tick_font)
    return lib.png_bytes(img)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  The window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def toggle_text(key, on):
    return ('☑ ' if on else '☐ ') + TOGGLES[key]


def toggle(key, on, tip):
    return sg.Button(toggle_text(key, on), key=key, button_color=ON_COLORS if on else OFF_COLORS, tooltip=f' {tip} ', border_width=0)


def show_toggle(window, key, on):
    window[key].update(toggle_text(key, on), button_color=ON_COLORS if on else OFF_COLORS)


def slider(key, rng, value, tip, length=18):
    return sg.Slider(rng, value, orientation='h', key=key, size=(length, 14), enable_events=True, tooltip=f' {tip} ', font=LIST_FONT,
                     trough_color=PANEL2, background_color=BG)


def frame(title, color, rows):
    return sg.Frame(f' {title} ', rows, title_color=color, font=BOLD, relief=sg.RELIEF_GROOVE, pad=(5, 4), vertical_alignment='top')


def max_mm(media):
    return max(6, int((lib.media_width(media) - 2 * MARGIN) / lib.DOTS_PER_MM))


def style_menus(window):
    """ Flat right-click menus in this program's colors (bd=0, activeborderwidth=1), sub-menus included - never Windows gray """
    colors = dict(bg=PANEL, fg=C_TEXT, activebackground=C_SEL, activeforeground='#ffffff', disabledforeground=C_DIM)
    menus = {id(m): m for m in [window.TKRightClickMenu] + [e.TKRightClickMenu for e in window.element_list()] if m is not None}

    def style(menu):
        try:
            menu.configure(bd=0, relief='flat', activeborderwidth=1, **colors)
        except sg.tk.TclError:
            return
        for child in menu.winfo_children():
            if isinstance(child, sg.tk.Menu):
                style(child)
    for menu in menus.values():
        style(menu)


def fit_min_size(window):
    """ The smallest the window may get: what its rows need at their layout size - so its bottom rows are never cut off """
    root = window.TKroot
    root.update_idletasks()
    window.set_min_size((min(root.winfo_reqwidth(), root.winfo_screenwidth() - 40), min(root.winfo_reqheight(), root.winfo_screenheight() - 80)))


def make_window(state):
    o, flt = state['options'], state['filters']
    left = [[sg.Text('Fonts', font=HEAD, text_color=C_FONTS), sg.Text('', key=K_COUNT, text_color=C_DIM, font=LIST_FONT), sg.Push(), sg.Text('Search', font=LIST_FONT),
             sg.Input('', key=K_SEARCH, size=(16, 1), enable_events=True, tooltip=' Search the font names - Ctrl+F.  Down or Enter: back to the list.  Esc clears ')],
            [toggle(K_FAV_ONLY, flt['fav_only'], 'Only your favorites (★ - Ctrl+D marks one)'),
             toggle(K_FAMILY, flt['family_only'], 'One font per family - fewer to flip through'),
             toggle(K_SHOW_HIDDEN, flt['show_hidden'], 'Show the fonts you hid (dimmed) - Del brings one back')],
            [sg.Graph((GALLERY_W, ROWS * ROW_H), (0, ROWS * ROW_H), (GALLERY_W, 0), key=K_GALLERY, enable_events=True, background_color=PANEL, pad=((5, 0), 4)),
             sg.Slider((0, 1), 0, orientation='v', key=K_SLIDER, size=(int(ROWS * ROW_H / 21), 16), enable_events=True, disable_number_display=True,
                       trough_color=PANEL2, background_color=BG, pad=(2, 4), tooltip=' Drag to jump through the list ')],
            [sg.Button('◀', key=K_PREV, size=(4, 1), font=BOLD, tooltip=' Previous font - Up, Left, the mouse wheel '),
             sg.Button('▶', key=K_NEXT, size=(4, 1), font=BOLD, tooltip=' Next font - Down, Right, the mouse wheel '),
             sg.Button('★ Favorite', key=K_FAV, tooltip=' Ctrl+D '), sg.Button('Random', key=K_RANDOM, tooltip=' Ctrl+R '),
             sg.Button('Hide', key=K_HIDE, tooltip=' Del - Hidden shows it again ')],
            [sg.Text('', key=K_FONT_NAME, font=HEAD, text_color=C_STAR, size=(38, 1))]]
    mode_row = [sg.Button('▬  Banner - down the strip', key=K_BANNER, font=BOLD, size=(24, 1), button_color=ON_COLORS if o['mode'] == BANNER else MODE_OFF,
                          tooltip=' The words run along the strip, as tall as the paper is wide '),
                sg.Button('☰  Across the paper', key=K_ACROSS, font=BOLD, size=(20, 1), button_color=ON_COLORS if o['mode'] == ACROSS else MODE_OFF,
                          tooltip=' The words read across the paper, line after line '),
                sg.Text('', key=K_INFO, text_color=C_TEXT, expand_x=True, justification='right')]
    preview = sg.Column([[sg.Image(key=K_PREVIEW, background_color=PREVIEW_BG)]], key=K_PREVIEW_COL, scrollable=True, size=(PREVIEW_W, PREVIEW_H),
                        background_color=PREVIEW_BG, expand_x=True, expand_y=True)
    top = max_mm(o['media'])
    size = frame('Size', C_SIZE, [[toggle(K_FILL, o['fill'], 'As big as the paper allows')],
                                  [slider(K_MM, (3, top), min(o['mm'], top), 'How tall the capital letters are, in mm - turns Fill off', 16)],
                                  [sg.Text('', key=K_SIZE_TEXT, text_color=C_DIM, font=LIST_FONT, size=(24, 1))]])
    dark = frame('Darkness', C_DARK, [[slider(K_DARKNESS, (1, 30), o['darkness'], f'1 = lightest, 30 = darkest.  Setup says {lib.setting("darkness")}', 14)],
                                      [toggle(K_SLOW, o['slow'], 'Prints slower so big black areas come out black, not gray')]])
    paper = frame('Paper', C_PAPER, [[sg.Combo(lib.MEDIA, o['media'], key=K_MEDIA, readonly=True, enable_events=True, size=(14, 1)),
                                      sg.Text('Copies'), sg.Spin(list(range(1, 21)), 1, key=K_COPIES, size=(3, 1))],
                                     [sg.pin(sg.Column([[sg.Text('Blank ends', font=LIST_FONT),
                                                         slider(K_ENDS, (0, 60), o['ends'], 'Blank paper before and after the banner, in mm', 12)]],
                                                       key=K_ENDS_ROW, pad=0, visible=o['mode'] == BANNER))]])
    style = frame('Style', C_STYLE, [[sg.Text('Thicker', font=LIST_FONT), slider(K_THICK, (0, 10), o['thick'], 'Fatter letters - 0 is the font as drawn', 14),
                                      sg.Text('Spacing', font=LIST_FONT), slider(K_SPACING, (-10, 40), o['spacing'], 'Room between the letters', 14)],
                                     [toggle(K_OUTLINE, o['outline'], 'Hollow letters - a line around each one'),
                                      toggle(K_SHADOW, o['shadow'], 'A shadow down and to the right'),
                                      toggle(K_REVERSE, o['reverse'], 'White letters on black - use Slow'),
                                      toggle(K_FRAME, o['frame'], 'A line around the lettering'),
                                      sg.Button(f'Inside: {o["pattern"]}', key=K_PATTERN, tooltip=' Solid, Gray, Stripes or Dots inside the letters - click for the next '),
                                      sg.pin(sg.Button(direction_text(o), key=K_DIRECTION, visible=o['mode'] == BANNER, tooltip=' Which end of the banner prints first ')),
                                      sg.pin(sg.Button(f'Line up: {o["align"]}', key=K_ALIGN, visible=o['mode'] == ACROSS, tooltip=' Left, Center or Right '))]])
    print_row = [sg.Button('Print', key=K_PRINT, size=(12, 1), font=HEAD, button_color=PRINT_COLORS, tooltip=' Ctrl+P '), sg.Button('Feed 1 inch', key=K_FEED),
                 sg.Button('Printer setup', key=K_SETUP), sg.Button('Reset style', key=K_RESET, tooltip=' Size, thickness, spacing and every style back to the start '),
                 sg.Text(lib.printer_summary(), key=K_STATUS, text_color=C_DIM, font=LIST_FONT, expand_x=True)]
    right = [[sg.Text('Your words', font=HEAD, text_color=C_WORDS), sg.Text('Tab: back to flipping fonts', text_color=C_DIM, font=LIST_FONT)],
             [sg.Multiline(state['text'], key=K_TEXT, size=(60, 2), font=('Segoe UI', 13), expand_x=True, enable_events=True, no_scrollbar=True)],
             mode_row, [preview], [size, dark, paper], [style]]
    layout = [[sg.Image(ICON, subsample=2), sg.Text(TITLE, font=('Segoe UI', 14, 'bold'), text_color=C_FONTS), sg.Text(f'v{VERSION}', text_color=C_DIM)],
              [sg.Column(left, vertical_alignment='top', pad=0), sg.Column(right, vertical_alignment='top', expand_x=True, expand_y=True, pad=0)],
              print_row]
    menu = ['', ['Rescan fonts', 'Reset style', '---', 'Edit Me', f'Version {VERSION}::Version', 'Exit']]
    window = sg.Window(f'{TITLE}  {VERSION}', layout, font=FONT, resizable=True, finalize=True, icon=ICON, right_click_menu=menu, margins=(8, 6))
    style_menus(window)
    fit_min_size(window)
    for tk_key, key in (('<Up>', K_UP), ('<Down>', K_DOWN), ('<Left>', K_UP), ('<Right>', K_DOWN), ('<Prior>', K_PGUP), ('<Next>', K_PGDN), ('<Home>', K_HOME),
                        ('<End>', K_END), ('<Alt-Up>', K_ALT_UP), ('<Alt-Down>', K_ALT_DOWN), ('<Delete>', K_DEL), ('<Escape>', K_ESCAPE),
                        ('<Control-f>', K_CTRL_F), ('<Control-d>', K_CTRL_D), ('<Control-r>', K_CTRL_R)):
        window.bind(tk_key, key)
    lib.bind_print_key(window, K_PRINT)                             # Ctrl+P - and Ctrl+Alt+P never prints
    for letter in 'fdrFDR':                                         # Ctrl+Alt + a letter belongs to Mike's system hotkeys
        window.TKroot.bind(f'<Control-Alt-{letter}>', lambda e: 'break')
    graph = window[K_GALLERY]
    if sys.platform.startswith('linux'):
        graph.bind('<Button-4>', '+UP')
        graph.bind('<Button-5>', '+DOWN')
    else:
        graph.bind('<MouseWheel>', '+WHEEL')                       # Windows' Button-4 is the mouse's Back button - not the wheel
    window[K_SEARCH].bind('<Return>', '+ENTER')
    window[K_TEXT].Widget.bind('<Tab>', lambda e: (graph.Widget.focus_set(), 'break')[1])
    window[K_PREVIEW_COL].bind('<Configure>', '+RESIZE')
    return window


def direction_text(o):
    return 'Direction: start first' if o['direction'] == 'start' else 'Direction: end first'


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  The font list
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def filter_fonts(state):
    """The fonts the list shows, after the search, ★ only, One per family and Hidden"""
    flt, query = state['filters'], state['query'].strip().lower()
    shown = []
    for fd in state['fonts']:
        name = fd['name']
        if fd.get('bitmap'):                                        # color-bitmap emoji fonts only lend their emoji
            continue
        if name in state['hidden'] and not flt['show_hidden']:
            continue
        if flt['fav_only'] and name not in state['favorites']:
            continue
        if flt['family_only'] and not fd['main'] and name not in state['favorites']:
            continue
        if query and query not in name.lower():
            continue
        shown.append(fd)
    return shown


def refilter(window, state):
    """New list after a filter change - stay on the same font if it is still in it"""
    current = state['font']
    state['shown'] = filter_fonts(state)
    names = [fd['name'] for fd in state['shown']]
    if current in names:
        state['cur'] = names.index(current)
    else:                                                           # the font that was showing is filtered out: the one next to it in A-Z order
        state['cur'] = max(0, min(bisect.bisect_left([n.lower() for n in names], current.lower()), len(names) - 1))
    state['top'] = max(0, state['cur'] - ROWS // 2)
    show_list(window, state)


def words_sample(state):
    first = next((line for line in state['text'].split('\n') if line.strip()), '')
    return (first.strip() or 'AaBbCc 123')[:40]


def show_list(window, state):
    """Draw the visible rows of the font list, the slider, the count and the font's name"""
    g, shown = window[K_GALLERY], state['shown']
    g.erase()
    if state['scanning']:
        g.draw_text(state['scanning'], (GALLERY_W // 2, 40), color=C_DIM, font=FONT)
        return
    total = sum(1 for fd in state['fonts'] if not fd.get('bitmap'))
    window[K_COUNT].update(f'{len(shown)} of {total}' if len(shown) != total else f'{total}')
    if not shown:
        g.draw_text('No fonts match', (GALLERY_W // 2, 40), color=C_DIM, font=FONT)
        window[K_FONT_NAME].update('')
        return
    cur = max(0, min(state['cur'], len(shown) - 1))
    state['cur'] = cur
    ahead = 2                                                       # rows kept showing past the chosen font, so you see what comes next
    state['top'] = max(0, min(max(state['top'], cur - ROWS + 1 + ahead), cur - ahead, len(shown) - ROWS))
    sample = words_sample(state)
    for row in range(ROWS):
        i = state['top'] + row
        if i >= len(shown):
            break
        fd, y = shown[i], row * ROW_H
        name = fd['name']
        hidden, favorite = name in state['hidden'], name in state['favorites']
        g.draw_rectangle((0, y), (GALLERY_W, y + ROW_H - 1), fill_color=C_SEL if i == cur else (PANEL if row % 2 == 0 else PANEL2), line_color=BG)
        label = ('★ ' if favorite else '') + name + ('   (hidden)' if hidden else '')
        g.draw_text(label, (8, y + 3), color=C_STAR if favorite else C_HIDDEN if hidden else (C_TEXT if i == cur else C_DIM), font=LIST_FONT,
                    text_location=sg.TEXT_LOCATION_TOP_LEFT)
        png = sample_png(face(fd), sample)
        if png:
            g.draw_image(data=png, location=(8, y + 20))
        else:
            g.draw_text("can't draw these letters", (8, y + 24), color=C_HIDDEN, font=LIST_FONT, text_location=sg.TEXT_LOCATION_TOP_LEFT)
    window[K_SLIDER].update(value=cur, range=(0, max(1, len(shown) - 1)))
    fd = shown[cur]
    state['font'] = fd['name']
    window[K_FONT_NAME].update(('★ ' if fd['name'] in state['favorites'] else '') + fd['name'], text_color=C_STAR if fd['name'] in state['favorites'] else C_FONTS)
    window[K_FAV].update('★ Unfavorite' if fd['name'] in state['favorites'] else '★ Favorite')
    window[K_HIDE].update('Unhide' if fd['name'] in state['hidden'] else 'Hide')


def move_to(window, state, index):
    if not state['shown']:
        return
    index = max(0, min(index, len(state['shown']) - 1))
    if index != state['cur'] or state['shown'][index]['name'] != state['font']:
        state['cur'] = index
        show_list(window, state)
        lib.save_setting('ban_font', state['font'])
        state['dirty'] = True


def current_font(state):
    return state['shown'][state['cur']] if state['shown'] else None


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Preview and printing
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def render(window, state):
    """Draw what will print for the current font, words and options"""
    fd, o = current_font(state), state['options']
    state['paper'] = None
    if fd is None:
        return
    try:
        paper, info, notes, cap_mm = make_print(fd, state['text'], lib.media_width(o['media']), o)
    except Exception as e:
        window[K_INFO].update(f"Can't draw this: {e}", text_color=C_WARN)
        window[K_PREVIEW].update(data=None)
        return
    state['paper'] = paper
    window[K_INFO].update(info + ('   -   ' + '   -   '.join(notes) if notes else ''), text_color=C_WARN if notes else C_TEXT)
    window[K_SIZE_TEXT].update(f'Capitals {cap_mm:.0f} mm tall' + ('  (Fill)' if o['fill'] else ''))
    if o['fill']:                                                   # the slider shows the size Fill picked, so turning Fill off starts there
        window[K_MM].update(value=max(3, min(max_mm(o['media']), round(cap_mm))))
    show_preview(window, state)


def show_preview(window, state):
    if state.get('paper') is None:
        return
    width = window[K_PREVIEW_COL].Widget.winfo_width()
    width = width if width > 100 else PREVIEW_W
    state['preview_w'] = width
    window[K_PREVIEW].update(data=preview_png(state['paper'], state['options'], width))
    window.refresh()
    window[K_PREVIEW_COL].contents_changed()


def do_print(window, state, values):
    o = state['options']
    render(window, state)
    if state.get('paper') is None:
        return
    img1 = lib.to_1bit(state['paper'])
    copies = int(values[K_COPIES] or 1)
    inches = img1.height * copies / lib.DPI
    if inches > LONG_PRINT_IN and sg.popup_yes_no(f'This uses {inches:.0f} inches of paper.  Print it?', title=TITLE, keep_on_top=True, font=FONT) != 'Yes':
        return
    try:
        sent = lib.send_raw(job_bytes(img1, o['media'], copies, o['darkness'], o['slow']))
        window[K_STATUS].update(f'Printed {state["font"]}: {sent}    ({lib.printer_summary()})', text_color=C_OK)
    except Exception as e:
        window[K_STATUS].update('Print failed - see the message', text_color=C_BAD)
        lib.popup_print_error(e)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Main
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def load_state():
    options = dict(DEFAULT_OPTIONS)
    options.update({k: v for k, v in (lib.setting('ban_options') or {}).items() if k in DEFAULT_OPTIONS})
    if options['darkness'] is None:
        options['darkness'] = int(float(lib.setting('darkness') or 15))
    if options['media'] not in lib.MEDIA:
        options['media'] = lib.RECEIPT
    filters = {'fav_only': False, 'family_only': False, 'show_hidden': False}
    filters.update({k: bool(v) for k, v in (lib.setting('ban_filters') or {}).items() if k in filters})
    return {'options': options, 'filters': filters, 'text': clean_text(lib.setting('ban_text') or DEFAULT_TEXT), 'font': lib.setting('ban_font') or '',
            'favorites': set(lib.setting('ban_favorites') or []), 'hidden': set(lib.setting('ban_hidden') or []), 'fonts': [], 'shown': [], 'cur': 0, 'top': 0,
            'query': '', 'scanning': 'Finding the fonts on this computer...', 'dirty': False, 'paper': None}


def start_scan(window, state):
    state['scanning'] = 'Finding the fonts on this computer...'
    show_list(window, state)
    threading.Thread(target=lambda: window.write_event_value(K_SCAN_DONE, scan_fonts(window)), daemon=True).start()


def focus_list(window):
    window[K_GALLERY].Widget.focus_set()


def typing(window):
    try:
        return lib.typing_has_focus(window)
    except Exception:
        return False


def save_options(state):
    lib.save_setting('ban_options', state['options'])


def set_mode(window, state, mode):
    o = state['options']
    o['mode'] = mode
    window[K_BANNER].update(button_color=ON_COLORS if mode == BANNER else MODE_OFF)
    window[K_ACROSS].update(button_color=ON_COLORS if mode == ACROSS else MODE_OFF)
    window[K_DIRECTION].update(visible=mode == BANNER)
    window[K_ALIGN].update(visible=mode == ACROSS)
    window[K_ENDS_ROW].update(visible=mode == BANNER)


def show_options(window, state):
    """Every option control set from state['options'] (after Reset style)"""
    o = state['options']
    for key, name in OPTION_TOGGLES.items():
        show_toggle(window, key, o[name])
    for key, name in SLIDERS.items():
        window[key].update(value=o[name])
    window[K_PATTERN].update(f'Inside: {o["pattern"]}')
    window[K_DIRECTION].update(direction_text(o))
    window[K_ALIGN].update(f'Line up: {o["align"]}')
    set_mode(window, state, o['mode'])


def main():
    state = load_state()
    window = make_window(state)
    start_scan(window, state)
    focus_list(window)
    while True:
        event, values = window.read(timeout=60 if state['dirty'] else None)
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        o = state['options']
        if values and clean_text(values[K_TEXT].rstrip('\n')) != state['text']:  # words and search are read from the values every time: a key
            state['text'] = clean_text(values[K_TEXT].rstrip('\n'))                  # the window also binds (Del) sends only the window's event
            lib.save_setting('ban_text', state['text'])
            show_list(window, state)
            state['dirty'] = True
        if values and values[K_SEARCH] != state['query'] and not state['scanning']:
            state['query'] = values[K_SEARCH]
            refilter(window, state)
            state['dirty'] = True
        if event == sg.TIMEOUT_KEY:
            if state['dirty']:
                state['dirty'] = False
                render(window, state)
            continue
        if event == K_ESCAPE:
            if values[K_SEARCH]:
                window[K_SEARCH].update('')
                state['query'] = ''
                refilter(window, state)
                state['dirty'] = True
                focus_list(window)
                continue
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, f'{TITLE}  version {VERSION}', '', f'Settings: {sg.user_settings_filename()}', f'Fonts found: {len(state["fonts"])}', '',
                              sg.get_versions(), keep_on_top=True, non_blocking=True, size=(80, 12), font=FONT)
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == 'Rescan fonts':
            start_scan(window, state)
        elif event == K_SCAN_PROGRESS:
            done, total = values[event]
            state['scanning'] = f'Finding the fonts on this computer...  {done} of {total} files'
            show_list(window, state)
        elif event == K_SCAN_DONE:
            state['fonts'], state['scanning'] = values[event], ''
            set_fallbacks(state['fonts'])
            names = {fd['name'] for fd in state['fonts']}
            if state['font'] not in names:
                state['font'] = next((n for n in FAVORITE_FONTS if n in names), state['fonts'][0]['name'] if state['fonts'] else '')
            refilter(window, state)
            state['dirty'] = True
        elif event in (K_TEXT, K_SEARCH):
            pass                                                    # done above
        elif event == K_SEARCH_ENTER or (event == K_DOWN and window.find_element_with_focus() is window[K_SEARCH]):
            focus_list(window)
        elif event == K_CTRL_F:
            window[K_SEARCH].set_focus()
            window[K_SEARCH].Widget.select_range(0, 'end')
        elif event in (K_UP, K_DOWN, K_PGUP, K_PGDN, K_HOME, K_END):
            if not typing(window):
                move_to(window, state, 0 if event == K_HOME else len(state['shown']) - 1 if event == K_END else state['cur'] + STEP[event])
        elif event in (K_ALT_UP, K_ALT_DOWN, K_PREV, K_NEXT, K_WHEEL_UP, K_WHEEL_DOWN):
            move_to(window, state, state['cur'] + STEP[event])
        elif event == K_WHEEL:
            delta = getattr(window[K_GALLERY].user_bind_event, 'delta', 0)
            move_to(window, state, state['cur'] + (-1 if delta > 0 else 1))
        elif event == K_GALLERY:
            x, y = values[K_GALLERY]
            if y is not None and 0 <= y < ROWS * ROW_H:
                move_to(window, state, state['top'] + int(y // ROW_H))
            focus_list(window)
        elif event == K_SLIDER:
            move_to(window, state, int(values[K_SLIDER]))
        elif event in (K_RANDOM, K_CTRL_R) and state['shown']:
            move_to(window, state, random.randrange(len(state['shown'])))
            focus_list(window)
        elif event in (K_FAV, K_CTRL_D) and state['shown']:
            name = state['font']
            state['favorites'] ^= {name}
            lib.save_setting('ban_favorites', sorted(state['favorites'], key=str.lower))
            window[K_STATUS].update(f'★ {name} is a favorite' if name in state['favorites'] else f'{name} is no longer a favorite', text_color=C_STAR)
            refilter(window, state) if state['filters']['fav_only'] else show_list(window, state)
            focus_list(window)
        elif (event == K_HIDE or (event == K_DEL and not typing(window))) and state['shown']:
            name = state['font']
            state['hidden'] ^= {name}
            lib.save_setting('ban_hidden', sorted(state['hidden'], key=str.lower))
            gone = name in state['hidden']
            window[K_STATUS].update(f'Hid {name} - Hidden shows it again' if gone else f'{name} is back in the list', text_color=C_WARN)
            if gone and not state['filters']['show_hidden']:
                cur = state['cur']
                state['shown'] = filter_fonts(state)
                state['cur'] = min(cur, len(state['shown']) - 1)
                show_list(window, state)
                if state['shown']:
                    lib.save_setting('ban_font', state['font'])
            else:
                show_list(window, state)
            state['dirty'] = True
            focus_list(window)
        elif event in FILTER_TOGGLES:
            name = FILTER_TOGGLES[event]
            state['filters'][name] = not state['filters'][name]
            show_toggle(window, event, state['filters'][name])
            lib.save_setting('ban_filters', state['filters'])
            refilter(window, state)
            state['dirty'] = True
            focus_list(window)
        elif event in (K_BANNER, K_ACROSS):
            set_mode(window, state, BANNER if event == K_BANNER else ACROSS)
            save_options(state)
            state['dirty'] = True
            focus_list(window)
        elif event in OPTION_TOGGLES:
            name = OPTION_TOGGLES[event]
            o[name] = not o[name]
            if event == K_FILL and not o['fill']:
                o['mm'] = int(values[K_MM])
            show_toggle(window, event, o[name])
            save_options(state)
            state['dirty'] = True
            focus_list(window)
        elif event in SLIDERS:
            o[SLIDERS[event]] = int(values[event])
            if event == K_MM and o['fill']:
                o['fill'] = False
                show_toggle(window, K_FILL, False)
            save_options(state)
            state['dirty'] = True
        elif event == K_PATTERN:
            o['pattern'] = PATTERNS[(PATTERNS.index(o['pattern']) + 1) % len(PATTERNS)]
            window[K_PATTERN].update(f'Inside: {o["pattern"]}')
            save_options(state)
            state['dirty'] = True
            focus_list(window)
        elif event == K_DIRECTION:
            o['direction'] = 'end' if o['direction'] == 'start' else 'start'
            window[K_DIRECTION].update(direction_text(o))
            save_options(state)
            state['dirty'] = True
            focus_list(window)
        elif event == K_ALIGN:
            o['align'] = ALIGNS[(ALIGNS.index(o['align']) + 1) % len(ALIGNS)]
            window[K_ALIGN].update(f'Line up: {o["align"]}')
            save_options(state)
            state['dirty'] = True
            focus_list(window)
        elif event == K_MEDIA:
            o['media'] = values[K_MEDIA]
            top = max_mm(o['media'])
            o['mm'] = min(o['mm'], top)
            window[K_MM].update(value=o['mm'], range=(3, top))
            save_options(state)
            state['dirty'] = True
            focus_list(window)
        elif event in (K_RESET, 'Reset style'):
            o.update({k: DEFAULT_OPTIONS[k] for k in STYLE_KEYS})
            show_options(window, state)
            save_options(state)
            state['dirty'] = True
            focus_list(window)
        elif event == K_PREVIEW_RESIZE:
            width = window[K_PREVIEW_COL].Widget.winfo_width()
            if state.get('paper') is not None and abs(width - state.get('preview_w', width)) > 30:
                show_preview(window, state)
        elif event == K_PRINT:
            do_print(window, state, values)
        elif event == K_FEED:
            try:
                lib.feed(1)
                window[K_STATUS].update(f'Fed 1 inch    ({lib.printer_summary()})', text_color=C_OK)
            except Exception as e:
                window[K_STATUS].update('Feed failed - see the message', text_color=C_BAD)
                lib.popup_print_error(e)
        elif event == K_SETUP:
            lib.open_setup()
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{TITLE} crashed', e, traceback.format_exc())
