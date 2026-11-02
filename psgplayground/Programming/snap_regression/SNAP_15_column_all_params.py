"""
SNAPSHOT TEST 15 - Column Element (16 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
layout, background_color, size/s, size_subsample_width/height (visible
clipping behavior on scrollable columns), pad, scrollable,
vertical_scroll_only, horizontal_scroll_only, element_justification,
vertical_alignment, expand_x/expand_y, visible, all sbar_* styling on a
scrollable column, grab. NOT covered (no resting-state visual):
justification (deprecated positioning param), right_click_menu,
enable_events, key/k/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

def col_content(n=6, tag=''):
    return [[sg.Text(f'{tag}Row {i}')] for i in range(n)]

header = "Column Element - 16 parameter variants (verified against 6.3.2 source)"

col_a = [
    [sg.Text('--- Size, Scrolling ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 default:'), sg.Column(col_content(3))],
    [sg.Text('2 scrollable vertical:'), sg.Column(col_content(10), scrollable=True, vertical_scroll_only=True, size=(160, 80))],
    [sg.Text('3 horizontal only:'), sg.Column([[sg.Text('Long row that scrolls horizontally sideways and keeps going')]], scrollable=True, horizontal_scroll_only=True, size=(160, 45))],
    [sg.Text('4 scrollable BOTH axes:'), sg.Column([[sg.Text(f'Wide row {i} ' + 'x' * 30)] for i in range(10)], scrollable=True, size=(160, 80))],
    [sg.Text('5 fixed size 160x60:'), sg.Column(col_content(3), size=(160, 60))],
    [sg.Text('6 s= alias 160x60:'), sg.Column(col_content(3), s=(160, 60))],
    [sg.Text('7 subsample w=2 (half width):'), sg.Column(col_content(8, 'Wide '), scrollable=True, vertical_scroll_only=True, size_subsample_width=2, size_subsample_height=2)],
    [sg.Text('8 subsample h=1 (full height):'), sg.Column(col_content(5), scrollable=True, vertical_scroll_only=True, size_subsample_height=1)],
]

col_b = [
    [sg.Text('--- Colors, Justification, Alignment ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('9 background grey:'), sg.Column(col_content(3), background_color='grey')],
    [sg.Text('10 element_justification=right:'), sg.Column([[sg.Text('right')], [sg.Button('right btn')]], element_justification='right', size=(160, 60))],
    [sg.Text('11 element_justification=center:'), sg.Column([[sg.Text('center')], [sg.Button('center btn')]], element_justification='center', size=(160, 60))],
    [sg.Text('12 expand_x:'), sg.Column(col_content(2), expand_x=True, background_color='light green')],
    [sg.Text('13 vertical_alignment top vs bottom:'),
     sg.Column([[sg.Text('TOP', background_color='pink')]], vertical_alignment='top'),
     sg.Column(col_content(4), background_color='light grey'),
     sg.Column([[sg.Text('BOTTOM', background_color='pink')]], vertical_alignment='bottom')],
    [sg.Text('14 pad=(30,15):'), sg.Column(col_content(2), pad=(30, 15), background_color='light yellow')],
    [sg.Text('15 sbar styled orange/navy w25:'), sg.Column(col_content(10), scrollable=True, vertical_scroll_only=True, size=(160, 80),
                                                           sbar_trough_color='orange', sbar_arrow_color='navy',
                                                           sbar_width=25, sbar_arrow_width=25)],
    [sg.Text('16 visible=False between arrows ->'), sg.Column(col_content(2), visible=False), sg.Text('<-'),
     sg.Column([[sg.Text('grab=True col', background_color='light blue')]], grab=True)],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 15 - Column Element All Params (16)', layout,
                   finalize=True, resizable=True, keep_on_top=True)
snap_window(window, 'output/screenshots/SNAP_15_column_all_params.png')
window.close()
