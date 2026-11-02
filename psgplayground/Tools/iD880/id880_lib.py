#!/usr/bin/env python
"""
id880_lib.py - shared code for the iD880 thermal printer programs (Setup, Notes, Address_Labels, Ship_Label, Picture, Figlet)

    Draw : everything is drawn with Pillow at the printer's own resolution (203 dpi = 8 dots per mm), then made 1-bit
    Send : the bitmap goes to the printer as ZPL (^GFA) or TSPL (BITMAP) - pick the language in iD880_Setup.pyw
    Path : USB = RAW job through the Windows printer queue (needs pywin32)      Ethernet = TCP port 9100
    Keep : all the iD880 programs share one PySimpleGUI User Settings file

    Paper: two continuous rolls - 3-1/8" receipt paper and continuous labels (4" wide unless changed in Setup)

Install:  python -m pip install --upgrade PySimpleGUI pillow pywin32 pymupdf
"""
import functools
import io
import os
import socket

import PySimpleGUI as sg
from PIL import Image, ImageFont, ImageOps

DPI = 203                                                           # iD880 resolution
DOTS_PER_MM = 8
HEAD_DOTS = 832                                                     # 104 mm print head - paper sits centered under it
SETTINGS_FILENAME = 'iD880_thermal_printer.json'
sg.user_settings_filename(filename=SETTINGS_FILENAME)              # every iD880 program reads and writes this same file

RECEIPT = 'Receipt paper'                                           # the two rolls - both continuous, so any length prints
LABELS = 'Labels'
MEDIA = (RECEIPT, LABELS)
RECEIPT_WIDTH = 640                                                 # 3-1/8" (80 mm) in dots
LABEL_WIDTHS = {'4" (102 mm)': 812, '3" (76 mm)': 609, '2-1/4" (57 mm)': 457, '2" (51 mm)': 406}
NUDGE_SETTING = {RECEIPT: 'receipt_nudge', LABELS: 'label_nudge'}     # dots to move the print right (+) or left (-) of centered

DEFAULTS = {'connection': 'windows', 'win_printer': '', 'ip': '192.168.1.100', 'port': 9100, 'language': 'ZPL', 'darkness': 15, 'speed': 3,
            'label_width': '4" (102 mm)', 'receipt_nudge': 0, 'label_nudge': 0}

GREEN, RED, BLUE, ORANGE = '#2E7D32', '#C62828', '#1565C0', '#EF6C00'   # Print / destructive / setup / warning
HINT_COLOR = '#A9C7E8'
SMALL_FONT = ('Helvetica', 10)                                      # hints and status lines (Windows shows Helvetica as Arial)
PREVIEW_BG = '#3C4650'
THEME = 'DarkGrey9'

LANCZOS = getattr(Image, 'Resampling', Image).LANCZOS
NO_DITHER = getattr(Image, 'Dither', Image).NONE

HELP_TEXT = '''Things to check:
  1. The printer is on, the lid is closed and paper is loaded
  2. iD880_Setup.pyw has the right connection (USB printer name, or IP address for Ethernet)
  3. Nothing prints, or commands print as text?  Change Language in Setup (ZPL <-> TSPL)
  4. USB printing needs pywin32 (python -m pip install pywin32) and the printer installed in Windows'''


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Settings
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def setting(name):
    sg.user_settings_load()                                         # re-read: another iD880 program (like Setup) may have changed it
    return sg.user_settings_get_entry(name, DEFAULTS.get(name))


def save_setting(name, value):
    sg.user_settings_load()                                         # merge with the newest file so other programs' changes survive
    sg.user_settings_set_entry(name, value)


def media_width(media):
    """Width in dots of the roll named media (RECEIPT or LABELS)"""
    return RECEIPT_WIDTH if media == RECEIPT else LABEL_WIDTHS.get(setting('label_width'), 812)


