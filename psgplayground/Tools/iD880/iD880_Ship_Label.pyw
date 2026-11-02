#!/usr/bin/env python
"""
iD880 Ship Label - print a carrier's shipping or return label (PDF or picture) as a 4x6 label on the continuous label roll

    Open the PDF, or click "Newest download" right after downloading a label.
    The label is found automatically.  Not right?  Drag a box around it on the page, or try "Top half" (for the common
    letter-size PDFs that put the label on the top half of the page).
    Drag a PDF or picture from Explorer (or a browser download) onto the big page area to open it.
    Dropping a file on this program's icon also opens it.   Ctrl+V pastes a picture from the clipboard.   Ctrl+P prints.   Esc closes.   PgUp/PgDn/Home/End change pages.

PDFs need PyMuPDF:   python -m pip install pymupdf        Drag and drop needs psgdnd:   python -m pip install psgdnd
Needs id880_lib.py in the same folder.   Run iD880_Setup.pyw once first to pick the printer.
"""
import os
import sys

import PySimpleGUI as sg
from PIL import Image, ImageGrab, ImageOps

import id880_lib as lib

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None

try:
    import psgdnd
except ImportError:
    psgdnd = None

K_GRAPH = '-GRAPH-'
K_GRAPH_UP = '-GRAPH-+UP'
K_OPEN = '-OPEN-'
K_NEWEST = '-NEWEST-'
K_PASTE = '-PASTE-'
K_CTRL_V = '-CTRL V-'
K_FILE = '-FILE-'
K_PREV = '-PREV-'
K_NEXT = '-NEXT-'
K_PAGE = '-PAGE-'
K_AUTO = '-AUTO-'
K_TOP = '-TOP-'
K_FULL = '-FULL-'
K_CROP_INFO = '-CROP INFO-'
K_TURN = '-TURN-'
K_LENGTH = '-LENGTH-'
K_MEDIA = '-MEDIA-'
K_DARKER = '-DARKER-'
K_PREVIEW = '-PREVIEW-'
K_ALL_PAGES = '-ALL PAGES-'
K_COPIES = '-COPIES-'
K_PRINT = '-PRINT-'
K_SETUP = '-SETUP-'
K_FEED = '-FEED-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_CTRL_P = '-CTRL P-'

GRAPH_W, GRAPH_H = 430, 556                                         # letter-page shape
TURNS = {'As is': 0, 'Auto': None, 'Left 90': 90, 'Right 90': 270, 'Upside down': 180}      # Pillow rotates counter-clockwise
LENGTHS = {'6 in  (4x6)': 6, '5 in': 5, '4 in  (4x4)': 4, 'Fit to width': None}     # None = full width, as long as it needs to be
FILE_TYPES = ('.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', '.tiff')
MODE_TEXT = {'auto': 'Found automatically', 'top': 'Found in the top half', 'full': 'Whole page', 'manual': 'Your box'}


class Document:
    """A PDF (drawn by PyMuPDF) or a picture.  Sizes are in PDF points, or pixels for pictures."""

    def __init__(self, path, picture=None):
        self.path, self.pdf, self.picture = path, None, None
        if picture is not None:                                     # a picture already in memory (the clipboard)
            self.picture, self.pages = picture.convert('RGB'), 1
        elif path.lower().endswith('.pdf'):
            if pymupdf is None:
                raise RuntimeError('Opening PDFs needs PyMuPDF:\n\n    python -m pip install pymupdf')
            self.pdf = pymupdf.open(path)
            self.pages = self.pdf.page_count
        else:
            self.picture = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
            self.pages = 1

    def size(self, page):
        if self.pdf is not None:
            return self.pdf[page].rect.width, self.pdf[page].rect.height
        return self.picture.size

    def render(self, page, zoom, clip=None):
        """The page, or the clip = (x0, y0, x1, y1) part of it, as an RGB picture with zoom output pixels per page unit"""
        if self.pdf is not None:
            p = self.pdf[page]
            area = pymupdf.Rect(p.rect.x0 + clip[0], p.rect.y0 + clip[1], p.rect.x0 + clip[2], p.rect.y0 + clip[3]) if clip else None
            pix = p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=area, alpha=False)
            return Image.frombytes('RGB', (pix.width, pix.height), pix.samples, 'raw', 'RGB', pix.stride)
        pic = self.picture.crop(tuple(round(v) for v in clip)) if clip else self.picture
        return pic.resize((max(1, round(pic.width * zoom)), max(1, round(pic.height * zoom))), lib.LANCZOS)


