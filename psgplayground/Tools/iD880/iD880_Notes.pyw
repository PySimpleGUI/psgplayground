#!/usr/bin/env python
"""
iD880 Notes - type a note, list or receipt and print it on the receipt paper (or the continuous labels) with the iD880

    Start a line with:   #  big heading      ##  heading      ###  small heading      #!  white-on-black banner
                         [ ] checkbox        [x] checked      -  or  *  bullet        ---  line across the paper
    Spaces in front of a line indent it - every 2 spaces is one step, so "  [ ] Milk" puts the box under the words of the line above.
    Keys in the editor - each one changes the line with the cursor (or every selected line), keeping its indent and words:
        Ctrl+B  checkbox      Ctrl+Shift+B  checked box      Ctrl+1 / 2 / 3  heading big / medium / small      Ctrl+4  banner
        Ctrl+0  plain line    Tab  one step right            Shift+Tab  one step left
    Ctrl+P prints.   Esc closes.   Click the preview, then Up/Down, PgUp/PgDn, Home/End scroll it.
    Your notes live as .txt files in one folder (pick it with Folder...).  Click a name in the list to load it - no file dialog.
    Ctrl+S saves.   Save as... asks only for a name.   Drop a .txt file on this program's icon to load it.
    The file you're working on opens again next time, and Save writes straight back to it - also for files from Open other file...

Needs id880_lib.py in the same folder.   Run iD880_Setup.pyw once first to pick the printer.
"""
import datetime
import os
import re
import sys

import PySimpleGUI as sg
from PIL import Image, ImageDraw

import id880_lib as lib

K_TEXT = '-TEXT-'
K_MEDIA = '-MEDIA-'
K_FAMILY = '-FAMILY-'
K_SIZE = '-SIZE-'
K_ALIGN = '-ALIGN-'
K_DATE = '-DATE-'
K_ALL_BOXES = '-ALL BOXES-'
K_COPIES = '-COPIES-'
K_PREVIEW = '-PREVIEW-'
K_PREVIEW_COL = '-PREVIEW COL-'
K_PREVIEW_CLICK = '-PREVIEW-+CLICK'
K_LENGTH = '-LENGTH-'
K_PRINT = '-PRINT-'
K_OPEN = '-OPEN-'
K_FILES = '-FILES-'
K_FOLDER = '-FOLDER-'
K_SAVE = '-SAVE-'
K_SAVE_AS = '-SAVE AS-'
K_NEW = '-NEW-'
K_DELETE = '-DELETE-'
K_FILE_NAME = '-FILE NAME-'
K_CTRL_S = '-CTRL S-'
K_CLEAR = '-CLEAR-'
K_SETUP = '-SETUP-'
K_FEED = '-FEED-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_CTRL_P = '-CTRL P-'
K_KEY_EDIT = '-KEY EDIT-'

OPTION_SETTINGS = {K_MEDIA: 'notes_media', K_FAMILY: 'notes_family', K_SIZE: 'notes_size', K_ALIGN: 'notes_align', K_DATE: 'notes_date', K_ALL_BOXES: 'notes_all_boxes'}

DEFAULT_FOLDER = os.path.join(os.path.expanduser('~'), 'Documents', 'iD880_Notes')
NOTE_TYPES = ('.txt', '.md')
INDENT_STEP = 2                                                     # spaces per indent step (a tab counts as one step)
LINE_START = re.compile(r'#!\s*|#{1,3}\s+|\[[ xX]\]\s*|[-*]\s+')    # what makes a line a banner, heading, checkbox or bullet
SYNTAX_HELP = ('#  heading    ##  smaller    ###  smallest    #!  banner\n[ ]  box    [x]  checked    -  bullet    ---  line\n'
               'Spaces in front indent a line')
KEYS_HELP = 'Ctrl+B  box    Ctrl+Shift+B  checked    Ctrl+0  plain\nCtrl+1  2  3  headings    Ctrl+4  banner    Tab  Shift+Tab  indent'
KEYS_HELP_COLOR = '#FFE082'