def media_offset(media):
    """Dots from the left end of the print head to the left edge of the paper (centered paper + the nudge from Setup)"""
    return max(0, (HEAD_DOTS - media_width(media)) // 2 + int(setting(NUDGE_SETTING.get(media, 'label_nudge')) or 0))


def printer_summary():
    if setting('connection') == 'network':
        where = f"Ethernet {setting('ip')}:{setting('port')}"
    else:
        where = f'USB "{setting("win_printer")}"' if setting('win_printer') else 'USB - no printer picked yet (open Printer setup)'
    return f"Printer: {where}    Language: {setting('language')}"


def open_setup():
    sg.execute_py_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'iD880_Setup.pyw'))


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Fonts and text
# ----------------------------------------------------------------------------------------------------------------------------------------------------
FONT_FILES = {'Sans': ('arial.ttf', 'DejaVuSans.ttf', 'LiberationSans-Regular.ttf'),
              'Sans Bold': ('arialbd.ttf', 'DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf'),
              'Serif': ('times.ttf', 'DejaVuSerif.ttf', 'LiberationSerif-Regular.ttf'),
              'Serif Bold': ('timesbd.ttf', 'DejaVuSerif-Bold.ttf', 'LiberationSerif-Bold.ttf'),
              'Mono': ('consola.ttf', 'cour.ttf', 'DejaVuSansMono.ttf', 'LiberationMono-Regular.ttf'),
              'Mono Bold': ('consolab.ttf', 'courbd.ttf', 'DejaVuSansMono-Bold.ttf', 'LiberationMono-Bold.ttf')}
FAMILIES = ('Sans', 'Serif', 'Mono')


@functools.lru_cache(maxsize=256)
def font(family='Sans', points=12, bold=False):
    """Pillow font sized in printer points (1 pt = 1/72 inch on the paper)"""
    name = family + (' Bold' if bold else '')
    pixels = max(8, round(points * DPI / 72))
    for filename in FONT_FILES.get(name, FONT_FILES['Sans']):
        try:
            return ImageFont.truetype(filename, pixels)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=pixels)
    except TypeError:
        return ImageFont.load_default()


def line_height(f):
    ascent, descent = f.getmetrics()
    return ascent + descent


def wrap(text, f, max_width):
    """Word-wrap one paragraph to max_width dots.  Words longer than a whole line get split."""
    if f.getlength(text) <= max_width:
        return [text]
    lines, line = [], ''
    for word in text.split():
        trial = word if not line else f'{line} {word}'
        if f.getlength(trial) <= max_width:
            line = trial
            continue
        if line:
            lines.append(line)
        while f.getlength(word) > max_width:
            cut = len(word) - 1
            while cut > 1 and f.getlength(word[:cut]) > max_width:
                cut -= 1
            lines.append(word[:cut])
            word = word[cut:]
        line = word
    lines.append(line)
    return lines


def mm_dots(mm):
    return round(mm * DOTS_PER_MM)


def inch_dots(inches):
    return round(inches * DPI)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Bitmaps and printer languages
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def to_1bit(img, threshold=150):
    """Black & white bitmap, width rounded up to whole bytes (padding is white).  Pillow 1-bit: 0 = black, 1 = white."""
    gray = img.convert('L')
    width8 = (gray.width + 7) // 8 * 8
    if width8 != gray.width:
        padded = Image.new('L', (width8, gray.height), 255)
        padded.paste(gray, (0, 0))
        gray = padded
    return gray.point(lambda p: 255 if p >= threshold else 0).convert('1', dither=NO_DITHER)


def zpl_graphic(img1):
    """ZPL ^GFA graphic field.  In ZPL a 1 bit is a black dot, the opposite of Pillow, so the bits are inverted."""
    data = ImageOps.invert(img1.convert('L')).convert('1', dither=NO_DITHER).tobytes()
    return f'^GFA,{len(data)},{len(data)},{img1.width // 8},{data.hex().upper()}'


