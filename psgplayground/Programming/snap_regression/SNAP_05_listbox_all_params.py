"""
SNAPSHOT 5 - Listbox (18), reflowed into 3 columns of 6.

All listboxes get an explicit size=(10, 5) unless the variant tests its
own size - without it tk renders a clipped 1-item-high box. Variant
parameters are unchanged from the original single-column version; only
the layout moved.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Listbox-18"

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

col_a = [
    [sg.Text('1 SINGLE'), sg.Listbox(DAYS, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, size=(10, 5), key='-L1-')],
    [sg.Text('2 BROWSE'), sg.Listbox(DAYS, select_mode=sg.LISTBOX_SELECT_MODE_BROWSE, size=(10, 5), key='-L2-')],
    [sg.Text('3 EXTENDED'), sg.Listbox(DAYS, select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED, size=(10, 5), key='-L3-')],
    [sg.Text('4 MULTIPLE'), sg.Listbox(DAYS, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, size=(10, 5), key='-L4-')],
    [sg.Text('5 Preselected'), sg.Listbox(DAYS, default_values=['Tue', 'Thu'], size=(10, 5), key='-L5-')],
    [sg.Text('6 SmallScroll'), sg.Listbox(DAYS, size=(10, 3), key='-L6-')],
]

col_b = [
    [sg.Text('7 Colors'), sg.Listbox(DAYS, background_color='black', text_color='lime', size=(10, 5), key='-L7-')],
    [sg.Text('8 Bold'), sg.Listbox(DAYS, font=('Helvetica', 12, 'bold'), size=(10, 5), key='-L8-')],
    [sg.Text('9 Disabled'), sg.Listbox(DAYS, disabled=True, size=(10, 5), key='-L9-')],
    [sg.Text('10 Tooltip'), sg.Listbox(DAYS, tooltip='Listbox tip!', size=(10, 5), key='-L10-')],
    [sg.Text('11 EnableEvents'), sg.Listbox(DAYS, enable_events=True, size=(10, 5), key='-L11-')],
    [sg.Text('12 NoScrollbar'), sg.Listbox(DAYS, no_scrollbar=True, size=(10, 5), key='-L12-')],
]

col_c = [
    [sg.Text('13 HScroll'), sg.Listbox(DAYS, horizontal_scroll=True, size=(10, 5), key='-L13-')],
    [sg.Text('14 RightClick'), sg.Listbox(DAYS, right_click_menu=['', ['A', 'B']], size=(10, 5), key='-L14-')],
    [sg.Text('15 Pad'), sg.Listbox(DAYS, pad=(20, 20), size=(10, 5), key='-L15-')],
    [sg.Text('16 HighlightColors'), sg.Listbox(DAYS, highlight_text_color='white', highlight_background_color='blue', size=(10, 5), key='-L16-')],
    [sg.Text('17 Courier'), sg.Listbox(DAYS, font=('Courier', 12), size=(12, 4), key='-L17-')],
    [sg.Text('18 Visible=False ->'), sg.Listbox(DAYS, visible=False, size=(10, 5), key='-L18-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header)],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 05 - Listbox (18)', layout, finalize=True, resizable=True)
snap_window(window, 'output/screenshots/SNAP_05_listbox_all_params.png')
window.close()