SAMPLE = '''#! GROCERIES
## Saturday
### Dairy
  [ ] Milk
  [x] Butter
### Pantry
  [ ] Coffee beans
## Sunday
[ ] Farmers market
  - Ask about the bakery's rye
---
Total budget: $40'''


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Drawing the note
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def mark_gap(f):
    """Distance from the left of a checkbox or bullet to its words - also the size of one indent step"""
    return round(f.size * 0.95)


def parse(text, family, points, all_boxes):
    """Typed text -> list of (kind, text, font, indent in dots).  Every INDENT_STEP spaces in front of a line indent it one step."""
    regular = lib.font(family, points)
    step = mark_gap(regular)                                        # one step puts a box under the words of an unindented box
    items = []
    for raw in text.rstrip().split('\n'):
        raw = raw.replace('\t', ' ' * INDENT_STEP)
        s = raw.strip()
        indent = round((len(raw) - len(raw.lstrip())) * step / INDENT_STEP)
        if s.startswith('#!'):
            items.append(('banner', s[2:].strip(), lib.font(family, points * 1.4, bold=True), 0))
        elif s.startswith('### '):
            items.append(('text', s[4:].strip(), lib.font(family, points * 1.1, bold=True), indent))
        elif s.startswith('## '):
            items.append(('text', s[3:].strip(), lib.font(family, points * 1.25, bold=True), indent))
        elif s.startswith('# '):
            items.append(('text', s[2:].strip(), lib.font(family, points * 1.6, bold=True), indent))
        elif s in ('---', '___', '==='):
            items.append(('rule', '', regular, 0))
        elif s[:3].lower() in ('[ ]', '[x]'):
            items.append(('checked' if s[1].lower() == 'x' else 'box', s[3:].strip(), regular, indent))
        elif s.startswith(('- ', '* ')):
            items.append(('bullet', s[2:].strip(), regular, indent))
        elif not s:
            items.append(('gap', '', regular, 0))
        else:
            items.append(('box' if all_boxes else 'text', s, regular, indent))
    return items


