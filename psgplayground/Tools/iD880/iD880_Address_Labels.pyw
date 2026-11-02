#!/usr/bin/env python
"""
iD880 Address Labels - mailing labels (From + To), To-only labels and return address labels on the continuous label roll

    Your return address is remembered.  To addresses can be saved in the address book on the left.
    Length "Fit to text" uses just enough label.  Pick a length (like 6 in for a 4x6 package label) and the text grows to fill it.
    Ctrl+P prints.   Esc closes.   Up/Down, PgUp/PgDn, Home/End scroll the preview (or the address book when it has focus).

Needs id880_lib.py in the same folder.   Run iD880_Setup.pyw once first to pick the printer.
"""
import PySimpleGUI as sg
from PIL import Image, ImageDraw

import id880_lib as lib

K_FROM = '-FROM-'
K_TO = '-TO-'
K_BOOK = '-BOOK-'
K_PASTE = '-PASTE-'
K_SAVE = '-SAVE-'
K_NEW = '-NEW-'
K_DELETE = '-DELETE-'
K_MEDIA = '-MEDIA-'
K_LENGTH = '-LENGTH-'
K_LAYOUT = '-LAYOUT-'
K_EXTRA = '-EXTRA-'
K_COPIES = '-COPIES-'
K_PREVIEW = '-PREVIEW-'
K_PREVIEW_COL = '-PREVIEW COL-'
K_FIT = '-FIT-'
K_PRINT = '-PRINT-'
K_SETUP = '-SETUP-'
K_FEED = '-FEED-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_CTRL_P = '-CTRL P-'

MAILING, TO_ONLY, RETURN_ONLY = 'Mailing label (From + To)', 'To address only', 'Return address only'
LAYOUTS = (MAILING, TO_ONLY, RETURN_ONLY)
LENGTHS = {'Fit to text': None, '1 in': 1, '1.5 in': 1.5, '2 in': 2, '3 in': 3, '4 in': 4, '6 in  (4x6)': 6}
FAMILY = 'Sans'
OPTION_SETTINGS = {K_MEDIA: 'addr_media', K_LENGTH: 'addr_length', K_LAYOUT: 'addr_layout', K_EXTRA: 'addr_extra'}


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Drawing the label
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def address_lines(text):
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def fit_points(lines, box_width, box_height, largest, smallest=9):
    """Biggest point size from largest down to smallest where the lines fit (box_height None = any height).  Returns (points, fits)"""
    for points in range(largest, smallest - 1, -1):
        bold, regular = lib.font(FAMILY, points, bold=True), lib.font(FAMILY, points)
        widest = max([bold.getlength(lines[0])] + [regular.getlength(s) for s in lines[1:]])
        if widest <= box_width and (box_height is None or len(lines) * lib.line_height(regular) <= box_height):
            return points, True
    return smallest, False


def block_size(lines, points):
    bold, regular = lib.font(FAMILY, points, bold=True), lib.font(FAMILY, points)
    return round(max([bold.getlength(lines[0])] + [regular.getlength(s) for s in lines[1:]])), len(lines) * lib.line_height(regular)


def draw_block(d, x, y, lines, points):
    """Address block, first line (the name) in bold"""
    bold, regular = lib.font(FAMILY, points, bold=True), lib.font(FAMILY, points)
    for i, s in enumerate(lines):
        d.text((x, y + i * lib.line_height(regular)), s, font=bold if i == 0 else regular, fill=0)


