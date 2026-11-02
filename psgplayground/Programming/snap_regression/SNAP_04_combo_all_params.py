"""
SNAPSHOT TEST 4 - Combo Element (26 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Original
variants 1-20 kept with identical parameters (reflowed into columns);
21-26 appended. Covered: values, default_value (first/last/custom text
NOT in list), size/s (tuple + bare int), auto_size_text, background/
text colors, button_background_color, button_arrow_color, readonly,
disabled, font, tooltip, pad/p, expand_x, visible.
NOT covered: bind_return_key/change_submits/enable_events/
enable_per_char_events (behavioral), key/k/setting/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Combo Element - 26 parameter variants (verified against 6.3.2 source)"

FRUIT = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry']

col_a = [
    [sg.Text('1 Plain editable'), sg.Combo(FRUIT, key='-C1-')],
    [sg.Text('2 Readonly'), sg.Combo(FRUIT, readonly=True, key='-C2-')],
    [sg.Text('3 enable_events'), sg.Combo(FRUIT, enable_events=True, key='-C3-')],
    [sg.Text('4 Small size 8'), sg.Combo(FRUIT, size=(8, 1), key='-C4-')],
    [sg.Text('5 Large size 30'), sg.Combo(FRUIT, size=(30, 1), key='-C5-')],
    [sg.Text('6 Custom colors black/lime'), sg.Combo(FRUIT, background_color='black', text_color='lime', key='-C6-')],
    [sg.Text('7 Bold font'), sg.Combo(FRUIT, font=('Helvetica', 12, 'bold'), key='-C7-')],
    [sg.Text('8 Tooltip'), sg.Combo(FRUIT, tooltip='Combo tooltip!', key='-C8-')],
    [sg.Text('9 Disabled'), sg.Combo(FRUIT, disabled=True, key='-C9-')],
]

col_b = [
    [sg.Text('10 Default last item'), sg.Combo(FRUIT, default_value='Elderberry', key='-C10-')],
    [sg.Text('11 Default first item'), sg.Combo(FRUIT, default_value='Apple', key='-C11-')],
    [sg.Text('12 button_arrow_color'), sg.Combo(FRUIT, button_arrow_color='red', key='-C12-')],
    [sg.Text('13 button_background_color'), sg.Combo(FRUIT, button_background_color='yellow', key='-C13-')],
    [sg.Text('14 Courier font'), sg.Combo(FRUIT, font=('Courier', 12), key='-C14-')],
    [sg.Text('15 Right-click menu'), sg.Combo(FRUIT, right_click_menu=['', ['Item A', 'Item B']], key='-C15-')],
    [sg.Text('16 pad=(20,20)'), sg.Combo(FRUIT, pad=(20, 20), key='-C16-')],
    [sg.Text('17 expand_x=True'), sg.Combo(FRUIT, expand_x=True, key='-C17-')],
    [sg.Text('18 Visible=False (label only)'), sg.Combo(FRUIT, visible=False, key='-C18-')],
]

col_c = [
    [sg.Text('19 auto_size_text=False'), sg.Combo(FRUIT, auto_size_text=False, size=(15, 1), key='-C19-')],
    [sg.Text('20 Combined color+font'), sg.Combo(FRUIT, background_color='navy', text_color='white', font=('Helvetica', 11, 'italic'), key='-C20-')],
    [sg.Text('21 default_value NOT in list'), sg.Combo(FRUIT, default_value='Custom typed text', key='-C21-')],
    [sg.Text('22 readonly + default + colors'), sg.Combo(FRUIT, readonly=True, default_value='Cherry',
                                                         background_color='light yellow', text_color='maroon', key='-C22-')],
    [sg.Text('23 s= size alias (12,1)'), sg.Combo(FRUIT, s=(12, 1), default_value='Banana', key='-C23-')],
    [sg.Text('24 size=25 bare int'), sg.Combo(FRUIT, size=25, default_value='Date', key='-C24-')],
    [sg.Text('25 p= alias asymmetric'), sg.Combo(FRUIT, p=((40, 5), (15, 0)), default_value='Apple', key='-C25-')],
    [sg.Text('26 arrow+button+text colors combined'), sg.Combo(FRUIT, default_value='Elderberry',
                                                               button_arrow_color='white', button_background_color='navy',
                                                               background_color='black', text_color='lime', key='-C26-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 04 - Combo Element All Params (26)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)
snap_window(window, 'output/screenshots/SNAP_04_combo_all_params.png')
window.close()