def zpl_job(img1, media, copies=1, extra_dark=False):
    """Continuous media (^MNN), tear-off (^MMT), direct thermal (^MTD).  Full head width with the bitmap placed over the centered paper."""
    darkness, speed = job_darkness_speed(extra_dark)
    lines = [f"~SD{darkness:02d}", '^XA', '^MTD', '^MMT', '^MNN', f'^PW{HEAD_DOTS}', f'^LL{img1.height}', f'^LH{media_offset(media)},0',
             f"^PR{speed}", '^FO0,0' + zpl_graphic(img1) + '^FS', f'^PQ{max(1, int(copies))}', '^XZ']
    return '\n'.join(lines).encode('ascii')


def tspl_job(img1, media, copies=1, extra_dark=False):
    """TSPL BITMAP data uses 0 = black dot, 1 = white - the same as Pillow, so the bytes go out as-is"""
    darkness, speed = job_darkness_speed(extra_dark)
    head = [f'SIZE {HEAD_DOTS / DOTS_PER_MM:.1f} mm,{img1.height / DOTS_PER_MM:.1f} mm', 'GAP 0 mm,0 mm', 'DIRECTION 1', f'REFERENCE {media_offset(media)},0',
            f"DENSITY {round(darkness / 2)}", f"SPEED {speed}", 'SET TEAR ON', 'CLS', f'BITMAP 0,0,{img1.width // 8},{img1.height},0,']
    return '\r\n'.join(head).encode('ascii') + img1.tobytes() + f'\r\nPRINT 1,{max(1, int(copies))}\r\n'.encode('ascii')


def job_darkness_speed(extra_dark=False):
    """Darkness (0-30) and speed (inches/second) for a job - Setup's, or the darkest and slowest for big solid black areas.
    Thermal heads can't heat fast enough for wide black areas, so they come out gray - printing slower gives each line more heat."""
    if extra_dark:
        return 30, 2
    return int(float(setting('darkness'))), int(float(setting('speed')))


def build_job(img1, media, copies=1, extra_dark=False):
    return tspl_job(img1, media, copies, extra_dark) if setting('language') == 'TSPL' else zpl_job(img1, media, copies, extra_dark)


def print_bitmap(img1, media, copies=1, extra_dark=False):
    """Print a 1-bit bitmap (from to_1bit) on media (RECEIPT or LABELS).  Returns a short message, raises on failure."""
    return send_raw(build_job(img1, media, copies, extra_dark))


def print_bitmaps(pages, media, sets=1):
    """Print several 1-bit bitmaps one after another as one job, the whole run sets times (1, 2, 3, 1, 2, 3...).  Returns a short message."""
    return send_raw(b'\n'.join(build_job(page, media) for _ in range(max(1, int(sets))) for page in pages))


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Getting bytes to the printer
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def list_windows_printers():
    try:
        import win32print
        return sorted(p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS))
    except Exception:
        return []


def feed(inches=1):
    """Feed paper out of the printer (no printing).  Returns a short message, raises on failure."""
    dots = round(inches * DPI)
    if setting('language') == 'TSPL':
        data = f'FEED {dots}\r\n'.encode('ascii')
    else:
        data = f'^XA^MNN^PW{HEAD_DOTS}^LL{dots}^FO0,0^GB8,1,1,W^FS^XZ'.encode('ascii')
    return send_raw(data)


def send_raw(data):
    """Send printer-language bytes unchanged.  Returns a short message, raises an exception with a readable reason on failure."""
    if setting('connection') == 'network':
        try:
            with socket.create_connection((setting('ip'), int(setting('port'))), timeout=6) as sock:
                sock.sendall(data)
        except OSError as e:
            raise RuntimeError(f"Could not reach the printer at {setting('ip')}:{setting('port')}\n{e}")
        return f"Sent {len(data):,} bytes to {setting('ip')}"
    try:
        import win32print
    except ImportError:
        raise RuntimeError('USB printing needs pywin32:    python -m pip install pywin32\n(or switch Setup to Ethernet)')
    name = setting('win_printer')
    if not name:
        raise RuntimeError('No printer picked yet - open Printer setup and choose the iD880')
    handle = win32print.OpenPrinter(name)
    try:
        win32print.StartDocPrinter(handle, 1, ('iD880 PySimpleGUI job', None, 'RAW'))
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, data)
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    finally:
        win32print.ClosePrinter(handle)
    return f'Sent {len(data):,} bytes to "{name}"'