def ink_mask(doc, page):
    """Low resolution map of where the page has printing (white = ink), and its scale in pixels per page unit"""
    w, h = doc.size(page)
    zoom = 100 / 72 if doc.pdf is not None else min(1.0, 1200 / max(w, h))
    return doc.render(page, zoom).convert('L').point(lambda p: 255 if p < 200 else 0), zoom


def ink(mask, zoom, region):
    return mask.crop(tuple(round(v * zoom) for v in region)).histogram()[255]


def box_around_ink(mask, zoom, region):
    """Box (page units) around the printing inside region (page units)"""
    px = tuple(round(v * zoom) for v in region)
    box = mask.crop(px).getbbox()
    if not box:
        return region
    pad = 4
    return (region[0] + max(0, box[0] - pad) / zoom, region[1] + max(0, box[1] - pad) / zoom,
            region[0] + min(px[2] - px[0], box[2] + pad) / zoom, region[1] + min(px[3] - px[1], box[3] + pad) / zoom)


def crop_for(doc, page, mode, manual):
    """The part of the page to print, in page units"""
    w, h = doc.size(page)
    if mode == 'full':
        return 0, 0, w, h
    if mode == 'manual' and manual:
        return max(0, manual[0]), max(0, manual[1]), min(w, manual[2]), min(h, manual[3])
    mask, zoom = ink_mask(doc, page)
    top = (0, 0, w, h / 2)
    if mode == 'top':
        return box_around_ink(mask, zoom, top)
    # Auto: a letter / A4 sheet with the printing mostly on the top half is the usual "label on top, instructions below" PDF
    top_ink, bottom_ink = ink(mask, zoom, top), ink(mask, zoom, (0, h / 2, w, h))
    if doc.pdf is not None and h >= 9 * 72 and h > w and top_ink and bottom_ink < top_ink * 0.25:
        return box_around_ink(mask, zoom, top)
    return box_around_ink(mask, zoom, (0, 0, w, h))


