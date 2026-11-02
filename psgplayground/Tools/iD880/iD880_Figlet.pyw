#!/usr/bin/env python
"""
iD880 Figlet - big FIGlet lettering printed on the iD880 - psgfiglet for the receipt printer

    Type your words, pick one of pyfiglet's 571 fonts and print.   Type in Filter to shorten the list.   Up/Down in a list steps through the fonts.
    Favorites:  Add to favorites (Ctrl+D) puts the font you're looking at in the Favorites list at the top.   Remove (or Delete in that list) takes it out.
        The first time, any favorites you saved in psgfiglet come over too.
        Layout    Upright - reads across the paper, long lines wrap between words      Sideways - one long banner down the roll
        Size      Fit the paper - as big as it can go             or a fixed size, 1 to 48 points (under 4 points use Solid blocks)
        Draw as   Characters - the FIGlet text itself              Solid blocks - every character filled in (bold - best for fonts made of #)
        Extra dark  prints at the darkest setting and slowest speed, whatever Setup says - big black areas print gray at normal speed
    Copy text puts the FIGlet text on the clipboard.   Random font picks one from the list.
    Ctrl+P prints.   Esc closes.   Click the preview, then Up/Down, PgUp/PgDn, Home/End scroll it.

Needs id880_lib.py in the same folder, and pyfiglet:   python -m pip install pyfiglet
"""
import functools
import random

import PySimpleGUI as sg
from PIL import Image, ImageDraw

import id880_lib as lib

try:
    import pyfiglet
except ImportError:
    pyfiglet = None

K_TEXT = '-TEXT-'
K_FILTER = '-FILTER-'
K_FONTS = '-FONTS-'
K_COUNT = '-COUNT-'
K_FAVS = '-FAVS-'
K_FAVS_DELETE = '-FAVS-+DELETE'
K_ADD_FAV = '-ADD FAV-'
K_REMOVE_FAV = '-REMOVE FAV-'
K_FONT_NAME = '-FONT NAME-'
K_CTRL_D = '-CTRL D-'
K_RANDOM = '-RANDOM-'
K_MEDIA = '-MEDIA-'
K_LAYOUT = '-LAYOUT-'
K_SIZE = '-SIZE-'
K_STYLE = '-STYLE-'
K_ALIGN = '-ALIGN-'
K_EXTRA_DARK = '-EXTRA DARK-'
K_INFO = '-INFO-'
K_PREVIEW = '-PREVIEW-'
K_PREVIEW_COL = '-PREVIEW COL-'
K_PREVIEW_CLICK = '-PREVIEW-+CLICK'
K_PRINT = '-PRINT-'
K_COPIES = '-COPIES-'
K_COPY = '-COPY-'
K_FEED = '-FEED-'
K_SETUP = '-SETUP-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_CTRL_P = '-CTRL P-'

UPRIGHT, SIDEWAYS = 'Upright', 'Sideways (banner)'
FIT = 'Fit the paper'
SIZES = [FIT] + [f'{n} pt' for n in (1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 18, 24, 36, 48)]
CHARACTERS, SOLID = 'Characters', 'Solid blocks'
SETTINGS = {K_MEDIA: 'fig_media', K_LAYOUT: 'fig_layout', K_SIZE: 'fig_size', K_STYLE: 'fig_style', K_ALIGN: 'fig_align', K_EXTRA_DARK: 'fig_extra_dark'}
MARGIN = lib.mm_dots(2)                                             # white left and right of the lettering
TOP = lib.mm_dots(3)                                                # white above and below
SMALLEST_CHARACTER = 5                                              # dots - drawn characters narrower than this blur together
SMALLEST_BLOCK = 1.5                                                # dots - solid blocks still print down to here
LONG_PRINT_IN = 24                                                  # ask before printing anything longer than this
PREVIEW_W, PREVIEW_H = 520, 600
FAVORITE_COLOR = '#FFE082'
DEFAULT_TEXT = 'Hello!'


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  FIGlet text
# ----------------------------------------------------------------------------------------------------------------------------------------------------
@functools.lru_cache(maxsize=4096)
def fig_rows(font, text):
    """One line of text in a FIGlet font - never wrapped - with blank rows and the shared left indent trimmed off"""
    rows = pyfiglet.Figlet(font=font, width=100000).renderText(text).replace('\r', '').split('\n')
    rows = [r.rstrip() for r in rows]
    while rows and not rows[-1]:
        rows.pop()
    while rows and not rows[0]:
        rows.pop(0)
    lead = min((len(r) - len(r.lstrip()) for r in rows if r), default=0)
    return tuple(r[lead:] for r in rows)


