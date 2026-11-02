"""
SNAPSHOT TEST 7b - Spin.update() (13 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
value (in list, int, text NOT in the values list), values (replace
alone - documents what tk shows afterward, and replace + value
together), disabled (True and re-enable), readonly (set and clear),
visible (hide and hide->restore), no-arg update as a no-op, and
sequential updates (last wins).

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref->] sit next to a reference element constructed
directly in the target state - the pair should render identically.

NOTE variant 4: update(values=...) WITHOUT a value - tk's spinbox
typically displays the FIRST item of the new list. Whatever renders
becomes the documented baseline; the annotation marks it as the
interesting cell.
NOTE variant 9: disabled=False sets the tk state to 'normal', which
also clears a readonly state - same interplay as Combo.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Spin.update() - 13 variants (verified against 6.3.2 source)"

R11 = list(range(0, 11))
SIZES = ['XS', 'S', 'M', 'L', 'XL']

col_a = [
    [sg.Text('--- value, values ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 value in list (5->9)'), sg.Spin(R11, initial_value=5, key='-S1-')],
    [sg.Text('2 value string in list (M->XL)'), sg.Spin(SIZES, initial_value='M', key='-S2-')],
    [sg.Text('3 value NOT in list'), sg.Spin(R11, initial_value=5, size=(10, 1), key='-S3-'), sg.Text('<- "custom"')],
    [sg.Text('4 values replaced alone'), sg.Spin(R11, initial_value=5, size=(10, 1), key='-S4-'), sg.Text('<- what shows?')],
    [sg.Text('5 values + value together'), sg.Spin(R11, initial_value=5, size=(10, 1), key='-S5-'), sg.Text('<- L')],
    [sg.Text('6 update() no args'), sg.Spin(R11, initial_value=7, key='-S6-'), sg.Text('<- 7 kept')],
    [sg.Text('7 sequential, last wins'), sg.Spin(R11, initial_value=0, key='-S7-'), sg.Text('<- 3')],
]

col_b = [
    [sg.Text('--- state, visibility ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('8 disabled=True [ref->]'), sg.Spin(R11, text_color='red', initial_value=5, key='-S8-'), sg.Spin(R11, text_color='red', initial_value=5, disabled=True)],
    [sg.Text('9 disabled True->False (re-enabled)'), sg.Spin(R11, initial_value=5, disabled=True, key='-S9-')],
    [sg.Text('10 readonly=True [ref->]'), sg.Spin(R11, text_color='red', initial_value=5, key='-S10-'), sg.Spin(R11, text_color='red', initial_value=5, readonly=True)],
    [sg.Text('11 readonly True->False'), sg.Spin(R11, initial_value=5, readonly=True, key='-S11-')],
    [sg.Text('12 visible=False ->'), sg.Spin(R11, initial_value=5, key='-S12-'), sg.Text('<-')],
    [sg.Text('13 visible False->True ->'), sg.Spin(R11, initial_value=5, key='-S13-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 07 - Spin.update() (13)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

# ---- perform the updates (the snapshot captures the AFTER state) ----
window['-S1-'].update(value=9)                                                  # 1
window['-S2-'].update(value='XL')                                               # 2
window['-S3-'].update(value='custom')                                           # 3
window['-S4-'].update(values=SIZES)                                             # 4
window['-S5-'].update(values=SIZES, value='L')                                  # 5
window['-S6-'].update()                                                         # 6
window['-S7-'].update(value=1)                                                  # 7
window['-S7-'].update(value=3)                                                  #    last wins
window['-S8-'].update(disabled=True)                                            # 8
window['-S9-'].update(disabled=False)                                           # 9
window['-S10-'].update(readonly=True)                                           # 10
window['-S11-'].update(readonly=True)                                           # 11
window['-S11-'].update(readonly=False)
window['-S12-'].update(visible=False)                                           # 12
window['-S13-'].update(visible=False)                                           # 13
window['-S13-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_07_spin_update.png')
window.close()