def build_label(doc, page, crop, turn, width, height, threshold):
    """Fit the cropped area onto a label width dots wide and height dots long (height None = fill the width, any length).
    Drawn straight at printer resolution so barcodes stay sharp."""
    margin = lib.mm_dots(2)
    crop_w, crop_h = crop[2] - crop[0], crop[3] - crop[1]
    angle = ((90 if crop_w > crop_h * 1.05 else 0) if height else 0) if turn is None else turn   # Auto only turns to fit a fixed length
    fit_w, fit_h = (crop_h, crop_w) if angle in (90, 270) else (crop_w, crop_h)
    zoom = (width - 2 * margin) / fit_w if height is None else min((width - 2 * margin) / fit_w, (height - 2 * margin) / fit_h)
    pic = doc.render(page, zoom, crop).convert('L')
    if angle:
        pic = pic.rotate(angle, expand=True)
    if height is None:
        height = pic.height + 2 * margin
    canvas = Image.new('L', (width, height), 255)
    canvas.paste(pic, ((width - pic.width) // 2, (height - pic.height) // 2))
    return lib.to_1bit(canvas, threshold)


def newest_download():
    folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    try:
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(FILE_TYPES)]
    except OSError:
        return None
    return max(files, key=os.path.getmtime) if files else None


class State:
    def __init__(self):
        self.doc, self.page, self.zoom, self.mode, self.manual = None, 0, 1.0, 'auto', None
        self.crop_figure, self.drag_figure, self.drag_start, self.drag_end, self.label = None, None, None, None, None


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def make_window():
    sg.theme(lib.THEME)
    length = lib.setting('ship_length') or '6 in  (4x6)'
    turn = lib.setting('ship_turn') or 'As is'
    left = sg.Column([[sg.Button('Open...', key=K_OPEN), sg.Button('Newest download', key=K_NEWEST, tooltip=' Newest PDF or picture in your Downloads folder '),
                       sg.Button('Paste', key=K_PASTE, tooltip=' Paste a picture from the clipboard (Ctrl+V) '),
                       sg.Text('', key=K_FILE, size=(28, 1), font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)],
                      [sg.Graph((GRAPH_W, GRAPH_H), (0, GRAPH_H), (GRAPH_W, 0), key=K_GRAPH, enable_events=True, drag_submits=True, background_color=lib.PREVIEW_BG)],
                      [sg.Button('< Prev', key=K_PREV), sg.Text('', key=K_PAGE, size=(11, 1), justification='c'), sg.Button('Next >', key=K_NEXT), sg.Push(),
                       sg.Text('Drag a box around the label', font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)]], vertical_alignment='top')
    find_buttons = [sg.Button('Auto', key=K_AUTO), sg.Button('Top half', key=K_TOP), sg.Button('Whole page', key=K_FULL)]
    find = sg.Frame('Find the label on the page', [find_buttons, [sg.Text('', key=K_CROP_INFO, size=(40, 1), font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)]], expand_x=True)
    media = lib.setting('ship_media') or lib.LABELS
    media_combo = sg.Combo(lib.MEDIA, media if media in lib.MEDIA else lib.LABELS, key=K_MEDIA, readonly=True, enable_events=True, size=(13, 1))
    turn_combo = sg.Combo(list(TURNS), turn if turn in TURNS else 'As is', key=K_TURN, readonly=True, enable_events=True, size=(11, 1))
    length_combo = sg.Combo(list(LENGTHS), length if length in LENGTHS else '6 in  (4x6)', key=K_LENGTH, readonly=True, enable_events=True, size=(11, 1))
    darker = sg.Slider((110, 230), lib.setting('ship_darker') or 160, orientation='h', key=K_DARKER, enable_events=True, size=(20, 15), disable_number_display=True)
    label = sg.Frame('Label', [[sg.Text('Print on'), media_combo, sg.Text('Rotate'), turn_combo], [sg.Text('Length'), length_combo, sg.Text('Lighter'), darker, sg.Text('Darker')]],
                     expand_x=True)
    preview = sg.Column([[sg.Image(key=K_PREVIEW, pad=(12, 12), background_color=lib.PREVIEW_BG)]], background_color=lib.PREVIEW_BG, element_justification='c', expand_x=True)
    print_row = [sg.Button('Print', key=K_PRINT, size=(10, 1), button_color=('white', lib.GREEN)), sg.Text('Copies'),
                 sg.Spin(list(range(1, 21)), initial_value=1, key=K_COPIES, size=(3, 1)), sg.Checkbox('Every page', key=K_ALL_PAGES, tooltip=' Print every page of the PDF ')]
    bottom_row = [sg.Push(), sg.Button('Feed 1 inch', key=K_FEED), sg.Button('Printer setup', key=K_SETUP, button_color=('white', lib.BLUE))]
    right = sg.Column([[find], [label], [preview], print_row, bottom_row], vertical_alignment='top')
    layout = [[left, sg.VerticalSeparator(), right], [sg.Text(lib.printer_summary(), key=K_STATUS, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)]]
    window = sg.Window('iD880 Ship Label', layout, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, finalize=True)
    lib.bind_scroll_keys(window)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Control-p>', K_CTRL_P)
    window.TKroot.bind('<Control-Alt-p>', lambda e: 'break')       # Ctrl+Alt+P belongs to other hotkeys (like typing PySimpleGUI) - it doesn't print
    window.bind('<Control-v>', K_CTRL_V)
    if psgdnd is not None:
        psgdnd.register_element_dnd(window[K_GRAPH], window, psgdnd.DROP_TYPE_FILES)
    prompt = 'Drag your shipping label (PDF or picture)\nhere, or click Open' if psgdnd is not None else 'Open the PDF or picture\nof your shipping label'
    window[K_GRAPH].draw_text(prompt, (GRAPH_W // 2, GRAPH_H // 2), color='white', font=('Helvetica', 14), text_location=sg.TEXT_LOCATION_CENTER)
    return window


def show_page(window, state):
    w, h = state.doc.size(state.page)
    state.zoom = min(GRAPH_W / w, GRAPH_H / h)
    graph = window[K_GRAPH]
    graph.erase()
    graph.draw_image(data=lib.png_bytes(state.doc.render(state.page, state.zoom)), location=(0, 0))
    state.crop_figure = None
    window[K_PAGE].update(f'Page {state.page + 1} of {state.doc.pages}')


def label_length(values):
    """Label length in dots, or None for 'Fit to width'"""
    inches = LENGTHS.get(values[K_LENGTH])
    return lib.inch_dots(inches) if inches else None


def update_label(window, state, values):
    crop = crop_for(state.doc, state.page, state.mode, state.manual)
    graph = window[K_GRAPH]
    if state.crop_figure is not None:
        graph.delete_figure(state.crop_figure)
    state.crop_figure = graph.draw_rectangle((crop[0] * state.zoom, crop[1] * state.zoom), (crop[2] * state.zoom, crop[3] * state.zoom), line_color='#FF5252', line_width=3)
    width = lib.media_width(values[K_MEDIA])
    state.label = build_label(state.doc, state.page, crop, TURNS[values[K_TURN]], width, label_length(values), int(values[K_DARKER]))
    window[K_PREVIEW].update(data=lib.preview_png(state.label, max_width=300, max_height=450))
    unit = 72 if state.doc.pdf is not None else None
    size = f'  -  {(crop[2] - crop[0]) / unit:.1f} x {(crop[3] - crop[1]) / unit:.1f} in' if unit else ''
    window[K_CROP_INFO].update(MODE_TEXT[state.mode] + size)


def open_document(window, state, values, path, picture=None):
    try:
        state.doc = Document(path, picture)
    except Exception as e:
        sg.popup_error('Could not open the file', path, str(e), title='iD880 Ship Label', keep_on_top=True)
        return
    state.page, state.mode, state.manual = 0, 'auto', None
    window[K_FILE].update(os.path.basename(path))
    if picture is None:
        lib.save_setting('ship_folder', os.path.dirname(os.path.abspath(path)))
    show_page(window, state)
    update_label(window, state, values)


def main():
    window = make_window()
    state = State()
    event, values = window.read(timeout=0)
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        open_document(window, state, values, sys.argv[1])
    while True:
        event, values = window.read()
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        if event == K_ESCAPE:
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70,10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == K_OPEN:
            path = sg.popup_get_file('Shipping label (PDF or picture)', initial_folder=lib.setting('ship_folder') or os.path.expanduser('~'), keep_on_top=True,
                                     file_types=(('Labels', ' '.join('*' + t for t in FILE_TYPES)), ('All files', '*.*')))
            if path:
                open_document(window, state, values, path)
        elif event == K_NEWEST:
            path = newest_download()
            if path:
                open_document(window, state, values, path)
            else:
                sg.popup_quick_message('No PDFs or pictures in your Downloads folder', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
        elif event in (K_PASTE, K_CTRL_V):
            try:
                grabbed = ImageGrab.grabclipboard()
            except Exception:
                grabbed = None
            if isinstance(grabbed, list):                           # copied files in Explorer come through as a list of paths
                grabbed = next((f for f in grabbed if str(f).lower().endswith(FILE_TYPES)), None)
                if grabbed:
                    open_document(window, state, values, str(grabbed))
                    continue
            if isinstance(grabbed, Image.Image):
                open_document(window, state, values, 'Clipboard picture', picture=grabbed)
            else:
                sg.popup_quick_message('No picture on the clipboard', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
        elif event == K_FEED:
            try:
                window[K_STATUS].update(f'Fed 1 inch    ({lib.printer_summary()})', text_color='#9CCC65')
                lib.feed(1)
            except Exception as e:
                window[K_STATUS].update('Feed failed - see the message', text_color='#FF8A65')
                lib.popup_print_error(e)
        elif event == K_SETUP:
            lib.open_setup()
        elif psgdnd is not None and psgdnd.is_drop_event(event):
            dropped = [f for f in str(values[event]).split(',') if f.lower().endswith(FILE_TYPES)]
            if dropped:
                open_document(window, state, values, dropped[0])
            else:
                sg.popup_quick_message('Drop a PDF or picture file', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
        elif state.doc is None:
            if event in (K_PRINT, K_CTRL_P):
                sg.popup_quick_message('Open a label first', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
            continue
        elif event in (K_PREV, K_NEXT) or lib.is_scroll_key(event):
            if lib.is_scroll_key(event) and lib.typing_has_focus(window):
                continue
            key = event[1] if lib.is_scroll_key(event) else None
            target = {K_PREV: state.page - 1, K_NEXT: state.page + 1, '<Prior>': state.page - 1, '<Up>': state.page - 1, '<Next>': state.page + 1, '<Down>': state.page + 1,
                      '<Home>': 0, '<End>': state.doc.pages - 1}[key or event]
            if 0 <= target < state.doc.pages and target != state.page:
                state.page = target
                show_page(window, state)
                update_label(window, state, values)
        elif event in (K_AUTO, K_TOP, K_FULL):
            state.mode = {K_AUTO: 'auto', K_TOP: 'top', K_FULL: 'full'}[event]
            update_label(window, state, values)
        elif event in (K_MEDIA, K_TURN, K_LENGTH, K_DARKER):
            lib.save_setting({K_MEDIA: 'ship_media', K_TURN: 'ship_turn', K_LENGTH: 'ship_length', K_DARKER: 'ship_darker'}[event], values[event])
            update_label(window, state, values)
        elif event == K_GRAPH:
            x, y = values[K_GRAPH]
            if x is None:
                continue
            graph = window[K_GRAPH]
            state.drag_start = state.drag_start or (x, y)
            state.drag_end = (x, y)
            if state.drag_figure is not None:
                graph.delete_figure(state.drag_figure)
            state.drag_figure = graph.draw_rectangle(state.drag_start, state.drag_end, line_color='#40C4FF', line_width=2)
        elif event == K_GRAPH_UP:
            if state.drag_figure is not None:
                window[K_GRAPH].delete_figure(state.drag_figure)
            if state.drag_start and state.drag_end and abs(state.drag_end[0] - state.drag_start[0]) > 8 and abs(state.drag_end[1] - state.drag_start[1]) > 8:
                (x0, x1), (y0, y1) = sorted((state.drag_start[0], state.drag_end[0])), sorted((state.drag_start[1], state.drag_end[1]))
                state.manual = (x0 / state.zoom, y0 / state.zoom, x1 / state.zoom, y1 / state.zoom)
                state.mode = 'manual'
                update_label(window, state, values)
            state.drag_figure = state.drag_start = state.drag_end = None
        elif event in (K_PRINT, K_CTRL_P):
            pages = range(state.doc.pages) if values[K_ALL_PAGES] else [state.page]
            width, height = lib.media_width(values[K_MEDIA]), label_length(values)
            try:
                jobs = [lib.build_job(build_label(state.doc, p, crop_for(state.doc, p, state.mode, state.manual), TURNS[values[K_TURN]], width, height, int(values[K_DARKER])),
                                      values[K_MEDIA], values[K_COPIES]) for p in pages]
                window[K_STATUS].update(f'Printed {len(jobs)} label(s): {lib.send_raw(b"".join(jobs))}    ({lib.printer_summary()})', text_color='#9CCC65')
            except Exception as e:
                window[K_STATUS].update('Print failed - see the message', text_color='#FF8A65')
                lib.popup_print_error(e)
    window.close()


if __name__ == '__main__':
    main()