def wrapped_rows(font, line, columns):
    """FIGlet blocks for one typed line, starting a new block between words whenever the next word would go past columns"""
    blocks, words, part = [], line.split(), ''
    for word in words:
        trial = f'{part} {word}' if part else word
        if part and columns and max(map(len, fig_rows(font, trial)), default=0) > columns:
            blocks.append(fig_rows(font, part))
            part = word
        else:
            part = trial
    blocks.append(fig_rows(font, part))
    return blocks


def fig_grid(font, text, columns=None, center=False):
    """All the typed lines as one grid of FIGlet rows, a blank row between blocks.  columns=None never wraps."""
    blocks = []
    for line in text.split('\n'):
        blocks += wrapped_rows(font, line, columns) if line.strip() else [('',)]
    width = max((len(r) for block in blocks for r in block), default=0)
    grid = []
    for block in blocks:
        pad = (width - max(map(len, block), default=0)) // 2 if center else 0
        grid += [' ' * pad + r for r in block] + ['']
    return grid[:-1], width


@functools.lru_cache(maxsize=1)
def mono_advance():
    """Dots one monospaced character takes across, per point of font size"""
    return lib.font('Mono', 100, True).getlength('M') / 100


def draw_grid(grid, columns, cell_w, style):
    """The FIGlet grid drawn in black on white.  Cells are cell_w dots wide (fractions allowed) and as tall as the font."""
    cell_h = cell_w * lib.DPI / 72 / mono_advance()                 # monospaced fonts are about twice as tall as wide
    img = Image.new('L', (max(1, round(columns * cell_w)), max(1, round(len(grid) * cell_h))), 255)
    d = ImageDraw.Draw(img)
    f = lib.font('Mono', round(cell_w / mono_advance() * 4) / 4, True) if style == CHARACTERS else None
    for r, row in enumerate(grid):
        y0, y1 = round(r * cell_h), round((r + 1) * cell_h)
        for c, ch in enumerate(row):
            if ch == ' ':
                continue
            x0, x1 = round(c * cell_w), round((c + 1) * cell_w)
            if f:
                d.text(((x0 + x1) / 2, (y0 + y1) / 2), ch, font=f, fill=0, anchor='mm')
            else:
                d.rectangle((x0, y0, max(x0, x1 - 1), max(y0, y1 - 1)), fill=0)
    return img