def draw_mark(d, x, y, f, kind):
    """Checkbox, checked box or bullet, centered on the text line that starts at y"""
    size = round(f.size * 0.62)
    top = round(y + f.getmetrics()[0] * 0.6 - size / 2)
    if kind == 'bullet':
        r = max(3, size // 4)
        d.ellipse([x + size // 2 - r, top + size // 2 - r, x + size // 2 + r, top + size // 2 + r], fill=0)
        return
    d.rectangle([x, top, x + size, top + size], outline=0, width=3)
    if kind == 'checked':
        d.line([(x + size * 0.2, top + size * 0.55), (x + size * 0.42, top + size * 0.8), (x + size * 0.85, top + size * 0.18)], fill=0, width=4)


def render(text, width, family, points, align, date_header, all_boxes):
    """The whole note as a grayscale picture exactly as wide as the paper (in printer dots)"""
    margin = lib.mm_dots(2)
    usable = width - 2 * margin
    items = parse(text, family, points, all_boxes)
    if date_header:
        stamp = datetime.datetime.now().strftime('%a %b %d, %Y   %I:%M %p')
        items = [('stamp', stamp, lib.font(family, max(9, points * 0.85)), 0), ('rule', '', None, 0)] + items
    ops, y = [], lib.mm_dots(3)
    for kind, s, f, indent in items:
        indent = min(indent, usable // 2)                           # a deep indent still leaves room for the words
        if kind == 'gap':
            y += lib.line_height(f) // 2
        elif kind == 'rule':
            ops.append(('rule', y + 10))
            y += 24
        elif kind == 'banner':
            pad, lh = lib.mm_dots(1.5), lib.line_height(f)
            lines = lib.wrap(s, f, usable - 2 * pad)
            ops.append(('fill', y, y + len(lines) * lh + 2 * pad))
            ops += [('text', margin + (usable - f.getlength(line)) / 2, y + pad + i * lh, line, f, 255) for i, line in enumerate(lines)]
            y += len(lines) * lh + 2 * pad + lib.mm_dots(1.5)
        elif kind in ('box', 'checked', 'bullet'):
            lh, gap = lib.line_height(f), mark_gap(f)
            lines = lib.wrap(s, f, usable - indent - gap)
            ops.append(('mark', margin + indent, y, f, kind))
            ops += [('text', margin + indent + gap, y + i * lh, line, f, 0) for i, line in enumerate(lines)]
            y += len(lines) * lh
        else:
            lh = lib.line_height(f)
            centered = kind == 'stamp' or align == 'Center'                 # centered lines ignore the indent
            for line in lib.wrap(s, f, usable if centered else usable - indent):
                ops.append(('text', margin + (usable - f.getlength(line)) / 2 if centered else margin + indent, y, line, f, 0))
                y += lh
    img = Image.new('L', (width, y + lib.mm_dots(5)), 255)
    d = ImageDraw.Draw(img)
    for op in ops:
        if op[0] == 'text':
            d.text(op[1:3], op[3], font=op[4], fill=op[5])
        elif op[0] == 'rule':
            d.line([(margin, op[1]), (width - margin, op[1])], fill=0, width=3)
        elif op[0] == 'fill':
            d.rectangle([margin, op[1], width - margin, op[2]], fill=0)
        elif op[0] == 'mark':
            draw_mark(d, *op[1:])
    return img


def update_preview(window, values):
    try:
        points = int(values[K_SIZE])
    except (TypeError, ValueError):
        points = 12
    img = render(values[K_TEXT], lib.media_width(values[K_MEDIA]), values[K_FAMILY], points, values[K_ALIGN], values[K_DATE], values[K_ALL_BOXES])
    img1 = lib.to_1bit(img)
    window[K_PREVIEW].update(data=lib.preview_png(img1, max_width=540))
    window.refresh()                                                # let tkinter size the new picture before the scroll area is measured
    window[K_PREVIEW_COL].contents_changed()
    window[K_LENGTH].update(f'{img1.height / lib.DPI:.1f} in  ({img1.height / lib.DOTS_PER_MM:.0f} mm) long')
    return img1


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def make_window(text):
    sg.theme(lib.THEME)
    media = lib.setting('notes_media') or lib.RECEIPT
    options = [sg.Text('Paper'), sg.Combo(lib.MEDIA, media if media in lib.MEDIA else lib.RECEIPT, key=K_MEDIA, readonly=True, enable_events=True, size=(13, 1)),
               sg.Text('Font'), sg.Combo(lib.FAMILIES, lib.setting('notes_family') or 'Sans', key=K_FAMILY, readonly=True, enable_events=True, size=(6, 1)),
               sg.Text('Size'), sg.Spin(list(range(8, 73)), initial_value=lib.setting('notes_size') or 12, key=K_SIZE, enable_events=True, size=(3, 1)),
               sg.Combo(['Left', 'Center'], lib.setting('notes_align') or 'Left', key=K_ALIGN, readonly=True, enable_events=True, size=(7, 1)),
               sg.Checkbox('Date & time at top', lib.setting('notes_date') or False, key=K_DATE, enable_events=True),
               sg.Checkbox('Every line is a checkbox', lib.setting('notes_all_boxes') or False, key=K_ALL_BOXES, enable_events=True)]
    files = sg.Column([[sg.Text('Notes', font=('Helvetica', 11, 'bold')), sg.Push(), sg.Button('Folder...', key=K_FOLDER, font=lib.SMALL_FONT)],
                       [sg.Listbox(list_notes(), key=K_FILES, size=(22, 22), enable_events=True, expand_y=True, tooltip=' Click a note to load it ')],
                       [sg.Button('New', key=K_NEW), sg.Button('Delete', key=K_DELETE, button_color=('white', lib.RED))]], vertical_alignment='top', expand_y=True)
    editor = sg.Column([[sg.Text('', key=K_FILE_NAME, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR, size=(40, 1)), sg.Push(),
                         sg.Button('Save', key=K_SAVE), sg.Button('Save as...', key=K_SAVE_AS)],
                        [sg.Multiline(text, key=K_TEXT, size=(42, 24), font=('Consolas', 12), enable_events=True, expand_x=True, expand_y=True)],
                        [sg.Text(SYNTAX_HELP, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)],
                        [sg.Text(KEYS_HELP, font=lib.SMALL_FONT, text_color=KEYS_HELP_COLOR)]],
                       expand_x=True, expand_y=True)
    preview = sg.Column([[sg.Image(key=K_PREVIEW, pad=(14, 14), background_color=lib.PREVIEW_BG)]], key=K_PREVIEW_COL, scrollable=True, vertical_scroll_only=True,
                        size=(580, 560), background_color=lib.PREVIEW_BG, expand_y=True)
    buttons = [sg.Button('Print', key=K_PRINT, size=(10, 1), button_color=('white', lib.GREEN)), sg.Text('Copies'),
               sg.Spin(list(range(1, 51)), initial_value=1, key=K_COPIES, size=(3, 1)), sg.Button('Open other file...', key=K_OPEN),
               sg.Button('Clear', key=K_CLEAR, button_color=('white', lib.RED)), sg.Push(), sg.Text('', key=K_LENGTH, font=lib.SMALL_FONT),
               sg.Button('Feed 1 inch', key=K_FEED), sg.Button('Printer setup', key=K_SETUP, button_color=('white', lib.BLUE))]
    layout = [options, [files, editor, preview], buttons, [sg.Text(lib.printer_summary(), key=K_STATUS, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)]]
    window = sg.Window('iD880 Notes', layout, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, finalize=True, resizable=True,
                       enable_close_attempted_event=True)          # the X asks about unsaved changes too
    lib.bind_scroll_keys(window)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Control-p>', K_CTRL_P)
    window.TKroot.bind('<Control-Alt-p>', lambda e: 'break')       # Ctrl+Alt+P belongs to other hotkeys (like typing PySimpleGUI) - it doesn't print
    window.bind('<Control-s>', K_CTRL_S)
    window[K_PREVIEW].bind('<Button-1>', '+CLICK')
    bind_editor_keys(window)
    return window


def chosen_lines(text_widget):
    """Line numbers of the selected lines, or of the line with the cursor"""
    sel = text_widget.tag_ranges('sel')
    first, last = (int(str(i).split('.')[0]) for i in (sel or (text_widget.index('insert'),) * 2))
    if sel and str(sel[1]).endswith('.0') and last > first:          # a selection ending at the start of a line leaves that line alone
        last -= 1
    return range(first, last + 1)


def indent_lines(text_widget, step):
    """Put INDENT_STEP spaces in front of the chosen lines, or take them away (step -1)"""
    for line in chosen_lines(text_widget):
        if step > 0:
            text_widget.insert(f'{line}.0', ' ' * INDENT_STEP)
        else:
            words = text_widget.get(f'{line}.0', f'{line}.end')
            text_widget.delete(f'{line}.0', f'{line}.{min(INDENT_STEP, len(words) - len(words.lstrip(" ")))}')


def set_line_start(text_widget, start):
    """Make the chosen lines checkboxes, headings... by swapping what they start with for start ('[ ] ', '## ', '' for plain).
    Their indent and words stay.  With one line, the cursor goes to its end, ready to type."""
    lines = chosen_lines(text_widget)
    for line in lines:
        words = text_widget.get(f'{line}.0', f'{line}.end')
        indent = len(words) - len(words.lstrip(' \t'))
        old = LINE_START.match(words, indent)
        text_widget.delete(f'{line}.{indent}', f'{line}.{old.end() if old else indent}')
        text_widget.insert(f'{line}.{indent}', start)
    if len(lines) == 1:
        text_widget.mark_set('insert', f'{lines[0]}.end')
        text_widget.see('insert')


def bind_editor_keys(window):
    """Editor keys:  Ctrl+B box, Ctrl+Shift+B checked box, Ctrl+1/2/3 headings, Ctrl+4 banner, Ctrl+0 plain, Tab / Shift+Tab indent.
    Each replaces what tkinter would do with the key (type a tab, move the focus...)"""
    text_widget = window[K_TEXT].Widget

    def edit(change):
        def on_key(event):
            change(event)
            window.write_event_value(K_KEY_EDIT, None)              # the editor's own change event doesn't fire for these keys
            return 'break'
        return on_key

    for key in ('<Control-b>', '<Control-B>'):                      # B with Shift held = checked.  Both names so Caps Lock doesn't matter.
        text_widget.bind(key, edit(lambda e: set_line_start(e.widget, '[x] ' if e.state & 0x0001 else '[ ] ')))
    for key, start in (('1', '# '), ('2', '## '), ('3', '### '), ('4', '#! '), ('0', '')):
        text_widget.bind(f'<Control-Key-{key}>', edit(lambda e, start=start: set_line_start(e.widget, start)))
    text_widget.bind('<Tab>', edit(lambda e: indent_lines(e.widget, 1)))
    for shift_tab in ('<Shift-Tab>', '<ISO_Left_Tab>'):             # Shift+Tab's name on Windows, and on Linux
        try:
            text_widget.bind(shift_tab, edit(lambda e: indent_lines(e.widget, -1)))
        except Exception:
            pass


def read_text_file(filename):
    with open(filename, encoding='utf-8', errors='replace') as f:
        return f.read()


def notes_folder():
    folder = lib.setting('notes_folder') or DEFAULT_FOLDER
    os.makedirs(folder, exist_ok=True)
    return folder


def list_notes():
    """Note names (without .txt) in the notes folder, newest first"""
    folder = notes_folder()
    names = [f for f in os.listdir(folder) if f.lower().endswith(NOTE_TYPES)]
    names.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
    return [os.path.splitext(f)[0] for f in names]


def note_path(name):
    """The file for the note called name in the notes folder - an existing .txt or .md, otherwise a new .txt"""
    name = os.path.splitext(name)[0] if name.lower().endswith(NOTE_TYPES) else name
    for ext in NOTE_TYPES:
        if os.path.isfile(os.path.join(notes_folder(), name + ext)):
            return os.path.join(notes_folder(), name + ext)
    return os.path.join(notes_folder(), name + '.txt')


def same_file(a, b):
    return bool(a and b) and os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def in_notes_folder(path):
    return bool(path) and same_file(os.path.dirname(path), notes_folder())


def note_name(path):
    """A note in the notes folder is shown by its name, any other file by its file name"""
    return os.path.splitext(os.path.basename(path))[0] if in_notes_folder(path) else os.path.basename(path)


def show_current(window, path):
    """Show the file the editor is working on (None = a new note) and remember it - it opens again next time, and Save goes straight to it"""
    lib.save_setting('notes_file', path)
    names = list_notes()
    name = note_name(path) if path else ''
    window[K_FILES].update(names, set_to_index=[names.index(name)] if in_notes_folder(path) and name in names else [])
    window[K_FILE_NAME].update(name if in_notes_folder(path) else f'{name}    (in {os.path.dirname(path)})' if path else '(new note)')


def save_file(window, path, text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    show_current(window, path)
    window[K_STATUS].update(f'Saved {note_name(path)}', text_color='#9CCC65')
    return path


def ask_name(current=None):
    """Ask for a note name -> its file in the notes folder (None if cancelled).  Asks before replacing a different note."""
    name = sg.popup_get_text('Name for this note', default_text=note_name(current) if current else '', title='iD880 Notes', keep_on_top=True)
    if not (name and name.strip()):
        return None
    path = note_path(name.strip())
    if os.path.isfile(path) and not same_file(path, current):
        if sg.popup_yes_no(f'There is already a note called "{note_name(path)}".  Replace it?', title='iD880 Notes', keep_on_top=True) != 'Yes':
            return None
    return path


def ask_save(name):
    """Save / Don't save / Cancel  ->  'Yes', 'No' or None"""
    layout = [[sg.Text(f'Save the changes to "{name}" first?')],
              [sg.Button('Save', key='Yes', button_color=('white', lib.GREEN), bind_return_key=True), sg.Button("Don't save", key='No'), sg.Button('Cancel')]]
    window = sg.Window('iD880 Notes', layout, keep_on_top=True, modal=True, finalize=True)
    window.bind('<Escape>', 'Cancel')
    event, _ = window.read(close=True)
    return event if event in ('Yes', 'No') else None


def ok_to_lose(window, values, current, saved_text):
    """True if the editor's text is unchanged, or the user agrees to drop (or saves) the changes"""
    if values[K_TEXT] == saved_text:
        return True
    answer = ask_save(note_name(current) if current else 'this note')
    if answer is None:
        return False
    if answer == 'Yes':
        path = current or ask_name()
        if not path:
            return False
        save_file(window, path, values[K_TEXT])
    return True


def main():
    current = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) else lib.setting('notes_file')
    current = current if current and os.path.isfile(current) else None     # the file being worked on - None for a new note with no name yet
    if current:
        text = read_text_file(current)
    else:
        text = lib.setting('notes_text')                            # a new note's text is kept from last time
        text = SAMPLE if text is None else text
    saved_text = text                                               # the text as last saved or loaded - anything else is a change
    window = make_window(text)
    show_current(window, current)
    img1, dirty = None, True
    while True:
        event, values = window.read(timeout=250 if dirty else None)
        if event in ('Exit', sg.WINDOW_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_ESCAPE):
            if values is None or ok_to_lose(window, values, current, saved_text):
                break
            continue
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70,10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif lib.is_scroll_key(event):
            lib.scroll_with_key(window, K_PREVIEW_COL, event)
        elif event == K_PREVIEW_CLICK:
            window[K_PREVIEW].Widget.focus_set()                    # so the scroll keys go to the preview
        elif event in (K_TEXT, K_KEY_EDIT):
            dirty = True
        elif event in OPTION_SETTINGS:
            lib.save_setting(OPTION_SETTINGS[event], values[event])
            dirty = True
        elif event == sg.TIMEOUT_KEY and dirty:
            img1, dirty = update_preview(window, values), False
            lib.save_setting('notes_text', values[K_TEXT])
        elif event in (K_PRINT, K_CTRL_P):
            if not values[K_TEXT].strip() and not values[K_DATE]:
                sg.popup_quick_message('Nothing to print yet', background_color=lib.ORANGE, text_color='white', keep_on_top=True)
                continue
            img1, dirty = update_preview(window, values), False
            try:
                window[K_STATUS].update(f'Printed: {lib.print_bitmap(img1, values[K_MEDIA], values[K_COPIES])}    ({lib.printer_summary()})', text_color='#9CCC65')
            except Exception as e:
                window[K_STATUS].update('Print failed - see the message', text_color='#FF8A65')
                lib.popup_print_error(e)
        elif event == K_FILES and values[K_FILES]:
            path = note_path(values[K_FILES][0])
            if not same_file(path, current) and ok_to_lose(window, values, current, saved_text):
                current, saved_text = path, read_text_file(path)
                window[K_TEXT].update(saved_text)
                dirty = True
            show_current(window, current)                           # if switching was cancelled, this highlights the note still being edited
        elif event in (K_SAVE, K_CTRL_S, K_SAVE_AS):
            path = current if current and event != K_SAVE_AS else ask_name(current)
            if path:
                current, saved_text = save_file(window, path, values[K_TEXT]), values[K_TEXT]
        elif event == K_NEW:
            if ok_to_lose(window, values, current, saved_text):
                current, saved_text = None, ''
                window[K_TEXT].update('')
                show_current(window, None)
                dirty = True
        elif event == K_DELETE and values[K_FILES]:
            path = note_path(values[K_FILES][0])
            if sg.popup_yes_no(f'Delete the note "{note_name(path)}"?', title='iD880 Notes', keep_on_top=True) == 'Yes':
                os.remove(path)
                if same_file(path, current):
                    current, saved_text = None, values[K_TEXT]      # the words stay in the editor as a new note
                show_current(window, current)
        elif event == K_FOLDER:
            folder = sg.popup_get_folder('Folder for your notes', default_path=notes_folder(), keep_on_top=True)
            if folder:
                lib.save_setting('notes_folder', folder)
                show_current(window, current)
        elif event == K_OPEN:
            filename = sg.popup_get_file('Text file to load', file_types=(('Text files', '*.txt *.md *.csv'), ('All files', '*.*')), keep_on_top=True)
            if filename and ok_to_lose(window, values, current, saved_text):
                current, saved_text = os.path.abspath(filename), read_text_file(filename)
                window[K_TEXT].update(saved_text)
                show_current(window, current)                       # Save now writes back to this file
                dirty = True
        elif event == K_CLEAR:
            if sg.popup_yes_no('Clear all the text?', title='iD880 Notes', keep_on_top=True) == 'Yes':
                window[K_TEXT].update('')
                dirty = True
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