def render(width, length_in, layout, from_text, to_text, extra):
    """Returns (grayscale picture, list of warnings).  length_in None = just long enough for the text."""
    m = lib.mm_dots(3)
    inner = width - 2 * m
    fixed = lib.inch_dots(length_in) if length_in else None
    from_lines = address_lines(from_text) or ['(your return address)']
    to_lines = address_lines(to_text) or ['(type the To address)']
    caption = lib.font(FAMILY, 9, bold=True)
    banner = lib.font(FAMILY, 12 if fixed and fixed < lib.inch_dots(2) else 16, bold=True)
    banner_h = lib.line_height(banner) + lib.mm_dots(2) if extra.strip() else 0
    space = max(lib.mm_dots(6), fixed - 2 * m - (banner_h + lib.mm_dots(1.5) if banner_h else 0)) if fixed else None      # room for the addresses
    warnings, ops = [], []
    y = m

    if layout in (TO_ONLY, RETURN_ONLY):
        lines = to_lines if layout == TO_ONLY else from_lines
        points, fits = fit_points(lines, inner, space, largest=(40 if layout == TO_ONLY else 32) if fixed else (22 if layout == TO_ONLY else 14))
        bw, bh = block_size(lines, points)
        top = y + max(0, (space - bh) // 2) if fixed else y
        ops.append(('block', m + (inner - bw) // 2, top, lines, points))
        y = top + bh
        if not fits:
            warnings.append('Too much text for this length - pick a longer label')
    else:
        indent = round(width * 0.08)
        cap_h = lib.line_height(caption)
        from_space = round(space * 0.3) - cap_h if fixed else None
        from_pt, from_fits = fit_points(from_lines, inner, from_space, largest=12 if fixed else 11)
        ops.append(('caption', m, y, 'FROM'))
        y += cap_h
        ops.append(('block', m, y, from_lines, from_pt))
        y = (m + round(space * 0.3)) if fixed else y + block_size(from_lines, from_pt)[1]
        y += lib.mm_dots(1.5)
        ops.append(('rule', y))
        y += lib.mm_dots(2)
        ops.append(('caption', m, y, 'SHIP TO'))
        y += cap_h + lib.mm_dots(1)
        to_space = (m + space - y) if fixed else None
        to_pt, to_fits = fit_points(to_lines, inner - indent, to_space, largest=28 if fixed else 20)
        bh = block_size(to_lines, to_pt)[1]
        top = y + max(0, (to_space - bh) // 3) if fixed else y
        ops.append(('block', m + indent, top, to_lines, to_pt))
        y = top + bh
        if not (from_fits and to_fits):
            warnings.append('Too much text for this length - pick a longer label')

    if banner_h:
        top = (fixed - m - banner_h) if fixed else y + lib.mm_dots(2)
        ops.append(('banner', top, extra.strip().upper()))
        y = top + banner_h
    height = fixed or y + m
    img = Image.new('L', (width, height), 255)
    d = ImageDraw.Draw(img)
    for op in ops:
        if op[0] == 'block':
            draw_block(d, *op[1:])
        elif op[0] == 'caption':
            d.text(op[1:3], op[3], font=caption, fill=0)
        elif op[0] == 'rule':
            d.line([(m, op[1]), (width - m, op[1])], fill=0, width=3)
        elif op[0] == 'banner':
            d.rectangle([m, op[1], width - m, op[1] + banner_h], fill=0)
            text = op[2] if banner.getlength(op[2]) <= inner - 16 else lib.wrap(op[2], banner, inner - 16)[0]
            d.text((m + (inner - banner.getlength(text)) / 2, op[1] + lib.mm_dots(1)), text, font=banner, fill=255)
    return img, warnings


def update_preview(window, values):
    img, warnings = render(lib.media_width(values[K_MEDIA]), LENGTHS.get(values[K_LENGTH]), values[K_LAYOUT], values[K_FROM], values[K_TO], values[K_EXTRA])
    img1 = lib.to_1bit(img)
    window[K_PREVIEW].update(data=lib.preview_png(img1, max_width=380))
    window.refresh()                                                # let tkinter size the new picture before the scroll area is measured
    window[K_PREVIEW_COL].contents_changed()
    size = f'{img1.height / lib.DPI:.2f} in long'
    window[K_FIT].update(f'{size}   -   {warnings[0]}' if warnings else size, text_color=lib.ORANGE if warnings else lib.HINT_COLOR)
    return img1


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Address book (saved in the shared settings file)
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def book():
    return dict(lib.setting('address_book') or {})


def book_names():
    return sorted(book(), key=str.lower)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def make_window():
    sg.theme(lib.THEME)
    media = lib.setting('addr_media') or lib.LABELS
    length = lib.setting('addr_length') or 'Fit to text'
    layout_name = lib.setting('addr_layout') or MAILING
    hint = dict(font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)
    from_box = sg.Multiline(lib.setting('from_address') or '', key=K_FROM, size=(40, 5), enable_events=True, expand_x=True)
    from_frame = sg.Frame('From  -  your return address', [[from_box]], expand_x=True)
    book_list = sg.Listbox(book_names(), key=K_BOOK, size=(20, 9), enable_events=True, tooltip=' Saved addresses - click one to use it ')
    to_box = sg.Multiline(lib.setting('last_to') or '', key=K_TO, size=(32, 6), enable_events=True)
    to_buttons = [sg.Button('Paste', key=K_PASTE), sg.Button('Save to book', key=K_SAVE), sg.Button('New', key=K_NEW),
                  sg.Button('Delete', key=K_DELETE, button_color=('white', lib.RED))]
    to_frame = sg.Frame('To', [[book_list, sg.Column([[to_box], to_buttons])]], expand_x=True)
    media_combo = sg.Combo(lib.MEDIA, media if media in lib.MEDIA else lib.LABELS, key=K_MEDIA, readonly=True, enable_events=True, size=(13, 1))
    length_combo = sg.Combo(list(LENGTHS), length if length in LENGTHS else 'Fit to text', key=K_LENGTH, readonly=True, enable_events=True, size=(11, 1))
    layout_combo = sg.Combo(LAYOUTS, layout_name if layout_name in LAYOUTS else MAILING, key=K_LAYOUT, readonly=True, enable_events=True, size=(26, 1))
    extra = sg.Input(lib.setting('addr_extra') or '', key=K_EXTRA, size=(22, 1), enable_events=True)
    label_frame = sg.Frame('Label', [[sg.Text('Print on'), media_combo, sg.Text('Length'), length_combo], [sg.Text('Layout'), layout_combo],
                                     [sg.Text('Extra line'), extra, sg.Text('like FRAGILE  (blank = none)', **hint)]], expand_x=True)
    print_row = [sg.Button('Print', key=K_PRINT, size=(10, 1), button_color=('white', lib.GREEN)), sg.Text('Copies'),
                 sg.Spin(list(range(1, 101)), initial_value=1, key=K_COPIES, size=(3, 1)), sg.Push(), sg.Button('Feed 1 inch', key=K_FEED),
                 sg.Button('Printer setup', key=K_SETUP, button_color=('white', lib.BLUE))]
    left = sg.Column([[from_frame], [to_frame], [label_frame], print_row, [sg.Text('', key=K_FIT, **hint)]], vertical_alignment='top')
    preview = sg.Column([[sg.Image(key=K_PREVIEW, pad=(14, 14), background_color=lib.PREVIEW_BG)]], key=K_PREVIEW_COL, scrollable=True, vertical_scroll_only=True,
                        size=(420, 560), background_color=lib.PREVIEW_BG, expand_y=True)
    layout = [[left, preview], [sg.Text(lib.printer_summary(), key=K_STATUS, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)]]
    window = sg.Window('iD880 Address Labels', layout, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, finalize=True, resizable=True)
    lib.bind_scroll_keys(window)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Control-p>', K_CTRL_P)
    window.TKroot.bind('<Control-Alt-p>', lambda e: 'break')       # Ctrl+Alt+P belongs to other hotkeys (like typing PySimpleGUI) - it doesn't print
    return window


def main():
    window = make_window()
    img1, dirty = None, True
    while True:
        event, values = window.read(timeout=250 if dirty else None)
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
        elif event in (K_FROM, K_TO):
            dirty = True
        elif event in OPTION_SETTINGS:
            lib.save_setting(OPTION_SETTINGS[event], values[event])
            dirty = True
        elif event == sg.TIMEOUT_KEY and dirty:
            img1, dirty = update_preview(window, values), False
            lib.save_setting('from_address', values[K_FROM])
            lib.save_setting('last_to', values[K_TO])
        elif event == K_BOOK and values[K_BOOK]:
            window[K_TO].update(book().get(values[K_BOOK][0], ''))
            dirty = True
        elif event == K_PASTE:
            window[K_TO].update('\n'.join(address_lines(sg.clipboard_get() or '')))
            dirty = True
        elif event == K_NEW:
            window[K_TO].update('')
            window[K_BOOK].update(set_to_index=[])
            dirty = True
        elif event == K_SAVE:
            lines = address_lines(values[K_TO])
            if not lines:
                sg.popup_quick_message('Type a To address first', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
                continue
            addresses = book()
            addresses[lines[0]] = '\n'.join(lines)
            lib.save_setting('address_book', addresses)
            names = book_names()
            window[K_BOOK].update(names, set_to_index=[names.index(lines[0])])
        elif event == K_DELETE and values[K_BOOK]:
            name = values[K_BOOK][0]
            if sg.popup_yes_no(f'Delete "{name}" from the address book?', title='iD880 Address Labels', keep_on_top=True) == 'Yes':
                addresses = book()
                addresses.pop(name, None)
                lib.save_setting('address_book', addresses)
                window[K_BOOK].update(book_names())
        elif event in (K_PRINT, K_CTRL_P):
            needs_to, needs_from = values[K_LAYOUT] != RETURN_ONLY, values[K_LAYOUT] != TO_ONLY
            if (needs_to and not address_lines(values[K_TO])) or (needs_from and not address_lines(values[K_FROM])):
                sg.popup_quick_message('Fill in the address first', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
                continue
            img1, dirty = update_preview(window, values), False
            try:
                window[K_STATUS].update(f'Printed: {lib.print_bitmap(img1, values[K_MEDIA], values[K_COPIES])}    ({lib.printer_summary()})', text_color='#9CCC65')
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