def make_print(text, font, paper_w, layout, size, style, align):
    """Returns (1-bit picture to print, FIGlet text, info lines, warn).  Raises if the font can't draw the text."""
    usable = paper_w - 2 * MARGIN
    sideways, center = layout == SIDEWAYS, align == 'Center' or layout == SIDEWAYS
    tall = lib.DPI / 72 / mono_advance()                            # cell height / cell width
    notes = []
    if size == FIT or sideways:
        grid, columns = fig_grid(font, text, None, center)          # Fit and Sideways never wrap
    if size == FIT:
        cell_w = usable / max(1, len(grid)) / tall if sideways else usable / max(1, columns)
    else:
        cell_w = int(size.split()[0]) * mono_advance()
        if sideways and len(grid) * cell_w * tall > usable:
            cell_w = usable / len(grid) / tall
            notes.append('Shrunk so it fits across the paper')
        elif not sideways:
            grid, columns = fig_grid(font, text, max(1, int(usable // cell_w)), center)
            cell_w = min(cell_w, usable / max(1, columns))          # one word wider than the paper gets shrunk
    img = draw_grid(grid, columns, cell_w, style)
    if sideways:
        img = img.rotate(270, expand=True)                          # turned clockwise: the start of the text prints first
    paper = Image.new('L', (paper_w, img.height + 2 * TOP), 255)
    paper.paste(img, ((paper_w - img.width) // 2 if center else MARGIN, TOP))
    letters = len(grid) * cell_w * tall / lib.DPI
    inches = paper.height / lib.DPI
    warn = cell_w < SMALLEST_BLOCK or (style == CHARACTERS and cell_w < SMALLEST_CHARACTER)
    if warn:
        notes.append('Too small to print clearly - try Solid blocks' if style == CHARACTERS and cell_w >= SMALLEST_BLOCK else 'Too small to print - try Sideways')
    info = [f'{columns} x {len(grid)} characters,  lettering {letters:.2f} in {"across" if sideways else "tall"}', f'Uses {inches:.1f} in of paper'] + notes
    return lib.to_1bit(paper), '\n'.join(grid), info, warn or inches > LONG_PRINT_IN


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def all_fonts():
    return sorted(pyfiglet.FigletFont.getFonts(), key=str.lower)


def load_favorites(fonts):
    """Saved favorite fonts.  The very first time, psgfiglet's favorites come over."""
    favorites = lib.setting('fig_favorites')
    if favorites is None:
        try:
            favorites = sg.UserSettings(filename='psgfiglet.json').get('-favorites-', []) or []
        except Exception:
            favorites = []
        favorites = sorted({f for f in favorites if f in fonts}, key=str.lower)
        lib.save_setting('fig_favorites', favorites)
    return [f for f in favorites if f in fonts]


def pick(listbox, names, current):
    """Highlight current in a font list (and scroll to it), or clear the highlight if it isn't there"""
    if current in names:
        listbox.update(set_to_index=[names.index(current)], scroll_to_index=max(0, names.index(current) - 4))
    else:
        listbox.update(set_to_index=[])


def show_fonts(window, shown, favorites, current):
    """Fill both font lists and show which font is in use"""
    window[K_FONTS].update(shown)
    window[K_FAVS].update(favorites)
    show_current(window, shown, favorites, current)
    window[K_COUNT].update(f'{len(shown)} fonts')


def show_current(window, shown, favorites, current):
    pick(window[K_FONTS], shown, current)
    pick(window[K_FAVS], favorites, current)
    window[K_FONT_NAME].update(f'Font:  {current}' + ('    (a favorite)' if current in favorites else ''))
    window[K_ADD_FAV].update(disabled=current in favorites)
    window[K_REMOVE_FAV].update(disabled=current not in favorites)


def make_window():
    sg.theme(lib.THEME)
    s = lib.setting
    hint = dict(font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)
    value = lambda key, default, allowed: s(SETTINGS[key]) if s(SETTINGS[key]) in allowed else default
    combo = dict(readonly=True, enable_events=True, size=(16, 1))
    text = sg.Multiline(s('fig_text') or DEFAULT_TEXT, key=K_TEXT, size=(34, 4), font=('Consolas', 12), enable_events=True, expand_x=True)
    fav_buttons = [sg.Button('Add to favorites', key=K_ADD_FAV, button_color=('white', lib.GREEN), tooltip=' Ctrl+D '),
                   sg.Button('Remove', key=K_REMOVE_FAV, button_color=('white', lib.RED), tooltip=' Takes the font out of Favorites (or press Delete in that list) ')]
    fonts = sg.Column([[sg.Text('Your words', font=('Helvetica', 11, 'bold'))], [text],
                       [sg.Text('', key=K_FONT_NAME, size=(34, 1), font=('Helvetica', 11, 'bold'), text_color=FAVORITE_COLOR)],
                       [sg.Text('Favorites', text_color=FAVORITE_COLOR)],
                       [sg.Listbox([], key=K_FAVS, size=(34, 7), enable_events=True)], fav_buttons,
                       [sg.Text('All fonts'), sg.Push(), sg.Text('Filter'), sg.Input('', key=K_FILTER, size=(12, 1), enable_events=True),
                        sg.Text('', key=K_COUNT, **hint)],
                       [sg.Listbox([], key=K_FONTS, size=(34, 12), enable_events=True, expand_y=True)],
                       [sg.Button('Random font', key=K_RANDOM), sg.Button('Copy text', key=K_COPY, tooltip=' The FIGlet text, onto the clipboard ')]],
                      vertical_alignment='top', expand_y=True)
    options = sg.Frame('Paper and lettering', [
        [sg.Text('Print on', size=(8, 1)), sg.Combo(lib.MEDIA, value(K_MEDIA, lib.RECEIPT, lib.MEDIA), key=K_MEDIA, **combo)],
        [sg.Text('Layout', size=(8, 1)), sg.Combo([UPRIGHT, SIDEWAYS], value(K_LAYOUT, UPRIGHT, (UPRIGHT, SIDEWAYS)), key=K_LAYOUT, **combo)],
        [sg.Text('Size', size=(8, 1)), sg.Combo(SIZES, value(K_SIZE, FIT, SIZES), key=K_SIZE, **combo)],
        [sg.Text('Draw as', size=(8, 1)), sg.Combo([CHARACTERS, SOLID], value(K_STYLE, CHARACTERS, (CHARACTERS, SOLID)), key=K_STYLE, **combo)],
        [sg.Text('Line up', size=(8, 1)), sg.Combo(['Center', 'Left'], value(K_ALIGN, 'Center', ('Center', 'Left')), key=K_ALIGN, **combo)],
        [sg.Checkbox('Extra dark  (prints slower)', value(K_EXTRA_DARK, True, (True, False)), key=K_EXTRA_DARK, enable_events=True,
                     tooltip=' Darkest setting at the slowest speed - big black areas need the extra heat to print solid black ')],
        [sg.Text('', key=K_INFO, size=(40, 3), **hint)]])
    print_row = [sg.Button('Print', key=K_PRINT, size=(10, 1), button_color=('white', lib.GREEN)), sg.Text('Copies'),
                 sg.Spin(list(range(1, 21)), initial_value=1, key=K_COPIES, size=(3, 1))]
    tool_row = [sg.Button('Feed 1 inch', key=K_FEED), sg.Button('Printer setup', key=K_SETUP, button_color=('white', lib.BLUE))]
    help_text = sg.Text('Upright - reads across the paper\nSideways - a long banner down the roll\nSolid blocks - darkest, best for fonts made of #',
                        **hint)
    controls = sg.Column([[options], print_row, tool_row, [help_text]], vertical_alignment='top')
    preview = sg.Column([[sg.Image(key=K_PREVIEW, pad=(12, 12), background_color=lib.PREVIEW_BG)]], key=K_PREVIEW_COL, scrollable=True,
                        vertical_scroll_only=True, size=(PREVIEW_W + 40, PREVIEW_H), background_color=lib.PREVIEW_BG, expand_y=True)
    right = sg.Column([[sg.Text('What will print', font=('Helvetica', 11, 'bold'))], [preview]], vertical_alignment='top', expand_y=True)
    layout = [[fonts, controls, right], [sg.Text(lib.printer_summary(), key=K_STATUS, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)]]
    window = sg.Window('iD880 Figlet', layout, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, finalize=True, resizable=True)
    lib.bind_scroll_keys(window)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Control-p>', K_CTRL_P)
    window.TKroot.bind('<Control-Alt-p>', lambda e: 'break')       # Ctrl+Alt+P belongs to other hotkeys (like typing PySimpleGUI) - it doesn't print
    window.bind('<Control-d>', K_CTRL_D)
    window[K_PREVIEW].bind('<Button-1>', '+CLICK')
    window[K_FAVS].bind('<Delete>', '+DELETE')
    return window


def update_preview(window, font, values):
    """Redraw what will print.  Returns (1-bit picture, FIGlet text) - or (None, '') if the font can't draw the text."""
    try:
        img1, text, info, warn = make_print(values[K_TEXT].rstrip() or ' ', font, lib.media_width(values[K_MEDIA]), values[K_LAYOUT], values[K_SIZE],
                                            values[K_STYLE], values[K_ALIGN])
    except Exception as e:
        window[K_INFO].update(f'The font "{font}" can\'t draw this\n{str(e)[:80]}', text_color=lib.ORANGE)
        return None, ''
    window[K_PREVIEW].update(data=lib.preview_png(img1, max_width=PREVIEW_W))
    window.refresh()                                                # let tkinter size the new picture before the scroll area is measured
    window[K_PREVIEW_COL].contents_changed()
    window[K_INFO].update('\n'.join(info), text_color=lib.ORANGE if warn else lib.HINT_COLOR)
    return img1, text


def main():
    if pyfiglet is None:
        sg.popup_error('iD880 Figlet needs pyfiglet.  Install it with:', 'python -m pip install pyfiglet', title='iD880 Figlet', keep_on_top=True)
        return
    window = make_window()
    fonts = all_fonts()
    font = lib.setting('fig_font') if lib.setting('fig_font') in fonts else 'standard'
    shown, favorites = fonts, load_favorites(fonts)
    show_fonts(window, shown, favorites, font)
    img1, fig_text, dirty = None, '', True
    while True:
        event, values = window.read(timeout=150 if dirty else None)
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        if event == K_ESCAPE:
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70,10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif lib.is_scroll_key(event):
            lib.scroll_with_key(window, K_PREVIEW_COL, event)
        elif event == K_PREVIEW_CLICK:
            window[K_PREVIEW].Widget.focus_set()                    # so the scroll keys go to the preview
        elif event == K_TEXT:
            dirty = True
        elif event == K_FILTER:
            shown = [f for f in fonts if values[K_FILTER].strip().lower() in f.lower()]
            show_fonts(window, shown, favorites, font)
        elif event in (K_FONTS, K_FAVS) and values[event] and values[event][0] != font:
            font, dirty = values[event][0], True
            lib.save_setting('fig_font', font)
            show_current(window, shown, favorites, font)
        elif event == K_RANDOM and shown:
            font, dirty = random.choice(shown), True
            lib.save_setting('fig_font', font)
            show_current(window, shown, favorites, font)
        elif event in (K_ADD_FAV, K_CTRL_D) and font not in favorites:
            favorites = sorted(favorites + [font], key=str.lower)
            lib.save_setting('fig_favorites', favorites)
            show_fonts(window, shown, favorites, font)
            window[K_STATUS].update(f'Added "{font}" to your favorites', text_color='#9CCC65')
        elif event in (K_REMOVE_FAV, K_FAVS_DELETE):
            gone = values[K_FAVS][0] if event == K_FAVS_DELETE and values[K_FAVS] else font
            if gone in favorites:
                favorites = [f for f in favorites if f != gone]
                lib.save_setting('fig_favorites', favorites)
                show_fonts(window, shown, favorites, font)
                window[K_STATUS].update(f'Took "{gone}" out of your favorites', text_color='#9CCC65')
        elif event in SETTINGS:
            lib.save_setting(SETTINGS[event], values[event])
            dirty = True
        elif event == sg.TIMEOUT_KEY and dirty:
            (img1, fig_text), dirty = update_preview(window, font, values), False
            lib.save_setting('fig_text', values[K_TEXT].rstrip())
        elif event == K_COPY:
            (img1, fig_text), dirty = update_preview(window, font, values), False
            sg.clipboard_set(fig_text)
            window[K_STATUS].update(f'Copied the "{font}" text to the clipboard', text_color='#9CCC65')
        elif event in (K_PRINT, K_CTRL_P):
            (img1, fig_text), dirty = update_preview(window, font, values), False
            if img1 is None:
                continue
            inches = img1.height * int(values[K_COPIES]) / lib.DPI
            if inches > LONG_PRINT_IN and sg.popup_yes_no(f'This uses {inches:.0f} inches of paper.  Print it?', title='iD880 Figlet', keep_on_top=True) != 'Yes':
                continue
            try:
                sent = lib.print_bitmap(img1, values[K_MEDIA], values[K_COPIES], values[K_EXTRA_DARK])
                window[K_STATUS].update(f'Printed: {sent}    ({lib.printer_summary()})', text_color='#9CCC65')
            except Exception as e:
                window[K_STATUS].update('Print failed - see the message', text_color='#FF8A65')
                lib.popup_print_error(e)
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
