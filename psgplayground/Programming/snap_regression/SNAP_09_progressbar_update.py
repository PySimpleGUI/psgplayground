"""
SNAPSHOT TEST 9b - ProgressBar.update() (10 variants), non-interactive.

Signature: update(current_count, max, bar_color, visible). Covered:
current_count (mid, zero, full), max changed (same count renders as a
different fill proportion), bar_color [ref], combined count+max+color,
visible (hide and hide->restore), no-arg no-op, and legacy
update_bar(count, max) as a smoke variant.

Pattern: created "before", update() after finalize, snapshot = "after".
[ref->] pairs must render identically.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "ProgressBar.update() - 10 variants"

def PB(key=None, **kwargs):
    kw = dict(max_value=100, orientation='h', size=(30, 15))
    if key is not None:
        kw['key'] = key
    kw.update(kwargs)
    return sg.ProgressBar(**kw)

col_a = [
    [sg.Text('1 current_count=50 (half)'), PB('-P1-')],
    [sg.Text('2 current_count=0 (empty)'), PB('-P2-')],
    [sg.Text('3 current_count=100 (full)'), PB('-P3-')],
    [sg.Text('4 max 100->200, count 50 = quarter'), PB('-P4-')],
    [sg.Text('5 update() no args (stays empty)'), PB('-P5-')],
]

col_b = [
    [sg.Text('6 bar_color yellow/black [ref v]'), PB('-P6-')],
    [sg.Text('   reference'), PB('-P6R-', bar_color=('yellow', 'black'))],
    [sg.Text('7 count+max+color combined'), PB('-P7-')],
    [sg.Text('8 update_bar(75) legacy smoke'), PB('-P8-')],
    [sg.Text('9 visible=False ->'), PB('-P9-'), sg.Text('<-')],
    [sg.Text('10 visible False->True ->'), PB('-P10-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 09 - ProgressBar.update() (10)', layout,
                   finalize=True, resizable=True, keep_on_top=True)

window['-P1-'].update(current_count=50)                                         # 1
window['-P2-'].update(current_count=0)                                          # 2
window['-P3-'].update(current_count=100)                                        # 3
window['-P4-'].update(current_count=50, max=200)                                # 4
window['-P5-'].update()                                                         # 5
window['-P6-'].update(current_count=60, bar_color=('yellow', 'black'))          # 6
window['-P6R-'].update(current_count=60)                                        #    ref: same fill, constructed colors
window['-P7-'].update(current_count=150, max=200, bar_color=('red', 'white'))   # 7
window['-P8-'].update_bar(75)                                                   # 8  legacy API
window['-P9-'].update(visible=False)                                            # 9
window['-P10-'].update(visible=False)                                           # 10
window['-P10-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_09_progressbar_update.png')
window.close()
