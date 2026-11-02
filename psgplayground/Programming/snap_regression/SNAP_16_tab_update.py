"""
SNAPSHOT TEST 16b - Tab.update() + Tab.select() (6 variants),
non-interactive. (TabGroup itself has no meaningful update();
post-finalize changes go through the individual Tabs.)

Tab signature: update(title, disabled, visible). Covered: title
changed, disabled=True [ref group], disabled True->False, tab hidden
via visible=False, hide->restore, and Tab.select() moving the active
tab (group shows Tab B selected instead of default first tab).

Pattern: created "before", update() after finalize, snapshot = "after".
Each variant gets its own small TabGroup so states can't interfere.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Tab.update() / Tab.select() - 6 variants"

def group(prefix, keys=('A', 'B', 'C')):
    return sg.TabGroup([[sg.Tab(f'{k}', [[sg.Text(f'{prefix} tab {k} content')]],
                                key=f'-{prefix}{k}-') for k in keys]])

col_a = [
    [sg.Text('1 title A->RENAMED'), group('T1')],
    [sg.Text('2 tab B disabled (grayed)'), group('T2')],
    [sg.Text('3 disabled True->False (B usable)'), group('T3')],
]

col_b = [
    [sg.Text('4 tab B hidden (A and C only)'), group('T4')],
    [sg.Text('5 tab B hidden then restored'), group('T5')],
    [sg.Text('6 select(): tab B active'), group('T6')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 16 - Tab update/select (6)', layout,
                   finalize=True, resizable=True, keep_on_top=True)

window['-T1A-'].update(title='RENAMED')                                         # 1
window['-T2B-'].update(disabled=True)                                           # 2
window['-T3B-'].update(disabled=True)                                           # 3
window['-T3B-'].update(disabled=False)
window['-T4B-'].update(visible=False)                                           # 4
window['-T5B-'].update(visible=False)                                           # 5
window['-T5B-'].update(visible=True)
window['-T6B-'].select()                                                        # 6

window.refresh()
snap_window(window, 'output/screenshots/SNAP_16_tab_update.png')
window.close()
