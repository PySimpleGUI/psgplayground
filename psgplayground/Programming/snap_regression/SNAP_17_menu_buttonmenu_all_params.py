"""
SNAPSHOT TEST 17 - Menu + ButtonMenu Elements, non-interactive.

Parameter lists verified against the PySimpleGUI 6.3.2 source.
Menu (only ONE menubar allowed per window, so the single sg.Menu here
stacks its styling params): menu_definition with separator + '!'
disabled item + '&' underline shortcut, background_color, text_color,
disabled_text_color, font. Menu tearoff not exercised (changes dropdown
only, invisible at rest).
ButtonMenu covered (14 variants): button_text, menu_def, button_color,
text_color/background_color, disabled, disabled_text_color, item_font,
font, tearoff, image_data (emoji), image_size, border_width, size,
auto_size_button=False clipping, pad, expand_x, tooltip, visible.
NOT covered: image_subsample/image_zoom (need a larger source image),
key/k/metadata.

NOTE: dropdown CONTENTS (item_font, item colors, tearoff strip, disabled
item greying) are not visible at rest - only the button/bar is captured.
Exercising them still smoke-tests that the release accepts the params.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Menu + ButtonMenu (verified against 6.3.2 source)"

menu_def = [['&File', ['&New', '&Open', '---', '!Disabled Item', 'E&xit']],
            ['&Edit', ['Copy', 'Paste']],
            ['Help', ['About']]]

MD = ['BM', ['Item A', 'Item B', '---', '!Item C Disabled']]

col_a = [
    [sg.Text('--- ButtonMenu: colors & state ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 plain:'), sg.ButtonMenu('1 Plain', MD, key='-BM1-')],
    [sg.Text('2 button_color tuple:'), sg.ButtonMenu('2 White on maroon', MD, button_color=('white', 'maroon'), key='-BM2-')],
    [sg.Text('3 text/background split:'), sg.ButtonMenu('3 White on navy', MD, text_color='white', background_color='navy', key='-BM3-')],
    [sg.Text('4 disabled:'), sg.ButtonMenu('4 Disabled', MD, disabled=True, key='-BM4-')],
    [sg.Text('5 item_font bold (dropdown only):'), sg.ButtonMenu('5 ItemFontBold', MD, item_font=('Helvetica', 12, 'bold'), key='-BM5-')],
    [sg.Text('6 tearoff=True (dropdown only):'), sg.ButtonMenu('6 Tearoff', MD, tearoff=True, key='-BM6-')],
    [sg.Text('7 disabled_text_color grey (dropdown):'), sg.ButtonMenu('7 DisabledGrey', MD, disabled_text_color='grey', key='-BM7-')],
]

col_b = [
    [sg.Text('--- ButtonMenu: fonts, size, images ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('8 button font Courier 12 bold:'), sg.ButtonMenu('8 Courier', MD, font=('Courier', 12, 'bold'), key='-BM8-')],
    [sg.Text('9 border_width=6:'), sg.ButtonMenu('9 Thick border', MD, border_width=6, key='-BM9-')],
    [sg.Text('10 size=(24,2):'), sg.ButtonMenu('10 Big fixed size', MD, size=(24, 2), key='-BM10-')],
    [sg.Text('11 auto_size=False size=(6,1) clips:'), sg.ButtonMenu('11 Clipped text', MD, auto_size_button=False, size=(6, 1), key='-BM11-')],
    [sg.Text('12 emoji image_data:'), sg.ButtonMenu('', MD, image_data=sg.EMOJI_BASE64_GOLD_STAR,
                                                    button_color=(sg.theme_background_color(), sg.theme_background_color()), key='-BM12-')],
    [sg.Text('13 pad=(30,15) + tooltip:'), sg.ButtonMenu('13 Padded', MD, pad=(30, 15), tooltip='ButtonMenu tooltip!', key='-BM13-')],
    [sg.Text('14 expand_x / hidden between arrows:'), sg.ButtonMenu('14 ExpandX', MD, expand_x=True, key='-BM14-'),
     sg.ButtonMenu('hidden', MD, visible=False, k='-BM15-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Menu(menu_def, background_color='black', text_color='white',
             disabled_text_color='grey', font=('Helvetica', 11))],
    [sg.Text('Menubar above: black bg, white text, & shortcuts underlined, one item disabled')],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 17 - Menu/ButtonMenu All Params', layout,
                   finalize=True, resizable=True, keep_on_top=True)
snap_window(window, 'output/screenshots/SNAP_17_menu_buttonmenu_all_params.png')
window.close()
