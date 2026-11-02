#!/usr/bin/env python
"""
iD880 Picture - print photos, drawings and screenshots on the iD880 (receipt paper or labels)

    A thermal printer can only make black dots, so a picture's grays have to be turned into patterns of dots.  Pick a Look:
        Photo - smooth      Floyd-Steinberg dots - the most natural for photos
        Photo - crisp       Atkinson dots - lighter and punchier, keeps highlights clean
        Newspaper dots      round halftone dots on a 45 degree screen, like a newspaper photo
        Fine pattern        Bayer ordered pattern - an even, regular texture
        Black & white       no dots, a straight cut-off - for text, logos, line drawings and screenshots
    Thermal dots spread a little when printed, so the dotted Looks lift the midtones a touch to make up for it.

    Bigger than the paper:  set Picture to a size like "8 in wide, in strips" and it prints as strips to cut and glue side by side.
        Every strip but the last has a hatched white glue tab on its right - the next strip goes on top of it.
            1  Cut the left edge off strips 2, 3...   (the dashed line, then straight down the picture's edge)
            2  Glue each strip on the tab of the one before - its edge on the arrows, the dashed lines in line, the picture matching
            3  Cut the top, bottom and outside edges on the dashed lines
        Neighboring strips both print the same 2 mm of picture at their seam, so a cut that wanders a little never shows.
        Glue tab sets the least tab width (strips share the picture equally, so tabs are often wider).
        Print picks one strip to reprint.   Copies prints whole sets.   Rotate "Auto" leaves strips as they are.

    Pictures come from the folder list on the left (click one, or use the arrow keys), Open..., Paste (Ctrl+V),
    Newest download, or by dragging a file onto the preview.  Double-click a folder in the list to go into it.
    Ctrl+P prints.   Esc closes.   Click the preview, then Up/Down, PgUp/PgDn, Home/End scroll it.

Needs id880_lib.py in the same folder.   Drag and drop needs psgdnd:   python -m pip install psgdnd
"""
import collections
import functools
import io
import math
import os
import sys
import time

import PySimpleGUI as sg
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageGrab, ImageOps

import id880_lib as lib

try:
    import psgdnd
except ImportError:
    psgdnd = None

K_FILES = '-FILES-'
K_FILES_OPEN = '-FILES-+OPEN'
K_FOLDER = '-FOLDER-'
K_FOLDER_NAME = '-FOLDER NAME-'
K_OPEN = '-OPEN-'
K_PASTE = '-PASTE-'
K_NEWEST = '-NEWEST-'
K_SOURCE = '-SOURCE-'
K_ORIGINAL = '-ORIGINAL-'
K_LOOK = '-LOOK-'
K_BRIGHT = '-BRIGHT-'
K_CONTRAST = '-CONTRAST-'
K_SHARP = '-SHARP-'
K_AUTO_LEVELS = '-AUTO LEVELS-'
K_INVERT = '-INVERT-'
K_RESET = '-RESET-'
K_MEDIA = '-MEDIA-'
K_ROTATE = '-ROTATE-'
K_SIZE = '-SIZE-'
K_TAB = '-TAB-'
K_WHICH = '-WHICH-'
K_INFO = '-INFO-'
K_HELP = '-HELP-'
K_DOTS = '-DOTS-'
K_PREVIEW = '-PREVIEW-'
K_PREVIEW_COL = '-PREVIEW COL-'
K_PREVIEW_CLICK = '-PREVIEW-+CLICK'
K_PRINT = '-PRINT-'
K_COPIES = '-COPIES-'
K_FEED = '-FEED-'
K_SETUP = '-SETUP-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_CTRL_P = '-CTRL P-'
K_CTRL_V = '-CTRL V-'
K_RENDERED = '-RENDERED-'

FLOYD, ATKINSON, HALFTONE, BAYER, THRESHOLD = 'floyd', 'atkinson', 'halftone', 'bayer', 'threshold'
LOOKS = {'Photo - smooth': dict(method=FLOYD, bright=10, contrast=15, sharp=4),
         'Photo - crisp': dict(method=ATKINSON, bright=5, contrast=15, sharp=4),
         'Newspaper dots': dict(method=HALFTONE, bright=10, contrast=20, sharp=2),
         'Fine pattern': dict(method=BAYER, bright=10, contrast=15, sharp=3),
         'Black & white  (text, logos)': dict(method=THRESHOLD, bright=0, contrast=0, sharp=0)}
LOOK_HELP = ('Smooth - most natural for photos\nCrisp - lighter, punchier photos\nNewspaper - round halftone dots\n'
             'Fine pattern - even, regular texture\nBlack & white - text, logos, line art')
STRIP_HELP = ('Putting the strips together:\n1  Cut the left edge off strips 2, 3...\n2  Glue each strip on the hatched tab of the one\n'
              '    before - edge on the arrows, dashed lines in line\n3  Cut on the dashed lines all around')