def query_network(data, wait=1.5):
    """Send a status request over Ethernet and return whatever the printer answers (USB through Windows can't read answers)"""
    if setting('connection') != 'network':
        raise RuntimeError('Reading answers from the printer only works with the Ethernet connection')
    reply = b''
    with socket.create_connection((setting('ip'), int(setting('port'))), timeout=6) as sock:
        sock.sendall(data)
        sock.settimeout(wait)
        try:
            while chunk := sock.recv(4096):
                reply += chunk
        except socket.timeout:
            pass
    return reply


def popup_print_error(e):
    sg.popup_error('Could not print', str(e), '', HELP_TEXT, title='iD880', keep_on_top=True)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Window helpers - previews and the standard scroll keys
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def png_bytes(img):
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    return bio.getvalue()


def preview_png(img, max_width=None, max_height=None):
    """PNG for an sg.Image - shrunk to fit if needed, with a thin grey edge so the paper's edges show"""
    im = img.convert('L')
    scale = min(1.0, (max_width or im.width) / im.width, (max_height or im.height) / im.height)
    if scale < 1:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), LANCZOS)
    return png_bytes(ImageOps.expand(im, border=1, fill=170))


K_SCROLL_KEY = '-SCROLL KEY-'
KT_SCROLL_KEY = lambda tk_key: (K_SCROLL_KEY, tk_key)
SCROLL_KEYS = {'<Up>': (-1, 'units'), '<Down>': (1, 'units'), '<Prior>': (-1, 'pages'), '<Next>': (1, 'pages'), '<Home>': (0, 'top'), '<End>': (1, 'bottom')}
TYPING_ELEMENTS = (sg.Input, sg.Combo, sg.Spin, sg.Slider)


def bind_print_key(window, print_key):
    """Ctrl+P prints.  Ctrl+Alt+P never prints - a tkinter <Control-p> binding also fires with Alt held, and Ctrl+Alt+P belongs to
    psghotkey (it types PySimpleGUI)."""
    window.bind('<Control-p>', print_key)
    for key in ('<Control-Alt-p>', '<Control-Alt-P>'):              # with and without Caps Lock / Shift
        window.TKroot.bind(key, lambda e: 'break')


def bind_scroll_keys(window):
    """Up/Down = 1 line, PgUp/PgDn = 1 page, Home/End = top/bottom.  Events arrive as KT_SCROLL_KEY(tk key)."""
    for tk_key in SCROLL_KEYS:
        window.bind(tk_key, KT_SCROLL_KEY(tk_key))


def is_scroll_key(event):
    return isinstance(event, tuple) and len(event) == 2 and event[0] == K_SCROLL_KEY


def yview_widget(element):
    if isinstance(element, sg.Column):
        frame = getattr(element, 'TKColFrame', None) or element.Widget
        return getattr(frame, 'canvas', frame)
    return element.Widget


def typing_has_focus(window):
    """True when the keyboard focus is in a field the user types or picks in - those keep their own arrow/Home/End keys"""
    focus = window.find_element_with_focus()
    return isinstance(focus, TYPING_ELEMENTS) or (isinstance(focus, sg.Multiline) and not focus.Disabled)


def scroll_with_key(window, target_key, event):
    """Scroll target_key's element for a scroll-key event.  Keys typed into an input field are left for the field."""
    amount, how = SCROLL_KEYS[event[1]]
    if typing_has_focus(window):
        return
    focus = window.find_element_with_focus()
    if isinstance(focus, sg.Listbox):                               # a Listbox handles arrows & pages itself - add Home/End
        if how in ('top', 'bottom'):
            focus.Widget.yview_moveto(amount)
        return
    try:
        widget = yview_widget(window[target_key])
        widget.yview_moveto(amount) if how in ('top', 'bottom') else widget.yview_scroll(amount, how)
    except Exception:
        pass
