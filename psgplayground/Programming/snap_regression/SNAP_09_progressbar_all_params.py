"""
SNAPSHOT TEST 9 - ProgressBar Element (16 variants), non-interactive.
Bars pre-filled to varying levels before capture (25/50/75%) so partial
fill rendering is exercised, not just the half mark.

Parameter list verified against the PySimpleGUI 6.3.2 source. Original
variants 1-10 kept with identical parameters; 11-16 appended. Covered:
max_value, orientation h/v, size, s alias, size_px, bar_color, style
('clam'/'alt'/'classic' - cross-platform ttk styles; 'vista'/'xpnative'
are Windows-only and deliberately skipped so the suite runs anywhere),
border_width, relief (sunken/ridge/raised), pad/p, expand_x, visible.
NOT covered: auto_size_text (no effect on a bar), right_click_menu,
key/k/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "ProgressBar Element - 16 variants, filled 25/50/75% (verified against 6.3.2 source)"

col_a = [
    [sg.Text('1:'), sg.ProgressBar(100, orientation='h', size=(25, 20), key='-P1-')],
    [sg.Text('2:'), sg.ProgressBar(100, orientation='h', size=(25, 20), bar_color=('red', 'black'), key='-P2-')],
    [sg.Text('3:'), sg.ProgressBar(100, orientation='v', size=(5, 10), key='-P3-')],
    [sg.Text('4:'), sg.ProgressBar(100, orientation='v', size=(5, 10), bar_color=('blue', 'white'), key='-P4-')],
    [sg.Text('5:'), sg.ProgressBar(100, orientation='h', size_px=(200, 30), key='-P5-')],
    [sg.Text('6:'), sg.ProgressBar(100, orientation='h', size=(25, 20), border_width=8, key='-P6-')],
    [sg.Text('7:'), sg.ProgressBar(100, orientation='h', size=(25, 20), relief=sg.RELIEF_SUNKEN, key='-P7-')],
    [sg.Text('8:'), sg.ProgressBar(100, orientation='h', size=(25, 20), relief=sg.RELIEF_RIDGE, key='-P8-')],
]

col_b = [
    [sg.Text('9:'), sg.ProgressBar(100, orientation='h', size=(10, 10), key='-P9-')],
    [sg.Text('10:'), sg.ProgressBar(100, orientation='h', size=(50, 30), key='-P10-')],
    [sg.Text('11 style=clam:'), sg.ProgressBar(100, orientation='h', size=(25, 20), style='clam', key='-P11-')],
    [sg.Text('12 style=alt:'), sg.ProgressBar(100, orientation='h', size=(25, 20), style='alt', key='-P12-')],
    [sg.Text('13 style=classic:'), sg.ProgressBar(100, orientation='h', size=(25, 20), style='classic', key='-P13-')],
    [sg.Text('14 relief raised border 4 pad 20,10:'), sg.ProgressBar(100, orientation='h', size=(25, 20),
                                                           relief=sg.RELIEF_RAISED, border_width=4, pad=(20, 10), key='-P14-')],
    [sg.Text('15 s= alias + p= alias:'), sg.ProgressBar(100, orientation='h', s=(25, 20),
                                                        p=((40, 5), (15, 0)), bar_color=('green', 'light grey'), key='-P15-')],
    [sg.Text('16 expand_x / hidden ->'), sg.ProgressBar(100, orientation='h', size=(15, 20), expand_x=True, key='-P16-'),
     sg.ProgressBar(100, orientation='h', size=(10, 20), visible=False, k='-P17-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 09 - ProgressBar Element All Params (16)', layout,
                   finalize=True, resizable=True, keep_on_top=True)
# Fill 25/50/75% cycling by variant number so partial fills are exercised
FILLS = {0: 25, 1: 50, 2: 75}
for i in range(1, 17):
    window[f'-P{i}-'].update(FILLS[i % 3])
snap_window(window, 'output/screenshots/SNAP_09_progressbar_all_params.png')
window.close()