STRIP_HELP_COLOR = '#A5D6A7'
ROTATIONS = {'As is': 0, 'Auto (bigger)': None, 'Left 90': 90, 'Right 90': 270, 'Upside down': 180}      # Pillow rotates counter-clockwise
FULL_WIDTH = 'Full paper width'
SIZES = {FULL_WIDTH: 1.0, '75% of paper width': 0.75, '50% of paper width': 0.5, '33% of paper width': 0.33, '25% of paper width': 0.25}
BIG_SIZES = {f'{n} in wide, in strips': n for n in (4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 20, 24)}      # wider than the paper: strips to cut and glue
GLUE_TABS = {'1/4 in (6 mm)': 0.25, '3/8 in (10 mm)': 0.375, '1/2 in (13 mm)': 0.5, '3/4 in (19 mm)': 0.75}     # the least tab - often wider
ALL_STRIPS = 'All strips'
PICTURE_TYPES = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tif', '.tiff')
DOT_GAIN = 0.85                                                     # gamma under 1 lifts midtones - thermal dots print a little fatter than they are
LONG_PRINT_IN = 24                                                  # ask before printing anything longer than this
LONG_STRIPS_IN = 72                                                 # strips are long on purpose - ask past 6 feet
SIDE = lib.mm_dots(1.5)                                             # white edge left and right of the picture - nothing prints closer to the paper's edge
BLEED = lib.mm_dots(2)                                              # neighboring strips both print this much of the picture at their seam
BORDER = lib.mm_dots(3)                                             # white border around the glued-together picture
LINE = 2                                                            # cut lines are 2 dots thick
STRIP_GAP = lib.mm_dots(5)                                          # space between the strips in the preview
MAX_PREVIEW_PIXELS = 16_000_000                                     # bigger previews are shrunk, even with "actual dots"
UP = '..' + os.sep
SETTINGS = {K_LOOK: 'pic_look', K_BRIGHT: 'pic_bright', K_CONTRAST: 'pic_contrast', K_SHARP: 'pic_sharp', K_AUTO_LEVELS: 'pic_auto_levels',
            K_INVERT: 'pic_invert', K_MEDIA: 'pic_media', K_ROTATE: 'pic_rotate', K_SIZE: 'pic_size', K_TAB: 'pic_glue_tab', K_DOTS: 'pic_dots'}
