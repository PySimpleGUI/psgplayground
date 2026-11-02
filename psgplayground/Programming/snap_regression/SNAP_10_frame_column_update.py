"""
SNAPSHOT TEST 10b - Frame.update() (5) + Column.update() (3) = 8
variants, non-interactive. Combined because both signatures are tiny:
Frame.update(value, visible) - value is the TITLE text.
Column.update(visible) - visibility only.

Pattern: created "before", update() after finalize, snapshot = "after".
[ref->] pairs must render identically.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Frame.update()(5) + Column.update()(3) - 8 variants"

def content(txt):
    return [[sg.Text(txt)]]

col_f = [
    [sg.Text('--- Frame.update() ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('F1 title changed [ref->]'),
     sg.Frame('BEFORE', content('title updated'), key='-F1-'),
     sg.Frame('AFTER', content('constructed'))],
    [sg.Text('F2 title empty string'),
     sg.Frame('title gone', content('no title now'), key='-F2-')],
    [sg.Text('F3 update() no args'),
     sg.Frame('unchanged', content('no-op'), key='-F3-')],
    [sg.Text('F4 visible=False ->'),
     sg.Frame('hidden', content('hidden'), key='-F4-'), sg.Text('<-')],
    [sg.Text('F5 visible False->True ->'),
     sg.Frame('restored', content('restored'), key='-F5-'), sg.Text('<-')],
]

col_c = [
    [sg.Text('--- Column.update() ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('C1 visible=False ->'),
     sg.Column(content('hidden column'), key='-C1-'), sg.Text('<-')],
    [sg.Text('C2 visible False->True ->'),
     sg.Column(content('restored column'), key='-C2-'), sg.Text('<-')],
    [sg.Text('C3 update() no args'),
     sg.Column(content('no-op column'), key='-C3-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_f, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 10 - Frame/Column update() (8)', layout,
                   finalize=True, resizable=True, keep_on_top=True)

window['-F1-'].update(value='AFTER')                                            # F1
window['-F2-'].update(value='')                                                 # F2
window['-F3-'].update()                                                         # F3
window['-F4-'].update(visible=False)                                            # F4
window['-F5-'].update(visible=False)                                            # F5
window['-F5-'].update(visible=True)
window['-C1-'].update(visible=False)                                            # C1
window['-C2-'].update(visible=False)                                            # C2
window['-C2-'].update(visible=True)
window['-C3-'].update()                                                         # C3

window.refresh()
snap_window(window, 'output/screenshots/SNAP_10_frame_column_update.png')
window.close()
