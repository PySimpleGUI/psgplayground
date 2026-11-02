"""
SNAPSHOT TEST 3 - Button Element (30 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Original
variants 1-24 kept with identical parameters (reflowed into columns);
25-30 appended. Covered: button_text, button_color (tuple + single
string), disabled, disabled_button_color, font, border_width, size/s
(incl. auto_size_button=False clipping), focus, bind_return_key,
tooltip, highlight_colors, mouseover_colors, use_ttk_buttons True/False,
right_click_menu, expand_x, pad/p, image_data, mouseover_image_source,
image_size, image_subsample, image_zoom, visible.
NOT covered: button_type/target/file_types/initial_folder/
default_extension (chooser-button plumbing, no resting visual),
image_filename/image_source (same paths as image_data),
change_submits/enable_events, key/k/metadata.

NOTE: variant 11 focus=True intentionally shows the focus ring - that
IS the feature under test. Window-level use_default_focus=False keeps
focus off everything else.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Button Element - 30 parameter variants (verified against 6.3.2 source)"

BG = (sg.theme_background_color(), sg.theme_background_color())

col_a = [
    [sg.Text('1 Plain'), sg.Button('1 Plain', key='-B1-')],
    [sg.Text('2 White on maroon'), sg.Button('2 White on maroon', button_color=('white', 'maroon'), key='-B2-')],
    [sg.Text('3 Black on gold'), sg.Button('3 Black on gold', button_color=('black', 'gold'), key='-B3-')],
    [sg.Text('4 Disabled'), sg.Button('4 Disabled', disabled=True, key='-B4-')],
    [sg.Text('5 Disabled custom color'), sg.Button('5 Disabled custom color', disabled=True, disabled_button_color=('grey', 'black'), key='-B5-')],
    [sg.Text('6 Bold font'), sg.Button('6 Bold font', font=('Helvetica', 12, 'bold'), key='-B6-')],
    [sg.Text('7 Large font 16'), sg.Button('7 Large font 16', font=('Helvetica', 16), key='-B7-')],
    [sg.Text('8 Thick border 6'), sg.Button('8 Thick border 6', border_width=6, key='-B8-')],
    [sg.Text('9 Big fixed size 20x3'), sg.Button('9 Big fixed size 20x3', size=(20, 3), key='-B9-')],
    [sg.Text('10 Small clipped size 6x1'), sg.Button('10 Small clipped size 6x1', size=(6, 1), auto_size_button=False, key='-B10-')],
]

col_b = [
    [sg.Text('11 Focus=True'), sg.Button('11 Focus=True', focus=True, key='-B11-')],
    [sg.Text('12 bind_return_key=True'), sg.Button('12 bind_return_key=True', bind_return_key=True, key='-B12-')],
    [sg.Text('13 Tooltip'), sg.Button('13 Tooltip', tooltip='Button tooltip!', key='-B13-')],
    [sg.Text('14 highlight_colors'), sg.Button('14 highlight_colors', highlight_colors=('red', 'white'), key='-B14-')],
    [sg.Text('15 mouseover_colors'), sg.Button('15 mouseover_colors', mouseover_colors=('white', 'green'), key='-B15-')],
    [sg.Text('16 use_ttk_buttons=True'), sg.Button('16 use_ttk_buttons=True', use_ttk_buttons=True, key='-B16-')],
    [sg.Text('17 use_ttk_buttons=False'), sg.Button('17 use_ttk_buttons=False', use_ttk_buttons=False, key='-B17-')],
    [sg.Text('18 button_color single string blue'), sg.Button('18 button_color single string blue', button_color='blue', key='-B18-')],
    [sg.Text('19 Right-click menu attached'), sg.Button('19 Right-click menu attached', right_click_menu=['', ['Item A', 'Item B']], key='-B19-')],
    [sg.Text('20 Expand X'), sg.Button('20 Expand X', expand_x=True, key='-B20-')],
]

col_c = [
    [sg.Text('21 pad=(30,30)'), sg.Button('21 pad=(30,30)', pad=(30, 30), key='-B21-')],
    [sg.Text('22 Combined color+font+border'), sg.Button('22 Combined color+font+border', button_color=('yellow', 'purple'), font=('Courier', 11, 'bold'), border_width=4, key='-B22-')],
    [sg.Text('23 Emoji image button'), sg.Button('', image_data=sg.EMOJI_BASE64_GOLD_STAR, button_color=BG, key='-B23-')],
    [sg.Text('24 Emoji + mouseover image'), sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_LAUGH, mouseover_image_source=sg.EMOJI_BASE64_HAPPY_BIG_SMILE, button_color=BG, key='-B24-')],
    [sg.Text('25 image_size=(80,80) stretch area'), sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_JOY, image_size=(80, 80), button_color=BG, key='-B25-')],
    [sg.Text('26 image_subsample=2 (half size)'), sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_JOY, image_subsample=2, button_color=BG, key='-B26-')],
    [sg.Text('27 image_zoom=2 (double size)'), sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_JOY, image_zoom=2, button_color=BG, key='-B27-')],
    [sg.Text('28 s= size alias (18,2)'), sg.Button('28 s alias', s=(18, 2), key='-B28-')],
    [sg.Text('29 p= alias asymmetric'), sg.Button('29 p alias', p=((40, 5), (15, 0)), key='-B29-')],
    [sg.Text('30 hidden between arrows ->'), sg.Button('hidden', visible=False, k='-B30-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 03 - Button Element All Params (30)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)
snap_window(window, 'output/screenshots/SNAP_03_button_all_params.png')
window.close()