PREVIEW_W, PREVIEW_H = 560, 620
THUMB = 220
Strip = collections.namedtuple('Strip', 'img top left land')       # picture, y of its top cut line, x of its picture's left edge, x where the next strip goes


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Turning grays into dots
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def bayer_tile(n=8):
    """Bayer ordered-dither thresholds: a fine, evenly spread pattern"""
    m = [[0]]
    while len(m) < n:
        k = len(m)
        m = [[4 * m[y % k][x % k] + ((0, 2), (3, 1))[y // k][x // k] for x in range(2 * k)] for y in range(2 * k)]
    return Image.frombytes('L', (n, n), bytes(round(255 * (m[y][x] + 0.5) / (n * n)) for y in range(n) for x in range(n)))


def halftone_tile(d=4):
    """Round dots on a 45 degree screen, like a newspaper.  Dots are d * 1.41 printer dots apart - about 36 lines per inch at 203 dpi."""
    n = 2 * d
    spot = [math.cos(math.pi * (x + y + 1) / d) + math.cos(math.pi * (x - y) / d) for y in range(n) for x in range(n)]
    order = sorted(range(n * n), key=lambda i: (-spot[i], i))        # dot centers turn black first
    rank = [0] * (n * n)
    for r, i in enumerate(order):
        rank[i] = r
    return Image.frombytes('L', (n, n), bytes(round(255 * (1 - (rank[i] + 0.5) / (n * n))) for i in range(n * n)))


TILES = {BAYER: bayer_tile(), HALFTONE: halftone_tile()}


@functools.lru_cache(maxsize=8)
def tiled(method, size):
    """The method's threshold tile repeated to fill size"""
    tile, (w, h) = TILES[method], size
    row = Image.new('L', (w, tile.height))
    for x in range(0, w, tile.width):
        row.paste(tile, (x, 0))
    out = Image.new('L', (w, h))
    for y in range(0, h, tile.height):
        out.paste(row, (0, y))
    return out


def atkinson(gray):
    """Atkinson error diffusion: passes on 6/8 of each dot's error, so light and dark areas stay clean"""
    w, h = gray.size
    px = list(gray.tobytes())
    out = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            i = row + x
            old = px[i]
            new = 255 if old >= 128 else 0
            out[i] = new
            err = (old - new) // 8
            if err:
                if x + 1 < w:
                    px[i + 1] += err
                if x + 2 < w:
                    px[i + 2] += err
                if y + 1 < h:
                    j = i + w
                    if x > 0:
                        px[j - 1] += err
                    px[j] += err
                    if x + 1 < w:
                        px[j + 1] += err
                    if y + 2 < h:
                        px[j + w] += err
    return Image.frombytes('L', (w, h), bytes(out))


def to_dots(gray, method, bright):
    """Gray picture -> black and white (as an L picture holding only 0 and 255)"""
    if method == FLOYD:
        return gray.convert('1').convert('L')
    if method == ATKINSON:
        return atkinson(gray)
    if method in TILES:                                             # white wherever the gray is at least the pattern's threshold
        return ImageChops.subtract(gray, tiled(method, gray.size), 1.0, 128).point(lambda p: 255 if p >= 128 else 0)
    cut = max(1, min(254, round(128 - bright * 1.5)))
    return gray.point(lambda p: 255 if p >= cut else 0)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  The picture pipeline:  flatten -> turn & size -> adjust -> dots -> onto the paper (or into strips)
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def flatten(img):
    """Any picture -> RGB, upright, with transparent parts made white (otherwise they print black)"""
    img = ImageOps.exif_transpose(img)
    if img.mode in ('RGBA', 'LA', 'PA') or (img.mode == 'P' and 'transparency' in img.info):
        img = img.convert('RGBA')
        return Image.alpha_composite(Image.new('RGBA', img.size, (255, 255, 255, 255)), img).convert('RGB')
    return img.convert('RGB')


def sized(src, rotate, pic_w):
    """Turned, scaled to pic_w dots wide, in gray"""
    angle = (270 if src.width > src.height * 1.05 else 0) if rotate is None else rotate
    pic = src.rotate(angle, expand=True) if angle else src
    return pic.convert('L').resize((pic_w, max(1, round(pic.height * pic_w / pic.width))), lib.LANCZOS)


def adjust(gray, method, bright, contrast, sharp, auto_levels, invert):
    if auto_levels:
        gray = ImageOps.autocontrast(gray, cutoff=1)
    if sharp:
        gray = gray.filter(ImageFilter.UnsharpMask(radius=1.6, percent=round(sharp * 30), threshold=2))
    if contrast:
        gray = ImageEnhance.Contrast(gray).enhance(1 + contrast / 100)
    if method != THRESHOLD:                                         # Black & white uses Brightness as its cut-off instead
        gamma = DOT_GAIN * 2 ** (-bright / 50)
        gray = gray.point([round(255 * (i / 255) ** gamma) for i in range(256)])
    return ImageOps.invert(gray) if invert else gray


def on_paper(dots, width):
    """Centered on a strip of paper as wide as the roll, with a little white above and below"""
    top = lib.mm_dots(3)
    paper = Image.new('L', (width, dots.height + 2 * top), 255)
    paper.paste(dots, ((width - dots.width) // 2, top))
    return lib.to_1bit(paper)


def placeholder():
    img = Image.new('RGB', (PREVIEW_W, 360), lib.PREVIEW_BG)
    d = ImageDraw.Draw(img)
    text = 'Drop a picture here,\nor pick one from the list'
    f = lib.font('Sans', 9)
    d.multiline_text((PREVIEW_W // 2, 180), text, font=f, fill='white', anchor='mm', align='center', spacing=10)
    return lib.png_bytes(img)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Big pictures:  strips that print one after another, then get cut and glued side by side
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def strip_seams(pic_w, paper_w, tab):
    """Picture columns where a picture pic_w dots wide gets split, from 0 to pic_w.  Every strip carries the same share of the picture
    and keeps a glue tab at least tab dots wide."""
    if pic_w <= paper_w - 2 * SIDE - 2 * BORDER:
        return [0, pic_w]
    per_strip = paper_w - SIDE - BORDER - BLEED - tab                # strip 1 is the tightest: border on its left, bleed and glue tab on its right
    count = math.ceil(pic_w / max(lib.mm_dots(10), per_strip))
    return [round(k * pic_w / count) for k in range(count + 1)]


def dashed(d, start, end):
    """Dashed cut line, LINE dots thick, from start to end - straight across or straight down"""
    (x0, y0), (x1, y1) = start, end
    dash, step = lib.mm_dots(3), lib.mm_dots(5)
    if y0 == y1:
        for x in range(x0, x1, step):
            d.rectangle((x, y0, min(x + dash, x1) - 1, y0 + LINE - 1), fill=0)
    else:
        for y in range(y0, y1, step):
            d.rectangle((x0, y, x0 + LINE - 1, min(y + dash, y1) - 1), fill=0)


def hatched(w, h):
    """Diagonal lines 3 mm apart - marks a glue tab"""
    img = Image.new('L', (max(1, w), max(1, h)), 255)
    d = ImageDraw.Draw(img)
    for x in range(-h, w, lib.mm_dots(3)):
        d.line((x, h, x + h, 0), fill=0, width=2)
    return img


def arrow(d, x, y):
    """Solid triangle pointing right, its tip at x"""
    s = lib.mm_dots(3)
    d.polygon([(x - s, y - s // 2), (x, y), (x - s, y + s // 2)], fill=0)


def steps_image(width, count):
    """How the strips go together - printed at the top of strip 1"""
    f, bold = lib.font('Sans', 9), lib.font('Sans', 9, True)
    others = 'strip 2' if count == 2 else f'strips 2-{count}'
    steps = (f"Cut the left edge off {others}: the dashed line, then straight down the picture's edge",
             'Glue each strip on the hatched tab of the one before - its edge on the arrows, the dashed lines in line',
             'Cut the top, bottom and outside edges on the dashed lines')
    indent, lh, gap = lib.mm_dots(4), lib.line_height(f), lib.mm_dots(1)
    rows = [lib.wrap(step, f, width - indent) for step in steps]
    img = Image.new('L', (width, sum(len(lines) for lines in rows) * lh + gap * (len(rows) - 1)), 255)
    d = ImageDraw.Draw(img)
    y = 0
    for n, lines in enumerate(rows, 1):
        d.text((0, y), str(n), font=bold, fill=0)
        for line in lines:
            d.text((indent, y), line, font=f, fill=0)
            y += lh
        y += gap
    return img


def make_strips(dots, paper_w, tab):
    """The dotted picture split into strips, each paper_w wide (black 0, white 255).  Top to bottom a strip is:
    number and arrows | dashed cut line | border | picture | border | dashed cut line | arrows and number"""
    seams = strip_seams(dots.width, paper_w, tab)
    count = len(seams) - 1
    title, small = lib.font('Sans', 12, True), lib.font('Sans', 9)
    strips = []
    for i in range(count):
        first, last = i == 0, i == count - 1
        a, b = seams[i] - (0 if first else BLEED), seams[i + 1] + (0 if last else BLEED)     # picture columns this strip prints
        left = SIDE + (BORDER if first else 0)                                                 # picture's left edge on the paper
        right = left + b - a
        steps = steps_image(paper_w - left - SIDE - lib.mm_dots(1.5), count) if first and count > 1 else None
        top = lib.mm_dots(7) + (steps.height + lib.mm_dots(2) if steps else 0) + lib.mm_dots(5)     # top cut line
        y0 = top + BORDER                                                                      # picture's top edge
        y1 = y0 + dots.height
        bottom = y1 + BORDER - LINE                                                            # bottom cut line
        img = Image.new('L', (paper_w, bottom + LINE + lib.mm_dots(6)), 255)
        img.paste(dots.crop((a, 0, b, dots.height)), (left, y0))
        d = ImageDraw.Draw(img)
        for y in (top, bottom):
            dashed(d, (SIDE, y), (paper_w - SIDE, y))
        if first:
            dashed(d, (left - BORDER, 0), (left - BORDER, img.height))                         # outside edge of the glued picture
        else:                                                                                  # cut here, then straight down the picture's edge
            dashed(d, (left - LINE, 0), (left - LINE, y0))
            dashed(d, (left - LINE, y1), (left - LINE, img.height))
        land = None
        if last:
            dashed(d, (right + BORDER - LINE, 0), (right + BORDER - LINE, img.height))         # outside edge of the glued picture
        else:
            tab_x = right + lib.mm_dots(1)
            img.paste(hatched(paper_w - SIDE - tab_x, bottom - top - LINE), (tab_x, top + LINE))     # glue tab
            land = left + seams[i + 1] - BLEED - a                                              # the next strip's edge goes here
            arrow(d, land - 1, top - lib.mm_dots(2.5))
            arrow(d, land - 1, bottom + LINE + lib.mm_dots(2.5))
        if count > 1:
            name, x = f'{i + 1} of {count}', left + lib.mm_dots(1.5)
            d.text((x, lib.mm_dots(1.5)), name, font=title, fill=0)
            d.text((x, bottom + LINE + lib.mm_dots(1.5)), name, font=small, fill=0)
            box_w, box_h, x = lib.mm_dots(1.5), lib.mm_dots(3), x + round(title.getlength(name)) + lib.mm_dots(3)
            if x + count * (box_w + 4) < paper_w - SIDE:                                        # little map - which strip this is
                for n in range(count):
                    d.rectangle((x, lib.mm_dots(2), x + box_w - 1, lib.mm_dots(2) + box_h - 1), fill=0 if n == i else 255, outline=0, width=2)
                    x += box_w + 4
        if steps:
            img.paste(steps, (left + lib.mm_dots(1.5), lib.mm_dots(7)))
        strips.append(Strip(img, top, left, land))
    return strips


def strips_preview(strips, chosen, actual_dots):
    """The strips side by side, lined up on their top cut lines.  Strips that won't print are pale.  Returns PNG data and True if shrunk."""
    paper_w, high = strips[0].img.width, max(s.top for s in strips)
    w = len(strips) * paper_w + (len(strips) - 1) * STRIP_GAP
    h = max(high - s.top + s.img.height for s in strips)
    scale = min(1.0, 1.0 if actual_dots else PREVIEW_W / w, math.sqrt(MAX_PREVIEW_PIXELS / (w * h)))
    out = Image.new('RGB', (round(w * scale) + 4, round(h * scale) + 4), lib.PREVIEW_BG)
    d = ImageDraw.Draw(out)
    for i, s in enumerate(strips):
        img = s.img if i in chosen else s.img.point(lambda p: 175 + p * 80 // 255)
        if scale < 1:
            img = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), lib.LANCZOS, reducing_gap=2.0)
        x, y = 2 + round(i * (paper_w + STRIP_GAP) * scale), 2 + round((high - s.top) * scale)
        out.paste(img, (x, y))
        d.rectangle((x - 1, y - 1, x + img.width, y + img.height), outline=(170, 170, 170))
    bio = io.BytesIO()
    out.save(bio, format='PNG', compress_level=1)                   # fast - big previews take a while to squeeze
    return bio.getvalue(), actual_dots and scale < 1


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Making what prints.  render() runs in a thread so big pictures don't freeze the window - it never touches the window or the settings file.
# ----------------------------------------------------------------------------------------------------------------------------------------------------
class Rendered:
    """What render() made from a job:  1-bit pages to print, preview PNG, size info"""
    def __init__(self, job, pages, png, info, long):
        self.job, self.pages, self.png, self.info, self.long = job, pages, png, info, long


def cached(cache, name, src, key, make):
    """make()'s last result, reused while the picture and key stay the same"""
    hit = cache.get(name)
    if hit and hit[0] is src and hit[1] == key:
        return hit[2]
    result = make()
    cache[name] = (src, key, result)
    return result


def paper_used(inches, paper):
    return f'Uses {inches:.1f} in of {paper}' if inches < 36 else f'Uses {inches:.0f} in ({inches / 12:.1f} ft) of {paper}'


def render(job, cache):
    src, rotate, pic_w = job['src'], job['rotate'], job['pic_w']
    base = cached(cache, 'base', src, (rotate, pic_w), lambda: sized(src, rotate, pic_w))
    look = (job['method'], job['bright'], job['contrast'], job['sharp'], job['auto_levels'], job['invert'])
    dots = cached(cache, 'dots', src, (rotate, pic_w) + look, lambda: to_dots(adjust(base, *look), job['method'], job['bright']))
    paper = job['media'].lower()
    if not job['big']:
        page = on_paper(dots, job['width'])
        png = lib.png_bytes(page.convert('L')) if job['dots'] else lib.preview_png(page, max_width=PREVIEW_W)
        inches = page.height / lib.DPI
        info = f'Picture {dots.width / lib.DPI:.2f} x {dots.height / lib.DPI:.2f} in\n{paper_used(inches, paper)}' + ('   (long!)' if inches > LONG_PRINT_IN else '')
        return Rendered(job, [page], png, info, inches > LONG_PRINT_IN)
    strips = make_strips(dots, job['width'], job['tab'])
    chosen = [i for i in range(len(strips)) if job['which'] in (ALL_STRIPS, f'Strip {i + 1}')]
    pages = [lib.to_1bit(strips[i].img) for i in chosen]
    png, shrunk = strips_preview(strips, chosen, job['dots'])
    inches = sum(page.height for page in pages) / lib.DPI
    notes = ([f'Printing {job["which"].lower()} only'] if job['which'] != ALL_STRIPS else []) + (['preview shrunk to fit'] if shrunk else [])
    lines = [f'{len(strips)} strips, glued {dots.width / lib.DPI:.1f} x {dots.height / lib.DPI:.1f} in', paper_used(inches, paper)] + [' - '.join(notes)] * bool(notes)
    return Rendered(job, pages, png, '\n'.join(lines), inches > LONG_STRIPS_IN)


def safe_render(job, cache):
    try:
        return render(job, cache)
    except Exception as e:                                          # handed back to the window to show
        return e


def same_print(a, b):
    """True when two jobs print exactly the same thing"""
    return all((a[k] is b[k]) if k == 'src' else a[k] == b[k] for k in a if k not in ('seq', 'dots'))


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  The folder list
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def pictures_folder():
    folder = lib.setting('pic_folder')
    if folder and os.path.isdir(folder):
        return folder
    pictures = os.path.join(os.path.expanduser('~'), 'Pictures')
    return pictures if os.path.isdir(pictures) else os.path.expanduser('~')


def folder_entries(folder):
    """'..\\' to go up, then the folders (ending in \\), then the pictures, newest first"""
    try:
        names = os.listdir(folder)
    except OSError:
        return [UP]
    folders = sorted((n + os.sep for n in names if os.path.isdir(os.path.join(folder, n)) and not n.startswith('.')), key=str.lower)
    pictures = [n for n in names if n.lower().endswith(PICTURE_TYPES)]
    pictures.sort(key=lambda n: os.path.getmtime(os.path.join(folder, n)), reverse=True)
    return ([UP] if os.path.dirname(folder.rstrip(os.sep)) != folder.rstrip(os.sep) else []) + folders + pictures


def show_folder(window, folder):
    lib.save_setting('pic_folder', folder)
    window[K_FOLDER_NAME].update(os.path.basename(folder.rstrip(os.sep)) or folder)
    window[K_FILES].update(folder_entries(folder))
    window[K_FILES].set_tooltip(f' {folder} ')


def newest_download():
    folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    try:
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(PICTURE_TYPES)]
    except OSError:
        return None
    return max(files, key=os.path.getmtime) if files else None


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
class State:
    def __init__(self):
        self.src, self.name, self.rendered, self.cache = None, '', None, {}
        self.seq, self.shown, self.busy, self.started, self.noted = 0, 0, False, 0.0, False     # render bookkeeping


def make_window():
    sg.theme(lib.THEME)
    s = lib.setting
    hint = dict(font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)
    look = s('pic_look') if s('pic_look') in LOOKS else 'Photo - smooth'
    start = LOOKS[look]
    value = lambda key, default: s(SETTINGS[key]) if s(SETTINGS[key]) is not None else default
    media, rotate, size, tab = value(K_MEDIA, lib.RECEIPT), value(K_ROTATE, 'As is'), value(K_SIZE, FULL_WIDTH), value(K_TAB, '1/2 in (13 mm)')
    size = size if size in SIZES or size in BIG_SIZES else FULL_WIDTH
    tab = tab if tab in GLUE_TABS else '1/2 in (13 mm)'
    top = [sg.Button('Open...', key=K_OPEN), sg.Button('Paste', key=K_PASTE, tooltip=' Picture from the clipboard (Ctrl+V) '),
           sg.Button('Newest download', key=K_NEWEST, tooltip=' Newest picture in your Downloads folder '), sg.Text('', key=K_SOURCE, size=(50, 1), **hint)]
    files = sg.Column([[sg.Text('', key=K_FOLDER_NAME, size=(18, 1), font=('Helvetica', 11, 'bold')), sg.Push(), sg.Button('Folder...', key=K_FOLDER, font=lib.SMALL_FONT)],
                       [sg.Listbox([], key=K_FILES, size=(30, 15), enable_events=True, expand_y=True)],
                       [sg.Text('Original', **hint)],
                       [sg.Image(key=K_ORIGINAL, size=(THUMB, THUMB), background_color=lib.PREVIEW_BG)]], vertical_alignment='top', expand_y=True)
    look_combo = sg.Combo(list(LOOKS), look, key=K_LOOK, readonly=True, enable_events=True, size=(26, 1))
    bright = sg.Slider((-50, 50), value(K_BRIGHT, start['bright']), 1, orientation='h', key=K_BRIGHT, enable_events=True, size=(20, 15))
    contrast = sg.Slider((-50, 50), value(K_CONTRAST, start['contrast']), 1, orientation='h', key=K_CONTRAST, enable_events=True, size=(20, 15))
    sharp = sg.Slider((0, 10), value(K_SHARP, start['sharp']), 1, orientation='h', key=K_SHARP, enable_events=True, size=(20, 15))
    switches = [sg.Checkbox('Auto levels', value(K_AUTO_LEVELS, True), key=K_AUTO_LEVELS, enable_events=True),
                sg.Checkbox('Invert', value(K_INVERT, False), key=K_INVERT, enable_events=True), sg.Push(), sg.Button('Reset look', key=K_RESET)]
    look_frame = sg.Frame('How it looks', [[sg.Text('Look'), look_combo], [sg.Text('Brightness', size=(10, 1)), bright], [sg.Text('Contrast', size=(10, 1)), contrast],
                                          [sg.Text('Sharpness', size=(10, 1)), sharp], switches])
    combo = dict(readonly=True, enable_events=True, size=(21, 1))
    media_combo = sg.Combo(lib.MEDIA, media, key=K_MEDIA, tooltip=' The roll you print on.   Label width is in Printer setup. ', **combo)
    size_tip = ' How wide the picture prints.   "in strips" sizes are wider than the paper - they print as strips you cut and glue side by side. '
    size_combo = sg.Combo(list(SIZES) + list(BIG_SIZES), size, key=K_SIZE, tooltip=size_tip, **combo)
    tab_combo = sg.Combo(list(GLUE_TABS), tab, key=K_TAB, tooltip=' Least width of the white tab the next strip is glued on ', **combo)
    which_combo = sg.Combo([ALL_STRIPS], ALL_STRIPS, key=K_WHICH, auto_size_text=False, tooltip=' Every strip, or just one to redo ', **combo)
    paper_frame = sg.Frame('Paper and picture size', [[sg.Text('Print on', size=(8, 1)), media_combo],
                                                      [sg.Text('Rotate', size=(8, 1)), sg.Combo(list(ROTATIONS), rotate, key=K_ROTATE, **combo)],
                                                      [sg.Text('Picture', size=(8, 1)), size_combo],
                                                      [sg.Text('Glue tab', size=(8, 1)), tab_combo],
                                                      [sg.Text('Print', size=(8, 1)), which_combo],
                                                      [sg.Text('', key=K_INFO, size=(44, 3), **hint)]], expand_x=True)
    print_row = [sg.Button('Print', key=K_PRINT, size=(10, 1), button_color=('white', lib.GREEN)), sg.Text('Copies'),
                 sg.Spin(list(range(1, 21)), initial_value=1, key=K_COPIES, size=(3, 1))]
    tool_row = [sg.Button('Feed 1 inch', key=K_FEED), sg.Button('Printer setup', key=K_SETUP, button_color=('white', lib.BLUE))]
    help_text = sg.Text(LOOK_HELP, key=K_HELP, size=(44, 6), **hint)
    controls = sg.Column([[look_frame], [paper_frame], print_row, tool_row, [help_text]], vertical_alignment='top')
    preview = sg.Column([[sg.Image(data=placeholder(), key=K_PREVIEW, pad=(12, 12), background_color=lib.PREVIEW_BG)]], key=K_PREVIEW_COL, scrollable=True,
                        size=(PREVIEW_W + 40, PREVIEW_H), background_color=lib.PREVIEW_BG, expand_y=True)
    right = sg.Column([[sg.Text('What will print', font=('Helvetica', 11, 'bold')), sg.Push(),
                        sg.Checkbox('Show the actual dots (1:1)', value(K_DOTS, False), key=K_DOTS, enable_events=True)], [preview]], vertical_alignment='top', expand_y=True)
    layout = [top, [files, controls, right], [sg.Text(lib.printer_summary(), key=K_STATUS, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)]]
    window = sg.Window('iD880 Picture', layout, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, finalize=True, resizable=True)
    lib.bind_scroll_keys(window)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Control-p>', K_CTRL_P)
    window.TKroot.bind('<Control-Alt-p>', lambda e: 'break')       # Ctrl+Alt+P belongs to other hotkeys (like typing PySimpleGUI) - it doesn't print
    window.bind('<Control-v>', K_CTRL_V)
    window[K_PREVIEW].bind('<Button-1>', '+CLICK')
    window[K_FILES].bind('<Double-Button-1>', '+OPEN')
    window[K_FILES].bind('<Return>', '+OPEN')
    if psgdnd is not None:
        for key in (K_PREVIEW, K_ORIGINAL, K_FILES):
            psgdnd.register_element_dnd(window[key], window, psgdnd.DROP_TYPE_FILES)
    show_folder(window, pictures_folder())
    sync_strip_controls(window, size)
    return window


def sync_strip_controls(window, size):
    """Glue tab and Print (which strips) only matter for the strip sizes"""
    big = size in BIG_SIZES
    window[K_TAB].update(disabled=not big)
    window[K_WHICH].update(disabled=not big)
    window[K_HELP].update(STRIP_HELP if big else LOOK_HELP, text_color=STRIP_HELP_COLOR if big else lib.HINT_COLOR)


def strip_choices(window, count, current):
    """Keep the Print list (All strips, Strip 1, Strip 2...) in step with the number of strips.  Returns the choice in effect."""
    choices = [ALL_STRIPS] + ([f'Strip {n}' for n in range(1, count + 1)] if count > 1 else [])
    choice = current if current in choices else ALL_STRIPS
    if window[K_WHICH].Values != choices:
        window[K_WHICH].update(value=choice, values=choices)
    return choice


def make_job(window, state, values):
    """Snapshot of everything render() needs, read from the window and the settings here in the GUI thread"""
    width = lib.media_width(values[K_MEDIA])
    big = BIG_SIZES.get(values[K_SIZE])
    tab = lib.inch_dots(GLUE_TABS.get(values[K_TAB], 0.5))
    rotate = ROTATIONS[values[K_ROTATE]]
    pic_w = lib.inch_dots(big) if big else max(8, round((width - 2 * SIDE) * SIZES[values[K_SIZE]]))
    which = strip_choices(window, len(strip_seams(pic_w, width, tab)) - 1 if big else 0, values[K_WHICH])
    state.seq += 1
    return dict(seq=state.seq, src=state.src, media=values[K_MEDIA], width=width, big=bool(big), pic_w=pic_w, tab=tab, which=which,
                rotate=(rotate or 0) if big else rotate, method=LOOKS[values[K_LOOK]]['method'], bright=int(values[K_BRIGHT]),
                contrast=int(values[K_CONTRAST]), sharp=int(values[K_SHARP]), auto_levels=values[K_AUTO_LEVELS], invert=values[K_INVERT], dots=values[K_DOTS])


def start_render(window, state, values):
    job = make_job(window, state, values)
    state.busy, state.started, state.noted = True, time.time(), False
    window.start_thread(lambda: safe_render(job, state.cache), K_RENDERED)


def show(window, state, rendered):
    state.rendered, state.shown = rendered, rendered.job['seq']
    window[K_PREVIEW].update(data=rendered.png)
    window.refresh()                                                # let tkinter size the new picture before the scroll area is measured
    window[K_PREVIEW_COL].contents_changed()
    window[K_INFO].update(rendered.info, text_color=lib.ORANGE if rendered.long else lib.HINT_COLOR)


def use_picture(window, state, picture, name):
    """Make picture (a Pillow image) the one being printed"""
    try:
        state.src = flatten(picture)
    except Exception as e:
        sg.popup_error('Could not read that picture', name, str(e), title='iD880 Picture', keep_on_top=True)
        return False
    state.name = name
    window[K_SOURCE].update(f'{name}    ({state.src.width} x {state.src.height} pixels)')
    thumb = state.src.copy()
    thumb.thumbnail((THUMB, THUMB))
    window[K_ORIGINAL].update(data=lib.png_bytes(thumb))
    return True


def open_file(window, state, path):
    try:
        with Image.open(path) as img:
            img.load()
            return use_picture(window, state, img, os.path.basename(path))
    except Exception as e:
        sg.popup_error('Could not open the picture', path, str(e), title='iD880 Picture', keep_on_top=True)
        return False


def print_picture(window, state, values):
    """Print what the window shows - made fresh here if the preview isn't up to date"""
    job = make_job(window, state, values)
    rendered = state.rendered
    if rendered is None or not same_print(rendered.job, job):
        window[K_STATUS].update('Getting the picture ready...', text_color=lib.HINT_COLOR)
        window.refresh()
        rendered = safe_render(job, state.cache)
        if isinstance(rendered, Exception):
            sg.popup_error('Could not make the picture', str(rendered), title='iD880 Picture', keep_on_top=True)
            return
        show(window, state, rendered)
    copies = int(values[K_COPIES])
    inches = sum(page.height for page in rendered.pages) * copies / lib.DPI
    too_long = inches > (LONG_STRIPS_IN if job['big'] else LONG_PRINT_IN)
    if too_long and sg.popup_yes_no(f'This uses {inches:.0f} inches of paper.  Print it?', title='iD880 Picture', keep_on_top=True) != 'Yes':
        return
    try:
        if job['big']:
            what = f'{len(rendered.pages)} strips' if job['which'] == ALL_STRIPS else job['which'].lower()
            sent = lib.print_bitmaps(rendered.pages, values[K_MEDIA], copies)
        else:
            what, sent = 'picture', lib.print_bitmap(rendered.pages[0], values[K_MEDIA], copies)
        window[K_STATUS].update(f'Printed {what}: {sent}    ({lib.printer_summary()})', text_color='#9CCC65')
    except Exception as e:
        window[K_STATUS].update('Print failed - see the message', text_color='#FF8A65')
        lib.popup_print_error(e)


def main():
    window = make_window()
    state = State()
    dirty = len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) and open_file(window, state, sys.argv[1])
    while True:
        event, values = window.read(timeout=200 if dirty or state.busy else None)
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        if event == K_ESCAPE:
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70,10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == sg.TIMEOUT_KEY:
            if dirty and state.src is None:
                dirty = False
            elif dirty and not state.busy:                          # changes have settled - make the new preview in the background
                start_render(window, state, values)
                dirty = False
            elif state.busy and not state.noted and time.time() - state.started > 0.6:
                window[K_INFO].update('Working on it...', text_color=lib.HINT_COLOR)
                state.noted = True
        elif event == K_RENDERED:
            state.busy = False
            result = values[K_RENDERED]
            if isinstance(result, Exception):
                window[K_INFO].update(f'Could not make the picture:\n{result}', text_color=lib.ORANGE)
            elif result.job['seq'] > state.shown:                   # an older one is ignored - Print already made a newer one
                show(window, state, result)
        elif lib.is_scroll_key(event):
            lib.scroll_with_key(window, K_PREVIEW_COL, event)
        elif event == K_PREVIEW_CLICK:
            window[K_PREVIEW].Widget.focus_set()                    # so the scroll keys go to the preview
        elif event == K_FILES and values[K_FILES]:
            name = values[K_FILES][0]
            if not name.endswith(os.sep):                           # folders open with a double-click or Enter
                dirty = open_file(window, state, os.path.join(pictures_folder(), name)) or dirty
        elif event == K_FILES_OPEN and values[K_FILES] and values[K_FILES][0].endswith(os.sep):
            name, folder = values[K_FILES][0], pictures_folder()
            show_folder(window, os.path.dirname(folder.rstrip(os.sep)) if name == UP else os.path.join(folder, name.rstrip(os.sep)))
        elif event == K_FOLDER:
            folder = sg.popup_get_folder('Folder of pictures', default_path=pictures_folder(), keep_on_top=True)
            if folder:
                show_folder(window, folder)
        elif event == K_OPEN:
            path = sg.popup_get_file('Picture to print', initial_folder=pictures_folder(), keep_on_top=True,
                                     file_types=(('Pictures', ' '.join('*' + t for t in PICTURE_TYPES)), ('All files', '*.*')))
            if path:
                dirty = open_file(window, state, path) or dirty
        elif event == K_NEWEST:
            path = newest_download()
            if path:
                dirty = open_file(window, state, path) or dirty
            else:
                sg.popup_quick_message('No pictures in your Downloads folder', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
        elif event in (K_PASTE, K_CTRL_V):
            try:
                grabbed = ImageGrab.grabclipboard()
            except Exception:
                grabbed = None
            if isinstance(grabbed, list):                           # files copied in Explorer arrive as a list of paths
                path = next((str(f) for f in grabbed if str(f).lower().endswith(PICTURE_TYPES)), None)
                dirty = (open_file(window, state, path) if path else False) or dirty
            elif isinstance(grabbed, Image.Image):
                dirty = use_picture(window, state, grabbed, 'Clipboard picture') or dirty
            else:
                sg.popup_quick_message('No picture on the clipboard', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
        elif psgdnd is not None and psgdnd.is_drop_event(event):
            path = next((f for f in str(values[event]).split(',') if f.lower().endswith(PICTURE_TYPES)), None)
            if path:
                dirty = open_file(window, state, path) or dirty
            else:
                sg.popup_quick_message('Drop a picture file', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
        elif event in (K_LOOK, K_RESET):
            look = LOOKS[values[K_LOOK]]
            for key, name in ((K_BRIGHT, 'bright'), (K_CONTRAST, 'contrast'), (K_SHARP, 'sharp')):
                window[key].update(look[name])
                lib.save_setting(SETTINGS[key], look[name])
            lib.save_setting(SETTINGS[K_LOOK], values[K_LOOK])
            dirty = True
        elif event in SETTINGS:
            lib.save_setting(SETTINGS[event], values[event])
            if event == K_SIZE:
                sync_strip_controls(window, values[K_SIZE])
            dirty = True
        elif event == K_WHICH:
            dirty = True
        elif event in (K_PRINT, K_CTRL_P):
            if state.src is None:
                sg.popup_quick_message('Pick a picture first', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
                continue
            print_picture(window, state, values)
        elif event == K_FEED:
            try:
                window[K_STATUS].update(f'Fed 1 inch    ({lib.printer_summary()})', text_color='#9CCC65')
                lib.feed(1)
            except Exception as e:
                window[K_STATUS].update('Feed failed - see the message', text_color='#FF8A65')
                lib.popup_print_error(e)
        elif event == K_SETUP:
            lib.open_setup()
    window.close()


if __name__ == '__main__':
    main()
