"""
SNAPSHOT TEST 12b - Table.update() (8 variants), non-interactive.

Signature: update(values, num_rows, visible, select_rows,
alternating_row_color, row_colors). Covered: values replaced (new data,
and fewer rows), num_rows changed (visible height), select_rows,
row_colors (per-row fg/bg), alternating_row_color, visible round trip,
no-arg no-op.

Pattern: created "before", update() after finalize, snapshot = "after".

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Table.update() - 8 variants"

HEADINGS = ['Name', 'Qty', 'Price']
DATA = [['Apple', 5, 1.25], ['Banana', 12, 0.50], ['Cherry', 40, 3.10], ['Date', 8, 4.00]]
DATA2 = [['Xray', 1, 9.99], ['Yankee', 2, 8.88]]

def T(key, **kwargs):
    kw = dict(values=DATA, headings=HEADINGS, num_rows=4, justification='left',
              auto_size_columns=False, col_widths=[8, 5, 6], key=key)
    kw.update(kwargs)
    return sg.Table(**kw)

col_a = [
    [sg.Text('1 values replaced (Xray/Yankee)'), T('-T1-')],
    [sg.Text('2 values fewer rows (2 of 4)'), T('-T2-')],
    [sg.Text('3 num_rows 4->2 (shorter)'), T('-T3-')],
    [sg.Text('4 select_rows=[1] (Banana)'), T('-T4-')],
]

col_b = [
    [sg.Text('5 row_colors: row0 white/red, row2 black/yellow'), T('-T5-')],
    [sg.Text('6 alternating_row_color grey'), T('-T6-')],
    [sg.Text('7 update() no args'), T('-T7-')],
    [sg.Text('8 visible False->True ->'), T('-T8-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 12 - Table.update() (8)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

window['-T1-'].update(values=DATA2)                                             # 1
window['-T2-'].update(values=DATA[:2])                                          # 2
window['-T3-'].update(num_rows=2)                                               # 3
window['-T4-'].update(select_rows=[1])                                          # 4
window['-T5-'].update(row_colors=[(0, 'white', 'red'),                          # 5
                                  (2, 'black', 'yellow')])
window['-T6-'].update(alternating_row_color='grey')                             # 6
window['-T7-'].update()                                                         # 7
window['-T8-'].update(visible=False)                                            # 8
window['-T8-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_12_table_update.png')
window.close()
