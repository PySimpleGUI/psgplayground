"""
SNAPSHOT TEST 6 - Checkbox(19) + Radio(19) = 38 elements, non-interactive.

Parameter lists verified against the PySimpleGUI 6.3.2 source. Original
Checkbox 1-15 and Radio 1-15 kept with identical parameters (reflowed
into side-by-side columns); CB16-19 and R16-19 appended.
Checkbox covered: text, default, disabled (both states), text/
background colors, checkbox_color, font, tooltip, highlight_thickness
(1 default, 5, 0), auto_size_text, size, pad/p, s alias, expand_x,
right_click_menu, visible. Radio covered: text, group_id (two groups
proving independent selection), default, disabled, circle_color,
font, colors, tooltip, auto_size_text, size, pad/p, s alias, expand_x,
right_click_menu, visible.
NOT covered: change_submits/enable_events (behavioral - kept from
original as smoke tests), key/k/setting/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Checkbox(19) + Radio(19) - 38 parameter variants (verified against 6.3.2 source)"

col_cb = [
    [sg.Text('--- Checkboxes ---', font=('Helvetica', 11, 'bold'))],
    [sg.Checkbox('1 Unchecked default', key='-CB1-')],
    [sg.Checkbox('2 Checked default', default=True, key='-CB2-')],
    [sg.Checkbox('3 Disabled unchecked', disabled=True, key='-CB3-')],
    [sg.Checkbox('4 Disabled checked', default=True, disabled=True, key='-CB4-')],
    [sg.Checkbox('5 Custom text/bg color', text_color='white', background_color='navy', key='-CB5-')],
    [sg.Checkbox('6 Orange checkbox_color', checkbox_color='orange', key='-CB6-')],
    [sg.Checkbox('7 Bold font', font=('Helvetica', 12, 'bold'), key='-CB7-')],
    [sg.Checkbox('8 Tooltip', tooltip='Checkbox tooltip!', key='-CB8-')],
    [sg.Checkbox('9 enable_events', enable_events=True, key='-CB9-')],
    [sg.Checkbox('10 Thick highlight_thickness=5', highlight_thickness=5, key='-CB10-')],
    [sg.Checkbox('11 auto_size_text=False size 20', auto_size_text=False, size=(20, 1), key='-CB11-')],
    [sg.Checkbox('12 Courier font', font=('Courier', 11), key='-CB12-')],
    [sg.Checkbox('13 pad=(20,20)', pad=(20, 20), key='-CB13-')],
    [sg.Checkbox('14 Right-click menu', right_click_menu=['', ['Item A', 'Item B']], key='-CB14-')],
    [sg.Checkbox('15 Visible=False (label only)', visible=False, key='-CB15-')],
    [sg.Checkbox('16 checkbox_color + checked', default=True, checkbox_color='lime', key='-CB16-')],
    [sg.Checkbox('17 highlight_thickness=0', highlight_thickness=0, key='-CB17-')],
    [sg.Checkbox('18 s= alias + p= alias', s=(25, 1), p=((40, 5), (15, 0)), key='-CB18-')],
    [sg.Checkbox('19 expand_x + bg', expand_x=True, background_color='light green', key='-CB19-')],
]

col_r = [
    [sg.Text('--- Radios (Group A / Group B) ---', font=('Helvetica', 11, 'bold'))],
    [sg.Radio('1 A default selected', 'GA', default=True, key='-R1-')],
    [sg.Radio('2 A plain', 'GA', key='-R2-')],
    [sg.Radio('3 A disabled', 'GA', disabled=True, key='-R3-')],
    [sg.Radio('4 A orange circle_color', 'GA', circle_color='orange', key='-R4-')],
    [sg.Radio('5 A bold font', 'GA', font=('Helvetica', 12, 'bold'), key='-R5-')],
    [sg.Radio('6 A custom colors', 'GA', text_color='white', background_color='maroon', key='-R6-')],
    [sg.Radio('7 A tooltip', 'GA', tooltip='Radio tooltip!', key='-R7-')],
    [sg.Radio('8 A enable_events', 'GA', enable_events=True, key='-R8-')],
    [sg.Radio('9 A pad=(20,20)', 'GA', pad=(20, 20), key='-R9-')],
    [sg.Radio('10 A visible=False', 'GA', visible=False, key='-R10-')],
    [sg.Radio('11 B default selected', 'GB', default=True, key='-R11-')],
    [sg.Radio('12 B disabled', 'GB', disabled=True, key='-R12-')],
    [sg.Radio('13 B Courier font', 'GB', font=('Courier', 11), key='-R13-')],
    [sg.Radio('14 B auto_size_text=False', 'GB', auto_size_text=False, size=(20, 1), key='-R14-')],
    [sg.Radio('15 B right-click menu', 'GB', right_click_menu=['', ['Item A', 'Item B']], key='-R15-')],
    [sg.Radio('16 B circle_color + selected', 'GC', default=True, circle_color='lime', key='-R16-')],
    [sg.Radio('17 B disabled + selected', 'GD', default=True, disabled=True, key='-R17-')],
    [sg.Radio('18 B s= alias + p= alias', 'GB', s=(25, 1), p=((40, 5), (15, 0)), key='-R18-')],
    [sg.Radio('19 B expand_x + bg', 'GB', expand_x=True, background_color='light green', key='-R19-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_cb, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_r, vertical_alignment='top')],
]

window = sg.Window('SNAP 06 - Checkbox/Radio All Params (38)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)
snap_window(window, 'output/screenshots/SNAP_06_checkbox_radio_all_params.png')
window.close()
